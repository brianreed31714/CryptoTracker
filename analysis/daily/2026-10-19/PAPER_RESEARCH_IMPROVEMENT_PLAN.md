# CryptoTracker controlled paper-research improvement plan — 2026-10-19

**Decision:** Retain Balanced EV, Runner Hunter, and DIY Whale as unchanged paper-only control sleeves. The objective is to measure whether the portfolio can achieve +1.00% per calendar day; it is a stretch target, **not** a return prediction, promise, or reason to take uncontrolled risk.

## Measurement contract

- Publish for **each sleeve**, every night: completed simulated trades, wins/losses, win rate, realized P&L (USD), average net return **per completed trade**, realized-equity daily return, since-first-observed-entry realized-equity return, mark-to-market portfolio daily / inception return when independently available, daily and inception equity drawdown, and target shortfall.
- Goal: **+1.00% marked-to-market portfolio return per calendar day**, with a compounded inception benchmark of `1.01 ** elapsed_calendar_days - 1`. This benchmark applies to idle days too. If marked-to-market returns are unavailable, only report the realized-equity proxy with that precise label. An average trade gain of +1% is **not** success against a +1% daily portfolio objective.
- Show explicit daily target hit/miss for the realized-equity proxy, and a separate full-portfolio pass/fail only if mark-to-market equity is available. Never silently treat missing prices or trades as profitable days.
- Full mark-to-market accounting remains **open** until position quotes can be valued reliably at fixed daily boundaries; never fabricate valuation of open positions.
- Flag missing/stale reports, absent services, late backfills, campaign vs daily count changes, publication gaps, and unverified local Windows versions.

## Research experiments (hypotheses, NOT promotions)

1. **Balanced EV control versus token-loss cooldown.** Compare fixed 30-, 60-, and 120-minute cooldowns after a net-loss exit in the *same token*. Analyze impact on missed runners and net returns. Do not suppress profitable subsequent entries in the baseline.
2. **Runner Hunter persistence and stop realism.** Evaluate 2 or 3 consecutive independent observations showing persistent positive momentum, stable liquidity, and executable quotes. Analyze executable stop-loss overruns, with explicit price-impact simulation. Compare realistic captured return to maximum favorable excursion.
3. **DIY Whale organic-demand and RISK_OFF constraints.** In separate paper-only variants, test excluding RISK_OFF entries versus imposing stricter RISK_OFF liquidity, buy/sell pressure, and volume acceleration, with token-specific re-entry cooldowns. Distinguish organic buying from any artificial attempts to move price. No price manipulation.
4. **Execution accounting.** Audit estimated cost below 0%, above 5%, and net losses below -20%. Negative estimated cost is NOT automatically an error or free profit: compare reference-quote timestamps, units, token decimals, transaction costs and executable Jupiter routes.
5. **Data-integrity reconciliation.** Compare consecutive-day cumulative closed trade counts with dated completed exits. Missing intermediate publication days make comparison inconclusive. Reconcile backfills and corrected trades by trade ID/timestamp before treating campaign deltas as today's P&L.

## Minimum evaluation protocol

- Freeze baseline model configurations; retain independent time-ordered paper/shadow variants.
- No look-ahead from a token's later price, future buy/sell pressure, or subsequent liquidity; replay only features already known when the entry/exit was scored.
- Use time-separated development and prospective out-of-sample periods; report net P&L, win rate, avg net trade return, *capital-based* daily performance, drawdown, profit factor, opportunity cost, and sample sizes.
- At least 30 completed exits for preliminary review **per variant**, preferably more with multiple market regimes; require stable prospective performance across multiple weeks before suggesting promotion.
- Do not increase hypothetical $0.75 probe size to $800–$1,000 without a separate depth/liquidity and slippage analysis. Do not enable live swaps.
- Protect the existing deployment gate: GitHub merge does not prove that a Windows service picked up the change. Validate runtime manifests and post-deployment published artifacts separately.

## Status at document creation

- Daily/inception 1% target and realized-equity drawdown scorecards merged via PR #4, commit `ddfad3b991d17f73bb0f96b129ae65db306f0a4a`, after GitHub CI passed.
- Read-only simulated-execution and publication quality audit proposed in follow-up branch; validate CI before merge.
- No executable strategy changes deployed. Actual historical improvement from cooldowns, persistence or RISK_OFF filters is **not yet demonstrated**.
