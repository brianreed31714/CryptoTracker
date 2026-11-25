from dataclasses import asdict
from datetime import datetime, timezone
import ast
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from research.strategy16_paper import PaperStudy, SIGNALS
from research.strategy16_runtime import PRODUCER, SizedQuoteAdapter, configured_observer, release_identity
from test_strategy16_paper import policy


def response(source='USDC',target='A',amount=10000000,output=10000):
    return {'inputMint':source,'outputMint':target,'inAmount':str(amount),
            'outAmount':str(output),'otherAmountThreshold':str(int(output*.99)),
            'transaction':'MUST_NOT_BE_STORED_OR_SIGNED','requestId':'fixture'}


class QuoteAdapterTests(unittest.TestCase):
    def test_raw_units_direction_conservative_output_and_no_taker(self):
        get=Mock(return_value=response())
        q=SizedQuoteAdapter(get,'USDC')('A','BUY','10')
        get.assert_called_once_with('USDC','A',10000000)
        self.assertEqual(q['output_amount'],'9900')
        self.assertEqual(q['input_amount'],'10')
        self.assertIsNotNone(datetime.fromisoformat(q['timestamp']).utcoffset())
        get=Mock(return_value=response('A','USDC',9900,12000000))
        q=SizedQuoteAdapter(get,'USDC')('A','SELL',9900)
        self.assertEqual(q['output_amount'],'11.88')
        get.assert_called_once_with('A','USDC',9900)

    def test_bad_response_identity_size_threshold_and_errors_fail_closed(self):
        for field,value in [('inputMint','OTHER'),('outputMint','OTHER'),('inAmount','1'),
                            ('outAmount','NaN'),('outAmount','1.2'),('outAmount','0'),
                            ('otherAmountThreshold','10001'),('otherAmountThreshold','0'),
                            ('errorCode',1)]:
            r=response();r[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):
                SizedQuoteAdapter(Mock(return_value=r),'USDC')('A','BUY',10)

    def test_absent_threshold_is_indicative_with_explicit_study_costs(self):
        r=response();del r['otherAmountThreshold']
        q=SizedQuoteAdapter(Mock(return_value=r),'USDC')('A','BUY',10)
        self.assertEqual(q['output_amount'],'10000')
        for token,side,amount in [('USDC','BUY',10),('A','BAD',10),('A','SELL','1.2'),('A','BUY',0)]:
            with self.subTest(token=token,side=side,amount=amount),self.assertRaises(ValueError):
                SizedQuoteAdapter(Mock(return_value=r),'USDC')(token,side,amount)


class ActivationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        (self.root/'paper_research_lab_v11_10.py').write_text('# fixture lab')
        (self.root/PRODUCER).write_text('# fixture producer')

    def manifest(self):
        directory=self.root/'data/strategy16';directory.mkdir(parents=True,exist_ok=True)
        m={'mode':'PAPER_ONLY','release':release_identity(self.root),'policy':asdict(policy())}
        (directory/'activation.json').write_text(json.dumps(m),encoding='utf-8')
        return m

    def test_absent_activation_has_no_database_or_quote_effect(self):
        get=Mock()
        self.assertIsNone(configured_observer(self.root,get,'USDC'))
        get.assert_not_called()
        self.assertFalse((self.root/'data').exists())

    def test_live_flag_bad_mode_and_release_drift_do_not_start_a_study(self):
        for kind in ('live','mode','release'):
            m=self.manifest()
            if kind=='mode':m['mode']='LIVE'
            if kind=='release':m['release']['lab_sha256']='d'*64
            (self.root/'data/strategy16/activation.json').write_text(json.dumps(m))
            get=Mock()
            with self.subTest(kind=kind),self.assertRaises(ValueError):
                configured_observer(self.root,get,'USDC',live_trading=kind=='live')
            get.assert_not_called()
            self.assertFalse((self.root/'data/strategy16/study.sqlite3').exists())

    def test_manifest_pipeline_records_paper_entry_and_private_report(self):
        self.manifest()
        get=Mock(side_effect=lambda i,o,a:response(i,o,a,10000 if i=='USDC' else 12000000))
        release=release_identity(self.root)
        observer=configured_observer(self.root,get,'USDC',loaded_lab_sha256=release['lab_sha256'],
                                     loaded_producer_sha256=release['producer_sha256'])
        now=datetime.now(timezone.utc).isoformat()
        report=observer(candidates=[{'token_address':'A','votes':{m:True for m in SIGNALS}}],
                        observed_at=now,source_sha256='a'*64,configuration_sha256='b'*64)
        self.assertEqual(next(b for b in report['books'] if b['book']=='strategy16')['entries'],1)
        latest=json.loads((self.root/'data/strategy16/latest.json').read_text())
        self.assertEqual(latest['cycles'],1)
        self.assertNotIn('MUST_NOT_BE_STORED_OR_SIGNED',json.dumps(latest))
        self.assertTrue(observer(candidates=[{'token_address':'A','votes':{m:True for m in SIGNALS}}],
            observed_at=now,source_sha256='a'*64,configuration_sha256='b'*64)['duplicate'])
        self.assertEqual(get.call_count,1)

    def test_changed_loaded_identity_is_not_relabelled_with_disk_identity(self):
        self.manifest();release=release_identity(self.root)
        get=Mock()
        with self.assertRaisesRegex(ValueError,'identity mismatch'):
            configured_observer(self.root,get,'USDC',loaded_lab_sha256='d'*64,
                                loaded_producer_sha256=release['producer_sha256'])
        get.assert_not_called()

    def test_report_only_access_preserves_database_bytes(self):
        path=self.root/'study.sqlite3'
        study=PaperStudy(path,policy())
        before=path.read_bytes()
        readonly=PaperStudy(path,policy(),read_only=True)
        self.assertEqual(readonly.report()['status'],'NO_OBSERVATIONS')
        with self.assertRaises(ValueError):readonly.process({})
        self.assertEqual(before,path.read_bytes())

    def test_report_only_does_not_create_missing_database(self):
        import sqlite3
        path=self.root/'missing.sqlite3'
        with self.assertRaises(sqlite3.OperationalError):PaperStudy(path,policy(),read_only=True)
        self.assertFalse(path.exists())

    def test_production_hook_supplies_quote_callback_without_signer(self):
        tree=ast.parse(Path(PRODUCER).read_text(encoding='utf-8'))
        configured=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)
                    and n.func.id=='configured_observer']
        self.assertEqual(len(configured),1)
        callback=configured[0].args[1]
        self.assertIsInstance(callback,ast.Lambda)
        self.assertEqual(callback.body.func.id,'jupiter_order')
        self.assertEqual(len(callback.body.args),4)
        self.assertEqual([k.arg for k in callback.body.keywords],['timeout_seconds'])
        self.assertEqual(callback.body.keywords[0].value.value,3)
        runtime=Path('research/strategy16_runtime.py').read_text()
        self.assertNotIn('sign_transaction(',runtime)
        self.assertNotIn('execute_order(',runtime)


if __name__=='__main__':unittest.main()
