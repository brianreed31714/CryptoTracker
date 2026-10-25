# CryptoTracker nightly three-sleeve review — 2026-10-24 (Pacific)

**Evidence cutoff:** October 24, 2026, approximately 18:05 Pacific. Latest sanitized completed-day publication is **2026-10-23**, GitHub main `9f8e724e9b7bcb9f25519639ff56c0c09dc19d5b`. No October 24 daily publication is available at this cutoff; October 21 is also missing. Do not infer an October 24 trading outcome or a confirmed outage from absence of that report.

**Control status:** PAPER ONLY, zero live swaps, original Balanced EV, Runner Hunter and DIY Whale eligibility/exit/sizing frozen. Do not activate real money, increase risk, promote variants or restart host services based on this report.

## Comparable October 23 paper results

| Baseline | Closed | Daily wins | Daily mean modeled net/trade | Daily realized-only equity return | Since-inception realized-only equity return | Inception realized-only max drawdown | Daily realized paper P&L |
|---|---:|---:|---:|---:|---:|---:|---:|
| Balanced EV | 3 | 0/3 (0%) | -1.991% | **-0.5352%** | +11.0106% | 11.9289% | -$0.089593 |
| Runner Hunter | 10 | 3/10 (30%) | -3.448% | **-1.7938%** | -5.6194% | 5.8265% | -$0.258587 |
| DIY Whale | 22 | 10/22 (45.5%) | -4.862% | **-5.6195%** | -10.1757% | 10.7851% | -$0.802229 |

All three lost money on October 23. Versus the previous **available** daily observation (October 22), Balanced EV moved from +1.2017% to -0.5352%; Runner Hunter from -2.6421% to -1.7938%; DIY Whale from +2.5672% to -5.6195%. These are *realized-equity-only* paper metrics from different inception dates, not comparable full-account mark-to-market (MTM) performance or evidence of a profitable trading strategy. Open positions are not valued. All three miss the aspirational compounded +1% per calendar day since inception; the account-size basis is roughly $15 of simulated equity per sleeve, not a verified $800–$1,000 capacity test. Balanced EV has the highest inception realized-only return but its 11.93% drawdown breaches the provisional <5% research preference.

## Campaign regime / chronological holdout (descriptive, not causal)

The cumulative campaign's 70/30 chronological split (from the latest October 23 campaign file) shows **no baseline passed the stable-positive-holdout gate**. Balanced EV has 158 cumulative completed exits, holdout 48, mean modeled net +0.485% per exit, holdout profit factor **1.241** (<1.3 gate). Runner Hunter has 91 cumulative exits, holdout 28, mean **-3.542%** and PF **0.405**. DIY Whale has 226 cumulative exits, holdout 68, mean **-2.855%** and PF **0.554**. These are trade-level modeled outcomes, not portfolio MTM; the legacy trade-compounded holdout drawdown is not an account-equity drawdown.

**DIY Whale's regime split is striking but unproven:** RISK_OFF had **147/226** historical exits, mean modeled net **-2.125%**, cumulative paper P&L **-$2.343164** and PF **0.698**; NEUTRAL had 74 exits, mean **+1.377%**, P&L **+$0.763983** and PF **1.509**; RISK_ON had only 5 exits (insufficient). These groups were not randomized and may differ by token, time, quote cost, liquidity and exposure. The already-registered `xp_diy_neutral_only` and `xp_diy_riskoff_strict` paper shadow arms are the appropriate **prospective** tests; **do not retroactively disable baseline RISK_OFF entries or claim a causal edge**. Reconciliation mismatches also constrain historical attribution.

## Material stop-loss risk and quote integrity

**DIY Whale October 23 YMBCOIN:** `STOP` after ~4.05 minutes, modeled net **-62.1557%** on the trade (raw token price **-50.0653%**, estimated quote cost **12.0904 percentage points**), against the model's **-8%** stop trigger. The observed raw price was **42.0653 percentage points** below trigger; estimated net return was **54.1557 points** below trigger. Paper P&L -$0.466168 represented about **58% of DIY Whale's -$0.802229 daily loss**. Entry regime was RISK_OFF. This follows October 22 Runner Hunter's KIMCHIBULL `STOP` **-66.9973% estimated net** against its -7% trigger.

**Runner Hunter October 23 SI276:** `STOP` modeled net **-18.8733%** (raw **-11.5918%**, estimated quote cost **7.2815 points**) against -7% trigger. A stop trigger is not a guaranteed liquidation price. We **cannot attribute the root cause** to latency, quote age, route changes, low depth or gaps without timestamped observation and quote provenance; the ~4-minute trade duration is **not quote age**.

October 23 simulated quote-quality flags:
- Balanced EV: 0 negative-cost exits; 0 with >5% estimated cost; 3/3 exits optional Helius unavailable.
- Runner Hunter: 1 negative-cost exit; 2/10 with >5% estimated cost; 10/10 Helius unavailable.
- DIY Whale: 5 negative-cost exits; 6/22 with >5% estimated cost; 22/22 Helius unavailable; 11/22 entries RISK_OFF; 1 exit below -20% modeled net. One mint recorded seven repeated losing exits.

**Helius**: all 35 focused October 23 exits lacked optional Helius evidence. Consequently there is no independent wallet-level organic-buying confirmation. Negative quote-cost estimates can indicate inconsistent mark/quote comparisons; they are not risk-free positive slippage. `EXECUTABLE_JUPITER` is a **simulated quote label**, not a real fill. The available trade CSV does **not** carry a timestamp for the liquidation quote, so freshness cannot be independently established.

## Reconciliation and publication integrity

The October 23 `quality_audit.json` reports `mismatch_review_required`: Balanced EV's campaign completed-count delta **5** vs **3** daily exits; DIY Whale's **26** vs **22**; Runner Hunter **10** vs **10** reconciles. Possible backfill/corrections are hypotheses, not confirmed explanations. October 21's daily publication remains missing.

The October 23 manifest lists source `bcb71184553da92043394f7444bf2d188c44a69e`, but lacks `shadow_experiments.json/.md` and `improvement_diagnostics.json/.md` even though those are generated by the publisher source at that commit. Its `raw/shadow_trades.csv` has the **legacy 13-column header**, without new `name_category_flags`, `organic_flow_at_entry`, or `novelty_study_version`. This is a concrete **published-output/source-contract mismatch**. A stale in-memory publisher is plausible, **not independently proven**. Do not interpret absent new variants as zero opportunities or valid negative evidence.

## Prospective DIY Whale name/flow arms

| Arm | Verified entries | Verified exits | Valid raw marks | Win rate | Average raw mark | Reason |
|---|---:|---:|---:|---:|---:|---|
| `xp_diy_control` | N/A | N/A | N/A | N/A | N/A | No observed new-version rows / activation unverified |
| `xp_diy_name12` | N/A | N/A | N/A | N/A | N/A | Same |
| `xp_diy_organic_flow` | N/A | N/A | N/A | N/A | N/A | Same |
| `xp_diy_name12_flow` | N/A | N/A | N/A | N/A | N/A | Same |
| `xp_diy_raunchy` | N/A | N/A | N/A | N/A | N/A | Same |
| `xp_diy_raunchy_flow` | N/A | N/A | N/A | N/A | N/A | Same |

These are not zero observations of an active experiment. A minimum of 30 valid, post-activation closed exits **per arm** is preliminary only; several weeks of independent, same-period, cost-aware evidence is required before considering a strategy change. Raw marks never prove executable net returns or a raunchy-name edge.

## Windows release provenance

Latest independent Windows-origin `cryptotracker-host-status/status.json` observed **2026-10-24T14:18:39.921977Z** (07:18 Pacific): `git_head=9f8e724e9b7bcb9f25519639ff56c0c09dc19d5b`, matching GitHub main; `source_code_synced=true`, `processes_stable=true`, `state=HOST_PROCESSES_STABLE_SOURCE_ONLY`. Crucially `in_memory_trader_digest_verified=false`, `post_sync_eod_verified=false`, and `broker_trade_health_verified=false`. This receipt is **not** fresh at the 18:05 Pacific review. It is neither proof of loaded novelty variants nor of post-sync EOD. No independently accessible processed-request ledger, active trader digest, repeated Smart Money health and fresh post-sync EOD bundle jointly satisfy the predecessor release gate.

Keep `deploy/requests/P-20261019-02.json` at **PENDING_HOST_VERIFICATION** until `P-20261019-01` processed provenance, loaded component digests, dependent blobs, sustained host health and post-sync EOD are all independently confirmed. No duplicate restart, status promotion or Pushover noise.

## October 24 engineering: safe research-only reporting

A new controlled PR adds two **read-only** diagnostics to the existing EOD publisher, with deterministic tests and CI gates:

1. **`research/paper_liquidation_mtm.py`**: explicit quote-backed point-in-time equity contract for each sleeve. Reads local paper state and an optional *future* timestamped Jupiter read-only liquidation quote snapshot; validates exact state cycle, token/raw amount, quote source, offset-aware timestamp, 120-second freshness, positive finite quote value, no duplicate quotes and sane cash accounting. If absent/stale/mismatched, output **N/A**; never substitute spot marks or completed-trade P&L. If flat, only point-in-time realized paper equity can be shown. **This PR does not implement a quote collector**, so no new MTM measurement is claimed yet. Prior-day comparable snapshots are also absent, so daily/inception full-account return and drawdown stay N/A. Publishes sanitized aggregate `liquidation_mtm_readiness.json/.md` only, not private state or raw quotes.
2. **`research/paper_stop_forensics.py`**: decomposes each simulated STOP into raw price gap below configured stop and additional estimated quote cost, with worst stops, counts and holding duration. Explicitly labels missing quote timestamps and refuses to infer execution or latency. Publishes sanitized `stop_forensics.json/.md` without token mints.

Neither module calls an RPC, changes entries/exits, touches paper state, signs transactions, increases position size or changes live trading. New generated files will only be observed **after separately verified host adoption**; GitHub merge/CI does not establish activation.

**Next gated action:** obtain fresh post-sync Windows proof, then introduce a separately reviewed read-only quote-capture pathway tied to actual paper position state and verified quote timestamps; collect prospective evidence for quote failures, liquidity, stop overruns, and $800/$1,000 capacity *before* any strategy or live-trading proposal.

## Evidence links

- `published/daily/2026-10-23/paper_summary.json`, `quality_audit.json`, `manifest.json`, `raw/paper_trades.csv`, `raw/shadow_trades.csv`.
- `published/daily/2026-10-22/paper_summary.json`, `quality_audit.json`.
- `analysis/daily/2026-10-22/NOVELTY_FLOW_PAPER_SHADOW_PROTOCOL.md`.
- `analysis/daily/2026-10-23/NIGHTLY_THREE_SLEEVE_REVIEW.md`.
- `cryptotracker-host-status/status.json`; issue #7; `deploy/requests/P-20261019-01.json` and `P-20261019-02.json`.

**Research decision:** Protect downside first. A recurring -60% paper stop loss and unverified liquidation economics are incompatible with an assumption of controlled drawdown or reliable +1% daily returns.
