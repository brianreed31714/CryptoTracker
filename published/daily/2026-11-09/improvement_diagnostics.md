# CryptoTracker sleeve-improvement diagnostics — 2026-11-09

**Paper-only read-only audit. No entry/exit changes. No live orders.**
Target: +1.00% per calendar day on mark-to-market portfolio equity; unavailable until verified open-position valuation exists.

| Sleeve | Daily exits | Daily realized P&L | Inception exits | Inception realized P&L | Avg net/trade inception |
|---|---:|---:|---:|---:|---:|
| balanced_ev | 13 | $-0.3059 | 328 | $+0.4140 | +0.08% |
| runner_hunter | 7 | $-0.1108 | 208 | $-2.5103 | -1.61% |
| diy_whale | 19 | $-0.2572 | 576 | $-4.6589 | -1.08% |

## Investigation flags

- **balanced_ev**: 4 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 32 observed reentries within 60m of a loss; RISK_OFF 1 completed exits / $-0.1678 inception.
- **runner_hunter**: 4 unusual daily cost estimates; 1 severe stop overruns; 0 gains-to-loss reversals; 8 observed reentries within 60m of a loss; RISK_OFF 1 completed exits / $-0.0889 inception.
- **diy_whale**: 8 unusual daily cost estimates; 1 severe stop overruns; 0 gains-to-loss reversals; 83 observed reentries within 60m of a loss; RISK_OFF 353 completed exits / $-3.1894 inception.

## Evaluation policy

Risk-off exclusions and cooldown counts are retrospective selection diagnostics, not backtests.
Runner persistence requires independent time-ordered observations. Profit exits require modeled executable routes.
Keep Balanced EV, Runner Hunter and DIY Whale frozen as controls; compare independent prospective paper variants.
Do not increase trade size or enable live swapping without verified liquidity, slippage, out-of-sample returns and drawdowns.
A merged GitHub change is not verified on the Windows trading host.
