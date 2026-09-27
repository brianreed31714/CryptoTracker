"""
CryptoTracker Smart Money Monitor - v2.2.1 CAMPAIGN STRENGTH
OBSERVATION ONLY. This script NEVER places trades.

What's new in v2:
- Groups repeated buys by the same trader/token into a "campaign"
- Separates meaningful capital from micro-transactions
- Flags LARGE_THEN_MICRO behavior instead of counting every tiny buy as bullish
- Tracks initial buy, first meaningful buy, largest buy, cumulative spend,
  micro-buy count, and campaign buy number
- Records richer DEX metrics: 5m/1h price, 5m/1h volume, 5m buys/sells,
  buy/sell ratio, liquidity and market cap
- Samples +1/+3/+5/+15/+30/+60 minute performance using exact-mint/base-token pricing
- Scores sustained accumulation campaigns and cross-wallet convergence
- Writes a per-wallet forward-performance scorecard
- Keeps Solana/Helius monitoring from v2
- Adds Robinhood Chain direct-RPC monitoring for EVM wallets
- Adds chain + confidence fields to every event
- Writes NEW v22 files so your existing v2.1 logs remain untouched

Recommended location:
C:\\Users\\brian\\OneDrive\\Desktop\\Docs\\CryptoTracker\\SmartMoneyMonitor\\smart_money_monitor_v2.py

Uses:
- Parent CryptoTracker .env for HELIUS_API_KEY
- SmartMoneyMonitor/traders.json
  Existing entries default to chain="solana".
  Robinhood entries use chain="robinhood".
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
import statistics
from dotenv import load_dotenv


# ---------------------------------------------------------------------------
# Paths / configuration
# ---------------------------------------------------------------------------

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
ENV_PATH = PROJECT_ROOT / ".env"
TRADERS_PATH = HERE / "traders.json"
DATA_DIR = HERE / "data"

# v2.2 writes new files; all v2.1 history remains untouched.
STATE_PATH = DATA_DIR / "state_v22.json"
EVENTS_CSV = DATA_DIR / "smart_money_events_v22.csv"
PERFORMANCE_CSV = DATA_DIR / "trader_performance_v22.csv"
CAMPAIGNS_CSV = DATA_DIR / "smart_money_campaigns_v22.csv"
WALLET_SCORECARD_CSV = DATA_DIR / "wallet_scorecard_v22.csv"

DATA_DIR.mkdir(parents=True, exist_ok=True)
load_dotenv(ENV_PATH)

HELIUS_API_KEY = os.getenv("HELIUS_API_KEY", "").strip()

POLL_SECONDS = int(os.getenv("SMART_MONEY_POLL_SECONDS", "15"))
HELIUS_LIMIT = int(os.getenv("SMART_MONEY_HELIUS_LIMIT", "20"))

# Classification thresholds.
MICRO_BUY_USD = float(os.getenv("SMART_MONEY_MICRO_BUY_USD", "50"))
MEANINGFUL_BUY_USD = float(os.getenv("SMART_MONEY_MEANINGFUL_BUY_USD", "500"))
STRONG_BUY_USD = float(os.getenv("SMART_MONEY_STRONG_BUY_USD", "2000"))
VERY_STRONG_BUY_USD = float(os.getenv("SMART_MONEY_VERY_STRONG_BUY_USD", "5000"))

# A campaign resets after this much inactivity in a trader/token.
CAMPAIGN_RESET_MINUTES = int(
    os.getenv("SMART_MONEY_CAMPAIGN_RESET_MINUTES", "60")
)

# v2.2 campaign-strength configuration.
SIGNAL_MIN_BUY_USD = float(os.getenv("SMART_MONEY_SIGNAL_MIN_BUY_USD", "100"))
ACCUMULATION_WINDOW_MINUTES = int(
    os.getenv("SMART_MONEY_ACCUMULATION_WINDOW_MINUTES", "15")
)
CONVERGENCE_WINDOW_MINUTES = int(
    os.getenv("SMART_MONEY_CONVERGENCE_WINDOW_MINUTES", "15")
)
CAMPAIGN_STRENGTH_MAX = float(
    os.getenv("SMART_MONEY_CAMPAIGN_STRENGTH_MAX", "25")
)
SAMPLE_SANITY_MAX_ABS_RETURN_PCT = float(
    os.getenv("SMART_MONEY_SAMPLE_SANITY_MAX_ABS_RETURN_PCT", "10000")
)

SAMPLE_MINUTES = [1, 3, 5, 15, 30, 60]

HELIUS_TX_URL = "https://api.helius.xyz/v0/addresses/{wallet}/transactions"
DEX_TOKEN_PAIRS_URL = "https://api.dexscreener.com/token-pairs/v1/solana/{mint}"

DEX_TOKEN_GENERIC_URL = "https://api.dexscreener.com/latest/dex/tokens/{mint}"

# Robinhood Chain mainnet.
ROBINHOOD_RPC_URL = os.getenv(
    "ROBINHOOD_RPC_URL",
    "https://rpc.mainnet.chain.robinhood.com",
).strip()
ROBINHOOD_CHAIN_ID = 4663
ROBINHOOD_MAX_BLOCKS_PER_CYCLE = int(
    os.getenv("SMART_MONEY_RH_MAX_BLOCKS_PER_CYCLE", "250")
)
ROBINHOOD_WETH = "0x0bd7d308f8e1639fab988df18a8011f41eacad73"
ROBINHOOD_USDG = "0x5fc5360d0400a0fd4f2af552add042d716f1d168"
TRANSFER_TOPIC0 = (
    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
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
    chain: str = "solana"
    confidence: str = ""
    enabled: bool = True


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc(ts: Optional[int] = None) -> str:
    dt = utc_now() if ts is None else datetime.fromtimestamp(ts, tz=timezone.utc)
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
                chain=str(item.get("chain", "solana")).strip().lower(),
                confidence=str(item.get("confidence", "")).strip(),
                enabled=True,
            )
        )

    if not traders:
        raise RuntimeError("No enabled traders found in traders.json")

    return traders


def default_state() -> dict:
    return {
        "initialized": {},
        "seen_signatures": [],
        "events": {},
        "campaigns": {},
        "campaign_seq": 0,
        "evm_last_block": {},
    }


def load_state() -> dict:
    if not STATE_PATH.exists():
        return default_state()

    try:
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        state = default_state()

    state.setdefault("initialized", {})
    state.setdefault("seen_signatures", [])
    state.setdefault("events", {})
    state.setdefault("campaigns", {})
    state.setdefault("campaign_seq", 0)
    state.setdefault("evm_last_block", {})
    return state


def save_state(state: dict) -> None:
    state["seen_signatures"] = state.get("seen_signatures", [])[-5000:]
    temp = STATE_PATH.with_suffix(".tmp")
    temp.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    temp.replace(STATE_PATH)


def append_csv(path: Path, row: dict, fieldnames: list[str]) -> None:
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def buy_size_class(usd: float) -> str:
    if usd <= 0:
        return "UNKNOWN"
    if usd < MICRO_BUY_USD:
        return "MICRO"
    if usd < MEANINGFUL_BUY_USD:
        return "SMALL"
    if usd < STRONG_BUY_USD:
        return "MEANINGFUL"
    if usd < VERY_STRONG_BUY_USD:
        return "STRONG"
    return "VERY_STRONG"


def campaign_key(wallet: str, mint: str) -> str:
    return f"{wallet}|{mint}"


def campaign_pattern(c: dict) -> str:
    """
    Descriptive only; it is NOT an accusation of manipulation.
    """
    anchor = safe_float(c.get("first_meaningful_buy_usd"))
    micro_after = int(c.get("micro_buys_after_anchor", 0))

    if anchor >= MEANINGFUL_BUY_USD and micro_after >= 3:
        return "LARGE_THEN_MICRO"
    if anchor >= MEANINGFUL_BUY_USD and micro_after > 0:
        return "LARGE_WITH_MICRO"
    if int(c.get("buy_count", 0)) >= 3:
        return "REPEATED_ACCUMULATION"
    if safe_float(c.get("largest_buy_usd")) >= MEANINGFUL_BUY_USD:
        return "LARGE_POSITION"
    return "EARLY"


EVENT_FIELDS = [
    "detected_at_utc",
    "trade_time_utc",
    "trader_name",
    "trader_handle",
    "wallet",
    "chain",
    "confidence",
    "signature",
    "tx_type",
    "token_mint",
    "token_symbol",
    "token_name",
    "token_amount_received",
    "estimated_spend_usd",
    "spend_asset",
    "spend_amount",
    "buy_size_class",

    # Campaign fields
    "campaign_id",
    "campaign_buy_number",
    "campaign_age_seconds",
    "campaign_pattern",
    "initial_buy_usd",
    "first_meaningful_buy_usd",
    "largest_buy_usd",
    "campaign_total_spend_usd",
    "campaign_meaningful_spend_usd",
    "campaign_micro_spend_usd",
    "campaign_micro_buy_count",
    "micro_buys_after_anchor",
    "is_micro_buy",
    "is_first_meaningful_buy",
    "is_signal_buy",
    "campaign_strength_score",
    "campaign_strength_label",
    "strength_components",
    "last_signal_utc",
    "last_meaningful_buy_utc",
    "latest_vs_previous_meaningful_ratio",
    "rapid_accumulation",
    "buying_pullback",
    "converging_trader_count",
    "converging_traders",

    # Market at detection
    "entry_price_usd",
    "liquidity_usd",
    "market_cap_usd",
    "volume_5m_usd",
    "volume_1h_usd",
    "price_change_5m_pct",
    "price_change_1h_pct",
    "buys_5m",
    "sells_5m",
    "buy_sell_ratio_5m",
]

PERFORMANCE_FIELDS = [
    "sampled_at_utc",
    "trader_name",
    "trader_handle",
    "chain",
    "confidence",
    "signature",
    "campaign_id",
    "campaign_buy_number",
    "campaign_pattern_at_entry",
    "token_mint",
    "token_symbol",
    "trade_time_utc",
    "estimated_spend_usd",
    "buy_size_class",
    "campaign_strength_score",
    "campaign_strength_label",
    "converging_trader_count",
    "horizon_minutes",
    "entry_price_usd",
    "sample_price_usd",
    "return_pct",
    "sample_status",
    "liquidity_usd",
    "market_cap_usd",
    "volume_5m_usd",
    "volume_1h_usd",
    "price_change_5m_pct",
    "price_change_1h_pct",
    "buys_5m",
    "sells_5m",
    "buy_sell_ratio_5m",
]

CAMPAIGN_FIELDS = [
    "updated_at_utc",
    "trader_name",
    "trader_handle",
    "wallet",
    "chain",
    "confidence",
    "token_mint",
    "token_symbol",
    "campaign_id",
    "campaign_start_utc",
    "last_buy_utc",
    "campaign_age_minutes",
    "buy_count",
    "micro_buy_count",
    "meaningful_buy_count",
    "micro_buys_after_anchor",
    "initial_buy_usd",
    "first_meaningful_buy_usd",
    "largest_buy_usd",
    "total_spend_usd",
    "meaningful_spend_usd",
    "micro_spend_usd",
    "campaign_pattern",
    "campaign_strength_score",
    "campaign_strength_label",
    "strength_components",
    "last_signal_utc",
    "last_meaningful_buy_utc",
    "latest_meaningful_buy_usd",
    "previous_meaningful_buy_usd",
    "latest_vs_previous_meaningful_ratio",
    "rapid_accumulation",
    "buying_pullback",
    "converging_trader_count",
    "converging_traders",
    "last_signature",
]


# ---------------------------------------------------------------------------
# Helius
# ---------------------------------------------------------------------------

def helius_recent_transactions(wallet: str) -> list[dict]:
    url = HELIUS_TX_URL.format(wallet=wallet)
    response = requests.get(
        url,
        params={"api-key": HELIUS_API_KEY, "limit": HELIUS_LIMIT},
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
    Heuristic buy detector. Only Helius SWAP transactions are considered.
    """
    if str(tx.get("type", "")).upper() != "SWAP":
        return None

    incoming = []
    outgoing = []

    for transfer in tx.get("tokenTransfers") or []:
        direction, amount, mint = token_transfer_direction(transfer, trader.wallet)
        if not mint or amount <= 0:
            continue

        record = {"mint": mint, "amount": amount}
        if direction == "IN":
            incoming.append(record)
        elif direction == "OUT":
            outgoing.append(record)

    bought = [t for t in incoming if t["mint"] not in QUOTE_MINTS]
    if not bought:
        return None

    bought.sort(key=lambda x: x["amount"], reverse=True)
    bought_token = bought[0]

    spend_asset = ""
    spend_amount = 0.0
    estimated_spend_usd = 0.0

    for mint in (USDC_MINT, USDT_MINT):
        stable_out = sum(t["amount"] for t in outgoing if t["mint"] == mint)
        if stable_out > 0:
            spend_asset = "USDC" if mint == USDC_MINT else "USDT"
            spend_amount = stable_out
            estimated_spend_usd = stable_out
            break

    if spend_amount == 0:
        sol_out = sum(t["amount"] for t in outgoing if t["mint"] == WSOL_MINT)
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


def dex_market(
    mint: str,
    chain: str = "solana",
    cache_seconds: int = 5,
) -> Optional[dict]:
    """
    Chain-aware DEX Screener lookup.

    Solana keeps the original v2 endpoint.
    Robinhood/EVM uses the generic token endpoint and chooses the
    highest-liquidity pair containing the requested token address.
    """
    chain = (chain or "solana").lower()
    cache_key = f"{chain}|{mint.lower()}"
    now = time.time()
    cached = _market_cache.get(cache_key)
    if cached and now - cached[0] <= cache_seconds:
        return cached[1]

    try:
        target = mint.lower()

        if chain == "solana":
            url = DEX_TOKEN_PAIRS_URL.format(mint=mint)
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            pairs = response.json()
            if not isinstance(pairs, list):
                pairs = []
            # Critical v2.2 fix: priceUsd is the BASE token price. Never use a
            # pair where the tracked mint is only the quote token.
            pairs = [
                p for p in pairs
                if p.get("chainId") == "solana"
                and str((p.get("baseToken") or {}).get("address", "")).lower() == target
            ]
        else:
            url = DEX_TOKEN_GENERIC_URL.format(mint=mint)
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            payload = response.json()
            pairs = payload.get("pairs") or []
            # Same exact-address rule for EVM/Robinhood Chain.
            pairs = [
                p for p in pairs
                if str((p.get("baseToken") or {}).get("address", "")).lower() == target
            ]

        if not pairs:
            _market_cache[cache_key] = (now, None)
            return None

        pair = max(
            pairs,
            key=lambda p: safe_float((p.get("liquidity") or {}).get("usd")),
        )

        base = pair.get("baseToken") or {}
        quote = pair.get("quoteToken") or {}
        txns = pair.get("txns") or {}
        m5_tx = txns.get("m5") or {}
        buys_5m = int(safe_float(m5_tx.get("buys")))
        sells_5m = int(safe_float(m5_tx.get("sells")))
        buy_sell_ratio = buys_5m / max(sells_5m, 1)

        base_is_target = True

        result = {
            "price_usd": safe_float(pair.get("priceUsd")),
            "liquidity_usd": safe_float((pair.get("liquidity") or {}).get("usd")),
            "market_cap_usd": safe_float(pair.get("marketCap") or pair.get("fdv")),
            "volume_5m_usd": safe_float((pair.get("volume") or {}).get("m5")),
            "volume_1h_usd": safe_float((pair.get("volume") or {}).get("h1")),
            "price_change_5m_pct": safe_float(
                (pair.get("priceChange") or {}).get("m5")
            ),
            "price_change_1h_pct": safe_float(
                (pair.get("priceChange") or {}).get("h1")
            ),
            "buys_5m": buys_5m,
            "sells_5m": sells_5m,
            "buy_sell_ratio_5m": buy_sell_ratio,
            "symbol": base.get("symbol", "") if base_is_target else quote.get("symbol", ""),
            "name": base.get("name", "") if base_is_target else quote.get("name", ""),
            "pair_address": pair.get("pairAddress", ""),
            "dex_chain_id": pair.get("chainId", ""),
        }

        _market_cache[cache_key] = (now, result)
        return result

    except Exception:
        _market_cache[cache_key] = (now, None)
        return None

def sol_price_usd() -> float:
    market = dex_market(WSOL_MINT, "solana")
    if not market:
        return 0.0
    return safe_float(market.get("price_usd"))


# ---------------------------------------------------------------------------
# Campaign handling
# ---------------------------------------------------------------------------

def create_campaign(
    trader: Trader,
    mint: str,
    symbol: str,
    timestamp: int,
    spend_usd: float,
    signature: str,
    state: dict,
) -> dict:
    state["campaign_seq"] = int(state.get("campaign_seq", 0)) + 1
    campaign_id = (
        f"{trader.name.replace(' ', '_')}-"
        f"{timestamp}-{state['campaign_seq']}"
    )

    is_micro = 0 < spend_usd < MICRO_BUY_USD
    is_meaningful = spend_usd >= MEANINGFUL_BUY_USD

    c = {
        "campaign_id": campaign_id,
        "trader_name": trader.name,
        "trader_handle": trader.handle,
        "wallet": trader.wallet,
        "chain": trader.chain,
        "confidence": trader.confidence,
        "token_mint": mint,
        "token_symbol": symbol,
        "start_timestamp": timestamp,
        "last_timestamp": timestamp,
        "buy_count": 1,
        "micro_buy_count": 1 if is_micro else 0,
        "meaningful_buy_count": 1 if is_meaningful else 0,
        "micro_buys_after_anchor": 0,
        "initial_buy_usd": spend_usd,
        "first_meaningful_buy_usd": spend_usd if is_meaningful else 0.0,
        "first_meaningful_timestamp": timestamp if is_meaningful else 0,
        "largest_buy_usd": spend_usd,
        "total_spend_usd": spend_usd,
        "meaningful_spend_usd": spend_usd if is_meaningful else 0.0,
        "micro_spend_usd": spend_usd if is_micro else 0.0,
        "last_signature": signature,
        "last_signal_timestamp": timestamp if spend_usd >= SIGNAL_MIN_BUY_USD else 0,
        "last_meaningful_timestamp": timestamp if is_meaningful else 0,
        "latest_meaningful_buy_usd": spend_usd if is_meaningful else 0.0,
        "previous_meaningful_buy_usd": 0.0,
        "meaningful_buy_history": (
            [{"timestamp": timestamp, "spend_usd": spend_usd}]
            if is_meaningful else []
        ),
        "campaign_strength_score": 0.0,
        "campaign_strength_label": "OBSERVE",
        "strength_components": "",
        "latest_vs_previous_meaningful_ratio": 0.0,
        "rapid_accumulation": 0,
        "buying_pullback": 0,
        "converging_trader_count": 1,
        "converging_traders": trader.name,
    }
    return c


def update_campaign(
    trader: Trader,
    mint: str,
    symbol: str,
    timestamp: int,
    spend_usd: float,
    signature: str,
    state: dict,
) -> tuple[dict, bool]:
    """
    Returns (campaign, is_new_campaign).

    A campaign is same trader + token until inactivity exceeds
    CAMPAIGN_RESET_MINUTES.
    """
    key = campaign_key(trader.wallet, mint)
    existing = state["campaigns"].get(key)

    if existing:
        inactive_seconds = timestamp - int(existing.get("last_timestamp", 0))
    else:
        inactive_seconds = 10**18

    if (
        not existing
        or inactive_seconds > CAMPAIGN_RESET_MINUTES * 60
        or inactive_seconds < 0
    ):
        c = create_campaign(
            trader, mint, symbol, timestamp, spend_usd, signature, state
        )
        state["campaigns"][key] = c
        return c, True

    c = existing
    c["token_symbol"] = symbol or c.get("token_symbol", "")
    c["last_timestamp"] = timestamp
    c["buy_count"] = int(c.get("buy_count", 0)) + 1
    c["total_spend_usd"] = safe_float(c.get("total_spend_usd")) + spend_usd
    c["largest_buy_usd"] = max(safe_float(c.get("largest_buy_usd")), spend_usd)
    c["last_signature"] = signature

    is_micro = 0 < spend_usd < MICRO_BUY_USD
    is_meaningful = spend_usd >= MEANINGFUL_BUY_USD

    if spend_usd >= SIGNAL_MIN_BUY_USD:
        c["last_signal_timestamp"] = timestamp

    if is_micro:
        c["micro_buy_count"] = int(c.get("micro_buy_count", 0)) + 1
        c["micro_spend_usd"] = safe_float(c.get("micro_spend_usd")) + spend_usd

        anchor_ts = int(c.get("first_meaningful_timestamp", 0) or 0)
        if anchor_ts and timestamp >= anchor_ts:
            c["micro_buys_after_anchor"] = (
                int(c.get("micro_buys_after_anchor", 0)) + 1
            )

    if is_meaningful:
        c["meaningful_buy_count"] = int(c.get("meaningful_buy_count", 0)) + 1
        c["meaningful_spend_usd"] = (
            safe_float(c.get("meaningful_spend_usd")) + spend_usd
        )

        previous = safe_float(c.get("latest_meaningful_buy_usd"))
        c["previous_meaningful_buy_usd"] = previous
        c["latest_meaningful_buy_usd"] = spend_usd
        c["last_meaningful_timestamp"] = timestamp
        hist = list(c.get("meaningful_buy_history") or [])
        hist.append({"timestamp": timestamp, "spend_usd": spend_usd})
        c["meaningful_buy_history"] = hist[-12:]

        if safe_float(c.get("first_meaningful_buy_usd")) <= 0:
            c["first_meaningful_buy_usd"] = spend_usd
            c["first_meaningful_timestamp"] = timestamp

    state["campaigns"][key] = c
    return c, False



def _verified_confidence(value: str) -> bool:
    text = str(value or "").lower()
    return "verified" in text and "unverified" not in text


def _converging_traders(state: dict, campaign: dict, now_ts: int) -> list[str]:
    """
    Distinct verified traders with a real signal-sized buy in the same exact
    token inside the convergence window. Same-wallet repeats count once.
    """
    mint = str(campaign.get("token_mint") or "")
    chain = str(campaign.get("chain") or "").lower()
    cutoff = now_ts - CONVERGENCE_WINDOW_MINUTES * 60
    found = {}

    for other in (state.get("campaigns") or {}).values():
        if str(other.get("token_mint") or "") != mint:
            continue
        if str(other.get("chain") or "").lower() != chain:
            continue
        if not _verified_confidence(other.get("confidence")):
            continue

        signal_ts = int(other.get("last_signal_timestamp", 0) or 0)
        if signal_ts < cutoff:
            continue

        wallet = str(other.get("wallet") or "")
        if wallet:
            found[wallet] = str(other.get("trader_name") or other.get("trader_handle") or short(wallet))

    return sorted(found.values())


def calculate_campaign_strength(
    campaign: dict,
    latest_spend_usd: float,
    timestamp: int,
    market: dict,
    state: dict,
) -> dict:
    """
    Score sustained verified accumulation rather than treating every repeat buy
    the same. Score is observation/confirmation only; SmartMoneyMonitor never
    places a trade.

    Core design:
      first meaningful buy        +8
      second meaningful buy       +4
      third+ meaningful buying    +4 max
      increasing meaningful size  +3
      meaningful spend >= $5k     +3
      meaningful spend >= $10k    +5 instead
      >=2 meaningful buys / 15m   +3
      buy during 5m pullback      +2 observation
      late extension              penalty
    Cross-wallet convergence is recorded separately so CryptoTracker can apply
    its existing multi-whale bonus without double counting here.
    """
    components = []
    score = 0.0

    verified = _verified_confidence(campaign.get("confidence"))
    meaningful_count = int(campaign.get("meaningful_buy_count", 0) or 0)
    meaningful_spend = safe_float(campaign.get("meaningful_spend_usd"))
    latest_meaningful = safe_float(campaign.get("latest_meaningful_buy_usd"))
    previous_meaningful = safe_float(campaign.get("previous_meaningful_buy_usd"))

    if verified and meaningful_count >= 1:
        score += 8.0
        components.append("first_meaningful:+8")

    if verified and meaningful_count >= 2:
        score += 4.0
        components.append("second_meaningful:+4")

    if verified and meaningful_count >= 3:
        score += 4.0
        components.append("third_plus_accumulation:+4")

    ratio = 0.0
    if previous_meaningful > 0 and latest_meaningful > 0:
        ratio = latest_meaningful / previous_meaningful
        if ratio >= 1.15:
            score += 3.0
            components.append("increasing_buy_size:+3")

    if meaningful_spend >= 10_000:
        score += 5.0
        components.append("meaningful_spend_10k:+5")
    elif meaningful_spend >= 5_000:
        score += 3.0
        components.append("meaningful_spend_5k:+3")

    history = list(campaign.get("meaningful_buy_history") or [])
    cutoff = timestamp - ACCUMULATION_WINDOW_MINUTES * 60
    recent_meaningful = [
        h for h in history
        if int(h.get("timestamp", 0) or 0) >= cutoff
    ]
    rapid = int(len(recent_meaningful) >= 2)
    if verified and rapid:
        score += 3.0
        components.append("rapid_accumulation:+3")

    p5 = safe_float(market.get("price_change_5m_pct"))
    p1h = safe_float(market.get("price_change_1h_pct"))
    buying_pullback = int(
        verified
        and latest_spend_usd >= MEANINGFUL_BUY_USD
        and meaningful_count >= 2
        and p5 < 0
    )
    if buying_pullback:
        # Small credit only. The main trader still requires independent quant
        # reacceleration before this can matter to a real entry.
        score += 2.0
        components.append("buying_pullback:+2")

    # Do not reward increasingly late chasing without bound.
    if p1h > 100 or p5 > 30:
        score -= 8.0
        components.append("extreme_extension:-8")
    elif p1h > 40 or p5 > 15:
        score -= 4.0
        components.append("late_extension:-4")

    convergence = _converging_traders(state, campaign, timestamp)

    # Small signal-sized buys can remain visible even before a $500 anchor,
    # but they do not get meaningful-accumulation points.
    if score <= 0 and verified and latest_spend_usd >= SIGNAL_MIN_BUY_USD:
        score = 2.0
        components.append("signal_sized_observation:+2")

    score = max(0.0, min(CAMPAIGN_STRENGTH_MAX, score))

    if score >= 20:
        label = "VERY_STRONG"
    elif score >= 12:
        label = "STRONG"
    elif score >= 6:
        label = "BUILDING"
    elif score > 0:
        label = "OBSERVE"
    else:
        label = "NONE"

    return {
        "score": round(score, 3),
        "label": label,
        "components": "|".join(components),
        "ratio": round(ratio, 4),
        "rapid": rapid,
        "buying_pullback": buying_pullback,
        "converging_trader_count": len(convergence),
        "converging_traders": "|".join(convergence),
    }


def append_campaign_snapshot(c: dict) -> None:
    now_ts = int(time.time())
    row = {
        "updated_at_utc": iso_utc(),
        "trader_name": c.get("trader_name", ""),
        "trader_handle": c.get("trader_handle", ""),
        "wallet": c.get("wallet", ""),
        "chain": c.get("chain", ""),
        "confidence": c.get("confidence", ""),
        "token_mint": c.get("token_mint", ""),
        "token_symbol": c.get("token_symbol", ""),
        "campaign_id": c.get("campaign_id", ""),
        "campaign_start_utc": iso_utc(int(c.get("start_timestamp", now_ts))),
        "last_buy_utc": iso_utc(int(c.get("last_timestamp", now_ts))),
        "campaign_age_minutes": round(
            max(0, int(c.get("last_timestamp", now_ts))
                - int(c.get("start_timestamp", now_ts))) / 60.0,
            3,
        ),
        "buy_count": int(c.get("buy_count", 0)),
        "micro_buy_count": int(c.get("micro_buy_count", 0)),
        "meaningful_buy_count": int(c.get("meaningful_buy_count", 0)),
        "micro_buys_after_anchor": int(c.get("micro_buys_after_anchor", 0)),
        "initial_buy_usd": round(safe_float(c.get("initial_buy_usd")), 6),
        "first_meaningful_buy_usd": round(
            safe_float(c.get("first_meaningful_buy_usd")), 6
        ),
        "largest_buy_usd": round(safe_float(c.get("largest_buy_usd")), 6),
        "total_spend_usd": round(safe_float(c.get("total_spend_usd")), 6),
        "meaningful_spend_usd": round(
            safe_float(c.get("meaningful_spend_usd")), 6
        ),
        "micro_spend_usd": round(safe_float(c.get("micro_spend_usd")), 6),
        "campaign_pattern": campaign_pattern(c),
        "campaign_strength_score": safe_float(c.get("campaign_strength_score")),
        "campaign_strength_label": c.get("campaign_strength_label", ""),
        "strength_components": c.get("strength_components", ""),
        "last_signal_utc": (
            iso_utc(int(c.get("last_signal_timestamp", 0)))
            if int(c.get("last_signal_timestamp", 0) or 0) > 0 else ""
        ),
        "last_meaningful_buy_utc": (
            iso_utc(int(c.get("last_meaningful_timestamp", 0)))
            if int(c.get("last_meaningful_timestamp", 0) or 0) > 0 else ""
        ),
        "latest_meaningful_buy_usd": round(safe_float(c.get("latest_meaningful_buy_usd")), 6),
        "previous_meaningful_buy_usd": round(safe_float(c.get("previous_meaningful_buy_usd")), 6),
        "latest_vs_previous_meaningful_ratio": safe_float(c.get("latest_vs_previous_meaningful_ratio")),
        "rapid_accumulation": int(c.get("rapid_accumulation", 0) or 0),
        "buying_pullback": int(c.get("buying_pullback", 0) or 0),
        "converging_trader_count": int(c.get("converging_trader_count", 0) or 0),
        "converging_traders": c.get("converging_traders", ""),
        "last_signature": c.get("last_signature", ""),
    }
    append_csv(CAMPAIGNS_CSV, row, CAMPAIGN_FIELDS)


# ---------------------------------------------------------------------------
# Event handling / performance sampling
# ---------------------------------------------------------------------------

def market_fields(market: dict) -> dict:
    return {
        "liquidity_usd": safe_float(market.get("liquidity_usd")),
        "market_cap_usd": safe_float(market.get("market_cap_usd")),
        "volume_5m_usd": safe_float(market.get("volume_5m_usd")),
        "volume_1h_usd": safe_float(market.get("volume_1h_usd")),
        "price_change_5m_pct": safe_float(market.get("price_change_5m_pct")),
        "price_change_1h_pct": safe_float(market.get("price_change_1h_pct")),
        "buys_5m": int(safe_float(market.get("buys_5m"))),
        "sells_5m": int(safe_float(market.get("sells_5m"))),
        "buy_sell_ratio_5m": round(
            safe_float(market.get("buy_sell_ratio_5m")), 6
        ),
    }


def record_buy(
    trader: Trader,
    tx: dict,
    buy: dict,
    state: dict,
) -> None:
    signature = tx.get("signature", "")
    timestamp = int(tx.get("timestamp") or time.time())
    mint = buy["token_mint"]

    market = dex_market(mint, trader.chain) or {}

    estimated_spend_usd = safe_float(buy.get("estimated_spend_usd"))
    if (
        estimated_spend_usd <= 0
        and buy.get("spend_asset") == "SOL"
        and safe_float(buy.get("spend_amount")) > 0
    ):
        estimated_spend_usd = safe_float(buy["spend_amount"]) * sol_price_usd()

    entry_price = safe_float(market.get("price_usd"))
    symbol = market.get("symbol") or short(mint, 4)
    name = market.get("name") or ""
    size_class = buy_size_class(estimated_spend_usd)

    # Important: capture whether this particular buy established the anchor
    # BEFORE campaign totals are printed/logged.
    prior = state["campaigns"].get(campaign_key(trader.wallet, mint))
    prior_first_meaningful = (
        safe_float(prior.get("first_meaningful_buy_usd")) if prior else 0.0
    )

    c, is_new_campaign = update_campaign(
        trader=trader,
        mint=mint,
        symbol=symbol,
        timestamp=timestamp,
        spend_usd=estimated_spend_usd,
        signature=signature,
        state=state,
    )

    is_micro = 0 < estimated_spend_usd < MICRO_BUY_USD
    is_first_meaningful = (
        estimated_spend_usd >= MEANINGFUL_BUY_USD
        and (is_new_campaign or prior_first_meaningful <= 0)
    )
    is_signal_buy = estimated_spend_usd >= SIGNAL_MIN_BUY_USD

    strength = calculate_campaign_strength(
        c,
        estimated_spend_usd,
        timestamp,
        market,
        state,
    )
    c["campaign_strength_score"] = strength["score"]
    c["campaign_strength_label"] = strength["label"]
    c["strength_components"] = strength["components"]
    c["latest_vs_previous_meaningful_ratio"] = strength["ratio"]
    c["rapid_accumulation"] = strength["rapid"]
    c["buying_pullback"] = strength["buying_pullback"]
    c["converging_trader_count"] = strength["converging_trader_count"]
    c["converging_traders"] = strength["converging_traders"]
    state["campaigns"][campaign_key(trader.wallet, mint)] = c

    age_seconds = max(0, timestamp - int(c.get("start_timestamp", timestamp)))

    row = {
        "detected_at_utc": iso_utc(),
        "trade_time_utc": iso_utc(timestamp),
        "trader_name": trader.name,
        "trader_handle": trader.handle,
        "wallet": trader.wallet,
        "chain": trader.chain,
        "confidence": trader.confidence,
        "signature": signature,
        "tx_type": tx.get("type", ""),
        "token_mint": mint,
        "token_symbol": symbol,
        "token_name": name,
        "token_amount_received": buy["token_amount_received"],
        "estimated_spend_usd": round(estimated_spend_usd, 6),
        "spend_asset": buy["spend_asset"],
        "spend_amount": buy["spend_amount"],
        "buy_size_class": size_class,

        "campaign_id": c["campaign_id"],
        "campaign_buy_number": int(c.get("buy_count", 0)),
        "campaign_age_seconds": age_seconds,
        "campaign_pattern": campaign_pattern(c),
        "initial_buy_usd": round(safe_float(c.get("initial_buy_usd")), 6),
        "first_meaningful_buy_usd": round(
            safe_float(c.get("first_meaningful_buy_usd")), 6
        ),
        "largest_buy_usd": round(safe_float(c.get("largest_buy_usd")), 6),
        "campaign_total_spend_usd": round(
            safe_float(c.get("total_spend_usd")), 6
        ),
        "campaign_meaningful_spend_usd": round(
            safe_float(c.get("meaningful_spend_usd")), 6
        ),
        "campaign_micro_spend_usd": round(
            safe_float(c.get("micro_spend_usd")), 6
        ),
        "campaign_micro_buy_count": int(c.get("micro_buy_count", 0)),
        "micro_buys_after_anchor": int(c.get("micro_buys_after_anchor", 0)),
        "is_micro_buy": int(is_micro),
        "is_first_meaningful_buy": int(is_first_meaningful),
        "is_signal_buy": int(is_signal_buy),
        "campaign_strength_score": strength["score"],
        "campaign_strength_label": strength["label"],
        "strength_components": strength["components"],
        "last_signal_utc": (
            iso_utc(int(c.get("last_signal_timestamp", 0)))
            if int(c.get("last_signal_timestamp", 0) or 0) > 0 else ""
        ),
        "last_meaningful_buy_utc": (
            iso_utc(int(c.get("last_meaningful_timestamp", 0)))
            if int(c.get("last_meaningful_timestamp", 0) or 0) > 0 else ""
        ),
        "latest_vs_previous_meaningful_ratio": strength["ratio"],
        "rapid_accumulation": strength["rapid"],
        "buying_pullback": strength["buying_pullback"],
        "converging_trader_count": strength["converging_trader_count"],
        "converging_traders": strength["converging_traders"],

        "entry_price_usd": entry_price,
        **market_fields(market),
    }

    append_csv(EVENTS_CSV, row, EVENT_FIELDS)
    append_campaign_snapshot(c)

    state["events"][signature] = {
        "trader_name": trader.name,
        "trader_handle": trader.handle,
        "chain": trader.chain,
        "confidence": trader.confidence,
        "signature": signature,
        "campaign_id": c["campaign_id"],
        "campaign_buy_number": int(c.get("buy_count", 0)),
        "campaign_pattern_at_entry": campaign_pattern(c),
        "token_mint": mint,
        "token_symbol": symbol,
        "trade_timestamp": timestamp,
        "trade_time_utc": iso_utc(timestamp),
        "entry_price_usd": entry_price,
        "estimated_spend_usd": estimated_spend_usd,
        "buy_size_class": size_class,
        "campaign_strength_score": strength["score"],
        "campaign_strength_label": strength["label"],
        "converging_trader_count": strength["converging_trader_count"],
        "sampled_minutes": [],
    }

    dollars = (
        f"${estimated_spend_usd:,.2f}"
        if estimated_spend_usd > 0
        else f"{safe_float(buy['spend_amount']):.4f} "
             f"{buy['spend_asset'] or 'unknown'}"
    )

    print()
    print("SMART MONEY BUY DETECTED")
    print(f"  Trader      : {trader.name} (@{trader.handle})")
    print(f"  Chain       : {trader.chain}")
    if trader.confidence:
        print(f"  Confidence  : {trader.confidence}")
    print(f"  Token       : {symbol} ({short(mint)})")
    print(f"  Spend       : {dollars} [{size_class}]")
    print(
        f"  Campaign    : #{int(c.get('buy_count', 0))} "
        f"| total ${safe_float(c.get('total_spend_usd')):,.2f}"
    )
    print(
        f"  Anchor      : ${safe_float(c.get('first_meaningful_buy_usd')):,.2f} "
        f"| micro after anchor {int(c.get('micro_buys_after_anchor', 0))}"
    )
    print(f"  Pattern     : {campaign_pattern(c)}")
    print(
        f"  Strength    : {strength['score']:.0f}/{CAMPAIGN_STRENGTH_MAX:.0f} "
        f"[{strength['label']}]"
    )
    if strength["components"]:
        print(f"  Components  : {strength['components']}")
    if strength["converging_trader_count"] >= 2:
        print(
            f"  Convergence : {strength['converging_trader_count']} traders | "
            f"{strength['converging_traders']}"
        )
    print(
        f"  Price       : ${entry_price:.10f}"
        if entry_price > 0
        else "  Price       : unavailable"
    )
    print(f"  Liquidity   : ${safe_float(market.get('liquidity_usd')):,.0f}")
    print(
        f"  Momentum    : 5m {safe_float(market.get('price_change_5m_pct')):+.1f}% "
        f"| 1h {safe_float(market.get('price_change_1h_pct')):+.1f}%"
    )
    print(
        f"  5m flow     : {int(safe_float(market.get('buys_5m')))} buys / "
        f"{int(safe_float(market.get('sells_5m')))} sells "
        f"| ratio {safe_float(market.get('buy_sell_ratio_5m')):.2f}"
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
            if minute in sampled or age_seconds < minute * 60:
                continue

            market = dex_market(
                event["token_mint"],
                event.get("chain", "solana"),
            )
            if not market:
                continue

            sample_price = safe_float(market.get("price_usd"))
            entry_price = safe_float(event.get("entry_price_usd"))
            if sample_price <= 0 or entry_price <= 0:
                continue

            return_pct = ((sample_price / entry_price) - 1.0) * 100.0
            sample_status = "OK"
            if abs(return_pct) > SAMPLE_SANITY_MAX_ABS_RETURN_PCT:
                sample_status = "ANOMALY"

            row = {
                "sampled_at_utc": iso_utc(),
                "trader_name": event["trader_name"],
                "trader_handle": event["trader_handle"],
                "chain": event.get("chain", "solana"),
                "confidence": event.get("confidence", ""),
                "signature": signature,
                "campaign_id": event.get("campaign_id", ""),
                "campaign_buy_number": event.get("campaign_buy_number", 0),
                "campaign_pattern_at_entry": event.get(
                    "campaign_pattern_at_entry", ""
                ),
                "token_mint": event["token_mint"],
                "token_symbol": event["token_symbol"],
                "trade_time_utc": event["trade_time_utc"],
                "estimated_spend_usd": round(
                    safe_float(event.get("estimated_spend_usd")), 6
                ),
                "buy_size_class": event.get("buy_size_class", ""),
                "campaign_strength_score": safe_float(event.get("campaign_strength_score")),
                "campaign_strength_label": event.get("campaign_strength_label", ""),
                "converging_trader_count": int(event.get("converging_trader_count", 0) or 0),
                "horizon_minutes": minute,
                "entry_price_usd": entry_price,
                "sample_price_usd": sample_price,
                "return_pct": round(return_pct, 6) if sample_status == "OK" else "",
                "sample_status": sample_status,
                **market_fields(market),
            }

            append_csv(PERFORMANCE_CSV, row, PERFORMANCE_FIELDS)

            sampled.add(minute)
            event["sampled_minutes"] = sorted(sampled)
            changed = True

            print(
                f"  PERFORMANCE: {event['trader_name']} "
                f"{event['token_symbol']} "
                f"campaign buy #{event.get('campaign_buy_number', 0)} "
                f"+{minute}m "
                f"{return_pct:+.2f}%"
                f"{' [ANOMALY SUPPRESSED]' if sample_status != 'OK' else ''}"
            )

    if changed:
        save_state(state)


WALLET_SCORECARD_FIELDS = [
    "updated_at_utc",
    "trader_name",
    "trader_handle",
    "chain",
    "confidence",
    "horizon_minutes",
    "sample_count",
    "median_return_pct",
    "positive_rate_pct",
    "return_10plus_rate_pct",
    "median_strength_score",
]


def rebuild_wallet_scorecard() -> None:
    """
    Rebuild per-wallet/per-horizon performance from clean v2.2 samples.
    This is descriptive research only; it does not automatically change weights.
    """
    if not PERFORMANCE_CSV.exists():
        return

    groups = {}
    try:
        with PERFORMANCE_CSV.open("r", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if str(row.get("sample_status") or "OK").upper() != "OK":
                    continue
                try:
                    ret = float(row.get("return_pct"))
                except (TypeError, ValueError):
                    continue
                horizon = int(safe_float(row.get("horizon_minutes")))
                key = (
                    str(row.get("trader_name") or ""),
                    str(row.get("trader_handle") or ""),
                    str(row.get("chain") or ""),
                    str(row.get("confidence") or ""),
                    horizon,
                )
                groups.setdefault(key, []).append({
                    "return": ret,
                    "strength": safe_float(row.get("campaign_strength_score")),
                })
    except Exception as exc:
        print(f"  SCORECARD WARNING: {exc}")
        return

    rows = []
    for key, vals in sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][4])):
        trader_name, handle, chain, confidence, horizon = key
        returns = [v["return"] for v in vals]
        strengths = [v["strength"] for v in vals if v["strength"] > 0]
        n = len(returns)
        rows.append({
            "updated_at_utc": iso_utc(),
            "trader_name": trader_name,
            "trader_handle": handle,
            "chain": chain,
            "confidence": confidence,
            "horizon_minutes": horizon,
            "sample_count": n,
            "median_return_pct": round(statistics.median(returns), 6) if returns else "",
            "positive_rate_pct": round(sum(r > 0 for r in returns) / n * 100.0, 3) if n else "",
            "return_10plus_rate_pct": round(sum(r >= 10 for r in returns) / n * 100.0, 3) if n else "",
            "median_strength_score": round(statistics.median(strengths), 3) if strengths else "",
        })

    tmp = WALLET_SCORECARD_CSV.with_suffix(".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=WALLET_SCORECARD_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(WALLET_SCORECARD_CSV)



def bootstrap_or_process_trader(
    trader: Trader,
    state: dict,
) -> int:
    """
    First run is intentionally safe:
    - recent transactions become baseline
    - old transactions are NOT treated as new buys
    - only genuinely new transactions are recorded afterward
    """
    txs = helius_recent_transactions(trader.wallet)
    if not txs:
        return 0

    seen = set(state["seen_signatures"])
    wallet_initialized = state["initialized"].get(trader.wallet, False)

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
        print("  New transactions after this point will be observed.")
        return 0

    new_txs = [
        tx for tx in txs
        if tx.get("signature") and tx.get("signature") not in seen
    ]
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
# Robinhood Chain direct-RPC monitoring
# ---------------------------------------------------------------------------

_evm_rpc_id = 0
_evm_meta_cache: dict[str, tuple[str, int]] = {}


def evm_rpc(method: str, params: list[Any]) -> Any:
    global _evm_rpc_id
    _evm_rpc_id += 1
    payload = {
        "jsonrpc": "2.0",
        "id": _evm_rpc_id,
        "method": method,
        "params": params,
    }

    response = requests.post(
        ROBINHOOD_RPC_URL,
        json=payload,
        timeout=25,
        headers={"Content-Type": "application/json"},
    )
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise RuntimeError(data["error"])
    return data.get("result")


def evm_hex_int(value: Any) -> int:
    try:
        return int(value or "0x0", 16)
    except (TypeError, ValueError):
        return 0


def evm_latest_block() -> int:
    return evm_hex_int(evm_rpc("eth_blockNumber", []))


def evm_chain_id() -> int:
    return evm_hex_int(evm_rpc("eth_chainId", []))


def evm_topic_address(topic: str) -> str:
    return "0x" + str(topic)[-40:].lower()


def evm_decode_symbol(raw: str) -> str:
    if not raw or raw == "0x":
        return ""

    try:
        data = bytes.fromhex(raw[2:])
    except Exception:
        return ""

    # ABI dynamic string.
    try:
        if len(data) >= 64:
            offset = int.from_bytes(data[0:32], "big")
            if offset + 32 <= len(data):
                length = int.from_bytes(data[offset:offset + 32], "big")
                text = data[offset + 32:offset + 32 + length].decode(
                    "utf-8", errors="ignore"
                )
                if text:
                    return text.strip("\x00")
    except Exception:
        pass

    try:
        return data[:32].rstrip(b"\x00").decode("utf-8", errors="ignore")
    except Exception:
        return ""


def evm_token_meta(contract: str) -> tuple[str, int]:
    contract = contract.lower()
    if contract in _evm_meta_cache:
        return _evm_meta_cache[contract]

    symbol = ""
    decimals = 18

    try:
        raw = evm_rpc(
            "eth_call",
            [{"to": contract, "data": "0x95d89b41"}, "latest"],
        )
        symbol = evm_decode_symbol(raw)
    except Exception:
        pass

    try:
        raw = evm_rpc(
            "eth_call",
            [{"to": contract, "data": "0x313ce567"}, "latest"],
        )
        if raw and raw != "0x":
            decimals = int(raw, 16)
    except Exception:
        pass

    _evm_meta_cache[contract] = (symbol or short(contract, 4), decimals)
    return _evm_meta_cache[contract]


def evm_parse_transfer(log: dict) -> Optional[dict]:
    topics = log.get("topics") or []
    if len(topics) < 3:
        return None
    if str(topics[0]).lower() != TRANSFER_TOPIC0:
        return None

    token = str(log.get("address") or "").lower()
    if not token:
        return None

    try:
        raw_amount = int(log.get("data") or "0x0", 16)
    except Exception:
        raw_amount = 0

    return {
        "token": token,
        "from": evm_topic_address(topics[1]),
        "to": evm_topic_address(topics[2]),
        "raw_amount": raw_amount,
    }


def evm_receipt(tx_hash: str) -> dict:
    return evm_rpc("eth_getTransactionReceipt", [tx_hash]) or {}


def evm_block(block_number: int, full_transactions: bool = True) -> dict:
    return evm_rpc(
        "eth_getBlockByNumber",
        [hex(block_number), full_transactions],
    ) or {}


def robinhood_weth_price_usd() -> float:
    market = dex_market(ROBINHOOD_WETH, "robinhood")
    return safe_float((market or {}).get("price_usd"))


def extract_robinhood_buy(
    tx: dict,
    receipt: dict,
    trader: Trader,
) -> Optional[dict]:
    wallet = trader.wallet.lower()
    incoming = []
    outgoing = []

    for raw in receipt.get("logs") or []:
        transfer = evm_parse_transfer(raw)
        if not transfer:
            continue

        symbol, decimals = evm_token_meta(transfer["token"])
        amount = (
            transfer["raw_amount"] / (10 ** decimals)
            if decimals >= 0 else float(transfer["raw_amount"])
        )

        record = {
            "token": transfer["token"],
            "symbol": symbol,
            "amount": amount,
        }

        if transfer["to"] == wallet and transfer["from"] != wallet:
            incoming.append(record)
        elif transfer["from"] == wallet and transfer["to"] != wallet:
            outgoing.append(record)

    if not incoming:
        return None

    # Exclude obvious quote/payment assets from "bought token" selection.
    quote_symbols = {"WETH", "ETH", "USDG", "USDC", "USDT", "DAI"}
    bought = [
        t for t in incoming
        if t["symbol"].upper() not in quote_symbols
    ]
    if not bought:
        return None

    # Prefer the incoming token with the highest available USD value;
    # otherwise fall back to largest raw token amount.
    for t in bought:
        market = dex_market(t["token"], "robinhood") or {}
        t["usd_value"] = t["amount"] * safe_float(market.get("price_usd"))

    bought.sort(
        key=lambda x: (safe_float(x.get("usd_value")), x["amount"]),
        reverse=True,
    )
    bought_token = bought[0]

    spend_asset = ""
    spend_amount = 0.0
    estimated_spend_usd = 0.0

    # Direct stablecoin/USD-like outflow.
    for row in outgoing:
        sym = row["symbol"].upper()
        if "USD" in sym or sym in {"USDC", "USDT", "DAI"}:
            spend_asset = row["symbol"]
            spend_amount += row["amount"]
            estimated_spend_usd += row["amount"]

    # Direct WETH outflow.
    if spend_amount <= 0:
        weth_out = sum(
            row["amount"]
            for row in outgoing
            if row["token"].lower() == ROBINHOOD_WETH
            or row["symbol"].upper() == "WETH"
        )
        if weth_out > 0:
            spend_asset = "WETH"
            spend_amount = weth_out
            px = robinhood_weth_price_usd()
            if px > 0:
                estimated_spend_usd = weth_out * px

    # Native ETH value when the wallet initiated the transaction.
    if spend_amount <= 0:
        tx_from = str(tx.get("from") or "").lower()
        native = evm_hex_int(tx.get("value")) / 1e18
        if tx_from == wallet and native > 0:
            spend_asset = "ETH"
            spend_amount = native
            px = robinhood_weth_price_usd()
            if px > 0:
                estimated_spend_usd = native * px

    return {
        "token_mint": bought_token["token"],
        "token_amount_received": bought_token["amount"],
        "spend_asset": spend_asset,
        "spend_amount": spend_amount,
        "estimated_spend_usd": estimated_spend_usd,
    }


def bootstrap_or_process_robinhood_trader(
    trader: Trader,
    state: dict,
) -> int:
    """
    Direct block polling.

    First run sets the current block as baseline. No historical activity is
    replayed. Later cycles inspect transactions sent by the watched EOA.
    """
    if evm_chain_id() != ROBINHOOD_CHAIN_ID:
        raise RuntimeError(
            f"Robinhood RPC chain mismatch; expected {ROBINHOOD_CHAIN_ID}"
        )

    latest = evm_latest_block()
    key = trader.wallet.lower()
    last = state["evm_last_block"].get(key)
    print(f"    Robinhood latest block: {latest:,}")

    if last is None:
        state["evm_last_block"][key] = latest
        save_state(state)
        print(
            f"    Initialized {trader.name} at block {latest:,}. "
            "Monitoring new blocks only."
        )
        return 0

    last = int(last)
    if latest <= last:
        print(f"    No new Robinhood blocks since {last:,}.")
        return 0

    backlog = latest - last

    # We only care about live monitoring. If the saved state is stale,
    # discard the historical backlog and reset to the current tip.
    if backlog > ROBINHOOD_MAX_BLOCKS_PER_CYCLE:
        print(
            f"    Stale Robinhood backlog detected: {backlog:,} blocks."
        )
        print(
            f"    Skipping historical backlog and resetting baseline "
            f"to {latest:,}."
        )
        state["evm_last_block"][key] = latest
        save_state(state)
        return 0

    start = last + 1
    end = latest
    print(
        f"    Checking {end - start + 1:,} new Robinhood block(s): "
        f"{start:,} -> {end:,}"
    )

    detected = 0
    wallet = trader.wallet.lower()

    for block_number in range(start, end + 1):
        block = evm_block(block_number, True)
        timestamp = evm_hex_int(block.get("timestamp")) or int(time.time())

        for tx in block.get("transactions") or []:
            if str(tx.get("from") or "").lower() != wallet:
                continue

            tx_hash = str(tx.get("hash") or "")
            if not tx_hash:
                continue

            receipt = evm_receipt(tx_hash)
            buy = extract_robinhood_buy(tx, receipt, trader)
            if not buy:
                continue

            synthetic_tx = {
                "signature": tx_hash,
                "timestamp": timestamp,
                "type": "EVM_SWAP_HEURISTIC",
            }
            record_buy(trader, synthetic_tx, buy, state)
            detected += 1

    state["evm_last_block"][key] = end
    save_state(state)

    return detected


def process_trader(trader: Trader, state: dict) -> int:
    chain = (trader.chain or "solana").lower()
    if chain == "solana":
        if not HELIUS_API_KEY:
            raise RuntimeError(
                f"HELIUS_API_KEY is required for Solana trader {trader.name}"
            )
        return bootstrap_or_process_trader(trader, state)

    if chain in {"robinhood", "robinhood_chain", "rh"}:
        return bootstrap_or_process_robinhood_trader(trader, state)

    raise RuntimeError(
        f"Unsupported chain '{trader.chain}' for trader {trader.name}"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    traders = load_traders()
    state = load_state()

    has_solana = any(t.chain == "solana" for t in traders)
    has_robinhood = any(
        t.chain in {"robinhood", "robinhood_chain", "rh"}
        for t in traders
    )

    if has_solana and not HELIUS_API_KEY:
        raise RuntimeError(
            f"HELIUS_API_KEY is missing. Add it to {ENV_PATH}"
        )

    print("=" * 80)
    print("CryptoTracker Smart Money Monitor v2.2.1 CAMPAIGN STRENGTH")
    print("SOLANA/HELIUS + ROBINHOOD CHAIN DIRECT RPC")
    print("OBSERVATION ONLY - THIS SCRIPT CANNOT PLACE TRADES")
    print("=" * 80)
    print(f"Project root      : {PROJECT_ROOT}")
    print(f"Helius            : {'configured' if HELIUS_API_KEY else 'not configured'}")
    print(
        f"Robinhood RPC     : "
        f"{'enabled' if has_robinhood else 'not used'}"
    )
    print(f"Poll interval     : {POLL_SECONDS} seconds")
    print(f"Campaign reset    : {CAMPAIGN_RESET_MINUTES} minutes inactivity")
    print(f"Micro buy         : < ${MICRO_BUY_USD:,.0f}")
    print(f"Meaningful anchor : >= ${MEANINGFUL_BUY_USD:,.0f}")
    print(f"Signal-sized buy  : >= ${SIGNAL_MIN_BUY_USD:,.0f}")
    print(f"Accumulation win  : {ACCUMULATION_WINDOW_MINUTES} minutes")
    print(f"Convergence win   : {CONVERGENCE_WINDOW_MINUTES} minutes")
    print(f"Tracked           : {len(traders)} trader(s)")
    print("Samples           : " + ", ".join(f"+{m}m" for m in SAMPLE_MINUTES))
    print()
    print("v2.2 files:")
    print(f"  {EVENTS_CSV.name}")
    print(f"  {PERFORMANCE_CSV.name}")
    print(f"  {CAMPAIGNS_CSV.name}")
    print(f"  {WALLET_SCORECARD_CSV.name}")
    print()

    for trader in traders:
        suffix = f" [{trader.confidence}]" if trader.confidence else ""
        print(
            f"  {trader.name:<24} "
            f"@{trader.handle:<18} "
            f"{trader.chain:<10} {short(trader.wallet)}{suffix}"
        )

    print()
    print("Press Ctrl+C to stop.")
    print()

    while True:
        cycle_started = time.time()

        try:
            stamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{stamp}] Starting cycle")

            for trader in traders:
                try:
                    print(f"  Checking {trader.name} [{trader.chain}]...")
                    detected = process_trader(trader, state)
                    print(f"  {trader.name} complete ({detected} new buy(s))")
                except requests.HTTPError as exc:
                    print(
                        f"[{datetime.now().strftime('%H:%M:%S')}] "
                        f"HTTP error for {trader.name}: {exc}"
                    )
                except Exception as exc:
                    print(
                        f"[{datetime.now().strftime('%H:%M:%S')}] "
                        f"Trader error for {trader.name}: {exc}"
                    )

            print("  Checking due performance samples...")
            sample_due_events(state)
            print("  Performance sampling complete.")
            rebuild_wallet_scorecard()

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
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] "
            f"Cycle complete in {elapsed:.1f}s. Next cycle in {sleep_for:.1f}s."
        )
        print()

        try:
            time.sleep(sleep_for)
        except KeyboardInterrupt:
            print("\nStopped.")
            break


if __name__ == "__main__":
    main()
