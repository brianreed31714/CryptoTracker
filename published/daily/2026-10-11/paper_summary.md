# CryptoTracker paper research — 2026-10-11

| Model | Trades | Shadow | W/L | Avg net | Median | Max DD | PnL | PF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| extended_probe | 1 | 5 | 1/0 | +16.57% | +16.57% | 0.00% | +0.1243 | 999.00 |
| patient_runner | 4 | 19 | 2/2 | +5.39% | -0.63% | 2.36% | +0.3235 | 6.90 |
| staged_runner | 4 | 0 | 2/2 | +4.78% | -0.63% | 2.36% | +0.2869 | 6.23 |
| runner_hunter | 4 | 9 | 3/1 | +3.46% | +1.20% | 2.60% | +0.1037 | 6.32 |
| balanced_ev | 5 | 19 | 4/1 | +1.99% | +0.69% | 3.55% | +0.1489 | 3.80 |
| low_friction | 2 | 25 | 2/0 | +1.58% | +1.58% | 0.00% | +0.0475 | 999.00 |
| anti_chase | 8 | 24 | 5/3 | +0.83% | +0.55% | 6.81% | +0.1000 | 1.83 |
| regime_filtered | 1 | 6 | 1/0 | +0.46% | +0.46% | 0.00% | +0.0069 | 999.00 |
| whale_luna | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| novelty_probe | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| fast_exit | 5 | 19 | 2/3 | -0.26% | -1.04% | 4.65% | -0.0193 | 0.75 |
| strict_baseline | 2 | 4 | 1/1 | -0.64% | -0.64% | 1.31% | -0.0192 | 0.02 |
| flow_breakout | 3 | 9 | 1/2 | -0.94% | -1.10% | 2.91% | -0.0423 | 0.30 |
| early_breakout | 3 | 7 | 0/3 | -1.35% | -1.02% | 3.99% | -0.0303 | 0.00 |
| diy_whale | 11 | 14 | 3/8 | -2.51% | -1.42% | 45.04% | -0.2071 | 0.56 |

## Three-sleeve comparison

| Sleeve | Entries | Closed | Win rate | Avg trade net | Max DD | Realized PnL |
|---|---:|---:|---:|---:|---:|---:|
| balanced_ev | 5 | 5 | 80.0% | +1.99% | 3.55% | $+0.15 |
| runner_hunter | 3 | 4 | 75.0% | +3.46% | 2.60% | $+0.10 |
| diy_whale | 11 | 11 | 27.3% | -2.51% | 45.04% | $-0.21 |

Average net trade return is NOT daily portfolio return. Compare capital-normalized equity changes separately; no-trade sleeves have insufficient evidence.

No live promotion occurs automatically. Any change requires explicit approval.
