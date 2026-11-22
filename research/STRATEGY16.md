# Strategy 16: fixed consensus shadow experiment

Issue #51; source baseline ec9c3e3383bb20e338f32104c1c46096a2b926b4.
Owner: Codex, operations session 01a1e1fa-b018-7b42-9185-6e38d8955a67.

This first stage is a non-executable signal evaluator, not a running sixteenth
trader or a claim of profitability. No production strategy, risk parameter,
process, runtime registry or Helius configuration is changed.

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
Batch
deduplication is within a single invocation only; persistent exactly-once
collection is a future adapter responsibility. Hash fields are provenance
references, not cryptographic authentication of the source.

The existing model_decisions CSV has naive timestamps and lacks a shared
candidate observation ID. It cannot be silently adapted or replayed as validated
consensus. A prospective adapter must capture candidate-level decisions from
all members before execution, retain immutable source/config identities, and
provide matching candidate IDs and authenticated UTC timestamps. BUY fill logs
are not candidate votes. No adapter or runtime is installed by this PR.

Acceptance for this stage: deterministic quorum, fail-closed evidence checks,
duplicate suppression, no input mutation, isolated standard-library tests and
CI. Rollback: revert this source PR/discard branch; no runtime rollback needed.

Next stage, separately reviewed: matched-opportunity shadow collection with
one shared virtual position and budget (never three added exposures), explicit
exits, calibrated fees/slippage/liquidity/failure simulation and full marked
equity. Compare ensemble, each component and strict_baseline on the same
prospective opportunities: net return, drawdown, exposure, expectancy, profit
factor, concentration, missed opportunities and coverage. Record abstentions.
Until priced accounting exists, report Strategy 16 as NOT RUNNING / UNPRICED;
do not fabricate a daily percentage or add it to the existing 15 balances.
Real-money execution is not authorized.
