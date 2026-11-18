# CryptoTracker Proposals — 2026-11-16

These are the current model-improvement proposals from the nightly review.
Each proposal has a stable ID that can be used directly in ChatGPT.

## P-20261116-01 — Continue name12-flow evaluation in shadow

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `paper_shadow model xp_diy_name12_flow`
- **Current:** 7 completed shadow observations; 6 wins, median net return 3.2458%, maximum drawdown 3.0276%; no promotion candidate
- **Proposed:** Keep the variant shadow-only and collect at least 12 distinct completed token-signal observations, deduplicated by token and campaign; report net returns, costs, MFE/MAE, and drawdown before reassessment. Do not promote automatically.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** Small-sample selection effects or repeated observations from the same token/campaign may make the apparent performance disappear; shadow results may not reflect executable live returns.
- **Evidence:**
  - The observed 6/7 hit rate and 3.2458% median are promising but based on fewer than 12 observations.
  - The research summary lists no promotion candidates, and other model comparisons are not established as independent controlled tests.

**Approve in ChatGPT:**

`Approve P-20261116-01`

**Decline in ChatGPT:**

`Decline P-20261116-01`

---

## P-20261116-02 — Reconcile forward-outcome coverage before rule changes

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `surge_followup_log, surge_followup_audit, and missed_opportunity_audit outcome reporting`
- **Current:** 57,855 follow-up rows but no reported horizons; missed-opportunity summary has 46 usable rejected signals without reported outcome distributions
- **Proposed:** In research reporting, reconcile signal identity and timestamps, then produce deduplicated 30/60/120-minute outcomes with MFE, MAE, and rejection reason where available; use the results to quantify missed-opportunity benefit and false-positive cost before considering entry-filter changes.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** Incomplete or survivorship-biased follow-up coverage could misstate both missed upside and the cost of admitting rejected signals.
- **Evidence:**
  - The follow-up summary reports no horizons despite 57,855 rows.
  - The missed-opportunity audit reports 46 usable rejected signals but no MFE/MAE or outcome breakdown in the supplied metrics.

**Approve in ChatGPT:**

`Approve P-20261116-02`

**Decline in ChatGPT:**

`Decline P-20261116-02`

---

## P-20261116-03 — Audit smart-money feed and campaign count alignment

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `SmartMoneyMonitor feed-health and filtered event/campaign reporting`
- **Current:** Filtered event and campaign files each contain 0 rows; feed health reports 1,334 event and campaign row deltas, latest status OK, 100% wallet coverage, and 1,834 failed wallet checks
- **Proposed:** Reconcile reporting windows, filtering rules, and counter semantics in a shadow research audit before using campaign strength or convergence in trading decisions.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** The differing counts may be explained by valid window or aggregation differences; treating them as a feed failure without reconciliation could prompt unnecessary changes.
- **Evidence:**
  - The daily filtered event and campaign files contain zero rows, leaving campaign strength and convergence unmeasurable for this review.
  - Feed-health deltas and failed-check counts are nonzero despite the empty filtered files, so the available summaries are not sufficient to establish campaign coverage or quality.

**Approve in ChatGPT:**

`Approve P-20261116-03`

**Decline in ChatGPT:**

`Decline P-20261116-03`

---

## Quick commands

`Review today's CryptoTracker proposals`
