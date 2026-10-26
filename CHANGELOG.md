# Changelog

## 1.3.9

Fixes from a Windows test of 1.3.8 in the ChatGPT app's Codex.

- **Windows Python:** the setup notes now name the error a Microsoft Store shortcut can give ("The file cannot be accessed by the system"), so your intern moves straight on to `py -3`, which worked.
- **Your intern does the steps it can do itself** (opening a file, running a check) instead of handing them to you, and gives the full path when you do need to open or check a file.
- **The self-test names any check it can't run on your computer.** On Windows, the symlink check needs admin rights or Developer Mode, so the count was one short with no explanation.

## 1.3.8

- **In the ChatGPT desktop app, your notes stay where the next chat can find them.** A Work chat with no project works in a folder the app makes for that one chat, and the next chat gets a new one, so notes set up there were out of reach a chat later. Setup now sends you to a Work chat with a project on your notes folder first, and `brain.py init` won't set up in one of those per-chat folders.

## 1.3.7

Connectors when you want them, not before.

- **In Codex, the plugin no longer brings Atlassian and Notion connectors.** Codex started both at every session, so anyone who doesn't use them got two sign-in errors each time, and installing in the ChatGPT app opened a sign-in page. Now setup asks which tools you use and connects only those, Atlassian and Notion included, the same way as every other tool. Cowork and Claude Code keep their five pre-listed connectors, which wait quietly until you sign in.
- **Connected Atlassian or Notion through the plugin in Codex?** After you update, ask your intern to connect it again ("connect Jira"). It takes one command, and your notes don't change.
- **Install steps for the ChatGPT desktop app:** Plugins, Add, Add a marketplace, then use the plugin in a Work chat. In a Chat conversation (where the plugin's Try now goes), the plugin doesn't load.

## 1.3.6

Fixes from a real Codex test: 21 turns of setup and everyday use on GPT-6.1 Sol, with nothing connected. Then the same turns again on the fixes, and once more on what that second run still caught.

- **Setup asks your name first,** so a debrief files your own promises as yours. Before, it could log one as something you were waiting on from yourself.
- **Your intern leaves its scripts' files alone.** The connection plan, the IT email, and the cheat sheet change only by re-running the script, and the check at the end of each task catches a hand edit. A hand-rewritten plan had lost its Codex steps, which also switched the cheat sheet back to slash commands.
- **Labels like `[stated]` stay in your files.** Chat and the status table you paste say it in plain words.
- **The status table is the one the script built,** with its notes on top, including any project whose status nobody has confirmed yet.
- **"Explain this" adds new terms to your glossary** every time: defined ones as confirmed, the rest as guesses. A new `brain.py term` command writes every glossary row, so a term lands in the right table with the right columns, moves up when it's confirmed, and a different meaning never overwrites the one you have. Your intern names the terms it added, and leaves everyday words out.
- **People and glossary tables stay tables.** The end-of-task check and the health check catch a row cut off by a blank line, or one with the wrong number of columns.
- **A stray character after a `since:` date** no longer turns off the "waiting N days" count, and the end-of-task check flags a follow-up line the tools can't read.
- **No guessed pronouns in chat** either, and no em dashes or HTML tags in replies.
- **Sorting your inbox writes nothing,** not even the day log.
- **More spoken dates:** "this coming Friday", "Monday morning", "first thing Tuesday", and "Thursday at 2pm".
- **Setup lists its steps' beats in order,** so the inbox shortcut, "Anything missing?", and the rest don't get skipped. The tool matcher now prints the "Anything missing?" line itself, and setup's first status table is the script's.
- **The product and marketing role packs say "company storage"** and count your workspace as company storage when setup recorded a company account, so a debrief no longer stops to ask whether the folder is approved.
- **In Codex,** the README says what the Atlassian and Notion connectors do before you sign in (a sign-in error at the start of each session) and how to turn one off.
- **The no-install kit works in ChatGPT Projects** (tested): add the files as Sources, choose Stay in Chat if it offers Work, and pick project-only memory.
- **Set up before 1.3.6?** The health check says your workspace's rules file (AGENTS.md) is missing the newer rules, and your intern offers to update it. It changes your standing rules, so it asks first.

## 1.3.5

Two fixes that were ready before 1.3.4 but didn't make it in.

- Your intern pauses before it sends or shares anything about money, contracts, legal, HR, or security, instead of before it reads or files notes about them. Reading those and filing notes in your folder no longer waits for a yes; sending, sharing, signing, and paying still do. Setup's question 15, the guardrail profile it writes, and the note on finance and contract tools all say it this way.
- In Codex, the client-ID route is in the right order. Codex opens the sign-in in the same command that prints the callback URL, so if your admin hasn't allowed that URL yet, send it to them and run `codex mcp login` once they have. Setup also says never to quote the client secret Codex saves in its config.
- The README shows four animated pictures, and the `.plugin` file always keeps the screenshots `plugin.json` lists, whatever the README shows.

## 1.3.4

Codex fixes from a second outside field test, on Windows.

- In Codex, your intern gives you its commands in words. Codex only takes its own slash commands, so typing `/briefing` there gets "Unrecognized command", while "give me my briefing" works. Setup, the tour, the cheat sheet, START-HERE, and the README's Codex steps all say it that way in Codex, and every command has a plain-language form (in `references/what-you-unlock.md`) that runs the same procedure.
- The connection plan has a real Codex version: `connect.py plan --surface codex`. The saved plan says it's for Codex and gives Codex's steps for each tool: its own plugin directory (`/plugins`) first, otherwise `codex mcp add` and `codex mcp login`, then setting the tool to ask before writes in Codex's config. It no longer carries Claude's steps, so the file stays right when you reopen it later. Atlassian and Notion, which come with the plugin, just need a sign-in.
- With a Codex plan, the IT email names Codex and the tour says commands in words, without being told.
- The IT email says "Error I saw" only for an error a connection attempt actually showed (`connect.py mark --error`, or a failed attempt). Any other note, like "admin approval required", goes in as a plain "Note".
- When a brief mentions a vague span like "next quarter", it keeps both dates `brain.py when` printed: "Q1 2027 (estimate), 2027-01-01 to 2027-03-31".

Thanks to Clint for two rounds of Windows and Codex field testing.

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
