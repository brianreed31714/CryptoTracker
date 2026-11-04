"""Fail-closed, date-scoped paper-strategy EOD Pushover summary.

Never infer portfolio ROI from realized-only returns or substitute zero for missing
evidence. The raw paper trade log supplies wins/losses; published summaries
supply modeled sleeve returns. No network calls or trading side effects.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

SLEEVES = (("balanced_ev", "Core"), ("runner_hunter", "Runner Hunter"), ("diy_whale", "DIY Whale"))


def format_paper_sleeves(root, day):
    base = Path(root) / "published" / "daily" / day
    try:
        summary = json.loads((base / "paper_summary.json").read_text(encoding="utf-8"))
        if summary.get("date") != day:
            raise ValueError("summary date mismatch")
        sleeves = summary["goal_1pct_daily"]["sleeves"]
        with (base / "raw" / "paper_trades.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
    except (OSError, ValueError, KeyError, TypeError, csv.Error):
        return ["PAPER STRATEGIES: MISSING — dated evidence unavailable; QC required"]

    output = ["PAPER STRATEGIES (MODELED, realized-only):"]
    for key, label in SLEEVES:
        metrics = sleeves.get(key)
        if not isinstance(metrics, dict):
            output.append(f"• {label}: MISSING — summary sleeve absent")
            continue
        sells = [r for r in rows if r.get("date") == day and r.get("model") == key and r.get("action") == "SELL"]
        wins = sum(1 for r in sells if _number(r.get("net_return_pct")) is not None and float(r["net_return_pct"]) > 0)
        losses = sum(1 for r in sells if _number(r.get("net_return_pct")) is not None and float(r["net_return_pct"]) < 0)
        flats = sum(1 for r in sells if _number(r.get("net_return_pct")) == 0)
        count = metrics.get("daily_completed")
        counts_ok = type(count) is int and count == len(sells) and wins + losses + flats == len(sells)
        day_pct = _number(metrics.get("daily_realized_equity_return_pct"))
        inception = _number(metrics.get("since_inception_realized_equity_return_pct"))
        drawdown = _number(metrics.get("since_inception_realized_equity_drawdown_pct"))
        pnl = _number(metrics.get("daily_realized_pnl_usd"))
        if not counts_ok or any(v is None for v in (day_pct, inception, drawdown, pnl)):
            output.append(f"• {label}: MISSING / RECONCILIATION REQUIRED — count or metric mismatch")
            continue
        output.append(
            f"• {label}: day {day_pct:+.2f}% | inception {inception:+.2f}% | DD {drawdown:.2f}%"
        )
        output.append(
            f"  {len(sells)} exits | W/L/flat {wins}/{losses}/{flats} | win {wins / len(sells) * 100:.0f}%"
            if sells else "  0 exits | W/L/flat 0/0/0 | win rate N/A"
        )
        output.append(f"  Realized paper P/L ${pnl:+.4f}")
    output.append("Invested-capital portfolio ROI: MISSING (open-position valuation unverified)")
    output.append("QC: modeled paper data; no executed swaps or independently verified device receipt")
    return output


def _number(value):
    if isinstance(value, bool):
        return None
    import math
    try:
        parsed = float(value)
    except (ValueError, TypeError, OverflowError):
        return None
    return parsed if math.isfinite(parsed) else None
