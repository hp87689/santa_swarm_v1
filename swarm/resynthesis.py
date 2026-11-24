"""Register-aware bounded arithmetic *resynthesis* (not merely dead code pruning).

Given a contiguous window from a valid program, discover cheaper arithmetic programs
that produce the same externally required register values/first target occurrences.
Every candidate is independently checked by core.replay before it can be accepted.

This implementation deliberately uses only Python's standard library. It considers
one- and two-instruction arithmetic identities, including multiplication, exact
division, and intermediate values not found anywhere in the parent program.
It explores windows of 3-10+ instructions and can delete several steps at once.
"""
from math import isqrt
import random
import time

from core import prune_dead_code, replay


def compute_states_and_live(puzzle, program):
    replay(puzzle, program)
    registers = [None] * puzzle.registers
    registers[:len(puzzle.seeds)] = puzzle.seeds
    states = [tuple(registers)]
    first_targets = set(puzzle.seeds) & set(puzzle.targets)
    mandatory = [None] * len(program)
    targets = set(puzzle.targets)
    for idx, (op, a, b, d) in enumerate(program):
        x, y = registers[a], registers[b]
        v = x+y if op == '+' else x-y if op == '-' else x*y if op == '*' else x//y
        registers[d] = v
        states.append(tuple(registers))
        if v in targets and v not in first_targets:
            mandatory[idx] = v
            first_targets.add(v)
    live = [set() for _ in range(len(program)+1)]
    for i in range(len(program)-1, -1, -1):
        _, a, b, d = program[i]
        live[i] = (live[i+1] - {d}) | {a, b}
    return states, live, mandatory


def recipes_one(registers, target, limit, cap=3):
    """Fast inverse lookup for every exact one-step recipe for target."""
    if target < 1 or target > limit:
        return []
    by_value = {}
    for r, v in enumerate(registers):
        if v is not None and v not in by_value:
            by_value[v] = r
    matches, seen = [], set()
    for x, a in by_value.items():
        for op, left, right in (
            ('+', a, by_value.get(target-x)),
            ('-', a, by_value.get(x-target)),
            ('-', by_value.get(target+x), a),
            ('*', a, by_value.get(target//x) if x and target % x == 0 else None),
            ('/', a, by_value.get(x//target) if target and x % target == 0 else None),
            ('/', by_value.get(target*x) if target*x <= limit else None, a),
        ):
            if left is None or right is None:
                continue
            recipe = (op, left, right)
            if recipe not in seen:
                seen.add(recipe)
                matches.append(recipe)
                if len(matches) >= cap:
                    return matches
    return matches


def inverse_intermediates(regs, target, limit, cap=300):
    """Candidate y values satisfying f(y, x)==target for some live x."""
    by_value = {}
    for r, value in enumerate(regs):
        if value is not None and value not in by_value:
            by_value[value] = r
    pairs, seen = [], set()
    for x, r in by_value.items():
        values = [target-x, target+x, x-target]
        if x and target % x == 0:
            values.append(target//x)
        if target*x <= limit:
            values.append(target*x)
        if target and x % target == 0:
            values.append(x//target)
        variants = [('+', target-x), ('-', target+x), ('-', x-target),
                    ('*', target//x if x and target % x == 0 else -1),
                    ('/', target*x if target*x <= limit else -1),
                    ('/', x//target if target and x % target == 0 else -1)]
        for op, y in variants:
            if not 1 <= y <= limit:
                continue
            tag = (op, y, r)
            if tag not in seen:
                seen.add(tag)
                pairs.append(tag)
                if len(pairs) >= cap:
                    return pairs
    # Both operands can be the newly constructed intermediate.
    for op, v in [('+', target//2 if target % 2 == 0 else -1),
                  ('*', isqrt(target))]:
        if op == '*' and v*v != target:
            continue
        if 1 <= v <= limit:
            pairs.append((op, v, None))
    return pairs


def two_step_recipes(regs, target, dest, forbidden_scratch, limit, max_trials=90):
    """Synthesizes y=f(a,b); target=g(y,x). Uses safe temporary register."""
    writable = [r for r in range(len(regs)) if r not in forbidden_scratch]
    if dest not in forbidden_scratch:
        writable.sort(key=lambda r: r != dest)
    attempts = 0
    for last_op, intermediate, x_reg in inverse_intermediates(regs, target, limit):
        firsts = recipes_one(regs, intermediate, limit, cap=2)
        if not firsts:
            continue
        for first_op, a, b in firsts:
            for temp in writable:
                # If using an existing x in the last step, don't destroy it first.
                if x_reg is not None and temp == x_reg:
                    continue
                first = [first_op, a, b, temp]
                if x_reg is None:
                    second = [last_op, temp, temp, dest]
                elif last_op == '+':
                    second = ['+', temp, x_reg, dest]
                elif last_op == '*':
                    second = ['*', temp, x_reg, dest]
                elif last_op == '-':
                    # y-x == target vs x-y == target
                    second = ['-', temp, x_reg, dest] if intermediate == target + regs[x_reg] else ['-', x_reg, temp, dest]
                else:
                    # y/x == target vs x/y == target
                    second = ['/', temp, x_reg, dest] if intermediate == target*regs[x_reg] else ['/', x_reg, temp, dest]
                attempts += 1
                yield [first, second]
                if attempts >= max_trials:
                    return


def attempt_replacement(puzzle, program, start, end, replacement, best_length):
    if len(program) - (end - start) + len(replacement) >= best_length:
        return None
    candidate = program[:start] + replacement + program[end:]
    try:
        replay(puzzle, candidate)
        reduced = prune_dead_code(puzzle, candidate)
        if len(reduced) < best_length:
            return reduced
    except (ValueError, TypeError, OverflowError, ZeroDivisionError):
        return None
    return None


def rewrite_window(puzzle, program, states, live, mandatory, start, end, max_trials=75):
    """Resynthesize a window from the state before it and obligations after it."""
    before, after = states[start], states[end]
    required_reg = {r: after[r] for r in live[end] if before[r] != after[r]}
    targets_in_window = {v for v in mandatory[start:end] if v is not None}
    changed = len(required_reg)
    length = end-start
    if length < 3 or changed > 2 or len(targets_in_window) > 2:
        return None
    # Need more than 2 instructions saved to be useful; limit replacement to <=2 ops.
    if changed == 1 and len(targets_in_window) <= 1:
        dest, target = next(iter(required_reg.items()))
        if targets_in_window and target not in targets_in_window:
            return None
        # goal register is overwritten at end; other live registers must remain unchanged.
        scratch_forbidden = live[end] - {dest}
        for op, a, b in recipes_one(before, target, puzzle.value_limit, cap=8):
            solution = attempt_replacement(puzzle, program, start, end, [[op, a, b, dest]], len(program))
            if solution is not None:
                return solution
        for repl in two_step_recipes(before, target, dest, scratch_forbidden, puzzle.value_limit, max_trials=max_trials):
            solution = attempt_replacement(puzzle, program, start, end, repl, len(program))
            if solution is not None:
                return solution
    elif changed == 0 and len(targets_in_window) == 1:
        target = next(iter(targets_in_window))
        # Any dead scratch register can hold the target, since the suffix does not read it.
        dsts = [r for r in range(puzzle.registers) if r not in live[end]]
        if not dsts:
            return None
        for dest in dsts[:4]:
            for op, a, b in recipes_one(before, target, puzzle.value_limit, cap=5):
                result = attempt_replacement(puzzle, program, start, end, [[op,a,b,dest]], len(program))
                if result is not None:
                    return result
            for repl in two_step_recipes(before, target, dest, live[end], puzzle.value_limit, max_trials=max_trials//4):
                result = attempt_replacement(puzzle, program, start, end, repl, len(program))
                if result is not None:
                    return result
    elif changed == 2 and all(t in required_reg.values() for t in targets_in_window):
        # Multi-output replacement: each goal is one exact operation. Try both orders.
        destinations = list(required_reg)
        for first_d, second_d in (destinations, destinations[::-1]):
            first_t, second_t = required_reg[first_d], required_reg[second_d]
            for op1, a1, b1 in recipes_one(before, first_t, puzzle.value_limit, cap=8):
                middle = list(before)
                middle[first_d] = first_t
                for op2, a2, b2 in recipes_one(middle, second_t, puzzle.value_limit, cap=8):
                    cand = [[op1,a1,b1,first_d],[op2,a2,b2,second_d]]
                    result = attempt_replacement(puzzle, program, start, end, cand, len(program))
                    if result is not None:
                        return result
    return None


def improve_resynthesis(puzzle, program, seed=0, width=9, max_windows=500, max_seconds=8.0):
    """Search many windows. Can find replacements with new intermediate values.

    Returns (best_program, diagnostics) and validates independently.
    """
    rng = random.Random(seed)
    best = prune_dead_code(puzzle, program)
    deadline = time.monotonic() + max_seconds
    total_windows = 0
    accepted = 0
    while time.monotonic() < deadline and total_windows < max_windows:
        states, live, mandatory = compute_states_and_live(puzzle, best)
        if len(best) < 3:
            break
        ends = list(range(3, len(best)+1))
        rng.shuffle(ends)
        ends.sort(key=lambda idx: mandatory[idx-1] is None)
        changed = False
        for end in ends:
            if time.monotonic() >= deadline or total_windows >= max_windows:
                break
            widths = list(range(3, min(width, end)+1))
            rng.shuffle(widths)
            # Prefer long windows, because they can save more operations.
            widths.sort(reverse=True)
            for w in widths:
                if time.monotonic() >= deadline or total_windows >= max_windows:
                    break
                total_windows += 1
                proposal = rewrite_window(puzzle, best, states, live, mandatory, end-w, end)
                if proposal is not None and len(proposal) < len(best):
                    best = proposal
                    accepted += 1
                    changed = True
                    break
            if changed:
                break
        if not changed:
            break
    replay(puzzle, best)
    return best, {'windows_tested':total_windows,'rewrites_accepted':accepted,
                  'instructions_saved':len(program)-len(best)}
