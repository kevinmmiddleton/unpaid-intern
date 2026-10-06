# Google Workspace playbook

Contents

- Routes at a glance
- Claude's Google connectors
- Google's own Workspace servers
- Meet transcripts
- Google Chat
- Fallbacks when nothing is approved
- Search shortcuts for the daily commands
- Gotchas

Checked against Anthropic and Google documentation in October 2026. Confirm in Claude's connector directory before relying on details.

## Routes at a glance

| Need | Best route | Admin gate | Fallback |
|---|---|---|---|
| Gmail | Claude's Gmail connector | Owner enables on Team and Enterprise; Workspace admin may need to mark Claude as trusted | Claude in Chrome on Gmail; print to PDF and drop |
| Calendar | Claude's Google Calendar connector | Same | Paste the day view |
| Drive, Docs, Sheets, Slides | Claude's Google Drive connector | Same | Download and drop |
| Meet transcripts | Drive connector (transcripts are saved as Docs) | Same | Open the transcript Doc and download it |
| Google Chat | Google's own Chat server (preview) | Developer preview plus a Google Cloud project | Copy the thread |

## Claude's Google connectors

These are Claude's connectors for Google Workspace. Each person signs in with their Google work account.

- **Gmail reads:** messages and threads; attachments appear as metadata only, so download an attachment and drop it when its contents matter.
- **Gmail writes:** send, reply, and forward exist and ask first by default. The guardrail profile still decides; the default in this skill is read only, with drafts kept in the conversation.
- **Calendar:** read calendars including shared ones; create, update, delete, and RSVP exist. Default: propose only.
- **Drive:** reads file text. Upload, share, move, and trash exist and ask first. Default: read only. Live editing of Docs, Sheets, and Slides is in beta.
- **Admin steps:** on Claude Team and Enterprise an Owner enables the connectors. If the user sees "Access blocked," a Google Workspace admin needs to mark Claude as trusted under API controls. Ask for the IT email (`connect.py it-request`) and send it.

## Google's own Workspace servers

Google also runs MCP servers for Gmail, Drive, Docs, Sheets, Slides, Calendar, Chat, and the people directory, in a developer preview. They need preview access and an OAuth client in the organization's own Google Cloud project, so they are an admin project, not a personal setup. One useful safety property: Google's Gmail server creates drafts and labels but cannot send.

## Meet transcripts

When transcription or Gemini notes are on, Meet saves them as Docs in the organizer's Drive. If the user can open the Doc, the Drive connector can read it. Then run `/debrief`. If the user was not the organizer, ask the organizer to share the transcript Doc.

## Google Chat

Claude's built-in connectors do not cover Chat. Options: Google's preview Chat server (admin project), the browser route on chat.google.com, or copying the thread into the conversation.

## Fallbacks when nothing is approved

- **Browser route:** Claude in Chrome on Gmail, Calendar, and Drive, if the extension is allowed.
- **Mail:** "Print, then Save as PDF" on a thread, or copy the text. Never forward work mail to a personal address.
- **Drive for desktop:** if the company approves it, the workspace folder can live in a synced Drive folder so files dropped from the web land where the agent reads.

## Search shortcuts for the daily commands

| Purpose | Gmail search |
|---|---|
| Asked of me, recent (then open each thread to check for a reply) | `to:me -from:me newer_than:2d -category:promotions -category:social` |
| Scheduling requests | `newer_than:2d subject:(invitation OR meeting OR call OR availability OR "find a time")` |
| A person, before `/prep` | `from:name@company.com OR to:name@company.com newer_than:14d` |
| Triage window | `is:unread newer_than:2d` |

## Gotchas

- Attachments are metadata only through the connector; download and drop what matters.
- Shared drives follow the user's own permissions; if a file is missing, check sharing before debugging the connector.
- Personal Gmail accounts work with Claude's connectors, but work data belongs in the work account the company approved.
