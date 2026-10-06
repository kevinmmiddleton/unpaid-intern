# Microsoft 365 playbook

Contents

- Routes at a glance
- Claude's Microsoft 365 connector
- Microsoft's own servers
- Office add-ins
- Teams meeting transcripts
- OneNote, Loop, Planner, and To Do
- Fallbacks when nothing is approved
- Using it in the daily commands
- Gotchas

Checked against Anthropic and Microsoft documentation in October 2026. Confirm in Claude's connector directory before relying on details.

## Routes at a glance

| Need | Best route | Admin gate | Fallback |
|---|---|---|---|
| Outlook mail and calendar | Claude's Microsoft 365 connector | Global Admin consent once per tenant | Claude in Chrome on Outlook on the web; save to PDF and drop |
| Teams chats, channels, meeting transcripts | Same connector | Same | Download the transcript from the meeting and drop it |
| SharePoint and OneDrive files | Same connector | Same | Download and drop |
| Working inside one document | Claude add-ins for Excel, Word, PowerPoint, Outlook | Marketplace install, sometimes admin-deployed | Copy and paste |
| OneNote, Loop, To Do | No reliable connector read | n/a | Export to PDF or Word and drop |
| Organizations on Microsoft 365 Copilot | Microsoft's own Work IQ servers | Copilot license, an app registration, admin approval | Claude's connector |

## Claude's Microsoft 365 connector

Built by Anthropic. Signs in with the user's Microsoft work account (delegated sign-in), so it sees only what the user can see.

- **Reads:** mail (including shared mailboxes), calendar, Teams chats and channels the user belongs to, meeting transcripts and recordings where available, and Office, PDF, and text files in SharePoint and OneDrive.
- **Writes:** off by default. If an admin enables them: draft and send mail, inbox rules, calendar changes, file updates, and Teams posts (each Teams send asks first). Keep them off unless the guardrail profile says otherwise.
- **Accounts:** work or school accounts only. Personal outlook.com, hotmail.com, and live.com accounts do not work.
- **Admin steps:** a Global Admin grants consent once for the whole tenant. On Claude Team and Enterprise plans an Owner also adds the connector. Write tools need a second consent plus an org setting.
- **Endpoint:** listed in Claude's directory as Microsoft 365. Use the directory entry rather than a hand-typed URL.

## Microsoft's own servers

Microsoft publishes Work IQ servers (mail, calendar, Teams, SharePoint, OneDrive, Word, people) for agents inside Microsoft's ecosystem. They need a Microsoft 365 Copilot license, an app registration in Entra ID, and admin approval in the Microsoft 365 admin center. Worth it only for organizations already standardized on Copilot; otherwise Claude's connector is simpler.

## Office add-ins

Claude add-ins for Excel, Word, and PowerPoint (with Outlook in beta) install from Microsoft's marketplace on paid Claude plans. They work on the open document, which makes them the quickest win where tenant-wide connectors are not approved. Some organizations require an admin to deploy add-ins.

## Teams meeting transcripts

- With the connector: ask for the transcript of a named meeting, then run `/debrief`.
- Without it: in the meeting's chat or recap, download the transcript (VTT or Word) and save it to `1-Inbox/`.
- Transcripts exist only if transcription or recording was on. Speaker labels can be wrong; `/debrief` marks doubtful attributions `[inferred]`.

## OneNote, Loop, Planner, and To Do

- **OneNote:** pages may appear in search but cannot be read through the connector. Export the page or section to PDF or Word and drop it.
- **Loop:** no first-party connector read found. Copy the content or export it.
- **Planner:** Microsoft has announced an MCP server; details were not verifiable in October 2026. Until then, export the plan to Excel and drop it.
- **To Do:** no official connector. Copy tasks into `Memory/followups.md` with `/capture`.

## Fallbacks when nothing is approved

- **Browser route:** Claude in Chrome on Outlook on the web and Teams on the web, if the company allows the extension.
- **Mail:** "Save as PDF" or copy the thread text into the drop folder. Never forward work mail to a personal address.
- **Daily digest:** an Outlook rule or search folder for "to me, unread, flagged" you check at `/briefing` time and paste from.
- **Calendar:** paste the day's agenda view, or export the calendar for the week.

## Using it in the daily commands

| Command | What to read |
|---|---|
| `/briefing` | Today's and tomorrow's calendar; unread mail addressed directly to the user; Teams mentions and direct messages ending in a question |
| `/prep` | The invite body and attachments; the last two weeks of mail and Teams threads with the attendees |
| `/debrief` | The Teams transcript for the meeting |
| `/slots` | The calendar for the next five to seven business days |
| `/triage` | Unread mail in the requested window, grouped by sender; never delete (mailboxes may be under retention or legal hold) |

## Gotchas

- Microsoft does not re-prompt for consent when the connector gains new permissions. If something newly added fails for everyone, the admin re-runs consent.
- Access cannot be limited to specific SharePoint sites.
- The Online Archive mailbox is not searched.
- Mail sent through the connector carries an "agent-initiated" marker.
- Conditional Access policies can block the connector because its traffic comes from Anthropic's cloud; Anthropic publishes the IP range for admins.
