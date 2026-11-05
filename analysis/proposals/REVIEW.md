# CryptoTracker Proposals — 2026-11-03

These are the current model-improvement proposals from the nightly review.
Each proposal has a stable ID that can be used directly in ChatGPT.

## P-20261103-01 — Continue shadow observation of xp_diy_name12

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `paper_shadow_research.xp_diy_name12`
- **Current:** Shadow-only; 17 completed observations; no promotion candidate
- **Proposed:** Continue unchanged in SHADOW and review again after more independent completed observations; do not promote or alter live settings based on this sample.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** The apparent advantage may be sampling noise, selection bias, or a shadow-return estimate that does not reflect executable fills and costs.
- **Evidence:**
  - 17 completions: 11 wins and 6 losses (64.71% win rate), median net return +2.0408%, and profit factor 2.7923.
  - Maximum drawdown is 8.6743%; shadow realized P&L is reported as $0, and the overall report lists no promotion candidates.

**Approve in ChatGPT:**

`Approve P-20261103-01`

**Decline in ChatGPT:**

`Decline P-20261103-01`

---

## P-20261103-02 — Report path-based follow-up and rejection outcomes

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `surge_followup and missed_opportunity daily reporting`
- **Current:** Follow-up metrics expose no score bands or horizons; rejected-signal audit has 90 usable rows but no summarized MFE/MAE or false-positive cost.
- **Proposed:** Validate outcome joins and produce accepted-versus-rejected 30/60/120-minute counts, median return, MFE, MAE, and false-positive cost by path and score band before considering entry-gate changes.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** Incorrect signal-to-outcome joins, repeated observations, or survivorship bias could make the added summaries misleading.
- **Evidence:**
  - The follow-up log has 47,406 rows, while reported score_bands is empty and horizons_found is empty.
  - The missed-opportunity audit reports 95 rejected signal rows and 90 usable rejected signals, but the supplied metrics contain no outcome summary for them.

**Approve in ChatGPT:**

`Approve P-20261103-02`

**Decline in ChatGPT:**

`Decline P-20261103-02`

---

## P-20261103-03 — Maintain Luna calibration as a shadow study

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `Luna review and outcome-calibration reporting`
- **Current:** AI confirmation is enabled with a maximum bonus of 5; daily review log has 22 rows, and outcome aggregates are not shown linked to individual Luna setup predictions.
- **Proposed:** Keep the current bonus unchanged and evaluate predictions in SHADOW, linking setup, confidence, and timestamp to fixed-horizon outcomes before proposing any prompt, threshold, or bonus change.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** Small samples, incomplete labels, or a mismatch between review records and outcome groups could produce a misleading calibration assessment.
- **Evidence:**
  - The 22 daily reviews have median confidence 76, which is too small to establish calibration.
  - POSITIVE|MEDIUM outcome groups have n=11 at 30 minutes with median return -0.976% and n=11 at 60 minutes with median -5.445%; the 120-minute group has n=9 and median -17.564%.

**Approve in ChatGPT:**

`Approve P-20261103-03`

**Decline in ChatGPT:**

`Decline P-20261103-03`

---

## P-20261103-04 — Audit smart-money campaign and scorecard evidence

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `SmartMoneyMonitor campaign-strength and wallet-scorecard reporting`
- **Current:** 175 campaign rows across 21 unique campaigns; median strength 0, zero multi-wallet convergence, and an empty wallet scorecard.
- **Proposed:** Investigate scorecard population and campaign-strength/convergence calculations in research reporting; keep smart-money scoring and trading influence unchanged until outcome-linked evidence is available.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** The zero strength or empty scorecard may reflect filtering or reporting semantics rather than a feed or scoring defect; changing the signal before resolving that could degrade candidate selection.
- **Evidence:**
  - The campaign summary reports median strength 0 and multi-wallet convergence count 0.
  - The wallet scorecard contains zero filtered rows despite latest feed status OK and latest wallet coverage of 100%; 1,360 of 11,250 wallet checks are reported failed.

**Approve in ChatGPT:**

`Approve P-20261103-04`

**Decline in ChatGPT:**

`Decline P-20261103-04`

---

## Quick commands

`Review today's CryptoTracker proposals`
