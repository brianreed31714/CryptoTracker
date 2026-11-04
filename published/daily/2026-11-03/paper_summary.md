# CryptoTracker paper research — 2026-11-03

| Model | Trades | Shadow | W/L | Avg net | Median | Max DD | PnL | PF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| diy_whale | 15 | 28 | 8/7 | -0.02% | +0.87% | 0.97% | -0.0021 | 0.99 |
| anti_chase | 13 | 51 | 3/10 | -0.86% | -0.47% | 10.76% | -0.1668 | 0.02 |
| balanced_ev | 12 | 46 | 3/9 | -1.40% | -0.61% | 1.62% | -0.2517 | 0.02 |
| fast_exit | 12 | 46 | 2/10 | -1.41% | -1.02% | 15.83% | -0.2546 | 0.05 |
| whale_luna | 2 | 8 | 1/1 | +0.42% | +0.42% | 0.43% | +0.0125 | 2.95 |
| regime_filtered | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| extended_probe | 0 | 6 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| novelty_probe | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| low_friction | 3 | 50 | 2/1 | -0.43% | +0.05% | 2.60% | -0.0193 | 0.51 |
| flow_breakout | 3 | 30 | 0/3 | -0.97% | -0.56% | 2.88% | -0.0435 | 0.00 |
| early_breakout | 4 | 30 | 0/4 | -1.15% | -1.12% | 4.52% | -0.0345 | 0.00 |
| patient_runner | 11 | 46 | 3/8 | -1.45% | -0.99% | 15.16% | -0.2393 | 0.16 |
| staged_runner | 11 | 0 | 3/8 | -1.54% | -0.98% | 16.00% | -0.2534 | 0.15 |
| strict_baseline | 8 | 18 | 2/6 | -4.52% | -2.84% | 32.02% | -0.5424 | 0.06 |
| runner_hunter | 4 | 15 | 0/4 | -7.08% | -7.44% | 1.58% | -0.2125 | 0.00 |

## Three-sleeve comparison

| Sleeve | Entries | Closed | Win rate | Avg trade net | Max DD | Realized PnL |
|---|---:|---:|---:|---:|---:|---:|
| balanced_ev | 12 | 12 | 25.0% | -1.40% | 1.62% | $-0.25 |
| runner_hunter | 4 | 4 | 0.0% | -7.08% | 1.58% | $-0.21 |
| diy_whale | 16 | 15 | 53.3% | -0.02% | 0.97% | $-0.00 |

## 1% daily goal — realized-equity proxy (not portfolio return)

| Sleeve | Daily realized-equity return | Daily target | Hit? | Since inception realized-equity return | Compounded target since first observed entry | Gap (USD) | Realized-equity DD since inception |
|---|---:|---:|---|---:|---:|---:|---:|
| balanced_ev | -1.60% | +1.00% | False | +3.04% | +43.08% | -6.00526702 | +11.93% |
| runner_hunter | -1.58% | +1.00% | False | -11.47% | +29.53% | -6.14876172 | +13.62% |
| diy_whale | -0.02% | +1.00% | False | -25.61% | +29.53% | -8.27008972 | +28.03% |

**Warning:** These are completed-trade realized-equity measurements, not mark-to-market portfolio returns. Open-position losses are excluded. The target compounds 1% per calendar day, not per trade.

Average net trade return is NOT daily portfolio return. Compare capital-normalized equity changes separately; no-trade sleeves have insufficient evidence.

No live promotion occurs automatically. Any change requires explicit approval.
