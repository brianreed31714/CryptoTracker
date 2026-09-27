"""
CryptoTracker - Whale Public Wallet Finder

READ ONLY:
- Uses public Solana/DEX data and your Helius API key.
- Does NOT load any private key.
- Cannot sign or send transactions.

Purpose:
Try to identify the public Solana wallets for:
1) Unipcs
2) DumbCrayonEater

Method:
- Find likely Solana token mints by symbol via DEX Screener.
- Inspect the largest holders for those tokens.
- Pull recent Helius transactions for each holder.
- Rank wallets by how closely their recent buys match the dollar-size
  fingerprints visible in the FOMO screenshots.

This is a candidate finder, not identity proof. Verify the top wallet using
multiple known trades before adding it to traders.json.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
ENV_FILE = PROJECT_ROOT / ".env"
load_dotenv(ENV_FILE)

HELIUS_API_KEY = os.getenv("HELIUS_API_KEY", "").strip()
RPC_URL = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"
HELIUS_TX_URL = "https://api.helius.xyz/v0/addresses/{wallet}/transactions"
DEX_SEARCH_URL = "https://api.dexscreener.com/latest/dex/search"

USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
USDT = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
WSOL = "So11111111111111111111111111111111111111112"

PROFILES = {
    "1": {
        "name": "Unipcs",
        "symbol": "JUGGERNAUT",
        "expected_buys": [22381.41, 19611.72, 19652.84, 19240.00, 21848.87],
    },
    "2": {
        "name": "DumbCrayonEater",
        "symbol": "ICOIN",
        "expected_buys": [2498.63, 2498.54, 2499.70, 2498.21, 4997.23],
    },
}

AMOUNT_TOLERANCE_PCT = 4.0
TX_LIMIT = 100
MAX_TOKEN_CANDIDATES = 5
MAX_HOLDERS_PER_TOKEN = 20


def sf(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def rpc(method: str, params: list):
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    r = requests.post(RPC_URL, json=payload, timeout=25)
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise RuntimeError(data["error"])
    return data.get("result")


def dex_candidates(symbol: str) -> list[dict]:
    r = requests.get(DEX_SEARCH_URL, params={"q": symbol}, timeout=20)
    r.raise_for_status()
    pairs = r.json().get("pairs") or []

    found = {}
    for p in pairs:
        if p.get("chainId") != "solana":
            continue

        base = p.get("baseToken") or {}
        quote = p.get("quoteToken") or {}

        token = None
        if str(base.get("symbol", "")).upper() == symbol.upper():
            token = base
        elif str(quote.get("symbol", "")).upper() == symbol.upper():
            token = quote

        if not token:
            continue

        mint = token.get("address", "")
        if not mint:
            continue

        row = {
            "mint": mint,
            "symbol": token.get("symbol", ""),
            "name": token.get("name", ""),
            "liquidity": sf((p.get("liquidity") or {}).get("usd")),
            "volume24h": sf((p.get("volume") or {}).get("h24")),
        }

        old = found.get(mint)
        if not old or row["liquidity"] > old["liquidity"]:
            found[mint] = row

    rows = list(found.values())
    rows.sort(key=lambda x: (x["liquidity"], x["volume24h"]), reverse=True)
    return rows[:MAX_TOKEN_CANDIDATES]


def largest_token_accounts(mint: str) -> list[str]:
    result = rpc(
        "getTokenLargestAccounts",
        [mint, {"commitment": "confirmed"}],
    )
    return [
        x.get("address")
        for x in (result or {}).get("value", [])
        if x.get("address")
    ][:MAX_HOLDERS_PER_TOKEN]


def token_account_owner(token_account: str) -> str:
    result = rpc(
        "getAccountInfo",
        [
            token_account,
            {"encoding": "jsonParsed", "commitment": "confirmed"},
        ],
    )
    try:
        return result["value"]["data"]["parsed"]["info"]["owner"]
    except Exception:
        return ""


def helius_transactions(wallet: str) -> list[dict]:
    r = requests.get(
        HELIUS_TX_URL.format(wallet=wallet),
        params={"api-key": HELIUS_API_KEY, "limit": TX_LIMIT},
        timeout=25,
    )
    r.raise_for_status()
    data = r.json()
    return data if isinstance(data, list) else []


def transfer_side(t: dict, wallet: str) -> str:
    src = t.get("fromUserAccount") or ""
    dst = t.get("toUserAccount") or ""
    if dst == wallet and src != wallet:
        return "IN"
    if src == wallet and dst != wallet:
        return "OUT"
    return "OTHER"


def target_buy(tx: dict, wallet: str, target_mint: str):
    if str(tx.get("type", "")).upper() != "SWAP":
        return None

    target_in = 0.0
    stable_out = 0.0

    for t in tx.get("tokenTransfers") or []:
        mint = t.get("mint", "")
        amount = sf(t.get("tokenAmount"))
        side = transfer_side(t, wallet)

        if side == "IN" and mint == target_mint:
            target_in += amount

        if side == "OUT" and mint in (USDC, USDT):
            stable_out += amount

    if target_in <= 0:
        return None

    return {
        "signature": tx.get("signature", ""),
        "timestamp": int(tx.get("timestamp") or 0),
        "stable_spend": stable_out,
    }


def amount_match(observed: float, expected: float) -> bool:
    if observed <= 0 or expected <= 0:
        return False
    return abs(observed - expected) / expected * 100.0 <= AMOUNT_TOLERANCE_PCT


def score_wallet(wallet: str, mint: str, expected: list[float]) -> dict:
    swaps = []
    for tx in helius_transactions(wallet):
        buy = target_buy(tx, wallet, mint)
        if buy:
            swaps.append(buy)

    used_expected = set()
    matches = []

    for swap in swaps:
        observed = swap["stable_spend"]
        if observed <= 0:
            continue

        for i, exp in enumerate(expected):
            if i in used_expected:
                continue
            if amount_match(observed, exp):
                used_expected.add(i)
                matches.append(
                    {
                        "observed": observed,
                        "expected": exp,
                        "signature": swap["signature"],
                    }
                )
                break

    match_count = len(matches)
    score = match_count * 100 + min(len(swaps), 10) * 5

    if match_count >= 2:
        score += 50
    if match_count >= 3:
        score += 100

    return {
        "wallet": wallet,
        "score": score,
        "matches": matches,
        "match_count": match_count,
        "target_buys": len(swaps),
    }


def short(s: str) -> str:
    if len(s) < 18:
        return s
    return f"{s[:8]}...{s[-8:]}"


def run_profile(profile: dict):
    name = profile["name"]
    symbol = profile["symbol"]
    expected = profile["expected_buys"]

    print()
    print("=" * 78)
    print(f"FINDING PUBLIC SOLANA WALLET: {name}")
    print("READ ONLY - NO PRIVATE KEY - NO TRADES")
    print("=" * 78)
    print(f"Token fingerprint: {symbol}")
    print("Expected buy sizes:")
    for x in expected:
        print(f"  ${x:,.2f}")
    print()

    tokens = dex_candidates(symbol)

    if not tokens:
        print(f"No exact Solana {symbol} token found on DEX Screener.")
        print("Possibilities: different chain, symbol changed, or token no longer indexed.")
        return

    print("Possible token mints:")
    for i, token in enumerate(tokens, 1):
        print(
            f"  {i}. {token['name']} | {token['mint']} | "
            f"liq ${token['liquidity']:,.0f} | vol24h ${token['volume24h']:,.0f}"
        )

    results = []
    seen = set()

    for token in tokens:
        mint = token["mint"]
        print()
        print(f"Scanning top holders of {symbol} mint {short(mint)} ...")

        try:
            token_accounts = largest_token_accounts(mint)
        except Exception as e:
            print(f"  RPC error: {e}")
            continue

        owners = []
        for acct in token_accounts:
            try:
                owner = token_account_owner(acct)
                if owner and owner not in owners:
                    owners.append(owner)
            except Exception:
                pass

        print(f"  {len(owners)} unique owner wallets found.")

        for i, wallet in enumerate(owners, 1):
            key = (mint, wallet)
            if key in seen:
                continue
            seen.add(key)

            try:
                result = score_wallet(wallet, mint, expected)
                result["mint"] = mint
                result["token_name"] = token["name"]
                results.append(result)

                if result["match_count"]:
                    print(
                        f"  MATCH: {wallet} | score {result['score']} | "
                        f"{result['match_count']} size matches"
                    )
                else:
                    print(
                        f"  checked {i:>2}/{len(owners)} {short(wallet)}",
                        end="\r",
                    )

            except Exception as e:
                print(f"\n  Error checking {short(wallet)}: {e}")

            time.sleep(0.08)

    print("\n")
    results.sort(
        key=lambda x: (x["score"], x["match_count"], x["target_buys"]),
        reverse=True,
    )

    print("=" * 78)
    print(f"TOP {name.upper()} CANDIDATES")
    print("=" * 78)

    for rank, r in enumerate(results[:10], 1):
        print(
            f"#{rank} score={r['score']} "
            f"matches={r['match_count']} token_buys={r['target_buys']}"
        )
        print(f"   wallet: {r['wallet']}")
        print(f"   mint:   {r['mint']}")
        for m in r["matches"]:
            print(
                f"   matched ${m['observed']:,.2f} "
                f"(expected ${m['expected']:,.2f})"
            )
            print(f"   tx: {m['signature']}")
        print()

    if not results:
        print("No candidates evaluated.")
        return

    best = results[0]
    if best["match_count"] >= 3:
        print("RESULT: VERY STRONG candidate. Send me this output before we add it.")
    elif best["match_count"] == 2:
        print("RESULT: PROMISING candidate. We should verify one more known trade.")
    elif best["match_count"] == 1:
        print("RESULT: WEAK candidate. Do not add it yet.")
    else:
        print("RESULT: No convincing wallet match among the top holders.")
        print("It may use a smart/custodial wallet or the trade may be on another chain.")


def main():
    if not HELIUS_API_KEY:
        print(f"ERROR: HELIUS_API_KEY missing from {ENV_FILE}")
        sys.exit(1)

    print("=" * 78)
    print("CRYPTOTRACKER - WHALE PUBLIC WALLET FINDER")
    print("=" * 78)
    print("1 = Unipcs")
    print("2 = DumbCrayonEater")
    print("3 = Run both")
    choice = input("Choose 1, 2, or 3: ").strip()

    if choice == "1":
        run_profile(PROFILES["1"])
    elif choice == "2":
        run_profile(PROFILES["2"])
    elif choice == "3":
        run_profile(PROFILES["1"])
        run_profile(PROFILES["2"])
    else:
        print("Invalid selection.")


if __name__ == "__main__":
    main()
