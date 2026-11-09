# CryptoTracker paper research — 2026-11-08

| Model | Trades | Shadow | W/L | Avg net | Median | Max DD | PnL | PF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| diy_whale | 14 | 34 | 5/9 | +1.55% | -0.72% | 2.15% | +0.1631 | 1.60 |
| regime_filtered | 1 | 2 | 1/0 | +31.34% | +31.34% | 0.00% | +0.4701 | 999.00 |
| flow_breakout | 4 | 18 | 2/2 | +5.02% | -1.66% | 5.72% | +0.3013 | 2.98 |
| extended_probe | 2 | 10 | 1/1 | +5.01% | +5.01% | 4.57% | +0.0751 | 3.19 |
| patient_runner | 8 | 35 | 3/5 | +4.30% | -2.57% | 11.66% | +0.5159 | 2.53 |
| staged_runner | 8 | 0 | 3/5 | +4.08% | -2.56% | 11.67% | +0.4897 | 2.46 |
| balanced_ev | 8 | 35 | 3/5 | +3.84% | -1.83% | 0.89% | +0.4603 | 2.76 |
| early_breakout | 5 | 17 | 2/3 | +3.51% | -3.16% | 7.08% | +0.1316 | 2.32 |
| runner_hunter | 8 | 23 | 4/4 | +2.74% | +1.48% | 0.64% | +0.1646 | 2.25 |
| strict_baseline | 7 | 17 | 4/3 | +1.96% | +1.19% | 6.50% | +0.2054 | 2.09 |
| fast_exit | 8 | 35 | 2/6 | +1.51% | -3.02% | 9.67% | +0.1810 | 1.59 |
| anti_chase | 9 | 37 | 2/7 | +1.42% | -2.66% | 10.41% | +0.1921 | 1.52 |
| low_friction | 0 | 35 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| novelty_probe | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| whale_luna | 3 | 9 | 1/2 | -1.43% | -4.45% | 6.19% | -0.0644 | 0.60 |

## Three-sleeve comparison

| Sleeve | Entries | Closed | Win rate | Avg trade net | Max DD | Realized PnL |
|---|---:|---:|---:|---:|---:|---:|
| balanced_ev | 8 | 8 | 37.5% | +3.84% | 0.89% | $+0.46 |
| runner_hunter | 8 | 8 | 50.0% | +2.74% | 0.64% | $+0.16 |
| diy_whale | 14 | 14 | 35.7% | +1.55% | 2.15% | $+0.16 |

## 1% daily goal — realized-equity proxy (not portfolio return)

| Sleeve | Daily realized-equity return | Daily target | Hit? | Since inception realized-equity return | Compounded target since first observed entry | Gap (USD) | Realized-equity DD since inception |
|---|---:|---:|---|---:|---:|---:|---:|
| balanced_ev | +3.05% | +1.00% | True | +3.71% | +50.38% | -6.99913683 | +12.54% |
| runner_hunter | +1.32% | +1.00% | True | -15.97% | +36.13% | -7.81533807 | +17.60% |
| diy_whale | +1.61% | +1.00% | True | -31.21% | +36.13% | -10.10134907 | +35.10% |

**Warning:** These are completed-trade realized-equity measurements, not mark-to-market portfolio returns. Open-position losses are excluded. The target compounds 1% per calendar day, not per trade.

Average net trade return is NOT daily portfolio return. Compare capital-normalized equity changes separately; no-trade sleeves have insufficient evidence.

No live promotion occurs automatically. Any change requires explicit approval.
