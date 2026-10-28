# CryptoTracker paper research — 2026-10-22

| Model | Trades | Shadow | W/L | Avg net | Median | Max DD | PnL | PF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| diy_whale | 14 | 19 | 8/6 | +3.43% | +1.36% | 0.90% | +0.3606 | 2.21 |
| patient_runner | 4 | 28 | 2/2 | +6.44% | +3.52% | 10.20% | +0.3864 | 3.47 |
| staged_runner | 4 | 0 | 2/2 | +4.34% | +0.70% | 10.19% | +0.2602 | 2.66 |
| anti_chase | 5 | 29 | 3/2 | +3.67% | +3.01% | 2.82% | +0.2750 | 7.45 |
| balanced_ev | 4 | 28 | 2/2 | +3.35% | +3.11% | 0.46% | +0.2009 | 3.57 |
| fast_exit | 4 | 28 | 3/1 | +1.55% | +0.96% | 0.90% | +0.0930 | 7.86 |
| flow_breakout | 0 | 16 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| whale_luna | 0 | 2 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| early_breakout | 0 | 14 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| low_friction | 0 | 30 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| regime_filtered | 0 | 8 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| novelty_probe | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| strict_baseline | 4 | 11 | 2/2 | -0.67% | -1.35% | 6.98% | -0.0404 | 0.62 |
| runner_hunter | 7 | 21 | 2/5 | -7.45% | -1.28% | 3.53% | -0.3912 | 0.32 |
| extended_probe | 2 | 10 | 1/1 | -29.51% | -29.51% | 67.00% | -0.4427 | 0.12 |

## Three-sleeve comparison

| Sleeve | Entries | Closed | Win rate | Avg trade net | Max DD | Realized PnL |
|---|---:|---:|---:|---:|---:|---:|
| balanced_ev | 4 | 4 | 50.0% | +3.35% | 0.46% | $+0.20 |
| runner_hunter | 7 | 7 | 28.6% | -7.45% | 3.53% | $-0.39 |
| diy_whale | 14 | 14 | 57.1% | +3.43% | 0.90% | $+0.36 |

## 1% daily goal — realized-equity proxy (not portfolio return)

| Sleeve | Daily realized-equity return | Daily target | Hit? | Since inception realized-equity return | Compounded target since first observed entry | Gap (USD) | Realized-equity DD since inception |
|---|---:|---:|---|---:|---:|---:|---:|
| balanced_ev | +1.20% | +1.00% | True | +12.77% | +26.97% | -2.130766 | +11.93% |
| runner_hunter | -2.64% | +1.00% | False | -3.90% | +14.95% | -2.8264422 | +3.90% |
| diy_whale | +2.57% | +1.00% | True | -3.94% | +14.95% | -2.8335612 | +9.82% |

**Warning:** These are completed-trade realized-equity measurements, not mark-to-market portfolio returns. Open-position losses are excluded. The target compounds 1% per calendar day, not per trade.

Average net trade return is NOT daily portfolio return. Compare capital-normalized equity changes separately; no-trade sleeves have insufficient evidence.

No live promotion occurs automatically. Any change requires explicit approval.
