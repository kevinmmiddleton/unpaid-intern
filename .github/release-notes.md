# Notes the next chat can find

New in 1.3.8: in the ChatGPT desktop app, setup makes sure your notes live in a Work chat's project folder, so every chat in that project finds them. A chat with no project works in a folder made just for it, and setup now sends you to a project chat before it makes anything. Also new this week (1.3.7): in Codex, the plugin no longer brings Atlassian and Notion connectors; setup connects only the tools you use.

If you're new here: your intern reads everything you hand it, preps your meetings, keeps your follow-ups, and never asks for a reference letter.

**Pick the line for where you work:**

- **Cowork:** download `unpaid-intern.plugin`. In Claude, open Customize, then Plugins, click + Add, choose Upload plugin, and pick the file. Then say "set me up."
- **Claude Code:** no download needed. Run `/plugin marketplace add kevinmmiddleton/unpaid-intern`, then `/plugin install unpaid-intern@unpaid-intern`.
- **Codex in the ChatGPT desktop app:** open Plugins, click Add, then Add a marketplace, enter `kevinmmiddleton/unpaid-intern`, and install Unpaid Intern. Use it in a Work chat.
- **Codex CLI:** run `codex plugin marketplace add kevinmmiddleton/unpaid-intern`, then `codex plugin add unpaid-intern@unpaid-intern`.
- **claude.ai or the Claude app:** download `unpaid-intern.zip` and upload it under Customize, then Skills. Code execution has to be on.
- **Microsoft Copilot, ChatGPT, Gemini, or no installs allowed:** download `unpaid-intern-no-install-kit.zip` and follow the README inside.
- **Cursor, GitHub Copilot, Gemini CLI, and other coding agents:** run `npx skills add kevinmmiddleton/unpaid-intern`.

It works on day one with nothing connected: paste a transcript, drop in a PDF, ask who someone is. Connecting your work tools is optional, and if one won't connect, your intern tells you what the error means and writes the email to IT. Some companies need an admin to approve a tool first, which can take a few days.

What's inside is in the [README](https://github.com/kevinmmiddleton/unpaid-intern#readme). Changes are in the [changelog](https://github.com/kevinmmiddleton/unpaid-intern/blob/main/CHANGELOG.md).
