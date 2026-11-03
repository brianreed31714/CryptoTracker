# CryptoTracker paper research — 2026-11-02

| Model | Trades | Shadow | W/L | Avg net | Median | Max DD | PnL | PF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| anti_chase | 18 | 42 | 5/13 | -0.93% | -0.72% | 18.09% | -0.2518 | 0.43 |
| patient_runner | 17 | 41 | 7/10 | -0.97% | -0.38% | 24.65% | -0.2477 | 0.50 |
| staged_runner | 17 | 0 | 7/10 | -1.18% | -0.38% | 27.56% | -0.2999 | 0.46 |
| balanced_ev | 18 | 41 | 4/14 | -1.41% | -1.06% | 2.41% | -0.3813 | 0.31 |
| fast_exit | 18 | 41 | 5/13 | -1.44% | -1.21% | 23.64% | -0.3879 | 0.31 |
| diy_whale | 19 | 21 | 6/13 | -3.23% | -2.84% | 3.94% | -0.4603 | 0.18 |
| runner_hunter | 7 | 11 | 4/3 | +5.47% | +1.62% | 1.04% | +0.2872 | 2.63 |
| whale_luna | 3 | 5 | 1/2 | +0.37% | -0.85% | 2.88% | +0.0165 | 1.38 |
| low_friction | 2 | 45 | 1/1 | +0.26% | +0.26% | 3.55% | +0.0077 | 1.15 |
| early_breakout | 5 | 19 | 2/3 | +0.22% | -0.61% | 5.53% | +0.0084 | 1.20 |
| flow_breakout | 5 | 22 | 2/3 | +0.13% | -0.84% | 5.86% | +0.0096 | 1.11 |
| regime_filtered | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| novelty_probe | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| strict_baseline | 11 | 10 | 5/6 | -2.31% | -0.28% | 30.32% | -0.3816 | 0.32 |
| extended_probe | 1 | 4 | 0/1 | -8.59% | -8.59% | 8.59% | -0.0644 | 0.00 |

## Three-sleeve comparison

| Sleeve | Entries | Closed | Win rate | Avg trade net | Max DD | Realized PnL |
|---|---:|---:|---:|---:|---:|---:|
| balanced_ev | 18 | 18 | 22.2% | -1.41% | 2.41% | $-0.38 |
| runner_hunter | 7 | 7 | 57.1% | +5.47% | 1.04% | $+0.29 |
| diy_whale | 20 | 19 | 31.6% | -3.23% | 3.94% | $-0.46 |

## 1% daily goal — realized-equity proxy (not portfolio return)

| Sleeve | Daily realized-equity return | Daily target | Hit? | Since inception realized-equity return | Compounded target since first observed entry | Gap (USD) | Realized-equity DD since inception |
|---|---:|---:|---|---:|---:|---:|---:|
| balanced_ev | -2.37% | +1.00% | False | +4.59% | +41.66% | -5.56042761 | +11.93% |
| runner_hunter | +2.17% | +1.00% | True | -10.05% | +28.24% | -5.74387593 | +13.62% |
| diy_whale | -3.94% | +1.00% | False | -25.11% | +28.24% | -8.00239393 | +28.03% |

**Warning:** These are completed-trade realized-equity measurements, not mark-to-market portfolio returns. Open-position losses are excluded. The target compounds 1% per calendar day, not per trade.

Average net trade return is NOT daily portfolio return. Compare capital-normalized equity changes separately; no-trade sleeves have insufficient evidence.

No live promotion occurs automatically. Any change requires explicit approval.
