# CryptoTracker paper research — 2026-10-30

| Model | Trades | Shadow | W/L | Avg net | Median | Max DD | PnL | PF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| diy_whale | 12 | 18 | 7/5 | +8.64% | +1.29% | 0.70% | +0.7778 | 4.75 |
| low_friction | 1 | 37 | 1/0 | +3.65% | +3.65% | 0.00% | +0.0548 | 999.00 |
| whale_luna | 1 | 6 | 1/0 | +3.64% | +3.64% | 0.00% | +0.0547 | 999.00 |
| staged_runner | 6 | 0 | 1/5 | +3.42% | -0.80% | 7.99% | +0.3081 | 3.23 |
| strict_baseline | 3 | 13 | 2/1 | +2.87% | +0.86% | 10.76% | +0.1291 | 1.80 |
| anti_chase | 5 | 36 | 1/4 | +1.93% | -0.97% | 7.25% | +0.1450 | 2.16 |
| patient_runner | 6 | 36 | 1/5 | +1.41% | -0.80% | 8.11% | +0.1265 | 1.90 |
| flow_breakout | 2 | 20 | 1/1 | +1.38% | +1.38% | 0.89% | +0.0414 | 4.10 |
| balanced_ev | 6 | 36 | 1/5 | +0.56% | -1.35% | 1.18% | +0.0508 | 1.25 |
| extended_probe | 0 | 5 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| novelty_probe | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| early_breakout | 3 | 19 | 1/2 | -0.17% | -0.81% | 1.19% | -0.0038 | 0.75 |
| fast_exit | 7 | 36 | 2/5 | -0.34% | -0.89% | 12.35% | -0.0359 | 0.83 |
| regime_filtered | 2 | 6 | 0/2 | -2.98% | -2.98% | 5.91% | -0.0894 | 0.00 |
| runner_hunter | 3 | 10 | 1/2 | -3.85% | -3.97% | 0.73% | -0.0865 | 0.12 |

## Three-sleeve comparison

| Sleeve | Entries | Closed | Win rate | Avg trade net | Max DD | Realized PnL |
|---|---:|---:|---:|---:|---:|---:|
| balanced_ev | 6 | 6 | 16.7% | +0.56% | 1.18% | $+0.05 |
| runner_hunter | 3 | 3 | 33.3% | -3.85% | 0.73% | $-0.09 |
| diy_whale | 13 | 12 | 58.3% | +8.64% | 0.70% | $+0.78 |

## 1% daily goal — realized-equity proxy (not portfolio return)

| Sleeve | Daily realized-equity return | Daily target | Hit? | Since inception realized-equity return | Compounded target since first observed entry | Gap (USD) | Realized-equity DD since inception |
|---|---:|---:|---|---:|---:|---:|---:|
| balanced_ev | +0.32% | +1.00% | False | +7.60% | +37.49% | -4.48416045 | +11.93% |
| runner_hunter | -0.65% | +1.00% | False | -11.25% | +24.47% | -5.3586819 | +11.33% |
| diy_whale | +6.83% | +1.00% | True | -18.87% | +24.47% | -6.5017119 | +28.03% |

**Warning:** These are completed-trade realized-equity measurements, not mark-to-market portfolio returns. Open-position losses are excluded. The target compounds 1% per calendar day, not per trade.

Average net trade return is NOT daily portfolio return. Compare capital-normalized equity changes separately; no-trade sleeves have insufficient evidence.

No live promotion occurs automatically. Any change requires explicit approval.
