import copy
import unittest
from research.strategy16_shadow import MEMBERS, POLICY, POLICY_HASH, evaluate, evaluate_batch
import hashlib
import json


class ConsensusTests(unittest.TestCase):
    def candidate(self):
        return dict(observation_id='cycle-1', token_address='token-a',
            evaluated_at='2026-11-22T06:00:10+00:00',rows=[dict(model=m,
            timestamp='2026-11-22T06:00:00+00:00',observation_id='cycle-1',
            token_address='token-a',action='ACCEPT' if i<2 else 'REJECT',
            source_sha256='a'*64,data_quality_flags='') for i,m in enumerate(MEMBERS)])

    def test_quorum_and_no_quorum(self):
        c=self.candidate();self.assertEqual(evaluate(**c)['action'],'SHADOW_CONSENSUS')
        c['rows'][0]['action']='REJECT';self.assertEqual(evaluate(**c)['action'],'REJECT')

    def test_bad_evidence_fails_closed(self):
        for field,value in [('timestamp','2026-11-22T05:00:00+00:00'),
             ('timestamp','2026-11-22T06:00:11+00:00'),
             ('timestamp','2026-11-22T06:00:00'),('action','BUY'),
             ('token_address','other'),('observation_id','other'),
             ('source_sha256',''),('data_quality_flags','MISSING')]:
            with self.subTest(field=field,value=value):
                c=self.candidate();c['rows'][0][field]=value
                self.assertEqual(evaluate(**c)['action'],'ABSTAIN')

    def test_missing_duplicate_and_unknown_votes(self):
        c=self.candidate();c['rows'].pop();self.assertEqual(evaluate(**c)['action'],'ABSTAIN')
        c=self.candidate();c['rows'][1]=copy.deepcopy(c['rows'][0]);self.assertEqual(evaluate(**c)['action'],'ABSTAIN')
        c=self.candidate();c['rows'][0]['model']='unknown';self.assertEqual(evaluate(**c)['action'],'ABSTAIN')

    def test_skew_and_dedup_and_input_immutable(self):
        c=self.candidate();before=copy.deepcopy(c)
        self.assertEqual(len(evaluate_batch([c,c])),1);self.assertEqual(c,before)
        c['rows'][0]['timestamp']='2026-11-22T05:59:40+00:00'
        self.assertEqual(evaluate(**c)['action'],'ABSTAIN')

    def test_conflicting_duplicates_abstain_in_both_orders(self):
        c=self.candidate();conflict=copy.deepcopy(c)
        for row in conflict['rows']: row['action']='REJECT'
        for batch in ([c,conflict],[conflict,c],[c,conflict,c]):
            result=evaluate_batch(batch)
            self.assertEqual(len(result),1)
            self.assertEqual(result[0]['reason'],'CONFLICTING_DUPLICATE')
            self.assertEqual(result[0]['action'],'ABSTAIN')

    def test_reordered_identical_duplicate(self):
        c=self.candidate();other=copy.deepcopy(c);other['rows'].reverse()
        self.assertEqual(len(evaluate_batch([c,other])),1)
        self.assertEqual(evaluate_batch([c,other])[0]['action'],'SHADOW_CONSENSUS')

    def test_policy_is_immutable_and_hash_matches(self):
        with self.assertRaises(TypeError): POLICY['maximum_age_seconds']=1000
        self.assertEqual(POLICY_HASH,hashlib.sha256(json.dumps(dict(POLICY),sort_keys=True).encode()).hexdigest())

    def test_malformed_batch_entries_do_not_hide_valid_candidate(self):
        for bad in ({},None,{'rows':[]},dict(self.candidate(),token_address=[])):
            results=evaluate_batch([bad,self.candidate()])
            self.assertEqual(results[0]['action'],'ABSTAIN')
            self.assertEqual(results[1]['action'],'SHADOW_CONSENSUS')

    def test_bad_digest_abstains(self):
        for digest in ('x'*64,'a',True):
            c=self.candidate();c['rows'][0]['source_sha256']=digest
            self.assertEqual(evaluate(**c)['action'],'ABSTAIN')

if __name__=='__main__': unittest.main()
