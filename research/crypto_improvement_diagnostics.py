"""Read-only CryptoTracker improvement diagnostics for the three paper sleeves.

Uses dated BUY/SELL observations; counterfactual exclusions are HYPOTHESES,
not executable backtests. There is NO trading, order API, configuration write,
or change to the existing entry/exit rules in this module.
"""
from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

SLEEVES = ("balanced_ev", "runner_hunter", "diy_whale")
STOPS_PCT = {"balanced_ev": -5.0, "runner_hunter": -7.0, "diy_whale": -8.0}
COOLDOWNS_MINUTES = (30, 60, 120)
REPORT_VERSION = 1


def _num(value, fallback=None):
    try:
        n = float(value)
        return n if math.isfinite(n) else fallback
    except (TypeError, ValueError):
        return fallback


def _date(value):
    return str(value or "")[:10]


def _time(value):
    try:
        result = datetime.fromisoformat(str(value or ""))
        return result if result.tzinfo is None else result.replace(tzinfo=None)
    except ValueError:
        return None


def read_rows(path):
    path = Path(path)
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _trade_key(row):
    return (
        str(row.get("model") or ""),
        str(row.get("token_address") or ""),
        str(row.get("entry_time") or ""),
    )


def _sells(rows, model, through_date):
    return sorted(
        (r for r in rows if r.get("model") == model
         and str(r.get("action") or "").upper() == "SELL"
         and _date(r.get("date") or r.get("timestamp")) <= through_date),
        key=lambda r: str(r.get("timestamp") or ""),
    )


def _aggregate(sells):
    net = [_num(r.get("realized_pnl_usd")) for r in sells]
    returns = [_num(r.get("net_return_pct")) for r in sells]
    good = [x for x in net if x is not None]
    ret_good = [x for x in returns if x is not None]
    pos = sum(max(x, 0.0) for x in good)
    neg = -sum(min(x, 0.0) for x in good)
    return {
        "completed": len(sells),
        "valid_pnl_rows": len(good),
        "net_pnl_usd": round(sum(good), 8),
        "win_rate_pct": round(100 * sum(x > 0 for x in good) / len(good), 4) if good else None,
        "avg_net_return_per_trade_pct": round(sum(ret_good) / len(ret_good), 4) if ret_good else None,
        "profit_factor": round(pos / neg, 4) if neg else None,
    }


def _cooldown_opportunities(all_rows, through_date, model):
    """Retrospective reentries after a losing exit. NOT a valid alternative P&L."""
    events = sorted(
        (r for r in all_rows if r.get("model") == model
         and str(r.get("action") or "").upper() in {"BUY", "SELL"}
         and _date(r.get("date") or r.get("timestamp")) <= through_date),
        key=lambda r: str(r.get("timestamp") or ""),
    )
    previous_loss = {}
    seen_buys = set()
    blocked = {minutes: [] for minutes in COOLDOWNS_MINUTES}
    for r in events:
        token = str(r.get("token_address") or "")
        moment = _time(r.get("timestamp"))
        if not token or moment is None:
            continue
        if r.get("action") == "SELL":
            pnl = _num(r.get("realized_pnl_usd"))
            if pnl is not None:
                if pnl < 0:
                    previous_loss[token] = moment
                else:
                    previous_loss.pop(token, None)
        elif r.get("action") == "BUY" and token in previous_loss:
            # Duplicate ingestion of the same event must not multiply counts.
            k = (token, str(r.get("timestamp")), str(r.get("entry_time")))
            if k in seen_buys:
                continue
            seen_buys.add(k)
            delta = (moment - previous_loss[token]).total_seconds() / 60
            for minutes in COOLDOWNS_MINUTES:
                if 0 <= delta < minutes:
                    blocked[minutes].append(_trade_key(r))
    return {str(k): {
        "observed_reentries_after_loss": len(v),
        "trade_keys": v[:20],
        "interpretation": "retrospective entry count, not prevented losses or a causal simulation",
    } for k, v in blocked.items()}


def _execution(sells, stop_pct):
    warn = []
    severe = []
    absent = 0
    for row in sells:
        cost = _num(row.get("estimated_cost_pct"))
        net = _num(row.get("net_return_pct"))
        quote = str(row.get("exit_quote_status") or "")
        if cost is not None and (cost < 0 or cost > 5):
            warn.append({"token": row.get("symbol"), "estimated_cost_pct": cost,
                         "timestamp": row.get("timestamp")})
        if row.get("reason") == "STOP" and net is not None and net < stop_pct - 3:
            severe.append({"token": row.get("symbol"), "net_return_pct": net,
                           "configured_stop_pct": stop_pct})
        if not quote.startswith("EXECUTABLE_JUPITER"):
            absent += 1
    return {
        "negative_or_over_5pct_estimated_cost_count": len(warn),
        "estimated_cost_outlier_samples": warn[:10],
        "stops_exceeding_threshold_by_more_than_3pp": severe[:10],
        "exit_quotations_missing_or_fallback_count": absent,
        "qualification": "Quotes are estimates, not settled swaps; large stop overruns and negative estimated costs require investigation.",
    }


def _profit_capture(sells):
    has_peak = 0
    ended_below_zero_after_8pct_peak = 0
    captured = []
    for row in sells:
        peak = _num(row.get("peak_return_pct"))
        raw = _num(row.get("raw_return_pct"))
        net = _num(row.get("net_return_pct"))
        if peak is None or raw is None or peak <= 0:
            continue
        has_peak += 1
        if peak >= 8 and net is not None and net < 0:
            ended_below_zero_after_8pct_peak += 1
        if raw > 0:
            captured.append(min(100.0, max(0.0, 100.0 * raw / peak)))
    return {
        "exits_with_positive_observed_peak": has_peak,
        "losing_exits_after_at_least_8pct_observed_peak": ended_below_zero_after_8pct_peak,
        "avg_positive_raw_peak_capture_pct": round(sum(captured) / len(captured), 3) if captured else None,
        "caveat": "Observed price extrema are sampled; peak capture is price-based, before execution cost.",
    }


def analyze(trades, report_date, initial_equity_usdc=15.0):
    """Generate an independently reviewable, deterministic, read-only audit."""
    datetime.strptime(report_date, "%Y-%m-%d")
    equity = _num(initial_equity_usdc)
    if equity is None or equity <= 0:
        raise ValueError("Initial research equity must be positive.")
    result = {
        "date": report_date,
        "version": REPORT_VERSION,
        "mode": "PAPER_READ_ONLY",
        "goal_daily_portfolio_return_pct": 1.0,
        "full_mark_to_market_available": False,
        "experiments_are": "historical diagnostics, not proven strategy changes",
        "promotion_allowed": False,
        "sleeves": {},
        "additional_research": {
            "runner_hunter": "Test independently timed 2- and 3-confirmation continuation with future executable quotes.",
            "diy_whale": "Test NEUTRAL-only versus strict RISK_OFF organic-flow criteria in prospectively isolated variants.",
            "balanced_ev": "Test 30/60/120-minute loss cooldown in parallel independent variants.",
            "profit_capture": "Test stage exits and narrower trailing rules against the frozen baseline using executable exit estimates.",
            "capital": "No scaling before adequate liquidity/slippage validation and stable prospective net portfolio returns.",
        },
    }
    for model in SLEEVES:
        all_exits = _sells(trades, model, report_date)
        daily_exits = [r for r in all_exits if _date(r.get("date") or r.get("timestamp")) == report_date]
        riskoff = [r for r in all_exits if r.get("entry_regime") == "RISK_OFF"]
        neutral = [r for r in all_exits if r.get("entry_regime") == "NEUTRAL"]
        today = _aggregate(daily_exits)
        inception = _aggregate(all_exits)
        # This figure is intentionally NOT a realized-equity daily return:
        # starting account equity may have changed and open positions are omitted.
        gross_daily_pnl_to_start = today["net_pnl_usd"] / equity * 100
        result["sleeves"][model] = {
            "daily": today,
            "inception": inception,
            "daily_realized_pnl_as_pct_of_initial_capital_not_portfolio_return": round(gross_daily_pnl_to_start, 5),
            "regime_selection": {
                "risk_off": _aggregate(riskoff),
                "neutral": _aggregate(neutral),
                "possible_avoided_historical_risk_off_losses_usd_not_causal": round(-sum(
                    _num(x.get("realized_pnl_usd"), 0) for x in riskoff
                ), 8),
                "limitation": "Removing trades changes capital availability, future signals, and the alternative equity path.",
            },
            "cooldown_candidates": _cooldown_opportunities(trades, report_date, model),
            "execution": _execution(daily_exits, STOPS_PCT[model]),
            "exit_capture": _profit_capture(daily_exits),
            "eligibility": {
                "minimum_prospective_exits_for_preliminary_review": 30,
                "qualification": "No promotion on these retrospective observations.",
            },
        }
    return result


def render_markdown(audit):
    lines = [
        f"# CryptoTracker sleeve-improvement diagnostics — {audit['date']}",
        "",
        "**Paper-only read-only audit. No entry/exit changes. No live orders.**",
        "Target: +1.00% per calendar day on mark-to-market portfolio equity; unavailable until verified open-position valuation exists.",
        "",
        "| Sleeve | Daily exits | Daily realized P&L | Inception exits | Inception realized P&L | Avg net/trade inception |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, row in audit["sleeves"].items():
        day = row["daily"]
        all_ = row["inception"]
        avg = all_["avg_net_return_per_trade_pct"]
        lines.append(f"| {name} | {day['completed']} | \${day['net_pnl_usd']:+.4f} | {all_['completed']} | \${all_['net_pnl_usd']:+.4f} | {avg:+.2f}% |" if avg is not None else
                     f"| {name} | {day['completed']} | \${day['net_pnl_usd']:+.4f} | {all_['completed']} | \${all_['net_pnl_usd']:+.4f} | N/A |")
    lines.extend(["", "## Investigation flags", ""])
    for name, row in audit["sleeves"].items():
        ex = row["execution"]
        pc = row["exit_capture"]
        cd = row["cooldown_candidates"]
        off = row["regime_selection"]["risk_off"]
        lines.append(
            f"- **{name}**: {ex['negative_or_over_5pct_estimated_cost_count']} unusual daily cost estimates; "
            f"{len(ex['stops_exceeding_threshold_by_more_than_3pp'])} severe stop overruns; "
            f"{pc['losing_exits_after_at_least_8pct_observed_peak']} gains-to-loss reversals; "
            f"{cd['60']['observed_reentries_after_loss']} observed reentries within 60m of a loss; "
            f"RISK_OFF {off['completed']} completed exits / \${off['net_pnl_usd']:+.4f} inception."
        )
    lines.extend(["", "## Evaluation policy", "",
                  "Risk-off exclusions and cooldown counts are retrospective selection diagnostics, not backtests.",
                  "Runner persistence requires independent time-ordered observations. Profit exits require modeled executable routes.",
                  "Keep Balanced EV, Runner Hunter and DIY Whale frozen as controls; compare independent prospective paper variants.",
                  "Do not increase trade size or enable live swapping without verified liquidity, slippage, out-of-sample returns and drawdowns.",
                  "A merged GitHub change is not verified on the Windows trading host.",
                  ""])
    return "\n".join(lines)


def generate(trades_path, report_date, destination, initial_equity_usdc=15.0):
    """Write only sanitized aggregated statistics; no wallet or credential data."""
    data = analyze(read_rows(trades_path), report_date, initial_equity_usdc)
    target = Path(destination)
    target.mkdir(parents=True, exist_ok=True)
    (target / "improvement_diagnostics.json").write_text(
        json.dumps(data, indent=2, sort_keys=True), encoding="utf-8"
    )
    (target / "improvement_diagnostics.md").write_text(
        render_markdown(data), encoding="utf-8"
    )
    return data
