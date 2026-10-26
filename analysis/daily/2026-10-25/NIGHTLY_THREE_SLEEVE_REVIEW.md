# CryptoTracker nightly review — 2026-10-25 (Pacific)

**Evidence cutoff:** October 25, 2026, ~17:59–18:00 Pacific. Connected GitHub `main` is `117646f41305e3fa68aeea82daa8b2cfe2cfd047` (PR #16, merged Oct 24). **Latest published daily trading evidence remains October 23**. No `published/daily/2026-10-24/` or `2026-10-25/` in the observed main tree; October 21 is also missing. Missing reports are not evidence of zero trading or proof of an outage. The latest observed host receipt is from Oct 24 07:18 Pacific, not fresh.

**Safety decision:** PAPER ONLY. Frozen original Balanced EV / Runner Hunter / DIY Whale entries, exits, stops and sizing. No order routing, execution changes, risk increase, Pushover, restart, deployment promotion or real-money activation. **No new October 24 or 25 return can be calculated.** Do not copy October 23 numbers into an October 25 performance claim.

## Most recent *verified publication* — Oct 23 (not Oct 25)

| Sleeve | Oct 23 exits | Oct 23 win rate | Oct 23 mean modeled quote-net/trade | Oct 23 realized-only paper-equity daily ROI | Since-inception realized-only ROI | Inception realized-only drawdown | Oct 23 simulated P&L |
|---|---:|---:|---:|---:|---:|---:|---:|
| Balanced EV | 3 | 0/3 = 0.0% | -1.9910% | -0.5352% | +11.0106% | 11.9289% | -$0.089593 |
| Runner Hunter | 10 | 3/10 = 30.0% | -3.4478% | -1.7938% | -5.6194% | 5.8265% | -$0.258587 |
| DIY Whale | 22 | 10/22 = 45.5% | -4.862% | -5.6195% | -10.1757% | 10.7851% | -$0.802229 |

These figures are **realized-only** simulated account equity and *modeled* Jupiter quote-net marks, not actual fills. Full portfolio daily/inception returns and drawdowns including open positions remain **N/A**. The last campaign's 70/30 chronological holdout still showed no original sleeve passing the stable-positive gate. Different inception dates prevent interpreting cross-sleeve inception ROI as a matched causal comparison. +1% daily remains an aspirational benchmark, not a demonstrated edge.

### Risk and integrity follow-up (no new causal proof)

- **Oct 22 Runner KIMCHIBULL STOP:** -66.9973% modeled quote-net vs -7% stop; -56.4972% raw price move and 10.5001 percentage points estimated cost.
- **Oct 23 DIY YMBCOIN STOP:** -62.1557% modeled quote-net vs -8% stop; -50.0653% raw move, 12.0904pp estimated cost; -$0.466168 paper P&L (~58% of DIY daily loss). **Runner SI276 STOP** -18.8733% net vs -7% stop.
- No timestamped liquidation quote exists in these historical trade rows, so quote age, routing/price-gap cause, and actual stop fill cannot be established. Holding time is not quote age.
- Oct 23 simulated quote quality: Balanced 0 negative estimated cost / 0 >5% cost; Runner 1 negative / 2 of 10 >5%; DIY 5 negative / 6 of 22 >5%. **Optional Helius unavailable on all 35 focused exits.** A negative estimated cost is a mark/quote inconsistency, not a guaranteed fill improvement.
- DIY historical RISK_OFF 147/226 exits, -$2.343164 modeled P&L vs NEUTRAL 74 exits, +$0.763983: confounded retrospective partition; test the already-registered neutral-only / strict-risk-off shadows prospectively, not baseline rewrites.
- Oct 23 quality audit campaign-vs-daily count deltas Balanced 5 vs 3, DIY 26 vs 22, Runner 10 vs 10; investigate reconciliation before trusting aggregate campaign claims. Oct 23 publication source `bcb7118` lacked shadow experiment and improvement diagnostic artifacts, and raw shadow CSV used legacy fields despite newer publisher source; loaded runtime code is unverified.

### Prospective novelty and flow variants — NOT activated/verified

| Arm | Verified entries | Verified exits | Valid raw marks | Missing/invalid | Win rate | Mean raw mark | Versioned metadata |
|---|---:|---:|---:|---:|---:|---:|---|
| `xp_diy_control` | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `xp_diy_name12` | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `xp_diy_organic_flow` | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `xp_diy_name12_flow` | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `xp_diy_raunchy` | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `xp_diy_raunchy_flow` | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

No independently verified post-activation entry/exit rows. N/A is not zero. Keep name, raunchy and buying-flow hypotheses preregistered under `analysis/daily/2026-10-22/NOVELTY_FLOW_PAPER_SHADOW_PROTOCOL.md`. At least 30 valid completed exits **per arm** for preliminary review only, across additional market regimes and time-ordered out-of-sample weeks. Raw shadow marks cannot establish executable net P&L or a causal name effect.

### Windows and deployment gate

The latest `cryptotracker-host-status/status.json` is **2026-10-24T14:18:39.921977Z** (Oct 24 07:18 Pacific), `git_head=9f8e724e9b7bcb9f25519639ff56c0c09dc19d5b`, `state=HOST_PROCESSES_STABLE_SOURCE_ONLY`, source synced and processes stable **at that timestamp**. This predates current `main=117646f` and is now stale. `in_memory_trader_digest_verified=false`, `post_sync_eod_verified=false`, `broker_trade_health_verified=false`. No independent proof that PR #16 or the new novelty arms are loaded, or that prior request `P-20261019-01` processed and produced post-sync EOD. Keep `P-20261019-02` **PENDING_HOST_VERIFICATION**. GitHub merges and process observation alone do not satisfy release provenance; do not initiate another restart.

### October 25 engineering: separately gated, opt-in quote-only collector

New PR (this branch) implements `research/paper_jupiter_quote_capture.py` with offline deterministic tests. It **does not auto-run or change the trader**. A deliberate local invocation must supply `--collect` AND `PAPER_QUOTE_CAPTURE_ENABLED=1`, and `LIVE_TRADING` must be false. It uses **only HTTPS GET** Jupiter Swap V2 `/order` **without a taker wallet** (Jupiter documents this as quote-only; no transaction); it never imports a signer or submits `/execute`, and rejects any returned transaction. A fixed USDC mint, verified input amount and optional echoed mints, positive integer output, explicit UTC receipt timestamp, 120-second freshness, strict paper state provenance, exact pre/post state-byte identity and atomic private local output make it fail closed on bad/missing/stale/future/changed quotes. The existing `research/paper_liquidation_mtm.py` can consume the snapshot; **full-account daily/inception returns and drawdown remain N/A** until real local collection, synchronized prior-day snapshots and independently verified Windows activation exist. No raw quote, mint, token amount, wallet or API key is published to GitHub.

**Provider reference:** Jupiter Swap API V2 quote-only GET /order, no taker: https://developers.jup.ag/docs/swap/order-and-execute . Quote values are estimates, never guaranteed fills. Future capacity tests at $800–$1,000 must use separately captured depth/price-impact quotes and actual simulated inventory, not a scale-up from $15 paper-equity marks.

### Next verification gates

1. All three GitHub Actions CI workflows must pass for this PR. Merge establishes source availability only; no activation claim.
2. Collect fresh Windows host provenance, processed-request ledger, exact trader digest, repeated supervisor and Smart Money heartbeat, fresh post-sync EOD and dependency hashes before any pending deployment promotion.
3. Verify first valid quote snapshot against same-cycle state, then matched day-boundary snapshots and open-position MTM, quote failures and stop overrun. Keep all returns **N/A** until required evidence exists.

**Decision:** Downside and measurement integrity first; do not chase +1% daily or switch to real money.
