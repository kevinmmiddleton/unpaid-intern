# Scripts

Both scripts use only the Python standard library (3.9 or newer). Run `python3 "${CLAUDE_SKILL_DIR}/scripts/<script>" <command>`; most commands take `--workspace <folder>`. If `${CLAUDE_SKILL_DIR}` is empty, find `scripts/` inside this skill's own folder. If Python can't run, `references/no-python.md` does each job by hand.

## brain.py keeps the record

It makes no network calls.

| Run | When |
|---|---|
| `init <folder>` | Create the workspace from templates; never overwrites existing files |
| `now [--tz Area/City]` | Any time the date, weekday, or time matters |
| `due [--open] [--days 3] [--stale 5]` | `--open` at session open (only what's due today, overdue, or stale; it also marks the session start for `check`); the full list for `/briefing`, `/pulse`, `/week`, `/gofer`, which also names the files waiting in 1-Inbox and lists your items just past the window, with weekdays |
| `when "<phrase>" ...` | Any spoken deadline: "Thursday", "end of month", "next Tuesday", "soon", "Friday I think". Prints the date and marks guesses with `~`; a hedge makes any date a guess. A phrase it can't read gets its own note; the others still resolve |
| `status [--all] [--copy]` | `/project-status`; builds the paste-ready table (`--copy` reaches the clipboard only when the script runs on the user's own computer) |
| `daylog` | `/close`; creates today's day log from the template |
| `project "<Name>"` / `area "<Name>"` | The brain dump and `/new-project`: a project folder plus its status row, or an area page (`area "Ramping up" --ramp-up --started <date>` makes the 30-60-90 page) |
| `archive <slug>` | `/tidy`: moves a finished project to `5-Archive/` and marks it done; refuses while its follow-ups are open |
| `check [--since ISO]` | Before handing back any task that wrote files: lists every file changed or moved since the session mark (or `--since`), verifies each weekday written in them against its date, and flags pronouns to review. Exit 1 when a weekday is wrong |
| `lint` | `/kb-lint`, `/tidy`; formats, links, duplicates, stale pages |
| `scan [--path P \| --stdin]` | After any ingest; flags likely secrets, account numbers, and HR, health, or pay details, and lists files it could not read. Exit 1 high, 4 medium, 3 not everything scanned |
| `pack` / `unpack` | Carry the workspace between sessions on surfaces that do not persist files. `pack --output` must point outside the workspace (the download folder) |
| `selftest` | After installing or editing the skill |

## connect.py connects tools and fixes them

Its data lives in `connectors/catalog.json` (77 tools, checked October 2026).

| Run | When |
|---|---|
| `screens --screen <id> [--role R] --json` | Setup and `/connect`: the picker questions, one screen at a time |
| `match "<answer>" ...` | Turn picker answers or typed tool names into tools; returns follow-up questions |
| `plan --tools a,b --surface S` | Write `Setup/connection-plan.md`; re-running keeps statuses |
| `mark <tool> <status> [--note]` | After each connection attempt |
| `diagnose "<error text>" [--tool T]` | Any connector error: plain meaning, who can fix it, whether it needs IT |
| `it-request [--write]` | One email to IT for everything blocked; the user sends it |
| `tour [--write \| --json]` | Setup's last step, and whenever a tool connects: what they unlocked, and a try-first picker |
| `mcp-json --tools a,b [--write]` | Claude Code only: a merge-safe `.mcp.json`, read-only addresses first |
| `check [--tools a,b]` | Only when asked, on Claude Code: tests the network from the user's computer (the only command that uses the network) |
| `list` / `selftest` | Browse the catalog; verify the install |
