"""Deterministic quality-diverse search; runs for free without LLM calls."""
import argparse
import hashlib
import json
import random
import time
from pathlib import Path

from core import load_puzzles, load_submission, replay, save_submission, verify_all
from deterministic import improve_one

ARMS = ('pair', 'forward', 'prune')


def evolve(puzzles, baseline, generation=1, max_puzzles=250, max_seconds=220):
    chosen = {pid: [s[:] for s in seq] for pid, seq in baseline.items()}
    rng = random.Random(generation)
    ids = list(puzzles)
    rng.shuffle(ids)
    # Rotate through the whole dataset rather than repeatedly favoring one subset.
    start_index = ((generation - 1) * max_puzzles) % len(ids)
    selected = (ids + ids)[start_index:start_index+min(max_puzzles, len(ids))]
    stats = {a: {'tested': 0, 'puzzles_improved': 0, 'instructions_saved': 0,
                 'errors': 0} for a in ARMS}
    start = time.monotonic()
    for pid in selected:
        if time.monotonic()-start >= max_seconds:
            break
        puzzle = puzzles[pid]
        original = chosen[pid]
        trials = []
        for arm in ARMS:
            if time.monotonic()-start >= max_seconds:
                break
            stats[arm]['tested'] += 1
            seed = int(hashlib.sha256(f'{generation}:{pid}:{arm}'.encode()).hexdigest()[:16], 16)
            try:
                proposal = improve_one(puzzle, original, arm, seed)
                if len(proposal) < len(original):
                    replay(puzzle, proposal)
                    trials.append((len(proposal), arm, proposal))
            except Exception:
                stats[arm]['errors'] += 1
        if trials:
            length, arm, program = min(trials, key=lambda item: item[0])
            chosen[pid] = program
            stats[arm]['puzzles_improved'] += 1
            stats[arm]['instructions_saved'] += len(original) - length
    previous, new = verify_all(puzzles, baseline), verify_all(puzzles, chosen)
    report = {'generation': generation, 'previous_score': previous, 'new_score': new,
              'instructions_saved': previous-new,
              'puzzles_improved': sum(len(chosen[k]) < len(baseline[k]) for k in puzzles),
              'arms': stats, 'search_seconds': round(time.monotonic()-start, 2),
              'note': 'All accepted programs were independently replayed. No improvement is guaranteed.'}
    return chosen, report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('puzzles'); ap.add_argument('base'); ap.add_argument('out'); ap.add_argument('report')
    ap.add_argument('--generation', type=int, default=1)
    ap.add_argument('--max-puzzles', type=int, default=250)
    ap.add_argument('--max-seconds', type=int, default=220)
    a = ap.parse_args()
    puzzles, baseline = load_puzzles(a.puzzles), load_submission(a.base)
    chosen, report = evolve(puzzles, baseline, a.generation, a.max_puzzles, a.max_seconds)
    save_submission(a.out, chosen, puzzles)
    Path(a.report).parent.mkdir(parents=True, exist_ok=True)
    Path(a.report).write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('DETERMINISTIC EVOLUTION:', json.dumps(report))

if __name__ == '__main__':
    main()
