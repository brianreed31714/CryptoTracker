"""Experimental runner sleeve: pure, paper-only signal scoring.

This module never submits orders. Integrate with the existing market-data,
paper ledger, and EOD evidence pipeline only after review.
All percentages are fractional (0.10 = 10%).
"""
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class RunnerSnapshot:
    token: str
    age_minutes: float
    change_5m: float
    change_15m: float
    volume_5m_usd: float
    liquidity_usd: float
    buys_5m: int
    sells_5m: int
    spread_pct: float
    price_impact_pct: float
    data_age_seconds: float
    suspicious: bool = False

@dataclass(frozen=True)
class RunnerDecision:
    eligible: bool
    score: float
    reason: str

def evaluate_runner(s: RunnerSnapshot) -> RunnerDecision:
    """Exploratory thresholds, not validated or optimized."""
    if s.suspicious or s.data_age_seconds > 90:
        return RunnerDecision(False, 0, "unsafe_or_stale")
    if s.liquidity_usd < 15000 or s.volume_5m_usd < 5000:
        return RunnerDecision(False, 0, "insufficient_liquidity_or_volume")
    if s.spread_pct > 0.05 or s.price_impact_pct > 0.05:
        return RunnerDecision(False, 0, "unexecutable_spread_or_impact")
    if s.age_minutes < 2 or s.age_minutes > 240:
        return RunnerDecision(False, 0, "outside_age_window")
    if s.buys_5m + s.sells_5m < 12:
        return RunnerDecision(False, 0, "insufficient_activity")
    buy_ratio = s.buys_5m / max(1, s.buys_5m + s.sells_5m)
    score = (
        30 * min(max(s.change_5m, 0) / .15, 1)
        + 20 * min(max(s.change_15m, 0) / .35, 1)
        + 20 * min(max(buy_ratio - .5, 0) / .3, 1)
        + 15 * min(s.volume_5m_usd / max(s.liquidity_usd, 1), 1)
        + 15 * min(s.buys_5m / 50, 1)
    )
    return RunnerDecision(score >= 55, round(score, 2),
                          "runner_candidate" if score >= 55 else "weak_momentum")
