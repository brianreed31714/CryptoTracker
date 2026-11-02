# CryptoTracker prospective paper-shadow variants — 2026-11-01

**UNPRICED shadow marks, no swaps. Neither net execution returns nor daily portfolio ROI.**

| Variant | Entry rows today | Exits today | Valid/total exits | Raw win rate | Avg raw mark/exit | Observation status |
|---|---:|---:|---:|---:|---:|---|
| xp_balanced_cd0 | 48 | 49 | 356/356 | 38.8% | -0.96% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_balanced_cd30 | 43 | 44 | 332/332 | 38.9% | -0.89% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_balanced_cd60 | 40 | 41 | 318/318 | 40.6% | -0.85% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_balanced_cd120 | 36 | 37 | 293/293 | 42.0% | -0.13% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_runner_control | 20 | 20 | 208/208 | 42.8% | -1.38% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_runner_confirm2 | 2 | 2 | 39/39 | 17.9% | -8.38% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_runner_confirm3 | 1 | 1 | 1/1 | 100.0% | +7.45% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_runner_early_trail | 20 | 20 | 209/209 | 44.0% | -1.44% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_control | 26 | 26 | 234/234 | 46.6% | +0.29% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_neutral_only | 16 | 16 | 134/134 | 45.5% | -0.24% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_riskoff_strict | 20 | 20 | 165/165 | 49.1% | +0.49% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_name12 | 7 | 7 | 75/75 | 42.7% | +0.23% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_organic_flow | 17 | 17 | 166/166 | 51.2% | +0.74% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_name12_flow | 6 | 6 | 57/57 | 43.9% | -0.93% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_raunchy | 0 | 0 | 7/7 | 57.1% | +13.39% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_raunchy_flow | 0 | 0 | 4/4 | 50.0% | +11.60% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |

## Evidence and safety gate

A zero entry or exit count is **not** evidence that the variant was activated or had no opportunities.
Invalid/missing price marks are excluded from return averages, counted separately, and cannot qualify for preliminary review.
All baseline paper models remain unchanged; variants are isolated observations.
No promotion from raw shadow returns. Require independent Windows host attestation, executable quotes, costs, open-position MTM, liquidity, and drawdown validation.
