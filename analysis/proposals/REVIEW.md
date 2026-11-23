# CryptoTracker Proposals — 2026-11-21

These are the current model-improvement proposals from the nightly review.
Each proposal has a stable ID that can be used directly in ChatGPT.

## P-20261121-01 — Continue SHADOW validation with outcome and execution labeling

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `Paper/shadow evaluation and daily outcome reporting`
- **Current:** No promotion candidates; follow-up horizons and Luna labeled outcomes are absent from the reported metrics; rejected-signal outcomes are not summarized.
- **Proposed:** Keep model and configuration settings unchanged in SHADOW. Reconcile token-level outcome labels and report independent or matched completed observations, median net return, hit rate, MFE/MAE, execution costs, and rejected-signal outcomes. Do not treat 12 observations as proof; require at least 12 relevant observations before considering a promotion review.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** Additional shadow evaluation costs time and may not resolve model differences if candidate samples overlap or outcome labels remain incomplete; small samples can still produce misleading rankings.
- **Evidence:**
  - Live trade metrics show 0 buys and 0 sells, with no usable realized execution or exit sample.
  - Luna has 8 reviewed rows and 0 labeled outcome rows; follow-up metrics report no horizons found.
  - The strongest-looking shadow variants have only 15 to 19 completions and report maximum drawdowns of 28.60% to 33.14%.
  - The missed-opportunity audit has 46 usable rejected signals but no reported outcome or MFE breakdown.

**Approve in ChatGPT:**

`Approve P-20261121-01`

**Decline in ChatGPT:**

`Decline P-20261121-01`

---

## Quick commands

`Review today's CryptoTracker proposals`
