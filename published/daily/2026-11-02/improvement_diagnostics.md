# CryptoTracker sleeve-improvement diagnostics — 2026-11-02

**Paper-only read-only audit. No entry/exit changes. No live orders.**
Target: +1.00% per calendar day on mark-to-market portfolio equity; unavailable until verified open-position valuation exists.

| Sleeve | Daily exits | Daily realized P&L | Inception exits | Inception realized P&L | Avg net/trade inception |
|---|---:|---:|---:|---:|---:|
| balanced_ev | 19 | $-0.3620 | 247 | $+0.7080 | +0.19% |
| runner_hunter | 7 | $+0.2872 | 156 | $-1.5074 | -1.29% |
| diy_whale | 24 | $-0.5335 | 447 | $-3.8392 | -1.15% |

## Investigation flags

- **balanced_ev**: 7 unusual daily cost estimates; 1 severe stop overruns; 0 gains-to-loss reversals; 26 observed reentries within 60m of a loss; RISK_OFF 1 completed exits / $-0.1678 inception.
- **runner_hunter**: 4 unusual daily cost estimates; 0 severe stop overruns; 1 gains-to-loss reversals; 7 observed reentries within 60m of a loss; RISK_OFF 1 completed exits / $-0.0889 inception.
- **diy_whale**: 9 unusual daily cost estimates; 1 severe stop overruns; 0 gains-to-loss reversals; 65 observed reentries within 60m of a loss; RISK_OFF 274 completed exits / $-3.5050 inception.

## Evaluation policy

Risk-off exclusions and cooldown counts are retrospective selection diagnostics, not backtests.
Runner persistence requires independent time-ordered observations. Profit exits require modeled executable routes.
Keep Balanced EV, Runner Hunter and DIY Whale frozen as controls; compare independent prospective paper variants.
Do not increase trade size or enable live swapping without verified liquidity, slippage, out-of-sample returns and drawdowns.
A merged GitHub change is not verified on the Windows trading host.
