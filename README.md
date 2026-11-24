# Santa Swarm v2.1.4 — Fix for old tests

This patch corrects outdated test mocks after the OpenRouter live free-model discovery upgrade. It changes **only two test files**. It does not change the actual swarm optimizer, its OpenRouter configuration, the Kaggle data, or the champion submission.

## Why the workflow stopped

The older rate-limit tests assumed the first OpenRouter request would be a POST to `/chat/completions`. Version 2.1.4 makes an initial GET request to `/models` to find zero-priced models. Old test mocks fed a simulated 429 chat-completion error into that initial catalog request, so the tests failed with `model_catalog_http_429` before testing the intended retry logic.

The remaining older test expected the error text `api_error_code=429`, but the current code correctly classifies an embedded account-error response as `http_429:unknown` (non-retryable).

## Install on Windows

1. Download and **Extract All** of this ZIP.
2. Open the extracted `tests` folder and copy **both** `.py` files.
3. Open your existing Santa Swarm GitHub repository folder, then open its `tests` folder.
4. Paste and choose **Replace the files in the destination**.
5. In GitHub Desktop, commit the two changed tests and **Push origin**.
6. In GitHub Actions, run a **new** `Santa Swarm — evolve and validate` workflow run.

Do **not** delete any other files. Do **not** change `swarm/agent_v2.py`. Do **not** change either API key. These tests use simulated responses and cannot spend your API quota.

## Expected verification

`Ran 42 tests` followed by `OK` means all 42 local tests passed. The small `PUBLIC BOOTSTRAP: previous_score 6, new_score 5` is from a miniature offline test; **it is not your real Kaggle score**.

The next important status is `AI AGENTS:` later in the workflow. It must show whether a free model actually returned usable ideas and code. Only `OVERALL EVOLUTION:` (and Kaggle confirmation) can establish an actual competition score change.

## Test status

Verified locally with the original v2.1.4 `agent_v2.py` and all 42 original/current tests after replacing these two outdated tests: **42 tests pass, 0 failures, 0 errors**. No live OpenRouter calls or full Kaggle benchmark were performed.
