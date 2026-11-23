# Santa Swarm v1.1 — beginner setup

This is an **autonomous, budget-$0, experimental optimization loop**, not a fully developed elite multi-agent optimizer. It:

1. Downloads the official Santa 2026 puzzles with your private Kaggle token.
2. Restores its last best valid submission from a previous GitHub Actions artifact.
3. When the incumbent score exceeds 140,000, attempts to import published Apache-licensed public Kaggle notebook output CSVs and validates each shorter program independently.
4. Looks up public mathematical research metadata (Crossref and public GitHub repositories).
5. Asks one free OpenRouter model to write an optimization function.
6. Tests that untrusted model code in a disposable no-network Docker container.
7. Independently rechecks every improved puzzle with a trusted exact interpreter.
8. Saves the best validated program per puzzle into a downloadable, reusable artifact.

It does NOT publish credentials, upload Kaggle input datasets to the repository, guarantee improvements, submit to Kaggle automatically, or promise a winning score. Further algorithm development will be needed.

## Before you start

- Visit https://www.kaggle.com/competitions/santa-2026 and **Join** / accept the rules.
- Make sure your GitHub repository is **Public** for free standard GitHub Actions minutes.
- Create a new **Kaggle API token** at https://www.kaggle.com/settings/api (the `KAGGLE_API_TOKEN` method), and keep it private.
- Your existing OpenRouter API key can be used. In https://openrouter.ai/settings/keys make sure spending limits prevent any paid charges; this starter specifies only `openrouter/free`.

## Put this code on GitHub without command-line programming

1. Download and extract the provided ZIP file to a new Windows folder, e.g. `Documents/Santa-Swarm`.
2. Install the free GitHub Desktop app at https://desktop.github.com and sign in.
3. In GitHub Desktop choose **File > Add local repository**, select the extracted `santa_swarm_v1` folder. If asked to **create a repository here**, confirm.
4. In the lower-left corner, enter commit summary `Initial Santa Swarm`, click **Commit to main**.
5. Click **Publish repository**. Enter name `santa-swarm-2026` and **uncheck** `Keep this code private`.
6. Open your new repo in the browser; check that the file `.github/workflows/swarm.yml` exists.

## Add your two GitHub Actions secrets

In GitHub open the repo, then choose **Settings > Secrets and variables > Actions > New repository secret**.

Create:

- `KAGGLE_API_TOKEN` — the Kaggle token text you generated under the modern API section. NOT a GitHub token.
- `OPENROUTER_API_KEY` — your OpenRouter API key text.

**Never paste keys into source files, commit messages, GitHub Issues, or this chat.**

## Start the first run

1. In your repository click **Actions**.
2. Select **Santa Swarm — evolve and validate** in the left column.
3. Click **Run workflow** > **Run workflow**.
4. Open the newest run. All steps should show a green checkmark.
5. Expand **Independently validate and merge shorter programs**. It prints score and instructions saved.
6. Under the run's **Artifacts**, download `champion`. Its `champion.csv` is a validated complete submission you can upload manually to the competition.

The workflow also runs automatically four times daily. Each successful run can recover the champion from the latest successful run. Artifact retention is finite (7 days here); keep periodic personal backups.

## Download a Kaggle submission

On the Actions run page, download the `champion` artifact. Unzip it. Upload `champion.csv` at https://www.kaggle.com/competitions/santa-2026/submit using your account; watch submission caps.

## How to read the logs

- `previous_score`: exact baseline instructions.
- `new_score`: total instructions in the verified champion (lower is better).
- `instructions_saved`: improvement in that run.
- `puzzles_improved`: puzzles whose instruction count decreased.
- `invalid_candidates_rejected`: programs rejected by the independent validator.

An improvement of 0 is not a bug. LLM-generated mathematical code is experimental and often not useful. It will need more advanced algorithm families to approach top-tier Kaggle results.

## Troubleshooting

- **Missing Kaggle token / download failed**: check the secret name, Kaggle token status, and whether you joined/accepted competition rules.
- **No AI candidate**: check OpenRouter key and quota. The workflow should still produce a valid baseline when the agent cannot generate code.
- **Docker failure**: check the container step's logs. The trusted validation step should still preserve the last baseline.
- **No available artifact**: the run must complete successfully before the `champion` artifact is available.
- **Workflow does not show up in Actions**: ensure `.github/workflows/swarm.yml` was committed on the default branch.
- **Can't afford anything**: do not enable paid runners, larger GitHub runners, paid models or paid HF Spaces. Stop the workflow if services request billing details.

## Terms and ethics

Public repositories and standard GitHub-hosted runner usage are normally free, but GitHub restricts abuse and resource-intensive unrelated workloads. Keep the current schedule conservative. Program optimization is software development for this repository; do not convert this to nonstop background mining, or use extensions to bypass quotas. Check competition-specific rules on external data, team participation, publicly sharing results, and code licensing.

Links: https://docs.github.com/en/actions/concepts/billing-and-usage ; https://openrouter.ai/collections/free-models ; https://github.com/Kaggle/kaggle-cli ; https://huggingface.co/docs/hub/spaces-overview

## Reality check and next major upgrades

This starter has one AI coder, a lightweight public research-metadata collector, public notebook OUTPUT CSV bootstrapping, deterministic dead-code pruning, and per-puzzle survivor selection. That is a real autonomous code-experiment loop, **not yet the finished multi-island swarm**. For a serious winning attempt, the next implementation milestones are:

1. Validate the official Kaggle sample score, import strong *licensed* public notebook algorithms, and compare baseline portfolios.
2. Add multiple competing search families (factorization/dictionaries, beam search, backward synthesis, DAG rewriting, joint target planning, register allocation).
3. Add population/lineage management, per-family experiment arms, adversarial correctness tests, and hard per-puzzle compute budgets.
4. Upgrade the research broker from metadata-only to paper abstract/full-text retrieval where access and licensing permit; reuse discoveries rather than repeated downloads.
5. Add optional Kaggle notebook compute when the CPU-only GitHub workflow has been shown to work.

The official deadline listed for **entry** is January 21, 2027, and the **final submission** deadline is January 28, 2027 (11:59 PM UTC). These are different deadlines.

**Storage caution:** GitHub Free includes a 500 MB Actions artifact storage quota. We retain champions for seven days and research logs for three days. The workflow can recover recent artifacts after restarts, but back up your latest `champion.csv` personally and reduce retention if storage becomes tight.


## Upgrading from v1 to v1.1

See `UPGRADE_TO_V1_1.md`. In `research-and-logs`, look at `logs/bootstrap.json` for the public-reference improvement; the final `state/report.json` measures only further AI optimization after that bootstrap.
