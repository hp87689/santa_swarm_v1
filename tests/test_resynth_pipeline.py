import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'swarm'))
from core import Puzzle, replay, save_submission, load_submission, verify_all
from resynth_driver import run

class ResynthesisPipelineTests(unittest.TestCase):
    def test_end_to_end_real_candidate_and_archive(self):
        puzzles={'scored_0001': Puzzle('scored_0001',(2,5),(14,),1000,8)}
        previous={'scored_0001':[['*',0,1,2],['+',2,0,2],['+',2,0,3]]}
        new, report = run(puzzles, previous, generation=7, max_seconds=3,
                          max_puzzles=1, seconds_per_puzzle=2,width=6,windows=60)
        self.assertEqual(report['previous_score'],3)
        self.assertEqual(report['new_score'],2)
        self.assertEqual(report['puzzles_improved'],1)
        self.assertEqual(report['instructions_saved'],1)
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'champion.csv'
            save_submission(out,new,puzzles)
            self.assertEqual(verify_all(puzzles,load_submission(out)),2)

if __name__=='__main__':unittest.main()
