# CryptoTracker sleeve-improvement diagnostics — 2026-10-27

**Paper-only read-only audit. No entry/exit changes. No live orders.**
Target: +1.00% per calendar day on mark-to-market portfolio equity; unavailable until verified open-position valuation exists.

| Sleeve | Daily exits | Daily realized P&L | Inception exits | Inception realized P&L | Avg net/trade inception |
|---|---:|---:|---:|---:|---:|
| balanced_ev | 6 | $-0.2382 | 170 | $+1.4015 | +0.55% |
| runner_hunter | 7 | $+0.1130 | 112 | $-1.3143 | -1.56% |
| diy_whale | 15 | $-0.4482 | 289 | $-2.6482 | -1.22% |

## Investigation flags

- **balanced_ev**: 3 unusual daily cost estimates; 1 severe stop overruns; 0 gains-to-loss reversals; 20 observed reentries within 60m of a loss; RISK_OFF 1 completed exits / $-0.1678 inception.
- **runner_hunter**: 4 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 6 observed reentries within 60m of a loss; RISK_OFF 1 completed exits / $-0.0889 inception.
- **diy_whale**: 6 unusual daily cost estimates; 2 severe stop overruns; 1 gains-to-loss reversals; 32 observed reentries within 60m of a loss; RISK_OFF 182 completed exits / $-3.3526 inception.

## Evaluation policy

Risk-off exclusions and cooldown counts are retrospective selection diagnostics, not backtests.
Runner persistence requires independent time-ordered observations. Profit exits require modeled executable routes.
Keep Balanced EV, Runner Hunter and DIY Whale frozen as controls; compare independent prospective paper variants.
Do not increase trade size or enable live swapping without verified liquidity, slippage, out-of-sample returns and drawdowns.
A merged GitHub change is not verified on the Windows trading host.
