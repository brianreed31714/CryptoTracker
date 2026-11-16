# CryptoTracker Proposals — 2026-11-14

These are the current model-improvement proposals from the nightly review.
Each proposal has a stable ID that can be used directly in ChatGPT.

## P-20261114-01 — Continue shadow evaluation of early_breakout

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `paper_shadow_research / early_breakout`
- **Current:** 17 completed shadow trades; 8 wins, 9 losses; median net return -0.2262%; profit factor 1.3942; maximum drawdown 13.5663%
- **Proposed:** Keep the existing model in SHADOW without changing its rules; collect at least 30 completed observations and report median return, hit rate, MFE/MAE, and drawdown before considering promotion.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** The apparent positive mean and profit factor may not persist; additional shadow results may remain regime-specific and do not establish live execution performance.
- **Evidence:**
  - The 17-observation cohort is below the 30-observation research checkpoint and below the 12-observation minimum for treating a result as more than preliminary.
  - Mean net return is +0.691% while median net return is -0.2262%, consistent with a result that may depend on a small number of large outcomes.
  - No promotion candidates are reported.

**Approve in ChatGPT:**

`Approve P-20261114-01`

**Decline in ChatGPT:**

`Decline P-20261114-01`

---

## P-20261114-02 — Extend the extended_probe shadow sample

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `paper_shadow_research / extended_probe`
- **Current:** 8 completed shadow trades; 4 wins, 4 losses; median net return 2.1187%; profit factor 2.4868; maximum drawdown 7.1803%
- **Proposed:** Continue the unchanged model in SHADOW and review again after at least 30 completed observations, including MFE/MAE and false-positive cost for rejected or failed candidates.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** The favorable early results may be chance-driven or tied to a narrow market regime; the sample does not validate live fills or tail risk.
- **Evidence:**
  - The current sample of 8 is too small to establish the reported positive median or profit factor.
  - The reported mean net return is 3.7962%, notably above the median 2.1187%, so outcome concentration should be checked as the sample grows.
  - No promotion candidates are reported.

**Approve in ChatGPT:**

`Approve P-20261114-02`

**Decline in ChatGPT:**

`Decline P-20261114-02`

---

## P-20261114-03 — Audit smart-money export coverage before using campaign signals

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `SmartMoneyMonitor daily event/campaign export and feed-health reconciliation`
- **Current:** Date-filtered event, campaign, and wallet-scorecard exports each show 0 rows; feed-health reports latest status OK, 100% latest wallet coverage, and 1,767 failed wallet checks across 16,962 rows.
- **Proposed:** Reconcile export time windows, filtering, and event-to-campaign joins against feed-health deltas; publish date-scoped counts and coverage before evaluating campaign strength. Do not change signal weights during this audit.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** The zero-row exports may be expected for the review window rather than a pipeline defect; changing signal use before confirming scope could discard valid information or overstate data availability.
- **Evidence:**
  - The daily filtered smart-money files contain zero rows, preventing calculation of campaign strength or convergence for this review.
  - Feed-health reports event and campaign row deltas of 1,318 and zero event-without-campaign cycles, indicating the zero-row exports need a scope or export reconciliation before interpretation.
  - The same feed-health file reports 1,767 failed wallet checks, despite 100% latest coverage.

**Approve in ChatGPT:**

`Approve P-20261114-03`

**Decline in ChatGPT:**

`Decline P-20261114-03`

---

## P-20261114-04 — Complete rejected-signal outcome and cost analysis

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `missed_opportunity_audit / rejected-signal forward outcomes`
- **Current:** Audit reports 78 usable rejected signals and 83/78 sampled 30m/60m rows, but the supplied metrics contain no outcome hit rates, MFE/MAE summaries, or false-positive cost.
- **Proposed:** Produce a date-scoped rejected-signal analysis with deduplicated counts, 30m/60m/120m hit rates, median MFE/MAE, and an explicit false-positive cost before proposing any entry-gate change.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** Outcome windows may be incomplete or overlapping, and retrospective labeling can overstate opportunity quality if it does not account for executable prices and costs.
- **Evidence:**
  - The audit establishes a rejected-signal sample but does not report whether those signals met a consistent missed-opportunity outcome definition.
  - Without outcome distributions and false-positive cost, the report counts alone cannot establish that relaxing a gate would improve expected results.
  - There were no live trades on the review date to validate any proposed gate relaxation.

**Approve in ChatGPT:**

`Approve P-20261114-04`

**Decline in ChatGPT:**

`Decline P-20261114-04`

---

## Quick commands

`Review today's CryptoTracker proposals`
