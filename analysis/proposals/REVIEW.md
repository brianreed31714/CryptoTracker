# CryptoTracker Proposals — 2026-11-17

These are the current model-improvement proposals from the nightly review.
Each proposal has a stable ID that can be used directly in ChatGPT.

## P-20261117-01 — Add a shadow-only, outcome-linked validation report

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `Paper/shadow model evaluation reporting`
- **Current:** The supplied daily metrics report aggregate model returns but do not provide usable follow-up horizons, MFE/MAE, per-trade execution costs, exit attribution, or Luna outcome labels; live trade count is zero.
- **Proposed:** For research review only, produce a per-token de-duplicated report linking entry decisions to executable quote costs, net outcomes, MFE/MAE, exit reason, and—where applicable—Luna and smart-money labels. Include sample size and false-positive outcomes; keep current live trading disabled and make no model promotion from this report alone.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** Additional linkage and reporting work may delay conclusions, and duplicate or incomplete token histories could still bias comparisons; results must remain observational until data quality and sample independence are checked.
- **Evidence:**
  - Live buys and sells are both 0, and the reported median preflight round-trip statistic is 0 with no quote sample count.
  - Follow-up metrics show 58,838 rows but no horizons found; Luna outcomes report 0 rows and 0 labeled rows.
  - Missed-opportunity audit reports 46 usable rejected signals but provides no outcome or false-positive-cost metrics in the supplied summary.
  - Paper and shadow model results differ materially for diy_whale, while the shadow sample has a negative median return despite a positive average.

**Approve in ChatGPT:**

`Approve P-20261117-01`

**Decline in ChatGPT:**

`Decline P-20261117-01`

---

## Quick commands

`Review today's CryptoTracker proposals`
