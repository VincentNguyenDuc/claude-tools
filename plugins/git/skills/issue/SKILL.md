---
name: issue
description: Create a GitHub issue with gh, with a title in the repo's convention and a structured body. Use when asked to open, file or create an issue, track a bug or task on GitHub, or "/git:issue <description>".
---

1. **Understand the request.** If the description is too vague to write acceptance criteria, ask one or two questions first.
2. **Match the repo's conventions:** look at recent titles (`gh issue list --state all --limit 15 --json title,labels`) and `git log --oneline -15`. If they use Conventional Commits, title it `type(scope): description`; otherwise a short imperative sentence. Keep it under 70 characters.
3. **Labels and assignees:** only use labels that exist (`gh label list`). Don't assign anyone unless asked.
4. **Body** (omit any section that would be empty):

   ```markdown
   ## Summary
   <1–2 sentences: the problem or the feature, and why it matters>

   ## Requirements
   - [ ] <checkable acceptance criterion>

   ## Context
   <links, error output, related issues/PRs>

   ## Implementation notes
   <constraints or suggested approach>
   ```

5. Create it with `gh issue create --title "<title>" --body-file -` (pass the body via a heredoc) plus any `--label` flags.
6. Return the issue number and URL.
