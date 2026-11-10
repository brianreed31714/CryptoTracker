# CryptoTracker paper research — 2026-11-09

| Model | Trades | Shadow | W/L | Avg net | Median | Max DD | PnL | PF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| fast_exit | 12 | 41 | 3/9 | -1.92% | -1.98% | 21.62% | -0.3458 | 0.18 |
| diy_whale | 16 | 23 | 2/14 | -2.11% | -1.24% | 2.39% | -0.2534 | 0.03 |
| anti_chase | 16 | 42 | 3/13 | -2.32% | -1.96% | 46.27% | -0.5576 | 0.37 |
| extended_probe | 1 | 3 | 1/0 | +3.09% | +3.09% | 0.00% | +0.0232 | 999.00 |
| regime_filtered | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| novelty_probe | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| low_friction | 2 | 41 | 1/1 | -0.18% | -0.18% | 1.03% | -0.0054 | 0.65 |
| early_breakout | 7 | 18 | 2/5 | -2.24% | -1.12% | 14.95% | -0.1175 | 0.09 |
| balanced_ev | 11 | 41 | 2/9 | -2.27% | -1.53% | 2.43% | -0.3741 | 0.05 |
| staged_runner | 11 | 0 | 2/9 | -2.68% | -2.90% | 27.40% | -0.4425 | 0.30 |
| patient_runner | 11 | 41 | 2/9 | -2.68% | -2.69% | 27.41% | -0.4428 | 0.30 |
| flow_breakout | 7 | 19 | 1/6 | -2.88% | -2.99% | 18.77% | -0.3022 | 0.05 |
| runner_hunter | 5 | 9 | 1/4 | -3.94% | -3.61% | 1.17% | -0.1476 | 0.14 |
| strict_baseline | 8 | 12 | 1/7 | -4.60% | -4.58% | 32.53% | -0.5520 | 0.14 |
| whale_luna | 1 | 4 | 0/1 | -13.96% | -13.96% | 13.96% | -0.2094 | 0.00 |

## Three-sleeve comparison

| Sleeve | Entries | Closed | Win rate | Avg trade net | Max DD | Realized PnL |
|---|---:|---:|---:|---:|---:|---:|
| balanced_ev | 11 | 11 | 18.2% | -2.27% | 2.43% | $-0.37 |
| runner_hunter | 5 | 5 | 20.0% | -3.94% | 1.17% | $-0.15 |
| diy_whale | 15 | 16 | 12.5% | -2.11% | 2.39% | $-0.25 |

## 1% daily goal — realized-equity proxy (not portfolio return)

| Sleeve | Daily realized-equity return | Daily target | Hit? | Since inception realized-equity return | Compounded target since first observed entry | Gap (USD) | Realized-equity DD since inception |
|---|---:|---:|---|---:|---:|---:|---:|
| balanced_ev | -2.38% | +1.00% | False | +2.31% | +51.88% | -7.43604169 | +12.54% |
| runner_hunter | -1.17% | +1.00% | False | -16.98% | +37.49% | -8.17117518 | +17.60% |
| diy_whale | -2.39% | +1.00% | False | -31.03% | +37.49% | -10.27917318 | +35.10% |

**Warning:** These are completed-trade realized-equity measurements, not mark-to-market portfolio returns. Open-position losses are excluded. The target compounds 1% per calendar day, not per trade.

Average net trade return is NOT daily portfolio return. Compare capital-normalized equity changes separately; no-trade sleeves have insufficient evidence.

No live promotion occurs automatically. Any change requires explicit approval.
