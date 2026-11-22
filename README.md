# claude-tools

Personal Claude Code plugin marketplace.

## Plugins

| Plugin | Contents |
|---|---|
| [`git`](plugins/git) | Skills: `commit`, `push`, `pull`, `sync`, `pr`, `merge-pr`, `issue`, `release`, `clean-branches` (with Git LFS and sparse-checkout handling) |
| [`dag`](plugins/dag) | Planning DAG in `.claude-dag/`. Skills: `plan`, `next`, `replan`, `status`, `validate`, `ui`. Also MCP tools, a SessionStart hook, a CLI and a web UI |
| [`kb`](plugins/kb) | Knowledge hub skills: `new-topic`, `find-canonical-papers`, `add-paper`, `paper-notes` |
| [`dev`](plugins/dev) | Skills: `codebase-analysis` |

## Install

Once per machine:

```
/plugin marketplace add VincentNguyenDuc/claude-tools
/plugin install git@claude-tools
/plugin install dag@claude-tools
/plugin install kb@claude-tools
/plugin install dev@claude-tools
```

Pull updates after pushing changes here:

```
/plugin marketplace update claude-tools
```

### Auto-enable in a project

Add to the project's `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "claude-tools": {
      "source": { "source": "github", "repo": "VincentNguyenDuc/claude-tools" }
    }
  },
  "enabledPlugins": {
    "git@claude-tools": true,
    "dag@claude-tools": true,
    "kb@claude-tools": true,
    "dev@claude-tools": true
  }
}
```

## Layout

```
.claude-plugin/marketplace.json     # lists plugins in this repo
plugins/<name>/
  .claude-plugin/plugin.json        # plugin manifest
  skills/<skill>/SKILL.md           # skills (invoked as /<plugin>:<skill>)
  commands/  agents/  hooks/  .mcp.json   # optional
```

Validate before pushing:

```
claude plugin validate .
claude plugin validate plugins/<name>
```

Project-local skills or CLAUDE.md rules take precedence over these defaults.
