"""Run register-aware mathematical resynthesis, preserve per-puzzle champions."""
import argparse
import hashlib
import json
import random
import time
from pathlib import Path

from core import load_puzzles, load_submission, replay, save_submission, verify_all
from resynthesis import improve_resynthesis


def run(puzzles, baseline, generation, max_seconds, max_puzzles, seconds_per_puzzle, width, windows):
    rng = random.Random(generation)
    names = list(puzzles)
    # Every generation gets a reproducible, rotating, random population sample.
    rng.shuffle(names)
    sample_size = max(1, min(max_puzzles, len(names)))
    offset = (generation * sample_size) % len(names)
    selected = [names[(offset+i) % len(names)] for i in range(sample_size)]
    best = {name: [op[:] for op in seq] for name, seq in baseline.items()}
    started = time.monotonic()
    stats = {'generation': generation, 'method':'bounded_arithmetic_resynthesis',
             'puzzles_attempted':0, 'puzzles_improved':0, 'windows_tested':0,
             'rewrites_accepted':0, 'total_instructions_saved':0,
             'errors':0, 'puzzle_improvements':[], 'error_examples':[]}
    for pid in selected:
        left = max_seconds - (time.monotonic() - started)
        if left < 0.02:
            break
        stats['puzzles_attempted'] += 1
        puzzle = puzzles[pid]
        original = best[pid]
        seed = int(hashlib.sha256(f'{pid}:{generation}:resynthesis'.encode()).hexdigest()[:14], 16)
        try:
            candidate, info = improve_resynthesis(
                puzzle, original, seed=seed, width=width, max_windows=windows,
                max_seconds=min(seconds_per_puzzle, left))
            stats['windows_tested'] += info['windows_tested']
            stats['rewrites_accepted'] += info['rewrites_accepted']
            if len(candidate) < len(original):
                replay(puzzle, candidate)
                best[pid] = candidate
                stats['puzzles_improved'] += 1
                reduction = len(original) - len(candidate)
                stats['total_instructions_saved'] += reduction
                stats['puzzle_improvements'].append({'id':pid, 'saved':reduction})
        except Exception as exc:
            stats['errors'] += 1
            if len(stats['error_examples']) < 4:
                stats['error_examples'].append(f'{pid}: {type(exc).__name__}: {str(exc)[:90]}')
    stats['previous_score'] = verify_all(puzzles, baseline)
    stats['new_score'] = verify_all(puzzles, best)
    stats['instructions_saved'] = stats['previous_score'] - stats['new_score']
    stats['elapsed_seconds'] = round(time.monotonic() - started, 2)
    assert stats['instructions_saved'] == stats['total_instructions_saved']
    return best, stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('puzzles'); ap.add_argument('baseline'); ap.add_argument('output'); ap.add_argument('report')
    ap.add_argument('--generation', type=int, default=1)
    ap.add_argument('--max-seconds', type=float, default=360)
    ap.add_argument('--max-puzzles', type=int, default=80)
    ap.add_argument('--seconds-per-puzzle', type=float, default=4)
    ap.add_argument('--width', type=int, default=10)
    ap.add_argument('--windows', type=int, default=500)
    args = ap.parse_args()
    puzzles = load_puzzles(args.puzzles)
    baseline = load_submission(args.baseline)
    best, stats = run(puzzles, baseline, args.generation, args.max_seconds,
                      args.max_puzzles, args.seconds_per_puzzle, args.width, args.windows)
    save_submission(args.output, best, puzzles)
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(json.dumps(stats, indent=2))
    print('GENUINE RESYNTHESIS:', json.dumps(stats))

if __name__ == '__main__':
    main()
