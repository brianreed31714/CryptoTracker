# CryptoTracker sleeve-improvement diagnostics — 2026-11-25

**Paper-only read-only audit. No entry/exit changes. No live orders.**
Target: +1.00% per calendar day on mark-to-market portfolio equity; unavailable until verified open-position valuation exists.

| Sleeve | Daily exits | Daily realized P&L | Inception exits | Inception realized P&L | Avg net/trade inception |
|---|---:|---:|---:|---:|---:|
| balanced_ev | 3 | $+0.0482 | 412 | $+0.4040 | +0.07% |
| runner_hunter | 3 | $-0.0266 | 250 | $-2.5982 | -1.39% |
| diy_whale | 11 | $-0.1536 | 778 | $-11.9281 | -2.04% |

## Investigation flags

- **balanced_ev**: 0 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 39 observed reentries within 60m of a loss; RISK_OFF 2 completed exits / $-0.2730 inception.
- **runner_hunter**: 2 unusual daily cost estimates; 0 severe stop overruns; 1 gains-to-loss reversals; 9 observed reentries within 60m of a loss; RISK_OFF 2 completed exits / $-0.0534 inception.
- **diy_whale**: 4 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 106 observed reentries within 60m of a loss; RISK_OFF 495 completed exits / $-7.9382 inception.

## Evaluation policy

Risk-off exclusions and cooldown counts are retrospective selection diagnostics, not backtests.
Runner persistence requires independent time-ordered observations. Profit exits require modeled executable routes.
Keep Balanced EV, Runner Hunter and DIY Whale frozen as controls; compare independent prospective paper variants.
Do not increase trade size or enable live swapping without verified liquidity, slippage, out-of-sample returns and drawdowns.
A merged GitHub change is not verified on the Windows trading host.
