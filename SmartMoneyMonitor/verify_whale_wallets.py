"""
CryptoTracker - Verify Whale Wallets

READ ONLY:
- Uses public Solana/DEX data and your Helius API key.
- Does NOT load any private key.
- Cannot sign or send transactions.

Purpose:
Verify two candidate public Solana wallets against the trade fingerprints
visible in the FOMO screenshots:

1) Unipcs
2) DumbCrayonEater

Recommended location:
C:\\Users\\brian\\OneDrive\\Desktop\\Docs\\CryptoTracker\\SmartMoneyMonitor\\verify_whale_wallets.py

Run:
    python verify_whale_wallets.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)

HELIUS_API_KEY = os.getenv("HELIUS_API_KEY", "").strip()

HELIUS_TX_URL = "https://api.helius.xyz/v0/addresses/{wallet}/transactions"
DEX_SEARCH_URL = "https://api.dexscreener.com/latest/dex/search"

USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
USDT = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"

TX_LIMIT = 100

WHALES = [
    {
        "name": "Unipcs",
        "handle": "unipcs",
        "wallet": "2heJbC32Tpfcb3nbUb5ER61K11FGZVfVGtVnDm6LDogF",
        "symbol": "JUGGERNAUT",
        "expected_buys": [22381.41, 19611.72, 19652.84, 19240.00, 21848.87],
    },
    {
        "name": "DumbCrayonEater",
        "handle": "DumbCrayonEater",
        "wallet": "5FGoPPj1nL8LCnfVnpTmreqQtqLuMXXAwuS1uahMrp8V",
        "symbol": "ICOIN",
        "expected_buys": [2498.63, 2498.54, 2499.70, 2498.21, 4997.23],
    },
]

AMOUNT_TOLERANCE_PCT = 5.0


def sf(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def helius_transactions(wallet: str) -> list[dict]:
    r = requests.get(
        HELIUS_TX_URL.format(wallet=wallet),
        params={"api-key": HELIUS_API_KEY, "limit": TX_LIMIT},
        timeout=25,
    )
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected Helius response: {data}")
    return data


def dex_mints_for_symbol(symbol: str) -> list[dict]:
    r = requests.get(
        DEX_SEARCH_URL,
        params={"q": symbol},
        timeout=20,
    )
    r.raise_for_status()

    pairs = r.json().get("pairs") or []
    by_mint = {}

    for p in pairs:
        if p.get("chainId") != "solana":
            continue

        for token_side in ("baseToken", "quoteToken"):
            token = p.get(token_side) or {}
            if str(token.get("symbol", "")).upper() != symbol.upper():
                continue

            mint = token.get("address", "")
            if not mint:
                continue

            liq = sf((p.get("liquidity") or {}).get("usd"))

            row = {
                "mint": mint,
                "symbol": token.get("symbol", ""),
                "name": token.get("name", ""),
                "liquidity_usd": liq,
                "volume_24h_usd": sf((p.get("volume") or {}).get("h24")),
            }

            existing = by_mint.get(mint)
            if not existing or row["liquidity_usd"] > existing["liquidity_usd"]:
                by_mint[mint] = row

    rows = list(by_mint.values())
    rows.sort(
        key=lambda x: (x["liquidity_usd"], x["volume_24h_usd"]),
        reverse=True,
    )
    return rows[:10]


def direction(transfer: dict, wallet: str) -> str:
    src = transfer.get("fromUserAccount") or ""
    dst = transfer.get("toUserAccount") or ""

    if dst == wallet and src != wallet:
        return "IN"
    if src == wallet and dst != wallet:
        return "OUT"
    return "OTHER"


def analyze_tx(tx: dict, wallet: str, candidate_mints: set[str]):
    if str(tx.get("type", "")).upper() != "SWAP":
        return None

    token_in = {}
    stable_out = 0.0

    for transfer in tx.get("tokenTransfers") or []:
        mint = transfer.get("mint", "")
        amount = sf(transfer.get("tokenAmount"))
        side = direction(transfer, wallet)

        if side == "IN" and mint in candidate_mints and amount > 0:
            token_in[mint] = token_in.get(mint, 0.0) + amount

        if side == "OUT" and mint in (USDC, USDT) and amount > 0:
            stable_out += amount

    if not token_in:
        return None

    target_mint = max(token_in, key=token_in.get)

    return {
        "signature": tx.get("signature", ""),
        "target_mint": target_mint,
        "stable_spend_usd": stable_out,
    }


def closest_expected(observed: float, expected: list[float]) -> tuple[float, float]:
    closest = min(expected, key=lambda x: abs(observed - x))
    pct_diff = abs(observed - closest) / closest * 100.0 if closest else 999999.0
    return closest, pct_diff


def verify(whale: dict) -> None:
    name = whale["name"]
    wallet = whale["wallet"]
    symbol = whale["symbol"]
    expected = whale["expected_buys"]

    print()
    print("=" * 82)
    print(f"{name.upper()} WALLET VERIFICATION")
    print("=" * 82)
    print(f"Wallet: {wallet}")
    print(f"Fingerprint token: {symbol}")
    print("Expected buys:")
    for x in expected:
        print(f"  ${x:,.2f}")
    print()

    mints = dex_mints_for_symbol(symbol)
    if not mints:
        print(f"No Solana {symbol} mint found through DEX Screener.")
        return

    print("Candidate token mints:")
    for i, item in enumerate(mints, 1):
        print(
            f"  {i}. {item['name']} | {item['mint']} | "
            f"liq ${item['liquidity_usd']:,.0f}"
        )

    candidate_mints = {x["mint"] for x in mints}
    txs = helius_transactions(wallet)

    print()
    print(f"Helius transactions fetched: {len(txs)}")

    observed_buys = []
    for tx in txs:
        result = analyze_tx(tx, wallet, candidate_mints)
        if result:
            observed_buys.append(result)

    print(f"{symbol} buys found in recent history: {len(observed_buys)}")
    print()

    if not observed_buys:
        print("VERDICT: NOT VERIFIED")
        print("No matching token buys found in recent Helius history.")
        return

    matched_expected = set()
    strong_matches = []

    print("Observed buys:")
    for buy in observed_buys:
        spend = buy["stable_spend_usd"]
        closest, diff_pct = closest_expected(spend, expected)

        label = ""
        if spend > 0:
            possibilities = [
                (i, x)
                for i, x in enumerate(expected)
                if i not in matched_expected
            ]
            if possibilities:
                i, exp = min(possibilities, key=lambda pair: abs(spend - pair[1]))
                exp_diff = abs(spend - exp) / exp * 100.0
                if exp_diff <= AMOUNT_TOLERANCE_PCT:
                    matched_expected.add(i)
                    strong_matches.append((spend, exp, buy["signature"]))
                    label = "  <-- FOMO SIZE MATCH"

        print(
            f"  spend ${spend:,.2f} | "
            f"closest screenshot ${closest:,.2f} | "
            f"diff {diff_pct:.2f}%{label}"
        )
        print(f"    mint: {buy['target_mint']}")
        print(f"    tx:   {buy['signature']}")

    print()
    print("-" * 82)
    print(f"Matched screenshot-size buys: {len(strong_matches)} / {len(expected)}")

    if len(strong_matches) >= 3:
        print("VERDICT: VERY STRONG MATCH")
    elif len(strong_matches) == 2:
        print("VERDICT: PROMISING MATCH")
    elif len(strong_matches) == 1:
        print("VERDICT: WEAK MATCH")
    else:
        print("VERDICT: NOT VERIFIED")


def main() -> None:
    if not HELIUS_API_KEY:
        print(f"ERROR: HELIUS_API_KEY missing from {ENV_FILE}")
        sys.exit(1)

    print("=" * 82)
    print("CRYPTOTRACKER - VERIFY WHALE PUBLIC WALLETS")
    print("READ ONLY - NO PRIVATE KEY - NO TRADES")
    print("=" * 82)

    for whale in WHALES:
        try:
            verify(whale)
        except requests.HTTPError as exc:
            print(f"\nHTTP ERROR verifying {whale['name']}: {exc}")
        except Exception as exc:
            print(f"\nERROR verifying {whale['name']}: {exc}")

    print()
    print("=" * 82)
    print("DONE")
    print("Send me the two VERDICT sections plus any FOMO SIZE MATCH lines.")
    print("=" * 82)


if __name__ == "__main__":
    main()
