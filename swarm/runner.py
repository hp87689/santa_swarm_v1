"""Runs ONLY inside sandbox, with no credentials or network."""
import argparse
import hashlib
import importlib.util
import random
import signal
from pathlib import Path

from core import load_puzzles, load_submission, prune_dead_code, replay, save_submission


def timed_out(_signum, _frame):
    raise TimeoutError("candidate timed out")


def load_agent(filename):
    if not Path(filename).is_file():
        return None
    spec = importlib.util.spec_from_file_location("candidate", filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, "optimize")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("puzzles")
    parser.add_argument("baseline")
    parser.add_argument("candidate")
    parser.add_argument("output")
    parser.add_argument("--generation", type=int, default=1)
    parser.add_argument("--per-puzzle-seconds", type=float, default=0.45)
    args = parser.parse_args()
    puzzles = load_puzzles(args.puzzles)
    baseline = load_submission(args.baseline)
    optimizer = None
    try:
        optimizer = load_agent(args.candidate)
    except Exception as e:
        print("Candidate could not load:", str(e)[:100])
    chosen = {}
    improvements = 0
    signal.signal(signal.SIGALRM, timed_out)
    for pid, p in puzzles.items():
        original = baseline[pid]
        best = prune_dead_code(p, original)
        if optimizer:
            signal.setitimer(signal.ITIMER_REAL, max(0.05, min(args.per_puzzle_seconds, 2.0)))
            try:
                seed = int(hashlib.sha256(f"{pid}:{args.generation}".encode()).hexdigest()[:12], 16)
                data = {"id": pid, "seeds": list(p.seeds), "targets": list(p.targets),
                        "value_limit": p.value_limit, "registers": p.registers}
                attempt = optimizer(data, [i[:] for i in best], random.Random(seed))
                if attempt is not None and len(attempt) < len(best):
                    replay(p, attempt)
                    best = attempt
            except (Exception, KeyboardInterrupt) as e:
                pass
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
        if len(best) < len(original):
            improvements += 1
        chosen[pid] = best
    save_submission(args.output, chosen, puzzles)
    print(f"Sandbox attempted improvements on {improvements}/{len(puzzles)} puzzles")


if __name__ == "__main__":
    main()
