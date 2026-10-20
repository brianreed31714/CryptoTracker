"""Isolated non-executable SHADOW variants of the three CryptoTracker controls.

Never route orders or modify the baseline strategies. Every variant uses the
same timestamped candidate stream and is scored separately. Returns are
UNPRICED MARK RETURNS, not executable/Jupiter net P&L or portfolio returns.
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class Variant:
    name: str
    base: str
    risk_policy: str = "ANY"
    confirmations: int = 1
    loss_cooldown_minutes: int = 0
    runner_activate_pct: float | None = None
    trail_pct: float | None = None


VARIANTS = (
    Variant("xp_balanced_cd0", "balanced_ev"),
    Variant("xp_balanced_cd30", "balanced_ev", loss_cooldown_minutes=30),
    Variant("xp_balanced_cd60", "balanced_ev", loss_cooldown_minutes=60),
    Variant("xp_balanced_cd120", "balanced_ev", loss_cooldown_minutes=120),
    Variant("xp_runner_control", "runner_hunter"),
    Variant("xp_runner_confirm2", "runner_hunter", confirmations=2),
    Variant("xp_runner_confirm3", "runner_hunter", confirmations=3),
    Variant("xp_runner_early_trail", "runner_hunter", runner_activate_pct=8.0, trail_pct=5.0),
    Variant("xp_diy_control", "diy_whale"),
    Variant("xp_diy_neutral_only", "diy_whale", risk_policy="NEUTRAL_ONLY"),
    Variant("xp_diy_riskoff_strict", "diy_whale", risk_policy="STRICT_RISK_OFF"),
)
VARIANT_NAMES = frozenset(v.name for v in VARIANTS)


def _num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _time(value):
    try:
        value = datetime.fromisoformat(str(value))
        return value if value.tzinfo is None else value.replace(tzinfo=None)
    except (ValueError, TypeError):
        return None


def update_confirmation(state, token, now, qualifies):
    """Observe at most once per independent 10-second clock interval.

    Only current/past data is considered. A failed observation resets a streak.
    """
    states = state.setdefault("confirmation_state", {})
    item = states.get(token) or {}
    prior = _time(item.get("last_time"))
    if not qualifies:
        states[token] = {"last_time": now.isoformat(), "streak": 0}
        return 0
    if prior is not None and (now - prior).total_seconds() < 10:
        return int(item.get("streak") or 0)
    fresh = prior is not None and 10 <= (now - prior).total_seconds() <= 300
    streak = (int(item.get("streak") or 0) + 1) if fresh else 1
    states[token] = {"last_time": now.isoformat(), "streak": min(3, streak)}
    if len(states) > 500:
        for k in list(states):
            prev = _time(states[k].get("last_time"))
            if prev is None or (now - prev).total_seconds() > 600:
                states.pop(k, None)
    return streak


def qualifies_flow(candidate):
    return (
        str(candidate.get("momentum_state") or "").upper() == "SURGING"
        and _num(candidate.get("volume_acceleration")) >= 1.15
        and _num(candidate.get("buy_sell_ratio_5m")) >= 1.05
        and _num(candidate.get("liquidity")) >= 20_000
        and _num(candidate.get("price_usd")) > 0
    )


def risk_allows(variant, candidate, regime):
    if variant.risk_policy == "ANY":
        return True
    status = str(regime.get("name") or "")
    if variant.risk_policy == "NEUTRAL_ONLY":
        return status == "NEUTRAL"
    if variant.risk_policy == "STRICT_RISK_OFF":
        if status != "RISK_OFF":
            return True
        # Exploratory thresholds, NOT fitted or demonstrated.
        return (
            _num(candidate.get("liquidity")) >= 100_000
            and _num(candidate.get("volume_5m")) >= 10_000
            and _num(candidate.get("buys_5m")) + _num(candidate.get("sells_5m")) >= 25
            and _num(candidate.get("buy_sell_ratio_5m")) >= 1.8
            and _num(candidate.get("volume_acceleration")) >= 1.7
        )
    return False


def eligible(variant, state, candidate, regime, now):
    if not risk_allows(variant, candidate, regime):
        return False
    token = str(candidate.get("token_address") or "")
    if not token:
        return False
    if variant.confirmations > 1:
        item = (state.get("confirmation_state") or {}).get(token) or {}
        last = _time(item.get("last_time"))
        if (last is None or (now - last).total_seconds() > 300
                or int(item.get("streak") or 0) < variant.confirmations):
            return False
    previous_loss = str((state.get("shadow_last_loss") or {}).get(token) or "")
    if previous_loss and variant.loss_cooldown_minutes:
        at = _time(previous_loss)
        if at is not None and 0 <= (now - at).total_seconds() < variant.loss_cooldown_minutes * 60:
            return False
    return True


def effective_spec(variant, base_spec):
    changes = {}
    if variant.runner_activate_pct is not None:
        changes["runner_activate_pct"] = variant.runner_activate_pct
    if variant.trail_pct is not None:
        changes["trail_pct"] = variant.trail_pct
    return replace(base_spec, **changes) if changes else base_spec


def summarize(shadow_csv, report_date):
    """Only compare raw shadow marks to raw shadow marks, never to executable paper."""
    source = Path(shadow_csv)
    rows = []
    if source.is_file():
        with source.open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    metrics = {}
    for variant in VARIANTS:
        sells = [r for r in rows if r.get("model") == variant.name
                 and r.get("action") == "SELL"
                 and str(r.get("date") or r.get("timestamp") or "")[:10] <= report_date]
        day = [r for r in sells
               if str(r.get("date") or r.get("timestamp") or "")[:10] == report_date]
        returns = [_num(r.get("net_return_pct")) for r in sells]
        wins = sum(x > 0 for x in returns)
        positive = sum(x for x in returns if x > 0)
        negative = -sum(x for x in returns if x < 0)
        metrics[variant.name] = {
            "control": variant.base,
            "n_completed_since_first_observed": len(sells),
            "n_completed_today": len(day),
            "raw_mark_avg_return_per_exit_pct": round(sum(returns) / len(returns), 4) if returns else None,
            "raw_mark_win_rate_pct": round(100 * wins / len(returns), 3) if returns else None,
            "raw_mark_profit_factor": round(positive / negative, 4) if negative else None,
            "sample_qualified_for_preliminary_review": len(sells) >= 30,
            "promotable": False,
        }
    return {
        "date": report_date,
        "mode": "NO_ORDERS_RAW_SHADOW_MARKS_ONLY",
        "not_executable_net_returns": True,
        "not_mark_to_market_portfolio_returns": True,
        "source_present": source.is_file(),
        "variants": metrics,
        "limitations": [
            "No Jupiter execution, price impact, priority fee, gas, failed-swap, or portfolio-equity modeling in raw shadow trades.",
            "Missing-price positions remain open; no false profit from stale quotes.",
            "30 completed exits is only preliminary, never sufficient to promote to a live account.",
            "Counterfactual profits require prospective validation with executable quote-based fill modeling.",
        ],
    }


def render_markdown(report):
    lines = [
        "# CryptoTracker prospective paper-shadow variants — " + report["date"],
        "",
        "**UNPRICED shadow marks, no swaps. Neither net execution returns nor daily portfolio ROI.**",
        "",
        "| Variant | Control | Closed today | Closed since observed | Avg raw mark/exit | Preliminary n>=30 |",
        "|---|---|---:|---:|---:|---|",
    ]
    for name, row in report["variants"].items():
        avg = row["raw_mark_avg_return_per_exit_pct"]
        lines.append(
            f"| {name} | {row['control']} | {row['n_completed_today']} | "
            f"{row['n_completed_since_first_observed']} | "
            f"{avg:+.2f}%" + " |" if avg is not None else
            f"| {name} | {row['control']} | {row['n_completed_today']} | "
            f"{row['n_completed_since_first_observed']} | N/A |"
        )
        # append final col in both cases
        lines[-1] += f" {'YES' if row['sample_qualified_for_preliminary_review'] else 'NO'} |"
    lines.extend(["", "## Gate", "",
                  "All baseline paper models remain unchanged; variants are isolated observations.",
                  "No promotion from raw shadow returns. Require independent executable quotes, losses, liquidity, prospective 1% portfolio-goal accounting and drawdown validation.",
                  ""])
    return "\n".join(lines)


def generate(shadow_csv, report_date, destination):
    report = summarize(shadow_csv, report_date)
    folder = Path(destination)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "shadow_experiments.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    (folder / "shadow_experiments.md").write_text(
        render_markdown(report), encoding="utf-8"
    )
    return report
