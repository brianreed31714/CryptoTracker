# CryptoTracker prospective paper-shadow variants — 2026-11-06

**UNPRICED shadow marks, no swaps. Neither net execution returns nor daily portfolio ROI.**

| Variant | Entry rows today | Exits today | Valid/total exits | Raw win rate | Avg raw mark/exit | Observation status |
|---|---:|---:|---:|---:|---:|---|
| xp_balanced_cd0 | 43 | 43 | 637/637 | 38.1% | -1.13% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_balanced_cd30 | 38 | 38 | 593/593 | 39.0% | -0.86% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_balanced_cd60 | 37 | 37 | 566/566 | 39.8% | -0.89% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_balanced_cd120 | 34 | 34 | 519/519 | 40.8% | -0.49% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_runner_control | 13 | 13 | 309/309 | 43.0% | -0.39% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_runner_confirm2 | 1 | 1 | 54/54 | 27.8% | -6.23% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_runner_confirm3 | 0 | 0 | 3/3 | 66.7% | +8.37% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_runner_early_trail | 13 | 13 | 312/312 | 44.2% | -0.36% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_control | 28 | 29 | 394/394 | 44.2% | -0.15% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_neutral_only | 13 | 13 | 228/228 | 44.3% | -0.36% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_riskoff_strict | 16 | 16 | 268/268 | 46.6% | +0.06% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_name12 | 5 | 5 | 122/122 | 46.7% | +0.40% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_organic_flow | 22 | 22 | 277/277 | 45.5% | +0.01% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_name12_flow | 2 | 2 | 82/82 | 43.9% | -0.80% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_raunchy | 0 | 0 | 7/7 | 57.1% | +13.39% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_raunchy_flow | 0 | 0 | 4/4 | 50.0% | +11.60% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |

## Evidence and safety gate

A zero entry or exit count is **not** evidence that the variant was activated or had no opportunities.
Invalid/missing price marks are excluded from return averages, counted separately, and cannot qualify for preliminary review.
All baseline paper models remain unchanged; variants are isolated observations.
No promotion from raw shadow returns. Require independent Windows host attestation, executable quotes, costs, open-position MTM, liquidity, and drawdown validation.
