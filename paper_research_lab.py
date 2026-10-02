#!/usr/bin/env python3
"""CryptoTracker paper-research laboratory.

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
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row.keys()), extrasaction="ignore")
        if not exists:
            writer.writeheader()
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
}


def _regime


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

def _candidate_row

def _candidate_row(candidate, regime, scores, data_quality=None):
    f = _features(candidate)
    now = datetime.now()
    data_quality = data_quality or {}
    row = {
        "timestamp": now.isoformat(),
        "date": now.date().isoformat(),
        "symbol": candidate.get("symbol", ""),
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
        "token_address": position.get("token_address", ""), "reason": reason,
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
        _append_csv(SHADOW_TRADE_FILE, {
            "timestamp": now.isoformat(), "date": now.date().isoformat(), "model": name,
            "action": "SELL", "symbol": position.get("symbol", ""),
            "token_address": position.get("token_address", ""), "reason": reason,
            "entry_time": position.get("entry_time", ""), "entry_price": position.get("entry_price", ""),
            "exit_price": price, "net_return_pct": round(raw_return, 8),
            "peak_return_pct": round(_num(position.get("peak_return_pct")), 8),
            "entry_regime": position.get("regime", ""),
        })
    model["shadow_positions"] = kept


def _add_shadow_positions(name, model, spec, ranked, regime, now):
    max_open = max(1, int(_num(os.getenv("PAPER_RESEARCH_SHADOW_POSITIONS_PER_MODEL", "5"), 5)))
    cooldown = max(0.0, _num(os.getenv("PAPER_RESEARCH_SHADOW_REENTRY_MINUTES", "60"), 60))
    positions = list(model.get("shadow_positions") or [])
    open_tokens = {str(p.get("token_address") or "") for p in positions}
    last_entries = model.setdefault("shadow_last_entry", {})

    for candidate, scores in ranked:
        if len(positions) >= max_open:
            break
        token = str(candidate.get("token_address") or "")
        if not token or token in open_tokens:
            continue
        safe, _ = _safety_pass(candidate)
        if spec.requires_risk_on and regime["name"] != "RISK_ON":
            safe = False
        if scores.get(name, 0.0) < spec.threshold:
            safe = False
        if not safe:
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
            "score": scores.get(name, 0.0), "peak_return_pct": 0.0,
            "regime": regime["name"], "decay_confirmations": 0,
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
        })
    model["shadow_positions"] = positions


def run_paper_research

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

    ranked_by_model = {
        name: sorted(scored, key=lambda item: item[1][name], reverse=True)
        for name in MODEL_SPECS
    }

    for name, spec in MODEL_SPECS.items():
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
            safe, reasons = _safety_pass(candidate)
            if spec.requires_risk_on and regime["name"] != "RISK_ON":
                safe = False
                reasons.append("regime_not_risk_on")
            if score < spec.threshold:
                safe = False
                reasons.append("score_below_threshold")
            if not safe:
                continue

            size = early_size if spec.size_key == "EARLY" else normal_size
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

        size = early_size if spec.size_key == "EARLY" else normal_size
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
        position = {
            "symbol": candidate.get("symbol", ""),
            "token_address": str(candidate.get("token_address") or ""),
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
            "token_address": position["token_address"],
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


def daily_summary

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

    summary = {
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


def campaign_summary

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
        stable = (
            all_stats["n"] >= 30
            and train["avg_net_return_pct"] > 0
            and holdout["avg_net_return_pct"] > 0
            and holdout["profit_factor"] >= 1.3
        )
        models.append({
            "model": name,
            "all": all_stats,
            "development_70pct": train,
            "holdout_30pct": holdout,
            "stable_positive_holdout": stable,
        })
    models.sort(
        key=lambda x: (
            x["stable_positive_holdout"],
            x["holdout_30pct"]["avg_net_return_pct"],
            x["all"]["realized_pnl_usd"],
        ),
        reverse=True,
    )
    summary = {
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
    daily_summary(report_date, write_files=True)
    summary = campaign_summary(write_files=True)
    models = summary.get("models") or []
    completed = sum(int((m.get("all") or {}).get("n", 0)) for m in models)
    if not completed:
        return "Paper lab: no completed model trades yet."
    top = models[0]
    all_stats = top.get("all") or {}
    return (
        f"Paper lab: {completed} exits | leader {top['model']} "
        f"{all_stats.get('avg_net_return_pct', 0):+.2f}% avg | "
        f"${all_stats.get('realized_pnl_usd', 0):+.4f}"
    )


if __name__ == "__main__":
    print(json.dumps(daily_summary(), indent=2))
