# CryptoTracker sleeve-improvement diagnostics — 2026-10-30

**Paper-only read-only audit. No entry/exit changes. No live orders.**
Target: +1.00% per calendar day on mark-to-market portfolio equity; unavailable until verified open-position valuation exists.

| Sleeve | Daily exits | Daily realized P&L | Inception exits | Inception realized P&L | Avg net/trade inception |
|---|---:|---:|---:|---:|---:|
| balanced_ev | 9 | $+0.0295 | 201 | $+1.1186 | +0.37% |
| runner_hunter | 3 | $-0.0865 | 134 | $-1.6879 | -1.68% |
| diy_whale | 18 | $+0.5402 | 371 | $-3.0685 | -1.10% |

## Investigation flags

- **balanced_ev**: 3 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 21 observed reentries within 60m of a loss; RISK_OFF 1 completed exits / $-0.1678 inception.
- **runner_hunter**: 2 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 6 observed reentries within 60m of a loss; RISK_OFF 1 completed exits / $-0.0889 inception.
- **diy_whale**: 8 unusual daily cost estimates; 2 severe stop overruns; 0 gains-to-loss reversals; 55 observed reentries within 60m of a loss; RISK_OFF 233 completed exits / $-3.4588 inception.

## Evaluation policy

Risk-off exclusions and cooldown counts are retrospective selection diagnostics, not backtests.
Runner persistence requires independent time-ordered observations. Profit exits require modeled executable routes.
Keep Balanced EV, Runner Hunter and DIY Whale frozen as controls; compare independent prospective paper variants.
Do not increase trade size or enable live swapping without verified liquidity, slippage, out-of-sample returns and drawdowns.
A merged GitHub change is not verified on the Windows trading host.
