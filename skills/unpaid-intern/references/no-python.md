# When Python can't run

Contents

- First, try the other names
- Build the folders by hand
- Dates without a script
- The due list by hand
- The status table by hand
- Projects, areas, and the archive by hand
- Checks and scans by hand
- Connecting tools by hand
- Carrying the workspace on the web
- When nothing can be installed at all

Some companies block Python, or the machine simply doesn't have it. The second brain still works. The scripts only do the jobs language models are bad at (dates, counting, spotting a leaked secret), so without them you do those jobs carefully, show your work, and say once that the result was not machine-checked.

## First, try the other names

On Windows, `python3` is often missing while Python is installed under another name, or it's a Microsoft Store shortcut that prints "Python was not found" instead of running. Before falling back, try once each, in order: `python3 --version`, `python --version`, `py -3 --version`. Use the first that prints a Python 3 version, in place of `python3`, for the whole session (`references/scripts.md` also says where the scripts are on each host). If none does, or code execution is turned off, use this page.

## Build the folders by hand

Read each file below from this skill's `templates/` folder and write it, unchanged, to the same path inside the person's `Second Brain` folder. Never overwrite a file that already exists. Also create the empty folders `4-Reference/sources/meetings/`, `5-Archive/processed/`, and `5-Archive/projects/`.

- `START-HERE.md`
- `AGENTS.md`
- `CLAUDE.md`
- `1-Inbox/README.md`
- `2-Projects/README.md`
- `2-Projects/_template/current.md`
- `2-Projects/_template/decisions.md`
- `2-Projects/_template/sources.md`
- `2-Projects/_template/context-map.md`
- `3-Areas/README.md`
- `3-Areas/_template.md`
- `3-Areas/_ramp-up.md`
- `4-Reference/INDEX.md`
- `4-Reference/glossary.md`
- `4-Reference/people.md`
- `4-Reference/sources/README.md`
- `5-Archive/README.md`
- `Memory/README.md`
- `Memory/project-status.md`
- `Memory/followups.md`
- `Memory/meetings.md`
- `Memory/decisions.md`
- `Memory/lessons.md`
- `Memory/scratch-today.md`
- `Memory/day-log/_template.md`
- `Setup/README.md`
- `Setup/preferences.md`
- `Setup/guardrail-profile.md`
- `Setup/setup-profile.md`
- `Setup/connection-plan.md`
- `Setup/my-commands.md`
- `Setup/it-request.md`

If the file tools can't write either (a plain chat), give the person the no-install kit's starter folder instead (see the last section).

## Dates without a script

- Take today's date from the conversation or the system, and say it with the weekday: "Today is Tuesday, October 6."
- For any date math, write the steps out: "Due Friday the 9th. Today is Tuesday the 6th. That's 3 days away." Count business days on a short calendar list, never in your head, and show the list for every count you report. For example, waiting since Thu Sep 24, today Mon Oct 5: Fri 25, Mon 28, Tue 29, Wed 30, Thu Oct 1, Fri 2, Mon 5 = 7 business days.
- A date that falls on a weekend is "past due over the weekend," not "0 days late."
- Spoken deadlines (`brain.py when` by hand): "Thursday" is the coming Thursday; "next Tuesday" is the one in the following week, written with `~` and the other reading named; "end of week" is Friday; "end of month" is the month's last weekday, with `~`; "soon" or "ASAP" has no date, so write a placeholder with `~` and say it's a guess; a vague span ("next quarter", "next month", "later this year") is a range, not a day, so name it with its first and last dates ("Q1 2027, an estimate: 2027-01-01 to 2027-03-31") and, if a follow-up needs one date, use its last weekday with `~`. A hedge ("I think", "maybe", "-ish", a question mark) makes any of these a guess too. Show the calendar line you used.

## The due list by hand

Read `Memory/followups.md`. Ignore lines inside `<!-- -->` comments and code fences. For each open line (`- [ ]`):

1. **Overdue, yours:** owner `@me` and the date is before today.
2. **Due today, yours.**
3. **Due soon, yours:** due within the next three business days.
4. **Waiting on others, past due:** owner `@waiting:Name` and the date has passed.
5. **Waiting on others, stale:** not past due, but `since:` is more than five business days ago.
6. **Waiting on others, not yet agreed:** `accepted: false` and due within the next ten business days.
7. **Waiting on others, due today or later:** every other open `@waiting` line. List each one with who, what, and when.
8. **Guessed dates coming up:** the date starts with `~` and falls within the next three business days. Ask the person to confirm it.
9. **Owner not recognized:** the owner is neither `@me` nor `@waiting:Name`.

Report only the groups that have items, soonest first. A line that doesn't match the format gets mentioned, not guessed at.

At session open (`due --open`), mention only groups 1, 2, 4, and 5, in two lines at most, and say nothing if they're empty.

For the full list, also look in 1-Inbox: any file there other than README.md is waiting to be filed. Name them (up to five) and offer to file them.

## The status table by hand

Read `Memory/project-status.md`. Leave out `watch` rows unless the person asks for them. Order the rest own, then support. The table has these columns:

`| Project | Status | Next step | Next checkpoint | Open (mine / waiting) | Updated |`

"Open" counts the open follow-ups tagged with the project's `#slug`: how many are `@me`, and how many are `@waiting`. Before handing it over, add a note for each of these:

- Updated is 14 or more days ago, or isn't a real date.
- Status is `on-track` but a tagged follow-up is overdue.
- Status is `done` but tagged follow-ups are still open.
- No next step, unless the project is `done` or `paused`.
- A status word that isn't one of: unconfirmed, not-started, in-progress, on-track, at-risk, blocked, paused, done.
- A row with the wrong number of columns (leave it out and say so).
- Open follow-ups that aren't tagged to any project.

Never paint a row green to make the table look better.

## Projects, areas, and the archive by hand

- **New project:** copy the four files in `2-Projects/_template/` to `2-Projects/<slug>/` (lowercase, hyphens), replace `<Project name>`, add a row to `Memory/project-status.md` (status `unconfirmed` unless they said how it's going, Updated today), and add a line under Projects in `4-Reference/INDEX.md`.
- **New area:** copy `3-Areas/_template.md` to `3-Areas/<slug>.md`, replace `<Area name>`, and add a line under Areas in the index. For someone new to the job, copy `3-Areas/_ramp-up.md` to `3-Areas/ramping-up.md` instead and fill in the start date and a review-by date about 30 days out.
- **Archive:** only when no open follow-up line (well-formed or not) carries the project's `#slug`. Move the folder to `5-Archive/projects/`, set the row's status to `done` with today's date, and update the index link. Nothing is deleted.

## Checks and scans by hand

- **Before filing anything from the inbox,** read it for: passwords and keys (long random strings, anything after `password`, `token`, `secret`, or `Bearer`), card and account numbers (long digit runs), government IDs, health, HR, or legal details, and customer contact records. If any appear, stop, don't file it, and ask the person to remove the original.
- **Weekly,** check the follow-up lines match the format, project rows use the allowed status words, every decision has a Why, and links in `4-Reference/INDEX.md` point at files that exist.

## Connecting tools by hand

The connection script's data is also kept as plain pages:

| Script job | Use instead |
|---|---|
| The setup questions (`screens`) | `references/setup-questions.md` |
| Which tool is which, and how each connects (`match`, `list`) | `connectors/catalog.md` |
| The connection plan (`plan`, `mark`) | Write `Setup/connection-plan.md` yourself: a table of Order, Tool, How it connects, and Status (to-do, connected, needs-admin, failed, using-fallback, skipped), then a short steps section per tool from the catalog. In Codex, write "Made on <date> for Codex" and use the catalog's Codex routes (its plugin directory first, then `codex mcp add` and login), never Claude's steps |
| An error message (`diagnose`) | `references/error-decoder.md` |
| The IT email (`it-request`) | Fill in `Setup/it-request.md` with each blocked tool's admin step and read-only option from the catalog. Never include passwords, codes, or tokens |
| The tour (`tour`) | `references/what-you-unlock.md`. In Codex, give each command in words from its last column, never as a slash |
| Claude Code settings (`mcp-json`) | Copy the address from the catalog into Claude Code's own add-connector command, read-only address first |
| The network test (`check`) | Skip it. Explain that it needs Python, and use the error decoder instead |

## Carrying the workspace on the web

On claude.ai, skills only run when code execution is on, and that also brings Python. If code execution is off, the skill won't load at all, so use the no-install kit below.

## When nothing can be installed at all

For companies that allow no skills, plugins, or Python, the no-install kit (in this skill at `extras/no-install-kit/`, and as `unpaid-intern-no-install-kit.zip` on the project's Releases page) gives people:

- **A starter `Second Brain` folder,** already built, to unzip into OneDrive, Google Drive, or Documents.
- **`INSTRUCTIONS.md`,** to paste into a Claude Project (or any assistant with saved instructions and file uploads). It carries the rules, the setup questions, and the core commands, and asks the assistant to hand back updated files at the end of each session.
- **`QUICK-START-PROMPT.md`,** a single prompt to paste at the start of any chat when that's all the company allows.

## The finishing check by hand

Before handing back a task that wrote files, list every file you wrote or moved this session, from your own steps. In each one, find any weekday next to a date and check it on a short calendar list you write out; if you can't verify it, remove the weekday and leave the plain date. Find any "he", "she", "his", or "her" and keep it only if a source gives that pronoun.
