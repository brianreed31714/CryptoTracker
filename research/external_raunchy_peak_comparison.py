"""Read-only descriptive external raunchy-ticker comparison; NEVER trading P&L.

The selected SmugCalls stream contains future peaks but no executable exit path,
liquidity, 5-minute buys/sells, or DIY Whale entry/exit eligibility. A peak is
an upper outcome observation, not a fill, ROI, or predictive backtest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from datetime import datetime, timezone

from research.external_raunchy_flow_audit import PATTERNS


def _summary(rows):
    n = len(rows)
    with_peak = [r for r in rows if r["peak"] is not None]
    hits = sum(r["peak"] >= 2 for r in with_peak)
    return {
        "n": n,
        "valid_peak_observations": len(with_peak),
        "future_peak_at_least_2x": hits,
        "future_peak_at_least_2x_pct": round(100 * hits / len(with_peak), 4) if with_peak else None,
    }


def _contrast(rows):
    hit = _summary([r for r in rows if r["raunchy"]])
    other = _summary([r for r in rows if not r["raunchy"]])
    result = {"raunchy_ticker": hit, "other_ticker": other,
              "difference_percentage_points": None, "approx_normal_95pct_ci_pp": None}
    if hit["valid_peak_observations"] and other["valid_peak_observations"]:
        n1, n0 = hit["valid_peak_observations"], other["valid_peak_observations"]
        p1 = hit["future_peak_at_least_2x"] / n1
        p0 = other["future_peak_at_least_2x"] / n0
        delta = p1 - p0
        se = math.sqrt(p1 * (1 - p1) / n1 + p0 * (1 - p0) / n0)
        result["difference_percentage_points"] = round(100 * delta, 4)
        result["approx_normal_95pct_ci_pp"] = [round(100 * (delta - 1.96 * se), 4),
                                               round(100 * (delta + 1.96 * se), 4)]
    return result


def analyze(path, start="2026-04-29", end="2026-10-29"):
    source = Path(path)
    seen = set()
    rows = []
    total = 0
    invalid = 0
    with source.open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            total += 1
            item = json.loads(line)
            try:
                day = datetime.fromtimestamp(int(item["t"]), timezone.utc).date().isoformat()
            except (KeyError, ValueError, TypeError, OverflowError, OSError):
                invalid += 1
                continue
            if not start <= day <= end:
                continue
            mint = str(item.get("mint") or "")
            if not mint or mint in seen:
                continue
            seen.add(mint)
            sym = str(item.get("sym") or "")
            try:
                peak = float(item["peak"])
                if not math.isfinite(peak) or peak < 0:
                    peak = None
            except (KeyError, TypeError, ValueError):
                peak = None
            try:
                cap = float(item["mc"])
                if not math.isfinite(cap) or cap < 0:
                    cap = None
            except (KeyError, TypeError, ValueError):
                cap = None
            rows.append({"month": day[:7], "raunchy": any(p.search(sym) for p in PATTERNS),
                         "categories": [i for i, p in enumerate(PATTERNS) if p.search(sym)],
                         "peak": peak, "market_cap": cap})
    months = sorted({r["month"] for r in rows})
    by_month = {m: _contrast([r for r in rows if r["month"] == m]) for m in months}
    periods = {
        "jul_aug_development_calendar": _contrast([r for r in rows if r["month"] in ("2026-07", "2026-08")]),
        "sep_oct_later_calendar_slice": _contrast([r for r in rows if r["month"] in ("2026-09", "2026-10")]),
    }
    bins = (0, 10000, 20000, 50000, float("inf"))
    weighted_control = 0.0
    covered = 0
    for month in months:
        for lo, hi in zip(bins[:-1], bins[1:]):
            stratum = [r for r in rows if r["month"] == month and
                       r["market_cap"] is not None and lo <= r["market_cap"] < hi and
                       r["peak"] is not None]
            h = [r for r in stratum if r["raunchy"]]
            o = [r for r in stratum if not r["raunchy"]]
            if h and o:
                covered += len(h)
                weighted_control += len(h) * sum(r["peak"] >= 2 for r in o) / len(o)
    return {
        "status": "DESCRIPTIVE_FUTURE_PEAK_NOT_TRADING_BACKTEST",
        "source": "Smurfetc/solana-memecoin-calls-dataset/calls.jsonl",
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "requested_window": [start, end],
        "source_rows": total, "invalid_timestamps": invalid,
        "unique_window_mints": len(rows),
        "overall": _contrast(rows), "by_month": by_month,
        "chronological_calendar_slices": periods,
        "category_overlap_allowed": {
            name: _summary([r for r in rows if i in r["categories"]])
            for i, name in enumerate(("sexual", "profanity", "toilet"))
        },
        "month_and_market_cap_standardized_control_rate_pct": (
            round(100 * weighted_control / covered, 4) if covered else None
        ),
        "standardized_covered_raunchy_count": covered,
        "flow_gate": "MISSING", "executable_net_roi_pct": None,
        "portfolio_drawdown_pct": None, "promotable": False,
        "limitations": [
            "Ticker-only keyword screening; token full names unavailable",
            "Selected caller stream, not all token launches or our scanner universe",
            "Peak is retrospective future ceiling, not executable fill or exit return",
            "Recent calls have less follow-up time; right censoring is not adjusted",
            "No 5m buy/sell counts, volume, acceleration, liquidity, or DIY baseline replay",
            "Unadjusted confidence interval assumes independent calls and ignores multiple testing",
            "Calendar slice is descriptive, not prospective out-of-sample profitability",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="external_raunchy_peak_comparison.json")
    parser.add_argument("--start", default="2026-04-29")
    parser.add_argument("--end", default="2026-10-29")
    args = parser.parse_args()
    result = analyze(args.input, args.start, args.end)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "by_month"}, indent=2))
