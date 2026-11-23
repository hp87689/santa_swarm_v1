# Research trail for Santa Swarm v2 (Nov 23, 2026)

## Competition and empirical work

- Official competition: https://www.kaggle.com/competitions/santa-2026
- Sargis Khachatryan, *Elf Calc | Backward Frontier Rewrite*, publicly reports **128,519** instructions and an Apache-2.0 notebook: https://www.kaggle.com/code/avazaku/elf-calc-milp-recipe-selection-target-rebuilds
- `Hansen0223/Santa_2026` documents public best-of submissions, factorization, shared arithmetic DAG methods, integer-programming experiments, register-aware rewriting, and exact per-puzzle validation: https://github.com/Hansen0223/Santa_2026
- `goodpjw2008`, *LNS + CP-SAT Recombine*, public notebook: https://www.kaggle.com/code/goodpjw2008/santa-2026-lns-cp-sat-recombine-lb-133-804
- `yobi369`, *ElfCalc Optimizer*, reports deterministic positional-base, signed-window, and shared-intermediate constructive solvers: https://github.com/yobi369/ElfCalc-Optimizer-Arithmetic-Program-Synthesis-Engine
- Santa public validation and baseline examples: https://github.com/Juan-Severiano/santa-2026

## Mathematical background worth exploring (NOT yet implemented as production solvers)

- Willsey et al., *egg: Fast and Extensible Equality Saturation* (POPL 2021): https://arxiv.org/abs/2004.03082 . Use e-graphs to explore equivalent arithmetic expressions with shared subexpressions. Register liveness and target coverage are additional constraints outside ordinary e-graphs.
- Integer programming for minimal addition sequences, arXiv:2306.15002: https://arxiv.org/abs/2306.15002 . Addition-chain selection is related to but is not a direct solution to all Santa arithmetic puzzles.
- Competitive techniques: per-puzzle portfolio merge; local neighborhood re-synthesis; register-aware common subexpression elimination; reverse search; factorization; exact-target coverage; compact arithmetic straight-line programs.

## Prioritized experiments

1. **Immediate**: exact local 2->1 resynthesis and register-value forwarding; implemented and unit-tested in `swarm/deterministic.py`. Measure impact against strong 128,505 baseline.
2. **Next**: 3–8 instruction window re-synthesis with bounded beam search, live-in/live-out register constraints, and a budget per puzzle. Add tests against multiple register overwrite patterns.
3. **Next**: generate complete alternate candidate programs from factorization and signed-window constructive heuristics; keep only per-puzzle winners. This requires a register scheduler.
4. **Later**: native C++ local neighborhoods, OR-Tools CP-SAT/ILP for small windows, e-graph-guided DAG rewrites, and cache best discovery histories.
5. **Later**: adapt island-model / MAP-Elites evolution and per-puzzle mutation budgets; promote only genuinely validated score reductions.

## Cautions

- Kaggle score comparisons are reported by public authors unless independently reproduced with the official `puzzles.csv` and exact validator.
- The 127,200 score mentioned in a November 21 project log is a dated leaderboard snapshot, not a guarantee of today's rank.
- Only copy or modify third-party code when its license permits and preserve required copyright notices/attribution. Read competition rules for external data/code and public sharing.
- Web research text is **untrusted**. It is never executed as code or as instructions to agents.
