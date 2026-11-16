# CryptoTracker paper research — 2026-11-15

| Model | Trades | Shadow | W/L | Avg net | Median | Max DD | PnL | PF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| low_friction | 1 | 21 | 1/0 | +1.53% | +1.53% | 0.00% | +0.0230 | 999.00 |
| early_breakout | 2 | 10 | 1/1 | +0.47% | +0.47% | 0.62% | +0.0070 | 2.52 |
| flow_breakout | 2 | 11 | 1/1 | +0.44% | +0.44% | 0.64% | +0.0132 | 2.37 |
| fast_exit | 5 | 21 | 2/3 | +0.11% | -0.65% | 1.70% | +0.0086 | 1.20 |
| whale_luna | 0 | 3 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| extended_probe | 0 | 1 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| novelty_probe | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| runner_hunter | 0 | 5 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| regime_filtered | 1 | 2 | 0/1 | -0.36% | -0.36% | 0.36% | -0.0054 | 0.00 |
| strict_baseline | 2 | 8 | 1/1 | -0.75% | -0.75% | 3.54% | -0.0225 | 0.58 |
| anti_chase | 6 | 21 | 1/5 | -0.82% | -1.04% | 4.86% | -0.0737 | 0.24 |
| balanced_ev | 5 | 21 | 1/4 | -0.86% | -1.43% | 0.43% | -0.0647 | 0.26 |
| patient_runner | 5 | 21 | 1/4 | -1.12% | -1.45% | 5.51% | -0.0841 | 0.10 |
| staged_runner | 5 | 0 | 1/4 | -1.12% | -1.44% | 5.53% | -0.0843 | 0.10 |
| diy_whale | 6 | 10 | 1/5 | -5.31% | -5.64% | 2.65% | -0.2390 | 0.07 |

## Three-sleeve comparison

| Sleeve | Entries | Closed | Win rate | Avg trade net | Max DD | Realized PnL |
|---|---:|---:|---:|---:|---:|---:|
| balanced_ev | 5 | 5 | 20.0% | -0.86% | 0.43% | $-0.06 |
| runner_hunter | 0 | 0 | 0.0% | +0.00% | 0.00% | $+0.00 |
| diy_whale | 6 | 6 | 16.7% | -5.31% | 2.65% | $-0.24 |

## 1% daily goal — realized-equity proxy (not portfolio return)

| Sleeve | Daily realized-equity return | Daily target | Hit? | Since inception realized-equity return | Compounded target since first observed entry | Gap (USD) | Realized-equity DD since inception |
|---|---:|---:|---|---:|---:|---:|---:|
| balanced_ev | -0.43% | +1.00% | False | +0.35% | +61.22% | -9.13091244 | +12.54% |
| runner_hunter | +0.00% | +1.00% | False | -17.60% | +45.95% | -9.53232954 | +17.60% |
| diy_whale | -2.65% | +1.00% | False | -41.41% | +45.95% | -13.10384654 | +41.80% |

**Warning:** These are completed-trade realized-equity measurements, not mark-to-market portfolio returns. Open-position losses are excluded. The target compounds 1% per calendar day, not per trade.

Average net trade return is NOT daily portfolio return. Compare capital-normalized equity changes separately; no-trade sleeves have insufficient evidence.

No live promotion occurs automatically. Any change requires explicit approval.
