# CryptoTracker Proposals — 2026-11-22

These are the current model-improvement proposals from the nightly review.
Each proposal has a stable ID that can be used directly in ChatGPT.

## P-20261122-01 — Require outcome coverage before strategy conclusions

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `Daily evidence and outcome-labeling review`
- **Current:** Follow-up horizon coverage is unavailable; Luna has 0 labeled outcomes; MFE/MAE and rejected-signal false-positive cost are not reported.
- **Proposed:** For research reviews, report matched sample counts by path and horizon, outcome-label coverage, MFE/MAE when available, and cost-adjusted outcomes for accepted and rejected signals before recommending parameter changes.
- **Confidence:** HIGH
- **Recommended mode:** SHADOW
- **Risk:** Additional labeling and matching requirements may delay conclusions; incomplete or mismatched outcomes could still bias comparisons.
- **Evidence:**
  - The supplied metrics report 63,500 follow-up rows but horizons_found is empty.
  - Luna outcomes report 0 rows and 0 labeled rows for 15 reviewed signals.
  - The missed-opportunity audit has 46 usable rejected signals but no reported outcome or false-positive-cost summary.

**Approve in ChatGPT:**

`Approve P-20261122-01`

**Decline in ChatGPT:**

`Decline P-20261122-01`

---

## P-20261122-02 — Continue runner_hunter shadow validation

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `paper_shadow_research.runner_hunter`
- **Current:** 13 completed shadow observations: 8 wins, 5 losses, 61.54% win rate, median net return 2.0368%, profit factor 2.0887%, and maximum drawdown 15.2702%; no promotion candidate is reported.
- **Proposed:** Keep runner_hunter in SHADOW and collect a further, independently timestamped cohort with comparable outcome and execution-cost reporting before considering promotion; make no live or configuration change.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** The apparent performance may reflect selection, overlapping observations, regime dependence, or costs not represented in the reported returns.
- **Evidence:**
  - The shadow result is directionally promising but based on only 13 completed observations.
  - The paper_research result for runner_hunter is only 4 completed observations, so it does not independently validate the shadow result.
  - The supplied research summary lists no promotion candidates, and shadow realized PnL is reported as $0.

**Approve in ChatGPT:**

`Approve P-20261122-02`

**Decline in ChatGPT:**

`Decline P-20261122-02`

---

## Quick commands

`Review today's CryptoTracker proposals`
