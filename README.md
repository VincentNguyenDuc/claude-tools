# claude-tools

Personal Claude Code plugin marketplace.

## Plugins

| Plugin | Contents |
|---|---|
| [`git`](plugins/git) | Skills: `commit`, `push`, `pull`, `sync`, `pr` |
| [`dag`](plugins/dag) | Planning DAG in `.claude-dag/`. Skills: `plan`, `next`, `replan`, `status`. Also MCP tools, a SessionStart hook, a CLI and a web UI |

## Install

Once per machine:

```
/plugin marketplace add VincentNguyenDuc/claude-tools
/plugin install git@claude-tools
/plugin install dag@claude-tools
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
    "dag@claude-tools": true
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
