# CryptoTracker paper research — 2026-10-26

| Model | Trades | Shadow | W/L | Avg net | Median | Max DD | PnL | PF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| diy_whale | 16 | 27 | 6/10 | -1.10% | -0.57% | 1.77% | -0.1322 | 0.58 |
| strict_baseline | 5 | 16 | 2/3 | +5.02% | -0.69% | 11.24% | +0.3761 | 3.04 |
| fast_exit | 1 | 34 | 1/0 | +0.23% | +0.23% | 0.00% | +0.0034 | 999.00 |
| flow_breakout | 0 | 28 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| whale_luna | 0 | 11 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| early_breakout | 0 | 22 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| low_friction | 0 | 36 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| regime_filtered | 0 | 3 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| anti_chase | 0 | 37 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| novelty_probe | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| staged_runner | 1 | 0 | 0/1 | -0.68% | -0.68% | 0.68% | -0.0103 | 0.00 |
| patient_runner | 1 | 33 | 0/1 | -0.68% | -0.68% | 0.68% | -0.0103 | 0.00 |
| balanced_ev | 1 | 34 | 0/1 | -1.35% | -1.35% | 0.12% | -0.0203 | 0.00 |
| runner_hunter | 4 | 19 | 1/3 | -19.04% | -5.80% | 4.02% | -0.5712 | 0.01 |
| extended_probe | 1 | 7 | 0/1 | -65.47% | -65.47% | 65.47% | -0.4910 | 0.00 |

## Three-sleeve comparison

| Sleeve | Entries | Closed | Win rate | Avg trade net | Max DD | Realized PnL |
|---|---:|---:|---:|---:|---:|---:|
| balanced_ev | 1 | 1 | 0.0% | -1.35% | 0.12% | $-0.02 |
| runner_hunter | 4 | 4 | 25.0% | -19.04% | 4.02% | $-0.57 |
| diy_whale | 16 | 16 | 37.5% | -1.10% | 1.77% | $-0.13 |

## 1% daily goal — realized-equity proxy (not portfolio return)

| Sleeve | Daily realized-equity return | Daily target | Hit? | Since inception realized-equity return | Compounded target since first observed entry | Gap (USD) | Realized-equity DD since inception |
|---|---:|---:|---|---:|---:|---:|---:|
| balanced_ev | -0.12% | +1.00% | False | +10.91% | +32.13% | -3.18283977 | +11.93% |
| runner_hunter | -4.02% | +1.00% | False | -9.18% | +19.61% | -4.31907914 | +9.18% |
| diy_whale | -1.02% | +1.00% | False | -14.74% | +19.61% | -5.15382414 | +15.96% |

**Warning:** These are completed-trade realized-equity measurements, not mark-to-market portfolio returns. Open-position losses are excluded. The target compounds 1% per calendar day, not per trade.

Average net trade return is NOT daily portfolio return. Compare capital-normalized equity changes separately; no-trade sleeves have insufficient evidence.

No live promotion occurs automatically. Any change requires explicit approval.
