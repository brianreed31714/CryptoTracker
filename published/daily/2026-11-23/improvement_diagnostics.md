# CryptoTracker sleeve-improvement diagnostics — 2026-11-23

**Paper-only read-only audit. No entry/exit changes. No live orders.**
Target: +1.00% per calendar day on mark-to-market portfolio equity; unavailable until verified open-position valuation exists.

| Sleeve | Daily exits | Daily realized P&L | Inception exits | Inception realized P&L | Avg net/trade inception |
|---|---:|---:|---:|---:|---:|
| balanced_ev | 4 | $+0.2320 | 404 | $+0.3960 | +0.07% |
| runner_hunter | 2 | $+0.0784 | 246 | $-2.5707 | -1.39% |
| diy_whale | 14 | $-0.3290 | 757 | $-10.2342 | -1.80% |

## Investigation flags

- **balanced_ev**: 4 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 38 observed reentries within 60m of a loss; RISK_OFF 2 completed exits / $-0.2730 inception.
- **runner_hunter**: 2 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 9 observed reentries within 60m of a loss; RISK_OFF 2 completed exits / $-0.0534 inception.
- **diy_whale**: 3 unusual daily cost estimates; 3 severe stop overruns; 1 gains-to-loss reversals; 106 observed reentries within 60m of a loss; RISK_OFF 479 completed exits / $-7.0004 inception.

## Evaluation policy

Risk-off exclusions and cooldown counts are retrospective selection diagnostics, not backtests.
Runner persistence requires independent time-ordered observations. Profit exits require modeled executable routes.
Keep Balanced EV, Runner Hunter and DIY Whale frozen as controls; compare independent prospective paper variants.
Do not increase trade size or enable live swapping without verified liquidity, slippage, out-of-sample returns and drawdowns.
A merged GitHub change is not verified on the Windows trading host.
