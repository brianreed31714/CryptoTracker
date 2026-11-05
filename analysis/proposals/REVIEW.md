# CryptoTracker Proposals — 2026-11-02

These are the current model-improvement proposals from the nightly review.
Each proposal has a stable ID that can be used directly in ChatGPT.

## P-20261102-01 — Validate follow-up outcome linkage before strategy tuning

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `SURGE_FOLLOWUP outcome reporting and missed-opportunity audit`
- **Current:** 45,560 follow-up rows; score_bands is empty and horizons_found is empty in the supplied metrics, despite an available missed-opportunity report.
- **Proposed:** In shadow research, audit deduplication and token/signal-to-outcome joins, then report 30/60/120-minute outcome coverage and rejection-level MFE, MAE, and false-positive cost before changing entry or rejection rules.
- **Confidence:** MEDIUM
- **Recommended mode:** SHADOW
- **Risk:** Join or deduplication errors could create misleading outcome rates; validate samples against source records before using the report for decisions.
- **Evidence:**
  - Follow-up metrics contain 45,560 rows but no score bands or horizons.
  - The missed-opportunity audit has 101 usable rejected signals but supplies no rejection-level cost or outcome summary.

**Approve in ChatGPT:**

`Approve P-20261102-01`

**Decline in ChatGPT:**

`Decline P-20261102-01`

---

## P-20261102-02 — Continue runner comparison without promotion

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `Shadow runner model evaluation`
- **Current:** runner_hunter has 11 completed trades and xp_runner_control has 13; no promotion candidates are reported.
- **Proposed:** Keep both variants in shadow and collect a deduplicated, candidate-matched comparison with entry and exit outcomes before considering any promotion; make no live or paper execution change from these aggregates.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** Promising small-sample results may regress out of sample or reflect overlapping candidates and selection effects.
- **Evidence:**
  - runner_hunter reports 8 wins from 11 trades, median net return 5.7708%, and profit factor 12.8313.
  - xp_runner_control reports 9 wins from 13 trades, median net return 5.7708%, and profit factor 7.0586.
  - The samples are small, and the reported shadow metrics do not establish independence or a causal advantage over a matched control.

**Approve in ChatGPT:**

`Approve P-20261102-02`

**Decline in ChatGPT:**

`Decline P-20261102-02`

---

## P-20261102-03 — Audit smart-money campaign strength inputs

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `SmartMoneyMonitor campaign scoring and wallet scorecard`
- **Current:** 120 campaign rows across 21 unique campaigns; median campaign strength 0, no multi-wallet convergence, and no wallet 30-minute scorecard entries.
- **Proposed:** In shadow research, verify campaign-strength and wallet-scorecard input coverage and scoring semantics against source events; do not use campaign strength to alter ranking or entries until the audit is complete.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** An audit may identify no data defect; treating the current zero values as a defect without source-level validation could lead to unjustified signal changes.
- **Evidence:**
  - Feed health reports latest status OK and 100% latest wallet coverage, but also 1,356 failed wallet checks in the available history.
  - The campaign metrics show zero median strength and zero multi-wallet convergence, while the wallet scorecard is empty.

**Approve in ChatGPT:**

`Approve P-20261102-03`

**Decline in ChatGPT:**

`Decline P-20261102-03`

---

## Quick commands

`Review today's CryptoTracker proposals`
