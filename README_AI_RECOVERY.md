# Santa Swarm v2.2.1 — OpenRouter Recovery + Champion-Aware AI

This is a targeted AI integration patch for **Santa Swarm v2.2**. It does not replace the trusted puzzle validator, solver, GitHub Actions workflow, or your saved champion.

## What was wrong

Generation 15 used `baidu/ernie-5.5-flash-preview:free`. The provider responded HTTP 400. The old code immediately stopped without trying the other free models. It also added `temperature`, `reasoning`, and a system message, which aren't supported by every free inference provider. Its requests didn't show the AI any actual programs from your currently accepted champion.

## What this patch changes

- Uses **minimal OpenRouter chat request**: `model`, one `user` message, and `max_tokens`. No optional reasoning/temperature/system-role settings.
- If a selected free model returns HTTP 400, 404, 502/503/504, provider-upstream 429, empty final output, or invalid candidate code, tries **one other independently selected free model**. Account quota, payment, or authentication errors stop without spending more calls.
- Uses current live catalog evidence to select ONLY zero-price `:free` text-chat models, or OpenRouter's documented `openrouter/free` fallback when the catalog offers no eligible candidate.
- Prioritizes general-purpose math and coding free models rather than alphabetically choosing a provider that previously failed.
- Caps request output-token budgets using each model's advertised limit where available.
- Allows JSON-wrapped or fenced Python source, and performs trusted AST shape checks before saving `candidate.py`.
- Provides the Mathematician with a small actual sample from the current `data/puzzles.csv` and `state/base.csv`, in addition to prior failed experiments and academic snippets.
- Records safe error categories (`parameter_unsupported`, `context_or_token_limit`, etc.) and the model used **without logging raw prompts or API keys**.

## Install on Windows / GitHub Desktop

1. Extract this ZIP.
2. Copy **`swarm/agent_v2.py`** into your repository's existing **`swarm`** folder; select **Replace**.
3. Copy **`tests/test_openrouter_recovery_221.py`** into the existing repository's **`tests`** folder; do not delete other tests.
4. Open **GitHub Desktop**. Commit: `Fix OpenRouter 400 fallback and champion-aware AI`.
5. Click **Push origin**.
6. On GitHub, go to **Actions → Santa Swarm — evolve and validate → Run workflow**. Use a NEW workflow run, not Re-run of the old commit.
7. In the run's `Research full public abstracts/READMEs and run three AI agent roles` step, check the line beginning `AI AGENTS:`.

## How to interpret the next log

- `candidate_saved` + `stages=[mathematician,programmer,critic]`: all three completed; candidate still requires sandbox validation and an actual score reduction.
- `candidate_saved` + `stages=[mathematician,programmer]`: executable candidate saved, but Critic failed. Independent validator still decides if it counts.
- `status=no_candidate` + `http_400:...`: both free model candidates failed; look in `api_calls` for *bad_request_category* and model names.
- `http_429:free_daily_limit`: stop, because this is an account allowance limit, not a bug.
- `instructions_saved=0`: generated code may have run correctly but failed to beat current strong baseline. Do not infer failure solely from green GitHub checks.

## Tested

64 offline/local tests passed, including 9 new tests for: HTTP 400 fallback, minimal request payloads, private-key redaction, tokenizer budget, invalid code fallback, account key failure, embedded 400, real champion example and mocked 3-agent lifecycle. There was no live OpenRouter API call and no claim of improved Kaggle score.

## Safety & cost

Only free models are selected. Maximum **two chat attempts per role**; the whole cycle can still consume up to six requests when failures occur. Each scheduled run should count against the account's daily allowance. AI code still goes to the existing networkless Docker sandbox. Do not make the repository's API key public.
