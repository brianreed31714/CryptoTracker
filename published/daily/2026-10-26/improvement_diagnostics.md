# CryptoTracker sleeve-improvement diagnostics — 2026-10-26

**Paper-only read-only audit. No entry/exit changes. No live orders.**
Target: +1.00% per calendar day on mark-to-market portfolio equity; unavailable until verified open-position valuation exists.

| Sleeve | Daily exits | Daily realized P&L | Inception exits | Inception realized P&L | Avg net/trade inception |
|---|---:|---:|---:|---:|---:|
| balanced_ev | 1 | $-0.0203 | 163 | $+1.6365 | +0.67% |
| runner_hunter | 4 | $-0.5712 | 103 | $-1.3769 | -1.78% |
| diy_whale | 16 | $-0.1322 | 269 | $-2.2116 | -1.10% |

## Investigation flags

- **balanced_ev**: 0 unusual daily cost estimates; 0 severe stop overruns; 0 gains-to-loss reversals; 20 observed reentries within 60m of a loss; RISK_OFF 1 completed exits / $-0.1678 inception.
- **runner_hunter**: 2 unusual daily cost estimates; 1 severe stop overruns; 0 gains-to-loss reversals; 6 observed reentries within 60m of a loss; RISK_OFF 1 completed exits / $-0.0889 inception.
- **diy_whale**: 7 unusual daily cost estimates; 1 severe stop overruns; 0 gains-to-loss reversals; 29 observed reentries within 60m of a loss; RISK_OFF 171 completed exits / $-3.0635 inception.

## Evaluation policy

Risk-off exclusions and cooldown counts are retrospective selection diagnostics, not backtests.
Runner persistence requires independent time-ordered observations. Profit exits require modeled executable routes.
Keep Balanced EV, Runner Hunter and DIY Whale frozen as controls; compare independent prospective paper variants.
Do not increase trade size or enable live swapping without verified liquidity, slippage, out-of-sample returns and drawdowns.
A merged GitHub change is not verified on the Windows trading host.
