# CryptoTracker paper research — 2026-10-20

| Model | Trades | Shadow | W/L | Avg net | Median | Max DD | PnL | PF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| diy_whale | 8 | 19 | 5/3 | +4.15% | +0.51% | 0.16% | +0.2489 | 8.61 |
| flow_breakout | 0 | 16 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| whale_luna | 0 | 4 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| early_breakout | 0 | 16 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| extended_probe | 0 | 6 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| novelty_probe | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| strict_baseline | 4 | 11 | 0/4 | -0.50% | -0.36% | 2.01% | -0.0303 | 0.00 |
| runner_hunter | 2 | 11 | 0/2 | -1.42% | -1.42% | 0.14% | -0.0214 | 0.00 |
| patient_runner | 1 | 24 | 0/1 | -6.56% | -6.56% | 6.56% | -0.0984 | 0.00 |
| fast_exit | 1 | 24 | 0/1 | -6.56% | -6.56% | 6.56% | -0.0984 | 0.00 |
| regime_filtered | 1 | 4 | 0/1 | -8.53% | -8.53% | 8.53% | -0.1279 | 0.00 |
| staged_runner | 1 | 0 | 0/1 | -8.67% | -8.67% | 8.67% | -0.1301 | 0.00 |
| balanced_ev | 1 | 24 | 0/1 | -9.88% | -9.88% | 0.88% | -0.1482 | 0.00 |
| low_friction | 1 | 24 | 0/1 | -10.01% | -10.01% | 10.01% | -0.1501 | 0.00 |
| anti_chase | 1 | 23 | 0/1 | -10.11% | -10.11% | 10.11% | -0.1517 | 0.00 |

## Three-sleeve comparison

| Sleeve | Entries | Closed | Win rate | Avg trade net | Max DD | Realized PnL |
|---|---:|---:|---:|---:|---:|---:|
| balanced_ev | 2 | 1 | 0.0% | -9.88% | 0.88% | $-0.15 |
| runner_hunter | 3 | 2 | 0.0% | -1.42% | 0.14% | $-0.02 |
| diy_whale | 9 | 8 | 62.5% | +4.15% | 0.16% | $+0.25 |

## 1% daily goal — realized-equity proxy (not portfolio return)

| Sleeve | Daily realized-equity return | Daily target | Hit? | Since inception realized-equity return | Compounded target since first observed entry | Gap (USD) | Realized-equity DD since inception |
|---|---:|---:|---|---:|---:|---:|---:|
| balanced_ev | -0.88% | +1.00% | False | +10.69% | +24.47% | -2.06655617 | +11.93% |
| runner_hunter | -0.14% | +1.00% | False | -1.48% | +12.68% | -2.12444545 | +3.15% |
| diy_whale | +1.70% | +1.00% | True | -0.46% | +12.68% | -1.97086445 | +9.82% |

**Warning:** These are completed-trade realized-equity measurements, not mark-to-market portfolio returns. Open-position losses are excluded. The target compounds 1% per calendar day, not per trade.

Average net trade return is NOT daily portfolio return. Compare capital-normalized equity changes separately; no-trade sleeves have insufficient evidence.

No live promotion occurs automatically. Any change requires explicit approval.
