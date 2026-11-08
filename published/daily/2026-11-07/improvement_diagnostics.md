# CryptoTracker sleeve-improvement diagnostics — 2026-11-07

**Paper-only read-only audit. No entry/exit changes. No live orders.**
Target: +1.00% per calendar day on mark-to-market portfolio equity; unavailable until verified open-position valuation exists.

| Sleeve | Daily exits | Daily realized P&L | Inception exits | Inception realized P&L | Avg net/trade inception |
|---|---:|---:|---:|---:|---:|
| balanced_ev | 7 | $-0.4854 | 306 | $+0.0968 | +0.02% |
| runner_hunter | 9 | $-0.2081 | 191 | $-2.5233 | -1.76% |
| diy_whale | 11 | $+0.1257 | 536 | $-4.9076 | -1.22% |

## Investigation flags

- **balanced_ev**: 3 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 29 observed reentries within 60m of a loss; RISK_OFF 1 completed exits / $-0.1678 inception.
- **runner_hunter**: 4 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 7 observed reentries within 60m of a loss; RISK_OFF 1 completed exits / $-0.0889 inception.
- **diy_whale**: 4 unusual daily cost estimates; 0 severe stop overruns; 1 gains-to-loss reversals; 74 observed reentries within 60m of a loss; RISK_OFF 323 completed exits / $-3.5999 inception.

## Evaluation policy

Risk-off exclusions and cooldown counts are retrospective selection diagnostics, not backtests.
Runner persistence requires independent time-ordered observations. Profit exits require modeled executable routes.
Keep Balanced EV, Runner Hunter and DIY Whale frozen as controls; compare independent prospective paper variants.
Do not increase trade size or enable live swapping without verified liquidity, slippage, out-of-sample returns and drawdowns.
A merged GitHub change is not verified on the Windows trading host.
