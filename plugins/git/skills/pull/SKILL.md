---
name: pull
description: Bring the current branch up to date with its own remote tracking branch (rebase by default, fast-forward on the default branch). Use when asked to pull, update the branch, or after a rejected push.
---

This updates the current branch from **its own upstream**. To bring in the latest default branch (e.g. `main`) into a feature branch, use the `sync` skill instead.

1. `git status --short` and `git rev-parse --abbrev-ref --symbolic-full-name @{u}`. If there's no upstream, say so and stop (nothing to pull; suggest `push` to publish the branch).
2. **Dirty tree.** If there are uncommitted changes:
   - Prefer asking the user: commit them (via the `commit` skill), or set them aside.
   - To set them aside, use a temporary WIP commit, or `git stash push -u -m "claude-pull-<timestamp>"`, record its SHA from `git stash list --format='%H %gs'`, and restore later with `git stash apply <sha>` then drop that exact entry. Never bare `git stash` / `git stash pop` (the stash stack is shared across worktrees and sessions).
3. `git fetch --prune origin`, then compare: `git rev-list --left-right --count HEAD...@{u}`.
   - Behind only: `git merge --ff-only @{u}`.
   - Ahead only: nothing to pull; say so.
   - Diverged:
     - On the default branch: stop and explain; don't create merge commits or rebase it without asking.
     - On a feature branch: `git rebase @{u}` (keeps history linear; local commits replayed on top).
4. **Conflicts.** Stop and list conflicted files. Read both sides and resolve them together with the user's intent in mind; never blanket `--ours`/`--theirs`. After resolving: `git add <files>` and `git rebase --continue`. If it gets messy, `git rebase --abort` restores the previous state—offer that.
5. If `.gitmodules` exists, run `git submodule update --init --recursive` afterwards.
6. Restore any set-aside changes (step 2), then report: how many commits came in, the new `HEAD` (`git log --oneline -1`), and ahead/behind status.
