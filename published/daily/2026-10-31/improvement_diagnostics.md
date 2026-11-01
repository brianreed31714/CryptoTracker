# CryptoTracker sleeve-improvement diagnostics — 2026-10-31

**Paper-only read-only audit. No entry/exit changes. No live orders.**
Target: +1.00% per calendar day on mark-to-market portfolio equity; unavailable until verified open-position valuation exists.

| Sleeve | Daily exits | Daily realized P&L | Inception exits | Inception realized P&L | Avg net/trade inception |
|---|---:|---:|---:|---:|---:|
| balanced_ev | 8 | $-0.1800 | 209 | $+0.9386 | +0.30% |
| runner_hunter | 8 | $-0.2790 | 142 | $-1.9669 | -1.85% |
| diy_whale | 25 | $-0.0768 | 396 | $-3.1453 | -1.06% |

## Investigation flags

- **balanced_ev**: 4 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 21 observed reentries within 60m of a loss; RISK_OFF 1 completed exits / $-0.1678 inception.
- **runner_hunter**: 3 unusual daily cost estimates; 2 severe stop overruns; 0 gains-to-loss reversals; 6 observed reentries within 60m of a loss; RISK_OFF 1 completed exits / $-0.0889 inception.
- **diy_whale**: 11 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 60 observed reentries within 60m of a loss; RISK_OFF 248 completed exits / $-3.4678 inception.

## Evaluation policy

Risk-off exclusions and cooldown counts are retrospective selection diagnostics, not backtests.
Runner persistence requires independent time-ordered observations. Profit exits require modeled executable routes.
Keep Balanced EV, Runner Hunter and DIY Whale frozen as controls; compare independent prospective paper variants.
Do not increase trade size or enable live swapping without verified liquidity, slippage, out-of-sample returns and drawdowns.
A merged GitHub change is not verified on the Windows trading host.
