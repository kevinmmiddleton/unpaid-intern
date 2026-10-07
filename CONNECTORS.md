# Connectors

A connector is the link between Claude and one of your work tools. Every connector here signs in with your own work login, so it only sees what you can already see. Nothing connects until you sign in.

## Listed by this plugin

These five show up as soon as the plugin is installed. Sign in to the ones you use and ignore the rest; nothing connects until you sign in. The entries match the ones Anthropic ships in its own plugins.

| Category | Tool | Good to know |
|---|---|---|
| Email | Gmail | Your Google Workspace admin may need to mark Claude as trusted |
| Calendar | Google Calendar | Same as Gmail |
| Chat | Slack | A Slack workspace admin approves the app once |
| Tracker and wiki | Atlassian (Jira, Confluence, Loom) | A site admin approves it once for the whole company |
| Wiki and docs | Notion | Enterprise workspaces can limit which AI apps connect |

## From Claude's connector directory

Setup walks you to these. They are not pre-listed, either because their sign-in is set up per company or because the directory listing is the reliable route.

| Category | Tools |
|---|---|
| Microsoft 365 | Outlook, Teams, SharePoint, and OneDrive in one sign-in. A Microsoft Global Admin approves it once. |
| Trackers | Asana, Linear (in Claude Code, setup uses its read-only address), monday.com, ClickUp, Smartsheet, Airtable |
| Google and files | Google Drive (also covers Docs, Sheets, Slides, and Meet transcripts), Box, Dropbox |
| Meetings | Zoom, Fireflies, Otter, Granola, Fathom, tl;dv |
| Design | Figma, Miro, Lucid, Canva |
| Customers and support | Salesforce (an admin turns it on first), HubSpot, Intercom, Freshservice |
| Everything else | 77 tools in all, including analytics, data, engineering, HR, finance, and automation bridges. The full list, with the admin step, read-only option, and fallback for each, is in `skills/unpaid-intern/connectors/catalog.json`. |

## In Claude Code

Claude Code signs in from your own computer, and a few tools behave differently there:

- **Gmail and Google Calendar** show as not configured, because they come from Claude's own connectors. Connect them on claude.ai with the same Claude account and they appear in `/mcp`.
- **Slack, Atlassian, and Notion** sign in from `/mcp` directly.
- **Everything else:** setup can write a Claude Code connector file for this folder with read-only addresses first. Asana and Box don't let apps register themselves from Claude Code, so connect those on claude.ai with the same account instead.
- **The plugin applies everywhere.** While the plugin is enabled, its five connectors and its ask-first hook are part of every Claude Code session, not just the one in your second brain folder. Disable the plugin in `/plugin` for projects where you don't want that.

## Asking first

Two things stand between your intern and anything that sends, shares, or deletes:

1. **The connector's own settings.** Right after each tool connects, setup walks you through setting its send, share, change, and delete tools to "Needs approval." Reads stay on.
2. **The plugin's ask-first hook.** Before connector tools whose names send, post, share, delete, pay for something, run code, or create or change a ticket, page, task, event, or file, Claude stops and asks you. Reads, searches, and drafts go through. This matters most in Claude Code, where the approval settings from claude.ai don't apply and where the hook's prompt appears even after "always allow." Anthropic's docs say plugin hooks load in Cowork, but that hasn't been tested here, so the connector settings in step 1 stay your guarantee there. In Codex the hook can't ask yet, so setup sets each tool to ask before writes in Codex's own settings instead. It's a pattern over tool names, tested in Python and JavaScript against about 200 tool names, most of them from Gmail, Google Calendar and Drive, Slack, Jira and Confluence, Notion, Asana, Linear, monday.com, ClickUp, Box, GitHub, Microsoft 365, Stripe, HubSpot, Supabase, Vercel, Figma, BigQuery, PagerDuty, ServiceNow, and Zapier. A tool with an unusual name could still slip past it; that's why step 1 still counts.

## When one won't connect

Paste the error message or share a screenshot. The agent explains what it means (an admin approval, a company network rule, an expired sign-in, a personal account where a work one should be), tells you who can fix it, and writes one email to IT for everything that's blocked. You send it.

Never paste a password, a one-time code, or a token into the chat. Those go on the sign-in page only.

## If nothing gets approved

Everything still works from pasted text and dropped files. Saved filters, report emails, and exports dropped into your folder fill the same memory.
