# Setup

Contents

- Who this is for
- How to ask
- Guided setup
  - Step 1: A home
  - Step 2: About them
  - Step 3: Brain dump
  - Step 4: A first win
  - Step 5: Their tools
  - Step 6: The tour and the habit
- Short on time
- Picking up where they left off
- Going deeper later
- Autonomy choices
- Policy check
- Where the workspace lives
- The first week
- Making it a habit

## Who this is for

Assume the person has never set up a connector, never opened a settings page they did not have to, and does not know what MCP means. Most of them will need help, and that is the point of this flow.

- One step per message, and keep each one short: a few lines, not a page. Say where to click in plain words. Never show raw script output; translate it into a line or two.
- Run every script yourself. Never ask the person to type a command.
- Never use jargon without a plain gloss: say "connector (the link between Claude and a tool)", not "MCP server".
- When something fails, it is the setup's fault, not theirs. Say what it means, say who can fix it, and move on.
- They can stop at any step. Progress lives in their folder, and `/setup` or `/connect` picks it up later.
- Set expectations without a stopwatch: "A few questions, a brain dump, and one real result before we connect anything. Connecting your tools comes after, and you can skip it. If your company has to approve a tool, that part can take a few days."
- If they arrived with a real task, do the task first and offer setup after.
- Write files from their answers only. Never fill a blank with a guess.

## How to ask

Use multiple-choice pickers wherever the surface has them, because clicking is easier than typing and nobody has to remember tool names.

- **Get the questions from the script** so they stay consistent: `python3 "${CLAUDE_SKILL_DIR}/scripts/connect.py" screens --screen <id> --json`. Screen ids, in the order setup uses them: `home`, `about`, `everyday`, `tracked`, `role` (add `--role "<their Role answer>"`), and `yours`.
- **With a picker** (the multiple-choice question tool in Cowork and Claude Code): send one screen per call. Each screen has at most four questions with at most four options, and every question gets an automatic Other box for typing. Keep the labels and descriptions exactly as the script gives them.
- **Without a picker** (for example a web chat): show the same questions as numbered lists (`connect.py screens --screen <id>` prints them that way), keeping the script's wording exactly, and accept replies like "1, 3" or plain words.
- **Turn answers into tools** with `connect.py match "<answer>" "<answer>" ...`. Pass the picked labels exactly, plus anything typed into Other. If it returns a follow-up (for example "Which note-taker?"), ask it next. If it returns something not in the catalog, say you will check Claude's connector directory for it, and fall back to exports if it is not there.

## Guided setup

Run this on the first visit (no `START-HERE.md` in the folder) and whenever the person runs `/setup` without a narrower request.

Open with two lines: what this is ("a folder of plain files I read and keep up to date, plus links to the tools you already use, if you want them") and what to expect (see "Who this is for"). The house intro, if it fits the moment: "Hi. I'm the intern. Let's get you set up."

The order matters: the person gets something useful in steps 3 and 4 with nothing connected. Connecting tools, the part most likely to stall on IT, comes after the first win.

### Step 1: A home

The second brain needs a folder that is still there tomorrow. Ask the `home` screen. It holds two questions: where the folder should live, and the account check.

- **Company OneDrive or Google Drive folder:** backed up and following company rules. Have them make a folder named `Second Brain` inside it.
- **Documents on this computer:** simplest, but only on this machine.
- **Not sure:** explain in two lines. A company-synced folder is backed up and follows company rules. Documents is simplest. Recommend the company folder if they have one, otherwise Documents.
- **Never** a personal cloud (personal iCloud, Dropbox, or Google Drive) for work files. Say why in one line: work files belong where the company keeps them.

Always make a dedicated `Second Brain` folder inside the place they picked. Never set up directly in Documents or in any folder that already holds other files.

Then connect it, by surface:

- **Cowork (in the Claude desktop app):** if no folder is connected, ask them to choose the folder. When the surface offers a folder-access request, use it so they get a folder picker instead of instructions. Otherwise walk them through it: open Finder (Mac) or File Explorer (Windows), go to the place they picked, make a folder called `Second Brain`, then select it in Claude.
- **Claude Code:** the folder Claude Code is running in, if it is a dedicated, empty folder. If it is a code repository or already holds other files, suggest `~/Documents/Second Brain` and starting Claude Code there.
- **Web chat:** files do not persist between chats. Explain the carry-forward routine in "Where the workspace lives", or suggest the desktop app if their company allows it.

Create the workspace: `python3 "${CLAUDE_SKILL_DIR}/scripts/brain.py" init "<folder>"`. It never overwrites anything. If Python can't run, build the same folders by hand (`references/no-python.md`).

Then one or two lines on what just appeared: 1-Inbox is where they drop things, Projects and Areas are where their work lives, and everything else is the assistant's record, explained in `START-HERE.md`.

Then offer the inbox shortcut, in one line, because it's what turns the inbox into a habit: a shortcut to 1-Inbox on their desktop, so saving a transcript, a PDF, or a screenshot for their intern is one drag. If they want it:

- **Mac:** in Finder, hold Option and Command and drag 1-Inbox onto the desktop. (Or right-click 1-Inbox, choose Make Alias, and drag the alias to the desktop.)
- **Windows:** in File Explorer, right-click 1-Inbox, then Send to, then Desktop (create shortcut).

If you can run commands on their computer (Claude Code), offer to make it for them, and only after a yes, since it writes outside the workspace. Skippable; never block setup on it.

**The account check** (the second question on the `home` screen): is this the Claude account the company gave them for work?

- **Yes, company account:** continue.
- **No, it's my own, or Not sure:** keep going, but treat it as personal. Plan the tools, write the IT request, and hold off on connecting work systems until they confirm the company allows it. Connecting work mail or chat to a personal AI account is exactly the line most AI policies draw. Keep customer, confidential, and regulated data out. See "Policy check".

Record the answer and today's date in `Setup/setup-profile.md`.

### Step 2: About them

Ask the `about` screen: their role, what they want help with first, and whether they're new to the job. Write the role to `START-HERE.md` and `Setup/setup-profile.md`, and the help-with answers to the `help first:` line in `Setup/preferences.md`. The role picks the tool screen in Step 5 and the role pack in `references/role-packs.md` (apply its projects meaning, briefing sections, and data cautions in Step 3). The help-with answers drive the first win and the tour.

**If they're new ("Yes, still ramping up"),** say one line about why this matters: ramping up means a flood of new names, acronyms, and projects, usually with an onboarding buddy who's too busy to help. Then:

- Add "Yes, still ramping up" to the `help first:` line, so the first win leads with `/who` and the tour keeps `/who` and `/explain` in view.
- Ask when they started, and run `brain.py area "Ramping up" --ramp-up --started <date>`. It makes a 30-60-90 page in 3-Areas.
- Offer the shortcut: "If you can see your org chart, take a screenshot and drop it in 1-Inbox. I'll learn who reports to whom." When one arrives, follow the org chart steps under `/who` in `references/commands.md`.

### Step 3: Brain dump

The fastest way to make the folders useful, and easier than a form.

1. Run `brain.py now`. On a desktop surface (Cowork, Claude Code), write the timezone it reports to `Setup/preferences.md` and say so in one line ("I've set your timezone to New York; tell me if that's wrong"). On the web, the sandbox's clock isn't theirs, so ask once which city's time they work in; if they skip it, note that in the day log and don't ask again this session. Leave the other preferences on their defaults until Step 6.
2. Say: "Tell me everything on your plate at work. Projects, things you owe people, things you're waiting on, the parts of your job that never end, people I should know. Talk or type, messy is fine. Ten minutes is plenty." Suggest dictation if they prefer to talk. If they're new, add: "Who have you met so far, and what do they do? Which acronyms have you been nodding along to?"
3. Turn the deadlines they actually said into dates in one call before you show anything, passing only their words, hedges included (for example `brain.py when "Thursday I think" "end of month"`); a hedge like "I think" or "maybe" comes back as a guess. For a waiting item with no date at all, pass "soon" and call the result a placeholder. Use exactly what it prints; anything it marks as a guess keeps its `~`.
4. Sort what they said into four piles and show the piles back in one short list before writing anything:
   - **Projects** (has a finish line): name, whether they own it, help with it, or keep an eye on it, and whether it's under way if they said so. Don't guess a status; a project nobody described stays "unconfirmed".
   - **Areas** (no end date): hiring, a weekly review, a team they support.
   - **Follow-ups**: what they owe and what they're waiting on, with an owner and the date from step 3. A `~` guess stays a `~` guess, in the follow-up line and in the project's next checkpoint alike.
   - **People**: who owns or decides what. Acronyms go on the glossary's open list, with the Best guess column left empty unless they offered one.
   - **From the role pack**: if it has data cautions or briefing sections, show the never-list line and the brief sections you'd add, so they confirm them with the rest.
5. Ask: "Anything wrong or missing?" Fix it. Nothing they didn't say gets added.
6. Write it: `brain.py project "<Name>" --role <own|support|watch>` for each project, up to five now (add `--status in-progress` only when they said it's under way), `brain.py area "<Name>"` for each area, follow-up lines in `Memory/followups.md` (with `since:` for waiting items and `accepted: false` unless they said the other person agreed), rows in `4-Reference/people.md`, and open acronyms in `4-Reference/glossary.md`.
7. Tell them where it all went in two lines, in folder names they can see: "Your projects are in 2-Projects, the ongoing stuff in 3-Areas, and what you owe in Memory/followups.md."

If they'd rather not do a brain dump, ask the plain question instead: "Name up to five things you're working on. For each, do you own it, help with it, or keep an eye on it?"

If the dump includes restricted details (someone's pay, a performance plan, a health issue), keep the ordinary work items and leave the details out, with one line: "Left out: the pay and performance details. Those belong in your HR system." When the work item is itself an HR, performance, or pay action about a named person (documenting someone's plan, setting someone's raise), don't log it at all; if they want a reminder, log it without the name or the detail ("weekly 1:1 notes, kept in your HR system").

Leave `Setup/guardrail-profile.md` on its safe defaults, except for the never-list line they confirmed. Leave the numbered questions in `Setup/setup-profile.md` blank until "Going deeper later" asks them.

### Step 4: A first win

Prove it works before asking for anything else.

Don't spend a turn asking which command to try. In the same message that confirms the brain dump was written, run the best match for what they asked help with, on what they just told you:

- Status updates, or nothing specific: `/project-status` on the projects from the brain dump.
- Tracking follow-ups: what's due this week, from `brain.py due`.
- Ramping up: `/who` on someone they named.
- Meeting prep and notes: `/prep` for their next meeting (ask them to paste the invite), or `/debrief` if they have a transcript handy.
- A morning brief: a first `/briefing` from the brain dump.

Then one line on what it adds once their tools are connected ("With your calendar connected, /prep finds the invite on its own"), and one line naming one other command they could try.

### Step 5: Their tools

Ask first: "Want to connect your work tools now, or later? Most take a minute or two. Anything your company has to approve, I'll put in one email to IT." Later is a fine answer: mark nothing, and `/connect` picks it up.

**5a. Pick.** Say: "Pick everything you use, even if you think IT won't allow it. I'll sort out what works." Then ask, one screen at a time:

1. `everyday`: email and calendar, chat, meetings, files.
2. `tracked`: tasks and tickets, the team wiki, design tools, customer tools.
3. `role` with `--role "<their Role answer>"`: tools specific to their kind of work. If they typed their own role into Other, skip this screen; the "Anything missing?" in the read-back covers it.

If they name their tools in their own words instead, run `connect.py match` on those words, then ask only the screens their list didn't cover (for example meetings and files). Run `connect.py match` on all the answers and ask any follow-ups it returns. Then go straight to the plan (5b) in the same turn: read the list back in one line and ask "Anything missing?" there, rather than in a turn of its own. Re-running the plan later keeps every status. Fill "Tools I actually use" in `Setup/preferences.md` from the answers.

**5b. Plan.** Run `connect.py plan --tools <ids from match> --surface <cowork|desktop|web|code> --workspace "<folder>"`. It writes `Setup/connection-plan.md` with every tool in easiest-first order, plain steps for each, and a status column. Translate its summary into three lines at most: ready to connect now; needs an admin first ("I'll write the email to IT for you at the end"); no connector yet ("We'll use exports or the browser for these").

**5c. Connect, one at a time.** Go down the plan in order. One tool per message. If they ask what a connector is, answer in one sentence. Before the first tool, always say what each connection involves, in this one complete line: "For each tool: you sign in, I walk you through setting anything that could send or delete to ask first, and then I'll ask before one small test read."

1. **Show the way in.** In Cowork, if a connector suggestion tool is available, search the connector directory for the tool and suggest it, so the person gets a Connect button instead of instructions. If the Unpaid Intern plugin is installed, the common tools are already listed under its connectors; tell them to ignore the ones they do not use. Otherwise give the plan's steps for that tool, numbered and short.
2. **Wait for "done".** Do not stack the next tool on top.
3. **Lock it down, by surface.** In Claude Code, the connector settings from claude.ai don't apply, so skip the settings walk: the plugin's ask-first hook (a `hooks/hooks.json` two folders above this skill's folder) is what asks there; if it's missing, offer to add `permissions.ask` rules ("Locking it down" in `references/connectors.md`). In Cowork, claude.ai, and Claude Desktop, walk them through every tool that sends, posts, deletes, shares, creates, or changes, using the steps under "Locking it down"; whether Cowork runs the plugin's hook hasn't been verified, so these settings are the guarantee there. Add a row to the Connected tools table in `Setup/guardrail-profile.md`: the tool, how it connected, scope "read, ask first" (the shipped default), and today's date.
4. **Test it gently.** Every tool gets a test, including the last one. End the lock-down message with the question ("Okay if I do one small test read?") and wait for their "done" on the lock-down and a yes to the test, even if they okayed the test earlier, then do one harmless read that proves access without pulling much content: calendar, the titles of the next three meetings; mail, how many unread messages arrived today; chat, the names of three channels they are in; tracker, how many open items are assigned to them; wiki or files, the name of one recently edited page or file. Say what you found in one line.
5. **Record it.** `connect.py mark <id> connected --workspace "<folder>"`.

When a tool will not connect:

- Ask them to paste the exact message or share a screenshot. Never ask for passwords, codes, or tokens.
- Run `connect.py diagnose "<the message>" --tool <id>`. Explain the top match in two lines: what it means and who can fix it.
- Mark it: `connect.py mark <id> needs-admin --note "<the message, without anything secret>"` when an admin has to act, or `failed` when the cause is unclear.
- Tell them the fallback for that tool, then move on: "Let's not let this one hold up the rest."
- A greyed-out connector or a Request button means the company's Claude Owner has to turn it on. Mark `needs-admin`.

**5d. One email to IT.** If anything is `needs-admin` or `failed`, run `connect.py it-request --workspace "<folder>" --name "<their name>" --write`. It asks for approval on the `needs-admin` tools and, separately, asks IT to look at the `failed` ones whose cause was unclear. Show them the email, point out the bracketed parts to fill in, and remind them they send it themselves. Never send it for them. Say plainly that approvals can take a few days, and that everything keeps working from files in the meantime.

If the person is on a personal account (Step 1), skip connecting work systems: mark those tools `skipped` with the note "waiting on account approval", then run `connect.py it-request --tools <those ids> --personal --workspace "<folder>" --write`. That version leads with asking for a company-approved AI account.

### Step 6: The tour and the habit

This is the payoff, and it teaches them what they now have.

1. Run `connect.py tour --workspace "<folder>" --write`. It writes `Setup/my-commands.md`, a personal cheat sheet built from what actually connected and what they asked for help with: four to start with, the rest of the core eight, and the extras kept out of the way.
2. Walk them through the "Start with these" section: four commands, one line each, naming what each one now reads for them ("`/prep` now pulls the invite and the last Teams thread"), and say the full cheat sheet is in their folder at `Setup/my-commands.md`.
3. End that same message by asking which one to try now, with the picker from `connect.py tour --workspace "<folder>" --json`, and run it for real.
4. Right after that first try, ask the `yours` screen: brief length, what the brief always covers, when the day starts, and whether they want it every weekday morning. If a reply leaves one of the four unanswered, ask that one before writing. Write `Setup/preferences.md` (brief length as the word cap: Three lines is 60, Short is 150, Fuller is 300; always include; working hours from the day-start answer). Never skip this screen.
5. Close with two lines: plain words work as well as commands, and the cheat sheet lives at `Setup/my-commands.md`.
6. If they said yes to a daily brief and the surface supports scheduled tasks, set up a weekday `/briefing` just before their day starts. First make sure send, delete, and share tools are blocked or need approval in each connector. Then ask which connected tools the brief may read without asking, and mark only those as yes in the guardrail profile. A scheduled brief reads and briefs. It never sends or changes anything.
7. Offer a weekly reset: Friday afternoon, `/week` for the week ahead, plus a short list of what's waiting in 1-Inbox and which projects look finished. It only proposes. Filing (`/sync-kb`) and archiving (`/tidy`) happen when the person says yes.
8. Hand them the first week (below) as one short list, and offer the deeper setup next week: voice, partners, and exactly what the agent is allowed to do. Keep every guardrail on its default for now; don't invite them to loosen reads or writes on day one.

## Short on time

If they say they only have a few minutes: Step 1, the `about` screen, then a first win on whatever they paste (`/explain`, or `/prep` for their next meeting). Say: "The brain dump and your tools can wait. Ask me to finish setup whenever you're ready."

## Picking up where they left off

If `START-HERE.md` exists and the person runs `/setup` or `/connect`, read `Setup/connection-plan.md`. Offer the next `to-do` tool, and re-check anything marked `needs-admin` ("Did IT approve Jira yet?"). If they want to add tools, ask the matching screen again and re-run `connect.py plan`; it keeps every status already set. Re-run `connect.py tour --write` whenever a tool connects, so the cheat sheet stays true.

## Going deeper later

Ask one question at a time. Accept "skip".

1. What are the three responsibilities that matter most?
2. Which recurring meetings should be prepped, and how deep (three lines or the full block)?
3. Who are your main partners, and what does each one own or decide?
4. What should the morning brief never include?
5. Paste three to five sentences you wrote, or describe your writing voice.
6. Which kinds of data must never be stored here, beyond the standard restricted list?

Then the autonomy questions, below. Then summarize the whole profile in plain language and wait for a yes. Only after the yes, write `Setup/setup-profile.md`, `Setup/guardrail-profile.md`, `Setup/preferences.md`, and `4-Reference/people.md`.

## Autonomy choices

Choose autonomy on purpose. Ask each one, offer the default, and record the answer in `Setup/guardrail-profile.md`.

| # | Question | Default |
|---|---|---|
| 7 | May the agent read connected systems without asking each time? Answer per system. A scheduled brief can only use systems marked yes | Ask first, until the user says yes for a system |
| 8 | May it update this workspace when asked to capture, debrief, close, or build? | Yes |
| 9 | Tracker and wiki: local draft only, or may a live yes authorize a named write? | Local draft only |
| 10 | Want one finishing word that confirms an external update the agent just listed in full, without a second pause? It never sends anything | None |
| 11 | Keep a backup copy before changing anything in an external system? | Yes |
| 12 | Mail and chat: read, draft, and send are three separate permissions. Which ones? | Read only, with drafts kept in the conversation; never send without the exact message approved |
| 13 | Tasks and notes: read only, or create and update after confirmation? | Read only |
| 14 | Calendar: propose only, or create events after a yes? | Propose only |
| 15 | Which actions always pause, no matter what? | Anything external, money, contracts, legal, HR, security, or irreversible |
| 16 | Interruption budget: how many proactive pings per day, and quiet hours? | 3 per day; no pings outside working hours |

Recommended path: start with the defaults for two weeks, then loosen one permission at a time when the user has seen it work. Never loosen the "never" list in the guardrail profile.

## Policy check

Before any work data flows in, confirm:

- Does the company have an AI policy, and which tools and accounts does it approve?
- Is this the company-provided account (for example a Team or Enterprise workspace), or a personal one? Putting work data into a personal AI account is one of the most common policy violations. If it is personal, keep to non-sensitive material only (no customer, confidential, or regulated data) until the company approves an account, and suggest the IT request.
- Where may work files be stored? The workspace inherits that storage's retention and sharing rules.
- Are any data classes banned from AI tools (customer data, source code, regulated data)? Add them to the guardrail profile's never list.

Record the date and answer in `Setup/setup-profile.md`. If the user does not know, say so plainly and suggest they ask before connecting anything.

## Where the workspace lives

| Surface | How | Notes |
|---|---|---|
| Cowork, in the Claude desktop app | Connect a folder the agent can read and write | Best experience. Scheduled tasks can run `/briefing` |
| Claude Desktop chat (not Cowork) | Same as claude.ai on the web: a skill upload and a code sandbox | Files don't persist between chats; carry the workspace as a zip |
| Claude Code | Run Claude Code in the workspace folder | Keep the workspace out of code repositories. `CLAUDE.md` imports `AGENTS.md` |
| claude.ai on the web | Keep the workspace in a Project's files or in a packed zip. Each session, rebuild a working copy with `brain.py unpack` (or `init` plus the project files). At `/close`, run `brain.py pack --output` into the folder the user downloads from, or copy changed files back into the Project | The code sandbox does not keep files between chats. This is the route for people whose company blocks desktop apps |
| Company-synced folder (OneDrive, Google Drive, Dropbox, Box) | Point the desktop app at the synced folder | Only with company approval. Inherits company retention and sharing |
| Other agents (Codex, Cursor, GitHub Copilot, Gemini CLI, Windsurf) | Open the folder | `AGENTS.md` carries the rules. Gemini CLI needs `context.fileName` set to `AGENTS.md`; Aider needs `read: AGENTS.md` |

Rules for every option:

- One workspace per person. `4-Reference/people.md` holds working notes that should not become a team document.
- The team's tracker and wiki stay the system of record. The workspace points to them.
- **Collisions:** some plugins and tools write their own `CLAUDE.md`, `memory/`, or `TASKS.md` into the current folder (for example a productivity plugin's start command). On Mac and Windows, `memory/` and `Memory/` are the same folder, so their files would mix with these. Run those tools in a different folder.
- If the folder already has a `CLAUDE.md`, `init` leaves it alone. Add the line `@AGENTS.md` to it so Claude Code reads the workspace rules.

## The first week

A ramp so nobody stares at an empty folder.

| Day | Do | Why |
|---|---|---|
| 1 | Guided setup, including one real result before connecting anything | The first win comes from their own brain dump |
| 2 | `/prep` before one meeting and `/debrief` after it | Meetings become sources |
| 3 | `/capture` every commitment you hear; `/close` at the end of the day | The follow-up list becomes trustworthy |
| 4 | `/project-status` before a one-on-one | The table you used to rebuild takes minutes |
| 5 | `/week` for the next week, then `/tidy` | The habit sticks when the record stays clean |
| Week 2 | Check on anything still `needs-admin`; re-run the tour when it connects | Live reads replace pasting |

## Making it a habit

- If the surface supports scheduled tasks, offer a weekday `/briefing` at the start of the user's working hours. Scheduled runs read and brief; they never send or change external systems. Before scheduling, make sure send, delete, and share tools are set to blocked in the connector settings, because an unattended run reads mail nobody has checked. Ask which systems the scheduled brief may read, and mark only those as yes in the guardrail profile; it skips the rest and says so.
- Offer one command per week, not all of them. Each one should replace a prompt the user already types.
- Once a month, suggest `/kb-lint` and a review of `Setup/guardrail-profile.md`.
