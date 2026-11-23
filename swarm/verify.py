"""TRUSTED host-side evaluator; never execute or import candidate.py."""
import argparse
import json
from pathlib import Path

from core import load_puzzles, load_submission, replay, save_submission, verify_all


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("puzzles")
    parser.add_argument("baseline")
    parser.add_argument("attempt")
    parser.add_argument("champion")
    parser.add_argument("report")
    parser.add_argument("--original", help="Champion before any public/deterministic improvements this run")
    parser.add_argument("--bootstrap-report")
    parser.add_argument("--deterministic-report")
    args = parser.parse_args()
    puzzles = load_puzzles(args.puzzles)
    baseline = load_submission(args.baseline)
    before = verify_all(puzzles, baseline)
    try:
        attempts = load_submission(args.attempt)
        if set(attempts) != set(puzzles):
            raise ValueError("Candidate submission has wrong ID set")
    except Exception as e:
        print("No usable candidate submission:", str(e)[:180])
        attempts = {}
    combined = dict(baseline)
    improved = 0
    rejected = 0
    for pid, puzzle in puzzles.items():
        attempt = attempts.get(pid)
        if attempt is None or len(attempt) >= len(combined[pid]):
            continue
        try:
            replay(puzzle, attempt)
        except Exception:
            rejected += 1
            continue
        combined[pid] = attempt
        improved += 1
    after = verify_all(puzzles, combined)
    assert after <= before
    save_submission(args.champion, combined, puzzles)
    report = {"previous_score": before, "new_score": after, "instructions_saved": before - after,
              "puzzles_improved": improved, "invalid_candidates_rejected": rejected,
              "puzzle_count": len(puzzles)}
    if args.original:
        initial = load_submission(args.original)
        initial_score = verify_all(puzzles, initial)
        report['run_start_score'] = initial_score
        report['total_instructions_saved_this_run'] = initial_score - after
        report['total_puzzles_improved_this_run'] = sum(
            len(combined[pid]) < len(initial[pid]) for pid in puzzles)
        print('OVERALL EVOLUTION:', json.dumps({
            'run_start_score': initial_score, 'final_score': after,
            'total_instructions_saved_this_run': initial_score-after,
            'total_puzzles_improved_this_run': report['total_puzzles_improved_this_run']}))
    for key, source in [('public_bootstrap', args.bootstrap_report),
                        ('deterministic_evolution', args.deterministic_report)]:
        if source and Path(source).exists():
            try:
                stage = json.loads(Path(source).read_text())
                report[key] = {'instructions_saved': stage.get('instructions_saved', 0),
                               'puzzles_improved': stage.get('puzzles_improved', 0)}
            except (ValueError, OSError):
                pass
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("VALIDATED CHAMPION:", json.dumps(report))


if __name__ == "__main__":
    main()
