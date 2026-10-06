# Changelog

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
