import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'swarm'))
from public_bootstrap import merge_public
from core import load_puzzles, load_submission, verify_all

class TestPublicBootstrap(unittest.TestCase):
    def test_merges_valid_and_rejects_invalid_shorter_programs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with (root / 'puzzles.csv').open('w', newline='') as f:
                w = csv.writer(f)
                w.writerow(['id','starting_values','targets','value_limit','registers'])
                w.writerow(['p1','[1]','[4]',1000,48])
                w.writerow(['p2','[1]','[4]',1000,48])
            baseline = [['+',0,0,1],['+',1,1,2],['+',0,0,3]]
            with (root / 'baseline.csv').open('w', newline='') as f:
                w = csv.writer(f); w.writerow(['id','program'])
                w.writerow(['p1',json.dumps(baseline)]); w.writerow(['p2',json.dumps(baseline)])
            pub = root / 'public'; pub.mkdir()
            with (pub / 'submission.csv').open('w', newline='') as f:
                w = csv.writer(f); w.writerow(['id','program'])
                w.writerow(['p1',json.dumps([['+',0,0,1],['+',1,1,2]])])
                w.writerow(['p2',json.dumps([['+',0,0,1],['+',0,0,1]])]) # invalid
            rep = merge_public(root/'puzzles.csv',root/'baseline.csv',pub,root/'champion.csv',root/'report.json')
            self.assertEqual(rep['previous_score'],6)
            self.assertEqual(rep['new_score'],5)
            self.assertEqual(rep['puzzles_improved'],1)
            self.assertEqual(rep['sources'][0]['rejected_puzzles'],1)
            self.assertEqual(verify_all(load_puzzles(root/'puzzles.csv'), load_submission(root/'champion.csv')),5)

if __name__ == '__main__':
    unittest.main()
