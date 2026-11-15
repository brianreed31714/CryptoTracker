# CryptoTracker paper research — 2026-11-14

| Model | Trades | Shadow | W/L | Avg net | Median | Max DD | PnL | PF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| staged_runner | 4 | 0 | 3/1 | +0.62% | +0.27% | 0.62% | +0.0371 | 4.98 |
| patient_runner | 4 | 25 | 3/1 | +0.59% | +0.20% | 0.63% | +0.0352 | 4.74 |
| anti_chase | 6 | 30 | 3/3 | +0.55% | +0.00% | 0.80% | +0.0497 | 3.23 |
| fast_exit | 4 | 25 | 1/3 | +0.15% | -0.13% | 1.08% | +0.0089 | 1.55 |
| balanced_ev | 4 | 25 | 1/3 | +0.02% | -0.38% | 0.16% | +0.0011 | 1.04 |
| whale_luna | 0 | 6 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| novelty_probe | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| regime_filtered | 1 | 5 | 0/1 | -0.27% | -0.27% | 0.27% | -0.0040 | 0.00 |
| low_friction | 4 | 28 | 1/3 | -0.32% | -0.39% | 1.57% | -0.0194 | 0.18 |
| early_breakout | 3 | 15 | 1/2 | -0.34% | -0.21% | 1.01% | -0.0076 | 0.00 |
| flow_breakout | 3 | 19 | 0/3 | -0.35% | -0.23% | 1.04% | -0.0157 | 0.00 |
| extended_probe | 3 | 7 | 1/2 | -0.45% | -4.40% | 4.74% | -0.0101 | 0.85 |
| runner_hunter | 3 | 12 | 1/2 | -0.50% | -1.51% | 0.29% | -0.0112 | 0.76 |
| strict_baseline | 1 | 5 | 0/1 | -1.60% | -1.60% | 1.60% | -0.0240 | 0.00 |
| diy_whale | 10 | 16 | 4/6 | -3.72% | -1.52% | 3.02% | -0.2791 | 0.13 |

## Three-sleeve comparison

| Sleeve | Entries | Closed | Win rate | Avg trade net | Max DD | Realized PnL |
|---|---:|---:|---:|---:|---:|---:|
| balanced_ev | 4 | 4 | 25.0% | +0.02% | 0.16% | $+0.00 |
| runner_hunter | 3 | 3 | 33.3% | -0.50% | 0.29% | $-0.01 |
| diy_whale | 10 | 10 | 40.0% | -3.72% | 3.02% | $-0.28 |

## 1% daily goal — realized-equity proxy (not portfolio return)

| Sleeve | Daily realized-equity return | Daily target | Hit? | Since inception realized-equity return | Compounded target since first observed entry | Gap (USD) | Realized-equity DD since inception |
|---|---:|---:|---|---:|---:|---:|---:|
| balanced_ev | +0.01% | +1.00% | False | +0.78% | +59.63% | -8.82673592 | +12.54% |
| runner_hunter | -0.09% | +1.00% | False | -17.60% | +44.51% | -9.31556807 | +17.60% |
| diy_whale | -2.99% | +1.00% | False | -39.66% | +44.51% | -12.62521407 | +40.09% |

**Warning:** These are completed-trade realized-equity measurements, not mark-to-market portfolio returns. Open-position losses are excluded. The target compounds 1% per calendar day, not per trade.

Average net trade return is NOT daily portfolio return. Compare capital-normalized equity changes separately; no-trade sleeves have insufficient evidence.

No live promotion occurs automatically. Any change requires explicit approval.
