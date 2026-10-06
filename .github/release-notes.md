# Your intern checks its work

New in 1.3.2: before your intern hands anything back, it runs a finishing check. The check lists every file it wrote or moved, so what it tells you it did is exactly what it did. It also verifies any weekday it wrote against the calendar, and flags any "he" or "she" a source didn't give. Dates stay plain unless a script printed the weekday, people stay "they" until a source says otherwise, and a follow-up never gets a recipient or a date the source didn't state. In the last round of behavior tests, all six runs passed.

New in 1.3.1, if you missed it: `/learn` builds you a 101 lesson on any topic from what you already have, and your intern keeps an eye on your inbox folder.

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
