import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class TestCompletePipeline(unittest.TestCase):
    def test_local_end_to_end_saves_and_reports_stage_improvements(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            puzzles = d/'puzzles.csv'
            with puzzles.open('w', newline='') as f:
                w = csv.writer(f)
                w.writerow(['id', 'starting_values', 'targets', 'value_limit', 'registers'])
                w.writerow(['p1', '[2,3,5]', '[10]', 100, 48])
                w.writerow(['p2', '[2,3]', '[5,10]', 100, 48])
            original = d/'base.csv'
            with original.open('w', newline='') as f:
                w = csv.writer(f)
                w.writerow(['id', 'program'])
                w.writerow(['p1', json.dumps([['+',0,1,3],['+',3,3,4]])])
                w.writerow(['p2', json.dumps([['+',0,1,2],['+',0,1,3],['+',3,3,4]])])
            evolved=d/'evolved.csv'; deterministic=d/'deterministic.json'
            subprocess.run([sys.executable, str(ROOT/'swarm/evolve.py'), str(puzzles), str(original), str(evolved), str(deterministic), '--generation','2', '--max-puzzles','2'], check=True, capture_output=True)
            final=d/'champion.csv'; rep=d/'report.json'
            subprocess.run([sys.executable, str(ROOT/'swarm/verify.py'), str(puzzles), str(evolved), str(d/'none.csv'), str(final), str(rep), '--original', str(original), '--deterministic-report', str(deterministic)], check=True, capture_output=True)
            data=json.loads(rep.read_text())
            self.assertEqual(data['run_start_score'], 5)
            self.assertEqual(data['new_score'], 3)
            self.assertEqual(data['total_instructions_saved_this_run'], 2)
            self.assertEqual(data['instructions_saved'], 0)  # no AI attempt, but true total is 2

if __name__ == '__main__':
    unittest.main()
