"""
CryptoTracker - Robinhood Chain Whale Wallet Finder v2

READ ONLY:
- Uses Robinhood Chain public JSON-RPC.
- Does NOT use Blockscout API.
- Does NOT load a private key.
- Cannot sign or send transactions.

Targets:
1) Unipcs
   JUGGERNAUT: 0xd7321801caae694090694ff55a9323139f043b88
   PONS:       0x39dbed3a2bd333467115de45665cc57f813c4571

2) DumbCrayonEater
   AI:         0x2e8c31162b855a2ffa90f6f8634643ad6f111e18

Method:
- Query ERC-20 Transfer logs directly with eth_getLogs.
- Build recipient/sender wallet candidates.
- Detect whether an address has deployed contract bytecode with eth_getCode.
- Prefer EOAs.
- For Unipcs, rank wallets that appear in BOTH JUGGERNAUT and PONS.
- For DumbCrayonEater, rank repeated AI recipient wallets.

This is discovery, not identity proof. We will verify top candidates against
known FOMO trades before adding them to the live SmartMoneyMonitor.
"""

from __future__ import annotations

import json
import sys
import time
from collections import Counter, defaultdict
from typing import Any

import requests

RPC_URL = "https://rpc.mainnet.chain.robinhood.com"
CHAIN_ID_EXPECTED = 4663

UNIPCS_JUGGERNAUT = "0xd7321801caae694090694ff55a9323139f043b88"
UNIPCS_PONS = "0x39dbed3a2bd333467115de45665cc57f813c4571"
DUMBCRAYON_AI = "0x2e8c31162b855a2ffa90f6f8634643ad6f111e18"

# keccak256("Transfer(address,address,uint256)")
TRANSFER_TOPIC0 = (
    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
)

# Public RPC is rate-limited. Keep chunks conservative.
BLOCK_CHUNK = 2_000
LOOKBACK_BLOCKS = 250_000
RPC_DELAY = 0.06
TOP_RESULTS = 20

session = requests.Session()
session.headers.update({
    "Content-Type": "application/json",
    "User-Agent": "CryptoTracker-RobinhoodWhaleFinder/2.0",
})

_rpc_id = 0


def rpc(method: str, params: list[Any]) -> Any:
    global _rpc_id
    _rpc_id += 1

    payload = {
        "jsonrpc": "2.0",
        "id": _rpc_id,
        "method": method,
        "params": params,
    }

    for attempt in range(5):
        r = session.post(RPC_URL, json=payload, timeout=30)

        if r.status_code in (429, 502, 503, 504):
            wait = min(2 ** attempt, 10)
            print(f"  RPC busy/rate-limited ({r.status_code}); retrying in {wait}s...")
            time.sleep(wait)
            continue

        r.raise_for_status()
        data = r.json()

        if "error" in data:
            err = data["error"]
            msg = str(err)

            # eth_getLogs providers often reject ranges that are too large.
            raise RuntimeError(msg)

        return data.get("result")

    raise RuntimeError("RPC unavailable after retries")


def hex_int(value: str) -> int:
    return int(value, 16)


def latest_block() -> int:
    return hex_int(rpc("eth_blockNumber", []))


def chain_id() -> int:
    return hex_int(rpc("eth_chainId", []))


def topic_to_address(topic: str) -> str:
    # Indexed EVM address is right-aligned in 32 bytes.
    return "0x" + topic[-40:].lower()


def get_code(address: str) -> str:
    return rpc("eth_getCode", [address, "latest"]) or "0x"


def is_contract(address: str, cache: dict[str, bool]) -> bool:
    address = address.lower()
    if address not in cache:
        try:
            code = get_code(address)
            cache[address] = code not in ("0x", "0x0", "")
        except Exception:
            # Unknown: don't automatically reject.
            cache[address] = False
        time.sleep(RPC_DELAY)
    return cache[address]


def get_logs_range(contract: str, start_block: int, end_block: int) -> list[dict]:
    filt = {
        "fromBlock": hex(start_block),
        "toBlock": hex(end_block),
        "address": contract,
        "topics": [TRANSFER_TOPIC0],
    }
    result = rpc("eth_getLogs", [filt])
    return result if isinstance(result, list) else []


def get_logs_adaptive(contract: str, start_block: int, end_block: int) -> list[dict]:
    """
    Query logs, recursively splitting the range when the public RPC rejects it.
    """
    try:
        return get_logs_range(contract, start_block, end_block)
    except Exception as exc:
        if start_block >= end_block:
            print(f"  Skipping block {start_block}: {exc}")
            return []

        mid = (start_block + end_block) // 2

        # Keep recursion from getting too chatty.
        if end_block - start_block > 50:
            print(
                f"  RPC rejected {end_block-start_block+1:,}-block range; "
                f"splitting..."
            )

        left = get_logs_adaptive(contract, start_block, mid)
        time.sleep(RPC_DELAY)
        right = get_logs_adaptive(contract, mid + 1, end_block)
        return left + right


def scan_contract(contract: str, from_block: int, to_block: int) -> list[dict]:
    all_logs: list[dict] = []
    current = from_block

    while current <= to_block:
        end = min(current + BLOCK_CHUNK - 1, to_block)

        try:
            logs = get_logs_adaptive(contract, current, end)
            all_logs.extend(logs)
            print(
                f"  blocks {current:,}-{end:,}: "
                f"{len(logs):,} transfers | total {len(all_logs):,}"
            )
        except Exception as exc:
            print(f"  ERROR blocks {current:,}-{end:,}: {exc}")

        current = end + 1
        time.sleep(RPC_DELAY)

    return all_logs


def parse_transfer_log(log: dict) -> dict | None:
    topics = log.get("topics") or []
    if len(topics) < 3:
        return None

    src = topic_to_address(topics[1])
    dst = topic_to_address(topics[2])

    try:
        amount_raw = int(log.get("data") or "0x0", 16)
    except ValueError:
        amount_raw = 0

    return {
        "from": src,
        "to": dst,
        "amount_raw": amount_raw,
        "block": hex_int(log.get("blockNumber") or "0x0"),
        "tx_hash": str(log.get("transactionHash") or ""),
        "log_index": hex_int(log.get("logIndex") or "0x0"),
    }


def build_stats(logs: list[dict]) -> dict[str, dict]:
    stats = defaultdict(lambda: {
        "in_count": 0,
        "out_count": 0,
        "in_raw": 0,
        "out_raw": 0,
        "first_block": None,
        "last_block": None,
        "tx_hashes": set(),
    })

    zero = "0x0000000000000000000000000000000000000000"

    for raw in logs:
        t = parse_transfer_log(raw)
        if not t:
            continue

        src = t["from"]
        dst = t["to"]
        block = t["block"]

        if dst != zero:
            d = stats[dst]
            d["in_count"] += 1
            d["in_raw"] += t["amount_raw"]
            d["tx_hashes"].add(t["tx_hash"])
            d["first_block"] = block if d["first_block"] is None else min(d["first_block"], block)
            d["last_block"] = block if d["last_block"] is None else max(d["last_block"], block)

        if src != zero:
            d = stats[src]
            d["out_count"] += 1
            d["out_raw"] += t["amount_raw"]
            d["tx_hashes"].add(t["tx_hash"])
            d["first_block"] = block if d["first_block"] is None else min(d["first_block"], block)
            d["last_block"] = block if d["last_block"] is None else max(d["last_block"], block)

    return stats


def candidate_score_single(s: dict) -> int:
    score = 0
    score += min(s["in_count"], 20) * 10
    score += min(len(s["tx_hashes"]), 20) * 3

    if s["in_count"] >= 2:
        score += 20
    if s["in_count"] >= 4:
        score += 30
    if s["in_count"] >= 8:
        score += 40

    if s["in_count"] > s["out_count"]:
        score += 10

    return score


def print_candidate(rank: int, wallet: str, score: int, s: dict, contract_flag: bool):
    kind = "CONTRACT" if contract_flag else "EOA"
    print(
        f"#{rank:<2} score={score:<4} {kind:<8} {wallet}"
    )
    print(
        f"    IN={s['in_count']} OUT={s['out_count']} "
        f"txs={len(s['tx_hashes'])} "
        f"blocks={s['first_block']}-{s['last_block']}"
    )


def run_unipcs(start: int, end: int):
    print()
    print("=" * 92)
    print("UNIPCS - DIRECT RPC DISCOVERY")
    print("=" * 92)
    print(f"JUGGERNAUT: {UNIPCS_JUGGERNAUT}")
    print(f"PONS:       {UNIPCS_PONS}")
    print()

    print("Scanning JUGGERNAUT Transfer logs...")
    jug_logs = scan_contract(UNIPCS_JUGGERNAUT, start, end)

    print()
    print("Scanning PONS Transfer logs...")
    pons_logs = scan_contract(UNIPCS_PONS, start, end)

    jug = build_stats(jug_logs)
    pons = build_stats(pons_logs)

    addresses = set(jug) | set(pons)
    code_cache: dict[str, bool] = {}
    ranked = []

    for wallet in addresses:
        js = jug.get(wallet, {
            "in_count": 0, "out_count": 0, "tx_hashes": set(),
            "first_block": None, "last_block": None
        })
        ps = pons.get(wallet, {
            "in_count": 0, "out_count": 0, "tx_hashes": set(),
            "first_block": None, "last_block": None
        })

        score = candidate_score_single(js)

        cross = (
            (js["in_count"] or js["out_count"])
            and (ps["in_count"] or ps["out_count"])
        )

        if cross:
            score += 250

        if js["in_count"] >= 3:
            score += 40

        if ps["in_count"] >= 1:
            score += 40

        ranked.append((score, wallet, js, ps, cross))

    ranked.sort(key=lambda x: x[0], reverse=True)

    print()
    print("-" * 92)
    print("TOP UNIPCS CANDIDATES")
    print("-" * 92)

    shown = 0
    for score, wallet, js, ps, cross in ranked:
        contract_flag = is_contract(wallet, code_cache)

        # Show EOAs first; contracts are usually routers/pools.
        if contract_flag and shown >= 10:
            continue

        shown += 1
        label = "CROSS-TOKEN MATCH" if cross else ""
        print(f"#{shown:<2} score={score:<4} {'CONTRACT' if contract_flag else 'EOA':<8} {wallet} {label}")
        print(
            f"    JUGGERNAUT IN={js['in_count']} OUT={js['out_count']} "
            f"txs={len(js['tx_hashes'])}"
        )
        print(
            f"    PONS       IN={ps['in_count']} OUT={ps['out_count']} "
            f"txs={len(ps['tx_hashes'])}"
        )

        if cross and not contract_flag:
            print("    *** HIGH-INTEREST EOA: activity in BOTH anchor tokens ***")

        if shown >= TOP_RESULTS:
            break

    eoas_cross = []
    for score, wallet, js, ps, cross in ranked[:100]:
        if cross and not is_contract(wallet, code_cache):
            eoas_cross.append((score, wallet, js, ps))

    print()
    if eoas_cross:
        print("BEST UNIPCS LEADS:")
        for score, wallet, js, ps in eoas_cross[:5]:
            print(
                f"  {wallet} | score {score} | "
                f"JUG IN {js['in_count']} | PONS IN {ps['in_count']}"
            )
    else:
        print("No EOA cross-token match found in this block window.")


def run_dumbcrayon(start: int, end: int):
    print()
    print("=" * 92)
    print("DUMBCRAYONEATER - DIRECT RPC DISCOVERY")
    print("=" * 92)
    print(f"AI: {DUMBCRAYON_AI}")
    print()

    print("Scanning AI Transfer logs...")
    logs = scan_contract(DUMBCRAYON_AI, start, end)
    stats = build_stats(logs)

    ranked = []
    for wallet, s in stats.items():
        ranked.append((candidate_score_single(s), wallet, s))

    ranked.sort(key=lambda x: x[0], reverse=True)

    code_cache: dict[str, bool] = {}

    print()
    print("-" * 92)
    print("TOP DUMBCRAYONEATER CANDIDATES")
    print("-" * 92)

    eoa_results = []
    contract_results = []

    # Only code-check the highest scoring addresses to minimize public RPC load.
    for score, wallet, s in ranked[:100]:
        contract_flag = is_contract(wallet, code_cache)
        row = (score, wallet, s, contract_flag)
        if contract_flag:
            contract_results.append(row)
        else:
            eoa_results.append(row)

    print("EOA candidates:")
    for rank, (score, wallet, s, _) in enumerate(eoa_results[:TOP_RESULTS], 1):
        print_candidate(rank, wallet, score, s, False)

    if not eoa_results:
        print("  No EOAs found in highest-ranked addresses.")

    print()
    print("Highest-scoring contracts/routers (for reference):")
    for rank, (score, wallet, s, _) in enumerate(contract_results[:5], 1):
        print_candidate(rank, wallet, score, s, True)

    print()
    print(
        "A second DumbCrayon contract will let us cross-token match these EOAs "
        "the same way we do for Unipcs."
    )


def main():
    print("=" * 92)
    print("CRYPTOTRACKER - ROBINHOOD CHAIN WHALE FINDER v2")
    print("DIRECT JSON-RPC | READ ONLY | NO BLOCKSCOUT API | NO PRIVATE KEYS")
    print("=" * 92)

    print("Checking Robinhood Chain RPC...")
    cid = chain_id()
    latest = latest_block()

    print(f"Chain ID:     {cid}")
    print(f"Latest block: {latest:,}")

    if cid != CHAIN_ID_EXPECTED:
        print(f"ERROR: expected chain ID {CHAIN_ID_EXPECTED}, got {cid}")
        sys.exit(1)

    start = max(0, latest - LOOKBACK_BLOCKS)
    print(f"Scan window:  {start:,} -> {latest:,} ({latest-start:,} blocks)")
    print()
    print("1 = Find Unipcs")
    print("2 = Find DumbCrayonEater")
    print("3 = Run both")
    choice = input("Choose 1, 2, or 3: ").strip()

    if choice == "1":
        run_unipcs(start, latest)
    elif choice == "2":
        run_dumbcrayon(start, latest)
    elif choice == "3":
        run_unipcs(start, latest)
        run_dumbcrayon(start, latest)
    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()
