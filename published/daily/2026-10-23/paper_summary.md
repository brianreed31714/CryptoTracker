# CryptoTracker paper research — 2026-10-23

| Model | Trades | Shadow | W/L | Avg net | Median | Max DD | PnL | PF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| diy_whale | 22 | 24 | 10/12 | -4.86% | -1.26% | 5.87% | -0.8022 | 0.26 |
| strict_baseline | 10 | 24 | 5/5 | +1.47% | +1.17% | 23.79% | +0.2205 | 1.48 |
| whale_luna | 0 | 13 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| low_friction | 0 | 47 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| regime_filtered | 0 | 2 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| novelty_probe | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| extended_probe | 3 | 12 | 1/2 | -1.34% | -3.63% | 8.00% | -0.0302 | 0.51 |
| fast_exit | 3 | 40 | 0/3 | -1.96% | -2.10% | 5.77% | -0.0882 | 0.00 |
| balanced_ev | 3 | 40 | 0/3 | -1.99% | -2.12% | 0.54% | -0.0896 | 0.00 |
| anti_chase | 5 | 44 | 1/4 | -2.04% | -2.12% | 10.24% | -0.1527 | 0.04 |
| flow_breakout | 1 | 28 | 0/1 | -2.10% | -2.10% | 2.10% | -0.0316 | 0.00 |
| staged_runner | 3 | 0 | 0/3 | -2.25% | -2.32% | 6.61% | -0.1011 | 0.00 |
| patient_runner | 3 | 40 | 0/3 | -2.25% | -2.32% | 6.62% | -0.1013 | 0.00 |
| early_breakout | 2 | 25 | 0/2 | -2.34% | -2.34% | 4.62% | -0.0351 | 0.00 |
| runner_hunter | 10 | 23 | 3/7 | -3.45% | -4.18% | 2.01% | -0.2586 | 0.32 |

## Three-sleeve comparison

| Sleeve | Entries | Closed | Win rate | Avg trade net | Max DD | Realized PnL |
|---|---:|---:|---:|---:|---:|---:|
| balanced_ev | 3 | 3 | 0.0% | -1.99% | 0.54% | $-0.09 |
| runner_hunter | 10 | 10 | 30.0% | -3.45% | 2.01% | $-0.26 |
| diy_whale | 22 | 22 | 45.5% | -4.86% | 5.87% | $-0.80 |

## 1% daily goal — realized-equity proxy (not portfolio return)

| Sleeve | Daily realized-equity return | Daily target | Hit? | Since inception realized-equity return | Compounded target since first observed entry | Gap (USD) | Realized-equity DD since inception |
|---|---:|---:|---|---:|---:|---:|---:|
| balanced_ev | -0.54% | +1.00% | False | +11.01% | +28.24% | -2.5848852 | +11.93% |
| runner_hunter | -1.79% | +1.00% | False | -5.62% | +16.10% | -3.25745033 | +5.83% |
| diy_whale | -5.62% | +1.00% | False | -10.18% | +16.10% | -3.94089433 | +10.79% |

**Warning:** These are completed-trade realized-equity measurements, not mark-to-market portfolio returns. Open-position losses are excluded. The target compounds 1% per calendar day, not per trade.

Average net trade return is NOT daily portfolio return. Compare capital-normalized equity changes separately; no-trade sleeves have insufficient evidence.

No live promotion occurs automatically. Any change requires explicit approval.
