import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "swarm"))
from core import Puzzle, replay, prune_dead_code


class TestCore(unittest.TestCase):
    def setUp(self):
        self.p = Puzzle("test", (1,), (4, 5), 1000, 48)

    def test_valid(self):
        p = [["+", 0, 0, 1], ["+", 1, 1, 2], ["+", 2, 0, 3]]
        self.assertEqual(replay(self.p, p), 3)

    def test_dead_code(self):
        p = [["+", 0, 0, 1], ["+", 1, 1, 2], ["+", 2, 0, 3], ["+", 1, 1, 4]]
        r = prune_dead_code(self.p, p)
        self.assertEqual(len(r), 3)
        self.assertEqual(replay(self.p, r), 3)

    def test_exact_division(self):
        p = Puzzle("test", (2, 3), (2,), 100, 48)
        with self.assertRaises(ValueError):
            replay(p, [["/", 1, 0, 2]])

    def test_overwrite_and_original_sources(self):
        p = Puzzle("test", (1,), (4,), 10, 48)
        self.assertEqual(replay(p, [["+", 0, 0, 0], ["+", 0, 0, 0]]), 2)

    def test_missing_target_rejected(self):
        with self.assertRaises(ValueError):
            replay(self.p, [["+", 0, 0, 1]])

    def test_zero_rejected(self):
        p = Puzzle("test", (1,), (1,), 100, 48)
        with self.assertRaises(ValueError):
            replay(p, [["-", 0, 0, 1]])


if __name__ == "__main__":
    unittest.main()
