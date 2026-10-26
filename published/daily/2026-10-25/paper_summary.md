# CryptoTracker paper research — 2026-10-25

| Model | Trades | Shadow | W/L | Avg net | Median | Max DD | PnL | PF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| strict_baseline | 0 | 1 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| balanced_ev | 0 | 1 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| flow_breakout | 0 | 1 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| whale_luna | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| early_breakout | 0 | 1 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| low_friction | 0 | 1 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| fast_exit | 0 | 1 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| patient_runner | 0 | 1 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| regime_filtered | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| anti_chase | 0 | 1 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| extended_probe | 0 | 3 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| staged_runner | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| novelty_probe | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| runner_hunter | 0 | 3 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| diy_whale | 1 | 2 | 0/1 | -4.06% | -4.06% | 0.24% | -0.0304 | 0.00 |

## Three-sleeve comparison

| Sleeve | Entries | Closed | Win rate | Avg trade net | Max DD | Realized PnL |
|---|---:|---:|---:|---:|---:|---:|
| balanced_ev | 0 | 0 | 0.0% | +0.00% | 0.00% | $+0.00 |
| runner_hunter | 0 | 0 | 0.0% | +0.00% | 0.00% | $+0.00 |
| diy_whale | 1 | 1 | 0.0% | -4.06% | 0.24% | $-0.03 |

## 1% daily goal — realized-equity proxy (not portfolio return)

| Sleeve | Daily realized-equity return | Daily target | Hit? | Since inception realized-equity return | Compounded target since first observed entry | Gap (USD) | Realized-equity DD since inception |
|---|---:|---:|---|---:|---:|---:|---:|
| balanced_ev | +0.00% | +1.00% | False | +11.05% | +30.82% | -2.96635744 | +11.93% |
| runner_hunter | +0.00% | +1.00% | False | -5.62% | +18.43% | -3.60779947 | +5.83% |
| diy_whale | -0.24% | +1.00% | False | -14.14% | +18.43% | -4.88573847 | +14.72% |

**Warning:** These are completed-trade realized-equity measurements, not mark-to-market portfolio returns. Open-position losses are excluded. The target compounds 1% per calendar day, not per trade.

Average net trade return is NOT daily portfolio return. Compare capital-normalized equity changes separately; no-trade sleeves have insufficient evidence.

No live promotion occurs automatically. Any change requires explicit approval.
