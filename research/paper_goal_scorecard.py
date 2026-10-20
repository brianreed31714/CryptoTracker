"""Paper-only 1%/day goal scorecards, calculated from completed trades.

Realized-equity measures are NOT mark-to-market portfolio returns.
Never label realized equity or average trade return as full portfolio growth.
"""
from __future__ import annotations
import csv
from datetime import date
from pathlib import Path

GOAL_DAILY_PCT = 1.0
FOCUS = ("balanced_ev", "runner_hunter", "diy_whale")

def _number(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def _trades(path):
    path = Path(path)
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))

def _day(row):
    return str(row.get("date") or row.get("timestamp") or "")[:10]

def _exit_rows(rows, model, through=None):
    return sorted(
        (r for r in rows if r.get("model") == model
         and str(r.get("action", "")).upper() == "SELL"
         and (through is None or _day(r) <= through)),
        key=lambda r: (str(r.get("timestamp") or r.get("exit_time") or ""), _day(r)),
    )

def _drawdown(start_equity, exits):
    if start_equity <= 0:
        return None
    equity = peak = start_equity
    worst = 0.0
    for row in exits:
        equity += _number(row.get("realized_pnl_usd"))
        peak = max(peak, equity)
        worst = max(worst, (peak - equity) * 100.0 / peak)
    return round(worst, 6)

def goal_scorecard(path, report_date, starting_equities=None):
    """Calculate dated and inception-to-date realized-equity goal *proxies*.

    Targets are 1% per calendar day, compounded since first observed model entry.
    This is deliberately NOT a claim that a paper model can achieve that return.
    """
    rows = _trades(path)
    starting_equities = starting_equities or {}
    out = {}
    for model in FOCUS:
        start = _number(starting_equities.get(model), 0.0)
        exits = _exit_rows(rows, model, report_date)
        previous = [r for r in exits if _day(r) < report_date]
        today = [r for r in exits if _day(r) == report_date]
        prior_pnl = sum(_number(r.get("realized_pnl_usd")) for r in previous)
        today_pnl = sum(_number(r.get("realized_pnl_usd")) for r in today)
        cumulative_pnl = prior_pnl + today_pnl
        opening = start + prior_pnl
        all_observed = [
            _day(r) for r in rows if r.get("model") == model
            and str(r.get("action", "")).upper() in ("BUY", "SELL")
            and _day(r) and _day(r) <= report_date
        ]
        first = min(all_observed) if all_observed else None
        elapsed = (date.fromisoformat(report_date) - date.fromisoformat(first)).days + 1 if first else None
        daily_return = round(100 * today_pnl / opening, 6) if opening > 0 else None
        inception_return = round(100 * cumulative_pnl / start, 6) if start > 0 else None
        target_compounded = round(100 * ((1.01 ** elapsed) - 1), 6) if elapsed is not None else None
        inception_actual_equity = start + cumulative_pnl if start > 0 else None
        target_equity = round(start * (1.01 ** elapsed), 8) if elapsed is not None and start > 0 else None
        target_shortfall = round(inception_actual_equity - target_equity, 8) if target_equity is not None else None
        out[model] = {
            "measurement": "realized_equity_only_excludes_open_position_mark_to_market",
            "goal_daily_pct": GOAL_DAILY_PCT,
            "daily_completed": len(today),
            "daily_realized_pnl_usd": round(today_pnl, 8),
            "daily_opening_realized_equity_usd": round(opening, 8) if start > 0 else None,
            "daily_realized_equity_return_pct": daily_return,
            "daily_goal_met_on_realized_basis": daily_return >= GOAL_DAILY_PCT if daily_return is not None else None,
            "daily_realized_equity_drawdown_pct": _drawdown(opening, today),
            "first_observed_date": first,
            "elapsed_calendar_days_inclusive": elapsed,
            "since_inception_realized_pnl_usd": round(cumulative_pnl, 8),
            "since_inception_realized_equity_return_pct": inception_return,
            "since_inception_realized_equity_drawdown_pct": _drawdown(start, exits),
            "since_inception_compounded_1pct_daily_target_pct": target_compounded,
            "since_inception_target_equity_usd": target_equity,
            "since_inception_actual_realized_equity_usd": round(inception_actual_equity, 8) if inception_actual_equity is not None else None,
            "since_inception_gap_vs_target_usd": target_shortfall,
            "full_portfolio_daily_return_pct": None,
            "full_portfolio_since_inception_return_pct": None,
            "full_portfolio_drawdown_pct": None,
            "mark_to_market_status": "unavailable_not_inferred_from_completed_trades",
            "sample_caveat": "No executed swaps; quote-based paper returns. Realized-only snapshots omit open-position risk.",
        }
    return {"date": report_date, "goal": "1% per calendar day compounded", "paper_only": True, "sleeves": out}
