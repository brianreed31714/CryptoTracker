# CryptoTracker sleeve-improvement diagnostics — 2026-11-21

**Paper-only read-only audit. No entry/exit changes. No live orders.**
Target: +1.00% per calendar day on mark-to-market portfolio equity; unavailable until verified open-position valuation exists.

| Sleeve | Daily exits | Daily realized P&L | Inception exits | Inception realized P&L | Avg net/trade inception |
|---|---:|---:|---:|---:|---:|
| balanced_ev | 5 | $+0.9781 | 395 | $+0.0420 | +0.01% |
| runner_hunter | 5 | $+0.9645 | 240 | $-2.7304 | -1.52% |
| diy_whale | 15 | $-0.4058 | 726 | $-8.7918 | -1.61% |

## Investigation flags

- **balanced_ev**: 3 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 37 observed reentries within 60m of a loss; RISK_OFF 2 completed exits / $-0.2730 inception.
- **runner_hunter**: 3 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 9 observed reentries within 60m of a loss; RISK_OFF 2 completed exits / $-0.0534 inception.
- **diy_whale**: 5 unusual daily cost estimates; 3 severe stop overruns; 1 gains-to-loss reversals; 104 observed reentries within 60m of a loss; RISK_OFF 457 completed exits / $-5.8157 inception.

## Evaluation policy

Risk-off exclusions and cooldown counts are retrospective selection diagnostics, not backtests.
Runner persistence requires independent time-ordered observations. Profit exits require modeled executable routes.
Keep Balanced EV, Runner Hunter and DIY Whale frozen as controls; compare independent prospective paper variants.
Do not increase trade size or enable live swapping without verified liquidity, slippage, out-of-sample returns and drawdowns.
A merged GitHub change is not verified on the Windows trading host.
