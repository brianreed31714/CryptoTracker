# CryptoTracker sleeve-improvement diagnostics — 2026-10-25

**Paper-only read-only audit. No entry/exit changes. No live orders.**
Target: +1.00% per calendar day on mark-to-market portfolio equity; unavailable until verified open-position valuation exists.

| Sleeve | Daily exits | Daily realized P&L | Inception exits | Inception realized P&L | Avg net/trade inception |
|---|---:|---:|---:|---:|---:|
| balanced_ev | 0 | $+0.0000 | 162 | $+1.6568 | +0.68% |
| runner_hunter | 0 | $+0.0000 | 98 | $-0.8432 | -1.15% |
| diy_whale | 1 | $-0.0304 | 248 | $-2.1212 | -1.14% |

## Investigation flags

- **balanced_ev**: 0 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 20 observed reentries within 60m of a loss; RISK_OFF 1 completed exits / $-0.1678 inception.
- **runner_hunter**: 0 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 6 observed reentries within 60m of a loss; RISK_OFF 1 completed exits / $-0.0889 inception.
- **diy_whale**: 0 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 26 observed reentries within 60m of a loss; RISK_OFF 159 completed exits / $-2.8124 inception.

## Evaluation policy

Risk-off exclusions and cooldown counts are retrospective selection diagnostics, not backtests.
Runner persistence requires independent time-ordered observations. Profit exits require modeled executable routes.
Keep Balanced EV, Runner Hunter and DIY Whale frozen as controls; compare independent prospective paper variants.
Do not increase trade size or enable live swapping without verified liquidity, slippage, out-of-sample returns and drawdowns.
A merged GitHub change is not verified on the Windows trading host.
