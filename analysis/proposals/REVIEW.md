# CryptoTracker Proposals — 2026-11-06

These are the current model-improvement proposals from the nightly review.
Each proposal has a stable ID that can be used directly in ChatGPT.

## P-20261106-01 — Validate follow-up outcome coverage before gate tuning

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `SURGE_FOLLOWUP outcome collection and daily reporting`
- **Current:** SURGE_FOLLOWUP_ENABLED=1; 50,586 follow-up rows are reported, but horizons_found is empty and score_bands is empty.
- **Proposed:** Keep collection in SHADOW and conduct a human-reviewed data audit distinguishing immature observations from missing or unmatched 30/60/120-minute outcomes; report horizon coverage by accepted/rejected status and rejection reason before using these data for strategy changes.
- **Confidence:** MEDIUM
- **Recommended mode:** SHADOW
- **Risk:** The empty horizon summary may reflect a reporting or maturity issue rather than missing outcome capture; the audit may take time and delay strategy decisions.
- **Evidence:**
  - The daily metrics report 50,586 follow-up rows but horizons_found=[].
  - The missed-opportunity audit reports 62 usable rejected signals, but the available summary does not provide outcome coverage or false-positive cost by rejection reason.
  - Without validated horizon coverage, missed-opportunity and follow-up evidence cannot reliably support entry-gate changes.

**Approve in ChatGPT:**

`Approve P-20261106-01`

**Decline in ChatGPT:**

`Decline P-20261106-01`

---

## Quick commands

`Review today's CryptoTracker proposals`
