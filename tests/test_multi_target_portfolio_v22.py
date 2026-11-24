"""Real arithmetic resynthesis, persistence and champion safety tests."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'swarm'))
from core import Puzzle,replay
from beam_resynthesis import improve_beam
from portfolio_v22 import load_memory,run_portfolio,_mutate_genome


class MultiTargetTests(unittest.TestCase):
    def setUp(self):
        self.puzzle=Puzzle('multi',(2,3,5),(10,12,15),1000,8)
        self.original=[['+',0,1,3],['+',3,2,4],['+',4,0,5],['+',4,2,6]]

    def test_three_output_reconstruction_not_dead_code(self):
        self.assertEqual(replay(self.puzzle,self.original),4)
        program,metrics=improve_beam(self.puzzle,self.original,max_seconds=1.3,
                                      max_windows=45,seed=3)
        self.assertEqual(replay(self.puzzle,program),3)
        self.assertEqual(metrics['instructions_saved'],1)
        self.assertGreater(metrics['states_expanded'],0)

    def test_preserve_critical_suffix_register(self):
        p=Puzzle('suffix',(2,3,5),(10,12,15,30),1000,9)
        code=self.original+[ ['*',4,1,7] ]  # 10*3 -> 30, r4 must survive
        self.assertEqual(replay(p,code),5)
        edited,_=improve_beam(p,code,max_seconds=1,max_windows=50,seed=41)
        self.assertLessEqual(len(edited),len(code))
        replay(p,edited)

    def test_no_fabricated_gain_on_one_step_solution(self):
        p=Puzzle('optimal',(2,3),(5,),100,6)
        code=[['+',0,1,2]]
        edited,metrics=improve_beam(p,code,max_seconds=.2)
        self.assertEqual(code,edited)
        self.assertEqual(metrics['instructions_saved'],0)

    def test_never_introduce_invalid_division_or_zero(self):
        p=Puzzle('numbers',(1,7),(10,),1000,8)
        code=[['+',0,0,1],['+',1,0,2],['+',2,1,2],['+',2,1,2],
              ['+',2,1,2],['+',2,0,3]]
        self.assertEqual(replay(p,code),6)
        edited,_=improve_beam(p,code,max_seconds=1.0,seed=7)
        self.assertLessEqual(len(edited),len(code))
        replay(p,edited)

    def test_multi_target_reg_limits(self):
        p=Puzzle('tight',(2,3,5),(10,12,15),1000,5)
        # Only five physical registers, reuse r3 and r4 as required.
        code=[['+',0,1,3],['+',3,2,4],['+',4,0,3],['+',4,2,4]]
        self.assertEqual(replay(p,code),4)
        edited,_=improve_beam(p,code,max_seconds=1,seed=3)
        replay(p,edited)
        self.assertLessEqual(len(edited),4)


class PopulationTests(unittest.TestCase):
    def test_score_is_validated_and_cannot_regress(self):
        p=Puzzle('m',(2,3,5),(10,12,15),1000,8)
        code=[['+',0,1,3],['+',3,2,4],['+',4,0,5],['+',4,2,6]]
        with tempfile.TemporaryDirectory() as d:
            memory=load_memory(Path(d)/'memo.json')
            new,info,memory=run_portfolio({'m':p},{'m':code},generation=1,
                memory=memory,max_puzzles=1,max_seconds=3,seconds_per_trial=1.2)
            self.assertEqual(info['previous_score'],4)
            self.assertEqual(info['new_score'],3)
            self.assertEqual(info['instructions_saved'],1)
            self.assertEqual(replay(p,new['m']),3)
            path=Path(d)/'memo.json'
            path.write_text(json.dumps(memory))
            fresh=load_memory(path)
            self.assertGreater(sum(x['tested'] for x in fresh['population']),0)
            _,info2,fresh=run_portfolio({'m':p},new,generation=2,memory=fresh,
                max_puzzles=1,max_seconds=1.5,seconds_per_trial=0.5)
            self.assertEqual(info2['new_score'],3)
            self.assertGreater(fresh['generation_count'],memory['generation_count']-1)
            self.assertEqual(len(fresh['population']),len(memory['population'])+1)

    def test_mutation_is_a_new_genome(self):
        import random
        with tempfile.TemporaryDirectory() as d:
            parent=load_memory(Path(d)/'missing.json')['population'][0]
            child=_mutate_genome(parent,random.Random(1),'new',2)
            self.assertEqual(child['id'],'new')
            self.assertEqual(child['tested'],0)
            self.assertNotEqual([child[k] for k in ('beam_width','helper_cap','exploration','window_size')],
                                [parent[k] for k in ('beam_width','helper_cap','exploration','window_size')])


if __name__=='__main__':unittest.main()
