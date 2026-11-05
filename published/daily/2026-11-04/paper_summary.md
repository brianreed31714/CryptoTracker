# CryptoTracker paper research — 2026-11-04

| Model | Trades | Shadow | W/L | Avg net | Median | Max DD | PnL | PF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| diy_whale | 20 | 33 | 8/12 | -0.15% | -2.20% | 3.95% | -0.0231 | 0.96 |
| extended_probe | 1 | 9 | 1/0 | +17.04% | +17.04% | 0.00% | +0.1278 | 999.00 |
| anti_chase | 5 | 61 | 2/3 | +2.12% | -0.46% | 3.72% | +0.1586 | 3.81 |
| flow_breakout | 4 | 39 | 1/3 | +2.10% | -0.72% | 3.26% | +0.1258 | 3.55 |
| early_breakout | 7 | 33 | 2/5 | +1.18% | -1.08% | 3.16% | +0.0620 | 2.45 |
| runner_hunter | 6 | 22 | 2/4 | +0.24% | -1.00% | 0.90% | +0.0107 | 1.08 |
| staged_runner | 11 | 0 | 5/6 | +0.17% | -1.08% | 6.97% | +0.0283 | 1.11 |
| patient_runner | 11 | 61 | 5/6 | +0.09% | -1.09% | 7.82% | +0.0149 | 1.05 |
| low_friction | 0 | 64 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| regime_filtered | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| novelty_probe | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| fast_exit | 11 | 60 | 3/8 | -0.11% | -1.39% | 8.52% | -0.0176 | 0.94 |
| balanced_ev | 11 | 60 | 3/8 | -0.12% | -1.22% | 0.85% | -0.0191 | 0.93 |
| whale_luna | 1 | 9 | 0/1 | -0.46% | -0.46% | 0.46% | -0.0070 | 0.00 |
| strict_baseline | 10 | 24 | 3/7 | -2.74% | -2.68% | 27.48% | -0.4115 | 0.20 |

## Three-sleeve comparison

| Sleeve | Entries | Closed | Win rate | Avg trade net | Max DD | Realized PnL |
|---|---:|---:|---:|---:|---:|---:|
| balanced_ev | 12 | 11 | 27.3% | -0.12% | 0.85% | $-0.02 |
| runner_hunter | 6 | 6 | 33.3% | +0.24% | 0.90% | $+0.01 |
| diy_whale | 20 | 20 | 40.0% | -0.15% | 3.95% | $-0.02 |

## 1% daily goal — realized-equity proxy (not portfolio return)

| Sleeve | Daily realized-equity return | Daily target | Hit? | Since inception realized-equity return | Compounded target since first observed entry | Gap (USD) | Realized-equity DD since inception |
|---|---:|---:|---|---:|---:|---:|---:|
| balanced_ev | -0.12% | +1.00% | False | +4.16% | +44.51% | -6.05207734 | +11.93% |
| runner_hunter | +0.08% | +1.00% | False | -11.30% | +30.82% | -6.31829117 | +13.62% |
| diy_whale | -0.22% | +1.00% | False | -31.11% | +30.82% | -9.28975317 | +32.03% |

**Warning:** These are completed-trade realized-equity measurements, not mark-to-market portfolio returns. Open-position losses are excluded. The target compounds 1% per calendar day, not per trade.

Average net trade return is NOT daily portfolio return. Compare capital-normalized equity changes separately; no-trade sleeves have insufficient evidence.

No live promotion occurs automatically. Any change requires explicit approval.
