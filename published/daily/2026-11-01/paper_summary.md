# CryptoTracker paper research — 2026-11-01

| Model | Trades | Shadow | W/L | Avg net | Median | Max DD | PnL | PF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| balanced_ev | 16 | 42 | 7/9 | +0.45% | -0.26% | 1.28% | +0.1087 | 1.34 |
| fast_exit | 16 | 42 | 6/10 | +0.27% | -0.41% | 13.36% | +0.0637 | 1.20 |
| diy_whale | 19 | 34 | 8/11 | +0.07% | -0.16% | 0.86% | +0.0102 | 1.05 |
| anti_chase | 16 | 43 | 6/10 | -0.00% | -0.75% | 16.27% | -0.0002 | 1.00 |
| staged_runner | 15 | 0 | 6/9 | -1.12% | -0.63% | 23.73% | -0.2509 | 0.41 |
| patient_runner | 15 | 42 | 5/10 | -1.43% | -1.19% | 23.98% | -0.3224 | 0.29 |
| extended_probe | 1 | 8 | 1/0 | +21.56% | +21.56% | 0.00% | +0.1617 | 999.00 |
| runner_hunter | 6 | 15 | 2/4 | +3.62% | -0.79% | 0.59% | +0.1628 | 3.13 |
| low_friction | 3 | 46 | 2/1 | +0.52% | +0.79% | 1.05% | +0.0234 | 2.49 |
| regime_filtered | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| novelty_probe | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| strict_baseline | 7 | 14 | 4/3 | -0.78% | +0.31% | 8.88% | -0.0818 | 0.55 |
| flow_breakout | 8 | 25 | 2/6 | -1.64% | -1.87% | 12.56% | -0.1967 | 0.17 |
| early_breakout | 5 | 25 | 1/4 | -2.04% | -2.13% | 9.91% | -0.0767 | 0.06 |
| whale_luna | 2 | 5 | 1/1 | -2.11% | -2.11% | 5.64% | -0.0634 | 0.25 |

## Three-sleeve comparison

| Sleeve | Entries | Closed | Win rate | Avg trade net | Max DD | Realized PnL |
|---|---:|---:|---:|---:|---:|---:|
| balanced_ev | 16 | 16 | 43.8% | +0.45% | 1.28% | $+0.11 |
| runner_hunter | 6 | 6 | 33.3% | +3.62% | 0.59% | $+0.16 |
| diy_whale | 19 | 19 | 42.1% | +0.07% | 0.86% | $+0.01 |

## 1% daily goal — realized-equity proxy (not portfolio return)

| Sleeve | Daily realized-equity return | Daily target | Hit? | Since inception realized-equity return | Compounded target since first observed entry | Gap (USD) | Realized-equity DD since inception |
|---|---:|---:|---|---:|---:|---:|---:|
| balanced_ev | +0.68% | +1.00% | False | +6.98% | +40.26% | -4.99132206 | +11.93% |
| runner_hunter | +1.25% | +1.00% | True | -12.03% | +26.97% | -5.85008173 | +13.62% |
| diy_whale | +0.09% | +1.00% | False | -22.29% | +26.97% | -7.38878273 | +28.03% |

**Warning:** These are completed-trade realized-equity measurements, not mark-to-market portfolio returns. Open-position losses are excluded. The target compounds 1% per calendar day, not per trade.

Average net trade return is NOT daily portfolio return. Compare capital-normalized equity changes separately; no-trade sleeves have insufficient evidence.

No live promotion occurs automatically. Any change requires explicit approval.
