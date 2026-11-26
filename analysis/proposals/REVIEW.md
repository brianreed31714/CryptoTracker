# CryptoTracker Proposals — 2026-11-24

These are the current model-improvement proposals from the nightly review.
Each proposal has a stable ID that can be used directly in ChatGPT.

## P-20261124-01 — Reconcile paper and shadow return attribution before ranking models

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `paper_research performance attribution`
- **Current:** 39 completed paper model observations and 258 completed shadow model observations are summarized across models; no preliminary paper leader or promotion candidate is reported.
- **Proposed:** Run a shadow-only per-trade reconciliation of entry/exit prices, fees, assumed slippage, net return, dollar PnL, exit reason, and MFE/MAE; document cohort overlap and defer model ranking or promotion until the accounting is coherent.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** Reconciliation may identify non-comparable or incomplete cohorts, delaying model comparisons; results must not be treated as an out-of-sample performance guarantee.
- **Evidence:**
  - diy_whale paper results (n=10) show 40% wins, median net return -1.1251%, and profit factor 0.0259, while its shadow results (n=14) show 57.14% wins, median +1.8038%, and profit factor 46.5769.
  - The diy_whale paper average net return is -20.5363% versus a median of -1.1251%; its shadow average is +34.6544% versus a median of +1.8038%, indicating substantial mean/median divergence.
  - Shadow summaries report $0 realized PnL while reporting nonzero net returns; the supplied metrics do not explain that accounting convention.

**Approve in ChatGPT:**

`Approve P-20261124-01`

**Decline in ChatGPT:**

`Decline P-20261124-01`

---

## P-20261124-02 — Label rejected-signal outcomes and false-positive cost

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `missed_opportunity_audit outcome analysis`
- **Current:** The audit has 53 signal rows and 46 usable rejected signals, but the supplied summary contains no MFE/MAE, hit rates, or false-positive cost.
- **Proposed:** For the existing rejected-signal sample, produce a shadow-only outcome table at the reported 30- and 60-minute horizons with MFE, MAE, executable-price assumptions, and false-positive cost; do not relax entry gates based on counts alone.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** Sparse or survivorship-biased follow-up coverage, and optimistic price marks, could overstate missed opportunity; require executable-price and missing-outcome reporting.
- **Evidence:**
  - The audit reports 46 usable rejected signals out of 53 signal rows.
  - The 30- and 60-minute samples each contain 53 rows, but no corresponding outcome statistics are supplied.
  - The configured missed-opportunity MFE flags (20% at 30 minutes and 50% at 60 minutes) do not by themselves quantify rejection precision or the cost of false positives.

**Approve in ChatGPT:**

`Approve P-20261124-02`

**Decline in ChatGPT:**

`Decline P-20261124-02`

---

## P-20261124-03 — Build a labeled Luna calibration cohort before tuning

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `Luna signal outcome labeling`
- **Current:** Three Luna signals are logged and no Luna outcome rows or labeled rows are reported.
- **Proposed:** Accumulate a shadow-only cohort with confidence, setup type, and fixed-horizon outcome labels including MFE and MAE; defer calibration or threshold changes until at least 12 relevant labeled observations are available.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** Even 12 observations may be underpowered or regime-specific; the proposed minimum is a research checkpoint, not proof of calibration.
- **Evidence:**
  - The current Luna sample is n=3, with two EARLY_ACCELERATION signals and one CONFLICTING_SIGNAL.
  - Median confidence is 75.0, but there are 0 outcome rows and 0 labeled rows, so confidence-to-outcome calibration cannot be assessed.

**Approve in ChatGPT:**

`Approve P-20261124-03`

**Decline in ChatGPT:**

`Decline P-20261124-03`

---

## Quick commands

`Review today's CryptoTracker proposals`
