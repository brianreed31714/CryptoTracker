# CryptoTracker paper research — 2026-11-06

| Model | Trades | Shadow | W/L | Avg net | Median | Max DD | PnL | PF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| diy_whale | 20 | 25 | 5/15 | -2.89% | -2.03% | 4.12% | -0.4334 | 0.19 |
| extended_probe | 1 | 6 | 1/0 | +7.64% | +7.64% | 0.00% | +0.0573 | 999.00 |
| regime_filtered | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| novelty_probe | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| low_friction | 1 | 29 | 0/1 | -0.33% | -0.33% | 0.33% | -0.0050 | 0.00 |
| whale_luna | 1 | 2 | 0/1 | -1.11% | -1.11% | 1.11% | -0.0166 | 0.00 |
| flow_breakout | 5 | 17 | 1/4 | -1.47% | -0.96% | 7.21% | -0.1101 | 0.03 |
| patient_runner | 9 | 28 | 2/7 | -1.66% | -0.87% | 17.39% | -0.2235 | 0.21 |
| staged_runner | 9 | 0 | 2/7 | -1.71% | -0.87% | 17.84% | -0.2315 | 0.21 |
| early_breakout | 4 | 13 | 1/3 | -1.74% | -0.58% | 6.89% | -0.0521 | 0.03 |
| anti_chase | 8 | 29 | 2/6 | -1.92% | -1.15% | 14.72% | -0.2301 | 0.20 |
| runner_hunter | 4 | 11 | 2/2 | -2.51% | -2.27% | 1.17% | -0.0754 | 0.50 |
| strict_baseline | 7 | 10 | 2/5 | -2.52% | -0.72% | 17.45% | -0.2644 | 0.07 |
| balanced_ev | 10 | 28 | 1/9 | -2.70% | -1.58% | 2.53% | -0.4051 | 0.01 |
| fast_exit | 10 | 28 | 1/9 | -2.76% | -1.61% | 24.69% | -0.4145 | 0.01 |

## Three-sleeve comparison

| Sleeve | Entries | Closed | Win rate | Avg trade net | Max DD | Realized PnL |
|---|---:|---:|---:|---:|---:|---:|
| balanced_ev | 10 | 10 | 10.0% | -2.70% | 2.53% | $-0.41 |
| runner_hunter | 4 | 4 | 50.0% | -2.51% | 1.17% | $-0.08 |
| diy_whale | 20 | 20 | 25.0% | -2.89% | 4.12% | $-0.43 |

## 1% daily goal — realized-equity proxy (not portfolio return)

| Sleeve | Daily realized-equity return | Daily target | Hit? | Since inception realized-equity return | Compounded target since first observed entry | Gap (USD) | Realized-equity DD since inception |
|---|---:|---:|---|---:|---:|---:|---:|
| balanced_ev | -2.53% | +1.00% | False | +3.94% | +47.41% | -6.5208609 | +11.93% |
| runner_hunter | -0.59% | +1.00% | False | -14.75% | +33.45% | -7.22939215 | +15.13% |
| diy_whale | -4.12% | +1.00% | False | -32.77% | +33.45% | -9.93261315 | +33.22% |

**Warning:** These are completed-trade realized-equity measurements, not mark-to-market portfolio returns. Open-position losses are excluded. The target compounds 1% per calendar day, not per trade.

Average net trade return is NOT daily portfolio return. Compare capital-normalized equity changes separately; no-trade sleeves have insufficient evidence.

No live promotion occurs automatically. Any change requires explicit approval.
