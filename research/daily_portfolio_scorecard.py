#!/usr/bin/env python3
"""Paper-only portfolio scorecard. Never interprets trade-average returns as equity returns."""
from __future__ import annotations
import csv
import json
import math
from datetime import date
from pathlib import Path

SLEEVES = ("balanced_ev", "runner_hunter", "diy_whale")
TARGET_DAILY_PCT = 1.0

def _float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

def scorecard(rows, *, as_of=None, target_pct=TARGET_DAILY_PCT):
    """rows: model,date,equity. Equity MUST include marked open positions.

    Missing/unmarked equity is not silently replaced with realized equity.
    Consecutive observed days only; no invented daily returns on missing dates.
    """
    as_of = as_of or date.today().isoformat()
    if date.fromisoformat(as_of).isoformat() != as_of:
        raise ValueError("as_of must be an ISO calendar date")
    out = {"as_of": as_of, "target_daily_pct": target_pct, "paper_only": True, "sleeves": {}}
    for model in SLEEVES:
        by_date = {}
        conflicting_dates = set()
        excluded_future_rows = 0
        excluded_invalid_rows = 0
        for row in rows:
            if not isinstance(row, dict) or row.get("model") != model:
                continue
            day = row.get("date")
            try:
                if not isinstance(day, str) or date.fromisoformat(day).isoformat() != day:
                    raise ValueError("invalid date")
            except ValueError:
                excluded_invalid_rows += 1
                continue
            if day > as_of:
                excluded_future_rows += 1
                continue
            equity = _float(row.get("equity"))
            if equity is None or not math.isfinite(equity) or equity <= 0:
                excluded_invalid_rows += 1
                continue
            if day in conflicting_dates:
                continue
            if day in by_date and by_date[day] != equity:
                conflicting_dates.add(day)
                del by_date[day]
                continue
            by_date[day] = equity
        dates = sorted(by_date)
        daily = []
        for prev, cur in zip(dates, dates[1:]):
            # Do not present multi-day jumps as a one-day return.
            if (date.fromisoformat(cur) - date.fromisoformat(prev)).days != 1:
                continue
            ret = 100 * (by_date[cur] / by_date[prev] - 1)
            daily.append({"date": cur, "return_pct": round(ret, 4), "target_met": ret >= target_pct, "gap_pp": round(ret-target_pct, 4)})
        inception = (100*(by_date[dates[-1]]/by_date[dates[0]]-1)) if len(dates)>=2 else None
        peak, max_dd = None, 0.0
        for d in dates:
            v = by_date[d]
            peak = max(peak or v, v)
            max_dd = max(max_dd, 100*(peak-v)/peak)
        n = len(daily)
        out["sleeves"][model] = {
            "first_equity_date": dates[0] if dates else None,
            "latest_equity_date": dates[-1] if dates else None,
            "stale": not dates or dates[-1] != as_of,
            "excluded_future_rows": excluded_future_rows,
            "excluded_invalid_rows": excluded_invalid_rows,
            "conflicting_equity_dates": sorted(conflicting_dates),
            "daily_portfolio_return_pct": daily[-1]["return_pct"] if daily and daily[-1]["date"]==as_of else None,
            "daily_target_gap_pp": daily[-1]["gap_pp"] if daily and daily[-1]["date"]==as_of else None,
            "since_inception_portfolio_return_pct": round(inception,4) if inception is not None else None,
            "observed_target_days": sum(x["target_met"] for x in daily),
            "observed_daily_return_days": n,
            "target_hit_rate_pct": round(100*sum(x["target_met"] for x in daily)/n,2) if n else None,
            "compounded_1pct_target_return_pct": round(100*((1+target_pct/100)**n-1),4) if n else None,
            "max_observed_equity_drawdown_pct": round(max_dd,4) if dates else None,
            "warning": "Requires verified daily mark-to-market equity including open positions; absent dates are not estimated.",
        }
    return out

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--equity-daily-csv", required=True, help="Verified daily mark-to-market snapshots: model,date,equity")
    p.add_argument("--as-of", default=date.today().isoformat())
    p.add_argument("--output", required=True)
    a=p.parse_args()
    with open(a.equity_daily_csv, newline="", encoding="utf-8") as f:
        rows=list(csv.DictReader(f))
    report=scorecard(rows, as_of=a.as_of)
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    Path(a.output).write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")

if __name__=="__main__":
    main()
