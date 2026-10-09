# Codex fixes

New in 1.3.4: Codex fixes from a second outside field test. In Codex, your intern gives you its commands in words ("give me my briefing"), since Codex doesn't take slash commands it didn't define. Your saved connection plan in Codex now has Codex's own steps instead of Claude's. The IT email only says "Error I saw" when there was an error, and a brief keeps both dates when it mentions "next quarter".

New in 1.3.3, if you missed it: Windows and Codex fixes from the first field test. Your intern finds Python under whatever name Windows gave it, and in Codex, setup connects your tools with Codex's own plugins and commands and sets each one to ask before it changes anything.

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
