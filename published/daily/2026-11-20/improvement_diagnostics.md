# CryptoTracker sleeve-improvement diagnostics — 2026-11-20

**Paper-only read-only audit. No entry/exit changes. No live orders.**
Target: +1.00% per calendar day on mark-to-market portfolio equity; unavailable until verified open-position valuation exists.

| Sleeve | Daily exits | Daily realized P&L | Inception exits | Inception realized P&L | Avg net/trade inception |
|---|---:|---:|---:|---:|---:|
| balanced_ev | 10 | $-0.2520 | 390 | $-0.9360 | -0.16% |
| runner_hunter | 4 | $-0.0737 | 235 | $-3.6949 | -2.10% |
| diy_whale | 21 | $-0.5316 | 711 | $-8.3860 | -1.57% |

## Investigation flags

- **balanced_ev**: 2 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 37 observed reentries within 60m of a loss; RISK_OFF 2 completed exits / $-0.2730 inception.
- **runner_hunter**: 0 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 9 observed reentries within 60m of a loss; RISK_OFF 2 completed exits / $-0.0534 inception.
- **diy_whale**: 7 unusual daily cost estimates; 0 severe stop overruns; 1 gains-to-loss reversals; 103 observed reentries within 60m of a loss; RISK_OFF 445 completed exits / $-5.4631 inception.

## Evaluation policy

Risk-off exclusions and cooldown counts are retrospective selection diagnostics, not backtests.
Runner persistence requires independent time-ordered observations. Profit exits require modeled executable routes.
Keep Balanced EV, Runner Hunter and DIY Whale frozen as controls; compare independent prospective paper variants.
Do not increase trade size or enable live swapping without verified liquidity, slippage, out-of-sample returns and drawdowns.
A merged GitHub change is not verified on the Windows trading host.
