#!/usr/bin/env python3
"""brain.py: deterministic helpers for the unpaid-intern skill.

Language models are bad at dates, business days, counting, and noticing a
leaked secret in a wall of text. This script does those jobs exactly.

Standard library only. Python 3.9 or newer. No network calls.

Usage:
  brain.py init <folder> [--dry-run] [--force]   create a workspace (never overwrites)
  brain.py now [--tz Area/City]                  current date and time
  brain.py due [--days 3] [--stale 5]            follow-ups due, overdue, and waiting
  brain.py status [--all] [--copy]               paste-ready project table
  brain.py daylog                                create today's day log
  brain.py project "<Name>" [--slug s] [--role own]   new project folder plus its status row
  brain.py area "<Name>" [--ramp-up]             new page for an ongoing responsibility (or a 30-60-90 ramp-up page)
  brain.py archive <slug> [--force]              move a finished project to 5-Archive (never deletes)
  brain.py lint                                  check formats, links, staleness
  brain.py scan [--path P | --stdin]             flag likely secrets and personal data
  brain.py pack [--output FILE.zip]              zip the workspace to carry it between sessions
  brain.py unpack <file.zip> <folder>            restore a packed workspace safely
  brain.py selftest                              run the built-in tests

due, status, daylog, project, area, archive, lint, scan, and pack take --workspace <folder>
(default: current folder). due, status, daylog, and lint also take
--today YYYY-MM-DD (default: today in the timezone set in preferences).

scan exit codes: 0 no high or medium findings (low-severity identifiers may
still be listed), 1 high-severity finding, 4 medium-severity finding,
3 some files could not be scanned (extract their text and use --stdin).
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_DIR / "templates"

# The workspace layout. Numbered folders sort in the order people use them.
INBOX = "1-Inbox"          # drop anything here; raw files are never edited
PROJECTS = "2-Projects"    # one folder per project
AREAS = "3-Areas"          # ongoing responsibilities with no end date
REFERENCE = "4-Reference"  # glossary, people, index, clean source notes
ARCHIVE = "5-Archive"      # filed drops and finished projects; nothing is deleted
MEMORY = "Memory"          # the lists the assistant keeps: follow-ups, decisions, meetings, day logs
SETUP = "Setup"            # preferences, guardrails, connections, cheat sheet
PROJECT_TABLE = f"{MEMORY}/project-status.md"
FOLLOWUPS = f"{MEMORY}/followups.md"

FOLLOWUP_RE = re.compile(
    r"^\s*-\s*\[(?P<done>[ xX])\]\s*"
    r"(?P<guess>~?)(?P<date>\d{4}-\d{2}-\d{2})\s*\|\s*"
    r"(?P<owner>@[^|]+?)\s*\|\s*"
    r"(?P<what>[^|]+?)\s*\|\s*"
    r"(?P<source>[^|]+?)\s*\|\s*"
    r"accepted:\s*(?P<accepted>true|false)\s*$",
    re.IGNORECASE,
)
LIST_MARKER_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s*")
DATE_PIPE_RE = re.compile(r"\d{4}-\d{1,2}-\d{1,2}\s*\|")
OWNER_RE = re.compile(r"^@(me|waiting:\s*\S.*)$", re.IGNORECASE)
SINCE_RE = re.compile(r"since:(\S+)")
TAG_RE = re.compile(r"(?<![\w&])#(\w[\w-]*)")
STATUS_VALUES = {"unconfirmed", "not-started", "in-progress", "on-track", "at-risk", "blocked", "paused", "done"}
ROLE_ORDER = {"own": 0, "support": 1, "watch": 2}
REL_WORDS = re.compile(
    r"(?i)\b(tomorrow|yesterday|next week|this week|last week|next month|"
    r"this quarter|next quarter|end of (?:the )?week|eod|eow|"
    r"by (?:monday|tuesday|wednesday|thursday|friday))\b"
)
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
REVIEW_RE = re.compile(r"(?im)^\s*review-by:\s*(\S+)")
DECISION_HEAD_RE = re.compile(r"^##\s+\d{4}-\d{2}-\d{2}")
TEXT_EXT = {".md", ".txt", ".csv", ".tsv", ".json", ".eml", ".vtt", ".srt",
            ".yaml", ".yml", ".html", ".htm", ".log", ".xml"}
MAX_SCAN_BYTES = 5_000_000
REQUIRED = ["START-HERE.md", "AGENTS.md", PROJECT_TABLE, FOLLOWUPS,
            f"{MEMORY}/meetings.md", f"{MEMORY}/decisions.md", f"{REFERENCE}/people.md",
            f"{SETUP}/preferences.md", f"{MEMORY}/scratch-today.md", f"{REFERENCE}/INDEX.md",
            f"{SETUP}/guardrail-profile.md"]


# ---------------------------------------------------------------- helpers


def write_lf(path, text: str) -> None:
    """Write UTF-8 text with Unix line endings on every platform, so files match across Mac, Windows, and Linux."""
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def find_workspace(arg: str) -> Path:
    ws = Path(arg).expanduser().resolve()
    if not (ws / MEMORY).is_dir():
        sys.exit(f"No workspace found at {ws}. Run 'brain.py init <folder>' or pass --workspace <folder>.")
    return ws


def parse_date(value: str) -> dt.date | None:
    try:
        return dt.date.fromisoformat(value.strip())
    except ValueError:
        return None


def strip_comments(text: str):
    """Return ([(line_number, text_without_html_comments)], line_where_an_unclosed_comment_starts)."""
    out, in_comment, start = [], False, None
    for n, line in enumerate(text.splitlines(), 1):
        live, rest = "", line
        while rest:
            if in_comment:
                end = rest.find("-->")
                if end == -1:
                    rest = ""
                    break
                rest, in_comment = rest[end + 3:], False
            else:
                beg = rest.find("<!--")
                if beg == -1:
                    live, rest = live + rest, ""
                    break
                live, rest, in_comment, start = live + rest[:beg], rest[beg + 4:], True, n
        out.append((n, live))
    return out, (start if in_comment else None)


def live_lines(text: str):
    """Yield (line_number, line) outside HTML comments and fenced code blocks."""
    lines, _ = strip_comments(text)
    in_fence = False
    for n, line in lines:
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence and line.strip():
            yield n, line


def read_pref(ws: Path | None, key: str) -> str | None:
    if ws is None:
        return None
    p = ws / SETUP / "preferences.md"
    if not p.exists():
        return None
    pat = re.compile(rf"^\s*[-*]?\s*{re.escape(key)}\s*:\s*(.+?)\s*$", re.IGNORECASE)
    for _, line in live_lines(read_text(p)):
        m = pat.match(line)
        if m:
            value = m.group(1).strip().strip("`")
            if value and not value.startswith("<"):
                return value
    return None


def now_in(tzname: str | None):
    if tzname:
        try:
            from zoneinfo import ZoneInfo
            return dt.datetime.now(ZoneInfo(tzname)), tzname
        except Exception as exc:  # unknown zone or missing tz database
            hint = " On Windows, 'pip install tzdata' adds the timezone database." if os.name == "nt" else ""
            print(f"Timezone '{tzname}' unavailable ({exc}); using this computer's local time.{hint}", file=sys.stderr)
    local = dt.datetime.now().astimezone()
    return local, str(local.tzinfo)


def get_today(ws: Path | None, override: str | None) -> dt.date:
    if override:
        day = parse_date(override)
        if day is None:
            sys.exit(f"--today must look like YYYY-MM-DD (for example 2026-10-04), got '{override}'.")
        return day
    return now_in(read_pref(ws, "timezone"))[0].date()


def add_business_days(day: dt.date, n: int) -> dt.date:
    added = 0
    while added < n:
        day += dt.timedelta(days=1)
        if day.weekday() < 5:
            added += 1
    return day


def business_days_between(start: dt.date, end: dt.date) -> int:
    """Business days after start, up to and including end."""
    count, day = 0, start
    while day < end:
        day += dt.timedelta(days=1)
        if day.weekday() < 5:
            count += 1
    return count


def late_text(due: dt.date, today: dt.date) -> str:
    bd = business_days_between(due, today)
    if bd == 0:
        return "past due over the weekend"
    return f"{bd} business day{'s' if bd != 1 else ''} late"


WINDOWS_RESERVED = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}


def slugify(text: str) -> str:
    import unicodedata
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", plain.lower()).strip("-")
    if slug in WINDOWS_RESERVED:  # Windows can't make a folder called con, nul, com1, and so on
        slug += "-project"
    return slug


def fallback_slug(kind: str, name: str) -> str:
    """For names with no Latin letters (Chinese, emoji): a short stable code, so two of them never collide."""
    import hashlib
    return f"{kind}-{hashlib.sha1(name.encode('utf-8')).hexdigest()[:6]}"


def fmt_day(day: dt.date) -> str:
    return day.strftime("%a %Y-%m-%d")


def escapes_root(root: Path, target: Path) -> bool:
    """True if target (or any existing parent below root) is a symlink, or target is outside root."""
    root = root.resolve()
    try:
        target.parent.resolve().relative_to(root)
    except ValueError:
        return True
    probe = target
    while True:
        if probe.is_symlink():
            return True
        if probe.parent == probe or probe == root or probe.parent == root:
            return probe.parent.is_symlink() if probe.parent != root else False
        probe = probe.parent


# ---------------------------------------------------------------- parsing

def looks_like_followup(line: str) -> bool:
    s = line.strip()
    if "|" not in s:
        return False
    return bool(LIST_MARKER_RE.match(s)) or bool(DATE_PIPE_RE.search(s))


def parse_followups(path: Path):
    """Return (items, bad_lines, unclosed_comment_line)."""
    items, bad = [], []
    if not path.exists():
        return items, bad, None
    lines, unclosed = strip_comments(read_text(path))
    in_fence = False
    for n, line in lines:
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not line.strip():
            continue
        m = FOLLOWUP_RE.match(line.rstrip())
        if not m:
            if looks_like_followup(line):
                bad.append((n, line.strip()))
            continue
        g = m.groupdict()
        date = parse_date(g["date"])
        if date is None:
            bad.append((n, line.strip()))
            continue
        owner = re.sub(r"\s+", " ", g["owner"].strip())
        since, since_bad = None, False
        sm = SINCE_RE.search(g["source"])
        if sm:
            since = parse_date(sm.group(1))
            since_bad = since is None
        low = owner.lower()
        waiting = owner.split(":", 1)[1].strip() if low.startswith("@waiting:") else None
        items.append({
            "line": n, "done": g["done"].lower() == "x", "guessed": g["guess"] == "~",
            "date": date, "owner": owner, "mine": low == "@me", "waiting_on": waiting,
            "what": g["what"].strip(), "source": g["source"].strip(),
            "accepted": g["accepted"].lower() == "true", "since": since, "since_bad": since_bad,
            "tags": TAG_RE.findall(line.lower()), "raw": line.strip(),
        })
    return items, bad, unclosed


def split_row(s: str):
    s = s.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", s)]


def parse_projects(path: Path):
    header, rows, bad = None, [], []
    if not path.exists():
        return header, rows, bad
    for n, line in live_lines(read_text(path)):
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = split_row(s)
        if header is None:
            if any(c.lower() == "project" for c in cells):
                header = [c.lower() for c in cells]
            continue
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        if len(cells) != len(header):
            bad.append((n, s))
            continue
        row = dict(zip(header, cells))
        if not row.get("project"):
            continue
        row["_line"] = n
        rows.append(row)
    return header, rows, bad


def compute_due(items, today: dt.date, days: int, stale: int, confirm_days: int = 10):
    horizon = add_business_days(today, days)
    confirm_horizon = add_business_days(today, confirm_days)
    out = {k: [] for k in ("overdue", "due_today", "due_soon", "waiting_overdue",
                           "waiting_stale", "unconfirmed", "guessed", "unknown_owner")}
    for it in items:
        if it["done"]:
            continue
        if it["mine"]:
            if it["date"] < today:
                out["overdue"].append(it)
            elif it["date"] == today:
                out["due_today"].append(it)
            elif it["date"] <= horizon:
                out["due_soon"].append(it)
        elif it["waiting_on"]:
            if it["date"] < today:
                out["waiting_overdue"].append(it)
            elif it["since"] and business_days_between(it["since"], today) > stale:
                out["waiting_stale"].append(it)
            listed = it in out["waiting_overdue"] or it in out["waiting_stale"]
            if not it["accepted"] and it["date"] <= confirm_horizon and not listed:
                out["unconfirmed"].append(it)
        else:
            out["unknown_owner"].append(it)
        if it["guessed"] and it["date"] <= horizon:
            out["guessed"].append(it)
    for key in out:
        out[key].sort(key=lambda x: x["date"])
    return out, horizon


# ---------------------------------------------------------------- commands

def cmd_init(args) -> int:
    dest = Path(args.folder).expanduser().resolve()
    if not TEMPLATES.is_dir():
        sys.exit(f"Templates not found at {TEMPLATES}. Is the skill folder complete?")
    repo = next((p for p in [dest, *dest.parents] if (p / ".git").exists()), None)
    if repo and not args.force:
        sys.exit(f"{dest} is inside a code repository ({repo}). Use a dedicated folder for the workspace, or pass --force.")
    existing = [p for p in dest.iterdir()] if dest.is_dir() else []
    created, skipped, refused = [], [], []
    for src in sorted(TEMPLATES.rglob("*")):
        rel = src.relative_to(TEMPLATES)
        target = dest / rel
        if src.is_dir():
            if not args.dry_run and not escapes_root(dest, target / "x"):
                target.mkdir(parents=True, exist_ok=True)
            continue
        if escapes_root(dest, target):
            refused.append(str(rel))
            continue
        if src.name == ".keep":
            if not args.dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
            continue
        if target.exists() or target.is_symlink():
            skipped.append(str(rel))
            continue
        created.append(str(rel))
        if not args.dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)
    verb = "Would create" if args.dry_run else "Created"
    print(f"{verb} {len(created)} files in {dest}")
    for c in created:
        print(f"  + {c}")
    if skipped:
        print(f"Left {len(skipped)} existing files untouched:")
        for s in skipped:
            print(f"  = {s}")
    if refused:
        print(f"Refused {len(refused)} path(s) that go through a symlink or outside the folder:")
        for r in refused:
            print(f"  ! {r}")
    tops = {p.name for p in TEMPLATES.iterdir()}
    others = [p for p in existing if p.name not in tops and not p.name.startswith(".")]
    if others:
        print(f"Note: the folder already had {len(others)} other item(s). Nothing was overwritten, but a dedicated folder keeps the workspace tidy.")
    claude_md = dest / "CLAUDE.md"
    if "CLAUDE.md" in skipped and claude_md.is_file() and "@AGENTS.md" not in read_text(claude_md):
        print("Note: an existing CLAUDE.md was kept. Add a line '@AGENTS.md' to it so Claude Code reads the workspace rules.")
    if "AGENTS.md" in skipped:
        print("Note: an existing AGENTS.md was kept. Compare it with the template in the skill's templates folder.")
    if not args.dry_run:
        print("Next: answer the setup questions, then run 'brain.py lint' to confirm the workspace is healthy.")
    return 0


def cmd_now(args) -> int:
    ws = None
    if args.workspace and (Path(args.workspace).expanduser() / MEMORY).is_dir():
        ws = Path(args.workspace).expanduser().resolve()
    now, label = now_in(args.tz or read_pref(ws, "timezone"))
    utc = now.astimezone(dt.timezone.utc)
    print(f"{now.strftime('%A, %B')} {now.day}, {now.year}")
    print(f"Local time: {now.strftime('%H:%M')} ({label})")
    print(f"ISO: {now.isoformat(timespec='seconds')}")
    print(f"UTC: {utc.strftime('%Y-%m-%d %H:%M')}")
    print(f"Week: {now.isocalendar()[1]}, quarter: Q{(now.month - 1) // 3 + 1}")
    return 0



QUOTED_RE = re.compile(r'"[^"\n]*"|\u201c[^\u201d\n]*\u201d')

# ---------------------------------------------------------------- relative dates ("Thursday", "end of month")

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]


def last_business_day(year: int, month: int) -> dt.date:
    nxt = dt.date(year + (month == 12), month % 12 + 1, 1)
    day = nxt - dt.timedelta(days=1)
    while day.weekday() >= 5:
        day -= dt.timedelta(days=1)
    return day


HEDGE_RE = re.compile(
    r"\b(?:i think|i guess|i believe|i'm pretty sure|pretty sure|maybe|probably|possibly|hopefully|tentatively|"
    r"roughly|around|about|or so|ish|if possible|give or take|ballpark|i'm not sure|not sure|i assume)\b|-ish\b|\?+",
    re.IGNORECASE)


def resolve_when(phrase: str, today: dt.date):
    """Turn a spoken deadline into (date, exact, note). A hedge ("I think", "maybe", "?") makes any date a guess."""
    hedges = [h.group(0).strip(" ?") or "?" for h in HEDGE_RE.finditer(phrase)]
    if hedges:
        rest = " ".join(HEDGE_RE.sub(" ", phrase).replace(",", " ").split()).strip(" .-")
        if rest:
            day, _, note = _resolve_when_core(rest, today)
            if day is not None:
                why = "it ended with a question mark" if hedges[0] == "?" else f"you said '{hedges[0]}'"
                return day, False, f"{note}; {why}, so it's a guess"
    return _resolve_when_core(phrase, today)


def _resolve_when_core(phrase: str, today: dt.date):
    """Turn a spoken deadline into (date, exact, note). Returns (None, False, note) when it can't."""
    raw = phrase
    p = " ".join(phrase.lower().replace(",", " ").split())
    for lead in ("due ", "by ", "on ", "before ", "until ", "no later than "):
        if p.startswith(lead):
            p = p[len(lead):]
    p = p.removeprefix("the ") if hasattr(p, "removeprefix") else (p[4:] if p.startswith("the ") else p)
    iso = parse_date(p)
    if iso:
        return iso, True, "a calendar date"
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?", p)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        y = int(m.group(3)) if m.group(3) else today.year
        y = y + 2000 if y < 100 else y
        order = (read_pref_text("date order") or "").lower()
        if a > 12:
            mo, d, exact, note = b, a, True, "read as day/month"
        elif b > 12:
            mo, d, exact, note = a, b, True, "read as month/day"
        elif order.startswith("day"):
            mo, d, exact, note = b, a, True, "read as day/month (your date order)"
        elif order.startswith("month"):
            mo, d, exact, note = a, b, True, "read as month/day (your date order)"
        else:
            mo, d, exact, note = a, b, a == b, f"read as month/day; as day/month it would be {b}/{a}. Set 'date order' in preferences to stop guessing"
        try:
            day = dt.date(y, mo, d)
        except ValueError:
            return None, False, f"'{raw}' isn't a real date"
        if not m.group(3) and (today - day).days > 60:
            day = day.replace(year=day.year + 1)
        return day, exact, note
    m = re.fullmatch(r"([a-z]{3,9})\.? (\d{1,2})(?:st|nd|rd|th)?(?: (\d{4}))?|(\d{1,2})(?:st|nd|rd|th)? ([a-z]{3,9})(?: (\d{4}))?", p)
    if m:
        name = (m.group(1) or m.group(5))[:3]
        d = int(m.group(2) or m.group(4))
        yr = m.group(3) or m.group(6)
        if name in MONTHS:
            try:
                day = dt.date(int(yr) if yr else today.year, MONTHS.index(name) + 1, d)
            except ValueError:
                return None, False, f"'{raw}' isn't a real date"
            if not yr and (today - day).days > 60:
                day = day.replace(year=day.year + 1)
            return day, True, "a calendar date"
    m = re.fullmatch(r"(\d{1,2})(st|nd|rd|th)", p)
    if m:
        d = int(m.group(1))
        y, mth = today.year, today.month
        if d < today.day:
            y, mth = today.year + (today.month == 12), today.month % 12 + 1
        try:
            return dt.date(y, mth, d), True, "the next time that day of the month comes around"
        except ValueError:
            return None, False, f"'{raw}' isn't a real date"
    if p in ("today", "eod", "end of day", "tonight", "end of today", "cob", "close of business"):
        return today, True, "today"
    if p in ("tomorrow", "tmrw", "end of tomorrow"):
        return today + dt.timedelta(days=1), True, "tomorrow"
    if p in ("asap", "as soon as possible", "right away"):
        return add_business_days(today, 1), False, "no date given; a placeholder of the next business day"
    if p in ("soon", "shortly", "in a bit", "later", "sometime", "when they can", "when i can"):
        return add_business_days(today, 5), False, "no date given; a placeholder five business days out"
    m = re.fullmatch(r"(this |next )?(mon|tues|tue|wednes|wed|thurs|thu|fri|satur|sat|sun)(day)?", p)
    if m:
        target = next(i for i, w in enumerate(WEEKDAYS) if w.startswith(m.group(2)[:3]))
        ahead = (target - today.weekday()) % 7
        if m.group(1) == "next ":
            upcoming = today + dt.timedelta(days=ahead or 7)
            following = (today - dt.timedelta(days=today.weekday())) + dt.timedelta(days=7 + target)
            if today.weekday() >= 5:  # on a weekend, "next Tuesday" splits people: this coming one, or the week after
                later = upcoming + dt.timedelta(days=7)
                return upcoming, False, f"\"next {WEEKDAYS[target].title()}\" read as the coming one; it could also mean {later.isoformat()}"
            if following == upcoming:
                return upcoming, True, f"next {WEEKDAYS[target].title()}"
            return following, False, f"\"next {WEEKDAYS[target].title()}\" read as the one next week; it could also mean {upcoming.isoformat()}"
        if ahead == 0:
            return today + dt.timedelta(days=7), False, f"read as a week from today, since today is {WEEKDAYS[target].title()}"
        return today + dt.timedelta(days=ahead), True, f"the coming {WEEKDAYS[target].title()}"
    weekend = today.weekday() >= 5
    if p in ("end of week", "end of the week", "eow", "this week", "end of this week", "by friday this week"):
        base = today if not weekend else today + dt.timedelta(days=7 - today.weekday())
        note = "read as the coming Friday (it's the weekend, so 'this week' could mean either)" if weekend else "read as Friday this week"
        return base + dt.timedelta(days=4 - base.weekday()), not weekend, note
    if p in ("next week", "end of next week", "eonw", "sometime next week"):
        monday = today - dt.timedelta(days=today.weekday()) + dt.timedelta(days=7)
        if weekend:
            return monday + dt.timedelta(days=4), False, f"read as Friday of the coming week; it could also mean {(monday + dt.timedelta(days=11)).isoformat()}"
        return monday + dt.timedelta(days=4), p == "end of next week", "read as Friday next week"
    if p in ("end of month", "end of the month", "eom", "this month", "end of this month", "month end", "month-end"):
        return last_business_day(today.year, today.month), False, "read as the last business day of this month"
    if p in ("end of next month", "next month"):
        y, mth = (today.year + (today.month == 12), today.month % 12 + 1)
        return last_business_day(y, mth), False, "read as the last business day of next month"
    m = re.fullmatch(r"(end of )?(this |next )?(quarter|q([1-4]))", p) or (re.fullmatch(r"(eoq)", p) and re.fullmatch(r"(end of )?(this |next )?(quarter|q([1-4]))", "quarter"))
    if m:
        cur = (today.month - 1) // 3 + 1
        if m.group(4):
            q = int(m.group(4))
            y = today.year if q >= cur else today.year + 1
        else:
            q, y = (cur, today.year) if m.group(2) != "next " else ((cur % 4) + 1, today.year + (cur == 4))
        return last_business_day(y, q * 3), False, f"read as the last business day of Q{q} {y}"
    m = re.fullmatch(r"(\d+|a|an|one|two|three|four|five|six) (days?|weeks?|months?) ago", p)
    if m:
        n = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6}.get(m.group(1)) or int(m.group(1))
        unit = m.group(2)
        if unit.startswith("day"):
            return today - dt.timedelta(days=n), True, f"{n} day(s) ago"
        if unit.startswith("week"):
            return today - dt.timedelta(days=7 * n), False, f"{n} week(s) ago, to the day; people usually round"
        y, mth = today.year + (today.month - 1 - n) // 12, (today.month - 1 - n) % 12 + 1
        return dt.date(y, mth, min(today.day, 28)), False, f"{n} month(s) ago, roughly"
    m = re.fullmatch(r"in (\d+|a|an|one|two|three|four|five|six) (business days?|working days?|days?|weeks?|months?)", p)
    if m:
        n = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6}.get(m.group(1)) or int(m.group(1))
        unit = m.group(2)
        if unit.startswith(("business", "working")):
            return add_business_days(today, n), True, f"{n} business day(s) from today"
        if unit.startswith("day"):
            return today + dt.timedelta(days=n), True, f"{n} day(s) from today"
        if unit.startswith("week"):
            return today + dt.timedelta(days=7 * n), True, f"{n} week(s) from today"
        y, mth = today.year + (today.month - 1 + n) // 12, (today.month - 1 + n) % 12 + 1
        day = min(today.day, (dt.date(y + (mth == 12), mth % 12 + 1, 1) - dt.timedelta(days=1)).day)
        return dt.date(y, mth, day), False, f"{n} month(s) from today"
    return None, False, f"couldn't read '{raw}' as a date"


_WHEN_WS: Path | None = None


def read_pref_text(key: str) -> str | None:
    return read_pref(_WHEN_WS, key) if _WHEN_WS else None


def cmd_when(args) -> int:
    global _WHEN_WS
    ws = None
    if args.workspace and (Path(args.workspace).expanduser() / MEMORY).is_dir():
        ws = Path(args.workspace).expanduser().resolve()
    _WHEN_WS = ws
    today = get_today(ws, args.today)
    rc = 0
    rows = []
    for phrase in args.phrase:
        day, exact, note = resolve_when(phrase, today)
        if day is None:
            rows.append(dict(phrase=phrase, date=None, exact=False, note=note))
            rc = 2 if len(args.phrase) == 1 else rc
            continue
        weekend = ""
        if day.weekday() >= 5:
            nxt = add_business_days(day, 1)
            weekend = f". It falls on a {day.strftime('%A')}; the next business day is {nxt.strftime('%a')} {nxt.isoformat()}"
        rows.append(dict(phrase=phrase, date=day.isoformat(), exact=exact, weekday=day.strftime("%a"),
                         write_as=("" if exact else "~") + day.isoformat(), note=note + weekend))
    if args.json:
        print(json.dumps(dict(today=today.isoformat(), results=rows), indent=1))
        return rc
    print(f"Today is {fmt_day(today)}.")
    for r in rows:
        if r["date"] is None:
            print(f'  "{r["phrase"]}": {r["note"]}. Ask the person, or log a guess with ~ and say it is a guess.')
        else:
            kind = "exact" if r["exact"] else "a guess, so write it with ~"
            print(f'  "{r["phrase"]}": {r["weekday"]} {r["date"]} ({kind}; {r["note"]}). Write as {r["write_as"]}')
    return rc

DUE_LABELS = [
    ("overdue", "Overdue, yours"),
    ("due_today", "Due today, yours"),
    ("due_soon", "Due soon, yours"),
    ("waiting_overdue", "Waiting on others, past due"),
    ("waiting_stale", "Waiting on others, stale"),
    ("unconfirmed", "Waiting on others, not yet agreed"),
    ("guessed", "Guessed dates coming up (confirm them)"),
    ("unknown_owner", "Owner not recognized (use @me or @waiting:Name)"),
]
OPEN_KEYS = ["overdue", "due_today", "waiting_overdue", "waiting_stale"]


def cmd_due(args) -> int:
    ws = find_workspace(args.workspace)
    today = get_today(ws, args.today)
    items, bad, unclosed = parse_followups(ws / FOLLOWUPS)
    out, horizon = compute_due(items, today, args.days, args.stale)
    if args.json:
        def ser(it):
            d = dict(it)
            d["date"] = it["date"].isoformat()
            d["since"] = it["since"].isoformat() if it["since"] else None
            return d
        payload = {k: [ser(i) for i in v] for k, v in out.items()}
        payload.update(today=today.isoformat(), horizon=horizon.isoformat(),
                       malformed_lines=[n for n, _ in bad], unclosed_comment_line=unclosed)
        print(json.dumps(payload, indent=2))
        return 0
    keys = OPEN_KEYS if args.open else [k for k, _ in DUE_LABELS]
    if args.open:
        print(f"Session open, {fmt_day(today)}: mention only these, in two lines at most. If the list is empty, say nothing about having checked.")
    else:
        print(f"Follow-ups as of {fmt_day(today)} (due soon = by {fmt_day(horizon)}; stale = more than {args.stale} business days)")
        open_items = [i for i in items if not i["done"]]
        mine = sum(1 for i in open_items if i["mine"])
        waiting = sum(1 for i in open_items if i["waiting_on"])
        print(f"Open: {len(open_items)} ({mine} yours, {waiting} waiting on others"
              + (f", {len(open_items) - mine - waiting} with an unrecognized owner" if len(open_items) - mine - waiting else "") + ")")
    any_hit = False
    for key, label in DUE_LABELS:
        if not out[key] or key not in keys:
            continue
        any_hit = True
        print(f"\n{label}")
        for it in out[key]:
            who = "" if it["mine"] else f" [{it['waiting_on'] or it['owner']}]"
            extra = ""
            if key in ("overdue", "waiting_overdue"):
                extra = f" ({late_text(it['date'], today)})"
            if key in ("waiting_overdue", "waiting_stale", "unconfirmed") and it["since"]:
                bd = business_days_between(it["since"], today)
                extra += f" (waiting {bd} business day{'s' if bd != 1 else ''}, since {it['since'].isoformat()})"
            if key in ("waiting_overdue", "waiting_stale") and not it["accepted"]:
                extra += " (not yet agreed)"
            print(f"  {it['date'].strftime('%a')} {it['date'].isoformat()}{'~' if it['guessed'] else ''}{who}  {it['what']}  <{it['source']}>{extra}  (line {it['line']})")
    if not any_hit:
        print("\nNothing to mention." if args.open else "\nNothing due, overdue, or stale.")
    problems = []
    if bad:
        problems.append(f"{len(bad)} line(s) look like follow-ups but do not match the format (lines {', '.join(str(n) for n, _ in bad)})")
    hidden = []
    if unclosed:
        problems.append(f"an HTML comment opened on line {unclosed} is never closed, so everything after it is hidden")
        all_lines = read_text(ws / FOLLOWUPS).splitlines()
        for n, line in enumerate(all_lines[unclosed:], unclosed + 1):
            m = FOLLOWUP_RE.match(line.rstrip())
            if m and line.lstrip().startswith("- [ ]"):
                d = parse_date(m.groupdict()["date"])
                if d:
                    when = late_text(d, today) if d < today else ("due today" if d == today else f"due {fmt_day(d)}")
                    hidden.append(f"  line {n}: {d.strftime('%a')} {d.isoformat()}  {m.groupdict()['what'].strip()} ({when})")
    if problems:
        print("\nWarning: " + "; ".join(problems) + ". These items are NOT in the list above. Run 'brain.py lint'.")
        if hidden:
            print("Open items hidden by the comment:")
            print("\n".join(hidden))
    return 0


def build_status(ws: Path, today: dt.date, include_watch: bool, stale_days: int):
    header, rows, bad_rows = parse_projects(ws / PROJECT_TABLE)
    items, _, _ = parse_followups(ws / FOLLOWUPS)
    open_items = [i for i in items if not i["done"]]
    table = ["| Project | Status | Next step | Next checkpoint | Open (mine / waiting) | Updated |",
             "|---|---|---|---|---|---|"]
    notes = []
    selected = [r for r in rows if include_watch or r.get("role", "").strip().lower() != "watch"]
    selected.sort(key=lambda r: ROLE_ORDER.get(r.get("role", "").strip().lower(), 3))
    known_slugs = {(r.get("slug") or slugify(r["project"])).strip().lower() for r in rows}
    if (ws / AREAS).is_dir():  # follow-ups tagged to an ongoing area count as tagged too
        known_slugs |= {p.stem.lower() for p in (ws / AREAS).glob("*.md") if not p.name.startswith("_") and p.name.lower() != "readme.md"}

    def cell(text: str) -> str:
        return text.replace("|", "\\|")

    for r in selected:
        slug = (r.get("slug") or slugify(r["project"])).strip().lower()
        tagged = [i for i in open_items if slug in i["tags"]]
        mine = sum(1 for i in tagged if i["mine"])
        wait = sum(1 for i in tagged if i["waiting_on"])
        overdue = sum(1 for i in tagged if i["date"] < today)
        status = r.get("status", "").strip().lower()
        nxt = r.get("next step", "").strip()
        checkpoint = (r.get("next checkpoint") or r.get("checkpoint") or "").strip()
        updated = r.get("updated", "").strip()
        name = r["project"]
        if status and status not in STATUS_VALUES:
            notes.append(f"{name}: status '{status}' is not one of {', '.join(sorted(STATUS_VALUES))}.")
        if status == "unconfirmed":
            notes.append(f"{name}: status not confirmed yet. Ask before calling it on track.")
        if status == "done" and (mine or wait):
            notes.append(f"{name}: marked done but has {mine + wait} open follow-up(s).")
        if status == "on-track" and overdue:
            notes.append(f"{name}: marked on-track but has {overdue} overdue follow-up(s). Confirm before sending.")
        if not nxt and status not in ("done", "paused"):
            notes.append(f"{name}: no next step.")
        upd = parse_date(updated) if updated else None
        if upd is None:
            notes.append(f"{name}: 'Updated' is not a YYYY-MM-DD date, so freshness is unknown.")
        elif (today - upd).days >= stale_days:
            notes.append(f"{name}: last updated {(today - upd).days} days ago. Confirm the status before sending.")
        table.append(f"| {cell(name)} | {status or 'unknown'} | {cell(nxt) or '(none)'} | {cell(checkpoint) or '(none)'} | {mine} / {wait} | {updated or '?'} |")
    untagged = [i for i in open_items if not (set(i["tags"]) & known_slugs)]
    if untagged:
        notes.append(f"{len(untagged)} open follow-up(s) are not tagged to a project. Add #project-slug to count them.")
    for n, s in bad_rows:
        notes.append(f"{PROJECT_TABLE} line {n} has the wrong number of columns, so it was left out: {s}")
    if header is None:
        notes.append(f"No project table found in {PROJECT_TABLE}.")
    return "\n".join(table), notes


def copy_to_clipboard(text: str) -> str | None:
    for cmd in (["pbcopy"], ["clip"], ["wl-copy"], ["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]):
        if shutil.which(cmd[0]):
            try:
                subprocess.run(cmd, input=text.encode("utf-8"), check=True)
                return cmd[0]
            except Exception:
                continue
    return None


def cmd_status(args) -> int:
    ws = find_workspace(args.workspace)
    today = get_today(ws, args.today)
    table, notes = build_status(ws, today, args.all, args.stale_days)
    print(f"Project status as of {fmt_day(today)}\n")
    print(table)
    if notes:
        print("\nNotes for you (not part of the paste):")
        for n in notes:
            print(f"  - {n}")
    if args.copy:
        tool = copy_to_clipboard(table)
        print(f"\nCopied the table with {tool} (this only reaches your clipboard when the script runs on your own computer)."
              if tool else "\nNo clipboard tool found; copy the table above by hand.")
    return 0


def _template_dir(ws: Path, rel: str) -> Path:
    local = ws / rel
    return local if local.exists() and not local.is_symlink() else TEMPLATES / rel


def _index_add(ws: Path, heading: str, line: str) -> str:
    idx = ws / REFERENCE / "INDEX.md"
    if not idx.exists() or escapes_root(ws, idx):
        return f"No {REFERENCE}/INDEX.md to update; add a line for it by hand."
    lines = read_text(idx).splitlines()
    target = line.split("](", 1)[1].split(")", 1)[0]
    if any(f"]({target})" in ln for _, ln in live_lines("\n".join(lines))):
        return "The index already links to it."
    try:
        start = next(i for i, ln in enumerate(lines) if ln.strip().lower() == f"## {heading.lower()}")
    except StopIteration:
        lines += ["", f"## {heading}", "", line]
    else:
        end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
        while end > start + 1 and not lines[end - 1].strip():
            end -= 1
        lines.insert(end, line)
    write_lf(idx, "\n".join(lines) + "\n")
    return f"Added a line to {REFERENCE}/INDEX.md."


def _clean_name(name: str) -> str:
    name = " ".join((name or "").split())
    return re.sub(r"[\[\]()<>]", "", name).strip()


def _table_add_row(path: Path, values: dict) -> bool:
    lines = read_text(path).splitlines() if path.exists() else []
    header_i = next((i for i, ln in enumerate(lines) if ln.strip().startswith("|") and "project" in ln.lower()), None)
    if header_i is None:
        return False
    header = [c.lower() for c in split_row(lines[header_i].strip())]
    i = header_i + 1
    while i < len(lines) and lines[i].strip().startswith("|"):
        cells = split_row(lines[i].strip())
        if values.get("slug") and "slug" in header and len(cells) == len(header) and cells[header.index("slug")] == values["slug"]:
            return False
        i += 1
    row = "| " + " | ".join(values.get(h, "").replace("|", "\\|") for h in header) + " |"
    lines.insert(i, row)
    write_lf(path, "\n".join(lines) + "\n")
    return True


def cmd_project(args) -> int:
    ws = find_workspace(args.workspace)
    today = get_today(ws, args.today)
    args.name = _clean_name(args.name)
    if not args.name:
        sys.exit("Give the project a name.")
    slug = (args.slug or slugify(args.name) or fallback_slug("project", args.name))[:40].strip("-")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug or ""):
        sys.exit(f"Slug '{slug}' must be lowercase letters, numbers, and hyphens. Pass --slug.")
    if args.role not in ROLE_ORDER:
        sys.exit("--role must be own, support, or watch.")
    dest = ws / PROJECTS / slug
    if escapes_root(ws, dest / "x"):
        sys.exit(f"Refusing {PROJECTS}/{slug}: it goes through a symlink or outside the workspace.")
    if dest.exists():
        sys.exit(f"{PROJECTS}/{slug} already exists. Pick another --slug.")
    src = _template_dir(ws, f"{PROJECTS}/_template")
    dest.mkdir(parents=True)
    for f in sorted(src.glob("*.md")):
        write_lf((dest / f.name), read_text(f).replace("<Project name>", args.name)
                 .replace("review-by: <YYYY-MM-DD>", f"review-by: {(today + dt.timedelta(days=30)).isoformat()}"))
    added = _table_add_row(ws / PROJECT_TABLE, {"project": args.name, "slug": slug, "role": args.role,
                                                "status": getattr(args, "status", None) or "unconfirmed", "next step": args.next or "",
                                                "next checkpoint": "", "updated": today.isoformat()})
    index_note = _index_add(ws, "Projects", f"- [{args.name}](../{PROJECTS}/{slug}/current.md): <one line: the goal>")
    print(f"Created {PROJECTS}/{slug}/ with current, decisions, sources, and context-map pages.")
    print("Added a row to the project status table." if added else f"Did not add a status row: {PROJECT_TABLE} already has #{slug}, or has no table. Check it.")
    print(index_note)
    print(f"Tag related follow-ups with #{slug}.")
    return 0


def cmd_area(args) -> int:
    ws = find_workspace(args.workspace)
    args.name = _clean_name(args.name)
    if not args.name:
        sys.exit("Give the area a name.")
    slug = (args.slug or slugify(args.name) or fallback_slug("area", args.name))[:40].strip("-")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug or ""):
        sys.exit(f"Slug '{slug}' must be lowercase letters, numbers, and hyphens. Pass --slug.")
    dest = ws / AREAS / f"{slug}.md"
    if escapes_root(ws, dest):
        sys.exit(f"Refusing {AREAS}/{slug}.md: it goes through a symlink or outside the workspace.")
    if dest.exists():
        sys.exit(f"{AREAS}/{slug}.md already exists. Pick another --slug.")
    src = _template_dir(ws, f"{AREAS}/_ramp-up.md" if getattr(args, "ramp_up", False) else f"{AREAS}/_template.md")
    dest.parent.mkdir(parents=True, exist_ok=True)
    body = read_text(src).replace("<Area name>", args.name)
    if getattr(args, "ramp_up", False):
        raw_start = getattr(args, "started", None)
        started = parse_date(raw_start or "")
        if raw_start and started is None:
            sys.exit(f"--started must be a date like 2026-09-21, got '{raw_start}'. Turn phrases into dates with 'brain.py when \"{raw_start}\"' first.")
        started = started or get_today(ws, None)
        body = body.replace("<YYYY-MM-DD, about 30 days from your start>", (started + dt.timedelta(days=30)).isoformat())
        body = body.replace("Started on: <YYYY-MM-DD>", f"Started on: {started.isoformat()}")
    write_lf(dest, body)
    index_note = _index_add(ws, "Areas", f"- [{args.name}](../{AREAS}/{slug}.md): <one line: what it covers>")
    print(f"Created {AREAS}/{slug}.md.")
    print(index_note)
    return 0


def cmd_archive(args) -> int:
    ws = find_workspace(args.workspace)
    today = get_today(ws, args.today)
    slug = args.slug
    src = ws / PROJECTS / slug
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug) or not src.is_dir() or src.is_symlink() or escapes_root(ws, src / "x"):
        sys.exit(f"No project folder {PROJECTS}/{slug} inside this workspace.")
    items, bad, _ = parse_followups(ws / FOLLOWUPS)
    open_items = [it for it in items if not it["done"] and slug in it["tags"]]
    open_items += [{"line": n, "what": ln.strip()} for n, ln in bad
                   if re.search(rf"(?<![\w&])#{re.escape(slug)}\b", ln.lower()) and not re.match(r"^\s*-\s*\[[xX]\]", ln)]
    if open_items and not args.force:
        print(f"{len(open_items)} open follow-up(s) are tagged #{slug}:")
        for it in open_items:
            print(f"  - line {it['line']}: {it['what']}")
        print("Close or move them first, or pass --force to archive anyway.")
        return 1
    dest = ws / ARCHIVE / "projects" / slug
    n = 2
    while dest.exists():
        dest = ws / ARCHIVE / "projects" / f"{slug}-{n}"
        n += 1
    if escapes_root(ws, dest / "x"):
        sys.exit("Refusing to move outside the workspace.")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dest))
    table = ws / PROJECT_TABLE
    updated_row = False
    if table.exists():
        lines = read_text(table).splitlines()
        header = None
        for i, ln in enumerate(lines):
            if not ln.strip().startswith("|"):
                continue
            cells = split_row(ln.strip())
            if header is None and any(c.lower() == "project" for c in cells):
                header = [c.lower() for c in cells]
                continue
            if header and len(cells) == len(header) and "slug" in header and cells[header.index("slug")] == slug:
                if "status" in header:
                    cells[header.index("status")] = "done"
                if "updated" in header:
                    cells[header.index("updated")] = today.isoformat()
                lines[i] = "| " + " | ".join(c.replace("|", "\\|") for c in cells) + " |"
                updated_row = True
        write_lf(table, "\n".join(lines) + "\n")
    idx = ws / REFERENCE / "INDEX.md"
    if idx.exists():
        write_lf(idx, read_text(idx).replace(f"../{PROJECTS}/{slug}/", f"../{ARCHIVE}/projects/{dest.name}/"))
    print(f"Moved {PROJECTS}/{slug} to {ARCHIVE}/projects/{dest.name}. Nothing was deleted.")
    print("The status row now says done." if updated_row else f"No status row for #{slug} in {PROJECT_TABLE}; update it by hand.")
    return 0


def cmd_daylog(args) -> int:
    ws = find_workspace(args.workspace)
    today = get_today(ws, args.today)
    folder = ws / MEMORY / "day-log"
    target = folder / f"{today.isoformat()}.md"
    if escapes_root(ws, target):
        sys.exit(f"Refusing to write {target}: it goes through a symlink or outside the workspace.")
    folder.mkdir(parents=True, exist_ok=True)
    if target.exists():
        print(f"Already exists: {target}")
        return 0
    template = folder / "_template.md"
    body = read_text(template) if template.is_file() and not template.is_symlink() else \
        "# Day log {{date}}\n\n## Moved forward\n\n## Still open\n\n## First move next session\n"
    body = body.replace("{{date}}", today.isoformat()).replace("{{weekday}}", today.strftime("%A"))
    write_lf(target, body)
    print(f"Created {target}")
    return 0


def iter_md(ws: Path, skip_dirs=(INBOX, ARCHIVE)):
    for p in sorted(ws.rglob("*.md")):
        rel = p.relative_to(ws)
        if rel.parts and rel.parts[0] in skip_dirs:
            continue
        yield p


def lint_workspace(ws: Path, today: dt.date):
    errors, warnings, info = [], [], []
    for rel in REQUIRED:
        if not (ws / rel).exists():
            errors.append(f"Missing {rel}. Run 'brain.py init' on this folder to restore it.")

    items, bad, unclosed = parse_followups(ws / FOLLOWUPS)
    if unclosed:
        errors.append(f"{FOLLOWUPS}: an HTML comment opened on line {unclosed} is never closed, so every line after it is hidden from the tools.")
    for n, line in bad:
        errors.append(f"{FOLLOWUPS} line {n} looks like a follow-up but does not match '- [ ] YYYY-MM-DD | @owner | deliverable | source | accepted: true|false': {line}")
    seen, no_since = {}, 0
    for it in items:
        if not OWNER_RE.match(it["owner"]):
            errors.append(f"{FOLLOWUPS} line {it['line']}: owner '{it['owner']}' should be @me or @waiting:Name.")
        if it["since_bad"]:
            warnings.append(f"{FOLLOWUPS} line {it['line']}: 'since:' is not a valid YYYY-MM-DD date.")
        if it["done"]:
            continue
        if it["waiting_on"] and it["since"] is None and not it["since_bad"]:
            no_since += 1
        key = (it["owner"].lower(), re.sub(r"\s+", " ", it["what"].lower()))
        if key in seen:
            warnings.append(f"{FOLLOWUPS} lines {seen[key]} and {it['line']} look like the same commitment.")
        else:
            seen[key] = it["line"]
        if len(it["what"]) < 8:
            warnings.append(f"{FOLLOWUPS} line {it['line']}: '{it['what']}' is too vague to be a deliverable.")
    if no_since:
        info.append(f"{no_since} waiting item(s) have no since: date, so they can never show as stale.")

    _, rows, bad_rows = parse_projects(ws / PROJECT_TABLE)
    for n, _ in bad_rows:
        errors.append(f"{PROJECT_TABLE} line {n} has the wrong number of columns.")
    for r in rows:
        status = r.get("status", "").strip().lower()
        if status and status not in STATUS_VALUES:
            warnings.append(f"{PROJECT_TABLE} line {r['_line']}: status '{status}' should be one of {', '.join(sorted(STATUS_VALUES))}.")
        role = r.get("role", "").strip().lower()
        if role and role not in ROLE_ORDER:
            warnings.append(f"{PROJECT_TABLE} line {r['_line']}: role '{role}' should be own, support, or watch.")

    dec = ws / MEMORY / "decisions.md"
    if dec.exists():
        lines = list(live_lines(read_text(dec)))
        starts = [i for i, (_, ln) in enumerate(lines) if DECISION_HEAD_RE.match(ln)]
        for idx, start in enumerate(starts):
            end = starts[idx + 1] if idx + 1 < len(starts) else len(lines)
            why = [ln for _, ln in lines[start:end] if ln.strip().lower().startswith("**why:**")]
            if not why or not why[0].split(":**", 1)[1].strip():
                warnings.append(f"{MEMORY}/decisions.md line {lines[start][0]}: decision has no reasoning under **Why:**.")

    knowledge = [ws / d for d in (PROJECTS, AREAS, REFERENCE) if (ws / d).is_dir()]
    rel_targets = [ws / FOLLOWUPS, ws / PROJECT_TABLE, ws / MEMORY / "decisions.md", ws / REFERENCE / "people.md"]
    sources = ws / REFERENCE / "sources"
    for d in knowledge:
        rel_targets += [p for p in d.rglob("*.md") if sources not in p.parents and p not in rel_targets]
    for p in rel_targets:
        if not p.exists():
            continue
        for n, line in live_lines(read_text(p)):
            m = REL_WORDS.search(QUOTED_RE.sub(" ", line))  # a quote keeps the speaker's words; the date column carries the date
            if m:
                warnings.append(f"{p.relative_to(ws)} line {n}: relative date '{m.group(0)}'. Write the absolute date.")

    for p in iter_md(ws):
        for n, line in live_lines(read_text(p)):
            for target in LINK_RE.findall(line):
                if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith(("#", "<")):
                    continue
                path_part = target.split("#", 1)[0]
                if path_part and not ((p.parent / path_part).exists() or (ws / path_part.lstrip("/")).exists()):
                    warnings.append(f"{p.relative_to(ws)} line {n}: broken link to '{target}'.")

    if knowledge:
        disputed = inferred = 0
        for p in (q for d in knowledge for q in d.rglob("*.md")):
            text = read_text(p)
            disputed += text.count("[disputed]")
            inferred += text.count("[inferred]")
            for m in REVIEW_RE.finditer(text):
                value = m.group(1)
                if value.startswith("<"):
                    continue
                day = parse_date(value)
                if day is None:
                    warnings.append(f"{p.relative_to(ws)}: review-by '{value}' is not a valid date.")
                elif day < today:
                    warnings.append(f"{p.relative_to(ws)}: review-by {value} has passed. Re-check the facts.")
        if disputed:
            info.append(f"{disputed} disputed claim(s) in the knowledge base. Resolve them with the source owner.")
        if inferred:
            info.append(f"{inferred} [inferred] claim(s) in the knowledge base. Confirm before anyone sends them.")
    raw = ws / INBOX
    if raw.is_dir():
        pending = [p for p in raw.iterdir() if p.is_file() and not p.name.startswith(".") and p.name.lower() != "readme.md"]
        if pending:
            info.append(f"{len(pending)} file(s) waiting in {INBOX}. Run /sync-kb on them.")
    return errors, warnings, info


def cmd_lint(args) -> int:
    ws = find_workspace(args.workspace)
    today = get_today(ws, args.today)
    errors, warnings, info = lint_workspace(ws, today)
    for label, group in (("Errors", errors), ("Warnings", warnings), ("Info", info)):
        if group:
            print(f"{label} ({len(group)})")
            for g in group:
                print(f"  - {g}")
    if not (errors or warnings or info):
        print("Workspace looks healthy.")
    return 1 if errors else 0


def luhn_ok(digits: str) -> bool:
    total, alt = 0, False
    for ch in reversed(digits):
        d = int(ch)
        if alt:
            d *= 2
            if d > 9:
                d -= 9
        total += d
        alt = not alt
    return total % 10 == 0


SCAN_PATTERNS = [
    ("high", "Private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("high", "AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("high", "Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("high", "GitHub token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b|\bgithub_pat_[A-Za-z0-9_]{40,}\b")),
    ("high", "Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("high", "Secret API key", re.compile(r"\b(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{16,}\b|\bsk-[A-Za-z0-9_\-]{24,}\b")),
    ("high", "JSON web token", re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}")),
    ("high", "US Social Security number", re.compile(r"\b(?!000|666|9\d\d)\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b")),
    ("medium", "Password or secret assignment", re.compile(r"(?i)\b(?:password|passwd|pwd|secret|api[_-]?key|access[_-]?token)\s*[:=]\s*[^\s<]{6,}")),
    ("medium", "Bank account (IBAN)", re.compile(r"\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]{4}){3,7}\b")),
    ("medium", "Account or routing number", re.compile(
        r"(?i)\b(?:account|acct|a/c|routing|aba|sort code|bsb)\s*(?:number|no\.?|num|#)?\s*[:#=]?\s*(?:\d[ -]?){6,17}\d\b")),
    ("medium", "UK National Insurance number", re.compile(r"\b(?!BG|GB|NK|KN|TN|NT|ZZ)[A-CEGHJ-PR-TW-Z][A-CEGHJ-NPR-TW-Z] ?\d{2} ?\d{2} ?\d{2} ?[A-D]\b")),
    ("medium", "Pay or compensation figure", re.compile(
        r"(?i)\b(?:salary|base pay|base salary|bonus|compensation|total comp|pay raise|raise|equity grant|RSUs?|stock options?|"
        r"offer|hourly rate|pay rate|pay band)\b[^\n]{0,30}?(?:[$€£]\s?\d[\d,.]*\s?[kKmM]?|\b\d[\d,.]*\s?[kKmM]?\s?(?:USD|EUR|GBP|CAD|AUD)\b|"
        r"\b\d[\d,.]*\s?[kK]?\s?(?:per year|a year|/yr|/year|per hour|an hour|/hr)\b)"
        r"|[$€£]\s?\d[\d,.]*\s?[kKmM]?\s+(?:base|salary|bonus|raise|OTE|total comp)\b"
        r"|\b(?:makes|earns|earning|is paid|gets paid|paid|bump (?:him|her|them) to|get (?:him|her|them) to|raise (?:him|her|them) to)\s+(?:about |around |roughly )?(?:[$€£]?\d{2,3}(?:[.,]\d+)?\s?[kK]\b|[$€£]?\d{2,3},\d{3}\b)"
        r"|\b(?:salary|base(?: pay| salary)?|offer|comp(?:ensation)?|bonus|raise|OTE)\s*(?:is|of|at|was|=|:)?\s*(?:about |around |roughly )?(?:[$€£]?\d{2,3}(?:[.,]\d+)?\s?[kK]\b|[$€£]?\d{2,3},\d{3}\b)")),
    ("medium", "HR matter", re.compile(
        r"(?i)\b(?:performance improvement plan|on a PIP|disciplinary (?:action|hearing|meeting)|written warning|final warning|"
        r"severance|harassment|grievance|HR (?:investigation|complaint|case)|misconduct|"
        r"(?:being|getting|was|were|will be|to be) (?:fired|let go|terminated|laid off)|layoff list|RIF list|demot(?:ed|ion)|laying (?:\w+ )?off|lay (?:\w+ )?off)\b")),
    ("medium", "Health detail", re.compile(
        r"(?i)\b(?:diagnosed with|medical leave|sick leave|disability leave|short-term disability|long-term disability|FMLA|"
        r"ADA accommodation|medical condition|mental health (?:leave|condition|issue|crisis)|prescribed|pregnan(?:t|cy)|"
        r"maternity leave|paternity leave|chemotherapy|hospitali[sz]ed|in rehab|patient (?:name|ID|record)|medical record number)\b")),
    ("low", "Date of birth label", re.compile(r"(?i)\b(?:dob|date of birth)\s*[:=]")),
    ("low", "Partial card number", re.compile(r"(?i)\b(?:card|visa|mastercard|amex)\b[^\n]{0,20}?\b(?:ending(?: in)?|last (?:4|four)|x{2,}|\*{2,})\s*:?\s*\d{4}\b")),
    ("low", "Email address", re.compile(r"\b[\w.+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b")),
    ("low", "Phone number", re.compile(r"(?<![\w-])(?:\+\d{1,3}[ .-]?)?\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}(?![\w-])")),
]
CARD_RE = re.compile(r"\b(?:\d[ -]?){12,18}\d\b")


def mask(value: str) -> str:
    value = value.strip()
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-2:]} ({len(value)} chars)"


def scan_text(text: str, label):
    findings = []
    for n, line in enumerate(text.splitlines(), 1):
        for sev, kind, pat in SCAN_PATTERNS:
            for m in pat.finditer(line):
                findings.append((sev, kind, label, n, mask(m.group(0))))
        for m in CARD_RE.finditer(line):
            digits = re.sub(r"\D", "", m.group(0))
            if 13 <= len(digits) <= 19 and luhn_ok(digits) and len(set(digits)) > 1:
                findings.append(("medium", "Payment card number", label, n, mask(digits)))
    return findings


def scan_paths(paths):
    """Return (findings, skipped) where skipped lists files that could not be scanned."""
    findings, skipped = [], []
    for root in paths:
        files = [root] if root.is_file() else sorted(p for p in root.rglob("*") if p.is_file())
        for p in files:
            if p.is_symlink():
                skipped.append((p, "symlink"))
                continue
            if p.name.startswith(".") and p.name != ".env":
                continue
            ext = p.suffix.lower()
            if ext not in TEXT_EXT:
                skipped.append((p, ext or "no extension"))
                continue
            if p.stat().st_size > MAX_SCAN_BYTES:
                skipped.append((p, "too large"))
                continue
            try:
                findings.extend(scan_text(read_text(p), p))
            except OSError:
                skipped.append((p, "unreadable"))
    return findings, skipped


def cmd_scan(args) -> int:
    if args.stdin:
        findings, skipped, base = scan_text(sys.stdin.read(), "stdin"), [], None
    else:
        if args.path:
            target = Path(args.path).expanduser().resolve()
            if not target.exists():
                sys.exit(f"Nothing at {target}.")
            base = target if target.is_dir() else target.parent
        else:
            target = base = find_workspace(args.workspace)
        findings, skipped = scan_paths([target])

    def where(p):
        if base is None or not isinstance(p, Path):
            return str(p)
        try:
            return str(p.relative_to(base))
        except ValueError:
            return str(p)

    order = {"high": 0, "medium": 1, "low": 2}
    serious = sorted([f for f in findings if f[0] != "low"], key=lambda f: (order[f[0]], str(f[2]), f[3]))
    low = {}
    for sev, kind, p, n, _ in findings:
        if sev == "low":
            low.setdefault((kind, where(p)), []).append(n)
    if serious:
        print(f"{len(serious)} possible finding(s). Matches are masked.")
        for sev, kind, p, n, shown in serious:
            print(f"  [{sev}] {kind}: {where(p)} line {n}: {shown}")
    if low:
        print("Personal identifiers to review (low severity):")
        for (kind, w), lines in sorted(low.items()):
            print(f"  [low] {kind}: {w}, {len(lines)} occurrence(s), first on line {lines[0]}")
    if skipped:
        kinds = {}
        for _, why in skipped:
            kinds[why] = kinds.get(why, 0) + 1
        summary = ", ".join(f"{k} x{v}" for k, v in sorted(kinds.items()))
        print(f"Not scanned: {len(skipped)} file(s) ({summary}). Extract their text and run 'scan --stdin', or review them by hand.")
    if not serious and not low:
        print("No findings in the text that was scanned." if skipped else
              "No likely secrets or personal identifiers found. (A clean scan is a lead, not a guarantee.)")
    if serious or low:
        print("Redact real hits with stable tokens such as [ACCOUNT-REDACTED]. Raw drops with restricted data should be removed by the user, not filed.")
    if any(f[0] == "high" for f in findings):
        return 1
    if any(f[0] == "medium" for f in findings):
        return 4
    return 3 if skipped else 0


def cmd_pack(args) -> int:
    ws = find_workspace(args.workspace)
    today = get_today(ws, getattr(args, "today", None))
    out = Path(args.output).expanduser().resolve() if args.output else ws.parent / f"second-brain-{today.isoformat()}.zip"
    if out.is_dir() or (args.output and (str(args.output).endswith(("/", "\\")) or out.suffix.lower() != ".zip")):
        out.mkdir(parents=True, exist_ok=True)
        out = out / f"second-brain-{today.isoformat()}.zip"
    try:
        out.resolve().relative_to(ws.resolve())
        sys.exit(f"Pack to a folder outside the workspace (the download folder), not {out}. A zip inside the workspace gets packed into the next zip.")
    except ValueError:
        pass
    out.parent.mkdir(parents=True, exist_ok=True)
    count = left_out = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(ws.rglob("*")):
            if p.is_symlink() or not p.is_file() or p.resolve() == out:
                continue
            rel = p.relative_to(ws)
            if not args.include_inbox and rel.parts[:1] == (INBOX,) and p.name.lower() != "readme.md":
                left_out += 1
                continue
            z.write(p, (Path("workspace") / rel).as_posix())
            count += 1
    print(f"Packed {count} file(s) into {out}")
    if left_out:
        print(f"Left out {left_out} raw drop(s) in {INBOX} (use --include-inbox to keep them).")
    print(f"Check: the zip exists ({out.stat().st_size // 1024 or 1} KB). To restore: brain.py unpack <zip> <folder>")
    return 0


def cmd_unpack(args) -> int:
    src = Path(args.zipfile).expanduser().resolve()
    dest = Path(args.folder).expanduser().resolve()
    dest.mkdir(parents=True, exist_ok=True)
    written, kept, unsafe, same = 0, [], [], 0
    with zipfile.ZipFile(src) as z:
        names = [i.filename.replace("\\", "/") for i in z.infolist() if not i.is_dir()]
        tops = {n.split("/", 1)[0] for n in names if "/" in n}
        # A zip of the folder itself (for example "Second Brain/...") unpacks the same as one made by pack.
        wrapper = next(iter(tops)) if len(tops) == 1 and all("/" in n for n in names) and any(
            n.split("/", 1)[1] in ("START-HERE.md", "AGENTS.md") or n.split("/", 1)[1].startswith("Memory/") for n in names) else None
        for info in z.infolist():
            if info.is_dir():
                continue
            parts = Path(info.filename.replace("\\", "/")).parts
            if parts and (parts[0] == "workspace" or parts[0] == wrapper):
                parts = parts[1:]
            if not parts or info.filename.startswith(("/", "\\")) or any(x in ("..", "") or ":" in x for x in parts):
                unsafe.append(info.filename)
                continue
            target = dest.joinpath(*parts)
            if os.path.commonpath([str(dest), str(target.resolve())]) != str(dest) or escapes_root(dest, target):
                unsafe.append(info.filename)
                continue
            if target.exists() and not args.overwrite:
                if target.is_file() and target.read_bytes() == z.read(info):
                    same += 1
                    continue
                template = TEMPLATES.joinpath(*parts)
                untouched = template.is_file() and target.is_file() and target.read_bytes() == template.read_bytes()
                if not untouched:
                    kept.append("/".join(parts))
                    continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(info) as fsrc, open(target, "wb") as fdst:
                shutil.copyfileobj(fsrc, fdst)
            written += 1
    for d in sorted(TEMPLATES.rglob("*")):
        if d.is_dir():
            folder = dest / d.relative_to(TEMPLATES)
            if not escapes_root(dest, folder / "x"):
                folder.mkdir(parents=True, exist_ok=True)
    print(f"Restored {written} file(s) into {dest}" + (f"; {same} already matched the zip" if same else ""))
    if kept:
        print(f"Kept {len(kept)} existing file(s) that differ from the zip. Pass --overwrite to replace them with the zip's versions.")
    if unsafe:
        print(f"Refused {len(unsafe)} unsafe path(s) in the zip: {', '.join(unsafe[:5])}")
    return 0


# ---------------------------------------------------------------- selftest

def cmd_selftest(args) -> int:
    checks = []

    def check(name, cond):
        checks.append((name, bool(cond)))

    quiet = contextlib.redirect_stdout(io.StringIO())
    today = dt.date(2026, 10, 7)  # a Wednesday
    check("business day add skips the weekend", add_business_days(dt.date(2026, 10, 9), 1) == dt.date(2026, 10, 12))
    check("business days between counts weekdays", business_days_between(dt.date(2026, 9, 25), today) == 8)
    mon = dt.date(2026, 10, 5)
    w = {ph: resolve_when(ph, mon) for ph in ("Thursday", "by Thursday", "next Tuesday", "end of month", "end of next week",
                                               "tomorrow", "10/9", "Oct 9", "in 3 business days", "soon", "Monday", "Q1", "whenever-ish", "by the 15th")}
    check("when: weekdays are exact", w["Thursday"][:2] == (dt.date(2026, 10, 8), True) and w["by Thursday"][0] == dt.date(2026, 10, 8))
    check("when: 'next Tuesday' is a guess that names the other reading", w["next Tuesday"][0] == dt.date(2026, 10, 13) and not w["next Tuesday"][1] and "2026-10-06" in w["next Tuesday"][2])
    check("when: end of month is the last business day, as a guess", w["end of month"][:2] == (dt.date(2026, 10, 30), False))
    check("when: end of next week is Friday next week", w["end of next week"][0] == dt.date(2026, 10, 16))
    check("when: dates and offsets", w["tomorrow"][0] == dt.date(2026, 10, 6) and w["10/9"][0] == w["Oct 9"][0] == dt.date(2026, 10, 9) and w["in 3 business days"][0] == dt.date(2026, 10, 8))
    check("when: vague words become labeled placeholders", w["soon"][1] is False and w["soon"][0] == dt.date(2026, 10, 12))
    check("when: today's weekday means next week, as a guess", w["Monday"][:2] == (dt.date(2026, 10, 12), False))
    check("when: quarters and days of the month", w["Q1"][0] == dt.date(2027, 3, 31) and w["by the 15th"][0] == dt.date(2026, 10, 15))
    check("when: refuses what it can't read", w["whenever-ish"][0] is None)
    sun = dt.date(2026, 10, 4)
    check("when: 'next Tuesday' on a weekend is a guess", resolve_when("next Tuesday", sun)[1] is False)
    check("when: 'end of next week' on a weekend is a guess", resolve_when("end of next week", sun)[1] is False)
    check("when: ambiguous slash dates are guesses; clear ones aren't", resolve_when("10/11", mon)[1] is False and resolve_when("15/10", mon)[:2] == (dt.date(2026, 10, 15), True))
    check("when: 'two weeks ago' is a labeled guess", resolve_when("two weeks ago", mon)[:2] == (dt.date(2026, 9, 21), False))
    check("when: a hedge makes a date a guess", resolve_when("by Thursday I think", mon)[:2] == (dt.date(2026, 10, 8), False))
    check("when: 'Friday?' is a guess", resolve_when("Friday?", mon)[:2] == (dt.date(2026, 10, 9), False))
    check("when: 'end of month-ish' is a guess", resolve_when("end of month-ish", mon)[1] is False and resolve_when("end of month-ish", mon)[0] is not None)
    check("when: a bare hedge still can't be read", resolve_when("maybe", mon)[0] is None)
    check("slugs avoid Windows device names and never collide on non-Latin names",
          slugify("CON") == "con-project" and fallback_slug("project", "定价") != fallback_slug("project", "发布"))
    check("weekend lateness is worded, not zero", late_text(dt.date(2026, 10, 9), dt.date(2026, 10, 11)) == "past due over the weekend")
    check("singular business day", late_text(dt.date(2026, 10, 6), today) == "1 business day late")

    with tempfile.TemporaryDirectory() as tmp:
        ws = Path(tmp) / "ws"
        with contextlib.redirect_stdout(io.StringIO()):
            rc = cmd_init(argparse.Namespace(folder=str(ws), dry_run=False, force=False))
        check("init succeeds", rc == 0)
        for rel in REQUIRED:
            check(f"init creates {rel}", (ws / rel).exists())
        marker = ws / MEMORY / "lessons.md"
        marker.write_text("keep me\n", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            cmd_init(argparse.Namespace(folder=str(ws), dry_run=False, force=False))
        check("init never overwrites", read_text(marker) == "keep me\n")
        check("guardrail template ships safe defaults", "<" not in read_text(ws / SETUP / "guardrail-profile.md").split("## Never")[1])

        found, skipped = scan_paths([ws])
        check("templates scan clean", not found)
        errors, warnings, _ = lint_workspace(ws, today)
        check("fresh workspace has no lint errors", not errors)
        check("fresh workspace has no lint warnings", not warnings)

        (ws / FOLLOWUPS).write_text("\n".join([
            "# Follow-ups",
            "- [ ] 2026-10-05 | @me | send revised timeline #launch | standup 10/05 | accepted: true",
            "- [ ] 2026-10-07 | @me | review pricing deck #launch | email 10/06 | accepted: true",
            "- [ ] ~2026-10-09 | @me | draft FAQ for support #launch | 1:1 10/06 | accepted: true",
            "- [ ] 2026-10-20 | @me | plan Q1 offsite | email 10/01 | accepted: true",
            "- [x] 2026-10-01 | @me | close out vendor survey | email 09/30 | accepted: true",
            "- [ ] 2026-10-06 | @waiting:Priya | security review notes #launch | email since:2026-10-01 | accepted: true",
            "- [ ] 2026-10-30 | @waiting:Sam | data export for analysis | since:2026-09-25 email | accepted: true",
            "- [ ] 2026-10-15 | @waiting:Lee | legal sign-off | thread since:2026-10-06 | accepted: false",
            "- [ ] 2027-03-01 | @waiting:Kim | annual vendor renewal notes | email since:2026-10-01 | accepted: false",
            "- [ ] 2026-10-05 | @me | send revised timeline #launch | duplicate | accepted: true",
            "- [ ] 2026-10-08 | @me | trailing comment still counts | 1:1 10/06 | accepted: true <!-- a note -->",
            "- [ ] 2026-10-08 | @Ana | owner written wrong | chat | accepted: true",
            "- [ ] 2026-10-20 | @waiting:Jo | bad since date here | email since:2026-13-45 | accepted: true",
            "- [ ] tomorrow | send the deck",
            "* [ ] 2026-10-01 | @me | wrong bullet marker | chat | accepted: true",
            "- [  ] 2026-10-01 | @me | two spaces in box | chat | accepted: true",
        ]) + "\n", encoding="utf-8")
        items, bad, unclosed = parse_followups(ws / FOLLOWUPS)
        out, horizon = compute_due(items, today, 3, 5)
        check("horizon is three business days out", horizon == dt.date(2026, 10, 12))
        check("overdue mine found", [i["what"] for i in out["overdue"]].count("send revised timeline #launch") == 2)
        check("due today found", len(out["due_today"]) == 1)
        check("due soon includes guessed and trailing-comment items", len(out["due_soon"]) == 2 and any(i["guessed"] for i in out["due_soon"]))
        check("far-off item excluded", all("offsite" not in i["what"] for k in out for i in out[k]))
        check("done item excluded", all("vendor survey" not in i["what"] for k in out for i in out[k]))
        check("waiting past due found", len(out["waiting_overdue"]) == 1)
        check("waiting stale found", len(out["waiting_stale"]) == 1 and out["waiting_stale"][0]["waiting_on"] == "Sam")
        check("unconfirmed limited to the confirm window", [i["waiting_on"] for i in out["unconfirmed"]] == ["Lee"])
        check("unknown owner surfaced, not dropped", [i["owner"] for i in out["unknown_owner"]] == ["@Ana"])
        check("malformed lines caught (no date, star bullet, double space)", len(bad) == 3)
        check("no unclosed comment in a clean file", unclosed is None)

        (ws / PROJECT_TABLE).write_text("\n".join([
            "# Projects",
            "| Project | Slug | Role | Status | Next step | Next checkpoint | Updated |",
            "|---|---|---|---|---|---|---|",
            "| Launch v2 | launch | own | on-track | lock the timeline | 2026-10-09 | 2026-10-06 |",
            "| Vendor survey | vendor | support | done | | 2026-10-01 | 2026-09-01 |",
            "| Market watch | market | watch | on-track | read the report | 2026-11-01 | 2026-10-01 |",
            "| Pricing A\\|B test | pricing | own | at-risk | pick the winner | 2026-10-10 | 2026-10-06 |",
        ]) + "\n", encoding="utf-8")
        table, notes = build_status(ws, today, False, 14)
        check("status includes owned project", "Launch v2" in table)
        check("status counts tagged follow-ups", "| 4 / 1 |" in table)
        check("status hides watch by default", "Market watch" not in table)
        check("status flags stale project", any("Vendor survey" in n and "days ago" in n for n in notes))
        check("status flags on-track with overdue items", any("Launch v2" in n and "overdue" in n for n in notes))
        check("status keeps escaped pipes", "Pricing A\\|B test" in table)
        table_all, _ = build_status(ws, today, True, 14)
        check("status --all includes watch", "Market watch" in table_all)

        (ws / PROJECTS).mkdir(parents=True, exist_ok=True)
        (ws / PROJECTS / "launch.md").write_text(
            "# Launch\nreview-by: 2026-09-01\n- Ships in Q4 [inferred]\n- See [the brief](missing-brief.md)\n- Decide by next week\n",
            encoding="utf-8")
        (ws / REFERENCE / "sources" / "quote.md").write_text("Priya said: we can do it by Friday, maybe tomorrow.\n", encoding="utf-8")
        (ws / AREAS).mkdir(parents=True, exist_ok=True)
        (ws / AREAS / "quoted.md").write_text("# Quoted\n- Marco said \"I'll have the rollback plan by Tuesday\" (due 2026-10-13)\n", encoding="utf-8")
        errors, warnings, info = lint_workspace(ws, today)
        check("lint flags malformed follow-ups", sum("does not match" in e for e in errors) == 3)
        check("lint flags unknown owner", any("'@Ana'" in e for e in errors))
        check("lint flags invalid since date", any("since:" in w for w in warnings))
        check("lint flags duplicate commitment", any("same commitment" in w for w in warnings))
        check("lint flags broken link", any("broken link" in w for w in warnings))
        check("lint flags stale review date", any("review-by 2026-09-01" in w for w in warnings))
        check("lint flags relative date", any("relative date" in w and "launch.md" in w for w in warnings))
        check("lint leaves quoted sources alone", not any("quote.md" in w for w in warnings))
        check("lint leaves a quoted relative date alone", not any("quoted.md" in w for w in warnings))
        check("lint counts inferred claims", any("[inferred]" in i for i in info))

        fu = ws / FOLLOWUPS
        fu.write_text(read_text(fu) + "<!-- forgot to close this\n- [ ] 2026-10-01 | @me | hidden overdue item | chat | accepted: true\n", encoding="utf-8")
        _, _, unclosed = parse_followups(fu)
        errors, _, _ = lint_workspace(ws, today)
        check("unclosed comment detected", unclosed is not None and any("never closed" in e for e in errors))

        leak = ws / INBOX / "export.txt"
        leak.write_text("key AKIA" + "ABCDEFGHIJKLMNOP\ncard 4111 1111 1111 1111\nssn 123-45-6789\n"
                        "contact jane.doe@example.com or (555) 123-4567\n", encoding="utf-8")
        (ws / INBOX / "deck.pdf").write_bytes(b"%PDF-1.4 binary")
        found, skipped = scan_paths([ws])
        kinds = {f[1] for f in found}
        check("scan catches access key", "AWS access key" in kinds)
        check("scan catches card number", "Payment card number" in kinds)
        check("scan catches SSN", "US Social Security number" in kinds)
        check("scan flags email and phone as low", {"Email address", "Phone number"} <= kinds)
        check("scan masks values", all("ABCDEFGHIJKLMNOP" not in f[4] for f in found))
        check("scan reports files it could not read", any(p.name == "deck.pdf" for p, _ in skipped))
        check("scan of plain text works without files", any(f[1] == "US Social Security number" for f in scan_text("id 123-45-6789", "stdin")))
        sensitive = ("Offered Dana $145k base plus a 10% bonus.\nMarco is on a performance improvement plan.\nSam makes 118k and I want to get him to 130k.\n"
                     "Sam makes $118,000.\nHer salary of 118k is low.\nThe base is $118k.\nThe offer is 140k.\nWe're laying off two people.\n"
                     "Sam is out on medical leave until March.\nHer salary is 120,000 USD.\n")
        s_kinds = {f[1] for f in scan_text(sensitive, "stdin")}
        check("scan flags pay, HR, and health details", {"Pay or compensation figure", "HR matter", "Health detail"} <= s_kinds)
        benign = ("We diagnosed the outage and fixed SSL termination.\nBonus round: 10k new users signed up.\n"
                  "The offer page loads in 2 seconds.\nRaise the issue with the platform team.\n")
        acct = {f[1] for f in scan_text("Account number: 00123456789\nacct # 4455667788\nrouting 021000021\nNI: AB 12 34 56 C\n", "stdin")}
        check("scan flags account, routing, and NI numbers", {"Account or routing number", "UK National Insurance number"} <= acct)
        check("scan flags a card's last four as low", any(f[1] == "Partial card number" for f in scan_text("billed twice, card ending 1111", "stdin")))
        check("scan leaves ordinary work talk alone", not [f for f in scan_text(benign, "stdin") if f[0] != "low"])

        with contextlib.redirect_stdout(io.StringIO()):
            rc = cmd_daylog(argparse.Namespace(workspace=str(ws), today=today.isoformat()))
        check("daylog creates today's file", rc == 0 and (ws / MEMORY / "day-log" / "2026-10-07.md").exists())
        check("daylog fills the date", "2026-10-07" in read_text(ws / MEMORY / "day-log" / "2026-10-07.md"))
        pw = Path(tmp) / "projects-ws"
        with contextlib.redirect_stdout(io.StringIO()):
            cmd_init(argparse.Namespace(folder=str(pw), dry_run=False, force=False))
            rc_p = cmd_project(argparse.Namespace(name="Pricing Refresh", slug=None, role="own", next="draft the options", workspace=str(pw), today="2026-10-07"))
            rc_p2 = 0
            try:
                cmd_project(argparse.Namespace(name="Pricing Refresh", slug=None, role="own", next=None, workspace=str(pw), today="2026-10-07"))
                rc_p2 = 0
            except SystemExit:
                rc_p2 = 1
            cmd_area(argparse.Namespace(name="Hiring", slug=None, workspace=str(pw)))
            cmd_area(argparse.Namespace(name="Ramping up", slug=None, workspace=str(pw), ramp_up=True, started="2026-10-01"))
        check("project creates a folder from the template", rc_p == 0 and "Pricing Refresh" in read_text(pw / PROJECTS / "pricing-refresh" / "current.md"))
        _, prow, _ = parse_projects(pw / PROJECT_TABLE)
        check("project adds one status row", [r["slug"] for r in prow] == ["pricing-refresh"] and prow[0]["updated"] == "2026-10-07")
        check("project refuses a duplicate", rc_p2 == 1)
        ramp = read_text(pw / AREAS / "ramping-up.md")
        check("ramp-up area gets the 30-60-90 page and dates", "First 30 days" in ramp and "Started on: 2026-10-01" in ramp and "<YYYY" not in ramp.split("Started on")[0])
        check("area creates a page and an index line", (pw / AREAS / "hiring.md").exists() and "3-Areas/hiring.md" in read_text(pw / REFERENCE / "INDEX.md"))
        (pw / FOLLOWUPS).write_text(read_text(pw / FOLLOWUPS) + "- [ ] 2026-10-09 | @me | send the pricing options #pricing-refresh | standup | accepted: true\n", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            rc_a = cmd_archive(argparse.Namespace(slug="pricing-refresh", force=False, workspace=str(pw), today="2026-10-08"))
        check("archive refuses while follow-ups are open", rc_a == 1 and (pw / PROJECTS / "pricing-refresh").is_dir())
        with contextlib.redirect_stdout(io.StringIO()):
            rc_a = cmd_archive(argparse.Namespace(slug="pricing-refresh", force=True, workspace=str(pw), today="2026-10-08"))
        _, prow, _ = parse_projects(pw / PROJECT_TABLE)
        check("archive moves, never deletes, and marks done", rc_a == 0 and (pw / ARCHIVE / "projects" / "pricing-refresh" / "current.md").exists()
              and not (pw / PROJECTS / "pricing-refresh").exists() and prow[0]["status"] == "done")
        lint_e, lint_w, _ = lint_workspace(pw, dt.date(2026, 10, 8))
        with contextlib.redirect_stdout(io.StringIO()):
            cmd_project(argparse.Namespace(name="Launch v2", slug=None, role="own", next=None, workspace=str(pw), today="2026-10-08"))
            cmd_area(argparse.Namespace(name="Café Ünïcode", slug=None, workspace=str(pw)))
            cmd_project(argparse.Namespace(name="Pipe | [Name]", slug=None, role="watch", next=None, workspace=str(pw), today="2026-10-08"))
        idx_text = read_text(pw / REFERENCE / "INDEX.md")
        check("index takes names that match the commented examples", "](../2-Projects/launch-v2/current.md)" in "\n".join(ln for _, ln in live_lines(idx_text)))
        check("accented names get a plain slug", (pw / AREAS / "cafe-unicode.md").exists())
        _, prow2, bad2 = parse_projects(pw / PROJECT_TABLE)
        check("pipes and brackets in a name keep the table valid", not bad2 and any(r["slug"] == "pipe-name" for r in prow2))
        check("index link follows the archived project", not [w for w in lint_w if "broken link" in w])
        manual = SKILL_DIR / "references" / "no-python.md"
        if manual.exists():
            section = read_text(manual).split("## Build the folders by hand", 1)[-1].split("\n## ", 1)[0]
            listed = set(re.findall(r"^- `([^`]+)`", section, flags=re.M))
            shipped = {q.relative_to(TEMPLATES).as_posix() for q in TEMPLATES.rglob("*") if q.is_file() and q.name != ".keep"}
            check("no-python manifest lists every template file", listed == shipped)

        zpath = Path(tmp) / "pack.zip"
        with contextlib.redirect_stdout(io.StringIO()):
            cmd_pack(argparse.Namespace(workspace=str(ws), output=str(zpath), include_inbox=False))
            outdir = Path(tmp) / "downloads"; outdir.mkdir()
            cmd_pack(argparse.Namespace(workspace=str(ws), output=str(outdir), include_inbox=False))
        with zipfile.ZipFile(zpath) as z:
            names = z.namelist()
        check("pack into a folder writes a dated zip inside it", len(list((Path(tmp) / "downloads").glob("second-brain-*.zip"))) == 1)
        check("pack includes memory", f"workspace/{PROJECT_TABLE}" in names)
        check("pack leaves raw drops out", not any(n.endswith("export.txt") for n in names))
        restored = Path(tmp) / "restored"
        with contextlib.redirect_stdout(io.StringIO()):
            cmd_unpack(argparse.Namespace(zipfile=str(zpath), folder=str(restored), overwrite=False))
        check("unpack restores files", (restored / PROJECT_TABLE).exists())
        evil = Path(tmp) / "evil.zip"
        with zipfile.ZipFile(evil, "w") as z:
            z.writestr("workspace/../../escaped.txt", "x")
            z.writestr("/abs.txt", "x")
        with contextlib.redirect_stdout(io.StringIO()):
            cmd_unpack(argparse.Namespace(zipfile=str(evil), folder=str(restored), overwrite=False))
        wrapped = Path(tmp) / "wrapped.zip"
        with zipfile.ZipFile(wrapped, "w") as z:
            z.writestr("Second Brain/START-HERE.md", "# Start here\n")
            z.writestr("Second Brain/Memory/followups.md", "# Follow-ups\n")
        into = Path(tmp) / "into"
        with contextlib.redirect_stdout(io.StringIO()):
            cmd_unpack(argparse.Namespace(zipfile=str(wrapped), folder=str(into), overwrite=False))
        with contextlib.redirect_stdout(io.StringIO()) as again:
            cmd_unpack(argparse.Namespace(zipfile=str(wrapped), folder=str(into), overwrite=False))
        check("unpacking the same zip twice reports matches, not conflicts", "already matched" in again.getvalue() and "differ" not in again.getvalue())
        deep = Path(tmp) / "not" / "there" / "yet"
        with contextlib.redirect_stdout(io.StringIO()):
            cmd_pack(argparse.Namespace(workspace=str(ws), output=str(deep), include_inbox=False, today="2026-10-05"))
        check("pack makes the download folder if it's missing", (deep / "second-brain-2026-10-05.zip").is_file())
        check("unpack accepts a zip of the folder itself", (into / "Memory" / "followups.md").is_file() and not (into / "Second Brain").exists())
        check("unpack refuses path traversal", not (Path(tmp) / "escaped.txt").exists() and not Path("/abs.txt").exists())

        if hasattr(os, "symlink"):
            outside = Path(tmp) / "outside"
            outside.mkdir()
            ws2 = Path(tmp) / "ws2"
            (ws2 / MEMORY).mkdir(parents=True)
            try:
                os.symlink(outside, ws2 / MEMORY / "day-log")
                with contextlib.redirect_stdout(io.StringIO()):
                    try:
                        cmd_daylog(argparse.Namespace(workspace=str(ws2), today=today.isoformat()))
                    except SystemExit:
                        pass
                check("daylog refuses to write through a symlink", not any(outside.iterdir()))
            except OSError:
                pass

        fenced = Path(tmp) / "fenced.md"
        fenced.write_text("```\n- [ ] 2026-10-01 | @me | example inside a code fence | doc | accepted: true\n```\n"
                          "- [x] 2026-10-05 | @me | send revised timeline #launch | standup (duplicate of line 2) | accepted: true\n", encoding="utf-8")
        f_items, f_bad, _ = parse_followups(fenced)
        check("follow-ups inside code fences are ignored", len(f_items) == 1 and not f_bad)
        check("the /tidy duplicate note keeps the line valid", f_items and f_items[0]["done"])

        fresh = Path(tmp) / "fresh"
        with contextlib.redirect_stdout(io.StringIO()):
            cmd_init(argparse.Namespace(folder=str(fresh), dry_run=False, force=False))
            cmd_unpack(argparse.Namespace(zipfile=str(zpath), folder=str(fresh), overwrite=False))
        check("unpack over an untouched new workspace restores the packed files", "Launch v2" in read_text(fresh / PROJECT_TABLE))
        check("unpack recreates empty folders", (restored / ARCHIVE / "processed").is_dir() and (restored / REFERENCE / "sources" / "meetings").is_dir() and (restored / AREAS).is_dir())

        card_only = Path(tmp) / "card.txt"
        card_only.write_text("card 4111 1111 1111 1111\n", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            rc_medium = cmd_scan(argparse.Namespace(stdin=False, path=str(card_only), workspace="."))
        check("scan exits 4 on a medium finding", rc_medium == 4)

        repo = Path(tmp) / "repo"
        (repo / ".git").mkdir(parents=True)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                cmd_init(argparse.Namespace(folder=str(repo / "sub" / "brain"), dry_run=False, force=False))
            nested_refused = False
        except SystemExit:
            nested_refused = True
        check("init refuses a folder nested inside a code repository", nested_refused)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                cmd_init(argparse.Namespace(folder=str(repo), dry_run=False, force=False))
            refused = False
        except SystemExit:
            refused = True
        check("init refuses a code repository without --force", refused)

        try:
            get_today(None, "2026-10-4")
            friendly = False
        except SystemExit as exc:
            friendly = "YYYY-MM-DD" in str(exc)
        check("bad --today gives a friendly error", friendly)

    passed = sum(1 for _, ok in checks if ok)
    for name, ok in checks:
        if not ok:
            print(f"FAIL  {name}")
    print(f"{passed}/{len(checks)} checks passed")
    return 0 if passed == len(checks) else 1


# ---------------------------------------------------------------- main

def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):  # Windows consoles and pipes default to a narrow code page
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
    parser = argparse.ArgumentParser(description="Deterministic helpers for the unpaid-intern skill.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    def add_common(p, today=True):
        p.add_argument("--workspace", default=".", help="workspace folder (default: current folder)")
        if today:
            p.add_argument("--today", help="override today's date, YYYY-MM-DD")

    p = sub.add_parser("init", help="create a workspace from templates")
    p.add_argument("folder")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true", help="allow a folder that is a code repository")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("now", help="current date and time")
    p.add_argument("--tz", help="IANA timezone, e.g. America/Chicago")
    p.add_argument("--workspace", default=".")
    p.set_defaults(func=cmd_now)

    p = sub.add_parser("due", help="follow-ups due, overdue, and waiting")
    add_common(p)
    p.add_argument("--days", type=int, default=3, help="business days ahead counted as due soon")
    p.add_argument("--stale", type=int, default=5, help="business days before a waiting item is stale")
    p.add_argument("--json", action="store_true")
    p.add_argument("--open", action="store_true", help="session open: only what is due today, overdue, or stale")
    p.set_defaults(func=cmd_due)

    p = sub.add_parser("when", help="turn spoken deadlines (Thursday, end of month) into dates; guesses get ~")
    p.add_argument("phrase", nargs="+")
    add_common(p)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_when)

    p = sub.add_parser("status", help="paste-ready project status table")
    add_common(p)
    p.add_argument("--all", action="store_true", help="include projects you only watch")
    p.add_argument("--copy", action="store_true", help="copy the table to the clipboard")
    p.add_argument("--stale-days", type=int, default=14)
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("daylog", help="create today's day log")
    add_common(p)
    p.set_defaults(func=cmd_daylog)

    p = sub.add_parser("project", help="create a project folder and its status row")
    p.add_argument("name")
    p.add_argument("--slug")
    p.add_argument("--role", default="own", help="own, support, or watch")
    p.add_argument("--status", default="unconfirmed", choices=sorted(STATUS_VALUES - {"done"}), help="only what the person said; unconfirmed until they do")
    p.add_argument("--next", help="next step")
    add_common(p)
    p.set_defaults(func=cmd_project)

    p = sub.add_parser("area", help="create a page for an ongoing responsibility")
    p.add_argument("name")
    p.add_argument("--slug")
    p.add_argument("--ramp-up", action="store_true", help="use the 30-60-90 ramp-up page")
    p.add_argument("--started", help="start date for --ramp-up, YYYY-MM-DD")
    add_common(p, today=False)
    p.set_defaults(func=cmd_area)

    p = sub.add_parser("archive", help="move a finished project to the archive (never deletes)")
    p.add_argument("slug")
    p.add_argument("--force", action="store_true", help="archive even with open follow-ups")
    add_common(p)
    p.set_defaults(func=cmd_archive)

    p = sub.add_parser("lint", help="check the workspace")
    add_common(p)
    p.set_defaults(func=cmd_lint)

    p = sub.add_parser("scan", help="flag likely secrets and personal data")
    add_common(p, today=False)
    g = p.add_mutually_exclusive_group()
    g.add_argument("--path", help="scan this file or folder instead of the workspace")
    g.add_argument("--stdin", action="store_true", help="scan text piped in, such as text extracted from a PDF")
    p.set_defaults(func=cmd_scan)

    p = sub.add_parser("pack", help="zip the workspace to carry it between sessions")
    add_common(p)
    p.add_argument("--output", help="zip file to write (default: next to the workspace)")
    p.add_argument("--include-inbox", action="store_true", help="also pack raw drops")
    p.set_defaults(func=cmd_pack)

    p = sub.add_parser("unpack", help="restore a packed workspace")
    p.add_argument("zipfile")
    p.add_argument("folder")
    p.add_argument("--overwrite", action="store_true", help="replace files that already exist")
    p.set_defaults(func=cmd_unpack)

    p = sub.add_parser("selftest", help="run the built-in tests")
    p.set_defaults(func=cmd_selftest)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
