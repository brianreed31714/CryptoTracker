# CryptoTracker prospective paper-shadow variants — 2026-11-26

**UNPRICED shadow marks, no swaps. Neither net execution returns nor daily portfolio ROI.**

| Variant | Entry rows today | Exits today | Valid/total exits | Raw win rate | Avg raw mark/exit | Observation status |
|---|---:|---:|---:|---:|---:|---|
| xp_balanced_cd0 | 26 | 26 | 1199/1199 | 39.7% | -0.36% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_balanced_cd30 | 25 | 25 | 1120/1120 | 40.6% | -0.45% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_balanced_cd60 | 24 | 24 | 1064/1064 | 41.4% | -0.47% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_balanced_cd120 | 24 | 24 | 987/987 | 42.5% | -0.19% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_runner_control | 11 | 11 | 560/560 | 40.5% | +22.44% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_runner_confirm2 | 1 | 1 | 77/77 | 29.9% | -5.01% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_runner_confirm3 | 0 | 0 | 3/3 | 66.7% | +8.37% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_runner_early_trail | 11 | 11 | 564/564 | 41.7% | +22.33% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_control | 20 | 21 | 790/790 | 42.8% | +1.16% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_neutral_only | 10 | 10 | 436/436 | 40.6% | -0.03% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_riskoff_strict | 13 | 13 | 520/520 | 44.0% | +1.70% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_name12 | 2 | 2 | 283/283 | 44.9% | -0.51% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_organic_flow | 14 | 14 | 560/560 | 42.9% | +1.28% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_name12_flow | 1 | 1 | 192/192 | 43.8% | -1.38% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_raunchy | 0 | 0 | 29/29 | 55.2% | +5.19% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_raunchy_flow | 0 | 0 | 13/13 | 38.5% | +2.23% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |

## Evidence and safety gate

A zero entry or exit count is **not** evidence that the variant was activated or had no opportunities.
Invalid/missing price marks are excluded from return averages, counted separately, and cannot qualify for preliminary review.
All baseline paper models remain unchanged; variants are isolated observations.
No promotion from raw shadow returns. Require independent Windows host attestation, executable quotes, costs, open-position MTM, liquidity, and drawdown validation.
