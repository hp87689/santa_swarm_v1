# Santa Swarm v2.1 — Mathematical Resynthesis (experimental)

**Goal: improve the code-generated programs beyond an already strong 128,504-instruction champion.**

This is an **experimental upgrade**, not a verified new Kaggle record. The new optimizer has passed synthetic tests but has **not yet been run against your actual Kaggle data or 128,504 champion** in this environment. It may find 0 improvements on a strong solution. Any claim of progress requires the independent validator's `OVERALL EVOLUTION` report.

## Why v2 got stuck

- The old deterministic code only pruned dead code, redirected duplicate values, or collapsed 2 instructions to 1.
- These shallow patterns are often already eliminated from strong public baselines.
- `previous_score == new_score` in `VALIDATED CHAMPION` measures the AI stage alone. Always inspect `OVERALL EVOLUTION` and `logs/deterministic.json`.
- Previous AI candidate code was not preserved as a source-code parent; it was regenerated from scratch each run.

## New in v2.1

1. **New arithmetic window resynthesizer, written for this project** (`swarm/resynthesis.py`):
   - Replay the program and compute register liveness and first required target occurrences.
   - Find windows of **3–10 instructions** and reason about the register and target values that must survive their replacement.
   - Construct one- or two-instruction replacements using *new intermediate arithmetic values*, not just instructions already in the candidate.
   - Try two-output recipes when a window has two required register values.
   - Verify every proposed change with the independent `core.replay()` and prune only after validation.
2. **New bounded driver** (`swarm/resynth_driver.py`): samples up to 80 puzzles per run, spends at most 4 seconds on each, and records searches and savings in `logs/resynthesis.json`.
3. **AI source-code heredity**: the latest AI-generated optimizer is retained as `state/last_candidate.py` in the GitHub champion artifact, then used as an untrusted parent for the next model-generated mutation. This is actual code evolution, although a useful mutation is not guaranteed.
4. **No repeated public-output imports once a champion exists**. Public notebook material may still be read for research. Kaggle public outputs are only an initial recovery/bootstrap if your champion artifact is lost.
5. Separate reporting for deterministic cleanup, arithmetic resynthesis and AI-generated optimizer. Exact validator remains independent.

Not yet included: exact CP-SAT, 3–8 instruction **multi-output** search, C++ large-neighborhood optimization, equality-saturation e-graphs, full multi-island evolving populations, or an automated Kaggle submission. Those require further engineering and real-data evaluation.

## Install on Windows using GitHub Desktop

1. **First back up the existing champion.** On GitHub open **Actions → latest successful Santa Swarm workflow → Artifacts → champion**, download and save its `champion.csv` somewhere outside your repository.
2. Download this ZIP and Windows right-click → **Extract All**.
3. Open the resulting `santa_swarm_v2_1` folder. **Copy the files INSIDE it** into your existing local `Santa-Swarm-2026` GitHub repository folder. Choose *Replace files in destination* when prompted. **Do not delete the `.git` directory**, do not delete your repository, and do not overwrite/delete existing GitHub secrets.
4. GitHub Desktop → **Changes** → commit `Add arithmetic resynthesis v2.1` → **Push origin**.
5. On GitHub: **Actions → Santa Swarm — evolve and validate → Run workflow → main → Run workflow**. Use a *new workflow run*, not “Re-run jobs” on an old one.
6. Open the successful run and locate the step **Genuine arithmetic window resynthesis**. It prints `GENUINE RESYNTHESIS: {...}`.
7. Also inspect **Independently verify every improvement** for `OVERALL EVOLUTION: {...}`. This is the entire run's score change.
8. Under **Artifacts → research-and-logs**, download `logs/resynthesis.json` and `logs/proposal.json` for troubleshooting. Do not send API keys.

## What success or failure looks like

The new research search reports:

```json
{
  "method":"bounded_arithmetic_resynthesis",
  "puzzles_attempted":80,
  "puzzles_improved":0,
  "windows_tested":40000,
  "instructions_saved":0,
  "previous_score":128504,
  "new_score":128504
}
```

**Example only.** `windows_tested > 0` and `instructions_saved = 0` means it really searched but found no accepted shorter program; that is not a bug by itself. `windows_tested = 0` or `errors > 0` means we should inspect diagnostics. The `OVERALL EVOLUTION` log tells us the net improvement, if any, across the entire workflow.

## Runtime / zero-cost limits

- GitHub Actions uses short scheduled jobs, not a permanent free virtual server. The workflow runs four times daily; GitHub may delay schedules or enforce appropriate-use limits.
- OpenRouter is optional for the deterministic optimizer. The three-stage AI research calls may fail due to free-model availability or quotas without preventing mathematically validated deterministic searches.
- **All LLM code remains untrusted** and runs only in a networkless Docker sandbox, without API credentials. Trusted host code never imports it. The retained AI source is only fed to the next generation as text.
- GitHub artifacts expire (7 days for champion); periodically back up your champion locally.

## Local verification and tests

`python -m unittest discover -s tests -v`

19 local tests passed on creation, including independent target checking, exact integer semantics, and a miniature original 3-instruction → 2-instruction arithmetic synthesis example. This is **not** a benchmark of your actual 128,504 Kaggle champion.

## Research ideas used

The approach is inspired by the mathematical concept of straight-line program resynthesis and public accounts of register-aware local search, not by copying competitors' finished submissions. The project's new optimizer code is independently written. For further reading:

- [Kaggle Santa 2026 rules and data](https://www.kaggle.com/competitions/santa-2026)
- [Hansen0223/Santa_2026 research repository](https://github.com/Hansen0223/Santa_2026)
- [Juan-Severiano/santa-2026 on Rust LNS and graph cut experiments](https://github.com/Juan-Severiano/santa-2026)
- [egg: Fast and Extensible Equality Saturation](https://arxiv.org/abs/2004.03082)

Do not represent imported public scores as discoveries made by this swarm.
