"""Read-only, fail-closed paper open-position liquidation equity contract.

Never queries Jupiter, signs orders, or touches trading state. The caller may
supply independently timestamped READ-ONLY quote observations; otherwise
open-position equity is explicitly UNAVAILABLE, never inferred from spot price.
Only aggregate sleeve values/statuses are published (no token IDs or wallets).

Future quote collector contract (not implemented by this module):
{
  "state_last_cycle_at": "<exact state.json last_cycle_at>",
  "quotes": [{
    "model": "balanced_ev",
    "token_address": "<paper position mint>",
    "entry_token_raw": 123456789,
    "exit_value_usdc": 1.23,
    "observed_at_utc": "2026-10-24T01:00:00+00:00",
    "status": "JUPITER_READ_ONLY_QUOTE"
  }]
}
A Jupiter quote is an estimate, NOT an executable fill or guarantee.
"""
from __future__ import annotations

import json
import math
from datetime import date, datetime, timezone
from pathlib import Path

FOCUS = ("balanced_ev", "runner_hunter", "diy_whale")
QUOTE_STATUS = "JUPITER_READ_ONLY_QUOTE"
MAX_QUOTE_AGE_SECONDS = 120


def finite_number(value):
    if isinstance(value, bool) or value is None or value == "":
        return None
    try:
        result = float(value)
    except (ValueError, TypeError, OverflowError):
        return None
    return result if math.isfinite(result) else None


def positive_raw_amount(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, str) and value.isascii() and value.isdecimal():
        result = int(value)
        return result if result > 0 else None
    return None


def aware_time(value):
    if not isinstance(value, str):
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    return result.astimezone(timezone.utc) if result.tzinfo else None


def _read_dict(path):
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except (OSError, ValueError, TypeError):
        return None


def _blank(reason, *, open_count=None, realized_equity=None):
    return {
        "status": reason,
        "open_positions": open_count,
        "realized_equity_usdc": round(realized_equity, 8) if realized_equity is not None else None,
        "quoted_open_liquidation_value_usdc": None,
        "point_in_time_paper_equity_usdc": None,
        "quote_age_seconds": None,
        "daily_full_portfolio_return_pct": None,
        "inception_full_portfolio_return_pct": None,
        "full_portfolio_drawdown_pct": None,
    }


def assess(state_path, quote_path, report_date, *, now_utc=None,
           max_quote_age_seconds=MAX_QUOTE_AGE_SECONDS):
    """Read-only snapshot readiness, no fabricated MTM on absent/invalid quotes.

    Report-date matching uses the state file's *local* cycle date, without
    inferring its timezone. Quote timestamps must be explicitly offset-aware.
    A matching cycle ID ties quotes to the state without guessing timezone.
    """
    date.fromisoformat(report_date)
    clock = now_utc or datetime.now(timezone.utc)
    if clock.tzinfo is None:
        raise ValueError("now_utc must have an explicit timezone")
    clock = clock.astimezone(timezone.utc)
    if max_quote_age_seconds <= 0:
        raise ValueError("max quote age must be positive")

    state = _read_dict(state_path)
    quotes = _read_dict(quote_path)
    cycle = str((state or {}).get("last_cycle_at") or "")
    models = (state or {}).get("models")
    state_ok = (
        isinstance(models, dict)
        and len(cycle) >= 19
        and cycle[:10] == report_date
        and isinstance(cycle, str)
    )
    quote_rows = quotes.get("quotes") if isinstance(quotes, dict) else None
    quotes_valid = isinstance(quote_rows, list)
    if quotes_valid:
        # A malformed or duplicate quote must not silently win a lookup.
        lookup = {}
        duplicates = set()
        for item in quote_rows:
            if not isinstance(item, dict) or not isinstance(item.get("model"), str):
                continue
            key = item["model"]
            if key in lookup:
                duplicates.add(key)
            lookup[key] = item
    else:
        lookup, duplicates = {}, set()

    result = {
        "schema": "PAPER_QUOTE_LIQUIDATION_READINESS_V1",
        "report_date": report_date,
        "assessed_at_utc": clock.isoformat(),
        "paper_only": True,
        "orders_submitted": False,
        "state_present": state is not None,
        "quote_snapshot_present": quotes is not None,
        "quote_snapshot_cycle_matches": bool(
            quotes_valid and quotes.get("state_last_cycle_at") == cycle and state_ok
        ),
        "quote_max_age_seconds": max_quote_age_seconds,
        "sleeves": {},
        "all_sleeves_point_in_time_equity_available": False,
        "full_portfolio_daily_return_pct": None,
        "full_portfolio_inception_return_pct": None,
        "full_portfolio_drawdown_pct": None,
        "daily_equity_history_status": "UNAVAILABLE_NO_MATCHED_PRIOR_DAY_QUOTE_SNAPSHOT",
        "warning": (
            "Read-only quote estimates, not fills. No open-position mark-to-market "
            "or portfolio returns may be inferred from raw token marks or realized PnL."
        ),
    }
    for name in FOCUS:
        if not state_ok:
            result["sleeves"][name] = _blank(
                "STATE_MISSING_OR_WRONG_REPORT_DATE"
            )
            continue
        model = models.get(name)
        if not isinstance(model, dict):
            result["sleeves"][name] = _blank("MODEL_STATE_MISSING")
            continue
        starting = finite_number(model.get("starting_equity"))
        realized = finite_number(model.get("realized_pnl"))
        if starting is None or starting <= 0 or realized is None:
            result["sleeves"][name] = _blank("INVALID_EQUITY_LEDGER")
            continue
        realized_equity = starting + realized
        if not math.isfinite(realized_equity) or realized_equity < 0:
            result["sleeves"][name] = _blank("INVALID_EQUITY_LEDGER")
            continue
        position = model.get("position")
        if position is None:
            result["sleeves"][name] = {
                **_blank("FLAT_STATE_QUOTE_NOT_REQUIRED", open_count=0,
                         realized_equity=realized_equity),
                "quoted_open_liquidation_value_usdc": 0.0,
                "point_in_time_paper_equity_usdc": round(realized_equity, 8),
            }
            continue
        if not isinstance(position, dict):
            result["sleeves"][name] = _blank(
                "INVALID_POSITION_STATE", open_count=1,
                realized_equity=realized_equity
            )
            continue
        size = finite_number(position.get("size_usdc"))
        raw = positive_raw_amount(position.get("entry_token_raw"))
        mint = position.get("token_address")
        if size is None or size <= 0 or size > realized_equity or raw is None or not isinstance(mint, str) or not mint:
            result["sleeves"][name] = _blank(
                "INVALID_POSITION_PROVENANCE", open_count=1,
                realized_equity=realized_equity
            )
            continue
        if not quotes_valid:
            reason = "MISSING_QUOTE_SNAPSHOT"
        elif quotes.get("state_last_cycle_at") != cycle:
            reason = "QUOTE_STATE_CYCLE_MISMATCH"
        elif name in duplicates:
            reason = "DUPLICATE_MODEL_QUOTES"
        elif name not in lookup:
            reason = "MISSING_LIQUIDATION_QUOTE"
        else:
            quote = lookup[name]
            if (quote.get("token_address") != mint
                    or positive_raw_amount(quote.get("entry_token_raw")) != raw):
                reason = "QUOTE_POSITION_IDENTITY_MISMATCH"
            elif quote.get("status") != QUOTE_STATUS:
                reason = "QUOTE_NOT_READ_ONLY_JUPITER_SUCCESS"
            else:
                value = finite_number(quote.get("exit_value_usdc"))
                observed = aware_time(quote.get("observed_at_utc"))
                if value is None or value <= 0:
                    reason = "INVALID_QUOTE_VALUE"
                elif observed is None:
                    reason = "QUOTE_TIMESTAMP_UNVERIFIED"
                elif not (0 <= (clock - observed).total_seconds() <= max_quote_age_seconds):
                    reason = "QUOTE_STALE_OR_FUTURE"
                else:
                    equity = realized_equity - size + value
                    if not math.isfinite(equity) or equity < 0:
                        reason = "INVALID_COMPUTED_EQUITY"
                    else:
                        result["sleeves"][name] = {
                            **_blank("READ_ONLY_QUOTE_ESTIMATE", open_count=1,
                                     realized_equity=realized_equity),
                            "quoted_open_liquidation_value_usdc": round(value, 8),
                            "point_in_time_paper_equity_usdc": round(equity, 8),
                            "quote_age_seconds": round((clock - observed).total_seconds(), 3),
                        }
                        continue
        result["sleeves"][name] = _blank(
            reason, open_count=1, realized_equity=realized_equity
        )

    result["all_sleeves_point_in_time_equity_available"] = all(
        result["sleeves"][name]["point_in_time_paper_equity_usdc"] is not None
        for name in FOCUS
    )
    return result


def render_markdown(report):
    lines = [
        "# CryptoTracker quote-based paper liquidation readiness — " + report["report_date"],
        "",
        "Read-only, paper-only audit. Quotes are **not** executable fills or actual broker equity.",
        "",
        "| Sleeve | State | Open | Realized-only equity | Quoted liquidation | Point-in-time paper equity |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for name, item in report["sleeves"].items():
        def show(value):
            return "N/A" if value is None else f"${value:.6f}"
        lines.append(
            f"| {name} | {item['status']} | "
            f"{item['open_positions'] if item['open_positions'] is not None else 'N/A'} | "
            f"{show(item['realized_equity_usdc'])} | "
            f"{show(item['quoted_open_liquidation_value_usdc'])} | "
            f"{show(item['point_in_time_paper_equity_usdc'])} |"
        )
    lines.extend([
        "",
        "Full portfolio daily/inception ROI and drawdown: **N/A** until complete, "
        "chronologically comparable quote-backed snapshots exist.",
        "No quote collection is implemented by this module. Missing/stale/failed "
        "quotes always produce N/A rather than a fabricated zero.",
        "No trades, live swaps, strategy changes or risk-limit changes.",
    ])
    return "\n".join(lines) + "\n"


def generate(state_path, quote_path, report_date, destination, *, now_utc=None):
    report = assess(state_path, quote_path, report_date, now_utc=now_utc)
    dest = Path(destination)
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "liquidation_mtm_readiness.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    (dest / "liquidation_mtm_readiness.md").write_text(
        render_markdown(report), encoding="utf-8"
    )
    return report
