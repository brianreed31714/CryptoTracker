import unittest
from unittest.mock import patch
import paper_research_lab_v11_10 as lab

class SignalActionsTest(unittest.TestCase):
    def run_cycle(self, rows=(), position=None, safe=False):
        candidate = {'token_address': 'token', 'symbol': 'TEST', 'paper_model_scores': {'strict_baseline': 10}}
        def cycle(*args, **kwargs):
            lab._CYCLE_ROWS.get().extend(rows)
            return {'models': {'strict_baseline': {'position': position}}, 'regime': {'name': 'NEUTRAL'}}
        with patch.object(lab, 'MODEL_SPECS', {'strict_baseline': lab.MODEL_SPECS['strict_baseline']}), patch.object(lab, '_run_paper_research', side_effect=cycle), patch.object(lab, '_model_safety_pass', return_value=(safe, ['score_below_threshold'])), patch.object(lab, '_append_csv'):
            result = lab.run_paper_research([candidate], {})
        return candidate['paper_actions'], result

    def test_specific_safety_reason_replaces_generic(self):
        rows=[(lab.DECISION_FILE, {'model':'strict_baseline','token_address':'token','reason':'no_eligible_candidate'})]
        actions,_=self.run_cycle(rows)
        self.assertIn('score_below_threshold',actions[0]['reason'])
        self.assertIn('score 10.0 <',actions[0]['reason'])

    def test_occupied(self):
        actions,_=self.run_cycle(position={'token_address':'other','symbol':'OTHER'})
        self.assertEqual(actions[0]['reason'],'position_occupied:OTHER')

    def test_ranking(self):
        actions,_=self.run_cycle(safe=True)
        self.assertEqual(actions[0]['reason'],'higher_ranked_candidate_selected')

    def test_quote_failure(self):
        rows=[(lab.DECISION_FILE, {'model':'strict_baseline','token_address':'token','reason':'no_executable_quote','integrity_detail':'quote timed out'})]
        actions,_=self.run_cycle(rows)
        self.assertEqual(actions[0]['reason'],'no_executable_quote:quote timed out')

    def test_actual_buy_and_sell_are_preserved(self):
        events=[{'model':'strict_baseline','token_address':'token','action':a,'reason':'MODEL_ENTRY' if a=='BUY' else 'STOP'} for a in ['SELL','BUY']]
        actions,result=self.run_cycle([(lab.TRADE_FILE,e) for e in events])
        self.assertEqual(actions,events)
        self.assertEqual(result['trade_events'],events)
        self.assertIsNone(lab._CYCLE_ROWS.get())

    def test_pages_preserve_all_text(self):
        lines=['x'*1200,'last reason']
        pages=lab.alert_pages(lines)
        self.assertTrue(all(len(p)<=1000 for p in pages))
        self.assertEqual(''.join(pages).replace('\n',''),''.join(lines))

if __name__=='__main__':
    unittest.main()
