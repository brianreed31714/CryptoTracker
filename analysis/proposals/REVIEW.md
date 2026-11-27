# CryptoTracker Proposals — 2026-11-25

These are the current model-improvement proposals from the nightly review.
Each proposal has a stable ID that can be used directly in ChatGPT.

## P-20261125-01 — Reconcile follow-up outcome coverage before strategy evaluation

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `SURGE_FOLLOWUP audit and outcome reporting`
- **Current:** 65,434 follow-up rows are reported, but score_bands is empty and horizons_found is empty; usable 30/60/120-minute outcome coverage is not demonstrated.
- **Proposed:** With human approval, perform a research-only audit of timestamp, token/signal joins, horizon availability, and outcome-label generation; report coverage and join failures before using these records to compare entry paths or false positives. Do not alter trading thresholds.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** A broader join or horizon window could create stale or mismatched labels and falsely inflate apparent opportunity quality.
- **Evidence:**
  - The daily metrics report 65,434 follow-up rows but no found outcome horizons.
  - The missed-opportunity audit reports 46 usable rejected signals but does not provide measured MFE/MAE or threshold-hit counts.

**Approve in ChatGPT:**

`Approve P-20261125-01`

**Decline in ChatGPT:**

`Decline P-20261125-01`

---

## P-20261125-02 — Reconcile smart-money export counts with feed-health counters

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `SmartMoneyMonitor daily event/campaign export and feed-health audit`
- **Current:** Daily filtered event and campaign exports each report 0 rows, while feed health reports 1,685 event and 1,685 campaign row deltas, 100% latest wallet coverage, and 0 event-without-campaign cycles.
- **Proposed:** With human approval, compare export time windows, timestamp filters, and row-count definitions, then document whether the zero-row exports are expected. Do not widen discovery or change trading behavior until the discrepancy is explained.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** Treating counters from different windows or scopes as equivalent could lead to unnecessary pipeline changes or reliance on stale campaign data.
- **Evidence:**
  - The manifest records 0 filtered rows for smart_money_events_v22.csv and smart_money_campaigns_v22.csv.
  - Feed-health metrics report 1,685 event_rows_delta and 1,685 campaign_rows_delta, with latest status OK and 100% latest wallet coverage.

**Approve in ChatGPT:**

`Approve P-20261125-02`

**Decline in ChatGPT:**

`Decline P-20261125-02`

---

## Quick commands

`Review today's CryptoTracker proposals`
