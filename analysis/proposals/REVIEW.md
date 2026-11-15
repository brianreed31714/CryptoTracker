# CryptoTracker Proposals — 2026-11-13

These are the current model-improvement proposals from the nightly review.
Each proposal has a stable ID that can be used directly in ChatGPT.

## P-20261113-01 — Investigate forward-outcome attribution completeness

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `SURGE_FOLLOWUP and missed-opportunity outcome attribution`
- **Current:** Follow-up metrics report no horizons; missed-opportunity audit reports MISSING_FORWARD_HORIZONS, zero 30/60-minute sample rows, and zero usable rejected signals.
- **Proposed:** With human approval, run a shadow-only data-quality investigation of timestamp, token-identity, and horizon joins; report 30/60/120-minute outcome completeness by path before using these records for strategy evaluation. Do not alter signals, trading settings, or execution.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** The investigation may identify a reporting or filtering artifact rather than a collection defect; changing attribution without validation could create misleading labels or double-count outcomes.
- **Evidence:**
  - The 55,069 follow-up rows have no reported horizons or score bands.
  - The missed-opportunity audit has 41 rows but only 1 signal, 1 rejected signal, and 0 usable rejected signals.
  - The latest audit status is MISSING_FORWARD_HORIZONS, with zero 30- and 60-minute sample rows.

**Approve in ChatGPT:**

`Approve P-20261113-01`

**Decline in ChatGPT:**

`Decline P-20261113-01`

---

## Quick commands

`Review today's CryptoTracker proposals`
