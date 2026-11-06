# CryptoTracker paper research — 2026-11-05

| Model | Trades | Shadow | W/L | Avg net | Median | Max DD | PnL | PF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| diy_whale | 12 | 29 | 5/7 | +1.29% | -0.70% | 2.78% | +0.1163 | 1.31 |
| flow_breakout | 5 | 23 | 2/3 | +4.32% | -0.13% | 3.07% | +0.3241 | 7.99 |
| extended_probe | 2 | 9 | 2/0 | +3.76% | +3.76% | 0.00% | +0.0563 | 999.00 |
| fast_exit | 9 | 38 | 4/5 | +2.42% | -0.14% | 8.34% | +0.3270 | 3.54 |
| anti_chase | 11 | 45 | 5/6 | +1.72% | -0.44% | 6.70% | +0.2832 | 2.59 |
| balanced_ev | 9 | 38 | 4/5 | +1.46% | -0.43% | 0.93% | +0.1974 | 2.35 |
| early_breakout | 5 | 22 | 1/4 | +1.14% | -0.56% | 4.72% | +0.0429 | 2.20 |
| low_friction | 0 | 42 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| regime_filtered | 0 | 4 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| novelty_probe | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| whale_luna | 1 | 5 | 0/1 | -0.44% | -0.44% | 0.44% | -0.0066 | 0.00 |
| staged_runner | 9 | 0 | 5/4 | -0.61% | +0.38% | 20.92% | -0.0817 | 0.78 |
| patient_runner | 9 | 38 | 5/4 | -0.61% | +0.36% | 20.99% | -0.0829 | 0.78 |
| strict_baseline | 10 | 18 | 5/5 | -8.09% | -4.67% | 73.73% | -1.2137 | 0.21 |
| runner_hunter | 8 | 19 | 3/5 | -8.52% | -0.54% | 4.53% | -0.5113 | 0.16 |

## Three-sleeve comparison

| Sleeve | Entries | Closed | Win rate | Avg trade net | Max DD | Realized PnL |
|---|---:|---:|---:|---:|---:|---:|
| balanced_ev | 9 | 9 | 44.4% | +1.46% | 0.93% | $+0.20 |
| runner_hunter | 8 | 8 | 37.5% | -8.52% | 4.53% | $-0.51 |
| diy_whale | 12 | 12 | 41.7% | +1.29% | 2.78% | $+0.12 |

## 1% daily goal — realized-equity proxy (not portfolio return)

| Sleeve | Daily realized-equity return | Daily target | Hit? | Since inception realized-equity return | Compounded target since first observed entry | Gap (USD) | Realized-equity DD since inception |
|---|---:|---:|---|---:|---:|---:|---:|
| balanced_ev | +1.26% | +1.00% | True | +5.88% | +45.95% | -6.01054681 | +11.93% |
| runner_hunter | -3.84% | +1.00% | False | -14.71% | +32.13% | -7.0257785 | +14.71% |
| diy_whale | +1.12% | +1.00% | True | -29.88% | +32.13% | -9.3010675 | +32.25% |

**Warning:** These are completed-trade realized-equity measurements, not mark-to-market portfolio returns. Open-position losses are excluded. The target compounds 1% per calendar day, not per trade.

Average net trade return is NOT daily portfolio return. Compare capital-normalized equity changes separately; no-trade sleeves have insufficient evidence.

No live promotion occurs automatically. Any change requires explicit approval.
