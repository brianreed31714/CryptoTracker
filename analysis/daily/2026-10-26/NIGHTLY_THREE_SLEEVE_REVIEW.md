# CryptoTracker nightly three-sleeve review — October 26, 2026 (Pacific)

**Evidence cutoff:** 2026-10-26 ~18:05 PDT. Connected GitHub inspected directly: `published/daily/2026-10-25/` is the newest available sanitized publication; no `published/daily/2026-10-26/manifest.json` at cutoff. October 24 and October 21 daily publications remain absent. **Do not interpret missing reports as no trading or as a host outage.** The October 25 publication is NEW since the prior review, and replaces October 23 as the latest dated evidence.

**Evidence labels:** `PUBLISHED / MODELED` = GitHub-sanitized simulated ledger, **not** real fills or independently attested live Windows process. `HOST OBSERVED` = remote attestation as of its timestamp only. `UNVERIFIED` = no independent loaded-code digest / release provenance. `MISSING` = required publication or snapshot unavailable. **PAPER ONLY; frozen original baselines; no orders, leverage, pumping, strategy promotion, Windows restart or Pushover.**

## Most recent published trading day — October 25 (not October 26)

| Metric | Balanced EV | Runner Hunter | DIY Whale |
|---|---:|---:|---:|
| Completed paper exits / wins | 0 / 0 | 0 / 0 | 1 / 0 |
| Win rate on completed exits | N/A (0 exits) | N/A (0 exits) | 0.0% |
| Mean modeled quote-net per exit | N/A | N/A | **-4.0564%** |
| Oct 25 published-day realized-only paper-equity ROI | **0.0000%** | **0.0000%** | **-0.2357%** |
| Oct 25 realized-only day drawdown | 0.0000% | 0.0000% | 0.2357% |
| Since-inception realized-only ROI | **+11.0452%** | **-5.6216%** | **-14.1411%** |
| Since-inception realized-only drawdown | 11.9289% | 5.8265% | **14.7236%** |
| Full-account daily/inception ROI and drawdown incl. open positions | N/A | N/A | N/A |

The reported zero realized-only return for the two sleeves means **zero completed exits in the October 25 published ledger**, not independently verified uninterrupted monitoring, zero exposure, or no trading on the missing October 24 date. The October 25 `paper_trades.csv` has one DIY Whale BUY/SELL pair: **GATO / GTA6CAT**, entry regime **RISK_OFF**, exit `FAILED_MOMENTUM`, raw price mark **-2.9531%**, estimated quote cost **1.1033 percentage points**, modeled net **-4.0564%** and simulated realized P&L **-$0.030423**. No actual swap or executable fill was observed. Oct 25 quote-cost outliers: 0 negative and 0 >5% for this one exit; no stop exits or fresh stop overruns. Optional Helius was unavailable on the **one** October 25 exit (1/1); 0-exit sleeves have N/A availability for exits, not 0% degraded.

**Publication and campaign reconciliation:** Oct 25 `quality_audit.json` explicitly says `inconclusive_missing_intermediate_publication` and names Oct 23 as the preceding publication. October 24 is missing, so changes in since-inception values since Oct 23 cannot be attributed solely to Oct 25. October 23 campaign-vs-daily discrepancies (Balanced 5 vs 3, DIY 26 vs 22, Runner 10 vs 10) remain unresolved. The October 25 manifest reports the new shadow/diagnostic/MTM/forensics outputs, unlike October 23's older schema. Manifest source commit `b061107ff280aeb488dd3f51a45ebb8bbaf5e422` is **source provenance only**, not a loaded trader digest. The Oct 25 publisher includes one DIY paper exit; do not assume the missing Oct 24 campaign activity was zero.

## Shadow novelty / buying-flow arms: observed rows, **not verified activation**

October 25 `shadow_experiments.json` has `host_runtime_activation_verified=false`. Four arms have **raw row observations**, but no arm has independently verified post-activation observations. The table is **descriptive unverified raw-row evidence**; verified runtime counts and returns for *all six* arms remain **N/A**, not zero.

| Arm | Oct 25 raw observed entries / exits | Valid raw marks | Invalid / unmatched exits | Versioned metadata rows | Raw win / mean mark | Independently verified |
|---|---:|---:|---:|---:|---|---|
| `xp_diy_control` | 1 / 1 | 1 | 0 / 0 | 2 | 0%; -2.9531% | **N/A** |
| `xp_diy_name12` | 1 / 1 | 1 | 0 / 0 | 2 | 0%; -2.9531% | **N/A** |
| `xp_diy_organic_flow` | 1 / 1 | 1 | 0 / 0 | 2 | 0%; -2.9531% | **N/A** |
| `xp_diy_name12_flow` | 1 / 1 | 1 | 0 / 0 | 2 | 0%; -2.9531% | **N/A** |
| `xp_diy_raunchy` | 0 / 0 observed | 0 observed | 0 / 0 observed | 0 | N/A | **N/A** |
| `xp_diy_raunchy_flow` | 0 / 0 observed | 0 observed | 0 / 0 observed | 0 | N/A | **N/A** |

Observed raw rows **do not** establish loaded Windows code, real organic wallet demand, causal uplift, fees, executable net returns, or matched portfolio equity. Identical marks in four arms are one shared token opportunity, not four independent profitable observations. No promotion: >=30 independently valid closed exits per arm is **preliminary only**, followed by time-separated prospective weeks and multiple regimes. Follow `analysis/daily/2026-10-22/NOVELTY_FLOW_PAPER_SHADOW_PROTOCOL.md`.

## Chronological holdout and regime risk

The October 25 `campaign_summary.json` retains a chronological 70/30 split. Original sleeves on **their own** 30% chronological holdout: Balanced EV **49 exits, +0.1900% mean modeled net/trade, profit factor 1.0962**; Runner Hunter **30 exits, -2.7614%, PF 0.4847**; DIY Whale **75 exits, -3.7348%, PF 0.4984**. Balanced's small positive trade average/PF does **not** demonstrate a stable positive portfolio return after costs and drawdown. These are not matched-calendar-window comparisons, and holdout trade-compounded drawdown fields must not be mistaken for realized-only account drawdown or quote-verified MTM. No proven +1%/day edge.

Retrospective DIY regime partition has advanced to **RISK_OFF 159 exits, -$2.812421 modeled P&L** versus **NEUTRAL 81 exits, +$0.566736**. The October 25 loss also entered in RISK_OFF. This is descriptive and confounded by token selection, time, costs and capital; do not edit the frozen baseline. Test the already pre-registered independent neutral-only and risk-off controls prospectively.

The historical unresolved risk events remain: Oct 22 Runner **KIMCHIBULL STOP -66.9973% modeled net vs -7% trigger** (raw -56.4972%, cost 10.5001pp); Oct 23 DIY **YMBCOIN STOP -62.1557% net vs -8%** (raw -50.0653%, cost 12.0904pp; ~58% of that day's DIY loss); Oct 23 Runner **SI276 -18.8733% net vs -7%**. Historic trade rows do not contain independently timestamped liquidation quotes; **latency is not an established cause**. Oct 23 quote-cost anomalies (Runner 1 negative / 2 >5%; DIY 5 negative / 6 >5%) and 35/35 unavailable optional Helius exits remain a concern.

## MTM readiness and deployment verification

Oct 25 `liquidation_mtm_readiness.json`: all three paper sleeves were **flat at the reported point-in-time snapshot** (zero open positions; point-in-time equities ~16.6568, 14.1568, 12.8788 USDC). **No matched prior-day quote/equity snapshots**, no quote snapshot present, `quote_snapshot_cycle_matches=false`, and `full_portfolio_*_return_pct=null`. Flat at one snapshot does **not** establish a complete daily MTM series, so full-account daily/inception ROI and drawdown remain **N/A**. PR #17's Jupiter V2 quote-only collector is merged but default OFF, unscheduled, and **not host-verified active**; never auto-enable it or infer results from source sync.

The newest independently read `cryptotracker-host-status/status.json` is **2026-10-26T16:16:11.226099Z (09:16 PDT)**, with `git_head=5b282bb52b9ff655108b8630954149f4a3b16395`, `source_code_synced=true`, `processes_stable=true`, and `state=HOST_PROCESSES_STABLE_SOURCE_ONLY`. **In-memory trader digest, post-sync EOD and broker trade health all false.** This is a **newer** source/process observation than October 24, but is **not** proof of loaded version, repeated process/Smart Money health, complete publication, or deployment success. The current GitHub `main` subsequently advanced with CI-green PR #18, so this host source receipt also predates the newest main commit.

`deploy/requests/P-20261019-02.json` remains **PENDING_HOST_VERIFICATION**. Do not advance until predecessor `P-20261019-01` processed ledger, exact loaded trader digest and dependent blob identities, repeated supervisor/Smart Money health, and a fresh post-sync EOD independently agree. No duplicate restarts.

## Engineering / CI integrity — October 26

The earlier PR #17 infrastructure-contract failure reported an **unmapped Python file** on a PR run. The corrective **PR #18** (`fix/quote-capture-registry-ownership`) registers `test_paper_jupiter_quote_capture.py` under `research_lab` ownership without weakening the fail-closed registry check. Independently inspected GitHub Actions for its exact head `e1f12a9ccc2f22135f64dd62bb3dfeca425bf11c`: **all three workflows completed successfully**, including Linux + Windows infrastructure jobs, Windows process safety, and both Python validation jobs. **PR #18 merged as `da8b9f38fea3a0bf8b3de6412e6310df6e214b90`**. Historical failed PR #17 runs remain historical failures; this fix does not retroactively change their result. Merge/green CI are **not** Windows activation.

**Four nonnegotiable controls:** (1) all required CI green before merging; (2) independently verify loaded code digest after deployment; (3) monitored trading process health with controlled recovery; (4) verified / modeled / unverified / missing distinctions in every nightly report.

**Next actions:** restore continuous sanitized daily publication and explain October 24 gap; independently verify host loaded-code and predecessor release ledger; inspect quote capture provenance without enabling it; collect valid matched-day quote/equity observations only through separately reviewed paper-only activation; evaluate stop-overrun attribution and hypothetical $800–$1,000 liquidity/slippage with timestamped read-only evidence. No changes to execution, risk, or frozen baselines.

**Decision:** No real-money activation or size increase. Prioritize repeatable risk-adjusted returns and controlled drawdown; +1% daily remains aspirational only.
