# CryptoTracker Proposals — 2026-11-04

These are the current model-improvement proposals from the nightly review.
Each proposal has a stable ID that can be used directly in ChatGPT.

## P-20261104-01 — Validate follow-up outcome and rejection-cost reporting

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `Daily follow-up and missed-opportunity analysis`
- **Current:** 48,610 follow-up rows are summarized with empty horizons_found and score_bands; the missed-opportunity audit reports usable rejected signals but no false-positive cost distribution.
- **Proposed:** In shadow research, validate signal-level outcome joins and publish 30m, 60m, and 120m sample counts, path and score-band MFE/MAE, and rejected-signal false-positive cost. Deduplicate horizon observations by signal when calculating sample sizes. Do not alter entry thresholds.
- **Confidence:** MEDIUM
- **Recommended mode:** SHADOW
- **Risk:** Incorrect joins, incomplete horizon maturity, or survivorship bias could produce misleading outcome and false-positive estimates.
- **Evidence:**
  - The daily summary reports 48,610 follow-up rows but no recognized outcome horizons or score bands.
  - The missed-opportunity audit reports 107 rejected signals and 106 usable rejected signals, but no false-positive cost metrics.
  - The audit has 130 30m and 128 60m samples, so outcome completeness and linkage can be checked against nontrivial raw counts.

**Approve in ChatGPT:**

`Approve P-20261104-01`

**Decline in ChatGPT:**

`Decline P-20261104-01`

---

## P-20261104-02 — Continue a controlled staged-versus-patient exit comparison

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `Paper exit-model evaluation`
- **Current:** staged_runner and patient_runner each have 14 completed paper trades; both have a 50.0% win rate, with median net returns of +0.236% and +0.2233%, respectively.
- **Proposed:** Continue shadow/paper evaluation on the same eligible entry set, varying only the exit policy, and report per-signal paired outcomes, median net return, MFE/MAE, profit factor, and drawdown before considering promotion.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** The current model samples may not use identical entries; without paired evaluation, apparent exit differences may reflect selection effects rather than exit quality.
- **Evidence:**
  - staged_runner: 14 completed, 7 wins, profit factor 1.349, maximum drawdown 6.97%.
  - patient_runner: 14 completed, 7 wins, profit factor 1.2908, maximum drawdown 7.82%.
  - The modest observed differences and small sample do not establish an exit-policy advantage.

**Approve in ChatGPT:**

`Approve P-20261104-02`

**Decline in ChatGPT:**

`Decline P-20261104-02`

---

## Quick commands

`Review today's CryptoTracker proposals`
