# CryptoTracker Proposals — 2026-11-26

These are the current model-improvement proposals from the nightly review.
Each proposal has a stable ID that can be used directly in ChatGPT.

## P-20261126-01 — Produce signal-level forward-outcome evidence

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `Surge follow-up and missed-opportunity research reporting`
- **Current:** 65,958 follow-up rows are reported, but score bands and outcome horizons are empty; 46 usable rejected signals lack reported outcome attribution.
- **Proposed:** In research/shadow reporting, link records to unique signal and token-time cohorts and report 30/60/120-minute MFE, MAE, executable net return, sample size, median, hit rate, and false-positive cost by path and accepted/rejected status. Do not change trading thresholds based on this report alone.
- **Confidence:** MEDIUM
- **Recommended mode:** SHADOW
- **Risk:** Incorrect signal deduplication, overlapping observation windows, or censored follow-ups could bias outcomes and make repeated scans appear to be independent signals.
- **Evidence:**
  - The follow-up metrics report 65,958 rows but no horizons_found and empty score_bands.
  - The missed-opportunity audit reports 46 usable rejected signals but provides no reported outcome metrics for them.

**Approve in ChatGPT:**

`Approve P-20261126-01`

**Decline in ChatGPT:**

`Decline P-20261126-01`

---

## P-20261126-02 — Collect outcome labels before Luna recalibration

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `Luna confirmation outcome linkage and calibration analysis`
- **Current:** 9 reviewed signals, median confidence 78.0, and 0 reported outcome or labeled rows.
- **Proposed:** Continue shadow-only collection linking each reviewed signal to defined forward outcomes and its setup/confidence; assess calibration only after at least 12 labeled observations, treating that threshold as exploratory rather than proof. Do not tune confidence or setup rules yet.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** Labels may be delayed, selectively missing, or influenced by repeated reviews of the same token, producing misleading calibration.
- **Evidence:**
  - The Luna sample is 9, below the 12-observation review threshold.
  - luna_outcomes reports 0 signals and 0 labeled rows, so predictive accuracy cannot be measured.

**Approve in ChatGPT:**

`Approve P-20261126-02`

**Decline in ChatGPT:**

`Decline P-20261126-02`

---

## P-20261126-03 — Reconcile smart-money campaign and wallet records

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `SmartMoneyMonitor campaign attribution and wallet scorecard audit`
- **Current:** 70 campaign rows represent 3 unique campaigns; median campaign strength is 0, convergence count is 0, and the wallet 30-minute scorecard is empty.
- **Proposed:** Audit campaign-row deduplication, event-to-campaign linkage, wallet scorecard coverage, and failed-check accounting in shadow research before using campaign strength or convergence to alter decisions.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** Over-aggressive deduplication or excluding intermittent wallet failures could hide valid campaign updates or create survivorship bias.
- **Evidence:**
  - The reported campaign count is 70 rows but only 3 unique campaigns, so the row count is not an adequate independent sample.
  - The wallet scorecard contains no rows; feed health reports 2,010 failed wallet checks across 25,601 rows despite latest status OK and 100% latest coverage.

**Approve in ChatGPT:**

`Approve P-20261126-03`

**Decline in ChatGPT:**

`Decline P-20261126-03`

---

## Quick commands

`Review today's CryptoTracker proposals`
