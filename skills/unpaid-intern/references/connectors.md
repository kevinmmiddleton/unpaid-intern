# Connecting work tools

Contents

- The short version
- The plugin and the catalog
- The routes, from best to fallback
- When IT only allows web logins
- Least privilege
- Locking it down
- What happens behind the scenes
- Claude plan and admin rules
- Other assistants
- Asking IT
- Testing a new connection
- When a connector fails
- Which playbook to read
- Keeping this current

Landscape verified in October 2026. Connectors change monthly; confirm against the vendor's docs and Claude's connector directory before relying on any endpoint.

## The short version

- Everything in this skill works with no connectors at all, from pasted text and dropped files.
- In setup, the user picks every tool they use; the agent connects them one at a time, easiest first, read-only, and moves past any that fail. `references/setup.md` has the flow.
- Most official connectors now sign in through the user's normal work login (OAuth or SSO), so the same web login IT already allows is the key. The catch: almost every one needs a one-time approval from an admin before anyone can use it.
- The workspace is the memory. Connectors are just faster ways to fill it.

## The plugin and the catalog

- **The catalog** (`connectors/catalog.json`) is the single source of truth: 77 tools, each with how it connects, the admin step, the read-only option, the fallback, and the vendor guide. `connect.py` reads it; the playbooks explain it.
- **The plugin build** pre-lists five connectors most offices use: Gmail, Google Calendar, Slack, Atlassian (Jira and Confluence), and Notion. The entries are the same ones Anthropic ships in its own plugins. After installing, they show as needing sign-in. Tell the user to sign in to the ones they use and ignore the rest; nothing connects until they sign in. Everything else (Asana, Linear, monday.com, ClickUp, Box, Microsoft 365, and the rest) comes from Claude's connector directory. In Claude Code, Gmail and Google Calendar come from the user's Claude account instead: connect them on claude.ai with the same account and they show up in `/mcp`.
- **Microsoft 365, Google Drive, Zoom, and most others** are added from Claude's connector directory. Microsoft 365 is left out of the plugin on purpose: its sign-in is registered with each company's Microsoft tenant, so the directory is the reliable route. In Cowork, when a connector suggestion tool is available, use it to put a Connect button in front of the user.

## The routes, from best to fallback

| Route | What it is | What it needs | Watch out for |
|---|---|---|---|
| 1. Paste and drop | Copy text in, or save files to `1-Inbox/` | Nothing | Manual, but always works |
| 2. Directory connector | A connector listed in Claude's directory (Microsoft 365, Google Workspace, Slack, Atlassian, Notion, and many more) | The user's work login; often a one-time admin approval | Read-only by default for many; check each tool's write settings |
| 3. Custom connector | The vendor's own remote MCP server, added by URL | URL plus the user's work login; on Team or Enterprise plans an Owner adds it | Auth settings cannot be edited later; remove and re-add |
| 4. Browser route | Claude in Chrome works inside pages the user is already logged into | A paid Claude plan, Chrome, and the extension allowed by IT | Higher prompt-injection risk; admins can block sites; slower |
| 5. Office add-ins | Claude inside Excel, Word, PowerPoint, and Outlook | Installed from Microsoft's marketplace, sometimes deployed by an admin | Works on the open document, not the whole tenant |
| 6. Scheduled exports | The tool emails or saves a report into a folder the agent reads | A saved filter, report subscription, or export | Data is as fresh as the schedule; the integration that needs no integration |
| 7. Automation bridge | Zapier, Make, or n8n exposes chosen actions as a connector | Approval for the bridge itself | Data passes through a third party; needs its own review |

Never, on a work account, without explicit approval: forward work mail to a personal address, create personal API tokens, run unofficial community servers on a work machine, or script around a login page.

## When IT only allows web logins

When someone asks whether it can work at all, first give the whole ladder in one line each (the directory connector with one admin approval, the email to IT, Claude in Chrome if IT allows browser extensions, then exports or paste), then start at step 1. Walk the steps in order and stop at the first route that works.

1. **Is the user's Claude account provided by the company?** If not, stop connecting work systems and see the policy check in `references/setup.md`.
2. **Look in Claude's connector directory** (Customize, then Connectors, then browse). If the tool is listed, connect it and sign in with the normal work login. On Team and Enterprise plans a member may see a Request button instead; that sends the request to the Owner.
3. **Read the error.** These all mean "an admin must approve this once," not "you are blocked forever":
   - "Your site admin must authorize this app" (Atlassian)
   - "Access blocked" or "This app is blocked" (Google Workspace)
   - "Need admin approval" (Microsoft 365)
   - A notice that a workspace admin must approve the app (Slack and many others)
   Run `connect.py diagnose "<message>" --tool <id>` to confirm, mark the tool `needs-admin`, and let `connect.py it-request` write the email.
4. **If the admin says no to connectors** but allows browser extensions, use the browser route for read-only work.
5. **If extensions are blocked too,** look for an Office add-in (Microsoft shops) or a scheduled export: a saved tracker filter emailed daily, a report subscription, a transcript folder. Point it at `1-Inbox/`.
6. **If the tool lives behind a VPN** (for example an on-premises tracker), cloud connectors cannot reach it because they run from Anthropic's cloud, not the user's laptop. Use exports, or ask IT whether Anthropic's option for private-network servers is available on the company plan.
7. **Otherwise,** paste and drop. Everything still works.

## Least privilege

- **Use a read-only option when one exists.** Verified examples: Linear and Lucid offer a read-only endpoint; GitHub offers a read-only endpoint; Salesforce has a read-only server; BigQuery has a read-only SQL tool; Pendo and PostHog have read-only modes; Greenhouse starts with read-only scopes; Coda and Stripe support read-only keys.
- **Otherwise, turn write tools to "Needs approval" or "Blocked"** in Claude's per-tool connector settings. Exact steps: "Locking it down" below.
- **Pick the narrowest scope at sign-in** when offered: specific Airtable bases, specific Trello workspaces, one Miro team.
- **Use the regional endpoint** when company data must stay in a region (several analytics and support tools publish separate EU addresses).
- **Record what is connected and how** in `Setup/guardrail-profile.md`, with the date.

## Locking it down

Do this right after each tool connects, before the test read. It takes a minute and it is the difference between "the intern can draft" and "the intern can send."

**In Claude (claude.ai, Claude Desktop, and Cowork):**

1. Open **Customize**, then **Connectors**, and click the tool you just connected.
2. Under its tool permissions, find every tool whose name starts with or contains send, reply, forward, post, share, invite, delete, trash, remove, move, create, update, or edit.
3. Set each one to **Needs approval** (or **Blocked** if the person never wants the intern near it). Leave search, read, get, list, and fetch tools alone.
4. Draft tools (create_draft, update_draft) can stay as they are: a draft never sends.

On Team and Enterprise plans, an admin may have already set a stricter ceiling; the person can always choose stricter, never looser. Menu names drift; if they don't match, look for the connector's tool list and its per-tool setting.

What to look for in the tools most offices connect (names change, so read the list rather than trusting this one):

| Tool | Set to Needs approval or Blocked |
|---|---|
| Gmail | send, reply, forward, trash |
| Google Calendar | create event, update event, delete event, respond to event |
| Google Drive | share, trash, create or update file |
| Microsoft 365 | anything that sends mail, posts to Teams, or changes files, if the connector offers it (the directory version is mostly search and read) |
| Slack | send message, schedule message, create canvas |
| Jira and Confluence | create, edit, transition, or comment on issues; create or update pages |
| Notion | create, update, move, or duplicate pages; create comments |
| Asana, monday.com, ClickUp | create, update, or delete tasks or items; comments |
| Linear | create, update, and comment tools. (In Claude Code, the connector file `mcp-json` writes uses Linear's read-only address, which has none.) |
| Box, Dropbox | upload, delete, share |

**In Claude Code:** the per-tool settings on claude.ai do not carry over to Claude Code sessions, so write tools can run without a prompt there. The Unpaid Intern plugin closes that gap with its ask-first hook (see `references/trust-and-safety.md`). Without the plugin, add `permissions.ask` rules for each write tool to `.claude/settings.local.json`, for example `"ask": ["mcp__slack__slack_send_message"]`.

**In Codex:** the plugin's ask-first hook doesn't run there (Codex reports its "ask" as unsupported and lets the tool run). Set each connected tool to ask before writes with `default_tools_approval_mode = "writes"` in Codex's config; the exact lines are in step 3 of 5c in `references/setup.md`.

Then add the row to the Connected tools table in `Setup/guardrail-profile.md`, with scope "read, ask first".

## What happens behind the scenes

- **Connector traffic comes from Anthropic's cloud,** not the user's computer. That is why servers behind a VPN fail, why vendor IP allowlists can block a connection without a clear error, and why some Microsoft tenants need Conditional Access adjusted for Anthropic's published IP range.
- **Sign-in is per person.** After an admin approves the app, each person signs in and sees only what their own account can see.
- **Some vendors meter it.** MCP calls can count against API limits, AI credits, or seat-based quotas (for example design tools with tight limits on viewer seats). If a connector stops partway through the day, check limits before debugging.
- **Claude Code and Codex are the exception.** They connect from the user's own computer, so VPNs, company proxies, and traffic inspection matter there and not in the Claude apps. `connect.py check` tests the network from that computer. The usual fixes come from IT: a proxy address for `HTTPS_PROXY`, and the company root certificate for `NODE_EXTRA_CA_CERTS` (Claude Code) or `CODEX_CA_CERTIFICATE` (Codex).
- **Writes are a separate decision.** Several connectors ship with write tools off until an admin turns them on. Leave them off unless the guardrail profile says otherwise.

## Claude plan and admin rules

As documented in October 2026; menus may differ as products change.

| Plan | Custom connectors | Notes |
|---|---|---|
| Free | One | Directory connectors vary by tool |
| Pro and Max | Add under Customize, then Connectors | Claude in Chrome available |
| Team | Owners and Primary Owners add; members request and then sign in individually | Owners can turn custom connectors off org-wide |
| Enterprise | Owners or a custom role with that permission | Admins control extensions, skills, and plugins; skill scanning may be on |

Skills need code execution turned on (Free, Pro, Max: in settings; Team and Enterprise: an Owner enables it).

## Other assistants

The workspace is plain files plus `AGENTS.md`, so it travels.

- **ChatGPT:** built-in apps for Gmail, Google Calendar, Drive, Outlook, Teams, SharePoint, and Slack. Custom MCP servers through developer mode, which admins enable on business plans.
- **Microsoft 365 Copilot:** reads Microsoft 365 natively. Outside tools come in through Copilot connectors, and Copilot Studio can add MCP tools.
- **Gemini Enterprise:** connectors for Google and Microsoft sources, with custom MCP servers in preview.
- **Coding agents** (Codex, Cursor, Copilot coding agent, Gemini CLI, Windsurf): open the workspace folder; they read `AGENTS.md`.

## Asking IT

`connect.py it-request --write` builds one email from everything marked `needs-admin` or `failed`, with each tool's admin step, read-only option, vendor guide, and the exact error the user saw. `Setup/it-request.md` is the blank version for anything the script does not know. What makes a yes likely:

- Keep the list short and put the most important tool first. If it runs past four or five tools, send the top two now and the rest after the pilot.
- Name the official vendor documentation and the read-only option.
- Say sign-in is per person, so nobody sees more than they already can.
- Say it runs in the company's AI account, not a personal one.
- Say how to undo it.
- Offer a two-week pilot and a short report on time saved.

## Testing a new connection

1. Confirm write and send tools are off or set to need approval.
2. Ask first, then run one harmless read: the titles of the next three meetings, how many unread messages arrived today, or how many open tickets are assigned to the user.
3. Ask what it can see, to confirm the scope matches expectations.
4. Record the connection, scope, and date in `Setup/guardrail-profile.md`, and run `connect.py mark <id> connected`.
5. Re-run `connect.py tour --write` and tell the user in one line what the connection just unlocked.

## When a connector fails

During setup: get the exact message or a screenshot (never passwords or codes), run `connect.py diagnose`, explain it in two lines, mark the tool, give the fallback, and move on to the next tool.

During daily work: say so in one line, name what is missing, and continue from files. Never stall and never fill the gap with guesses. Then check `references/troubleshooting.md`.

## Which playbook to read

| Tools | Playbook |
|---|---|
| Outlook, Teams, SharePoint, OneDrive, OneNote, Loop, Planner, To Do | `references/stack-microsoft-365.md` |
| Gmail, Calendar, Drive, Docs, Sheets, Slides, Chat, Meet | `references/stack-google-workspace.md` |
| Jira, Confluence, Loom, Linear, GitHub, GitLab, Azure DevOps, Sentry | `references/stack-dev-and-tracking.md` |
| Slack, Asana, monday.com, ClickUp, Notion, Airtable, Smartsheet, Trello, Wrike, Coda, Basecamp, Figma, Miro, Canva, Lucid | `references/stack-work-management.md` |
| Salesforce, HubSpot, Gong, Zendesk, Intercom, ServiceNow, Freshdesk, Freshservice | `references/stack-revenue-and-support.md` |
| Zoom, Webex, Fireflies, Otter, Granola, Fathom, tl;dv, Box, Dropbox, Egnyte, Amplitude, Mixpanel, Pendo, PostHog, Similarweb, Looker, Tableau, Power BI, Snowflake, BigQuery, Databricks, Workday, Greenhouse, Ashby, Lever, Rippling, Stripe, QuickBooks, NetSuite, DocuSign, Zapier, Make, n8n | `references/stack-meetings-files-data.md` |

## Keeping this current

- Prefer the listing in Claude's connector directory over a hand-typed URL.
- Update `connectors/catalog.json` first, then the playbook. `connect.py selftest` checks the catalog, and inside the plugin it checks that the plugin's connector list still matches.
- Endpoints in the playbooks were checked against vendor documentation in October 2026. If one fails, check the vendor's current docs before assuming the user did something wrong.
- When a correction is confirmed, update the playbook and note the date.
