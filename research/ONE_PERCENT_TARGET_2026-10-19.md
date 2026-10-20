# Paper research: 1% daily portfolio target (2026-10-19)

**Decision:** All three sleeves remain paper-only. +1% per day is an aspirational performance benchmark, not a promised return or an average-per-trade threshold.

## Reporting contract
Run `python -m unittest test_daily_portfolio_scorecard.py` and `python research/daily_portfolio_scorecard.py --equity-daily-csv <verified_daily_mtm.csv> --as-of YYYY-MM-DD --output <scorecard.json>`. Input columns: `model,date,equity`. Equity must represent cash plus realistically marked open paper positions **net of liabilities** at a consistent cutoff. Do not substitute realized-only balances or trade averages.

Publish daily portfolio return, difference from +1% in percentage points, since-inception return, target-hit days/rate, compounded +1% benchmark, and equity drawdown. Missing mark-to-market evidence produces null values and a warning, not fabricated numbers. The scorecard tracks observed consecutive calendar days; if a market-day-only convention is chosen later, explicitly version it and change the benchmark denominator consistently.

## Planned follow-up work (not implemented by this PR)
1. Instrument end-of-day marked open-position equity, freshness/coverage checks, and publishing the generated scorecard as an allowlisted evidence artifact.
2. Reconcile daily trades with campaign changes, including late-recorded or revised exits; flag mismatches.
3. Correct trade-compounded 'drawdown' labeling; report portfolio-equity drawdown separately.
4. Audit negative simulated execution costs and stop slippage; compare realistic Jupiter entry/exit quotes.
5. Add **separate paper experiments**: per-token re-entry cooldown, Runner Hunter momentum persistence, DIY Whale stronger RISK_OFF liquidity/organic-demand gate. Do not modify baseline trading logic until tests and evidence support it.

**Deployment:** This branch contains only a scorecard library, tests and documentation. No live trading or runtime deployment is implied.
