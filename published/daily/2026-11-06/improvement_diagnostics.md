# CryptoTracker sleeve-improvement diagnostics — 2026-11-06

**Paper-only read-only audit. No entry/exit changes. No live orders.**
Target: +1.00% per calendar day on mark-to-market portfolio equity; unavailable until verified open-position valuation exists.

| Sleeve | Daily exits | Daily realized P&L | Inception exits | Inception realized P&L | Avg net/trade inception |
|---|---:|---:|---:|---:|---:|
| balanced_ev | 11 | $-0.4138 | 299 | $+0.5822 | +0.13% |
| runner_hunter | 5 | $-0.1787 | 182 | $-2.3152 | -1.70% |
| diy_whale | 23 | $-0.5516 | 525 | $-5.0333 | -1.28% |

## Investigation flags

- **balanced_ev**: 5 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 29 observed reentries within 60m of a loss; RISK_OFF 1 completed exits / $-0.1678 inception.
- **runner_hunter**: 3 unusual daily cost estimates; 1 severe stop overruns; 0 gains-to-loss reversals; 7 observed reentries within 60m of a loss; RISK_OFF 1 completed exits / $-0.0889 inception.
- **diy_whale**: 9 unusual daily cost estimates; 2 severe stop overruns; 1 gains-to-loss reversals; 73 observed reentries within 60m of a loss; RISK_OFF 316 completed exits / $-3.8153 inception.

## Evaluation policy

Risk-off exclusions and cooldown counts are retrospective selection diagnostics, not backtests.
Runner persistence requires independent time-ordered observations. Profit exits require modeled executable routes.
Keep Balanced EV, Runner Hunter and DIY Whale frozen as controls; compare independent prospective paper variants.
Do not increase trade size or enable live swapping without verified liquidity, slippage, out-of-sample returns and drawdowns.
A merged GitHub change is not verified on the Windows trading host.
