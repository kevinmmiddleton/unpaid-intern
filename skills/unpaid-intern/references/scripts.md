# Scripts

Both scripts use only the Python standard library (3.9 or newer). Most commands take `--workspace <folder>`.

## Running them on any host

Work these out once per session, then reuse them:

1. **Find the scripts.** In Codex and other hosts, they're in the `scripts/` folder next to the SKILL.md that loaded this skill; use its full path. In Claude, use `${CLAUDE_SKILL_DIR}/scripts/`, and if that comes up empty, the same folder next to SKILL.md.
2. **Find Python.** Try `python3 --version`, then `python --version`, then `py -3 --version`, and use the first that prints a Python 3 version. On Windows, `python3` is often a Microsoft Store shortcut: it prints "Python was not found" (or opens the Store) instead of a version, so move on to the next name.
3. **Run** `<python> "<scripts folder>/<script>" <command>`: for example `python3 "${CLAUDE_SKILL_DIR}/scripts/brain.py" due` in Claude, or `py -3 "<scripts folder>\brain.py" due` on Windows.
4. **On Windows PowerShell,** read files with `Get-Content -Encoding UTF8 <file>`. If you write a workspace file from PowerShell instead of your edit tool, add `-Encoding utf8` (to `Set-Content`, `Add-Content`, or `Out-File`), and never use `>` or `>>`. Without it, Windows PowerShell reads and writes the ANSI code page or UTF-16, so text garbles and the scripts misread the file.

If none of the three names works, `references/no-python.md` does each job by hand. Other files in this skill name a script and a command (`brain.py due`); run it this way.

## brain.py keeps the record

It makes no network calls.

| Run | When |
|---|---|
| `init <folder>` | Create the workspace from templates; never overwrites existing files |
| `now [--tz Area/City]` | Any time the date, weekday, or time matters. If the timezone in preferences isn't one this computer knows (common on Windows, which has no timezone database), it uses the computer's clock and says so once per workspace |
| `due [--open] [--days 3] [--stale 5]` | `--open` at session open (only what's due today, overdue, or stale; it also marks the session start for `check`); the full list for `/briefing`, `/pulse`, `/week`, `/gofer`, which lists every waiting item with who, what, and when, names the files waiting in 1-Inbox, and lists your items just past the window, with weekdays |
| `when "<phrase>" ...` | Any spoken deadline: "Thursday", "end of month", "next Tuesday", "soon", "Friday I think". Prints the date and marks guesses with `~`; a hedge makes any date a guess. A vague span ("next quarter", "next month", "later this year") comes back as a labeled range, such as Q1 2027 (estimate) with its first and last dates, plus a `~` date for a follow-up line. A phrase it can't read gets its own note; the others still resolve |
| `status [--all] [--copy]` | `/project-status`; builds the paste-ready table (`--copy` reaches the clipboard only when the script runs on the user's own computer) |
| `daylog` | `/close`; creates today's day log from the template |
| `project "<Name>"` / `area "<Name>"` | The brain dump and `/new-project`: a project folder plus its status row, or an area page (`area "Ramping up" --ramp-up --started <date>` makes the 30-60-90 page) |
| `archive <slug>` | `/tidy`: moves a finished project to `5-Archive/` and marks it done; refuses while its follow-ups are open |
| `check [--since ISO]` | Before handing back any task that wrote files: lists every file changed since the session mark (or `--since`), shows moves as source -> destination, labels files setup created on their own, verifies each weekday written in them against its date, and flags pronouns to review. Exit 1 when a weekday is wrong |
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
| `plan --tools a,b --surface S` | Write `Setup/connection-plan.md`; re-running keeps statuses. Surfaces: `cowork`, `desktop`, `web`, `code`, and `codex` (Codex's own steps: its plugin directory, then `codex mcp add` and login) |
| `mark <tool> <status> [--note \| --error]` | After each connection attempt. `--error` holds the exact message an attempt showed; `--note` holds anything else. The IT email quotes only an `--error` (or a `failed` note) as an error |
| `diagnose "<error text>" [--tool T]` | Any connector error: plain meaning, who can fix it, whether it needs IT |
| `it-request [--write] [--assistant NAME]` | One email to IT for everything blocked; the user sends it. Outside Claude, `--assistant` names the product (it defaults to Claude) |
| `tour [--write \| --json] [--plain]` | Setup's last step, and whenever a tool connects: what they unlocked, and a try-first picker. `--plain` (on by default for a Codex plan) gives each command as words to say, since Codex rejects the kit's slash commands |
| `mcp-json --tools a,b [--write]` | Claude Code: a merge-safe `.mcp.json`, read-only addresses first. In Codex, run it without `--write` to read each tool's address (setup Step 5) |
| `check [--tools a,b]` | Only when asked, on Claude Code or Codex: tests the network from the user's computer (the only command that uses the network) |
| `list` / `selftest` | Browse the catalog; verify the install |
