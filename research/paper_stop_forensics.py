"""Read-only paper stop-loss gap and quote-cost forensics.

A STOP threshold is a trigger, not an executed exit guarantee. This audit
uses the already-recorded paper trade ledger; it never fetches quotes, trades,
changes stop settings, or claims to know quote age without a timestamp.
"""
from __future__ import annotations

import csv
import json
import math
from datetime import datetime
from pathlib import Path

STOP_PCT = {"balanced_ev": -5.0, "runner_hunter": -7.0, "diy_whale": -8.0}


def number(value):
    if isinstance(value, bool):
        return None
    try:
        n = float(value)
        return n if math.isfinite(n) else None
    except (ValueError, TypeError, OverflowError):
        return None


def duration_minutes(start, end):
    try:
        a = datetime.fromisoformat(str(start))
        b = datetime.fromisoformat(str(end))
        if (a.tzinfo is None) != (b.tzinfo is None):
            return None
        seconds = (b - a).total_seconds()
        return round(seconds / 60, 3) if seconds >= 0 else None
    except (TypeError, ValueError):
        return None


def analyze(rows, report_date):
    models = {}
    for model, trigger in STOP_PCT.items():
        exits = [r for r in rows
                 if r.get("date") == report_date
                 and r.get("model") == model
                 and r.get("action") == "SELL"]
        stops = [r for r in exits if str(r.get("reason") or "").startswith("STOP")]
        valid = []
        invalid = 0
        for row in stops:
            raw = number(row.get("raw_return_pct"))
            net = number(row.get("net_return_pct"))
            cost = number(row.get("estimated_cost_pct"))
            pnl = number(row.get("realized_pnl_usd"))
            if raw is None or net is None or cost is None or pnl is None:
                invalid += 1
                continue
            # A gap below the trigger and additional quote cost are distinct.
            # An estimated negative cost is possible and must be flagged.
            valid.append({
                "symbol": str(row.get("symbol") or "")[:24],
                "raw_return_pct": round(raw, 6),
                "estimated_net_return_pct": round(net, 6),
                "estimated_cost_pct": round(cost, 6),
                "raw_stop_overrun_pp": round(max(0, trigger - raw), 6),
                "net_stop_overrun_pp": round(max(0, trigger - net), 6),
                "estimated_pnl_usdc": round(pnl, 8),
                "holding_minutes": duration_minutes(row.get("entry_time"), row.get("timestamp")),
                "entry_regime": str(row.get("entry_regime") or "")[:20],
                "exit_quote_status": str(row.get("exit_quote_status") or "")[:40],
                "quote_timestamp_verified": False,
            })
        worst = sorted(valid, key=lambda r: r["estimated_net_return_pct"])[:3]
        models[model] = {
            "configured_stop_trigger_pct": trigger,
            "all_completed_exits": len(exits),
            "stop_exits": len(stops),
            "valid_stop_exits": len(valid),
            "invalid_stop_marks": invalid,
            "stop_raw_gap_count": sum(r["raw_stop_overrun_pp"] > 0 for r in valid),
            "stop_net_overrun_count": sum(r["net_stop_overrun_pp"] > 0 for r in valid),
            "stop_over_20pct_net_loss_count": sum(r["estimated_net_return_pct"] < -20 for r in valid),
            "negative_estimated_quote_cost_count": sum(r["estimated_cost_pct"] < 0 for r in valid),
            "quote_timestamp_verified_count": 0,
            "worst_stops": worst,
        }
    return {
        "schema": "PAPER_STOP_FORENSICS_V1",
        "report_date": report_date,
        "paper_only": True,
        "quote_age_status": "UNVERIFIED_NO_QUOTE_OBSERVED_AT_IN_TRADE_LEDGER",
        "execution_note": (
            "All exits are simulated Jupiter quote estimates, not executed fills. "
            "Holding duration is NOT quote age; no route, fill, or timestamp provenance inferred."
        ),
        "models": models,
    }


def generate(csv_path, report_date, destination):
    try:
        with Path(csv_path).open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
    except (OSError, ValueError):
        rows = []
    report = analyze(rows, report_date)
    dest = Path(destination)
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "stop_forensics.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    lines = [
        f"# CryptoTracker simulated stop-overrun forensics — {report_date}",
        "",
        "| Sleeve | Stop trigger | Stops | Invalid | Raw gap | Net overrun | Worst net stop |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, data in report["models"].items():
        worst = data["worst_stops"][0] if data["worst_stops"] else None
        label = f"{worst['symbol']} {worst['estimated_net_return_pct']:.2f}%" if worst else "N/A"
        lines.append(
            f"| {name} | {data['configured_stop_trigger_pct']:.1f}% | "
            f"{data['stop_exits']} | {data['invalid_stop_marks']} | "
            f"{data['stop_raw_gap_count']} | {data['stop_net_overrun_count']} | {label} |"
        )
    lines.extend([
        "",
        "**No quote-observation timestamp is present in the trade ledger.** "
        "Holding minutes are not quote age. Stop triggers do not guarantee fills. "
        "Simulated costs and Jupiter labels do not establish executable returns.",
        "",
        "No orders, live swaps, baseline changes or automatic promotion.",
    ])
    (dest / "stop_forensics.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report
