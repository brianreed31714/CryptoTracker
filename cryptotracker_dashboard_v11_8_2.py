from pathlib import Path
from datetime import datetime, timedelta
import json
import os
import re
import subprocess
import sys
import time

import altair as alt
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

st.set_page_config(
    page_title="CryptoTracker Control Center",
    page_icon="🪙",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
section.main > div.block-container,
div[data-testid="stAppViewContainer"] .main .block-container {
  padding-top: 1.2rem !important;
  padding-bottom: 1rem !important;
  padding-left: .35rem !important;
  padding-right: .55rem !important;
  max-width: 100% !important;
}
[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"] {
  display: none !important;
}
.app-title {font-size: 1.45rem; font-weight: 800; margin-bottom: 0; line-height:1.05;}
.subtle {color:#8a94a6; font-size:.72rem; line-height:1.1;}
.status-pill {
  display:inline-block; padding:.25rem .6rem; border-radius:999px;
  font-weight:700; font-size:.78rem; border:1px solid rgba(255,255,255,.12);
}
.good {background:rgba(25,195,125,.13); color:#20d391;}
.warn {background:rgba(255,184,0,.13); color:#ffbd2e;}
.bad {background:rgba(255,80,80,.13); color:#ff6b6b;}
div[data-testid="stMetric"] {
  border:1px solid rgba(130,140,160,.22); border-radius:12px;
  padding:7px 8px; background:rgba(120,130,150,.045);
}

div[data-testid="stMetricLabel"] {font-size:.70rem !important;}
div[data-testid="stMetricValue"] {font-size:1.35rem !important;}
h2, h3 {font-size:1.05rem !important; margin-top:.55rem !important; margin-bottom:.35rem !important;}
div[data-testid="stDataFrame"] {font-size:.72rem;}
.stCaptionContainer, small {font-size:.68rem !important;}
hr {margin:.45rem 0 !important;}
section[data-testid="stSidebar"] {min-width: 240px;}
.entry-header {
  border:1px solid rgba(130,140,160,.25); border-radius:12px;
  padding:.48rem .65rem; margin:.15rem 0 .45rem 0;
  background:rgba(120,130,150,.045);
}
.entry-name {font-size:1.02rem; font-weight:800; line-height:1.15;}
.entry-result-pass {color:#20d391; font-weight:800;}
.entry-result-fail {color:#ff6b6b; font-weight:800;}

.dep-card {
  border:1px solid rgba(130,140,160,.22); border-radius:10px;
  padding:.42rem .52rem; background:rgba(120,130,150,.045); min-height:64px;
}
.dep-name {font-size:.72rem; color:#9aa4b5; line-height:1.1;}
.dep-state {font-size:.94rem; font-weight:800; margin-top:.18rem; line-height:1.15;}
.dep-detail {font-size:.63rem; color:#8a94a6; margin-top:.12rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;}
.run {color:#20d391;}
.stop {color:#ff6b6b;}
.info {color:#79b8ff;}

</style>
""", unsafe_allow_html=True)

ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / ".env"
load_dotenv(ENV_FILE)

DATA_DIR = ROOT / "data"
SNAP_DIR = DATA_DIR / "auto_snapshots"
POSITION_FILE = DATA_DIR / "position.json"
DAILY_STATE_FILE = DATA_DIR / "daily_state_v11.json"
COOLDOWN_FILE = DATA_DIR / "cooldowns.json"
SMART_DIR = ROOT / "SmartMoneyMonitor" / "data"
WALLET_SCORECARD_V22 = SMART_DIR / "wallet_scorecard_v22.csv"
SOCIAL_SENTIMENT_FILE = DATA_DIR / "social_sentiment_current.json"
CONFIRMATION_FEED_FILE = DATA_DIR / "confirmation_feed_log.csv"
REACCEL_WATCH_FILE = DATA_DIR / "reacceleration_watch_v115.json"
REACCEL_LOG_FILE = DATA_DIR / "reacceleration_watch_log.csv"
DISCOVERY_SOURCE_LOG_FILE = DATA_DIR / "discovery_source_log.csv"
X_API_USAGE_FILE = DATA_DIR / "x_api_usage_log.csv"
HOLDER_METRICS_LATEST_FILE = DATA_DIR / "holder_metrics_latest.json"
AI_CONFIRMATION_LOG_FILE = DATA_DIR / "ai_confirmation_log.csv"
CRYPTO_EOD_STATE_FILE = DATA_DIR / "crypto_eod_report_state.json"

def today_str():
    return datetime.now().strftime("%Y-%m-%d")

def latest_snapshot_path():
    p = SNAP_DIR / f"{today_str()}.csv"
    if p.exists():
        return p
    files = sorted(SNAP_DIR.glob("*.csv"), reverse=True)
    return files[0] if files else None

def latest_trade_path():
    p = DATA_DIR / f"trades_{today_str()}.csv"
    if p.exists():
        return p
    files = sorted(DATA_DIR.glob("trades_*.csv"), reverse=True)
    return files[0] if files else None

def read_csv_safe(path):
    try:
        return pd.read_csv(path) if path and path.exists() else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def read_json_safe(path):
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    except Exception:
        return None

def num(v, d=2, prefix="", suffix=""):
    try:
        if pd.isna(v): return "—"
        return f"{prefix}{float(v):,.{d}f}{suffix}"
    except Exception:
        return "—"

def pct(v, d=1):
    try:
        if pd.isna(v): return "—"
        return f"{float(v):+.{d}f}%"
    except Exception:
        return "—"


def env_float(name, default):
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return float(default)

def env_int(name, default):
    try:
        return int(float(os.getenv(name, default)))
    except (TypeError, ValueError):
        return int(default)

def env_bool(name, default=True):
    value = os.getenv(name)
    if value is None:
        return bool(default)
    return str(value).strip().lower() in {"1","true","yes","y","on"}

def current_entry_settings():
    """Read the live V11.8.2 entry / protection thresholds from .env."""
    return {
        # NORMAL
        "MIN_BUY_SCORE": env_float("MIN_BUY_SCORE", 80),
        "MIN_BUY_SCORE_DELTA": env_float("MIN_BUY_SCORE_DELTA", 20),
        "MIN_BUY_LIQUIDITY": env_float("MIN_BUY_LIQUIDITY", 40000),
        "MIN_BUY_5M_VOLUME": env_float("MIN_BUY_5M_VOLUME", 2000),
        "MIN_BUY_VOLUME_ACCEL": env_float("MIN_BUY_VOLUME_ACCEL", 1.50),
        "MIN_BUY_SELL_RATIO": env_float("MIN_BUY_SELL_RATIO", 1.20),
        "MIN_BUY_5M_PCT": env_float("MIN_BUY_5M_PCT", 1.00),
        "MAX_BUY_5M_PCT": env_float("MAX_BUY_5M_PCT", 15.00),
        "MIN_BUY_1H_PCT": env_float("MIN_BUY_1H_PCT", -10.00),
        "MAX_BUY_1H_PCT": env_float("MAX_BUY_1H_PCT", 40.00),
        "MIN_5M_TRANSACTIONS": env_int("MIN_5M_TRANSACTIONS", 15),

        # EARLY_ACCEL
        "EARLY_ACCEL_MIN_SCORE": env_float("EARLY_ACCEL_MIN_SCORE", 60),
        "EARLY_ACCEL_MIN_SCORE_DELTA": env_float("EARLY_ACCEL_MIN_SCORE_DELTA", 35),
        "EARLY_ACCEL_MIN_LIQUIDITY": env_float("EARLY_ACCEL_MIN_LIQUIDITY", 50000),
        "EARLY_ACCEL_MIN_5M_VOLUME": env_float("EARLY_ACCEL_MIN_5M_VOLUME", 750),
        "EARLY_ACCEL_MIN_VOLUME_ACCEL": env_float("EARLY_ACCEL_MIN_VOLUME_ACCEL", 2.50),
        "EARLY_ACCEL_MIN_BUY_SELL_RATIO": env_float("EARLY_ACCEL_MIN_BUY_SELL_RATIO", 1.40),
        "EARLY_ACCEL_MIN_5M_PCT": env_float("EARLY_ACCEL_MIN_5M_PCT", 1.00),
        "EARLY_ACCEL_MAX_5M_PCT": env_float("EARLY_ACCEL_MAX_5M_PCT", 10.00),
        "EARLY_ACCEL_MIN_1H_PCT": env_float("EARLY_ACCEL_MIN_1H_PCT", -10.00),
        "EARLY_ACCEL_MAX_1H_PCT": env_float("EARLY_ACCEL_MAX_1H_PCT", 30.00),
        "EARLY_ACCEL_MIN_5M_TRANSACTIONS": env_int("EARLY_ACCEL_MIN_5M_TRANSACTIONS", 15),
        "EARLY_CONFIRM_MIN_POINTS": env_int("EARLY_CONFIRM_MIN_POINTS", 3),
        "EARLY_CONFIRM_MIN_POSITIVE_FLOW_POINTS": env_int("EARLY_CONFIRM_MIN_POSITIVE_FLOW_POINTS", 2),
        "EARLY_CONFIRM_MIN_RISING_SCORE_POINTS": env_int("EARLY_CONFIRM_MIN_RISING_SCORE_POINTS", 1),

        # Execution / ranking
        "NORMAL_MIN_ROUNDTRIP_RETURN_PCT": env_float("NORMAL_MIN_ROUNDTRIP_RETURN_PCT", 97.0),
        "EARLY_MIN_ROUNDTRIP_RETURN_PCT": env_float("EARLY_MIN_ROUNDTRIP_RETURN_PCT", 98.5),
        "DELTA_RANK_MAX_BONUS": env_float("DELTA_RANK_MAX_BONUS", 5.0),

        # Protection / hold
        "PRE_RUNNER_PROTECT_ACTIVATE_PCT": env_float("PRE_RUNNER_PROTECT_ACTIVATE_PCT", 6.0),
        "PRE_RUNNER_PROFIT_FLOOR_PCT": env_float("PRE_RUNNER_PROFIT_FLOOR_PCT", 2.0),
        "MAX_HOLD_MINUTES": env_float("MAX_HOLD_MINUTES", 30.0),
        "EXTENDED_HOLD_MAX_MINUTES": env_float("EXTENDED_HOLD_MAX_MINUTES", 60.0),

        # Re-entry
        "COOLDOWN_MINUTES": env_float("COOLDOWN_MINUTES", 20),
        "ALLOW_STRONG_REENTRY": env_bool("ALLOW_STRONG_REENTRY", True),
        "MAX_ENTRIES_PER_TOKEN_60M": env_int("MAX_ENTRIES_PER_TOKEN_60M", 1),
        "REENTRY_MIN_SCORE": env_float("REENTRY_MIN_SCORE", 120),
        "REENTRY_MIN_SCORE_DELTA": env_float("REENTRY_MIN_SCORE_DELTA", 35),
        "REENTRY_MIN_LIQUIDITY": env_float("REENTRY_MIN_LIQUIDITY", 75000),
        "REENTRY_MIN_5M_VOLUME": env_float("REENTRY_MIN_5M_VOLUME", 10000),
        "REENTRY_MIN_VOLUME_ACCEL": env_float("REENTRY_MIN_VOLUME_ACCEL", 1.75),
        "REENTRY_MIN_BUY_SELL_RATIO": env_float("REENTRY_MIN_BUY_SELL_RATIO", 1.75),
        "REENTRY_MIN_5M_PCT": env_float("REENTRY_MIN_5M_PCT", 2.00),
        "REENTRY_MAX_5M_PCT": env_float("REENTRY_MAX_5M_PCT", 15.00),
        "REENTRY_MIN_1H_PCT": env_float("REENTRY_MIN_1H_PCT", 10.00),
        "REENTRY_MIN_5M_TRANSACTIONS": env_int("REENTRY_MIN_5M_TRANSACTIONS", 15),
    }


def cooldown_is_active(token_address, settings):
    data = read_json_safe(COOLDOWN_FILE) or {}
    text = data.get(str(token_address), "")
    if not text:
        return False
    try:
        sold_at = datetime.fromisoformat(text)
        return (datetime.now() - sold_at) < timedelta(minutes=settings["COOLDOWN_MINUTES"])
    except Exception:
        return False

def entries_last_60m(token_address, trades_df):
    if trades_df is None or trades_df.empty:
        return 0
    if "action" not in trades_df.columns:
        return 0
    df = trades_df[trades_df["action"].astype(str).str.upper() == "BUY"].copy()
    token_col = next((c for c in ["token_address","token_mint","mint"] if c in df.columns), None)
    if token_col:
        df = df[df[token_col].astype(str) == str(token_address)]
    elif "symbol" in df.columns:
        return 0
    ts_col = next((c for c in ["timestamp","time","entry_time"] if c in df.columns), None)
    if not ts_col:
        return 0
    ts = pd.to_datetime(df[ts_col], errors="coerce")
    cutoff = pd.Timestamp.now() - pd.Timedelta(minutes=60)
    try:
        if getattr(ts.dt, "tz", None) is not None:
            cutoff = cutoff.tz_localize(ts.dt.tz)
    except Exception:
        pass
    return int((ts >= cutoff).sum())

def _early_persistence_status(token_address, snaps_df, settings):
    """Mirror V11.8 EARLY persistence using recent snapshot rows."""
    if snaps_df is None or snaps_df.empty or not token_address:
        return False, "no trajectory data"

    if "token_address" not in snaps_df.columns:
        return False, "no token-address trajectory"

    hist = snaps_df[snaps_df["token_address"].astype(str) == str(token_address)].copy()
    if hist.empty:
        return False, "no prior scans"

    if "timestamp" in hist.columns:
        hist["timestamp"] = pd.to_datetime(hist["timestamp"], errors="coerce")
        hist = hist.sort_values("timestamp")

    min_points = max(2, int(settings["EARLY_CONFIRM_MIN_POINTS"]))
    hist = hist.tail(max(6, min_points))

    if len(hist) < min_points:
        return False, f"{len(hist)}/{min_points} scans"

    recent = hist.tail(min_points)
    p5 = pd.to_numeric(recent.get("price_5m", 0), errors="coerce").fillna(0)
    bs = pd.to_numeric(recent.get("buy_sell_ratio_5m", 0), errors="coerce").fillna(0)
    scores = pd.to_numeric(recent.get("momentum_score", 0), errors="coerce").fillna(0)

    positive_flow = int(((p5 > 0) & (bs >= 1.20)).sum())
    rising = int((scores.diff() > 0).sum())

    need_flow = int(settings["EARLY_CONFIRM_MIN_POSITIVE_FLOW_POINTS"])
    need_rising = int(settings["EARLY_CONFIRM_MIN_RISING_SCORE_POINTS"])

    ok = positive_flow >= need_flow and rising >= need_rising
    detail = (
        f"{len(recent)} scans | positive flow {positive_flow}/{need_flow} | "
        f"score rises {rising}/{need_rising}"
    )
    return ok, detail


def build_entry_check(candidate, trades_df, snaps_df):
    """Dashboard mirror of the V11.8.2 local quant gates."""
    s = current_entry_settings()

    score = float(candidate.get("momentum_score", 0) or 0)
    delta = float(candidate.get("score_delta", 0) or 0)
    liq = float(candidate.get("liquidity", 0) or 0)
    vol5 = float(candidate.get("volume_5m", 0) or 0)
    volx = float(candidate.get("volume_acceleration", 0) or 0)
    bs = float(candidate.get("buy_sell_ratio_5m", 0) or 0)
    p5 = float(candidate.get("price_5m", 0) or 0)
    p1h = float(candidate.get("price_1h", 0) or 0)
    buys = float(candidate.get("buys_5m", 0) or 0)
    sells = float(candidate.get("sells_5m", 0) or 0)
    tx5 = buys + sells
    state = str(candidate.get("momentum_state", "")).upper()
    token = str(candidate.get("token_address", ""))

    normal_checks = [
        ("Raw score", score >= s["MIN_BUY_SCORE"], f"{score:.0f}", f">= {s['MIN_BUY_SCORE']:.0f}"),
        ("Score delta", delta >= s["MIN_BUY_SCORE_DELTA"], f"{delta:+.0f}", f">= +{s['MIN_BUY_SCORE_DELTA']:.0f}"),
        ("Liquidity", liq >= s["MIN_BUY_LIQUIDITY"], f"${liq:,.0f}", f">= ${s['MIN_BUY_LIQUIDITY']:,.0f}"),
        ("5m volume", vol5 >= s["MIN_BUY_5M_VOLUME"], f"${vol5:,.0f}", f">= ${s['MIN_BUY_5M_VOLUME']:,.0f}"),
        ("Volume accel", volx >= s["MIN_BUY_VOLUME_ACCEL"], f"{volx:.2f}x", f">= {s['MIN_BUY_VOLUME_ACCEL']:.2f}x"),
        ("Buy/sell", bs >= s["MIN_BUY_SELL_RATIO"], f"{bs:.2f}", f">= {s['MIN_BUY_SELL_RATIO']:.2f}"),
        ("5m move min", p5 >= s["MIN_BUY_5M_PCT"], f"{p5:+.1f}%", f">= +{s['MIN_BUY_5M_PCT']:.1f}%"),
        ("5m move max", p5 <= s["MAX_BUY_5M_PCT"], f"{p5:+.1f}%", f"<= +{s['MAX_BUY_5M_PCT']:.1f}%"),
        ("1h move min", p1h >= s["MIN_BUY_1H_PCT"], f"{p1h:+.1f}%", f">= {s['MIN_BUY_1H_PCT']:+.1f}%"),
        ("1h move max", p1h <= s["MAX_BUY_1H_PCT"], f"{p1h:+.1f}%", f"<= +{s['MAX_BUY_1H_PCT']:.1f}%"),
        ("5m transactions", tx5 >= s["MIN_5M_TRANSACTIONS"], f"{tx5:.0f}", f">= {s['MIN_5M_TRANSACTIONS']}"),
    ]

    early_checks = [
        ("Raw score", score >= s["EARLY_ACCEL_MIN_SCORE"], f"{score:.0f}", f">= {s['EARLY_ACCEL_MIN_SCORE']:.0f}"),
        ("Score delta", delta >= s["EARLY_ACCEL_MIN_SCORE_DELTA"], f"{delta:+.0f}", f">= +{s['EARLY_ACCEL_MIN_SCORE_DELTA']:.0f}"),
        ("Liquidity", liq >= s["EARLY_ACCEL_MIN_LIQUIDITY"], f"${liq:,.0f}", f">= ${s['EARLY_ACCEL_MIN_LIQUIDITY']:,.0f}"),
        ("5m volume", vol5 >= s["EARLY_ACCEL_MIN_5M_VOLUME"], f"${vol5:,.0f}", f">= ${s['EARLY_ACCEL_MIN_5M_VOLUME']:,.0f}"),
        ("Volume accel", volx >= s["EARLY_ACCEL_MIN_VOLUME_ACCEL"], f"{volx:.2f}x", f">= {s['EARLY_ACCEL_MIN_VOLUME_ACCEL']:.2f}x"),
        ("Buy/sell", bs >= s["EARLY_ACCEL_MIN_BUY_SELL_RATIO"], f"{bs:.2f}", f">= {s['EARLY_ACCEL_MIN_BUY_SELL_RATIO']:.2f}"),
        ("5m move min", p5 >= s["EARLY_ACCEL_MIN_5M_PCT"], f"{p5:+.1f}%", f">= +{s['EARLY_ACCEL_MIN_5M_PCT']:.1f}%"),
        ("5m move max", p5 <= s["EARLY_ACCEL_MAX_5M_PCT"], f"{p5:+.1f}%", f"<= +{s['EARLY_ACCEL_MAX_5M_PCT']:.1f}%"),
        ("1h move min", p1h >= s["EARLY_ACCEL_MIN_1H_PCT"], f"{p1h:+.1f}%", f">= {s['EARLY_ACCEL_MIN_1H_PCT']:+.1f}%"),
        ("1h move max", p1h <= s["EARLY_ACCEL_MAX_1H_PCT"], f"{p1h:+.1f}%", f"<= +{s['EARLY_ACCEL_MAX_1H_PCT']:.1f}%"),
        ("5m transactions", tx5 >= s["EARLY_ACCEL_MIN_5M_TRANSACTIONS"], f"{tx5:.0f}", f">= {s['EARLY_ACCEL_MIN_5M_TRANSACTIONS']}"),
    ]

    normal_pass = all(ok for _, ok, _, _ in normal_checks)
    early_quant_pass = all(ok for _, ok, _, _ in early_checks)
    persistence_ok, persistence_detail = _early_persistence_status(token, snaps_df, s)

    if normal_pass:
        path = "NORMAL"
        path_checks = normal_checks
    elif early_quant_pass and persistence_ok:
        path = "EARLY_ACCEL"
        path_checks = early_checks + [
            ("EARLY persistence", True, persistence_detail, "persistent across recent scans")
        ]
    elif early_quant_pass:
        path = "EARLY_PENDING"
        path_checks = early_checks + [
            ("EARLY persistence", False, persistence_detail, "persistent across recent scans")
        ]
    else:
        normal_fails = sum(1 for _, ok, _, _ in normal_checks if not ok)
        early_fails = sum(1 for _, ok, _, _ in early_checks if not ok)
        path = "NONE"
        path_checks = normal_checks if normal_fails <= early_fails else early_checks

    cooldown = cooldown_is_active(token, s)
    entries = entries_last_60m(token, trades_df)

    reentry = (
        s["ALLOW_STRONG_REENTRY"]
        and entries < s["MAX_ENTRIES_PER_TOKEN_60M"]
        and state == "SURGING"
        and score >= s["REENTRY_MIN_SCORE"]
        and delta >= s["REENTRY_MIN_SCORE_DELTA"]
        and liq >= s["REENTRY_MIN_LIQUIDITY"]
        and vol5 >= s["REENTRY_MIN_5M_VOLUME"]
        and volx >= s["REENTRY_MIN_VOLUME_ACCEL"]
        and bs >= s["REENTRY_MIN_BUY_SELL_RATIO"]
        and p5 >= s["REENTRY_MIN_5M_PCT"]
        and p5 <= s["REENTRY_MAX_5M_PCT"]
        and p1h >= s["REENTRY_MIN_1H_PCT"]
        and tx5 >= s["REENTRY_MIN_5M_TRANSACTIONS"]
    )

    rows = [("State", state == "SURGING", state or "—", "SURGING")] + path_checks
    rows.append((
        "Cooldown",
        (not cooldown) or reentry,
        "OVERRIDDEN" if reentry else ("ACTIVE" if cooldown else "clear"),
        "clear or strong re-entry",
    ))

    failed = [name for name, ok, _, _ in rows if not ok]
    return rows, path, failed


def _parse_any_datetime(value):
    """Parse timestamps and normalize them to local, timezone-naive datetimes.

    Some dependency files use UTC/offset-aware timestamps (for example social
    sentiment), while local CSV/file timestamps are timezone-naive. Normalizing
    here prevents Python from trying to compare aware and naive datetimes.
    """
    if value in (None, ""):
        return None
    try:
        ts = pd.to_datetime(value, errors="coerce")
        if pd.isna(ts):
            return None
        dt = ts.to_pydatetime()
        if getattr(dt, "tzinfo", None) is not None:
            dt = dt.astimezone().replace(tzinfo=None)
        return dt
    except Exception:
        return None


def _age_text(dt):
    if dt is None:
        return "—"
    try:
        now = datetime.now(dt.tzinfo) if getattr(dt, "tzinfo", None) else datetime.now()
        seconds = max(0, (now - dt).total_seconds())
        if seconds < 60:
            return f"{seconds:.0f}s ago"
        if seconds < 3600:
            return f"{seconds/60:.1f}m ago"
        return f"{seconds/3600:.1f}h ago"
    except Exception:
        return "—"


@st.cache_data(ttl=5, show_spinner=False)
def running_processes():
    """Best-effort local process discovery. Read-only; never starts/stops anything."""
    rows = []
    if os.name == "nt":
        command = (
            "Get-CimInstance Win32_Process | "
            "Where-Object { $_.Name -match '^python(w)?\\.exe$' -or $_.CommandLine -match 'python|streamlit' } | "
            "Select-Object ProcessId,Name,CommandLine | ConvertTo-Json -Compress"
        )
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                capture_output=True, text=True, timeout=4, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if result.returncode == 0 and result.stdout.strip():
                parsed = json.loads(result.stdout)
                if isinstance(parsed, dict):
                    parsed = [parsed]
                for item in parsed:
                    rows.append({
                        "pid": item.get("ProcessId"),
                        "name": item.get("Name", ""),
                        "cmd": item.get("CommandLine", "") or "",
                    })
                return rows
        except Exception:
            pass

    # macOS/Linux fallback; also useful if the dashboard is ever moved off Windows.
    try:
        result = subprocess.run(
            ["ps", "-eo", "pid,args"], capture_output=True, text=True, timeout=3
        )
        for line in result.stdout.splitlines()[1:]:
            parts = line.strip().split(None, 1)
            if len(parts) == 2 and ("python" in parts[1].lower() or "streamlit" in parts[1].lower()):
                rows.append({"pid": parts[0], "name": "python", "cmd": parts[1]})
    except Exception:
        pass
    return rows


def process_match(processes, patterns):
    """
    Regex-based process matcher.

    Searches BOTH the process name and full command line. This is more robust
    on Windows than relying on a literal filename fragment in CommandLine.
    Each item in patterns is a regular expression.
    """
    compiled = [re.compile(p, re.IGNORECASE) for p in patterns]

    for proc in processes:
        haystack = " ".join([
            str(proc.get("name", "") or ""),
            str(proc.get("cmd", "") or ""),
        ])

        if any(rx.search(haystack) for rx in compiled):
            return proc

    return None


def daily_trade_metrics(trades_df):
    """Return completed trades, realized $, deployed $, return %, wins and losses.

    Daily return is realized P/L divided by capital deployed across completed trades.
    That makes it a trade-performance percentage, not a whole-wallet return.
    """
    if trades_df is None or trades_df.empty or "action" not in trades_df.columns:
        return 0, 0.0, 0.0, 0.0, 0, 0
    sells = trades_df[trades_df["action"].astype(str).str.upper() == "SELL"].copy()
    if sells.empty:
        return 0, 0.0, 0.0, 0.0, 0, 0
    pnl = pd.to_numeric(sells.get("realized_pnl_usd", 0), errors="coerce").fillna(0)
    deployed = pd.to_numeric(sells.get("input_usd", 0), errors="coerce").fillna(0)
    realized = float(pnl.sum())
    capital = float(deployed.sum())
    return_pct = realized / capital * 100.0 if capital > 0 else 0.0
    wins = int((pnl > 0).sum())
    losses = int((pnl < 0).sum())
    return len(sells), realized, capital, return_pct, wins, losses


def dependency_activity_rows(snap_path, snaps_df, trade_path, trades_df):
    """Build an observed-activity log from dependency outputs.

    This reflects data/file updates, which is more reliable than scraping another
    process's terminal window. It is not a packet-level log of every HTTP request.
    """
    rows = []

    if snap_path and snap_path.exists():
        dt = None
        if not snaps_df.empty and "timestamp" in snaps_df.columns:
            valid = pd.to_datetime(snaps_df["timestamp"], errors="coerce").dropna()
            if not valid.empty:
                dt = valid.max().to_pydatetime()
        dt = dt or datetime.fromtimestamp(snap_path.stat().st_mtime)
        rows.append({"Time": dt, "Source": "Trader / Market Scanner", "Activity": "DEX scan snapshot updated", "Detail": snap_path.name})

    if trade_path and trade_path.exists() and trades_df is not None and not trades_df.empty:
        last = trades_df.iloc[-1]
        dt = _parse_any_datetime(last.get("timestamp")) or datetime.fromtimestamp(trade_path.stat().st_mtime)
        detail = f"{last.get('action', 'TRADE')} {last.get('symbol', '')}".strip()
        reason = last.get("reason", "")
        if pd.notna(reason) and str(reason).strip():
            detail += f" | {reason}"
        rows.append({"Time": dt, "Source": "Trader", "Activity": "Trade log updated", "Detail": detail})

    events_path = SMART_DIR / "smart_money_events_v21.csv"
    events = read_csv_safe(events_path)
    if events_path.exists():
        dt = datetime.fromtimestamp(events_path.stat().st_mtime)
        detail = events_path.name
        if not events.empty:
            last = events.iloc[-1]
            for col in ["timestamp", "detected_at", "event_time"]:
                if col in events.columns:
                    dt = _parse_any_datetime(last.get(col)) or dt
                    break
            detail = " | ".join(str(last.get(c, "")) for c in ["trader", "action", "symbol"] if c in events.columns and str(last.get(c, "")).strip()) or detail
        rows.append({"Time": dt, "Source": "Smart Money", "Activity": "Whale data updated", "Detail": detail})

    rows.sort(key=lambda r: r["Time"] if r["Time"] is not None else datetime.min, reverse=True)
    for row in rows:
        row["Age"] = _age_text(row["Time"])
        row["Time"] = row["Time"].strftime("%H:%M:%S") if row["Time"] else "—"
    return rows


refresh = 10

h1,h2 = st.columns([5.2,1])
with h1:
    st.markdown('<div class="app-title">CryptoTracker</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtle">V11.8.2 • sustained momentum • Luna • smart money • protection</div>', unsafe_allow_html=True)
with h2:
    st.markdown("**READ ONLY**")
    st.caption(f"Refresh: {refresh}s")

snap_path = latest_snapshot_path()
trade_path = latest_trade_path()
snaps = read_csv_safe(snap_path)
trades = read_csv_safe(trade_path)
position = read_json_safe(POSITION_FILE)
daily_state = read_json_safe(DAILY_STATE_FILE) or {}
holder_metrics_state = read_json_safe(HOLDER_METRICS_LATEST_FILE) or {}
holder_metrics_tokens = (
    holder_metrics_state.get("tokens") or {}
    if isinstance(holder_metrics_state, dict)
    else {}
)

# Resolve trader state BEFORE rendering scanner health. The scanner is embedded
# in the trader, and V11.x intentionally pauses market scans while monitoring an
# open position or after a persistent daily risk lock.
_status_processes = running_processes()
_status_trader_proc = process_match(_status_processes, [
    r"auto_trader_with_alerts.*\.py",
])

def _today_daily_lock_reason():
    """Return a current-day persistent risk-lock explanation, if one exists."""
    if str(daily_state.get("date") or "") != today_str():
        return ""

    if bool(daily_state.get("drawdown_locked")):
        return "daily drawdown circuit breaker locked"

    if bool(daily_state.get("target_locked")):
        return "daily target locked"

    return ""

def _trade_limit_pause_reason(trades_df):
    """Detect flat-state entry limits that intentionally stop new scans/entries."""
    try:
        completed_now, realized_now, _, _, _, _ = daily_trade_metrics(trades_df)
    except Exception:
        completed_now, realized_now = 0, 0.0

    try:
        max_trades = int(float(os.getenv("MAX_TRADES_PER_DAY", "14")))
    except Exception:
        max_trades = 14

    try:
        max_realized_loss = abs(float(os.getenv("DAILY_REALIZED_LOSS_LIMIT_USD", "3.0")))
    except Exception:
        max_realized_loss = 3.0

    if completed_now >= max_trades:
        return f"daily trade limit reached ({completed_now}/{max_trades})"

    if realized_now <= -max_realized_loss:
        return (
            f"absolute daily loss limit reached "
            f"(${realized_now:+.2f} <= -${max_realized_loss:.2f})"
        )

    return ""

# ------------------------------------------------------------------
# LIVE SCANNER / SURGING DIAGNOSTICS — status-aware
# ------------------------------------------------------------------
st.markdown("### Live Scanner")

scanner_age = None
if snap_path and snap_path.exists():
    scanner_age = max(0.0, time.time() - snap_path.stat().st_mtime)

pause_reason = _today_daily_lock_reason()
if not pause_reason and not position:
    pause_reason = _trade_limit_pause_reason(trades)

if not _status_trader_proc:
    # No matching trader process means this is genuinely stopped, regardless of
    # how recent the last snapshot happens to be.
    status_text, status_class = "TRADER / SCANNER STOPPED", "bad"
    status_detail = "No auto_trader_with_alerts*.py process detected."

elif position:
    symbol = str(position.get("symbol") or "open token")
    status_text, status_class = "POSITION MONITORING — SCAN PAUSED", "info"
    status_detail = (
        f"Trader is running and monitoring {symbol}. "
        "Market discovery snapshots pause while a position is open."
    )

elif pause_reason:
    status_text, status_class = "ENTRIES DISABLED — SCAN PAUSED", "warn"
    status_detail = f"Trader is running. {pause_reason}."

elif scanner_age is None:
    status_text, status_class = "WAITING FOR FIRST SCAN", "warn"
    status_detail = "Trader is running but no snapshot CSV exists yet."

elif scanner_age <= 150:
    status_text, status_class = "SCANNER LIVE", "good"
    status_detail = (
        f"Trader running | snapshot age {scanner_age / 60.0:.1f} min."
    )

elif scanner_age <= 600:
    status_text, status_class = "SCANNER DELAYED", "warn"
    status_detail = (
        f"Trader is running, but the latest completed snapshot is "
        f"{scanner_age / 60.0:.1f} min old."
    )

else:
    # Important distinction from the old dashboard: the trader process exists,
    # so do not claim it is stopped just because the snapshot is old.
    status_text, status_class = "SCANNER STALE — TRADER RUNNING", "bad"
    status_detail = (
        f"Trader process detected, but no completed market snapshot for "
        f"{scanner_age / 60.0:.1f} min. Check the trader console for a hang/error."
    )

st.markdown(
    f'<span class="status-pill {status_class}">● {status_text}</span>',
    unsafe_allow_html=True,
)
st.caption(status_detail)

if "timestamp" in snaps.columns and snaps["timestamp"].notna().any():
    newest_display = snaps["timestamp"].max()
    st.caption(f"Latest scanner data: {newest_display}")

st.divider()

if snaps.empty:
    st.warning("No CryptoTracker snapshot CSV found yet.")
    st.info("This dashboard expects data/auto_snapshots/YYYY-MM-DD.csv from the current CryptoTracker.")
    time.sleep(refresh)
    st.rerun()

# Normalize numerics
numeric_cols = [
    "price_usd","market_cap","liquidity","volume_5m","volume_1h","volume_6h","volume_24h",
    "price_5m","price_1h","price_6h","price_24h","buys_5m","sells_5m",
    "buy_sell_ratio_5m","volume_acceleration","momentum_score","score_delta",
    "price_delta_pct","volume_delta_pct","liquidity_delta_pct"
]
for c in numeric_cols:
    if c in snaps.columns:
        snaps[c] = pd.to_numeric(snaps[c], errors="coerce")

if "timestamp" in snaps.columns:
    snaps["timestamp"] = pd.to_datetime(snaps["timestamp"], errors="coerce")

# CURRENT SCAN ONLY.
# The snapshot CSV accumulates all scans throughout the day. Using the most
# recent row for every token mixes stale rows from older cycles with the newest
# scanner output. That is why the dashboard could show a different ENTRY CHECK
# than the live console.
#
# We instead identify the newest scan timestamp and only use rows from that
# current scan window. Scanner rows can be written a few seconds apart, so keep
# a small tolerance around the newest timestamp.
if "timestamp" in snaps.columns and snaps["timestamp"].notna().any():
    newest_ts = snaps["timestamp"].max()
    current_cutoff = newest_ts - pd.Timedelta(seconds=20)
    current_scan = snaps[snaps["timestamp"] >= current_cutoff].copy()
else:
    newest_ts = None
    current_scan = snaps.tail(150).copy()

# If duplicate rows for a token occur inside the same scan window, keep only
# the newest one for that token.
if "token_address" in current_scan.columns:
    if "timestamp" in current_scan.columns:
        current_scan = (
            current_scan
            .sort_values("timestamp")
            .groupby("token_address", as_index=False)
            .tail(1)
        )
    else:
        current_scan = current_scan.drop_duplicates("token_address", keep="last")

# V11.8 ranking: raw quant dominates; delta is only a small capped tie-breaker.
latest = current_scan.copy()
if not latest.empty:
    delta_cap = env_float("DELTA_RANK_MAX_BONUS", 5.0)
    latest["_dashboard_priority"] = (
        pd.to_numeric(latest.get("momentum_score", 0), errors="coerce").fillna(0)
        + (
            pd.to_numeric(latest.get("score_delta", 0), errors="coerce")
            .fillna(0)
            .clip(lower=0) * 0.10
        ).clip(upper=delta_cap)
    )
    latest = latest.sort_values(
        ["_dashboard_priority", "momentum_score"],
        ascending=[False, False],
        na_position="last",
    )

best = latest.iloc[0] if not latest.empty else None
surging = latest[
    latest.get(
        "momentum_state",
        pd.Series(index=latest.index, dtype=str),
    ).astype(str).str.upper() == "SURGING"
]
building = latest[
    latest.get(
        "momentum_state",
        pd.Series(index=latest.index, dtype=str),
    ).astype(str).str.upper().isin(["BUILDING", "STRONG"])
]
watch_count = len(latest)

# Live ENTRY CHECK.
# IMPORTANT: the trader's console audits SURGING candidates, not simply the
# highest raw-score token. A FADING token can have the highest score and still
# never be the candidate shown in the console ENTRY CHECK.
entry_candidate = surging.iloc[0] if not surging.empty else None

if entry_candidate is not None:
    entry_rows, entry_path, entry_failed = build_entry_check(entry_candidate, trades, snaps)
    symbol = str(entry_candidate.get("symbol", "—"))
    state = str(entry_candidate.get("momentum_state", "—"))
    score = float(entry_candidate.get("momentum_score", 0) or 0)
    delta = float(entry_candidate.get("score_delta", 0) or 0)
    result_text = (
        "LOCAL ENTRY GATES PASSED"
        if not entry_failed
        else "REJECTED — " + ", ".join(entry_failed)
    )
    result_class = "entry-result-pass" if not entry_failed else "entry-result-fail"

    st.markdown(
        f"""
        <div class="entry-header">
          <div class="entry-name">
            ENTRY CHECK: {symbol}
            &nbsp;•&nbsp; {state}
            &nbsp;•&nbsp; Score {score:.0f}
            &nbsp;•&nbsp; Δ {delta:+.0f}
          </div>
          <div class="{result_class}">{result_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    entry_df = pd.DataFrame(
        [
            {
                "Status": "PASS" if ok else "FAIL",
                "Check": name,
                "Current": current,
                "Required": required,
            }
            for name, ok, current, required in entry_rows
        ]
    )

    def _entry_style(row):
        if row["Status"] == "PASS":
            return ["color:#20d391;font-weight:700", "", "", ""]
        return ["color:#ff6b6b;font-weight:800", "", "", ""]

    st.dataframe(
        entry_df.style.apply(_entry_style, axis=1),
        hide_index=True,
        use_container_width=True,
        height=350,
        column_config={
            "Status": st.column_config.TextColumn(""),
            "Check": st.column_config.TextColumn("Check", width="medium"),
            "Current": st.column_config.TextColumn("Current", width="medium"),
            "Required": st.column_config.TextColumn("Required", width="large"),
        },
    )
    st.caption(
        "Local gate calculation from the current snapshot + your .env thresholds. "
        "Jupiter preflight/execution happens after these gates pass."
    )
    st.divider()
else:
    st.markdown(
        """
        <div class="entry-header">
          <div class="entry-name">ENTRY CHECK: no SURGING candidate</div>
          <div class="entry-result-fail">No token currently qualifies for entry-state diagnostics.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()




# ------------------------------------------------------------------
# V11.5 DISCOVERY + REACCELERATION WATCH
# ------------------------------------------------------------------
st.markdown("### V11.8.2 Discovery, Holders & Reacceleration")

reaccel_state = read_json_safe(REACCEL_WATCH_FILE) or {}
reaccel_tokens = (reaccel_state.get("tokens") or {}) if isinstance(reaccel_state, dict) else {}
reaccel_log = read_csv_safe(REACCEL_LOG_FILE)
discovery_log = read_csv_safe(DISCOVERY_SOURCE_LOG_FILE)
x_usage_log = read_csv_safe(X_API_USAGE_FILE)

watching = 0
ready = 0
now_local = datetime.now()

for token, item in reaccel_tokens.items():
    try:
        first_watch = datetime.fromisoformat(str(item.get("first_watch_at") or ""))
        age_min = max(0.0, (now_local - first_watch).total_seconds() / 60.0)
        if age_min <= 120:
            if item.get("triggered_at"):
                ready += 1
            else:
                watching += 1
    except Exception:
        continue

today_text = now_local.date().isoformat()
today_discovery = discovery_log.copy()
if not today_discovery.empty and "logged_at" in today_discovery.columns:
    today_discovery = today_discovery[
        today_discovery["logged_at"].astype(str).str.startswith(today_text)
    ]

whale_discoveries = 0
gecko_discoveries = 0
if not today_discovery.empty and "source" in today_discovery.columns:
    whale_discoveries = int((today_discovery["source"].astype(str) == "WHALE").sum())
    gecko_discoveries = int((today_discovery["source"].astype(str) == "GECKO_NEW_POOL").sum())

missed_file = DATA_DIR / f"missed_opportunities_{today_text}.csv"
missed = read_csv_safe(missed_file)
missed_runners = 0
if not missed.empty:
    m30 = pd.to_numeric(missed.get("missed_20_in_30m", 0), errors="coerce").fillna(0)
    m60 = pd.to_numeric(missed.get("missed_50_in_60m", 0), errors="coerce").fillna(0)
    missed_runners = int(((m30 > 0) | (m60 > 0)).sum())

# V11.5.1: exact on-demand Token-X API usage today.
x_requests = 0
x_hits = 0
x_unique_tokens = 0
if not x_usage_log.empty and "date_local" in x_usage_log.columns:
    x_today = x_usage_log[
        x_usage_log["date_local"].astype(str) == today_text
    ].copy()
    if "source" in x_today.columns:
        x_today = x_today[x_today["source"].astype(str) == "TOKEN_X"]
    if "cache_hit" in x_today.columns:
        cache_flag = pd.to_numeric(x_today["cache_hit"], errors="coerce").fillna(0)
        x_today = x_today[cache_flag == 0]
    x_requests = len(x_today)
    if "bonus" in x_today.columns:
        x_hits = int((pd.to_numeric(x_today["bonus"], errors="coerce").fillna(0) > 0).sum())
    if "token_address" in x_today.columns:
        x_unique_tokens = int(
            x_today["token_address"].astype(str).replace("", pd.NA).dropna().nunique()
        )

r1, r2, r3, r4, r5, r6, r7 = st.columns(7)
r1.metric("Reaccel watching", watching)
r2.metric("Reaccel ready", ready)
r3.metric("Whale discoveries", whale_discoveries)
r4.metric("Gecko discoveries", gecko_discoveries)
r5.metric("Missed runners", missed_runners)
r6.metric("Targeted X req", x_requests)
r7.metric("X signal hits", x_hits)
st.caption(
    f"Targeted X has queried {x_unique_tokens} unique token(s) today. "
    "Cached lookups do not count as new X API requests."
)

if not reaccel_log.empty:
    recent_reaccel = reaccel_log.tail(12).copy()
    show_cols = [
        c for c in [
            "logged_at", "event", "symbol", "watch_reason",
            "quant_score", "score_delta", "price_5m", "price_1h", "entry_path"
        ]
        if c in recent_reaccel.columns
    ]
    if show_cols:
        st.dataframe(
            recent_reaccel[show_cols].iloc[::-1],
            hide_index=True,
            use_container_width=True,
            height=210,
        )
else:
    st.caption(
        "No reacceleration events yet. Extended high-quality SURGING tokens will "
        "appear here when they enter WATCHING or later reset to REACCEL_READY."
    )

if not today_discovery.empty:
    with st.expander("Today's external discovery injections", expanded=False):
        show_cols = [
            c for c in ["logged_at", "token_address", "source", "symbol", "detail"]
            if c in today_discovery.columns
        ]
        st.dataframe(
            today_discovery[show_cols].tail(50).iloc[::-1],
            hide_index=True,
            use_container_width=True,
        )

st.divider()


# ------------------------------------------------------------------
# LIVE CONFIRMATION FEEDS
# ------------------------------------------------------------------
st.markdown("### Live Confirmation Feeds")
confirmation_feed = read_csv_safe(CONFIRMATION_FEED_FILE)

if confirmation_feed.empty:
    st.info(
        "No confirmation feed audit rows yet. V11.8.2 will create "
        "data/confirmation_feed_log.csv when SURGING candidates are evaluated."
    )
else:
    if "logged_at" in confirmation_feed.columns:
        confirmation_feed["logged_at"] = pd.to_datetime(
            confirmation_feed["logged_at"],
            errors="coerce",
        )

    for col in ("bonus", "quant_score", "score_delta"):
        if col in confirmation_feed.columns:
            confirmation_feed[col] = pd.to_numeric(
                confirmation_feed[col],
                errors="coerce",
            )

    now_ts = pd.Timestamp.now()
    if getattr(now_ts, "tzinfo", None) is not None:
        now_ts = now_ts.tz_localize(None)

    recent = confirmation_feed.copy()
    if "logged_at" in recent.columns and recent["logged_at"].notna().any():
        # Normalize timezone-aware timestamps to local-naive for comparisons.
        try:
            recent["_local_time"] = recent["logged_at"].apply(
                lambda x: (
                    x.tz_convert(None)
                    if getattr(x, "tzinfo", None) is not None
                    else x
                )
                if pd.notna(x) else pd.NaT
            )
        except Exception:
            recent["_local_time"] = recent["logged_at"]
        last_60_cutoff = now_ts - pd.Timedelta(minutes=60)
        recent60 = recent[
            recent["_local_time"].notna()
            & (recent["_local_time"] >= last_60_cutoff)
        ].copy()
    else:
        recent["_local_time"] = pd.NaT
        recent60 = recent.tail(0).copy()

    positive60 = recent60[pd.to_numeric(recent60.get("bonus", 0), errors="coerce").fillna(0) > 0]
    birdeye_hits = positive60[positive60.get("source", pd.Series(dtype=str)).astype(str) == "BIRDEYE"]
    tokenx_hits = positive60[positive60.get("source", pd.Series(dtype=str)).astype(str) == "TOKEN_X"]
    whale_hits = positive60[positive60.get("source", pd.Series(dtype=str)).astype(str) == "LOCAL_WHALE"]

    f1, f2, f3, f4 = st.columns(4)
    f1.metric("Positive confirmations · 60m", len(positive60))
    f2.metric("Whale hits · 60m", len(whale_hits))
    f3.metric("Birdeye hits · 60m", len(birdeye_hits))
    f4.metric("Token-X hits · 60m", len(tokenx_hits))

    display = recent.sort_values(
        "_local_time",
        ascending=False,
        na_position="last",
    ).head(30).copy()

    if "_local_time" in display.columns:
        display["Time"] = display["_local_time"].dt.strftime("%H:%M:%S")
    else:
        display["Time"] = "—"

    def _feed_bonus(v):
        try:
            return f"{float(v):+.1f}"
        except Exception:
            return "—"

    display["Bonus"] = display.get("bonus", pd.Series(index=display.index)).apply(_feed_bonus)
    display["Token"] = display.get("symbol", pd.Series(index=display.index)).fillna("—").astype(str)
    display["Source"] = display.get("source", pd.Series(index=display.index)).fillna("—").astype(str)
    display["Status"] = display.get("status", pd.Series(index=display.index)).fillna("—").astype(str)
    display["Entry"] = display.get("entry_path", pd.Series(index=display.index)).fillna("—").astype(str)
    display["Detail"] = display.get("summary", pd.Series(index=display.index)).fillna("").astype(str)

    st.dataframe(
        display[["Time", "Token", "Source", "Status", "Bonus", "Entry", "Detail"]],
        hide_index=True,
        use_container_width=True,
        height=310,
        column_config={
            "Time": st.column_config.TextColumn("Time", width="small"),
            "Token": st.column_config.TextColumn("Token", width="small"),
            "Source": st.column_config.TextColumn("Source", width="small"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Bonus": st.column_config.TextColumn("Pts", width="small"),
            "Entry": st.column_config.TextColumn("Quant path", width="small"),
            "Detail": st.column_config.TextColumn("Detail", width="large"),
        },
    )
    st.caption(
        "V11.8.2: raw Token-X score influence is disabled; X evidence is still supplied to Luna. "
        "This table shows Local Whale / Birdeye / targeted Token-X audit evidence."
    )

st.divider()


# ------------------------------------------------------------------
# V11.8.2 LUNA / PROTECTION / EOD STATUS
# ------------------------------------------------------------------
st.markdown("### V11.8.2 Intelligence & Protection")

ai_log = read_csv_safe(AI_CONFIRMATION_LOG_FILE)
eod_state = read_json_safe(CRYPTO_EOD_STATE_FILE) or {}
v118 = current_entry_settings()

today_ai = ai_log.copy()
if not today_ai.empty and "reviewed_at" in today_ai.columns:
    today_ai = today_ai[today_ai["reviewed_at"].astype(str).str.startswith(today_str())]

healthy_count = 0
if not today_ai.empty and "setup_type" in today_ai.columns:
    healthy_count = int(
        (today_ai["setup_type"].astype(str).str.upper() == "HEALTHY_SURGE").sum()
    )

last_ai_setup = "—"
last_ai_conf = "—"
if not ai_log.empty:
    last_ai = ai_log.iloc[-1]
    last_ai_setup = str(last_ai.get("setup_type") or last_ai.get("assessment") or "—")
    try:
        last_ai_conf = f"{float(last_ai.get('confidence', 0)):.0f}%"
    except Exception:
        last_ai_conf = "—"

eod_enabled = env_bool("PUSHOVER_CRYPTO_EOD_ENABLED", True)
eod_group = bool(str(os.getenv("PUSHOVER_CRYPTO_EOD_GROUP_KEY") or "").strip())
eod_app = bool(str(os.getenv("PUSHOVER_CRYPTO_EOD_TOKEN") or "").strip())
eod_sent_today = str(eod_state.get("last_sent_date") or "") == today_str()
eod_hour = env_int("PUSHOVER_CRYPTO_EOD_HOUR", 23)
eod_minute = env_int("PUSHOVER_CRYPTO_EOD_MINUTE", 0)

i1, i2, i3, i4 = st.columns(4)
i1.metric("HEALTHY_SURGE today", healthy_count)
i2.metric("Latest Luna setup", last_ai_setup, help=f"Confidence: {last_ai_conf}")
i3.metric(
    "EOD Pushover",
    "SENT" if eod_sent_today else ("READY" if eod_enabled and (eod_group or os.getenv("PUSHOVER_USER_KEY")) else "NOT CONFIGURED")
)
i4.metric(
    "EOD route",
    "GROUP / EOD APP" if eod_group and eod_app else (
        "GROUP / STANDARD APP" if eod_group else "PERSONAL FALLBACK"
    )
)

st.caption(
    f"EOD schedule {eod_hour:02d}:{eod_minute:02d} {os.getenv('CRYPTO_EOD_TIMEZONE','America/Los_Angeles')} | "
    f"NORMAL RT ≥ {v118['NORMAL_MIN_ROUNDTRIP_RETURN_PCT']:.1f}% | "
    f"EARLY RT ≥ {v118['EARLY_MIN_ROUNDTRIP_RETURN_PCT']:.1f}% | "
    f"pre-runner protection {v118['PRE_RUNNER_PROTECT_ACTIVATE_PCT']:.0f}% peak → "
    f"{v118['PRE_RUNNER_PROFIT_FLOOR_PCT']:.0f}% floor"
)

if position:
    peak_now = float(position.get("peak_pnl_pct", 0) or 0)
    runner_now = bool(position.get("runner_mode"))
    pre_runner_active = (
        (not runner_now)
        and peak_now >= v118["PRE_RUNNER_PROTECT_ACTIVATE_PCT"]
    )
    protection = (
        "RUNNER"
        if runner_now
        else ("PRE-RUNNER FLOOR ACTIVE" if pre_runner_active else "BUILDING")
    )
    st.caption(
        f"Open-position protection: {protection} | peak {peak_now:+.2f}% | "
        f"base max hold {v118['MAX_HOLD_MINUTES']:.0f}m | "
        f"healthy extension up to {v118['EXTENDED_HOLD_MAX_MINUTES']:.0f}m"
    )

if not ai_log.empty:
    ai_display = ai_log.tail(12).iloc[::-1].copy()
    ai_cols = [
        c for c in [
            "reviewed_at", "symbol", "entry_path", "assessment", "confidence",
            "setup_type", "continuation_band", "ai_bonus", "risk_level", "summary"
        ]
        if c in ai_display.columns
    ]
    with st.expander("Recent Luna momentum reviews", expanded=False):
        st.dataframe(
            ai_display[ai_cols],
            hide_index=True,
            use_container_width=True,
            height=260,
        )

st.divider()


# ------------------------------------------------------------------
# SYSTEM STATUS: dependent processes + today's realized performance
# ------------------------------------------------------------------
processes = _status_processes
# Match any current/future trader script. Reuse the process state already
# resolved for the Live Scanner status so both sections agree.
trader_proc = _status_trader_proc
social_proc = process_match(processes, [
    r"social_sentiment_monitor.*\.py",
])
smart_proc = process_match(processes, [
    r"smart_money_monitor.*(?:\.py)?",
])

completed, realized, deployed, day_return_pct, wins, losses = daily_trade_metrics(trades)

st.markdown("### System Status")
d1,d2,d3,d4 = st.columns(4)

def dep_card(col, name, proc=None, fixed_state=None, detail=""):
    if fixed_state:
        state, css = fixed_state, "info"
    elif proc:
        state, css = "RUNNING", "run"
        detail = detail or f"PID {proc.get('pid', '—')}"
    else:
        state, css = "STOPPED", "stop"
    col.markdown(
        f'<div class="dep-card"><div class="dep-name">{name}</div>'
        f'<div class="dep-state {css}">● {state}</div>'
        f'<div class="dep-detail">{detail or "—"}</div></div>',
        unsafe_allow_html=True,
    )

def proc_detail(proc):
    if not proc:
        return ""
    cmd = str(proc.get("cmd", "") or "")
    m = re.search(r"([A-Za-z0-9_\-.]+\.py)", cmd, re.IGNORECASE)
    script = m.group(1) if m else str(proc.get("name", "") or "")
    return f"{script} | PID {proc.get('pid', '—')}"

dep_card(d1, "Trader", trader_proc, detail=proc_detail(trader_proc))

if not trader_proc:
    dep_card(
        d2,
        "Market Scanner",
        fixed_state="STOPPED",
        detail="embedded scanner unavailable because trader is stopped",
    )
elif position:
    dep_card(
        d2,
        "Market Scanner",
        fixed_state="PAUSED — POSITION",
        detail=f"monitoring {position.get('symbol', 'open token')}",
    )
elif pause_reason:
    dep_card(
        d2,
        "Market Scanner",
        fixed_state="PAUSED — RISK",
        detail=pause_reason,
    )
elif scanner_age is not None and scanner_age <= 150:
    dep_card(
        d2,
        "Market Scanner",
        fixed_state="LIVE",
        detail=f"latest snapshot {scanner_age / 60.0:.1f}m ago",
    )
elif scanner_age is not None:
    dep_card(
        d2,
        "Market Scanner",
        fixed_state="STALE",
        detail=f"latest snapshot {scanner_age / 60.0:.1f}m ago",
    )
else:
    dep_card(
        d2,
        "Market Scanner",
        fixed_state="WAITING",
        detail="no snapshot yet",
    )
dep_card(
    d3,
    "Targeted Token-X",
    fixed_state="ON-DEMAND",
    detail="queried only for top quant candidates; 13-influencer polling OFF",
)
dep_card(d4, "Smart Money / Whale", smart_proc, detail=proc_detail(smart_proc))

if social_proc:
    st.warning(
        "The old 13-influencer social_sentiment_monitor process is still running. "
        "Stop that process to eliminate its continuous X API polling."
    )

p1,p2,p3,p4 = st.columns(4)
p1.metric("Today's Trade Return", f"{day_return_pct:+.2f}%")
p2.metric("Today's Realized P&L", f"${realized:+.4f}")
p3.metric("Completed Trades", str(completed))
p4.metric("Win / Loss", f"{wins} / {losses}")
st.caption(
    f"Today's Trade Return = realized P/L ÷ ${deployed:.2f} deployed across completed trades. "
    "This is trade performance, not whole-wallet return."
)

activity_rows = dependency_activity_rows(snap_path, snaps, trade_path, trades)
with st.expander("Dependency / call activity log", expanded=True):
    if activity_rows:
        st.dataframe(pd.DataFrame(activity_rows), hide_index=True, use_container_width=True, height=180)
    else:
        st.info("No dependency activity detected yet.")
    st.caption(
        "Shows observed outputs from the trader, scanner and smart-money monitor. "
        "Targeted Token-X request-level usage is captured separately in x_api_usage_log.csv."
    )

# Trade stats are computed in the top status strip.

# Metrics
m1,m2,m3,m4 = st.columns(4)
m1.metric("Watched", f"{watch_count}")
m2.metric("SURGING", f"{len(surging)}")
m3.metric("Best", str(best.get("symbol","—")) if best is not None else "—")
m4.metric("Score", num(best.get("momentum_score"),0) if best is not None else "—")

m5,m6,m7,m8 = st.columns(4)
m5.metric("Δ Score", num(best.get("score_delta"),0,prefix="+") if best is not None and float(best.get("score_delta",0) or 0)>=0 else num(best.get("score_delta"),0) if best is not None else "—")
m6.metric("5m", pct(best.get("price_5m")) if best is not None else "—")
m7.metric("Vol Accel", num(best.get("volume_acceleration"),2,suffix="x") if best is not None else "—")
m8.metric("P&L", num(realized,2,prefix="$"))

# Current position
st.subheader("Current Position")
if position:
    p1,p2,p3,p4 = st.columns(4)
    p1.metric("Token", str(position.get("symbol","—")))
    p2.metric("Entry", num(position.get("entry_usdc"),2,prefix="$"))
    p3.metric("Score", num(position.get("entry_score", position.get("score")),1))
    p4.metric("Peak P&L", pct(position.get("peak_pnl_pct")))

    h1,h2,h3,h4 = st.columns(4)
    h1.metric("Market Cap", num(position.get("current_market_cap"),0,prefix="$"))
    h2.metric("Holders", f"{int(float(position.get('current_holder_count',0) or 0)):,}" if float(position.get("current_holder_count",0) or 0) > 0 else "—")
    h3.metric("Holder Δ 10m", pct(position.get("holder_change_10m_pct")) if position.get("holder_change_10m_pct") not in (None, "") else "—")
    h4.metric("MC / Holder", num(position.get("current_market_cap_per_holder"),0,prefix="$") if float(position.get("current_market_cap_per_holder",0) or 0) > 0 else "—")

    peak_now = float(position.get("peak_pnl_pct", 0) or 0)
    runner_now = bool(position.get("runner_mode"))
    protect_at = env_float("PRE_RUNNER_PROTECT_ACTIVATE_PCT", 6.0)
    floor_at = env_float("PRE_RUNNER_PROFIT_FLOOR_PCT", 2.0)
    if runner_now:
        protect_text = "RUNNER protection active"
    elif peak_now >= protect_at:
        protect_text = f"PRE-RUNNER floor active at +{floor_at:.1f}%"
    else:
        protect_text = f"pre-runner protection activates at +{protect_at:.1f}% peak"

    st.caption(
        "Scanner discovery is intentionally paused while the trader monitors "
        f"this open position. V11.8.2 protection: {protect_text}."
    )
else:
    st.info("No open position.")

# V11.5.2: join the most recent Helius holder/adoption metrics onto the
# scanner leaderboard without changing the underlying snapshot CSV.
if not latest.empty and holder_metrics_tokens and "token_address" in latest.columns:
    latest = latest.copy()

    def _holder_metric_for(addr, key):
        row = holder_metrics_tokens.get(str(addr), {}) or {}
        return row.get(key, "")

    for key in [
        "holder_count",
        "holder_count_capped",
        "holder_change_10m",
        "holder_change_10m_pct",
        "holder_change_30m",
        "holder_change_30m_pct",
        "market_cap_per_holder",
        "observed_at",
    ]:
        latest[key] = latest["token_address"].map(
            lambda addr, k=key: _holder_metric_for(addr, k)
        )

# Candidate table
st.subheader("Momentum Leaderboard")
cols = [
    "symbol","momentum_state","momentum_score","score_delta","price_5m","price_1h",
    "volume_5m","volume_acceleration","buy_sell_ratio_5m","liquidity","market_cap",
    "holder_count","holder_change_10m_pct","holder_change_30m_pct","market_cap_per_holder"
]
show_cols = [c for c in cols if c in latest.columns]
st.dataframe(latest[show_cols].head(18), hide_index=True, use_container_width=True, height=320)

# Holder/adoption panel — only tokens queried by the cost-controlled Helius layer.
st.subheader("Holder & Market-Cap Metrics")
holder_rows = []
for token_address, item in holder_metrics_tokens.items():
    if not isinstance(item, dict):
        continue
    holder_rows.append({
        "Token": item.get("symbol") or token_address[:8],
        "Market Cap": float(item.get("market_cap", 0) or 0),
        "Holders": int(float(item.get("holder_count", 0) or 0)),
        "Holder Δ 10m": item.get("holder_change_10m", ""),
        "Holder Δ 10m %": item.get("holder_change_10m_pct", ""),
        "Holder Δ 30m": item.get("holder_change_30m", ""),
        "Holder Δ 30m %": item.get("holder_change_30m_pct", ""),
        "MC / Holder": float(item.get("market_cap_per_holder", 0) or 0),
        "Observed": item.get("observed_at", ""),
    })

if holder_rows:
    holder_df = pd.DataFrame(holder_rows)
    holder_df = holder_df.sort_values("Market Cap", ascending=False)
    st.dataframe(
        holder_df.head(25),
        hide_index=True,
        use_container_width=True,
        height=260,
        column_config={
            "Market Cap": st.column_config.NumberColumn(format="$%.0f"),
            "Holders": st.column_config.NumberColumn(format="%d"),
            "Holder Δ 10m %": st.column_config.NumberColumn(format="%+.1f%%"),
            "Holder Δ 30m %": st.column_config.NumberColumn(format="%+.1f%%"),
            "MC / Holder": st.column_config.NumberColumn(format="$%.0f"),
        },
    )
    st.caption(
        "Holder counts are Helius unique positive-balance owners. Counts are cached "
        "for 10 minutes by default; market cap can update more frequently."
    )
else:
    st.caption(
        "No holder metrics yet. V11.5.2 populates this after it encounters a "
        "SURGING or REACCEL candidate."
    )

# Charts
c1,c2 = st.columns(2)
with c1:
    st.subheader("Momentum Score — Top Tokens")
    chart_df = latest.head(20).copy()
    if not chart_df.empty and "symbol" in chart_df and "momentum_score" in chart_df:
        chart = alt.Chart(chart_df).mark_bar().encode(
            x=alt.X("momentum_score:Q", title="Momentum Score"),
            y=alt.Y("symbol:N", sort="-x", title=None),
            tooltip=["symbol:N","momentum_state:N","momentum_score:Q","score_delta:Q","price_5m:Q","volume_acceleration:Q"]
        ).properties(height=230)
        st.altair_chart(chart, use_container_width=True)

with c2:
    st.subheader("Score vs 5-Minute Move")
    if "momentum_score" in latest and "price_5m" in latest:
        scatter = alt.Chart(latest.head(60)).mark_circle(size=90).encode(
            x=alt.X("momentum_score:Q", title="Momentum Score"),
            y=alt.Y("price_5m:Q", title="5m Price %"),
            tooltip=["symbol:N","momentum_state:N","momentum_score:Q","score_delta:Q","price_5m:Q","liquidity:Q"]
        ).properties(height=230)
        st.altair_chart(scatter, use_container_width=True)

# Trade history
st.divider()
st.subheader("Recent Trades")
if trades.empty:
    st.info("No trade CSV rows found.")
else:
    preferred = ["timestamp","action","symbol","reason","entry_path","input_usd","output_usd","realized_pnl_usd","roundtrip_preflight_pct","ai_assessment","ai_confidence","ai_bonus","confidence_tier","peak_pnl_pct","runner_mode","score","score_delta","state","router","signature"]
    st.dataframe(trades[[c for c in preferred if c in trades.columns]].tail(12).iloc[::-1], hide_index=True, use_container_width=True, height=260)

# Smart money monitor — optional, auto-detected.
st.divider()
st.subheader("Smart Money Monitor")
events_path = (
    SMART_DIR / "smart_money_events_v22.csv"
    if (SMART_DIR / "smart_money_events_v22.csv").exists()
    else SMART_DIR / "smart_money_events_v21.csv"
)
perf_path = (
    SMART_DIR / "trader_performance_v22.csv"
    if (SMART_DIR / "trader_performance_v22.csv").exists()
    else SMART_DIR / "trader_performance_v21.csv"
)
campaigns_path = (
    SMART_DIR / "smart_money_campaigns_v22.csv"
    if (SMART_DIR / "smart_money_campaigns_v22.csv").exists()
    else SMART_DIR / "smart_money_campaigns_v21.csv"
)

events = read_csv_safe(events_path)
perf = read_csv_safe(perf_path)
campaigns = read_csv_safe(campaigns_path)

if events.empty and campaigns.empty:
    st.info("Smart Money Monitor v2.1 data not found yet. This section will populate automatically if its data folder is under CryptoTracker/SmartMoneyMonitor/data.")
else:
    a,b,c = st.columns(3)
    a.metric("Smart-Money Events", str(len(events)))
    b.metric("Campaign Rows", str(len(campaigns)))
    bcount = events["trader"].nunique() if (not events.empty and "trader" in events.columns) else "—"
    c.metric("Tracked Traders Seen", str(bcount))

    if not events.empty:
        preferred = ["detected_at_utc","trader_name","chain","token_symbol","estimated_spend_usd",
                     "campaign_strength_score","campaign_strength_label","converging_trader_count",
                     "campaign_pattern","confidence","price_change_5m_pct","price_change_1h_pct",
                     "buy_sell_ratio_5m","liquidity_usd"]
        st.dataframe(events[[x for x in preferred if x in events.columns]].tail(12).iloc[::-1], hide_index=True, use_container_width=True, height=260)


# Smart Money v2.2 campaign-strength research
if campaigns_path.exists() and not campaigns.empty and "campaign_strength_score" in campaigns.columns:
    st.divider()
    st.subheader("Smart Money v2.2 — Campaign Strength")

    camp = campaigns.copy()
    for c in ["campaign_strength_score", "meaningful_spend_usd", "buy_count",
              "meaningful_buy_count", "converging_trader_count",
              "latest_vs_previous_meaningful_ratio"]:
        if c in camp.columns:
            camp[c] = pd.to_numeric(camp[c], errors="coerce")

    # Keep newest snapshot for each campaign.
    if "updated_at_utc" in camp.columns:
        camp["_dt"] = pd.to_datetime(camp["updated_at_utc"], errors="coerce", utc=True)
        camp = camp.sort_values("_dt")
    if "campaign_id" in camp.columns:
        camp = camp.groupby("campaign_id", as_index=False).tail(1)

    camp = camp.sort_values("campaign_strength_score", ascending=False, na_position="last")
    cols = [
        c for c in [
            "trader_name", "token_symbol", "campaign_strength_score",
            "campaign_strength_label", "buy_count", "meaningful_buy_count",
            "meaningful_spend_usd", "latest_vs_previous_meaningful_ratio",
            "rapid_accumulation", "buying_pullback",
            "converging_trader_count", "converging_traders",
            "campaign_pattern", "last_signal_utc"
        ] if c in camp.columns
    ]
    st.dataframe(camp[cols].head(20), hide_index=True, use_container_width=True, height=300)

scorecard = read_csv_safe(WALLET_SCORECARD_V22)
if not scorecard.empty:
    st.subheader("Wallet Forward Performance")
    sc = scorecard.copy()
    preferred_h = 30
    if "horizon_minutes" in sc.columns:
        sc["horizon_minutes"] = pd.to_numeric(sc["horizon_minutes"], errors="coerce")
        sc30 = sc[sc["horizon_minutes"] == preferred_h]
        if not sc30.empty:
            sc = sc30

    score_cols = [
        c for c in [
            "trader_name", "horizon_minutes", "sample_count",
            "median_return_pct", "positive_rate_pct",
            "return_10plus_rate_pct", "median_strength_score"
        ] if c in sc.columns
    ]
    st.dataframe(sc[score_cols], hide_index=True, use_container_width=True, height=220)

st.caption("Read-only V11.8.2 dashboard. CryptoTracker and Smart Money Monitor remain independent background processes.")
time.sleep(refresh)
st.rerun()