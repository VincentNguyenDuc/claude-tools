---
name: push
description: Push committed work to the remote, setting upstream if needed and recovering safely from rejected pushes. Use when asked to push, or "commit and push".
---

If the project defines its own push skill or rules, those take precedence over these defaults.

1. If there are uncommitted changes and the user asked to commit too, follow the `commit` skill first. If they only asked to push, mention the uncommitted changes and push what's committed.
2. **Default branch.** If on `main`/`master` and the repo uses PRs (protected branch, merge-commit history, other contributors), confirm before pushing directly. Solo repos that commit to the default branch can push without asking.
3. **Submodules.** If the commits being pushed move a submodule pointer, push the submodule first so the pointer resolves on the remote. Say which repo and branch before pushing a submodule shared with others.
4. **Git LFS.** If the commits add LFS files (`git lfs ls-files` lists them), check `git lfs version` works first; LFS objects upload through the pre-push hook. Mention that they count toward the remote's LFS storage quota.
5. **Push.**
   - With upstream: `git push`.
   - Without upstream: `git push -u origin HEAD`.
6. **Rejected (non-fast-forward).** Don't force. Run the `pull` skill (rebase onto the remote branch), resolve any conflicts, then push again.
7. **Force-push rules.** Never force-push the default branch or a branch others push to. On the user's own feature branch after a deliberate rebase/amend, use `git push --force-with-lease` only after the user agrees, never plain `--force`.
8. Report the pushed range from the push output (e.g. `bca4cce..007f0ec feature/x`) and, if GitHub printed a "create a pull request" link and no PR exists yet, mention the `pr` skill.
