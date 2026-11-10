# CryptoTracker sleeve-improvement diagnostics — 2026-11-09

**Paper-only read-only audit. No entry/exit changes. No live orders.**
Target: +1.00% per calendar day on mark-to-market portfolio equity; unavailable until verified open-position valuation exists.

| Sleeve | Daily exits | Daily realized P&L | Inception exits | Inception realized P&L | Avg net/trade inception |
|---|---:|---:|---:|---:|---:|
| balanced_ev | 11 | $-0.3741 | 326 | $+0.3458 | +0.07% |
| runner_hunter | 5 | $-0.1476 | 206 | $-2.5471 | -1.65% |
| diy_whale | 16 | $-0.2534 | 573 | $-4.6551 | -1.08% |

## Investigation flags

- **balanced_ev**: 2 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 32 observed reentries within 60m of a loss; RISK_OFF 1 completed exits / $-0.1678 inception.
- **runner_hunter**: 2 unusual daily cost estimates; 1 severe stop overruns; 0 gains-to-loss reversals; 8 observed reentries within 60m of a loss; RISK_OFF 1 completed exits / $-0.0889 inception.
- **diy_whale**: 6 unusual daily cost estimates; 1 severe stop overruns; 0 gains-to-loss reversals; 83 observed reentries within 60m of a loss; RISK_OFF 351 completed exits / $-3.1993 inception.

## Evaluation policy

Risk-off exclusions and cooldown counts are retrospective selection diagnostics, not backtests.
Runner persistence requires independent time-ordered observations. Profit exits require modeled executable routes.
Keep Balanced EV, Runner Hunter and DIY Whale frozen as controls; compare independent prospective paper variants.
Do not increase trade size or enable live swapping without verified liquidity, slippage, out-of-sample returns and drawdowns.
A merged GitHub change is not verified on the Windows trading host.
