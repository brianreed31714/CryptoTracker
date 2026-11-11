# CryptoTracker Proposals — 2026-11-09

These are the current model-improvement proposals from the nightly review.
Each proposal has a stable ID that can be used directly in ChatGPT.

## P-20261109-01 — Run matched-entry, exit-only shadow comparison

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `Paper/shadow exit evaluation`
- **Current:** fast_exit is the paper preliminary leader but has 14 completed trades and negative net results; no promotion candidates are reported.
- **Proposed:** Continue shadow evaluation using matched candidate entries and vary only the exit rule; report signal-level net returns, hit rate, MFE/MAE, and execution assumptions before considering any promotion.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** Shadow results can remain biased by overlapping candidates, outliers, incomplete outcomes, or unrealistic execution assumptions; they must not be treated as live-performance evidence.
- **Evidence:**
  - fast_exit: n=14, 5 wins and 9 losses, median net return -1.1482%, profit factor 0.3444.
  - Shadow flow_breakout: n=22, average net return +2.7054% but median -0.5078%; the positive average does not establish robust performance.
  - No model is listed as a promotion candidate, and available summaries do not isolate exit effects on matched entries.

**Approve in ChatGPT:**

`Approve P-20261109-01`

**Decline in ChatGPT:**

`Decline P-20261109-01`

---

## P-20261109-02 — Validate Luna outcomes at the signal level before recalibration

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `Luna confidence and setup calibration`
- **Current:** Luna has 17 daily review rows; outcome summaries group 106 signals across multiple horizons, with several setup/confidence groups below 12 observations.
- **Proposed:** Produce a signal-level calibration study by setup and confidence, preserving horizon outcomes per signal and reporting sample sizes, median return, hit rate, MFE, and MAE; leave Luna scoring and thresholds unchanged during the study.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** Small or selectively labeled groups may produce unstable calibration estimates, and horizon outcomes from one signal are correlated.
- **Evidence:**
  - POSITIVE|MEDIUM has n=8 per horizon and changes from +2.125% median return at 30 minutes to -1.502% at 60 minutes.
  - NEUTRAL|HIGH has only n=2; other NEUTRAL|MEDIUM results have n=1.
  - The 318 outcome rows span 106 signals and multiple horizons, so treating rows as independent would overstate evidence.

**Approve in ChatGPT:**

`Approve P-20261109-02`

**Decline in ChatGPT:**

`Decline P-20261109-02`

---

## P-20261109-03 — Reconcile rejected-signal outcome coverage

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `Missed-opportunity audit and follow-up reporting`
- **Current:** The audit reports 93 usable rejected signals; reported 30- and 60-minute samples are 105 and 102, without rejected-signal MFE/MAE or false-positive-cost summaries.
- **Proposed:** Reconcile signal-to-outcome linkage and horizon coverage, then report rejected-signal MFE/MAE and estimated false-negative opportunity separately from accepted-signal outcomes; make no entry-gate changes until those results are available.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** Outcome linkage or survivorship effects may bias retrospective estimates, and future market conditions may not match the reviewed sample.
- **Evidence:**
  - The audit lists 106 signal rows, 94 rejected rows, and 93 usable rejected signals.
  - Reported horizon sample counts differ from usable rejected-signal count, and the daily metrics provide no rejected-signal return or MFE/MAE breakdown.
  - Without outcome-linked rejection costs, the current evidence cannot quantify the trade-off between missed winners and avoided false positives.

**Approve in ChatGPT:**

`Approve P-20261109-03`

**Decline in ChatGPT:**

`Decline P-20261109-03`

---

## P-20261109-04 — Audit smart-money campaign score coverage

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `SmartMoneyMonitor campaign and wallet scorecard pipeline`
- **Current:** There are 31 campaign rows across 13 unique campaigns, median campaign strength is 0, multi-wallet convergence is 0, and the wallet 30-minute scorecard is empty.
- **Proposed:** Verify campaign-strength and convergence calculation coverage, including why the scorecard is empty, and keep smart-money signals observational until coverage and outcome value are demonstrated.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** A coverage issue may be temporary or limited to the filtered daily extract; changing signal weighting before diagnosis could discard useful information or amplify unvalidated data.
- **Evidence:**
  - Campaign strength median is 0 and multi-wallet convergence count is 0 in the daily metrics.
  - The wallet 30-minute scorecard contains no rows.
  - Feed health is latest OK with 100% latest wallet coverage, but the log also records 1,737 failed wallet checks across 15,570 rows.

**Approve in ChatGPT:**

`Approve P-20261109-04`

**Decline in ChatGPT:**

`Decline P-20261109-04`

---

## Quick commands

`Review today's CryptoTracker proposals`
