---
name: release
description: Cut a versioned release. Bumps the version, updates the changelog, tags, pushes and creates a GitHub release with gh. Use when asked to release, cut or tag a version, publish a release, or "/git:release [patch | minor | major | X.Y.Z]".
---

1. **Preconditions.** Must be on the default branch with a clean tree and up to date with its upstream (`git fetch`, then compare `HEAD` with `@{u}`). If not, stop and say what's wrong.
2. **Current version:** latest tag (`git tag --sort=-v:refname | head -5`). Keep the repo's tag format (`v1.2.3` or `1.2.3`). No tags yet: start at `0.1.0` and ask.
3. **Next version:** the argument if given. Otherwise read the commits since the last tag (`git log --oneline <tag>..HEAD`): breaking changes (`!`, `BREAKING CHANGE`) → major (minor while below 1.0), features → minor, everything else → patch. Show the reasoning and the proposed version.
4. **Version files.** Find where the repo declares its version (e.g. `pyproject.toml`, `package.json`, `Cargo.toml`, `CMakeLists.txt` `project(... VERSION ...)`, `.claude-plugin/plugin.json`, `__version__`) by searching for the current version string. Update every real declaration; refresh lockfiles if the tool needs it (`uv lock`, `npm install --package-lock-only`, …).
5. **Changelog.** If `CHANGELOG.md` has an `## [Unreleased]` section, rename it to `## [X.Y.Z] - YYYY-MM-DD` and add a fresh empty `[Unreleased]` above. If there's no changelog, draft release notes from the commits instead (don't create a CHANGELOG unless the user wants one).
6. **Commit and tag:** commit the version and changelog changes in the repo's style (e.g. `chore(release): vX.Y.Z`), ending with the attribution trailer from the system reminder if there is one, then `git tag -a <tag> -m "<tag>"`.
7. **Confirm before publishing.** Show the version, the tag, and the notes. Pushing a tag and creating a release are public and hard to undo, so wait for a yes.
8. **Publish:** `git push --follow-tags`, then `gh release create <tag> --verify-tag --title "<tag>" --notes-file -` with the changelog section or drafted notes. Attach build artifacts only if the user asks or the repo documents them.
9. Report the release URL. If anything failed after the tag was pushed, say exactly what state things are in rather than retrying destructively.
