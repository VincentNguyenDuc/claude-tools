---
name: sync
description: Sync the current branch with the latest default branch (or upstream fork), and fast-forward the local default branch. Use when asked to sync, update from main, catch up with main, or sync a fork.
---

If the project defines its own sync rules, those take precedence over these defaults.

1. **Find the source of truth.**
   - Remote: use `upstream` if it exists (this is a fork), otherwise `origin`.
   - Default branch: `git symbolic-ref --short refs/remotes/<remote>/HEAD` (strip the remote prefix); fall back to `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`.
2. **Dirty tree.** Handle uncommitted changes the same way as the `pull` skill (ask; WIP commit or tagged stash; never bare `git stash`).
3. `git fetch --prune <remote>` (and `origin` too if different).
4. **Update the local default branch** without checking it out:
   - If on it: `git merge --ff-only <remote>/<default>`.
   - Otherwise: `git fetch <remote> <default>:<default>` (fast-forward only; if it refuses, the local default branch has diverged—report it, don't fix it silently).
   - For a fork, if the user wants, push the updated default branch to `origin` so the fork stays current.
5. **Update the current feature branch** (skip if on the default branch):
   - If the branch is not on the remote yet, or only the user has pushed to it and there's no open PR with review in progress: `git rebase <remote>/<default>`.
   - If others have pushed to it or a PR is under review: `git merge <remote>/<default>` to avoid rewriting shared history.
   - When unsure which, ask. Resolve conflicts as described in the `pull` skill.
6. After a rebase of an already-pushed branch, the next push needs `--force-with-lease`. Say so and ask before pushing; don't push automatically.
7. Restore set-aside changes, then report: commits pulled into the default branch, how the feature branch was updated (rebase/merge), and ahead/behind status vs. its upstream and vs. the default branch.
