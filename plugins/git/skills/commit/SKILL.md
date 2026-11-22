---
name: commit
description: Commit the current changes with a well-scoped staging set and a message that matches the repo's style. Use when asked to commit, save work to git, or "commit this".
---

If the project defines its own commit skill or commit rules (CLAUDE.md, CONTRIBUTING.md), those take precedence over these defaults.

1. **Look first.** Run `git status --short`, `git diff`, `git diff --staged`, and `git log --oneline -15` (in parallel).
2. **Branch check.** If on the default branch (`main`/`master`) and the repo's history shows a PR/branch workflow (merge commits, other remote branches), suggest creating a branch first (`git switch -c <type>/<short-topic>`). If the repo is clearly solo and commits straight to the default branch, commit there.
3. **Stage by path, only what belongs to this change.** Never `git add -A` / `git add .` blindly.
   - Never stage secrets or local config: `.env*`, `*.pem`, `*.key`, `credentials*.json`, `.claude/settings.local.json`. If one is already staged, unstage it and warn.
   - Never stage OS/editor junk or build output (`.DS_Store`, `node_modules/`, `dist/`, `build/`, `__pycache__/`, sim/work dirs). If such files show as untracked, suggest a `.gitignore` entry.
   - If unrelated changes are mixed in, ask whether to split them into separate commits.
   - **Large files and Git LFS.** Warn about any file over 100 MB (GitHub rejects them). If `.gitattributes` has `filter=lfs` patterns, check every new binary (PDFs, images, archives, datasets, …) with `git check-attr filter -- <file>`; it should print `filter: lfs`. If a binary type isn't tracked, offer `git lfs track "*.<ext>"` and stage `.gitattributes` together with it.
4. **Message.** Match the style in `git log`:
   - If the log uses Conventional Commits (`feat:`, `fix(scope):`), use them.
   - Otherwise: a short imperative subject (≤ 72 chars, no trailing period), matching the log's casing.
   - Add a body (blank line after subject) only when it explains *why* or something non-obvious; wrap at 72.
   - End with the attribution trailer from the system reminder, if there is one.
   - Pass the message via a heredoc so formatting survives.
5. **Hooks.** If a pre-commit hook fails, fix the cause, re-stage, and create the commit again. Never use `--no-verify`. If a hook auto-modified files, re-stage them and commit.
6. **Never** amend, rebase, or rewrite existing commits unless the user asks.
7. **Submodules.** If a submodule has uncommitted changes, say so; don't commit inside it unless asked. Stage a moved submodule pointer only if that submodule commit is pushed.
8. Finish by showing `git log --oneline -1` and a one-line `git status` summary (what's left uncommitted, ahead/behind upstream).
