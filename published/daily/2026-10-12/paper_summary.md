# CryptoTracker paper research — 2026-10-12

| Model | Trades | Shadow | W/L | Avg net | Median | Max DD | PnL | PF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| strict_baseline | 4 | 7 | 3/1 | +5.07% | +3.86% | 3.27% | +0.3044 | 7.21 |
| patient_runner | 1 | 14 | 1/0 | +4.41% | +4.41% | 0.00% | +0.0662 | 999.00 |
| staged_runner | 1 | 0 | 1/0 | +4.39% | +4.39% | 0.00% | +0.0658 | 999.00 |
| balanced_ev | 1 | 14 | 1/0 | +1.78% | +1.78% | 0.00% | +0.0267 | 999.00 |
| fast_exit | 1 | 14 | 1/0 | +0.50% | +0.50% | 0.00% | +0.0076 | 999.00 |
| flow_breakout | 0 | 11 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| whale_luna | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| early_breakout | 0 | 8 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| low_friction | 0 | 15 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| regime_filtered | 0 | 7 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| anti_chase | 0 | 14 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| extended_probe | 0 | 7 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| novelty_probe | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| diy_whale | 9 | 10 | 4/5 | -1.09% | -0.90% | 26.74% | -0.0738 | 0.67 |
| runner_hunter | 4 | 10 | 2/2 | -1.45% | -2.36% | 13.56% | -0.0435 | 0.59 |

## Three-sleeve comparison

| Sleeve | Entries | Closed | Win rate | Avg trade net | Max DD | Realized PnL |
|---|---:|---:|---:|---:|---:|---:|
| balanced_ev | 1 | 1 | 100.0% | +1.78% | 0.00% | $+0.03 |
| runner_hunter | 4 | 4 | 50.0% | -1.45% | 13.56% | $-0.04 |
| diy_whale | 8 | 9 | 44.4% | -1.09% | 26.74% | $-0.07 |

Average net trade return is NOT daily portfolio return. Compare capital-normalized equity changes separately; no-trade sleeves have insufficient evidence.

No live promotion occurs automatically. Any change requires explicit approval.
