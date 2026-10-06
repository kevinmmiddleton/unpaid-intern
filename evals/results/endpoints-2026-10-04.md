# Connector endpoint check, 2026-10-04

`connect.py check` run from a Linux sandbox against every connector in the catalog that has a fixed address (58 of 77; the rest connect through Claude's directory or a company-specific address). Nothing was signed in.

What this proves and what it doesn't: a sign-in request (HTTP 401) plus the server's published protected-resource details shows the host is a live, sign-in-protected connector server. It does not prove the exact path, because many servers answer any path the same way. Only signing in proves that, and that needs a real account.

| Result | Count |
|---|---|
| Reachable, asks for sign-in, no published details | 3 |
| Reachable and identifies as a sign-in-protected connector | 52 |
| Reachable (answered without sign-in) | 1 |
| Refused from this sandbox | 2 |

| Tool | Result |
|---|---|
| Microsoft 365 (Outlook, Teams, SharePoint, OneDrive) | Reachable. It asks for sign-in, which is normal. (It didn't publish details to confirm the exact address.) |
| Slack | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Webex Meetings | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Fireflies | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Otter | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Granola | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Fathom | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| tl;dv | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Atlassian (Jira, Confluence, Loom) | Reachable. It asks for sign-in, which is normal. (It didn't publish details to confirm the exact address.) |
| Trello | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Linear | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| GitHub | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| GitLab | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Sentry | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| PagerDuty | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Datadog | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Asana | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| monday.com | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| ClickUp | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Notion | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Airtable | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Smartsheet | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Wrike | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Coda | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Guru | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Figma | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Miro | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Canva | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Lucid | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| HubSpot | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Gong | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Intercom | Reachable. It asks for sign-in, which is normal. (It didn't publish details to confirm the exact address.) |
| Box | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Dropbox | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Egnyte | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Amplitude | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Mixpanel | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Pendo | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| PostHog | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Similarweb | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| BigQuery | Reachable (HTTP 200). |
| Tableau Cloud | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Greenhouse | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Ashby | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Stripe | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| QuickBooks | Refused (HTTP 403). Often an IP allowlist or a company firewall rule. |
| Docusign | Refused (HTTP 403). Often an IP allowlist or a company firewall rule. |
| Zapier | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Make | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Apollo | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Outreach | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| ZoomInfo | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Clay | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Close | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Klaviyo | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Ahrefs | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Supermetrics | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |
| Hex | Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof. |

The two refusals (QuickBooks and Docusign) are HTTP 403 from the sandbox's network, which is what an IP allowlist or bot filter looks like. Connectors in Cowork and claude.ai connect from Anthropic's cloud, so this result doesn't predict theirs. Run `connect.py check` from Claude Code on your own computer for your network's answer.
