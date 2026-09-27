"""
CryptoTracker - Verify Unipcs Trade Fingerprint v3

READ ONLY.
- Queries Robinhood Chain public JSON-RPC directly.
- No Blockscout.
- No private key.
- No trading.

Goal:
Take the strongest EOA candidates from the prior Unipcs scan and reconstruct
their JUGGERNAUT buy transactions.

For each JUGGERNAUT receipt by a candidate wallet, this script:
1) Finds the transaction hash.
2) Downloads the transaction receipt.
3) Parses ERC-20 Transfer logs.
4) Looks for assets sent OUT by the candidate in the same transaction.
5) Queries token symbol/decimals.
6) If the outgoing asset looks USD-denominated, compares spend against the
   five known FOMO buy sizes:
      22,381.41
      19,611.72
      19,652.84
      19,240.00
      21,848.87
7) Reports the strongest candidate.

A 3+ trade-size match is strong evidence.
"""

from __future__ import annotations

import sys
import time
from collections import defaultdict
from typing import Any

import requests

RPC_URL = "https://rpc.mainnet.chain.robinhood.com"
CHAIN_ID_EXPECTED = 4663

JUGGERNAUT = "0xd7321801caae694090694ff55a9323139f043b88".lower()
PONS = "0x39dbed3a2bd333467115de45665cc57f813c4571".lower()

TRANSFER_TOPIC0 = (
    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
)

EXPECTED_USD = [22381.41, 19611.72, 19652.84, 19240.00, 21848.87]
MATCH_TOLERANCE_PCT = 6.0

# Strongest EOAs from your previous direct-RPC scan.
CANDIDATES = [
    "0x2dbaf98620ac5bbe3441f756feff82702d095b1a",
    "0xcd6b980029e6e6e0733ac8ec3e02be9410d09799",
    "0xd4627ecb405b64448ee6b07dcf860bf55590c83d",
    "0xc06ebbefd94032b85424d51906e2a335efae264b",
    "0x8e2a9d954e7c88a00d3571eeab3d5e733a309426",
    "0xfad4c8f1e71e4c56b87733bd916ff7cff46c6c29",
    "0xad01c28d5886137e056775af56915de824c8fce5",
    "0xca5b3bbb368db39d223a9fa57a577f9a98a03638",
    "0xb2e6cf3e1ff4ce3f4ecb0baebbc06e3f351f027e",
    "0x5f1c5951c5b1cc112ba9e89b9467edca33063453",
    "0x12d2b8ac38c59758a062a9f757f2740461779439",
]

LOOKBACK_BLOCKS = 250_000
BLOCK_CHUNK = 2_000
RPC_DELAY = 0.05

session = requests.Session()
session.headers.update({
    "Content-Type": "application/json",
    "User-Agent": "CryptoTracker-UnipcsFingerprint/3.0",
})

_rpc_id = 0
meta_cache: dict[str, tuple[str, int]] = {}


def rpc(method: str, params: list[Any]) -> Any:
    global _rpc_id
    _rpc_id += 1
    payload = {"jsonrpc": "2.0", "id": _rpc_id, "method": method, "params": params}

    for attempt in range(5):
        r = session.post(RPC_URL, json=payload, timeout=30)

        if r.status_code in (429, 502, 503, 504):
            wait = min(2 ** attempt, 10)
            print(f"  RPC busy ({r.status_code}); retrying in {wait}s...")
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


def decode_symbol(raw: str) -> str:
    if not raw or raw == "0x":
        return ""

    data = bytes.fromhex(raw[2:])

    # ABI dynamic string
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

    # bytes32 fallback
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


def parse_transfer(log: dict) -> dict | None:
    topics = log.get("topics") or []
    if len(topics) < 3 or topics[0].lower() != TRANSFER_TOPIC0:
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


def candidate_jug_buys(jug_logs: list[dict]) -> dict[str, list[dict]]:
    wanted = {x.lower() for x in CANDIDATES}
    buys = defaultdict(list)

    for log in jug_logs:
        t = parse_transfer(log)
        if not t:
            continue

        if t["to"] in wanted:
            buys[t["to"]].append(t)

    return buys


def candidate_pons_counts(pons_logs: list[dict]) -> dict[str, dict]:
    wanted = {x.lower() for x in CANDIDATES}
    counts = {w: {"in": 0, "out": 0} for w in wanted}

    for log in pons_logs:
        t = parse_transfer(log)
        if not t:
            continue

        if t["to"] in counts:
            counts[t["to"]]["in"] += 1
        if t["from"] in counts:
            counts[t["from"]]["out"] += 1

    return counts


def tx_receipt(tx_hash: str) -> dict:
    return rpc("eth_getTransactionReceipt", [tx_hash]) or {}


def tx_object(tx_hash: str) -> dict:
    return rpc("eth_getTransactionByHash", [tx_hash]) or {}


def outgoing_assets(wallet: str, receipt: dict) -> list[dict]:
    wallet = wallet.lower()
    totals = defaultdict(int)

    for raw in receipt.get("logs") or []:
        t = parse_transfer(raw)
        if not t:
            continue

        if t["from"] == wallet and t["token"] != JUGGERNAUT:
            totals[t["token"]] += t["amount_raw"]

    result = []

    for token, raw_amount in totals.items():
        symbol, decimals = token_meta(token)
        amount = raw_amount / (10 ** decimals) if decimals >= 0 else float(raw_amount)

        result.append({
            "token": token,
            "symbol": symbol,
            "decimals": decimals,
            "amount": amount,
        })

    return result


def looks_usd(symbol: str) -> bool:
    s = symbol.upper()
    markers = ("USD", "USDC", "USDT", "USDS", "DAI")
    return any(m in s for m in markers)


def best_size_match(amount: float, used: set[int]) -> tuple[int | None, float, float]:
    best_i = None
    best_expected = 0.0
    best_diff = 999999.0

    for i, exp in enumerate(EXPECTED_USD):
        if i in used:
            continue
        diff = abs(amount - exp) / exp * 100.0

        if diff < best_diff:
            best_i = i
            best_expected = exp
            best_diff = diff

    return best_i, best_expected, best_diff


def inspect_candidate(wallet: str, jug_events: list[dict], pons_stat: dict) -> dict:
    wallet = wallet.lower()
    print()
    print("=" * 90)
    print(f"CANDIDATE {wallet}")
    print(
        f"JUGGERNAUT receipts: {len(jug_events)} | "
        f"PONS IN {pons_stat['in']} OUT {pons_stat['out']}"
    )
    print("=" * 90)

    # Unique tx hashes only, sorted oldest -> newest by block.
    unique = {}
    for e in jug_events:
        unique[e["tx_hash"]] = e

    events = sorted(unique.values(), key=lambda x: x["block"])

    used_expected = set()
    matches = []
    stable_buys = []
    unknown_buys = []

    for n, event in enumerate(events, 1):
        txh = event["tx_hash"]

        try:
            receipt = tx_receipt(txh)
            tx = tx_object(txh)
        except Exception as exc:
            print(f"  {n:>2}. receipt error {txh[:12]}...: {exc}")
            continue

        assets = outgoing_assets(wallet, receipt)

        # Native value if wallet itself submitted the transaction.
        native_value = 0.0
        if str(tx.get("from") or "").lower() == wallet:
            native_value = h2i(tx.get("value")) / 1e18

        print(f"  BUY TX {n:>2} | block {event['block']:,}")
        print(f"    tx: {txh}")

        if not assets and native_value <= 0:
            print("    no direct outgoing asset detected from candidate")
            continue

        usd_asset_found = False

        for asset in assets:
            print(
                f"    OUT: {asset['amount']:,.6f} {asset['symbol']} "
                f"({asset['token']})"
            )

            if looks_usd(asset["symbol"]):
                usd_asset_found = True
                stable_buys.append(asset["amount"])

                i, expected, diff = best_size_match(asset["amount"], used_expected)

                if i is not None and diff <= MATCH_TOLERANCE_PCT:
                    used_expected.add(i)
                    matches.append({
                        "observed": asset["amount"],
                        "expected": expected,
                        "diff": diff,
                        "tx": txh,
                        "symbol": asset["symbol"],
                    })
                    print(
                        f"    >>> FOMO SIZE MATCH: ${asset['amount']:,.2f} "
                        f"vs ${expected:,.2f} ({diff:.2f}% diff)"
                    )

        if native_value > 0:
            print(f"    native tx value: {native_value:,.8f}")

        if not usd_asset_found:
            unknown_buys.append({
                "tx": txh,
                "assets": assets,
                "native": native_value,
            })

        time.sleep(RPC_DELAY)

    print()
    print("FINGERPRINT SUMMARY")
    print("-" * 90)
    print(f"Matched FOMO sizes: {len(matches)} / {len(EXPECTED_USD)}")

    for m in matches:
        print(
            f"  ${m['observed']:,.2f} {m['symbol']} "
            f"~ expected ${m['expected']:,.2f} | diff {m['diff']:.2f}%"
        )

    if stable_buys:
        print(f"Detected USD-like outgoing buys: {len(stable_buys)}")
        print(f"USD-like spend total: ${sum(stable_buys):,.2f}")

    print(f"PONS activity: IN {pons_stat['in']} / OUT {pons_stat['out']}")

    score = len(matches) * 200
    score += min(len(events), 20) * 5
    score += min(pons_stat["in"] + pons_stat["out"], 20) * 3

    if len(matches) >= 3:
        verdict = "VERY STRONG"
    elif len(matches) == 2:
        verdict = "PROMISING"
    elif len(matches) == 1:
        verdict = "WEAK"
    else:
        verdict = "NO SIZE MATCH"

    print(f"VERDICT: {verdict}")
    print(f"Verification score: {score}")

    return {
        "wallet": wallet,
        "matches": len(matches),
        "stable_total": sum(stable_buys),
        "jug_txs": len(events),
        "pons_in": pons_stat["in"],
        "pons_out": pons_stat["out"],
        "score": score,
        "verdict": verdict,
    }


def main():
    print("=" * 90)
    print("CRYPTOTRACKER - UNIPCS FOMO FINGERPRINT VERIFIER v3")
    print("DIRECT ROBINHOOD CHAIN RPC | READ ONLY")
    print("=" * 90)

    cid = chain_id()
    latest = latest_block()

    print(f"Chain ID: {cid}")
    print(f"Latest block: {latest:,}")

    if cid != CHAIN_ID_EXPECTED:
        print(f"ERROR: expected chain ID {CHAIN_ID_EXPECTED}")
        sys.exit(1)

    start = max(0, latest - LOOKBACK_BLOCKS)
    print(f"Scan window: {start:,} -> {latest:,}")
    print()
    print("Known FOMO JUGGERNAUT sizes:")
    print("  " + ", ".join(f"${x:,.2f}" for x in EXPECTED_USD))
    print()

    print("Scanning JUGGERNAUT...")
    jug_logs = scan_contract(JUGGERNAUT, start, latest)

    print()
    print("Scanning PONS...")
    pons_logs = scan_contract(PONS, start, latest)

    buys = candidate_jug_buys(jug_logs)
    pons = candidate_pons_counts(pons_logs)

    results = []

    for wallet in CANDIDATES:
        w = wallet.lower()

        if not buys.get(w):
            print(f"\nSkipping {w}: no JUGGERNAUT receipts in scan window.")
            continue

        result = inspect_candidate(
            w,
            buys[w],
            pons.get(w, {"in": 0, "out": 0}),
        )
        results.append(result)

    results.sort(
        key=lambda x: (x["matches"], x["score"], x["stable_total"]),
        reverse=True,
    )

    print()
    print("=" * 90)
    print("FINAL UNIPCS RANKING")
    print("=" * 90)

    for rank, r in enumerate(results, 1):
        print(
            f"#{rank} {r['wallet']} | "
            f"matches {r['matches']}/5 | "
            f"JUG txs {r['jug_txs']} | "
            f"PONS {r['pons_in']}/{r['pons_out']} | "
            f"USD spend ${r['stable_total']:,.2f} | "
            f"{r['verdict']}"
        )

    print()
    if results and results[0]["matches"] >= 3:
        print("TOP RESULT HAS A STRONG FOMO TRADE-SIZE FINGERPRINT.")
        print("Send me the FINAL UNIPCS RANKING plus its FOMO SIZE MATCH lines.")
    else:
        print("No candidate reached 3 trade-size matches.")
        print(
            "If spends are shown in a non-USD token, send me the top candidate "
            "transaction output and we'll add historical price conversion."
        )


if __name__ == "__main__":
    main()
