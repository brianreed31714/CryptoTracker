# CryptoTracker paper research — 2026-10-29

| Model | Trades | Shadow | W/L | Avg net | Median | Max DD | PnL | PF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| strict_baseline | 12 | 18 | 4/8 | -3.51% | -2.34% | 44.20% | -0.6313 | 0.32 |
| diy_whale | 19 | 38 | 7/12 | -4.44% | -1.04% | 7.24% | -0.6322 | 0.51 |
| patient_runner | 8 | 47 | 6/2 | +6.41% | +0.40% | 2.38% | +0.7698 | 22.42 |
| staged_runner | 8 | 0 | 6/2 | +6.00% | +0.41% | 2.41% | +0.7199 | 20.83 |
| whale_luna | 5 | 6 | 4/1 | +4.13% | +1.73% | 0.64% | +0.3099 | 33.20 |
| anti_chase | 10 | 45 | 7/3 | +2.98% | +1.36% | 4.88% | +0.4477 | 7.03 |
| balanced_ev | 10 | 47 | 6/4 | +1.65% | +0.40% | 0.58% | +0.2472 | 3.63 |
| fast_exit | 10 | 47 | 6/4 | +1.53% | +0.43% | 3.63% | +0.2294 | 5.16 |
| extended_probe | 1 | 14 | 1/0 | +1.25% | +1.25% | 0.00% | +0.0094 | 999.00 |
| flow_breakout | 6 | 31 | 4/2 | +1.17% | +0.40% | 1.50% | +0.1055 | 5.67 |
| runner_hunter | 3 | 22 | 1/2 | +0.50% | -2.41% | 0.29% | +0.0113 | 1.29 |
| early_breakout | 3 | 28 | 2/1 | +0.48% | +0.05% | 0.80% | +0.0107 | 2.77 |
| regime_filtered | 0 | 2 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| novelty_probe | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| low_friction | 3 | 49 | 1/2 | -0.59% | -0.64% | 2.34% | -0.0265 | 0.25 |

## Three-sleeve comparison

| Sleeve | Entries | Closed | Win rate | Avg trade net | Max DD | Realized PnL |
|---|---:|---:|---:|---:|---:|---:|
| balanced_ev | 10 | 10 | 60.0% | +1.65% | 0.58% | $+0.25 |
| runner_hunter | 3 | 3 | 33.3% | +0.50% | 0.29% | $+0.01 |
| diy_whale | 20 | 19 | 36.8% | -4.44% | 7.24% | $-0.63 |

## 1% daily goal — realized-equity proxy (not portfolio return)

| Sleeve | Daily realized-equity return | Daily target | Hit? | Since inception realized-equity return | Compounded target since first observed entry | Gap (USD) | Realized-equity DD since inception |
|---|---:|---:|---|---:|---:|---:|---:|
| balanced_ev | +1.56% | +1.00% | True | +7.26% | +36.13% | -4.33078634 | +11.93% |
| runner_hunter | +0.08% | +1.00% | False | -10.68% | +23.24% | -5.08727811 | +10.75% |
| diy_whale | -5.39% | +1.00% | False | -26.09% | +23.24% | -7.39999311 | +28.03% |

**Warning:** These are completed-trade realized-equity measurements, not mark-to-market portfolio returns. Open-position losses are excluded. The target compounds 1% per calendar day, not per trade.

Average net trade return is NOT daily portfolio return. Compare capital-normalized equity changes separately; no-trade sleeves have insufficient evidence.

No live promotion occurs automatically. Any change requires explicit approval.
