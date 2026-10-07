"""
CryptoTracker V11.10 - Fair Multi-Model Paper Research + Executable Exit Evidence

Design goals:
- Quant data remains the primary entry decision-maker.
- Verified smart-money activity is the strongest confirmation layer.
- The 13-account social monitor is secondary confirmation, not an override.
- NORMAL and EARLY_ACCEL have separate position sizes.
- NORMAL requires stronger score acceleration (+35 by default).
- New entries stop after a +2% account-equity day; an open trade can be
  closed with a configurable buffer to crystallize the daily target.
- A percentage daily drawdown circuit breaker prevents quota chasing.
- V10.4 confirmed soft exits and runner behavior remain intact.
- 15-minute stagnant positions can exit when market-cap structure is weak.
- V11.1 cross-checks DEX Screener with GeckoTerminal before execution.
- V11.1 samples Jupiter round-trip execution twice and rejects anomalous quotes.
- Birdeye aggregate Smart Money and candidate-specific X activity add confirmation.
- Runner profit floors help keep genuine runners from fading back to near-flat exits.
- V11.5.1 disables continuous 13-influencer X polling; targeted Token-X remains on-demand.
- V11.5.2 observes Helius holder count/growth and market-cap-per-holder without changing entry gates.
- V11.5.3 carries market-cap + holder features into surge forward-performance research for later reassessment.
- V11.7 upgrades GPT-5.6 Luna from snapshot confirmation to a bounded momentum-pattern analyst after quant gates pass.
- V11.8 favors sustained acceleration, fixes evolving CSV schemas, improves EOD delivery, and protects mid-sized winners.

V11.9 runs protected multi-model paper research and cannot submit swaps while paper mode is authoritative.\n\nImportant: DAILY_TARGET_PCT is a target/lock, not a guaranteed return.
No trading strategy can reliably guarantee a positive return every day.
"""

import base64
import csv
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from dotenv import dotenv_values, load_dotenv
from solders.keypair import Keypair
from solders.message import to_bytes_versioned
from solders.signature import Signature
from solders.transaction import VersionedTransaction

import market_scanner_2 as ms
import paper_research_lab_v11_10 as paper_lab
import publish_daily_evidence as evidence_publisher


ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / ".env"
CONFIG_FILE = ROOT / ".env.config"

# Load committed non-secret settings first, then local secrets.
load_dotenv(CONFIG_FILE)
load_dotenv(ENV_FILE, override=True)

# Safety/research mode and EOD timing are repository-authoritative. A stale
# local .env may still provide secrets and optional local tuning, but it cannot
# reactivate real swaps or silently undo an approved reporting schedule.
_AUTHORITATIVE_CONFIG_KEYS = (
    "LIVE_TRADING",
    "PAPER_RESEARCH_ENABLED",
    "PAPER_RESEARCH_MAX_QUOTES_PER_CYCLE",
    "PAPER_RESEARCH_SHADOW_POSITIONS_PER_MODEL",
    "PAPER_RESEARCH_SHADOW_REENTRY_MINUTES",
    "PAPER_PROBE_TRADE_SIZE_USDC",
    "PAPER_EXTENDED_LIVE_5M_PCT",
    "PAPER_EXTENDED_LIVE_1H_PCT",
    "PAPER_EXTENDED_MIN_LIQUIDITY",
    "PAPER_EXTENDED_MIN_TX5",
    "PAPER_EXTENDED_MIN_QUANT",
    "PAPER_EXTENDED_MIN_VOLUME_ACCEL",
    "PAPER_EXTENDED_MIN_BUY_SELL",
    "PAPER_EXTENDED_MAX_5M_PCT",
    "PAPER_EXTENDED_MAX_1H_PCT",
    "PAPER_STAGE1_TAKE_PCT",
    "PAPER_STAGE1_FRACTION",
    "PAPER_STAGE2_TAKE_PCT",
    "PAPER_STAGE2_FRACTION",
    "PAPER_NOVELTY_MIN_SCORE",
    "PAPER_NOVELTY_MIN_LIQUIDITY",
    "PAPER_NOVELTY_MIN_TX5",
    "PAPER_NOVELTY_MIN_QUANT",
    "PAPER_NOVELTY_TREND_TERMS",
    "PAPER_NOVELTY_SHOCK_TERMS",
    "PAPER_NOVELTY_MEME_TERMS",
    "PAPER_EXIT_SCORE_BELOW",
    "PAPER_EXIT_DELTA_BELOW",
    "PAPER_EXIT_BUY_SELL_BELOW",
    "PAPER_EXIT_VOLUME_ACCEL_BELOW",
    "PAPER_EXIT_CONFIRMATIONS",
    "EVIDENCE_PUBLISH_ENABLED",
    "PUSHOVER_CRYPTO_EOD_ENABLED",
    "CRYPTO_EOD_TIMEZONE",
    "PUSHOVER_CRYPTO_EOD_HOUR",
    "PUSHOVER_CRYPTO_EOD_MINUTE",
    "CRYPTO_EOD_ONCE_DATE",
    "CRYPTO_EOD_ONCE_HOUR",
    "CRYPTO_EOD_ONCE_MINUTE",
    "HELIUS_ENABLED",
    "SOLANA_RPC_URL",
)
_config_values = dotenv_values(CONFIG_FILE)
for _key in _AUTHORITATIVE_CONFIG_KEYS:
    if _key in _config_values and _config_values[_key] is not None:
        os.environ[_key] = str(_config_values[_key])

DATA_DIR = ROOT / "data"
AUTO_SNAPSHOT_DIR = DATA_DIR / "auto_snapshots"
POSITION_FILE = DATA_DIR / "position.json"
COOLDOWN_FILE = DATA_DIR / "cooldowns.json"
DAILY_STATE_FILE = DATA_DIR / "daily_state_v11.json"
CRYPTO_EOD_STATE_FILE = DATA_DIR / "crypto_eod_report_state.json"

# Observation-only surge research. These files NEVER affect execution.
SURGE_FOLLOWUP_FILE = DATA_DIR / "surge_followup_log.csv"
SURGE_FOLLOWUP_AUDIT_FILE = DATA_DIR / "surge_followup_audit.csv"
SURGE_FOLLOWUP_STATE_FILE = DATA_DIR / "surge_followup_state.json"
SOCIAL_SENTIMENT_FILE = DATA_DIR / "social_sentiment_current.json"
CONFIRMATION_FEED_FILE = DATA_DIR / "confirmation_feed_log.csv"
CONFIRMATION_FEED_STATE_FILE = DATA_DIR / "confirmation_feed_state.json"
REACCEL_WATCH_FILE = DATA_DIR / "reacceleration_watch_v115.json"
REACCEL_LOG_FILE = DATA_DIR / "reacceleration_watch_log.csv"
DISCOVERY_SOURCE_LOG_FILE = DATA_DIR / "discovery_source_log.csv"
X_API_USAGE_FILE = DATA_DIR / "x_api_usage_log.csv"
HOLDER_METRICS_HISTORY_FILE = DATA_DIR / "holder_metrics_history.csv"
HOLDER_METRICS_LATEST_FILE = DATA_DIR / "holder_metrics_latest.json"
AI_CONFIRMATION_LOG_FILE = DATA_DIR / "ai_confirmation_log.csv"
AI_EOD_REVIEW_FILE = DATA_DIR / "ai_eod_review.json"
MISSED_OPPORTUNITY_AUDIT_FILE = DATA_DIR / "missed_opportunity_audit.csv"

# SmartMoneyMonitor v2.1 runs separately and remains observation-only.
# V10 reads its CSV outputs; it never controls or modifies the monitor.
SMART_MONEY_DIR = ROOT / "SmartMoneyMonitor" / "data"
SMART_MONEY_CAMPAIGNS_FILE_V22 = SMART_MONEY_DIR / "smart_money_campaigns_v22.csv"
SMART_MONEY_EVENTS_FILE_V22 = SMART_MONEY_DIR / "smart_money_events_v22.csv"
SMART_MONEY_CAMPAIGNS_FILE_V21 = SMART_MONEY_DIR / "smart_money_campaigns_v21.csv"
SMART_MONEY_EVENTS_FILE_V21 = SMART_MONEY_DIR / "smart_money_events_v21.csv"


def active_smart_money_campaigns_file():
    return (
        SMART_MONEY_CAMPAIGNS_FILE_V22
        if SMART_MONEY_CAMPAIGNS_FILE_V22.exists()
        else SMART_MONEY_CAMPAIGNS_FILE_V21
    )


def active_smart_money_events_file():
    return (
        SMART_MONEY_EVENTS_FILE_V22
        if SMART_MONEY_EVENTS_FILE_V22.exists()
        else SMART_MONEY_EVENTS_FILE_V21
    )


JUPITER_BASE = "https://api.jup.ag/swap/v2"
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
USDC_DECIMALS = 6
ZERO_SIGNATURE = Signature.default()

PUSHOVER_URL = "https://api.pushover.net/1/messages.json"
_ALERT_LAST_SENT = {}

# V11.1 short-lived in-process caches. These reduce paid/API traffic while keeping
# the trading loop responsive. None of these files or caches can place trades.
_BIRDEYE_SMART_CACHE = {"fetched_at": 0.0, "tokens": {}}
_TOKEN_SOCIAL_CACHE = {}
_GECKO_PRICE_CACHE = {}
_TOKEN_DECIMALS_CACHE = {}
_API_WARNING_LAST = {}
_GECKO_DISCOVERY_CACHE = {"fetched_at": 0.0, "tokens": []}
_HOLDER_METRICS_CACHE = {}
_AI_CONFIRMATION_CACHE = {}
_WALLET_USDC_BALANCE_CACHE = {"value": None, "fetched_at": 0.0}
_HELIUS_CIRCUIT = {"open_until": 0.0, "reason": "", "opened_at": 0.0, "alerted": False}

DEFAULTS = {
    "SCAN_INTERVAL_SECONDS": 60,

    # ----------------------------
    # Dedicated Crypto EOD Pushover report
    # ----------------------------
    "PUSHOVER_CRYPTO_EOD_ENABLED": 1,
    "PUSHOVER_CRYPTO_EOD_HOUR": 23,
    "PUSHOVER_CRYPTO_EOD_MINUTE": 55,

    # ----------------------------
    # V11 position sizing
    # ----------------------------
    # Fixed sizing is the default while the live model is still earning evidence.
    # Risk-based sizing is supported but intentionally OFF by default.
    "TRADE_SIZE_USDC": 1.50,  # backward-compatible alias for NORMAL
    "NORMAL_TRADE_SIZE_USDC": 1.50,
    "EARLY_ACCEL_TRADE_SIZE_USDC": 0.75,
    "USE_RISK_BASED_SIZING": 0,
    "NORMAL_RISK_PCT": 0.50,
    "EARLY_RISK_PCT": 0.25,
    "MIN_TRADE_SIZE_USDC": 0.50,
    "MAX_TRADE_SIZE_USDC": 3.00,
    "MAX_POSITION_PCT_EQUITY": 15.0,
    "CONFIRMATION_SIZE_BOOST_MAX_PCT": 25.0,
    "NEGATIVE_SOCIAL_SIZE_REDUCTION_PCT": 25.0,

    # Once discovered, keep scanning a token even after it drops out of
    # DEX Screener's latest/boosted discovery feeds.
    "PERSISTENT_WATCH_HOURS": 2.0,
    "UNIVERSE_RETENTION_HOURS": 24.0,
    "MAX_ACTIVE_SCAN_TOKENS": 100,

    # Protected Helius reliability controls.
    "WALLET_BALANCE_CACHE_SECONDS": 300,
    "HELIUS_MAX_RETRIES": 3,
    "HELIUS_BACKOFF_BASE_SECONDS": 1.0,
    "HELIUS_BACKOFF_MAX_SECONDS": 8.0,
    "HELIUS_CIRCUIT_BREAKER_SECONDS": 86400,

    # ----------------------------
    # V11.5 multi-source discovery
    # ----------------------------
    # Discovery broadens WHAT gets evaluated; it does not weaken any buy gate.
    "MULTISOURCE_DISCOVERY_ENABLED": 1,

    # Fresh verified SmartMoneyMonitor buys can inject a Solana mint directly
    # into the scanner even when DEX Screener discovery has not surfaced it yet.
    "WHALE_DISCOVERY_ENABLED": 1,
    "WHALE_DISCOVERY_MAX_AGE_MINUTES": 60,
    "WHALE_DISCOVERY_MIN_SPEND_USD": 50.0,
    "WHALE_DISCOVERY_MAX_TOKENS": 30,

    # Free GeckoTerminal new-pool discovery is best-effort and optional.
    "GECKO_DISCOVERY_ENABLED": 1,
    "GECKO_DISCOVERY_REFRESH_SECONDS": 300,
    "GECKO_DISCOVERY_MAX_TOKENS": 25,

    # ----------------------------
    # V11.5 reacceleration watch
    # ----------------------------
    # Extended tokens are WATCHED, not bought. They must later reset and pass
    # the existing NORMAL/EARLY quant rules before becoming eligible.
    "REACCEL_WATCH_ENABLED": 1,
    "REACCEL_WATCH_MAX_AGE_MINUTES": 120,
    "REACCEL_WATCH_MIN_SCORE": 60,
    "REACCEL_WATCH_MIN_DELTA": 35,
    "REACCEL_WATCH_MIN_LIQUIDITY": 40_000,
    "REACCEL_WATCH_MIN_5M_VOLUME": 750,
    "REACCEL_WATCH_MIN_VOLUME_ACCEL": 1.50,
    "REACCEL_WATCH_MIN_BUY_SELL_RATIO": 1.10,
    "REACCEL_WATCH_MIN_5M_TRANSACTIONS": 8,
    "REACCEL_PRIORITY_BONUS": 0.0,
    "REACCEL_PUSH_ENABLED": 1,

    # Nightly false-negative review generated from surge_followup_log.csv.
    "MISSED_OPPORTUNITY_REPORT_ENABLED": 1,
    "MISSED_OPPORTUNITY_MIN_30M_MFE_PCT": 20.0,
    "MISSED_OPPORTUNITY_MIN_60M_MFE_PCT": 50.0,

    # Observation-only surge follow-up research.
    "SURGE_FOLLOWUP_ENABLED": 1,
    "SURGE_FOLLOWUP_AUDIT_ENABLED": 1,
    "SURGE_SIGNAL_DEDUPE_MINUTES": 10,
    "SURGE_FOLLOWUP_MAX_MINUTES": 120,
    "SURGE_FOLLOWUP_POLL_MINUTES": 2,

    # ----------------------------
    # V11 external confirmation
    # ----------------------------
    # Social is intentionally capped and NEVER changes the quant gate.
    "SOCIAL_SENTIMENT_ENABLED": 0,
    "SOCIAL_SCORE_WEIGHT": 0.15,
    "SOCIAL_MAX_BONUS": 15.0,
    "SOCIAL_ECOSYSTEM_MULTIPLIER": 0.25,
    "SOCIAL_MAX_AGE_MINUTES": 15,

    # Persistent confirmation-source audit log. Best-effort only; never affects trades.
    "CONFIRMATION_FEED_LOG_ENABLED": 1,
    "CONFIRMATION_FEED_SURGING_ONLY": 1,
    "CONFIRMATION_FEED_DEDUPE_MINUTES": 5,

    "SURGE_PUSH_ENABLED": 1,
    "SURGE_PUSH_COOLDOWN_MINUTES": 10,

    # Smart money is stronger than social, but is still confirmatory only.
    # It can rank/sizemodulate an already-valid quant setup; it cannot bypass
    # liquidity, volume, anti-chase, transaction, score/delta, or Jupiter gates.
    "SMART_MONEY_ENABLED": 1,
    "SMART_MONEY_MAX_AGE_MINUTES": 15,
    "SMART_MONEY_MAX_BONUS": 25,
    "SMART_MONEY_MULTI_WHALE_BONUS": 10,
    # V11.1: repeated accumulation is no longer automatically rewarded.
    # First meaningful / large fresh buys matter more than late repeat buying.
    "SMART_MONEY_ACCUMULATION_BONUS": 0,

    # Birdeye aggregate Smart Money: optional, confirmation-only.
    "BIRDEYE_SMART_MONEY_ENABLED": 0,
    "BIRDEYE_SMART_MONEY_REFRESH_SECONDS": 300,
    "BIRDEYE_SMART_MONEY_MAX_BONUS": 15.0,
    "BIRDEYE_SMART_MONEY_MAX_PENALTY": 10.0,
    "BIRDEYE_MIN_SMART_TRADERS": 2,

    # Candidate-specific X search. Uses the existing X_BEARER_TOKEN.
    # Only the top quant-valid candidates are searched to control cost.
    "TOKEN_SOCIAL_ENABLED": 1,
    "TOKEN_SOCIAL_TOP_N": 2,
    "TOKEN_SOCIAL_LOOKBACK_MINUTES": 30,
    "TOKEN_SOCIAL_CACHE_SECONDS": 300,
    "TOKEN_SOCIAL_MAX_BONUS": 0.0,
    "TOKEN_SOCIAL_MIN_UNIQUE_AUTHORS": 2,
    "X_API_USAGE_LOG_ENABLED": 1,

    # ----------------------------
    # V11.5.2 holder / adoption metrics (observation-only)
    # ----------------------------
    # Helius getTokenAccounts is queried only for the most relevant live
    # candidates and the open position. Results are cached to control usage.
    "HOLDER_METRICS_ENABLED": 1,
    "HOLDER_METRICS_CACHE_SECONDS": 600,
    "HOLDER_METRICS_MAX_TOKENS_PER_CYCLE": 10,
    "HOLDER_METRICS_PAGE_LIMIT": 1000,
    "HOLDER_METRICS_MAX_PAGES": 10,
    "HOLDER_METRICS_HISTORY_RETENTION_HOURS": 48,
    "HOLDER_METRICS_ALERTS_ENABLED": 1,

    # ----------------------------
    # V11.6 GPT-5.6 Luna confirmation layer
    # ----------------------------
    # AI NEVER bypasses quant hard gates, never executes trades, and never
    # controls exits. It only nudges ranking/composite score among already-valid
    # SURGING candidates. The adjustment is deterministic and capped by code.
    "AI_CONFIRMATION_ENABLED": 1,
    "AI_CONFIRMATION_TOP_N": 2,
    "AI_CONFIRMATION_CACHE_SECONDS": 300,
    "AI_CONFIRMATION_MAX_BONUS": 5.0,
    "AI_HEALTHY_SURGE_MAX_BONUS": 8.0,
    "DELTA_RANK_MAX_BONUS": 5.0,
    "AI_CONFIRMATION_MIN_CONFIDENCE": 60,
    "AI_CONFIRMATION_HIGH_CONFIDENCE": 80,
    "AI_CONFIRMATION_REASONING_EFFORT": 1,  # V11.7: low reasoning for multi-signal pattern analysis
    "AI_EOD_REVIEW_ENABLED": 1,
    # SHADOW research only: link Luna decisions to 30/60/120m forward outcomes.
    "LUNA_OUTCOME_SCORECARD_ENABLED": 1,
    # SHADOW research only: diagnose false-negative report generation/coverage.
    "MISSED_OPPORTUNITY_AUDIT_ENABLED": 1,

    # ----------------------------
    # V11.1 execution-integrity gate
    # ----------------------------
    "EXECUTION_INTEGRITY_ENABLED": 1,
    "GECKOTERMINAL_ENABLED": 1,
    "EXEC_REQUIRE_GECKO_PRICE": 0,
    "EXEC_REQUIRE_JUPITER_PRICE_CONSENSUS": 0,
    "EXEC_MAX_DEX_GECKO_DIVERGENCE_PCT": 3.0,
    "EXEC_MAX_JUPITER_CONSENSUS_DIVERGENCE_PCT": 3.0,
    "EXEC_MAX_ROUNDTRIP_RETURN_PCT": 100.5,
    "EXEC_ROUNDTRIP_SAMPLES": 2,
    "EXEC_ROUNDTRIP_SAMPLE_DELAY_SECONDS": 2.0,
    "EXEC_MAX_ROUNDTRIP_SAMPLE_SPREAD_PCT": 2.0,

    # ----------------------------
    # V11 quant-first entry model
    # ----------------------------
    "MIN_BUY_SCORE": 80,
    "MIN_BUY_SCORE_DELTA": 20,
    "MIN_BUY_LIQUIDITY": 40_000,
    "MIN_BUY_5M_VOLUME": 2_000,
    "MIN_BUY_VOLUME_ACCEL": 1.50,
    "MIN_BUY_SELL_RATIO": 1.20,
    "MIN_BUY_5M_PCT": 1.00,
    "MAX_BUY_5M_PCT": 15.00,
    "MIN_BUY_1H_PCT": -10.00,
    "MAX_BUY_1H_PCT": 40.00,
    "MIN_5M_TRANSACTIONS": 15,

    # Smaller EARLY probe: less absolute activity is allowed only when
    # acceleration/flow is substantially stronger and extension is limited.
    "EARLY_ACCEL_MIN_SCORE": 60,
    "EARLY_ACCEL_MIN_SCORE_DELTA": 35,
    "EARLY_ACCEL_MIN_LIQUIDITY": 50_000,
    "EARLY_ACCEL_MIN_5M_VOLUME": 750,
    "EARLY_ACCEL_MIN_VOLUME_ACCEL": 2.50,
    "EARLY_ACCEL_MIN_BUY_SELL_RATIO": 1.40,
    "EARLY_ACCEL_MIN_5M_PCT": 1.00,
    "EARLY_ACCEL_MAX_5M_PCT": 10.00,
    "EARLY_ACCEL_MIN_1H_PCT": -10.00,
    "EARLY_ACCEL_MAX_1H_PCT": 30.00,
    "EARLY_ACCEL_MIN_5M_TRANSACTIONS": 15,
    # EARLY_ACCEL must persist across multiple scanner observations before entry.
    "EARLY_CONFIRM_MIN_POINTS": 3,
    "EARLY_CONFIRM_MIN_POSITIVE_FLOW_POINTS": 2,
    "EARLY_CONFIRM_MIN_RISING_SCORE_POINTS": 1,

    # Backward-compatible overall floor. V11.8 applies path-specific floors below.
    "MIN_ROUNDTRIP_RETURN_PCT": 97.0,
    "NORMAL_MIN_ROUNDTRIP_RETURN_PCT": 97.0,
    "EARLY_MIN_ROUNDTRIP_RETURN_PCT": 98.5,

    # ----------------------------
    # Exit / runner model
    # ----------------------------
    "STOP_LOSS_PCT": -6.0,
    "EMERGENCY_STOP_PCT": -12.0,
    "STOP_CONFIRMATIONS_REQUIRED": 2,
    "MAX_HOLD_MINUTES": 30,
    "EXTENDED_HOLD_MAX_MINUTES": 60,
    "EXTENDED_HOLD_MIN_PNL_PCT": -1.0,
    "EXTENDED_HOLD_MIN_SCORE": 60,
    "EXTENDED_HOLD_MIN_BUY_SELL_RATIO": 1.10,
    "RUNNER_MAX_HOLD_MINUTES": 120,

    "MOMENTUM_EXIT_GRACE_MINUTES": 10.0,
    "SOFT_EXIT_REQUIRE_MC_CONFIRMATION": 1,

    # At 15m, a non-runner with < +3% P/L can be recycled, but only when
    # rolling market-cap structure is actually weak.
    "STAGNANT_EXIT_MINUTES": 15.0,
    "STAGNANT_EXIT_MAX_PNL_PCT": 3.0,

    "RUNNER_ACTIVATE_PCT": 10.0,
    "RUNNER_DRAWDOWN_10_25_PCT": 8.0,
    "RUNNER_DRAWDOWN_25_50_PCT": 10.0,
    "RUNNER_DRAWDOWN_50_PLUS_PCT": 15.0,

    # Executable-P&L floors activate only after a trade has become a runner.
    # Two consecutive quote breaches are required by default to reduce noise exits.
    "RUNNER_PROFIT_FLOOR_10_PCT": 4.0,
    "RUNNER_PROFIT_FLOOR_20_PCT": 10.0,
    "RUNNER_PROFIT_FLOOR_30_PCT": 15.0,
    "RUNNER_PROFIT_FLOOR_50_PCT": 25.0,
    "RUNNER_FLOOR_CONFIRMATIONS_REQUIRED": 2,

    # Protect useful mid-sized moves before full runner mode.
    "PRE_RUNNER_PROTECT_ACTIVATE_PCT": 6.0,
    "PRE_RUNNER_PROFIT_FLOOR_PCT": 2.0,
    "PRE_RUNNER_FLOOR_CONFIRMATIONS_REQUIRED": 2,

    "MC_ROLLING_WINDOW_MINUTES": 5.0,

    "EXIT_SCORE_BELOW": 35,
    "EXIT_SCORE_DELTA_BELOW": -20,

    # ----------------------------
    # Account/day risk controls
    # ----------------------------
    # Target means "stop/lock when reached", never "force trades until reached".
    "DAILY_TARGET_PCT": 2.0,
    "DAILY_TARGET_LOCK_ENABLED": 1,
    "DAILY_TARGET_LOCK_BUFFER_PCT": 0.25,
    "MAX_DAILY_DRAWDOWN_PCT": 1.50,
    # Optional fallback when wallet RPC is unavailable. 0 = no fallback baseline.
    "DAILY_REFERENCE_CAPITAL_USDC": 0.0,

    "MAX_TRADES_PER_DAY": 6,
    # Legacy absolute backstop remains in addition to percentage drawdown.
    "DAILY_REALIZED_LOSS_LIMIT_USD": 3.00,
    "COOLDOWN_MINUTES": 20,

    # Re-entry remains extremely conservative.
    "ALLOW_STRONG_REENTRY": 1,
    "MAX_ENTRIES_PER_TOKEN_60M": 1,
    "REENTRY_MIN_SCORE": 120,
    "REENTRY_MIN_SCORE_DELTA": 35,
    "REENTRY_MIN_LIQUIDITY": 75_000,
    "REENTRY_MIN_5M_VOLUME": 10_000,
    "REENTRY_MIN_VOLUME_ACCEL": 1.75,
    "REENTRY_MIN_BUY_SELL_RATIO": 1.75,
    "REENTRY_MIN_5M_PCT": 2.00,
    "REENTRY_MAX_5M_PCT": 15.00,
    "REENTRY_MIN_1H_PCT": 10.00,
    "REENTRY_MAX_1H_PCT": 30.00,
    "REENTRY_MIN_5M_TRANSACTIONS": 15,
}


# ============================================================
# BASIC HELPERS
# ============================================================

def safe_number(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def pct_change(current, previous):
    if previous <= 0:
        return 0.0
    return ((current - previous) / previous) * 100.0


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def env_int(name, default):
    value = os.getenv(name)
    return int(value) if value is not None else int(default)


def env_float(name, default):
    value = os.getenv(name)
    return float(value) if value is not None else float(default)


def ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    AUTO_SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path, value):
    tmp = Path(str(path) + ".tmp")
    tmp.write_text(json.dumps(value, indent=2), encoding="utf-8")
    tmp.replace(path)

def _append_csv_schema_safe(path, fieldnames, row):
    """Append a CSV row while safely migrating an older header/schema.

    V11.8 fixes the research-log corruption that occurred when new columns were
    added to an existing CSV without rewriting its header. Existing values are
    preserved by column name where possible.
    """
    fieldnames = list(fieldnames)
    try:
        if path.exists() and path.stat().st_size > 0:
            with path.open("r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                existing_fields = reader.fieldnames or []
                existing_rows = list(reader)
            if existing_fields != fieldnames:
                backup = path.with_name(
                    f"{path.stem}.pre_v118_schema_{datetime.now():%Y%m%d_%H%M%S}{path.suffix}"
                )
                try:
                    path.replace(backup)
                except Exception:
                    backup = None
                with path.open("w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                    writer.writeheader()
                    for old in existing_rows:
                        writer.writerow({k: old.get(k, "") for k in fieldnames})
                if backup:
                    print(f"  CSV schema migrated: {path.name} | backup {backup.name}")
        exists = path.exists() and path.stat().st_size > 0
        with path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            if not exists:
                writer.writeheader()
            writer.writerow({k: row.get(k, "") for k in fieldnames})
        return True
    except Exception as exc:
        print(f"  CSV write warning ({path.name}): {exc}")
        return False


# ============================================================
# PUSHOVER ALERTS
# ============================================================

def personal_pushover_user_key():
    """Brian's personal Pushover user key."""
    return str(os.getenv("PUSHOVER_USER_KEY") or "").strip()


def movement_pushover_user_key():
    """
    Recipient for SURGE / BUY / SELL movement alerts.

    If a Delivery Group key is configured, Pushover's message API accepts that
    group key in the normal `user` field and delivers the alert to every active
    group member. If no group key is configured, preserve legacy behavior and
    fall back to the personal PUSHOVER_USER_KEY.
    """
    return str(
        os.getenv("PUSHOVER_CRYPTO_MOVEMENT_GROUP_KEY")
        or os.getenv("PUSHOVER_USER_KEY")
        or ""
    ).strip()


def personal_pushover_configured():
    return bool(
        personal_pushover_user_key()
        and str(os.getenv("PUSHOVER_API_TOKEN") or "").strip()
    )


def movement_pushover_configured():
    return bool(
        movement_pushover_user_key()
        and str(os.getenv("PUSHOVER_API_TOKEN") or "").strip()
    )


def pushover_configured():
    """Backward-compatible alias for personal/system alerts."""
    return personal_pushover_configured()


def send_pushover(
    title,
    message,
    priority=0,
    sound="pushover",
    audience="personal",
):
    """
    Best-effort alerting only.

    audience="movement":
        Uses PUSHOVER_CRYPTO_MOVEMENT_GROUP_KEY when configured, otherwise
        falls back to PUSHOVER_USER_KEY.

    audience="personal":
        Always uses PUSHOVER_USER_KEY.

    A Pushover failure must NEVER stop trading or change trade state.
    """
    api_token = str(os.getenv("PUSHOVER_API_TOKEN") or "").strip()
    if str(audience).lower() == "movement":
        user_key = movement_pushover_user_key()
    else:
        user_key = personal_pushover_user_key()

    if not user_key or not api_token:
        return False

    try:
        response = requests.post(
            PUSHOVER_URL,
            data={
                "token": api_token,
                "user": user_key,
                "title": str(title)[:250],
                "message": str(message)[:1024],
                "priority": int(priority),
                "sound": sound,
            },
            timeout=15,
        )

        if not response.ok:
            print(
                f"  PUSHOVER WARNING ({audience}): HTTP {response.status_code} "
                f"{response.text[:300]}"
            )
            return False

        return True

    except Exception as exc:
        print(f"  PUSHOVER WARNING ({audience}): {exc}")
        return False


def send_pushover_once(
    key,
    title,
    message,
    cooldown_seconds=900,
    priority=0,
    sound="pushover",
    audience="personal",
):
    """
    Prevents repeated transient errors/risk-limit messages from
    waking you every minute.
    """
    now = time.time()
    # Include audience in the in-memory de-dupe key so group and personal tests
    # never suppress one another.
    alert_key = f"{audience}:{key}"
    last = _ALERT_LAST_SENT.get(alert_key, 0)

    if now - last < cooldown_seconds:
        return False

    sent = send_pushover(
        title,
        message,
        priority=priority,
        sound=sound,
        audience=audience,
    )

    if sent:
        _ALERT_LAST_SENT[alert_key] = now

    return sent



def crypto_eod_timezone():
    """Timezone used only for the once-per-day CryptoTracker performance report."""
    name = str(os.getenv("CRYPTO_EOD_TIMEZONE") or "America/Los_Angeles").strip()
    try:
        return ZoneInfo(name)
    except Exception:
        return ZoneInfo("America/Los_Angeles")


def crypto_eod_recipient_candidates():
    """
    Ordered EOD recipients.

    Prefer the dedicated EOD Delivery Group, then a dedicated EOD user,
    then the normal personal Pushover user. Invalid/stale candidates are
    skipped automatically by send_crypto_eod_pushover().
    """
    raw = [
        ("EOD_GROUP", os.getenv("PUSHOVER_CRYPTO_EOD_GROUP_KEY")),
        ("EOD_USER", os.getenv("PUSHOVER_CRYPTO_EOD_USER_KEY")),
        ("PERSONAL_USER", os.getenv("PUSHOVER_USER_KEY")),
    ]
    out = []
    seen = set()
    for label, value in raw:
        key = str(value or "").strip()
        if key and key not in seen:
            out.append((label, key))
            seen.add(key)
    return out


def crypto_eod_recipient_key():
    """Backward-compatible accessor for the preferred EOD recipient."""
    candidates = crypto_eod_recipient_candidates()
    return candidates[0][1] if candidates else ""


def crypto_eod_token_candidates():
    """
    Ordered Pushover application tokens.

    Prefer the dedicated EOD application token. Fall back to the already
    working standard/movement application token when necessary.
    """
    raw = [
        ("EOD_APP", os.getenv("PUSHOVER_CRYPTO_EOD_TOKEN")),
        ("STANDARD_APP", os.getenv("PUSHOVER_API_TOKEN")),
    ]
    out = []
    seen = set()
    for label, value in raw:
        token = str(value or "").strip()
        if token and token not in seen:
            out.append((label, token))
            seen.add(token)
    return out


def crypto_eod_api_token():
    """Backward-compatible accessor for the preferred EOD app token."""
    candidates = crypto_eod_token_candidates()
    return candidates[0][1] if candidates else ""


def crypto_eod_pushover_configured():
    return bool(crypto_eod_recipient_candidates() and crypto_eod_token_candidates())


def _pushover_error_text(response):
    try:
        body = response.json()
        errors = body.get("errors") or []
        if isinstance(errors, list):
            return " | ".join(str(x) for x in errors)
    except Exception:
        pass
    return str(getattr(response, "text", "") or "")[:300]


def send_crypto_eod_pushover(title, message):
    """
    Reliable EOD Pushover routing.

    Tries the preferred EOD group first. If that identifier is stale/invalid,
    it automatically falls back to the dedicated EOD user and then the normal
    personal user. It also falls back from the dedicated EOD app token to the
    standard Pushover app token.

    The first successful route wins, preventing one bad group key from
    suppressing the nightly report.
    """
    recipients = crypto_eod_recipient_candidates()
    tokens = crypto_eod_token_candidates()

    if not recipients:
        print("  CRYPTO EOD PUSHOVER WARNING: no recipient keys configured.")
        return False
    if not tokens:
        print("  CRYPTO EOD PUSHOVER WARNING: no Pushover application token configured.")
        return False

    for recipient_label, user_key in recipients:
        invalid_recipient = False

        for token_label, api_token in tokens:
            try:
                response = requests.post(
                    PUSHOVER_URL,
                    data={
                        "token": api_token,
                        "user": user_key,
                        "title": str(title)[:250],
                        "message": str(message)[:1024],
                        "priority": 0,
                        "sound": "pushover",
                    },
                    timeout=15,
                )

                if response.ok:
                    print(
                        f"  CRYPTO EOD PUSHOVER SENT: "
                        f"{recipient_label} via {token_label}"
                    )
                    return True

                error_text = _pushover_error_text(response)
                print(
                    f"  CRYPTO EOD ROUTE FAILED: "
                    f"{recipient_label} via {token_label} | "
                    f"HTTP {response.status_code} | {error_text}"
                )

                lower_error = error_text.lower()
                if (
                    response.status_code == 400
                    and "user identifier is not valid" in lower_error
                ):
                    invalid_recipient = True
                    break

            except Exception as exc:
                print(
                    f"  CRYPTO EOD ROUTE ERROR: "
                    f"{recipient_label} via {token_label} | {exc}"
                )

        if invalid_recipient:
            print(
                f"  CRYPTO EOD: skipping invalid {recipient_label} "
                f"and trying the next configured recipient."
            )

    print("  CRYPTO EOD PUSHOVER FAILED: all configured routes were rejected.")
    return False


def test_crypto_eod_pushover():
    """
    Test the same resilient route used by the scheduled EOD report.
    This does not mark today's report as sent.
    """
    load_dotenv(ENV_FILE)

    recipients = crypto_eod_recipient_candidates()
    tokens = crypto_eod_token_candidates()

    if not recipients:
        print("CRYPTO EOD TEST FAILED: no group/user recipient key found.")
        return False
    if not tokens:
        print("CRYPTO EOD TEST FAILED: no EOD or standard Pushover app token is available.")
        return False

    now = datetime.now(crypto_eod_timezone())

    print("CRYPTO EOD TEST ROUTES:")
    print("  Recipients: " + " -> ".join(label for label, _ in recipients))
    print("  App tokens: " + " -> ".join(label for label, _ in tokens))

    sent = send_crypto_eod_pushover(
        "CryptoTracker — EOD TEST",
        "CryptoTracker V11.8.1 EOD fallback routing test.\n"
        f"Test time: {now.strftime('%Y-%m-%d %I:%M:%S %p %Z')}\n"
        "This test does not mark today's EOD report as sent.",
    )

    print("CRYPTO EOD TEST PASSED." if sent else "CRYPTO EOD TEST FAILED.")
    return sent


def test_eod_group_pushover():
    """
    Direct test of the Crypto EOD application -> EOD Delivery Group route.

    This intentionally requires PUSHOVER_CRYPTO_EOD_GROUP_KEY and does not
    fall back to a personal user key.
    """
    load_dotenv(ENV_FILE)

    group_key = str(os.getenv("PUSHOVER_CRYPTO_EOD_GROUP_KEY") or "").strip()
    api_token = str(os.getenv("PUSHOVER_CRYPTO_EOD_TOKEN") or "").strip()

    if not group_key:
        print(
            "EOD GROUP TEST FAILED: "
            "PUSHOVER_CRYPTO_EOD_GROUP_KEY is missing."
        )
        return False

    if not api_token:
        print(
            "EOD GROUP TEST FAILED: PUSHOVER_CRYPTO_EOD_TOKEN is missing."
        )
        return False

    try:
        response = requests.post(
            PUSHOVER_URL,
            data={
                "token": api_token,
                "user": group_key,
                "title": "CryptoTracker — EOD GROUP TEST",
                "message": (
                    "Crypto EOD Delivery Group is working.\n"
                    "Everyone subscribed to the EOD group should receive this test.\n"
                    "Scheduled Crypto EOD performance reports will use this group."
                ),
                "priority": 0,
                "sound": "pushover",
            },
            timeout=15,
        )

        print(f"EOD GROUP HTTP: {response.status_code}")
        print(f"EOD GROUP BODY: {response.text[:500]}")

        if response.ok:
            print("EOD GROUP TEST PASSED.")
            return True

        print("EOD GROUP TEST FAILED.")
        return False

    except Exception as exc:
        print(f"EOD GROUP TEST FAILED: {exc}")
        return False


def test_movement_group_pushover():
    """
    Direct test of the Crypto Movement application -> Delivery Group route.

    This requires PUSHOVER_CRYPTO_MOVEMENT_GROUP_KEY. It intentionally does
    NOT fall back to the personal user key, because the point of this test is
    to prove that the Delivery Group itself works.
    """
    load_dotenv(ENV_FILE)

    group_key = str(
        os.getenv("PUSHOVER_CRYPTO_MOVEMENT_GROUP_KEY") or ""
    ).strip()
    api_token = str(os.getenv("PUSHOVER_API_TOKEN") or "").strip()

    if not group_key:
        print(
            "MOVEMENT GROUP TEST FAILED: "
            "PUSHOVER_CRYPTO_MOVEMENT_GROUP_KEY is missing."
        )
        return False

    if not api_token:
        print(
            "MOVEMENT GROUP TEST FAILED: PUSHOVER_API_TOKEN is missing."
        )
        return False

    try:
        response = requests.post(
            PUSHOVER_URL,
            data={
                "token": api_token,
                "user": group_key,
                "title": "CryptoTracker — GROUP TEST",
                "message": (
                    "Crypto Movement Delivery Group is working.\n"
                    "Everyone subscribed to this group should receive this test.\n"
                    "SURGE / BUY / SELL alerts will use this group."
                ),
                "priority": 0,
                "sound": "pushover",
            },
            timeout=15,
        )

        print(f"MOVEMENT GROUP HTTP: {response.status_code}")
        print(f"MOVEMENT GROUP BODY: {response.text[:500]}")

        if response.ok:
            print("MOVEMENT GROUP TEST PASSED.")
            return True

        print("MOVEMENT GROUP TEST FAILED.")
        return False

    except Exception as exc:
        print(f"MOVEMENT GROUP TEST FAILED: {exc}")
        return False


def send_surging_alerts(candidates, settings):
    """
    Compact V11.5.4 SURGING alert.

    The title already carries token + state, so the body does not repeat it.
    Disabled/zero-value confirmation sources are omitted. Formatting only;
    trading behavior is unchanged.
    """
    if not pushover_configured():
        return
    if not bool(settings.get("SURGE_PUSH_ENABLED", 1)):
        return

    cooldown_seconds = max(
        60,
        int(float(settings.get("SURGE_PUSH_COOLDOWN_MINUTES", 10)) * 60),
    )

    for c in candidates:
        if str(c.get("momentum_state", "")).upper() != "SURGING":
            continue

        token = str(c.get("token_address", ""))
        symbol = str(c.get("symbol") or token[:8] or "UNKNOWN")
        tx5 = safe_number(c.get("buys_5m")) + safe_number(c.get("sells_5m"))

        reasons = entry_reasons(c, settings)
        eligible = not reasons

        quant_raw = safe_number(
            c.get("quant_score_raw", c.get("momentum_score"))
        )
        composite = safe_number(c.get("composite_score", quant_raw))

        entry_text = (
            f"ELIGIBLE {surge_entry_path(c, settings)}"
            if eligible
            else "REJECTED"
        )

        lines = [
            (
                f"Quant {quant_raw:.0f} ({safe_number(c.get('score_delta')):+.0f})"
                f" | Comp {composite:.0f} | {entry_text}"
            ),
            (
                f"5m {safe_number(c.get('price_5m')):+.1f}% | "
                f"1h {safe_number(c.get('price_1h')):+.1f}%"
            ),
        ]

        if bool(settings.get("HOLDER_METRICS_ALERTS_ENABLED", 1)):
            lines.extend(holder_alert_lines(c).splitlines())

        lines.append(
            f"Liq {_compact_usd(c.get('liquidity'))} | "
            f"Vol5 {_compact_usd(c.get('volume_5m'))} | "
            f"VolX {safe_number(c.get('volume_acceleration')):.2f}x"
        )
        lines.append(
            f"B/S {safe_number(c.get('buy_sell_ratio_5m')):.2f} | "
            f"Tx5 {tx5:.0f}"
        )

        confirm_parts = []
        whale_bonus = safe_number(c.get("whale_score_bonus"))
        token_x_bonus = safe_number(c.get("token_social_bonus"))
        if whale_bonus != 0:
            confirm_parts.append(f"Whale {whale_bonus:+.0f}")
        if token_x_bonus > 0:
            confirm_parts.append(f"X +{token_x_bonus:.0f}")

        ai_detail = c.get("ai_confirmation_detail") or {}
        ai_status = str(ai_detail.get("status") or "")
        if ai_status in {"OK", "CACHED"}:
            ai_assess = str(ai_detail.get("assessment") or "NEUTRAL")
            ai_conf = int(safe_number(ai_detail.get("confidence")))
            ai_bonus = safe_number(c.get("ai_confirmation_bonus"))
            confirm_parts.append(
                f"AI {ai_assess[:3]} {ai_conf}% {ai_bonus:+.0f}"
            )

        if confirm_parts:
            lines.append("Confirm: " + " | ".join(confirm_parts))

        scored_whales = [
            w for w in (c.get("whale_activity") or [])
            if safe_number(w.get("points")) > 0
        ]
        for w in scored_whales[:2]:
            trader = str(w.get("trader_name") or "Whale")
            spend = max(
                safe_number(w.get("largest_buy_usd")),
                safe_number(w.get("total_spend_usd")),
            )
            lines.append(
                f"{trader}: {_compact_usd(spend)} | "
                f"{safe_number(w.get('age_minutes')):.0f}m | "
                f"+{safe_number(w.get('points')):.0f}"
            )

        if reasons:
            lines.append(
                "Blocked: " + ", ".join(str(x) for x in reasons)
            )

        send_pushover_once(
            key=f"surging:{token}",
            title=f"SURGING: {symbol}",
            message="\n".join(lines),
            cooldown_seconds=cooldown_seconds,
            priority=0,
            sound="pushover",
            audience="movement",
        )



# ============================================================
# V11.5.2 HOLDER / ADOPTION METRICS — OBSERVATION ONLY
# ============================================================

HOLDER_HISTORY_FIELDS = [
    "observed_at",
    "symbol",
    "token_address",
    "holder_count",
    "holder_count_capped",
    "market_cap",
    "market_cap_per_holder",
    "pages_fetched",
]


def _compact_usd(value):
    value = safe_number(value)
    if value <= 0:
        return "n/a"
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:,.0f}"


def _format_token_price(value):
    """Readable token price for alerts across normal and micro-price tokens."""
    value = safe_number(value)
    if value <= 0:
        return "n/a"
    if value >= 1:
        return f"${value:,.4f}"
    if value >= 0.01:
        return f"${value:.6f}"
    if value >= 0.0001:
        return f"${value:.8f}"
    if value >= 0.000001:
        return f"${value:.10f}"
    return f"${value:.4e}"


def _holder_count_text(count, capped=False):
    count = int(safe_number(count))
    if count <= 0:
        return "n/a"
    return f"{count:,}+" if capped else f"{count:,}"


def _holder_delta_text(delta, pct):
    if delta in (None, ""):
        return "n/a"
    d = int(safe_number(delta))
    p = safe_number(pct)
    return f"{d:+,} ({p:+.1f}%)"


def _load_holder_history(token_address, retention_hours=48):
    if not HOLDER_METRICS_HISTORY_FILE.exists():
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=max(1, retention_hours))
    rows = []

    try:
        with HOLDER_METRICS_HISTORY_FILE.open("r", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if str(row.get("token_address") or "") != str(token_address):
                    continue
                dt = _parse_utc_any(row.get("observed_at"))
                if dt is None or dt < cutoff:
                    continue
                rows.append({
                    "dt": dt,
                    "holder_count": int(safe_number(row.get("holder_count"))),
                })
    except Exception as exc:
        print(f"  Holder-history warning: {exc}")

    rows.sort(key=lambda r: r["dt"])
    return rows


def _prior_holder_sample(history, now_utc, target_minutes):
    """
    Use the newest sample at least target_minutes old. With a 10-minute
    holder cache this produces stable 10m/30m comparisons without extra RPCs.
    """
    cutoff = now_utc - timedelta(minutes=target_minutes)
    eligible = [r for r in history if r["dt"] <= cutoff and r["holder_count"] > 0]
    return eligible[-1] if eligible else None


def _holder_change(current_count, prior):
    if not prior:
        return "", ""
    old = int(safe_number(prior.get("holder_count")))
    if old <= 0:
        return "", ""
    delta = int(current_count) - old
    pct = delta / old * 100.0
    return delta, pct


def _save_holder_latest(token_address, metrics):
    latest = load_json(HOLDER_METRICS_LATEST_FILE, {"tokens": {}})
    if not isinstance(latest, dict):
        latest = {"tokens": {}}
    latest.setdefault("tokens", {})
    latest["updated_at"] = datetime.now(timezone.utc).isoformat()
    latest["tokens"][str(token_address)] = metrics
    save_json(HOLDER_METRICS_LATEST_FILE, latest)


def _append_holder_history(metrics):
    exists = HOLDER_METRICS_HISTORY_FILE.exists()
    try:
        with HOLDER_METRICS_HISTORY_FILE.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=HOLDER_HISTORY_FIELDS)
            if not exists:
                writer.writeheader()
            writer.writerow({
                field: metrics.get(field, "")
                for field in HOLDER_HISTORY_FIELDS
            })
    except Exception as exc:
        print(f"  Holder-history write warning: {exc}")


def _helius_holder_count(token_address, settings):
    """
    Count unique positive-balance token-account owners using Helius
    getTokenAccounts. Helius pages at up to 1000 token accounts per call.

    If HOLDER_METRICS_MAX_PAGES is reached while pages remain full, the count
    is marked capped and shown as e.g. 10,000+ rather than pretending it is exact.
    """
    helius_key = str(os.getenv("HELIUS_API_KEY") or "").strip()
    if not helius_enabled(settings):
        return {
            "holder_count": 0,
            "holder_count_capped": False,
            "pages_fetched": 0,
            "status": "HELIUS_DISABLED",
        }
    if _helius_circuit_open():
        return {
            "holder_count": 0,
            "holder_count_capped": False,
            "pages_fetched": 0,
            "status": "HELIUS_CIRCUIT_OPEN",
        }
    if not helius_key:
        return {
            "holder_count": 0,
            "holder_count_capped": False,
            "pages_fetched": 0,
            "status": "NO_HELIUS_KEY",
        }

    limit = max(1, min(1000, int(settings.get("HOLDER_METRICS_PAGE_LIMIT", 1000))))
    max_pages = max(1, int(settings.get("HOLDER_METRICS_MAX_PAGES", 10)))
    owners = set()
    pages_fetched = 0
    capped = False

    url = f"https://mainnet.helius-rpc.com/?api-key={helius_key}"

    for page in range(1, max_pages + 1):
        payload = {
            "jsonrpc": "2.0",
            "id": f"holders-{token_address[:8]}-{page}",
            "method": "getTokenAccounts",
            "params": {
                "page": page,
                "limit": limit,
                "displayOptions": {},
                "mint": token_address,
            },
        }

        body = _helius_post_json(
            url,
            payload,
            timeout=25,
            settings=settings,
        )

        accounts = ((body.get("result") or {}).get("token_accounts") or [])
        if not accounts:
            break

        pages_fetched += 1

        for account in accounts:
            owner = str(account.get("owner") or "").strip()
            amount = safe_number(account.get("amount"))
            if owner and amount > 0:
                owners.add(owner)

        # A short page proves there are no additional pages.
        if len(accounts) < limit:
            break

        if page == max_pages:
            capped = True

    return {
        "holder_count": len(owners),
        "holder_count_capped": capped,
        "pages_fetched": pages_fetched,
        "status": "OK",
    }


def holder_metrics_for_token(token_address, symbol, market_cap, settings, force=False):
    """
    Return current holder count plus 10m/30m holder growth and market-cap/holder.
    This layer is observation-only: values are logged/displayed/alerted but never
    enter entry_reasons(), quant score, sizing, or exit decisions.
    """
    token_address = str(token_address or "").strip()
    if not token_address or not bool(settings.get("HOLDER_METRICS_ENABLED", 1)):
        return {}

    cache_seconds = max(60, int(settings.get("HOLDER_METRICS_CACHE_SECONDS", 600)))
    cached = _HOLDER_METRICS_CACHE.get(token_address)

    if (
        not force
        and cached
        and time.time() - safe_number(cached.get("fetched_at")) < cache_seconds
    ):
        result = dict(cached.get("metrics") or {})
        # Market cap changes every scan even while holder count is cached.
        mc = safe_number(market_cap)
        hc = int(safe_number(result.get("holder_count")))
        result["market_cap"] = mc
        result["market_cap_per_holder"] = (mc / hc) if mc > 0 and hc > 0 else 0.0
        return result

    now_utc = datetime.now(timezone.utc)
    retention = int(settings.get("HOLDER_METRICS_HISTORY_RETENTION_HOURS", 48))
    history = _load_holder_history(token_address, retention)

    try:
        raw = _helius_holder_count(token_address, settings)
    except Exception as exc:
        _warn_api_once(
            f"holder-metrics:{token_address}",
            f"Holder metrics warning for {symbol or token_address[:8]}: {exc}",
            900,
        )
        # A recent cached value is better than blanking the alert on one failed RPC.
        if cached:
            return dict(cached.get("metrics") or {})
        return {
            "holder_status": "ERROR",
            "holder_count": 0,
            "holder_count_capped": False,
            "holder_change_10m": "",
            "holder_change_10m_pct": "",
            "holder_change_30m": "",
            "holder_change_30m_pct": "",
            "market_cap": safe_number(market_cap),
            "market_cap_per_holder": 0.0,
        }

    count = int(safe_number(raw.get("holder_count")))
    prior10 = _prior_holder_sample(history, now_utc, 10)
    prior30 = _prior_holder_sample(history, now_utc, 30)
    d10, p10 = _holder_change(count, prior10)
    d30, p30 = _holder_change(count, prior30)

    # Once pagination is capped, count is only a lower bound; suppress growth
    # rather than imply false precision.
    if bool(raw.get("holder_count_capped")):
        d10 = p10 = d30 = p30 = ""

    mc = safe_number(market_cap)
    metrics = {
        "observed_at": now_utc.isoformat(),
        "symbol": str(symbol or ""),
        "token_address": token_address,
        "holder_status": raw.get("status", "OK"),
        "holder_count": count,
        "holder_count_capped": bool(raw.get("holder_count_capped")),
        "holder_change_10m": d10,
        "holder_change_10m_pct": p10,
        "holder_change_30m": d30,
        "holder_change_30m_pct": p30,
        "market_cap": mc,
        "market_cap_per_holder": (mc / count) if mc > 0 and count > 0 else 0.0,
        "pages_fetched": int(safe_number(raw.get("pages_fetched"))),
    }

    _append_holder_history(metrics)
    _save_holder_latest(token_address, metrics)
    _HOLDER_METRICS_CACHE[token_address] = {
        "fetched_at": time.time(),
        "metrics": metrics,
    }

    return metrics


def apply_holder_metrics(candidates, settings):
    """
    Enrich the most relevant live candidates only.

    Priority:
      1) SURGING
      2) REACCEL READY/WATCHING
      3) existing ranking order

    Holder metrics remain observation-only and do not affect ranking or trading.
    """
    if not bool(settings.get("HOLDER_METRICS_ENABLED", 1)):
        return candidates

    max_tokens = max(1, int(settings.get("HOLDER_METRICS_MAX_TOKENS_PER_CYCLE", 10)))

    priority = sorted(
        candidates,
        key=lambda c: (
            1 if str(c.get("momentum_state") or "").upper() == "SURGING" else 0,
            1 if c.get("reacceleration_ready") else 0,
            1 if c.get("reacceleration_watch") == "WATCHING" else 0,
            safe_number(c.get("momentum_score")),
        ),
        reverse=True,
    )

    enriched = 0
    for c in priority:
        interesting = (
            str(c.get("momentum_state") or "").upper() == "SURGING"
            or bool(c.get("reacceleration_ready"))
            or c.get("reacceleration_watch") == "WATCHING"
        )
        if not interesting:
            continue
        if enriched >= max_tokens:
            break

        metrics = holder_metrics_for_token(
            c.get("token_address"),
            c.get("symbol"),
            c.get("market_cap"),
            settings,
        )
        c.update(metrics)
        enriched += 1

    if enriched:
        print(f"  Holder metrics: enriched {enriched} candidate(s)")

    return candidates


def update_position_holder_metrics(position, settings):
    if not position or not bool(settings.get("HOLDER_METRICS_ENABLED", 1)):
        return position

    metrics = holder_metrics_for_token(
        position.get("token_address"),
        position.get("symbol"),
        position.get("current_market_cap"),
        settings,
    )
    if not metrics:
        return position

    position["current_holder_count"] = int(safe_number(metrics.get("holder_count")))
    position["current_holder_count_capped"] = bool(metrics.get("holder_count_capped"))
    position["holder_change_10m"] = metrics.get("holder_change_10m", "")
    position["holder_change_10m_pct"] = metrics.get("holder_change_10m_pct", "")
    position["holder_change_30m"] = metrics.get("holder_change_30m", "")
    position["holder_change_30m_pct"] = metrics.get("holder_change_30m_pct", "")
    position["current_market_cap_per_holder"] = safe_number(metrics.get("market_cap_per_holder"))
    return position


def holder_alert_lines(obj, market_cap_key="market_cap"):
    """
    Compact holder/adoption block used by SURGE / BUY / SELL alerts.
    """
    mc = safe_number(obj.get(market_cap_key))
    holders = int(safe_number(
        obj.get("holder_count", obj.get("current_holder_count"))
    ))
    capped = bool(
        obj.get("holder_count_capped", obj.get("current_holder_count_capped", False))
    )
    per_holder = safe_number(
        obj.get("market_cap_per_holder", obj.get("current_market_cap_per_holder"))
    )

    return (
        f"MC {_compact_usd(mc)} | Holders {_holder_count_text(holders, capped)} | "
        f"MC/H {_compact_usd(per_holder)}\n"
        f"HΔ 10m {_holder_delta_text(obj.get('holder_change_10m'), obj.get('holder_change_10m_pct'))} | "
        f"30m {_holder_delta_text(obj.get('holder_change_30m'), obj.get('holder_change_30m_pct'))}"
    )


# ============================================================
# CONFIG
# ============================================================

def load_settings():
    load_dotenv(ENV_FILE)

    settings = {}
    for key, default in DEFAULTS.items():
        if isinstance(default, int):
            settings[key] = env_int(key, default)
        else:
            settings[key] = env_float(key, default)

    settings["LIVE_TRADING"] = env_bool("LIVE_TRADING", False)
    settings["PAPER_RESEARCH_ENABLED"] = env_bool(
        "PAPER_RESEARCH_ENABLED",
        True,
    )

    api_key = os.getenv("JUPITER_API_KEY")
    private_key_text = os.getenv("SOLANA_BOT_PRIVATE_KEY")
    public_key = os.getenv("SOLANA_BOT_PUBLIC_KEY")

    missing = []
    if not api_key:
        missing.append("JUPITER_API_KEY")
    if not private_key_text:
        missing.append("SOLANA_BOT_PRIVATE_KEY")
    if not public_key:
        missing.append("SOLANA_BOT_PUBLIC_KEY")

    if missing:
        raise RuntimeError(
            "Missing required .env values: " + ", ".join(missing)
        )

    secret_bytes = bytes(
        int(part.strip())
        for part in private_key_text.split(",")
        if part.strip()
    )

    if len(secret_bytes) != 64:
        raise RuntimeError(
            "SOLANA_BOT_PRIVATE_KEY must contain a 64-byte keypair."
        )

    signer = Keypair.from_bytes(secret_bytes)

    if str(signer.pubkey()) != public_key:
        raise RuntimeError(
            "Private key does not match SOLANA_BOT_PUBLIC_KEY."
        )

    return settings, api_key, signer, public_key


# ============================================================
# COMPATIBLE SNAPSHOT / CROSS-SCAN IMPLEMENTATION
# ============================================================

SNAPSHOT_FIELDS = [
    "timestamp",
    "symbol",
    "name",
    "token_address",
    "pair_address",
    "dex",
    "price_usd",
    "market_cap",
    "liquidity",
    "volume_5m",
    "volume_1h",
    "volume_6h",
    "volume_24h",
    "price_5m",
    "price_1h",
    "price_6h",
    "price_24h",
    "buys_5m",
    "sells_5m",
    "buys_1h",
    "sells_1h",
    "buy_sell_ratio_5m",
    "buy_sell_ratio_1h",
    "volume_acceleration",
    "momentum_score",
    "elapsed_minutes",
    "score_delta",
    "price_delta_pct",
    "volume_delta_pct",
    "liquidity_delta_pct",
    "momentum_state",
    "pair_url",
]


def auto_snapshot_file():
    return AUTO_SNAPSHOT_DIR / f"{datetime.now():%Y-%m-%d}.csv"


def load_previous_snapshots():
    path = auto_snapshot_file()
    previous = {}

    if not path.exists():
        return previous

    try:
        with path.open("r", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                address = row.get("token_address")
                if address:
                    previous[address] = row
    except Exception as exc:
        print(f"  Snapshot read warning: {exc}")

    return previous


def calculate_cross_scan(current, previous):
    if not previous:
        return {
            "elapsed_minutes": 0.0,
            "score_delta": 0.0,
            "price_delta_pct": 0.0,
            "volume_delta_pct": 0.0,
            "liquidity_delta_pct": 0.0,
        }

    try:
        current_time = datetime.fromisoformat(current["timestamp"])
        previous_time = datetime.fromisoformat(previous["timestamp"])
        elapsed = (current_time - previous_time).total_seconds() / 60.0
    except Exception:
        elapsed = 0.0

    return {
        "elapsed_minutes": round(elapsed, 2),
        "score_delta": round(
            safe_number(current["momentum_score"])
            - safe_number(previous.get("momentum_score")),
            2,
        ),
        "price_delta_pct": round(
            pct_change(
                safe_number(current["price_usd"]),
                safe_number(previous.get("price_usd")),
            ),
            2,
        ),
        "volume_delta_pct": round(
            pct_change(
                safe_number(current["volume_5m"]),
                safe_number(previous.get("volume_5m")),
            ),
            2,
        ),
        "liquidity_delta_pct": round(
            pct_change(
                safe_number(current["liquidity"]),
                safe_number(previous.get("liquidity")),
            ),
            2,
        ),
    }


def classify_state(row):
    score = safe_number(row["momentum_score"])
    delta = safe_number(row["score_delta"])
    p5 = safe_number(row["price_5m"])
    p1 = safe_number(row["price_1h"])
    accel = safe_number(row["volume_acceleration"])
    ratio = safe_number(row["buy_sell_ratio_5m"])

    if (
        score >= 55
        and delta >= 15
        and p5 > 1
        and accel > 1.5
    ):
        return "SURGING"

    if delta <= -15:
        return "FADING"

    if p5 > 0 and p1 < -5:
        return "BOUNCE"

    if (
        score >= 70
        and p5 > 2
        and p1 > 5
        and accel > 1.5
        and ratio > 1.5
    ):
        return "STRONG"

    if score >= 40 and p5 > 0 and p1 > 0:
        return "BUILDING"

    if score >= 40:
        return "STEADY"

    return "NEUTRAL"


def append_auto_snapshot(row):
    path = auto_snapshot_file()
    exists = path.exists()

    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=SNAPSHOT_FIELDS,
            extrasaction="ignore",
        )
        if not exists:
            writer.writeheader()

        writer.writerow({
            field: row.get(field, "")
            for field in SNAPSHOT_FIELDS
        })


# ============================================================
# SURGE FOLLOW-UP RESEARCH (OBSERVATION ONLY)
# ============================================================

SURGE_SAMPLE_MINUTES = [1, 3, 5, 10, 15, 30, 45, 60, 90, 120]

SURGE_LOG_FIELDS = [
    "logged_at",
    "record_type",
    "signal_id",
    "symbol",
    "token_address",
    "pair_url",
    "signal_time",
    "signal_price_usd",
    "signal_score",
    "signal_score_delta",
    "signal_state",
    "signal_liquidity",
    "signal_market_cap",
    "signal_holder_count",
    "signal_holder_count_capped",
    "signal_market_cap_per_holder",
    "signal_holder_change_10m",
    "signal_holder_change_10m_pct",
    "signal_holder_change_30m",
    "signal_holder_change_30m_pct",
    "signal_ai_bonus",
    "signal_ai_assessment",
    "signal_ai_confidence",
    "signal_ai_risk_level",
    "signal_ai_contradiction_detected",
    "signal_ai_summary",
    "signal_volume_5m",
    "signal_volume_1h",
    "signal_volume_acceleration",
    "signal_buys_5m",
    "signal_sells_5m",
    "signal_buy_sell_ratio_5m",
    "signal_price_5m_pct",
    "signal_price_1h_pct",
    "signal_tx_5m",
    "entry_path",
    "local_entry_pass",
    "local_rejection_reasons",
    "cooldown_active",
    "strong_reentry_override",
    "configured_min_liquidity",
    "configured_min_5m_volume",
    "configured_min_volume_accel",
    "configured_min_buy_sell_ratio",
    "configured_min_5m_pct",
    "configured_max_5m_pct",
    "configured_min_1h_pct",
    "configured_max_1h_pct",
    "configured_min_5m_transactions",
    "horizon_minutes",
    "actual_elapsed_minutes",
    "sample_status",
    "sample_source",
    "sample_price_usd",
    "sample_market_cap",
    "sample_market_cap_return_pct",
    "sample_holder_count",
    "sample_holder_count_capped",
    "sample_holder_change_from_signal",
    "sample_holder_change_from_signal_pct",
    "sample_market_cap_per_holder",
    "sample_holder_observed_at",
    "return_pct",
    "mfe_pct",
    "mae_pct",
    "time_to_mfe_minutes",
    "time_to_mae_minutes",
]


SURGE_AUDIT_FIELDS = [
    "logged_at",
    "event",
    "signal_id",
    "symbol",
    "token_address",
    "entry_path",
    "local_entry_pass",
    "dedupe_minutes",
    "minutes_since_prior_signal",
    "horizon_minutes",
    "actual_elapsed_minutes",
    "sample_status",
    "sample_source",
    "detail",
]


def surge_audit_enabled(settings):
    return int(settings.get("SURGE_FOLLOWUP_AUDIT_ENABLED", 1)) != 0


def append_surge_audit(settings, event, **values):
    """Best-effort SHADOW audit. Never affects trading decisions or execution."""
    if not surge_audit_enabled(settings):
        return
    try:
        row = {field: "" for field in SURGE_AUDIT_FIELDS}
        row.update(values)
        row["logged_at"] = datetime.now().isoformat()
        row["event"] = str(event)
        _append_csv_schema_safe(SURGE_FOLLOWUP_AUDIT_FILE, SURGE_AUDIT_FIELDS, row)
    except Exception as exc:
        print(f"  Surge audit warning: {exc}")


def surge_research_enabled(settings):
    return int(settings.get("SURGE_FOLLOWUP_ENABLED", 1)) != 0


def append_surge_log(row):
    """Best-effort research logging only; V11.8 schema-safe."""
    _append_csv_schema_safe(SURGE_FOLLOWUP_FILE, SURGE_LOG_FIELDS, row)


def load_surge_state():
    state = load_json(
        SURGE_FOLLOWUP_STATE_FILE,
        {"signals": {}},
    )
    if not isinstance(state, dict):
        state = {"signals": {}}
    state.setdefault("signals", {})
    return state


def save_surge_state(state):
    save_json(SURGE_FOLLOWUP_STATE_FILE, state)


def _entry_path_checks(candidate, settings):
    """Return complete quant-only NORMAL and EARLY_ACCEL gate results."""
    tx5 = (
        safe_number(candidate.get("buys_5m"))
        + safe_number(candidate.get("sells_5m"))
    )
    quant_score = safe_number(
        candidate.get("quant_score_raw", candidate.get("momentum_score"))
    )

    normal = [
        (quant_score >= settings["MIN_BUY_SCORE"], "quant score too low"),
        (candidate["score_delta"] >= settings["MIN_BUY_SCORE_DELTA"], "score acceleration too low"),
        (candidate["liquidity"] >= settings["MIN_BUY_LIQUIDITY"], "liquidity too low"),
        (candidate["volume_5m"] >= settings["MIN_BUY_5M_VOLUME"], "5m volume too low"),
        (candidate["volume_acceleration"] >= settings["MIN_BUY_VOLUME_ACCEL"], "volume acceleration too low"),
        (candidate["buy_sell_ratio_5m"] >= settings["MIN_BUY_SELL_RATIO"], "buy/sell ratio too low"),
        (candidate["price_5m"] >= settings["MIN_BUY_5M_PCT"], "5m price too weak"),
        (candidate["price_5m"] <= settings["MAX_BUY_5M_PCT"], "5m price too extended"),
        (candidate["price_1h"] >= settings["MIN_BUY_1H_PCT"], "1h price too weak"),
        (candidate["price_1h"] <= settings["MAX_BUY_1H_PCT"], "1h price too extended"),
        (tx5 >= settings["MIN_5M_TRANSACTIONS"], "too few 5m transactions"),
    ]

    early = [
        (quant_score >= settings["EARLY_ACCEL_MIN_SCORE"], "quant score too low"),
        (candidate["score_delta"] >= settings["EARLY_ACCEL_MIN_SCORE_DELTA"], "score acceleration too low"),
        (candidate["liquidity"] >= settings["EARLY_ACCEL_MIN_LIQUIDITY"], "liquidity too low"),
        (candidate["volume_5m"] >= settings["EARLY_ACCEL_MIN_5M_VOLUME"], "5m volume too low"),
        (candidate["volume_acceleration"] >= settings["EARLY_ACCEL_MIN_VOLUME_ACCEL"], "volume acceleration too low"),
        (candidate["buy_sell_ratio_5m"] >= settings["EARLY_ACCEL_MIN_BUY_SELL_RATIO"], "buy/sell ratio too low"),
        (candidate["price_5m"] >= settings["EARLY_ACCEL_MIN_5M_PCT"], "5m price too weak"),
        (candidate["price_5m"] <= settings["EARLY_ACCEL_MAX_5M_PCT"], "5m price too extended"),
        (candidate["price_1h"] >= settings["EARLY_ACCEL_MIN_1H_PCT"], "1h price too weak"),
        (candidate["price_1h"] <= settings["EARLY_ACCEL_MAX_1H_PCT"], "1h price too extended"),
        (tx5 >= settings["EARLY_ACCEL_MIN_5M_TRANSACTIONS"], "too few 5m transactions"),
    ]

    return {
        "NORMAL": {"passed": all(p for p, _ in normal), "checks": normal},
        "EARLY_ACCEL": {"passed": all(p for p, _ in early), "checks": early},
    }


def surge_entry_path(candidate, settings):
    paths = _entry_path_checks(candidate, settings)
    if paths["NORMAL"]["passed"]:
        return "NORMAL"
    if paths["EARLY_ACCEL"]["passed"]:
        return "EARLY_ACCEL"
    return "NONE"


def surge_signal_base_row(signal):
    return {
        "signal_id": signal.get("signal_id", ""),
        "symbol": signal.get("symbol", ""),
        "token_address": signal.get("token_address", ""),
        "pair_url": signal.get("pair_url", ""),
        "signal_time": signal.get("signal_time", ""),
        "signal_price_usd": signal.get("signal_price_usd", ""),
        "signal_score": signal.get("signal_score", ""),
        "signal_score_delta": signal.get("signal_score_delta", ""),
        "signal_state": signal.get("signal_state", ""),
        "signal_liquidity": signal.get("signal_liquidity", ""),
        "signal_market_cap": signal.get("signal_market_cap", ""),
        "signal_holder_count": signal.get("signal_holder_count", ""),
        "signal_holder_count_capped": signal.get("signal_holder_count_capped", ""),
        "signal_market_cap_per_holder": signal.get("signal_market_cap_per_holder", ""),
        "signal_holder_change_10m": signal.get("signal_holder_change_10m", ""),
        "signal_holder_change_10m_pct": signal.get("signal_holder_change_10m_pct", ""),
        "signal_holder_change_30m": signal.get("signal_holder_change_30m", ""),
        "signal_holder_change_30m_pct": signal.get("signal_holder_change_30m_pct", ""),
        "signal_ai_bonus": signal.get("signal_ai_bonus", ""),
        "signal_ai_assessment": signal.get("signal_ai_assessment", ""),
        "signal_ai_confidence": signal.get("signal_ai_confidence", ""),
        "signal_ai_risk_level": signal.get("signal_ai_risk_level", ""),
        "signal_ai_contradiction_detected": signal.get("signal_ai_contradiction_detected", ""),
        "signal_ai_summary": signal.get("signal_ai_summary", ""),
        "signal_volume_5m": signal.get("signal_volume_5m", ""),
        "signal_volume_1h": signal.get("signal_volume_1h", ""),
        "signal_volume_acceleration": signal.get(
            "signal_volume_acceleration", ""
        ),
        "signal_buys_5m": signal.get("signal_buys_5m", ""),
        "signal_sells_5m": signal.get("signal_sells_5m", ""),
        "signal_buy_sell_ratio_5m": signal.get(
            "signal_buy_sell_ratio_5m", ""
        ),
        "signal_price_5m_pct": signal.get("signal_price_5m_pct", ""),
        "signal_price_1h_pct": signal.get("signal_price_1h_pct", ""),
        "signal_tx_5m": signal.get("signal_tx_5m", ""),
        "entry_path": signal.get("entry_path", ""),
        "local_entry_pass": signal.get("local_entry_pass", ""),
        "local_rejection_reasons": signal.get(
            "local_rejection_reasons", ""
        ),
        "cooldown_active": signal.get("cooldown_active", ""),
        "strong_reentry_override": signal.get(
            "strong_reentry_override", ""
        ),
        "configured_min_liquidity": signal.get(
            "configured_min_liquidity", ""
        ),
        "configured_min_5m_volume": signal.get(
            "configured_min_5m_volume", ""
        ),
        "configured_min_volume_accel": signal.get(
            "configured_min_volume_accel", ""
        ),
        "configured_min_buy_sell_ratio": signal.get(
            "configured_min_buy_sell_ratio", ""
        ),
        "configured_min_5m_pct": signal.get(
            "configured_min_5m_pct", ""
        ),
        "configured_max_5m_pct": signal.get(
            "configured_max_5m_pct", ""
        ),
        "configured_min_1h_pct": signal.get(
            "configured_min_1h_pct", ""
        ),
        "configured_max_1h_pct": signal.get(
            "configured_max_1h_pct", ""
        ),
        "configured_min_5m_transactions": signal.get(
            "configured_min_5m_transactions", ""
        ),
    }


def direct_token_market_snapshot(token_address):
    """
    Used only when a tracked surge is no longer present in the normal scan.
    This is read-only and never affects entry/exit decisions.

    V11.5.3 captures price + market cap from the SAME DEX request so forward
    performance can later be analyzed by both price return and MC trajectory.
    """
    pairs = ms.get_token_pairs(token_address)
    pair = ms.choose_best_pair(pairs)

    if not pair:
        return {
            "price_usd": 0.0,
            "market_cap": 0.0,
        }

    return {
        "price_usd": scanner_safe_number(pair.get("priceUsd")),
        "market_cap": scanner_safe_number(
            pair.get("marketCap") or pair.get("fdv")
        ),
    }


def direct_token_price(token_address):
    """Backward-compatible price-only wrapper."""
    return safe_number(
        direct_token_market_snapshot(token_address).get("price_usd")
    )


def register_surge_signals(candidates, settings):
    """
    Start a two-hour research window for SURGING candidates.

    To avoid creating 10 nearly identical signals during one continuous surge,
    the same token is deduped for SURGE_SIGNAL_DEDUPE_MINUTES. A later surge can
    therefore become a new independent signal.
    """
    if not surge_research_enabled(settings):
        return

    try:
        state = load_surge_state()
        now = datetime.now()
        dedupe_minutes = float(
            settings.get("SURGE_SIGNAL_DEDUPE_MINUTES", 10)
        )
        added = 0

        for candidate in candidates:
            if candidate.get("momentum_state") != "SURGING":
                continue

            token = candidate.get("token_address", "")
            if not token:
                continue

            append_surge_audit(
                settings,
                "CANDIDATE_SEEN",
                symbol=candidate.get("symbol", "?"),
                token_address=token,
                entry_path=surge_entry_path(candidate, settings),
                detail="SURGING candidate entered forward-outcome registration",
            )

            # Find the most recent signal for this token.
            most_recent = None
            for existing in state["signals"].values():
                if existing.get("token_address") != token:
                    continue
                try:
                    dt = datetime.fromisoformat(
                        existing.get("signal_time", "")
                    )
                except Exception:
                    continue
                if most_recent is None or dt > most_recent:
                    most_recent = dt

            minutes_since_prior_signal = (
                (now - most_recent).total_seconds() / 60.0
                if most_recent is not None else None
            )
            if (
                most_recent is not None
                and minutes_since_prior_signal < dedupe_minutes
            ):
                append_surge_audit(
                    settings,
                    "DEDUPED",
                    symbol=candidate.get("symbol", "?"),
                    token_address=token,
                    entry_path=surge_entry_path(candidate, settings),
                    dedupe_minutes=dedupe_minutes,
                    minutes_since_prior_signal=round(minutes_since_prior_signal, 3),
                    detail="Existing signal inside dedupe window; no new follow-up episode created",
                )
                continue

            failures = entry_reasons(candidate, settings)
            cooldown = cooldown_active(token, settings)
            reentry = (
                cooldown
                and strong_reentry_allowed(candidate, settings)
            )

            signal_id = (
                f"{token[:8]}-"
                f"{int(now.timestamp())}-"
                f"{int(safe_number(candidate.get('momentum_score')))}"
            )

            price = safe_number(candidate.get("price_usd"))

            # V11.5.3: make sure every deduped SURGING research episode has
            # holder/adoption features at signal time. This remains observation
            # only and cannot change entry_reasons(), ranking, or sizing.
            if (
                bool(settings.get("HOLDER_METRICS_ENABLED", 1))
                and not candidate.get("holder_count")
            ):
                candidate.update(
                    holder_metrics_for_token(
                        token,
                        candidate.get("symbol"),
                        candidate.get("market_cap"),
                        settings,
                    )
                )

            tx5 = (
                safe_number(candidate.get("buys_5m"))
                + safe_number(candidate.get("sells_5m"))
            )

            signal = {
                "signal_id": signal_id,
                "symbol": candidate.get("symbol", "?"),
                "token_address": token,
                "pair_url": candidate.get("pair_url", ""),
                "signal_time": now.isoformat(),
                "signal_price_usd": price,
                "signal_score": safe_number(
                    candidate.get("momentum_score")
                ),
                "signal_score_delta": safe_number(
                    candidate.get("score_delta")
                ),
                "signal_state": candidate.get(
                    "momentum_state", ""
                ),
                "signal_liquidity": safe_number(
                    candidate.get("liquidity")
                ),
                "signal_market_cap": safe_number(
                    candidate.get("market_cap")
                ),
                "signal_holder_count": int(
                    safe_number(candidate.get("holder_count"))
                ),
                "signal_holder_count_capped": 1
                    if candidate.get("holder_count_capped") else 0,
                "signal_market_cap_per_holder": safe_number(
                    candidate.get("market_cap_per_holder")
                ),
                "signal_holder_change_10m": candidate.get(
                    "holder_change_10m", ""
                ),
                "signal_holder_change_10m_pct": candidate.get(
                    "holder_change_10m_pct", ""
                ),
                "signal_holder_change_30m": candidate.get(
                    "holder_change_30m", ""
                ),
                "signal_holder_change_30m_pct": candidate.get(
                    "holder_change_30m_pct", ""
                ),
                "signal_ai_bonus": safe_number(
                    candidate.get("ai_confirmation_bonus")
                ),
                "signal_ai_assessment": str(
                    (candidate.get("ai_confirmation_detail") or {}).get(
                        "assessment", ""
                    )
                ),
                "signal_ai_confidence": int(
                    safe_number(
                        (candidate.get("ai_confirmation_detail") or {}).get(
                            "confidence"
                        )
                    )
                ),
                "signal_ai_risk_level": str(
                    (candidate.get("ai_confirmation_detail") or {}).get(
                        "risk_level", ""
                    )
                ),
                "signal_ai_contradiction_detected": int(
                    bool(
                        (candidate.get("ai_confirmation_detail") or {}).get(
                            "contradiction_detected"
                        )
                    )
                ),
                "signal_ai_summary": str(
                    (candidate.get("ai_confirmation_detail") or {}).get(
                        "summary", ""
                    )
                )[:300],
                "signal_volume_5m": safe_number(
                    candidate.get("volume_5m")
                ),
                "signal_volume_1h": safe_number(
                    candidate.get("volume_1h")
                ),
                "signal_volume_acceleration": safe_number(
                    candidate.get("volume_acceleration")
                ),
                "signal_buys_5m": safe_number(
                    candidate.get("buys_5m")
                ),
                "signal_sells_5m": safe_number(
                    candidate.get("sells_5m")
                ),
                "signal_buy_sell_ratio_5m": safe_number(
                    candidate.get("buy_sell_ratio_5m")
                ),
                "signal_price_5m_pct": safe_number(
                    candidate.get("price_5m")
                ),
                "signal_price_1h_pct": safe_number(
                    candidate.get("price_1h")
                ),
                "signal_tx_5m": tx5,
                "entry_path": surge_entry_path(
                    candidate, settings
                ),
                "local_entry_pass": 1 if not failures else 0,
                "local_rejection_reasons": "|".join(failures),
                "cooldown_active": 1 if cooldown else 0,
                "strong_reentry_override": 1 if reentry else 0,
                "configured_min_liquidity": settings[
                    "MIN_BUY_LIQUIDITY"
                ],
                "configured_min_5m_volume": settings[
                    "MIN_BUY_5M_VOLUME"
                ],
                "configured_min_volume_accel": settings[
                    "MIN_BUY_VOLUME_ACCEL"
                ],
                "configured_min_buy_sell_ratio": settings[
                    "MIN_BUY_SELL_RATIO"
                ],
                "configured_min_5m_pct": settings[
                    "MIN_BUY_5M_PCT"
                ],
                "configured_max_5m_pct": settings[
                    "MAX_BUY_5M_PCT"
                ],
                "configured_min_1h_pct": settings[
                    "MIN_BUY_1H_PCT"
                ],
                "configured_max_1h_pct": settings[
                    "MAX_BUY_1H_PCT"
                ],
                "configured_min_5m_transactions": settings[
                    "MIN_5M_TRANSACTIONS"
                ],
                "sampled_horizons": [],
                "mfe_pct": 0.0,
                "mae_pct": 0.0,
                "time_to_mfe_minutes": 0.0,
                "time_to_mae_minutes": 0.0,
                "last_price_check": now.isoformat(),
                "complete": False,
            }

            append_surge_audit(
                settings,
                "PATH_ASSIGNED",
                signal_id=signal_id,
                symbol=signal.get("symbol", "?"),
                token_address=token,
                entry_path=signal.get("entry_path", ""),
                local_entry_pass=signal.get("local_entry_pass", ""),
                detail="Quant-only entry path recorded for SHADOW outcome analysis",
            )

            state["signals"][signal_id] = signal
            append_surge_audit(
                settings,
                "SIGNAL_REGISTERED",
                signal_id=signal_id,
                symbol=signal.get("symbol", "?"),
                token_address=token,
                entry_path=signal.get("entry_path", ""),
                local_entry_pass=signal.get("local_entry_pass", ""),
                detail="Follow-up episode persisted to surge state",
            )

            row = surge_signal_base_row(signal)
            row.update({
                "logged_at": datetime.now().isoformat(),
                "record_type": "SIGNAL",
                "horizon_minutes": 0,
                "actual_elapsed_minutes": 0.0,
                "sample_status": "SIGNAL",
                "sample_source": "scanner",
                "sample_price_usd": price,
                "sample_market_cap": signal.get("signal_market_cap", ""),
                "sample_market_cap_return_pct": 0.0,
                "sample_holder_count": signal.get("signal_holder_count", ""),
                "sample_holder_count_capped": signal.get("signal_holder_count_capped", ""),
                "sample_holder_change_from_signal": 0
                    if signal.get("signal_holder_count") else "",
                "sample_holder_change_from_signal_pct": 0.0
                    if signal.get("signal_holder_count") else "",
                "sample_market_cap_per_holder": signal.get(
                    "signal_market_cap_per_holder", ""
                ),
                "sample_holder_observed_at": candidate.get("observed_at", ""),
                "return_pct": 0.0,
                "mfe_pct": 0.0,
                "mae_pct": 0.0,
                "time_to_mfe_minutes": 0.0,
                "time_to_mae_minutes": 0.0,
            })
            append_surge_log(row)
            added += 1

            print(
                f"  SURGE RESEARCH: tracking "
                f"{signal['symbol']} for 120m | "
                f"score {signal['signal_score']:.0f} "
                f"({signal['signal_score_delta']:+.0f}) | "
                f"{'LOCAL PASS' if signal['local_entry_pass'] else 'LOCAL REJECT'}"
            )

        if added:
            save_surge_state(state)

    except Exception as exc:
        print(f"  Surge research warning (register): {exc}")


def surge_sample_tolerance_minutes(horizon):
    # Prevent a restart hours later from pretending a 3-hour price was the +1m
    # sample. Short horizons get a small fixed tolerance; long horizons get 15%.
    return max(2.0, float(horizon) * 0.15)


def update_surge_followups(candidates, settings):
    """
    Update active surge signals.

    Prices already collected by the normal market scan are reused first.
    If a signal has fallen out of the normal candidate list, a direct DEX
    Screener lookup is made only when the research poll interval has elapsed.

    This function is intentionally isolated from trading logic. All errors are
    swallowed after printing a warning.
    """
    if not surge_research_enabled(settings):
        return

    try:
        state = load_surge_state()
        signals = state.get("signals", {})
        if not signals:
            return

        now = datetime.now()
        candidate_map = {
            c.get("token_address"): c
            for c in (candidates or [])
            if c.get("token_address")
        }
        changed = False
        active_count = 0
        max_minutes = float(
            settings.get("SURGE_FOLLOWUP_MAX_MINUTES", 120)
        )
        poll_minutes = max(
            1.0,
            float(settings.get("SURGE_FOLLOWUP_POLL_MINUTES", 2)),
        )

        for signal_id, signal in list(signals.items()):
            if signal.get("complete"):
                continue

            try:
                signal_time = datetime.fromisoformat(
                    signal["signal_time"]
                )
            except Exception:
                signal["complete"] = True
                changed = True
                continue

            elapsed = max(
                0.0,
                (now - signal_time).total_seconds() / 60.0,
            )

            if elapsed > max_minutes + 30:
                # Anything still missing after this point is explicitly marked
                # missed instead of being sampled at a misleading late price.
                pass

            active_count += 1
            token = signal.get("token_address", "")
            current_price = 0.0
            current_market_cap = 0.0
            current_holder_count = 0
            current_holder_capped = False
            current_holder_observed_at = ""
            current_market_cap_per_holder = 0.0
            sample_source = ""

            current_candidate = candidate_map.get(token)
            if current_candidate:
                current_price = safe_number(
                    current_candidate.get("price_usd")
                )
                current_market_cap = safe_number(
                    current_candidate.get("market_cap")
                )
                current_holder_count = int(
                    safe_number(current_candidate.get("holder_count"))
                )
                current_holder_capped = bool(
                    current_candidate.get("holder_count_capped")
                )
                current_holder_observed_at = str(
                    current_candidate.get("observed_at") or ""
                )
                current_market_cap_per_holder = safe_number(
                    current_candidate.get("market_cap_per_holder")
                )
                sample_source = "scanner"
            else:
                last_check_text = signal.get("last_price_check", "")
                try:
                    last_check = datetime.fromisoformat(
                        last_check_text
                    )
                    mins_since_check = (
                        now - last_check
                    ).total_seconds() / 60.0
                except Exception:
                    mins_since_check = 999.0

                due_horizon_exists = any(
                    h not in signal.get("sampled_horizons", [])
                    and elapsed >= h
                    for h in SURGE_SAMPLE_MINUTES
                )

                if (
                    mins_since_check >= poll_minutes
                    or due_horizon_exists
                ):
                    try:
                        market_snapshot = direct_token_market_snapshot(token)
                        current_price = safe_number(
                            market_snapshot.get("price_usd")
                        )
                        current_market_cap = safe_number(
                            market_snapshot.get("market_cap")
                        )
                        sample_source = "direct_dex"
                        signal["last_price_check"] = now.isoformat()
                        changed = True
                        # Small delay protects the public endpoint when several
                        # tracked signals need a direct lookup in one cycle.
                        time.sleep(min(scanner_request_delay(), 0.10))
                    except Exception as exc:
                        print(
                            f"  Surge research price warning "
                            f"{signal.get('symbol', '?')}: {exc}"
                        )

            # Reuse the latest already-observed holder sample. Do not create
            # extra Helius traffic solely for research follow-ups.
            if current_holder_count <= 0:
                holder_latest = load_json(
                    HOLDER_METRICS_LATEST_FILE,
                    {"tokens": {}},
                )
                try:
                    holder_row = (
                        holder_latest.get("tokens", {}).get(token, {})
                        if isinstance(holder_latest, dict)
                        else {}
                    )
                except Exception:
                    holder_row = {}

                if holder_row:
                    current_holder_count = int(
                        safe_number(holder_row.get("holder_count"))
                    )
                    current_holder_capped = bool(
                        holder_row.get("holder_count_capped")
                    )
                    current_holder_observed_at = str(
                        holder_row.get("observed_at") or ""
                    )
                    current_market_cap_per_holder = safe_number(
                        holder_row.get("market_cap_per_holder")
                    )

            # Recompute MC/holder using the current sample MC whenever both are
            # known, rather than leaving a stale ratio from the holder cache.
            if current_market_cap > 0 and current_holder_count > 0:
                current_market_cap_per_holder = (
                    current_market_cap / current_holder_count
                )

            signal_price = safe_number(
                signal.get("signal_price_usd")
            )
            signal_market_cap = safe_number(
                signal.get("signal_market_cap")
            )
            signal_holder_count = int(
                safe_number(signal.get("signal_holder_count"))
            )

            return_pct = None
            if current_price > 0 and signal_price > 0:
                return_pct = (
                    (current_price - signal_price)
                    / signal_price
                    * 100.0
                )

                if return_pct > safe_number(signal.get("mfe_pct")):
                    signal["mfe_pct"] = round(return_pct, 6)
                    signal["time_to_mfe_minutes"] = round(
                        elapsed, 3
                    )
                    changed = True

                if return_pct < safe_number(signal.get("mae_pct")):
                    signal["mae_pct"] = round(return_pct, 6)
                    signal["time_to_mae_minutes"] = round(
                        elapsed, 3
                    )
                    changed = True

            market_cap_return_pct = ""
            if current_market_cap > 0 and signal_market_cap > 0:
                market_cap_return_pct = (
                    (current_market_cap - signal_market_cap)
                    / signal_market_cap
                    * 100.0
                )

            holder_change_from_signal = ""
            holder_change_from_signal_pct = ""
            if (
                current_holder_count > 0
                and signal_holder_count > 0
                and not current_holder_capped
                and not bool(signal.get("signal_holder_count_capped"))
            ):
                holder_change_from_signal = (
                    current_holder_count - signal_holder_count
                )
                holder_change_from_signal_pct = (
                    holder_change_from_signal / signal_holder_count * 100.0
                )

            sampled = list(signal.get("sampled_horizons", []))

            for horizon in SURGE_SAMPLE_MINUTES:
                if horizon in sampled:
                    continue
                if elapsed < horizon:
                    continue

                tolerance = surge_sample_tolerance_minutes(horizon)

                if horizon in (30, 60, 120):
                    append_surge_audit(
                        settings,
                        "OUTCOME_DUE",
                        signal_id=signal_id,
                        symbol=signal.get("symbol", "?"),
                        token_address=token,
                        entry_path=signal.get("entry_path", ""),
                        local_entry_pass=signal.get("local_entry_pass", ""),
                        horizon_minutes=horizon,
                        actual_elapsed_minutes=round(elapsed, 3),
                        detail="Scheduled forward-outcome horizon is due",
                    )

                base_row = surge_signal_base_row(signal)
                base_row.update({
                    "logged_at": datetime.now().isoformat(),
                    "record_type": "SAMPLE",
                    "horizon_minutes": horizon,
                    "actual_elapsed_minutes": round(elapsed, 3),
                    "mfe_pct": round(
                        safe_number(signal.get("mfe_pct")), 6
                    ),
                    "mae_pct": round(
                        safe_number(signal.get("mae_pct")), 6
                    ),
                    "time_to_mfe_minutes": signal.get(
                        "time_to_mfe_minutes", ""
                    ),
                    "time_to_mae_minutes": signal.get(
                        "time_to_mae_minutes", ""
                    ),
                    "sample_market_cap": (
                        round(current_market_cap, 6)
                        if current_market_cap > 0 else ""
                    ),
                    "sample_market_cap_return_pct": (
                        round(market_cap_return_pct, 6)
                        if market_cap_return_pct != "" else ""
                    ),
                    "sample_holder_count": (
                        current_holder_count
                        if current_holder_count > 0 else ""
                    ),
                    "sample_holder_count_capped": (
                        1 if current_holder_capped else 0
                    ) if current_holder_count > 0 else "",
                    "sample_holder_change_from_signal": (
                        holder_change_from_signal
                    ),
                    "sample_holder_change_from_signal_pct": (
                        round(holder_change_from_signal_pct, 6)
                        if holder_change_from_signal_pct != "" else ""
                    ),
                    "sample_market_cap_per_holder": (
                        round(current_market_cap_per_holder, 6)
                        if current_market_cap_per_holder > 0 else ""
                    ),
                    "sample_holder_observed_at": current_holder_observed_at,
                })

                if elapsed <= horizon + tolerance and return_pct is not None:
                    base_row.update({
                        "sample_status": "OK",
                        "sample_source": sample_source,
                        "sample_price_usd": current_price,
                        "return_pct": round(return_pct, 6),
                    })
                elif elapsed > horizon + tolerance:
                    base_row.update({
                        "sample_status": "MISSED",
                        "sample_source": "",
                        "sample_price_usd": "",
                        "return_pct": "",
                    })
                else:
                    # Price lookup failed but we are still inside the allowed
                    # sampling window. Leave it pending and retry next cycle.
                    continue

                append_surge_log(base_row)
                if horizon in (30, 60, 120):
                    append_surge_audit(
                        settings,
                        "OUTCOME_CAPTURED" if base_row.get("sample_status") == "OK" else "OUTCOME_MISSED",
                        signal_id=signal_id,
                        symbol=signal.get("symbol", "?"),
                        token_address=token,
                        entry_path=signal.get("entry_path", ""),
                        local_entry_pass=signal.get("local_entry_pass", ""),
                        horizon_minutes=horizon,
                        actual_elapsed_minutes=round(elapsed, 3),
                        sample_status=base_row.get("sample_status", ""),
                        sample_source=base_row.get("sample_source", ""),
                        detail=(
                            "Forward outcome written to surge_followup_log.csv"
                            if base_row.get("sample_status") == "OK"
                            else "Horizon exceeded tolerance before a valid price sample was available"
                        ),
                    )
                sampled.append(horizon)
                signal["sampled_horizons"] = sampled
                changed = True

            if all(h in sampled for h in SURGE_SAMPLE_MINUTES):
                signal["complete"] = True
                changed = True
                append_surge_audit(
                    settings,
                    "SIGNAL_COMPLETE",
                    signal_id=signal_id,
                    symbol=signal.get("symbol", "?"),
                    token_address=token,
                    entry_path=signal.get("entry_path", ""),
                    local_entry_pass=signal.get("local_entry_pass", ""),
                    detail="All configured follow-up horizons are finalized",
                )
                print(
                    f"  SURGE RESEARCH COMPLETE: "
                    f"{signal.get('symbol', '?')} | "
                    f"MFE {safe_number(signal.get('mfe_pct')):+.1f}% | "
                    f"MAE {safe_number(signal.get('mae_pct')):+.1f}%"
                )

        # Keep completed signal state for six hours, then prune it. The CSV is
        # permanent, so pruning state cannot lose research history.
        prune_before = now - timedelta(hours=6)
        for signal_id, signal in list(signals.items()):
            if not signal.get("complete"):
                continue
            try:
                signal_time = datetime.fromisoformat(
                    signal.get("signal_time", "")
                )
            except Exception:
                signal_time = datetime.min
            if signal_time < prune_before:
                del signals[signal_id]
                changed = True

        if changed:
            state["signals"] = signals
            save_surge_state(state)

        if active_count:
            print(
                f"  Surge follow-up: {active_count} active signal(s)"
            )

    except Exception as exc:
        print(f"  Surge research warning (follow-up): {exc}")


# ============================================================
# TRADE STATE / LOGGING
# ============================================================

def load_position():
    return load_json(POSITION_FILE, None)


def save_position(position):
    save_json(POSITION_FILE, position)


def clear_position():
    if POSITION_FILE.exists():
        POSITION_FILE.unlink()


def trade_log_file():
    return DATA_DIR / f"trades_{datetime.now():%Y-%m-%d}.csv"


TRADE_FIELDS = [
    "timestamp",
    "action",
    "symbol",
    "token_address",
    "reason",
    "input_mint",
    "output_mint",
    "total_input_raw",
    "total_output_raw",
    "input_usd",
    "output_usd",
    "realized_pnl_usd",
    "score",
    "score_delta",
    "quant_score",
    "composite_score",
    "social_bonus",
    "whale_bonus",
    "birdeye_smart_bonus",
    "token_social_bonus",
    "token_social_unique_authors",
    "token_social_posts_10m",
    "ai_confirmation_bonus",
    "ai_assessment",
    "ai_confidence",
    "ai_risk_level",
    "ai_contradiction_detected",
    "ai_summary",
    "confidence_tier",
    "entry_path",
    "reacceleration_entry",
    "discovery_source",
    "trade_size_usdc",
    "daily_return_pct",
    "state",
    "roundtrip_preflight_pct",
    "roundtrip_sample_1_pct",
    "roundtrip_sample_2_pct",
    "dex_price_usd",
    "gecko_price_usd",
    "dex_gecko_divergence_pct",
    "jupiter_implied_price_usd",
    "jupiter_consensus_divergence_pct",
    "entry_market_cap",
    "exit_market_cap",
    "peak_market_cap",
    "mc_rolling_avg_5m",
    "mc_velocity_5m_pct",
    "entry_holder_count",
    "exit_holder_count",
    "entry_market_cap_per_holder",
    "exit_market_cap_per_holder",
    "holder_change_10m",
    "holder_change_10m_pct",
    "holder_change_30m",
    "holder_change_30m_pct",
    "runner_mode",
    "peak_pnl_pct",
    "router",
    "fee_bps",
    "signature",
]


def log_trade(row):
    path = trade_log_file()

    # V10.1 adds roundtrip_preflight_pct to the trade log. If today's CSV
    # was created by V10, migrate its header once so the new column does not
    # shift later rows out of alignment. Existing records are preserved.
    if path.exists():
        try:
            with path.open("r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                existing_fields = reader.fieldnames or []
                existing_rows = list(reader)

            if existing_fields != TRADE_FIELDS:
                tmp = Path(str(path) + ".tmp")
                with tmp.open("w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=TRADE_FIELDS)
                    writer.writeheader()
                    for existing in existing_rows:
                        writer.writerow({
                            field: existing.get(field, "")
                            for field in TRADE_FIELDS
                        })
                tmp.replace(path)
        except Exception as exc:
            raise RuntimeError(
                f"Could not migrate trade log schema: {exc}"
            ) from exc

    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=TRADE_FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerow({
            field: row.get(field, "")
            for field in TRADE_FIELDS
        })


def today_trade_stats():
    path = trade_log_file()

    if not path.exists():
        return 0, 0.0

    completed = 0
    realized = 0.0

    try:
        with path.open("r", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("action") == "SELL":
                    completed += 1
                    realized += safe_number(row.get("realized_pnl_usd"))
    except Exception:
        pass

    return completed, realized


def crypto_eod_trade_stats(settings):
    """Summarize today's completed CryptoTracker trades from the canonical CSV."""
    path = trade_log_file()
    rows = []
    if path.exists():
        try:
            with path.open("r", newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
        except Exception as exc:
            print(f"  Crypto EOD trade-log warning: {exc}")

    buys = [r for r in rows if str(r.get("action", "")).upper() == "BUY"]
    sells = [r for r in rows if str(r.get("action", "")).upper() == "SELL"]

    realized = sum(safe_number(r.get("realized_pnl_usd")) for r in sells)
    deployed = sum(safe_number(r.get("input_usd")) for r in sells)
    trade_return_pct = (realized / deployed * 100.0) if deployed > 0 else 0.0
    wins = sum(1 for r in sells if safe_number(r.get("realized_pnl_usd")) > 0)
    losses = sum(1 for r in sells if safe_number(r.get("realized_pnl_usd")) < 0)

    def row_return_pct(r):
        entry = safe_number(r.get("input_usd"))
        pnl = safe_number(r.get("realized_pnl_usd"))
        return (pnl / entry * 100.0) if entry > 0 else 0.0

    best = max(sells, key=row_return_pct) if sells else None
    worst = min(sells, key=row_return_pct) if sells else None

    runner_threshold = safe_number(settings.get("RUNNER_ACTIVATE_PCT", 10.0))
    runners = sum(
        1 for r in sells
        if str(r.get("runner_mode", "")).strip().lower() in {"1", "true", "yes"}
        or safe_number(r.get("peak_pnl_pct")) >= runner_threshold
    )

    normal_entries = sum(1 for r in buys if str(r.get("entry_path", "")).upper() == "NORMAL")
    early_entries = sum(1 for r in buys if str(r.get("entry_path", "")).upper() == "EARLY_ACCEL")
    whale_confirms = sum(1 for r in buys if safe_number(r.get("whale_bonus")) > 0)
    birdeye_confirms = sum(1 for r in buys if safe_number(r.get("birdeye_smart_bonus")) > 0)
    token_social_confirms = sum(1 for r in buys if safe_number(r.get("token_social_bonus")) > 0)
    macro_social_confirms = sum(1 for r in buys if safe_number(r.get("social_bonus")) > 0)

    return {
        "completed": len(sells),
        "realized": realized,
        "deployed": deployed,
        "trade_return_pct": trade_return_pct,
        "wins": wins,
        "losses": losses,
        "best": best,
        "worst": worst,
        "runners": runners,
        "normal_entries": normal_entries,
        "early_entries": early_entries,
        "whale_confirms": whale_confirms,
        "birdeye_confirms": birdeye_confirms,
        "token_social_confirms": token_social_confirms,
        "macro_social_confirms": macro_social_confirms,
        "row_return_pct": row_return_pct,
    }



MISSED_OPPORTUNITY_FIELDS = [
    "report_date",
    "symbol",
    "token_address",
    "signal_time",
    "signal_score",
    "signal_score_delta",
    "signal_market_cap",
    "signal_holder_count",
    "signal_market_cap_per_holder",
    "signal_holder_change_10m_pct",
    "signal_holder_change_30m_pct",
    "rejection_reasons",
    "mfe_30m_pct",
    "return_30m_pct",
    "mfe_60m_pct",
    "return_60m_pct",
    "mae_60m_pct",
    "missed_20_in_30m",
    "missed_50_in_60m",
]


def generate_missed_opportunity_report(settings, report_date=None):
    """
    Nightly false-negative review from the existing observation-only surge log.

    Uses MFE because the question is "did a rejected signal later offer a large
    move?", not merely where price happened to be exactly at the horizon.
    """
    if not bool(settings.get("MISSED_OPPORTUNITY_REPORT_ENABLED", 1)):
        return {
            "rejected_signals": 0,
            "missed_20_30": 0,
            "missed_50_60": 0,
            "best": None,
        }

    report_date = report_date or datetime.now(crypto_eod_timezone()).date().isoformat()
    out_path = DATA_DIR / f"missed_opportunities_{report_date}.csv"

    signals = {}
    samples = {}

    if not SURGE_FOLLOWUP_FILE.exists():
        return {
            "rejected_signals": 0,
            "missed_20_30": 0,
            "missed_50_60": 0,
            "best": None,
        }

    try:
        with SURGE_FOLLOWUP_FILE.open("r", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                signal_time = str(row.get("signal_time") or "")
                if not signal_time.startswith(report_date):
                    continue

                signal_id = str(row.get("signal_id") or "")
                if not signal_id:
                    continue

                if str(row.get("record_type") or "").upper() == "SIGNAL":
                    if int(safe_number(row.get("local_entry_pass"))) != 0:
                        continue
                    signals[signal_id] = row
                elif str(row.get("record_type") or "").upper() == "SAMPLE":
                    horizon = int(safe_number(row.get("horizon_minutes")))
                    if horizon in (30, 60) and str(row.get("sample_status") or "").upper() == "OK":
                        samples[(signal_id, horizon)] = row

    except Exception as exc:
        print(f"  Missed-opportunity report warning: {exc}")
        return {
            "rejected_signals": 0,
            "missed_20_30": 0,
            "missed_50_60": 0,
            "best": None,
        }

    threshold30 = float(settings.get("MISSED_OPPORTUNITY_MIN_30M_MFE_PCT", 20.0))
    threshold60 = float(settings.get("MISSED_OPPORTUNITY_MIN_60M_MFE_PCT", 50.0))

    # One representative rejected signal per token/day, selecting the signal
    # with the largest known 60m (or 30m) MFE. This avoids counting one
    # continuous surge ten times.
    per_token = {}

    for signal_id, sig in signals.items():
        s30 = samples.get((signal_id, 30))
        s60 = samples.get((signal_id, 60))
        if not s30 and not s60:
            continue

        mfe30 = safe_number((s30 or {}).get("mfe_pct"))
        ret30 = safe_number((s30 or {}).get("return_pct"))
        mfe60 = safe_number((s60 or {}).get("mfe_pct"))
        ret60 = safe_number((s60 or {}).get("return_pct"))
        mae60 = safe_number((s60 or s30 or {}).get("mae_pct"))

        token = str(sig.get("token_address") or signal_id)
        score_key = max(mfe60, mfe30)

        record = {
            "report_date": report_date,
            "symbol": sig.get("symbol", "?"),
            "token_address": sig.get("token_address", ""),
            "signal_time": sig.get("signal_time", ""),
            "signal_score": safe_number(sig.get("signal_score")),
            "signal_score_delta": safe_number(sig.get("signal_score_delta")),
            "signal_market_cap": safe_number(sig.get("signal_market_cap")),
            "signal_holder_count": int(
                safe_number(sig.get("signal_holder_count"))
            ),
            "signal_market_cap_per_holder": safe_number(
                sig.get("signal_market_cap_per_holder")
            ),
            "signal_holder_change_10m_pct": sig.get(
                "signal_holder_change_10m_pct", ""
            ),
            "signal_holder_change_30m_pct": sig.get(
                "signal_holder_change_30m_pct", ""
            ),
            "rejection_reasons": sig.get("local_rejection_reasons", ""),
            "mfe_30m_pct": mfe30,
            "return_30m_pct": ret30,
            "mfe_60m_pct": mfe60,
            "return_60m_pct": ret60,
            "mae_60m_pct": mae60,
            "missed_20_in_30m": 1 if mfe30 >= threshold30 else 0,
            "missed_50_in_60m": 1 if mfe60 >= threshold60 else 0,
            "_score_key": score_key,
        }

        old = per_token.get(token)
        if old is None or score_key > old["_score_key"]:
            per_token[token] = record

    rows = sorted(
        per_token.values(),
        key=lambda r: r["_score_key"],
        reverse=True,
    )

    try:
        with out_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=MISSED_OPPORTUNITY_FIELDS)
            writer.writeheader()
            for row in rows:
                writer.writerow({
                    field: row.get(field, "")
                    for field in MISSED_OPPORTUNITY_FIELDS
                })
    except Exception as exc:
        print(f"  Missed-opportunity CSV warning: {exc}")

    best = rows[0] if rows else None
    summary = {
        "rejected_signals": len(rows),
        "missed_20_30": sum(int(r["missed_20_in_30m"]) for r in rows),
        "missed_50_60": sum(int(r["missed_50_in_60m"]) for r in rows),
        "best": best,
        "path": str(out_path),
    }

    if rows:
        print(
            f"  False-negative review: {len(rows)} rejected token(s) | "
            f"+20% MFE/30m {summary['missed_20_30']} | "
            f"+50% MFE/60m {summary['missed_50_60']}"
        )

    return summary



MISSED_OPPORTUNITY_AUDIT_FIELDS = [
    "logged_at",
    "report_date",
    "source_exists",
    "signal_rows",
    "rejected_signal_rows",
    "sample_30_rows",
    "sample_60_rows",
    "usable_rejected_signals",
    "report_exists",
    "threshold_30m_mfe_pct",
    "threshold_60m_mfe_pct",
    "status",
    "detail",
]


def audit_missed_opportunity_pipeline(settings, report_date=None):
    """SHADOW-only audit of the false-negative evidence pipeline."""
    if not bool(settings.get("MISSED_OPPORTUNITY_AUDIT_ENABLED", 1)):
        return {}

    report_date = report_date or datetime.now(crypto_eod_timezone()).date().isoformat()
    report_path = DATA_DIR / f"missed_opportunities_{report_date}.csv"

    signal_rows = 0
    rejected_signal_rows = 0
    sample_30_rows = 0
    sample_60_rows = 0
    usable_ids = set()
    rejected_ids = set()
    samples_by_id = set()
    source_exists = SURGE_FOLLOWUP_FILE.exists()

    if source_exists:
        try:
            with SURGE_FOLLOWUP_FILE.open("r", newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    if not str(row.get("signal_time") or "").startswith(report_date):
                        continue
                    signal_id = str(row.get("signal_id") or "")
                    record_type = str(row.get("record_type") or "").upper()
                    if record_type == "SIGNAL":
                        signal_rows += 1
                        if int(safe_number(row.get("local_entry_pass"))) == 0:
                            rejected_signal_rows += 1
                            if signal_id:
                                rejected_ids.add(signal_id)
                    elif record_type == "SAMPLE":
                        horizon = int(safe_number(row.get("horizon_minutes")))
                        ok = str(row.get("sample_status") or "").upper() == "OK"
                        if horizon == 30:
                            sample_30_rows += 1
                        elif horizon == 60:
                            sample_60_rows += 1
                        if signal_id and horizon in (30, 60) and ok:
                            samples_by_id.add(signal_id)
        except Exception as exc:
            detail = f"read_error: {exc}"
        else:
            detail = ""
    else:
        detail = "surge_followup_log.csv not present"

    usable_ids = rejected_ids.intersection(samples_by_id)

    if not source_exists:
        status = "NO_SOURCE_LOG"
    elif rejected_signal_rows == 0:
        status = "VALID_ZERO_REJECTED_SIGNALS"
    elif not usable_ids:
        status = "MISSING_FORWARD_HORIZONS"
    elif report_path.exists():
        status = "REPORT_AVAILABLE"
    else:
        status = "REPORT_MISSING_WITH_USABLE_DATA"

    row = {
        "logged_at": datetime.now().isoformat(),
        "report_date": report_date,
        "source_exists": 1 if source_exists else 0,
        "signal_rows": signal_rows,
        "rejected_signal_rows": rejected_signal_rows,
        "sample_30_rows": sample_30_rows,
        "sample_60_rows": sample_60_rows,
        "usable_rejected_signals": len(usable_ids),
        "report_exists": 1 if report_path.exists() else 0,
        "threshold_30m_mfe_pct": float(
            settings.get("MISSED_OPPORTUNITY_MIN_30M_MFE_PCT", 20.0)
        ),
        "threshold_60m_mfe_pct": float(
            settings.get("MISSED_OPPORTUNITY_MIN_60M_MFE_PCT", 50.0)
        ),
        "status": status,
        "detail": detail[:300],
    }
    _append_csv_schema_safe(
        MISSED_OPPORTUNITY_AUDIT_FILE,
        MISSED_OPPORTUNITY_AUDIT_FIELDS,
        row,
    )
    print(
        f"  Missed-opportunity audit: {status} | "
        f"rejected={rejected_signal_rows} usable={len(usable_ids)}"
    )
    return row


def maybe_send_crypto_eod_report(settings, api_key, wallet_address, force=False):
    """
    Send exactly one Crypto EOD performance report per Pacific calendar day.
    force=True bypasses time/de-duplication for a manual test and does not
    consume the scheduled report for tonight.
    """
    if not bool(settings.get("PUSHOVER_CRYPTO_EOD_ENABLED", 1)):
        return False
    if not crypto_eod_pushover_configured():
        _warn_api_once(
            "eod-route-missing",
            "Crypto EOD inactive: configure an EOD group/user key and either PUSHOVER_CRYPTO_EOD_TOKEN or PUSHOVER_API_TOKEN.",
            3600,
        )
        return False

    now = datetime.now(crypto_eod_timezone())
    hour = int(settings.get("PUSHOVER_CRYPTO_EOD_HOUR", 23))
    minute = int(settings.get("PUSHOVER_CRYPTO_EOD_MINUTE", 55))
    report_date = now.date().isoformat()
    state = load_json(CRYPTO_EOD_STATE_FILE, {})

    # Repository-triggered one-time EOD. This lets an approved remote request
    # run the full local analysis immediately without permanently moving the
    # recurring 8 PM schedule or allowing arbitrary remote commands.
    once_date = str(os.getenv("CRYPTO_EOD_ONCE_DATE") or "").strip()
    try:
        once_hour = int(os.getenv("CRYPTO_EOD_ONCE_HOUR", str(hour)))
        once_minute = int(os.getenv("CRYPTO_EOD_ONCE_MINUTE", str(minute)))
    except Exception:
        once_hour, once_minute = hour, minute
    once_key = f"{once_date}T{once_hour:02d}:{once_minute:02d}"
    manual_once_due = (
        bool(once_date)
        and once_date == report_date
        and (now.hour, now.minute) >= (once_hour, once_minute)
        and state.get("manual_once_key") != once_key
    )

    if not force and not manual_once_due and (now.hour, now.minute) < (hour, minute):
        return False
    if (
        not force
        and not manual_once_due
        and state.get("last_sent_date") == report_date
    ):
        return False

    stats = crypto_eod_trade_stats(settings)
    position = load_position()
    wallet_cash = wallet_usdc_balance(wallet_address)
    liquidation = None
    current_equity = wallet_cash

    if position and wallet_cash is not None:
        try:
            liquidation = jupiter_liquidation_value_usdc(
                api_key,
                position["token_address"],
                position["raw_token_amount"],
            )
            current_equity = wallet_cash + liquidation
        except Exception as exc:
            print(f"  Crypto EOD open-position valuation warning: {exc}")

    day_status = daily_account_status(settings, current_equity)
    account_return = day_status.get("return_pct")

    lines = [
        f"Account day: {account_return:+.2f}%" if account_return is not None else "Account day: unavailable",
        f"Realized: ${stats['realized']:+.4f} | Trade return: {stats['trade_return_pct']:+.2f}%",
        f"Completed: {stats['completed']} | W/L: {stats['wins']}/{stats['losses']}",
    ]

    if stats["completed"]:
        best = stats["best"]
        worst = stats["worst"]
        lines.append(
            f"Best: {best.get('symbol', '?')} {stats['row_return_pct'](best):+.2f}% | "
            f"Worst: {worst.get('symbol', '?')} {stats['row_return_pct'](worst):+.2f}%"
        )
        lines.append(
            f"Runners: {stats['runners']} | Entries N/E: "
            f"{stats['normal_entries']}/{stats['early_entries']}"
        )
        lines.append(
            f"Confirmations W/B/X/M: {stats['whale_confirms']}/"
            f"{stats['birdeye_confirms']}/{stats['token_social_confirms']}/"
            f"{stats['macro_social_confirms']}"
        )
    else:
        lines.append("No completed trades today.")

    x_usage = x_api_daily_stats(report_date)
    lines.append(
        f"Targeted X: {x_usage['requests']} req | "
        f"{x_usage['hits']} signal hit(s) | "
        f"{x_usage['unique_tokens']} token(s)"
    )

    ai_usage = ai_daily_stats(report_date)
    lines.append(
        f"Luna AI: {ai_usage['calls']} call(s) | "
        f"P/N/N: {ai_usage['positive']}/{ai_usage['neutral']}/{ai_usage['negative']} | "
        f"avg conf {ai_usage['avg_confidence']:.0f}%"
    )

    try:
        lines.append(paper_lab.eod_summary_text(report_date))
    except Exception as exc:
        print(f"  Paper research EOD warning: {exc}")

    missed = generate_missed_opportunity_report(
        settings,
        report_date=report_date,
    )
    audit_missed_opportunity_pipeline(
        settings,
        report_date=report_date,
    )
    generate_luna_outcome_scorecard(
        settings,
        report_date=report_date,
    )
    if missed.get("rejected_signals"):
        lines.append(
            f"Missed runners MFE: +20/30m {missed['missed_20_30']} | "
            f"+50/60m {missed['missed_50_60']}"
        )
        best_miss = missed.get("best") or {}
        if best_miss:
            best_mfe = max(
                safe_number(best_miss.get("mfe_60m_pct")),
                safe_number(best_miss.get("mfe_30m_pct")),
            )
            lines.append(
                f"Top miss: {best_miss.get('symbol', '?')} "
                f"MFE {best_mfe:+.1f}% | "
                f"{str(best_miss.get('rejection_reasons') or '')[:80]}"
            )

    ai_lesson = luna_eod_review(
        report_date,
        stats,
        missed,
        settings,
    )
    if ai_lesson:
        lines.append(ai_lesson)

    try:
        publish_result = evidence_publisher.publish_daily_evidence(report_date)
        lines.append(
            f"Evidence publish: {publish_result.get('status', 'UNKNOWN')}"
        )
    except Exception as exc:
        print(f"  Evidence publish warning: {exc}")
        lines.append("Evidence publish: ERROR")

    if position:
        open_text = f"Open: {position.get('symbol', '?')} ${safe_number(position.get('entry_usdc')):.2f} entry"
        if liquidation is not None:
            entry = safe_number(position.get("entry_usdc"))
            open_pnl = ((liquidation - entry) / entry * 100.0) if entry > 0 else 0.0
            open_text += f" | value ${liquidation:.4f} ({open_pnl:+.2f}%)"
        lines.append(open_text)
    else:
        lines.append("Open position: none")

    sent = send_crypto_eod_pushover(
        "CryptoTracker — EOD Performance",
        "\n".join(lines),
    )
    if sent:
        if force:
            print("  Crypto EOD forced report sent; tonight's scheduled report remains eligible.")
        elif manual_once_due:
            save_json(
                CRYPTO_EOD_STATE_FILE,
                {
                    "last_sent_date": report_date,
                    "sent_at": now.isoformat(),
                    "manual_once_key": once_key,
                },
            )
            print("  Crypto EOD one-time report sent; recurring report consumed for today.")
        else:
            save_json(
                CRYPTO_EOD_STATE_FILE,
                {
                    "last_sent_date": report_date,
                    "sent_at": now.isoformat(),
                    "manual_once_key": state.get("manual_once_key", ""),
                },
            )
            print("  Crypto EOD Pushover report sent.")
    return sent


def helius_enabled(settings=None):
    """Repository-controlled Helius switch; local stale settings cannot override it."""
    settings = settings or {}
    raw = settings.get("HELIUS_ENABLED")
    if raw is None:
        raw = os.getenv("HELIUS_ENABLED", "1")
    return str(raw).strip().lower() not in {"0", "false", "no", "off"}


def _is_helius_url(url):
    return "helius" in str(url or "").lower()


def _helius_circuit_open():
    return time.time() < safe_number(_HELIUS_CIRCUIT.get("open_until"))


def helius_data_quality():
    if not helius_enabled():
        return "UNAVAILABLE_DISABLED"
    if _helius_circuit_open():
        return "UNAVAILABLE_CIRCUIT_OPEN"
    return "AVAILABLE"


def _permanent_helius_failure(status_code, text):
    text = str(text or "").lower()
    markers = (
        "service halted", "credits exhausted", "credit usage",
        "upgrade plan", "plan credits", "payment required",
        "quota exhausted", "monthly credits",
    )
    return (
        int(status_code or 0) in {402, 403}
        or any(marker in text for marker in markers)
    )


def _open_helius_circuit(reason, settings=None):
    settings = settings or {}
    seconds = settings.get("HELIUS_CIRCUIT_BREAKER_SECONDS")
    if seconds is None:
        seconds = os.getenv("HELIUS_CIRCUIT_BREAKER_SECONDS", "86400")
    try:
        seconds = max(3600, int(float(seconds)))
    except Exception:
        seconds = 86400
    now = time.time()
    _HELIUS_CIRCUIT.update({
        "open_until": now + seconds,
        "opened_at": now,
        "reason": str(reason or "Helius unavailable")[:300],
    })
    _warn_api_once(
        "helius-permanent-halt",
        f"Helius disabled for {seconds // 3600}h: {_HELIUS_CIRCUIT['reason']}",
        seconds,
    )
    if not _HELIUS_CIRCUIT.get("alerted"):
        _HELIUS_CIRCUIT["alerted"] = True
        try:
            send_pushover_once(
                "helius-service-halted",
                "CryptoTracker data degraded",
                "Helius service is halted or out of credits. Helius-only holder data is disabled; wallet reads use fallback Solana RPC. Paper trading continues.",
                cooldown_seconds=seconds,
                audience="personal",
            )
        except Exception:
            pass


def _solana_rpc_url():
    explicit = str(os.getenv("SOLANA_RPC_URL") or "").strip()
    if explicit:
        return explicit

    helius_key = str(os.getenv("HELIUS_API_KEY") or "").strip()
    if helius_enabled() and helius_key and not _helius_circuit_open():
        return f"https://mainnet.helius-rpc.com/?api-key={helius_key}"

    return "https://api.mainnet-beta.solana.com"


def _helius_post_json(url, payload, timeout=25, settings=None):
    """POST JSON with retries, but fail fast and open a circuit on permanent Helius failures."""
    settings = settings or {}
    is_helius = _is_helius_url(url)
    if is_helius and not helius_enabled(settings):
        raise RuntimeError("HELIUS_DISABLED")
    if is_helius and _helius_circuit_open():
        raise RuntimeError(
            f"HELIUS_CIRCUIT_OPEN: {_HELIUS_CIRCUIT.get('reason', 'service unavailable')}"
        )

    def _num(key, default, cast=float):
        raw = settings.get(key)
        if raw is None:
            raw = os.getenv(key)
        try:
            return cast(raw) if raw not in (None, "") else cast(default)
        except Exception:
            return cast(default)

    retries = max(0, _num("HELIUS_MAX_RETRIES", 3, int))
    base_delay = max(0.25, _num("HELIUS_BACKOFF_BASE_SECONDS", 1.0))
    max_delay = max(base_delay, _num("HELIUS_BACKOFF_MAX_SECONDS", 8.0))
    provider = "Helius" if is_helius else "Solana RPC"

    for attempt in range(retries + 1):
        try:
            response = requests.post(url, json=payload, timeout=timeout)
            response_text = str(getattr(response, "text", "") or "")[:1000]
            if is_helius and _permanent_helius_failure(response.status_code, response_text):
                reason = f"HTTP {response.status_code}: {response_text[:240]}"
                _open_helius_circuit(reason, settings)
                raise RuntimeError(f"HELIUS_PERMANENT_FAILURE: {reason}")

            retryable = response.status_code in {429, 500, 502, 503, 504}
            if retryable and attempt < retries:
                retry_after = safe_number(response.headers.get("Retry-After"))
                delay = retry_after if retry_after > 0 else min(
                    max_delay, base_delay * (2 ** attempt)
                )
                print(
                    f"  {provider} HTTP {response.status_code}; "
                    f"retry {attempt + 1}/{retries} in {delay:.1f}s..."
                )
                time.sleep(delay)
                continue

            response.raise_for_status()
            body = response.json()
            error = body.get("error")
            if error:
                error_text = str(error).lower()
                if is_helius and _permanent_helius_failure(0, error_text):
                    _open_helius_circuit(error, settings)
                    raise RuntimeError(f"HELIUS_PERMANENT_FAILURE: {error}")
                throttled = (
                    "429" in error_text
                    or "too many requests" in error_text
                    or "rate limit" in error_text
                )
                if throttled and attempt < retries:
                    delay = min(max_delay, base_delay * (2 ** attempt))
                    print(
                        f"  {provider} throttled; "
                        f"retry {attempt + 1}/{retries} in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    continue
                raise RuntimeError(str(error))
            return body

        except RuntimeError:
            raise
        except requests.RequestException as exc:
            if attempt >= retries:
                raise
            delay = min(max_delay, base_delay * (2 ** attempt))
            print(
                f"  {provider} request warning: {exc}; "
                f"retry {attempt + 1}/{retries} in {delay:.1f}s..."
            )
            time.sleep(delay)

    raise RuntimeError(f"{provider} request failed after retries.")


def invalidate_wallet_usdc_balance_cache():
    _WALLET_USDC_BALANCE_CACHE["fetched_at"] = 0.0


def wallet_usdc_balance(wallet_address, force=False):
    """Return wallet USDC with a 5-minute cache and stale fallback on RPC failure."""
    now = time.time()
    try:
        cache_seconds = max(
            0, int(float(os.getenv("WALLET_BALANCE_CACHE_SECONDS", "300")))
        )
    except Exception:
        cache_seconds = 300

    cached_value = _WALLET_USDC_BALANCE_CACHE.get("value")
    cached_at = safe_number(_WALLET_USDC_BALANCE_CACHE.get("fetched_at"))
    cache_age = max(0.0, now - cached_at) if cached_at > 0 else float("inf")

    if not force and cached_value is not None and cache_age < cache_seconds:
        return safe_number(cached_value)

    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenAccountsByOwner",
            "params": [
                wallet_address,
                {"mint": USDC_MINT},
                {"encoding": "jsonParsed"},
            ],
        }
        body = _helius_post_json(_solana_rpc_url(), payload, timeout=20)

        total = 0.0
        for item in ((body.get("result") or {}).get("value") or []):
            info = (
                (((item.get("account") or {}).get("data") or {}).get("parsed") or {})
                .get("info") or {}
            )
            amount = (info.get("tokenAmount") or {}).get("uiAmountString")
            total += safe_number(amount)

        _WALLET_USDC_BALANCE_CACHE["value"] = total
        _WALLET_USDC_BALANCE_CACHE["fetched_at"] = now
        return total

    except Exception as exc:
        if cached_value is not None:
            print(
                f"  Wallet USDC balance warning: {exc} | "
                f"using cached ${safe_number(cached_value):.4f} "
                f"({cache_age / 60.0:.1f}m old)"
            )
            return safe_number(cached_value)
        print(f"  Wallet USDC balance warning: {exc}")
        return None

def load_daily_state():
    return load_json(DAILY_STATE_FILE, {})


def save_daily_state(state):
    save_json(DAILY_STATE_FILE, state)


def ensure_daily_state(settings, current_equity_usdc=None):
    """
    Persist the day's starting trading equity so a restart cannot reset the
    +2% target or drawdown calculation.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    state = load_daily_state()

    if state.get("date") == today and safe_number(state.get("baseline_equity_usdc")) > 0:
        return state

    baseline = safe_number(current_equity_usdc)

    # If V11 is first started mid-day while flat, reconstruct the day's
    # approximate starting equity from current USDC minus realized P/L so
    # restarting/upgrading does not erase earlier completed trades.
    if baseline > 0 and not load_position():
        _, realized_today = today_trade_stats()
        reconstructed = baseline - realized_today
        if reconstructed > 0:
            baseline = reconstructed

    if baseline <= 0:
        baseline = safe_number(settings.get("DAILY_REFERENCE_CAPITAL_USDC"))

    state = {
        "date": today,
        "baseline_equity_usdc": baseline,
        "target_locked": False,
        "drawdown_locked": False,
        "created_at": datetime.now().isoformat(),
    }
    save_daily_state(state)
    return state


def daily_account_status(settings, current_equity_usdc=None):
    state = ensure_daily_state(settings, current_equity_usdc)
    baseline = safe_number(state.get("baseline_equity_usdc"))
    current = safe_number(current_equity_usdc)

    # RPC fallback: when flat, realized P/L can still enforce the daily limit
    # if the user supplied DAILY_REFERENCE_CAPITAL_USDC.
    if current <= 0 and baseline > 0:
        _, realized = today_trade_stats()
        current = baseline + realized

    return_pct = (
        ((current - baseline) / baseline) * 100.0
        if baseline > 0 and current > 0 else None
    )

    return {
        "state": state,
        "baseline_equity_usdc": baseline,
        "current_equity_usdc": current,
        "return_pct": return_pct,
        "target_pct": float(settings.get("DAILY_TARGET_PCT", 2.0)),
        "drawdown_pct": float(settings.get("MAX_DAILY_DRAWDOWN_PCT", 1.5)),
    }


def set_daily_lock(kind, current_equity_usdc=None):
    state = load_daily_state()
    if not state:
        return
    if kind == "target":
        state["target_locked"] = True
        state["target_locked_at"] = datetime.now().isoformat()
    elif kind == "drawdown":
        state["drawdown_locked"] = True
        state["drawdown_locked_at"] = datetime.now().isoformat()
    if current_equity_usdc is not None:
        state["lock_equity_usdc"] = safe_number(current_equity_usdc)
    save_daily_state(state)


def confidence_tier(candidate):
    local_whale = safe_number(candidate.get("whale_score_bonus"))
    birdeye = safe_number(candidate.get("birdeye_smart_bonus"))
    token_social = safe_number(candidate.get("token_social_bonus"))
    social = safe_number(candidate.get("social_score_bonus"))
    source = str(candidate.get("social_score_source") or "NONE")
    direct_social = max(0.0, social) if source == "DIRECT" else 0.0
    smart = max(0.0, local_whale) + max(0.0, birdeye)
    direct = token_social + direct_social
    ai = candidate.get("ai_confirmation_detail") or {}
    healthy_ai = bool(
        str(ai.get("assessment") or "").upper() == "POSITIVE"
        and str(ai.get("setup_type") or "").upper() == "HEALTHY_SURGE"
        and safe_number(ai.get("confidence")) >= 80
    )

    if smart >= 15 and healthy_ai:
        return "STRONG"
    if smart >= 10 or healthy_ai or direct >= 5:
        return "CONFIRMED"
    if local_whale + birdeye + social < -5:
        return "CAUTION"
    return "BASE"

def choose_trade_size(candidate, settings, wallet_address):
    """
    Quant determines whether we trade. Whale/social confirmation can only
    modulate size within a bounded range after the quant path has passed.
    """
    path = surge_entry_path(candidate, settings)
    if path == "EARLY_ACCEL":
        fixed = float(settings.get("EARLY_ACCEL_TRADE_SIZE_USDC", 0.75))
        risk_pct = float(settings.get("EARLY_RISK_PCT", 0.25))
    else:
        fixed = float(
            settings.get(
                "NORMAL_TRADE_SIZE_USDC",
                settings.get("TRADE_SIZE_USDC", 1.50),
            )
        )
        risk_pct = float(settings.get("NORMAL_RISK_PCT", 0.50))

    usdc_balance = wallet_usdc_balance(wallet_address)
    equity = safe_number(usdc_balance)

    if bool(settings.get("USE_RISK_BASED_SIZING", 0)) and equity > 0:
        stop_distance = max(0.01, abs(float(settings.get("STOP_LOSS_PCT", -6.0))))
        size = equity * (risk_pct / 100.0) / (stop_distance / 100.0)
        allocation_cap = equity * (
            float(settings.get("MAX_POSITION_PCT_EQUITY", 15.0)) / 100.0
        )
        size = min(size, allocation_cap)
    else:
        size = fixed

    whale = max(0.0, safe_number(candidate.get("whale_score_bonus")))
    birdeye = max(0.0, safe_number(candidate.get("birdeye_smart_bonus")))
    token_social = max(0.0, safe_number(candidate.get("token_social_bonus")))
    social = safe_number(candidate.get("social_score_bonus"))
    social_source = str(candidate.get("social_score_source") or "NONE")

    positive_external = whale + birdeye + token_social
    if social_source == "DIRECT":
        positive_external += max(0.0, social)
    ai = candidate.get("ai_confirmation_detail") or {}
    if (
        str(ai.get("assessment") or "").upper() == "POSITIVE"
        and str(ai.get("setup_type") or "").upper() == "HEALTHY_SURGE"
        and safe_number(ai.get("confidence")) >= 80
    ):
        positive_external += max(0.0, safe_number(candidate.get("ai_confirmation_bonus")))

    max_boost = float(settings.get("CONFIRMATION_SIZE_BOOST_MAX_PCT", 25.0))
    # Full max boost requires broad confirmation, not a single weak source.
    boost_pct = min(max_boost, max_boost * positive_external / 50.0)
    size *= 1.0 + boost_pct / 100.0

    if social < 0:
        reduction = min(
            float(settings.get("NEGATIVE_SOCIAL_SIZE_REDUCTION_PCT", 25.0)),
            abs(social),
        )
        size *= 1.0 - reduction / 100.0

    size = max(float(settings.get("MIN_TRADE_SIZE_USDC", 0.50)), size)
    size = min(float(settings.get("MAX_TRADE_SIZE_USDC", 3.00)), size)

    # Never attempt to spend the entire available USDC balance.
    if usdc_balance is not None and usdc_balance > 0:
        size = min(size, max(0.0, usdc_balance * 0.95))

    return round(size, 6), confidence_tier(candidate)


# ============================================================
# JUPITER
# ============================================================

def jupiter_order(
    api_key,
    input_mint,
    output_mint,
    raw_amount,
    taker=None,
):
    params = {
        "inputMint": input_mint,
        "outputMint": output_mint,
        "amount": str(int(raw_amount)),
    }

    if taker:
        params["taker"] = taker

    response = requests.get(
        f"{JUPITER_BASE}/order",
        params=params,
        headers={
            "x-api-key": api_key,
            "Accept": "application/json",
        },
        timeout=25,
    )

    if not response.ok:
        raise RuntimeError(
            f"Jupiter /order HTTP {response.status_code}: "
            f"{response.text}"
        )

    return response.json()


def sign_transaction(transaction_b64, signer):
    raw = base64.b64decode(transaction_b64)
    tx = VersionedTransaction.from_bytes(raw)

    required = tx.message.header.num_required_signatures
    signer_keys = list(tx.message.account_keys[:required])

    try:
        signer_index = signer_keys.index(signer.pubkey())
    except ValueError as exc:
        raise RuntimeError(
            "Bot wallet is not a required signer."
        ) from exc

    wallet_signature = signer.sign_message(
        to_bytes_versioned(tx.message)
    )

    signatures = list(tx.signatures)

    while len(signatures) < required:
        signatures.append(ZERO_SIGNATURE)

    signatures[signer_index] = wallet_signature

    signed = VersionedTransaction.populate(
        tx.message,
        signatures,
    )

    return base64.b64encode(
        bytes(signed)
    ).decode("ascii")


def execute_order(api_key, signed_transaction, request_id):
    try:
        response = requests.post(
            f"{JUPITER_BASE}/execute",
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
            },
            json={
                "signedTransaction": signed_transaction,
                "requestId": request_id,
            },
            timeout=60,
        )
    except requests.RequestException as exc:
        raise RuntimeError(
            "UNKNOWN_EXECUTION_STATE: transport error. "
            "Do not automatically retry."
        ) from exc

    if not response.ok:
        raise RuntimeError(
            "UNKNOWN_EXECUTION_STATE: "
            f"/execute HTTP {response.status_code}: {response.text}"
        )

    return response.json()


def real_swap(
    api_key,
    signer,
    wallet_address,
    input_mint,
    output_mint,
    raw_amount,
):
    order = jupiter_order(
        api_key,
        input_mint,
        output_mint,
        raw_amount,
        taker=wallet_address,
    )

    if not order.get("transaction"):
        raise RuntimeError(
            "Jupiter could not build transaction: "
            f"{order.get('errorCode')} "
            f"{order.get('errorMessage')}"
        )

    signed = sign_transaction(
        order["transaction"],
        signer,
    )

    result = execute_order(
        api_key,
        signed,
        order["requestId"],
    )

    if (
        result.get("status") != "Success"
        or result.get("code") != 0
    ):
        raise RuntimeError(
            f"Swap failed: status={result.get('status')} "
            f"code={result.get('code')} "
            f"error={result.get('error')}"
        )

    return order, result


# ============================================================
# SCANNER COMPATIBILITY WRAPPERS
# ============================================================

def scanner_safe_number(value):
    if hasattr(ms, "safe_number"):
        return ms.safe_number(value)
    return safe_number(value)


def scanner_request_delay():
    return getattr(ms, "REQUEST_DELAY", 0.08)


def scanner_max_tokens():
    return getattr(ms, "MAX_TOKENS_PER_RUN", 150)


def parse_iso_datetime(value):
    try:
        return datetime.fromisoformat(str(value))
    except Exception:
        return None


def age_hours(timestamp_text, now=None):
    now = now or datetime.now()
    dt = parse_iso_datetime(timestamp_text)
    if dt is None:
        return float("inf")
    return max(0.0, (now - dt).total_seconds() / 3600.0)



def _valid_solana_mint(value):
    value = str(value or "").strip()
    if not (32 <= len(value) <= 50):
        return False
    allowed = set("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")
    return all(ch in allowed for ch in value)


def _parse_utc_any(value):
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def discover_recent_whale_tokens(settings):
    """
    Best-effort discovery source. A verified recent Solana whale buy may add
    a token mint to the scan universe, but cannot bypass any quant/execution gate.
    """
    if not bool(settings.get("MULTISOURCE_DISCOVERY_ENABLED", 1)):
        return {}
    if not bool(settings.get("WHALE_DISCOVERY_ENABLED", 1)):
        return {}
    smart_events_file = active_smart_money_events_file()
    if not smart_events_file.exists():
        return {}

    now = datetime.now(timezone.utc)
    max_age = float(settings.get("WHALE_DISCOVERY_MAX_AGE_MINUTES", 60))
    min_spend = float(settings.get("WHALE_DISCOVERY_MIN_SPEND_USD", 50.0))
    max_tokens = max(0, int(settings.get("WHALE_DISCOVERY_MAX_TOKENS", 30)))

    newest = {}

    try:
        with smart_events_file.open("r", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if str(row.get("chain") or "").lower() != "solana":
                    continue

                confidence = str(row.get("confidence") or "").lower()
                if "verified" not in confidence or "unverified" in confidence:
                    continue

                mint = str(row.get("token_mint") or "").strip()
                if not _valid_solana_mint(mint):
                    continue

                dt = _parse_utc_any(
                    row.get("trade_time_utc") or row.get("detected_at_utc")
                )
                if dt is None:
                    continue

                age_min = (now - dt).total_seconds() / 60.0
                if age_min < 0 or age_min > max_age:
                    continue

                spend = safe_number(row.get("estimated_spend_usd"))
                size_class = str(row.get("buy_size_class") or "").upper()
                first_meaningful = bool(int(safe_number(row.get("is_first_meaningful_buy"))))

                # Let a clearly meaningful/large first buy through even if the
                # monitor could not estimate spend perfectly.
                meaningful_shape = (
                    first_meaningful
                    or size_class in {"MEANINGFUL", "STRONG"}
                    or str(row.get("campaign_pattern") or "").upper() == "LARGE_POSITION"
                )
                if spend < min_spend and not meaningful_shape:
                    continue

                old = newest.get(mint)
                if old is None or dt > old["dt"]:
                    newest[mint] = {
                        "dt": dt,
                        "source": "WHALE",
                        "symbol": str(row.get("token_symbol") or ""),
                        "trader": str(row.get("trader_name") or ""),
                        "spend": spend,
                        "size_class": size_class,
                        "first_meaningful": first_meaningful,
                    }

    except Exception as exc:
        print(f"  Whale discovery warning: {exc}")
        return {}

    ranked = sorted(
        newest.items(),
        key=lambda kv: kv[1]["dt"],
        reverse=True,
    )[:max_tokens]

    return {mint: meta for mint, meta in ranked}


def _gecko_relationship_mint(pool, relationship_name):
    try:
        rel_id = (
            (((pool.get("relationships") or {}).get(relationship_name) or {})
             .get("data") or {})
            .get("id")
        )
        rel_id = str(rel_id or "")
        # GeckoTerminal token relationship ids normally look like
        # "solana_<mint>".
        if rel_id.startswith("solana_"):
            rel_id = rel_id[len("solana_"):]
        return rel_id if _valid_solana_mint(rel_id) else ""
    except Exception:
        return ""


def discover_gecko_new_pool_tokens(settings):
    """
    Free GeckoTerminal new-pool discovery. Failure is non-fatal and simply
    leaves DEX/whale discovery in control for that cycle.
    """
    if not bool(settings.get("MULTISOURCE_DISCOVERY_ENABLED", 1)):
        return {}
    if not bool(settings.get("GECKO_DISCOVERY_ENABLED", 1)):
        return {}

    refresh = max(
        60,
        int(settings.get("GECKO_DISCOVERY_REFRESH_SECONDS", 300)),
    )
    age = time.time() - safe_number(_GECKO_DISCOVERY_CACHE.get("fetched_at"))

    if age < refresh:
        return {
            item["mint"]: item
            for item in (_GECKO_DISCOVERY_CACHE.get("tokens") or [])
            if item.get("mint")
        }

    max_tokens = max(0, int(settings.get("GECKO_DISCOVERY_MAX_TOKENS", 25)))
    excluded = {
        USDC_MINT,
        "So11111111111111111111111111111111111111112",  # wrapped SOL
    }

    found = []
    try:
        response = requests.get(
            "https://api.geckoterminal.com/api/v2/networks/solana/new_pools",
            params={"page": 1},
            headers={"Accept": "application/json"},
            timeout=15,
        )
        response.raise_for_status()
        body = response.json()

        for pool in body.get("data") or []:
            mint = _gecko_relationship_mint(pool, "base_token")
            if not mint or mint in excluded:
                continue
            attrs = pool.get("attributes") or {}
            found.append({
                "mint": mint,
                "source": "GECKO_NEW_POOL",
                "pool_name": str(attrs.get("name") or ""),
                "pool_address": str(attrs.get("address") or pool.get("id") or ""),
            })
            if len(found) >= max_tokens:
                break

        _GECKO_DISCOVERY_CACHE["fetched_at"] = time.time()
        _GECKO_DISCOVERY_CACHE["tokens"] = found

    except Exception as exc:
        _warn_api_once(
            "gecko-discovery",
            f"GeckoTerminal discovery warning: {exc}",
            900,
        )
        # Keep any previously cached token list if the refresh fails.
        found = _GECKO_DISCOVERY_CACHE.get("tokens") or []

    return {
        item["mint"]: item
        for item in found
        if item.get("mint")
    }


def log_discovery_sources(source_map):
    """
    Lightweight audit of externally injected discoveries. This log is
    informational only and cannot affect trading.
    """
    if not source_map:
        return

    fields = [
        "logged_at",
        "token_address",
        "source",
        "symbol",
        "detail",
    ]
    exists = DISCOVERY_SOURCE_LOG_FILE.exists()

    # Avoid writing identical source/token rows every minute by checking the
    # last 250 rows for today's token/source combination.
    seen = set()
    if exists:
        try:
            with DISCOVERY_SOURCE_LOG_FILE.open("r", newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))[-250:]
            today = datetime.now().date().isoformat()
            for row in rows:
                if str(row.get("logged_at") or "").startswith(today):
                    seen.add((row.get("token_address"), row.get("source")))
        except Exception:
            pass

    try:
        with DISCOVERY_SOURCE_LOG_FILE.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            if not exists:
                writer.writeheader()

            for mint, meta in source_map.items():
                source = str(meta.get("source") or "EXTERNAL")
                key = (mint, source)
                if key in seen:
                    continue

                detail = ""
                if source == "WHALE":
                    detail = (
                        f"{meta.get('trader') or 'verified wallet'} | "
                        f"{meta.get('size_class') or ''} | "
                        f"${safe_number(meta.get('spend')):,.0f}"
                    )
                elif source == "GECKO_NEW_POOL":
                    detail = str(meta.get("pool_name") or meta.get("pool_address") or "")

                writer.writerow({
                    "logged_at": datetime.now().isoformat(),
                    "token_address": mint,
                    "source": source,
                    "symbol": str(meta.get("symbol") or ""),
                    "detail": detail,
                })
    except Exception as exc:
        print(f"  Discovery-source log warning: {exc}")


def external_discovery_tokens(settings):
    whale = discover_recent_whale_tokens(settings)
    gecko = discover_gecko_new_pool_tokens(settings)

    # Whale injection gets precedence when the same mint appears in both.
    combined = {}
    for mint, meta in gecko.items():
        combined[mint] = meta
    for mint, meta in whale.items():
        combined[mint] = meta

    if combined:
        log_discovery_sources(combined)

    print(
        f"  external discovery : {len(whale)} whale + "
        f"{len(gecko)} Gecko new-pool token(s)"
    )
    return combined


def scan_candidates(settings):
    if hasattr(ms, "ensure_directories"):
        ms.ensure_directories()

    previous_snapshots = load_previous_snapshots()

    universe = ms.load_universe()
    dex_discovered = list(ms.discover_tokens())
    external_sources = external_discovery_tokens(settings)

    # External tokens are evaluated immediately, but they receive no special
    # trading privilege. All paths still run through the same quant gates.
    discovered = list(dict.fromkeys(
        list(external_sources.keys()) + dex_discovered
    ))

    now = datetime.now()
    now_text = now.isoformat()

    # last_seen tracks the last time the token appeared in a discovery feed.
    # It is intentionally NOT updated merely because we scan the token.
    for address in discovered:
        if address not in universe:
            universe[address] = {
                "first_seen": now_text,
                "last_seen": now_text,
            }
        else:
            universe[address]["last_seen"] = now_text

    discovered_set = set(discovered)
    dex_discovered_set = set(dex_discovered)

    # Record the most recent discovery source for prioritization/audit.
    for address in discovered:
        meta = universe.setdefault(address, {
            "first_seen": now_text,
            "last_seen": now_text,
        })
        if address in external_sources:
            meta["discovery_source"] = str(
                external_sources[address].get("source") or "EXTERNAL"
            )
        elif address in dex_discovered_set:
            meta["discovery_source"] = "DEX"

    # Keep the universe file bounded while preserving a longer history
    # than the active watch window.
    retention_hours = settings["UNIVERSE_RETENTION_HOURS"]
    universe = {
        address: meta
        for address, meta in universe.items()
        if (
            address in discovered_set
            or age_hours(meta.get("last_seen"), now) <= retention_hours
        )
    }

    ms.save_universe(universe)

    # FIX: Older builds sorted retained tokens oldest-first. If the universe
    # exceeded MAX_TOKENS_PER_RUN, recently discovered tokens could disappear
    # from scanning. V7 explicitly keeps a rolling active watchlist and
    # prioritizes current + recently discovered tokens newest-first.
    watch_hours = settings["PERSISTENT_WATCH_HOURS"]

    active_watch = [
        address
        for address, meta in universe.items()
        if (
            address in discovered_set
            or age_hours(meta.get("last_seen"), now) <= watch_hours
        )
    ]

    def watch_sort_key(address):
        meta = universe.get(address, {})
        dt = parse_iso_datetime(meta.get("last_seen"))
        timestamp = dt.timestamp() if dt else 0.0
        source = str(meta.get("discovery_source") or "")
        source_priority = {
            "WHALE": 3,
            "GECKO_NEW_POOL": 2,
            "DEX": 1,
        }.get(source, 0)
        return (
            1 if address in discovered_set else 0,
            source_priority,
            timestamp,
        )

    active_watch.sort(
        key=watch_sort_key,
        reverse=True,
    )

    max_tokens = min(
        scanner_max_tokens(),
        max(25, int(settings.get("MAX_ACTIVE_SCAN_TOKENS", 100))),
    )

    if len(active_watch) > max_tokens:
        print(
            f"  Watchlist warning: {len(active_watch)} active tokens "
            f"but scanner cap is {max_tokens}; newest tokens get priority."
        )

    addresses = active_watch[:max_tokens]

    persistent_count = sum(
        1
        for address in addresses
        if address not in discovered_set
    )

    print(
        f"  persistent watch  : {persistent_count} retained tokens "
        f"(window {watch_hours:.1f}h)"
    )
    print(
        f"  scanning total    : {len(addresses)} unique tokens"
    )

    candidates = []

    for token_address in addresses:
        try:
            pairs = ms.get_token_pairs(token_address)
            pair = ms.choose_best_pair(pairs)

            if not pair:
                continue

            metrics = ms.calculate_metrics(pair)

            if not ms.passes_filters(pair, metrics):
                continue

            base = pair.get("baseToken", {})
            actual_address = base.get(
                "address",
                token_address,
            )

            market_cap = scanner_safe_number(
                pair.get("marketCap")
            )
            fdv = scanner_safe_number(
                pair.get("fdv")
            )
            valuation = market_cap if market_cap > 0 else fdv

            score = ms.calculate_score(metrics)

            row = {
                "timestamp": datetime.now().isoformat(),
                "symbol": base.get("symbol", "?"),
                "name": base.get("name", "?"),
                "token_address": actual_address,
                "pair_address": pair.get("pairAddress", ""),
                "dex": pair.get("dexId", "?"),
                "price_usd": scanner_safe_number(
                    pair.get("priceUsd")
                ),
                "market_cap": valuation,
                "liquidity": scanner_safe_number(
                    pair.get("liquidity", {}).get("usd")
                ),
                "volume_5m": metrics["volume_5m"],
                "volume_1h": metrics["volume_1h"],
                "volume_6h": metrics["volume_6h"],
                "volume_24h": metrics["volume_24h"],
                "price_5m": metrics["price_5m"],
                "price_1h": metrics["price_1h"],
                "price_6h": metrics["price_6h"],
                "price_24h": metrics["price_24h"],
                "buys_5m": metrics["buys_5m"],
                "sells_5m": metrics["sells_5m"],
                "buys_1h": metrics["buys_1h"],
                "sells_1h": metrics["sells_1h"],
                "buy_sell_ratio_5m": round(
                    metrics["buy_sell_ratio_5m"], 4
                ),
                "buy_sell_ratio_1h": round(
                    metrics["buy_sell_ratio_1h"], 4
                ),
                "volume_acceleration": round(
                    metrics["volume_acceleration"], 4
                ),
                "momentum_score": score,
                "pair_url": pair.get("url", ""),
                "discovery_source": str(
                    universe.get(actual_address, {}).get("discovery_source")
                    or universe.get(token_address, {}).get("discovery_source")
                    or "DEX"
                ),
            }

            previous = previous_snapshots.get(
                actual_address
            )

            row.update(
                calculate_cross_scan(row, previous)
            )

            row["momentum_state"] = classify_state(row)

            append_auto_snapshot(row)
            candidates.append(row)

        except Exception as exc:
            print(
                f"  Scanner warning "
                f"{token_address[:8]}...: {exc}"
            )

        time.sleep(scanner_request_delay())

    candidates.sort(
        key=lambda x: (
            x["momentum_state"] == "SURGING",
            x["score_delta"],
            x["momentum_score"],
        ),
        reverse=True,
    )

    return candidates



# ============================================================
# V11.5 REACCELERATION WATCH
# ============================================================

REACCEL_LOG_FIELDS = [
    "logged_at",
    "event",
    "symbol",
    "token_address",
    "watch_age_minutes",
    "watch_reason",
    "discovery_source",
    "quant_score",
    "score_delta",
    "price_5m",
    "price_1h",
    "liquidity",
    "volume_5m",
    "volume_acceleration",
    "buy_sell_ratio_5m",
    "transactions_5m",
    "entry_path",
]


def _append_reaccel_log(candidate, event, watch, settings):
    try:
        exists = REACCEL_LOG_FILE.exists()
        tx5 = (
            safe_number(candidate.get("buys_5m"))
            + safe_number(candidate.get("sells_5m"))
        )
        with REACCEL_LOG_FILE.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=REACCEL_LOG_FIELDS)
            if not exists:
                writer.writeheader()
            writer.writerow({
                "logged_at": datetime.now().isoformat(),
                "event": event,
                "symbol": candidate.get("symbol", "?"),
                "token_address": candidate.get("token_address", ""),
                "watch_age_minutes": safe_number(candidate.get("reacceleration_age_minutes")),
                "watch_reason": str(watch.get("watch_reason") or ""),
                "discovery_source": str(candidate.get("discovery_source") or ""),
                "quant_score": safe_number(candidate.get("momentum_score")),
                "score_delta": safe_number(candidate.get("score_delta")),
                "price_5m": safe_number(candidate.get("price_5m")),
                "price_1h": safe_number(candidate.get("price_1h")),
                "liquidity": safe_number(candidate.get("liquidity")),
                "volume_5m": safe_number(candidate.get("volume_5m")),
                "volume_acceleration": safe_number(candidate.get("volume_acceleration")),
                "buy_sell_ratio_5m": safe_number(candidate.get("buy_sell_ratio_5m")),
                "transactions_5m": tx5,
                "entry_path": surge_entry_path(candidate, settings),
            })
    except Exception as exc:
        print(f"  Reacceleration log warning: {exc}")


def _reaccel_watch_quality(candidate, settings):
    tx5 = (
        safe_number(candidate.get("buys_5m"))
        + safe_number(candidate.get("sells_5m"))
    )
    return (
        safe_number(candidate.get("momentum_score"))
            >= float(settings.get("REACCEL_WATCH_MIN_SCORE", 60))
        and safe_number(candidate.get("score_delta"))
            >= float(settings.get("REACCEL_WATCH_MIN_DELTA", 35))
        and safe_number(candidate.get("liquidity"))
            >= float(settings.get("REACCEL_WATCH_MIN_LIQUIDITY", 40_000))
        and safe_number(candidate.get("volume_5m"))
            >= float(settings.get("REACCEL_WATCH_MIN_5M_VOLUME", 750))
        and safe_number(candidate.get("volume_acceleration"))
            >= float(settings.get("REACCEL_WATCH_MIN_VOLUME_ACCEL", 1.5))
        and safe_number(candidate.get("buy_sell_ratio_5m"))
            >= float(settings.get("REACCEL_WATCH_MIN_BUY_SELL_RATIO", 1.10))
        and tx5 >= int(settings.get("REACCEL_WATCH_MIN_5M_TRANSACTIONS", 8))
    )


def _extension_watch_reason(candidate, settings):
    """
    Watch only tokens whose otherwise-interesting surge is blocked by
    anti-chase extension. This avoids turning every rejected token into a watch.
    """
    if str(candidate.get("momentum_state") or "").upper() != "SURGING":
        return ""

    if not _reaccel_watch_quality(candidate, settings):
        return ""

    reasons = []
    if safe_number(candidate.get("price_5m")) > float(settings["MAX_BUY_5M_PCT"]):
        reasons.append("5m extended")
    if safe_number(candidate.get("price_1h")) > float(settings["MAX_BUY_1H_PCT"]):
        reasons.append("1h extended")

    return " + ".join(reasons)


def update_reacceleration_watch(candidates, settings):
    """
    Extended token -> WATCHING.
    Later reset -> READY only if it passes an existing NORMAL or EARLY_ACCEL path.

    IMPORTANT: READY never bypasses the quant model. It is a priority/context
    label for a token that the quant model has independently made eligible again.
    """
    if not bool(settings.get("REACCEL_WATCH_ENABLED", 1)):
        return candidates

    state = load_json(REACCEL_WATCH_FILE, {"tokens": {}})
    if not isinstance(state, dict):
        state = {"tokens": {}}
    state.setdefault("tokens", {})
    tokens = state["tokens"]

    now = datetime.now()
    max_age = float(settings.get("REACCEL_WATCH_MAX_AGE_MINUTES", 120))
    candidate_map = {
        str(c.get("token_address") or ""): c
        for c in candidates
        if c.get("token_address")
    }

    changed = False

    # Expire old watches.
    for token, watch in list(tokens.items()):
        try:
            created = datetime.fromisoformat(str(watch.get("first_watch_at") or ""))
            age = (now - created).total_seconds() / 60.0
        except Exception:
            age = max_age + 1

        if age > max_age:
            del tokens[token]
            changed = True

    # Add freshly extended candidates to the watch.
    for c in candidates:
        token = str(c.get("token_address") or "")
        if not token:
            continue

        reason = _extension_watch_reason(c, settings)
        if not reason:
            continue

        if token not in tokens:
            watch = {
                "symbol": str(c.get("symbol") or "?"),
                "first_watch_at": now.isoformat(),
                "last_seen_at": now.isoformat(),
                "watch_reason": reason,
                "peak_price_5m": safe_number(c.get("price_5m")),
                "peak_price_1h": safe_number(c.get("price_1h")),
                "triggered_at": "",
                "discovery_source": str(c.get("discovery_source") or ""),
            }
            tokens[token] = watch
            c["reacceleration_watch"] = "WATCHING"
            c["reacceleration_age_minutes"] = 0.0
            _append_reaccel_log(c, "WATCH_START", watch, settings)
            changed = True
        else:
            watch = tokens[token]
            watch["last_seen_at"] = now.isoformat()
            watch["peak_price_5m"] = max(
                safe_number(watch.get("peak_price_5m")),
                safe_number(c.get("price_5m")),
            )
            watch["peak_price_1h"] = max(
                safe_number(watch.get("peak_price_1h")),
                safe_number(c.get("price_1h")),
            )
            changed = True

    # Evaluate watched tokens that are present in this scan.
    for token, watch in tokens.items():
        c = candidate_map.get(token)
        if not c:
            continue

        try:
            created = datetime.fromisoformat(str(watch.get("first_watch_at") or ""))
            age_min = max(0.0, (now - created).total_seconds() / 60.0)
        except Exception:
            age_min = 0.0

        c["reacceleration_watch"] = "WATCHING"
        c["reacceleration_age_minutes"] = age_min
        c["reacceleration_watch_reason"] = str(watch.get("watch_reason") or "")
        c["reacceleration_peak_5m_pct"] = safe_number(watch.get("peak_price_5m"))
        c["reacceleration_peak_1h_pct"] = safe_number(watch.get("peak_price_1h"))

        paths = _entry_path_checks(c, settings)
        quant_ready = bool(
            str(c.get("momentum_state") or "").upper() == "SURGING"
            and (paths["NORMAL"]["passed"] or paths["EARLY_ACCEL"]["passed"])
        )

        if not quant_ready:
            continue

        c["reacceleration_watch"] = "READY"
        c["reacceleration_ready"] = True
        c["reacceleration_priority_bonus"] = float(
            settings.get("REACCEL_PRIORITY_BONUS", 5.0)
        )

        if not watch.get("triggered_at"):
            watch["triggered_at"] = now.isoformat()
            changed = True
            _append_reaccel_log(c, "REACCEL_READY", watch, settings)

            print(
                f"  REACCEL READY: {c.get('symbol', '?')} | "
                f"watched {age_min:.1f}m after {watch.get('watch_reason')} | "
                f"now passes {surge_entry_path(c, settings)}"
            )

            if bool(settings.get("REACCEL_PUSH_ENABLED", 1)):
                send_pushover_once(
                    key=f"reaccel-ready:{token}",
                    title=f"CryptoTracker REACCEL READY: {c.get('symbol', '?')}",
                    message=(
                        f"Previously rejected: {watch.get('watch_reason')}\n"
                        f"Watch age: {age_min:.1f}m\n"
                        f"Now passes: {surge_entry_path(c, settings)}\n"
                        f"Quant {safe_number(c.get('momentum_score')):.0f} "
                        f"({safe_number(c.get('score_delta')):+.0f})\n"
                        f"5m {safe_number(c.get('price_5m')):+.1f}% | "
                        f"1h {safe_number(c.get('price_1h')):+.1f}%\n"
                        f"VolX {safe_number(c.get('volume_acceleration')):.2f} | "
                        f"B/S {safe_number(c.get('buy_sell_ratio_5m')):.2f}"
                    ),
                    cooldown_seconds=3600,
                    priority=0,
                    sound="pushover",
                    audience="movement",
                )

    if changed:
        state["tokens"] = tokens
        save_json(REACCEL_WATCH_FILE, state)

    return candidates


# ============================================================
# ENTRY / COOLDOWN
# ============================================================

def token_entries_last_minutes(token_address, minutes=60):
    """
    Count completed BUY executions for this token in the recent window.
    Uses the daily trade log, so restarts do not reset the count.
    """
    path = trade_log_file()

    if not path.exists():
        return 0

    cutoff = datetime.now() - timedelta(minutes=minutes)
    count = 0

    try:
        with path.open("r", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("action") != "BUY":
                    continue
                if row.get("token_address") != token_address:
                    continue

                try:
                    ts = datetime.fromisoformat(row.get("timestamp", ""))
                except Exception:
                    continue

                if ts >= cutoff:
                    count += 1
    except Exception:
        return 0

    return count


def load_social_sentiment(settings):
    if not bool(settings.get("SOCIAL_SENTIMENT_ENABLED", 1)):
        return {}
    data = load_json(SOCIAL_SENTIMENT_FILE, {})
    if not data:
        return {}

    try:
        updated = datetime.fromisoformat(
            str(data.get("updated_at","")).replace("Z","+00:00")
        )
        # normalize aware timestamp to local-naive comparison safely
        age_minutes = (
            datetime.now(updated.tzinfo) - updated
        ).total_seconds() / 60.0
        if age_minutes > settings.get("SOCIAL_MAX_AGE_MINUTES", 15):
            return {}
    except Exception:
        return {}

    return data.get("scores") or {}


def candidate_social_score(candidate, social_scores, settings):
    """
    Prefer a direct token-symbol score. If none exists, allow a smaller SOL
    ecosystem contribution because this trader is Solana-focused.
    """
    symbol = str(candidate.get("symbol","")).upper().strip()
    direct = social_scores.get(symbol)
    if direct:
        return float(direct.get("score",0) or 0), "DIRECT"

    sol = social_scores.get("SOL") or social_scores.get("SOLANA")
    if sol:
        return (
            float(sol.get("score",0) or 0)
            * settings.get("SOCIAL_ECOSYSTEM_MULTIPLIER", 0.25),
            "SOL_ECOSYSTEM",
        )

    return 0.0, "NONE"


def apply_social_scores(candidates, settings):
    """
    V11: social sentiment is confirmation only. It never changes the quant
    momentum score used by entry gates. The direct/eco score is converted to
    a bounded bonus used for ranking and modest size modulation.
    """
    social_scores = load_social_sentiment(settings)
    weight = float(settings.get("SOCIAL_SCORE_WEIGHT", 0.15))
    max_bonus = abs(float(settings.get("SOCIAL_MAX_BONUS", 15.0)))

    for c in candidates:
        quant = safe_number(c.get("momentum_score"))
        social, source = candidate_social_score(
            c, social_scores, settings
        )
        raw_bonus = social * weight
        bonus = max(-max_bonus, min(max_bonus, raw_bonus))

        c["quant_score_raw"] = quant
        c["social_score"] = social
        c["social_score_source"] = source
        c["social_score_bonus"] = bonus

        # IMPORTANT: c["momentum_score"] stays quant-only in V11.
        c["composite_score"] = quant + bonus

    return candidates


def _parse_utc(text):
    try:
        dt = datetime.fromisoformat(str(text).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _csv_rows(path):
    if not path.exists():
        return []
    try:
        with path.open("r", newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except Exception as exc:
        print(f"  Smart-money read warning {path.name}: {exc}")
        return []


def load_recent_smart_money(settings):
    """
    Return the newest campaign state for each trader/token plus the newest
    event metadata. Only fresh activity inside SMART_MONEY_MAX_AGE_MINUTES is
    considered.

    Important:
    - UNKNOWN / unpriced events receive zero points.
    - Solana candidates are matched to Solana whale activity by mint first.
    - We do NOT cross-match a Robinhood token to a Solana token just because
      the ticker happens to be the same.
    """
    if not bool(settings.get("SMART_MONEY_ENABLED", 1)):
        return []

    campaigns = _csv_rows(active_smart_money_campaigns_file())
    events = _csv_rows(active_smart_money_events_file())
    if not campaigns:
        return []

    max_age = float(settings.get("SMART_MONEY_MAX_AGE_MINUTES", 15))
    now = datetime.now(timezone.utc)

    # Newest event per campaign lets us reject UNKNOWN / unpriced activity.
    latest_event = {}
    for row in events:
        cid = str(row.get("campaign_id") or "")
        if not cid:
            continue
        dt = _parse_utc(row.get("trade_time_utc") or row.get("detected_at_utc"))
        old = latest_event.get(cid)
        if old is None or (dt and (old[0] is None or dt > old[0])):
            latest_event[cid] = (dt, row)

    # The campaign CSV appends a new snapshot every time the campaign changes.
    # Keep only the newest snapshot for each campaign id.
    newest = {}
    for row in campaigns:
        cid = str(row.get("campaign_id") or "")
        if not cid:
            continue
        dt = _parse_utc(row.get("updated_at_utc") or row.get("last_buy_utc"))
        old = newest.get(cid)
        if old is None or (dt and (old[0] is None or dt > old[0])):
            newest[cid] = (dt, row)

    out = []
    for _, row in newest.values():
        signal_time = _parse_utc(
            row.get("last_signal_utc") or row.get("last_buy_utc")
        )
        if signal_time is None:
            continue
        age_min = max(0.0, (now - signal_time).total_seconds() / 60.0)
        if age_min > max_age:
            continue

        cid = str(row.get("campaign_id") or "")
        event = (latest_event.get(cid) or (None, {}))[1]

        # Do not score unresolved/unknown activity.
        size_class = str(event.get("buy_size_class") or "").upper()
        estimated = safe_number(event.get("estimated_spend_usd"))
        largest = safe_number(row.get("largest_buy_usd"))
        if size_class == "UNKNOWN" or (largest <= 0 and estimated <= 0):
            scoreable = False
        else:
            scoreable = True

        out.append({
            "trader_name": str(row.get("trader_name") or ""),
            "trader_handle": str(row.get("trader_handle") or "").lower(),
            "chain": str(row.get("chain") or "").lower(),
            "confidence": str(row.get("confidence") or ""),
            "token_mint": str(row.get("token_mint") or ""),
            "token_symbol": str(row.get("token_symbol") or "").upper(),
            "campaign_id": cid,
            "last_buy_utc": row.get("last_buy_utc") or "",
            "age_minutes": age_min,
            "largest_buy_usd": largest,
            "total_spend_usd": safe_number(row.get("total_spend_usd")),
            "meaningful_spend_usd": safe_number(row.get("meaningful_spend_usd")),
            "meaningful_buy_count": int(safe_number(row.get("meaningful_buy_count"))),
            "buy_count": int(safe_number(row.get("buy_count"))),
            "campaign_pattern": str(row.get("campaign_pattern") or "").upper(),
            "latest_buy_size_class": size_class,
            "latest_estimated_spend_usd": estimated,
            "latest_is_first_meaningful_buy": bool(int(safe_number(event.get("is_first_meaningful_buy")))),
            "first_meaningful_buy_usd": safe_number(row.get("first_meaningful_buy_usd")),
            "campaign_age_minutes": safe_number(row.get("campaign_age_minutes")),
            "campaign_strength_score": safe_number(row.get("campaign_strength_score")),
            "campaign_strength_label": str(row.get("campaign_strength_label") or "").upper(),
            "strength_components": str(row.get("strength_components") or ""),
            "last_signal_utc": row.get("last_signal_utc") or row.get("last_buy_utc") or "",
            "last_meaningful_buy_utc": row.get("last_meaningful_buy_utc") or "",
            "latest_vs_previous_meaningful_ratio": safe_number(
                row.get("latest_vs_previous_meaningful_ratio")
            ),
            "rapid_accumulation": bool(int(safe_number(row.get("rapid_accumulation")))),
            "buying_pullback": bool(int(safe_number(row.get("buying_pullback")))),
            "converging_trader_count": int(safe_number(row.get("converging_trader_count"))),
            "converging_traders": str(row.get("converging_traders") or ""),
            "scoreable": scoreable,
        })

    return out


def _base_whale_points(activity):
    """
    V11.8.2 smart-money scoring.

    SmartMoneyMonitor v2.2 supplies a bounded campaign-strength score that
    rewards sustained meaningful accumulation. If only legacy v2.1 files are
    available, preserve the prior size-based fallback.
    """
    if not activity.get("scoreable"):
        return 0.0

    confidence = str(activity.get("confidence") or "").lower()
    if "verified" not in confidence or "unverified" in confidence:
        return 0.0

    campaign_strength = safe_number(activity.get("campaign_strength_score"))
    if campaign_strength > 0:
        return campaign_strength

    # Legacy v2.1 fallback.
    size_class = str(activity.get("latest_buy_size_class") or "").upper()
    spend = safe_number(activity.get("latest_estimated_spend_usd"))
    first_meaningful = bool(activity.get("latest_is_first_meaningful_buy"))

    if first_meaningful and spend >= 500:
        return 15.0
    if size_class == "STRONG" or spend >= 2000:
        return 20.0
    if size_class == "MEANINGFUL" or spend >= 500:
        return 12.0
    if size_class == "SMALL" or spend >= 100:
        return 5.0
    return 0.0


def candidate_whale_score(candidate, activities, settings):
    token = str(candidate.get("token_address") or "")
    symbol = str(candidate.get("symbol") or "").upper()

    # CryptoTracker is currently a Solana trader. Matching by mint is safest.
    matches = [
        a for a in activities
        if a.get("chain") == "solana"
        and a.get("token_mint") == token
    ]

    # Fallback by symbol ONLY within Solana, never cross-chain.
    if not matches and symbol:
        matches = [
            a for a in activities
            if a.get("chain") == "solana"
            and a.get("token_symbol") == symbol
        ]

    if not matches:
        return 0.0, [], "NONE"

    total = 0.0
    traders = set()
    details = []

    for a in matches:
        pts = _base_whale_points(a)

        first_meaningful = bool(a.get("latest_is_first_meaningful_buy"))
        p1h = safe_number(candidate.get("price_1h"))
        late_penalty = 0.0

        # v2.2 strength already includes an extension penalty. Retain the
        # old CryptoTracker penalty only for legacy v2.1 activities.
        if safe_number(a.get("campaign_strength_score")) <= 0 and pts > 0 and not first_meaningful:
            if p1h > 100:
                late_penalty = 10.0
            elif p1h > 30:
                late_penalty = 5.0
            pts -= late_penalty

        trader_id = a.get("trader_handle") or a.get("trader_name")
        if pts > 0:
            traders.add(trader_id)
        total += pts

        details.append({
            **a,
            "points": pts,
            "first_meaningful_bonus": first_meaningful,
            "late_extension_penalty": late_penalty,
        })

    if len(traders) >= 2:
        total += float(settings.get("SMART_MONEY_MULTI_WHALE_BONUS", 10))

    total = max(
        -10.0,
        min(float(settings.get("SMART_MONEY_MAX_BONUS", 25)), total),
    )

    source = "+".join(sorted(traders)) if traders else "OBSERVED_ZERO"
    return total, details, source


def _delta_rank_bonus(candidate, settings):
    """Small capped ranking tie-breaker after the delta gate has passed."""
    delta = max(0.0, safe_number(candidate.get("score_delta")))
    cap = max(0.0, float(settings.get("DELTA_RANK_MAX_BONUS", 5.0)))
    # 0.10 point per delta point, capped. Extreme one-scan jumps no longer dominate.
    return min(cap, delta * 0.10)


def apply_whale_scores(candidates, settings):
    """
    V11: verified/scoreable smart money is the strongest external confirmation,
    but it does not alter the quant score or bypass any quant hard gate.
    """
    activities = load_recent_smart_money(settings)

    for c in candidates:
        quant = safe_number(
            c.get("quant_score_raw", c.get("momentum_score"))
        )
        bonus, details, source = candidate_whale_score(
            c, activities, settings
        )
        social_bonus = safe_number(c.get("social_score_bonus"))

        c["pre_whale_score"] = quant + social_bonus
        c["whale_score_bonus"] = bonus
        c["whale_score_source"] = source
        c["whale_activity"] = details
        c["composite_score"] = quant + social_bonus + bonus

        # V11.8: delta remains a hard eligibility feature, but extreme one-scan
        # jumps no longer dominate ranking. Use only a small capped tie-breaker.
        c["entry_priority_score"] = (
            quant
            + _delta_rank_bonus(c, settings)
            + bonus
            + social_bonus
        )

    return candidates


def _warn_api_once(key, message, cooldown_seconds=1800):
    now = time.time()
    if now - _API_WARNING_LAST.get(key, 0.0) >= cooldown_seconds:
        print(f"  {message}")
        _API_WARNING_LAST[key] = now


def load_birdeye_smart_money(settings):
    """Fetch/caches Birdeye aggregate Smart Money token flow (optional)."""
    if not bool(settings.get("BIRDEYE_SMART_MONEY_ENABLED", 1)):
        return {}

    api_key = str(os.getenv("BIRDEYE_API_KEY") or "").strip()
    if not api_key:
        _warn_api_once("birdeye-key", "Birdeye Smart Money inactive: BIRDEYE_API_KEY not set.")
        return {}

    now = time.time()
    refresh = float(settings.get("BIRDEYE_SMART_MONEY_REFRESH_SECONDS", 300))
    if now - _BIRDEYE_SMART_CACHE.get("fetched_at", 0.0) < refresh:
        return _BIRDEYE_SMART_CACHE.get("tokens", {})

    interval = str(os.getenv("BIRDEYE_SMART_MONEY_INTERVAL") or "1d").strip()
    style = str(os.getenv("BIRDEYE_SMART_MONEY_TRADER_STYLE") or "trenchers").strip()
    merged = {}

    try:
        for sort_by in ("smart_traders_no", "net_flow"):
            r = requests.get(
                "https://public-api.birdeye.so/smart-money/v1/token/list",
                headers={"X-API-KEY": api_key, "x-chain": "solana", "Accept": "application/json"},
                params={
                    "interval": interval,
                    "trader_style": style,
                    "sort_by": sort_by,
                    "sort_type": "desc",
                    "offset": 0,
                    "limit": 20,
                },
                timeout=20,
            )
            if not r.ok:
                raise RuntimeError(f"HTTP {r.status_code}: {r.text[:250]}")
            body = r.json()
            for row in body.get("data") or []:
                token = str(row.get("token") or "")
                if not token:
                    continue
                current = merged.get(token, {})
                # Same token can appear in both rankings; do not double-count flow.
                merged[token] = {
                    "token": token,
                    "symbol": str(row.get("symbol") or current.get("symbol") or ""),
                    "net_flow": safe_number(row.get("net_flow", current.get("net_flow"))),
                    "smart_traders_no": max(
                        int(safe_number(row.get("smart_traders_no"))),
                        int(safe_number(current.get("smart_traders_no"))),
                    ),
                    "trader_style": str(row.get("trader_style") or current.get("trader_style") or style),
                    "market_cap": safe_number(row.get("market_cap", current.get("market_cap"))),
                    "liquidity": safe_number(row.get("liquidity", current.get("liquidity"))),
                }

        _BIRDEYE_SMART_CACHE["fetched_at"] = now
        _BIRDEYE_SMART_CACHE["tokens"] = merged
        return merged
    except Exception as exc:
        _warn_api_once("birdeye-fetch", f"Birdeye Smart Money warning: {exc}", 900)
        return _BIRDEYE_SMART_CACHE.get("tokens", {})


def candidate_birdeye_smart_score(candidate, token_map, settings):
    row = token_map.get(str(candidate.get("token_address") or ""))
    if not row:
        return 0.0, None

    flow = safe_number(row.get("net_flow"))
    traders = int(safe_number(row.get("smart_traders_no")))
    min_traders = int(settings.get("BIRDEYE_MIN_SMART_TRADERS", 2))
    max_bonus = float(settings.get("BIRDEYE_SMART_MONEY_MAX_BONUS", 15.0))
    max_penalty = float(settings.get("BIRDEYE_SMART_MONEY_MAX_PENALTY", 10.0))

    points = 0.0
    if flow > 0:
        points += 2.0
        if flow >= 500:
            points += 1.0
        if flow >= 2_500:
            points += 2.0
        if flow >= 10_000:
            points += 2.0
    elif flow < 0:
        points -= min(max_penalty, 2.0 + min(8.0, abs(flow) / 2_500.0))

    if traders >= min_traders:
        points += 2.0
    if traders >= 5:
        points += 2.0
    if traders >= 10:
        points += 2.0
    if traders >= 25:
        points += 1.0
    if str(row.get("trader_style") or "").lower() == "trenchers":
        points += 1.0

    points = max(-max_penalty, min(max_bonus, points))
    return points, row


def apply_birdeye_smart_money_scores(candidates, settings):
    token_map = load_birdeye_smart_money(settings)
    for c in candidates:
        bonus, detail = candidate_birdeye_smart_score(c, token_map, settings)
        c["birdeye_smart_bonus"] = bonus
        c["birdeye_smart_detail"] = detail or {}
        c["composite_score"] = safe_number(c.get("composite_score", c.get("momentum_score"))) + bonus
        c["entry_priority_score"] = safe_number(c.get("entry_priority_score", c.get("momentum_score"))) + bonus
    return candidates


def _normalize_post_text(text):
    value = re.sub(r"https?://\S+", "", str(text or "").lower())
    value = re.sub(r"\s+", " ", value).strip()
    return value



X_API_USAGE_FIELDS = [
    "requested_at",
    "date_local",
    "source",
    "endpoint",
    "symbol",
    "token_address",
    "http_status",
    "success",
    "posts_returned",
    "bonus",
    "cache_hit",
]


def log_x_api_usage(
    settings,
    *,
    source,
    endpoint,
    symbol="",
    token_address="",
    http_status="",
    success=0,
    posts_returned=0,
    bonus=0.0,
    cache_hit=0,
):
    """
    Audit actual X API usage without writing bearer tokens, headers, or secrets.
    One row = one targeted lookup attempt. Cached results are logged separately
    only when explicitly requested with cache_hit=1.
    """
    if not bool(settings.get("X_API_USAGE_LOG_ENABLED", 1)):
        return

    try:
        exists = X_API_USAGE_FILE.exists()
        now = datetime.now()
        with X_API_USAGE_FILE.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=X_API_USAGE_FIELDS)
            if not exists:
                writer.writeheader()
            writer.writerow({
                "requested_at": now.isoformat(),
                "date_local": now.date().isoformat(),
                "source": source,
                "endpoint": endpoint,
                "symbol": symbol,
                "token_address": token_address,
                "http_status": http_status,
                "success": int(bool(success)),
                "posts_returned": int(safe_number(posts_returned)),
                "bonus": safe_number(bonus),
                "cache_hit": int(bool(cache_hit)),
            })
    except Exception as exc:
        print(f"  X usage log warning: {exc}")


def x_api_daily_stats(report_date=None):
    """
    Summarize TARGETED Token-X traffic only. This makes the paid X account's
    incremental use measurable without counting the retired macro monitor.
    """
    report_date = report_date or datetime.now().date().isoformat()
    summary = {
        "requests": 0,
        "successes": 0,
        "errors": 0,
        "hits": 0,
        "posts": 0,
        "unique_tokens": 0,
    }

    if not X_API_USAGE_FILE.exists():
        return summary

    tokens = set()
    try:
        with X_API_USAGE_FILE.open("r", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if str(row.get("date_local") or "") != report_date:
                    continue
                if str(row.get("source") or "") != "TOKEN_X":
                    continue
                # Actual paid request rows only. Cache hits are not API calls.
                if int(safe_number(row.get("cache_hit"))) != 0:
                    continue

                summary["requests"] += 1
                success = int(safe_number(row.get("success"))) != 0
                if success:
                    summary["successes"] += 1
                else:
                    summary["errors"] += 1
                summary["posts"] += int(safe_number(row.get("posts_returned")))
                if safe_number(row.get("bonus")) > 0:
                    summary["hits"] += 1
                token = str(row.get("token_address") or "").strip()
                if token:
                    tokens.add(token)

        summary["unique_tokens"] = len(tokens)
    except Exception as exc:
        print(f"  X usage stats warning: {exc}")

    return summary


def token_social_signal(candidate, settings):
    """Candidate-specific X mention velocity. Confirmation only; never bypasses quant gates."""
    if not bool(settings.get("TOKEN_SOCIAL_ENABLED", 1)):
        return {"bonus": 0.0, "status": "DISABLED"}

    bearer = str(os.getenv("X_BEARER_TOKEN") or "").strip()
    if not bearer:
        _warn_api_once("x-token-key", "Token social inactive: X_BEARER_TOKEN not set.")
        return {"bonus": 0.0, "status": "NO_KEY"}

    token = str(candidate.get("token_address") or "")
    symbol = str(candidate.get("symbol") or "").strip()
    if not token:
        return {"bonus": 0.0, "status": "NO_TOKEN"}

    cache_seconds = float(settings.get("TOKEN_SOCIAL_CACHE_SECONDS", 300))
    cached = _TOKEN_SOCIAL_CACHE.get(token)
    if cached and time.time() - cached.get("fetched_at", 0.0) < cache_seconds:
        return cached.get("result", {"bonus": 0.0, "status": "CACHE_EMPTY"})

    terms = [f'"{token}"']
    if symbol and 2 <= len(symbol) <= 15 and re.fullmatch(r"[A-Za-z0-9_]+", symbol):
        terms.append(f'"${symbol}"')
    query = "(" + " OR ".join(terms) + ") -is:retweet"

    try:
        r = requests.get(
            "https://api.x.com/2/tweets/search/recent",
            headers={"Authorization": f"Bearer {bearer}"},
            params={
                "query": query,
                "max_results": 10,
                "tweet.fields": "created_at,author_id,public_metrics",
            },
            timeout=20,
        )
        if not r.ok:
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:250]}")
        posts = r.json().get("data") or []

        now = datetime.now(timezone.utc)
        lookback = float(settings.get("TOKEN_SOCIAL_LOOKBACK_MINUTES", 30))
        rows = []
        for post in posts:
            dt = _parse_utc(post.get("created_at"))
            if dt is None:
                continue
            age = max(0.0, (now - dt).total_seconds() / 60.0)
            if age <= lookback:
                rows.append((age, post))

        posts10 = [p for age, p in rows if age <= 10]
        posts30 = [p for age, p in rows if age <= 30]
        authors10 = {str(p.get("author_id") or "") for p in posts10 if p.get("author_id")}
        authors30 = {str(p.get("author_id") or "") for p in posts30 if p.get("author_id")}
        contract_mentions = sum(token.lower() in str(p.get("text") or "").lower() for p in posts30)

        recent_rate = len(posts10) / 10.0
        older_count = max(0, len(posts30) - len(posts10))
        older_rate = older_count / 20.0
        velocity_ratio = recent_rate / max(0.05, older_rate)

        normalized = [_normalize_post_text(p.get("text")) for p in posts30]
        unique_texts = len({x for x in normalized if x})
        duplicate_ratio = 0.0 if not normalized else max(0.0, 1.0 - unique_texts / len(normalized))

        engagement = 0
        for p in posts30:
            m = p.get("public_metrics") or {}
            engagement += sum(int(safe_number(m.get(k))) for k in ("like_count", "retweet_count", "reply_count", "quote_count"))

        points = 0.0
        if len(posts10) >= 2: points += 2
        if len(posts10) >= 4: points += 2
        if len(authors10) >= 2: points += 2
        if len(authors10) >= 4: points += 2
        if contract_mentions >= 1: points += 2
        if contract_mentions >= 3: points += 1
        if velocity_ratio >= 1.5: points += 1
        if velocity_ratio >= 2.5: points += 1
        if engagement >= 10: points += 1
        if duplicate_ratio >= 0.50: points -= 3

        max_bonus = float(settings.get("TOKEN_SOCIAL_MAX_BONUS", 12.0))
        bonus = max(0.0, min(max_bonus, points))
        top_posts = []
        for age, p in sorted(rows, key=lambda x: x[0])[:5]:
            m = p.get("public_metrics") or {}
            post_engagement = sum(
                int(safe_number(m.get(k)))
                for k in ("like_count", "retweet_count", "reply_count", "quote_count")
            )
            top_posts.append({
                "age_minutes": round(age, 1),
                "author_id": str(p.get("author_id") or ""),
                "engagement": post_engagement,
                "text": str(p.get("text") or "").replace("\n", " ")[:240],
            })

        result = {
            "bonus": bonus,
            "status": "OK",
            "posts_10m": len(posts10),
            "posts_30m": len(posts30),
            "unique_authors_10m": len(authors10),
            "unique_authors_30m": len(authors30),
            "contract_mentions": contract_mentions,
            "velocity_ratio": velocity_ratio,
            "duplicate_ratio": duplicate_ratio,
            "engagement": engagement,
            "top_posts": top_posts,
            "query": query,
        }
        log_x_api_usage(
            settings,
            source="TOKEN_X",
            endpoint="/2/tweets/search/recent",
            symbol=symbol,
            token_address=token,
            http_status=r.status_code,
            success=1,
            posts_returned=len(posts),
            bonus=bonus,
            cache_hit=0,
        )
        _TOKEN_SOCIAL_CACHE[token] = {"fetched_at": time.time(), "result": result}
        return result
    except Exception as exc:
        status_code = ""
        try:
            status_code = r.status_code
        except Exception:
            pass
        log_x_api_usage(
            settings,
            source="TOKEN_X",
            endpoint="/2/tweets/search/recent",
            symbol=symbol,
            token_address=token,
            http_status=status_code,
            success=0,
            posts_returned=0,
            bonus=0.0,
            cache_hit=0,
        )
        _warn_api_once("x-token-search", f"Token-specific X search warning: {exc}", 900)
        result = {"bonus": 0.0, "status": "ERROR"}
        _TOKEN_SOCIAL_CACHE[token] = {"fetched_at": time.time(), "result": result}
        return result


def apply_token_social_scores(candidates, settings):
    if not bool(settings.get("TOKEN_SOCIAL_ENABLED", 1)):
        return candidates

    eligible = []
    for c in candidates:
        if str(c.get("momentum_state") or "").upper() != "SURGING":
            continue
        paths = _entry_path_checks(c, settings)
        if paths["NORMAL"]["passed"] or paths["EARLY_ACCEL"]["passed"]:
            eligible.append(c)

    eligible.sort(key=lambda c: safe_number(c.get("entry_priority_score", c.get("momentum_score"))), reverse=True)
    top_n = max(0, int(settings.get("TOKEN_SOCIAL_TOP_N", 2)))
    selected_ids = {id(c) for c in eligible[:top_n]}

    for c in candidates:
        if id(c) in selected_ids:
            sig = token_social_signal(c, settings)
        else:
            sig = {"bonus": 0.0, "status": "NOT_QUERIED"}
        bonus = safe_number(sig.get("bonus"))
        c["token_social_bonus"] = bonus
        c["token_social_detail"] = sig
        c["composite_score"] = safe_number(c.get("composite_score", c.get("momentum_score"))) + bonus
        c["entry_priority_score"] = safe_number(c.get("entry_priority_score", c.get("momentum_score"))) + bonus
    return candidates



# ============================================================
# V11.6 GPT-5.6 LUNA — BOUNDED SECONDARY CONFIRMATION
# ============================================================

AI_CONFIRMATION_FIELDS = [
    "reviewed_at",
    "symbol",
    "token_address",
    "entry_path",
    "quant_score",
    "score_delta",
    "composite_before_ai",
    "assessment",
    "confidence",
    "risk_level",
    "contradiction_detected",
    "setup_type",
    "continuation_band",
    "ai_bonus",
    "summary",
    "strengths_json",
    "risks_json",
    "model",
    "input_tokens",
    "output_tokens",
    "total_tokens",
]


def _openai_model_name():
    return str(os.getenv("OPENAI_MODEL") or "gpt-5.6-luna").strip()


def _extract_responses_output_text(payload):
    if isinstance(payload, dict) and payload.get("output_text"):
        return str(payload.get("output_text") or "")

    parts = []
    for item in (payload or {}).get("output") or []:
        for content in item.get("content") or []:
            if content.get("type") in {"output_text", "text"}:
                value = content.get("text")
                if value:
                    parts.append(str(value))
    return "\n".join(parts).strip()


def _append_ai_confirmation_log(row):
    _append_csv_schema_safe(AI_CONFIRMATION_LOG_FILE, AI_CONFIRMATION_FIELDS, row)


def _ai_bonus_from_review(review, settings):
    """
    The model does NOT choose its own score adjustment.

    Code maps assessment + confidence into a bounded adjustment:
      high-confidence positive/negative -> +/- max bonus
      moderate-confidence              -> +/- 60% of max bonus
      neutral / low-confidence         -> 0
    """
    assessment = str(review.get("assessment") or "NEUTRAL").upper()
    confidence = int(safe_number(review.get("confidence")))
    min_conf = int(settings.get("AI_CONFIRMATION_MIN_CONFIDENCE", 60))
    high_conf = int(settings.get("AI_CONFIRMATION_HIGH_CONFIDENCE", 80))
    standard_max = abs(float(settings.get("AI_CONFIRMATION_MAX_BONUS", 5.0)))
    setup_type = str(review.get("setup_type") or "").upper()
    positive_max = (
        abs(float(settings.get("AI_HEALTHY_SURGE_MAX_BONUS", 8.0)))
        if setup_type == "HEALTHY_SURGE"
        else standard_max
    )

    if assessment not in {"POSITIVE", "NEGATIVE"} or confidence < min_conf:
        return 0.0

    cap = positive_max if assessment == "POSITIVE" else standard_max
    magnitude = cap if confidence >= high_conf else cap * 0.60
    return round(magnitude if assessment == "POSITIVE" else -magnitude, 2)


def _recent_token_snapshot_history(token_address, max_points=6):
    """Return the most recent intraday scanner snapshots for one token.

    This reuses CryptoTracker's existing daily snapshot CSV, so V11.7 gains
    trajectory context without another API call. Newest point is last.
    """
    token = str(token_address or "")
    if not token:
        return []
    path = auto_snapshot_file()
    if not path.exists():
        return []
    rows = []
    try:
        with path.open("r", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if str(row.get("token_address") or "") != token:
                    continue
                rows.append({
                    "timestamp": str(row.get("timestamp") or ""),
                    "score": round(safe_number(row.get("momentum_score")), 2),
                    "score_delta": round(safe_number(row.get("score_delta")), 2),
                    "price_5m_pct": round(safe_number(row.get("price_5m")), 3),
                    "price_1h_pct": round(safe_number(row.get("price_1h")), 3),
                    "volume_5m_usd": round(safe_number(row.get("volume_5m")), 2),
                    "volume_acceleration": round(safe_number(row.get("volume_acceleration")), 3),
                    "buy_sell_ratio_5m": round(safe_number(row.get("buy_sell_ratio_5m")), 3),
                    "transactions_5m": int(safe_number(row.get("buys_5m")) + safe_number(row.get("sells_5m"))),
                    "liquidity_usd": round(safe_number(row.get("liquidity")), 2),
                })
    except Exception as exc:
        print(f"  AI history read warning: {exc}")
        return []
    return rows[-max(2, int(max_points)):]


def _trajectory_summary(points):
    """Small deterministic context block; Luna still evaluates the pattern."""
    if not points:
        return {"points_available": 0}
    first, last = points[0], points[-1]
    scores = [safe_number(x.get("score")) for x in points]
    vols = [safe_number(x.get("volume_5m_usd")) for x in points]
    ratios = [safe_number(x.get("buy_sell_ratio_5m")) for x in points]
    return {
        "points_available": len(points),
        "score_change_window": round(scores[-1] - scores[0], 2),
        "score_rising_points": sum(1 for a, b in zip(scores, scores[1:]) if b > a),
        "score_falling_points": sum(1 for a, b in zip(scores, scores[1:]) if b < a),
        "volume_change_pct_window": round(pct_change(vols[-1], vols[0]), 2) if vols and vols[0] else 0.0,
        "buy_sell_ratio_change_window": round(ratios[-1] - ratios[0], 3) if ratios else 0.0,
        "first_timestamp": first.get("timestamp", ""),
        "last_timestamp": last.get("timestamp", ""),
    }


def _ai_candidate_payload(candidate, settings):
    token_x = candidate.get("token_social_detail") or {}
    whales = candidate.get("whale_activity") or []
    token = str(candidate.get("token_address") or "")
    history = _recent_token_snapshot_history(token, max_points=6)

    whale_summary = []
    for w in whales[:3]:
        whale_summary.append({
            "trader": w.get("trader_name") or w.get("trader_handle") or "",
            "points": safe_number(w.get("points")),
            "largest_buy_usd": safe_number(w.get("largest_buy_usd")),
            "campaign_total_usd": safe_number(w.get("total_spend_usd")),
            "latest_buy_usd": safe_number(w.get("latest_estimated_spend_usd")),
            "age_minutes": safe_number(w.get("age_minutes")),
            "pattern": w.get("campaign_pattern") or "",
        })

    return {
        "symbol": str(candidate.get("symbol") or ""),
        "entry_path": surge_entry_path(candidate, settings),
        "quant": {
            "score": safe_number(
                candidate.get("quant_score_raw", candidate.get("momentum_score"))
            ),
            "score_delta": safe_number(candidate.get("score_delta")),
            "price_5m_pct": safe_number(candidate.get("price_5m")),
            "price_1h_pct": safe_number(candidate.get("price_1h")),
            "volume_5m_usd": safe_number(candidate.get("volume_5m")),
            "volume_1h_usd": safe_number(candidate.get("volume_1h")),
            "volume_acceleration": safe_number(candidate.get("volume_acceleration")),
            "buy_sell_ratio_5m": safe_number(candidate.get("buy_sell_ratio_5m")),
            "transactions_5m": int(
                safe_number(candidate.get("buys_5m"))
                + safe_number(candidate.get("sells_5m"))
            ),
            "liquidity_usd": safe_number(candidate.get("liquidity")),
            "cross_scan_price_delta_pct": safe_number(candidate.get("price_delta_pct")),
            "cross_scan_volume_delta_pct": safe_number(candidate.get("volume_delta_pct")),
            "cross_scan_liquidity_delta_pct": safe_number(candidate.get("liquidity_delta_pct")),
            "elapsed_minutes_since_previous_scan": safe_number(candidate.get("elapsed_minutes")),
        },
        "momentum_trajectory": {
            "summary": _trajectory_summary(history),
            "recent_points": history,
        },
        "momentum_phase": {
            "reacceleration_ready": bool(candidate.get("reacceleration_ready")),
            "reacceleration_state": str(candidate.get("reacceleration_watch") or ""),
            "reacceleration_age_minutes": safe_number(candidate.get("reacceleration_age_minutes")),
            "reacceleration_watch_reason": str(candidate.get("reacceleration_watch_reason") or ""),
            "reacceleration_peak_5m_pct": candidate.get("reacceleration_peak_5m_pct", ""),
            "reacceleration_peak_1h_pct": candidate.get("reacceleration_peak_1h_pct", ""),
        },
        "market_structure": {
            "market_cap_usd": safe_number(candidate.get("market_cap")),
            "holder_count": int(safe_number(candidate.get("holder_count"))),
            "holder_count_capped": bool(candidate.get("holder_count_capped")),
            "holder_change_10m": candidate.get("holder_change_10m", ""),
            "holder_change_10m_pct": candidate.get("holder_change_10m_pct", ""),
            "holder_change_30m": candidate.get("holder_change_30m", ""),
            "holder_change_30m_pct": candidate.get("holder_change_30m_pct", ""),
            "market_cap_per_holder": safe_number(
                candidate.get("market_cap_per_holder")
            ),
        },
        "confirmations": {
            "verified_whale_bonus": safe_number(candidate.get("whale_score_bonus")),
            "verified_whales": whale_summary,
            "targeted_x_bonus": safe_number(candidate.get("token_social_bonus")),
            "targeted_x": {
                "status": token_x.get("status", ""),
                "posts_10m": int(safe_number(token_x.get("posts_10m"))),
                "posts_30m": int(safe_number(token_x.get("posts_30m"))),
                "unique_authors_10m": int(
                    safe_number(token_x.get("unique_authors_10m"))
                ),
                "unique_authors_30m": int(
                    safe_number(token_x.get("unique_authors_30m"))
                ),
                "contract_mentions": int(
                    safe_number(token_x.get("contract_mentions"))
                ),
                "velocity_ratio": safe_number(token_x.get("velocity_ratio")),
                "duplicate_ratio": safe_number(token_x.get("duplicate_ratio")),
                "engagement": int(safe_number(token_x.get("engagement"))),
                "recent_posts": (token_x.get("top_posts") or [])[:5],
            },
        },
        "important_constraints": {
            "quant_gates_already_passed": True,
            "ai_cannot_override_quant": True,
            "ai_is_secondary_confirmation_only": True,
        },
    }


def luna_candidate_review(candidate, settings):
    """
    Review an already quant-valid candidate with GPT-5.6 Luna.

    Failure is neutral and non-blocking. The model cannot place trades and
    receives no private key, wallet signing material, or API credentials.
    """
    if not bool(settings.get("AI_CONFIRMATION_ENABLED", 1)):
        return {
            "status": "DISABLED",
            "assessment": "NEUTRAL",
            "confidence": 0,
            "ai_bonus": 0.0,
        }

    api_key = str(os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        _warn_api_once(
            "openai-key",
            "Luna confirmation inactive: OPENAI_API_KEY not set.",
            1800,
        )
        return {
            "status": "NO_KEY",
            "assessment": "NEUTRAL",
            "confidence": 0,
            "ai_bonus": 0.0,
        }

    token = str(candidate.get("token_address") or "")
    cache_seconds = max(
        60,
        int(settings.get("AI_CONFIRMATION_CACHE_SECONDS", 300)),
    )
    cached = _AI_CONFIRMATION_CACHE.get(token)
    if (
        cached
        and time.time() - safe_number(cached.get("fetched_at")) < cache_seconds
    ):
        result = dict(cached.get("result") or {})
        result["status"] = "CACHED"
        return result

    model = _openai_model_name()
    candidate_data = _ai_candidate_payload(candidate, settings)

    schema = {
        "type": "object",
        "properties": {
            "assessment": {
                "type": "string",
                "enum": ["POSITIVE", "NEUTRAL", "NEGATIVE"],
            },
            "confidence": {
                "type": "integer",
                "minimum": 0,
                "maximum": 100,
            },
            "risk_level": {
                "type": "string",
                "enum": ["LOW", "MEDIUM", "HIGH"],
            },
            "contradiction_detected": {"type": "boolean"},
            "setup_type": {
                "type": "string",
                "enum": [
                    "EARLY_ACCELERATION",
                    "HEALTHY_SURGE",
                    "REACCELERATION",
                    "LATE_CHASE",
                    "FADING_MOMENTUM",
                    "SOCIAL_PUMP",
                    "LOW_PARTICIPATION",
                    "CONFLICTING_SIGNAL"
                ],
            },
            "continuation_band": {
                "type": "string",
                "enum": ["LOW", "MEDIUM", "HIGH"],
            },
            "summary": {"type": "string"},
            "strengths": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 3,
            },
            "risks": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 3,
            },
        },
        "required": [
            "assessment",
            "confidence",
            "risk_level",
            "contradiction_detected",
            "setup_type",
            "continuation_band",
            "summary",
            "strengths",
            "risks",
        ],
        "additionalProperties": False,
    }

    system_prompt = (
        "You are an independent secondary momentum-pattern analyst for a quant-first "
        "Solana trading system. The hard quantitative entry gates have already passed. "
        "You are NOT the trade decision-maker and must not default toward either caution "
        "or optimism. Evaluate the supplied evidence symmetrically. Your main job is to "
        "distinguish sustainable early acceleration or healthy reacceleration from a "
        "late chase, fading move, low-participation spike, conflicting setup, or likely "
        "socially amplified pump. Use trajectory, not just the latest snapshot: consider "
        "whether score, price momentum, volume, buy/sell flow, transactions, liquidity, "
        "and holder breadth are strengthening or deteriorating across recent scans. "
        "Treat reacceleration as potentially constructive when a previously extended "
        "token reset and independently re-qualified. Evaluate verified whale activity "
        "in context of freshness and liquidity. For targeted-X evidence, consider author "
        "diversity, velocity, engagement, duplicate behavior, and the actual recent post "
        "text; distinguish organic discussion from repetitive promotional hype. Missing "
        "data is uncertainty, not negative evidence. Do not invent facts, future prices, "
        "or precise probabilities. The continuation band is a qualitative research label "
        "for expected near-term momentum persistence, not a calibrated probability. Keep "
        "summary, strengths, and risks concise and evidence-based."
    )

    reasoning_effort = (
        "low"
        if int(settings.get("AI_CONFIRMATION_REASONING_EFFORT", 0)) == 1
        else "none"
    )

    payload = {
        "model": model,
        "reasoning": {"effort": reasoning_effort},
        "max_output_tokens": 450,
        "input": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    "Review this candidate as secondary confirmation only:\n"
                    + json.dumps(candidate_data, separators=(",", ":"))
                ),
            },
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "crypto_candidate_confirmation",
                "strict": True,
                "schema": schema,
            }
        },
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=35,
        )
        if not response.ok:
            raise RuntimeError(
                f"HTTP {response.status_code}: {response.text[:300]}"
            )

        body = response.json()
        raw_text = _extract_responses_output_text(body)
        review = json.loads(raw_text)

        review["assessment"] = str(
            review.get("assessment") or "NEUTRAL"
        ).upper()
        review["risk_level"] = str(
            review.get("risk_level") or "MEDIUM"
        ).upper()
        review["confidence"] = max(
            0,
            min(100, int(safe_number(review.get("confidence")))),
        )
        review["ai_bonus"] = _ai_bonus_from_review(review, settings)
        review["status"] = "OK"
        review["model"] = model

        usage = body.get("usage") or {}
        review["input_tokens"] = int(safe_number(usage.get("input_tokens")))
        review["output_tokens"] = int(safe_number(usage.get("output_tokens")))
        review["total_tokens"] = int(safe_number(usage.get("total_tokens")))

        _AI_CONFIRMATION_CACHE[token] = {
            "fetched_at": time.time(),
            "result": dict(review),
        }

        if not bool(candidate.get("ai_test_mode")):
            _append_ai_confirmation_log({
                    "reviewed_at": datetime.now().isoformat(),
                "symbol": candidate.get("symbol", ""),
                "token_address": token,
                "entry_path": surge_entry_path(candidate, settings),
                "quant_score": safe_number(
                    candidate.get("quant_score_raw", candidate.get("momentum_score"))
                ),
                "score_delta": safe_number(candidate.get("score_delta")),
                "composite_before_ai": safe_number(
                    candidate.get("composite_score", candidate.get("momentum_score"))
                ),
                "assessment": review.get("assessment", ""),
                "confidence": review.get("confidence", 0),
                "risk_level": review.get("risk_level", ""),
                "contradiction_detected": int(
                    bool(review.get("contradiction_detected"))
                ),
                "setup_type": str(review.get("setup_type") or ""),
                "continuation_band": str(review.get("continuation_band") or ""),
                "ai_bonus": review.get("ai_bonus", 0),
                "summary": str(review.get("summary") or "")[:300],
                "strengths_json": json.dumps(
                    review.get("strengths") or [],
                    separators=(",", ":"),
                ),
                "risks_json": json.dumps(
                    review.get("risks") or [],
                    separators=(",", ":"),
                ),
                "model": model,
                "input_tokens": review.get("input_tokens", 0),
                "output_tokens": review.get("output_tokens", 0),
                "total_tokens": review.get("total_tokens", 0),
            })

        return review

    except Exception as exc:
        _warn_api_once(
            "openai-luna-confirmation",
            f"Luna confirmation warning: {exc}",
            900,
        )
        return {
            "status": "ERROR",
            "assessment": "NEUTRAL",
            "confidence": 0,
            "risk_level": "MEDIUM",
            "contradiction_detected": False,
            "setup_type": "CONFLICTING_SIGNAL",
            "continuation_band": "MEDIUM",
            "summary": "",
            "strengths": [],
            "risks": [],
            "ai_bonus": 0.0,
            "model": model,
        }


def apply_ai_confirmation_scores(candidates, settings):
    """
    Query Luna only for the highest-priority SURGING candidates that already
    pass NORMAL or EARLY_ACCEL quant gates.

    AI affects only composite/ranking by a bounded +/- adjustment. It never
    changes momentum_score and cannot rescue a failed quant setup.
    """
    for c in candidates:
        c["ai_confirmation_bonus"] = 0.0
        c["ai_confirmation_detail"] = {
            "status": "NOT_QUERIED",
            "assessment": "NEUTRAL",
            "confidence": 0,
        }

    if not bool(settings.get("AI_CONFIRMATION_ENABLED", 1)):
        return candidates

    eligible = []
    for c in candidates:
        if str(c.get("momentum_state") or "").upper() != "SURGING":
            continue
        checks = _entry_path_checks(c, settings)
        if checks["NORMAL"]["passed"] or checks["EARLY_ACCEL"]["passed"]:
            eligible.append(c)

    eligible.sort(
        key=lambda c: safe_number(
            c.get("entry_priority_score", c.get("momentum_score"))
        ),
        reverse=True,
    )
    top_n = max(0, int(settings.get("AI_CONFIRMATION_TOP_N", 2)))
    selected_ids = {id(c) for c in eligible[:top_n]}

    for c in candidates:
        if id(c) not in selected_ids:
            continue

        review = luna_candidate_review(c, settings)
        bonus = safe_number(review.get("ai_bonus"))

        c["ai_confirmation_bonus"] = bonus
        c["ai_confirmation_detail"] = review
        c["composite_score"] = (
            safe_number(c.get("composite_score", c.get("momentum_score")))
            + bonus
        )
        c["entry_priority_score"] = (
            safe_number(c.get("entry_priority_score", c.get("momentum_score")))
            + bonus
        )

        print(
            f"  Luna AI {c.get('symbol','?')}: "
            f"{review.get('assessment','NEUTRAL')} "
            f"{int(safe_number(review.get('confidence')))}% | "
            f"{bonus:+.0f} pts | "
            f"{review.get('setup_type','?')}/{review.get('continuation_band','?')} | "
            f"{str(review.get('summary') or '')[:120]}"
        )

    return candidates


def ai_daily_stats(report_date):
    summary = {
        "calls": 0,
        "positive": 0,
        "neutral": 0,
        "negative": 0,
        "avg_confidence": 0.0,
        "input_tokens": 0,
        "output_tokens": 0,
    }
    if not AI_CONFIRMATION_LOG_FILE.exists():
        return summary

    confidences = []
    try:
        with AI_CONFIRMATION_LOG_FILE.open(
            "r",
            newline="",
            encoding="utf-8",
        ) as f:
            for row in csv.DictReader(f):
                if not str(row.get("reviewed_at") or "").startswith(report_date):
                    continue
                summary["calls"] += 1
                assessment = str(row.get("assessment") or "NEUTRAL").upper()
                if assessment == "POSITIVE":
                    summary["positive"] += 1
                elif assessment == "NEGATIVE":
                    summary["negative"] += 1
                else:
                    summary["neutral"] += 1

                conf = safe_number(row.get("confidence"))
                confidences.append(conf)
                summary["input_tokens"] += int(
                    safe_number(row.get("input_tokens"))
                )
                summary["output_tokens"] += int(
                    safe_number(row.get("output_tokens"))
                )
    except Exception as exc:
        print(f"  AI daily stats warning: {exc}")

    if confidences:
        summary["avg_confidence"] = sum(confidences) / len(confidences)
    return summary



LUNA_OUTCOME_FIELDS = [
    "report_date",
    "signal_id",
    "symbol",
    "token_address",
    "signal_time",
    "entry_path",
    "local_entry_pass",
    "quant_baseline_group",
    "quant_score",
    "score_delta",
    "ai_assessment",
    "ai_confidence",
    "ai_confidence_band",
    "ai_bonus",
    "ai_risk_level",
    "ai_summary",
    "horizon_minutes",
    "sample_status",
    "outcome_labeled",
    "return_pct",
    "mfe_pct",
    "mae_pct",
]


def generate_luna_outcome_scorecard(settings, report_date=None):
    """
    SHADOW-only Luna outcome scorecard.

    Links each Luna-reviewed SURGING signal to 30/60/120-minute forward outcomes.
    Quant eligibility/path is retained as the baseline context. No thresholds,
    ranking, sizing, entries, or exits are changed by this function.
    """
    if not bool(settings.get("LUNA_OUTCOME_SCORECARD_ENABLED", 1)):
        return {"signals": 0, "outcome_rows": 0, "labeled_rows": 0}

    report_date = report_date or datetime.now(crypto_eod_timezone()).date().isoformat()
    out_path = DATA_DIR / f"luna_outcomes_{report_date}.csv"
    signals = {}
    samples = {}

    if SURGE_FOLLOWUP_FILE.exists():
        try:
            with SURGE_FOLLOWUP_FILE.open("r", newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    if not str(row.get("signal_time") or "").startswith(report_date):
                        continue
                    signal_id = str(row.get("signal_id") or "")
                    if not signal_id:
                        continue
                    record_type = str(row.get("record_type") or "").upper()
                    if record_type == "SIGNAL":
                        assessment = str(row.get("signal_ai_assessment") or "").strip()
                        confidence = safe_number(row.get("signal_ai_confidence"))
                        bonus = safe_number(row.get("signal_ai_bonus"))
                        if assessment or confidence or bonus:
                            signals[signal_id] = row
                    elif record_type == "SAMPLE":
                        horizon = int(safe_number(row.get("horizon_minutes")))
                        if horizon in (30, 60, 120):
                            samples[(signal_id, horizon)] = row
        except Exception as exc:
            print(f"  Luna outcome scorecard warning: {exc}")

    min_conf = int(settings.get("AI_CONFIRMATION_MIN_CONFIDENCE", 60))
    high_conf = int(settings.get("AI_CONFIRMATION_HIGH_CONFIDENCE", 80))
    rows = []

    for signal_id, sig in signals.items():
        conf = int(safe_number(sig.get("signal_ai_confidence")))
        if conf >= high_conf:
            conf_band = "HIGH"
        elif conf >= min_conf:
            conf_band = "MEDIUM"
        else:
            conf_band = "LOW"

        entry_path = str(sig.get("entry_path") or "NONE").upper()
        local_pass = int(safe_number(sig.get("local_entry_pass")))
        baseline = entry_path if local_pass else "REJECTED"

        for horizon in (30, 60, 120):
            sample = samples.get((signal_id, horizon)) or {}
            status = str(sample.get("sample_status") or "MISSING").upper()
            labeled = (
                status == "OK"
                and sample.get("return_pct") not in (None, "")
            )
            rows.append({
                "report_date": report_date,
                "signal_id": signal_id,
                "symbol": sig.get("symbol", ""),
                "token_address": sig.get("token_address", ""),
                "signal_time": sig.get("signal_time", ""),
                "entry_path": entry_path,
                "local_entry_pass": local_pass,
                "quant_baseline_group": baseline,
                "quant_score": safe_number(sig.get("signal_score")),
                "score_delta": safe_number(sig.get("signal_score_delta")),
                "ai_assessment": sig.get("signal_ai_assessment", ""),
                "ai_confidence": conf,
                "ai_confidence_band": conf_band,
                "ai_bonus": safe_number(sig.get("signal_ai_bonus")),
                "ai_risk_level": sig.get("signal_ai_risk_level", ""),
                "ai_summary": str(sig.get("signal_ai_summary") or "")[:300],
                "horizon_minutes": horizon,
                "sample_status": status,
                "outcome_labeled": 1 if labeled else 0,
                "return_pct": sample.get("return_pct", ""),
                "mfe_pct": sample.get("mfe_pct", ""),
                "mae_pct": sample.get("mae_pct", ""),
            })

    try:
        with out_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=LUNA_OUTCOME_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
    except Exception as exc:
        print(f"  Luna outcome CSV warning: {exc}")

    labeled_rows = sum(int(r["outcome_labeled"]) for r in rows)
    if signals:
        print(
            f"  Luna outcome scorecard: {len(signals)} signal(s) | "
            f"{labeled_rows}/{len(rows)} horizon rows labeled"
        )
    return {
        "signals": len(signals),
        "outcome_rows": len(rows),
        "labeled_rows": labeled_rows,
        "path": str(out_path),
    }


def luna_eod_review(report_date, stats, missed, settings):
    """
    Once-per-day learning summary. Observation only; it cannot modify settings.
    """
    if not bool(settings.get("AI_EOD_REVIEW_ENABLED", 1)):
        return ""
    api_key = str(os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        return ""

    model = _openai_model_name()
    review_input = {
        "date": report_date,
        "trades": {
            "completed": int(stats.get("completed", 0)),
            "realized_usd": safe_number(stats.get("realized")),
            "trade_return_pct": safe_number(stats.get("trade_return_pct")),
            "wins": int(stats.get("wins", 0)),
            "losses": int(stats.get("losses", 0)),
            "runners": int(stats.get("runners", 0)),
            "normal_entries": int(stats.get("normal_entries", 0)),
            "early_entries": int(stats.get("early_entries", 0)),
        },
        "missed_opportunities": {
            "rejected_signals": int(missed.get("rejected_signals", 0)),
            "missed_20_30": int(missed.get("missed_20_30", 0)),
            "missed_50_60": int(missed.get("missed_50_60", 0)),
            "best": missed.get("best") or {},
        },
        "paper_research": paper_lab.daily_summary(
            report_date,
            write_files=True,
        ),
        "paper_campaign_walk_forward": paper_lab.campaign_summary(
            write_files=True,
        ),
        "instruction": (
            "Compare the independent paper models and identify one "
            "evidence-based lesson worth investigating. "
            "Do not recommend changing a threshold from one day of data."
        ),
    }

    schema = {
        "type": "object",
        "properties": {
            "lesson": {"type": "string"},
            "confidence": {
                "type": "integer",
                "minimum": 0,
                "maximum": 100,
            },
        },
        "required": ["lesson", "confidence"],
        "additionalProperties": False,
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "reasoning": {"effort": "none"},
                "max_output_tokens": 220,
                "input": [
                    {
                        "role": "system",
                        "content": (
                            "You are a cautious research assistant reviewing one "
                            "day of an automated momentum strategy. Produce only "
                            "a hypothesis/lesson for later testing. Never infer a "
                            "rule change from insufficient evidence."
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(
                            review_input,
                            separators=(",", ":"),
                            default=str,
                        ),
                    },
                ],
                "text": {
                    "format": {
                        "type": "json_schema",
                        "name": "crypto_eod_lesson",
                        "strict": True,
                        "schema": schema,
                    }
                },
            },
            timeout=35,
        )
        if not response.ok:
            raise RuntimeError(
                f"HTTP {response.status_code}: {response.text[:250]}"
            )
        body = response.json()
        parsed = json.loads(_extract_responses_output_text(body))
        lesson = str(parsed.get("lesson") or "").strip()
        confidence = int(safe_number(parsed.get("confidence")))

        existing = load_json(AI_EOD_REVIEW_FILE, {})
        if not isinstance(existing, dict):
            existing = {}
        existing[report_date] = {
            "reviewed_at": datetime.now().isoformat(),
            "model": model,
            "lesson": lesson,
            "confidence": confidence,
            "usage": body.get("usage") or {},
        }
        save_json(AI_EOD_REVIEW_FILE, existing)

        if lesson:
            return f"Luna lesson ({confidence}%): {lesson[:180]}"
    except Exception as exc:
        _warn_api_once(
            "openai-luna-eod",
            f"Luna EOD review warning: {exc}",
            1800,
        )

    return ""




# ============================================================
# V11.2 CONFIRMATION FEED AUDIT (OBSERVATION ONLY)
# ============================================================

CONFIRMATION_FEED_FIELDS = [
    "logged_at",
    "symbol",
    "token_address",
    "momentum_state",
    "quant_score",
    "score_delta",
    "quant_eligible",
    "entry_path",
    "source",
    "status",
    "bonus",
    "summary",
    "detail_json",
]


def _confirmation_feed_state():
    state = load_json(CONFIRMATION_FEED_STATE_FILE, {"last": {}})
    if not isinstance(state, dict):
        state = {"last": {}}
    state.setdefault("last", {})
    return state


def _save_confirmation_feed_state(state):
    try:
        # Keep only today's state keys so the tiny de-dupe file never grows forever.
        today = datetime.now().strftime("%Y-%m-%d")
        last = state.get("last") or {}
        state["last"] = {
            k: v for k, v in last.items()
            if str(v.get("date") or "") == today
        }
        save_json(CONFIRMATION_FEED_STATE_FILE, state)
    except Exception as exc:
        print(f"  Confirmation-feed state warning: {exc}")


def _confirmation_entry_context(candidate, settings):
    try:
        checks = _entry_path_checks(candidate, settings)
        normal = bool(checks["NORMAL"]["passed"])
        early = bool(checks["EARLY_ACCEL"]["passed"])
    except Exception:
        normal = False
        early = False

    if normal:
        path = "NORMAL"
    elif early:
        path = "EARLY_ACCEL"
    else:
        path = "NONE"

    return bool(normal or early), path


def _append_confirmation_feed(candidate, source, status, bonus, summary, detail, settings):
    """
    Best-effort observation log. A logging failure can NEVER change a trade decision.
    De-dupes identical token/source observations for a short configurable window.
    """
    if not bool(settings.get("CONFIRMATION_FEED_LOG_ENABLED", 1)):
        return False

    try:
        ensure_dirs()

        eligible, entry_path = _confirmation_entry_context(candidate, settings)
        now = datetime.now()
        now_iso = now.isoformat()
        token = str(candidate.get("token_address") or "")
        symbol = str(candidate.get("symbol") or token[:8] or "UNKNOWN")
        state_name = str(candidate.get("momentum_state") or "")

        detail = detail if isinstance(detail, dict) else {"value": detail}
        detail_text = json.dumps(detail, separators=(",", ":"), sort_keys=True, default=str)
        signature = json.dumps(
            {
                "status": str(status),
                "bonus": round(safe_number(bonus), 4),
                "summary": str(summary),
                "detail": detail,
                "quant_score": round(
                    safe_number(candidate.get("quant_score_raw", candidate.get("momentum_score"))),
                    2,
                ),
                "score_delta": round(safe_number(candidate.get("score_delta")), 2),
                "state": state_name,
                "eligible": eligible,
                "entry_path": entry_path,
            },
            sort_keys=True,
            default=str,
        )

        dedupe_seconds = max(
            0.0,
            float(settings.get("CONFIRMATION_FEED_DEDUPE_MINUTES", 5)) * 60.0,
        )
        state = _confirmation_feed_state()
        key = f"{token}|{source}"
        prior = (state.get("last") or {}).get(key) or {}
        same_signature = prior.get("signature") == signature
        age_seconds = time.time() - safe_number(prior.get("epoch"))

        if same_signature and age_seconds < dedupe_seconds:
            return False

        row = {
            "logged_at": now_iso,
            "symbol": symbol,
            "token_address": token,
            "momentum_state": state_name,
            "quant_score": safe_number(
                candidate.get("quant_score_raw", candidate.get("momentum_score"))
            ),
            "score_delta": safe_number(candidate.get("score_delta")),
            "quant_eligible": int(eligible),
            "entry_path": entry_path,
            "source": str(source),
            "status": str(status),
            "bonus": safe_number(bonus),
            "summary": str(summary)[:500],
            "detail_json": detail_text[:4000],
        }

        exists = CONFIRMATION_FEED_FILE.exists()
        with CONFIRMATION_FEED_FILE.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CONFIRMATION_FEED_FIELDS)
            if not exists:
                writer.writeheader()
            writer.writerow(row)

        state["last"][key] = {
            "date": now.strftime("%Y-%m-%d"),
            "epoch": time.time(),
            "signature": signature,
        }
        _save_confirmation_feed_state(state)
        return True

    except Exception as exc:
        print(f"  Confirmation-feed log warning: {exc}")
        return False


def log_confirmation_feeds(candidates, settings):
    """
    Persist what each external confirmation layer actually contributed.

    By default only SURGING candidates are audited. Token-X is logged only when it
    was actually queried (top-N quant-valid candidates), so NOT_QUERIED rows do not
    create noise. Zero-hit rows ARE logged for queried/relevant sources, which lets
    us distinguish 'feed active but no match' from 'feed unavailable'.
    """
    if not bool(settings.get("CONFIRMATION_FEED_LOG_ENABLED", 1)):
        return

    surging_only = bool(settings.get("CONFIRMATION_FEED_SURGING_ONLY", 1))

    for c in candidates:
        is_surging = str(c.get("momentum_state") or "").upper() == "SURGING"
        if surging_only and not is_surging:
            continue

        eligible, entry_path = _confirmation_entry_context(c, settings)

        # 1) Existing 13-account macro/ecosystem social layer.
        social_source = str(c.get("social_score_source") or "NONE")
        social_score = safe_number(c.get("social_score"))
        social_bonus = safe_number(c.get("social_score_bonus"))
        social_hit = social_source not in {"", "NONE"} and abs(social_score) > 0
        _append_confirmation_feed(
            c,
            "MACRO_SOCIAL",
            "HIT" if social_hit else "NO_HIT",
            social_bonus,
            (
                f"{social_source} sentiment {social_score:+.2f}"
                if social_hit
                else "No direct token/SOL-ecosystem sentiment match"
            ),
            {
                "score": social_score,
                "score_source": social_source,
                "bonus": social_bonus,
            },
            settings,
        )

        # 2) Local verified SmartMoneyMonitor / Helius wallet layer.
        whale_details = c.get("whale_activity") or []
        whale_bonus = safe_number(c.get("whale_score_bonus"))
        whale_source = str(c.get("whale_score_source") or "NONE")
        positive_whales = [
            w for w in whale_details
            if safe_number(w.get("points")) > 0
        ]
        if positive_whales:
            best_whale = max(
                positive_whales,
                key=lambda w: safe_number(w.get("points")),
            )
            whale_summary = (
                f"{len(positive_whales)} scored wallet/campaign hit(s); "
                f"{best_whale.get('trader_name') or best_whale.get('trader_handle') or 'wallet'} "
                f"+{safe_number(best_whale.get('points')):.0f} pts, "
                f"${safe_number(best_whale.get('latest_estimated_spend_usd')):,.0f} latest buy"
            )
            whale_status = "HIT"
        elif whale_details:
            whale_summary = f"{len(whale_details)} recent wallet observation(s), none scoreable/positive"
            whale_status = "OBSERVED_ZERO"
        else:
            whale_summary = "No recent matched verified wallet activity"
            whale_status = "NO_HIT"

        _append_confirmation_feed(
            c,
            "LOCAL_WHALE",
            whale_status,
            whale_bonus,
            whale_summary,
            {
                "source": whale_source,
                "matched_count": len(whale_details),
                "positive_count": len(positive_whales),
                "activities": [
                    {
                        "trader": w.get("trader_name") or w.get("trader_handle"),
                        "points": safe_number(w.get("points")),
                        "latest_spend_usd": safe_number(w.get("latest_estimated_spend_usd")),
                        "largest_buy_usd": safe_number(w.get("largest_buy_usd")),
                        "campaign_total_usd": safe_number(w.get("total_spend_usd")),
                        "pattern": w.get("campaign_pattern"),
                        "age_minutes": safe_number(w.get("age_minutes")),
                    }
                    for w in whale_details[:5]
                ],
            },
            settings,
        )

        # 3) Birdeye aggregate Smart Money layer.
        b = c.get("birdeye_smart_detail") or {}
        b_bonus = safe_number(c.get("birdeye_smart_bonus"))
        if b:
            smart_traders = int(safe_number(b.get("smart_traders_no")))
            net_flow = safe_number(b.get("net_flow"))
            b_status = "HIT" if b_bonus != 0 or smart_traders > 0 else "OBSERVED_ZERO"
            b_summary = (
                f"{smart_traders} smart trader(s); "
                f"net flow ${net_flow:+,.0f}; "
                f"style {b.get('trader_style') or '—'}"
            )
        else:
            b_status = "NO_HIT"
            b_summary = "Token not present in current Birdeye Smart Money rankings"

        _append_confirmation_feed(
            c,
            "BIRDEYE",
            b_status,
            b_bonus,
            b_summary,
            b,
            settings,
        )

        # 4) Candidate-specific X search. Only log actual queries.
        x = c.get("token_social_detail") or {}
        x_status = str(x.get("status") or "NOT_QUERIED")
        if x_status != "NOT_QUERIED":
            x_bonus = safe_number(c.get("token_social_bonus"))
            if x_status == "OK":
                x_summary = (
                    f"{int(safe_number(x.get('posts_10m')))} posts/10m, "
                    f"{int(safe_number(x.get('posts_30m')))} posts/30m; "
                    f"{int(safe_number(x.get('unique_authors_10m')))} authors/10m; "
                    f"{int(safe_number(x.get('contract_mentions')))} contract mention(s); "
                    f"velocity {safe_number(x.get('velocity_ratio')):.2f}x"
                )
                display_status = "HIT" if x_bonus > 0 else "NO_HIT"
            else:
                x_summary = f"Token-specific X query status: {x_status}"
                display_status = x_status

            _append_confirmation_feed(
                c,
                "TOKEN_X",
                display_status,
                x_bonus,
                x_summary,
                x,
                settings,
            )


def strong_reentry_allowed(candidate, settings):
    """
    Override an active cooldown only for a high-confidence second leg.
    This does NOT bypass Jupiter round-trip preflight or other live safeguards.
    """
    if not bool(settings.get("ALLOW_STRONG_REENTRY", 1)):
        return False

    entries = token_entries_last_minutes(
        candidate["token_address"],
        60,
    )

    if entries >= settings["MAX_ENTRIES_PER_TOKEN_60M"]:
        return False

    tx5 = (
        safe_number(candidate["buys_5m"])
        + safe_number(candidate["sells_5m"])
    )

    checks = [
        candidate["momentum_state"] == "SURGING",
        candidate["momentum_score"] >= settings["REENTRY_MIN_SCORE"],
        candidate["score_delta"] >= settings["REENTRY_MIN_SCORE_DELTA"],
        candidate["liquidity"] >= settings["REENTRY_MIN_LIQUIDITY"],
        candidate["volume_5m"] >= settings["REENTRY_MIN_5M_VOLUME"],
        candidate["volume_acceleration"] >= settings["REENTRY_MIN_VOLUME_ACCEL"],
        candidate["buy_sell_ratio_5m"] >= settings["REENTRY_MIN_BUY_SELL_RATIO"],
        candidate["price_5m"] >= settings["REENTRY_MIN_5M_PCT"],
        candidate["price_5m"] <= settings["REENTRY_MAX_5M_PCT"],
        candidate["price_1h"] >= settings["REENTRY_MIN_1H_PCT"],
        candidate["price_1h"] <= settings["REENTRY_MAX_1H_PCT"],
        tx5 >= settings["REENTRY_MIN_5M_TRANSACTIONS"],
    ]

    return all(checks)


def cooldown_active(token_address, settings):
    cooldowns = load_json(COOLDOWN_FILE, {})
    text = cooldowns.get(token_address)

    if not text:
        return False

    try:
        sold_at = datetime.fromisoformat(text)
    except Exception:
        return False

    return (
        datetime.now() - sold_at
        < timedelta(
            minutes=settings["COOLDOWN_MINUTES"]
        )
    )


def set_cooldown(token_address):
    cooldowns = load_json(COOLDOWN_FILE, {})
    cooldowns[token_address] = datetime.now().isoformat()
    save_json(COOLDOWN_FILE, cooldowns)


def _early_accel_persistence_ok(candidate, settings):
    """Require an EARLY_ACCEL setup to persist across recent scanner observations."""
    points = _recent_token_snapshot_history(candidate.get("token_address"), max_points=6)
    min_points = max(2, int(settings.get("EARLY_CONFIRM_MIN_POINTS", 3)))
    if len(points) < min_points:
        return False, f"early persistence needs {min_points} scans"

    recent = points[-min_points:]
    positive_flow = sum(
        1 for p in recent
        if safe_number(p.get("price_5m_pct")) > 0
        and safe_number(p.get("buy_sell_ratio_5m")) >= 1.20
    )
    rising = sum(
        1 for a, b in zip(recent, recent[1:])
        if safe_number(b.get("score")) > safe_number(a.get("score"))
    )
    if positive_flow < int(settings.get("EARLY_CONFIRM_MIN_POSITIVE_FLOW_POINTS", 2)):
        return False, "early persistence lacks repeated positive flow"
    if rising < int(settings.get("EARLY_CONFIRM_MIN_RISING_SCORE_POINTS", 1)):
        return False, "early persistence lacks score follow-through"
    return True, ""


def entry_reasons(candidate, settings):
    """
    V11: a SURGING token is eligible when EITHER the complete NORMAL path or
    the complete EARLY_ACCEL path passes. This prevents the normal absolute-volume
    floor from accidentally defeating the early-acceleration path.
    """
    failures = []

    if candidate["momentum_state"] != "SURGING":
        failures.append("state != SURGING")
    else:
        paths = _entry_path_checks(candidate, settings)
        if paths["EARLY_ACCEL"]["passed"] and not paths["NORMAL"]["passed"]:
            persistence_ok, persistence_reason = _early_accel_persistence_ok(candidate, settings)
            if not persistence_ok:
                failures.append(persistence_reason)

        if not (paths["NORMAL"]["passed"] or paths["EARLY_ACCEL"]["passed"]):
            # Report the closer path so Pushover/dashboard messages stay concise.
            normal_fail = [r for passed, r in paths["NORMAL"]["checks"] if not passed]
            early_fail = [r for passed, r in paths["EARLY_ACCEL"]["checks"] if not passed]
            if len(early_fail) < len(normal_fail):
                failures.extend([f"early: {r}" for r in early_fail])
            elif len(normal_fail) < len(early_fail):
                failures.extend([f"normal: {r}" for r in normal_fail])
            else:
                # On a tie, favor EARLY_ACCEL when its score/delta threshold is met;
                # otherwise report NORMAL. This makes fresh acceleration diagnostics useful.
                early_score_ready = (
                    candidate["momentum_score"] >= settings["EARLY_ACCEL_MIN_SCORE"]
                    and candidate["score_delta"] >= settings["EARLY_ACCEL_MIN_SCORE_DELTA"]
                )
                chosen = early_fail if early_score_ready else normal_fail
                prefix = "early" if early_score_ready else "normal"
                failures.extend([f"{prefix}: {r}" for r in chosen])

    # V11: enforce the rolling per-token entry cap even after the ordinary
    # cooldown expires. Previously MAX_ENTRIES_PER_TOKEN_60M only constrained
    # the strong-reentry override, which still allowed another normal entry
    # once COOLDOWN_MINUTES elapsed.
    entries_60m = token_entries_last_minutes(candidate["token_address"], 60)
    if entries_60m >= int(settings["MAX_ENTRIES_PER_TOKEN_60M"]):
        failures.append("per-token 60m entry cap")
    else:
        cooldown = cooldown_active(candidate["token_address"], settings)
        if cooldown and not strong_reentry_allowed(candidate, settings):
            failures.append("cooldown")

    return failures


def print_entry_audit(candidate, settings):
    """Print NORMAL and EARLY_ACCEL gate results side-by-side for auditability."""
    tx5 = safe_number(candidate["buys_5m"]) + safe_number(candidate["sells_5m"])
    paths = _entry_path_checks(candidate, settings)
    selected = surge_entry_path(candidate, settings)

    cooldown = cooldown_active(candidate["token_address"], settings)
    reentry_override = cooldown and strong_reentry_allowed(candidate, settings)

    print("  ENTRY AUDIT")
    print(f"    State: {candidate['momentum_state']} | selected path: {selected}")

    labels = [
        ("Score", candidate["momentum_score"], settings["MIN_BUY_SCORE"], settings["EARLY_ACCEL_MIN_SCORE"], ""),
        ("Delta", candidate["score_delta"], settings["MIN_BUY_SCORE_DELTA"], settings["EARLY_ACCEL_MIN_SCORE_DELTA"], "+"),
        ("Liquidity", candidate["liquidity"], settings["MIN_BUY_LIQUIDITY"], settings["EARLY_ACCEL_MIN_LIQUIDITY"], "$"),
        ("5m volume", candidate["volume_5m"], settings["MIN_BUY_5M_VOLUME"], settings["EARLY_ACCEL_MIN_5M_VOLUME"], "$"),
        ("Vol accel", candidate["volume_acceleration"], settings["MIN_BUY_VOLUME_ACCEL"], settings["EARLY_ACCEL_MIN_VOLUME_ACCEL"], "x"),
        ("Buy/sell", candidate["buy_sell_ratio_5m"], settings["MIN_BUY_SELL_RATIO"], settings["EARLY_ACCEL_MIN_BUY_SELL_RATIO"], ""),
        ("5m tx", tx5, settings["MIN_5M_TRANSACTIONS"], settings["EARLY_ACCEL_MIN_5M_TRANSACTIONS"], ""),
    ]
    for label, actual, normal_min, early_min, unit in labels:
        if unit == "$":
            actual_txt=f"${actual:,.0f}"; n_txt=f"${normal_min:,.0f}"; e_txt=f"${early_min:,.0f}"
        elif unit == "x":
            actual_txt=f"{actual:.2f}x"; n_txt=f"{normal_min:.2f}x"; e_txt=f"{early_min:.2f}x"
        elif label == "Delta":
            actual_txt=f"{actual:+.0f}"; n_txt=f"+{normal_min:.0f}"; e_txt=f"+{early_min:.0f}"
        else:
            actual_txt=f"{actual:.0f}" if label in ("Score", "5m tx") else f"{actual:.2f}"
            n_txt=f"{normal_min:.0f}" if label in ("Score", "5m tx") else f"{normal_min:.2f}"
            e_txt=f"{early_min:.0f}" if label in ("Score", "5m tx") else f"{early_min:.2f}"
        print(f"    {label:<12} {actual_txt:<12} | NORMAL >= {n_txt:<10} | EARLY >= {e_txt}")

    print(
        f"    5m move      {candidate['price_5m']:+.1f}% | "
        f"NORMAL {settings['MIN_BUY_5M_PCT']:+.1f}%..{settings['MAX_BUY_5M_PCT']:+.1f}% | "
        f"EARLY {settings['EARLY_ACCEL_MIN_5M_PCT']:+.1f}%..{settings['EARLY_ACCEL_MAX_5M_PCT']:+.1f}%"
    )
    print(
        f"    1h move      {candidate['price_1h']:+.1f}% | "
        f"NORMAL {settings['MIN_BUY_1H_PCT']:+.1f}%..{settings['MAX_BUY_1H_PCT']:+.1f}% | "
        f"EARLY {settings['EARLY_ACCEL_MIN_1H_PCT']:+.1f}%..{settings['EARLY_ACCEL_MAX_1H_PCT']:+.1f}%"
    )

    for path_name in ("NORMAL", "EARLY_ACCEL"):
        fails = [reason for passed, reason in paths[path_name]["checks"] if not passed]
        print(
            f"    {path_name:<11}: "
            + ("PASS" if not fails else "FAIL - " + ", ".join(fails))
        )

    if cooldown:
        print(
            "    Cooldown: "
            + ("OVERRIDDEN by strong re-entry" if reentry_override else "ACTIVE")
        )
    else:
        print("    Cooldown: clear")


def geckoterminal_token_price(token_mint, settings):
    if not bool(settings.get("GECKOTERMINAL_ENABLED", 1)):
        return None
    cached = _GECKO_PRICE_CACHE.get(token_mint)
    if cached and time.time() - cached.get("fetched_at", 0.0) < 30:
        return cached.get("price")
    try:
        r = requests.get(
            f"https://api.geckoterminal.com/api/v2/networks/solana/tokens/{token_mint}",
            headers={"Accept": "application/json"},
            timeout=15,
        )
        if not r.ok:
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
        attrs = ((r.json().get("data") or {}).get("attributes") or {})
        price = safe_number(attrs.get("price_usd"))
        if price <= 0:
            return None
        _GECKO_PRICE_CACHE[token_mint] = {"fetched_at": time.time(), "price": price}
        return price
    except Exception as exc:
        _warn_api_once("gecko-price", f"GeckoTerminal price warning: {exc}", 900)
        return None


def token_decimals_rpc(token_mint):
    if token_mint in _TOKEN_DECIMALS_CACHE:
        return _TOKEN_DECIMALS_CACHE[token_mint]
    try:
        payload = {"jsonrpc": "2.0", "id": 1, "method": "getTokenSupply", "params": [token_mint]}
        r = requests.post(_solana_rpc_url(), json=payload, timeout=15)
        r.raise_for_status()
        body = r.json()
        if body.get("error"):
            raise RuntimeError(str(body["error"]))
        decimals = int((((body.get("result") or {}).get("value") or {}).get("decimals")))
        _TOKEN_DECIMALS_CACHE[token_mint] = decimals
        return decimals
    except Exception as exc:
        _warn_api_once("token-decimals", f"Token-decimals RPC warning: {exc}", 900)
        return None


def jupiter_roundtrip_sample(api_key, token_mint, trade_usdc):
    raw_usdc = int(round(trade_usdc * (10 ** USDC_DECIMALS)))
    buy_quote = jupiter_order(api_key, USDC_MINT, token_mint, raw_usdc)
    token_raw = int(buy_quote.get("outAmount") or 0)
    if token_raw <= 0:
        raise RuntimeError("Buy quote returned zero output.")
    sell_quote = jupiter_order(api_key, token_mint, USDC_MINT, token_raw)
    reverse_raw = int(sell_quote.get("outAmount") or 0)
    return_pct = reverse_raw / raw_usdc * 100.0 if raw_usdc > 0 else 0.0

    implied_price = None
    decimals = token_decimals_rpc(token_mint)
    if decimals is not None:
        token_ui = token_raw / (10 ** decimals)
        if token_ui > 0:
            implied_price = trade_usdc / token_ui

    return {
        "return_pct": return_pct,
        "token_raw": token_raw,
        "reverse_raw": reverse_raw,
        "implied_price_usd": implied_price,
        "buy_router": buy_quote.get("router", ""),
        "sell_router": sell_quote.get("router", ""),
    }


def execution_integrity_check(candidate, api_key, trade_usdc, settings):
    """Cross-source entry check: DEX + GeckoTerminal + two Jupiter round trips."""
    path = surge_entry_path(candidate, settings)
    if path == "EARLY_ACCEL":
        min_roundtrip = float(settings.get("EARLY_MIN_ROUNDTRIP_RETURN_PCT", 98.5))
    else:
        min_roundtrip = float(settings.get("NORMAL_MIN_ROUNDTRIP_RETURN_PCT", settings.get("MIN_ROUNDTRIP_RETURN_PCT", 97.0)))

    if not bool(settings.get("EXECUTION_INTEGRITY_ENABLED", 1)):
        rt = jupiter_roundtrip_sample(api_key, candidate["token_address"], trade_usdc)
        return {"passed": rt["return_pct"] >= min_roundtrip, "reasons": [],
                "worst_roundtrip_pct": rt["return_pct"], "samples": [rt],
                "dex_price_usd": safe_number(candidate.get("price_usd")), "gecko_price_usd": None}

    reasons = []
    dex_price = safe_number(candidate.get("price_usd"))
    gecko_price = geckoterminal_token_price(candidate["token_address"], settings)
    dex_gecko_div = None
    if dex_price > 0 and gecko_price and gecko_price > 0:
        dex_gecko_div = abs(dex_price - gecko_price) / ((dex_price + gecko_price) / 2.0) * 100.0
        if dex_gecko_div > float(settings.get("EXEC_MAX_DEX_GECKO_DIVERGENCE_PCT", 3.0)):
            reasons.append(f"DEX/Gecko divergence {dex_gecko_div:.2f}%")
    elif bool(settings.get("EXEC_REQUIRE_GECKO_PRICE", 0)):
        reasons.append("GeckoTerminal price unavailable")

    samples = []
    sample_count = max(1, int(settings.get("EXEC_ROUNDTRIP_SAMPLES", 2)))
    delay = max(0.0, float(settings.get("EXEC_ROUNDTRIP_SAMPLE_DELAY_SECONDS", 2.0)))
    for i in range(sample_count):
        samples.append(jupiter_roundtrip_sample(api_key, candidate["token_address"], trade_usdc))
        if i + 1 < sample_count and delay > 0:
            time.sleep(delay)

    rts = [safe_number(s.get("return_pct")) for s in samples]
    worst_rt, best_rt = min(rts), max(rts)
    rt_spread = best_rt - worst_rt
    if worst_rt < min_roundtrip:
        reasons.append(f"round-trip {worst_rt:.2f}% < {path} minimum {min_roundtrip:.2f}%")
    if best_rt > float(settings.get("EXEC_MAX_ROUNDTRIP_RETURN_PCT", 100.5)):
        reasons.append(f"round-trip {best_rt:.2f}% anomalously high")
    if rt_spread > float(settings.get("EXEC_MAX_ROUNDTRIP_SAMPLE_SPREAD_PCT", 2.0)):
        reasons.append(f"round-trip samples unstable ({rt_spread:.2f} pts)")

    implied = [safe_number(s.get("implied_price_usd")) for s in samples if safe_number(s.get("implied_price_usd")) > 0]
    implied_price = sum(implied) / len(implied) if implied else None
    consensus_prices = [p for p in (dex_price, gecko_price) if p and p > 0]
    consensus = sum(consensus_prices) / len(consensus_prices) if consensus_prices else None
    jup_div = None
    if implied_price and consensus:
        jup_div = abs(implied_price - consensus) / consensus * 100.0
        if jup_div > float(settings.get("EXEC_MAX_JUPITER_CONSENSUS_DIVERGENCE_PCT", 3.0)):
            reasons.append(f"Jupiter/market price divergence {jup_div:.2f}%")
    elif bool(settings.get("EXEC_REQUIRE_JUPITER_PRICE_CONSENSUS", 0)):
        reasons.append("Jupiter implied-price comparison unavailable")

    return {
        "passed": not reasons,
        "reasons": reasons,
        "worst_roundtrip_pct": worst_rt,
        "best_roundtrip_pct": best_rt,
        "roundtrip_spread_pct": rt_spread,
        "samples": samples,
        "dex_price_usd": dex_price,
        "gecko_price_usd": gecko_price,
        "dex_gecko_divergence_pct": dex_gecko_div,
        "jupiter_implied_price_usd": implied_price,
        "jupiter_consensus_divergence_pct": jup_div,
    }


def preflight_roundtrip(api_key, token_mint, trade_usdc):
    """Backward-compatible single Jupiter round-trip helper."""
    return jupiter_roundtrip_sample(api_key, token_mint, trade_usdc)["return_pct"]


# ============================================================
# POSITION MONITORING
# ============================================================

def jupiter_liquidation_value_usdc(
    api_key,
    token_mint,
    raw_token_amount,
):
    quote = jupiter_order(
        api_key,
        token_mint,
        USDC_MINT,
        int(raw_token_amount),
    )

    return (
        int(quote.get("outAmount") or 0)
        / (10 ** USDC_DECIMALS)
    )


def held_token_momentum(token_address):
    try:
        pairs = ms.get_token_pairs(token_address)
        pair = ms.choose_best_pair(pairs)

        if not pair:
            return None

        metrics = ms.calculate_metrics(pair)
        score = ms.calculate_score(metrics)

        previous = load_previous_snapshots().get(
            token_address
        )

        previous_score = (
            safe_number(
                previous.get("momentum_score")
            )
            if previous else score
        )

        market_cap = scanner_safe_number(
            pair.get("marketCap")
        )
        if market_cap <= 0:
            market_cap = scanner_safe_number(
                pair.get("fdv")
            )

        return {
            "score": score,
            "score_delta": score - previous_score,
            "price_usd": scanner_safe_number(pair.get("priceUsd")),
            "price_5m": metrics["price_5m"],
            "price_1h": metrics["price_1h"],
            "volume_acceleration": metrics[
                "volume_acceleration"
            ],
            "market_cap": market_cap,
        }

    except Exception:
        return None


def update_market_cap_tracking(position, momentum, settings):
    """Update persistent, time-based market-cap trend metrics for an open trade."""
    current_mc = safe_number(
        (momentum or {}).get("market_cap")
    )
    if current_mc <= 0:
        return position

    now = datetime.now()
    window_minutes = max(
        1.0,
        float(settings.get("MC_ROLLING_WINDOW_MINUTES", 5.0)),
    )

    samples = position.get("mc_samples") or []
    cleaned = []
    for sample in samples:
        try:
            dt = datetime.fromisoformat(str(sample.get("time", "")))
            mc = safe_number(sample.get("market_cap"))
            if mc > 0 and (now - dt).total_seconds() <= 15 * 60:
                cleaned.append({"time": dt.isoformat(), "market_cap": mc})
        except Exception:
            continue

    cleaned.append({"time": now.isoformat(), "market_cap": current_mc})
    cutoff = now - timedelta(minutes=window_minutes)
    recent = []
    for sample in cleaned:
        try:
            if datetime.fromisoformat(sample["time"]) >= cutoff:
                recent.append(sample)
        except Exception:
            pass

    if not recent:
        recent = [cleaned[-1]]

    avg_mc = sum(safe_number(x["market_cap"]) for x in recent) / len(recent)
    oldest_mc = safe_number(recent[0]["market_cap"])
    velocity = (
        ((current_mc - oldest_mc) / oldest_mc) * 100.0
        if oldest_mc > 0 else 0.0
    )

    previous_avg = safe_number(position.get("mc_rolling_avg_5m"))
    avg_change = (
        ((avg_mc - previous_avg) / previous_avg) * 100.0
        if previous_avg > 0 else 0.0
    )

    entry_mc = safe_number(position.get("entry_market_cap"))
    if entry_mc <= 0:
        entry_mc = current_mc
        position["entry_market_cap"] = current_mc

    peak_mc = max(
        safe_number(position.get("peak_market_cap")),
        current_mc,
    )

    position["mc_samples"] = cleaned[-30:]
    position["current_market_cap"] = current_mc
    position["peak_market_cap"] = peak_mc
    position["mc_rolling_avg_5m"] = avg_mc
    position["mc_rolling_avg_change_pct"] = avg_change
    position["mc_velocity_5m_pct"] = velocity
    position["mc_vs_avg_pct"] = (
        ((current_mc - avg_mc) / avg_mc) * 100.0
        if avg_mc > 0 else 0.0
    )
    position["mc_gain_from_entry_pct"] = (
        ((current_mc - entry_mc) / entry_mc) * 100.0
        if entry_mc > 0 else 0.0
    )
    position["mc_drawdown_from_peak_pct"] = (
        ((current_mc - peak_mc) / peak_mc) * 100.0
        if peak_mc > 0 else 0.0
    )
    return position


def runner_allowed_drawdown(peak_pnl_pct, settings):
    if peak_pnl_pct >= 50.0:
        return float(settings["RUNNER_DRAWDOWN_50_PLUS_PCT"])
    if peak_pnl_pct >= 25.0:
        return float(settings["RUNNER_DRAWDOWN_25_50_PCT"])
    return float(settings["RUNNER_DRAWDOWN_10_25_PCT"])


def runner_profit_floor(peak_pnl_pct, settings):
    if peak_pnl_pct >= 50.0:
        return float(settings.get("RUNNER_PROFIT_FLOOR_50_PCT", 25.0))
    if peak_pnl_pct >= 30.0:
        return float(settings.get("RUNNER_PROFIT_FLOOR_30_PCT", 15.0))
    if peak_pnl_pct >= 20.0:
        return float(settings.get("RUNNER_PROFIT_FLOOR_20_PCT", 10.0))
    if peak_pnl_pct >= 10.0:
        return float(settings.get("RUNNER_PROFIT_FLOOR_10_PCT", 4.0))
    return None


def choose_exit(position, current_usdc, momentum, settings):
    entry_usdc = float(position["entry_usdc"])

    pnl_pct = (
        (current_usdc - entry_usdc)
        / entry_usdc
        * 100.0
        if entry_usdc > 0 else 0.0
    )

    peak = max(
        float(position.get("peak_pnl_pct", 0)),
        pnl_pct,
    )

    held_minutes = (
        datetime.now()
        - datetime.fromisoformat(
            position["entry_time"]
        )
    ).total_seconds() / 60.0

    runner_mode = bool(position.get("runner_mode", False))
    if peak >= float(settings["RUNNER_ACTIVATE_PCT"]):
        runner_mode = True
    position["runner_mode"] = runner_mode

    current_mc = safe_number(position.get("current_market_cap"))
    avg_mc = safe_number(position.get("mc_rolling_avg_5m"))
    avg_change = safe_number(position.get("mc_rolling_avg_change_pct"))
    mc_velocity = safe_number(position.get("mc_velocity_5m_pct"))

    dex_falling = bool(
        momentum
        and safe_number(momentum.get("price_5m")) < 0
    )
    mc_trend_weak = bool(
        current_mc > 0
        and avg_mc > 0
        and current_mc < avg_mc
        and avg_change < 0
    )
    # V11 soft-exit confirmation is deliberately stricter than the hard-stop
    # confirmation: the token must be below its rolling MC average AND the
    # current market cap must be lower than the oldest point in the rolling
    # window (negative MC velocity). A score wobble alone no longer sells.
    soft_exit_mc_weak = bool(
        current_mc > 0
        and avg_mc > 0
        and current_mc < avg_mc
        and mc_velocity < 0
        and len(position.get("mc_samples") or []) >= 3
    )
    trend_confirms_down = dex_falling or mc_trend_weak

    stop_breaches = int(position.get("stop_loss_breach_count", 0) or 0)
    if pnl_pct <= float(settings["STOP_LOSS_PCT"]):
        stop_breaches += 1
    else:
        stop_breaches = 0
    position["stop_loss_breach_count"] = stop_breaches

    if not (
        peak >= float(settings.get("PRE_RUNNER_PROTECT_ACTIVATE_PCT", 6.0))
        and pnl_pct <= float(settings.get("PRE_RUNNER_PROFIT_FLOOR_PCT", 2.0))
    ):
        position["pre_runner_floor_breach_count"] = 0

    reason = None

    if pnl_pct <= float(settings["EMERGENCY_STOP_PCT"]):
        reason = "EMERGENCY_STOP"

    elif pnl_pct <= float(settings["STOP_LOSS_PCT"]) and (
        trend_confirms_down
        or stop_breaches >= int(settings["STOP_CONFIRMATIONS_REQUIRED"])
    ):
        reason = "STOP_LOSS_CONFIRMED"

    elif runner_mode:
        profit_floor = runner_profit_floor(peak, settings)
        floor_breaches = int(position.get("runner_floor_breach_count", 0) or 0)
        if profit_floor is not None and pnl_pct <= profit_floor:
            floor_breaches += 1
        else:
            floor_breaches = 0
        position["runner_floor_breach_count"] = floor_breaches
        position["last_runner_profit_floor_pct"] = profit_floor

        required_floor_breaches = int(settings.get("RUNNER_FLOOR_CONFIRMATIONS_REQUIRED", 2))
        if profit_floor is not None and floor_breaches >= required_floor_breaches:
            reason = "RUNNER_PROFIT_FLOOR"

        allowed_dd = runner_allowed_drawdown(peak, settings)
        drawdown = peak - pnl_pct

        runner_breaches = int(position.get("runner_drawdown_breach_count", 0) or 0)
        if drawdown >= allowed_dd:
            runner_breaches += 1
        else:
            runner_breaches = 0
        position["runner_drawdown_breach_count"] = runner_breaches

        mc_history_ready = len(position.get("mc_samples") or []) >= 3
        if reason is None and drawdown >= allowed_dd and (
            mc_trend_weak
            or (not mc_history_ready and runner_breaches >= 2)
        ):
            reason = "RUNNER_TREND_BREAK"

        elif reason is None and held_minutes >= float(settings["RUNNER_MAX_HOLD_MINUTES"]):
            reason = "RUNNER_MAX_HOLD"

    elif (
        peak >= float(settings.get("PRE_RUNNER_PROTECT_ACTIVATE_PCT", 6.0))
        and pnl_pct <= float(settings.get("PRE_RUNNER_PROFIT_FLOOR_PCT", 2.0))
    ):
        breaches = int(position.get("pre_runner_floor_breach_count", 0) or 0) + 1
        position["pre_runner_floor_breach_count"] = breaches
        if breaches >= int(settings.get("PRE_RUNNER_FLOOR_CONFIRMATIONS_REQUIRED", 2)):
            reason = "PRE_RUNNER_PROFIT_FLOOR"

    elif (
        held_minutes >= float(settings.get("STAGNANT_EXIT_MINUTES", 15.0))
        and pnl_pct < float(settings.get("STAGNANT_EXIT_MAX_PNL_PCT", 3.0))
        and soft_exit_mc_weak
    ):
        reason = "STAGNANT_15M_MC_WEAK"

    elif held_minutes >= float(settings["MAX_HOLD_MINUTES"]):
        # V11.8: give still-healthy, non-runner positions up to 60m to mature.
        extend_ok = bool(
            held_minutes < float(settings.get("EXTENDED_HOLD_MAX_MINUTES", 60.0))
            and pnl_pct >= float(settings.get("EXTENDED_HOLD_MIN_PNL_PCT", -1.0))
            and not soft_exit_mc_weak
            and momentum
            and safe_number(momentum.get("score")) >= float(settings.get("EXTENDED_HOLD_MIN_SCORE", 60))
            and safe_number(momentum.get("buy_sell_ratio_5m")) >= float(settings.get("EXTENDED_HOLD_MIN_BUY_SELL_RATIO", 1.10))
        )
        if not extend_ok:
            reason = "MAX_HOLD"

    elif (
        momentum
        and held_minutes
        >= float(settings["MOMENTUM_EXIT_GRACE_MINUTES"])
    ):
        require_mc = bool(settings.get("SOFT_EXIT_REQUIRE_MC_CONFIRMATION", 1))
        mc_confirmed = soft_exit_mc_weak or not require_mc

        if (
            momentum["score"] < settings["EXIT_SCORE_BELOW"]
            and mc_confirmed
        ):
            reason = "MOMENTUM_SCORE_FAIL_MC_CONFIRMED"

        elif (
            momentum["score_delta"]
            <= settings["EXIT_SCORE_DELTA_BELOW"]
            and mc_confirmed
        ):
            reason = "MOMENTUM_DELTA_FAIL_MC_CONFIRMED"

        elif (
            momentum["price_5m"] < 0
            and momentum["volume_acceleration"] < 0.75
            and mc_confirmed
        ):
            reason = "MOMENTUM_FADE_MC_CONFIRMED"

    position["peak_pnl_pct"] = peak
    position["last_pnl_pct"] = pnl_pct
    position["last_runner_allowed_drawdown_pct"] = (
        runner_allowed_drawdown(peak, settings)
        if runner_mode else 0.0
    )
    position["last_mc_trend_weak"] = mc_trend_weak
    position["last_soft_exit_mc_weak"] = soft_exit_mc_weak
    position["last_mc_velocity_5m_pct"] = mc_velocity

    return reason, pnl_pct, peak, held_minutes


# ============================================================
# BUY / SELL
# ============================================================

def buy_candidate(
    candidate,
    settings,
    api_key,
    signer,
    wallet_address,
):
    # Guarantee BUY alerts/trade logs have holder data. Normally this is a cache
    # hit because SURGING candidates were enriched before entry selection.
    if bool(settings.get("HOLDER_METRICS_ENABLED", 1)):
        candidate.update(
            holder_metrics_for_token(
                candidate.get("token_address"),
                candidate.get("symbol"),
                candidate.get("market_cap"),
                settings,
            )
        )

    size, tier = choose_trade_size(
        candidate,
        settings,
        wallet_address,
    )

    if size <= 0:
        print("  BUY REJECTED: no spendable USDC available.")
        return None

    integrity = execution_integrity_check(candidate, api_key, size, settings)
    roundtrip = safe_number(integrity.get("worst_roundtrip_pct"))
    sample_text = ", ".join(
        f"{safe_number(s.get('return_pct')):.2f}%" for s in integrity.get("samples", [])
    )
    print(f"  Execution integrity: Jupiter round trips [{sample_text}]")
    if integrity.get("gecko_price_usd"):
        print(
            f"  Price consensus: DEX ${safe_number(integrity.get('dex_price_usd')):.10g} | "
            f"Gecko ${safe_number(integrity.get('gecko_price_usd')):.10g} | "
            f"div {safe_number(integrity.get('dex_gecko_divergence_pct')):.2f}%"
        )

    if not integrity.get("passed"):
        print("  EXECUTION-INTEGRITY REJECTED: " + "; ".join(integrity.get("reasons") or ["unknown integrity failure"]))
        print("  No buy was submitted to Jupiter.")
        return None

    if not settings["LIVE_TRADING"]:
        print(
            f"  PAPER SIGNAL: would BUY "
            f"${size:.2f} {candidate['symbol']}"
        )
        return None

    raw_usdc = int(
        round(size * (10 ** USDC_DECIMALS))
    )

    order, result = real_swap(
        api_key,
        signer,
        wallet_address,
        USDC_MINT,
        candidate["token_address"],
        raw_usdc,
    )

    input_raw = int(
        result.get("totalInputAmount")
        or raw_usdc
    )
    output_raw = int(
        result.get("totalOutputAmount")
        or 0
    )

    if output_raw <= 0:
        raise RuntimeError(
            "Buy succeeded but output amount was zero."
        )

    entry_usdc = (
        input_raw
        / (10 ** USDC_DECIMALS)
    )

    position = {
        "symbol": candidate["symbol"],
        "name": candidate["name"],
        "token_address": candidate["token_address"],
        "raw_token_amount": str(output_raw),
        "entry_usdc": entry_usdc,
        "entry_time": datetime.now().isoformat(),
        "entry_score": safe_number(candidate.get("quant_score_raw", candidate["momentum_score"])),
        "entry_score_delta": candidate["score_delta"],
        "entry_state": candidate["momentum_state"],
        "entry_path": surge_entry_path(candidate, settings),
        "reacceleration_entry": bool(candidate.get("reacceleration_ready")),
        "discovery_source": str(candidate.get("discovery_source") or "DEX"),
        "entry_composite_score": safe_number(candidate.get("composite_score", candidate["momentum_score"])),
        "entry_social_bonus": safe_number(candidate.get("social_score_bonus")),
        "entry_whale_bonus": safe_number(candidate.get("whale_score_bonus")),
        "entry_birdeye_smart_bonus": safe_number(candidate.get("birdeye_smart_bonus")),
        "entry_token_social_bonus": safe_number(candidate.get("token_social_bonus")),
        "entry_token_social_detail": candidate.get("token_social_detail") or {},
        "entry_ai_confirmation_bonus": safe_number(candidate.get("ai_confirmation_bonus")),
        "entry_ai_confirmation_detail": candidate.get("ai_confirmation_detail") or {},
        "entry_confidence_tier": tier,
        "planned_trade_size_usdc": size,
        "roundtrip_preflight_pct": round(roundtrip, 6),
        "execution_integrity": integrity,
        "entry_market_price_usd": safe_number(candidate.get("price_usd")),
        "current_market_price_usd": safe_number(candidate.get("price_usd")),
        "entry_market_cap": safe_number(candidate.get("market_cap")),
        "entry_holder_count": int(safe_number(candidate.get("holder_count"))),
        "entry_holder_count_capped": bool(candidate.get("holder_count_capped")),
        "current_holder_count": int(safe_number(candidate.get("holder_count"))),
        "current_holder_count_capped": bool(candidate.get("holder_count_capped")),
        "holder_change_10m": candidate.get("holder_change_10m", ""),
        "holder_change_10m_pct": candidate.get("holder_change_10m_pct", ""),
        "holder_change_30m": candidate.get("holder_change_30m", ""),
        "holder_change_30m_pct": candidate.get("holder_change_30m_pct", ""),
        "entry_market_cap_per_holder": safe_number(candidate.get("market_cap_per_holder")),
        "current_market_cap_per_holder": safe_number(candidate.get("market_cap_per_holder")),
        "current_market_cap": safe_number(candidate.get("market_cap")),
        "peak_market_cap": safe_number(candidate.get("market_cap")),
        "mc_rolling_avg_5m": safe_number(candidate.get("market_cap")),
        "mc_rolling_avg_change_pct": 0.0,
        "mc_velocity_5m_pct": 0.0,
        "mc_samples": [{
            "time": datetime.now().isoformat(),
            "market_cap": safe_number(candidate.get("market_cap")),
        }],
        "peak_pnl_pct": 0.0,
        "runner_mode": False,
        "stop_loss_breach_count": 0,
        "runner_drawdown_breach_count": 0,
        "runner_floor_breach_count": 0,
        "buy_signature": result.get("signature", ""),
    }

    save_position(position)

    log_trade({
        "timestamp": datetime.now().isoformat(),
        "action": "BUY",
        "symbol": candidate["symbol"],
        "token_address": candidate["token_address"],
        "reason": (
            f"REACCEL_ENTRY_{surge_entry_path(candidate, settings)}"
            if candidate.get("reacceleration_ready")
            else f"SURGING_ENTRY_{surge_entry_path(candidate, settings)}"
        ),
        "input_mint": USDC_MINT,
        "output_mint": candidate["token_address"],
        "total_input_raw": input_raw,
        "total_output_raw": output_raw,
        "input_usd": entry_usdc,
        "score": safe_number(candidate.get("quant_score_raw", candidate["momentum_score"])),
        "score_delta": candidate["score_delta"],
        "quant_score": safe_number(candidate.get("quant_score_raw", candidate["momentum_score"])),
        "composite_score": safe_number(candidate.get("composite_score", candidate["momentum_score"])),
        "social_bonus": safe_number(candidate.get("social_score_bonus")),
        "whale_bonus": safe_number(candidate.get("whale_score_bonus")),
        "birdeye_smart_bonus": safe_number(candidate.get("birdeye_smart_bonus")),
        "token_social_bonus": safe_number(candidate.get("token_social_bonus")),
        "token_social_unique_authors": safe_number((candidate.get("token_social_detail") or {}).get("unique_authors_10m")),
        "token_social_posts_10m": safe_number((candidate.get("token_social_detail") or {}).get("posts_10m")),
        "ai_confirmation_bonus": safe_number(candidate.get("ai_confirmation_bonus")),
        "ai_assessment": str((candidate.get("ai_confirmation_detail") or {}).get("assessment", "")),
        "ai_confidence": int(safe_number((candidate.get("ai_confirmation_detail") or {}).get("confidence"))),
        "ai_risk_level": str((candidate.get("ai_confirmation_detail") or {}).get("risk_level", "")),
        "ai_contradiction_detected": int(bool((candidate.get("ai_confirmation_detail") or {}).get("contradiction_detected"))),
        "ai_summary": str((candidate.get("ai_confirmation_detail") or {}).get("summary", ""))[:300],
        "confidence_tier": tier,
        "entry_path": surge_entry_path(candidate, settings),
        "reacceleration_entry": 1 if candidate.get("reacceleration_ready") else 0,
        "discovery_source": str(candidate.get("discovery_source") or "DEX"),
        "trade_size_usdc": entry_usdc,
        "daily_return_pct": "",
        "state": candidate["momentum_state"],
        "roundtrip_preflight_pct": round(roundtrip, 6),
        "roundtrip_sample_1_pct": safe_number((integrity.get("samples") or [{}])[0].get("return_pct")),
        "roundtrip_sample_2_pct": safe_number((integrity.get("samples") or [{}, {}])[1].get("return_pct")) if len(integrity.get("samples") or []) > 1 else "",
        "dex_price_usd": safe_number(integrity.get("dex_price_usd")),
        "gecko_price_usd": safe_number(integrity.get("gecko_price_usd")),
        "dex_gecko_divergence_pct": safe_number(integrity.get("dex_gecko_divergence_pct")),
        "jupiter_implied_price_usd": safe_number(integrity.get("jupiter_implied_price_usd")),
        "jupiter_consensus_divergence_pct": safe_number(integrity.get("jupiter_consensus_divergence_pct")),
        "entry_market_cap": safe_number(candidate.get("market_cap")),
        "peak_market_cap": safe_number(candidate.get("market_cap")),
        "mc_rolling_avg_5m": safe_number(candidate.get("market_cap")),
        "mc_velocity_5m_pct": 0.0,
        "entry_holder_count": int(safe_number(candidate.get("holder_count"))),
        "entry_market_cap_per_holder": safe_number(candidate.get("market_cap_per_holder")),
        "holder_change_10m": candidate.get("holder_change_10m", ""),
        "holder_change_10m_pct": candidate.get("holder_change_10m_pct", ""),
        "holder_change_30m": candidate.get("holder_change_30m", ""),
        "holder_change_30m_pct": candidate.get("holder_change_30m_pct", ""),
        "runner_mode": 0,
        "peak_pnl_pct": 0.0,
        "router": order.get("router", ""),
        "fee_bps": order.get("feeBps", ""),
        "signature": result.get("signature", ""),
    })

    print(
        f"  BUY SUCCESS: {candidate['symbol']} "
        f"{result.get('signature', '')}"
    )

    signature = result.get("signature", "")
    buy_price = safe_number(candidate.get("price_usd"))
    tx5 = (
        safe_number(candidate.get("buys_5m"))
        + safe_number(candidate.get("sells_5m"))
    )

    buy_lines = [
        (
            f"Amount ${entry_usdc:.2f} | Price {_format_token_price(buy_price)}"
        ),
        (
            f"Path {surge_entry_path(candidate, settings)}"
            f"{' | REACCEL' if candidate.get('reacceleration_ready') else ''}"
            f" | {tier}"
        ),
        (
            f"Quant {safe_number(candidate.get('quant_score_raw', candidate['momentum_score'])):.0f} "
            f"({candidate['score_delta']:+.0f}) | "
            f"Comp {safe_number(candidate.get('composite_score', candidate['momentum_score'])):.0f}"
        ),
        (
            f"5m {safe_number(candidate.get('price_5m')):+.1f}% | "
            f"1h {safe_number(candidate.get('price_1h')):+.1f}%"
        ),
    ]

    if bool(settings.get("HOLDER_METRICS_ALERTS_ENABLED", 1)):
        buy_lines.extend(holder_alert_lines(candidate).splitlines())

    buy_lines.extend([
        (
            f"Liq {_compact_usd(candidate.get('liquidity'))} | "
            f"Vol5 {_compact_usd(candidate.get('volume_5m'))} | "
            f"VolX {safe_number(candidate.get('volume_acceleration')):.2f}x"
        ),
        (
            f"B/S {safe_number(candidate.get('buy_sell_ratio_5m')):.2f} | "
            f"Tx5 {tx5:.0f}"
        ),
    ])

    confirm_parts = []
    whale_bonus = safe_number(candidate.get("whale_score_bonus"))
    token_x_bonus = safe_number(candidate.get("token_social_bonus"))
    if whale_bonus != 0:
        confirm_parts.append(f"Whale {whale_bonus:+.0f}")
    if token_x_bonus > 0:
        confirm_parts.append(f"X +{token_x_bonus:.0f}")

    ai_detail = candidate.get("ai_confirmation_detail") or {}
    if str(ai_detail.get("status") or "") in {"OK", "CACHED"}:
        ai_assess = str(ai_detail.get("assessment") or "NEUTRAL")
        ai_conf = int(safe_number(ai_detail.get("confidence")))
        ai_bonus = safe_number(candidate.get("ai_confirmation_bonus"))
        confirm_parts.append(
            f"AI {ai_assess} {ai_conf}% {ai_bonus:+.0f}"
        )

    if confirm_parts:
        buy_lines.append("Confirm " + " | ".join(confirm_parts))

    if str(ai_detail.get("status") or "") in {"OK", "CACHED"}:
        ai_summary = str(ai_detail.get("summary") or "").strip()
        if ai_summary:
            buy_lines.append(f"AI note {ai_summary[:120]}")

    dex_gecko_div = safe_number(
        integrity.get("dex_gecko_divergence_pct")
    )
    jup_consensus_div = safe_number(
        integrity.get("jupiter_consensus_divergence_pct")
    )
    buy_lines.append(
        f"Exec RT {roundtrip:.1f}% | "
        f"DEX/Gecko {dex_gecko_div:.1f}% | "
        f"Jup div {jup_consensus_div:.1f}%"
    )

    router = str(order.get("router") or "")
    if router:
        buy_lines.append(f"Route {router} | Fee {order.get('feeBps', '')} bps")

    buy_lines.append(f"Tx {signature}")


    send_pushover(
        f"BUY: {candidate['symbol']}",
        "\n".join(buy_lines),
        priority=0,
        sound="cashregister",
        audience="movement",
    )

    return position


def sell_position(
    position,
    reason,
    settings,
    api_key,
    signer,
    wallet_address,
):
    token = position["token_address"]
    raw_amount = int(
        position["raw_token_amount"]
    )

    if not settings["LIVE_TRADING"]:
        print(
            f"  PAPER SIGNAL: would SELL "
            f"{position['symbol']} ({reason})"
        )
        return

    order, result = real_swap(
        api_key,
        signer,
        wallet_address,
        token,
        USDC_MINT,
        raw_amount,
    )

    output_raw = int(
        result.get("totalOutputAmount")
        or 0
    )

    actual_usdc = (
        output_raw
        / (10 ** USDC_DECIMALS)
    )

    entry_usdc = float(
        position["entry_usdc"]
    )

    realized = actual_usdc - entry_usdc

    log_trade({
        "timestamp": datetime.now().isoformat(),
        "action": "SELL",
        "symbol": position["symbol"],
        "token_address": token,
        "reason": reason,
        "input_mint": token,
        "output_mint": USDC_MINT,
        "total_input_raw": result.get(
            "totalInputAmount",
            raw_amount,
        ),
        "total_output_raw": output_raw,
        "input_usd": entry_usdc,
        "output_usd": actual_usdc,
        "realized_pnl_usd": round(realized, 8),
        "score": position.get("entry_score", ""),
        "score_delta": position.get("entry_score_delta", ""),
        "quant_score": position.get("entry_score", ""),
        "composite_score": position.get("entry_composite_score", ""),
        "social_bonus": position.get("entry_social_bonus", ""),
        "whale_bonus": position.get("entry_whale_bonus", ""),
        "birdeye_smart_bonus": position.get("entry_birdeye_smart_bonus", ""),
        "token_social_bonus": position.get("entry_token_social_bonus", ""),
        "token_social_unique_authors": safe_number((position.get("entry_token_social_detail") or {}).get("unique_authors_10m")),
        "token_social_posts_10m": safe_number((position.get("entry_token_social_detail") or {}).get("posts_10m")),
        "ai_confirmation_bonus": safe_number(position.get("entry_ai_confirmation_bonus")),
        "ai_assessment": str((position.get("entry_ai_confirmation_detail") or {}).get("assessment", "")),
        "ai_confidence": int(safe_number((position.get("entry_ai_confirmation_detail") or {}).get("confidence"))),
        "ai_risk_level": str((position.get("entry_ai_confirmation_detail") or {}).get("risk_level", "")),
        "ai_contradiction_detected": int(bool((position.get("entry_ai_confirmation_detail") or {}).get("contradiction_detected"))),
        "ai_summary": str((position.get("entry_ai_confirmation_detail") or {}).get("summary", ""))[:300],
        "confidence_tier": position.get("entry_confidence_tier", ""),
        "entry_path": position.get("entry_path", ""),
        "trade_size_usdc": position.get("planned_trade_size_usdc", entry_usdc),
        "daily_return_pct": position.get("last_daily_return_pct", ""),
        "roundtrip_preflight_pct": position.get("roundtrip_preflight_pct", ""),
        "roundtrip_sample_1_pct": safe_number((((position.get("execution_integrity") or {}).get("samples") or [{}])[0]).get("return_pct")),
        "roundtrip_sample_2_pct": safe_number((((position.get("execution_integrity") or {}).get("samples") or [{}, {}])[1]).get("return_pct")) if len(((position.get("execution_integrity") or {}).get("samples") or [])) > 1 else "",
        "dex_price_usd": safe_number((position.get("execution_integrity") or {}).get("dex_price_usd")),
        "gecko_price_usd": safe_number((position.get("execution_integrity") or {}).get("gecko_price_usd")),
        "dex_gecko_divergence_pct": safe_number((position.get("execution_integrity") or {}).get("dex_gecko_divergence_pct")),
        "jupiter_implied_price_usd": safe_number((position.get("execution_integrity") or {}).get("jupiter_implied_price_usd")),
        "jupiter_consensus_divergence_pct": safe_number((position.get("execution_integrity") or {}).get("jupiter_consensus_divergence_pct")),
        "entry_market_cap": safe_number(position.get("entry_market_cap")),
        "exit_market_cap": safe_number(position.get("current_market_cap")),
        "peak_market_cap": safe_number(position.get("peak_market_cap")),
        "mc_rolling_avg_5m": safe_number(position.get("mc_rolling_avg_5m")),
        "mc_velocity_5m_pct": safe_number(position.get("mc_velocity_5m_pct")),
        "entry_holder_count": int(safe_number(position.get("entry_holder_count"))),
        "exit_holder_count": int(safe_number(position.get("current_holder_count"))),
        "entry_market_cap_per_holder": safe_number(position.get("entry_market_cap_per_holder")),
        "exit_market_cap_per_holder": safe_number(position.get("current_market_cap_per_holder")),
        "holder_change_10m": position.get("holder_change_10m", ""),
        "holder_change_10m_pct": position.get("holder_change_10m_pct", ""),
        "holder_change_30m": position.get("holder_change_30m", ""),
        "holder_change_30m_pct": position.get("holder_change_30m_pct", ""),
        "runner_mode": 1 if position.get("runner_mode") else 0,
        "peak_pnl_pct": safe_number(position.get("peak_pnl_pct")),
        "router": order.get("router", ""),
        "fee_bps": order.get("feeBps", ""),
        "signature": result.get("signature", ""),
    })

    set_cooldown(token)
    clear_position()

    print(
        f"  SELL SUCCESS: "
        f"${actual_usdc:.6f} USDC | "
        f"P/L ${realized:+.6f}"
    )

    pnl_pct = (
        (realized / entry_usdc) * 100.0
        if entry_usdc > 0
        else 0.0
    )

    held_minutes = 0.0
    try:
        held_minutes = (
            datetime.now()
            - datetime.fromisoformat(position["entry_time"])
        ).total_seconds() / 60.0
    except Exception:
        pass

    signature = result.get("signature", "")

    entry_price = safe_number(position.get("entry_market_price_usd"))
    exit_price = safe_number(position.get("current_market_price_usd"))
    peak_pnl = safe_number(position.get("peak_pnl_pct"))

    entry_mc = safe_number(position.get("entry_market_cap"))
    exit_mc = safe_number(position.get("current_market_cap"))
    mc_change_pct = (
        ((exit_mc - entry_mc) / entry_mc) * 100.0
        if entry_mc > 0 and exit_mc > 0
        else 0.0
    )

    entry_holders = int(safe_number(position.get("entry_holder_count")))
    exit_holders = int(safe_number(position.get("current_holder_count")))
    holder_net = (
        exit_holders - entry_holders
        if entry_holders > 0 and exit_holders > 0
        else None
    )
    holder_net_pct = (
        (holder_net / entry_holders) * 100.0
        if holder_net is not None and entry_holders > 0
        else None
    )

    sell_lines = [
        f"Reason {reason}",
        (
            f"Held {held_minutes:.1f}m | "
            f"P/L ${realized:+.4f} ({pnl_pct:+.2f}%) | "
            f"Peak {peak_pnl:+.2f}%"
        ),
        (
            f"Received ${actual_usdc:.4f} | "
            f"Entry ${entry_usdc:.4f}"
        ),
        (
            f"Price {_format_token_price(entry_price)} → "
            f"{_format_token_price(exit_price)}"
        ),
        (
            f"Path {position.get('entry_path', 'n/a')} | "
            f"{position.get('entry_confidence_tier', 'n/a')} | "
            f"{'RUNNER' if position.get('runner_mode') else 'NORMAL'}"
        ),
    ]

    entry_ai = position.get("entry_ai_confirmation_detail") or {}
    if str(entry_ai.get("status") or "") in {"OK", "CACHED"}:
        sell_lines.append(
            f"AI entry {entry_ai.get('assessment','NEUTRAL')} "
            f"{int(safe_number(entry_ai.get('confidence')))}% | "
            f"{safe_number(position.get('entry_ai_confirmation_bonus')):+.0f}"
        )

    if bool(settings.get("HOLDER_METRICS_ALERTS_ENABLED", 1)):
        sell_lines.extend([
            (
                f"MC {_compact_usd(entry_mc)} → {_compact_usd(exit_mc)} "
                f"({mc_change_pct:+.1f}%)"
            ),
            (
                f"Holders "
                f"{_holder_count_text(entry_holders, position.get('entry_holder_count_capped'))} → "
                f"{_holder_count_text(exit_holders, position.get('current_holder_count_capped'))}"
                + (
                    f" ({holder_net:+,}, {holder_net_pct:+.1f}%)"
                    if holder_net is not None and holder_net_pct is not None
                    else ""
                )
            ),
            (
                f"HΔ 10m {_holder_delta_text(position.get('holder_change_10m'), position.get('holder_change_10m_pct'))} | "
                f"30m {_holder_delta_text(position.get('holder_change_30m'), position.get('holder_change_30m_pct'))}"
            ),
            f"MC/H {_compact_usd(position.get('current_market_cap_per_holder'))}",
        ])

    last_daily = position.get("last_daily_return_pct")
    if last_daily not in (None, ""):
        sell_lines.append(f"Day P/L {safe_number(last_daily):+.2f}%")

    router = str(order.get("router") or "")
    if router:
        sell_lines.append(f"Route {router} | Fee {order.get('feeBps', '')} bps")

    sell_lines.append(f"Tx {signature}")


    send_pushover(
        f"SELL: {position['symbol']}",
        "\n".join(sell_lines),
        priority=0,
        sound="cashregister",
        audience="movement",
    )


# ============================================================
# RISK / LOOP
# ============================================================

def trading_allowed(settings, wallet_address):
    completed, realized = today_trade_stats()

    if completed >= settings["MAX_TRADES_PER_DAY"]:
        return False, "daily trade limit reached", None

    if realized <= -abs(
        settings["DAILY_REALIZED_LOSS_LIMIT_USD"]
    ):
        return False, "legacy absolute daily loss limit reached", None

    flat_equity = wallet_usdc_balance(wallet_address)
    status = daily_account_status(settings, flat_equity)
    state = status["state"]

    if state.get("target_locked"):
        return False, "daily target locked", status

    if state.get("drawdown_locked"):
        return False, "daily drawdown circuit breaker locked", status

    daily_return = status.get("return_pct")
    if daily_return is not None:
        if (
            bool(settings.get("DAILY_TARGET_LOCK_ENABLED", 1))
            and daily_return >= float(settings.get("DAILY_TARGET_PCT", 2.0))
        ):
            set_daily_lock("target", flat_equity)
            status["state"] = load_daily_state()
            return False, (
                f"daily target reached ({daily_return:+.2f}%)"
            ), status

        if daily_return <= -abs(float(settings.get("MAX_DAILY_DRAWDOWN_PCT", 1.5))):
            set_daily_lock("drawdown", flat_equity)
            status["state"] = load_daily_state()
            return False, (
                f"daily drawdown limit reached ({daily_return:+.2f}%)"
            ), status

    return True, "", status


def display_candidate(candidate):
    quant = safe_number(
        candidate.get("quant_score_raw", candidate.get("momentum_score"))
    )
    composite = safe_number(candidate.get("composite_score", quant))
    print(
        f"  Best: {candidate['symbol']} | "
        f"quant {quant:.0f} "
        f"({candidate['score_delta']:+.0f}) | "
        f"composite {composite:.0f} | "
        f"{candidate['momentum_state']} | "
        f"5m {candidate['price_5m']:+.1f}% | "
        f"vol ${candidate['volume_5m']:,.0f} | "
        f"B/S {candidate['buy_sell_ratio_5m']:.2f} | "
        f"volX {candidate['volume_acceleration']:.2f}"
        + (
            f" | social {safe_number(candidate.get('social_score')):+.1f}"
            f" ({safe_number(candidate.get('social_score_bonus')):+.1f} pts)"
            if candidate.get("social_score_source") not in (None, "", "NONE")
            else ""
        )
        + (
            f" | whale {safe_number(candidate.get('whale_score_bonus')):+.0f}"
            f" ({candidate.get('whale_score_source')})"
            if safe_number(candidate.get("whale_score_bonus")) != 0
            else ""
        )
        + (
            f" | Birdeye {safe_number(candidate.get('birdeye_smart_bonus')):+.0f}"
            if safe_number(candidate.get("birdeye_smart_bonus")) != 0
            else ""
        )
        + (
            f" | TokenX +{safe_number(candidate.get('token_social_bonus')):.0f}"
            if safe_number(candidate.get("token_social_bonus")) > 0
            else ""
        )
        + (
            f" | AI {str((candidate.get('ai_confirmation_detail') or {}).get('assessment') or 'NEUTRAL')} "
            f"{int(safe_number((candidate.get('ai_confirmation_detail') or {}).get('confidence')))}% "
            f"{safe_number(candidate.get('ai_confirmation_bonus')):+.0f}"
            if str((candidate.get('ai_confirmation_detail') or {}).get('status') or "") in {"OK", "CACHED"}
            else ""
        )
        + f" | {confidence_tier(candidate)}"
    )


def run_cycle(
    settings,
    api_key,
    signer,
    wallet_address,
):
    print()
    print(
        f"[{datetime.now():%Y-%m-%d %H:%M:%S}] "
        f"Starting cycle"
    )

    position = load_position()

    if position:
        # Keep existing surge research alive while a real position is open.
        # This does NOT perform discovery or influence exit logic.
        update_surge_followups([], settings)

        try:
            liquidation_usdc = (
                jupiter_liquidation_value_usdc(
                    api_key,
                    position["token_address"],
                    position["raw_token_amount"],
                )
            )

            momentum = held_token_momentum(
                position["token_address"]
            )

            position = update_market_cap_tracking(
                position,
                momentum,
                settings,
            )
            if momentum and safe_number(momentum.get("price_usd")) > 0:
                position["current_market_price_usd"] = safe_number(
                    momentum.get("price_usd")
                )
            position = update_position_holder_metrics(
                position,
                settings,
            )

            reason, pnl_pct, peak, held_minutes = (
                choose_exit(
                    position,
                    liquidation_usdc,
                    momentum,
                    settings,
                )
            )

            wallet_cash = wallet_usdc_balance(wallet_address)
            daily_equity = None
            if wallet_cash is not None:
                daily_equity = wallet_cash + liquidation_usdc

            day_status = daily_account_status(settings, daily_equity)
            daily_return = day_status.get("return_pct")
            if daily_return is not None:
                target_trigger = (
                    float(settings.get("DAILY_TARGET_PCT", 2.0))
                    + float(settings.get("DAILY_TARGET_LOCK_BUFFER_PCT", 0.25))
                )
                if (
                    bool(settings.get("DAILY_TARGET_LOCK_ENABLED", 1))
                    and daily_return >= target_trigger
                ):
                    reason = "DAILY_TARGET_LOCK"
                elif daily_return <= -abs(
                    float(settings.get("MAX_DAILY_DRAWDOWN_PCT", 1.5))
                ):
                    reason = "DAILY_DRAWDOWN_STOP"

            position["last_daily_return_pct"] = daily_return
            save_position(position)

            mc = safe_number(position.get("current_market_cap"))
            mc_avg = safe_number(position.get("mc_rolling_avg_5m"))
            mc_vel = safe_number(position.get("mc_velocity_5m_pct"))
            runner = "RUNNER" if position.get("runner_mode") else "NORMAL"

            print(
                f"  HOLD {position['symbol']} | "
                f"value ${liquidation_usdc:.4f} | "
                f"P/L {pnl_pct:+.2f}% | "
                f"peak {peak:+.2f}% | "
                f"{held_minutes:.1f} min | {runner} | "
                f"MC ${mc:,.0f} | avg5 ${mc_avg:,.0f} | "
                f"MCv {mc_vel:+.1f}% | "
                f"holders {_holder_count_text(position.get('current_holder_count'), position.get('current_holder_count_capped'))}"
                + (
                    f" | Day {daily_return:+.2f}%"
                    if daily_return is not None else ""
                )
            )

            if reason:
                sell_position(
                    position,
                    reason,
                    settings,
                    api_key,
                    signer,
                    wallet_address,
                )
                if reason == "DAILY_TARGET_LOCK":
                    set_daily_lock("target")
                elif reason == "DAILY_DRAWDOWN_STOP":
                    set_daily_lock("drawdown")

            return

        except Exception as exc:
            if "UNKNOWN_EXECUTION_STATE" in str(exc):
                raise
            print(
                f"  Position-monitor warning: {exc}"
            )

            send_pushover_once(
                f"position-monitor:{type(exc).__name__}:{str(exc)[:120]}",
                "CryptoTracker POSITION WARNING",
                (
                    f"Could not fully monitor the open "
                    f"{position.get('symbol', '?')} position this cycle.\n"
                    f"The bot will try again next cycle.\n\n"
                    f"Error: {exc}"
                ),
                cooldown_seconds=900,
                priority=0,
                sound="siren",
            )
            return

    allowed, reason, day_status = trading_allowed(
        settings,
        wallet_address,
    )

    if day_status and day_status.get("return_pct") is not None:
        print(
            f"  Day P/L: {day_status['return_pct']:+.2f}% | "
            f"target +{day_status['target_pct']:.2f}% | "
            f"max DD -{day_status['drawdown_pct']:.2f}%"
        )

    if not allowed:
        update_surge_followups([], settings)

        print(
            f"  New entries disabled: {reason}"
        )

        send_pushover_once(
            f"risk:{reason}",
            "CryptoTracker RISK LIMIT",
            (
                f"New entries disabled.\n"
                f"Reason: {reason}"
            ),
            cooldown_seconds=21600,
            priority=0,
            sound="siren",
        )
        return

    print("  Scanning market...")
    candidates = scan_candidates(settings)
    candidates = apply_social_scores(candidates, settings)
    candidates = apply_whale_scores(candidates, settings)
    candidates = apply_birdeye_smart_money_scores(candidates, settings)
    candidates = apply_token_social_scores(candidates, settings)

    # V11.5: extended tokens are tracked across cycles. A later reset is marked
    # REACCEL READY only when the existing NORMAL/EARLY quant rules pass again.
    candidates = update_reacceleration_watch(candidates, settings)

    # Observation-only confirmation audit. It cannot modify candidate scores or execution.
    log_confirmation_feeds(candidates, settings)

    # V11.5 ranking: quant remains the gate. REACCEL READY is only a modest
    # prioritization signal among candidates that still must independently pass
    # NORMAL or EARLY_ACCEL.
    candidates.sort(
        key=lambda c: (
            str(c.get("momentum_state")) == "SURGING",
            1 if c.get("reacceleration_ready") else 0,
            safe_number(c.get("entry_priority_score"))
                + safe_number(c.get("reacceleration_priority_bonus")),
            safe_number(c.get("quant_score_raw", c.get("momentum_score"))),
        ),
        reverse=True,
    )

    # V11.5.2 holder/adoption data is observation-only. It is added before
    # Luna so the AI can see holder/market-cap context.
    candidates = apply_holder_metrics(candidates, settings)

    # V11.7: Luna analyzes momentum patterns only for already-valid quant setups. Its bounded +/- score
    # can alter ranking/composite score but NEVER momentum_score or hard gates.
    candidates = apply_ai_confirmation_scores(candidates, settings)

    # Re-rank after Luna's bounded secondary-confirmation adjustment.
    candidates.sort(
        key=lambda c: (
            str(c.get("momentum_state")) == "SURGING",
            1 if c.get("reacceleration_ready") else 0,
            safe_number(c.get("entry_priority_score"))
                + safe_number(c.get("reacceleration_priority_bonus")),
            safe_number(c.get("quant_score_raw", c.get("momentum_score"))),
        ),
        reverse=True,
    )

    # V11.9 paper laboratory: independent virtual portfolios share this
    # enriched candidate stream. The lab receives no signer and cannot swap.
    if bool(settings.get("PAPER_RESEARCH_ENABLED", 1)):
        for candidate in candidates:
            candidate["research_entry_path"] = surge_entry_path(candidate, settings)
        try:
            paper_lab.run_paper_research(
                candidates,
                settings,
                price_lookup=direct_token_market_snapshot,
                integrity_lookup=lambda candidate, size: execution_integrity_check(
                    candidate,
                    api_key,
                    size,
                    settings,
                ),
                exit_value_lookup=lambda position: jupiter_liquidation_value_usdc(
                    api_key,
                    position["token_address"],
                    int(position.get("entry_token_raw") or 0),
                ),
                data_quality={
                    "helius_status": helius_data_quality(),
                    "flags": "" if helius_data_quality() == "AVAILABLE" else "HELIUS_UNAVAILABLE_OPTIONAL",
                },
            )
        except Exception as exc:
            print(f"  PAPER RESEARCH WARNING: {exc}")

    # Notify immediately when a token is SURGING. This is informational only
    # and does not bypass or alter any entry/risk rule.
    send_surging_alerts(candidates, settings)

    # Observation-only research happens before any entry decision or Jupiter
    # execution. Thus a locally valid signal that later fails to execute
    # (for example, a gasless minimum) is still tracked for two hours.
    register_surge_signals(candidates, settings)
    update_surge_followups(candidates, settings)

    if not candidates:
        print(
            "  No candidates passed base filters."
        )
        return

    display_candidate(candidates[0])

    chosen = None

    for candidate in candidates:
        if not entry_reasons(
            candidate,
            settings,
        ):
            chosen = candidate
            break

    if not chosen:
        print(
            "  No candidate met entry rules."
        )

        # Only show detailed PASS/FAIL diagnostics for SURGING candidates.
        # Non-SURGING records are intentionally omitted to keep console output clean.
        diagnostic_candidates = [
            c for c in candidates
            if c.get("momentum_state") == "SURGING"
        ][:3]

        for candidate in diagnostic_candidates:
            print_entry_audit(
                candidate,
                settings,
            )

        return

    selected_entry_path = surge_entry_path(chosen, settings)

    if chosen.get("reacceleration_ready"):
        print(
            f"  REACCELERATION ENTRY SIGNAL: {chosen['symbol']} | "
            f"watched {safe_number(chosen.get('reacceleration_age_minutes')):.1f}m | "
            f"score={chosen['momentum_score']:.0f} | "
            f"delta={chosen['score_delta']:+.0f}"
        )
    elif (
        cooldown_active(chosen["token_address"], settings)
        and strong_reentry_allowed(chosen, settings)
    ):
        print(
            f"  STRONG RE-ENTRY SIGNAL: {chosen['symbol']} | "
            f"cooldown overridden | "
            f"score={chosen['momentum_score']:.0f} | "
            f"delta={chosen['score_delta']:+.0f}"
        )
    elif selected_entry_path == "EARLY_ACCEL":
        print(
            f"  EARLY ACCELERATION SIGNAL: {chosen['symbol']} | "
            f"score={chosen['momentum_score']:.0f} | "
            f"delta={chosen['score_delta']:+.0f}"
        )
    else:
        print(
            f"  ENTRY SIGNAL: {chosen['symbol']} | "
            f"score={chosen['momentum_score']:.0f} | "
            f"delta={chosen['score_delta']:+.0f}"
        )

    print_entry_audit(
        chosen,
        settings,
    )

    buy_candidate(
        chosen,
        settings,
        api_key,
        signer,
        wallet_address,
    )


def print_settings(settings, wallet_address):
    print("=" * 82)
    print("CRYPTOTRACKER V11.9 - PROTECTED MULTI-MODEL PAPER RESEARCH")
    print("=" * 82)
    print(f"Wallet:                 {wallet_address}")
    print(
        f"Mode:                   "
        f"{'LIVE REAL-MONEY TRADING' if settings['LIVE_TRADING'] else 'PAPER / SIGNAL ONLY'}"
    )
    print(f"Scan interval:          {settings['SCAN_INTERVAL_SECONDS']:.0f} seconds")
    print(
        f"Trade sizes:            NORMAL ${settings['NORMAL_TRADE_SIZE_USDC']:.2f} | "
        f"EARLY ${settings['EARLY_ACCEL_TRADE_SIZE_USDC']:.2f}"
    )
    print(
        f"Risk sizing:            "
        f"{'ENABLED' if settings.get('USE_RISK_BASED_SIZING', 0) else 'OFF'} | "
        f"normal risk {settings['NORMAL_RISK_PCT']:.2f}% | "
        f"early risk {settings['EARLY_RISK_PCT']:.2f}%"
    )
    print(
        f"Daily objective:        +{settings['DAILY_TARGET_PCT']:.2f}% target/lock | "
        f"trigger buffer +{settings['DAILY_TARGET_LOCK_BUFFER_PCT']:.2f}%"
    )
    print(
        f"Daily circuit breaker:  -{settings['MAX_DAILY_DRAWDOWN_PCT']:.2f}% | "
        f"max completed trades {settings['MAX_TRADES_PER_DAY']}"
    )
    print(
        f"Entry NORMAL:           quant >= {settings['MIN_BUY_SCORE']:.0f} | "
        f"delta >= +{settings['MIN_BUY_SCORE_DELTA']:.0f}"
    )
    print(
        f"Normal gates:           liq ${settings['MIN_BUY_LIQUIDITY']:,.0f} | "
        f"vol ${settings['MIN_BUY_5M_VOLUME']:,.0f} | "
        f"volX {settings['MIN_BUY_VOLUME_ACCEL']:.2f} | "
        f"B/S {settings['MIN_BUY_SELL_RATIO']:.2f} | "
        f"tx {settings['MIN_5M_TRANSACTIONS']}"
    )
    print(
        f"Entry EARLY:            quant >= {settings['EARLY_ACCEL_MIN_SCORE']:.0f} | "
        f"delta >= +{settings['EARLY_ACCEL_MIN_SCORE_DELTA']:.0f} | "
        f"size ${settings['EARLY_ACCEL_TRADE_SIZE_USDC']:.2f}"
    )
    print(
        f"Early gates:            liq ${settings['EARLY_ACCEL_MIN_LIQUIDITY']:,.0f} | "
        f"vol ${settings['EARLY_ACCEL_MIN_5M_VOLUME']:,.0f} | "
        f"volX {settings['EARLY_ACCEL_MIN_VOLUME_ACCEL']:.2f} | "
        f"B/S {settings['EARLY_ACCEL_MIN_BUY_SELL_RATIO']:.2f} | "
        f"tx {settings['EARLY_ACCEL_MIN_5M_TRANSACTIONS']}"
    )
    print(
        f"Anti-chase NORMAL:      5m {settings['MIN_BUY_5M_PCT']:+.1f}%.."
        f"{settings['MAX_BUY_5M_PCT']:+.1f}% | "
        f"1h {settings['MIN_BUY_1H_PCT']:+.1f}%..{settings['MAX_BUY_1H_PCT']:+.1f}%"
    )
    print(
        f"Anti-chase EARLY:       5m {settings['EARLY_ACCEL_MIN_5M_PCT']:+.1f}%.."
        f"{settings['EARLY_ACCEL_MAX_5M_PCT']:+.1f}% | "
        f"1h {settings['EARLY_ACCEL_MIN_1H_PCT']:+.1f}%.."
        f"{settings['EARLY_ACCEL_MAX_1H_PCT']:+.1f}%"
    )
    print(
        f"Social confirmation:    weight {settings.get('SOCIAL_SCORE_WEIGHT', 0.15):.2f} | "
        f"cap +/-{settings.get('SOCIAL_MAX_BONUS', 15):.0f} | quant gate unchanged"
    )
    print(
        f"Smart-money confirm:    local max +{settings.get('SMART_MONEY_MAX_BONUS', 25):.0f} | "
        f"Birdeye max +{settings.get('BIRDEYE_SMART_MONEY_MAX_BONUS', 15):.0f}"
    )
    print(
        f"Token-specific X:       top {settings.get('TOKEN_SOCIAL_TOP_N', 2)} candidates | "
        f"max +{settings.get('TOKEN_SOCIAL_MAX_BONUS', 12):.0f}"
    )
    print(
        f"Luna AI confirmation:   "
        f"{'ENABLED' if settings.get('AI_CONFIRMATION_ENABLED', 1) else 'OFF'} | "
        f"model {_openai_model_name()} | "
        f"top {settings.get('AI_CONFIRMATION_TOP_N', 2)} | "
        f"cap +/-{settings.get('AI_CONFIRMATION_MAX_BONUS', 5):.0f} | "
        f"quant gate unchanged"
    )
    print(
        f"Confirmation feed log:  "
        f"{'ENABLED' if settings.get('CONFIRMATION_FEED_LOG_ENABLED', 1) else 'OFF'} | "
        f"{'SURGING only' if settings.get('CONFIRMATION_FEED_SURGING_ONLY', 1) else 'all candidates'} | "
        f"dedupe {settings.get('CONFIRMATION_FEED_DEDUPE_MINUTES', 5):.0f}m"
    )
    print(
        f"Execution integrity:    {'ENABLED' if settings.get('EXECUTION_INTEGRITY_ENABLED', 1) else 'OFF'} | "
        f"DEX/Gecko <= {settings.get('EXEC_MAX_DEX_GECKO_DIVERGENCE_PCT', 3):.1f}% | "
        f"Jupiter RT {settings['MIN_ROUNDTRIP_RETURN_PCT']:.1f}%..{settings.get('EXEC_MAX_ROUNDTRIP_RETURN_PCT', 100.5):.1f}%"
    )
    print(
        f"Normal stop:            {settings['STOP_LOSS_PCT']:.1f}% confirmed | "
        f"emergency {settings['EMERGENCY_STOP_PCT']:.1f}%"
    )
    print(
        f"Soft-exit grace:        {settings['MOMENTUM_EXIT_GRACE_MINUTES']:.0f}m | "
        f"stagnant review {settings['STAGNANT_EXIT_MINUTES']:.0f}m"
    )
    print(
        f"Runner:                 activate +{settings['RUNNER_ACTIVATE_PCT']:.1f}% | "
        f"max hold {settings['RUNNER_MAX_HOLD_MINUTES']:.0f}m"
    )
    print(
        f"Runner drawdowns:       {settings['RUNNER_DRAWDOWN_10_25_PCT']:.0f}% / "
        f"{settings['RUNNER_DRAWDOWN_25_50_PCT']:.0f}% / "
        f"{settings['RUNNER_DRAWDOWN_50_PLUS_PCT']:.0f}%"
    )
    print(
        f"Runner profit floors:   +{settings.get('RUNNER_PROFIT_FLOOR_10_PCT', 4):.0f}% / "
        f"+{settings.get('RUNNER_PROFIT_FLOOR_20_PCT', 10):.0f}% / "
        f"+{settings.get('RUNNER_PROFIT_FLOOR_30_PCT', 15):.0f}% / "
        f"+{settings.get('RUNNER_PROFIT_FLOOR_50_PCT', 25):.0f}%"
    )
    print(
        f"Round-trip minimum:     {settings['MIN_ROUNDTRIP_RETURN_PCT']:.1f}%"
    )
    print(
        f"Per-token cap:          {settings['MAX_ENTRIES_PER_TOKEN_60M']} entry/token/60m"
    )
    print(
        f"Discovery sources:      DEX + "
        f"{'verified whale' if settings.get('WHALE_DISCOVERY_ENABLED', 1) else 'whale OFF'} + "
        f"{'Gecko new pools' if settings.get('GECKO_DISCOVERY_ENABLED', 1) else 'Gecko OFF'}"
    )
    print(
        f"Reaccel watch:          "
        f"{'ENABLED' if settings.get('REACCEL_WATCH_ENABLED', 1) else 'OFF'} | "
        f"max {settings.get('REACCEL_WATCH_MAX_AGE_MINUTES', 120):.0f}m | "
        f"priority +{settings.get('REACCEL_PRIORITY_BONUS', 5):.0f}"
    )
    print(
        f"False-negative review:  "
        f"{'ENABLED' if settings.get('MISSED_OPPORTUNITY_REPORT_ENABLED', 1) else 'OFF'}"
    )
    print(
        f"Macro influencer X:      "
        f"{'ENABLED' if settings.get('SOCIAL_SENTIMENT_ENABLED', 0) else 'OFF (do not run separate monitor)'}"
    )
    print(
        f"Targeted Token-X:        "
        f"{'ENABLED' if settings.get('TOKEN_SOCIAL_ENABLED', 1) else 'OFF'} | "
        f"top {int(settings.get('TOKEN_SOCIAL_TOP_N', 2))} | "
        f"cache {int(settings.get('TOKEN_SOCIAL_CACHE_SECONDS', 300))}s"
    )
    print(
        f"X request audit:         "
        f"{'ENABLED' if settings.get('X_API_USAGE_LOG_ENABLED', 1) else 'OFF'}"
    )
    print(
        f"Holder metrics:          "
        f"{'ENABLED' if settings.get('HOLDER_METRICS_ENABLED', 1) else 'OFF'} | "
        f"cache {int(settings.get('HOLDER_METRICS_CACHE_SECONDS', 600)) // 60}m | "
        f"max {int(settings.get('HOLDER_METRICS_MAX_TOKENS_PER_CYCLE', 10))} token(s)/cycle"
    )
    print(
        "MC/holder scoring:       OBSERVATION ONLY — no entry/exit weight yet"
    )
    movement_group_present = bool(
        str(os.getenv("PUSHOVER_CRYPTO_MOVEMENT_GROUP_KEY") or "").strip()
    )
    print(
        f"Pushover personal:      "
        f"{'ENABLED' if personal_pushover_configured() else 'NOT CONFIGURED'}"
    )
    print(
        f"Pushover movement:      "
        f"{'GROUP' if movement_group_present and movement_pushover_configured() else ('PERSONAL FALLBACK' if movement_pushover_configured() else 'NOT CONFIGURED')}"
    )
    eod_group_present = bool(
        str(os.getenv("PUSHOVER_CRYPTO_EOD_GROUP_KEY") or "").strip()
    )
    eod_route = (
        "GROUP"
        if eod_group_present and crypto_eod_pushover_configured()
        else ("USER FALLBACK" if crypto_eod_pushover_configured() else "NOT CONFIGURED")
    )
    print(
        f"Crypto EOD Pushover:     "
        f"{eod_route} "
        f"@ {int(settings.get('PUSHOVER_CRYPTO_EOD_HOUR', 23)):02d}:"
        f"{int(settings.get('PUSHOVER_CRYPTO_EOD_MINUTE', 55)):02d} "
        f"{os.getenv('CRYPTO_EOD_TIMEZONE') or 'America/Los_Angeles'}"
    )
    print("=" * 82)



def test_luna_confirmation():
    """Live API smoke test using synthetic market data. Never trades."""
    load_dotenv(ENV_FILE)

    if not str(os.getenv("OPENAI_API_KEY") or "").strip():
        print("LUNA TEST FAILED: OPENAI_API_KEY is missing.")
        return False

    settings = {}
    for key, default in DEFAULTS.items():
        if isinstance(default, int):
            settings[key] = env_int(key, default)
        else:
            settings[key] = env_float(key, default)

    candidate = {
        "symbol": "TEST",
        "token_address": "SyntheticTestMintNotARealToken",
        "ai_test_mode": True,
        "momentum_state": "SURGING",
        "momentum_score": 95,
        "quant_score_raw": 95,
        "score_delta": 40,
        "price_usd": 0.00125,
        "price_5m": 4.2,
        "price_1h": 13.5,
        "volume_5m": 18000,
        "volume_1h": 85000,
        "volume_acceleration": 2.54,
        "buy_sell_ratio_5m": 1.65,
        "buys_5m": 52,
        "sells_5m": 31,
        "liquidity": 95000,
        "market_cap": 725000,
        "holder_count": 640,
        "holder_count_capped": False,
        "holder_change_10m": 34,
        "holder_change_10m_pct": 5.6,
        "holder_change_30m": 101,
        "holder_change_30m_pct": 18.7,
        "market_cap_per_holder": 1132.81,
        "whale_score_bonus": 10,
        "whale_activity": [{
            "trader_name": "Synthetic verified wallet",
            "points": 10,
            "largest_buy_usd": 2500,
            "total_spend_usd": 2500,
            "latest_estimated_spend_usd": 2500,
            "age_minutes": 4,
            "campaign_pattern": "LARGE_POSITION",
        }],
        "token_social_bonus": 4,
        "token_social_detail": {
            "status": "OK",
            "posts_10m": 4,
            "posts_30m": 7,
            "unique_authors_10m": 3,
            "unique_authors_30m": 5,
            "contract_mentions": 2,
            "velocity_ratio": 1.8,
            "duplicate_ratio": 0.0,
            "engagement": 28,
        },
        "composite_score": 109,
        "entry_priority_score": 129,
    }

    # Synthetic test is not written to the normal AI confirmation log.
    try:
        review = luna_candidate_review(candidate, settings)
    except Exception as exc:
        print(f"LUNA TEST FAILED: {exc}")
        return False

    if review.get("status") not in {"OK", "CACHED"}:
        print(f"LUNA TEST FAILED: {review.get('status')}")
        return False

    print("LUNA TEST PASSED")
    print(f"Model:      {review.get('model')}")
    print(f"Assessment: {review.get('assessment')}")
    print(f"Confidence: {review.get('confidence')}%")
    print(f"Risk:       {review.get('risk_level')}")
    print(f"Setup:      {review.get('setup_type')}")
    print(f"Continue:   {review.get('continuation_band')}")
    print(f"Bonus:      {safe_number(review.get('ai_bonus')):+.0f}")
    print(f"Summary:    {review.get('summary')}")
    print(
        f"Tokens:     in {int(safe_number(review.get('input_tokens')))} | "
        f"out {int(safe_number(review.get('output_tokens')))}"
    )
    return True


def main():
    ensure_dirs()

    if "--test-ai" in sys.argv:
        ok = test_luna_confirmation()
        sys.exit(0 if ok else 1)

    if "--test-eod" in sys.argv:
        ok = test_crypto_eod_pushover()
        sys.exit(0 if ok else 1)

    if "--test-eod-group" in sys.argv:
        ok = test_eod_group_pushover()
        sys.exit(0 if ok else 1)

    if "--test-movement-group" in sys.argv:
        ok = test_movement_group_pushover()
        sys.exit(0 if ok else 1)

    try:
        (
            settings,
            api_key,
            signer,
            wallet_address,
        ) = load_settings()
    except Exception as exc:
        print(f"CONFIG ERROR: {exc}")
        sys.exit(1)

    print_settings(
        settings,
        wallet_address,
    )

    if "--send-eod-now" in sys.argv:
        ok = maybe_send_crypto_eod_report(
            settings,
            api_key,
            wallet_address,
            force=True,
        )
        sys.exit(0 if ok else 1)

    if settings["LIVE_TRADING"]:
        print()
        print(
            "*** REAL MONEY MODE IS ENABLED ***"
        )

        require_start_live_confirmation = (
            str(os.getenv("REQUIRE_START_LIVE_CONFIRMATION", "1"))
            .strip()
            .lower()
            not in {"0", "false", "no", "off"}
        )

        if require_start_live_confirmation:
            print("Type exactly START LIVE to begin:")
            if input("> ").strip() != "START LIVE":
                print("Cancelled.")
                return
        else:
            print("Live startup confirmation: DISABLED (automatic)")

        if pushover_configured():
            if send_pushover(
                "CryptoTracker LIVE",
                (
                    f"Live trading started.\n"
                    f"Normal size: ${settings['NORMAL_TRADE_SIZE_USDC']:.2f} | "
                    f"Early size: ${settings['EARLY_ACCEL_TRADE_SIZE_USDC']:.2f}\n"
                    f"Daily target: +{settings['DAILY_TARGET_PCT']:.2f}% | "
                    f"Max DD: -{settings['MAX_DAILY_DRAWDOWN_PCT']:.2f}%\n"
                    f"Max completed trades/day: {settings['MAX_TRADES_PER_DAY']}"
                ),
                priority=0,
                sound="pushover",
            ):
                print("Pushover startup alert sent.")
        else:
            print(
                "WARNING: Pushover keys are not configured; "
                "no phone alerts will be sent."
            )
    else:
        print()
        print(
            "LIVE_TRADING is false. No swaps "
            "will be executed."
        )

    print()
    print("Press Ctrl+C to stop.")

    while True:
        started = time.time()

        try:
            run_cycle(
                settings,
                api_key,
                signer,
                wallet_address,
            )

            # Dedicated once-per-day performance channel. EOD uses its own
            # Delivery Group when set; SURGE / BUY / SELL use the movement group.
            maybe_send_crypto_eod_report(
                settings,
                api_key,
                wallet_address,
            )

        except KeyboardInterrupt:
            print("\nStopped by user.")
            break

        except Exception as exc:
            print()
            print(f"FATAL: {exc}")

            if "UNKNOWN_EXECUTION_STATE" in str(exc):
                print(
                    "HALTING: inspect wallet before restarting."
                )

                send_pushover(
                    "CryptoTracker HALTED",
                    (
                        "UNKNOWN EXECUTION STATE.\n"
                        "Bot has halted to avoid a duplicate trade.\n"
                        "Inspect the wallet before restarting.\n\n"
                        f"Error: {exc}"
                    ),
                    priority=1,
                    sound="siren",
                )
                break

            send_pushover_once(
                f"fatal:{type(exc).__name__}:{str(exc)[:120]}",
                "CryptoTracker ERROR",
                (
                    "A bot cycle failed. It will retry next cycle.\n\n"
                    f"Error: {exc}"
                ),
                cooldown_seconds=900,
                priority=0,
                sound="siren",
            )

            print(
                "Will try again on the next cycle."
            )

        elapsed = time.time() - started

        # Important: scans themselves take time. This schedules the next scan
        # so cycle STARTS are about 60 seconds apart when possible.
        wait = max(
            1,
            settings["SCAN_INTERVAL_SECONDS"]
            - elapsed,
        )

        print(
            f"  Next cycle in {wait:.0f} seconds..."
        )

        try:
            time.sleep(wait)
        except KeyboardInterrupt:
            print("\nStopped by user.")
            break


if __name__ == "__main__":
    main()
