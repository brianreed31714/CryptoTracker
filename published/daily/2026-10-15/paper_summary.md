# CryptoTracker paper research — 2026-10-15

| Model | Trades | Shadow | W/L | Avg net | Median | Max DD | PnL | PF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| diy_whale | 18 | 21 | 7/11 | -6.35% | -1.98% | 99.67% | -0.8577 | 0.18 |
| regime_filtered | 2 | 2 | 2/0 | +5.28% | +5.28% | 0.00% | +0.1583 | 999.00 |
| staged_runner | 6 | 0 | 2/4 | +2.52% | -1.04% | 6.67% | +0.2268 | 3.22 |
| patient_runner | 6 | 35 | 2/4 | +2.31% | -1.00% | 6.60% | +0.2079 | 3.05 |
| balanced_ev | 7 | 35 | 3/4 | +1.33% | -0.50% | 6.10% | +0.1392 | 2.49 |
| fast_exit | 7 | 35 | 2/5 | +1.23% | -0.43% | 5.77% | +0.1287 | 2.11 |
| anti_chase | 7 | 33 | 2/5 | +0.54% | -0.52% | 6.64% | +0.0570 | 1.56 |
| strict_baseline | 8 | 16 | 2/6 | +0.10% | -1.40% | 17.96% | +0.0125 | 1.04 |
| whale_luna | 0 | 2 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| novelty_probe | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| low_friction | 5 | 42 | 1/4 | -0.88% | -0.90% | 6.13% | -0.0662 | 0.29 |
| early_breakout | 4 | 22 | 0/4 | -1.61% | -1.10% | 6.34% | -0.0484 | 0.00 |
| flow_breakout | 4 | 23 | 0/4 | -1.79% | -1.43% | 7.01% | -0.1075 | 0.00 |
| runner_hunter | 11 | 16 | 2/9 | -3.40% | -2.45% | 34.27% | -0.2802 | 0.29 |
| extended_probe | 4 | 8 | 1/3 | -9.70% | -8.12% | 35.18% | -0.2909 | 0.06 |

## Three-sleeve comparison

| Sleeve | Entries | Closed | Win rate | Avg trade net | Max DD | Realized PnL |
|---|---:|---:|---:|---:|---:|---:|
| balanced_ev | 7 | 7 | 42.9% | +1.33% | 6.10% | $+0.14 |
| runner_hunter | 11 | 11 | 18.2% | -3.40% | 34.27% | $-0.28 |
| diy_whale | 17 | 18 | 38.9% | -6.35% | 99.67% | $-0.86 |

Average net trade return is NOT daily portfolio return. Compare capital-normalized equity changes separately; no-trade sleeves have insufficient evidence.

No live promotion occurs automatically. Any change requires explicit approval.
