# CryptoTracker sleeve-improvement diagnostics — 2026-11-08

**Paper-only read-only audit. No entry/exit changes. No live orders.**
Target: +1.00% per calendar day on mark-to-market portfolio equity; unavailable until verified open-position valuation exists.

| Sleeve | Daily exits | Daily realized P&L | Inception exits | Inception realized P&L | Avg net/trade inception |
|---|---:|---:|---:|---:|---:|
| balanced_ev | 8 | $+0.4603 | 314 | $+0.5571 | +0.12% |
| runner_hunter | 8 | $+0.1646 | 200 | $-2.3954 | -1.60% |
| diy_whale | 14 | $+0.1631 | 556 | $-4.6814 | -1.12% |

## Investigation flags

- **balanced_ev**: 4 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 30 observed reentries within 60m of a loss; RISK_OFF 1 completed exits / $-0.1678 inception.
- **runner_hunter**: 6 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 7 observed reentries within 60m of a loss; RISK_OFF 1 completed exits / $-0.0889 inception.
- **diy_whale**: 10 unusual daily cost estimates; 0 severe stop overruns; 1 gains-to-loss reversals; 78 observed reentries within 60m of a loss; RISK_OFF 339 completed exits / $-3.3348 inception.

## Evaluation policy

Risk-off exclusions and cooldown counts are retrospective selection diagnostics, not backtests.
Runner persistence requires independent time-ordered observations. Profit exits require modeled executable routes.
Keep Balanced EV, Runner Hunter and DIY Whale frozen as controls; compare independent prospective paper variants.
Do not increase trade size or enable live swapping without verified liquidity, slippage, out-of-sample returns and drawdowns.
A merged GitHub change is not verified on the Windows trading host.
