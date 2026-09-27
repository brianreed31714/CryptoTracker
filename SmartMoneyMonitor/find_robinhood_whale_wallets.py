"""
CryptoTracker - Robinhood Chain Whale Wallet Finder

READ ONLY.
- Does NOT load any private key.
- Cannot sign or send transactions.
- Uses the public Robinhood Chain Blockscout API.

Goal:
Find likely public EVM wallets for:
  1) Unipcs
  2) DumbCrayonEater

Starting anchors supplied from FOMO:
  Unipcs:
    PONS contract: 0x39dbed3a2bd333467115de45665cc57f813c4571
    JUGGERNAUT contract: 0xd7321801caae694090694ff55a9323139f043b88
    Known JUGGERNAUT buy sizes:
      $22,381.41, $19,611.72, $19,652.84, $19,240.00, $21,848.87

  DumbCrayonEater:
    Artificial Inu / AI contract:
      0x2e8c31162b855a2ffa90f6f8634643ad6f111e18

Method:
1. Pull recent ERC-20 transfer activity for the known token contract.
2. Build candidate EOA wallets receiving the token.
3. Look up each candidate wallet's token transfers.
4. Score wallets for repeated inbound buys / interaction with the anchor token.
5. For Unipcs, add a large bonus if the same wallet also interacts with PONS.
6. Show the top candidates plus explorer links for manual verification.

IMPORTANT:
This is wallet discovery, not identity proof. A top-ranked candidate should be
verified against FOMO timestamps / amounts before adding it to traders.json.
"""

from __future__ import annotations

import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode

import requests

BLOCKSCOUT = "https://robinhoodchain.blockscout.com/api/v2"
EXPLORER = "https://robinhoodchain.blockscout.com"

UNIPCS_JUGGERNAUT = "0xd7321801caae694090694ff55a9323139f043b88"
UNIPCS_PONS = "0x39dbed3a2bd333467115de45665cc57f813c4571"
DUMBCRAYON_AI = "0x2e8c31162b855a2ffa90f6f8634643ad6f111e18"

UNIPCS_KNOWN_BUYS = [22381.41, 19611.72, 19652.84, 19240.00, 21848.87]

# How many pages of token transfers to inspect.
# Increase if needed, but start modestly to avoid hammering the explorer.
TOKEN_PAGES = 10
ADDRESS_PAGES = 3
PAGE_DELAY = 0.12
TOP_CANDIDATES_TO_DEEP_CHECK = 40

session = requests.Session()
session.headers.update({
    "User-Agent": "CryptoTracker-WhaleFinder/1.0",
    "Accept": "application/json",
})


def get_json(url: str, params: dict | None = None) -> dict:
    r = session.get(url, params=params, timeout=25)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, dict):
        raise RuntimeError(f"Unexpected response from {url}: {type(data).__name__}")
    return data


def addr_hash(obj: Any) -> str:
    if isinstance(obj, dict):
        return str(obj.get("hash") or "").lower()
    return str(obj or "").lower()


def is_eoa(obj: Any) -> bool:
    if not isinstance(obj, dict):
        return True
    return not bool(obj.get("is_contract"))


def raw_token_amount(item: dict) -> float:
    total = item.get("total") or {}
    value = total.get("value")
    decimals = total.get("decimals")

    try:
        value_f = float(value)
    except (TypeError, ValueError):
        return 0.0

    try:
        decimals_i = int(decimals)
    except (TypeError, ValueError):
        decimals_i = 0

    return value_f / (10 ** decimals_i)


def fetch_paginated(url: str, max_pages: int, extra_params: dict | None = None) -> list[dict]:
    items: list[dict] = []
    params = dict(extra_params or {})

    for _ in range(max_pages):
        data = get_json(url, params=params or None)
        page_items = data.get("items") or []
        if not isinstance(page_items, list):
            break

        items.extend(page_items)

        next_params = data.get("next_page_params")
        if not isinstance(next_params, dict) or not next_params:
            break

        params = dict(extra_params or {})
        params.update(next_params)
        time.sleep(PAGE_DELAY)

    return items


def token_transfers(contract: str, pages: int = TOKEN_PAGES) -> list[dict]:
    url = f"{BLOCKSCOUT}/tokens/{contract}/transfers"
    return fetch_paginated(url, pages)


def address_token_transfers(wallet: str, pages: int = ADDRESS_PAGES) -> list[dict]:
    url = f"{BLOCKSCOUT}/addresses/{wallet}/token-transfers"
    return fetch_paginated(url, pages, {"type": "ERC-20"})


def contract_of_transfer(item: dict) -> str:
    token = item.get("token") or {}
    return str(token.get("address_hash") or "").lower()


def timestamp_str(item: dict) -> str:
    return str(item.get("timestamp") or "")


def initial_candidates(contract: str) -> tuple[Counter, dict]:
    transfers = token_transfers(contract)
    inbound = Counter()
    details = defaultdict(lambda: {
        "received_count": 0,
        "sent_count": 0,
        "received_amount": 0.0,
        "sent_amount": 0.0,
        "latest": "",
    })

    c = contract.lower()

    for item in transfers:
        if contract_of_transfer(item) != c:
            continue

        src_obj = item.get("from")
        dst_obj = item.get("to")
        src = addr_hash(src_obj)
        dst = addr_hash(dst_obj)
        amount = raw_token_amount(item)
        ts = timestamp_str(item)

        if dst and dst != c and is_eoa(dst_obj):
            inbound[dst] += 1
            d = details[dst]
            d["received_count"] += 1
            d["received_amount"] += amount
            if ts > d["latest"]:
                d["latest"] = ts

        if src and src != c and is_eoa(src_obj):
            d = details[src]
            d["sent_count"] += 1
            d["sent_amount"] += amount
            if ts > d["latest"]:
                d["latest"] = ts

    return inbound, details


def wallet_anchor_stats(wallet: str, anchor_contracts: dict[str, str]) -> dict:
    transfers = address_token_transfers(wallet)

    stats = {
        name: {
            "in_count": 0,
            "out_count": 0,
            "in_amount": 0.0,
            "out_amount": 0.0,
            "latest": "",
            "tx_hashes": [],
        }
        for name in anchor_contracts
    }

    wanted = {v.lower(): k for k, v in anchor_contracts.items()}

    for item in transfers:
        contract = contract_of_transfer(item)
        name = wanted.get(contract)
        if not name:
            continue

        src = addr_hash(item.get("from"))
        dst = addr_hash(item.get("to"))
        amount = raw_token_amount(item)
        ts = timestamp_str(item)
        tx = str(item.get("transaction_hash") or "")

        s = stats[name]

        if dst == wallet.lower():
            s["in_count"] += 1
            s["in_amount"] += amount

        if src == wallet.lower():
            s["out_count"] += 1
            s["out_amount"] += amount

        if ts > s["latest"]:
            s["latest"] = ts

        if tx and tx not in s["tx_hashes"]:
            s["tx_hashes"].append(tx)

    return stats


def score_unipcs(wallet: str, initial: dict, stats: dict) -> tuple[int, list[str]]:
    score = 0
    reasons = []

    jug = stats["JUGGERNAUT"]
    pons = stats["PONS"]

    # Strongest signal: repeated JUGGERNAUT receipts.
    score += min(jug["in_count"], 10) * 20
    if jug["in_count"] >= 3:
        score += 50
        reasons.append(f"{jug['in_count']} JUGGERNAUT receipts")
    if jug["in_count"] >= 5:
        score += 75

    # Cross-token fingerprint is especially valuable.
    if pons["in_count"] > 0 or pons["out_count"] > 0:
        score += 150
        reasons.append("also interacts with PONS")

    if pons["in_count"] >= 2:
        score += 50

    # Give a modest bump to wallets repeatedly appearing in recent contract history.
    rec = initial.get(wallet, {})
    rc = int(rec.get("received_count", 0))
    if rc:
        score += min(rc, 10) * 5

    # Net holding / active campaign hints.
    if jug["in_count"] > jug["out_count"]:
        score += 15

    return score, reasons


def score_dumbcrayon(wallet: str, initial: dict, stats: dict) -> tuple[int, list[str]]:
    score = 0
    reasons = []

    ai = stats["AI"]

    score += min(ai["in_count"], 12) * 20

    if ai["in_count"] >= 2:
        score += 35
        reasons.append(f"{ai['in_count']} AI receipts")
    if ai["in_count"] >= 4:
        score += 60
    if ai["in_count"] >= 8:
        score += 80

    rec = initial.get(wallet, {})
    rc = int(rec.get("received_count", 0))
    if rc:
        score += min(rc, 10) * 5

    if ai["in_count"] > ai["out_count"]:
        score += 15

    return score, reasons


def print_stats(wallet: str, stats: dict):
    for name, s in stats.items():
        print(
            f"     {name:<11} IN {s['in_count']:>2} | OUT {s['out_count']:>2} | "
            f"latest {s['latest'] or '-'}"
        )
    print(f"     explorer: {EXPLORER}/address/{wallet}")


def run_unipcs():
    print()
    print("=" * 88)
    print("UNIPCS - ROBINHOOD CHAIN WALLET DISCOVERY")
    print("=" * 88)
    print(f"JUGGERNAUT: {UNIPCS_JUGGERNAUT}")
    print(f"PONS:       {UNIPCS_PONS}")
    print()

    inbound, initial = initial_candidates(UNIPCS_JUGGERNAUT)
    candidates = [w for w, _ in inbound.most_common(TOP_CANDIDATES_TO_DEEP_CHECK)]

    print(f"Candidate EOAs from JUGGERNAUT transfers: {len(inbound)}")
    print(f"Deep-checking top {len(candidates)}...\n")

    ranked = []

    for i, wallet in enumerate(candidates, 1):
        try:
            stats = wallet_anchor_stats(
                wallet,
                {
                    "JUGGERNAUT": UNIPCS_JUGGERNAUT,
                    "PONS": UNIPCS_PONS,
                },
            )
            score, reasons = score_unipcs(wallet, initial, stats)
            ranked.append((score, wallet, stats, reasons))
            print(f"  checked {i:>2}/{len(candidates)} {wallet[:10]}... score={score}")
        except Exception as e:
            print(f"  error {wallet}: {e}")
        time.sleep(PAGE_DELAY)

    ranked.sort(key=lambda x: x[0], reverse=True)

    print()
    print("-" * 88)
    print("TOP UNIPCS CANDIDATES")
    print("-" * 88)

    for rank, (score, wallet, stats, reasons) in enumerate(ranked[:10], 1):
        print(f"#{rank} score={score}  wallet={wallet}")
        if reasons:
            print("     " + "; ".join(reasons))
        print_stats(wallet, stats)
        print()

    if ranked:
        best = ranked[0]
        if best[2]["PONS"]["in_count"] or best[2]["PONS"]["out_count"]:
            print("BEST SIGNAL: top wallet has both JUGGERNAUT and PONS activity.")
            print("That cross-token match is the one I want to inspect next.")
        else:
            print("No candidate showed the stronger JUGGERNAUT + PONS cross-token fingerprint.")


def run_dumbcrayon():
    print()
    print("=" * 88)
    print("DUMBCRAYONEATER - ROBINHOOD CHAIN WALLET DISCOVERY")
    print("=" * 88)
    print(f"AI: {DUMBCRAYON_AI}")
    print()

    inbound, initial = initial_candidates(DUMBCRAYON_AI)
    candidates = [w for w, _ in inbound.most_common(TOP_CANDIDATES_TO_DEEP_CHECK)]

    print(f"Candidate EOAs from AI transfers: {len(inbound)}")
    print(f"Deep-checking top {len(candidates)}...\n")

    ranked = []

    for i, wallet in enumerate(candidates, 1):
        try:
            stats = wallet_anchor_stats(wallet, {"AI": DUMBCRAYON_AI})
            score, reasons = score_dumbcrayon(wallet, initial, stats)
            ranked.append((score, wallet, stats, reasons))
            print(f"  checked {i:>2}/{len(candidates)} {wallet[:10]}... score={score}")
        except Exception as e:
            print(f"  error {wallet}: {e}")
        time.sleep(PAGE_DELAY)

    ranked.sort(key=lambda x: x[0], reverse=True)

    print()
    print("-" * 88)
    print("TOP DUMBCRAYONEATER CANDIDATES")
    print("-" * 88)

    for rank, (score, wallet, stats, reasons) in enumerate(ranked[:10], 1):
        print(f"#{rank} score={score}  wallet={wallet}")
        if reasons:
            print("     " + "; ".join(reasons))
        print_stats(wallet, stats)
        print()

    print(
        "For DumbCrayonEater, one contract is enough to generate candidates, "
        "but a second known FOMO contract will make identification much stronger."
    )


def main():
    print("=" * 88)
    print("CRYPTOTRACKER - ROBINHOOD CHAIN WHALE WALLET FINDER")
    print("READ ONLY - PUBLIC BLOCKCHAIN DATA - NO PRIVATE KEYS - NO TRADES")
    print("=" * 88)
    print("Robinhood Chain: chain ID 4663")
    print("Explorer/API: Robinhood Chain Blockscout")
    print()
    print("1 = Find Unipcs")
    print("2 = Find DumbCrayonEater")
    print("3 = Run both")
    choice = input("Choose 1, 2, or 3: ").strip()

    try:
        if choice == "1":
            run_unipcs()
        elif choice == "2":
            run_dumbcrayon()
        elif choice == "3":
            run_unipcs()
            run_dumbcrayon()
        else:
            print("Invalid choice.")
    except requests.HTTPError as e:
        print()
        print(f"HTTP ERROR: {e}")
        print(
            "If Blockscout is rate-limiting the public API, wait a minute and "
            "run again. The script is read-only."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
