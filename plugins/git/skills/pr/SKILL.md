---
name: pr
description: Open or update a GitHub pull request for the current branch using gh, with a summary and test plan. Use when asked to open/create/make a PR, update a PR description, or check a PR's status.
---

If the project defines its own PR rules or template, those take precedence over these defaults.

1. **Preconditions.**
   - `gh auth status` must succeed; if not, tell the user to run `gh auth login`.
   - If on the default branch with new commits, offer to move them to a new branch (`git switch -c <type>/<topic>`) before opening a PR.
   - If there are uncommitted changes, ask whether to commit them first (`commit` skill).
   - Make sure the branch is pushed and up to date with its upstream (`push` skill).
2. **Existing PR?** `gh pr view --json number,url,state,title,isDraft 2>/dev/null`. If one is open, update it (`gh pr edit`) instead of creating a duplicate, and report its URL.
3. **Base branch:** the repo's default branch unless the user says otherwise (`gh repo view --json defaultBranchRef -q .defaultBranchRef.name`). For forks, target the upstream repo.
4. **Gather context:** `git log --oneline <base>..HEAD` and `git diff <base>...HEAD --stat` (plus the full diff if needed to describe it accurately).
5. **Title:** short (≤ 70 chars), imperative, describing the overall change. Follow Conventional Commits if the repo's history uses them.
6. **Body:** if `.github/pull_request_template.md` (or `.github/PULL_REQUEST_TEMPLATE/`) exists, fill it in. Otherwise:

   ```markdown
   ## Summary
   - <what changed and why, 1-4 bullets>

   ## Test plan
   - [ ] <how this was / should be verified>

   ## Notes
   <optional: follow-ups, risks, screenshots; omit if empty>
   ```

   End the body with the attribution line from the system reminder, if there is one. Don't write bare `@name` mentions unless you intend to notify a real user; put code like `@types/node` in backticks.
7. **Create:** `gh pr create --base <base> --title "<title>" --body-file <tmpfile>` (body via heredoc to a temp file so formatting survives).
   - Use `--draft` if the user says draft/WIP or the work is clearly incomplete (failing tests, TODOs left).
   - Don't add reviewers, assignees, or labels unless asked.
8. Report the PR URL. If CI checks exist, offer to watch them (`gh pr checks --watch`).
