# Windows and Codex fixes

New in 1.3.3: Windows and Codex fixes from the first outside field test. Your intern finds Python under whatever name Windows gave it, and the scripts stop repeating a timezone warning. In Codex, setup now connects your tools with Codex's own plugins and commands and sets each one to ask before it changes anything. Your briefing lists everything you're waiting on, with who and when; vague deadlines like "next quarter" come back as a labeled range; and the finishing check shows each move as where it came from and where it went.

New in 1.3.2, if you missed it: before your intern hands anything back, it runs a finishing check that lists every file it wrote or moved and verifies any weekday it wrote.

If you're new here: your intern reads everything you hand it, preps your meetings, keeps your follow-ups, and never asks for a reference letter.

**Pick the line for where you work:**

- **Cowork:** download `unpaid-intern.plugin`, open it, and click Install. Then say "set me up."
- **Claude Code:** no download needed. Run `/plugin marketplace add kevinmmiddleton/unpaid-intern`, then `/plugin install unpaid-intern@unpaid-intern`.
- **Codex:** run `codex plugin marketplace add kevinmmiddleton/unpaid-intern`, then `codex plugin add unpaid-intern@unpaid-intern`.
- **claude.ai or the Claude app:** download `unpaid-intern.zip` and upload it under Customize, then Skills. Code execution has to be on.
- **Microsoft Copilot, ChatGPT, Gemini, or no installs allowed:** download `unpaid-intern-no-install-kit.zip` and follow the README inside.
- **Cursor, GitHub Copilot, Gemini CLI, and other coding agents:** run `npx skills add kevinmmiddleton/unpaid-intern`.

It works on day one with nothing connected: paste a transcript, drop in a PDF, ask who someone is. Connecting your work tools is optional, and if one won't connect, your intern tells you what the error means and writes the email to IT. Some companies need an admin to approve a tool first, which can take a few days.

What's inside is in the [README](https://github.com/kevinmmiddleton/unpaid-intern#readme). Changes are in the [changelog](https://github.com/kevinmmiddleton/unpaid-intern/blob/main/CHANGELOG.md).
