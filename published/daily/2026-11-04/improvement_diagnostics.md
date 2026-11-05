# CryptoTracker sleeve-improvement diagnostics — 2026-11-04

**Paper-only read-only audit. No entry/exit changes. No live orders.**
Target: +1.00% per calendar day on mark-to-market portfolio equity; unavailable until verified open-position valuation exists.

| Sleeve | Daily exits | Daily realized P&L | Inception exits | Inception realized P&L | Avg net/trade inception |
|---|---:|---:|---:|---:|---:|
| balanced_ev | 11 | $-0.0191 | 275 | $+0.6241 | +0.15% |
| runner_hunter | 6 | $+0.0107 | 168 | $-1.6952 | -1.35% |
| diy_whale | 20 | $-0.0231 | 486 | $-4.6666 | -1.28% |

## Investigation flags

- **balanced_ev**: 8 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 27 observed reentries within 60m of a loss; RISK_OFF 1 completed exits / $-0.1678 inception.
- **runner_hunter**: 3 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 7 observed reentries within 60m of a loss; RISK_OFF 1 completed exits / $-0.0889 inception.
- **diy_whale**: 9 unusual daily cost estimates; 3 severe stop overruns; 2 gains-to-loss reversals; 71 observed reentries within 60m of a loss; RISK_OFF 291 completed exits / $-3.4042 inception.

## Evaluation policy

Risk-off exclusions and cooldown counts are retrospective selection diagnostics, not backtests.
Runner persistence requires independent time-ordered observations. Profit exits require modeled executable routes.
Keep Balanced EV, Runner Hunter and DIY Whale frozen as controls; compare independent prospective paper variants.
Do not increase trade size or enable live swapping without verified liquidity, slippage, out-of-sample returns and drawdowns.
A merged GitHub change is not verified on the Windows trading host.
