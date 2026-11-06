# CryptoTracker prospective paper-shadow variants — 2026-11-05

**UNPRICED shadow marks, no swaps. Neither net execution returns nor daily portfolio ROI.**

| Variant | Entry rows today | Exits today | Valid/total exits | Raw win rate | Avg raw mark/exit | Observation status |
|---|---:|---:|---:|---:|---:|---|
| xp_balanced_cd0 | 42 | 42 | 590/590 | 38.5% | -1.11% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_balanced_cd30 | 40 | 40 | 551/551 | 39.2% | -0.84% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_balanced_cd60 | 38 | 38 | 526/526 | 40.1% | -0.87% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_balanced_cd120 | 37 | 37 | 482/482 | 41.3% | -0.46% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_runner_control | 22 | 22 | 295/295 | 43.7% | -0.29% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_runner_confirm2 | 5 | 5 | 53/53 | 28.3% | -6.16% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_runner_confirm3 | 1 | 1 | 3/3 | 66.7% | +8.37% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_runner_early_trail | 22 | 22 | 298/298 | 45.0% | -0.29% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_control | 22 | 22 | 365/365 | 44.9% | -0.02% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_neutral_only | 14 | 14 | 215/215 | 45.6% | -0.25% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_riskoff_strict | 16 | 16 | 252/252 | 47.6% | +0.17% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_name12 | 1 | 1 | 117/117 | 47.0% | +0.50% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_organic_flow | 20 | 20 | 255/255 | 46.7% | +0.16% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_name12_flow | 0 | 0 | 80/80 | 45.0% | -0.69% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_raunchy | 0 | 0 | 7/7 | 57.1% | +13.39% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |
| xp_diy_raunchy_flow | 0 | 0 | 4/4 | 50.0% | +11.60% | SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION |

## Evidence and safety gate

A zero entry or exit count is **not** evidence that the variant was activated or had no opportunities.
Invalid/missing price marks are excluded from return averages, counted separately, and cannot qualify for preliminary review.
All baseline paper models remain unchanged; variants are isolated observations.
No promotion from raw shadow returns. Require independent Windows host attestation, executable quotes, costs, open-position MTM, liquidity, and drawdown validation.
