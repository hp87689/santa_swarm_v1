# Santa Swarm 2026 — OpenRouter AI stage hotfix

This patch fixes the crash in `swarm/agent_v2.py` reported as:
`AI AGENTS: {"status":"no_candidate","stages":[],"error":"'NoneType' object is not subscriptable"}`

## Install without typing code

1. Extract this ZIP.
2. Open its `swarm` folder and copy **agent_v2.py**.
3. In Windows File Explorer, open your existing `Santa-Swarm-2026` GitHub project folder, then open its `swarm` folder.
4. Paste the new `agent_v2.py` there and choose **Replace the file in the destination**.
5. Open GitHub Desktop, enter a commit message such as `Fix OpenRouter empty AI responses`, click **Commit to main**, then **Push origin**.
6. On GitHub, go to **Actions → Santa Swarm — evolve and validate → Run workflow**. Choose `main`.
7. Expand the AI step. Look for `AI AGENTS:` and its `api_calls` details.

## What this patch changes

- Handles OpenRouter HTTP errors, absent choices, null content and zero-length content without the misleading Python `NoneType` crash.
- Asks for low reasoning effort so more output tokens can be used for the final JSON/code response. It cannot force every free model to comply.
- Prints which model responded and whether output was empty, including finish reason and token counts where provided.
- Keeps the existing champion even when the model cannot produce an optimizer.
- Makes NO additional paid API calls and does not require new secrets. The default model remains `openrouter/free`.

## Important

This is a targeted AI reliability patch, not a guarantee that an AI-generated optimizer improves 128,504. A successful AI stage should show `candidate_saved` and stages `mathematician`, `programmer`, `critic`. Independently validated score reductions are still required to claim progress.

This ZIP contains only the changed Python file, the installation guide, and optional offline tests. You don't need to replace the full project.
