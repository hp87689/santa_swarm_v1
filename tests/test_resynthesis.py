import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'swarm'))
from core import Puzzle, replay
from resynthesis import improve_resynthesis, recipes_one, rewrite_window, compute_states_and_live

class ResynthesisTests(unittest.TestCase):
    def test_two_step_is_new_math_not_dead_code(self):
        # 2*5=10, +2=12, +2=14 (3), whereas (2+5)*2=14 (2).
        p = Puzzle('toy', (2,5), (14,), 1000, 8)
        orig = [['*',0,1,2],['+',2,0,2],['+',2,0,3]]
        self.assertEqual(replay(p,orig), 3)
        new, log = improve_resynthesis(p, orig, width=4, max_windows=30, max_seconds=2)
        self.assertEqual(replay(p,new),2)
        self.assertEqual(log['instructions_saved'],1)
    def test_validate_source_preservation(self):
        # r2 = 10, r3 = 12, r4 = 14, and later 10 participates in a target.
        # Illegal rewrite must never remove the necessary 10.
        p = Puzzle('toy', (2,5), (14,20), 1000, 8)
        orig = [['*',0,1,2],['+',2,0,3],['+',3,0,4],['*',2,0,5]]
        self.assertEqual(replay(p,orig),4)
        new, _ = improve_resynthesis(p,orig,width=5,max_windows=100,max_seconds=2)
        replay(p,new)
        self.assertLessEqual(len(new),4)
    def test_no_invalid_subtraction_or_division(self):
        p = Puzzle('toy',(1,7),(10,),1000,8)
        orig = [['+',0,0,1],['+',1,0,2],['+',2,1,2],['+',2,1,2],['+',2,1,2],['+',2,0,3]]
        self.assertEqual(replay(p,orig),6)
        new, _ = improve_resynthesis(p,orig,width=8,max_windows=80,max_seconds=2)
        replay(p,new)
    def test_can_rewrite_target_written_to_dead_register(self):
        p = Puzzle('toy', (2,5), (14, ), 1000, 8)
        # r2 is overwritten after target and is dead: target still counts.
        orig = [['*',0,1,2],['+',2,0,2],['+',2,0,3],['+',0,0,3]]
        self.assertEqual(replay(p,orig),4)
        new, log = improve_resynthesis(p,orig,max_windows=90,max_seconds=2)
        replay(p,new)
        self.assertLessEqual(len(new),3)
    def test_one_step_inverse(self):
        vals = [2,5,None,None]
        self.assertTrue(any(op=='+' for op,a,b in recipes_one(vals,7,100)))
        self.assertTrue(any(op=='*' for op,a,b in recipes_one(vals,10,100)))
    def test_does_not_fabricate_improvements(self):
        p = Puzzle('toy',(2,5),(7,),1000,8)
        prog = [['+',0,1,2]]
        new, log = improve_resynthesis(p,prog,width=10,max_windows=40,max_seconds=1)
        self.assertEqual(len(new),1)
        self.assertEqual(log['instructions_saved'],0)

if __name__=='__main__':unittest.main()
