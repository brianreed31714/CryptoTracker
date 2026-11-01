# CryptoTracker Proposals — 2026-10-30

These are the current model-improvement proposals from the nightly review.
Each proposal has a stable ID that can be used directly in ChatGPT.

## P-20261030-01 — Continue organic-flow model in shadow only

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `paper_research model xp_diy_organic_flow`
- **Current:** Shadow evaluation; 13 completed; no promotion candidate
- **Proposed:** Keep in SHADOW and collect a larger, deduplicated, matched comparison against the baseline across market conditions before considering any promotion; make no live or entry-rule change.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** A small or right-tail-driven result may not persist; overlapping candidates, selection effects, and unmodeled execution costs may overstate performance.
- **Evidence:**
  - 13 completed shadow observations: 9 wins and 4 losses (69.23% win rate).
  - Median net return is 6.978%, profit factor 6.7411, and max drawdown 10.0198%; shadow realized PnL is reported as 0.
  - The sample is small, model variants may share candidate observations, and the research summary lists no promotion candidates.

**Approve in ChatGPT:**

`Approve P-20261030-01`

**Decline in ChatGPT:**

`Decline P-20261030-01`

---

## P-20261030-02 — Validate follow-up and missed-opportunity outcome reporting

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `SURGE_FOLLOWUP and MISSED_OPPORTUNITY audit/reporting`
- **Current:** 41,323 follow-up rows with no reported horizons or score bands; 78 usable rejected signals without summarized outcomes
- **Proposed:** Audit outcome coverage and deduplication, then report sample counts and token-level 30/60/120-minute returns, MFE, and MAE by path, acceptance status, and rejection reason before using these data to tune trading rules.
- **Confidence:** MEDIUM
- **Recommended mode:** SHADOW
- **Risk:** Duplicate or incomplete token-horizon observations, survivorship/selection bias, or inconsistent labels could produce misleading group comparisons.
- **Evidence:**
  - The follow-up summary reports 41,323 rows and path counts but empty score_bands and horizons_found.
  - The missed-opportunity audit reports 78 usable rejected signals and 87 sampled rows at both 30 and 60 minutes, but no outcome values in the supplied metrics.
  - Without outcome distributions and rejection-reason attribution, false-positive cost and missed-signal value cannot be estimated.

**Approve in ChatGPT:**

`Approve P-20261030-02`

**Decline in ChatGPT:**

`Decline P-20261030-02`

---

## Quick commands

`Review today's CryptoTracker proposals`
