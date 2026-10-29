# CryptoTracker sleeve-improvement diagnostics — 2026-10-28

**Paper-only read-only audit. No entry/exit changes. No live orders.**
Target: +1.00% per calendar day on mark-to-market portfolio equity; unavailable until verified open-position valuation exists.

| Sleeve | Daily exits | Daily realized P&L | Inception exits | Inception realized P&L | Avg net/trade inception |
|---|---:|---:|---:|---:|---:|
| balanced_ev | 10 | $-0.5648 | 182 | $+0.8419 | +0.31% |
| runner_hunter | 14 | $-0.2411 | 128 | $-1.6127 | -1.68% |
| diy_whale | 32 | $-0.5844 | 326 | $-3.2613 | -1.33% |

## Investigation flags

- **balanced_ev**: 3 unusual daily cost estimates; 1 severe stop overruns; 0 gains-to-loss reversals; 20 observed reentries within 60m of a loss; RISK_OFF 1 completed exits / $-0.1678 inception.
- **runner_hunter**: 7 unusual daily cost estimates; 1 severe stop overruns; 0 gains-to-loss reversals; 6 observed reentries within 60m of a loss; RISK_OFF 1 completed exits / $-0.0889 inception.
- **diy_whale**: 12 unusual daily cost estimates; 2 severe stop overruns; 1 gains-to-loss reversals; 46 observed reentries within 60m of a loss; RISK_OFF 201 completed exits / $-3.5629 inception.

## Evaluation policy

Risk-off exclusions and cooldown counts are retrospective selection diagnostics, not backtests.
Runner persistence requires independent time-ordered observations. Profit exits require modeled executable routes.
Keep Balanced EV, Runner Hunter and DIY Whale frozen as controls; compare independent prospective paper variants.
Do not increase trade size or enable live swapping without verified liquidity, slippage, out-of-sample returns and drawdowns.
A merged GitHub change is not verified on the Windows trading host.
