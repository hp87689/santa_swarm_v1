import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'swarm'))
from core import Puzzle, replay, prune_dead_code
from deterministic import pair_collapse, value_forward, improve_one
from evolve import evolve


class TestEvolutionarySearch(unittest.TestCase):
    def test_pair_collapse(self):
        puzzle = Puzzle('p', (2, 3, 5), (10,), 100, 48)
        # 2+3=5; 5+5=10. The initial 5 seed makes the first step unnecessary
        # only AFTER changing the dependent second instruction.
        program = [['+', 0, 1, 3], ['+', 3, 3, 4]]
        self.assertEqual(len(prune_dead_code(puzzle, program)), 2)
        out = pair_collapse(puzzle, program, random.Random(42))
        self.assertIsNotNone(out)
        self.assertEqual(replay(puzzle, out), 1)

    def test_value_forward(self):
        puzzle = Puzzle('p', (2, 3), (5, 10), 100, 48)
        program = [['+', 0, 1, 2], ['+', 0, 1, 3], ['+', 3, 3, 4]]
        self.assertEqual(len(prune_dead_code(puzzle, program)), 3)
        out = value_forward(puzzle, program, random.Random(99))
        self.assertIsNotNone(out)
        self.assertEqual(replay(puzzle, out), 2)

    def test_never_accept_invalid_rewrite(self):
        puzzle = Puzzle('p', (2, 3), (5, 10), 100, 48)
        program = [['+', 0, 1, 2], ['+', 2, 2, 3]]
        for arm in ('pair', 'forward', 'prune'):
            result = improve_one(puzzle, program, arm, 91)
            self.assertEqual(replay(puzzle, result), len(result))
            self.assertLessEqual(len(result), len(program))

    def test_evolve_portfolio_improves_with_valid_output(self):
        puzzles = {
            'p1': Puzzle('p1', (2, 3, 5), (10,), 100, 48),
            'p2': Puzzle('p2', (2, 3), (5, 10), 100, 48),
        }
        before = {
            'p1': [['+', 0, 1, 3], ['+', 3, 3, 4]],
            'p2': [['+', 0, 1, 2], ['+', 0, 1, 3], ['+', 3, 3, 4]],
        }
        chosen, report = evolve(puzzles, before, generation=4, max_puzzles=2, max_seconds=3)
        self.assertEqual(report['previous_score'], 5)
        self.assertLessEqual(report['new_score'], 3)
        self.assertEqual(sum(replay(p, chosen[pid]) for pid, p in puzzles.items()), report['new_score'])

if __name__ == '__main__':
    unittest.main()
