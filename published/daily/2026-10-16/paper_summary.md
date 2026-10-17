# CryptoTracker paper research — 2026-10-16

| Model | Trades | Shadow | W/L | Avg net | Median | Max DD | PnL | PF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| runner_hunter | 4 | 12 | 3/1 | +5.95% | +3.91% | 1.15% | +0.1784 | 21.73 |
| strict_baseline | 3 | 5 | 2/1 | +4.15% | +1.41% | 5.82% | +0.1869 | 3.14 |
| early_breakout | 2 | 8 | 2/0 | +4.11% | +4.11% | 0.00% | +0.0616 | 999.00 |
| flow_breakout | 2 | 10 | 2/0 | +4.08% | +4.08% | 0.00% | +0.1224 | 999.00 |
| anti_chase | 4 | 21 | 3/1 | +3.49% | +4.20% | 0.82% | +0.2095 | 18.11 |
| balanced_ev | 5 | 19 | 3/2 | +1.70% | +1.59% | 3.71% | +0.1273 | 2.88 |
| regime_filtered | 3 | 10 | 2/1 | +1.61% | +4.18% | 3.66% | +0.0724 | 2.32 |
| staged_runner | 5 | 0 | 3/2 | +1.59% | +3.96% | 5.33% | +0.1189 | 1.82 |
| extended_probe | 2 | 5 | 1/1 | +1.48% | +1.48% | 1.54% | +0.0223 | 2.92 |
| fast_exit | 5 | 19 | 3/2 | +1.25% | +0.98% | 4.04% | +0.0940 | 2.55 |
| whale_luna | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| low_friction | 0 | 21 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| novelty_probe | 0 | 0 | 0/0 | +0.00% | +0.00% | 0.00% | +0.0000 | 0.00 |
| diy_whale | 8 | 14 | 3/5 | -1.26% | -0.84% | 29.94% | -0.0754 | 0.76 |
| patient_runner | 5 | 19 | 2/3 | -6.21% | -4.35% | 37.51% | -0.4661 | 0.30 |

## Three-sleeve comparison

| Sleeve | Entries | Closed | Win rate | Avg trade net | Max DD | Realized PnL |
|---|---:|---:|---:|---:|---:|---:|
| balanced_ev | 5 | 5 | 60.0% | +1.70% | 3.71% | $+0.13 |
| runner_hunter | 4 | 4 | 75.0% | +5.95% | 1.15% | $+0.18 |
| diy_whale | 9 | 8 | 37.5% | -1.26% | 29.94% | $-0.08 |

Average net trade return is NOT daily portfolio return. Compare capital-normalized equity changes separately; no-trade sleeves have insufficient evidence.

No live promotion occurs automatically. Any change requires explicit approval.
