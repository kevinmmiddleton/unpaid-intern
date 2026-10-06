# Contributing

Ideas, fixes, and "this connector changed its address" reports are all welcome. The fastest route is an [issue](https://github.com/kevinmmiddleton/unpaid-intern/issues/new/choose).

## How the repo fits together

The repo root is the plugin. Everything else hangs off it:

| Path | What it is |
|---|---|
| `skills/unpaid-intern/` | The skill: `SKILL.md`, references, templates, the two scripts, and the connector catalog |
| `commands/` | The slash commands, one file each |
| `hooks/hooks.json` | The ask-first hook (generated) |
| `.mcp.json` | Plugin connector list (generated) |
| `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json` | This repo as its own install source for Claude Code and Codex (generated). It's also listed in the [claude-plugins](https://github.com/kevinmmiddleton/claude-plugins) catalog |
| `plugin.json`, `mcp.json` | The Codex and ChatGPT manifest and connector list (generated from `.claude-plugin/plugin.json` and the catalog) |
| `evals/` | Behavior scenarios and the latest results |
| `tools/` | The build script, the hook rules, and the brand image scripts |

## Before you open a pull request

```
python3 tools/build.py          # regenerate derived files after editing the catalog, plugin.json, or hook rules
python3 tools/build.py --test   # every self-test
python3 tools/build.py --dist   # optional: build the three release files into dist/
```

Only the Python standard library, Python 3.9 or newer. CI runs the same checks on Mac, Windows, and Linux.

House style for anything a user reads: plain words, no em dashes, and never claim the intern did something it didn't.

## Adding or fixing a connector

Edit `skills/unpaid-intern/connectors/catalog.json`, then run `python3 tools/build.py` so the markdown copy and the plugin config catch up. If it changes which tools the plugin bundles, update `BUNDLED_ORDER` in `tools/build.py`.

## Cutting a release

Bump `version` in `.claude-plugin/plugin.json` and in the `SKILL.md` frontmatter, add a `CHANGELOG.md` entry, update `.github/release-notes.md`, then push a tag that matches (`v1.3.1`). The release workflow builds and attaches the files.
