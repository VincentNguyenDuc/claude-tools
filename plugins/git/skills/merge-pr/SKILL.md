---
name: merge-pr
description: Merge a GitHub pull request with gh, matching the repo's merge style, then clean up the branch locally and remotely. Use when asked to merge a PR, "ship it", or "/git:merge-pr [number | url]".
---

1. **Find the PR:** the number or URL given, else the current branch's PR: `gh pr view --json number,title,state,isDraft,baseRefName,headRefName,mergeable,mergeStateStatus,statusCheckRollup,reviewDecision`.
2. **Check it can merge:**
   - Already merged or closed: say so and stop.
   - Draft: ask before marking it ready (`gh pr ready`).
   - Conflicts (`mergeable: CONFLICTING`): stop and suggest the `sync` skill on the PR branch.
   - Failing or pending checks, or changes requested: list them and ask whether to proceed. Never use `--admin` to bypass protections unless the user asks.
3. **Strategy:** use what the user says. Otherwise match the repo: check `gh repo view --json squashMergeAllowed,mergeCommitAllowed,rebaseMergeAllowed` and the default branch history (`Merge pull request #…` commits mean `--merge`; single PR-titled commits mean `--squash`). Default to `--squash` when both fit.
4. **Local state:** if the working tree has uncommitted changes, ask before continuing (commit them via the `commit` skill, or leave the branch as it is). Don't stash silently.
5. **Merge:** `gh pr merge <number> --<strategy> --delete-branch`. gh deletes the remote branch and, when run on the PR branch, switches to the base branch and deletes the local one.
6. **Tidy up:** `git fetch --prune`, then make sure the base branch is current (`git pull --ff-only` on it). If the local head branch still exists, delete it with `git branch -d`; after a squash merge that needs `-D`, which is safe once the PR shows `MERGED`.
7. Report: `PR #N merged into <base> (<strategy>)`, the new base commit (`git log --oneline -1`), and which branches were deleted.
