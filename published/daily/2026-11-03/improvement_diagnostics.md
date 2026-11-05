# CryptoTracker sleeve-improvement diagnostics — 2026-11-03

**Paper-only read-only audit. No entry/exit changes. No live orders.**
Target: +1.00% per calendar day on mark-to-market portfolio equity; unavailable until verified open-position valuation exists.

| Sleeve | Daily exits | Daily realized P&L | Inception exits | Inception realized P&L | Avg net/trade inception |
|---|---:|---:|---:|---:|---:|
| balanced_ev | 17 | $-0.0648 | 264 | $+0.6431 | +0.16% |
| runner_hunter | 6 | $-0.1985 | 162 | $-1.7059 | -1.40% |
| diy_whale | 19 | $-0.8044 | 466 | $-4.6435 | -1.33% |

## Investigation flags

- **balanced_ev**: 6 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 26 observed reentries within 60m of a loss; RISK_OFF 1 completed exits / $-0.1678 inception.
- **runner_hunter**: 1 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 7 observed reentries within 60m of a loss; RISK_OFF 1 completed exits / $-0.0889 inception.
- **diy_whale**: 10 unusual daily cost estimates; 1 severe stop overruns; 1 gains-to-loss reversals; 67 observed reentries within 60m of a loss; RISK_OFF 280 completed exits / $-3.6383 inception.

## Evaluation policy

Risk-off exclusions and cooldown counts are retrospective selection diagnostics, not backtests.
Runner persistence requires independent time-ordered observations. Profit exits require modeled executable routes.
Keep Balanced EV, Runner Hunter and DIY Whale frozen as controls; compare independent prospective paper variants.
Do not increase trade size or enable live swapping without verified liquidity, slippage, out-of-sample returns and drawdowns.
A merged GitHub change is not verified on the Windows trading host.
