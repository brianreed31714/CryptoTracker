"""Paper-only observability flags for risky simulated fills and reconciliation.

Never places orders, adjusts positions, or modifies entry/exit decisions.
"""
from __future__ import annotations
import csv
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

SLEEVES = ("balanced_ev", "runner_hunter", "diy_whale")

def number(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def csv_rows(path):
    path = Path(path)
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def audit_paper_day(rows, report_date, published_root=None):
    models = {}
    for name in SLEEVES:
        sells = [r for r in rows if r.get("model") == name
                 and r.get("date") == report_date and r.get("action") == "SELL"]
        buys = [r for r in rows if r.get("model") == name
                and r.get("date") == report_date and r.get("action") == "BUY"]
        failed_tokens = Counter(str(r.get("token_address") or r.get("symbol") or "")
                                for r in sells if number(r.get("realized_pnl_usd")) < 0)
        models[name] = {
            "completed": len(sells),
            "entries": len(buys),
            "negative_estimated_execution_cost_exits": sum(number(r.get("estimated_cost_pct")) < 0 for r in sells),
            "over_5pct_estimated_execution_cost_exits": sum(number(r.get("estimated_cost_pct")) > 5 for r in sells),
            "severe_net_loss_below_minus_20pct": sum(number(r.get("net_return_pct")) < -20 for r in sells),
            "unavailable_helius_exits": sum(
                str(r.get("helius_status") or "") in ("UNAVAILABLE_DISABLED", "HELIUS_UNAVAILABLE_OPTIONAL")
                or "HELIUS_UNAVAILABLE" in str(r.get("data_quality_flags") or "")
                for r in sells
            ),
            "risk_off_entries": sum(r.get("entry_regime") == "RISK_OFF" for r in buys),
            "tokens_with_repeated_loss_exits": {token: count for token, count in failed_tokens.items() if token and count >= 2},
            "execution_warning": "Jupiter executable quote labels are simulation estimates; no swaps were submitted.",
        }
    return {
        "date": report_date,
        "paper_only": True,
        "models": models,
        "reconciliation": reconcile_published_campaign(report_date, models, published_root),
    }

def reconcile_published_campaign(report_date, daily_models, root):
    if root is None:
        return {"status": "not_checked_no_publication_path"}
    root = Path(root)
    current = root / report_date / "campaign_summary.json"
    if not current.exists():
        return {"status": "not_checked_current_campaign_unpublished"}
    previous_dates = sorted(p.name for p in root.iterdir()
                            if p.is_dir() and p.name < report_date
                            and (p / "campaign_summary.json").exists())
    if not previous_dates:
        return {"status": "not_checked_no_previous_campaign"}
    previous_date = previous_dates[-1]
    try:
        today = date.fromisoformat(report_date)
        before = date.fromisoformat(previous_date)
    except ValueError:
        return {"status": "not_checked_invalid_date"}
    if (today - before).days != 1:
        return {"status": "inconclusive_missing_intermediate_publication", "previous_publication": previous_date}
    try:
        current_models = {m["model"]: m for m in json.loads(current.read_text())["models"]}
        prev_models = {m["model"]: m for m in json.loads((root / previous_date / "campaign_summary.json").read_text())["models"]}
    except (KeyError, ValueError, OSError, TypeError):
        return {"status": "not_checked_invalid_campaign_summary"}
    details = {}
    for name in SLEEVES:
        old = (prev_models.get(name) or {}).get("all") or {}
        now = (current_models.get(name) or {}).get("all") or {}
        if "n" not in old or "n" not in now:
            continue
        count_delta = int(now["n"]) - int(old["n"])
        observed = daily_models[name]["completed"]
        pnl_delta = number(now.get("realized_pnl_usd")) - number(old.get("realized_pnl_usd"))
        details[name] = {
            "daily_completed": observed,
            "campaign_completed_delta": count_delta,
            "count_reconciled": count_delta == observed,
            "campaign_pnl_delta_usd": round(pnl_delta, 8),
            "note": "Mismatch can be caused by historical backfill or corrections; investigate rather than attributing to today's trades.",
        }
    return {
        "status": "mismatch_review_required" if any(not x["count_reconciled"] for x in details.values()) else "counts_reconciled",
        "previous_publication": previous_date,
        "by_sleeve": details,
    }
