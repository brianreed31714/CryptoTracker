# CryptoTracker Proposals — 2026-11-18

These are the current model-improvement proposals from the nightly review.
Each proposal has a stable ID that can be used directly in ChatGPT.

## P-20261118-01 — Add outcome-label coverage checks to daily evidence

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `Daily evidence pipeline: follow-up, Luna, missed-opportunity, and strategy outcome reporting`
- **Current:** Follow-ups have no reported outcome horizons; Luna outcomes have zero labeled rows; missed-opportunity forward outcomes and MFE/MAE are unavailable in the metrics.
- **Proposed:** In SHADOW/RESEARCH reporting only, publish eligible, matched, and labeled counts by source and horizon, plus MFE/MAE and realized-return coverage where available. Flag missing or unmatched outcomes as unavailable rather than interpreting them as zero. Make no trading-setting changes.
- **Confidence:** MEDIUM
- **Recommended mode:** SHADOW
- **Risk:** Incorrect or survivorship-biased joins could create misleading coverage or outcome statistics; validate token identity, timestamps, horizon definitions, and duplicate handling before using the report for decisions.
- **Evidence:**
  - Follow-up metrics report 59,826 rows but horizons_found is empty.
  - Luna reports 20 reviews but zero outcome rows, signals, or labeled rows.
  - The missed-opportunity audit reports 46 usable rejected signals, but the supplied metrics do not report their forward outcomes or false-positive cost.
  - Live trade metrics report zero buys and sells, leaving no live outcome sample for validation.

**Approve in ChatGPT:**

`Approve P-20261118-01`

**Decline in ChatGPT:**

`Decline P-20261118-01`

---

## Quick commands

`Review today's CryptoTracker proposals`
