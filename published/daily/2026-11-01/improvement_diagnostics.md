# CryptoTracker sleeve-improvement diagnostics — 2026-11-01

**Paper-only read-only audit. No entry/exit changes. No live orders.**
Target: +1.00% per calendar day on mark-to-market portfolio equity; unavailable until verified open-position valuation exists.

| Sleeve | Daily exits | Daily realized P&L | Inception exits | Inception realized P&L | Avg net/trade inception |
|---|---:|---:|---:|---:|---:|
| balanced_ev | 16 | $+0.1087 | 225 | $+1.0473 | +0.31% |
| runner_hunter | 6 | $+0.1628 | 148 | $-1.8041 | -1.63% |
| diy_whale | 19 | $+0.0102 | 419 | $-3.3428 | -1.06% |

## Investigation flags

- **balanced_ev**: 4 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 22 observed reentries within 60m of a loss; RISK_OFF 1 completed exits / $-0.1678 inception.
- **runner_hunter**: 1 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 7 observed reentries within 60m of a loss; RISK_OFF 1 completed exits / $-0.0889 inception.
- **diy_whale**: 6 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 63 observed reentries within 60m of a loss; RISK_OFF 260 completed exits / $-3.3626 inception.

## Evaluation policy

Risk-off exclusions and cooldown counts are retrospective selection diagnostics, not backtests.
Runner persistence requires independent time-ordered observations. Profit exits require modeled executable routes.
Keep Balanced EV, Runner Hunter and DIY Whale frozen as controls; compare independent prospective paper variants.
Do not increase trade size or enable live swapping without verified liquidity, slippage, out-of-sample returns and drawdowns.
A merged GitHub change is not verified on the Windows trading host.
