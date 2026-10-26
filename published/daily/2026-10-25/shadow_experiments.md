# CryptoTracker prospective paper-shadow variants — 2026-10-25

**UNPRICED shadow marks, no swaps. Neither net execution returns nor daily portfolio ROI.**

| Variant | Entry rows today | Exits today | Valid/total exits | Raw win rate | Avg raw mark/exit | Observation status |
|---|---:|---:|---:|---:|---:|---|
| xp_balanced_cd0 | 2 | 2 | 2/2 | 50.0% | -0.38% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_balanced_cd30 | 2 | 2 | 2/2 | 50.0% | -0.38% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_balanced_cd60 | 2 | 2 | 2/2 | 50.0% | -0.38% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_balanced_cd120 | 2 | 2 | 2/2 | 50.0% | -0.38% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_runner_control | 5 | 4 | 4/4 | 50.0% | -3.39% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_runner_confirm2 | 3 | 3 | 3/3 | 0.0% | -4.46% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_runner_confirm3 | 0 | 0 | 0/0 | N/A | N/A | NO_ROWS_ACTIVATION_UNVERIFIED |
| xp_runner_early_trail | 5 | 4 | 4/4 | 75.0% | -2.94% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_control | 1 | 1 | 1/1 | 0.0% | -2.95% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_neutral_only | 0 | 0 | 0/0 | N/A | N/A | NO_ROWS_ACTIVATION_UNVERIFIED |
| xp_diy_riskoff_strict | 0 | 0 | 0/0 | N/A | N/A | NO_ROWS_ACTIVATION_UNVERIFIED |
| xp_diy_name12 | 1 | 1 | 1/1 | 0.0% | -2.95% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_organic_flow | 1 | 1 | 1/1 | 0.0% | -2.95% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_name12_flow | 1 | 1 | 1/1 | 0.0% | -2.95% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_raunchy | 0 | 0 | 0/0 | N/A | N/A | NO_ROWS_ACTIVATION_UNVERIFIED |
| xp_diy_raunchy_flow | 0 | 0 | 0/0 | N/A | N/A | NO_ROWS_ACTIVATION_UNVERIFIED |

## Evidence and safety gate

A zero entry or exit count is **not** evidence that the variant was activated or had no opportunities.
Invalid/missing price marks are excluded from return averages, counted separately, and cannot qualify for preliminary review.
All baseline paper models remain unchanged; variants are isolated observations.
No promotion from raw shadow returns. Require independent Windows host attestation, executable quotes, costs, open-position MTM, liquidity, and drawdown validation.
