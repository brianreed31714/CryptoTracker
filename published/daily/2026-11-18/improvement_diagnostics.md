# CryptoTracker sleeve-improvement diagnostics — 2026-11-18

**Paper-only read-only audit. No entry/exit changes. No live orders.**
Target: +1.00% per calendar day on mark-to-market portfolio equity; unavailable until verified open-position valuation exists.

| Sleeve | Daily exits | Daily realized P&L | Inception exits | Inception realized P&L | Avg net/trade inception |
|---|---:|---:|---:|---:|---:|
| balanced_ev | 5 | $-0.0118 | 371 | $-0.4154 | -0.07% |
| runner_hunter | 8 | $-0.2714 | 229 | $-3.6061 | -2.10% |
| diy_whale | 21 | $-0.2049 | 676 | $-7.4903 | -1.48% |

## Investigation flags

- **balanced_ev**: 3 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 35 observed reentries within 60m of a loss; RISK_OFF 1 completed exits / $-0.1678 inception.
- **runner_hunter**: 4 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 9 observed reentries within 60m of a loss; RISK_OFF 2 completed exits / $-0.0534 inception.
- **diy_whale**: 12 unusual daily cost estimates; 1 severe stop overruns; 0 gains-to-loss reversals; 97 observed reentries within 60m of a loss; RISK_OFF 423 completed exits / $-4.9469 inception.

## Evaluation policy

Risk-off exclusions and cooldown counts are retrospective selection diagnostics, not backtests.
Runner persistence requires independent time-ordered observations. Profit exits require modeled executable routes.
Keep Balanced EV, Runner Hunter and DIY Whale frozen as controls; compare independent prospective paper variants.
Do not increase trade size or enable live swapping without verified liquidity, slippage, out-of-sample returns and drawdowns.
A merged GitHub change is not verified on the Windows trading host.
