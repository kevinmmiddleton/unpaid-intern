# CRM, revenue, and support tools playbook

Contents

- Handle with care
- Routes at a glance
- Notes on specific tools
- What belongs in the workspace
- Using them in the daily commands

Checked against vendor documentation in October 2026. Prefer Claude's connector directory over hand-typed URLs.

## Handle with care

These systems hold customer records, contact details, deal values, and ticket contents. The rules that matter most:

- **Read-only first.** Use a read-only server or scope when one exists. Otherwise set every write tool to blocked or needs approval.
- **Records stay in the source system.** Account names, your own notes, and agreed next steps are fine where policy allows. Individuals' contact details, ticket bodies, contract values, and account numbers stay in the CRM or support tool: redact them to tokens such as `[CONTACT-REDACTED]` or `[ACCOUNT-NUMBER-REDACTED]` and link to the record instead.
- **Use the regional endpoint** if the company's data must stay in a region.
- **Check the company's AI policy specifically for customer data.** Many policies allow AI for internal notes and ban it for customer records.

## Routes at a glance

| Tool | Official remote server | Read-only option | Admin gate | Fallback |
|---|---|---|---|---|
| Salesforce | Yes (in directory) | Yes: a reads-only server | Admin turns on the MCP service and each server, and creates the client app | Scheduled report emails |
| HubSpot | Yes (in directory) | No switch; uses the user's own HubSpot permissions | Custom setups need an auth app | Saved views, report emails |
| Gong | Yes | Read-only by design (answers and briefs, not raw transcripts) | Technical admin; uses Gong credits | Call brief emails |
| Intercom | Yes (in directory), with an EU endpoint | Writes limited to internal notes and articles | User consent | Exports |
| ServiceNow | Yes, built per instance by an admin | Admin chooses the tools | Plugin, Now Assist, admin role | Report emails |
| Freshdesk | Yes (API key only, not web login) | No read-only mode | Growth plan or higher | Exports |
| Freshservice | Yes (in directory) | Set per-tool approval in Claude | Plan action limits | Report emails |
| Zendesk | No documented official server as of October 2026 | n/a | n/a | Saved views exported with ID, subject, status, and SLA columns only; browser route |

## Notes on specific tools

- **Salesforce:** ask for the reads-only server specifically. The other servers can write and delete records.
- **HubSpot:** a "sensitive data" setting can hide activities; missing activity history is not a connector bug.
- **Gong:** returns summaries and answers rather than raw transcripts, and excludes private calls. Good for `/prep` on an account.
- **ServiceNow:** every instance is different. The admin decides which tools exist, so ask them what is exposed before relying on it.
- **Freshdesk:** needs an API key, which many "web login only" companies will not issue. Treat it as an admin request.
- **Zendesk:** an endpoint may respond, but there is no public documentation or announcement. Do not recommend it until Zendesk documents it.

## What belongs in the workspace

| Keep | Leave in the source system |
|---|---|
| Account-level status in your own words | Contact details, records, and ticket bodies |
| Your commitments to an account (`/capture`) | Deal values, contract terms, and account numbers |
| Decisions with the reasoning | Anything a customer wrote, beyond a short attributed quote |
| A link to the record | A copy of the record |

## Using them in the daily commands

| Command | What to read |
|---|---|
| `/briefing` | Tickets or cases assigned to the user and breaching soon; deals with a next step due today |
| `/prep` | For a customer meeting: account summary, open tickets, recent calls, last decision, open commitments both ways |
| `/debrief` | The call summary or transcript, then commitments with the customer logged as `@me` or `@waiting:Name` |
| `/draft` | Customer replies are always drafts; run `/redline` before anything goes out |
| `/gofer` | Renewals, escalations, and stalled deals sorted by what a week of waiting would cost |
