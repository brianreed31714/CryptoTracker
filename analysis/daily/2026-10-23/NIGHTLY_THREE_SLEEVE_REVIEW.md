# CryptoTracker nightly three-sleeve review — 2026-10-23 (Pacific)

**Evidence cutoff:** inspected GitHub at approximately 18:00 Pacific on October 23, 2026. The most recent sanitized daily publication is **2026-10-22**, not October 23. The October 21 publication is missing, so historical continuity is not established. No 2026-10-23 EOD trade performance is asserted.

**Safety:** PAPER ONLY; no executed swaps. All three baselines are unchanged. No order, allocation, stop, live-swap or deployment-request change in this review.

## Latest comparable daily evidence: October 22

| Baseline | Completed paper exits | Daily win rate | Mean paper net/trade | Realized paper P&L | Daily realized-only equity ROI | Inception realized-only equity ROI | Inception realized-only drawdown |
|---|---:|---:|---:|---:|---:|---:|---:|
| Balanced EV | 4 | 50.0% | +3.35% | +$0.200851 | +1.2017% | +12.7684% | 11.9289% |
| Runner Hunter | 7 | 28.6% | -7.45% | -$0.391219 | -2.6421% | -3.8955% | 3.8955% |
| DIY Whale | 14 | 57.1% | +3.43% | +$0.360641 | +2.5672% | -3.9430% | 9.8193% |

**Crucial interpretation:** daily and inception percentages above are **realized-only paper-equity proxies**, NOT full portfolio mark-to-market, NOT real brokerage returns, and NOT proof of a sustained 1% daily edge. The first-observed inception dates differ: Balanced EV September 29, Runner Hunter and DIY Whale October 9. On the 1%-per-calendar-day compounded aspiration, *none* of the three has met its inception target. The desired drawdown threshold <5% is breached by Balanced EV (11.93%) and DIY Whale (9.82%) on the realized-only measure, which can understate open-position risk. The daily figures are small-dollar paper observations (model starting equity approximately $15 each), not tests of $800–$1,000 capacity.

### Changes since October 20 and recent failure modes

October 20: Balanced EV 1 exit, -$0.148246; Runner Hunter 2 exits, -$0.021359; DIY Whale 8 exits, +$0.248948. October 22: Balanced EV 4 exits, +$0.200851; Runner Hunter 7 exits, -$0.391219; DIY Whale 14 exits, +$0.360641. These are separate daily snapshots, not a contiguous 3-day backtest: October 21 is absent.

- **Runner Hunter:** October 22 had 1 exit below -20% estimated net return, 2 exits with estimated execution cost >5%, and 1 negative estimated-cost observation. This is the clearest recent downside concern; prioritize quote/fill-cost integrity and stop overrun before faster entry rules.
- **DIY Whale:** 8 of 14 entries were in RISK_OFF, 5 of 14 exits showed negative estimated execution costs, 1 exit exceeded 5% estimated cost, and two mints had repeated losing exits. This argues for *prospective* regime/organic-flow comparisons, not immediate baseline changes.
- **Balanced EV:** 1 of 4 exits had negative estimated execution cost. Its daily recovery does not erase 11.93% realized-only inception drawdown.
- **All sleeves:** Helius optional-data status was unavailable for all 25 exits (4+7+14). No validated wallet-level organic-demand attribution. Negative estimated costs and >5% quote costs must be investigated rather than treated as trustworthy executable alpha.

## Shadow experiments: observations versus activation

New PR #14 novelty/raunchy/flow arms were merged at commit `aee632ec43b37facb680d239b4a6f4775617fc80` on October 22 Pacific / October 23 UTC. The **latest published October 22 manifest was produced from older source `a7c7d012df40141329fafe649825181d3cfb3504`**. It contains `shadow_trades.csv` but **does not contain** `shadow_experiments.json`, `shadow_experiments.md`, or `improvement_diagnostics.json` despite their current publisher source contract. The legacy shadow CSV header lacks the new name/flow metadata. Therefore **there is no credible post-activation sample yet** for any of the five new variants; don't report their missing rows as zero eligible coins.

| New DIY Whale arm | Confirmed prospective entries | Confirmed exits | Win rate | Avg raw mark | Evidence |
|---|---:|---:|---|---|---|
| `xp_diy_name12` | N/A | N/A | N/A | N/A | Not observed/activation unverified |
| `xp_diy_organic_flow` | N/A | N/A | N/A | N/A | Not observed/activation unverified |
| `xp_diy_name12_flow` | N/A | N/A | N/A | N/A | Not observed/activation unverified |
| `xp_diy_raunchy` | N/A | N/A | N/A | N/A | Not observed/activation unverified |
| `xp_diy_raunchy_flow` | N/A | N/A | N/A | N/A | Not observed/activation unverified |

The `xp_diy_control` arm likewise has **no independently verified new-version comparative report**. Raw price marks would not be net executable returns even if observed. The 30-valid-exit-per-arm threshold is preliminary only.

## Windows host / deployment provenance

At observation **2026-10-23T19:47:03Z**, the independently fetched `cryptotracker-host-status/status.json` reports:

- `git_head=aee632ec43b37facb680d239b4a6f4775617fc80`, equal to GitHub main; `source_code_synced=true`.
- `state=HOST_PROCESSES_STABLE_SOURCE_ONLY`, `processes_stable=true`.
- `post_sync_eod_verified=false`, `in_memory_trader_digest_verified=false`, `broker_trade_health_verified=false`.

Issue #7 includes previous host-local evidence that P-20261019-01 was processed October 19; today's independently available sanitized status **does not** include a new processed-request ledger, loaded trader digest, or post-sync EOD verification. Therefore the staged `P-20261019-02` remains **PENDING_HOST_VERIFICATION**. Do not equate source sync or process existence with active strategy code; do not trigger an additional restart. Recheck host-origin post-sync EOD and exact loaded code/Smart Money feed health before release.

## Next safe engineering improvement — observation integrity

Implement a read-only enhancement to `research/paper_shadow_experiments.py` that reports per-arm **BUY and SELL counts**, valid versus missing/nonfinite raw marks, unmatched/open observed entries, versioned name/flow metadata, distinct closed mints and first/last observed dates. Critically, absent variant rows are **`NO_ROWS_ACTIVATION_UNVERIFIED`**, not a claim of zero opportunities or a zero-return strategy. This closes a material false-confidence gap in the nightly research reporting and preserves existing entry/exit logic. Unit tests should cover missing source, mixed schema, invalid marks, unmatched positions, future-dated records and no-auto-promotion. Validate in all GitHub CI workflows; only merge after green.

## Evidence sources

- `published/daily/2026-10-22/paper_summary.json` and `campaign_summary.json` (dated metrics)
- `published/daily/2026-10-22/quality_audit.json` (simulated execution/data warnings)
- `published/daily/2026-10-22/manifest.json` (source provenance and missing generated artifacts)
- `published/daily/2026-10-20/paper_summary.json` (earlier comparison)
- `cryptotracker-host-status/status.json` (independent host report)
- `deploy/requests/P-20261019-02.json` and issue #7 (release gates)
- `analysis/daily/2026-10-22/NOVELTY_FLOW_PAPER_SHADOW_PROTOCOL.md` (prospective study rules)

**Research decision:** prioritize measurement integrity, quote-based liquidation/open-position MTM, adverse fill/stop realism, and prospective matched-period validation. Do not raise risk or start real-money trading based on these paper results.
