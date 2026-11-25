# CryptoTracker sleeve-improvement diagnostics — 2026-11-22

**Paper-only read-only audit. No entry/exit changes. No live orders.**
Target: +1.00% per calendar day on mark-to-market portfolio equity; unavailable until verified open-position valuation exists.

| Sleeve | Daily exits | Daily realized P&L | Inception exits | Inception realized P&L | Avg net/trade inception |
|---|---:|---:|---:|---:|---:|
| balanced_ev | 5 | $+0.1220 | 400 | $+0.1640 | +0.03% |
| runner_hunter | 4 | $+0.0813 | 244 | $-2.6491 | -1.45% |
| diy_whale | 17 | $-1.1134 | 743 | $-9.9052 | -1.78% |

## Investigation flags

- **balanced_ev**: 2 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 38 observed reentries within 60m of a loss; RISK_OFF 2 completed exits / $-0.2730 inception.
- **runner_hunter**: 1 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 9 observed reentries within 60m of a loss; RISK_OFF 2 completed exits / $-0.0534 inception.
- **diy_whale**: 8 unusual daily cost estimates; 2 severe stop overruns; 1 gains-to-loss reversals; 104 observed reentries within 60m of a loss; RISK_OFF 469 completed exits / $-6.8338 inception.

## Evaluation policy

Risk-off exclusions and cooldown counts are retrospective selection diagnostics, not backtests.
Runner persistence requires independent time-ordered observations. Profit exits require modeled executable routes.
Keep Balanced EV, Runner Hunter and DIY Whale frozen as controls; compare independent prospective paper variants.
Do not increase trade size or enable live swapping without verified liquidity, slippage, out-of-sample returns and drawdowns.
A merged GitHub change is not verified on the Windows trading host.
