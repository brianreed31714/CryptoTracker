# Helius credit review — November 15, 2026

The strongest explanation for the previous million-credit burn is repetitive
Enhanced Transactions wallet-history polling. The implementation fetched each
wallet's latest 20 transactions on every poll and only then deduplicated locally.
An unchanged/empty history still required a provider request. Reducing the result
limit does not reduce its fixed 100-credit request cost.

## Evidence and limits

Reviewed the local main checkout at `9ae1bd6`, historical Git configuration and
code, and local runtime CSVs without making any authenticated Helius requests.
The active-release manifest selects
`auto_trader_with_alerts_v11_10_research_fairness.py`; this review changes that
engine and the configured Smart Money v2.3 observer. Manifest metadata alone
does not prove current process health or deployment.

* Git configuration before the hard-disable commit `cd173d6` had
  `SMART_MONEY_POLL_SECONDS=15`. Monitor versions used the Enhanced Transactions
  address-history endpoint once per Solana wallet per polling cycle.
* The private current wallet configuration contains three enabled Solana wallets
  and one Robinhood wallet. Wallet identities are deliberately omitted here.
* Surviving September 27 feed-health rows show 211 cycles, each attempting checks
  for three Solana wallets. All 211 cycles report Helius errors. The initial
  recorded cycle interval is approximately 120 seconds, so the 15-second tracked
  default is not proof of the actual runtime cadence during the incident.
* Holder-history data starts September 29. Every retained row has zero fetched
  pages and zero holders. It does not establish successful holder calls or their
  spend before exhaustion. The old holder defaults allowed ten tokens per cycle,
  ten pages per token and a ten-minute in-memory cache. Newly rotating tokens,
  expired caches and restarts could multiply that optional workload.
* Current tracked Helius switches are disabled. The newer public-RPC observer
  avoids Helius. Later healthy public-RPC cycles are not historical Helius spend.
* No account billing ledger or per-method provider usage export was available.
  Failed/throttled requests are not proof of billed credits. Other scripts,
  concurrent old processes and other uses of the API key cannot be excluded.

## Workload arithmetic, not a billing reconciliation

For three Solana wallets and continuous successful requests:

| Poll interval | History calls/day | Credits/day | Time to consume 1M |
|---|---:|---:|---:|
| 15 seconds (historical tracked default) | 17,280 | 1,728,000 | 13.9 hours |
| 120 seconds (observed initial log spacing) | 2,160 | 216,000 | 4.63 days |
| One hour (new optional paid history cache) | 72 | 7,200 | 138.9 days |

The two-minute workload alone is consistent with the reported exhaustion in a
few days. The one-hour optional cache cuts that workload by 96.7%; retaining
public RPC instead eliminates Helius history spending by this observer entirely.

Holder scans cost ten credits **per page**, not per token. The old ten-page
maximum could cost 100 credits per token refresh. Ten rotating fresh tokens
every minute could theoretically spend 1.44M/day, while a fixed set of ten
tokens refreshed every ten minutes would spend 144k/day. These are illustrative
upper workloads, not measured usage; the retained holder logs cannot attribute
the previous exhaustion to holder scans.

## Implemented controls

* Shared SQLite reservations: 1,000 credits in any rolling hour, 20,000 in any
  rolling 24 hours and 600,000 in any rolling 31 days. Limits are checked
  atomically across service instances. Every retry reserves again before sending.
* Six-hour persistent holder cache, one candidate per cycle and at most two
  pages per holder refresh (20 credits without retries). Rotating candidates and
  other holder entry points still share the global budget.
* A stable set of ten tokens, each refreshed four times daily at two pages,
  would cost roughly 800 credits/day, excluding failures/retries. Candidate
  turnover can cost more, so this estimate does not replace the budget.
* Persistent cache claims prevent simultaneous duplicate refreshes; empty history
  is cached too. Failure cooldowns survive restart; 402/403 provider halts persist
  across both current services for 24 hours.
* Unknown methods, invalid policy, failed ledger access and budget exhaustion
  prevent paid calls. Budget/caching controls read tracked configuration directly
  so a stale local `.env` cannot inflate spending limits.
* Failed holder refreshes do not become zero-holder historical samples. Cached
  samples retain their observation time. Six-hour baselines cannot masquerade
  as ten-/thirty-minute holder growth, and capped counts remain lower bounds.
* Normal wallet observations and balances remain on public RPC. Optional legacy
  paid wallet history receives an hourly persistent cache and the shared cap.
  Its latest-20 history window can miss activity on busy wallets at that slower
  cadence; use the existing public-RPC observer for regular monitoring.
* Local `python helius_usage.py` reports estimated credits by method and window.
  Usage rows contain method, timestamp and credits; cache keys are hashed. The
  local cache may contain wallet-history responses and must stay private.

The 600k rolling cap leaves 400k of a 1M allowance for headroom and other usage.
It does **not** constrain unrelated API clients, old scripts or separate copies
of the repository. It is not a provider-enforced account cap. Do not delete or
replace the ledger when deploying; a fresh ledger has no knowledge of prior
account spending. The user reports that credits have now been restored.

## Validation and release status

Offline tests cover rolling limits, concurrency, restart persistence, retries,
cache reuse including empty responses, failure cooldown, provider halts, corrupt
ledgers, unpriced methods, stale environment overrides, holder page limits,
observation integrity, and shared Smart Money accounting. Existing public-RPC
and infrastructure contract tests also passed: 75 tests total, with syntax checks
and release preflights for trader, Smart Money and dashboard passing. CI workflows include the new
tests on Linux and Windows; remote CI execution has not been claimed.

This is a prepared local change. Both paid-provider switches remain zero and
no running service has been restarted. Re-enabling the provider is a separate
release/configuration change so it cannot silently reactivate legacy polling.

## Provider references

[Helius credit documentation](https://www.helius.dev/docs/billing/credits),
checked November 15, 2026, lists Enhanced Transactions at 100 credits/request,
DAS including `getTokenAccounts` at 10, standard RPC at 1, and Parsed Events at
10. Parsed Events is the successor to legacy Enhanced Transactions. Migrating
Smart Money to it needs a separate response-schema/classification change; this
patch preserves existing classification and defaults to public RPC.
