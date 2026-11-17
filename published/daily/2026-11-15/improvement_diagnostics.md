# CryptoTracker sleeve-improvement diagnostics — 2026-11-15

**Paper-only read-only audit. No entry/exit changes. No live orders.**
Target: +1.00% per calendar day on mark-to-market portfolio equity; unavailable until verified open-position valuation exists.

| Sleeve | Daily exits | Daily realized P&L | Inception exits | Inception realized P&L | Avg net/trade inception |
|---|---:|---:|---:|---:|---:|
| balanced_ev | 7 | $-0.0998 | 346 | $+0.0174 | +0.00% |
| runner_hunter | 0 | $+0.0000 | 214 | $-2.6394 | -1.64% |
| diy_whale | 6 | $-0.2390 | 619 | $-6.2109 | -1.34% |

## Investigation flags

- **balanced_ev**: 5 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 35 observed reentries within 60m of a loss; RISK_OFF 1 completed exits / $-0.1678 inception.
- **runner_hunter**: 0 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 8 observed reentries within 60m of a loss; RISK_OFF 2 completed exits / $-0.0534 inception.
- **diy_whale**: 1 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 90 observed reentries within 60m of a loss; RISK_OFF 381 completed exits / $-4.2167 inception.

## Evaluation policy

Risk-off exclusions and cooldown counts are retrospective selection diagnostics, not backtests.
Runner persistence requires independent time-ordered observations. Profit exits require modeled executable routes.
Keep Balanced EV, Runner Hunter and DIY Whale frozen as controls; compare independent prospective paper variants.
Do not increase trade size or enable live swapping without verified liquidity, slippage, out-of-sample returns and drawdowns.
A merged GitHub change is not verified on the Windows trading host.
