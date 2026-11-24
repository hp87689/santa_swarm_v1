# Santa Swarm v2.1.3 — Smart OpenRouter 429 handler

**One-file patch.** Keep your existing Santa Swarm project and current `champion.csv`; do not reinstall or delete anything. This patch does not import other people's solutions or change your mathematical optimizer.

## What it changes

Previous code treated every HTTP 429 exactly alike and immediately gave up. The new patch reads OpenRouter's `error.metadata.limit_source` and reports one of:

- `http_429:free_daily_limit`: your *account's* daily free-request quota is exhausted. Stop; a new API key from the same OpenRouter account won't help. Let the limit reset. Do not retry.
- `http_429:free_minute_limit`: your account's free requests/minute cap was reached. Retry in a future workflow after the limit resets; do not immediately retry.
- `http_429:upstream_provider_shared_pool`: the current free model's provider has insufficient capacity; try **one other `:free` model**.
- `http_429:unknown`: server didn't supply enough information to classify the limit; stop, rather than burning quota.

The patch also recognizes the provider's common “rate-limited upstream” message when metadata is unavailable. It preserves your `OPENROUTER_API_KEY` GitHub secret and excludes key contents from logs. It NEVER falls back to paid OpenRouter models.

## Install (Windows)

1. Download and extract the ZIP.
2. Copy the file `swarm/agent_v2.py` from this ZIP.
3. In the Santa Swarm GitHub project on your computer open the existing `swarm` folder, paste `agent_v2.py`, and select **Replace**.
4. GitHub Desktop → **Commit to main** → **Push origin**.
5. In GitHub → Actions → *Santa Swarm — evolve and validate* → **Run workflow**.
6. Open `AI AGENTS:` in the new log and look for `limit_source` in `api_calls`.

Do not copy only the outer patch folder on top of your repository. You only need to replace one Python file. Do not share your key with anyone, including ChatGPT.

**Note:** If you rotate to another valid OpenRouter API key, update the existing `OPENROUTER_API_KEY` repository secret. A second key from the same account does **not** reset the account-level free limit. Do not create extra accounts to evade provider limits. You can also use keys from different legitimate API providers, but that requires an integration change; the existing code expects OpenRouter-compatible requests and key authentication.

## Testing / caveats

- 6 targeted offline tests verified daily/minute/unknown 429 stop behavior, provider-specific fallback, and no key leakage in diagnostics.
- The patch hasn't been tested with your OpenRouter account. Provider/model availability may change. An `AI AGENTS: status=candidate_saved` only means it generated candidate code, not that the code improved the Kaggle score.
