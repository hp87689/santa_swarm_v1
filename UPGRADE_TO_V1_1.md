# Santa Swarm v1.1 — public-solution bootstrap

**Purpose:** Fix the main weakness in v1: it repeatedly optimized the official 1,490,379-instruction sample instead of importing strong public reference programs.

This is a *targeted bootstrap upgrade*, not yet a multi-agent evolutionary solver.

## What changed

- Before invoking the research/coding agent, the GitHub workflow uses the Kaggle CLI to request output files from two published Apache-2.0 Kaggle notebooks when its current saved score is above 140,000.
- It searches those outputs for a complete `id,program` CSV, validates every shorter puzzle program with the trusted local interpreter, and merges only valid improvements.
- It records the initial score, resulting score, files found and contributions in `logs/bootstrap.json`.
- If access or outputs fail, it **does not** invent a score or crash: it keeps the prior best solution and explains what happened in logs.
- The `six` Kaggle dependency fix is included.

## Installation with GitHub Desktop on Windows

1. Make a backup of your current project directory and download your latest **champion** GitHub Actions artifact (important).
2. Extract this ZIP. Open `santa_swarm_v1_1` and copy **all contents** into your existing `santa_swarm_v1` project folder. Replace files when Windows prompts.
3. Open GitHub Desktop and select the existing repository `santa-swarm-2026`.
4. Enter commit message `Bootstrap from public Kaggle notebooks`, then **Commit to main** and **Push origin**.
5. Open GitHub → Actions → **Santa Swarm — evolve and validate** → **Run workflow** on `main`.
6. Expand **Bootstrap from Apache-licensed public Kaggle notebook outputs**. Look for `PUBLIC BOOTSTRAP:`. The score displayed here is the imported public portfolio improvement.
7. Download `research-and-logs` artifact and check `logs/bootstrap.json`. If `new_score` remains around 1.49 million, the public notebook download may have failed, or the notebook outputs may not contain a usable complete CSV. Send those log messages for diagnosis.

**No additional API keys are needed**, and no public notebook code is executed: only output CSVs are parsed and independently validated. Open-source licensing and Kaggle competition rules should still be reviewed before submissions that reuse public artifacts.

## Public reference notebooks

- https://www.kaggle.com/code/avazaku/elf-calc-milp-recipe-selection-target-rebuilds — public notebook page reports 128,519 (Apache 2.0); availability of downloadable complete CSV has not been verified from inside this project.
- https://www.kaggle.com/code/pardheev/132-219-best-public-score-santa-2026 — public notebook page reports 132,141 (Apache 2.0); availability of downloadable complete CSV has not been verified from inside this project.

**Important:** Reported notebook scores are *not* guaranteed as results of this patch. Only an observed `logs/bootstrap.json` score plus our exact replay constitutes a locally validated result. The Kaggle website must still accept any actual submission.

**Note on logs:** The final `state/report.json` now describes only the *post-bootstrap AI optimizer* pass. Look at `logs/bootstrap.json` to see the large sample-to-public improvement.
