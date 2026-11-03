# CryptoTracker sleeve-improvement diagnostics — 2026-11-01

**Paper-only read-only audit. No entry/exit changes. No live orders.**
Target: +1.00% per calendar day on mark-to-market portfolio equity; unavailable until verified open-position valuation exists.

| Sleeve | Daily exits | Daily realized P&L | Inception exits | Inception realized P&L | Avg net/trade inception |
|---|---:|---:|---:|---:|---:|
| balanced_ev | 19 | $+0.1313 | 228 | $+1.0700 | +0.31% |
| runner_hunter | 7 | $+0.1724 | 149 | $-1.7946 | -1.61% |
| diy_whale | 23 | $+0.0473 | 423 | $-3.3056 | -1.04% |

## Investigation flags

- **balanced_ev**: 5 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 23 observed reentries within 60m of a loss; RISK_OFF 1 completed exits / $-0.1678 inception.
- **runner_hunter**: 1 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 7 observed reentries within 60m of a loss; RISK_OFF 1 completed exits / $-0.0889 inception.
- **diy_whale**: 8 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 63 observed reentries within 60m of a loss; RISK_OFF 264 completed exits / $-3.3254 inception.

## Evaluation policy

Risk-off exclusions and cooldown counts are retrospective selection diagnostics, not backtests.
Runner persistence requires independent time-ordered observations. Profit exits require modeled executable routes.
Keep Balanced EV, Runner Hunter and DIY Whale frozen as controls; compare independent prospective paper variants.
Do not increase trade size or enable live swapping without verified liquidity, slippage, out-of-sample returns and drawdowns.
A merged GitHub change is not verified on the Windows trading host.
