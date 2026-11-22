import copy
import unittest
from research.strategy16_shadow import MEMBERS, evaluate, evaluate_batch


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

if __name__=='__main__': unittest.main()
