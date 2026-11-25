# CryptoTracker Proposals — 2026-11-23

These are the current model-improvement proposals from the nightly review.
Each proposal has a stable ID that can be used directly in ChatGPT.

## P-20261123-01 — Build a shadow matched-outcome review for accepted and rejected candidates

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `SURGE follow-up and missed-opportunity outcome analysis`
- **Current:** 64,032 follow-up rows with no horizons found; 53 audited signal rows including 46 usable rejected signals, with no reported outcome or false-positive-cost summaries
- **Proposed:** Conduct an offline, deduplicated review matched by token and signal time; report 30/60/120-minute hit rates, median returns, MFE/MAE, and false-positive cost separately for accepted and rejected candidates. Do not alter entry thresholds during this review.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** Token/time matching, duplicate signals, incomplete price histories, or selection bias could distort estimated opportunity costs.
- **Evidence:**
  - The follow-up metrics contain no found horizons or score-band results.
  - The missed-opportunity audit identifies 46 usable rejected signals but supplies no outcome breakdown.
  - Available shadow results have negative medians in both strict_baseline (n=12) and xp_balanced_cd0 (n=38), so aggregate means alone are not a sound basis for loosening gates.

**Approve in ChatGPT:**

`Approve P-20261123-01`

**Decline in ChatGPT:**

`Decline P-20261123-01`

---

## P-20261123-02 — Validate Luna outcome linkage before calibration

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `Luna confirmation outcome labeling`
- **Current:** 14 reviewed signals with median confidence 78 and zero labeled outcome rows
- **Proposed:** Run a shadow-only linkage and labeling audit by signal and setup type, then report labeled sample counts, hit rates, median returns, and MFE/MAE by confidence band; make no confidence or gating changes until outcomes are available.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** A small or selectively matchable labeled cohort may create misleading confidence-band estimates.
- **Evidence:**
  - The review log contains 14 signals across four setup categories.
  - Luna outcomes report zero signals and zero labeled rows, preventing calibration despite the logged confidence scores.

**Approve in ChatGPT:**

`Approve P-20261123-02`

**Decline in ChatGPT:**

`Decline P-20261123-02`

---

## P-20261123-03 — Audit smart-money strength and wallet-check data before using campaign signals

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `SmartMoneyMonitor campaign-strength and feed-health validation`
- **Current:** 98 campaign rows across 13 unique campaigns; median strength 0, zero convergence, zero scorecard rows, and 1,970 failed wallet checks
- **Proposed:** Perform a shadow data-integrity review of strength generation, campaign deduplication, convergence calculation, scorecard population, and failed-check denominators. Keep smart-money signal influence unchanged until the audit is complete.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** The apparent zero strength or convergence may reflect field semantics or filtering rather than a feed defect, so an incorrect diagnosis could waste research effort.
- **Evidence:**
  - Campaign strength has a reported median of 0 and multi-wallet convergence count is 0.
  - The wallet scorecard contains zero rows while the feed-health log records 1,970 failed wallet checks.
  - Latest feed status is OK with 100% coverage, but that does not resolve the strength, scorecard, or failure-count discrepancies.

**Approve in ChatGPT:**

`Approve P-20261123-03`

**Decline in ChatGPT:**

`Decline P-20261123-03`

---

## Quick commands

`Review today's CryptoTracker proposals`
