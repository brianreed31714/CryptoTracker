"""
CryptoTracker Smart Money Monitor - v1
Observation-only. It NEVER places trades.

What it does:
- Loads Helius API key from the parent CryptoTracker .env
- Loads tracked wallets from SmartMoneyMonitor/traders.json
- Polls Helius Enhanced Transactions for new wallet activity
- Detects likely token buys/swaps
- Records each new smart-money buy
- Samples DEX Screener price at +1, +3, +5, +15, +30 minutes
- Writes CSV data for later analysis

Recommended location:
C:\\Users\\brian\\OneDrive\\Desktop\\Docs\\CryptoTracker\\SmartMoneyMonitor\\smart_money_monitor.py

Expected parent .env:
C:\\Users\\brian\\OneDrive\\Desktop\\Docs\\CryptoTracker\\.env
"""

from __future__ import annotations

import csv
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import requests
from dotenv import load_dotenv


# ---------------------------------------------------------------------------
# Paths / configuration
# ---------------------------------------------------------------------------

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
ENV_PATH = PROJECT_ROOT / ".env"
TRADERS_PATH = HERE / "traders.json"
DATA_DIR = HERE / "data"
STATE_PATH = DATA_DIR / "state.json"
EVENTS_CSV = DATA_DIR / "smart_money_events.csv"
PERFORMANCE_CSV = DATA_DIR / "trader_performance.csv"

DATA_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(ENV_PATH)

HELIUS_API_KEY = os.getenv("HELIUS_API_KEY", "").strip()

# Polling is independent from the main CryptoTracker 60-second scan.
POLL_SECONDS = int(os.getenv("SMART_MONEY_POLL_SECONDS", "15"))

# Number of recent Helius transactions fetched per trader each cycle.
HELIUS_LIMIT = int(os.getenv("SMART_MONEY_HELIUS_LIMIT", "20"))

# Ignore tiny likely-probe buys in the main performance study.
# They are still printed, but below this threshold are tagged "TINY".
MIN_MEANINGFUL_USD = float(os.getenv("SMART_MONEY_MIN_MEANINGFUL_USD", "50"))

# Sample horizons after a buy.
SAMPLE_MINUTES = [1, 3, 5, 15, 30]

HELIUS_TX_URL = "https://api.helius.xyz/v0/addresses/{wallet}/transactions"

DEX_TOKEN_PAIRS_URL = (
    "https://api.dexscreener.com/token-pairs/v1/solana/{mint}"
)

USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
USDT_MINT = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
WSOL_MINT = "So11111111111111111111111111111111111111112"

QUOTE_MINTS = {USDC_MINT, USDT_MINT, WSOL_MINT}


# ---------------------------------------------------------------------------
# Models / helpers
# ---------------------------------------------------------------------------

@dataclass
class Trader:
    name: str
    handle: str
    wallet: str
    enabled: bool = True


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc(ts: Optional[int] = None) -> str:
    if ts is None:
        dt = utc_now()
    else:
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return dt.isoformat()


def short(addr: str, n: int = 6) -> str:
    if not addr:
        return ""
    if len(addr) <= n * 2 + 3:
        return addr
    return f"{addr[:n]}...{addr[-n:]}"


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def load_traders() -> list[Trader]:
    if not TRADERS_PATH.exists():
        raise FileNotFoundError(
            f"Missing {TRADERS_PATH}. Put traders.json beside this script."
        )

    raw = json.loads(TRADERS_PATH.read_text(encoding="utf-8"))
    traders = []

    for item in raw.get("traders", []):
        if not item.get("enabled", True):
            continue

        traders.append(
            Trader(
                name=item["name"],
                handle=item.get("handle", ""),
                wallet=item["wallet"],
                enabled=True,
            )
        )

    if not traders:
        raise RuntimeError("No enabled traders found in traders.json")

    return traders


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {
            "initialized": {},
            "seen_signatures": [],
            "events": {},
        }

    try:
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        state = {}

    state.setdefault("initialized", {})
    state.setdefault("seen_signatures", [])
    state.setdefault("events", {})
    return state


def save_state(state: dict) -> None:
    # Keep the seen set bounded so state.json does not grow forever.
    state["seen_signatures"] = state.get("seen_signatures", [])[-5000:]

    temp = STATE_PATH.with_suffix(".tmp")
    temp.write_text(
        json.dumps(state, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    temp.replace(STATE_PATH)


def append_csv(path: Path, row: dict, fieldnames: list[str]) -> None:
    exists = path.exists()

    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerow(row)


EVENT_FIELDS = [
    "detected_at_utc",
    "trade_time_utc",
    "trader_name",
    "trader_handle",
    "wallet",
    "signature",
    "tx_type",
    "token_mint",
    "token_symbol",
    "token_name",
    "token_amount_received",
    "estimated_spend_usd",
    "spend_asset",
    "spend_amount",
    "entry_price_usd",
    "liquidity_usd",
    "market_cap_usd",
    "volume_5m_usd",
    "price_change_5m_pct",
    "buy_size_class",
]

PERFORMANCE_FIELDS = [
    "sampled_at_utc",
    "trader_name",
    "trader_handle",
    "signature",
    "token_mint",
    "token_symbol",
    "trade_time_utc",
    "horizon_minutes",
    "entry_price_usd",
    "sample_price_usd",
    "return_pct",
    "liquidity_usd",
    "market_cap_usd",
    "volume_5m_usd",
    "price_change_5m_pct",
]


# ---------------------------------------------------------------------------
# Helius
# ---------------------------------------------------------------------------

def helius_recent_transactions(wallet: str) -> list[dict]:
    url = HELIUS_TX_URL.format(wallet=wallet)

    response = requests.get(
        url,
        params={
            "api-key": HELIUS_API_KEY,
            "limit": HELIUS_LIMIT,
        },
        timeout=20,
    )
    response.raise_for_status()

    data = response.json()
    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected Helius response: {data}")

    return data


def token_transfer_direction(
    transfer: dict,
    wallet: str,
) -> tuple[str, float, str]:
    """
    Returns: direction, amount, mint
    direction is IN / OUT / OTHER.

    Helius Enhanced Transaction transfer objects normally expose
    fromUserAccount/toUserAccount and tokenAmount.
    """
    mint = transfer.get("mint", "")
    amount = safe_float(transfer.get("tokenAmount"))

    from_user = transfer.get("fromUserAccount") or ""
    to_user = transfer.get("toUserAccount") or ""

    if to_user == wallet and from_user != wallet:
        return "IN", amount, mint

    if from_user == wallet and to_user != wallet:
        return "OUT", amount, mint

    return "OTHER", amount, mint


def extract_buy(tx: dict, trader: Trader) -> Optional[dict]:
    """
    Heuristic smart-money buy detector.

    We only consider transactions classified by Helius as SWAP.
    A buy must have a non-quote token flowing into the tracked wallet.

    This is observation logic, not trade-execution logic.
    """
    tx_type = str(tx.get("type", "")).upper()
    if tx_type != "SWAP":
        return None

    transfers = tx.get("tokenTransfers") or []
    incoming = []
    outgoing = []

    for transfer in transfers:
        direction, amount, mint = token_transfer_direction(
            transfer,
            trader.wallet,
        )

        if not mint or amount <= 0:
            continue

        record = {
            "mint": mint,
            "amount": amount,
        }

        if direction == "IN":
            incoming.append(record)
        elif direction == "OUT":
            outgoing.append(record)

    # Candidate bought assets: token flowed into wallet and is not a common quote.
    bought = [
        t for t in incoming
        if t["mint"] not in QUOTE_MINTS
    ]

    if not bought:
        return None

    # Usually a swap has one bought asset. If there are several, choose the
    # largest token amount and preserve observation-only semantics.
    bought.sort(key=lambda x: x["amount"], reverse=True)
    bought_token = bought[0]

    spend_asset = ""
    spend_amount = 0.0
    estimated_spend_usd = 0.0

    # Prefer stablecoin outflow because it gives us direct USD sizing.
    for mint in (USDC_MINT, USDT_MINT):
        stable_out = sum(
            t["amount"] for t in outgoing
            if t["mint"] == mint
        )
        if stable_out > 0:
            spend_asset = "USDC" if mint == USDC_MINT else "USDT"
            spend_amount = stable_out
            estimated_spend_usd = stable_out
            break

    # If the swap spent WSOL, capture the SOL amount. USD estimate is filled
    # later using DEX Screener's SOL price.
    if spend_amount == 0:
        sol_out = sum(
            t["amount"] for t in outgoing
            if t["mint"] == WSOL_MINT
        )
        if sol_out > 0:
            spend_asset = "SOL"
            spend_amount = sol_out

    return {
        "token_mint": bought_token["mint"],
        "token_amount_received": bought_token["amount"],
        "spend_asset": spend_asset,
        "spend_amount": spend_amount,
        "estimated_spend_usd": estimated_spend_usd,
    }


# ---------------------------------------------------------------------------
# DEX Screener
# ---------------------------------------------------------------------------

_market_cache: dict[str, tuple[float, Optional[dict]]] = {}


def dex_market(mint: str, cache_seconds: int = 5) -> Optional[dict]:
    now = time.time()

    cached = _market_cache.get(mint)
    if cached and now - cached[0] <= cache_seconds:
        return cached[1]

    url = DEX_TOKEN_PAIRS_URL.format(mint=mint)

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        pairs = response.json()

        if not isinstance(pairs, list) or not pairs:
            _market_cache[mint] = (now, None)
            return None

        # Prefer highest-liquidity Solana pair for a more robust price.
        pairs = [
            p for p in pairs
            if p.get("chainId") == "solana"
        ]

        if not pairs:
            _market_cache[mint] = (now, None)
            return None

        pair = max(
            pairs,
            key=lambda p: safe_float(
                (p.get("liquidity") or {}).get("usd")
            ),
        )

        base = pair.get("baseToken") or {}
        quote = pair.get("quoteToken") or {}

        result = {
            "price_usd": safe_float(pair.get("priceUsd")),
            "liquidity_usd": safe_float(
                (pair.get("liquidity") or {}).get("usd")
            ),
            "market_cap_usd": safe_float(
                pair.get("marketCap") or pair.get("fdv")
            ),
            "volume_5m_usd": safe_float(
                (pair.get("volume") or {}).get("m5")
            ),
            "price_change_5m_pct": safe_float(
                (pair.get("priceChange") or {}).get("m5")
            ),
            "symbol": (
                base.get("symbol")
                if base.get("address") == mint
                else quote.get("symbol", "")
            ),
            "name": (
                base.get("name")
                if base.get("address") == mint
                else quote.get("name", "")
            ),
            "pair_address": pair.get("pairAddress", ""),
        }

        _market_cache[mint] = (now, result)
        return result

    except Exception:
        _market_cache[mint] = (now, None)
        return None


def sol_price_usd() -> float:
    market = dex_market(WSOL_MINT)
    if not market:
        return 0.0
    return safe_float(market.get("price_usd"))


# ---------------------------------------------------------------------------
# Event handling / performance sampling
# ---------------------------------------------------------------------------

def buy_size_class(usd: float) -> str:
    if usd <= 0:
        return "UNKNOWN"
    if usd < 50:
        return "TINY"
    if usd < 500:
        return "WEAK"
    if usd < 2000:
        return "MEANINGFUL"
    if usd < 5000:
        return "STRONG"
    return "VERY_STRONG"


def record_buy(
    trader: Trader,
    tx: dict,
    buy: dict,
    state: dict,
) -> None:
    signature = tx.get("signature", "")
    timestamp = int(tx.get("timestamp") or time.time())
    mint = buy["token_mint"]

    market = dex_market(mint) or {}

    estimated_spend_usd = buy["estimated_spend_usd"]

    if (
        estimated_spend_usd <= 0
        and buy["spend_asset"] == "SOL"
        and buy["spend_amount"] > 0
    ):
        estimated_spend_usd = (
            buy["spend_amount"] * sol_price_usd()
        )

    entry_price = safe_float(market.get("price_usd"))

    symbol = market.get("symbol") or short(mint, 4)
    name = market.get("name") or ""
    size_class = buy_size_class(estimated_spend_usd)

    row = {
        "detected_at_utc": iso_utc(),
        "trade_time_utc": iso_utc(timestamp),
        "trader_name": trader.name,
        "trader_handle": trader.handle,
        "wallet": trader.wallet,
        "signature": signature,
        "tx_type": tx.get("type", ""),
        "token_mint": mint,
        "token_symbol": symbol,
        "token_name": name,
        "token_amount_received": buy["token_amount_received"],
        "estimated_spend_usd": round(estimated_spend_usd, 6),
        "spend_asset": buy["spend_asset"],
        "spend_amount": buy["spend_amount"],
        "entry_price_usd": entry_price,
        "liquidity_usd": safe_float(market.get("liquidity_usd")),
        "market_cap_usd": safe_float(market.get("market_cap_usd")),
        "volume_5m_usd": safe_float(market.get("volume_5m_usd")),
        "price_change_5m_pct": safe_float(
            market.get("price_change_5m_pct")
        ),
        "buy_size_class": size_class,
    }

    append_csv(EVENTS_CSV, row, EVENT_FIELDS)

    state["events"][signature] = {
        "trader_name": trader.name,
        "trader_handle": trader.handle,
        "signature": signature,
        "token_mint": mint,
        "token_symbol": symbol,
        "trade_timestamp": timestamp,
        "trade_time_utc": iso_utc(timestamp),
        "entry_price_usd": entry_price,
        "estimated_spend_usd": estimated_spend_usd,
        "sampled_minutes": [],
    }

    dollars = (
        f"${estimated_spend_usd:,.2f}"
        if estimated_spend_usd > 0
        else f"{buy['spend_amount']:.4f} {buy['spend_asset'] or 'unknown'}"
    )

    print()
    print("SMART MONEY BUY DETECTED")
    print(f"  Trader      : {trader.name} (@{trader.handle})")
    print(f"  Token       : {symbol} ({short(mint)})")
    print(f"  Spend       : {dollars} [{size_class}]")
    print(f"  Token amount: {buy['token_amount_received']:,.6f}")
    print(
        f"  Price       : ${entry_price:.10f}"
        if entry_price > 0
        else "  Price       : unavailable"
    )
    print(
        f"  Liquidity   : ${safe_float(market.get('liquidity_usd')):,.0f}"
    )
    print(
        f"  5m move     : {safe_float(market.get('price_change_5m_pct')):+.1f}%"
    )
    print(f"  Signature   : {signature}")
    print("  MODE        : OBSERVATION ONLY - NO TRADE")


def sample_due_events(state: dict) -> None:
    now_ts = int(time.time())
    changed = False

    for signature, event in list(state["events"].items()):
        trade_ts = int(event["trade_timestamp"])
        age_seconds = now_ts - trade_ts
        sampled = set(event.get("sampled_minutes", []))

        for minute in SAMPLE_MINUTES:
            if minute in sampled:
                continue

            if age_seconds < minute * 60:
                continue

            market = dex_market(event["token_mint"])
            if not market:
                continue

            sample_price = safe_float(market.get("price_usd"))
            entry_price = safe_float(event.get("entry_price_usd"))

            if sample_price <= 0 or entry_price <= 0:
                continue

            return_pct = (
                (sample_price / entry_price) - 1.0
            ) * 100.0

            row = {
                "sampled_at_utc": iso_utc(),
                "trader_name": event["trader_name"],
                "trader_handle": event["trader_handle"],
                "signature": signature,
                "token_mint": event["token_mint"],
                "token_symbol": event["token_symbol"],
                "trade_time_utc": event["trade_time_utc"],
                "horizon_minutes": minute,
                "entry_price_usd": entry_price,
                "sample_price_usd": sample_price,
                "return_pct": round(return_pct, 6),
                "liquidity_usd": safe_float(
                    market.get("liquidity_usd")
                ),
                "market_cap_usd": safe_float(
                    market.get("market_cap_usd")
                ),
                "volume_5m_usd": safe_float(
                    market.get("volume_5m_usd")
                ),
                "price_change_5m_pct": safe_float(
                    market.get("price_change_5m_pct")
                ),
            }

            append_csv(
                PERFORMANCE_CSV,
                row,
                PERFORMANCE_FIELDS,
            )

            sampled.add(minute)
            event["sampled_minutes"] = sorted(sampled)
            changed = True

            print(
                f"  PERFORMANCE: {event['trader_name']} "
                f"{event['token_symbol']} +{minute}m "
                f"{return_pct:+.2f}%"
            )

        # Once all sample horizons are complete and the event is old enough,
        # keep the record in state for restart visibility. It is tiny and useful.

    if changed:
        save_state(state)


def bootstrap_or_process_trader(
    trader: Trader,
    state: dict,
) -> int:
    """
    First run behavior is intentionally safe:
    - Fetch recent transactions
    - Mark them seen
    - Do NOT pretend old transactions were just detected

    Subsequent cycles process only genuinely new transactions.
    """
    txs = helius_recent_transactions(trader.wallet)

    if not txs:
        return 0

    seen = set(state["seen_signatures"])
    wallet_initialized = state["initialized"].get(
        trader.wallet,
        False,
    )

    if not wallet_initialized:
        for tx in txs:
            sig = tx.get("signature")
            if sig and sig not in seen:
                state["seen_signatures"].append(sig)
                seen.add(sig)

        state["initialized"][trader.wallet] = True
        save_state(state)

        print(
            f"  Initialized {trader.name}: "
            f"{len(txs)} recent transactions marked as baseline."
        )
        print(
            "  New transactions after this point will be observed."
        )
        return 0

    new_txs = [
        tx for tx in txs
        if tx.get("signature")
        and tx.get("signature") not in seen
    ]

    # Helius returns newest first; process oldest -> newest.
    new_txs.sort(key=lambda x: int(x.get("timestamp") or 0))

    detected = 0

    for tx in new_txs:
        sig = tx.get("signature")
        if not sig:
            continue

        buy = extract_buy(tx, trader)

        if buy:
            record_buy(trader, tx, buy, state)
            detected += 1

        state["seen_signatures"].append(sig)
        seen.add(sig)

    if new_txs:
        save_state(state)

    return detected


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if not HELIUS_API_KEY:
        raise RuntimeError(
            f"HELIUS_API_KEY is missing. Add it to {ENV_PATH}"
        )

    traders = load_traders()
    state = load_state()

    print("=" * 72)
    print("CryptoTracker Smart Money Monitor v1")
    print("OBSERVATION ONLY - THIS SCRIPT CANNOT PLACE TRADES")
    print("=" * 72)
    print(f"Project root : {PROJECT_ROOT}")
    print(f"Helius       : configured")
    print(f"Poll interval: {POLL_SECONDS} seconds")
    print(f"Tracked      : {len(traders)} trader(s)")
    print(
        "Samples      : "
        + ", ".join(f"+{m}m" for m in SAMPLE_MINUTES)
    )
    print()

    for trader in traders:
        print(
            f"  {trader.name:<24} "
            f"@{trader.handle:<18} {short(trader.wallet)}"
        )

    print()
    print("Press Ctrl+C to stop.")
    print()

    while True:
        cycle_started = time.time()

        try:
            for trader in traders:
                try:
                    bootstrap_or_process_trader(
                        trader,
                        state,
                    )
                except requests.HTTPError as exc:
                    print(
                        f"[{datetime.now().strftime('%H:%M:%S')}] "
                        f"Helius HTTP error for {trader.name}: {exc}"
                    )
                except Exception as exc:
                    print(
                        f"[{datetime.now().strftime('%H:%M:%S')}] "
                        f"Trader error for {trader.name}: {exc}"
                    )

            sample_due_events(state)

        except KeyboardInterrupt:
            print("\nStopped.")
            break
        except Exception as exc:
            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] "
                f"Cycle error: {exc}"
            )

        elapsed = time.time() - cycle_started
        sleep_for = max(1.0, POLL_SECONDS - elapsed)

        try:
            time.sleep(sleep_for)
        except KeyboardInterrupt:
            print("\nStopped.")
            break


if __name__ == "__main__":
    main()
