"""Independent Santa 2026 Elf Calculator reader, interpreter, and optimizer.

This module must never be replaced by model-generated code.
"""
import csv
import json
from dataclasses import dataclass
from pathlib import Path

MAX_STEPS = 4096
MAX_BYTES = 131072


@dataclass(frozen=True)
class Puzzle:
    id: str
    seeds: tuple[int, ...]
    targets: tuple[int, ...]
    value_limit: int
    registers: int


def load_puzzles(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError("Puzzle file is empty")
    puzzles = {}
    for row in rows:
        p = Puzzle(
            id=row["id"],
            seeds=tuple(json.loads(row["starting_values"])),
            targets=tuple(json.loads(row["targets"])),
            value_limit=int(row["value_limit"]),
            registers=int(row["registers"]),
        )
        if p.id in puzzles or not 1 <= p.registers <= 48:
            raise ValueError(f"Invalid puzzle ID or register count: {p.id}")
        if not p.seeds or len(p.seeds) > p.registers or not p.targets:
            raise ValueError(f"Bad seeds/targets: {p.id}")
        if not 1 <= p.value_limit <= 10**18:
            raise ValueError(f"Bad value limit: {p.id}")
        if any(type(v) is not int or v < 1 or v > p.value_limit for v in p.seeds + p.targets):
            raise ValueError(f"Out-of-range starting/target value: {p.id}")
        puzzles[p.id] = p
    return puzzles


def parse_program(raw):
    if len(raw.encode("utf-8")) > MAX_BYTES:
        raise ValueError("Program cell exceeds 128 KiB")
    obj = json.loads(raw)
    if type(obj) is not list or len(obj) > MAX_STEPS:
        raise ValueError("Program has wrong shape or exceeds 4096 instructions")
    return obj


def load_submission(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, strict=True)
        if next(reader, None) != ["id", "program"]:
            raise ValueError(f"Unexpected submission header: {path}")
        result = {}
        for line in reader:
            if len(line) != 2 or line[0] in result:
                raise ValueError("Malformed/duplicate submission row")
            result[line[0]] = parse_program(line[1])
    return result


def save_submission(path, programs, puzzles):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if set(programs) != set(puzzles):
        raise ValueError("Submission must contain precisely the scored IDs")
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "program"])
        for pid in puzzles:
            writer.writerow([pid, json.dumps(programs[pid], separators=(",", ":"))])


def replay(puzzle, program, trace=False):
    """Return outputs by step. Raise for ANY invalid step/target/limit."""
    if type(program) is not list or len(program) > MAX_STEPS:
        raise ValueError("Invalid instruction count")
    raw = json.dumps(program, separators=(",", ":"))
    if len(raw.encode("utf-8")) > MAX_BYTES:
        raise ValueError("Program exceeds 128 KiB")
    regs = [None] * puzzle.registers
    regs[: len(puzzle.seeds)] = puzzle.seeds
    missing = set(puzzle.targets) - set(puzzle.seeds)
    outputs = []
    for i, ins in enumerate(program):
        if type(ins) is not list or len(ins) != 4:
            raise ValueError(f"Step {i}: instruction must be a four-element list")
        op, a, b, dest = ins
        if type(op) is not str or op not in ("+", "-", "*", "/"):
            raise ValueError(f"Step {i}: illegal operation")
        if any(type(v) is not int or not 0 <= v < puzzle.registers for v in (a, b, dest)):
            raise ValueError(f"Step {i}: illegal register")
        x, y = regs[a], regs[b]
        if x is None or y is None:
            raise ValueError(f"Step {i}: undefined source register")
        if op == "+":
            v = x + y
        elif op == "-":
            v = x - y
        elif op == "*":
            v = x * y
        else:
            if y == 0 or x % y:
                raise ValueError(f"Step {i}: division is not exact")
            v = x // y
        if not 1 <= v <= puzzle.value_limit:
            raise ValueError(f"Step {i}: nonpositive or value exceeds limit")
        regs[dest] = v
        missing.discard(v)
        if trace:
            outputs.append(v)
    if missing:
        raise ValueError(f"Missing {len(missing)} targets; example {min(missing)}")
    return outputs if trace else len(program)


def verify_all(puzzles, programs):
    if set(puzzles) != set(programs):
        raise ValueError("Puzzle/submission ID mismatch")
    return sum(replay(p, programs[pid]) for pid, p in puzzles.items())


def prune_dead_code(puzzle, program):
    """Delete steps with no effect on the first occurrence of any required target.

    Standard backward register-liveness pass; true semantics checked by replay.
    """
    outputs = replay(puzzle, program, trace=True)
    missing = set(puzzle.targets) - set(puzzle.seeds)
    mandatory = set()
    for i, v in enumerate(outputs):
        if v in missing:
            mandatory.add(i)
            missing.remove(v)
    live = set()
    retain = [False] * len(program)
    for i in range(len(program) - 1, -1, -1):
        _, a, b, d = program[i]
        if i in mandatory or d in live:
            retain[i] = True
            live.discard(d)
            live.add(a)
            live.add(b)
    candidate = [ins for i, ins in enumerate(program) if retain[i]]
    replay(puzzle, candidate)
    return candidate
