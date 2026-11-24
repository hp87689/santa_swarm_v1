# Santa Swarm v2.1.2 — OpenRouter reasoning-token fix

This is a **one-file AI patch**, not a full new swarm. Keep all your existing v2.1 project files and the 128,504 champion.

## What the generation 9 error proves

The free router selected `nvidia/nemotron-3.5-lightning:free` and consumed all 2,200 generated tokens in reasoning (`finish_reason=length`), leaving no final answer. The OpenRouter API key *was used*, but no mathematician proposal could be parsed and the programmer/critic stages did not run.

## Changes in this patch

- Chooses explicit zero-cost models instead of the unpredictable `openrouter/free` router: `google/gemma-4-31b-it:free` for mathematics and critique, `cohere/north-mini-code:free` for code.
- Requests `reasoning: {"enabled": false}`. Providers can still ignore the request; the patch logs what actually happened.
- Tries **at most one other free model per role** on empty/malformed responses or recoverable errors. Does **not retry** a 401/402/403/429 error, to avoid wasting the free quota.
- Rejects model names that aren't explicitly free, even if an environment override is supplied.
- Allows models to return JSON surrounded by a ` ```json ` code fence.
- Saves diagnostics in `logs/proposal.json` and `AI AGENTS:` with actual routed models, finish reasons, and token usage. No key is logged.

## Install (Windows / GitHub Desktop)

1. Extract this ZIP.
2. Open the `swarm` folder inside it and copy `agent_v2.py`.
3. Open your existing local GitHub repository folder (`Santa-Swarm-2026`) and enter its `swarm` subfolder.
4. Paste **only `agent_v2.py`**, choose **Replace the file**. Don't delete anything else.
5. In GitHub Desktop, **Commit to main** with message `Fix free OpenRouter reasoning exhaustion`, then **Push origin**.
6. GitHub website → **Actions** → **Santa Swarm — evolve and validate** → **Run workflow** on `main`.
7. Open the `Research full public abstracts/READMEs and run three AI agent roles` step. Copy the new `AI AGENTS:` line into ChatGPT.

### What we hope to see

`"status":"candidate_saved"` and `"stages":["mathematician","programmer","critic"]` indicates that all agent roles ran and generated code. It does **not** mean the code improved the champion; that still requires the independent validator's `OVERALL EVOLUTION` and `VALIDATED CHAMPION` logs.

If the primary model fails and fallback works, `api_calls` will contain both attempts. If all fail, the detailed error remains visible. The existing deterministic search and champion will still run.

## Testing / limitations

- Six new unit tests for fallback, refusal of paid models, reasoning setting, and quota-aware error handling passed locally, plus the existing 19 project tests.
- The patch was **not tested against your private OpenRouter account**, and no real Kaggle score reduction can be claimed until the next run.
- Explicit model availability, provider behavior, and free quotas may change. This is a reliability fix, not yet a genuine multi-island evolutionary algorithm.
