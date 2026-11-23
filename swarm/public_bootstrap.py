"""Bootstrap from publicly shared competition notebook *output CSVs*.

Downloaded CSVs are untrusted: their content is never executed; each chosen
program is replayed by the independent local interpreter before merging.
"""
import argparse
import csv
import json
from pathlib import Path
from core import load_puzzles, load_submission, replay, save_submission, verify_all

MAX_CSV_BYTES = 150 * 1024 * 1024


def is_submission_csv(path):
    try:
        if path.stat().st_size > MAX_CSV_BYTES:
            return False
        with path.open(encoding="utf-8-sig", newline="") as f:
            return next(csv.reader(f), None) == ["id", "program"]
    except (OSError, UnicodeError, csv.Error):
        return False


def merge_public(puzzles_path, base_path, public_dir, output_path, report_path):
    puzzles = load_puzzles(puzzles_path)
    incumbent = load_submission(base_path)
    before = verify_all(puzzles, incumbent)
    report = {"previous_score": before, "new_score": before,
              "instructions_saved": 0, "puzzles_improved": 0, "sources": []}
    chosen = dict(incumbent)
    root = Path(public_dir)
    candidates = sorted(root.rglob("*.csv")) if root.is_dir() else []
    for source in candidates:
        if not is_submission_csv(source):
            continue
        entry = {"file": str(source), "improved_puzzles": 0,
                 "instructions_saved": 0, "rejected_puzzles": 0}
        try:
            submitted = load_submission(source)
            if set(submitted) != set(puzzles):
                raise ValueError("Submission does not contain exactly the scored IDs")
        except Exception as error:
            entry["status"] = "unusable_file"
            entry["reason"] = str(error)[:160]
            report["sources"].append(entry)
            continue
        for pid, puzzle in puzzles.items():
            new = submitted[pid]
            old = chosen[pid]
            if len(new) >= len(old):
                continue
            try:
                replay(puzzle, new)
            except Exception:
                entry["rejected_puzzles"] += 1
                continue
            chosen[pid] = new
            entry["improved_puzzles"] += 1
            entry["instructions_saved"] += len(old) - len(new)
        entry["status"] = "checked"
        report["sources"].append(entry)
    after = verify_all(puzzles, chosen)
    save_submission(output_path, chosen, puzzles)
    report["new_score"] = after
    report["instructions_saved"] = before - after
    report["puzzles_improved"] = sum(len(chosen[p]) < len(incumbent[p]) for p in puzzles)
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    Path(report_path).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("PUBLIC BOOTSTRAP:", json.dumps(report))
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("needs", "merge"))
    parser.add_argument("--puzzles", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--public", default="data/public")
    parser.add_argument("--output", default="state/public_base.csv")
    parser.add_argument("--report", default="logs/bootstrap.json")
    parser.add_argument("--threshold", type=int, default=140000)
    args = parser.parse_args()
    if args.operation == "needs":
        score = verify_all(load_puzzles(args.puzzles), load_submission(args.base))
        print(f"Current champion: {score}; public bootstrap threshold: {args.threshold}")
        raise SystemExit(0 if score > args.threshold else 1)
    merge_public(args.puzzles, args.base, args.public, args.output, args.report)


if __name__ == "__main__":
    main()
