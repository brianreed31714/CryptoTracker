#!/usr/bin/env python3
"""CryptoTracker V11.10 paper-research laboratory.

Runs independent virtual portfolios against the same candidate stream used by
the live trader.  It never signs or submits a transaction.  Every candidate,
model decision, simulated fill, exit, and daily model summary is written under
``data/paper_research`` for later walk-forward evaluation.
"""

from __future__ import annotations

import csv
import json
import math
import os
import re
from difflib import SequenceMatcher
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from statistics import median


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "paper_research"
STATE_FILE = DATA_DIR / "state.json"
OBS_FILE = DATA_DIR / "candidate_observations.csv"
DECISION_FILE = DATA_DIR / "model_decisions.csv"
TRADE_FILE = DATA_DIR / "paper_trades.csv"
SHADOW_TRADE_FILE = DATA_DIR / "shadow_trades.csv"
EQUITY_FILE = DATA_DIR / "model_equity.csv"
SUMMARY_DIR = DATA_DIR / "daily"


def _num(value, default=0.0):
    try:
        return float(value if value not in (None, "") else default)
    except (TypeError, ValueError):
        return float(default)


def _clip(value, lo=0.0, hi=1.0):
    return max(lo, min(hi, value))


def _bool_env(name, default=True):
    raw = str(os.getenv(name, "1" if default else "0")).strip().lower()
    return raw not in {"0", "false", "no", "off"}


def _append_csv(path, row):
    """Append while safely evolving CSV schemas without losing old rows."""
    path.parent.mkdir(parents=True, exist_ok=True)
    new_fields = list(row.keys())
    exists = path.exists() and path.stat().st_size > 0

    if not exists:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=new_fields,
                extrasaction="ignore",
            )
            writer.writeheader()
            writer.writerow(row)
        return

    try:
        with path.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            old_fields = list(reader.fieldnames or [])
            old_rows = list(reader)
    except Exception:
        old_fields = []
        old_rows = []

    combined_fields = list(old_fields)
    for field in new_fields:
        if field not in combined_fields:
            combined_fields.append(field)

    if combined_fields != old_fields:
        temp = path.with_suffix(path.suffix + ".schema.tmp")
        with temp.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=combined_fields,
                extrasaction="ignore",
            )
            writer.writeheader()
            for old_row in old_rows:
                writer.writerow(old_row)
        temp.replace(path)

    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=combined_fields or new_fields,
            extrasaction="ignore",
        )
        writer.writerow(row)


def _load_state(starting_equity):
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {
        "created_at": datetime.now().isoformat(),
        "models": {
            name: {
                "starting_equity": starting_equity,
                "realized_pnl": 0.0,
                "peak_equity": starting_equity,
                "max_drawdown_pct": 0.0,
                "completed": 0,
                "wins": 0,
                "losses": 0,
                "position": None,
            }
            for name in MODEL_SPECS
        },
    }


def _save_state(state):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temp = STATE_FILE.with_suffix(".tmp")
    temp.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    temp.replace(STATE_FILE)


@dataclass(frozen=True)
class ModelSpec:
    threshold: float
    roundtrip_floor: float
    stop_pct: float
    grace_minutes: float
    runner_activate_pct: float
    trail_pct: float
    max_hold_minutes: float
    size_key: str = "NORMAL"
    requires_risk_on: bool = False
    score_kind: str = "balanced"


MODEL_SPECS = {
    "strict_baseline": ModelSpec(99, 97.0, -6, 10, 10, 8, 30, score_kind="strict"),
    "balanced_ev": ModelSpec(58, 98.5, -5, 5, 8, 6, 45),
    "flow_breakout": ModelSpec(62, 99.0, -4, 3, 6, 5, 30, score_kind="flow"),
    "whale_luna": ModelSpec(58, 98.5, -5, 5, 8, 6, 60, score_kind="whale_ai"),
    "early_breakout": ModelSpec(62, 99.0, -4, 3, 6, 5, 30, size_key="EARLY", score_kind="early"),
    "low_friction": ModelSpec(55, 99.5, -5, 5, 8, 6, 45),
    "fast_exit": ModelSpec(58, 98.5, -4, 3, 6, 5, 30),
    "patient_runner": ModelSpec(58, 98.5, -7, 10, 10, 10, 120),
    "regime_filtered": ModelSpec(55, 98.5, -5, 5, 8, 6, 45, requires_risk_on=True),
    "anti_chase": ModelSpec(56, 98.8, -5, 5, 8, 6, 45, score_kind="anti_chase"),
    "extended_probe": ModelSpec(62, 97.0, -6, 5, 10, 10, 60, size_key="PROBE", score_kind="extended"),
    "staged_runner": ModelSpec(58, 98.5, -6, 10, 15, 12, 120, score_kind="balanced"),
    "novelty_probe": ModelSpec(58, 97.0, -6, 5, 10, 10, 60, size_key="PROBE", score_kind="novelty"),
    "runner_hunter": ModelSpec(55, 97.0, -7, 4, 12, 9, 90, size_key="PROBE", score_kind="runner_hunter"),
    "diy_whale": ModelSpec(56, 97.0, -8, 12, 15, 10, 180, size_key="PROBE", score_kind="diy_whale"),
}


_DEFAULT_NOVELTY_TREND_TERMS = (
    "ai,gpt,chatgpt,openai,claude,grok,agent,robot,quantum,"
    "nvidia,tesla,spacex,apple,google,meta,musk,elon,altman,"
    "trump,bezos,zuckerberg"
)
_DEFAULT_NOVELTY_SHOCK_TERMS = (
    "fart,butt,poop,shit,fuck,dick,cock,boob,titty,piss,bitch,balls,cum"
)
_DEFAULT_NOVELTY_MEME_TERMS = (
    "pepe,bonk,doge,shib,inu,cat,dog,frog,baby,moon,pump,wojak,chad,69,420"
)


def _term_list(env_name, default_text):
    raw = str(os.getenv(env_name, default_text) or "")
    return [
        re.sub(r"[^a-z0-9]+", "", item.lower())
        for item in raw.split(",")
        if re.sub(r"[^a-z0-9]+", "", item.lower())
    ]


def _name_novelty(candidate):
    """Deterministic paper-only name novelty / cultural-affinity proxy."""
    name = str(candidate.get("name") or "")
    symbol = str(candidate.get("symbol") or "")
    raw = (name + " " + symbol).strip()
    compact = re.sub(r"[^a-z0-9]+", "", raw.lower())
    words = [
        re.sub(r"[^a-z0-9]+", "", x.lower())
        for x in re.split(r"[^A-Za-z0-9]+", raw)
        if x
    ]

    if not compact or compact in {"unknown", "none"}:
        return {
            "name_novelty_score": 0.0,
            "novelty_shock_score": 0.0,
            "novelty_trend_score": 0.0,
            "novelty_meme_score": 0.0,
            "novelty_style_score": 0.0,
            "novelty_flags": "",
        }

    shock_terms = _term_list(
        "PAPER_NOVELTY_SHOCK_TERMS",
        _DEFAULT_NOVELTY_SHOCK_TERMS,
    )
    trend_terms = _term_list(
        "PAPER_NOVELTY_TREND_TERMS",
        _DEFAULT_NOVELTY_TREND_TERMS,
    )
    meme_terms = _term_list(
        "PAPER_NOVELTY_MEME_TERMS",
        _DEFAULT_NOVELTY_MEME_TERMS,
    )

    def direct_hits(terms):
        return sorted({
            term for term in terms
            if len(term) >= 2 and (
                term in compact
                or any(term == word for word in words)
            )
        })

    shock_hits = direct_hits(shock_terms)
    trend_hits = direct_hits(trend_terms)
    meme_hits = direct_hits(meme_terms)

    fuzzy_term = ""
    fuzzy_ratio = 0.0
    for term in trend_terms:
        if len(term) < 4:
            continue
        ratio = SequenceMatcher(None, compact, term).ratio()
        if ratio > fuzzy_ratio:
            fuzzy_ratio = ratio
            fuzzy_term = term
    if fuzzy_ratio >= 0.72 and fuzzy_term and fuzzy_term not in trend_hits:
        trend_hits.append(fuzzy_term)

    shock_score = min(30.0, 18.0 * len(shock_hits))
    trend_score = min(
        35.0,
        18.0 * len(trend_hits)
        + (8.0 if fuzzy_ratio >= 0.72 else 0.0),
    )
    meme_score = min(20.0, 8.0 * len(meme_hits))

    style_score = 0.0
    if any(ch.isdigit() for ch in raw):
        style_score += 3.0
    if any(ch in raw for ch in ("$", "!", "?", "_", "-")):
        style_score += 3.0
    if 5 <= len(compact) <= 18:
        style_score += 4.0
    semantic_hits = set(shock_hits + trend_hits + meme_hits)
    if len(semantic_hits) >= 2:
        style_score += 5.0
    style_score = min(15.0, style_score)

    score = min(100.0, shock_score + trend_score + meme_score + style_score)
    flags = []
    if shock_hits:
        flags.append("shock:" + ",".join(shock_hits[:3]))
    if trend_hits:
        flags.append("trend:" + ",".join(trend_hits[:3]))
    if meme_hits:
        flags.append("meme:" + ",".join(meme_hits[:3]))
    if fuzzy_ratio >= 0.72 and fuzzy_term:
        flags.append(f"fuzzy:{fuzzy_term}:{fuzzy_ratio:.2f}")

    return {
        "name_novelty_score": round(score, 4),
        "novelty_shock_score": round(shock_score, 4),
        "novelty_trend_score": round(trend_score, 4),
        "novelty_meme_score": round(meme_score, 4),
        "novelty_style_score": round(style_score, 4),
        "novelty_flags": "|".join(flags),
    }



def _regime(candidates):
    usable = [c for c in candidates if _num(c.get("liquidity")) >= 20_000]
    if not usable:
        return {"name": "NO_DATA", "breadth": 0.0, "median_5m": 0.0, "median_score": 0.0}
    breadth = sum(str(c.get("momentum_state")).upper() == "SURGING" for c in usable) / len(usable)
    med_5m = median(_num(c.get("price_5m")) for c in usable)
    med_score = median(_num(c.get("quant_score_raw", c.get("momentum_score"))) for c in usable)
    if breadth >= 0.08 and med_5m > 0 and med_score >= 45:
        name = "RISK_ON"
    elif breadth <= 0.02 or med_5m < -2:
        name = "RISK_OFF"
    else:
        name = "NEUTRAL"
    return {"name": name, "breadth": breadth, "median_5m": med_5m, "median_score": med_score}


def _features(candidate):
    tx5 = _num(candidate.get("buys_5m")) + _num(candidate.get("sells_5m"))
    ai = candidate.get("ai_confirmation_detail") or {}
    ai_positive = str(ai.get("assessment") or "").upper() == "POSITIVE"
    novelty = _name_novelty(candidate)
    return {
        "quant": _num(candidate.get("quant_score_raw", candidate.get("momentum_score"))),
        "delta": _num(candidate.get("score_delta")),
        "liquidity": _num(candidate.get("liquidity")),
        "volume_5m": _num(candidate.get("volume_5m")),
        "volume_accel": _num(candidate.get("volume_acceleration")),
        "buy_sell": _num(candidate.get("buy_sell_ratio_5m")),
        "tx5": tx5,
        "price_5m": _num(candidate.get("price_5m")),
        "price_1h": _num(candidate.get("price_1h")),
        "whale": _num(candidate.get("whale_score_bonus")) + _num(candidate.get("birdeye_smart_bonus")),
        "token_social": _num(candidate.get("token_social_bonus")),
        "ai_confidence": _num(ai.get("confidence")) if ai_positive else 0.0,
        "entry_path": str(candidate.get("research_entry_path") or "NONE"),
        **novelty,
    }


def _safety_pass(candidate):
    f = _features(candidate)
    reasons = []
    if str(candidate.get("momentum_state")).upper() != "SURGING":
        reasons.append("not_surging")
    if f["liquidity"] < 20_000:
        reasons.append("liquidity_lt_20k")
    if f["tx5"] < 8:
        reasons.append("tx5_lt_8")
    if not (0.5 <= f["price_5m"] <= 25):
        reasons.append("price_5m_outside_research_band")
    if not (-20 <= f["price_1h"] <= 100):
        reasons.append("price_1h_outside_research_band")
    if _num(candidate.get("price_usd")) <= 0:
        reasons.append("missing_price")
    return not reasons, reasons


def _model_safety_pass(name, candidate, spec, regime, score):
    """Paper-only eligibility; existing control models retain their old gates."""
    if name == "diy_whale":
        # Early organic discovery only. Never generate orders to manufacture
        # demand or treat our own hypothetical price impact as profit.
        f = _features(candidate)
        reasons = []
        if _num(candidate.get("price_usd")) <= 0:
            reasons.append("missing_price")
        if f["liquidity"] < 50000:
            reasons.append("liquidity_lt_50k")
        if f["volume_5m"] < 3500 or f["tx5"] < 15:
            reasons.append("activity_too_low")
        if f["buy_sell"] < 1.10 or f["volume_accel"] < 1.10:
            reasons.append("organic_flow_unconfirmed")
        if not (-5 <= f["price_5m"] <= 12) or not (-15 <= f["price_1h"] <= 35):
            reasons.append("not_early_accumulation")
        if score < spec.threshold:
            reasons.append("score_below_threshold")
        return not reasons, reasons

    if name == "runner_hunter":
        f = _features(candidate)
        reasons = []
        if str(candidate.get("momentum_state") or "").upper() != "SURGING":
            reasons.append("not_surging")
        if _num(candidate.get("price_usd")) <= 0:
            reasons.append("missing_price")
        if f["liquidity"] < 20000:
            reasons.append("liquidity_lt_20k")
        if f["volume_5m"] < 5000 or f["tx5"] < 12:
            reasons.append("activity_too_low")
        if f["volume_accel"] < 1.15 or f["buy_sell"] < 1.05:
            reasons.append("flow_not_confirmed")
        if f["delta"] <= 0:
            reasons.append("not_accelerating")
        if not (1 <= f["price_5m"] <= 100) or not (-20 <= f["price_1h"] <= 350):
            reasons.append("outside_runner_band")
        if score < spec.threshold:
            reasons.append("score_below_threshold")
        return not reasons, reasons

    if name not in {"extended_probe", "novelty_probe"}:
        safe, reasons = _safety_pass(candidate)
        if spec.requires_risk_on and regime["name"] != "RISK_ON":
            safe = False
            reasons.append("regime_not_risk_on")
        if score < spec.threshold:
            safe = False
            reasons.append("score_below_threshold")
        return safe, reasons

    f = _features(candidate)
    reasons = []
    if str(candidate.get("momentum_state") or "").upper() != "SURGING":
        reasons.append("not_surging")
    if _num(candidate.get("price_usd")) <= 0:
        reasons.append("missing_price")

    if name == "extended_probe":
        extended = (
            f["price_5m"] > _num(os.getenv("PAPER_EXTENDED_LIVE_5M_PCT", "15"), 15)
            or f["price_1h"] > _num(os.getenv("PAPER_EXTENDED_LIVE_1H_PCT", "40"), 40)
        )
        if not extended:
            reasons.append("not_extended")
        if f["liquidity"] < _num(os.getenv("PAPER_EXTENDED_MIN_LIQUIDITY", "40000"), 40000):
            reasons.append("liquidity")
        if f["tx5"] < _num(os.getenv("PAPER_EXTENDED_MIN_TX5", "15"), 15):
            reasons.append("tx5")
        if f["quant"] < _num(os.getenv("PAPER_EXTENDED_MIN_QUANT", "70"), 70):
            reasons.append("quant")
        if f["delta"] <= 0:
            reasons.append("delta_not_positive")
        if f["volume_accel"] < _num(os.getenv("PAPER_EXTENDED_MIN_VOLUME_ACCEL", "1.25"), 1.25):
            reasons.append("volume_accel")
        if f["buy_sell"] < _num(os.getenv("PAPER_EXTENDED_MIN_BUY_SELL", "1.10"), 1.10):
            reasons.append("buy_sell")
        if not (0.5 <= f["price_5m"] <= _num(os.getenv("PAPER_EXTENDED_MAX_5M_PCT", "60"), 60)):
            reasons.append("5m_too_extreme")
        if not (-20 <= f["price_1h"] <= _num(os.getenv("PAPER_EXTENDED_MAX_1H_PCT", "250"), 250)):
            reasons.append("1h_too_extreme")

    elif name == "novelty_probe":
        if f["name_novelty_score"] < _num(os.getenv("PAPER_NOVELTY_MIN_SCORE", "45"), 45):
            reasons.append("novelty_below_floor")
        if f["liquidity"] < _num(os.getenv("PAPER_NOVELTY_MIN_LIQUIDITY", "20000"), 20000):
            reasons.append("liquidity")
        if f["tx5"] < _num(os.getenv("PAPER_NOVELTY_MIN_TX5", "8"), 8):
            reasons.append("tx5")
        if f["quant"] < _num(os.getenv("PAPER_NOVELTY_MIN_QUANT", "55"), 55):
            reasons.append("quant")
        if f["delta"] < -5:
            reasons.append("delta")
        if f["volume_accel"] < 1.0:
            reasons.append("volume_accel")
        if f["buy_sell"] < 1.0:
            reasons.append("buy_sell")
        if not (0.0 <= f["price_5m"] <= 60):
            reasons.append("5m_extreme")
        if not (-30 <= f["price_1h"] <= 250):
            reasons.append("1h_extreme")

    if score < spec.threshold:
        reasons.append("score_below_threshold")
    return not reasons, reasons



def _model_score(candidate, spec, regime):
    f = _features(candidate)
    if spec.score_kind == "strict":
        return 100.0 if f["entry_path"] in {"NORMAL", "EARLY_ACCEL"} else 0.0

    negative_penalty = 0.0
    if f["delta"] < 0:
        negative_penalty += min(18.0, abs(f["delta"]) * 0.30)
    if f["volume_accel"] < 1.0:
        negative_penalty += min(12.0, (1.0 - f["volume_accel"]) * 12.0)
    if f["buy_sell"] < 1.0:
        negative_penalty += min(12.0, (1.0 - f["buy_sell"]) * 18.0)
    if f["price_5m"] > 12.0:
        negative_penalty += min(15.0, (f["price_5m"] - 12.0) * 0.9)
    if f["price_1h"] > 45.0:
        negative_penalty += min(15.0, (f["price_1h"] - 45.0) * 0.25)

    balanced = 100 * (
        0.30 * _clip(f["quant"] / 120)
        + 0.20 * _clip(f["delta"] / 60)
        + 0.15 * _clip((f["volume_accel"] - 1) / 3)
        + 0.15 * _clip((f["buy_sell"] - 1) / 1.5)
        + 0.10 * _clip(f["tx5"] / 80)
        + 0.05 * _clip(math.log10(max(f["volume_5m"], 1)) / 5)
        + 0.05 * _clip(1 - abs(f["price_5m"] - 6) / 20)
    ) - negative_penalty

    if spec.score_kind == "flow":
        score = 100 * (
            0.30 * _clip((f["volume_accel"] - 1) / 3)
            + 0.25 * _clip((f["buy_sell"] - 1) / 1.5)
            + 0.20 * _clip(f["delta"] / 60)
            + 0.15 * _clip(f["tx5"] / 80)
            + 0.10 * _clip(1 - abs(f["price_5m"] - 5) / 18)
        )
        return _clip(score - negative_penalty, 0, 100)
    if spec.score_kind == "whale_ai":
        score = 0.60 * balanced + 40 * (
            0.45 * _clip(f["whale"] / 25)
            + 0.35 * _clip(f["ai_confidence"] / 100)
            + 0.20 * _clip(f["token_social"] / 10)
        )
        return _clip(score, 0, 100)
    if spec.score_kind == "early":
        score = 100 * (
            0.30 * _clip(f["delta"] / 70)
            + 0.25 * _clip((f["volume_accel"] - 1) / 4)
            + 0.20 * _clip((f["buy_sell"] - 1) / 2)
            + 0.15 * _clip(f["tx5"] / 60)
            + 0.10 * _clip(1 - abs(f["price_5m"] - 4) / 15)
        )
        return _clip(score - negative_penalty, 0, 100)
    if spec.score_kind == "diy_whale":
        # Focus on early organic flow, not artificially moving the price.
        score = 100 * (
            0.25 * _clip((f["volume_accel"] - 1) / 2.5)
            + 0.23 * _clip((f["buy_sell"] - 1) / 1.5)
            + 0.18 * _clip(f["tx5"] / 75)
            + 0.16 * _clip(f["quant"] / 110)
            + 0.10 * _clip(max(f["delta"], 0) / 50)
            + 0.08 * _clip(1 - abs(f["price_5m"] - 3) / 15)
        )
        return _clip(score, 0, 100)
    if spec.score_kind == "runner_hunter":
        # Intentionally no generic price-extension penalty: test momentum
        # continuation separately from balanced_ev, with explicit safety gates.
        score = 100 * (
            0.22 * _clip(f["delta"] / 70)
            + 0.25 * _clip((f["volume_accel"] - 1) / 4)
            + 0.20 * _clip((f["buy_sell"] - 1) / 2)
            + 0.15 * _clip(f["tx5"] / 80)
            + 0.10 * _clip(f["price_5m"] / 40)
            + 0.08 * _clip(f["quant"] / 120)
        )
        return _clip(score, 0, 100)
    if spec.score_kind == "extended":
        extension_strength = max(
            _clip((f["price_5m"] - 15.0) / 45.0),
            _clip((f["price_1h"] - 40.0) / 210.0),
        )
        score = 100 * (
            0.24 * _clip(f["quant"] / 140)
            + 0.18 * _clip(f["delta"] / 100)
            + 0.18 * _clip((f["volume_accel"] - 1) / 4)
            + 0.18 * _clip((f["buy_sell"] - 1) / 2)
            + 0.10 * _clip(f["tx5"] / 100)
            + 0.12 * extension_strength
        )
        return _clip(score, 0, 100)
    if spec.score_kind == "novelty":
        score = (
            0.45 * f["name_novelty_score"]
            + 20.0 * _clip(f["quant"] / 120)
            + 12.5 * _clip(max(f["delta"], 0) / 60)
            + 12.5 * _clip(max(f["volume_accel"] - 1, 0) / 3)
            + 10.0 * _clip(max(f["buy_sell"] - 1, 0) / 1.5)
        )
        return _clip(score, 0, 100)
    if spec.score_kind == "anti_chase":
        extension_penalty = 0.0
        if f["price_5m"] > 9:
            extension_penalty += (f["price_5m"] - 9) * 2.0
        if f["price_1h"] > 35:
            extension_penalty += (f["price_1h"] - 35) * 0.35
        if f["price_5m"] < 1:
            extension_penalty += (1 - f["price_5m"]) * 5.0
        return _clip(balanced + 6.0 - extension_penalty, 0, 100)
    if regime["name"] == "RISK_ON":
        balanced += 7
    elif regime["name"] == "RISK_OFF":
        balanced -= 12
    return _clip(balanced, 0, 100)

def _candidate_row(candidate, regime, scores, data_quality=None):
    f = _features(candidate)
    now = datetime.now()
    data_quality = data_quality or {}
    row = {
        "timestamp": now.isoformat(),
        "date": now.date().isoformat(),
        "symbol": candidate.get("symbol", ""),
        "name": candidate.get("name", ""),
        "token_address": candidate.get("token_address", ""),
        "state": candidate.get("momentum_state", ""),
        "discovery_source": candidate.get("discovery_source", ""),
        "price_usd": _num(candidate.get("price_usd")),
        "market_cap": _num(candidate.get("market_cap")),
        **f,
        "regime": regime["name"],
        "market_breadth": regime["breadth"],
        "helius_status": data_quality.get("helius_status", "UNKNOWN"),
        "data_quality_flags": data_quality.get("flags", ""),
    }
    for name in MODEL_SPECS:
        row[f"score_{name}"] = round(scores[name], 6)
    return row


def _current_price(position, candidates_by_token, price_lookup):
    token = position.get("token_address")
    candidate = candidates_by_token.get(token)
    if candidate:
        return _num(candidate.get("price_usd")), candidate
    try:
        snap = price_lookup(token) if price_lookup else {}
        return _num((snap or {}).get("price_usd")), None
    except Exception:
        return 0.0, None


def _close_position(
    name,
    model,
    position,
    exit_price,
    reason,
    now,
    exit_value_usdc=None,
    exit_quote_status="MARK_FALLBACK",
):
    entry_price = _num(position.get("entry_price"))
    raw_return = ((exit_price - entry_price) / entry_price * 100) if entry_price > 0 else 0.0
    size = _num(position.get("size_usdc"))

    if exit_value_usdc is not None and size > 0:
        net_return = ((_num(exit_value_usdc) - size) / size) * 100.0
        cost_pct = raw_return - net_return
    else:
        cost_pct = max(0.0, 100.0 - _num(position.get("roundtrip_pct"), 100.0))
        net_return = raw_return - cost_pct

    pnl = size * net_return / 100.0
    model["realized_pnl"] = _num(model.get("realized_pnl")) + pnl
    model["completed"] = int(model.get("completed", 0)) + 1
    if pnl > 0:
        model["wins"] = int(model.get("wins", 0)) + 1
    elif pnl < 0:
        model["losses"] = int(model.get("losses", 0)) + 1
    equity = _num(model.get("starting_equity")) + _num(model.get("realized_pnl"))
    model["peak_equity"] = max(_num(model.get("peak_equity"), equity), equity)
    peak = _num(model.get("peak_equity"), equity)
    drawdown = ((peak - equity) / peak * 100) if peak > 0 else 0.0
    model["max_drawdown_pct"] = max(_num(model.get("max_drawdown_pct")), drawdown)
    model["position"] = None
    _append_csv(TRADE_FILE, {
        "timestamp": now.isoformat(), "date": now.date().isoformat(), "model": name,
        "action": "SELL", "symbol": position.get("symbol", ""),
        "name": position.get("name", ""),
        "token_address": position.get("token_address", ""), "reason": reason,
        "name_novelty_score": position.get("name_novelty_score", ""),
        "name_novelty_flags": position.get("name_novelty_flags", ""),
        "entry_time": position.get("entry_time", ""), "entry_price": entry_price,
        "exit_price": exit_price, "size_usdc": size,
        "raw_return_pct": round(raw_return, 8), "estimated_cost_pct": round(cost_pct, 8),
        "net_return_pct": round(net_return, 8), "realized_pnl_usd": round(pnl, 8),
        "peak_return_pct": round(_num(position.get("peak_return_pct")), 8),
        "roundtrip_preflight_pct": position.get("roundtrip_pct", ""),
        "entry_regime": position.get("regime", ""),
        "exit_quote_status": exit_quote_status,
        "exit_value_usdc": round(_num(exit_value_usdc), 8) if exit_value_usdc is not None else "",
        "helius_status": position.get("helius_status", "UNKNOWN"),
        "data_quality_flags": position.get("data_quality_flags", ""),
        "equity_after": round(equity, 8),
    })


def _record_staged_partial(model, position, exit_price, now, stage_key, fraction):
    """Record a virtual scale-out without ending the paper trade."""
    if position.get(stage_key):
        return
    entry_price = _num(position.get("entry_price"))
    if entry_price <= 0:
        return
    raw_return = ((exit_price - entry_price) / entry_price) * 100.0
    cost_pct = max(0.0, 100.0 - _num(position.get("roundtrip_pct"), 100.0))
    net_return = raw_return - cost_pct
    fraction = max(0.0, min(fraction, _num(position.get("remaining_fraction"), 1.0)))
    tranche_size = _num(position.get("size_usdc")) * fraction
    pnl = tranche_size * net_return / 100.0
    position["staged_realized_pnl"] = _num(position.get("staged_realized_pnl")) + pnl
    position["remaining_fraction"] = max(
        0.0,
        _num(position.get("remaining_fraction"), 1.0) - fraction,
    )
    position[stage_key] = True
    _append_csv(TRADE_FILE, {
        "timestamp": now.isoformat(), "date": now.date().isoformat(),
        "model": "staged_runner", "action": "PARTIAL_SELL",
        "symbol": position.get("symbol", ""), "name": position.get("name", ""),
        "token_address": position.get("token_address", ""),
        "reason": stage_key.upper(), "entry_time": position.get("entry_time", ""),
        "entry_price": entry_price, "exit_price": exit_price,
        "size_usdc": round(tranche_size, 8),
        "raw_return_pct": round(raw_return, 8),
        "estimated_cost_pct": round(cost_pct, 8),
        "net_return_pct": round(net_return, 8),
        "realized_pnl_usd": round(pnl, 8),
        "peak_return_pct": round(_num(position.get("peak_return_pct")), 8),
        "remaining_fraction": round(_num(position.get("remaining_fraction")), 8),
        "roundtrip_preflight_pct": position.get("roundtrip_pct", ""),
        "entry_regime": position.get("regime", ""),
        "name_novelty_score": position.get("name_novelty_score", ""),
        "name_novelty_flags": position.get("name_novelty_flags", ""),
        "exit_quote_status": "STAGED_MARK_CONSERVATIVE_COST",
        "exit_value_usdc": "",
        "helius_status": position.get("helius_status", "UNKNOWN"),
        "data_quality_flags": position.get("data_quality_flags", ""),
        "equity_after": (
            _num(model.get("starting_equity"))
            + _num(model.get("realized_pnl"))
        ),
    })


def _close_staged_position(
    model,
    position,
    exit_price,
    reason,
    now,
    exit_value_usdc=None,
    exit_quote_status="MARK_FALLBACK",
):
    """Close the remaining staged-runner tranche and score the whole trade."""
    entry_price = _num(position.get("entry_price"))
    size = _num(position.get("size_usdc"))
    remaining_fraction = _num(position.get("remaining_fraction"), 1.0)
    remaining_size = size * remaining_fraction
    raw_return = ((exit_price - entry_price) / entry_price * 100) if entry_price > 0 else 0.0

    if exit_value_usdc is not None and remaining_size > 0:
        remaining_net_return = (
            (_num(exit_value_usdc) - remaining_size) / remaining_size * 100.0
        )
        cost_pct = raw_return - remaining_net_return
    else:
        cost_pct = max(0.0, 100.0 - _num(position.get("roundtrip_pct"), 100.0))
        remaining_net_return = raw_return - cost_pct

    remaining_pnl = remaining_size * remaining_net_return / 100.0
    partial_pnl = _num(position.get("staged_realized_pnl"))
    total_pnl = partial_pnl + remaining_pnl
    weighted_return = total_pnl / size * 100.0 if size > 0 else 0.0

    model["realized_pnl"] = _num(model.get("realized_pnl")) + total_pnl
    model["completed"] = int(model.get("completed", 0)) + 1
    if total_pnl > 0:
        model["wins"] = int(model.get("wins", 0)) + 1
    elif total_pnl < 0:
        model["losses"] = int(model.get("losses", 0)) + 1

    equity = _num(model.get("starting_equity")) + _num(model.get("realized_pnl"))
    model["peak_equity"] = max(_num(model.get("peak_equity"), equity), equity)
    peak = _num(model.get("peak_equity"), equity)
    drawdown = ((peak - equity) / peak * 100) if peak > 0 else 0.0
    model["max_drawdown_pct"] = max(_num(model.get("max_drawdown_pct")), drawdown)
    model["position"] = None

    _append_csv(TRADE_FILE, {
        "timestamp": now.isoformat(), "date": now.date().isoformat(),
        "model": "staged_runner", "action": "SELL",
        "symbol": position.get("symbol", ""), "name": position.get("name", ""),
        "token_address": position.get("token_address", ""), "reason": reason,
        "entry_time": position.get("entry_time", ""), "entry_price": entry_price,
        "exit_price": exit_price, "size_usdc": size,
        "raw_return_pct": round(raw_return, 8),
        "estimated_cost_pct": round(cost_pct, 8),
        "net_return_pct": round(weighted_return, 8),
        "realized_pnl_usd": round(total_pnl, 8),
        "staged_partial_pnl_usd": round(partial_pnl, 8),
        "remaining_fraction_closed": round(remaining_fraction, 8),
        "peak_return_pct": round(_num(position.get("peak_return_pct")), 8),
        "roundtrip_preflight_pct": position.get("roundtrip_pct", ""),
        "entry_regime": position.get("regime", ""),
        "name_novelty_score": position.get("name_novelty_score", ""),
        "name_novelty_flags": position.get("name_novelty_flags", ""),
        "exit_quote_status": exit_quote_status,
        "exit_value_usdc": (
            round(_num(exit_value_usdc), 8)
            if exit_value_usdc is not None else ""
        ),
        "helius_status": position.get("helius_status", "UNKNOWN"),
        "data_quality_flags": position.get("data_quality_flags", ""),
        "equity_after": round(equity, 8),
    })


def _manage_staged_position(
    model,
    spec,
    candidates_by_token,
    price_lookup,
    exit_value_lookup,
    now,
):
    position = model.get("position")
    if not position:
        return

    price, candidate = _current_price(position, candidates_by_token, price_lookup)
    if price <= 0:
        return

    entry_price = _num(position.get("entry_price"))
    raw_return = ((price - entry_price) / entry_price * 100) if entry_price > 0 else 0.0
    position["peak_return_pct"] = max(_num(position.get("peak_return_pct")), raw_return)
    position.setdefault("remaining_fraction", 1.0)
    position.setdefault("staged_realized_pnl", 0.0)
    try:
        age = (now - datetime.fromisoformat(position["entry_time"])).total_seconds() / 60.0
    except Exception:
        age = 0.0

    stage1_pct = _num(os.getenv("PAPER_STAGE1_TAKE_PCT", "15"), 15)
    stage2_pct = _num(os.getenv("PAPER_STAGE2_TAKE_PCT", "30"), 30)
    stage1_fraction = _num(os.getenv("PAPER_STAGE1_FRACTION", "0.25"), 0.25)
    stage2_fraction = _num(os.getenv("PAPER_STAGE2_FRACTION", "0.25"), 0.25)

    if raw_return >= stage1_pct:
        _record_staged_partial(
            model, position, price, now, "stage1_done", stage1_fraction
        )
    if raw_return >= stage2_pct:
        _record_staged_partial(
            model, position, price, now, "stage2_done", stage2_fraction
        )

    decay, decay_reasons = _dynamic_decay(candidate)
    if age >= spec.grace_minutes and decay:
        position["decay_confirmations"] = int(position.get("decay_confirmations", 0)) + 1
    else:
        position["decay_confirmations"] = 0

    peak_ret = _num(position.get("peak_return_pct"))
    profit_floor = None
    if peak_ret >= 60:
        profit_floor = max(30.0, peak_ret - 20.0)
    elif peak_ret >= 30:
        profit_floor = max(15.0, peak_ret - 15.0)
    elif peak_ret >= 15:
        profit_floor = max(5.0, peak_ret - 10.0)

    reason = None
    if raw_return <= spec.stop_pct:
        reason = "STOP"
    elif age >= spec.max_hold_minutes:
        reason = "MAX_HOLD"
    elif profit_floor is not None and raw_return <= profit_floor:
        reason = f"STAGED_PROFIT_FLOOR:{profit_floor:.1f}"
    elif (
        not position.get("stage1_done")
        and position["decay_confirmations"] >= int(
            _num(os.getenv("PAPER_EXIT_CONFIRMATIONS", "2"), 2)
        )
    ):
        reason = "MOMENTUM_DECAY:" + ",".join(decay_reasons)
    elif not position.get("stage1_done") and age >= spec.grace_minutes and raw_return <= -2.0:
        reason = "FAILED_MOMENTUM"

    if reason:
        exit_value = None
        quote_status = "MARK_FALLBACK"
        remaining_fraction = _num(position.get("remaining_fraction"), 1.0)
        if exit_value_lookup and _num(position.get("entry_token_raw")) > 0 and remaining_fraction > 0:
            try:
                quote_position = dict(position)
                quote_position["entry_token_raw"] = int(
                    _num(position.get("entry_token_raw")) * remaining_fraction
                )
                exit_value = exit_value_lookup(quote_position)
                if exit_value is not None and _num(exit_value) > 0:
                    quote_status = "EXECUTABLE_JUPITER_REMAINDER"
                else:
                    exit_value = None
                    quote_status = "EXIT_QUOTE_EMPTY"
            except Exception as exc:
                quote_status = "EXIT_QUOTE_ERROR:" + str(exc)[:80]
        _close_staged_position(
            model, position, price, reason, now,
            exit_value_usdc=exit_value,
            exit_quote_status=quote_status,
        )
    else:
        _append_csv(DECISION_FILE, {
            "timestamp": now.isoformat(), "date": now.date().isoformat(),
            "model": "staged_runner", "action": "HOLD",
            "symbol": position.get("symbol", ""),
            "token_address": position.get("token_address", ""),
            "score": "", "threshold": spec.threshold,
            "reason": (
                f"pnl={raw_return:+.3f};peak={peak_ret:+.3f};"
                f"floor={profit_floor if profit_floor is not None else ''};"
                f"remaining={_num(position.get('remaining_fraction'),1.0):.2f}"
            ),
            "regime": "", "roundtrip_pct": position.get("roundtrip_pct", ""),
        })


def _dynamic_decay(candidate):
    if not candidate:
        return False, []
    f = _features(candidate)
    reasons = []
    if str(candidate.get("momentum_state") or "").upper() != "SURGING":
        reasons.append("not_surging")
    if f["quant"] < _num(os.getenv("PAPER_EXIT_SCORE_BELOW", "35"), 35):
        reasons.append("score_decay")
    if f["delta"] <= _num(os.getenv("PAPER_EXIT_DELTA_BELOW", "-20"), -20):
        reasons.append("delta_decay")
    if f["buy_sell"] < _num(os.getenv("PAPER_EXIT_BUY_SELL_BELOW", "0.85"), 0.85):
        reasons.append("sell_pressure")
    if f["volume_accel"] < _num(os.getenv("PAPER_EXIT_VOLUME_ACCEL_BELOW", "0.75"), 0.75):
        reasons.append("volume_decay")
    return bool(reasons), reasons


def _manage_position(
    name,
    model,
    spec,
    candidates_by_token,
    price_lookup,
    exit_value_lookup,
    now,
):
    position = model.get("position")
    if not position:
        return
    price, candidate = _current_price(position, candidates_by_token, price_lookup)
    if price <= 0:
        _append_csv(DECISION_FILE, {
            "timestamp": now.isoformat(), "date": now.date().isoformat(), "model": name,
            "action": "HOLD_NO_PRICE", "symbol": position.get("symbol", ""),
            "token_address": position.get("token_address", ""), "score": "",
            "threshold": spec.threshold, "reason": "price_unavailable", "regime": "",
            "roundtrip_pct": position.get("roundtrip_pct", ""),
        })
        return

    entry_price = _num(position.get("entry_price"))
    raw_return = ((price - entry_price) / entry_price * 100) if entry_price > 0 else 0.0
    position["peak_return_pct"] = max(_num(position.get("peak_return_pct")), raw_return)
    try:
        age = (now - datetime.fromisoformat(position["entry_time"])).total_seconds() / 60.0
    except Exception:
        age = 0.0

    decay, decay_reasons = _dynamic_decay(candidate)
    if age >= spec.grace_minutes and decay:
        position["decay_confirmations"] = int(position.get("decay_confirmations", 0)) + 1
    else:
        position["decay_confirmations"] = 0

    reason = None
    if raw_return <= spec.stop_pct:
        reason = "STOP"
    elif age >= spec.max_hold_minutes:
        reason = "MAX_HOLD"
    elif position["peak_return_pct"] >= spec.runner_activate_pct and (
        position["peak_return_pct"] - raw_return >= spec.trail_pct
    ):
        reason = "RUNNER_TRAIL"
    elif position["decay_confirmations"] >= int(_num(os.getenv("PAPER_EXIT_CONFIRMATIONS", "2"), 2)):
        reason = "MOMENTUM_DECAY:" + ",".join(decay_reasons)
    elif age >= spec.grace_minutes and raw_return <= -2.0:
        reason = "FAILED_MOMENTUM"

    if reason:
        exit_value = None
        quote_status = "MARK_FALLBACK"
        if exit_value_lookup and _num(position.get("entry_token_raw")) > 0:
            try:
                exit_value = exit_value_lookup(position)
                if exit_value is not None and _num(exit_value) > 0:
                    quote_status = "EXECUTABLE_JUPITER"
                else:
                    exit_value = None
                    quote_status = "EXIT_QUOTE_EMPTY"
            except Exception as exc:
                quote_status = "EXIT_QUOTE_ERROR:" + str(exc)[:80]
        _close_position(
            name, model, position, price, reason, now,
            exit_value_usdc=exit_value,
            exit_quote_status=quote_status,
        )
    else:
        _append_csv(DECISION_FILE, {
            "timestamp": now.isoformat(), "date": now.date().isoformat(), "model": name,
            "action": "HOLD", "symbol": position.get("symbol", ""),
            "token_address": position.get("token_address", ""), "score": "",
            "threshold": spec.threshold,
            "reason": f"pnl={raw_return:+.3f};age={age:.1f};decay={position.get('decay_confirmations',0)}",
            "regime": "", "roundtrip_pct": position.get("roundtrip_pct", ""),
        })


def _shadow_exit_reason(position, candidate, spec, price, now):
    entry_price = _num(position.get("entry_price"))
    raw_return = ((price - entry_price) / entry_price * 100) if entry_price > 0 else 0.0
    position["peak_return_pct"] = max(_num(position.get("peak_return_pct")), raw_return)
    try:
        age = (now - datetime.fromisoformat(position["entry_time"])).total_seconds() / 60.0
    except Exception:
        age = 0.0
    decay, _ = _dynamic_decay(candidate)
    if age >= spec.grace_minutes and decay:
        position["decay_confirmations"] = int(position.get("decay_confirmations", 0)) + 1
    else:
        position["decay_confirmations"] = 0
    if raw_return <= spec.stop_pct:
        return "STOP", raw_return
    if age >= spec.max_hold_minutes:
        return "MAX_HOLD", raw_return
    if position["peak_return_pct"] >= spec.runner_activate_pct and (
        position["peak_return_pct"] - raw_return >= spec.trail_pct
    ):
        return "RUNNER_TRAIL", raw_return
    if position["decay_confirmations"] >= int(_num(os.getenv("PAPER_EXIT_CONFIRMATIONS", "2"), 2)):
        return "MOMENTUM_DECAY", raw_return
    if age >= spec.grace_minutes and raw_return <= -2.0:
        return "FAILED_MOMENTUM", raw_return
    return None, raw_return


def _manage_shadow_positions(name, model, spec, candidates_by_token, price_lookup, now):
    positions = list(model.get("shadow_positions") or [])
    kept = []
    for position in positions:
        price, candidate = _current_price(position, candidates_by_token, price_lookup)
        if price <= 0:
            kept.append(position)
            continue
        reason, raw_return = _shadow_exit_reason(position, candidate, spec, price, now)
        if not reason:
            kept.append(position)
            continue
        # Experimental cooldowns observe their OWN earlier shadow losses.
        # This is a raw-price loss proxy, not a net/executed loss.
        if name.startswith("xp_") and raw_return < 0:
            model.setdefault("shadow_last_loss", {})[
                str(position.get("token_address") or "")
            ] = now.isoformat()
        _append_csv(SHADOW_TRADE_FILE, {
            "timestamp": now.isoformat(), "date": now.date().isoformat(), "model": name,
            "action": "SELL", "symbol": position.get("symbol", ""),
            "token_address": position.get("token_address", ""), "reason": reason,
            "entry_time": position.get("entry_time", ""), "entry_price": position.get("entry_price", ""),
            "exit_price": price, "net_return_pct": round(raw_return, 8),
            "peak_return_pct": round(_num(position.get("peak_return_pct")), 8),
            "entry_regime": position.get("regime", ""),
            "name": position.get("name", ""),
            "name_novelty_score": position.get("name_novelty_score") if position.get("name_novelty_score") is not None else "",
            "name_category_flags": position.get("name_category_flags", ""),
            "organic_flow_at_entry": position.get("organic_flow_at_entry", ""),
            "novelty_study_version": position.get("novelty_study_version", ""),
        })
    model["shadow_positions"] = kept


def _add_shadow_positions(
    name, model, spec, ranked, regime, now,
    *, source_name=None, policy_gate=None, max_open_override=None,
    cooldown_override=None,
):
    from research.paper_shadow_experiments import novelty_metadata

    max_open = max(
        1, int(max_open_override) if max_open_override is not None
        else int(_num(os.getenv("PAPER_RESEARCH_SHADOW_POSITIONS_PER_MODEL", "5"), 5))
    )
    cooldown = (
        max(0.0, float(cooldown_override))
        if cooldown_override is not None
        else max(0.0, _num(os.getenv("PAPER_RESEARCH_SHADOW_REENTRY_MINUTES", "60"), 60))
    )
    positions = list(model.get("shadow_positions") or [])
    open_tokens = {str(p.get("token_address") or "") for p in positions}
    last_entries = model.setdefault("shadow_last_entry", {})

    for candidate, scores in ranked:
        if len(positions) >= max_open:
            break
        token = str(candidate.get("token_address") or "")
        if not token or token in open_tokens:
            continue
        source = source_name or name
        safe, _ = _model_safety_pass(
            source, candidate, spec, regime, scores.get(source, 0.0)
        )
        if not safe or (policy_gate is not None and not policy_gate(candidate)):
            continue
        last = str(last_entries.get(token) or "")
        if last:
            try:
                minutes_since = (now - datetime.fromisoformat(last)).total_seconds() / 60.0
                if minutes_since < cooldown:
                    continue
            except Exception:
                pass
        position = {
            "symbol": candidate.get("symbol", ""), "token_address": token,
            "entry_time": now.isoformat(), "entry_price": _num(candidate.get("price_usd")),
            "score": scores.get(source_name or name, 0.0), "peak_return_pct": 0.0,
            "regime": regime["name"], "decay_confirmations": 0,
            **novelty_metadata(candidate),
        }
        positions.append(position)
        open_tokens.add(token)
        last_entries[token] = now.isoformat()
        _append_csv(SHADOW_TRADE_FILE, {
            "timestamp": now.isoformat(), "date": now.date().isoformat(), "model": name,
            "action": "BUY", "symbol": position["symbol"], "token_address": token,
            "reason": "SHADOW_MULTI_CANDIDATE", "entry_time": now.isoformat(),
            "entry_price": position["entry_price"], "exit_price": "",
            "net_return_pct": "", "peak_return_pct": "", "entry_regime": regime["name"],
            "name": position.get("name", ""),
            "name_novelty_score": position.get("name_novelty_score") if position.get("name_novelty_score") is not None else "",
            "name_category_flags": position.get("name_category_flags", ""),
            "organic_flow_at_entry": position.get("organic_flow_at_entry", ""),
            "novelty_study_version": position.get("novelty_study_version", ""),
        })
    model["shadow_positions"] = positions


def run_paper_research(
    candidates,
    settings,
    price_lookup=None,
    integrity_lookup=None,
    exit_value_lookup=None,
    data_quality=None,
):
    """Run one protected research cycle. This function cannot submit a transaction."""
    if not _bool_env("PAPER_RESEARCH_ENABLED", True):
        return {}

    now = datetime.now()
    data_quality = data_quality or {}
    helius_status = str(data_quality.get("helius_status") or "UNKNOWN")
    quality_flags = str(data_quality.get("flags") or "")
    starting_equity = _num(os.getenv("PAPER_STARTING_EQUITY_USDC", "15"), 15)
    state = _load_state(starting_equity)

    for name in MODEL_SPECS:
        state.setdefault("models", {}).setdefault(name, {
            "starting_equity": starting_equity,
            "realized_pnl": 0.0,
            "peak_equity": starting_equity,
            "max_drawdown_pct": 0.0,
            "completed": 0,
            "wins": 0,
            "losses": 0,
            "position": None,
            "shadow_positions": [],
            "shadow_last_entry": {},
        })
        state["models"][name].setdefault("shadow_positions", [])
        state["models"][name].setdefault("shadow_last_entry", {})

    regime = _regime(candidates)
    candidates_by_token = {
        str(c.get("token_address")): c
        for c in candidates
        if c.get("token_address")
    }

    for name, spec in MODEL_SPECS.items():
        model = state["models"][name]
        if name == "staged_runner":
            _manage_staged_position(
                model,
                spec,
                candidates_by_token,
                price_lookup,
                exit_value_lookup,
                now,
            )
        else:
            _manage_position(
                name,
                model,
                spec,
                candidates_by_token,
                price_lookup,
                exit_value_lookup,
                now,
            )
        _manage_shadow_positions(
            name,
            model,
            spec,
            candidates_by_token,
            price_lookup,
            now,
        )

    scored = []
    for candidate in candidates:
        novelty = _name_novelty(candidate)
        candidate["paper_name_novelty"] = novelty
        scores = {
            name: _model_score(candidate, spec, regime)
            for name, spec in MODEL_SPECS.items()
        }
        candidate["paper_model_scores"] = scores
        scored.append((candidate, scores))

    top_n = int(_num(os.getenv("PAPER_RESEARCH_LOG_TOP_N", "25"), 25))
    for candidate, scores in scored[:max(1, top_n)]:
        _append_csv(
            OBS_FILE,
            _candidate_row(candidate, regime, scores, data_quality),
        )

    normal_size = _num(settings.get("NORMAL_TRADE_SIZE_USDC", 1.5), 1.5)
    early_size = _num(settings.get("EARLY_ACCEL_TRADE_SIZE_USDC", 0.75), 0.75)
    probe_size = _num(os.getenv("PAPER_PROBE_TRADE_SIZE_USDC", "0.75"), 0.75)

    ranked_by_model = {
        name: sorted(scored, key=lambda item: item[1][name], reverse=True)
        for name in MODEL_SPECS
    }

    # Separate raw-mark-only shadow experiments. No quotes, trades, or changes
    # to baseline model parameters are caused by this section.
    if _bool_env("PAPER_SHADOW_EXPERIMENTS_ENABLED", True):
        from research.paper_shadow_experiments import (
            VARIANTS, effective_spec, eligible, qualifies_flow,
            update_confirmation,
        )
        experimental_models = state.setdefault("experiments", {})
        shadow_price_cache = {}

        def cached_shadow_price(token):
            if token not in shadow_price_cache:
                shadow_price_cache[token] = (
                    price_lookup(token) if price_lookup else {}
                )
            return shadow_price_cache[token]

        for variant in VARIANTS:
            base_spec = MODEL_SPECS[variant.base]
            variant_spec = effective_spec(variant, base_spec)
            study = experimental_models.setdefault(variant.name, {
                "shadow_positions": [], "shadow_last_entry": {},
                "shadow_last_loss": {}, "confirmation_state": {},
            })
            _manage_shadow_positions(
                variant.name, study, variant_spec, candidates_by_token,
                cached_shadow_price, now,
            )
            if variant.confirmations > 1:
                for candidate, scores in scored:
                    token = str(candidate.get("token_address") or "")
                    if not token:
                        continue
                    okay, _ = _model_safety_pass(
                        variant.base, candidate, base_spec, regime,
                        scores.get(variant.base, 0.0),
                    )
                    update_confirmation(
                        study, token, now,
                        okay and qualifies_flow(candidate),
                    )
            _add_shadow_positions(
                variant.name, study, variant_spec,
                ranked_by_model[variant.base], regime, now,
                source_name=variant.base,
                policy_gate=lambda candidate, v=variant, s=study: eligible(
                    v, s, candidate, regime, now
                ),
                max_open_override=1,
                # Compare optional loss cooldowns without an overriding
                # blanket 60-minute cooldown on ALL entries.
                cooldown_override=0,
            )

    for name, spec in MODEL_SPECS.items():
        if name == "staged_runner":
            continue
        _add_shadow_positions(
            name,
            state["models"][name],
            spec,
            ranked_by_model[name],
            regime,
            now,
        )

    # Nominate first, quote second. This removes sequential model-order bias.
    nominations = {}
    model_nomination = {}
    for name, spec in MODEL_SPECS.items():
        model = state["models"][name]
        if model.get("position"):
            continue

        for candidate, scores in ranked_by_model[name]:
            score = scores.get(name, 0.0)
            safe, reasons = _model_safety_pass(
                name, candidate, spec, regime, score
            )
            if not safe:
                continue

            size = (early_size if spec.size_key == "EARLY" else probe_size if spec.size_key == "PROBE" else normal_size)
            token = str(candidate.get("token_address") or "")
            key = f"{token}|{size:.8f}"
            nominations.setdefault(
                key,
                {"candidate": candidate, "size": size, "models": []},
            )
            nominations[key]["models"].append(name)
            model_nomination[name] = (key, candidate, scores)
            break

    quote_cache = {}
    configured_quote_cap = int(
        _num(
            os.getenv(
                "PAPER_RESEARCH_MAX_QUOTES_PER_CYCLE",
                str(len(MODEL_SPECS)),
            ),
            len(MODEL_SPECS),
        )
    )
    max_quotes = max(len(MODEL_SPECS), configured_quote_cap)

    for key, item in list(nominations.items())[:max_quotes]:
        if not integrity_lookup:
            quote_cache[key] = {"error": "integrity_lookup_unavailable"}
            continue
        try:
            quote_cache[key] = (
                integrity_lookup(item["candidate"], item["size"]) or {}
            )
        except Exception as exc:
            quote_cache[key] = {"error": str(exc)}

    for name, spec in MODEL_SPECS.items():
        model = state["models"][name]
        if model.get("position"):
            continue

        nomination = model_nomination.get(name)
        if not nomination:
            if ranked_by_model[name]:
                candidate, scores = ranked_by_model[name][0]
            else:
                candidate, scores = {}, {name: 0.0}
            _append_csv(DECISION_FILE, {
                "timestamp": now.isoformat(),
                "date": now.date().isoformat(),
                "model": name,
                "action": "REJECT",
                "symbol": candidate.get("symbol", ""),
                "token_address": candidate.get("token_address", ""),
                "score": round(scores.get(name, 0.0), 6),
                "threshold": spec.threshold,
                "reason": "no_eligible_candidate",
                "regime": regime["name"],
                "roundtrip_pct": 0.0,
                "integrity_detail": "",
                "helius_status": helius_status,
                "data_quality_flags": quality_flags,
            })
            continue

        key, candidate, scores = nomination
        integrity = quote_cache.get(key, {})
        roundtrip = _num(integrity.get("worst_roundtrip_pct"))
        reasons = []
        if roundtrip <= 0:
            reasons.append("no_executable_quote")
        elif roundtrip < spec.roundtrip_floor:
            reasons.append("roundtrip_below_model_floor")
        if integrity.get("passed") is False:
            reasons.extend(
                str(x)
                for x in (integrity.get("reasons") or [])
            )

        _append_csv(DECISION_FILE, {
            "timestamp": now.isoformat(),
            "date": now.date().isoformat(),
            "model": name,
            "action": "ENTER" if not reasons else "REJECT",
            "symbol": candidate.get("symbol", ""),
            "token_address": candidate.get("token_address", ""),
            "score": round(scores.get(name, 0.0), 6),
            "threshold": spec.threshold,
            "reason": ";".join(dict.fromkeys(reasons)) or "qualified",
            "regime": regime["name"],
            "roundtrip_pct": roundtrip,
            "integrity_detail": str(integrity.get("error") or "")[:180],
            "helius_status": helius_status,
            "data_quality_flags": quality_flags,
        })
        if reasons:
            continue

        size = (early_size if spec.size_key == "EARLY" else probe_size if spec.size_key == "PROBE" else normal_size)
        samples = list(integrity.get("samples") or [])
        chosen_sample = (
            min(
                samples,
                key=lambda x: _num(x.get("return_pct"), 999.0),
            )
            if samples
            else {}
        )
        entry_token_raw = int(_num(chosen_sample.get("token_raw")))
        novelty = _name_novelty(candidate)
        position = {
            "symbol": candidate.get("symbol", ""),
            "name": candidate.get("name", ""),
            "token_address": str(candidate.get("token_address") or ""),
            "name_novelty_score": novelty["name_novelty_score"],
            "name_novelty_flags": novelty["novelty_flags"],
            "entry_time": now.isoformat(),
            "entry_price": _num(candidate.get("price_usd")),
            "size_usdc": size,
            "score": scores.get(name, 0.0),
            "roundtrip_pct": roundtrip,
            "entry_token_raw": entry_token_raw,
            "peak_return_pct": 0.0,
            "regime": regime["name"],
            "decay_confirmations": 0,
            "helius_status": helius_status,
            "data_quality_flags": quality_flags,
        }
        model["position"] = position
        _append_csv(TRADE_FILE, {
            "timestamp": now.isoformat(),
            "date": now.date().isoformat(),
            "model": name,
            "action": "BUY",
            "symbol": position["symbol"],
            "name": position.get("name", ""),
            "token_address": position["token_address"],
            "name_novelty_score": position.get("name_novelty_score", ""),
            "name_novelty_flags": position.get("name_novelty_flags", ""),
            "reason": "MODEL_ENTRY",
            "entry_time": now.isoformat(),
            "entry_price": position["entry_price"],
            "exit_price": "",
            "size_usdc": size,
            "raw_return_pct": "",
            "estimated_cost_pct": 100.0 - roundtrip,
            "net_return_pct": "",
            "realized_pnl_usd": "",
            "peak_return_pct": "",
            "roundtrip_preflight_pct": roundtrip,
            "entry_regime": regime["name"],
            "exit_quote_status": "",
            "exit_value_usdc": "",
            "helius_status": helius_status,
            "data_quality_flags": quality_flags,
            "equity_after": (
                _num(model.get("starting_equity"))
                + _num(model.get("realized_pnl"))
            ),
        })

    for name, model in state["models"].items():
        equity = (
            _num(model.get("starting_equity"))
            + _num(model.get("realized_pnl"))
        )
        _append_csv(EQUITY_FILE, {
            "timestamp": now.isoformat(),
            "date": now.date().isoformat(),
            "model": name,
            "equity": round(equity, 8),
            "realized_pnl": round(_num(model.get("realized_pnl")), 8),
            "completed": int(model.get("completed", 0)),
            "open_symbol": (model.get("position") or {}).get("symbol", ""),
            "shadow_open": len(model.get("shadow_positions") or []),
            "max_drawdown_pct": round(
                _num(model.get("max_drawdown_pct")),
                8,
            ),
            "helius_status": helius_status,
            "data_quality_flags": quality_flags,
        })

    state["last_cycle_at"] = now.isoformat()
    state["last_regime"] = regime
    _save_state(state)
    return {"regime": regime, "models": state["models"]}


def _max_drawdown_from_returns(returns):
    equity = 1.0
    peak = 1.0
    max_dd = 0.0
    for value in returns:
        equity *= max(0.000001, 1.0 + _num(value) / 100.0)
        peak = max(peak, equity)
        if peak > 0:
            max_dd = max(max_dd, (peak - equity) / peak * 100.0)
    return max_dd


def daily_summary(report_date=None, write_files=True):
    report_date = report_date or datetime.now().date().isoformat()
    rows = []
    shadow_rows = []

    if TRADE_FILE.exists():
        try:
            with TRADE_FILE.open("r", newline="", encoding="utf-8") as handle:
                rows = [
                    r
                    for r in csv.DictReader(handle)
                    if r.get("date") == report_date
                ]
        except Exception:
            rows = []

    if SHADOW_TRADE_FILE.exists():
        try:
            with SHADOW_TRADE_FILE.open(
                "r",
                newline="",
                encoding="utf-8",
            ) as handle:
                shadow_rows = [
                    r
                    for r in csv.DictReader(handle)
                    if r.get("date") == report_date
                ]
        except Exception:
            shadow_rows = []

    results = []
    for name in MODEL_SPECS:
        sells = [
            r
            for r in rows
            if r.get("model") == name and r.get("action") == "SELL"
        ]
        buys = [
            r
            for r in rows
            if r.get("model") == name and r.get("action") == "BUY"
        ]
        shadow_sells = [
            r
            for r in shadow_rows
            if r.get("model") == name and r.get("action") == "SELL"
        ]
        pnls = [_num(r.get("realized_pnl_usd")) for r in sells]
        returns = [_num(r.get("net_return_pct")) for r in sells]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        gross_win = sum(wins)
        gross_loss = abs(sum(losses))
        avg_ret = sum(returns) / len(returns) if returns else 0.0
        med_ret = median(returns) if returns else 0.0
        profit_factor = (
            gross_win / gross_loss
            if gross_loss > 0
            else (999.0 if gross_win > 0 else 0.0)
        )
        results.append({
            "model": name,
            "entries": len(buys),
            "completed": len(sells),
            "shadow_completed": len(shadow_sells),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate_pct": (
                len(wins) / len(sells) * 100
                if sells
                else 0.0
            ),
            "realized_pnl_usd": sum(pnls),
            "avg_net_return_pct": avg_ret,
            "median_net_return_pct": med_ret,
            "profit_factor": profit_factor,
            "max_drawdown_pct": _max_drawdown_from_returns(returns),
        })

    ranked = sorted(
        results,
        key=lambda r: (
            r["completed"] >= 12,
            r["avg_net_return_pct"],
            min(r["profit_factor"], 10.0),
            -r["max_drawdown_pct"],
            r["median_net_return_pct"],
            r["realized_pnl_usd"],
        ),
        reverse=True,
    )

    from research.paper_goal_scorecard import goal_scorecard
    starting_equities = {
        name: _num(((_load_state(_num(os.getenv("PAPER_STARTING_EQUITY_USDC", "15"), 15)).get("models") or {}).get(name) or {}).get("starting_equity"), _num(os.getenv("PAPER_STARTING_EQUITY_USDC", "15"), 15))
        for name in ("balanced_ev", "runner_hunter", "diy_whale")
    }
    goal_metrics = goal_scorecard(TRADE_FILE, report_date, starting_equities)
    for row in results:
        if row["model"] in goal_metrics["sleeves"]:
            row["goal_1pct_daily"] = goal_metrics["sleeves"][row["model"]]
            # The previous value compounds percentage returns on each trade and
            # is not a portfolio drawdown; replace it with realized-equity DD.
            row["trade_compounded_drawdown_pct_legacy"] = row["max_drawdown_pct"]
            row["max_drawdown_pct"] = row["goal_1pct_daily"]["daily_realized_equity_drawdown_pct"]
    summary = {
        "goal_1pct_daily": goal_metrics,
        "portfolio_metrics_caveat": "1% target measured on realized equity only; mark-to-market portfolio return unavailable.", 
        "date": report_date,
        "generated_at": datetime.now().isoformat(),
        "ranking_basis": (
            "sample-qualified normalized return, profit factor, drawdown, "
            "median return; dollar PnL secondary"
        ),
        "minimum_completed_for_preliminary_comparison": 12,
        "minimum_completed_for_promotion_review": 30,
        "models": ranked,
        "leader": (
            ranked[0]["model"]
            if ranked and ranked[0]["completed"] >= 12
            else None
        ),
        "promotion_eligible": [
            r["model"]
            for r in ranked
            if r["completed"] >= 30
            and r["avg_net_return_pct"] > 0
            and r["profit_factor"] >= 1.3
            and r["max_drawdown_pct"] <= 15
        ],
    }

    # Dedicated three-sleeve scorecard; preserve zeros as no-trade evidence,
    # never represent average trade return as daily portfolio return.
    sleeve_names = ("balanced_ev", "runner_hunter", "diy_whale")
    sleeve_rows = [next(r for r in results if r["model"] == name)
                   for name in sleeve_names]
    qualified = [r for r in sleeve_rows if r["completed"] >= 12]
    summary["three_sleeve_comparison"] = {
        "models": sleeve_rows,
        "leader": max(qualified, key=lambda r: r["avg_net_return_pct"])["model"]
                  if qualified else None,
        "note": "Average net trade return is NOT daily portfolio return. "
                "Compare capital-normalized equity changes separately; "
                "no-trade sleeves have insufficient evidence.",
    }

    if write_files:
        SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
        (SUMMARY_DIR / f"{report_date}.json").write_text(
            json.dumps(summary, indent=2),
            encoding="utf-8",
        )
        md = [
            f"# CryptoTracker paper research — {report_date}",
            "",
            "| Model | Trades | Shadow | W/L | Avg net | Median | Max DD | PnL | PF |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for row in ranked:
            md.append(
                f"| {row['model']} | {row['completed']} | "
                f"{row['shadow_completed']} | {row['wins']}/{row['losses']} | "
                f"{row['avg_net_return_pct']:+.2f}% | "
                f"{row['median_net_return_pct']:+.2f}% | "
                f"{row['max_drawdown_pct']:.2f}% | "
                f"{row['realized_pnl_usd']:+.4f} | "
                f"{row['profit_factor']:.2f} |"
            )
        md.extend(["", "## Three-sleeve comparison",
                   "",
                   "| Sleeve | Entries | Closed | Win rate | Avg trade net | Max DD | Realized PnL |",
                   "|---|---:|---:|---:|---:|---:|---:|"])
        for r in sleeve_rows:
            md.append(f"| {r['model']} | {r['entries']} | {r['completed']} | "
                      f"{r['win_rate_pct']:.1f}% | {r['avg_net_return_pct']:+.2f}% | "
                      f"{r['max_drawdown_pct']:.2f}% | ${r['realized_pnl_usd']:+.2f} |")
        md.extend(["", "## 1% daily goal — realized-equity proxy (not portfolio return)", "",
                   "| Sleeve | Daily realized-equity return | Daily target | Hit? | Since inception realized-equity return | Compounded target since first observed entry | Gap (USD) | Realized-equity DD since inception |",
                   "|---|---:|---:|---|---:|---:|---:|---:|"])
        for key, score in goal_metrics["sleeves"].items():
            def fmt(value):
                return f"{value:+.2f}%" if value is not None else "N/A"
            md.append(
                f"| {key} | {fmt(score['daily_realized_equity_return_pct'])} | +1.00% | "
                f"{score['daily_goal_met_on_realized_basis']} | "
                f"{fmt(score['since_inception_realized_equity_return_pct'])} | "
                f"{fmt(score['since_inception_compounded_1pct_daily_target_pct'])} | "
                f"{score['since_inception_gap_vs_target_usd']} | "
                f"{fmt(score['since_inception_realized_equity_drawdown_pct'])} |"
            )
        md.extend(["", "**Warning:** These are completed-trade realized-equity measurements, "
                   "not mark-to-market portfolio returns. Open-position losses are excluded. "
                   "The target compounds 1% per calendar day, not per trade."])
        md.extend(["", summary["three_sleeve_comparison"]["note"]])
        md.extend([
            "",
            "No live promotion occurs automatically. "
            "Any change requires explicit approval.",
        ])
        (SUMMARY_DIR / f"{report_date}.md").write_text(
            "\n".join(md) + "\n",
            encoding="utf-8",
        )

    return summary


def campaign_summary(write_files=True):
    """Score the full paper campaign with a chronological 70/30 holdout."""
    rows = []
    if TRADE_FILE.exists():
        try:
            with TRADE_FILE.open("r", newline="", encoding="utf-8") as handle:
                rows = [r for r in csv.DictReader(handle) if r.get("action") == "SELL"]
        except Exception:
            rows = []

    def segment_stats(items):
        pnls = [_num(r.get("realized_pnl_usd")) for r in items]
        returns = [_num(r.get("net_return_pct")) for r in items]
        gross_win = sum(x for x in pnls if x > 0)
        gross_loss = abs(sum(x for x in pnls if x < 0))
        return {
            "n": len(items),
            "avg_net_return_pct": sum(returns) / len(returns) if returns else 0.0,
            "median_net_return_pct": median(returns) if returns else 0.0,
            "realized_pnl_usd": sum(pnls),
            "win_rate_pct": sum(x > 0 for x in pnls) / len(pnls) * 100 if pnls else 0.0,
            "profit_factor": gross_win / gross_loss if gross_loss else (999.0 if gross_win else 0.0),
            "max_drawdown_pct": _max_drawdown_from_returns(returns),
        }

    models = []
    for name in MODEL_SPECS:
        items = sorted(
            [r for r in rows if r.get("model") == name],
            key=lambda r: str(r.get("timestamp") or ""),
        )
        split = max(1, int(len(items) * 0.70)) if items else 0
        train = segment_stats(items[:split])
        holdout = segment_stats(items[split:])
        all_stats = segment_stats(items)
        optional_helius_degraded = sum(
            "HELIUS_UNAVAILABLE_OPTIONAL" in str(r.get("data_quality_flags") or "")
            for r in items
        )
        all_stats["optional_helius_degraded_trades"] = optional_helius_degraded
        by_regime = {}
        for regime_name in ("RISK_ON", "NEUTRAL", "RISK_OFF", "NO_DATA"):
            regime_items = [
                r for r in items
                if str(r.get("entry_regime") or "") == regime_name
            ]
            if regime_items:
                by_regime[regime_name] = segment_stats(regime_items)
        stable = (
            all_stats["n"] >= 30
            and train["avg_net_return_pct"] > 0
            and holdout["avg_net_return_pct"] > 0
            and holdout["profit_factor"] >= 1.3
            and holdout["max_drawdown_pct"] <= 15
        )
        models.append({
            "model": name,
            "all": all_stats,
            "development_70pct": train,
            "holdout_30pct": holdout,
            "by_entry_regime": by_regime,
            "stable_positive_holdout": stable,
        })
    models.sort(
        key=lambda x: (
            x["stable_positive_holdout"],
            x["all"]["n"] >= 12,
            x["holdout_30pct"]["avg_net_return_pct"],
            min(x["holdout_30pct"]["profit_factor"], 10.0),
            -x["holdout_30pct"]["max_drawdown_pct"],
            x["all"]["avg_net_return_pct"],
            x["all"]["realized_pnl_usd"],
        ),
        reverse=True,
    )
    from research.paper_goal_scorecard import goal_scorecard
    # Include inactive calendar days in the 1%-per-day target; using the
    # most recent SELL date would silently skip days with no realized exits.
    through_date = datetime.now().date().isoformat()
    state = _load_state(_num(os.getenv("PAPER_STARTING_EQUITY_USDC", "15"), 15))
    starts = {
        name: _num(((state.get("models") or {}).get(name) or {}).get("starting_equity"), _num(os.getenv("PAPER_STARTING_EQUITY_USDC", "15"), 15))
        for name in ("balanced_ev", "runner_hunter", "diy_whale")
    }
    goal_metrics = goal_scorecard(TRADE_FILE, through_date, starts)
    for item in models:
        name = item["model"]
        if name in goal_metrics["sleeves"]:
            item["goal_1pct_daily"] = goal_metrics["sleeves"][name]
            item["all"]["trade_compounded_drawdown_pct_legacy"] = item["all"]["max_drawdown_pct"]
            item["all"]["max_drawdown_pct"] = goal_metrics["sleeves"][name]["since_inception_realized_equity_drawdown_pct"]
    summary = {
        "goal_1pct_daily": goal_metrics,
        "generated_at": datetime.now().isoformat(),
        "split": "chronological_70_30",
        "minimum_completed_for_promotion_review": 30,
        "models": models,
        "promotion_candidates": [
            x["model"] for x in models if x["stable_positive_holdout"]
        ],
    }
    if write_files:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        (DATA_DIR / "campaign_summary.json").write_text(
            json.dumps(summary, indent=2),
            encoding="utf-8",
        )
    return summary


def eod_summary_text(report_date=None):
    """Compact EOD summary with daily and campaign account-equivalent returns."""
    daily = daily_summary(report_date, write_files=True)
    campaign = campaign_summary(write_files=True)
    models = campaign.get("models") or []
    if not models:
        return "Paper lab: no completed model trades yet."

    top = models[0]
    model_name = top.get("model", "unknown")
    all_stats = top.get("all") or {}
    holdout = top.get("holdout_30pct") or {}

    campaign_completed = int(all_stats.get("n", 0) or 0)
    if not campaign_completed:
        return "Paper lab: no completed model trades yet."

    configured_start = _num(
        os.getenv("PAPER_STARTING_EQUITY_USDC", "15"),
        15,
    )
    state = _load_state(configured_start)
    model_state = (state.get("models") or {}).get(model_name) or {}
    starting_equity = _num(
        model_state.get("starting_equity"),
        configured_start,
    )
    if starting_equity <= 0:
        starting_equity = configured_start if configured_start > 0 else 15.0

    campaign_pnl = _num(all_stats.get("realized_pnl_usd"))
    campaign_return_pct = (
        campaign_pnl / starting_equity * 100.0
        if starting_equity > 0
        else 0.0
    )
    ending_equity = starting_equity + campaign_pnl

    daily_model = next(
        (
            row for row in (daily.get("models") or [])
            if row.get("model") == model_name
        ),
        {},
    )
    daily_pnl = _num(daily_model.get("realized_pnl_usd"))
    daily_return_pct = (
        daily_pnl / starting_equity * 100.0
        if starting_equity > 0
        else 0.0
    )

    avg_trade = _num(all_stats.get("avg_net_return_pct"))
    median_trade = _num(all_stats.get("median_net_return_pct"))
    wins = int(round(campaign_completed * _num(all_stats.get("win_rate_pct")) / 100.0))
    losses = max(0, campaign_completed - wins)

    holdout_n = int(holdout.get("n", 0) or 0)
    holdout_avg = _num(holdout.get("avg_net_return_pct"))

    if top.get("stable_positive_holdout"):
        promotion_text = "Promotion: ELIGIBLE FOR REVIEW"
    elif campaign_completed < 30:
        promotion_text = (
            f"Promotion: NOT YET — need {30 - campaign_completed} more trades"
        )
    else:
        promotion_text = "Promotion: NOT YET — holdout criteria unmet"

    return "\n".join([
        f"Paper day: {daily_return_pct:+.2f}% | ${daily_pnl:+.4f}",
        (
            f"Campaign: {campaign_return_pct:+.2f}% | "
            f"${starting_equity:.2f} -> ${ending_equity:.2f}"
        ),
        (
            f"Leader: {model_name} | {campaign_completed} trades | "
            f"{wins}W/{losses}L"
        ),
        f"Avg trade: {avg_trade:+.2f}% | Median: {median_trade:+.2f}%",
        (
            "1%/day goal (realized-only): "
            + " | ".join(
                f"{key}: day "
                f"{(value.get('daily_realized_equity_return_pct') if value.get('daily_realized_equity_return_pct') is not None else float('nan')):+.2f}%"
                f", inception "
                f"{(value.get('since_inception_realized_equity_return_pct') if value.get('since_inception_realized_equity_return_pct') is not None else float('nan')):+.2f}%"
                f", target {value.get('since_inception_compounded_1pct_daily_target_pct')}%"
                for key, value in daily.get("goal_1pct_daily", {}).get("sleeves", {}).items()
            )
        ),
        f"Holdout: {holdout_n} trades | {holdout_avg:+.2f}% avg",
        promotion_text,
    ])


if __name__ == "__main__":
    print(json.dumps(daily_summary(), indent=2))
