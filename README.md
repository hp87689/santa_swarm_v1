# Santa Optimizer — one AI call instead of a swarm

This patch changes **only** `.github/workflows/swarm.yml`. It is designed for the Santa Swarm v2.2.2 project. It does not change your mathematical optimizer, API key, data, or champion.

## What happens
- Four scheduled GitHub Actions cycles a day, as before; all four run deterministic mathematical search.
- OpenRouter is attempted only on the 01:17 UTC daily scheduled cycle (GitHub may delay it).
- The AI step sets `SANTA_AGENT_MODE=direct` (one research+coding response, optional one fallback model). Multi-agent mode is **not** used.
- Manual Run workflow has a checkbox **run_ai**, default off. Tick it when you intentionally want to test the AI.
- If no `candidate.py` is generated, the networkless AI code sandbox is skipped; the verifier still preserves the best valid solution.
- Experiment history is not overwritten with a new score when no AI was attempted.

## Install using Windows / GitHub Desktop
1. Extract this ZIP.
2. Show hidden folders in File Explorer (View > Show > Hidden items).
3. Open the patch folder `.github` > `workflows`, and copy **swarm.yml**.
4. Paste it into your current Santa Swarm project `.github` > `workflows`, and choose **Replace**.
5. In GitHub Desktop, commit as `Schedule one AI call per day; optimize without AI otherwise`, then **Push origin**.
6. Open GitHub Actions > **Santa Swarm — evolve and validate** > **Run workflow**.
7. For a free mathematical-only run, leave **run_ai** unchecked. To test the AI once, tick **run_ai**.

Your existing `OPENROUTER_API_KEY` remains in GitHub Secrets and is only exposed to the optional AI step. Do not share your key.

## Results
- `OVERALL EVOLUTION:` is the actual submission progress on every cycle.
- `AI AGENTS:` appears only when the optional AI step ran.
- `AI SKIPPED:` is expected and means **zero OpenRouter requests were attempted** on that run.

## Honest limits
A previous `upstream_provider_shared_pool` 429 came from congestion at the free model provider, not necessarily from your own request volume. Fewer calls reduce waste but cannot guarantee free model capacity. v2.2.2 already uses a single-call agent by default; this patch primarily reduces how **often** it is called. This patch does not guarantee a Kaggle score improvement.
