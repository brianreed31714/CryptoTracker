# CryptoTracker paper research — 2026-10-28

| Model | Trades | Shadow | W/L | Avg net | Median | Max DD | PnL | PF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| runner_hunter | 14 | 28 | 4/10 | -2.30% | -1.19% | 1.84% | -0.2411 | 0.28 |
| strict_baseline | 13 | 18 | 3/10 | -2.32% | -1.22% | 31.60% | -0.4523 | 0.22 |
| diy_whale | 32 | 37 | 8/24 | -2.44% | -1.68% | 4.75% | -0.5844 | 0.27 |
| whale_luna | 0 | 7 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| low_friction | 0 | 51 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| novelty_probe | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| early_breakout | 6 | 24 | 1/5 | -1.31% | -0.93% | 7.69% | -0.0590 | 0.04 |
| flow_breakout | 6 | 27 | 1/5 | -1.45% | -0.98% | 8.49% | -0.1309 | 0.01 |
| anti_chase | 10 | 50 | 1/9 | -2.88% | -1.18% | 26.64% | -0.4318 | 0.03 |
| fast_exit | 10 | 46 | 1/9 | -3.32% | -1.35% | 29.35% | -0.4984 | 0.01 |
| balanced_ev | 10 | 46 | 1/9 | -3.77% | -1.77% | 3.53% | -0.5648 | 0.03 |
| patient_runner | 9 | 46 | 1/8 | -4.94% | -5.10% | 37.62% | -0.6672 | 0.01 |
| staged_runner | 9 | 0 | 1/8 | -4.94% | -5.10% | 37.62% | -0.6673 | 0.01 |
| extended_probe | 3 | 14 | 0/3 | -9.25% | -4.63% | 26.31% | -0.2081 | 0.00 |
| regime_filtered | 1 | 8 | 0/1 | -12.44% | -12.44% | 12.44% | -0.1867 | 0.00 |

## Three-sleeve comparison

| Sleeve | Entries | Closed | Win rate | Avg trade net | Max DD | Realized PnL |
|---|---:|---:|---:|---:|---:|---:|
| balanced_ev | 10 | 10 | 10.0% | -3.77% | 3.53% | $-0.56 |
| runner_hunter | 14 | 14 | 28.6% | -2.30% | 1.84% | $-0.24 |
| diy_whale | 32 | 32 | 25.0% | -2.44% | 4.75% | $-0.58 |

## 1% daily goal — realized-equity proxy (not portfolio return)

| Sleeve | Daily realized-equity return | Daily target | Hit? | Since inception realized-equity return | Compounded target since first observed entry | Gap (USD) | Realized-equity DD since inception |
|---|---:|---:|---|---:|---:|---:|---:|
| balanced_ev | -3.44% | +1.00% | False | +5.61% | +34.78% | -4.3758 | +11.93% |
| runner_hunter | -1.77% | +1.00% | False | -10.75% | +22.02% | -4.9155666 | +10.75% |
| diy_whale | -4.74% | +1.00% | False | -21.74% | +22.02% | -6.5641746 | +22.28% |

**Warning:** These are completed-trade realized-equity measurements, not mark-to-market portfolio returns. Open-position losses are excluded. The target compounds 1% per calendar day, not per trade.

Average net trade return is NOT daily portfolio return. Compare capital-normalized equity changes separately; no-trade sleeves have insufficient evidence.

No live promotion occurs automatically. Any change requires explicit approval.
