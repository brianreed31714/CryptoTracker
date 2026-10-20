# CryptoTracker paper research — 2026-10-19

| Model | Trades | Shadow | W/L | Avg net | Median | Max DD | PnL | PF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| diy_whale | 19 | 22 | 11/8 | +5.20% | +0.70% | 0.73% | +0.7414 | 3.23 |
| flow_breakout | 3 | 22 | 2/1 | +16.52% | +9.28% | 0.34% | +0.7435 | 148.43 |
| anti_chase | 4 | 34 | 2/2 | +10.35% | +4.54% | 8.47% | +0.6212 | 5.73 |
| extended_probe | 4 | 6 | 1/3 | +6.71% | -3.36% | 12.71% | +0.2014 | 3.03 |
| early_breakout | 2 | 21 | 1/1 | +4.91% | +4.91% | 0.28% | +0.0736 | 36.21 |
| staged_runner | 7 | 0 | 3/4 | +4.88% | -0.19% | 16.96% | +0.5125 | 2.36 |
| balanced_ev | 8 | 31 | 3/5 | +4.54% | -0.37% | 1.19% | +0.5453 | 3.14 |
| patient_runner | 7 | 30 | 3/4 | +4.47% | -0.15% | 17.00% | +0.4693 | 2.25 |
| fast_exit | 8 | 30 | 2/6 | +3.70% | -1.75% | 18.79% | +0.4442 | 2.44 |
| runner_hunter | 9 | 12 | 3/6 | +2.32% | -1.49% | 0.62% | +0.1565 | 1.66 |
| whale_luna | 2 | 8 | 1/1 | +0.33% | +0.33% | 8.56% | +0.0099 | 1.08 |
| novelty_probe | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| low_friction | 1 | 32 | 0/1 | -0.26% | -0.26% | 0.26% | -0.0040 | 0.00 |
| strict_baseline | 6 | 12 | 2/4 | -0.85% | -5.19% | 23.02% | -0.0761 | 0.83 |
| regime_filtered | 3 | 6 | 0/3 | -2.23% | -1.57% | 6.61% | -0.1005 | 0.00 |

## Three-sleeve comparison

| Sleeve | Entries | Closed | Win rate | Avg trade net | Max DD | Realized PnL |
|---|---:|---:|---:|---:|---:|---:|
| balanced_ev | 8 | 8 | 37.5% | +4.54% | 1.19% | $+0.55 |
| runner_hunter | 9 | 9 | 33.3% | +2.32% | 0.62% | $+0.16 |
| diy_whale | 20 | 19 | 57.9% | +5.20% | 0.73% | $+0.74 |

## 1% daily goal — realized-equity proxy (not portfolio return)

| Sleeve | Daily realized-equity return | Daily target | Hit? | Since inception realized-equity return | Compounded target since first observed entry | Gap (USD) | Realized-equity DD since inception |
|---|---:|---:|---|---:|---:|---:|---:|
| balanced_ev | +3.37% | +1.00% | True | +11.56% | +23.24% | -1.75173038 | +11.93% |
| runner_hunter | +1.07% | +1.00% | True | -1.28% | +11.57% | -1.9272162 | +3.15% |
| diy_whale | +5.38% | +1.00% | True | -3.12% | +11.57% | -2.2028942 | +9.82% |

**Warning:** These are completed-trade realized-equity measurements, not mark-to-market portfolio returns. Open-position losses are excluded. The target compounds 1% per calendar day, not per trade.

Average net trade return is NOT daily portfolio return. Compare capital-normalized equity changes separately; no-trade sleeves have insufficient evidence.

No live promotion occurs automatically. Any change requires explicit approval.
