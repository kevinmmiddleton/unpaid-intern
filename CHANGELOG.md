# Changelog

## Unreleased

- People stay "they" until a source gives a pronoun. `/debrief` and `/sync-kb` repeat the rule where they write follow-ups, people pages, and source notes.
- `/debrief` runs every spoken deadline ("by Thursday") through `brain.py when` before writing the follow-up, and notes who asked whom in people.md.
- `/learn` reads the project's follow-ups and status rows while gathering, and names anything late or waiting in its check-in.

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
