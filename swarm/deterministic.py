"""Trusted, bounded, register-aware arithmetic program improvement strategies.

Improvements are proposed, not assumed: every candidate is fully re-validated
with core.replay, which must NEVER be replaced by an LLM. Pure standard library.
"""
import random
from core import replay, prune_dead_code


def trace(puzzle, program):
    replay(puzzle, program)
    regs = [None] * puzzle.registers
    regs[:len(puzzle.seeds)] = puzzle.seeds
    before, after = [], []
    for op, a, b, d in program:
        before.append(tuple(regs))
        x, y = regs[a], regs[b]
        z = x + y if op == '+' else x - y if op == '-' else x*y if op == '*' else x//y
        regs[d] = z
        after.append(z)
    return before, after


def checked(puzzle, program, original_length):
    """A rejected candidate returns None rather than silently entering the population."""
    if len(program) >= original_length:
        return None
    try:
        replay(puzzle, program)
        trimmed = prune_dead_code(puzzle, program)
        if len(trimmed) < original_length:
            return trimmed
    except (ValueError, TypeError, OverflowError):
        return None
    return None


def pair_expressions(regs, target, value_limit):
    """Find 1-instruction recipes for a target from CURRENT live registers.

    Exact value arithmetic avoids a naive 48x48x4 search.
    """
    value_to_reg = {}
    for idx, val in enumerate(regs):
        if val is not None and val not in value_to_reg:
            value_to_reg[val] = idx
    seen = set()
    for x, a in value_to_reg.items():
        recipes = (
            ('+', a, value_to_reg.get(target - x)),
            ('-', a, value_to_reg.get(x - target)),
            ('-', value_to_reg.get(target + x), a),
            ('*', a, value_to_reg.get(target // x) if x and target % x == 0 else None),
            ('/', a, value_to_reg.get(x // target) if target and x % target == 0 else None),
            ('/', value_to_reg.get(target * x) if target * x <= value_limit else None, a),
        )
        for op, left, right in recipes:
            if left is None or right is None:
                continue
            rec = (op, left, right)
            if rec not in seen:
                seen.add(rec)
                yield rec


def pair_collapse(puzzle, program, rng, max_checks=60):
    """Attempt to synthesize two consecutive instructions as one.

    Operands must exist before the original two-instruction window. Each
    tentative rewrite is checked against the full puzzle, so target coverage,
    overwrites, positive values and exact division remain enforced.
    """
    if len(program) < 2:
        return None
    before, outputs = trace(puzzle, program)
    idx = list(range(len(program)-1))
    rng.shuffle(idx)
    # Prefer windows ending at target production, but do explore other windows.
    idx.sort(key=lambda i: outputs[i+1] not in puzzle.targets)
    checks = 0
    for i in idx:
        output = outputs[i+1]
        dest = program[i+1][3]
        for op, a, b in pair_expressions(before[i], output, puzzle.value_limit):
            candidate = program[:i] + [[op, a, b, dest]] + program[i+2:]
            checks += 1
            improved = checked(puzzle, candidate, len(program))
            if improved is not None:
                return improved
            if checks >= max_checks:
                return None
    return None


def value_forward(puzzle, program, rng, max_checks=70):
    """Remove recomputation when its result is already present elsewhere.

    Redirect consumers of the eliminated destination register to a register
    already holding the same value, until either register is overwritten.
    Reject every ambiguous case unless independent full replay passes.
    """
    if not program:
        return None
    before, outputs = trace(puzzle, program)
    idx = list(range(len(program)))
    rng.shuffle(idx)
    checks = 0
    for i in idx:
        d = program[i][3]
        equivalents = [r for r, v in enumerate(before[i]) if v == outputs[i]]
        rng.shuffle(equivalents)
        for alt in equivalents:
            candidate = [ins[:] for ins in program[:i]]
            alt_still_valid = True
            redirect = alt != d
            for orig in program[i+1:]:
                op, a, b, dest = orig
                if redirect:
                    # Sources are read BEFORE destination is updated.
                    if a == d: a = alt
                    if b == d: b = alt
                candidate.append([op, a, b, dest])
                if dest == d:
                    redirect = False
                elif redirect and dest == alt:
                    # Future reads of d might still exist; we let replay
                    # reject any incorrect result, but never redirect again.
                    redirect = False
                    alt_still_valid = False
                    break
            if not alt_still_valid:
                continue
            checks += 1
            improved = checked(puzzle, candidate, len(program))
            if improved is not None:
                return improved
            if checks >= max_checks:
                return None
    return None


def improve_one(puzzle, program, arm, seed, rounds=2):
    rng = random.Random(seed)
    best = prune_dead_code(puzzle, program)
    if arm == 'prune':
        return best
    optimizer = {'pair': pair_collapse, 'forward': value_forward}[arm]
    for _ in range(rounds):
        proposal = optimizer(puzzle, best, rng)
        if proposal is None or len(proposal) >= len(best):
            break
        best = proposal
    return best
