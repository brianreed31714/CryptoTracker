# CryptoTracker Proposals — 2026-11-08

These are the current model-improvement proposals from the nightly review.
Each proposal has a stable ID that can be used directly in ChatGPT.

## P-20261108-01 — Validate shadow return and profit-factor aggregation

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `Paper/shadow trade outcome and model-ranking reports`
- **Current:** Shadow model summaries include extreme average returns and profit factors that are far from their medians, alongside substantial drawdowns; no promotion candidates are reported.
- **Proposed:** In SHADOW, reconcile trade-level returns, units, outliers, and aggregation for the affected models before using mean return or profit factor in rankings. Preserve uncapped results and report robust summaries; make no model or execution changes during the audit.
- **Confidence:** MEDIUM
- **Recommended mode:** SHADOW
- **Risk:** A legitimate small number of extreme runner outcomes may explain the mean/median gap; treating them as errors or capping them could understate genuine tail performance.
- **Evidence:**
  - Runner Hunter: n=24, 50.0% win rate, median return +0.0215%, average +537.5367%, PF 78.5146, and max drawdown 77.9215%.
  - Extended Probe: n=10, median return +8.1788% versus average +1292.986% and max drawdown 72.9329%.
  - Several shadow models report zero realized PnL, so the return summaries require interpretation distinct from realized account performance.

**Approve in ChatGPT:**

`Approve P-20261108-01`

**Decline in ChatGPT:**

`Decline P-20261108-01`

---

## P-20261108-02 — Run matched shadow replay for exit variants

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `Patient Runner versus Fast Exit outcome evaluation`
- **Current:** Exit summaries are separate model aggregates; same-entry pairing and comparable censoring are not established.
- **Proposed:** Compare both exit policies on the same eligible entries in SHADOW, recording net return, hit rate, MFE, MAE, and drawdown at common horizons. Keep live and paper exit settings unchanged until the paired evaluation is sufficiently populated.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** A matched sample may be smaller or affected by incomplete outcome horizons; apparent differences may not generalize to future market regimes.
- **Evidence:**
  - Patient Runner: n=37, 56.76% wins, median net return +1.7783%, max drawdown 81.4708%.
  - Fast Exit: n=37, 51.35% wins, median net return +0.4288%, max drawdown 29.3443%.
  - The aggregate profiles suggest a return-versus-drawdown trade-off, but the available summaries do not establish a controlled comparison.

**Approve in ChatGPT:**

`Approve P-20261108-02`

**Decline in ChatGPT:**

`Decline P-20261108-02`

---

## P-20261108-03 — Continue horizon-specific Luna calibration in shadow

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `Luna confirmation calibration and outcome reporting`
- **Current:** AI confirmation is enabled with a maximum bonus of 5; the available outcome groups include only 13 POSITIVE|MEDIUM signals per horizon.
- **Proposed:** Keep Luna scoring and thresholds unchanged while tracking signal-level, horizon-specific outcomes against matched quant-valid controls in SHADOW. Report sample sizes, hit rates, median return, MFE, and MAE before considering any calibration change.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** Signals are few and horizon outcomes overlap; selection effects or market-regime changes could produce misleading calibration conclusions.
- **Evidence:**
  - For POSITIVE|MEDIUM, n=13 at each horizon; median return is +0.347% at 30m, -2.504% at 60m, and -18.16% at 120m.
  - For the same group, median MFE increases from 13.558% at 30m to 21.531% at 120m, while median MAE worsens from -9.505% to -19.147%.
  - The daily review contains 21 Luna rows, which is too small to establish a calibration change.

**Approve in ChatGPT:**

`Approve P-20261108-03`

**Decline in ChatGPT:**

`Decline P-20261108-03`

---

## Quick commands

`Review today's CryptoTracker proposals`
