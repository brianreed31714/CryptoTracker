# Strategy 16: fixed consensus shadow experiment

Issue #51; source baseline ec9c3e3383bb20e338f32104c1c46096a2b926b4.
Owner: Codex, operations session 01a1e1fa-b018-7b42-9185-6e38d8955a67.

The source implementation now includes candidate collection, persistent paper
positions, quote-based accounting and report snapshots. It is disabled by
default. No activation manifest is committed or installed, no Windows process
is restarted, and no existing strategy, risk or Helius setting is changed.
Source tests do not establish a running sixteenth strategy or profitability.

Frozen research cohort: extended_probe, regime_filtered, whale_luna. The former
had positive returns in two available completed-week comparisons; the latter
two had comparatively encouraging seed/drawdown observations. These are
descriptive selection hypotheses, not evidence of the best independent signals.
Selection used historical observations and any replay is in-sample research.
All future changes require a new version/policy hash and fresh evaluation.

Two of three ACCEPT votes on the same token and observation produce one
SHADOW_CONSENSUS signal. All three explicit votes must be present, fresh (60s),
timezone-aware, within 10s of one another, source-referenced and quality-clean.
Duplicate, conflicting, missing, future or stale votes cause ABSTAIN. Batch
groups are checked in full before emitting consensus: contradictory duplicate
envelopes abstain regardless of their order, while identical reordered votes
deduplicate. Malformed envelopes emit explicit abstentions. The policy mapping
and member tuple are immutable and its digest covers the declared quorum;
source digests require 64 lowercase hexadecimal characters (format validation
only, not source authentication).
The pure evaluator deduplicates within a batch. The paper study additionally
commits complete cycles, decisions, positions and snapshots transactionally in
SQLite, with persistent cycle/observation identities across restarts and
concurrent ingestion. Hash fields are provenance
references, not cryptographic authentication of the source.

The existing model_decisions CSV has naive timestamps and lacks a shared
candidate observation ID. It cannot be silently adapted or replayed as validated
consensus. A prospective adapter must capture candidate-level decisions from
all members before execution, retain immutable source/config identities, and
provide matching candidate IDs and authenticated UTC timestamps. BUY fill logs
are not candidate votes. The opt-in lab adapter captures all three component
votes and the strict_baseline control before base-model entries; it records
candidate features, gate reasons, UTC capture/evaluation timestamps and frozen
source/config identities. No runtime activation is installed by this PR.

Source acceptance: deterministic quorum, fail-closed evidence checks, persistent
duplicate suppression, one virtual position/budget per comparison book, fees,
slippage, explicit exits, unpriced/failed-route handling, dated marked snapshots,
read-only period reporting, end-to-end standard-library tests and CI on Linux
and Windows. Rollback before activation: revert source PR/discard branch.

The paper study compares the ensemble, its three individual signals,
strict_baseline and cash on a common candidate stream. All active books use
the same explicit study size/exit assumptions. These are controlled signal
comparisons, not replays of the existing models' different sizing/exit ledgers.
Candidates share a declared priority: descending recorded quant score, then
token identity as a deterministic tie-break; each book still needs its own vote.
The ensemble has one shared virtual position and budget, never three added
exposures. The frozen cohort is retained; the later full-history study weakens
extended_probe as a default member but does not silently retune this experiment.

## Accounting and failures

`research/strategy16_paper.py` has no network client, trader import, signer,
transaction submission or broker/order API. A caller supplies sized quotes.
`StudyPolicy` requires explicit seed, notional, per-side USD fee, additional
slippage basis points, net stop/take-profit percentages and maximum holding
seconds. These are recorded research assumptions, not measured/calibrated
execution costs and not modifications to production risk settings.

A buy deducts notional plus the entry fee once and records raw token units.
A liquidation quote values those exact units, less additional slippage and
the exit fee. A close credits net proceeds and realizes proceeds minus the
recorded entry cost. No partial-sale aggregation or added component returns
are involved. Stops, take profit and maximum holding time are simulated exits
at available quotes, never guaranteed execution prices.

Failed/stale/future/wrong-token/wrong-direction/wrong-size quotes cannot create
a simulated fill. A missing exit route leaves the position open and marked
equity/return null. A buy quote does not establish a same-cycle exit value.
Drawdown retains its observed priced maximum and explicitly flags incomplete
coverage; it cannot be read as the full risk of unpriced positions. The report
also records realized balances, wins/losses, expectancy, profit factor,
token contribution/concentration, sampled exposure and skipped/abstained
opportunities. Identical retries do not request new quotes or repeat fills.
Conflicting committed cycles halt the study; they are never overwritten.

Code, producer configuration or study-policy changes require a new reviewed
study identity/database. Existing history is not reset or silently migrated.
An unrelated/incomplete database is rejected. Transactions roll back all
books and journals together on failure. Study data belongs under private
`data/strategy16/`, already excluded from Git.

## Source wiring and separate activation

The existing trader's paper-lab call now checks for
`data/strategy16/activation.json`. Without it, the observer is `None`: no study
database, extra quotes, or changes to the original 15 books. An invalid
activation/observer emits an explicit warning and leaves their normal path
available. A valid activation must specify:

- `mode`: exactly `PAPER_ONLY`; effective `LIVE_TRADING` must be false.
- `release`: exactly the identity returned by
  `research.strategy16_runtime.release_identity(ROOT)`, binding the study,
  adapter, lab and producer source bytes.
- `policy`: the explicit `StudyPolicy` fields described above.

Creating that local manifest is a separately authorized release/activation
action. This PR does not create it, merge itself, deploy or restart anything.
After authorized activation the adapter uses the existing Jupiter GET helper
without a taker. It validates both mint addresses and raw input/output amounts,
uses a conservative output threshold when supplied, and applies explicit
additional study cost assumptions. It never calls signing or execution code.
See [Jupiter's order documentation](https://github.com/jup-ag/docs/blob/main/docs/swap/order-and-execute.mdx)
for quote-only requests without a taker. No live connectivity is exercised in
these tests; provider output remains indicative, not confirmed fills.

Entry quote acquisition is bounded by the immutable study quote budget and
cached per token in a cycle. Exit quotes are cached by token/raw position size.
The adapter starts no further requests after its configured collection budget
(five seconds by default); the paper-only callback uses a three-second request
timeout. A request already in progress must return or time out. Existing callers
retain their previous 25-second default. Collection is synchronous, so its actual
latency and coverage must be checked during the authorized paper activation.
No Helius/token-decimal RPC is needed. Freshness is evaluated after acquisition;
slow acquisition can cause explicit abstention rather than using old votes.
The dedicated SQLite database is authoritative; `latest.json` is an atomic
private report view for EOD consumers. It is not a runtime activation attestation.

## Private reporting

`PaperStudy(..., read_only=True).report()` and `.period(start_utc, end_utc)`
read existing state without changing the database. Period comparisons select
the latest observed endpoints at or before each aware UTC cutoff and retain
their timestamps. Missing, unpriced or identical endpoints yield null returns;
no interpolation or invented zero is used. There are no external cash flows
in these dedicated simulated books. Report-only mode never creates a missing DB.

The offline JSONL CLI can ingest prospective captured cycles into an isolated
study and export JSON, or read an existing database without ingestion:

```text
python -m research.strategy16_paper --database PRIVATE/study.sqlite3 --policy PRIVATE/policy.json --cycles PRIVATE/cycles.jsonl --report PRIVATE/latest.json
python -m research.strategy16_paper --database PRIVATE/study.sqlite3 --policy PRIVATE/policy.json --report PRIVATE/eod.json --period-start START_UTC --period-end END_UTC
```

Direct JSONL inputs use the strict contract emitted by `capture_cycle`; votes
are explicit booleans, not BUY events. Each normalized sized quote contains
`status=OK`, token identity, `side=BUY|SELL`, `input_amount`, `output_amount`,
an aware `timestamp`, lowercase SHA-256 provenance and empty quality flags.
Inputs/outputs are USD-to-raw-units for BUY and raw-units-to-USD for SELL.
Never convert old naive decision CSVs into purported prospective performance.

After activation, verify new capture timestamps, source/policy identity, quote
coverage, simulated BUY/SELL records and the dedicated marked snapshots before
including Strategy16's percentages in EOD reports. Until then its operational
status remains NOT RUNNING; synthetic test trades are not performance history.
Keep its figures separate from the original 15 balances and never sum strategy
percentages into portfolio ROI. Real-money execution is not authorized.

Post-activation rollback, when separately authorized: remove the paper opt-in
and revert the release through the controlled procedure; preserve study DB,
journal, snapshots and existing paper states for audit. The original 15 books
do not share the new study's budget, positions or files.
