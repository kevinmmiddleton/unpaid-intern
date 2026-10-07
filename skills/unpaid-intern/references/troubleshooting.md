# Troubleshooting

Contents

- Setup and scripts
- Connectors and sign-in
- Briefing quality
- Records and memory
- When in doubt

Vendor details checked in October 2026. Find the symptom, try the fix, and if it still fails, say what you tried in one line and continue from files. For any connector error message, run `connect.py diagnose "<message>" --tool <id>` first; it covers more messages than this table.

## Setup and scripts

| Symptom | Likely cause | Fix |
|---|---|---|
| `brain.py` not found | `${CLAUDE_SKILL_DIR}` is empty on this surface (always, in Codex and other hosts) | Use the `scripts/` folder next to the SKILL.md that loaded, by full path (`references/scripts.md`) |
| "No workspace found" | Running from the wrong folder | Pass `--workspace <folder>`, or run `init` first |
| Scripts cannot run at all | Code execution is off, or no Python under that name | Try `python3 --version`, then `python --version`, then `py -3 --version`, and use the first that prints a Python 3 version (on Windows, `python3` is often a Microsoft Store shortcut). Otherwise follow `references/no-python.md`, which builds the folders and does each script's job by hand. On the web, code execution has to be on for skills to load at all; if it can't be, use the no-install kit |
| `now` says it's using this computer's clock | The timezone in preferences isn't one this computer knows: a typo, or Windows, which has no timezone database | Nothing to fix if they work in this computer's time zone; it says so once per workspace. Otherwise check the name is an Area/City one like `America/Chicago` |
| Claude Code ignores the workspace rules | An existing `CLAUDE.md` does not import `AGENTS.md` | Add the line `@AGENTS.md` to `CLAUDE.md` |
| Another tool overwrote `CLAUDE.md` or created `memory/` or `TASKS.md` | A plugin's start command ran in this folder. On Mac and Windows, folder names ignore capitals, so another tool's `memory/` lands inside this workspace's `Memory/` | Restore the import line, move the other tool's files out of `Memory/`, and run that plugin in a different folder |
| `selftest` fails | The skill folder is incomplete or was edited | Reinstall the skill; if edited on purpose, read the failing check |
| The workspace is gone in a new chat | The surface's code sandbox does not keep files (common on the web) | Rebuild with `brain.py unpack <zip> <folder>`; end every session with `brain.py pack` |
| `scan` says some files were not scanned | PDFs, spreadsheets, and images are not plain text | Extract the text and pipe it to `brain.py scan --stdin`, or review by hand |

## Connectors and sign-in

| Symptom | Likely cause | Fix |
|---|---|---|
| "Your site admin must authorize this app" | Atlassian needs first consent from a site admin | Ask for the IT email (`connect.py it-request`) and send it to the Atlassian admin |
| "Access blocked" on Google | Workspace admin has not marked Claude as trusted | Ask for the IT email and send it to the Google Workspace admin |
| "Need admin approval" on Microsoft | Tenant-wide consent not granted yet | Ask for the IT email and send it to a Microsoft Global Admin |
| Connector appears but is greyed out, or shows Request | On Team or Enterprise, only Owners add it | Click Request, or ask the Claude Owner |
| Works in the browser but the connector cannot reach the tool | The tool sits behind a VPN or an IP allowlist; connectors run from Anthropic's cloud | Ask IT to allow the connector, or use exports and the drop folder |
| Claude Code or Codex: certificate errors such as `SELF_SIGNED_CERT_IN_CHAIN` | The company inspects secure traffic | Ask IT for the root certificate and set `NODE_EXTRA_CA_CERTS` (Claude Code) or `CODEX_CA_CERTIFICATE` (Codex) to its path before starting it; `connect.py check` confirms |
| Claude Code: timeouts or `407` | A company proxy is required | Ask IT for the proxy address and set `HTTPS_PROXY`; `connect.py check` confirms |
| Adding Slack by web address fails with `invalid_client` | Slack does not allow automatic app registration | Use Slack from the connector directory or the plugin, not a hand-added address |
| Claude Code: Asana or Box says it "does not support dynamic client registration" | These tools do not let apps register themselves | Connect it on claude.ai with the same Claude account; it then shows up in `/mcp` |
| Claude Code: Gmail or Google Calendar shows "not configured" | They come from Claude's own connectors, not a web address | Connect them on claude.ai with the same Claude account; they then show up in `/mcp` |
| The plugin lists tools the user does not use | The plugin pre-lists common connectors | Ignore them; nothing connects until the user signs in |
| A personal Microsoft account fails | The Microsoft 365 connector supports work and school accounts only | Use the work account |
| Signed in but results are empty | Wrong region endpoint, missing permission in the tool, or data hidden by policy | Check the region, check that the user can see it in the tool itself, then ask the admin |
| Worked yesterday, fails today | Expired sign-in, revoked consent, or a usage limit | Reconnect; if many users fail at once, the admin re-runs consent; check vendor usage limits |
| Need to change how a custom connector signs in | Auth settings cannot be edited after adding | Remove and re-add the connector |
| OneNote pages show up but cannot be read | Not supported by the connector | Export to PDF or Word and drop it |
| Gmail attachment contents missing | The connector returns attachment metadata only | Download the attachment and drop it |
| The tool keeps writing when it should not | Write tools are on | Set them to blocked or needs approval in the connector's tool settings, and update the guardrail profile |

## Briefing quality

| Symptom | Likely cause | Fix |
|---|---|---|
| Brief is too long | No word cap, or every section is filled | Set `word cap` in preferences; omit empty sections |
| Items the user already handled keep appearing | The thread was not re-checked | Open each thread once before surfacing it; replied or reacted means resolved |
| Group emails show up as "needs you" | Group aliases treated as personal asks | Only direct asks count; anyone-could-answer messages do not |
| Too many pings | No interruption budget | Set `interruption budget per day` and quiet hours; batch into the next brief |
| A quiet brief, but a connector was down | Silence looks like a quiet day | Always say once when a source was unavailable |
| Dates are off by a day | Date math done in the head, or the wrong timezone | Run `brain.py now` and `brain.py due`; set `timezone` in preferences |

## Records and memory

| Symptom | Likely cause | Fix |
|---|---|---|
| Follow-ups missing from the due list | Lines do not match the format, or an HTML comment was left open | Run `brain.py lint`; it reports both |
| Duplicate follow-ups | Captured twice from two sources | `/tidy` merges them |
| `/project-status` shows 0 / 0 for a project | Follow-ups are not tagged | Add `#project-slug` to the follow-up lines |
| A project row is flagged stale | Updated date is old | Confirm the status with the user, then update the date |
| The agent "remembers" something that is no longer true | An old note is impersonating current state | Rewrite the project's `current.md` forward; history stays in `decisions.md` |
| Workspace is getting slow to read | Too much raw material kept | Move processed drops out; keep notes short; retire unread pages |
| Restricted data found in the workspace | A raw paste or export went straight in | Run `brain.py scan`; redact anything already filed; ask the user to remove the original drop |

## When in doubt

- Say what you could not do, in one line.
- Continue from files.
- Never guess to fill a gap.
- If it keeps happening, add a row to `Memory/lessons.md` with the cause and the fix.
