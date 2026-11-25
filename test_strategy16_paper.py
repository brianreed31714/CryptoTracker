import copy
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from research.strategy16_paper import (
    BOOKS, SIGNALS, PaperStudy, ProspectiveCollector, StudyPolicy, capture_cycle,
)

BASE=datetime(2026,11,25,0,0,tzinfo=timezone.utc)


def stamp(seconds=0):
    return (BASE+timedelta(seconds=seconds)).isoformat()


def policy(**kwargs):
    args=dict(seed_usd='100',notional_usd='10',fee_per_side_usd='0.1',slippage_bps='100',
              stop_loss_pct='5',take_profit_pct='10',max_hold_seconds=60)
    args.update(kwargs)
    return StudyPolicy(**args)


def sized_quote(token,side,amount,output,seconds):
    return dict(status='OK',token_address=token,side=side,input_amount=str(amount),
                output_amount=str(output),timestamp=stamp(seconds),source_sha256='c'*64,
                data_quality_flags='')


def cycle(seconds=0,tokens=('A',),votes=None):
    c=capture_cycle(cycle_id='cycle-'+str(seconds),observed_at=stamp(seconds),
        candidates=[dict(token_address=t,votes=votes or {m:True for m in SIGNALS}) for t in tokens],
        source_sha256='a'*64,configuration_sha256='b'*64)
    c['entry_quotes']={t:sized_quote(t,'BUY',10,10000,seconds) for t in tokens}
    return c


def book(report,name='strategy16'):
    return next(x for x in report['books'] if x['book']==name)


class PaperStudyTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'study.sqlite3'
        self.study=PaperStudy(self.path,policy())

    def liquidate(self,seconds,output):
        c=cycle(seconds,tokens=())
        c['liquidation_quotes']['A|9900']=sized_quote('A','SELL',9900,output,seconds)
        return self.study.process(c)

    def test_complete_entry_and_exit_with_fees_slippage_and_restart(self):
        r=self.study.process(cycle())
        self.assertEqual(book(r)['cash'],'89.9')
        self.assertEqual(book(r)['position']['units'],9900)
        self.assertIsNone(book(r)['marked_return_pct'])
        self.study=PaperStudy(self.path,policy())
        r=self.liquidate(10,12)
        b=book(r)
        self.assertEqual(float(b['cash']),101.68)
        self.assertEqual(float(b['realized_pnl']),1.68)
        self.assertEqual(float(b['marked_return_pct']),1.68)
        self.assertEqual((b['completed'],b['wins'],b['losses']),(1,1,0))
        self.assertEqual(float(b['expectancy_usd']),1.68)
        self.assertEqual(book(r,'cash')['cash'],'100')

    def test_single_shared_budget_and_deterministic_candidate_order(self):
        r=self.study.process(cycle(tokens=('B','A')))
        for name in BOOKS[:-1]:
            b=book(r,name)
            self.assertEqual(b['entries'],1)
            self.assertEqual(b['position']['token_address'],'A')
            self.assertEqual(b['cash'],'89.9')
            self.assertEqual(b['occupied_skips'],1)

    def test_persistent_duplicate_does_not_repeat_entry_or_counts(self):
        c=cycle();first=self.study.process(c)
        r=PaperStudy(self.path,policy()).process(c)
        self.assertTrue(r['duplicate'])
        self.assertEqual(r['cycles'],1)
        self.assertEqual(book(first),book(r))

    def test_identical_envelopes_and_reordered_votes_deduplicate(self):
        c=cycle();c['observations'].append(copy.deepcopy(c['observations'][0]))
        r=self.study.process(c)
        other=copy.deepcopy(c)
        for o in other['observations']:o['rows'].reverse()
        self.assertTrue(self.study.process(other)['duplicate'])
        self.assertEqual(book(r)['entries'],1)

    def test_conflicting_same_cycle_halts_without_new_fills(self):
        self.study.process(cycle())
        c=cycle();c['entry_quotes']['A']['output_amount']='20000'
        with self.assertRaisesRegex(ValueError,'halted'):self.study.process(c)
        with self.assertRaisesRegex(ValueError,'halted'):self.study.process(cycle(10))
        self.assertEqual(self.study.report()['cycles'],1)
        self.assertEqual(self.study.report()['fault'],'CONFLICTING_CYCLE')

    def test_conflicting_envelopes_abstain_before_any_trade(self):
        c=cycle();other=copy.deepcopy(c['observations'][0])
        for v in other['rows']:v['action']='REJECT'
        c['observations'] += [other,copy.deepcopy(c['observations'][0])]
        r=self.study.process(c)
        self.assertTrue(all(b['entries']==0 for b in r['books']))

    def test_concurrent_cycle_ingestion_exactly_once(self):
        def submit(_):return PaperStudy(self.path,policy()).process(cycle())
        with ThreadPoolExecutor(max_workers=4) as executor:
            reports=list(executor.map(submit,range(4)))
        self.assertEqual(sum(not r['duplicate'] for r in reports),1)
        self.assertEqual(book(self.study.report())['entries'],1)

    def test_non_increasing_time_and_source_drift_rejected(self):
        self.study.process(cycle())
        for change in ('timestamp','source','config'):
            c=cycle(10)
            if change=='timestamp':
                c['observed_at']=stamp()
                for o in c['observations']:o['evaluated_at']=stamp()
            else:c['source_sha256' if change=='source' else 'configuration_sha256']='d'*64
            with self.subTest(change=change),self.assertRaises(ValueError):self.study.process(c)
        self.assertEqual(self.study.report()['cycles'],1)

    def test_observation_cannot_be_reused_in_a_new_cycle(self):
        first=cycle();self.study.process(first)
        c=cycle(10)
        c['observations'][0]['observation_id']=first['observations'][0]['observation_id']
        for v in c['observations'][0]['rows']:v['observation_id']=first['observations'][0]['observation_id']
        with self.assertRaisesRegex(ValueError,'identity reused'):self.study.process(c)

    def test_missing_stale_future_and_dirty_votes_abstain(self):
        for kind in ('missing','stale','future','dirty','baseline','naive'):
            c=cycle()
            if kind=='missing':c['observations'][0]['rows'].pop(0)
            else:
                row=next(v for v in c['observations'][0]['rows'] if v['model']==('strict_baseline' if kind=='baseline' else SIGNALS[0]))
                if kind in ('stale','baseline'):row['timestamp']=stamp(-70)
                if kind=='future':row['timestamp']=stamp(1)
                if kind=='dirty':row['data_quality_flags']='BAD'
                if kind=='naive':row['timestamp']='2026-11-25T00:00:00'
            # Each case uses a separate immutable study.
            study=PaperStudy(Path(self.temp.name)/(kind+'.sqlite3'),policy())
            with self.subTest(kind=kind):
                self.assertTrue(all(b['entries']==0 for b in study.process(c)['books']))

    def test_no_quorum_still_measures_individual_signal_control(self):
        votes={m:m==SIGNALS[0] for m in SIGNALS}
        r=self.study.process(cycle(votes=votes))
        self.assertEqual(book(r)['entries'],0)
        self.assertEqual(book(r,SIGNALS[0])['entries'],1)
        self.assertEqual(book(r,'strict_baseline')['entries'],0)

    def test_invalid_sized_quotes_never_create_positions(self):
        edits=[('token_address','other'),('side','SELL'),('input_amount','11'),
               ('timestamp',stamp(-31)),('timestamp',stamp(1)),('source_sha256','bad'),
               ('status','FAILED'),('output_amount','NaN'),('output_amount','Infinity'),
               ('output_amount','-1'),('output_amount',True),('data_quality_flags','BAD')]
        for i,(field,value) in enumerate(edits):
            c=cycle();c['entry_quotes']['A'][field]=value
            study=PaperStudy(Path(self.temp.name)/f'quote-{i}.sqlite3',policy())
            with self.subTest(field=field,value=value):
                self.assertEqual(book(study.process(c))['entries'],0)

    def test_failed_exit_remains_open_and_unpriced_without_fabricated_profit(self):
        self.study.process(cycle())
        r=self.study.process(cycle(120,tokens=()))
        b=book(r)
        self.assertIsNotNone(b['position'])
        self.assertIsNone(b['marked_equity'])
        self.assertIsNone(b['marked_return_pct'])
        self.assertEqual(b['completed'],0)
        self.assertEqual(b['realized_pnl'],'0')
        self.assertFalse(b['drawdown_complete'])

    def test_mark_loss_stop_and_max_hold(self):
        self.study.process(cycle())
        r=self.liquidate(5,10)
        self.assertIsNotNone(book(r)['position'])
        self.assertGreater(float(book(r)['max_drawdown_pct']),0)
        r=self.liquidate(10,9)
        self.assertEqual(float(book(r)['realized_pnl']),-1.29)
        self.assertEqual(book(r)['losses'],1)
        self.assertEqual(float(book(r)['profit_factor']),0)
        with self.study.connect() as db:
            self.assertEqual(json.loads(db.execute("SELECT payload FROM events WHERE book='strategy16' AND kind='SELL'").fetchone()[0])['reason'],'STOP')
        other=PaperStudy(Path(self.temp.name)/'hold.sqlite3',policy())
        other.process(cycle())
        c=cycle(60,tokens=());c['liquidation_quotes']['A|9900']=sized_quote('A','SELL',9900,10,60)
        self.assertEqual(book(other.process(c))['completed'],1)

    def test_cash_insufficiency_never_borrows(self):
        study=PaperStudy(Path(self.temp.name)/'small.sqlite3',policy(seed_usd='10.1'))
        study.process(cycle())
        c=cycle(5,tokens=());c['liquidation_quotes']['A|9900']=sized_quote('A','SELL',9900,1,5)
        study.process(c)
        b=book(study.process(cycle(10)))
        self.assertEqual(b['entries'],1)
        self.assertIsNone(b['position'])
        self.assertGreaterEqual(float(b['cash']),0)

    def test_transaction_failure_rolls_back_every_book_and_journal(self):
        with self.study.connect() as db:
            db.execute("CREATE TRIGGER fail_buy BEFORE INSERT ON events WHEN NEW.book='whale_luna' AND NEW.kind='BUY' BEGIN SELECT RAISE(ABORT,'injected'); END")
        with self.assertRaises(sqlite3.IntegrityError):self.study.process(cycle())
        r=self.study.report()
        self.assertEqual(r['cycles'],0)
        self.assertTrue(all(b['cash']=='100' and b['entries']==0 for b in r['books']))

    def test_policy_drift_and_missing_book_cannot_reset_history(self):
        with self.assertRaisesRegex(ValueError,'policy changed'):
            PaperStudy(self.path,replace(policy(),notional_usd='5'))
        with self.study.connect() as db:db.execute("DELETE FROM books WHERE name='strategy16'")
        with self.assertRaisesRegex(ValueError,'corrupt'):PaperStudy(self.path,policy())

    def test_policy_rejects_invalid_assumptions(self):
        for args in ({'seed_usd':'0'},{'notional_usd':'101'},{'fee_per_side_usd':'-1'},
                     {'slippage_bps':'10000'},{'stop_loss_pct':'0'},{'max_hold_seconds':True},
                     {'take_profit_pct':'NaN'}):
            with self.subTest(args=args),self.assertRaises(ValueError):policy(**args)

    def test_period_endpoints_and_unpriced_or_missing_periods(self):
        self.study.process(cycle(0,tokens=()))
        self.study.process(cycle(1))
        self.liquidate(10,12)
        p=self.study.period(stamp(0),stamp(10))
        self.assertEqual(float(book(p)['marked_return_pct']),1.68)
        self.assertEqual(book(p)['final_closes'],1)
        self.assertIsNone(book(self.study.period(stamp(0),stamp(1)))['marked_return_pct'])
        self.assertIsNone(book(self.study.period(stamp(-10),stamp(10)))['marked_return_pct'])
        self.assertIsNone(book(self.study.period(stamp(20),stamp(30)))['marked_return_pct'])
        with self.assertRaises(ValueError):self.study.period(stamp(10),stamp(0))

    def test_unrelated_database_is_not_modified(self):
        path=Path(self.temp.name)/'other.sqlite3'
        db=sqlite3.connect(path)
        db.execute('CREATE TABLE existing (x TEXT)');db.commit();db.close()
        with self.assertRaisesRegex(ValueError,'Not a Strategy16'):PaperStudy(path,policy())
        db=sqlite3.connect(path)
        self.assertEqual(db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall(),[('existing',)])
        db.close()

    def test_implementation_identity_change_requires_new_study(self):
        with patch('research.strategy16_paper.IMPLEMENTATION_SHA256','d'*64):
            with self.assertRaisesRegex(ValueError,'policy changed'):PaperStudy(self.path,policy())

    def test_baseline_skew_and_pre_entry_liquidation_are_rejected(self):
        c=cycle()
        for r in c['observations'][0]['rows']:
            if r['model']=='strict_baseline':r['timestamp']=stamp(-11)
        self.assertEqual(book(self.study.process(c))['entries'],0)
        self.study.process(cycle(10))
        c=cycle(20,tokens=());c['liquidation_quotes']['A|9900']=sized_quote('A','SELL',9900,12,9)
        self.assertIsNone(book(self.study.process(c))['marked_return_pct'])

    def test_cash_status_and_concentration_are_explicit(self):
        self.assertEqual(self.study.report()['status'],'NO_OBSERVATIONS')
        self.study.process(cycle())
        r=self.liquidate(10,12)
        self.assertEqual(r['status'],'PAPER_STUDY_COLLECTING')
        self.assertEqual(float(book(r)['largest_token_share_of_gross_wins_pct']),100)
        self.assertEqual(book(r,'cash')['entries'],0)


class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.study=PaperStudy(Path(self.temp.name)/'study.sqlite3',policy())
        self.args=dict(candidates=[dict(token_address='A',votes={m:True for m in SIGNALS},features={'score':80})],
                       observed_at=stamp(),source_sha256='a'*64,configuration_sha256='b'*64)

    def test_collection_then_restart_retry_does_not_request_new_quotes(self):
        provider=Mock(return_value=sized_quote('A','BUY',10,10000,1))
        collector=ProspectiveCollector(self.study,provider,clock=lambda:BASE+timedelta(seconds=2))
        self.assertEqual(book(collector(**self.args))['entries'],1)
        again=ProspectiveCollector(PaperStudy(self.study.path,policy()),provider)
        self.assertTrue(again(**self.args)['duplicate'])
        self.assertEqual(provider.call_count,1)

    def test_concurrent_collectors_acquire_one_quote_and_one_fill(self):
        provider=Mock(return_value=sized_quote('A','BUY',10,10000,1))
        def run(_):
            return ProspectiveCollector(PaperStudy(self.study.path,policy()),provider,
                clock=lambda:BASE+timedelta(seconds=2))(**self.args)
        with ThreadPoolExecutor(max_workers=3) as executor:r=list(executor.map(run,range(3)))
        self.assertEqual(sum(not x['duplicate'] for x in r),1)
        self.assertEqual(provider.call_count,1)

    def test_provider_failure_and_slow_collection_fail_closed(self):
        provider=Mock(side_effect=RuntimeError('no route'))
        c=ProspectiveCollector(self.study,provider,clock=lambda:BASE+timedelta(seconds=2))
        self.assertEqual(book(c(**self.args))['entries'],0)
        other=PaperStudy(Path(self.temp.name)/'slow.sqlite3',policy())
        provider=Mock(return_value=sized_quote('A','BUY',10,10000,70))
        c=ProspectiveCollector(other,provider,clock=lambda:BASE+timedelta(seconds=71))
        self.assertEqual(book(c(**self.args))['entries'],0)

    def test_explicit_booleans_only_and_no_legacy_timestamp_adaptation(self):
        bad=copy.deepcopy(self.args);bad['candidates'][0]['votes'][SIGNALS[0]]='BUY'
        c=capture_cycle(cycle_id='x',**bad)
        self.assertEqual(len(c['observations'][0]['rows']),3)
        bad['observed_at']='2026-11-25T00:00:00'
        with self.assertRaises(ValueError):capture_cycle(cycle_id='x',**bad)

    def test_conflicting_capture_halts_and_stores_feature_provenance(self):
        provider=Mock(return_value=sized_quote('A','BUY',10,10000,1))
        c=ProspectiveCollector(self.study,provider,clock=lambda:BASE+timedelta(seconds=2))
        c(**self.args)
        bad=copy.deepcopy(self.args);bad['candidates'][0]['features']['score']=81
        with self.assertRaisesRegex(ValueError,'halted'):c(**bad)
        with self.study.connect() as db:
            payload=json.loads(db.execute('SELECT payload FROM cycles').fetchone()[0])
        self.assertEqual(payload['candidate_evidence']['A']['features']['score'],80)
        self.assertEqual(provider.call_count,1)

    def test_entry_quote_budget_and_candidate_order(self):
        study=PaperStudy(Path(self.temp.name)/'budget.sqlite3',policy(max_entry_quotes_per_cycle=1))
        args=copy.deepcopy(self.args)
        args['candidates']=[dict(token_address=t,votes={m:True for m in SIGNALS}) for t in ('B','A')]
        provider=Mock(side_effect=lambda t,s,a:sized_quote(t,s,a,10000,1))
        c=ProspectiveCollector(study,provider,clock=lambda:BASE+timedelta(seconds=2))
        self.assertEqual(book(c(**args))['position']['token_address'],'A')
        provider.assert_called_once_with('A','BUY','10')

    def test_collection_deadline_does_not_begin_additional_requests(self):
        args=copy.deepcopy(self.args)
        args['candidates']=[dict(token_address=t,votes={m:True for m in SIGNALS}) for t in ('A','B')]
        provider=Mock(side_effect=lambda t,s,a:sized_quote(t,s,a,10000,1))
        c=ProspectiveCollector(self.study,provider,clock=lambda:BASE+timedelta(seconds=2))
        with patch('research.strategy16_paper.monotonic',side_effect=[0,1,6]):
            c(**args)
        provider.assert_called_once_with('A','BUY','10')

    def test_common_quant_priority_is_used_for_quote_budget_and_entry(self):
        study=PaperStudy(Path(self.temp.name)/'quant.sqlite3',policy(max_entry_quotes_per_cycle=1))
        args=copy.deepcopy(self.args)
        args['candidates']=[dict(token_address=t,votes={m:True for m in SIGNALS},features={'quant':q})
                            for t,q in [('A',70),('B',90)]]
        provider=Mock(side_effect=lambda t,s,a:sized_quote(t,s,a,10000,1))
        c=ProspectiveCollector(study,provider,clock=lambda:BASE+timedelta(seconds=2))
        self.assertEqual(book(c(**args))['position']['token_address'],'B')
        provider.assert_called_once_with('B','BUY','10')

    def test_cli_persists_and_exports_report_without_order_dependencies(self):
        root=Path(self.temp.name)
        (root/'policy.json').write_text(json.dumps(policy().__dict__))
        (root/'cycles.jsonl').write_text(json.dumps(cycle())+'\n')
        args=[sys.executable,'-m','research.strategy16_paper','--database',str(root/'cli.sqlite3'),
              '--policy',str(root/'policy.json'),'--cycles',str(root/'cycles.jsonl'),'--report',str(root/'report.json')]
        subprocess.run(args,check=True,capture_output=True,text=True)
        subprocess.run(args,check=True,capture_output=True,text=True)
        self.assertEqual(json.loads((root/'report.json').read_text())['cycles'],1)


class LabAdapterTests(unittest.TestCase):
    def test_lab_to_collector_to_ledger_end_to_end(self):
        import paper_research_lab_v11_10 as lab
        with tempfile.TemporaryDirectory() as temp:
            study=PaperStudy(Path(temp)/'study.sqlite3',policy())
            moment=[0]
            provider=lambda token,side,amount:sized_quote(token,side,amount,10000 if side=='BUY' else 12,moment[0])
            collector=ProspectiveCollector(study,provider,clock=lambda:BASE+timedelta(seconds=moment[0]))
            def observe(**kwargs):
                kwargs['observed_at']=stamp(moment[0])
                return collector(**kwargs)
            with patch.object(lab,'_load_state',side_effect=lambda *a:{'models':{}}),\
                 patch.object(lab,'_save_state'),patch.object(lab,'_append_csv'),\
                 patch.object(lab,'_add_shadow_positions'),\
                 patch.object(lab,'_model_safety_pass',return_value=(True,[])),\
                 patch.dict('os.environ',{'PAPER_SHADOW_EXPERIMENTS_ENABLED':'0'}):
                result=lab._run_paper_research([{'token_address':'A','price_usd':1}],{},strategy16_observer=observe)
                self.assertEqual(book(result['strategy16'])['entries'],1)
                moment[0]=10
                result=lab._run_paper_research([],{},strategy16_observer=observe)
                self.assertEqual(book(result['strategy16'])['completed'],1)
                self.assertEqual(float(book(result['strategy16'])['marked_return_pct']),1.68)

    def test_explicit_prospective_adapter_captures_all_four_decisions(self):
        import paper_research_lab_v11_10 as lab
        candidate={'token_address':'A','price_usd':1}
        scores={m:80 for m in SIGNALS}
        observer=Mock(return_value={'mode':'PAPER_SIMULATION_ONLY'})
        with patch.object(lab,'_model_safety_pass',return_value=(True,[])) as gate:
            r=lab._observe_strategy16(observer,[(candidate,scores)],{'name':'RISK_ON'},'')
        data=observer.call_args.kwargs
        self.assertEqual(set(data['candidates'][0]['votes']),set(SIGNALS))
        self.assertEqual(gate.call_count,4)
        self.assertEqual(len(data['source_sha256']),64)
        self.assertIsNotNone(datetime.fromisoformat(data['observed_at']).utcoffset())
        self.assertEqual(r['mode'],'PAPER_SIMULATION_ONLY')

    def test_optional_observer_runs_before_entries_and_failure_is_visible(self):
        import paper_research_lab_v11_10 as lab
        state={'models':{}}
        calls=[]
        def observer(*args):calls.append('observer');return {'mode':'PAPER_SIMULATION_ONLY'}
        with patch.object(lab,'_load_state',return_value=state),patch.object(lab,'_save_state'),\
             patch.object(lab,'_append_csv'),patch.object(lab,'_manage_position'),\
             patch.object(lab,'_manage_staged_position'),patch.object(lab,'_manage_shadow_positions'),\
             patch.object(lab,'_add_shadow_positions',side_effect=lambda *a,**k:calls.append('entries')),\
             patch.object(lab,'_observe_strategy16',side_effect=observer),\
             patch.dict('os.environ',{'PAPER_SHADOW_EXPERIMENTS_ENABLED':'0'}):
            result=lab._run_paper_research([],{},strategy16_observer=Mock())
            self.assertEqual(calls[0],'observer')
            self.assertIn('strategy16',result)
        with patch.object(lab,'_load_state',return_value={'models':{}}),patch.object(lab,'_save_state'),\
             patch.object(lab,'_append_csv'),patch.object(lab,'_add_shadow_positions'),\
             patch.object(lab,'_observe_strategy16',side_effect=RuntimeError),\
             patch.dict('os.environ',{'PAPER_SHADOW_EXPERIMENTS_ENABLED':'0'}):
            result=lab._run_paper_research([],{},strategy16_observer=Mock())
            self.assertEqual(result['strategy16']['status'],'OBSERVER_FAILED')
        with patch.object(lab,'_load_state',return_value={'models':{}}),patch.object(lab,'_save_state'),\
             patch.object(lab,'_append_csv'),patch.object(lab,'_add_shadow_positions'),\
             patch.object(lab,'_observe_strategy16') as observe,\
             patch.dict('os.environ',{'PAPER_SHADOW_EXPERIMENTS_ENABLED':'0'}):
            self.assertNotIn('strategy16',lab._run_paper_research([],{}))
            observe.assert_not_called()


if __name__=='__main__':unittest.main()
