# CryptoTracker paper research — 2026-10-31

| Model | Trades | Shadow | W/L | Avg net | Median | Max DD | PnL | PF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| diy_whale | 25 | 39 | 10/15 | -0.41% | -0.22% | 1.53% | -0.0768 | 0.80 |
| early_breakout | 1 | 30 | 1/0 | +2.63% | +2.63% | 0.00% | +0.0197 | 999.00 |
| flow_breakout | 1 | 35 | 1/0 | +2.45% | +2.45% | 0.00% | +0.0367 | 999.00 |
| whale_luna | 2 | 10 | 1/1 | +0.36% | +0.36% | 2.54% | +0.0108 | 1.28 |
| regime_filtered | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| novelty_probe | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| anti_chase | 8 | 52 | 3/5 | -0.82% | -2.15% | 8.16% | -0.0984 | 0.53 |
| patient_runner | 7 | 49 | 4/3 | -0.94% | +1.10% | 16.10% | -0.0992 | 0.63 |
| staged_runner | 7 | 0 | 4/3 | -1.13% | +0.14% | 16.14% | -0.1188 | 0.54 |
| fast_exit | 8 | 49 | 4/4 | -1.17% | -0.57% | 13.87% | -0.1398 | 0.46 |
| balanced_ev | 8 | 49 | 3/5 | -1.50% | -2.43% | 1.33% | -0.1800 | 0.38 |
| low_friction | 1 | 53 | 0/1 | -2.67% | -2.67% | 2.67% | -0.0401 | 0.00 |
| strict_baseline | 5 | 19 | 2/3 | -2.92% | -3.30% | 14.30% | -0.2192 | 0.22 |
| runner_hunter | 8 | 28 | 1/7 | -4.65% | -2.92% | 2.10% | -0.2790 | 0.08 |
| extended_probe | 3 | 10 | 0/3 | -9.28% | -13.36% | 25.81% | -0.2088 | 0.00 |

## Three-sleeve comparison

| Sleeve | Entries | Closed | Win rate | Avg trade net | Max DD | Realized PnL |
|---|---:|---:|---:|---:|---:|---:|
| balanced_ev | 8 | 8 | 37.5% | -1.50% | 1.33% | $-0.18 |
| runner_hunter | 8 | 8 | 12.5% | -4.65% | 2.10% | $-0.28 |
| diy_whale | 26 | 25 | 40.0% | -0.41% | 1.53% | $-0.08 |

## 1% daily goal — realized-equity proxy (not portfolio return)

| Sleeve | Daily realized-equity return | Daily target | Hit? | Since inception realized-equity return | Compounded target since first observed entry | Gap (USD) | Realized-equity DD since inception |
|---|---:|---:|---|---:|---:|---:|---:|
| balanced_ev | -1.12% | +1.00% | False | +6.26% | +38.87% | -4.89171855 | +11.93% |
| runner_hunter | -2.10% | +1.00% | False | -13.11% | +25.72% | -5.82435528 | +13.11% |
| diy_whale | -0.64% | +1.00% | False | -20.97% | +25.72% | -7.00274428 | +28.03% |

**Warning:** These are completed-trade realized-equity measurements, not mark-to-market portfolio returns. Open-position losses are excluded. The target compounds 1% per calendar day, not per trade.

Average net trade return is NOT daily portfolio return. Compare capital-normalized equity changes separately; no-trade sleeves have insufficient evidence.

No live promotion occurs automatically. Any change requires explicit approval.
