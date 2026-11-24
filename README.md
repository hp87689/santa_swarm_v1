# Santa Swarm v2.2 — Multi-target Evolutionary Search

This is an **experimental zero-cost, restartable optimizer** for Kaggle Santa 2026. It is not a promise of winning, and no actual score improvement below your 128,504-instruction champion has yet been measured on your private Kaggle run.

## Important first: protect the champion

Before installing, in GitHub go to **Actions → most recent successful run → Artifacts → champion**. Download and save `champion.csv` somewhere outside your GitHub repository. Never delete `.git`, `.github`, `state/champion.csv` if you have it, or your GitHub Actions secrets.

## What is new in v2.2?

1. `swarm/beam_resynthesis.py`: a **new target-directed beam search** for arithmetic subprograms. Unlike older local rewriting, it can replace a window that must generate **up to three distinct target values** and preserve up to three changed, suffix-live register outputs. It synthesizes intermediate arithmetic values, preserves register states required later, and uses exact integer replay. Each proposed rewrite must **strictly reduce instruction count** and pass the unchanged independent validator.
2. `swarm/portfolio_v22.py`: a population of different search *configurations* (beam widths, depths, window widths, helper exploration, legacy search). It selects strategies using an exploration/exploitation score, records actual instructions saved, and mutates strategy parameters every other generation. This is evolution of search policies, not a trained LLM or proof of globally optimal arithmetic programs.
3. `state/evolution_memory.json` persisted in the `champion` artifact across cloud restarts. The archive remembers **which strategy actually worked** and evolves future variants. Do not delete the artifact if you want to retain that memory.
4. New workflow step **Evolve mathematical search strategies and optimize shared targets**. The optimization requires **zero AI calls**, so it keeps running even when OpenRouter free models are unavailable. Existing AI and research stages are retained unchanged from v2.1.5.
5. `logs/portfolio.json` and `EVOLUTIONARY PORTFOLIO:` diagnostics report tested windows, expanded search states, accepted candidates, valid improvement counts, previous score and new score. `OVERALL EVOLUTION:` remains the authoritative entire-run score.

### Honest testing status

**55 local unit tests passed.** New test puzzle with seeds `[2,3,5]` and targets `[10,12,15]` was reduced from **4 instructions to 3** by genuinely different arithmetic. A second run proved it does not regress the champion. Tests also check suffix preservation, valid divisions, tight register limits, and saved strategy memory.

The optimizer **has not yet been benchmarked on the full 1,000 competition puzzles with your current champion**. It is entirely possible it will save zero instructions on such an advanced baseline. Its success or failure must be measured from the next workflow's `EVOLUTIONARY PORTFOLIO` and `OVERALL EVOLUTION` lines, not from the miniature test scores.

## Beginner-friendly upgrade

1. Back up your latest `champion.csv` as explained above.
2. Download `Santa_Swarm_v2_2_MultiTarget_Evolution.zip`, right-click and select **Extract All**.
3. Open the extracted `santa_swarm_v2_2` folder. Select **everything inside it**, including the `.github` directory. In Windows File Explorer choose **View → Show → Hidden items** if necessary.
4. Copy those files into your **existing local GitHub repository folder** (your working Santa Swarm folder). Choose **Replace files in destination** if asked. Do not delete the repository folder; do not delete its hidden `.git` directory; **do not create a nested folder**.
5. Open GitHub Desktop; in **Changes**, inspect that the two new files (`beam_resynthesis.py`, `portfolio_v22.py`) and workflow are present. Commit with message `Add multi-target evolutionary optimizer v2.2`; click **Push origin**.
6. On GitHub go to **Actions → Santa Swarm — evolve and validate → Run workflow** and run the `main` branch. Do not rerun a job from an older commit.
7. In the successful run open the step **Evolve mathematical search strategies and optimize shared targets**. Look for `EVOLUTIONARY PORTFOLIO:`. Also expand **Independently verify every improvement and preserve champion** and look for `OVERALL EVOLUTION:`.
8. Send those **two log lines**, not your API keys. If either step fails, provide the last 15–20 lines of its error log.

## Existing OpenRouter integration

The package includes v2.1.5 `swarm/agent_v2.py` unchanged. It continues to attempt zero-priced models only. The AI stage may still fail because of free-tier capacity; **this does not block the deterministic mathematical search**. As before, generated AI code executes in a network-disabled, credential-free container. No API key is stored in this ZIP.

## Limits and future priorities

- **Search quality:** useful for bounded multi-output repairs, not yet global arithmetic DAG resynthesis or exact CP-SAT search.
- **Optimization time:** this workflow adds up to 190 seconds per scheduled run for 70 puzzles with at most ~1.2 seconds per strategy attempt. No guaranteed savings.
- **Persistence:** artifacts now retained 30 days rather than 7. GitHub Actions artifacts are not an eternal database: download occasional backups, and keep track of free service limits and applicable terms.
- **Cost:** no paid models, no paid compute requested. Public-repository Actions usage remains subject to GitHub acceptable-use rules and runner limits.
- **Score:** the old public baseline is used only if no valid retained champion exists; no public-submission import is performed when a champion is restored.

### Research used for design (inspiration, not copied competition submissions)

- [Kaggle Santa 2026 Competition](https://www.kaggle.com/competitions/santa-2026)
- [eSLIM: Circuit Minimization with SAT-Based Local Improvement](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.SAT.2024.23)
- [Towards a library for straight-line programs](https://www.texmacs.org/joris/slp/slp.html)
- [Santa 2026 Backward Frontier Rewrite](https://www.kaggle.com/code/avazaku/elf-calc-shared-helpers-chain-resynthesis)
- [Juan-Severiano Santa 2026 experimental approaches](https://github.com/Juan-Severiano/santa-2026)

### Development check

`python -m unittest discover -s tests -v`

Local benchmark: `PYTHONPATH=swarm python -m unittest tests/test_multi_target_portfolio_v22.py -v` (or run full discovery).
