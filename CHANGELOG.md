# Changelog

## 1.3.3

Windows and Codex fixes from the first outside field test.

- Scripts run on any host. The skill says where its scripts live outside Claude (the folder next to SKILL.md), and finds Python by trying `python3`, then `python`, then `py -3`, since on Windows `python3` is often a Microsoft Store shortcut.
- The folder tree in the skill's instructions and the arrows in `brain.py check` are plain text now, so Windows PowerShell shows them cleanly.
- On Windows PowerShell, the skill reads and writes workspace files as UTF-8, and the scripts read files saved with a byte-order mark.
- No more timezone warning on every command. Without the timezone data, times come from the computer's clock, and `brain.py now` says so once per workspace.
- Setup's account question asks about "the account you're using here", so it reads right in Codex too. When the first win is meeting prep and there's no invite, your intern preps the recurring meeting from your brain dump and lists what to paste, or offers a /briefing instead.
- The tour's "Start with these" draws only from the core eight, so it and the rest of the core eight add up to exactly eight.
- `brain.py due` lists everything you're waiting on, with who, what, and when, not just a count.
- `brain.py when` turns vague spans ("next quarter", "next month", "later this year") into a labeled range, such as Q1 2027 (estimate), with its first and last dates. "By Thursday" stays a day.
- `brain.py check` shows moves as `source -> destination` and labels the files setup created apart from what the session wrote.
- `/learn` lessons take up to about 20 minutes, depending on how much your sources cover.
- The README's Codex steps mention the sign-in warning for Atlassian and Notion, and the Windows `py` command.
- Setup has a Codex branch: where to make the folder, connecting tools through Codex's plugin directory or with `codex mcp add` and `codex mcp login`, and setting each one to ask before writes in Codex's config, since the plugin's ask-first hook doesn't run there. The IT email can name the product you use (`connect.py it-request --assistant Codex`), and then asks for that product's admin steps instead of Claude's. `connect.py check` and the error decoder name Codex's certificate setting, `CODEX_CA_CERTIFICATE`.
- A `/briefing` over its word cap keeps every waiting item that's late, stale, not yet agreed, or due inside the window, and sums up the rest in one line.
- Setup says a scheduled brief that reads your folder works only while the computer is awake and the Claude desktop app is open, and to set it up from the desktop app.
- `brain.py when` reads "end of year" and "EOY". The error decoder recognizes Windows' "is not recognized" message for a missing Python.

## 1.3.2

- People stay "they" until a source gives a pronoun. `/debrief` and `/sync-kb` repeat the rule where they write follow-ups, people pages, and source notes.
- `/debrief` runs every spoken deadline ("by Thursday") through `brain.py when` before writing the follow-up, and notes who asked whom in people.md.
- `/learn` reads the project's follow-ups and status rows while gathering, and names anything late or waiting in its check-in.
- `/briefing` keeps only the due script's items under its date-window label, and `/sync-kb` runs `brain.py when` on any date that has no year.
- `brain.py due` also lists your items just past the due-soon window, with their weekdays, so a brief quotes them instead of working one out.
- A finishing check, `brain.py check`, ends any task that writes files. It lists every file the session changed or moved, so your intern reports exactly what it wrote, verifies each weekday against its date, and flags pronouns no source gave. Dates are plain dates unless a script printed the weekday, and a commitment never gets a recipient or a date the source didn't state.
- The date rule covers every date your intern writes: deadlines quoted from notes, placeholder dates, and checkpoints read from records all come from `brain.py when`. `/learn` quotes a status row's fields separately, with the date it was last updated, and writes plain dates unless a script printed the weekday.

## 1.3.1

- `/learn` builds a 101 lesson on any topic from your own sources: your project folder, your notes, and read-only searches of connected tools. You get one HTML file with a 30-second version you can say out loud, the mix-up people get wrong, the line to use if someone asks, and a quiz that explains every miss. It checks the sources and the mix-up with you before it writes anything. 28 commands now.
- The inbox does more of the work. `/briefing` and `/pulse` tell you when files are waiting in 1-Inbox and offer to file them, `/debrief` looks there first instead of asking you to paste, and "file my inbox" files everything waiting. Setup offers a shortcut to the inbox on your desktop, so saving something for your intern is one drag.
- The README leads with what everyone deals with (too many meetings, too many projects) instead of only new hires, and shows the inbox in action.

## 1.3.0 (first public release)

- Guided, click-through setup for people who have never connected a tool: a permanent folder, multiple-choice tool pickers, one connection at a time, and a tour of what each connection unlocked.
- The new-here path: a 30-60-90 page, an org chart read from a screenshot, questions about new names, and `/who`.
- Eight core commands up front, nineteen more when you want them.
- 77 work tools in the connector catalog, with plain-English error decoding and one email to IT for everything blocked.
- An ask-first hook in the plugin: connector tools whose names send, share, change, pay for, or delete something outside your folder ask you first, even after "always allow" in Claude Code (not yet verified in Cowork). It's a name pattern, tested in Python and JavaScript against about 200 tool names.
- Five connectors pre-listed in the plugin (Gmail, Google Calendar, Slack, Atlassian, Notion); everything else from Claude's connector directory.
- `brain.py when` turns spoken deadlines ("Thursday", "end of month") into dates and marks guesses.
- 42 behavior scenarios, with every round's results in `evals/results/`.
- Installs straight from this repo in Claude Code and Codex (`/plugin marketplace add kevinmmiddleton/unpaid-intern`), and it's also listed in my [claude-plugins](https://github.com/kevinmmiddleton/claude-plugins) catalog.
- A Codex and ChatGPT manifest: the same skill installs and loads in Codex from this repo.
- `brain.py when` hears hedges: "Thursday I think", "Friday?", and "end of month-ish" come back as guesses.
- Works without Python (step-by-step fallback) and without installs (the no-install kit).
