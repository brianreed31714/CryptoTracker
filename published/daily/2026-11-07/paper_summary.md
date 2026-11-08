# CryptoTracker paper research — 2026-11-07

| Model | Trades | Shadow | W/L | Avg net | Median | Max DD | PnL | PF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| early_breakout | 1 | 16 | 1/0 | +6.72% | +6.72% | 0.00% | +0.0504 | 999.00 |
| diy_whale | 11 | 28 | 5/6 | +1.52% | -3.32% | 1.66% | +0.1257 | 1.44 |
| flow_breakout | 0 | 18 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| low_friction | 0 | 31 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| regime_filtered | 0 | 2 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| extended_probe | 0 | 3 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| novelty_probe | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| strict_baseline | 8 | 12 | 1/7 | -3.07% | -4.08% | 23.59% | -0.3688 | 0.35 |
| runner_hunter | 9 | 13 | 2/7 | -3.08% | -4.47% | 1.64% | -0.2081 | 0.29 |
| anti_chase | 3 | 29 | 1/2 | -3.83% | -3.85% | 11.71% | -0.1725 | 0.04 |
| whale_luna | 4 | 5 | 0/4 | -3.99% | -2.54% | 15.17% | -0.2393 | 0.00 |
| balanced_ev | 7 | 28 | 0/7 | -4.62% | -3.85% | 3.12% | -0.4854 | 0.00 |
| fast_exit | 7 | 28 | 0/7 | -4.80% | -4.69% | 29.26% | -0.5043 | 0.00 |
| patient_runner | 7 | 27 | 0/7 | -5.23% | -5.03% | 31.61% | -0.5494 | 0.00 |
| staged_runner | 7 | 0 | 0/7 | -5.36% | -5.02% | 32.32% | -0.5631 | 0.00 |

## Three-sleeve comparison

| Sleeve | Entries | Closed | Win rate | Avg trade net | Max DD | Realized PnL |
|---|---:|---:|---:|---:|---:|---:|
| balanced_ev | 7 | 7 | 0.0% | -4.62% | 3.12% | $-0.49 |
| runner_hunter | 9 | 9 | 22.2% | -3.08% | 1.64% | $-0.21 |
| diy_whale | 12 | 11 | 45.5% | +1.52% | 1.66% | $+0.13 |

## 1% daily goal — realized-equity proxy (not portfolio return)

| Sleeve | Daily realized-equity return | Daily target | Hit? | Since inception realized-equity return | Compounded target since first observed entry | Gap (USD) | Realized-equity DD since inception |
|---|---:|---:|---|---:|---:|---:|---:|
| balanced_ev | -3.12% | +1.00% | False | +0.65% | +48.89% | -7.23614027 | +11.93% |
| runner_hunter | -1.64% | +1.00% | False | -16.82% | +34.78% | -7.74107373 | +16.82% |
| diy_whale | +1.26% | +1.00% | True | -32.72% | +34.78% | -10.12534073 | +35.10% |

**Warning:** These are completed-trade realized-equity measurements, not mark-to-market portfolio returns. Open-position losses are excluded. The target compounds 1% per calendar day, not per trade.

Average net trade return is NOT daily portfolio return. Compare capital-normalized equity changes separately; no-trade sleeves have insufficient evidence.

No live promotion occurs automatically. Any change requires explicit approval.
