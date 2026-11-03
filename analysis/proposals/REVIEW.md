# CryptoTracker Proposals — 2026-11-01

These are the current model-improvement proposals from the nightly review.
Each proposal has a stable ID that can be used directly in ChatGPT.

## P-20261101-01 — Restore signal-level forward-outcome reporting

- **Status:** PENDING
- **Type:** CODE
- **Target:** `surge follow-up and missed-opportunity audit pipeline`
- **Current:** 44,383 follow-up rows are present, but score_bands is empty and no outcome horizons are detected; rejected-signal audit counts are available without usable reported outcome detail.
- **Proposed:** After human approval, audit the joins and reporting so each eligible signal has clearly matched 30/60/120-minute outcomes, MFE/MAE, decision path, and coverage denominators. Keep the work in shadow/research and do not change trading thresholds.
- **Confidence:** MEDIUM
- **Recommended mode:** SHADOW
- **Risk:** Incorrect signal-time joins or incomplete horizon handling could introduce lookahead or mislabel outcomes; validate timestamps and coverage before using the report for strategy decisions.
- **Evidence:**
  - Follow-up metrics report 44,383 rows but score_bands={} and horizons_found=[].
  - The missed-opportunity audit reports 107 usable rejected signals and sample counts of 121 at 30 minutes and 119 at 60 minutes, but the supplied metrics do not provide their outcome distribution or false-positive cost.

**Approve in ChatGPT:**

`Approve P-20261101-01`

**Decline in ChatGPT:**

`Decline P-20261101-01`

---

## P-20261101-02 — Continue runner_hunter evaluation in shadow only

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `paper_research runner_hunter evaluation`
- **Current:** Preliminary shadow leader with 17 completed trades; no promotion candidate is reported.
- **Proposed:** Continue shadow-only, execution-cost-aware evaluation and compare against its paper cohort using non-overlapping signal-level outcomes; do not promote to live based on the current samples.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** Small, potentially overlapping or selected cohorts may inflate apparent performance; the 25.71% shadow drawdown also signals meaningful downside despite positive median return.
- **Evidence:**
  - Shadow runner_hunter has 17 completions, 70.59% wins, median net return 1.7066%, and 25.71% maximum drawdown.
  - The separate paper runner_hunter cohort has only 7 completions and median net return -0.3903%, indicating limited and not yet consistent evidence across modes.

**Approve in ChatGPT:**

`Approve P-20261101-02`

**Decline in ChatGPT:**

`Decline P-20261101-02`

---

## Quick commands

`Review today's CryptoTracker proposals`
