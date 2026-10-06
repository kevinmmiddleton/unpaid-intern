# Meetings, files, data, people, and finance tools playbook

Contents

- Meeting platforms
- Transcript and note tools
- File storage
- Product analytics
- BI and data warehouses
- HR and recruiting
- Finance, payments, and contracts
- Automation bridges
- Gotchas

Checked against vendor documentation in October 2026. Prefer Claude's connector directory over hand-typed URLs, and confirm endpoints in vendor docs before relying on them.

## Meeting platforms

| Tool | Route | Admin gate | Notes |
|---|---|---|---|
| Zoom | Zoom-built connector in Claude's directory | Paid Zoom plan; an owner or admin with privileges; AI Companion recording and summary turned on | Reads meeting search, summaries, transcripts, recordings, Team Chat, and docs, for meetings the user hosted or can access |
| Webex | Cisco's remote server for meetings | Org admin enables it in Control Hub | Reads meetings, summaries, recordings, and transcripts; can also create and change meetings, so keep writes off |
| Microsoft Teams | See `references/stack-microsoft-365.md` | | |
| Google Meet | See `references/stack-google-workspace.md` | | |

## Transcript and note tools

All of these hold verbatim conversation. Run `/debrief` on what they return and keep only what the record needs.

| Tool | Route | Read-only | Admin gate |
|---|---|---|---|
| Fireflies | Remote server (in directory) | Read tools | None documented |
| Otter | Remote server (in directory) | Read tools | Enterprise IT controls and audit log |
| Granola | Remote server (in directory) | Read | Enterprise: off by default; admins set scopes and can block transcripts |
| Fathom | Remote server (in directory) | Read-only | None documented |
| tl;dv | Remote server (in directory) | Read | Pro plan or higher |

Fallback for any of them: download the transcript and save it to `1-Inbox/`.

## File storage

| Tool | Route | Writes | Admin gate |
|---|---|---|---|
| Box | Remote server (in directory) | Yes; keep off | Admin enables it in the Admin Console |
| Dropbox | Remote server, beta (in directory) | Create, move, share, and delete: set delete to blocked | Team app controls |
| Egnyte | Remote server (in directory) | Mostly read | AI add-on plus admin toggle and client allowlist |
| SharePoint and OneDrive | See `references/stack-microsoft-365.md` | | |
| Google Drive | See `references/stack-google-workspace.md` | | |

## Product analytics

| Tool | Route | Read-only or narrowing | Notes |
|---|---|---|---|
| Amplitude | Remote server (in directory), EU endpoint available | Can edit content; set writes to need approval | Uses the user's Amplitude permissions |
| Mixpanel | Remote server (in directory), regional endpoints | Can edit the event dictionary | Org admin enables it for most accounts; reads are not audit-logged |
| Pendo | Remote server (in directory), regional endpoints | Separate read and write toggles | Subscription admin, then a Claude Owner |
| PostHog | Remote server (in directory), EU endpoint | Read-only mode, tool filters, pin to one project | Includes session replays and person data: use read-only and avoid replays |
| Similarweb | Remote server (in directory) | Read | Needs an API key and an API-enabled plan, even through the directory |

Use these for `/prep` and `/project-status` evidence: one number with its source and date, labeled `[stated]`. Never let the agent compute a metric from partial data and present it as the official number.

## BI and data warehouses

| Tool | Route | Read-only | Admin gate |
|---|---|---|---|
| Looker | Remote server, preview | Admin allowlists tools | Admin enables it and registers the client |
| Tableau | Hosted server for Tableau Cloud | Admins can exclude tools but cannot turn it off | Tableau Server customers must host their own |
| Power BI | Remote server, preview | Query only | Tenant setting; may need an Entra app |
| Snowflake | Managed server per account | Through a read-only role; keep SQL on a separate server | Admin builds the server; network policies can block cloud clients |
| BigQuery | Google remote server | Use the read-only SQL tool and deny the full one | Admin creates the client and grants the tool-user role |
| Databricks | Managed servers (Genie, SQL, functions) | Through Unity Catalog grants | Account admin creates the app |

For a second brain, the best warehouse access is a named question answered by a governed tool (a Genie space, a Cortex agent, a saved Looker explore), not open SQL.

## HR and recruiting

These hold the most sensitive data in the company: pay, identity numbers, candidate records, offers. Default: do not connect them to a personal second brain. If a recruiter or HR partner needs one, use read-only scopes, keep candidate and employee records out of the workspace, and check the company policy first.

| Tool | Route | Notes |
|---|---|---|
| Greenhouse | Remote server, beta | Read-only scopes by default; site admin connects first |
| Ashby | Remote server, beta | Narrow writes; org admin toggle; elevated-access users only |
| Workday | Early access only | Use scheduled report emails until it is generally available |
| Lever | No official server | Exports, saved reports |
| Rippling | Not verifiable in October 2026 | Report emails |

## Finance, payments, and contracts

| Tool | Route | Caution |
|---|---|---|
| Stripe | Remote server (in directory) | Write tools can move money. Use a restricted read-only key and test mode first |
| QuickBooks | Remote server (in directory, US) | Can send invoices and payment links; keep writes off |
| NetSuite | Remote server (in directory) | Needs a custom role; the Administrator role is blocked by design |
| DocuSign | Remote server, beta (in directory) | Can send envelopes; contract terms are sensitive |

Anything involving money or contracts always pauses for the user, regardless of the guardrail profile.

## Automation bridges

| Bridge | Route | Use when |
|---|---|---|
| Zapier | Remote server, beta (in directory) | A tool has no connector but has a Zapier app; expose only the actions you need |
| Make | Remote server (in directory) | Same, through Make scenarios |
| n8n | Per instance (in directory) | The company runs n8n; only workflows flagged for MCP are exposed |

Bridges move data through a third party. They need their own approval and their own entry in the guardrail profile.

## Gotchas

- Several of these use endpoints that are specific to a company's instance or region. The wrong region returns empty results or breaks data-residency rules.
- A few tools need an API key even through Claude's directory, which "web login only" companies may not allow.
- Some tools hide data on purpose (private calls, sensitive activities, blocked transcripts). Missing data is often policy, not a bug.
