# Santa Swarm 2026 — v2: Research + Evolution

**Cost target: $0.** This is a *working but experimental* multi-strategy evolution loop, not a guaranteed winning solver. It is intended to upgrade your **validated 128,505-instruction champion** without starting over. Never discard your champion backup.

## What changed from v1.1

- The existing **independent verifier** (`swarm/core.py`) remains unchanged. Every proposed shorter program must survive exact arithmetic replay.
- Three local algorithm families compete **without consuming any OpenRouter requests**:
  - `pair`: resynthesize two adjacent instructions with one existing-register arithmetic instruction.
  - `forward`: eliminate duplicated values and redirect later uses to another live register when safe.
  - `prune`: backwards register-aware dead-code elimination.
- Each run explores up to 250 puzzles and records **per-strategy results** in `logs/deterministic.json`.
- A real research collector reads bounded excerpts from **public research GitHub READMEs and arXiv abstracts**, rather than title metadata alone. It does NOT download every paper PDF or automatically execute copied code. See `docs/RESEARCH.md`.
- The AI now has three roles (mathematician, coder, critic) executed sequentially using `openrouter/free`, up to three calls per run. It writes a bounded `candidate.py` optimizer, which is tested in a no-network container. The critic is advisory; the verifier alone decides validity.
- Saved `state/agent_history.json` remembers recent AI attempts between runs. Logs distinguish deterministic improvements from AI improvements.
- Previous `champion` GitHub Actions artifact is still restored, so the starting score should remain **128,505 or lower** if that artifact is available.
- Public output imports are attempted on manual runs and periodically, even when your champion is already strong. Only shorter programs that pass the exact validator are admitted.

**Not yet implemented:** full multi-island populations, CP-SAT/MILP mathematical search, e-graph equality saturation, performance-optimized C++ LNS, automatic paper-to-implementation synthesis, and Kaggle leaderboard submission. These are research milestones, not hidden v2 features.

## Beginner-friendly upgrade (Windows + GitHub Desktop)

1. On GitHub, open **Actions** → latest successful **Santa Swarm — evolve and validate** run. Download the `champion` artifact to your PC and keep a backup of `champion.csv` somewhere safe.
2. Download this v2 ZIP. Windows: right click → **Extract All**.
3. Open the extracted `santa_swarm_v2` folder, select all the files and folders **inside** it (including the `.github` folder) and **copy them into the same local GitHub repository folder you have used for v1.1**. When Windows asks, choose **Replace the files in the destination**. **DO NOT delete the existing `.git` folder** or rename your GitHub repository. There is no reason to recreate your API secrets.
4. Open **GitHub Desktop** → select your existing Santa Swarm repository → **Changes**. Verify it lists updated/new files. Enter commit summary `Upgrade Santa Swarm to v2` → **Commit to main** → **Push origin**.
5. Open your GitHub repository in the browser → **Actions** → **Santa Swarm — evolve and validate** → **Run workflow** → `main` → **Run workflow**.
6. Open that run. Expand **Evolve deterministic algorithms (no AI quota used)** and **Independently verify every improvement and preserve champion**. The first shows what the algorithm families did; the second shows the additional AI outcome.
7. Download artifacts after it succeeds. `champion` contains `champion.csv`, `report.json`, and `agent_history.json`. `research-and-logs` contains `logs/deterministic.json`, `logs/research.json`, `logs/proposal.json`, `logs/bootstrap.json` and `scratch/sandbox.log` when available.

**NOTE:** Never upload your `KAGGLE_API_TOKEN` or `OPENROUTER_API_KEY` to GitHub as plain source files or paste them into ChatGPT. The previous repository secrets remain valid.

## What scores will mean

- **Public bootstrap** (`logs/bootstrap.json`): change from imported public notebooks (if accessible). This may be zero.
- **Deterministic evolution** (`logs/deterministic.json`): score before and after `pair`, `forward`, and `prune` search.
- **AI evolution** (`state/report.json`): score before and after the model-generated `candidate.py` was attempted.
- **Overall improvement**: compare the current `state/report.json` new score to your original saved baseline (128,505). Do not confuse individual stage reports with total per-run progress.

Zero instructions saved is possible for strong starting solutions; the system must NEVER report invented progress.

## Free cloud limits and reliability

- Current public GitHub **standard hosted runners** are normally free, but GitHub enforces acceptable-use rules, job length caps, storage and retention limits. This workflow runs 4 times/day in short restartable jobs. It is *not* a permanent cloud server.
- OpenRouter `openrouter/free` is rate-limited (currently 50/day without purchased credits, subject to change). At most 3 calls per run × 4 runs = 12 possible calls/day for this workflow, leaving room for retries/manual runs. OpenRouter model routing may be unavailable temporarily.
- Champion artifacts are retained for 7 days. If successful runs stop, your champion may expire; keep local backups. If restoration fails, the official sample would be used as the fallback. Always verify **previous_score** before trusting a new run.
- Public GitHub code becomes visible to everyone. Do not commit Kaggle credentials, imported competition puzzle data, or tokens.

## Research and competition rules

The research broker fetches READMEs and arXiv abstracts as **untrusted data**. The AI cannot execute source text or browse arbitrary websites in the sandbox. Code from external projects can be incorporated only under compatible licenses/attribution and Kaggle rules. The package itself copies no third-party optimizer source. See `docs/RESEARCH.md` for public links and proposed future solver families.

## Local self-tests (optional)

Run: `python -m unittest discover -s tests -v`. There are no third-party Python dependencies for trusted logic. CI automatically runs this step before downloading the Kaggle data.

## If the next run fails

- `Missing KAGGLE_API_TOKEN`: make sure your **GitHub Actions secret** still exists, then rerun the **new** workflow.
- `No AI candidate`: OpenRouter may be unavailable or the free quota exceeded; deterministic evolution should still run and save the valid previous champion.
- `No previous champion`: your existing successful run's artifact must still be downloadable; otherwise keep your backup and ask for restore steps instead of accepting the sample baseline.
- `No improvements`: inspect `logs/deterministic.json` and `logs/proposal.json`; this indicates a hard local optimum or limited search, not necessarily a software error.

No automatic submissions are made on your behalf. Submit a validated `champion.csv` manually on Kaggle when appropriate and within competition submission limits.

## Additional source retrieval

On manual runs and approximately every fourth scheduled run, the workflow also downloads public Kaggle notebook **source** (`kaggle kernels pull`) for two known notebooks. This code is treated as untrusted research data and never executed. The research digest excerpts these files when available, alongside fetched READMEs and arXiv abstracts. The workflow remains functional if a notebook cannot be downloaded.

After verification, `swarm/feedback.py` records whether the last AI-generated candidate actually saved instructions. This evidence is loaded into the next agent's reasoning so it can avoid repeating unsuccessful approaches.
