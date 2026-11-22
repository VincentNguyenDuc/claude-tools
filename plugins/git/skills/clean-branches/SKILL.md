---
name: clean-branches
description: Find merged, stale and orphaned git branches, local and remote, and delete the ones the user picks. Use when asked to clean up, prune or tidy branches, or "/git:clean-branches [merged | gone | stale | all | <branch>]".
---

1. **Gather** (in parallel, after `git fetch --prune origin`):
   - Default branch: `git symbolic-ref --short refs/remotes/origin/HEAD` (e.g. `origin/main`).
   - `git for-each-ref --sort=-committerdate --format='%(refname:short)|%(committerdate:relative)|%(upstream:short)|%(upstream:track)' refs/heads/`
   - `git branch --merged <default>` and `git branch -r --merged origin/<default>`
   - `git worktree list` (branches checked out in other worktrees)
2. **Categorize** every branch except the default branch:

   | Category | Meaning |
   |---|---|
   | merged | fully merged into the default branch |
   | gone | local branch whose upstream was deleted (`[gone]`); often squash-merged PRs |
   | stale | last commit older than 30 days and not merged |
   | remote-only merged | remote branch merged into the default branch with no local branch |
   | active | everything else (never offered for deletion) |

3. **Protect:** never delete the default branch, `main`/`master`/`develop`, the current branch, or a branch checked out in another worktree. Never delete release branches (`release/*`) without the user naming them.
4. **Show the plan.** With no argument, show a table grouped by category (name, age, local/remote) and ask what to delete. With an argument, show exactly which branches match and ask for confirmation.
5. **Delete:**
   - Local: `git branch -d <name>`. If git refuses because the branch isn't merged (normal for `gone` branches after a squash merge), say so and use `-D` only after the user confirms that branch.
   - Remote: `git push origin --delete <name>`, only for branches the user confirmed. Warn if the branch looks like someone else's (author of its last commit isn't the user).
6. Run `git fetch --prune` and report what was deleted and what remains.
