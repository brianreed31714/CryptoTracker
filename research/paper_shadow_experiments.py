"""Isolated non-executable SHADOW variants of the three CryptoTracker controls.

Never route orders or modify the baseline strategies. Every variant uses the
same timestamped candidate stream and is scored separately. Returns are
UNPRICED MARK RETURNS, not executable/Jupiter net P&L or portfolio returns.
"""
from __future__ import annotations

import csv
import json
from collections import Counter
import math
import re
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
    novelty_policy: str = "ANY"
    require_organic_flow: bool = False


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
    # Pre-registered prospective tests. Score 12 is an experimental
    # threshold, NOT a validated alpha signal or reason to place orders.
    Variant("xp_diy_name12", "diy_whale", novelty_policy="SCORE12"),
    Variant("xp_diy_organic_flow", "diy_whale", require_organic_flow=True),
    Variant("xp_diy_name12_flow", "diy_whale", novelty_policy="SCORE12", require_organic_flow=True),
    Variant("xp_diy_raunchy", "diy_whale", novelty_policy="RAUNCHY"),
    Variant("xp_diy_raunchy_flow", "diy_whale", novelty_policy="RAUNCHY", require_organic_flow=True),
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



# Deliberately transparent keyword heuristics; not NLP and not measured alpha.
# Coin compounds such as "FARTCOIN" and "CUMROCKET" are intentional matches.
# Some linguistic false positives/negatives remain and should be audited.
_NAME_PATTERNS = {
    "sexual": re.compile(
        r"sex(?!ton)|sexy|porn|xxx|nsfw|nude|naked|dick|cock(?!roach)|"
        r"pussy|tits|boob|cum(?!ber|ulat)|jizz|horny|boner|dildo|milf|"
        r"sperm|orgasm|slut|whore|onlyfans|fap|thot",
        re.IGNORECASE,
    ),
    "profanity": re.compile(
        r"fuck|fuk|fck|shit|bitch|cunt|bastard|wtf|damn|piss|motherf|stfu|bullshit",
        re.IGNORECASE,
    ),
    "toilet": re.compile(
        r"fart|poop|toilet|diarrhea|turd|peepee|puke|vomit|shart|butt(?!on|er)",
        re.IGNORECASE,
    ),
}


def name_categories(candidate):
    """Classify known-at-observation name/symbol text, never future outcomes."""
    raw = " ".join(str(candidate.get(key) or "") for key in ("name", "symbol"))
    if not raw.strip():
        return ()
    return tuple(category for category, pattern in _NAME_PATTERNS.items()
                 if pattern.search(raw))


def qualifies_diy_organic_flow(candidate):
    """Fixed, prospective *stricter* DIY flow hypothesis, not an order trigger.

    No future observations, whale classifications or post-entry prices.
    Missing volume, price or buy-side counts conservatively fail.
    """
    buys = _num(candidate.get("buys_5m"))
    sells = _num(candidate.get("sells_5m"))
    return (
        _num(candidate.get("price_usd")) > 0
        and _num(candidate.get("liquidity")) >= 50_000
        and _num(candidate.get("volume_5m")) >= 5_000
        and buys >= 10
        and buys + sells >= 15
        and _num(candidate.get("buy_sell_ratio_5m")) >= 1.4
        and _num(candidate.get("volume_acceleration")) >= 1.4
    )


def novelty_metadata(candidate):
    """Return research-only fields logged at shadow entry/exit."""
    details = candidate.get("paper_name_novelty")
    score = None
    if isinstance(details, dict):
        try:
            value = float(details.get("name_novelty_score"))
            if math.isfinite(value):
                score = value
        except (TypeError, ValueError):
            pass
    return {
        "name": str(candidate.get("name") or ""),
        "name_novelty_score": score,
        "name_category_flags": "|".join(name_categories(candidate)),
        "organic_flow_at_entry": qualifies_diy_organic_flow(candidate),
        "novelty_study_version": "NOVELTY_FLOW_V1_20261022",
    }

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
    if variant.novelty_policy == "SCORE12":
        value = novelty_metadata(candidate)["name_novelty_score"]
        if value is None or value < 12:
            return False
    elif variant.novelty_policy == "RAUNCHY":
        if not name_categories(candidate):
            return False
    elif variant.novelty_policy != "ANY":
        return False
    if variant.require_organic_flow and not qualifies_diy_organic_flow(candidate):
        return False
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


def _raw_mark_return(row):
    """Parse only finite observed shadow price marks; missing is NOT zero."""
    try:
        value = float(row.get("net_return_pct"))
        return value if math.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def _entry_key(row):
    """Correlate observed BUY/SELL rows without guessing missing identifiers."""
    mint = str(row.get("token_address") or "").strip()
    entered = str(row.get("entry_time") or "").strip()
    return (mint, entered) if mint and entered else None


def _row_date(row):
    return str(row.get("date") or row.get("timestamp") or "")[:10]


def summarize(shadow_csv, report_date):
    """Read-only prospective shadow diagnostics; never executable P&L.

    Zero rows are *not* evidence of zero qualifying opportunities: the
    source may be stale or the new trader version may not be active.
    """
    source = Path(shadow_csv)
    rows = []
    if source.is_file():
        with source.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
    metrics = {}
    novelty_arm_names = frozenset(
        v.name for v in VARIANTS
        if v.base == "diy_whale" and
        (v.novelty_policy != "ANY" or v.require_organic_flow)
    )
    for variant in VARIANTS:
        observed = [r for r in rows if r.get("model") == variant.name
                    and _row_date(r) and _row_date(r) <= report_date]
        buys = [r for r in observed if r.get("action") == "BUY"]
        sells = [r for r in observed if r.get("action") == "SELL"]
        day_buys = [r for r in buys if _row_date(r) == report_date]
        day_sells = [r for r in sells if _row_date(r) == report_date]
        valid = [(r, value) for r in sells
                 if (value := _raw_mark_return(r)) is not None]
        returns = [value for _, value in valid]
        positive = sum(x for x in returns if x > 0)
        negative = -sum(x for x in returns if x < 0)
        entry_counts = Counter(k for r in buys if (k := _entry_key(r)) is not None)
        exit_counts = Counter(k for r in sells if (k := _entry_key(r)) is not None)
        unmatched_entries = sum(max(count - exit_counts[key], 0)
                                for key, count in entry_counts.items())
        unmatched_exits = sum(max(count - entry_counts[key], 0)
                              for key, count in exit_counts.items())
        unkeyed = sum(_entry_key(r) is None for r in buys + sells)
        versioned = sum(r.get("novelty_study_version") == "NOVELTY_FLOW_V1_20261022"
                        for r in observed)
        if not observed:
            status = "NO_ROWS_ACTIVATION_UNVERIFIED"
        elif variant.name in novelty_arm_names and versioned != len(observed):
            status = "MISSING_OR_MIXED_NOVELTY_VERSION_UNVERIFIED"
        else:
            status = "SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION"
        observed_dates = sorted({_row_date(r) for r in observed})
        metrics[variant.name] = {
            "control": variant.base,
            "n_entries_today": len(day_buys),
            "n_entries_since_first_observed": len(buys),
            "n_completed_since_first_observed": len(sells),
            "n_completed_today": len(day_sells),
            "n_valid_raw_mark_exits": len(valid),
            "n_invalid_raw_mark_exits": len(sells) - len(valid),
            "n_negative_raw_mark_exits": sum(x < 0 for x in returns),
            "n_unclosed_observed_entries": unmatched_entries,
            "n_unmatched_exit_rows": unmatched_exits,
            "n_rows_missing_entry_identifiers": unkeyed,
            "n_distinct_mints_closed": len({str(r.get("token_address"))
                                            for r in sells if r.get("token_address")}),
            "first_observed_date": observed_dates[0] if observed_dates else None,
            "last_observed_date": observed_dates[-1] if observed_dates else None,
            "row_observation_status": status,
            "novelty_study_versioned_rows": versioned,
            "raw_mark_avg_return_per_exit_pct": round(sum(returns) / len(returns), 4) if returns else None,
            "raw_mark_win_rate_pct": round(100 * sum(x > 0 for x in returns) / len(returns), 3) if returns else None,
            "raw_mark_profit_factor": round(positive / negative, 4) if negative else None,
            "sample_qualified_for_preliminary_review": (
                len(valid) >= 30 and len(valid) == len(sells)
                and unmatched_exits == 0 and unkeyed == 0
                and status == "SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION"
            ),
            "novelty_policy": variant.novelty_policy,
            "stricter_organic_flow_required": variant.require_organic_flow,
            "entry_name_metadata_observed": sum(bool(r.get("name") or r.get("symbol")) for r in sells),
            "raunchy_category_exits": sum(bool(r.get("name_category_flags")) for r in sells),
            "promotable": False,
        }
    return {
        "date": report_date,
        "mode": "NO_ORDERS_RAW_SHADOW_MARKS_ONLY",
        "not_executable_net_returns": True,
        "not_mark_to_market_portfolio_returns": True,
        "source_present": source.is_file(),
        "source_rows_observed": len(rows),
        "host_runtime_activation_verified": False,
        "variants": metrics,
        "novelty_study": {
            "status": "PROSPECTIVE_UNPRICED_SHADOW_NO_AUTOPROMOTION",
            "control": "xp_diy_control",
            "variants": sorted(novelty_arm_names),
            "minimum_preliminary_exits_per_arm": 30,
            "comparability_note": "Different variants select different entries; raw-mark averages are not paired causal uplifts.",
            "unavailable": ["executable fill costs", "open-position MTM", "true organic-wallet attribution"],
        },
        "limitations": [
            "Zero shadow rows cannot distinguish an inactive variant from no eligible candidates.",
            "Row evidence proves observations were written, NOT that Windows trader digest or EOD activation was verified.",
            "Score >=12 and stricter flow cutoffs are predeclared hypotheses, not retrospectively optimized thresholds.",
            "Raunchy categories use transparent heuristic name/symbol matches; audit ambiguous and false-positive names.",
            "No Jupiter execution, price impact, priority fee, gas, failed-swap, or portfolio-equity modeling in raw shadow trades.",
            "Missing-price positions remain open; no false profit from stale quotes.",
            "30 valid completed exits is only preliminary, never sufficient to promote to a live account.",
            "Counterfactual profits require prospective validation with executable quote-based fill modeling.",
        ],
    }


def render_markdown(report):
    lines = [
        "# CryptoTracker prospective paper-shadow variants — " + report["date"],
        "",
        "**UNPRICED shadow marks, no swaps. Neither net execution returns nor daily portfolio ROI.**",
        "",
        "| Variant | Entry rows today | Exits today | Valid/total exits | Raw win rate | Avg raw mark/exit | Observation status |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for name, row in report["variants"].items():
        avg = row["raw_mark_avg_return_per_exit_pct"]
        win = row["raw_mark_win_rate_pct"]
        avg_text = f"{avg:+.2f}%" if avg is not None else "N/A"
        win_text = f"{win:.1f}%" if win is not None else "N/A"
        lines.append(
            f"| {name} | {row['n_entries_today']} | {row['n_completed_today']} | "
            f"{row['n_valid_raw_mark_exits']}/{row['n_completed_since_first_observed']} | "
            f"{win_text} | {avg_text} | {row['row_observation_status']} |"
        )
    lines.extend([
        "", "## Evidence and safety gate", "",
        "A zero entry or exit count is **not** evidence that the variant was activated or had no opportunities.",
        "Invalid/missing price marks are excluded from return averages, counted separately, and cannot qualify for preliminary review.",
        "All baseline paper models remain unchanged; variants are isolated observations.",
        "No promotion from raw shadow returns. Require independent Windows host attestation, executable quotes, costs, open-position MTM, liquidity, and drawdown validation.",
        "",
    ])
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
