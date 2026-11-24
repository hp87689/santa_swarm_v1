# Santa Swarm v2.1.4 — Live free-model selection

**Purpose:** Repair the failed AI stage from generation 12 (`429` upstream Gemma; `404` Cohere fallback) without altering the arithmetic solver or losing the 128,504 champion.

## Changes
- Reads OpenRouter's current `GET /api/v1/models` catalog once per GitHub run.
- Filters models to `:free` entries with **zero prompt, completion, and request prices**, a text input/output modality, and a `/api/v1/chat/completions` endpoint.
- Ranks those models for mathematical reasoning/coding; avoids reasoning-heavy names when possible. This is heuristic only; a listing does not guarantee immediate provider capacity.
- Chooses two distinct free models (at most two inference attempts per role). Upstream-provider 429, model 404, provider 502/503/504, or empty content can trigger a fallback. Account-level daily/minute 429, authentication, and payment errors stop immediately.
- A `200 OK` response containing an API error is also handled.
- Logs the eligible model count and attempted model IDs but not your API key or raw server body.
- Model overrides (`OPENROUTER_MODEL`, `OPENROUTER_FALLBACK_MODEL`) are honored only if the live catalog confirms they're eligible free models. You don't need to configure them.

## Install on Windows
1. Save a backup of the latest `champion.csv` if you haven't already.
2. Extract this ZIP.
3. Copy **only** `swarm/agent_v2.py` into your existing Santa-Swarm-2026 GitHub project folder's `swarm` directory, selecting **Replace**.
4. Do not delete any other files or the hidden `.git` directory.
5. GitHub Desktop: **Commit to main** (e.g. `Use live OpenRouter free-model catalog`) and **Push origin**.
6. GitHub: **Actions** > **Santa Swarm — evolve and validate** > **Run workflow**.
7. Expand the `python swarm/agent_v2.py` step and copy the line starting `AI AGENTS:`. Check whether `stages` now contains `mathematician`, `programmer`, and `critic`.

## What this does not promise
- No paid model will be called by this module, but availability and success cannot be guaranteed for free endpoints.
- It is an API reliability fix, **not** a more powerful arithmetic optimizer. `candidate_saved` means the AI generated code, not that Kaggle score improved. Verify `OVERALL EVOLUTION` separately.
- A `404` may indicate model removal **or** data-policy/provider restrictions; if all attempts return 404, review your OpenRouter model/provider access and privacy settings rather than rotating keys.
- This module has no access to your OpenRouter token during offline testing; live integration must be verified in your GitHub workflow.

## Tests
The complete local v2.1 solver test suite plus routing tests passed: 29 total.

For the complete test suite, integrate `tests/test_live_model_routing.py` into the project and run `python -m unittest discover -s tests -p 'test_*.py'`. The tests are optional for a one-file install.
