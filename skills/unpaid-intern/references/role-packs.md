# Role packs

Contents

- How to use a role pack
- Product manager
- Engineering manager
- Sales and account executive
- Customer success and support
- Marketing
- Operations and program management
- Finance
- Legal
- Recruiting and HR
- Data analyst
- Designer
- Executive assistant and chief of staff
- Any people manager
- Pairing with role plugins and skills

## How to use a role pack

During setup, ask the user's role and apply the matching pack:

- **Projects table:** what a "project" means in this role (a deal, a matter, a requisition). Rows still use the same columns, so `/project-status` still works.
- **Briefing sections:** add them to the briefing line in `Setup/preferences.md`.
- **Connect first:** the one or two tools to connect first, read-only.
- **Most-used commands:** the three to teach in week one.
- **Data cautions:** add them to the never list in `Setup/guardrail-profile.md`.

Packs are starting points. The user's answers override everything here.

## Product manager

- **Projects table:** initiatives and launches; watch rows for dependencies owned by other teams.
- **Briefing sections:** decisions due this week, launches inside two weeks, open questions blocking engineering, stakeholder asks.
- **Connect first:** tracker (Jira, Linear, Asana), then mail or chat.
- **Most-used commands:** `/prep`, `/debrief`, `/write-epic`. Then `/project-status` for one-on-ones and `/grill` before a big call.
- **Data cautions:** unreleased roadmap and pricing stay in approved storage.

## Engineering manager

- **Projects table:** workstreams, migrations, incidents in follow-up.
- **Briefing sections:** on-call and incident follow-ups, reviews waiting on the user, one-on-ones today with last notes, hiring loops.
- **Connect first:** code host (read-only), tracker, then chat.
- **Most-used commands:** `/prep` for one-on-ones, `/debrief` for incident reviews, `/decision` for architecture calls.
- **Data cautions:** no secrets, credentials, or production data in the workspace; performance notes about people stay out (use the HR system).

## Sales and account executive

- **Projects table:** active deals and key accounts; Next checkpoint is the next meeting or close date.
- **Briefing sections:** meetings with customers today, deals with a next step due, follow-ups promised to buyers, renewals inside 60 days.
- **Connect first:** CRM (read-only), then calendar and mail.
- **Most-used commands:** `/prep` (account brief), `/debrief` (call to commitments), `/draft` plus `/redline` for buyer emails.
- **Data cautions:** contact details, contract terms, and pricing exceptions stay in the CRM; the workspace links to the record.

## Customer success and support

- **Projects table:** accounts in onboarding, at risk, or renewing; escalations.
- **Briefing sections:** escalations and tickets near breach, renewals inside 90 days, promises made to customers, account health score changes.
- **Connect first:** support tool or CRM (read-only), then chat.
- **Most-used commands:** `/prep` for customer calls, `/capture` for every promise, `/explain` to turn technical notes into customer-ready language.
- **Data cautions:** ticket bodies and customer personal data stay in the support tool.

## Marketing

- **Projects table:** campaigns, launches, content pieces.
- **Briefing sections:** reviews and approvals waiting on the user, launch dates inside two weeks, performance changes worth a look.
- **Connect first:** work-management tool, then analytics.
- **Most-used commands:** `/draft`, `/redline`, `/project-status`.
- **Data cautions:** unannounced launches and lead lists stay in approved storage.

## Operations and program management

- **Projects table:** programs and cross-team initiatives; risks as their own rows if they need owners.
- **Briefing sections:** milestones inside two weeks, risks without owners, dependencies waiting more than five business days, decisions needed from leadership.
- **Connect first:** tracker and wiki, then calendar.
- **Most-used commands:** `/project-status`, `/gofer`, `/week`.
- **Data cautions:** vendor contracts and pricing stay in procurement systems.

## Finance

- **Projects table:** close tasks, forecasts, audit requests, vendor reviews.
- **Briefing sections:** close calendar for the week, reconciliations waiting, approvals due, questions from leadership.
- **Connect first:** files (spreadsheets) and mail. Accounting systems only read-only and only with approval.
- **Most-used commands:** `/capture`, `/project-status`, `/redline` on anything going to leadership.
- **Data cautions:** account numbers, payroll, bank details, and anything material and non-public stay out. Never let the agent move money.

## Legal

- **Projects table:** matters and contract reviews, with counterparties as watch rows.
- **Briefing sections:** deadlines and response dates, signatures pending, requests from the business.
- **Connect first:** mail and the document store. Contract tools only with approval.
- **Most-used commands:** `/capture`, `/decision`, `/explain` (for translating legal positions to the business).
- **Data cautions:** privileged material stays out of the workspace entirely. Label anything sensitive and check the firm or company policy before connecting anything.

## Recruiting and HR

- **Projects table:** open requisitions and HR programs, not individual candidates or employees.
- **Briefing sections:** interviews today, feedback overdue from interviewers, offers in flight, program deadlines.
- **Connect first:** calendar and mail. Applicant tracking or HR systems only read-only and only with approval.
- **Most-used commands:** `/slots`, `/prep`, `/capture`.
- **Data cautions:** candidate and employee records, compensation, and health information never go in the workspace. Refer to people by role and requisition.

## Data analyst

- **Projects table:** analyses and recurring reports; stakeholders as people rows.
- **Briefing sections:** requests waiting, dashboards that broke, reviews due.
- **Connect first:** a governed analytics or warehouse tool (read-only), then the tracker.
- **Most-used commands:** `/capture` for requests, `/explain` for turning results into plain English, `/redline` before results go to leadership.
- **Data cautions:** no row-level personal data in the workspace; record the query and the source, not the extract.

## Designer

- **Projects table:** design projects and reviews.
- **Briefing sections:** reviews and critiques today, feedback waiting, handoffs due.
- **Connect first:** design tool (read), then tracker or chat.
- **Most-used commands:** `/debrief` for critiques, `/capture`, `/decision` for design calls with the reasoning.
- **Data cautions:** unreleased designs stay in the design tool; the workspace links to them.

## Executive assistant and chief of staff

- **Projects table:** the principal's priorities and recurring operating rhythms.
- **Briefing sections:** the principal's day with prep, conflicts to resolve, decisions the principal owes, follow-ups from leadership meetings.
- **Connect first:** calendar and mail (delegated access only if policy allows), then chat.
- **Most-used commands:** `/slots`, `/prep`, `/gofer`.
- **Data cautions:** delegated access follows the principal's rules; never send as the principal without explicit approval of the exact message.

## Any people manager

Add to any pack:

- A watch row per direct report's main project (not a row per person).
- `/prep` for one-on-ones pulls last notes, open follow-ups both ways, and decisions since last time.
- Performance, compensation, and personal matters stay out of the workspace; record only agreed actions.

## Pairing with role plugins and skills

Anthropic publishes role plugins for Claude and Claude Code. Verified names in October 2026: `product-management`, `engineering`, `sales`, `customer-support`, `marketing`, `operations`, `finance`, `legal`, `human-resources`, `data`, `design`, `productivity`, and `enterprise-search`. Useful general skills include the built-in document skills (Word, Excel, PowerPoint, PDF), `skill-creator`, `internal-comms`, and `doc-coauthoring`.

- In Claude: Customize, then Plugins, then browse or add a marketplace.
- In Claude Code: `/plugin marketplace add anthropics/knowledge-work-plugins`, then `/plugin install <name>@knowledge-work-plugins`.

How they fit: this skill is the memory and the daily loop; role plugins are specialist procedures. Let a role plugin draft the forecast or the contract review; let this skill log the decision and the follow-ups.

Watch for collisions. Some plugins create their own `CLAUDE.md`, memory folder, or task file when started. Run those start commands in a different folder, or skip them inside this workspace.

Treat any third-party plugin or skill as software: read it before installing it (see `references/trust-and-safety.md`).
