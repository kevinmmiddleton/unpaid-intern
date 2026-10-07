# Workspace and file formats

Contents

- Layout
- Memory/project-status.md
- Memory/followups.md
- Memory/meetings.md
- Memory/decisions.md
- 4-Reference/people.md
- Setup/preferences.md
- Memory/scratch-today.md and day logs
- Memory/lessons.md
- Projects, areas, and context clusters
- The context spine
- Inbox

`brain.py` parses these formats. Keep them exactly, or the due list and the status table go wrong without warning. After editing by hand, run `brain.py lint`.

## Layout

The layout borrows the folders most second-brain systems use (projects, areas, reference, archive, plus an inbox), so it feels familiar to anyone who has tried one. Numbers make the folders sort in the order people use them.

```
Second Brain/
  START-HERE.md            owner, purpose, what's in each folder, next-session intent
  AGENTS.md                standing rules for any agent
  CLAUDE.md                one line: @AGENTS.md
  1-Inbox/                 raw drops, never edited; README.md explains it
  2-Projects/
    README.md
    _template/             current.md, decisions.md, sources.md, context-map.md
    <slug>/                one folder per project (brain.py project)
  3-Areas/
    README.md
    _template.md
    <slug>.md              one page per ongoing responsibility (brain.py area)
  4-Reference/
    INDEX.md               one line per page, the map of everything
    glossary.md            confirmed meanings only
    people.md              partners and what they own or decide
    sources/               clean source notes; meetings/ for meeting notes
  5-Archive/
    processed/             raw drops after /sync-kb
    projects/              finished projects (brain.py archive); nothing is deleted
  Memory/
    project-status.md      one row per project
    followups.md           commitments, one per line
    meetings.md            short meeting ledger
    decisions.md           decisions with reasoning, newest first
    lessons.md             corrections and their fixes
    scratch-today.md       today's threads, not commitments
    day-log/               one file per working day, plus _template.md
  Setup/
    preferences.md         voice, briefing, scheduling, notifications, tools
    guardrail-profile.md   what the assistant may read, write, and send
    setup-profile.md       setup answers
    connection-plan.md     tools picked in setup, easiest first, with a status each (connect.py)
    my-commands.md         personal cheat sheet from the tour (connect.py tour)
    it-request.md          blank template; connect.py it-request writes filled-in copies
```

Rules for the layout:

- **Projects finish; areas don't.** A project has a stop condition. An area is a standing responsibility. When a project grows out of an area, it gets its own folder.
- **Nothing is deleted.** Finished projects move to `5-Archive/projects/` with `brain.py archive <slug>`, which refuses while follow-ups tagged with that project are still open.
- **Timeless, dated, or a pointer.** Every stored fact is one of the three. Slow-changing knowledge (how things work, who owns what, decisions) is stored. Fast-changing facts (counts, statuses, balances) get an "as of" date or a link to where they live, never a bare copy that will rot.
- **Organize for retrieval, not for tidiness.** Keep related material together in a project or area so one folder gives the whole picture. Don't build folders before there is something to put in them.

## Memory/project-status.md

One markdown table. Column names matter; order does not.

```
| Project | Slug | Role | Status | Next step | Next checkpoint | Updated |
|---|---|---|---|---|---|---|
| Launch v2 | launch-v2 | own | at-risk | lock the timeline with engineering | 2026-10-09 | 2026-10-06 |
```

- **Role:** `own`, `support`, or `watch`. `/project-status` leaves out `watch` unless asked.
- **Status:** `unconfirmed` (just added; nobody has said how it's going), `not-started`, `in-progress` (under way, not yet assessed), `on-track`, `at-risk`, `blocked`, `paused`, or `done`.
- **Next step:** a concrete action, not "continue work".
- **Updated:** the date the row was last confirmed true, not the date it was last typed. A row older than 14 days gets flagged before anyone sends it.
- Never mark a row `on-track` because a draft exists. Status reflects what the owner confirmed.

## Memory/followups.md

One line per commitment:

```
- [ ] YYYY-MM-DD | @owner | deliverable #project-slug | source | accepted: true|false
```

| Part | Rule |
|---|---|
| `[ ]` or `[x]` | Open or done. Never delete a line to make it go away |
| Date | When it is due. Prefix `~` for a guessed date and confirm it soon |
| `@me` | The user's own commitment. `accepted: true` |
| `@waiting:Name` | Someone else owes it. `accepted: true` only with their agreement quoted in the source |
| Deliverable | A concrete thing someone could hand over. "Look into it" is not a deliverable |
| `#project-slug` | Optional tag that links it to a project in `/project-status` |
| Source | Where it came from: "standup 2026-10-06", "email from Priya". Add `since:YYYY-MM-DD` to track how long you have waited |
| `accepted:` | Whether the owner agreed. Unconfirmed waiting items show up as "not yet agreed" |

Examples:

```
- [ ] 2026-10-09 | @me | send revised timeline to the launch group #launch-v2 | standup 2026-10-06 | accepted: true
- [ ] ~2026-10-14 | @waiting:Priya | security review notes #launch-v2 | email since:2026-10-06 | accepted: false
- [x] 2026-10-02 | @me | share survey results #research | 1:1 2026-09-30 | accepted: true
```

## Memory/meetings.md

A ledger, not the notes. Full notes go in `4-Reference/sources/meetings/`.

```
| Date | Meeting | Outcome | Decisions | Follow-ups | Source |
|---|---|---|---|---|---|
| 2026-10-06 | Launch standup | timeline slips one week | ship date moves to 10/20 | 2 logged | [notes](../4-Reference/sources/meetings/2026-10-06-launch-standup.md) |
```

## Memory/decisions.md

Newest first. The reasoning is the point.

```
## 2026-10-06 | Move launch to Oct 20

**Decision:** Ship on 2026-10-20 instead of 2026-10-13.
**Why:** Security review needs five more business days; shipping without it breaks the release policy.
**Who:** Launch lead decided; engineering and security agreed in standup.
**Revisit if:** Security review finishes before 2026-10-13.
**Provenance:** Launch standup 2026-10-06, notes in 4-Reference/sources/meetings/.
```

## 4-Reference/people.md

Who's who and how everyone relates. Facts only: never judgments about motives, competence, or reliability, and no personal contact details or photos.

```
| Name | Role | Team | Reports to | Owns or decides | Last talked | Source |
|---|---|---|---|---|---|---|
| Priya Shah | Director of Pricing | Revenue | Dana Lee | list prices, discount bands | 2026-10-06 | org chart, 2026-10-02 |
```

Below the table, a "Still figuring out" list holds names that came up before anyone explained them (Name, where they came up, best guess). `/who` and setup's org-chart step clear it.

## Setup/preferences.md

Key-value lines the scripts and commands read. Keep the `key: value` format.

- `timezone: America/New_York` is read by `brain.py` for "today".
- Briefing: sections, word cap, always include, never include.
- Scheduling: buffer minutes, focus blocks, meeting windows, default length.
- Notifications: interruption budget per day, quiet hours.
- Tools I actually use: which mail, chat, calendar, tracker, wiki, notes, and transcript tools.
- Voice: a short sample of the user's real writing. `/draft` matches it.

## Memory/scratch-today.md and day logs

- `scratch-today.md` holds threads in motion. Nothing in it is a commitment until it moves to `followups.md`.
- `brain.py daylog` creates `Memory/day-log/YYYY-MM-DD.md` from `_template.md`. `/close` fills it: moved forward, decided, still open, started and not finished, first move next session.
- Session open reads only the newest day log, three bullets at most.

## Memory/lessons.md

One row per real correction: what went wrong, the fix, and where the fix now lives (a preference line, a rule in the guardrail profile, or a change to a command). A one-time taste is not a lesson.

## Projects, areas, and context clusters

- `4-Reference/INDEX.md` lists every page in one line each.
- `4-Reference/glossary.md` holds acronyms and internal terms. A meaning goes in only when a source defines it or the user confirmed it.
- Each project gets a context cluster in `2-Projects/<slug>/`, created with `brain.py project "<Name>"` (or copied from `2-Projects/_template/` by hand):
  - `current.md`: goal, decisions in force, open questions, next action, stop condition, and a `review-by: YYYY-MM-DD` line.
  - `decisions.md`: project-level decision history, append only.
  - `sources.md`: what each source covers and where it lives.
  - `context-map.md`: pointers only (tracker, main doc, channel, shared folder).
- Each ongoing responsibility gets one page in `3-Areas/`, created with `brain.py area "<Name>"`.
- Claims on knowledge pages carry `[stated]`, `[inferred]`, or `[confirmed]`. Details in `references/knowledge-base.md`.

## The context spine

Use it when a project spans many sessions, or when old handoff notes are starting to compete with each other.

| Layer | File | Changes |
|---|---|---|
| Stable instruction | `AGENTS.md` | Rarely |
| Current state | `2-Projects/<slug>/current.md` | Constantly |
| Map | `2-Projects/<slug>/context-map.md` | When a pointer moves |
| History | `2-Projects/<slug>/decisions.md` | Append only; history, not instructions |

At the end of a substantial session, rewrite `current.md` forward so it describes today. Never let an old prompt or an old handoff impersonate today's state.

## Inbox

- `1-Inbox/` receives raw drops. Never edit a raw file.
- `/sync-kb` scans a drop first. If restricted data turns up, it stops and asks the user to remove the original. Otherwise it redacts lesser identifiers, writes a clean source note, updates the right knowledge page, logs commitments in `followups.md`, and moves the raw file to `5-Archive/processed/`.
- Raw drops are never merged into the knowledge base wholesale.
