# CryptoTracker Proposals — 2026-11-20

These are the current model-improvement proposals from the nightly review.
Each proposal has a stable ID that can be used directly in ChatGPT.

## P-20261120-01 — Keep early_breakout shadow-only and extend validation

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `paper_research.early_breakout`
- **Current:** 16 completed shadow observations; no promotion candidate; no live execution evidence
- **Proposed:** Continue shadow-only evaluation and do not promote. Reassess after a larger set of independent observations with execution costs and MFE/MAE reported.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** Shadow returns may overstate executable results, and overlapping token or time-window observations could make the effective sample smaller than 16.
- **Evidence:**
  - Shadow early_breakout has 16 completed observations, 11 wins (68.75%), median net return 1.7072%, and maximum drawdown 3.0082%.
  - The shadow result is not realized PnL, and the research summary lists no promotion candidates.
  - Paper results across model variants are weak and do not independently confirm this shadow result.

**Approve in ChatGPT:**

`Approve P-20261120-01`

**Decline in ChatGPT:**

`Decline P-20261120-01`

---

## P-20261120-02 — Reconcile forward outcomes before tuning signal gates

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `surge_followup and missed_opportunity outcome reporting`
- **Current:** 61,520 follow-up rows with no reported horizons or score bands; 46 usable rejected signals without reported MFE/MAE outcomes
- **Proposed:** Conduct a research-only linkage audit for accepted and rejected signals, reporting available 30/60/120-minute MFE/MAE, entry quote costs, and false-positive costs before changing thresholds.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** Timestamp or token-identity mismatches could bias linked outcomes; unavailable market data may leave some signals unlabeled.
- **Evidence:**
  - The follow-up summary reports horizons_found as empty and score_bands as empty.
  - The missed-opportunity audit reports 46 usable rejected signals but no outcome MFE values in the supplied metrics.
  - Without these outcomes, current anti-chase and missed-opportunity thresholds cannot be evaluated for benefit versus false-positive cost.

**Approve in ChatGPT:**

`Approve P-20261120-02`

**Decline in ChatGPT:**

`Decline P-20261120-02`

---

## Quick commands

`Review today's CryptoTracker proposals`
