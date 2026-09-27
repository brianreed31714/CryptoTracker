"""
CryptoTracker - Unipcs Actual Funder Trace v5

READ ONLY.
- Robinhood Chain public JSON-RPC only.
- No Blockscout.
- No private key.
- No trading.
- Writes a plain-text log file for drag/drop back into ChatGPT.

Purpose:
Work backward from the JUGGERNAUT receipt transactions already identified
for the strongest Unipcs EOA candidates.

For each transaction:
1) Fetch transaction + receipt.
2) Record tx.from / tx.to.
3) Parse every ERC-20 Transfer log.
4) Identify:
   - who received JUGGERNAUT
   - who sent any payment-like assets
   - which contracts/routers were involved
5) Build a "funding actor" graph from direct token outflows.
6) Aggregate likely payer addresses across many JUGGERNAUT transactions.
7) Rank actual funder candidates by repeated participation.

This is discovery, not identity proof.
"""

from __future__ import annotations

import contextlib
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import requests

RPC_URL = "https://rpc.mainnet.chain.robinhood.com"
CHAIN_ID_EXPECTED = 4663

JUGGERNAUT = "0xd7321801caae694090694ff55a9323139f043b88".lower()
PONS = "0x39dbed3a2bd333467115de45665cc57f813c4571".lower()

TRANSFER_TOPIC0 = (
    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
)

# Strongest EOA candidates from the prior scan.
CANDIDATES = [
    "0x2dbaf98620ac5bbe3441f756feff82702d095b1a",
    "0xcd6b980029e6e6e0733ac8ec3e02be9410d09799",
    "0xc06ebbefd94032b85424d51906e2a335efae264b",
    "0xfad4c8f1e71e4c56b87733bd916ff7cff46c6c29",
    "0xd4627ecb405b64448ee6b07dcf860bf55590c83d",
    "0xca5b3bbb368db39d223a9fa57a577f9a98a03638",
    "0x8e2a9d954e7c88a00d3571eeab3d5e733a309426",
    "0x12d2b8ac38c59758a062a9f757f2740461779439",
    "0x5f1c5951c5b1cc112ba9e89b9467edca33063453",
    "0xb2e6cf3e1ff4ce3f4ecb0baebbc06e3f351f027e",
]

LOOKBACK_BLOCKS = 250_000
BLOCK_CHUNK = 2_000
RPC_DELAY = 0.05

TOP_FUNDERS = 30

session = requests.Session()
session.headers.update({
    "Content-Type": "application/json",
    "User-Agent": "CryptoTracker-UnipcsFunderTrace/5.0",
})

_rpc_id = 0
meta_cache: dict[str, tuple[str, int]] = {}
code_cache: dict[str, bool] = {}


def rpc(method: str, params: list[Any]) -> Any:
    global _rpc_id
    _rpc_id += 1
    payload = {"jsonrpc": "2.0", "id": _rpc_id, "method": method, "params": params}

    for attempt in range(5):
        r = session.post(RPC_URL, json=payload, timeout=30)

        if r.status_code in (429, 502, 503, 504):
            wait = min(2 ** attempt, 10)
            print(f"RPC busy ({r.status_code}); retrying in {wait}s...")
            time.sleep(wait)
            continue

        r.raise_for_status()
        data = r.json()

        if "error" in data:
            raise RuntimeError(str(data["error"]))

        return data.get("result")

    raise RuntimeError("RPC unavailable after retries")


def h2i(v: str | None) -> int:
    return int(v or "0x0", 16)


def latest_block() -> int:
    return h2i(rpc("eth_blockNumber", []))


def chain_id() -> int:
    return h2i(rpc("eth_chainId", []))


def topic_addr(topic: str) -> str:
    return "0x" + topic[-40:].lower()


def get_code(address: str) -> str:
    return rpc("eth_getCode", [address, "latest"]) or "0x"


def is_contract(address: str) -> bool:
    address = address.lower()
    if address not in code_cache:
        try:
            code_cache[address] = get_code(address) not in ("0x", "0x0", "")
        except Exception:
            code_cache[address] = False
        time.sleep(RPC_DELAY)
    return code_cache[address]


def get_logs(contract: str, start: int, end: int) -> list[dict]:
    filt = {
        "fromBlock": hex(start),
        "toBlock": hex(end),
        "address": contract,
        "topics": [TRANSFER_TOPIC0],
    }
    result = rpc("eth_getLogs", [filt])
    return result if isinstance(result, list) else []


def get_logs_adaptive(contract: str, start: int, end: int) -> list[dict]:
    try:
        return get_logs(contract, start, end)
    except Exception:
        if start >= end:
            return []
        mid = (start + end) // 2
        left = get_logs_adaptive(contract, start, mid)
        time.sleep(RPC_DELAY)
        right = get_logs_adaptive(contract, mid + 1, end)
        return left + right


def scan_contract(contract: str, start: int, end: int) -> list[dict]:
    out = []
    cur = start

    while cur <= end:
        hi = min(cur + BLOCK_CHUNK - 1, end)
        logs = get_logs_adaptive(contract, cur, hi)
        out.extend(logs)
        print(f"  blocks {cur:,}-{hi:,}: {len(logs):,} transfers")
        cur = hi + 1
        time.sleep(RPC_DELAY)

    return out


def parse_transfer(log: dict) -> dict | None:
    topics = log.get("topics") or []
    if len(topics) < 3 or str(topics[0]).lower() != TRANSFER_TOPIC0:
        return None

    try:
        amount_raw = int(log.get("data") or "0x0", 16)
    except Exception:
        amount_raw = 0

    return {
        "token": str(log.get("address") or "").lower(),
        "from": topic_addr(topics[1]),
        "to": topic_addr(topics[2]),
        "amount_raw": amount_raw,
        "tx_hash": str(log.get("transactionHash") or ""),
        "block": h2i(log.get("blockNumber")),
    }


def decode_symbol(raw: str) -> str:
    if not raw or raw == "0x":
        return ""

    data = bytes.fromhex(raw[2:])

    try:
        if len(data) >= 64:
            offset = int.from_bytes(data[0:32], "big")
            if offset + 32 <= len(data):
                length = int.from_bytes(data[offset:offset+32], "big")
                s = data[offset+32:offset+32+length].decode("utf-8", errors="ignore")
                if s:
                    return s.strip("\x00")
    except Exception:
        pass

    try:
        return data[:32].rstrip(b"\x00").decode("utf-8", errors="ignore")
    except Exception:
        return ""


def token_meta(contract: str) -> tuple[str, int]:
    contract = contract.lower()

    if contract in meta_cache:
        return meta_cache[contract]

    symbol = ""
    decimals = 18

    try:
        raw_symbol = rpc(
            "eth_call",
            [{"to": contract, "data": "0x95d89b41"}, "latest"],
        )
        symbol = decode_symbol(raw_symbol)
    except Exception:
        pass

    try:
        raw_decimals = rpc(
            "eth_call",
            [{"to": contract, "data": "0x313ce567"}, "latest"],
        )
        if raw_decimals and raw_decimals != "0x":
            decimals = int(raw_decimals, 16)
    except Exception:
        pass

    meta_cache[contract] = (symbol or contract[:10], decimals)
    time.sleep(RPC_DELAY)
    return meta_cache[contract]


def tx_receipt(tx_hash: str) -> dict:
    return rpc("eth_getTransactionReceipt", [tx_hash]) or {}


def tx_object(tx_hash: str) -> dict:
    return rpc("eth_getTransactionByHash", [tx_hash]) or {}


def candidate_jug_events(jug_logs: list[dict]) -> dict[str, list[dict]]:
    wanted = {x.lower() for x in CANDIDATES}
    events = defaultdict(list)

    for raw in jug_logs:
        t = parse_transfer(raw)
        if not t:
            continue
        if t["to"] in wanted:
            events[t["to"]].append(t)

    return events


def extract_all_transfers(receipt: dict) -> list[dict]:
    transfers = []
    for raw in receipt.get("logs") or []:
        t = parse_transfer(raw)
        if t:
            transfers.append(t)
    return transfers


def classify_actor(address: str) -> str:
    if not address:
        return "UNKNOWN"
    return "CONTRACT" if is_contract(address) else "EOA"


def inspect_tx(receiver: str, event: dict, funder_counter: Counter, funder_details: dict):
    txh = event["tx_hash"]
    receipt = tx_receipt(txh)
    tx = tx_object(txh)
    transfers = extract_all_transfers(receipt)

    tx_from = str(tx.get("from") or "").lower()
    tx_to = str(tx.get("to") or "").lower()

    print()
    print(f"TX {txh}")
    print(f"  block:      {event['block']:,}")
    print(f"  receiver:   {receiver}")
    print(f"  tx.from:    {tx_from or '-'} [{classify_actor(tx_from)}]")
    print(f"  tx.to:      {tx_to or '-'} [{classify_actor(tx_to)}]")

    # Identify JUG receipt and every actor sending a non-JUG token.
    payer_rows = []
    seen_payers = set()

    for t in transfers:
        if t["token"] == JUGGERNAUT and t["to"] == receiver:
            symbol, decimals = token_meta(t["token"])
            amount = t["amount_raw"] / (10 ** decimals)
            print(f"  JUG IN:     {amount:,.6f} {symbol}")

    for t in transfers:
        if t["token"] == JUGGERNAUT:
            continue

        sender = t["from"]
        if not sender or sender == "0x0000000000000000000000000000000000000000":
            continue

        symbol, decimals = token_meta(t["token"])
        amount = t["amount_raw"] / (10 ** decimals)

        payer_rows.append({
            "sender": sender,
            "recipient": t["to"],
            "token": t["token"],
            "symbol": symbol,
            "amount": amount,
        })

        if sender not in seen_payers:
            seen_payers.add(sender)
            funder_counter[sender] += 1
            funder_details[sender]["txs"].add(txh)
            funder_details[sender]["receivers"].add(receiver)
            funder_details[sender]["symbols"].add(symbol)

    if not payer_rows:
        print("  payment flows: none found outside JUGGERNAUT")
    else:
        print("  payment-like token outflows:")
        for row in payer_rows:
            print(
                f"    {row['sender']} -> {row['recipient']} | "
                f"{row['amount']:,.8f} {row['symbol']} "
                f"({row['token']})"
            )

    # Native value path from tx.from.
    native_value = h2i(tx.get("value")) / 1e18
    if native_value > 0:
        print(f"  native value: {native_value:,.8f}")
        funder_counter[tx_from] += 1
        funder_details[tx_from]["txs"].add(txh)
        funder_details[tx_from]["receivers"].add(receiver)
        funder_details[tx_from]["symbols"].add("NATIVE")

    return {
        "tx_hash": txh,
        "tx_from": tx_from,
        "tx_to": tx_to,
        "payer_rows": payer_rows,
        "native_value": native_value,
    }


def main_run():
    print("=" * 96)
    print("CRYPTOTRACKER - UNIPCS ACTUAL FUNDER TRACE v5")
    print("DIRECT ROBINHOOD CHAIN RPC | READ ONLY")
    print("=" * 96)

    cid = chain_id()
    latest = latest_block()

    print(f"Chain ID:     {cid}")
    print(f"Latest block: {latest:,}")

    if cid != CHAIN_ID_EXPECTED:
        raise RuntimeError(f"Expected chain ID {CHAIN_ID_EXPECTED}, got {cid}")

    start = max(0, latest - LOOKBACK_BLOCKS)
    print(f"Scan window:  {start:,} -> {latest:,}")
    print()

    print("Scanning JUGGERNAUT transfers...")
    jug_logs = scan_contract(JUGGERNAUT, start, latest)
    events_by_receiver = candidate_jug_events(jug_logs)

    total_candidate_events = sum(len(v) for v in events_by_receiver.values())
    print()
    print(f"Candidate JUGGERNAUT receipt events found: {total_candidate_events}")

    funder_counter = Counter()
    funder_details = defaultdict(lambda: {
        "txs": set(),
        "receivers": set(),
        "symbols": set(),
    })

    for receiver in CANDIDATES:
        receiver = receiver.lower()
        events = events_by_receiver.get(receiver, [])
        if not events:
            continue

        print()
        print("#" * 96)
        print(f"RECEIVER {receiver} | {len(events)} JUGGERNAUT txs")
        print("#" * 96)

        unique = {}
        for event in events:
            unique[event["tx_hash"]] = event

        for event in sorted(unique.values(), key=lambda x: x["block"]):
            try:
                inspect_tx(receiver, event, funder_counter, funder_details)
            except Exception as exc:
                print(f"  ERROR inspecting {event['tx_hash']}: {exc}")
            time.sleep(RPC_DELAY)

    print()
    print("=" * 96)
    print("AGGREGATED FUNDER CANDIDATES")
    print("=" * 96)

    ranked = []
    for address, count in funder_counter.items():
        details = funder_details[address]
        contract_flag = is_contract(address)
        score = count * 10
        if not contract_flag:
            score += 50
        if len(details["receivers"]) >= 2:
            score += 25
        if len(details["symbols"]) >= 2:
            score += 10

        ranked.append((
            score,
            address,
            count,
            contract_flag,
            details,
        ))

    ranked.sort(key=lambda x: (x[0], x[2]), reverse=True)

    for rank, (score, address, count, contract_flag, details) in enumerate(ranked[:TOP_FUNDERS], 1):
        print(
            f"#{rank:<2} score={score:<4} "
            f"{'CONTRACT' if contract_flag else 'EOA':<8} {address}"
        )
        print(
            f"    candidate tx appearances: {count} | "
            f"unique txs: {len(details['txs'])} | "
            f"receivers: {len(details['receivers'])}"
        )
        print(
            f"    symbols: {', '.join(sorted(details['symbols'])) or '-'}"
        )

    print()
    print("=" * 96)
    print("EOA-ONLY SHORTLIST")
    print("=" * 96)

    eoa_rank = [
        row for row in ranked if not row[3]
    ][:15]

    for rank, (score, address, count, _, details) in enumerate(eoa_rank, 1):
        print(
            f"#{rank:<2} {address} | score {score} | "
            f"tx appearances {count} | unique txs {len(details['txs'])} | "
            f"symbols {', '.join(sorted(details['symbols'])) or '-'}"
        )

    print()
    print("NEXT STEP:")
    print(
        "If one EOA dominates many of the JUGGERNAUT transactions, "
        "we will test that address against PONS and known FOMO timing/amounts."
    )


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for stream in self.streams:
            stream.write(data)
            stream.flush()
        return len(data)

    def flush(self):
        for stream in self.streams:
            stream.flush()


def main():
    script_dir = Path(__file__).resolve().parent
    log_path = script_dir / "unipcs_funder_trace_log.txt"

    with log_path.open("w", encoding="utf-8") as log_file:
        tee_out = Tee(sys.__stdout__, log_file)
        tee_err = Tee(sys.__stderr__, log_file)

        with contextlib.redirect_stdout(tee_out), contextlib.redirect_stderr(tee_err):
            print("=" * 96)
            print("LOGGING ENABLED")
            print(f"Log file: {log_path}")
            print("Upload this .txt file to ChatGPT after the run.")
            print("=" * 96)
            print()

            try:
                main_run()
            except KeyboardInterrupt:
                print("\nStopped by user.")
            except Exception:
                import traceback
                print("\nUNHANDLED ERROR")
                traceback.print_exc()
            finally:
                print()
                print("=" * 96)
                print("RUN COMPLETE")
                print(f"Upload: {log_path.name}")
                print("=" * 96)


if __name__ == "__main__":
    main()
