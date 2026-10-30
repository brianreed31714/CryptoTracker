# CryptoTracker paper research — 2026-10-27

| Model | Trades | Shadow | W/L | Avg net | Median | Max DD | PnL | PF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| diy_whale | 15 | 22 | 4/11 | -3.98% | -2.06% | 3.50% | -0.4482 | 0.09 |
| runner_hunter | 7 | 20 | 1/6 | +2.15% | -1.88% | 0.66% | +0.1130 | 2.05 |
| extended_probe | 2 | 12 | 1/1 | +0.84% | +0.84% | 7.70% | +0.0125 | 1.22 |
| whale_luna | 1 | 8 | 1/0 | +0.83% | +0.83% | 0.00% | +0.0125 | 999.00 |
| low_friction | 0 | 45 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| regime_filtered | 0 | 2 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| novelty_probe | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| early_breakout | 1 | 25 | 0/1 | -0.49% | -0.49% | 0.49% | -0.0037 | 0.00 |
| anti_chase | 3 | 44 | 1/2 | -0.84% | -0.53% | 5.09% | -0.0380 | 0.50 |
| patient_runner | 6 | 44 | 2/4 | -1.74% | -1.12% | 10.67% | -0.1568 | 0.19 |
| staged_runner | 6 | 0 | 2/4 | -1.75% | -1.12% | 10.67% | -0.1571 | 0.19 |
| strict_baseline | 5 | 16 | 1/4 | -1.95% | -2.25% | 9.42% | -0.1460 | 0.04 |
| flow_breakout | 2 | 26 | 0/2 | -2.56% | -2.56% | 5.10% | -0.0769 | 0.00 |
| balanced_ev | 6 | 44 | 1/5 | -2.65% | -1.91% | 1.51% | -0.2382 | 0.05 |
| fast_exit | 7 | 43 | 0/7 | -3.00% | -2.21% | 19.30% | -0.3150 | 0.00 |

## Three-sleeve comparison

| Sleeve | Entries | Closed | Win rate | Avg trade net | Max DD | Realized PnL |
|---|---:|---:|---:|---:|---:|---:|
| balanced_ev | 6 | 6 | 16.7% | -2.65% | 1.51% | $-0.24 |
| runner_hunter | 7 | 7 | 14.3% | +2.15% | 0.66% | $+0.11 |
| diy_whale | 14 | 15 | 26.7% | -3.98% | 3.50% | $-0.45 |

## 1% daily goal — realized-equity proxy (not portfolio return)

| Sleeve | Daily realized-equity return | Daily target | Hit? | Since inception realized-equity return | Compounded target since first observed entry | Gap (USD) | Realized-equity DD since inception |
|---|---:|---:|---|---:|---:|---:|---:|
| balanced_ev | -1.43% | +1.00% | False | +9.34% | +33.45% | -3.61607242 | +11.93% |
| runner_hunter | +0.83% | +1.00% | False | -8.76% | +20.81% | -4.43597526 | +10.11% |
| diy_whale | -3.50% | +1.00% | False | -17.65% | +20.81% | -5.76981826 | +18.21% |

**Warning:** These are completed-trade realized-equity measurements, not mark-to-market portfolio returns. Open-position losses are excluded. The target compounds 1% per calendar day, not per trade.

Average net trade return is NOT daily portfolio return. Compare capital-normalized equity changes separately; no-trade sleeves have insufficient evidence.

No live promotion occurs automatically. Any change requires explicit approval.
