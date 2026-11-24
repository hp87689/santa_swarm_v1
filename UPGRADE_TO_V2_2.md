# Upgrade Santa Swarm v2.1.5 to v2.2

**Keep your existing champion.** Back up the most recent `champion.csv` artifact from GitHub first.

1. Extract the ZIP.
2. Open the inner `santa_swarm_v2_2` folder.
3. Copy all contents (including hidden `.github`) into your GitHub Desktop repository folder and replace matching files.
4. **Do not delete `.git`, repository secrets, or existing backups.**
5. Commit in GitHub Desktop with `Add multi-target evolution v2.2` and click **Push origin**.
6. On GitHub → Actions → Santa Swarm — evolve and validate → Run workflow.
7. Look for `EVOLUTIONARY PORTFOLIO:` and `OVERALL EVOLUTION:`.

This update changes the local search optimizer, persistent strategy memory, tests and GitHub workflow. It **does not** guarantee any score improvement against your 128,504 champion. It does not replace your OpenRouter key or use paid models.
