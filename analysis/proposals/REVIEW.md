# CryptoTracker Proposals — 2026-11-15

These are the current model-improvement proposals from the nightly review.
Each proposal has a stable ID that can be used directly in ChatGPT.

## P-20261115-01 — Validate follow-up outcome completeness before tuning entries

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `SURGE_FOLLOWUP audit and daily outcome reporting`
- **Current:** 56,676 follow-up rows are reported, but horizons_found and score_bands are empty.
- **Proposed:** In research/shadow, investigate why outcome horizons and score bands are absent; validate horizon coverage and report outcome counts, returns, MFE, and MAE by path and score band before using follow-ups to change entry gates.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** The missing summaries may reflect filtering or report-generation issues rather than missing raw outcomes; conclusions could be biased if the underlying records are incomplete or duplicated.
- **Evidence:**
  - The daily metrics report 56,676 follow-up rows across NONE (49,119), NORMAL (6,754), and EARLY_ACCEL (803).
  - Despite those rows, horizons_found and score_bands are empty, so follow-up outcome quality and rejected-signal cost cannot be assessed.

**Approve in ChatGPT:**

`Approve P-20261115-01`

**Decline in ChatGPT:**

`Decline P-20261115-01`

---

## P-20261115-02 — Keep Luna calibration unchanged pending a larger shadow sample

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `Luna confidence/setup calibration and AI_CONFIRMATION_MAX_BONUS`
- **Current:** AI_CONFIRMATION_MAX_BONUS=5; daily Luna log has 10 reviews.
- **Proposed:** Make no bonus or gate adjustment; shadow-track at least 12 independent Luna-reviewed signals per relevant setup/confidence group, with token-clustered 30/60/120-minute returns, MFE, MAE, and false-positive rates.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** Signals may be correlated or regime-specific, and small-group results may not persist; changing calibration before a larger independent sample could suppress useful confirmations.
- **Evidence:**
  - The daily Luna log contains 10 reviews, below the minimum sample threshold for calibration claims.
  - POSITIVE|MEDIUM outcomes are weak in a small sample: n=5 at 30 and 60 minutes, positive rates 40% and 0%, and median returns -5.213% and -7.771%; n=4 at 120 minutes.

**Approve in ChatGPT:**

`Approve P-20261115-02`

**Decline in ChatGPT:**

`Decline P-20261115-02`

---

## Quick commands

`Review today's CryptoTracker proposals`
