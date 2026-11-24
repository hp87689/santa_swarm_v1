"""Goal-directed multi-output arithmetic resynthesis.

Rebuild short spans of register programs with 1..4 new instructions.
Goals consist of required target first-occurrences and the final register values
read by the unchanged suffix. This is a genuine local search; no public solutions
are imported by this module. Every accepted edit is independently replayed.

Design deliberately favors bounded search over exponential exhaustive expansion.
See docs/RESEARCH.md for relevant mathematical background.
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass
from heapq import nsmallest
from typing import Iterable

from core import replay, prune_dead_code
from resynthesis import compute_states_and_live


@dataclass(frozen=True)
class Plan:
    regs: tuple
    found: frozenset
    steps: tuple


def _compute(op, x, y, limit):
    if op == '+':
        z = x+y
    elif op == '-':
        z = x-y
    elif op == '*':
        z = x*y
    else:
        if y == 0 or x % y:
            return None
        z = x//y
    return z if 1 <= z <= limit else None


def _value_map(regs):
    values = {}
    for i, x in enumerate(regs):
        if x is not None and x not in values:
            values[x] = i
    return values


def _goal_recipes(regs, goal, limit, cap=18):
    """Produce all promising exact one-instruction expressions for a goal."""
    values = _value_map(regs)
    found = set()
    results = []
    for x, a in values.items():
        options = (
            ('+', a, values.get(goal-x)),
            ('-', a, values.get(x-goal)),
            ('-', values.get(goal+x), a),
            ('*', a, values.get(goal//x) if x and goal % x == 0 else None),
            ('/', a, values.get(x//goal) if goal and x % goal == 0 else None),
            ('/', values.get(goal*x) if goal*x <= limit else None, a),
        )
        for op, l, r in options:
            if l is None or r is None:
                continue
            recipe = (op, l, r)
            if recipe in found or _compute(op, regs[l], regs[r], limit) != goal:
                continue
            found.add(recipe)
            results.append(recipe)
            if len(results) >= cap:
                return results
    return results


def _inverse_values(regs, goals, limit):
    """Values that could create some outstanding goal in one further instruction."""
    inv = set()
    vals = _value_map(regs)
    for goal in goals:
        if not 1 <= goal <= limit:
            continue
        inv.add(goal)
        for x in vals:
            poss = (goal-x, goal+x, x-goal, goal*x)
            for v in poss:
                if 1 <= v <= limit:
                    inv.add(v)
            if x and goal % x == 0:
                inv.add(goal//x)
            if goal and x % goal == 0:
                inv.add(x//goal)
    return inv


def _helper_recipes(regs, missing_values, original_values, limit, cap=28, exploration=0, rng=None):
    """Generate novel helper computations, ranked by goal relevance.

    This is the search branch that allows new intermediates not present in the
    original instruction window. Its cost is O(k^2), k<=48 registers.
    """
    vals = _value_map(regs)
    if len(vals) > 40:
        # Keep representatives closest in log magnitude to outstanding goals;
        # always retain values appearing as original intermediate outputs.
        required = set(original_values) | set(missing_values)
        ranked = sorted(vals, key=lambda v: (v not in required,
                                min((abs(v.bit_length()-g.bit_length()) for g in missing_values), default=0), v))
        vals = {v: vals[v] for v in ranked[:40]}
    inv = _inverse_values(regs, missing_values, limit)
    existing = set(_value_map(regs))
    candidates = {}
    items = list(vals.items())
    # Operators have exact integer semantics. Repeating the same value doesn't
    # help produce a novel intermediate unless it creates a required goal.
    for xi, (x,a) in enumerate(items):
        for y,b in items[xi:]:
            pairs = [('+',a,b,x+y),('*',a,b,x*y)]
            if x>y:
                pairs.append(('-',a,b,x-y))
            elif y>x:
                pairs.append(('-',b,a,y-x))
            if y and x%y==0:
                pairs.append(('/',a,b,x//y))
            if x and y%x==0 and y != x:
                pairs.append(('/',b,a,y//x))
            for op, left, right, z in pairs:
                if z in existing or not 1 <= z <= limit:
                    continue
                if z in inv:
                    score = 0 if z in missing_values else 1
                elif z in original_values:
                    score = 2
                elif exploration:
                    score = 4+min((abs(z.bit_length()-g.bit_length()) for g in missing_values), default=0)
                else:
                    continue
                if z not in candidates or candidates[z][0] > score:
                    candidates[z] = (score,(op,left,right,z))
    records = list(candidates.values())
    if rng is not None and exploration:
        rng.shuffle(records)
    records.sort(key=lambda item:item[0])
    return [recipe for _,recipe in records[:cap]]


def _obligations(puzzle, program, states, live, mandatory, start, end):
    before, after = states[start], states[end]
    unchanged_live = {r for r in live[end] if before[r] == after[r]}
    changed_live = {r: after[r] for r in live[end] if before[r] != after[r]}
    targets = {v for v in mandatory[start:end] if v is not None}
    # A target already present at the beginning was necessarily hit earlier;
    # these would not normally appear in mandatory[] but be conservative.
    targets.difference_update(v for v in before if v is not None)
    return unchanged_live, changed_live, targets


def _destinations(before, protected, required_reg, width, rng):
    """Goal register destinations + safe disposable registers.

    A register required to remain unchanged by the suffix is never written.
    Other registers may be overwritten, but the final replay is authoritative.
    """
    scratch = [r for r,v in enumerate(before) if r not in protected and r not in required_reg and v is None]
    scratch += [r for r,v in enumerate(before) if r not in protected and r not in required_reg and v is not None]
    # Avoid unnecessarily clobbering seed/input values.
    scratch = scratch[:max(1,width)]
    return list(required_reg) + scratch


def _search_window(puzzle, program, states, live, mandatory, start, end, *,
                   beam_width=20, max_depth=4, helper_cap=20, seed=0, deadline=None,
                   exploration=0):
    before = states[start]
    protected, required_regs, must_hit = _obligations(puzzle, program, states, live, mandatory, start, end)
    original_len = end-start
    depth_limit = min(max_depth, original_len-1)
    if depth_limit < 1 or len(required_regs) > 3 or len(must_hit) > 3:
        return None, 0
    if not must_hit and not required_regs:
        return None, 0
    if len(must_hit | set(required_regs.values())) > depth_limit + 1:
        # Helper values can serve multiple goals but every distinct required
        # value must be produced at least once, unless present in 'before'.
        missing = (must_hit | set(required_regs.values())) - set(x for x in before if x is not None)
        if len(missing) > depth_limit:
            return None, 0
    original_values = {states[i+1][program[i][3]] for i in range(start,end)}
    rng = random.Random(seed)
    initial = Plan(tuple(before), frozenset(), tuple())
    frontier = [initial]
    seen = set()
    expansions = 0
    dests = _destinations(before, protected, required_regs, 4, rng)
    all_goals = must_hit | set(required_regs.values())
    if not dests:
        return None, 0

    for depth in range(1,depth_limit+1):
        if deadline and time.monotonic() >= deadline:
            break
        proposals = []
        for node in frontier:
            if deadline and time.monotonic() >= deadline:
                break
            reg = node.regs
            missing_regs = {r:v for r,v in required_regs.items() if reg[r] != v}
            missing_targets = must_hit - set(node.found)
            missing_values = missing_targets | set(missing_regs.values())
            # Don't generate a helper unless enough remaining instructions exist
            # to realize all required targets/outputs.
            moves = []
            for goal in sorted(missing_values):
                for op,a,b in _goal_recipes(reg,goal,puzzle.value_limit,cap=12):
                    if goal in missing_targets:
                        for d in dests:
                            if d not in protected and (d not in required_regs or required_regs[d] == goal):
                                moves.append((op,a,b,d,goal,False))
                    for d,v in missing_regs.items():
                        if v == goal and d not in protected:
                            moves.append((op,a,b,d,goal,False))
            if depth < depth_limit and missing_values:
                for op,a,b,goal in _helper_recipes(reg,missing_values,original_values,
                                puzzle.value_limit, cap=helper_cap,
                                exploration=exploration,rng=rng):
                    # Helpers are stored only in disposable registers. Avoid
                    # overwriting useful goal registers and allow later goals.
                    for d in dests:
                        if d not in required_regs and d not in protected:
                            moves.append((op,a,b,d,goal,True))
                            break
            # Reorder with a seeded variation, keeping goal-completing moves first.
            rng.shuffle(moves)
            moves.sort(key=lambda m: m[-1])
            for op,a,b,d,v,is_helper in moves[:max(30,beam_width*7)]:
                if deadline and time.monotonic() >= deadline:
                    break
                if op not in ('+','-','*','/') or reg[a] is None or reg[b] is None:
                    continue
                output = _compute(op,reg[a],reg[b],puzzle.value_limit)
                if output != v:
                    continue
                nxt = list(reg)
                nxt[d] = output
                # Existing required register must never be overwritten after it
                # is correct (prevents oscillation and spurious state blow-up).
                if d in required_regs and reg[d] == required_regs[d]:
                    continue
                if nxt == list(reg) and v not in missing_targets:
                    continue
                found = node.found | ({v} if v in must_hit else set())
                step = (op,a,b,d)
                history = node.steps+(step,)
                key = (tuple(nxt),found)
                if key in seen:
                    continue
                seen.add(key)
                expansions+=1
                if all(nxt[r]==v for r,v in required_regs.items()) and must_hit <= found:
                    candidate = program[:start]+[list(x) for x in history]+program[end:]
                    if len(candidate) >= len(program):
                        continue
                    try:
                        replay(puzzle,candidate)
                        trimmed = prune_dead_code(puzzle,candidate)
                        if len(trimmed) < len(program):
                            return trimmed, expansions
                    except (ValueError, TypeError, OverflowError, ZeroDivisionError):
                        pass
                remaining = must_hit-found
                wrong = sum(nxt[r] != v for r,v in required_regs.items())
                total = len(remaining)+wrong
                # Prioritize satisfied obligations, then closeness to one-step
                # future reachability, then shorter sequence/novelty diversity.
                reach = sum(bool(_goal_recipes(nxt,g,puzzle.value_limit,cap=1)) for g in
                            (remaining | set(v for r,v in required_regs.items() if nxt[r]!=v)))
                closeness = min((abs(v.bit_length()-g.bit_length()) for v in nxt if v is not None
                                 for g in missing_values),default=0)
                score = (total,-reach,closeness, rng.random())
                proposals.append((score, Plan(tuple(nxt),frozenset(found),history)))
        if not proposals:
            break
        frontier = [node for _,node in nsmallest(beam_width, proposals, key=lambda item:item[0])]
    return None, expansions


def improve_beam(puzzle, program, *, seed=0, max_seconds=2.5, max_windows=50,
                 window_size=11, max_depth=4, beam_width=16, helper_cap=20, exploration=0):
    """Timed stochastic local search. Returns a valid program and honest metrics."""
    started = time.monotonic()
    deadline = started + max_seconds
    best = prune_dead_code(puzzle,program)
    rng = random.Random(seed)
    windows_tested = 0
    expanded = 0
    accepted = 0
    while windows_tested < max_windows and time.monotonic() < deadline and len(best)>=3:
        states,live,mandatory=compute_states_and_live(puzzle,best)
        # Prefer windows containing multiple target creations; these are not
        # handled by the earlier 1/2-step resynthesis implementation.
        windows = []
        for end in range(3,len(best)+1):
            for width in range(3,min(end,window_size)+1):
                start = end-width
                n_targets = sum(1 for v in mandatory[start:end] if v is not None)
                priority = (-min(n_targets,3),-width,rng.random())
                windows.append((priority,start,end))
        rng.shuffle(windows)
        windows.sort(key=lambda x:x[0])
        improved = False
        for _,start,end in windows:
            if windows_tested>=max_windows or time.monotonic()>=deadline:
                break
            windows_tested+=1
            proposal,count=_search_window(puzzle,best,states,live,mandatory,start,end,
                                           beam_width=beam_width,max_depth=max_depth,
                                           helper_cap=helper_cap,seed=rng.getrandbits(32),
                                           deadline=deadline,exploration=exploration)
            expanded+=count
            if proposal is not None and len(proposal)<len(best):
                replay(puzzle,proposal)
                best=proposal
                accepted+=1
                improved=True
                break
        if not improved:
            break
    replay(puzzle,best)
    return best,{'windows_tested':windows_tested,'states_expanded':expanded,
                 'rewrites_accepted':accepted,'instructions_saved':len(program)-len(best),
                 'elapsed_seconds':round(time.monotonic()-started,3)}
