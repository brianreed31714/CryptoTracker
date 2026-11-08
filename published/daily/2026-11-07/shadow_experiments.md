# CryptoTracker prospective paper-shadow variants — 2026-11-07

**UNPRICED shadow marks, no swaps. Neither net execution returns nor daily portfolio ROI.**

| Variant | Entry rows today | Exits today | Valid/total exits | Raw win rate | Avg raw mark/exit | Observation status |
|---|---:|---:|---:|---:|---:|---|
| xp_balanced_cd0 | 31 | 31 | 668/668 | 38.2% | -1.09% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_balanced_cd30 | 29 | 29 | 622/622 | 39.1% | -0.80% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_balanced_cd60 | 27 | 27 | 593/593 | 40.1% | -0.81% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_balanced_cd120 | 24 | 24 | 543/543 | 41.6% | -0.39% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_runner_control | 14 | 14 | 323/323 | 42.4% | -0.39% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_runner_confirm2 | 2 | 2 | 56/56 | 26.8% | -6.44% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_runner_confirm3 | 0 | 0 | 3/3 | 66.7% | +8.37% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_runner_early_trail | 14 | 14 | 326/326 | 43.6% | -0.36% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_control | 18 | 17 | 411/411 | 43.6% | -0.19% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_neutral_only | 12 | 11 | 239/239 | 43.5% | -0.39% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_riskoff_strict | 13 | 12 | 280/280 | 45.7% | +0.01% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_name12 | 4 | 3 | 125/125 | 45.6% | +0.32% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_organic_flow | 18 | 17 | 294/294 | 44.2% | -0.20% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_name12_flow | 3 | 2 | 84/84 | 42.9% | -0.85% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_raunchy | 0 | 0 | 7/7 | 57.1% | +13.39% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_raunchy_flow | 0 | 0 | 4/4 | 50.0% | +11.60% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |

## Evidence and safety gate

A zero entry or exit count is **not** evidence that the variant was activated or had no opportunities.
Invalid/missing price marks are excluded from return averages, counted separately, and cannot qualify for preliminary review.
All baseline paper models remain unchanged; variants are isolated observations.
No promotion from raw shadow returns. Require independent Windows host attestation, executable quotes, costs, open-position MTM, liquidity, and drawdown validation.
