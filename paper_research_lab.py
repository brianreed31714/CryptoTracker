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

    balanced = 100 * (
        0.30 * _clip(f["quant"] / 120)
        + 0.20 * _clip(f["delta"] / 60)
        + 0.15 * _clip((f["volume_accel"] - 1) / 3)
        + 0.15 * _clip((f["buy_sell"] - 1) / 1.5)
        + 0.10 * _clip(f["tx5"] / 80)
        + 0.05 * _clip(math.log10(max(f["volume_5m"], 1)) / 5)
        + 0.05 * _clip(1 - abs(f["price_5m"] - 6) / 20)
    )
    if spec.score_kind == "flow":
        return 100 * (
            0.30 * _clip((f["volume_accel"] - 1) / 3)
            + 0.25 * _clip((f["buy_sell"] - 1) / 1.5)
            + 0.20 * _clip(f["delta"] / 60)
            + 0.15 * _clip(f["tx5"] / 80)
            + 0.10 * _clip(1 - abs(f["price_5m"] - 5) / 18)
        )
    if spec.score_kind == "whale_ai":
        return 0.60 * balanced + 40 * (
            0.45 * _clip(f["whale"] / 25)
            + 0.35 * _clip(f["ai_confidence"] / 100)
            + 0.20 * _clip(f["token_social"] / 10)
        )
    if spec.score_kind == "early":
        return 100 * (
            0.30 * _clip(f["delta"] / 70)
            + 0.25 * _clip((f["volume_accel"] - 1) / 4)
            + 0.20 * _clip((f["buy_sell"] - 1) / 2)
            + 0.15 * _clip(f["tx5"] / 60)
            + 0.10 * _clip(1 - abs(f["price_5m"] - 4) / 15)
        )
    if regime["name"] == "RISK_ON":
        balanced += 7
    elif regime["name"] == "RISK_OFF":
        balanced -= 12
    return _clip(balanced, 0, 100)


def _candidate_row(candidate, regime, scores):
    f = _features(candidate)
    now = datetime.now()
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


def _close_position(name, model, position, exit_price, reason, now):
    entry_price = _num(position.get("entry_price"))
    raw_return = ((exit_price - entry_price) / entry_price * 100) if entry_price > 0 else 0.0
    cost_pct = max(0.0, 100.0 - _num(position.get("roundtrip_pct"), 100.0))
    net_return = raw_return - cost_pct
    size = _num(position.get("size_usdc"))
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
        "equity_after": round(equity, 8),
    })


def _manage_position(name, model, spec, candidates_by_token, price_lookup, now):
    position = model.get("position")
    if not position:
        return
    price, _ = _current_price(position, candidates_by_token, price_lookup)
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
    reason = None
    if raw_return <= spec.stop_pct:
        reason = "STOP"
    elif age >= spec.max_hold_minutes:
        reason = "MAX_HOLD"
    elif position["peak_return_pct"] >= spec.runner_activate_pct and (
        position["peak_return_pct"] - raw_return >= spec.trail_pct
    ):
        reason = "RUNNER_TRAIL"
    elif age >= spec.grace_minutes and raw_return <= -2.0:
        reason = "FAILED_MOMENTUM"
    if reason:
        _close_position(name, model, position, price, reason, now)
    else:
        _append_csv(DECISION_FILE, {
            "timestamp": now.isoformat(), "date": now.date().isoformat(), "model": name,
            "action": "HOLD", "symbol": position.get("symbol", ""),
            "token_address": position.get("token_address", ""), "score": "",
            "threshold": spec.threshold, "reason": f"pnl={raw_return:+.3f};age={age:.1f}",
            "regime": "", "roundtrip_pct": position.get("roundtrip_pct", ""),
        })


def run_paper_research(candidates, settings, price_lookup=None, integrity_lookup=None):
    """Run one research cycle.  This function cannot submit a transaction."""
    if not _bool_env("PAPER_RESEARCH_ENABLED", True):
        return {}
    now = datetime.now()
    starting_equity = _num(os.getenv("PAPER_STARTING_EQUITY_USDC", "15"), 15)
    state = _load_state(starting_equity)
    for name in MODEL_SPECS:
        state.setdefault("models", {}).setdefault(name, {
            "starting_equity": starting_equity, "realized_pnl": 0.0,
            "peak_equity": starting_equity, "max_drawdown_pct": 0.0,
            "completed": 0, "wins": 0, "losses": 0, "position": None,
        })

    regime = _regime(candidates)
    candidates_by_token = {str(c.get("token_address")): c for c in candidates if c.get("token_address")}
    for name, spec in MODEL_SPECS.items():
        _manage_position(name, state["models"][name], spec, candidates_by_token, price_lookup, now)

    scored = []
    for candidate in candidates:
        scores = {name: _model_score(candidate, spec, regime) for name, spec in MODEL_SPECS.items()}
        candidate["paper_model_scores"] = scores
        scored.append((candidate, scores))

    top_n = int(_num(os.getenv("PAPER_RESEARCH_LOG_TOP_N", "25"), 25))
    for candidate, scores in scored[:max(1, top_n)]:
        _append_csv(OBS_FILE, _candidate_row(candidate, regime, scores))

    quote_cache = {}
    max_quotes = int(_num(os.getenv("PAPER_RESEARCH_MAX_QUOTES_PER_CYCLE", "3"), 3))
    normal_size = _num(settings.get("NORMAL_TRADE_SIZE_USDC", 1.5), 1.5)
    early_size = _num(settings.get("EARLY_ACCEL_TRADE_SIZE_USDC", 0.75), 0.75)

    for name, spec in MODEL_SPECS.items():
        model = state["models"][name]
        if model.get("position"):
            continue
        ranked = sorted(scored, key=lambda item: item[1][name], reverse=True)
        candidate, scores = ranked[0] if ranked else ({}, {name: 0.0})
        score = scores.get(name, 0.0)
        safe, reasons = _safety_pass(candidate) if candidate else (False, ["no_candidate"])
        if spec.requires_risk_on and regime["name"] != "RISK_ON":
            safe = False
            reasons.append("regime_not_risk_on")
        if score < spec.threshold:
            safe = False
            reasons.append("score_below_threshold")
        token = str(candidate.get("token_address") or "")
        roundtrip = 0.0
        integrity_reason = ""
        if safe and token:
            if token not in quote_cache and integrity_lookup and len(quote_cache) < max_quotes:
                size = early_size if spec.size_key == "EARLY" else normal_size
                try:
                    quote_cache[token] = integrity_lookup(candidate, size) or {}
                except Exception as exc:
                    quote_cache[token] = {"error": str(exc)}
            integrity = quote_cache.get(token, {})
            roundtrip = _num(integrity.get("worst_roundtrip_pct"))
            if roundtrip <= 0:
                safe = False
                reasons.append("no_executable_quote")
                integrity_reason = str(integrity.get("error") or "")[:180]
            elif roundtrip < spec.roundtrip_floor:
                safe = False
                reasons.append("roundtrip_below_model_floor")

        action = "ENTER" if safe else "REJECT"
        _append_csv(DECISION_FILE, {
            "timestamp": now.isoformat(), "date": now.date().isoformat(), "model": name,
            "action": action, "symbol": candidate.get("symbol", ""),
            "token_address": token, "score": round(score, 6), "threshold": spec.threshold,
            "reason": ";".join(dict.fromkeys(reasons)) or "qualified",
            "regime": regime["name"], "roundtrip_pct": roundtrip,
            "integrity_detail": integrity_reason,
        })
        if not safe:
            continue
        size = early_size if spec.size_key == "EARLY" else normal_size
        position = {
            "symbol": candidate.get("symbol", ""), "token_address": token,
            "entry_time": now.isoformat(), "entry_price": _num(candidate.get("price_usd")),
            "size_usdc": size, "score": score, "roundtrip_pct": roundtrip,
            "peak_return_pct": 0.0, "regime": regime["name"],
        }
        model["position"] = position
        _append_csv(TRADE_FILE, {
            "timestamp": now.isoformat(), "date": now.date().isoformat(), "model": name,
            "action": "BUY", "symbol": position["symbol"], "token_address": token,
            "reason": "MODEL_ENTRY", "entry_time": now.isoformat(),
            "entry_price": position["entry_price"], "exit_price": "", "size_usdc": size,
            "raw_return_pct": "", "estimated_cost_pct": 100.0 - roundtrip,
            "net_return_pct": "", "realized_pnl_usd": "", "peak_return_pct": "",
            "roundtrip_preflight_pct": roundtrip,
            "equity_after": _num(model.get("starting_equity")) + _num(model.get("realized_pnl")),
        })

    for name, model in state["models"].items():
        equity = _num(model.get("starting_equity")) + _num(model.get("realized_pnl"))
        _append_csv(EQUITY_FILE, {
            "timestamp": now.isoformat(), "date": now.date().isoformat(), "model": name,
            "equity": round(equity, 8), "realized_pnl": round(_num(model.get("realized_pnl")), 8),
            "completed": int(model.get("completed", 0)),
            "open_symbol": (model.get("position") or {}).get("symbol", ""),
            "max_drawdown_pct": round(_num(model.get("max_drawdown_pct")), 8),
        })
    state["last_cycle_at"] = now.isoformat()
    state["last_regime"] = regime
    _save_state(state)
    return {"regime": regime, "models": state["models"]}


def daily_summary(report_date=None, write_files=True):
    report_date = report_date or datetime.now().date().isoformat()
    rows = []
    if TRADE_FILE.exists():
        try:
            with TRADE_FILE.open("r", newline="", encoding="utf-8") as handle:
                rows = [r for r in csv.DictReader(handle) if r.get("date") == report_date]
        except Exception:
            rows = []
    results = []
    for name in MODEL_SPECS:
        sells = [r for r in rows if r.get("model") == name and r.get("action") == "SELL"]
        buys = [r for r in rows if r.get("model") == name and r.get("action") == "BUY"]
        pnls = [_num(r.get("realized_pnl_usd")) for r in sells]
        returns = [_num(r.get("net_return_pct")) for r in sells]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        gross_win = sum(wins)
        gross_loss = abs(sum(losses))
        results.append({
            "model": name, "entries": len(buys), "completed": len(sells),
            "wins": len(wins), "losses": len(losses),
            "win_rate_pct": (len(wins) / len(sells) * 100) if sells else 0.0,
            "realized_pnl_usd": sum(pnls),
            "avg_net_return_pct": (sum(returns) / len(returns)) if returns else 0.0,
            "median_net_return_pct": median(returns) if returns else 0.0,
            "profit_factor": (gross_win / gross_loss) if gross_loss > 0 else (999.0 if gross_win > 0 else 0.0),
        })
    ranked = sorted(results, key=lambda r: (r["realized_pnl_usd"], r["avg_net_return_pct"]), reverse=True)
    summary = {
        "date": report_date,
        "generated_at": datetime.now().isoformat(),
        "minimum_completed_for_preliminary_comparison": 12,
        "minimum_completed_for_promotion_review": 30,
        "models": ranked,
        "leader": ranked[0]["model"] if ranked and ranked[0]["completed"] >= 12 else None,
        "promotion_eligible": [
            r["model"] for r in ranked
            if r["completed"] >= 30 and r["avg_net_return_pct"] > 0 and r["profit_factor"] >= 1.3
        ],
    }
    if write_files:
        SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
        (SUMMARY_DIR / f"{report_date}.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        md = [f"# CryptoTracker paper research — {report_date}", "", "| Model | Trades | W/L | Avg net | P&L | PF |", "|---|---:|---:|---:|---:|---:|"]
        for row in ranked:
            md.append(
                f"| {row['model']} | {row['completed']} | {row['wins']}/{row['losses']} | "
                f"{row['avg_net_return_pct']:+.2f}% | ${row['realized_pnl_usd']:+.4f} | {row['profit_factor']:.2f} |"
            )
        md.extend(["", "No live promotion occurs automatically. Any change requires explicit approval."])
        (SUMMARY_DIR / f"{report_date}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return summary


def eod_summary_text(report_date=None):
    summary = daily_summary(report_date, write_files=True)
    models = summary.get("models") or []
    completed = sum(int(m.get("completed", 0)) for m in models)
    if not completed:
        return "Paper lab: no completed model trades yet."
    top = models[0]
    return (
        f"Paper lab: {completed} exits | leader {top['model']} "
        f"{top['avg_net_return_pct']:+.2f}% avg | ${top['realized_pnl_usd']:+.4f}"
    )


if __name__ == "__main__":
    print(json.dumps(daily_summary(), indent=2))
