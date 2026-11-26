"""Prospective quote-driven paper study. Standard library only; no order API.

SQLite commits an entire cycle, its decisions and all books atomically. Quotes
are supplied by the caller, never fetched or executed by this module.
"""
from __future__ import annotations

import argparse
import copy
from contextlib import contextmanager, nullcontext
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import sqlite3
from time import monotonic

from research.strategy16_shadow import MEMBERS, POLICY_HASH, aware, evaluate_batch

BOOKS = ('strategy16', *MEMBERS, 'strict_baseline', 'cash')
SIGNALS = (*MEMBERS, 'strict_baseline')
IMPLEMENTATION_SHA256 = hashlib.sha256(
    Path(__file__).read_bytes() + Path(__file__).with_name('strategy16_shadow.py').read_bytes()
).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def number(value):
    if isinstance(value, bool):
        raise ValueError('Boolean is not an amount')
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError('Invalid amount') from None
    if not result.is_finite():
        raise ValueError('Non-finite amount')
    return result


def hash_value(value):
    if not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
        raise ValueError('Invalid SHA256 identity')
    return value


def candidate_order(token, evidence):
    """One predeclared common quant priority, with deterministic mint tie-break."""
    quant=number(evidence.get(token,{}).get('features',{}).get('quant',0))
    return -quant,token


@dataclass(frozen=True)
class StudyPolicy:
    """Explicit research assumptions, never production trading parameters."""
    seed_usd: str
    notional_usd: str
    fee_per_side_usd: str
    slippage_bps: str
    stop_loss_pct: str
    take_profit_pct: str
    max_hold_seconds: int
    quote_max_age_seconds: int = 30
    max_entry_quotes_per_cycle: int = 5
    collection_max_seconds: int = 5
    version: str = 'strategy16-paper-v1'

    def __post_init__(self):
        for name in ('seed_usd', 'notional_usd', 'fee_per_side_usd', 'slippage_bps', 'stop_loss_pct', 'take_profit_pct'):
            value = number(getattr(self, name))
            object.__setattr__(self, name, str(value))
            if value < 0:
                raise ValueError('Negative policy amount')
        if not (number(self.seed_usd) > 0 and number(self.notional_usd) > 0):
            raise ValueError('Positive seed and notional required')
        if number(self.notional_usd) + number(self.fee_per_side_usd) > number(self.seed_usd):
            raise ValueError('Notional plus entry fee exceeds seed')
        if number(self.slippage_bps) >= 10000 or not 0 < number(self.stop_loss_pct) <= 100 or number(self.take_profit_pct) <= 0:
            raise ValueError('Invalid research thresholds')
        if any(type(x) is not int or x <= 0 for x in (self.max_hold_seconds, self.quote_max_age_seconds, self.max_entry_quotes_per_cycle, self.collection_max_seconds)) or not self.version:
            raise ValueError('Invalid research identity/interval')


def quote(value, *, token, side, amount, now, policy):
    """Conservative sized quote: gross output minus explicit extra slippage/fee.

    amount is USD for BUY and integer raw tokens for SELL. Quote token identity,
    direction, notional and timestamp must match; mark prices are not quotes.
    """
    if not isinstance(value, dict) or value.get('status') != 'OK' or value.get('data_quality_flags'):
        raise ValueError('Failed or dirty quote')
    hash_value(value.get('source_sha256'))
    if value.get('token_address') != token or value.get('side') != side:
        raise ValueError('Quote identity/direction mismatch')
    if not 0 <= (now - aware(value['timestamp'])).total_seconds() <= policy.quote_max_age_seconds:
        raise ValueError('Stale/future quote')
    if number(value['input_amount']) != number(amount):
        raise ValueError('Quote size mismatch')
    output = number(value['output_amount'])
    if output <= 0:
        raise ValueError('Non-positive quote output')
    adjusted = output * (1 - number(policy.slippage_bps) / 10000)
    if side == 'BUY':
        units = int(adjusted)
        if units <= 0:
            raise ValueError('Insufficient raw token output')
        return units
    net = adjusted - number(policy.fee_per_side_usd)
    if net < 0:
        raise ValueError('Exit fee exceeds proceeds')
    return net


def capture_cycle(*, cycle_id, observed_at, candidates, source_sha256, configuration_sha256, data_quality_flags=''):
    """Normalize explicit prospective safety decisions, never infer votes from fills.

    Caller captures these before entries. A missing/non-boolean component vote
    becomes invalid evidence rather than an inferred REJECT/ACCEPT.
    """
    stamp = aware(observed_at).isoformat()
    hash_value(source_sha256); hash_value(configuration_sha256)
    if not isinstance(cycle_id, str) or not cycle_id:
        raise ValueError('Cycle identity required')
    observations = []
    evidence = {}
    for candidate in candidates:
        token = candidate['token_address']
        if not isinstance(token, str) or not token:
            raise ValueError('Token identity required')
        observation_id = digest([cycle_id, token, source_sha256, configuration_sha256])
        votes = candidate.get('votes', {})
        rows = [dict(model=m, timestamp=stamp, observation_id=observation_id,
                     token_address=token, action=('ACCEPT' if votes[m] else 'REJECT'),
                     source_sha256=source_sha256, data_quality_flags=data_quality_flags)
                for m in SIGNALS if type(votes.get(m)) is bool]
        observations.append(dict(observation_id=observation_id, token_address=token,
                                 evaluated_at=stamp, rows=rows))
        context={'features':candidate.get('features',{}), 'reasons':candidate.get('reasons',{})}
        if token in evidence and evidence[token] != context:
            raise ValueError('Conflicting candidate context')
        evidence[token]=context
    observations=sorted({canonical(o):o for o in observations}.values(),key=canonical)
    return dict(cycle_id=cycle_id, observed_at=stamp, source_sha256=source_sha256,
                configuration_sha256=configuration_sha256, observations=observations,
                candidate_evidence=evidence, entry_quotes={}, liquidation_quotes={})


class PaperStudy:
    def __init__(self, path, policy, *, read_only=False):
        self.path = str(path)
        self.read_only=read_only
        self.policy = policy
        self.identity = digest({'policy': asdict(policy), 'consensus': POLICY_HASH,
                                'implementation': IMPLEMENTATION_SHA256})
        with self.connect() as db:
            if read_only:
                old=db.execute("SELECT value FROM metadata WHERE key='identity'").fetchone()
                if not old or old[0]!=self.identity:
                    raise ValueError('Read-only study identity mismatch')
                return
            tables={x[0] for x in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
            expected={'metadata','books','cycles','events','observations','book_snapshots'}
            if tables and tables!=expected:
                raise ValueError('Not a Strategy16 study database; existing tables left untouched')
            db.executescript('''
                CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS books (name TEXT PRIMARY KEY, state TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS cycles (id TEXT PRIMARY KEY, sha TEXT NOT NULL, stamp TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, cycle TEXT NOT NULL, book TEXT NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS observations (id TEXT NOT NULL, token TEXT NOT NULL, sha TEXT NOT NULL, PRIMARY KEY(id,token));
                CREATE TABLE IF NOT EXISTS book_snapshots (cycle TEXT NOT NULL, book TEXT NOT NULL, stamp TEXT NOT NULL, state TEXT NOT NULL, PRIMARY KEY(cycle,book));
            ''')
            db.execute('BEGIN IMMEDIATE')
            old = db.execute("SELECT value FROM metadata WHERE key='identity'").fetchone()
            if old and old[0] != self.identity:
                raise ValueError('Study policy changed; use a new study database')
            existing={r[0] for r in db.execute('SELECT name FROM books')}
            if (old and existing!=set(BOOKS)) or (not old and existing):
                raise ValueError('Incomplete/corrupt study books; do not reset existing history')
            db.execute("INSERT OR IGNORE INTO metadata VALUES ('identity',?)", (self.identity,))
            for name in BOOKS:
                state = dict(cash=policy.seed_usd, realized_pnl='0', position=None,
                             marked_equity=policy.seed_usd, peak=policy.seed_usd,
                             max_drawdown_pct='0', completed=0, wins=0, losses=0,
                             priced_cycles=0, unpriced_cycles=0, entries=0,
                             occupied_skips=0, quote_failures=0, accepting_signals=0,
                             pnl_by_token={}, entry_notional='0', gross_wins='0',
                             gross_losses='0', exposed_cycles=0, gross_wins_by_token={},
                             rejected_signals=0, abstentions=0, budget_skips=0)
                db.execute('INSERT OR IGNORE INTO books VALUES (?,?)', (name, canonical(state)))

    @contextmanager
    def connect(self):
        db=sqlite3.connect(Path(self.path).resolve().as_uri()+'?mode=ro',uri=True,timeout=30) if self.read_only else sqlite3.connect(self.path,timeout=30)
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def event(db, cycle, book, kind, **payload):
        db.execute('INSERT INTO events(cycle,book,kind,payload) VALUES (?,?,?,?)',
                   (cycle, book, kind, canonical(payload)))

    def positions(self):
        with self.connect() as db:
            return {name: json.loads(state)['position'] for name, state in db.execute('SELECT name,state FROM books')}

    def process(self, cycle, *, _connection=None):
        if self.read_only:
            raise ValueError('Cannot process into a read-only study')
        cycle = copy.deepcopy(cycle)
        for observation in cycle['observations']:
            observation['rows'] = sorted(observation['rows'], key=canonical)
        # Reordered or repeated identical envelopes are the same input.
        cycle['observations'] = sorted({canonical(o):o for o in cycle['observations']}.values(), key=canonical)
        fingerprint = digest(cycle)
        now = aware(cycle['observed_at'])
        hash_value(cycle['source_sha256']); hash_value(cycle['configuration_sha256'])
        if not isinstance(cycle['cycle_id'], str) or not cycle['cycle_id']:
            raise ValueError('Invalid cycle id')
        envelopes = []
        ballots = {}
        for o in cycle['observations']:
            # The emitter's time is part of the immutable cycle; no look-ahead votes.
            if aware(o['evaluated_at']) != now:
                raise ValueError('Observation time differs from cycle')
            envelopes.append(dict(o, rows=[r for r in o['rows'] if r.get('model') != 'strict_baseline']))
            key = (o['observation_id'], o['token_address'])
            ballots.setdefault(key, []).append(o)
        decisions = evaluate_batch(envelopes)
        with (nullcontext(_connection) if _connection is not None else self.connect()) as db:
            if _connection is None:
                db.execute('BEGIN IMMEDIATE')
            fault = db.execute("SELECT value FROM metadata WHERE key='fault'").fetchone()
            if fault:
                raise ValueError('Study halted by conflicting prior evidence; start a reviewed new study')
            prior = db.execute('SELECT sha FROM cycles WHERE id=?', (cycle['cycle_id'],)).fetchone()
            if prior:
                if prior[0] == fingerprint:
                    return self._report(db, duplicate=True)
                db.execute("INSERT OR REPLACE INTO metadata VALUES ('fault','CONFLICTING_CYCLE')")
                db.commit()
                raise ValueError('Conflicting repeated cycle; study halted')
            last = db.execute("SELECT value FROM metadata WHERE key='last_stamp'").fetchone()
            if last and now <= aware(last[0]):
                raise ValueError('Non-increasing cycle timestamp')
            identity = digest([cycle['source_sha256'], cycle['configuration_sha256']])
            old = db.execute("SELECT value FROM metadata WHERE key='source_identity'").fetchone()
            if old and old[0] != identity:
                raise ValueError('Source/config identity changed; start a new study')
            for o in cycle['observations']:
                old_observation=db.execute('SELECT sha FROM observations WHERE id=? AND token=?',
                                           (o['observation_id'],o['token_address'])).fetchone()
                if old_observation:
                    raise ValueError('Observation identity reused in a different cycle')
            for key, group in ballots.items():
                db.execute('INSERT INTO observations VALUES (?,?,?)', (*key,digest(group)))
            db.execute("INSERT OR IGNORE INTO metadata VALUES ('source_identity',?)", (identity,))
            db.execute('INSERT INTO cycles VALUES (?,?,?,?)',
                       (cycle['cycle_id'], fingerprint, now.isoformat(), canonical(cycle)))
            states = {n:json.loads(s) for n,s in db.execute('SELECT name,state FROM books')}
            exited = set()
            for name, state in states.items():
                pos = state['position']
                if not pos:
                    continue
                state['exposed_cycles'] += 1
                key = f"{pos['token_address']}|{pos['units']}"
                try:
                    raw_quote=cycle['liquidation_quotes'].get(key)
                    if not isinstance(raw_quote,dict) or aware(raw_quote['timestamp'])<aware(pos['entered_at']):
                        raise ValueError('Liquidation quote predates position')
                    proceeds = quote(cycle['liquidation_quotes'].get(key), token=pos['token_address'],
                                     side='SELL', amount=pos['units'], now=now, policy=self.policy)
                except (KeyError, TypeError, ValueError):
                    state['marked_equity'] = None
                    state['quote_failures'] += 1
                    self.event(db, cycle['cycle_id'], name, 'UNPRICED_POSITION', token=pos['token_address'])
                    continue
                state['marked_equity'] = str(number(state['cash']) + proceeds)
                change = 100 * (proceeds / number(pos['cost']) - 1)
                age = (now - aware(pos['entered_at'])).total_seconds()
                reason = ('STOP' if change <= -number(self.policy.stop_loss_pct) else
                          'TAKE_PROFIT' if change >= number(self.policy.take_profit_pct) else
                          'MAX_HOLD' if age >= self.policy.max_hold_seconds else None)
                if reason:
                    pnl = proceeds - number(pos['cost'])
                    state['cash'] = str(number(state['cash']) + proceeds)
                    state['realized_pnl'] = str(number(state['realized_pnl']) + pnl)
                    state['gross_wins'] = str(number(state['gross_wins']) + max(pnl, 0))
                    state['gross_losses'] = str(number(state['gross_losses']) + max(-pnl, 0))
                    token=pos['token_address']
                    state['gross_wins_by_token'][token]=str(number(state['gross_wins_by_token'].get(token,'0'))+max(pnl,0))
                    state['pnl_by_token'][pos['token_address']] = str(number(state['pnl_by_token'].get(pos['token_address'], '0')) + pnl)
                    state['completed'] += 1
                    state['wins'] += int(pnl > 0); state['losses'] += int(pnl < 0)
                    state['position'] = None
                    exited.add(name)
                    self.event(db, cycle['cycle_id'], name, 'SELL', reason=reason,
                               token=pos['token_address'], units=pos['units'], proceeds_usd=str(proceeds), pnl_usd=str(pnl))
            for decision in sorted(decisions, key=lambda d:(candidate_order(d.get('token_address',''),cycle.get('candidate_evidence',{})),d.get('observation_id',''))):
                key = (decision.get('observation_id'), decision.get('token_address'))
                all_ballots = ballots.get(key, [])
                valid = decision['action'] != 'ABSTAIN' and len(all_ballots) == 1
                votes = {r['model']:r['action'] for r in all_ballots[0]['rows']} if valid else {}
                # Baseline uses the same causal evidence requirements as a member.
                baseline = [r for r in all_ballots[0]['rows'] if r.get('model')=='strict_baseline'] if valid else []
                if len(baseline) != 1 or baseline[0].get('action') not in ('ACCEPT','REJECT'):
                    valid = False
                elif valid:
                    b = baseline[0]
                    try:
                        valid = (b.get('token_address')==key[1] and b.get('observation_id')==key[0]
                                 and b.get('source_sha256')==cycle['source_sha256'] and not b.get('data_quality_flags')
                                 and 0 <= (now-aware(b['timestamp'])).total_seconds() <= 60
                                 and all(abs((aware(b['timestamp'])-aware(r['timestamp'])).total_seconds())<=10
                                         for r in all_ballots[0]['rows']))
                    except (KeyError, TypeError, ValueError, AttributeError):
                        valid = False
                if valid:
                    valid = all(r['source_sha256']==cycle['source_sha256'] for r in all_ballots[0]['rows'])
                for name in BOOKS[:-1]:
                    state = states[name]
                    accept = valid and (decision['action']=='SHADOW_CONSENSUS' if name=='strategy16' else votes.get(name)=='ACCEPT')
                    self.event(db, cycle['cycle_id'], name, 'DECISION', token=key[1],
                               action='ACCEPT' if accept else 'REJECT' if valid else 'ABSTAIN',
                               consensus_reason=decision.get('reason'))
                    if not accept:
                        state['rejected_signals' if valid else 'abstentions'] += 1
                        continue
                    state['accepting_signals'] += 1
                    if state['position'] or name in exited:
                        state['occupied_skips'] += 1
                        continue
                    notional = number(self.policy.notional_usd)
                    cost = notional + number(self.policy.fee_per_side_usd)
                    if number(state['cash']) < cost:
                        state['budget_skips'] += 1
                        self.event(db, cycle['cycle_id'], name, 'SKIP_BUDGET', token=key[1])
                        continue
                    try:
                        units = quote(cycle['entry_quotes'].get(key[1]), token=key[1], side='BUY',
                                      amount=notional, now=now, policy=self.policy)
                    except (KeyError, TypeError, ValueError):
                        state['quote_failures'] += 1
                        self.event(db, cycle['cycle_id'], name, 'SKIP_QUOTE', token=key[1])
                        continue
                    state['cash'] = str(number(state['cash'])-cost)
                    state['position'] = dict(token_address=key[1], units=units, cost=str(cost), entered_at=now.isoformat())
                    state['entries'] += 1
                    state['entry_notional'] = str(number(state['entry_notional'])+notional)
                    # An entry quote cannot establish a same-cycle liquidation value.
                    state['marked_equity'] = None
                    self.event(db, cycle['cycle_id'], name, 'BUY', token=key[1], units=units, cost_usd=str(cost))
            for name, state in states.items():
                if not state['position']:
                    state['marked_equity'] = state['cash']
                if state['marked_equity'] is None:
                    state['unpriced_cycles'] += 1
                else:
                    state['priced_cycles'] += 1
                    state['peak'] = str(max(number(state['peak']), number(state['marked_equity'])))
                    dd = 100*(1-number(state['marked_equity'])/number(state['peak']))
                    state['max_drawdown_pct'] = str(max(number(state['max_drawdown_pct']), dd))
                db.execute('UPDATE books SET state=? WHERE name=?', (canonical(state), name))
                db.execute('INSERT INTO book_snapshots VALUES (?,?,?,?)',
                           (cycle['cycle_id'],name,now.isoformat(),canonical(state)))
            db.execute("INSERT OR REPLACE INTO metadata VALUES ('last_stamp',?)", (now.isoformat(),))
            return self._report(db)

    def _report(self, db, duplicate=False):
        rows = []
        for name,state in db.execute('SELECT name,state FROM books ORDER BY name'):
            s=json.loads(state); equity=s['marked_equity'];closed=s['completed']
            rows.append(dict(book=name, **s,
                realized_balance_usd=str(number(self.policy.seed_usd)+number(s['realized_pnl'])),
                marked_return_pct=str(100*(number(equity)/number(self.policy.seed_usd)-1)) if equity is not None else None,
                realized_return_pct=str(100*number(s['realized_pnl'])/number(self.policy.seed_usd)),
                breakeven_closes=closed-s['wins']-s['losses'],
                expectancy_usd=str(number(s['realized_pnl'])/closed) if closed else None,
                profit_factor=str(number(s['gross_wins'])/number(s['gross_losses'])) if number(s['gross_losses']) else None,
                sampled_exposure_cycles=s['exposed_cycles'],
                largest_token_share_of_gross_wins_pct=str(100*max((number(x) for x in s['gross_wins_by_token'].values()),default=Decimal(0))/number(s['gross_wins'])) if number(s['gross_wins']) else None,
                drawdown_complete=s['unpriced_cycles']==0))
        fault=db.execute("SELECT value FROM metadata WHERE key='fault'").fetchone()
        last=db.execute("SELECT value FROM metadata WHERE key='last_stamp'").fetchone()
        source=db.execute("SELECT value FROM metadata WHERE key='source_identity'").fetchone()
        cycles=db.execute('SELECT COUNT(*) FROM cycles').fetchone()[0]
        return dict(mode='PAPER_SIMULATION_ONLY', comparison_basis='COMMON_SIZE_AND_EXIT_POLICY_SIGNAL_COMPARISON',
                    policy=asdict(self.policy), policy_sha256=self.identity,
                    consensus_policy_sha256=POLICY_HASH,source_identity_sha256=source[0] if source else None,
                    implementation_sha256=IMPLEMENTATION_SHA256,
                    as_of_utc=last[0] if last else None,cycles=cycles,
                    status='HALTED' if fault else 'PAPER_STUDY_COLLECTING' if cycles else 'NO_OBSERVATIONS',
                    fault=fault[0] if fault else None, duplicate=duplicate, books=rows)

    def report(self):
        with self.connect() as db:
            return self._report(db)

    def period(self, start_at, end_at):
        """Latest sampled endpoints; never interpolate missing/unpriced equity.

        Dedicated study books have no external deposits or withdrawals. Returns
        describe simulated net liquidation equity only, not historical engines.
        """
        start,end=aware(start_at),aware(end_at)
        if end<=start:
            raise ValueError('Period must increase')
        rows=[]
        with self.connect() as db:
            for name in BOOKS:
                points=[]
                for cutoff in (start,end):
                    point=db.execute('SELECT stamp,state FROM book_snapshots WHERE book=? AND stamp<=? ORDER BY stamp DESC LIMIT 1',
                                     (name,cutoff.isoformat())).fetchone()
                    points.append((point[0],json.loads(point[1])) if point else None)
                a,b=points
                usable=bool(a and b and a[0]!=b[0] and a[1]['marked_equity'] is not None
                            and b[1]['marked_equity'] is not None and number(a[1]['marked_equity'])>0)
                rows.append(dict(book=name,beginning_sample_at_utc=a[0] if a else None,
                                 ending_sample_at_utc=b[0] if b else None,
                                 beginning_marked_equity_usd=a[1]['marked_equity'] if a else None,
                                 ending_marked_equity_usd=b[1]['marked_equity'] if b else None,
                                 marked_return_pct=str(100*(number(b[1]['marked_equity'])/number(a[1]['marked_equity'])-1)) if usable else None,
                                 final_closes=b[1]['completed']-a[1]['completed'] if a and b else None))
        return dict(start_at_utc=start.isoformat(),end_at_utc=end.isoformat(),
                    basis='LATEST_SAMPLED_SIMULATED_LIQUIDATION_EQUITY_NO_EXTERNAL_FLOWS',books=rows)


class ProspectiveCollector:
    """Opt-in lab observer; sized quote callback is injected by a reviewed caller.

    Only this observer's supplied quotes are used; failed requests stay explicit
    and no mark-price fallback or transaction submission is provided.
    """
    def __init__(self, study, quote_provider, clock=None):
        self.study=study;self.quote_provider=quote_provider
        self.clock=clock or (lambda:datetime.now(timezone.utc))

    def __call__(self, *, candidates, observed_at, source_sha256, configuration_sha256, data_quality_flags=''):
        cycle=capture_cycle(cycle_id=observed_at, observed_at=observed_at, candidates=candidates,
                            source_sha256=source_sha256, configuration_sha256=configuration_sha256,
                            data_quality_flags=data_quality_flags)
        captured=digest(cycle)
        # Serialize acquisition too: two collectors cannot acquire different
        # quotes for the same cycle and race to turn a retry into new trades.
        with self.study.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            old=db.execute('SELECT payload FROM cycles WHERE id=?',(observed_at,)).fetchone()
            if old:
                if json.loads(old[0]).get('capture_sha256')!=captured:
                    db.execute("INSERT OR REPLACE INTO metadata VALUES ('fault','CONFLICTING_CAPTURE')")
                    db.commit()
                    raise ValueError('Conflicting capture; study halted')
                return self.study._report(db,duplicate=True)
            positions=[json.loads(s)['position'] for (s,) in db.execute('SELECT state FROM books')]
            started=monotonic()
            for p in positions:
                if not p:
                    continue
                key=f"{p['token_address']}|{p['units']}"
                if key in cycle['liquidation_quotes']:
                    continue
                if monotonic()-started>=self.study.policy.collection_max_seconds:
                    cycle['liquidation_quotes'][key]={'status':'COLLECTION_DEADLINE'}
                    continue
                try:
                    cycle['liquidation_quotes'][key]=self.quote_provider(p['token_address'],'SELL',p['units'])
                except Exception:
                    cycle['liquidation_quotes'][key]={'status':'FAILED'}
            requests=0
            for c in sorted(candidates,key=lambda c:candidate_order(c['token_address'],cycle['candidate_evidence'])):
                token=c['token_address']
                if token in cycle['entry_quotes'] or not any(c.get('votes',{}).values()):
                    continue
                if (requests>=self.study.policy.max_entry_quotes_per_cycle or data_quality_flags
                    or monotonic()-started>=self.study.policy.collection_max_seconds):
                    cycle['entry_quotes'][token]={'status':'QUOTE_BUDGET_OR_QUALITY'}
                    continue
                requests+=1
                try:
                    cycle['entry_quotes'][token]=self.quote_provider(token,'BUY',self.study.policy.notional_usd)
                except Exception:
                    cycle['entry_quotes'][token]={'status':'FAILED'}
            # Evaluate after quote acquisition; no quote from the future is used.
            evaluated=aware(self.clock().isoformat()).isoformat()
            cycle.update(observed_at=evaluated,captured_at=aware(observed_at).isoformat(),capture_sha256=captured)
            for o in cycle['observations']:
                o['evaluated_at']=evaluated
            return self.study.process(cycle,_connection=db)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database',required=True)
    parser.add_argument('--policy',required=True,help='JSON StudyPolicy with explicit research assumptions')
    parser.add_argument('--cycles',help='Prospective JSONL cycles; omitted for report-only mode')
    parser.add_argument('--report',required=True,help='Private JSON report output')
    parser.add_argument('--period-start',help='Optional aware beginning cutoff')
    parser.add_argument('--period-end',help='Optional aware ending cutoff')
    args=parser.parse_args()
    if bool(args.period_start)!=bool(args.period_end):
        parser.error('Both period cutoffs are required')
    if Path(args.report).resolve() in {Path(p).resolve() for p in (args.database,args.policy,args.cycles) if p}:
        parser.error('Report must not overwrite database, policy or input cycles')
    study=PaperStudy(args.database, StudyPolicy(**json.loads(Path(args.policy).read_text())),read_only=not args.cycles)
    if args.cycles:
        with Path(args.cycles).open(encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    study.process(json.loads(line))
    report=study.report()
    if args.period_start:
        report['period']=study.period(args.period_start,args.period_end)
    Path(args.report).write_text(json.dumps(report,indent=2),encoding='utf-8')


if __name__=='__main__':
    main()
