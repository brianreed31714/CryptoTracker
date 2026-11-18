# CryptoTracker sleeve-improvement diagnostics — 2026-11-16

**Paper-only read-only audit. No entry/exit changes. No live orders.**
Target: +1.00% per calendar day on mark-to-market portfolio equity; unavailable until verified open-position valuation exists.

| Sleeve | Daily exits | Daily realized P&L | Inception exits | Inception realized P&L | Avg net/trade inception |
|---|---:|---:|---:|---:|---:|
| balanced_ev | 12 | $-0.4245 | 358 | $-0.4070 | -0.08% |
| runner_hunter | 4 | $-0.0326 | 218 | $-2.6720 | -1.63% |
| diy_whale | 19 | $-0.6421 | 638 | $-6.8531 | -1.43% |

## Investigation flags

- **balanced_ev**: 3 unusual daily cost estimates; 2 severe stop overruns; 0 gains-to-loss reversals; 35 observed reentries within 60m of a loss; RISK_OFF 1 completed exits / $-0.1678 inception.
- **runner_hunter**: 0 unusual daily cost estimates; 1 severe stop overruns; 0 gains-to-loss reversals; 8 observed reentries within 60m of a loss; RISK_OFF 2 completed exits / $-0.0534 inception.
- **diy_whale**: 7 unusual daily cost estimates; 2 severe stop overruns; 0 gains-to-loss reversals; 92 observed reentries within 60m of a loss; RISK_OFF 396 completed exits / $-4.7533 inception.

## Evaluation policy

Risk-off exclusions and cooldown counts are retrospective selection diagnostics, not backtests.
Runner persistence requires independent time-ordered observations. Profit exits require modeled executable routes.
Keep Balanced EV, Runner Hunter and DIY Whale frozen as controls; compare independent prospective paper variants.
Do not increase trade size or enable live swapping without verified liquidity, slippage, out-of-sample returns and drawdowns.
A merged GitHub change is not verified on the Windows trading host.
