"""Strategy 16: deterministic, non-executable shadow signal consensus.

No trading imports, network, orders, position management or runtime registration.
Input is a complete decision batch for ONE candidate observation, not fills.
"""
from datetime import datetime, timezone
import hashlib
import json

MEMBERS = ('extended_probe', 'regime_filtered', 'whale_luna')
POLICY = dict(name='strategy16_consensus_v1', members=MEMBERS, quorum=2,
              maximum_age_seconds=60, maximum_skew_seconds=10,
              mode='SHADOW_SIGNAL_ONLY', position_execution=False)
POLICY_HASH = hashlib.sha256(json.dumps(POLICY, sort_keys=True).encode()).hexdigest()


def aware(value):
    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError('Timezone-aware timestamp required')
    return value.astimezone(timezone.utc)


def evaluate(rows, *, observation_id, token_address, evaluated_at):
    """Require exactly one fresh vote/member; duplicates and conflicts abstain.

    ACCEPT/REJECT are candidate decisions from an explicit adapter, never BUY
    fills inferred as votes. No mutable state or hidden historical selection.
    """
    result = dict(strategy=POLICY['name'], policy_sha256=POLICY_HASH,
                  observation_id=observation_id, token_address=token_address,
                  action='ABSTAIN', reason='INVALID_EVIDENCE', votes=[],
                  classification='SHADOW_SIGNAL_ONLY_NOT_PERFORMANCE')
    try:
        now = aware(evaluated_at)
        if not observation_id or not token_address or len(rows) != len(MEMBERS):
            return result
        votes = {};times=[]
        for row in rows:
            member=row['model'];ts=aware(row['timestamp'])
            if (member not in MEMBERS or member in votes or
                row['observation_id'] != observation_id or
                row['token_address'] != token_address or
                row['action'] not in ('ACCEPT','REJECT') or
                row.get('data_quality_flags') or not row.get('source_sha256') or
                not 0 <= (now-ts).total_seconds() <= POLICY['maximum_age_seconds']):
                return result
            votes[member]=row['action'];times.append(ts)
        if (max(times)-min(times)).total_seconds()>POLICY['maximum_skew_seconds']:
            return result
        accepted=sorted(k for k,v in votes.items() if v=='ACCEPT')
        result.update(action='SHADOW_CONSENSUS' if len(accepted)>=2 else 'REJECT',
                      reason='QUORUM' if len(accepted)>=2 else 'NO_QUORUM',votes=accepted)
        return result
    except (KeyError,ValueError,TypeError,AttributeError):
        return result


def evaluate_batch(candidates):
    """Suppress repeated observation/token pairs within this supplied batch."""
    seen=set();out=[]
    for candidate in candidates:
        key=(candidate['observation_id'],candidate['token_address'])
        if key in seen:
            continue
        seen.add(key)
        out.append(evaluate(**candidate))
    return out
