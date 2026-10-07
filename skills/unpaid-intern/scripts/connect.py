#!/usr/bin/env python3
"""connect.py: connect work tools to the second brain, and fix them when they don't connect.

Built for people who have never set up a connector. It turns "which tools do
you use?" into a personal plan, decodes error messages into plain language,
writes the request to IT, and (only when asked) tests the network.

Standard library only. Python 3.9 or newer. Only `check` uses the network.

Usage:
  connect.py list [--category C] [--json]          every known tool and how it connects
  connect.py screens [--screen ID] [--role R] [--json]  setup questions, ready for a picker
  connect.py match <answer> [<answer> ...]         turn picker answers or tool names into tools
  connect.py plan --tools a,b [--surface S]        write Setup/connection-plan.md (keeps statuses)
  connect.py mark <tool> <status> [--note TEXT]    record how a connection went
  connect.py diagnose [TEXT | --stdin] [--tool T]  explain an error message and what to do
  connect.py it-request [--tools a,b] [--write]    one email to IT for everything that needs an admin
  connect.py tour [--help-first ...] [--write]     what the connected tools unlock, with a try-it for each
  connect.py mcp-json --tools a,b [--write]        Claude Code config, read-only addresses first
  connect.py check [--tools a,b] [--timeout 8]     network test from THIS computer (opt-in)
  connect.py export-md [--check]                   refresh the markdown copies used when Python can't run
  connect.py selftest                              run the built-in tests

Surfaces: cowork, desktop, web, code. Statuses: to-do, connected, needs-admin,
failed, using-fallback, skipped. plan, mark, tour, it-request, and check take
--workspace <folder> (default: current folder).
"""
from __future__ import annotations

import argparse
import contextlib
import io
import datetime as dt
import difflib
import json
import os
import re
import shutil
import socket
import ssl
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def utf8_console(streams=None) -> None:
    """Windows consoles and pipes default to a narrow code page. Print UTF-8 so text never garbles or crashes there."""
    for s in ((sys.stdout, sys.stderr) if streams is None else streams):
        try: s.reconfigure(encoding="utf-8", errors="replace")
        except Exception: pass


utf8_console()

HERE = Path(__file__).resolve().parent
CATALOG_PATH = HERE.parent / "connectors" / "catalog.json"
SETUP = "Setup"
PLAN_REL = Path(SETUP) / "connection-plan.md"
STATUSES = ["to-do", "connected", "needs-admin", "failed", "using-fallback", "skipped"]
SURFACES = ["cowork", "desktop", "web", "code"]
ROUTE_ORDER = {"one-click": 0, "add-by-url": 1, "api-key": 2, "admin-project": 3, "none": 4}
ROUTE_SHORT = {"one-click": "One click", "add-by-url": "Add by web address", "api-key": "Needs a key",
               "admin-project": "IT sets it up", "none": "No connector yet"}
CATEGORY_ORDER = ["suite", "chat", "meetings", "files", "tracker", "docs", "work-management", "crm", "support",
                  "sales", "design", "analytics", "dev", "data", "marketing", "hr", "finance", "automation"]
SURFACE_NAME = {"cowork": "Cowork", "desktop": "Claude Desktop", "web": "claude.ai", "code": "Claude Code"}


# ---------------------------------------------------------------- catalog


def write_lf(path, text: str) -> None:
    """Write UTF-8 text with Unix line endings on every platform, so files match across Mac, Windows, and Linux."""
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)

def load_catalog(path: Path = CATALOG_PATH) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.exit(f"Catalog not found at {path}. Reinstall the skill; connectors/catalog.json ships with it.")


def by_id(cat: dict) -> dict:
    return {c["id"]: c for c in cat["connectors"]}


def norm(text: str) -> str:
    text = text.lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9.;+ ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


SECRET_PATTERNS = [
    (r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{8,}", "Bearer [REDACTED]"),
    (r"(?i)\b(code|token|access_token|refresh_token|id_token|password|passwd|pwd|secret|client_secret|api[_-]?key|session|sig|signature)=[^\s&\"']+", r"\1=[REDACTED]"),
    (r"(?i)\bbasic\s+[A-Za-z0-9+/=]{8,}", "Basic [REDACTED]"),
    (r"\beyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}", "[REDACTED-JWT]"),
    (r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}|\bgithub_pat_[A-Za-z0-9_]{20,}", "[REDACTED-TOKEN]"),
    (r"\bxox[abposr]-[A-Za-z0-9-]{10,}|\bxapp-[A-Za-z0-9-]{10,}", "[REDACTED-TOKEN]"),
    (r"\b(AKIA|ASIA)[A-Z0-9]{16}\b", "[REDACTED-KEY]"),
    (r"\bsk-[A-Za-z0-9_-]{16,}", "[REDACTED-KEY]"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?(-----END [A-Z ]*PRIVATE KEY-----|$)", "[REDACTED-PRIVATE-KEY]"),
    (r"\b[A-Za-z0-9+/_-]{40,}={0,2}", "[REDACTED-LONG-STRING]"),
]


KEY_VALUE = re.compile(r"""(?i)(["']?)([\w-]*(?:password|passwd|secret|api[_ -]?key|token))\1(\s*[:=]\s*)(["']?)([^\s"',&}]+)\4""")


def redact(text: str) -> str:
    """Strip anything that looks like a secret before it is written to a file or an email."""
    out = text or ""
    for pat, repl in SECRET_PATTERNS:
        out = re.sub(pat, repl, out, flags=re.S)

    def kv(m):
        if m.group(2).lower().startswith("invalid"):
            return m.group(0)
        return f"{m.group(1)}{m.group(2)}{m.group(1)}{m.group(3)}[REDACTED]"
    out = KEY_VALUE.sub(kv, out)
    return " ".join(out.split())


GROUP_ALIASES = {
    "google workspace": ["gmail", "google-calendar", "google-drive"],
    "g suite": ["gmail", "google-calendar", "google-drive"],
    "gsuite": ["gmail", "google-calendar", "google-drive"],
    "google apps": ["gmail", "google-calendar", "google-drive"],
}
NOTHING = {"none", "n a", "na", "nothing", "no", "nope", "not really", "nothing else", "that s it", "thats it", "none of these",
           "other", "others", "something else", "other tools", "not sure", "dunno", "i don t know", "idk", "we don t use anything",
           "nothing really", "none really", "not much", "nothing else really", "no others", "that s all", "thats all"}
FILLER = {"we", "use", "uses", "our", "my", "the", "a", "an", "in", "for", "cloud", "too", "also", "mostly", "sometimes", "i",
          "team", "teams s", "company", "it", "s", "and", "app", "version", "only", "mainly", "plus", "with"}
# Tool names that are also everyday words: only trust them in short answers.
AMBIGUOUS = {"make", "word", "close", "monday", "zoom", "loop", "box", "hex", "clay", "guru", "office", "drive", "sentry",
             "stripe", "lucid", "planner", "excel", "teams", "linear", "notion", "slack", "make com", "outreach", "apollo", "intercom"}


def build_index(cat: dict, labels: bool = True):
    """Map normalized names, aliases, ids, and (optionally) picker labels to tool ids or follow-ups."""
    idx: dict[str, dict] = {k: {"ids": list(v)} for k, v in GROUP_ALIASES.items()}
    for c in cat["connectors"]:
        for key in [c["id"], c["name"], *c.get("aliases", [])]:
            idx.setdefault(norm(key), {"ids": [c["id"]]})
        short = norm(re.sub(r"\(.*?\)", "", c["name"]))
        idx.setdefault(short, {"ids": [c["id"]]})
    if labels:
        for s in cat.get("screens", []):
            for q in s["questions"]:
                for o in q["options"]:
                    entry = {"ids": list(o.get("ids", []))}
                    if o.get("followup"):
                        entry["followup"] = o["followup"]
                    idx[norm(o["label"])] = entry
    return idx


def split_answers(values) -> list[str]:
    out = []
    for v in values:
        for part in re.split(r"[,\n;/]|\s\+\s", v or ""):
            part = part.strip()
            if part:
                out.append(part)
    return out


def match_answers(cat: dict, values) -> dict:
    idx = build_index(cat)
    tool_idx = build_index(cat, labels=False)
    names = list(tool_idx.keys())  # fuzzy matching only against real tool names
    result = {"ids": [], "followups": [], "unknown": [], "no_tool": []}

    def add(hit, raw):
        if hit.get("followup"):
            result["followups"].append({"answer": raw, "ask": hit["followup"]})
        if not hit["ids"] and not hit.get("followup"):
            result["no_tool"].append(raw)
        for i in hit["ids"]:
            if i not in result["ids"]:
                result["ids"].append(i)

    # Picker labels can contain "/" or ",", so try each whole answer first.
    pending = []
    for v in values:
        if norm(v or "") in NOTHING:
            continue
        hit = idx.get(norm(v or ""))
        if hit is not None and (v or "").strip():
            add(hit, v.strip())
        else:
            pending.append(v)
    for raw in split_answers(pending):
        key = norm(re.sub(r"\(.*?\)", " ", raw)) or norm(raw)
        if key in NOTHING:
            continue
        hit = idx.get(key) or idx.get(norm(raw))
        if hit is None:
            pieces = [p.strip() for p in re.split(r"\band\b|\bor\b|\bplus\b|&", key) if p.strip()]
            if len(pieces) > 1:
                sub = match_answers(cat, pieces)
                for k in result:
                    result[k].extend(x for x in sub[k] if x not in result[k])
                continue
        if hit is None and " " in key:
            squashed = key.replace(" ", "")  # "sales force" is Salesforce, "click up" is ClickUp
            hit = tool_idx.get(squashed)
        if hit is None and len(key) >= 4 and " " not in key:
            targets = [n for n in names if n not in AMBIGUOUS and " " not in n]
            close = difflib.get_close_matches(key, targets, n=1, cutoff=0.75)
            if not close:
                # Everyday-word names only match close typos of longer names: "slakc" yes, "words" no.
                risky = [n for n in names if n in AMBIGUOUS and len(n) >= 5 and n[0] == key[0]]
                close = difflib.get_close_matches(key, risky, n=1, cutoff=0.8)
            if close:
                hit = tool_idx[close[0]]
        if hit is None:
            # Whole-word scan: "we use jira cloud" finds jira.
            words = f" {key} "
            content = [w for w in key.split() if w not in FILLER]
            found = [n for n in sorted(names, key=len, reverse=True) if len(n) >= 3 and f" {n} " in words
                     and not (n in AMBIGUOUS and len(content) > 1)]
            if found:
                ids = []
                for n in found:
                    for i in tool_idx[n]["ids"]:
                        if i not in ids:
                            ids.append(i)
                hit = {"ids": ids}
        if hit is None:
            result["unknown"].append(raw)
            continue
        add(hit, raw)
    return result


def resolve_tools(cat: dict, tools_arg: str | None, keep_unknown: bool = False) -> list[str]:
    """Catalog ids for the tools named. With keep_unknown, names the catalog doesn't know come back as
    'other:<name>' so the plan and the IT email still carry them."""
    if not tools_arg:
        return []
    m = match_answers(cat, split_answers([tools_arg]))
    if m["unknown"] and not keep_unknown:
        print("Not in the catalog: " + ", ".join(m["unknown"]), file=sys.stderr)
    others = [f"other:{re.sub(r'^(other:)+', '', u.strip())[:60]}" for u in m["unknown"]] if keep_unknown else []
    return m["ids"] + [o for o in others if o != "other:"]


def needs_admin_once(c: dict) -> bool:
    return bool(re.search(r"\b(admin|approv|consent|enable|turn(s)? it on|owner)", c.get("admin", ""), re.I))


def other_tool(tid: str) -> dict:
    """A stand-in catalog entry for a tool the catalog doesn't know."""
    name = tid.split(":", 1)[1]
    return {"id": tid, "name": name, "aliases": [], "category": "other", "provides": [], "route": "none",
            "bundled": False, "admin": "", "readonly": "",
            "fallback": "Save a report or export into 1-Inbox, or paste what you need.",
            "notes": "Not in this kit's catalog. Check Claude's connector directory first (Customize, then Connectors); new connectors appear often.",
            "docs": ""}


def tools_with_others(cat: dict, ids) -> dict:
    tools = dict(by_id(cat))
    for i in ids:
        if i.startswith("other:") and i not in tools:
            tools[i] = other_tool(i)
    return tools


def sort_key(c: dict):
    cat_rank = CATEGORY_ORDER.index(c["category"]) if c["category"] in CATEGORY_ORDER else 99
    return (ROUTE_ORDER.get(c["route"], 9), 0 if c.get("bundled") else 1, cat_rank, c["name"].lower())


def mcp_url(c: dict, readonly: bool = True) -> str:
    if readonly and c.get("readonly_url"):
        return c["readonly_url"]
    return (c.get("mcp") or {}).get("url", "")


# ---------------------------------------------------------------- list / screens / match

def cmd_list(args) -> int:
    cat = load_catalog()
    rows = [c for c in cat["connectors"] if not args.category or c["category"] == args.category]
    rows.sort(key=lambda c: (c["category"], c["name"].lower()))
    if args.json:
        print(json.dumps(rows, indent=1, ensure_ascii=False))
        return 0
    cur = None
    for c in rows:
        if c["category"] != cur:
            cur = c["category"]
            print(f"\n{cur}")
        flag = " (comes with the plugin)" if c.get("bundled") else ""
        print(f"  {c['id']:<16} {c['name']}: {ROUTE_SHORT[c['route']]}{flag}")
    print(f"\n{len(rows)} tools. Routes: " + "; ".join(f"{ROUTE_SHORT[k]} = {v}" for k, v in cat["routes"].items()))
    return 0


def screens_for(cat: dict, role: str | None, only: str | None = None):
    out = []
    for s in cat["screens"]:
        if only:
            if s["id"] == only or (only == "role" and role and norm(s["when"]) == norm(role)):
                out.append(s)
        elif s["when"] == "always" or (role and norm(s["when"]) == norm(role)):
            out.append(s)
    return out


def cmd_screens(args) -> int:
    cat = load_catalog()
    screens = screens_for(cat, args.role, args.screen)
    roles = [s["when"] for s in cat["screens"] if s["when"] != "always"]
    if args.screen and not screens:
        if args.screen == "role":
            sys.exit(f"No role screen for '{args.role or ''}'. Roles: {'; '.join(roles)}. If they typed their own role, ask in plain words which other tools they use every week.")
        ids = [s["id"] for s in cat["screens"] if s["when"] == "always"]
        sys.exit(f"No screen '{args.screen}'. Screens: {', '.join(ids)}, or 'role' with --role.")
    if args.role and not args.screen and not any(s["when"] != "always" for s in screens):
        print(f"No role screen for '{args.role}'. Roles: {', '.join(roles)}. Showing the shared screens only.", file=sys.stderr)
    if args.json:
        payload = []
        for s in screens:
            payload.append({"id": s["id"], "title": s["title"], "questions": [
                {"question": q["question"], "header": q["header"], "multiSelect": q["multiSelect"],
                 "options": [{"label": o["label"], "description": o["description"]} for o in q["options"]]}
                for q in s["questions"]]})
        print(json.dumps({"screens": payload, "role_screens": roles}, indent=1, ensure_ascii=False))
        return 0
    for n, s in enumerate(screens, 1):
        print(f"Screen {n}: {s['title']}")
        for q in s["questions"]:
            kind = "pick all that apply" if q["multiSelect"] else "pick one"
            print(f"\n  {q['question']} ({kind})")
            for i, o in enumerate(q["options"], 1):
                print(f"    {i}. {o['label']}: {o['description']}")
            print(f"    {len(q['options']) + 1}. Something else (type it)")
        print()
    if not args.role and not args.screen:
        print("Role screens (show the one matching the Role answer): " + "; ".join(roles))
    if args.text:
        print("\nOn a surface without a picker, paste each question as a numbered list and let the person reply with numbers, like '1, 3'.")
    return 0


def cmd_match(args) -> int:
    cat = load_catalog()
    m = match_answers(cat, args.answers)
    if args.json:
        print(json.dumps(m, indent=1, ensure_ascii=False))
        return 0
    tools = by_id(cat)
    if m["ids"]:
        print("Tools: " + ", ".join(f"{tools[i]['name']} [{i}]" for i in m["ids"]))
        print("Use: --tools " + ",".join(m["ids"]))
    for f in m["followups"]:
        print(f"Ask next: {f['ask']}")
    if m["no_tool"]:
        print("No connector needed: " + ", ".join(m["no_tool"]))
    if m["unknown"]:
        print("Not in the catalog: " + ", ".join(m["unknown"]) +
              ". Check Claude's connector directory for it; if it is not there, use exports or the browser.")
    return 0


# ---------------------------------------------------------------- plan / mark

def steps_for(c: dict, surface: str) -> list[str]:
    name = c["name"].split(" (")[0]
    url = mcp_url(c)
    r = c["route"]
    if r in ("admin-project", "api-key", "none"):
        if r == "none":
            if c["id"].startswith("other:"):
                return [f"Look for {name} in Claude's connector directory (Customize, then Connectors). If it's there, connect it like any other tool.",
                        "If it isn't, use the fallback below; it still feeds your second brain."]
            return [f"There is no connector for {name} yet. Use the fallback below; it still works with the second brain."]
        steps = ["Ask me for the IT email. I'll write it with exactly what the admin needs to do, and you send it."]
        if r == "api-key":
            steps.append("Once there's a key, an admin or your Claude Owner adds it. Never paste a key into the chat.")
        steps.append("Use the fallback below until it is set up.")
        return steps
    if surface == "code":
        if url and c.get("claude_code") != "account":
            pre = [f"If you installed the Unpaid Intern plugin, {name} is already listed: type /mcp, pick it, and sign in."] if c.get("bundled") else []
            return pre + ["Otherwise, ask me to add it to this folder's Claude Code settings (read-only where possible).",
                          "Restart Claude Code, type /mcp, pick " + name + ", and sign in with your work account."]
        return [f"Connect {name} on claude.ai first (Customize, then Connectors), signed in to the same Claude account you use in Claude Code.",
                "Back in Claude Code, type /mcp. Connectors from your Claude account show up there."]
    steps = []
    if c.get("code_only"):
        return [f"{name} isn't a one-click connector in the Claude apps yet. Check Claude's connector directory (Customize, then Connectors) in case it has arrived.",
                "If it isn't there, use the fallback below. It still feeds your second brain."]
    if c.get("bundled") and surface in ("cowork", "desktop"):
        steps.append(f"If you installed the Unpaid Intern plugin, {name} is already listed under the plugin's connectors. Click it and sign in, then skip to the last step.")
    if r == "one-click":
        steps += ["Open Customize, then Connectors (in older versions this is under Settings).",
                  f"Find {name}. Use Browse or the search box if it is not on the first screen.",
                  "Click Connect and sign in with your work account, not a personal one."]
    else:  # add-by-url
        steps += ["Open Customize, then Connectors (in older versions, Settings), and choose Add custom connector.",
                  f"Name: {name}. Address: {url or '(your company-specific address; ask the admin)'}",
                  "Click Add, then Connect, and sign in with your work account.",
                  "On company Claude plans, only an Owner can add custom connectors. If you can't, send the Owner the name and address above."]
    steps.append("If you see Request instead of Connect, your company's Claude Owner has to turn it on. Click Request; it is not something you did wrong.")
    steps.append("Open the connector's tool settings and set anything that sends, posts, deletes, or shares to need approval, or turn it off.")
    return steps


def parse_plan(path: Path):
    statuses, log = {}, []
    if not path.exists():
        return statuses, log
    in_log = False
    for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        if line.strip().lower() == "## log":
            in_log = True
            continue
        if in_log:
            if line.startswith("## "):
                in_log = False
            elif line.startswith("- "):
                log.append(line)
            continue
        if line.startswith("|") and not line.startswith("|---"):
            cells = [x.strip() for x in line.strip().strip("|").split("|")]
            if len(cells) >= 5 and cells[2] and cells[2] != "Id":
                statuses[cells[2].strip("`")] = cells[4]
    return statuses, log


def render_plan(cat: dict, ids: list[str], surface: str, statuses: dict, log: list[str], today: str) -> str:
    tools = tools_with_others(cat, ids)
    chosen = sorted((tools[i] for i in ids if i in tools), key=sort_key)
    lines = ["# My connection plan", "",
             f"Made on {today} for {SURFACE_NAME[surface]}. Easiest first. Connect them one at a time; stop whenever you like and pick it up later.",
             "Adding tools later keeps every status already set here.", "",
             "Status: to-do, connected, needs-admin, failed, using-fallback, or skipped.", "",
             "| Order | Tool | Id | How it connects | Status |", "|---|---|---|---|---|"]
    for n, c in enumerate(chosen, 1):
        short = "Claude Code only" if c.get("code_only") and surface != "code" else ROUTE_SHORT[c["route"]]
        if c["id"].startswith("other:"):
            short = "Check Claude's directory"
        elif c["route"] == "one-click" and needs_admin_once(c):
            short = "One click, often after an admin approves it once"
        lines.append(f"| {n} | {c['name']} | `{c['id']}` | {short} | {statuses.get(c['id'], 'to-do')} |")
    lines += ["", "## Steps", ""]
    for n, c in enumerate(chosen, 1):
        lines.append(f"### {n}. {c['name']}")
        lines.append("")
        how = ("Only in Claude Code for now. Elsewhere, use the fallback." if c.get("code_only") and surface != "code"
               else "Not in this kit's catalog yet." if c["id"].startswith("other:") else cat["routes"][c["route"]])
        lines.append(f"How it connects: {how}")
        lines.append("")
        for i, s in enumerate(steps_for(c, surface), 1):
            lines.append(f"{i}. {s}")
        lines.append("")
        if c.get("admin"):
            lines.append(f"- What your admin does (for IT, if needed): {c['admin']}")
        if c.get("readonly"):
            lines.append(f"- Keeping it read-only: {c['readonly']}")
        if c.get("fallback"):
            lines.append(f"- Until it works: {c['fallback']}")
        if c.get("notes"):
            lines.append(f"- Good to know: {c['notes']}")
        lines.append("- If it fails: copy the exact error message (or take a screenshot) and say \"it didn't work\". I'll tell you what it means and who can fix it.")
        if c.get("docs"):
            lines.append(f"- Vendor guide: {c['docs']}")
        lines.append("")
    lines += ["## Log", ""]
    lines += log if log else [f"- {today} plan created"]
    lines.append("")
    return "\n".join(lines)


def plan_surface(path: Path) -> str | None:
    if not path.exists():
        return None
    m = re.search(r"for (Cowork|Claude Desktop|claude\.ai|Claude Code)\.", path.read_text(encoding="utf-8-sig", errors="replace"))
    return {v: k for k, v in SURFACE_NAME.items()}[m.group(1)] if m else None


def workspace(arg: str) -> Path:
    ws = Path(arg).expanduser().resolve()
    if not (ws / SETUP).is_dir():
        sys.exit(f"No workspace found at {ws} (no Setup folder). Run 'brain.py init <folder>' first, or pass --workspace <folder>.")
    return ws


def today_str(arg: str | None) -> str:
    if arg:
        try:
            return dt.date.fromisoformat(arg).isoformat()
        except ValueError:
            sys.exit(f"--today must look like 2026-10-04, got '{arg}'.")
    return dt.date.today().isoformat()


def cmd_plan(args) -> int:
    cat = load_catalog()
    ws = workspace(args.workspace)
    path = ws / PLAN_REL
    statuses, log = parse_plan(path)
    surface = args.surface or plan_surface(path) or "cowork"
    ids = list(statuses.keys())
    for i in resolve_tools(cat, args.tools, keep_unknown=True):
        if i not in ids:
            ids.append(i)
    if not ids:
        sys.exit("No tools given. Pass --tools with ids, names, or picker answers, for example --tools 'Outlook (Microsoft 365),Slack,Jira'.")
    text = render_plan(cat, ids, surface, statuses, log, today_str(args.today))
    if args.print:
        print(text)
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    write_lf(path, text)
    tools = tools_with_others(cat, ids)
    groups: dict[str, list[str]] = {}
    for i in ids:
        if i in tools:
            c = tools[i]
            key = c["route"]
            if key == "one-click" and needs_admin_once(c):
                key = "one-click-admin"
            if i.startswith("other:"):
                key = "other"
            groups.setdefault(key, []).append(c["name"].split(" (")[0])
    print(f"Wrote {PLAN_REL}.")
    labels = {"one-click": "Ready to connect now",
              "one-click-admin": "Connect now, though many companies have an admin approve it once first",
              "add-by-url": "Add by web address", "api-key": "Needs a key from an admin",
              "admin-project": "Needs IT to set it up first", "none": "No connector yet (we'll use exports or the browser)",
              "other": "Not in this kit's catalog (we'll check Claude's directory, then fall back to exports)"}
    order = ["one-click", "one-click-admin", "add-by-url", "api-key", "admin-project", "none", "other"]
    for r in sorted(groups, key=order.index):
        print(f"{labels[r]}: {', '.join(groups[r])}")
    return 0


def cmd_mark(args) -> int:
    cat = load_catalog()
    ws = workspace(args.workspace)
    path = ws / PLAN_REL
    if not path.exists():
        sys.exit("No connection plan yet. Run 'connect.py plan --tools ...' first.")
    status = args.status.lower()
    if status not in STATUSES:
        sys.exit(f"Status must be one of: {', '.join(STATUSES)}.")
    statuses, log = parse_plan(path)
    ids = [args.tool] if args.tool in statuses else resolve_tools(cat, args.tool)
    if len(ids) != 1:
        sys.exit(f"Could not tell which tool '{args.tool}' means. Use its id from the plan table.")
    tid = ids[0]
    if tid not in statuses:
        sys.exit(f"'{tid}' is not in the plan. Add it with 'connect.py plan --tools {tid}'.")
    statuses[tid] = status
    day = today_str(args.today)
    clean = redact(args.note).replace("|", "/") if args.note else ""
    note = f": {clean}" if clean else ""
    log.append(f"- {day} {tid} {status}{note}")
    surface = plan_surface(path) or "cowork"
    made = re.search(r"^Made on (\d{4}-\d{2}-\d{2})", path.read_text(encoding="utf-8-sig", errors="replace"), flags=re.M)
    write_lf(path, render_plan(cat, list(statuses.keys()), surface, statuses, log, made.group(1) if made else day))
    done = sum(1 for s in statuses.values() if s in ("connected", "using-fallback", "skipped"))
    print(f"{tid}: {status}. {done} of {len(statuses)} settled.")
    nxt = [t for t, s in statuses.items() if s == "to-do"]
    if nxt:
        print(f"Next up: {by_id(cat)[nxt[0]]['name']}" if nxt[0] in by_id(cat) else f"Next up: {nxt[0]}")
    return 0


# ---------------------------------------------------------------- tour

TOUR_MARK = "<!-- made by connect.py tour; re-run it to refresh -->"


def read_help_first(ws: Path | None) -> list[str]:
    if not ws:
        return []
    p = ws / SETUP / "preferences.md"
    if not p.exists():
        return []
    m = re.search(r"^- help first:\s*(.+)$", p.read_text(encoding="utf-8-sig", errors="replace"), flags=re.M)
    if not m or m.group(1).strip().startswith("<"):
        return []
    return split_help(m.group(1), load_catalog())


def split_help(text: str, cat: dict) -> list[str]:
    """Split a help-first answer into picker labels. Some labels contain commas ("Yes, still ramping up"),
    so known labels are lifted out whole before splitting what is left on commas."""
    labels = sorted({o["label"] for s in cat["screens"] for q in s["questions"]
                     if q["header"] in ("Help with", "New here?") for o in q["options"]}, key=len, reverse=True)
    found, rest = [], text
    for lab in labels:
        i = rest.lower().find(lab.lower())
        if i >= 0:
            found.append(lab)
            rest = rest[:i] + "," + rest[i + len(lab):]
    found += [x.strip() for x in re.split(r"[,;]", rest) if x.strip()]
    return found


def build_tour(cat: dict, connected: list[str], pending: list[str], help_first: list[str]):
    tools = by_id(cat)
    kinds = cat["kinds"]

    def sources(ids, uses):
        hits = []
        for i in ids:
            c = tools.get(i)
            if not c:
                continue
            shared = [k for k in uses if k in c.get("provides", [])]
            if shared:
                hits.append((c["name"].split(" (")[0], shared))
        return hits

    hf = {norm(h) for h in help_first}
    rows = []
    for cmd in cat["commands"]:
        live = sources(connected, cmd["uses"])
        soon = sources(pending, cmd["uses"])
        wanted = bool(hf & {norm(h) for h in cmd["helps"]})
        score = (0 if wanted else 1, 0 if cmd.get("core") else 1, 0 if cmd.get("starter") else 1, -len(live))
        rows.append(dict(cmd=cmd, live=live, soon=soon, wanted=wanted, score=score))
    # "Start with these" draws only from the core eight, so it and "the rest of the core eight" add up to
    # exactly SKILL.md's core table. A wanted extra (say /slots for meeting help) waits with the others.
    core = [r for r in rows if r["cmd"].get("core")]
    start = sorted([r for r in core if r["wanted"] or (not hf and r["cmd"].get("starter"))], key=lambda r: r["score"])[:4]
    if len(start) < 4:
        extra = sorted([r for r in core if r not in start and r["cmd"].get("starter")], key=lambda r: r["score"])
        start += extra[: 4 - len(start)]

    def reads(r):
        if r["live"]:
            parts = []
            for name, shared in r["live"]:
                parts.append(f"{name} ({', '.join(kinds[k].replace('your ', '') for k in shared)})")
            return "Reads live: " + "; ".join(parts) + "."
        if not r["cmd"]["uses"]:
            return "Works from your own records. Nothing to connect."
        return (r["cmd"].get("without") or "Works today from pasted text and dropped files.")

    def better(r):
        if r["soon"] and not r["live"]:
            return "Gets better once " + " and ".join(n for n, _ in r["soon"]) + " connect" + ("s" if len(r["soon"]) == 1 else "") + "."
        return ""
    return start, rows, reads, better


def cmd_tour(args) -> int:
    cat = load_catalog()
    ws = None
    p = Path(args.workspace).expanduser().resolve()
    if (p / SETUP).is_dir():
        ws = p
    connected = resolve_tools(cat, args.connected) if args.connected else []
    pending: list[str] = []
    if ws and (ws / PLAN_REL).exists():
        st, _ = parse_plan(ws / PLAN_REL)
        if not args.connected:
            connected = [t for t, s in st.items() if s == "connected"]
        pending = [t for t, s in st.items() if s in ("to-do", "needs-admin", "failed")]
    help_first = split_help(args.help_first or "", cat) or read_help_first(ws)
    start, rows, reads, better = build_tour(cat, connected, pending, help_first)

    if args.json:
        print(json.dumps({"question": "Which one do you want to try first?", "header": "Try first", "multiSelect": False,
                          "options": [{"label": r["cmd"]["command"], "description": r["cmd"]["what"]} for r in start],
                          "try_it": {r["cmd"]["command"]: r["cmd"]["try_it"] for r in start}}, indent=1))
        return 0

    out = [TOUR_MARK, "# What you just unlocked", ""]
    if connected:
        names = [by_id(cat)[i]["name"].split(" (")[0] for i in connected if i in by_id(cat)]
        out.append("Connected: " + ", ".join(names) + ".")
    else:
        out.append("Nothing connected yet. Everything below still works from pasted text and dropped files.")
    out += ["", "## Start with these", ""]
    for r in start:
        c = r["cmd"]
        out.append(f"**{c['command']}**: {c['what']}")
        out.append(f"- {reads(r)}")
        b = better(r)
        if b:
            out.append(f"- {b}")
        out.append(f"- Try it: `{c['try_it']}`")
        out.append("")
    core_rest = [r for r in rows if r not in start and r["cmd"].get("core")]
    if core_rest:
        out += ["## The rest of the core eight", ""]
        for r in core_rest:
            tail = " (live)" if r["live"] else ""
            out.append(f"- **{r['cmd']['command']}**{tail}: {r['cmd']['what']}")
        out.append("")
    extra = [r["cmd"]["command"] for r in rows if r not in start and not r["cmd"].get("core")]
    out += [f"There are {len(extra)} more for later. When you're ready, ask \"what else can you do?\"", ""]
    out += ["## Good to know", "",
            "- You never have to remember these. Say what you want in plain words and the agent picks the command.",
            "- Nothing gets sent, posted, or deleted without you seeing it first.",
            "- To add a tool, ask me to connect it. This page refreshes when something new connects.", ""]
    text = "\n".join(out)
    if args.write:
        if not ws:
            sys.exit("--write needs --workspace pointing at a workspace.")
        dest = ws / SETUP / "my-commands.md"
        if dest.exists() and not dest.read_text(encoding="utf-8-sig", errors="replace").startswith(TOUR_MARK):
            dest = ws / SETUP / "my-commands-new.md"
        write_lf(dest, text)
        print(f"Wrote {dest.relative_to(ws)}.")
        return 0
    print(text)
    return 0


# ---------------------------------------------------------------- diagnose

DIAGNOSES = [
    dict(id="atlassian-admin", strong=[r"site admin (must|needs to|has to) (authori[sz]e|approve)", r"contact your site admin"], pats=[r"authori[sz]e this app.*admin", r"admin (must|needs to) authori[sz]e", r"\bsite admin"],
         title="Your Atlassian site admin has to approve Claude once",
         means="Jira and Confluence ask a site admin to approve a new app the first time anyone in the company connects it.",
         fix="Send the IT request to whoever administers Jira or Confluence. After one approval, everyone can connect.",
         who="Your Jira or Confluence site admin", it=True),
    dict(id="microsoft-consent", strong=[r"AADSTS65001", r"AADSTS90094", r"AADSTS900941", r"AADSTS700016"], pats=[r"need admin approval", r"admin(istrator)? approval required", r"requires? admin(istrator)? consent", r"admin consent", r"application .{0,80}not found in the directory"],
         title="A Microsoft admin has to approve Claude for your company",
         means="Your company requires an administrator to approve apps that read Outlook, Teams, or SharePoint. It is a one-time, company-wide step.",
         fix="Send the IT request to your Microsoft 365 admin. They grant consent once and then everyone can connect.",
         who="A Microsoft 365 Global Admin (sometimes called the tenant admin)", it=True),
    dict(id="microsoft-conditional", strong=[r"AADSTS53000", r"AADSTS53003", r"AADSTS530003", r"AADSTS50158"], pats=[r"conditional access", r"device (is not|must be) (compliant|managed)"],
         title="Your company only allows sign-ins from approved devices or places",
         means="Microsoft sign-in rules (Conditional Access) blocked it. Connectors in Claude sign in from Anthropic's cloud, which those rules may not allow.",
         fix="Send the IT request and include the exact error code. IT decides whether to allow it. Use the fallback meanwhile.",
         who="Your IT or identity team", it=True),
    dict(id="not-assigned", strong=[r"AADSTS50105"], pats=[r"not assigned to (a role|the application|this app)", r"is not assigned", r"not (been )?granted access to (this|the) app"],
         title="Your company limits this app to certain people",
         means="The app is approved, but only for a list of people or groups, and you are not on it yet.",
         fix="Send the IT request and ask to be added to the app's assigned users or group.",
         who="Your Microsoft 365 or identity admin", it=True),
    dict(id="mfa", strong=[r"AADSTS50076", r"AADSTS50079"], pats=[r"multi-?factor", r"\bMFA\b", r"additional verification", r"two-?step verification required"],
         title="Your company wants an extra verification step",
         means="The sign-in needs a second check, like an authenticator app prompt.",
         fix="Connect again and finish every prompt on the sign-in page, including the authenticator. Never paste a code into the chat; it goes on the sign-in page only.",
         who="Nobody; you can fix this one", it=False),
    dict(id="personal-account", strong=[r"AADSTS50020", r"AADSTS500200"], pats=[r"personal microsoft account", r"does not exist in tenant", r"@(outlook|hotmail|live)\.com", r"\bMSA\b"],
         title="That was a personal account, not your work one",
         means="The Microsoft 365 connector only works with work or school accounts.",
         fix="Disconnect, connect again, and pick your work account (you@yourcompany.com) when it asks.",
         who="Nobody; you can fix this one", it=False),
    dict(id="app-blocked", strong=[r"admin_policy_enforced", r"org_internal", r"error 403: access_denied"], pats=[r"access_denied", r"hasn'?t given you access", r"admin must enable", r"must be enabled by (an|your) admin", r"has not enabled", r"not (been )?enabled (for|in|by) (your|this) (org|organi[sz]ation|company)", r"access blocked", r"has not been approved by your (organi[sz]ation|admin)", r"blocked by your (admin|administrator|organi[sz]ation)", r"app (is )?blocked", r"not (yet )?approved (for|in|by) (this|your) (workspace|organi[sz]ation)", r"restricted (third[- ]party )?integrations", r"integrations? (are|is) restricted", r"admin (has )?restricted"],
         title="Your company has not approved this app yet",
         means="An admin controls which apps may sign in with your work account. In Google Workspace this is the trusted apps list; in Slack it is app approval.",
         fix="Send the IT request. Mention the exact message you saw.",
         who="The admin for that tool", it=True),
    dict(id="needs-approval", pats=[r"requires? (admin )?approval", r"approval required", r"request to install", r"install request", r"request sent", r"(will )?need(s)? to approve", r"pending approval", r"approval (is )?pending"],
         title="An admin has to approve the app first",
         means="The tool lets people request apps, and an admin approves them.",
         fix="Submit the request if the tool offers a button, then send the IT request so the admin knows what it is for.",
         who="The admin for that tool", it=True),
    dict(id="claude-owner", strong=[r"(admin|administrator|owner)('s)? (has )?(disabled|turned off|restricted) (this |custom )?connectors?", r"(custom )?connectors (are|have been) (disabled|turned off)"], pats=[r"gr[ae]yed out", r"contact your (owner|admin(istrator)?)", r"only (owners|admins|administrators) can", r"request (access|this connector)", r"not enabled for your organi[sz]ation", r"disabled by your organi[sz]ation", r"organi[sz]ation has (disabled|restricted)", r"\bRequest\b button", r"organi[sz]ation (does ?n[o']t|doesn't|does not) allow", r"not allowed (by|in) your organi[sz]ation", r"(blocked|restricted) by (your )?(organi[sz]ation|company|admin)"],
         title="Your company's Claude Owner has to turn this on",
         means="On company Claude plans, the Owner decides which connectors people can use, and only Owners add custom ones.",
         fix="Click Request if you see it, or send the Owner the tool's name. The IT request covers this too.",
         who="Whoever runs your company's Claude account (the Owner)", it=True),
    dict(id="blocked-network", weak=[r"\b403\b", r"forbidden"], pats=[r"ip (address )?(is )?not allowed", r"ip allow ?list", r"ip restriction", r"not allowed from (this|your) (ip|network|location)", r"network polic", r"allow ?list", r"not on the allow"],
         title="The tool refused the connection",
         means="Either your account doesn't have permission for this, or the tool only accepts traffic from your office network or VPN. Connectors in claude.ai, Claude Desktop, and Cowork come from Anthropic's cloud, not your computer, so being on VPN does not help them.",
         fix="Ask the admin to allow Claude's connector, or use the fallback. In Claude Code the connection comes from your own computer, so turning on VPN can fix it there.",
         who="The admin for that tool, or your network team", it=True),
    dict(id="tls-inspection", pats=[r"self[- ]signed", r"SELF_SIGNED_CERT_IN_CHAIN", r"UNABLE_TO_GET_ISSUER_CERT", r"unable to verify the first certificate", r"CERTIFICATE_VERIFY_FAILED", r"certificate verify failed", r"unable to get local issuer", r"\bx509\b", r"ERR_TLS", r"UnknownIssuer", r"invalid peer certificate"],
         title="Your company inspects secure traffic, and Claude Code or Codex doesn't trust it yet",
         means="Many companies check encrypted traffic with their own certificate. This only affects tools running on your computer, like Claude Code and Codex.",
         fix="Ask IT: \"My AI tool fails certificate checks behind our traffic inspection. Which root certificate file should I use?\" Then point NODE_EXTRA_CA_CERTS (Claude Code) or CODEX_CA_CERTIFICATE (Codex) at that file before starting it.",
         who="Your IT or network team", it=True),
    dict(id="proxy", pats=[r"\b407\b", r"proxy authentication", r"proxy error", r"tunneling socket", r"HTTPS?_PROXY"],
         title="Your company network needs a proxy setting",
         means="Traffic from your computer has to go through a company proxy. This affects Claude Code, not connectors in the Claude apps.",
         fix="Ask IT for the proxy address, then set HTTPS_PROXY to it before starting Claude Code.",
         who="Your IT or network team", it=True),
    dict(id="unreachable", weak=[r"timed? ?out"], pats=[r"ENOTFOUND", r"getaddrinfo", r"EAI_AGAIN", r"could not resolve", r"name or service not known", r"nodename nor servname", r"ETIMEDOUT", r"ECONNREFUSED", r"connection refused", r"network is unreachable", r"fetch failed", r"ECONNRESET", r"socket hang up", r"could ?n[o']t reach", r"unable to reach", r"(could not|couldn't|can't|cannot) be reached"],
         title="The connection didn't get through",
         means="Something between Claude and the tool stopped the connection: a firewall, a VPN requirement, or a short outage.",
         fix="Wait a minute and try again. If you use Claude Code, ask me to run a network check from your computer to see where it stops. If it keeps failing, use the fallback and send the IT request with the exact message.",
         who="Your IT or network team, if it keeps happening", it=False),
    dict(id="expired", weak=[r"\b401\b", r"unauthori[sz]ed"], pats=[r"invalid[_ ]token", r"token (has )?expired", r"expired (token|session)", r"session (has )?expired", r"re-?authenticat", r"sign in again", r"invalid_grant", r"refresh token"],
         title="Your sign-in expired",
         means="Connections sign you out after a while, or when a password or admin setting changes.",
         fix="Disconnect the connector and connect it again. If everyone at your company hit this on the same day, the admin may need to approve the app again.",
         who="You can: reconnect it. If it happens to everyone, the tool's admin", it=False),
    dict(id="rate-limit", pats=[r"\b429\b", r"rate[- ]?limit", r"too many requests", r"\bquota\b", r"usage limit", r"daily limit"],
         title="You hit the tool's usage limit",
         means="Some tools cap how many requests a connector can make per day, especially on lower plans or view-only seats.",
         fix="Wait and try later, and ask for fewer, bigger reads. If it happens daily, the tool's plan may be the limit.",
         who="Nobody, or the tool's admin about the plan", it=False),
    dict(id="oauth-client", strong=[r"redirect_uri", r"dynamic client registration", r"invalid_client", r"AADSTS50011"], pats=[r"unauthorized_client", r"client registration", r"registration (is )?not supported", r"client[_ ]id"],
         title="This tool won't let Claude register itself",
         means="Some tools (Slack, Asana, and Box among them) do not let apps sign up automatically, so adding them by web address, or from a plugin inside Claude Code, fails.",
         fix="Use the tool from Claude's connector directory instead of adding the address by hand. In Claude Code, connect it on claude.ai with the same account and it shows up in /mcp. In Codex, install the tool's plugin from Codex's own directory (/plugins) if it has one, otherwise use the fallback. If none of these works, an admin creates an app and shares a client ID (in Codex, pass it with `--oauth-client-id`, and give the admin the callback URL Codex prints).",
         who="Nobody if the directory has it; otherwise the tool's admin", it=False),
    dict(id="callback-port", pats=[r"EADDRINUSE", r"address already in use", r"port \d+ (is )?(in use|already)", r"callback (server|port)"],
         title="Another sign-in is already in progress",
         means="Claude Code opens a small sign-in helper on your computer, and something else is using it.",
         fix="Close other sign-in windows, restart Claude Code, and try again.",
         who="Nobody; you can fix this one", it=False),
    dict(id="region", pats=[r"wrong region", r"data residency", r"region mismatch", r"not found in (this|your) region", r"\beu\b (workspace|instance|endpoint|region)", r"use the eu"],
         title="Your company's account lives in a different region",
         means="Some tools keep EU or other regional accounts at a different web address.",
         fix="Use the regional connector or address. `connect.py list` notes regional addresses where they exist.",
         who="Nobody, or the tool's admin to confirm the region", it=False),
    dict(id="plan-gate", pats=[r"upgrade (your|to|the) (plan|account|subscription|workspace)", r"upgrade to (a |an )?(business|enterprise|pro|paid|premium|team|growth)", r"(not|n't) available (on|in|with) (your|this|the) (current )?([\w.-]+ )?plan", r"requires? (a |an )?(paid|business|enterprise|pro|growth) plan", r"plan (does not|doesn't) (include|support)", r"(not|n't) included in (your|this|the) (current )?([\w.-]+ )?plan", r"feature (is not|isn't|not) available"],
         title="Your plan for that tool doesn't include it",
         means="Some tools only offer connectors on higher plans.",
         fix="Use the fallback. If it matters, ask the tool's owner whether the company plan includes it.",
         who="Whoever owns that tool's subscription", it=False),
    dict(id="no-python", pats=[r"code execution", r"python3?: command not found", r"command not found: python", r"no module named", r"python (is )?not (available|found|installed)", r"python was not found", r"\bpy(thon3?)?'? is not recognized as"],
         title="Scripts can't run here",
         means="Code execution is off, or Python isn't installed under that name. The second brain still works; the scripts just do the date math and checks.",
         fix="Try `python`, then `py -3`, in place of `python3` (on Windows, `python3` is often a Microsoft Store shortcut). If none runs on your own computer, Python isn't installed there: carry on by hand, or ask IT for Python 3. In a web chat, turn on code execution in Claude's settings (an Owner does this on company plans).",
         who="IT, if Python isn't on your work computer; your Claude Owner, if code execution is off for everyone", it=False),
    dict(id="empty", pats=[r"no results", r"returned nothing", r"\b0 results", r"can'?t find (any|my)", r"cannot see", r"is empty"],
         title="It connected, but found nothing",
         means="Usually not an error: the connector sees only what you can see, in the region and workspace you signed in to.",
         fix="Open the tool in your browser and check you can see the item there. Then check you connected the right workspace or region.",
         who="Nobody, usually", it=False),
    dict(id="server-error", weak=[r"\b5\d\d\b"], pats=[r"internal server error", r"bad gateway", r"service unavailable", r"gateway time-?out", r"temporarily unavailable"],
         title="The tool itself is having trouble",
         means="The error came from the tool's side, not yours. These usually clear up on their own.",
         fix="Try again in a few minutes. If it lasts, check the tool's status page, and use the fallback meanwhile.",
         who="Nobody at your company; it's on the tool's side", it=False),
    dict(id="auth-failed", strong=[r"user (denied|cancel+ed|declined)", r"(denied|cancel+ed|declined) (the )?(authori[sz]ation|consent|request|sign[- ]?in)", r"authori[sz]ation (was )?(denied|cancel+ed)"], pats=[r"authori[sz]ation with the mcp server failed", r"authentication failed", r"sign[- ]?in failed", r"oauth (flow )?failed", r"could ?n[o']t complete (the )?(sign[- ]?in|authori[sz]ation)"],
         title="The sign-in didn't finish",
         means="Claude started the sign-in, but it didn't complete. Often a window was closed early, the wrong account was picked, or the sign-in page showed its own error.",
         fix="Disconnect and connect again, finish every screen, and pick your work account. If the sign-in page showed an error of its own, paste that one; it says more.",
         who="Nobody, usually", it=False),
    dict(id="wrong-address", weak=[r"\b404\b"], pats=[r"<html", r"<!doctype", r"unexpected token <", r"not valid json", r"text/html"],
         title="That address isn't a connector",
         means="The web address points to a normal web page, not the tool's connector.",
         fix="Remove it and add the tool from the connector directory, or use the address in `connect.py list`.",
         who="Nobody; you can fix this one", it=False),
    dict(id="generic", pats=[r"failed to connect", r"could ?n[o']t connect", r"connection failed", r"error connecting", r"server disconnected", r"mcp error"],
         title="The connector couldn't start",
         means="A general failure. The cause is usually one of the others on this list, and the full message often says which.",
         fix="Disconnect and connect again. If it fails twice, take a screenshot of the full message and run this again with all of its text.",
         who="Depends on the full message", it=False),
]

GENERIC_STEPS = ["Disconnect the connector and connect it again.",
                 "Open the tool in your browser and make sure your normal login works there.",
                 "Copy the full error message, or take a screenshot, and run diagnose again with all of its text.",
                 "If it still fails, send the IT request with the exact message, and use the fallback meanwhile."]


DIAGNOSIS_EXAMPLES = [
    ("atlassian-admin", "Your site admin must authorize this app for the site before you can use it."),
    ("microsoft-consent", "Need admin approval. AADSTS65001: The user or administrator has not consented"),
    ("microsoft-conditional", "AADSTS53003: Access has been blocked by Conditional Access policies."),
    ("personal-account", "AADSTS50020: User account from identity provider does not exist in tenant"),
    ("app-blocked", "Access blocked: Claude has not been approved by your organization"),
    ("claude-owner", "This connector is greyed out. Contact your owner to enable it."),
    ("blocked-network", "HTTP 403 Forbidden: IP address is not allowed"),
    ("tls-inspection", "Error: SELF_SIGNED_CERT_IN_CHAIN self signed certificate in certificate chain"),
    ("tls-inspection", "client error (Connect): invalid peer certificate: UnknownIssuer"),
    ("proxy", "407 Proxy Authentication Required"),
    ("unreachable", "getaddrinfo ENOTFOUND mcp.example.com"),
    ("expired", "401 Unauthorized: invalid_token, the access token has expired"),
    ("claude-owner", "Your organization doesn't allow this connector"),
    ("rate-limit", "429 Too Many Requests"),
    ("oauth-client", "Error: invalid_client. Dynamic client registration is not supported"),
    ("callback-port", "listen EADDRINUSE: address already in use :::3118"),
    ("region", "This workspace is in the EU region. Use the EU endpoint."),
    ("plan-gate", "This feature is not available on your plan. Upgrade to Business."),
    ("plan-gate", "This feature isn't available on your current Smartsheet plan."),
    ("no-python", "bash: python3: command not found"),
    ("no-python", "Python was not found; run without arguments to install from the Microsoft Store"),
    ("no-python", "python3 : The term 'python3' is not recognized as the name of a cmdlet, function, script file, or operable program."),
    ("no-python", "'py' is not recognized as an internal or external command, operable program or batch file."),
    ("empty", "The search returned nothing, 0 results"),
    ("wrong-address", "Unexpected token < in JSON at position 0"),
    ("not-assigned", "AADSTS50105: The signed in user is not assigned to a role for the application"),
    ("mfa", "AADSTS50076: Due to a configuration change, you must use multi-factor authentication"),
    ("server-error", "502 Bad Gateway"),
    ("auth-failed", "Authorization with the MCP server failed"),

        ("app-blocked", "Error 403: access_denied. The developer hasn't given you access to this app."),
        ("app-blocked", "Error 403: org_internal This client is restricted to users within its organization."),
        ("oauth-client", "Access blocked: This app's request is invalid. Error 400: redirect_uri_mismatch"),
        ("needs-approval", "Install Request Sent. A workspace admin will need to approve this app."),
        ("atlassian-admin", "Contact your site admin to request access"),
        ("app-blocked", "Your workspace has restricted third-party integrations"),
        ("unreachable", "Couldn't reach the MCP server"),
        ("microsoft-consent", "AADSTS700016: Application with identifier was not found in the directory"),
        ("oauth-client", "Failed to connect: does not support dynamic client registration"),
        ("auth-failed", "OAuth error: access_denied (user denied)"),
        ("auth-failed", "The user canceled the authorization"),
        ("claude-owner", "Your organization's admin has disabled this connector"),
        ("claude-owner", "Your administrator has disabled custom connectors"),
        ("app-blocked", "Approval required. Your Box admin must enable this app"),
        ("app-blocked", "Your org has not enabled the Salesforce Hosted MCP Server"),
        ("blocked-network", "Your IP address is not on the allowlist"),
        ("oauth-client", "AADSTS50011: The redirect URI specified in the request does not match"),
]


def diagnose(text: str):
    hits = []
    for d in DIAGNOSES:
        score = (3 * sum(1 for p in d.get("strong", []) if re.search(p, text, flags=re.I))
                 + sum(1 for p in d.get("pats", []) if re.search(p, text, flags=re.I))
                 + 0.4 * sum(1 for p in d.get("weak", []) if re.search(p, text, flags=re.I)))
        if score:
            hits.append((score, d))
    hits.sort(key=lambda x: (-x[0], 1 if x[1]["id"] in ("generic", "wrong-address", "empty") else 0))
    return [d for _, d in hits]


def cmd_diagnose(args) -> int:
    text = sys.stdin.read() if args.stdin else " ".join(args.text or [])
    if not text.strip():
        sys.exit("Paste the error text after 'diagnose', or pipe it in with --stdin.")
    cat = load_catalog()
    tool = None
    if args.tool:
        ids = resolve_tools(cat, args.tool)
        tool = by_id(cat).get(ids[0]) if ids else None
    found = diagnose(text)[:3]
    if args.json:
        print(json.dumps({"matches": [{k: d[k] for k in ("id", "title", "means", "fix", "who", "it")} for d in found],
                          "tool": tool["id"] if tool else None}, indent=1))
        return 0 if found else 2
    if not found:
        print("I don't recognize this message yet. Try these, in order:")
        for i, s in enumerate(GENERIC_STEPS, 1):
            print(f"  {i}. {s}")
    for n, d in enumerate(found):
        print(("Most likely: " if n == 0 else "Also possible: ") + d["title"])
        print(f"  What it means: {d['means']}")
        print(f"  What to do: {d['fix']}")
        print(f"  Who can fix it: {d['who']}")
        if d["it"]:
            print("  Add this tool to the IT request: `connect.py it-request`.")
        print()
    if tool:
        if tool.get("admin"):
            print(f"For {tool['name']}: {tool['admin']}")
        if tool.get("fallback"):
            print(f"Meanwhile: {tool['fallback']}")
        if tool.get("docs"):
            print(f"Vendor guide: {tool['docs']}")
    return 0 if found else 2


# ---------------------------------------------------------------- IT request

def cmd_it_request(args) -> int:
    cat = load_catalog()
    ids = resolve_tools(cat, args.tools, keep_unknown=True)
    if args.tools and not ids:
        sys.exit("No tools named. Use ids from `connect.py list`, or tool names.")
    notes: dict[str, list[str]] = {}
    statuses: dict[str, str] = {}
    ws = None
    if args.workspace:
        p = Path(args.workspace).expanduser().resolve()
        if (p / PLAN_REL).exists():
            ws = p
    if ws:
        statuses, log = parse_plan(ws / PLAN_REL)
        if not ids:
            wanted = ("needs-admin", "failed", "skipped") if args.personal else ("needs-admin", "failed")
            ids = [t for t, s in statuses.items() if s in wanted]
        for line in log:
            m = re.match(r"- \S+ (\S+) (needs-admin|failed)(?:: (.*))?", line)
            if m and m.group(3):
                notes.setdefault(m.group(1), []).append(redact(m.group(3)))
    tools = tools_with_others(cat, ids)
    ids = [i for i in ids if i in tools and (tools[i]["route"] != "none" or i.startswith("other:"))]
    if not ids and not args.personal:
        sys.exit("Nothing needs IT yet. Pass --tools, or mark tools as needs-admin or failed in the plan first.")
    unclear = [i for i in ids if statuses.get(i) == "failed" and not args.personal]
    chosen = sorted((tools[i] for i in ids if i not in unclear), key=sort_key)
    unclear_tools = sorted((tools[i] for i in unclear), key=sort_key)
    names = [c["name"].split(" (")[0] for c in chosen + unclear_tools]
    listing = ("work tools" if not names else names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1])
    who = args.name or "<your name>"
    ai = (getattr(args, "assistant", None) or "Claude").strip() or "Claude"
    plan_example = ("Claude Team or Enterprise workspace" if ai == "Claude" else
                    "ChatGPT Business or Enterprise workspace, which includes Codex" if ai.lower() == "codex" else
                    f"{ai} business or enterprise workspace")
    if args.personal:
        out = [f"Subject: Request for an approved AI account, and read-only connectors for {listing}", "",
               "Hi <IT team or app owner>,", "",
               f"I'd like to use an AI assistant to prepare for meetings and keep track of follow-ups. I'm currently on a personal {ai} account, so I haven't connected any work tools. First question: is there a company-approved AI account I should use, or can we set one up (for example a {plan_example})?", "",
               "Once that's settled, I'd like to connect these tools read-only. Each person signs in with their own account, so it only sees what I can already see.", "",
               "What I'm asking for", ""]
    else:
        out = [f"Subject: Request to approve read-only AI connectors for {listing}", "",
               "Hi <IT team or app owner>,", "",
               f"I'd like to connect a few work tools to our company's {ai} account so my AI assistant can read my own mail, meetings, and work items, help me prepare for meetings, and keep track of follow-ups. Each person signs in with their own account, so it only sees what I can already see.", "",
               "What I'm asking for", ""]
    def claude_only(text):
        return ai != "Claude" and any(w in (text or "").lower() for w in ("claude", "anthropic"))
    chosen_ids = {x["id"] for x in chosen}
    def what_needed(c):
        if (c.get("admin") or "").startswith("Same as Gmail") and "gmail" not in chosen_ids:
            c = dict(c, admin=by_id(cat)["gmail"]["admin"])
        if c["id"].startswith("other:"):
            return ("Is there an approved way to connect it to our AI assistant (a connector in Claude's directory, or a read-only export)?" if ai == "Claude" else
                    f"Is there an approved way to connect it to our AI assistant (a connector that works with {ai}, or a read-only export)?")
        if claude_only(c.get("admin")):
            short = c["name"].split(" (")[0]
            where = "our ChatGPT workspace's settings (Workspace apps)" if ai.lower() == "codex" else f"our {ai} workspace's settings"
            return f"An admin makes {short} available for {ai} in {where}. If {short}'s own admin approves new apps, they approve it there once."
        return c.get("admin") or "Approval to connect it with my own login."
    if not chosen:
        out = out[:-2]
    for n, c in enumerate(chosen, 1):
        out.append(f"{n}. {c['name']}")
        out.append(f"   What's needed: {what_needed(c)}")
        if c.get("readonly") and not claude_only(c["readonly"]):
            out.append(f"   Read-only: {c['readonly']}")
        url = mcp_url(c)
        if url and not claude_only(url):
            out.append(f"   Connector address: {url}")
        if c.get("docs") and not claude_only(c["docs"]):
            out.append(f"   Setup guide: {c['docs']}")
        for note in notes.get(c["id"], []):
            out.append(f"   Error I saw: {note}")
        out.append("")
    if unclear_tools:
        out += ["Also not working yet (I couldn't tell why)", ""]
        for n, c in enumerate(unclear_tools, 1):
            out.append(f"{n}. {c['name']}: it didn't connect and the error didn't say why. Could you check whether it's allowed, or blocked by a network rule?")
            for note in notes.get(c["id"], []):
                out.append(f"   What happened: {note}")
            out.append("")
    out += ["What it will not do", "",
            "- Send, post, delete, or share anything on its own. Those tools stay off or need my approval every time.",
            "- Store customer records, credentials, or HR, legal, or health information.", "",
            ("Account: <the company-approved account, once we have one>" if args.personal else
             f"Account: <our company's {plan_example}, or 'I need to confirm which account is approved'>"),
            f"How to undo it: revoke the app in each tool's admin console. I can also disconnect it myself in {ai}'s settings.", "",
            "Happy to start as a small pilot and report back on what it saves.", "", "Thanks,", who, ""]
    text = "\n".join(out)
    if args.write:
        if not ws:
            sys.exit("--write needs --workspace pointing at a workspace with a connection plan.")
        day = today_str(getattr(args, "today", None))
        dest = ws / SETUP / f"it-request-{day}.md"
        k = 2
        while dest.exists():
            dest = ws / SETUP / f"it-request-{day}-{k}.md"
            k += 1
        write_lf(dest, text)
        print(f"Wrote {dest.relative_to(ws)}. Review the bracketed parts, then send it yourself.")
        return 0
    print(text)
    return 0


# ---------------------------------------------------------------- Claude Code config

def cmd_mcp_json(args) -> int:
    cat = load_catalog()
    tools = by_id(cat)
    ids = resolve_tools(cat, args.tools)
    if not ids:
        sys.exit("Pass --tools, for example --tools slack,atlassian,linear.")
    servers, skipped = {}, []
    for i in ids:
        c = tools[i]
        url = mcp_url(c, readonly=not args.full_access)
        if args.plugin and c.get("bundled"):
            skipped.append(f"{c['name']}: already listed by the plugin; type /mcp and sign in")
            continue
        if c["route"] == "none":
            skipped.append(f"{c['name']}: no connector yet")
            continue
        if c["route"] in ("admin-project", "api-key") and not url:
            skipped.append(f"{c['name']}: your admin has to set it up first; ask for the IT email")
            continue
        if c.get("claude_code") == "account" or (not url and c.get("in_directory")):
            skipped.append(f"{c['name']}: connect it on claude.ai with the same Claude account; it then shows up in /mcp")
            continue
        if not url:
            skipped.append(f"{c['name']}: needs a company-specific address from your admin")
            continue
        entry = {"type": "http", "url": url}
        for k in ("headers", "oauth"):
            if (c.get("mcp") or {}).get(k):
                entry[k] = c["mcp"][k]
        servers[i] = entry
    out_path = Path(args.output).expanduser()
    if out_path.is_dir():
        sys.exit(f"{out_path} is a folder. Pass the file path, for example {out_path / '.mcp.json'}.")
    if args.write and not out_path.parent.exists():
        sys.exit(f"The folder {out_path.parent} does not exist. Nothing was written.")
    existing = {}
    if out_path.exists():
        try:
            existing = json.loads(out_path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError:
            sys.exit(f"{out_path} is not valid JSON. Fix or move it first; nothing was changed.")
        if not isinstance(existing, dict) or not isinstance(existing.get("mcpServers", {}), dict):
            sys.exit(f"{out_path} is not in the expected format (an object with an mcpServers object). Nothing was changed.")
    merged = dict(existing)
    merged["mcpServers"] = dict(existing.get("mcpServers") or {})
    added, kept = [], []
    for k, v in servers.items():
        if k in merged["mcpServers"]:
            kept.append(k)
        else:
            merged["mcpServers"][k] = v
            added.append(k)
    text = json.dumps(merged, indent=2) + "\n"
    if args.write:
        if not added:
            print("Nothing new to add; the file was not touched.")
        else:
            backup = None
            if out_path.exists():
                stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
                backup = out_path.with_name(f"{out_path.name}.bak-{stamp}")
                n = 2
                while backup.exists():
                    backup = out_path.with_name(f"{out_path.name}.bak-{stamp}-{n}")
                    n += 1
                shutil.copy2(out_path, backup)
            write_lf(out_path, text)
            print(f"Wrote {out_path}" + (f" (backup: {backup.name})" if backup else "") + ".")
    else:
        print(text)
    if added:
        print("Added: " + ", ".join(added), file=sys.stderr)
    if kept:
        print("Already there, left untouched: " + ", ".join(kept), file=sys.stderr)
    for s_ in skipped:
        print("Skipped " + s_, file=sys.stderr)
    if any("headers" in servers[k] for k in added):
        print("GitHub reads a token from the GITHUB_PAT environment variable. Only if your company allows personal tokens: create a fine-grained, read-only one and set it before starting Claude Code. Never paste it into chat.", file=sys.stderr)
    if added:
        print("Next: restart Claude Code, type /mcp, and sign in to each one.", file=sys.stderr)
    return 0


# ---------------------------------------------------------------- network check (opt-in)

CHECK_BANNER = """This tests the network from the computer this script runs on.
- That is what Claude Code and Codex use, so the results apply to them.
- Connectors in claude.ai, Claude Desktop, and Cowork connect from Anthropic's cloud, not your computer. A failure here does not mean they will fail.
- If this ran inside a sandbox (Cowork, claude.ai, or Codex's, which blocks the network unless you allow it), it tested the sandbox, not your laptop. The real test runs from Claude Code, or from Codex with network access allowed, on your own computer.
- Nothing is signed in and no account data is sent."""


def confirm_resource(url: str, www_auth: str, timeout: float):
    """MCP servers that ask for sign-in publish what they protect (RFC 9728). True if this host says it is a
    sign-in protected server, False if it points somewhere else, None if there's nothing to check."""
    from urllib.parse import urlsplit
    m = re.search(r'resource_metadata="([^"]+)"', www_auth or "")
    parts = urlsplit(url)
    candidates = [m.group(1)] if m else []
    candidates += [f"{parts.scheme}://{parts.netloc}/.well-known/oauth-protected-resource{parts.path.rstrip('/')}",
                   f"{parts.scheme}://{parts.netloc}/.well-known/oauth-protected-resource"]
    norm_url = url.rstrip("/")
    for meta in candidates:
        try:
            req = urllib.request.Request(meta, headers={"User-Agent": "unpaid-intern-connect-check/1.0", "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read(200_000).decode("utf-8", "replace"))
        except Exception:
            continue
        res = str(data.get("resource", "")).rstrip("/")
        if not res:
            continue
        # Many servers echo whatever path you ask about, so this proves the host, not the exact path.
        return urlsplit(res).netloc == parts.netloc
    return None


def probe(url: str, timeout: float):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                       "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                                  "clientInfo": {"name": "unpaid-intern-connect-check", "version": "1.0"}}}).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Content-Type": "application/json", "Accept": "application/json, text/event-stream",
        "User-Agent": "unpaid-intern-connect-check/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return "ok", f"Reachable (HTTP {r.status})."
    except urllib.error.HTTPError as e:
        if e.code == 401:
            confirmed = confirm_resource(url, e.headers.get("WWW-Authenticate", ""), timeout)
            if confirmed is True:
                return "ok", "Reachable, and it identifies itself as a sign-in protected connector. Signing in is the final proof."
            if confirmed is False:
                return "moved", "Reachable, but it points to a different server. The catalog may be out of date."
            return "ok", "Reachable. It asks for sign-in, which is normal. (It didn't publish details to confirm the exact address.)"
        if e.code in (400, 404, 405, 406, 415):
            return "ok", f"Reachable (HTTP {e.code}). The server answered; sign-in happens in Claude."
        if e.code == 403:
            return "blocked", "Refused (HTTP 403). Often an IP allowlist or a company firewall rule."
        if e.code == 407:
            return "proxy", "Your network wants proxy credentials (HTTP 407). Ask IT for the proxy setting."
        if e.code == 429:
            return "ok", "Reachable, but rate-limited right now (HTTP 429)."
        return "server", f"The tool answered with an error (HTTP {e.code}). Try again later."
    except urllib.error.URLError as e:
        reason = e.reason
        text = str(reason)
        if isinstance(reason, ssl.SSLCertVerificationError) or "CERTIFICATE_VERIFY_FAILED" in text:
            return "tls", "Certificate check failed. Likely company traffic inspection; Claude Code needs NODE_EXTRA_CA_CERTS, and Codex needs CODEX_CA_CERTIFICATE. (Python's certificate store can differ from theirs, so treat this as a strong hint.)"
        if isinstance(reason, socket.gaierror):
            return "dns", "Could not look up the address. A VPN, a proxy, or a DNS rule is in the way."
        if isinstance(reason, (socket.timeout, TimeoutError)) or "timed out" in text:
            return "timeout", "Timed out. A firewall or proxy is probably holding the connection."
        if isinstance(reason, ConnectionRefusedError):
            return "refused", "Connection refused. A firewall or proxy is in the way."
        return "network", f"Network error: {text[:120]}"
    except (socket.timeout, TimeoutError):
        return "timeout", "Timed out. A firewall or proxy is probably holding the connection."
    except ssl.SSLError as e:
        return "tls", f"Secure connection failed ({str(e)[:80]}). Likely company traffic inspection."


def cmd_check(args) -> int:
    cat = load_catalog()
    tools = by_id(cat)
    ids = resolve_tools(cat, args.tools)
    if not ids:
        p = Path(args.workspace).expanduser().resolve() / PLAN_REL
        if p.exists():
            ids = list(parse_plan(p)[0].keys())
    if not ids:
        ids = [c["id"] for c in cat["connectors"] if c.get("bundled")]
    print(CHECK_BANNER)
    print()
    proxy = any(os.environ.get(k) for k in ("HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy"))
    ca = os.environ.get("NODE_EXTRA_CA_CERTS")
    codex_ca = os.environ.get("CODEX_CA_CERTIFICATE")
    print(f"Proxy setting (HTTPS_PROXY): {'set' if proxy else 'not set'}")
    print(f"Extra certificates for Claude Code (NODE_EXTRA_CA_CERTS): {'set, file found' if ca and Path(ca).exists() else ('set, but the file is missing' if ca else 'not set')}")
    print(f"Extra certificates for Codex (CODEX_CA_CERTIFICATE): {'set, file found' if codex_ca and Path(codex_ca).exists() else ('set, but the file is missing' if codex_ca else 'not set')}")
    print()
    bad = 0
    for i in ids:
        c = tools.get(i)
        if not c:
            continue
        url = mcp_url(c)
        if not url:
            print(f"- {c['name']}: skipped (no fixed address to test; it connects through Claude's directory or a company-specific address).")
            continue
        kind, msg = probe(url, args.timeout)
        bad += kind != "ok"
        print(f"- {c['name']}: {msg}")
    print()
    if bad:
        print("For anything that failed, run `connect.py diagnose` with the message above, or send the IT request.")
    else:
        print("Everything tested is reachable from here.")
    return 2 if bad else 0


# ---------------------------------------------------------------- markdown copies (for no-Python use)

GEN_NOTE = "Generated by `connect.py export-md` from the scripts' own data. Do not edit by hand; edit the source and re-run."
CATEGORY_TITLES = {"suite": "Mail, calendar, and office suites", "chat": "Chat", "meetings": "Meetings and transcripts",
                   "files": "Files", "tracker": "Trackers", "docs": "Docs and wikis", "work-management": "Work management",
                   "crm": "CRM", "support": "Support desks", "sales": "Sales tools", "design": "Design and whiteboards",
                   "analytics": "Product analytics", "dev": "Engineering", "data": "Data and dashboards",
                   "marketing": "Marketing", "hr": "People and recruiting", "finance": "Finance and contracts",
                   "automation": "Automation bridges"}


def _cell(text: str) -> str:
    return (text or "").replace("|", "/").replace("\n", " ").strip() or "-"


def markdown_copies(cat: dict) -> dict:
    out = {}
    tools = sorted(cat["connectors"], key=lambda c: (CATEGORY_ORDER.index(c["category"]) if c["category"] in CATEGORY_ORDER else 99, c["name"].lower()))
    cats = [k for k in CATEGORY_ORDER if any(c["category"] == k for c in tools)]
    lines = ["# Connector catalog", "", "Contents", ""] + [f"- {CATEGORY_TITLES[k]}" for k in cats] + [
        "", GEN_NOTE, "",
        f"Checked {cat['version']}. {cat['note']}", "",
        "How it connects: " + " ".join(f"**{ROUTE_SHORT[k]}**: {v}" for k, v in cat["routes"].items()), ""]
    for k in cats:
        lines += [f"## {CATEGORY_TITLES[k]}", "", "| Tool | Id | How it connects | Address | Admin step | Read-only | Until it works |", "|---|---|---|---|---|---|---|"]
        for c in (c for c in tools if c["category"] == k):
            addr = mcp_url(c, False) or c.get("url_template") or ("Claude's directory" if c.get("in_directory") else "-")
            name = c["name"] + (" (listed by the plugin)" if c.get("bundled") else "")
            lines.append(f"| {_cell(name)} | `{c['id']}` | {ROUTE_SHORT[c['route']]} | {_cell(addr)} | {_cell(c.get('admin'))} | {_cell(c.get('readonly'))} | {_cell(c.get('fallback'))} |")
        lines.append("")
    out["connectors/catalog.md"] = "\n".join(lines)

    lines = ["# Error decoder", "", GEN_NOTE, "",
             "Find the message that looks most like the one on screen. If two rows fit, the more specific one wins. If nothing fits: disconnect and connect again, check the login works in the tool's own website, then send the IT email with the exact message.", "",
             "| Looks like | What it means | What to do | Who can fix it | Goes in the IT email |", "|---|---|---|---|---|"]
    examples: dict = {}
    for want, text in DIAGNOSIS_EXAMPLES:
        examples.setdefault(want, []).append(text)
    for d in DIAGNOSES:
        looks = "; ".join(f'"{_cell(t)}"' for t in examples.get(d["id"], [])[:3]) or "-"
        lines.append(f"| {looks} | {_cell(d['title'])}. {_cell(d['means'])} | {_cell(d['fix'])} | {_cell(d['who'])} | {'Yes' if d['it'] else 'No'} |")
    out["references/error-decoder.md"] = "\n".join(lines) + "\n"

    lines = ["# Setup questions", "", "Contents", ""] + [f"- {sc['title']}" for sc in cat["screens"]] + ["", GEN_NOTE, "",
             "Ask one screen at a time. With a picker, use these exact labels; without one, show them as a numbered list and accept replies like \"1, 3\". Every question also accepts \"something else\" in the person's own words.", ""]
    for sc in cat["screens"]:
        when = "" if sc["when"] == "always" else f" (only if Role is \"{sc['when']}\")"
        lines += [f"## {sc['title']}{when}", ""]
        for q in sc["questions"]:
            kind = "pick all that apply" if q["multiSelect"] else "pick one"
            lines += [f"**{q['question']}** ({kind})", ""]
            for i, o in enumerate(q["options"], 1):
                maps = f" Tools: {', '.join(o['ids'])}." if o.get("ids") else ""
                follow = f" Then ask: {o['followup']}" if o.get("followup") else ""
                lines.append(f"{i}. {o['label']}: {o['description']}{maps}{follow}")
            lines.append("")
    out["references/setup-questions.md"] = "\n".join(lines)

    lines = ["# What each command unlocks", "", GEN_NOTE, "",
             "Use this for the tour when scripts can't run: pick four of the core eight that match what the person asked for help with, say what each one reads for them, and have them try one. List the other four core commands after them; mention the rest only when asked.", ""]
    for title, rows_ in (("The core eight", [c for c in cat["commands"] if c.get("core")]),
                         ("When you want more", [c for c in cat["commands"] if not c.get("core")])):
        lines += [f"## {title}", "", "| Command | What it does | Reads (when connected) | With nothing connected | Try it |", "|---|---|---|---|---|"]
        for c in rows_:
            reads = ", ".join(cat["kinds"][k].replace("your ", "") for k in c["uses"]) or "nothing; your own records"
            without = c.get("without") or ("Works fully." if not c["uses"] else "Works from pasted text and dropped files.")
            lines.append(f"| {c['command']} | {_cell(c['what'])} | {_cell(reads)} | {_cell(without)} | `{c['try_it']}` |")
        lines.append("")
    lines.pop()
    out["references/what-you-unlock.md"] = "\n".join(lines) + "\n"
    return out


def cmd_export_md(args) -> int:
    cat = load_catalog()
    root = HERE.parent
    stale = []
    for rel, text in markdown_copies(cat).items():
        path = root / rel
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != text:
            stale.append(rel)
            if not args.check:
                write_lf(path, text)
    if args.check:
        print("Markdown copies are current." if not stale else "Out of date: " + ", ".join(stale))
        return 1 if stale else 0
    print("Wrote " + ", ".join(stale) if stale else "Markdown copies were already current.")
    return 0


# ---------------------------------------------------------------- selftest

def cmd_selftest(args) -> int:
    results = []

    def check(name, cond):
        results.append((name, bool(cond)))

    cat = load_catalog()
    tools = by_id(cat)
    ids = [c["id"] for c in cat["connectors"]]
    check("catalog ids unique", len(ids) == len(set(ids)))
    check("routes known", all(c["route"] in ROUTE_ORDER for c in cat["connectors"]))
    check("route text for every route", set(cat["routes"]) == set(ROUTE_ORDER))
    check("categories ordered", all(c["category"] in CATEGORY_ORDER for c in cat["connectors"]))
    check("addresses are https", all(not mcp_url(c, False) or mcp_url(c, False).startswith("https://") for c in cat["connectors"]))
    check("read-only addresses are https", all(not c.get("readonly_url") or c["readonly_url"].startswith("https://") for c in cat["connectors"]))
    check("bundled tools have an mcp entry", all("mcp" in c for c in cat["connectors"] if c.get("bundled")))
    check("one-click or add-by-url tools have an address or directory listing",
          all(mcp_url(c, False) or c.get("in_directory") or c.get("url_template") for c in cat["connectors"] if c["route"] in ("one-click", "add-by-url")))
    check("every tool has a fallback or is a bridge", all(c.get("fallback") or c["category"] == "automation" for c in cat["connectors"]))
    check("no em dashes in catalog", "\u2014" not in CATALOG_PATH.read_text(encoding="utf-8"))
    alias_owner = {}
    clash = []
    for c in cat["connectors"]:
        for a in [c["id"], *c.get("aliases", [])]:
            k = norm(a)
            if k in alias_owner and alias_owner[k] != c["id"]:
                clash.append(k)
            alias_owner[k] = c["id"]
    check("aliases do not collide", not clash)

    # screens fit the picker limits
    ok = True
    for s in cat["screens"]:
        if len(s["questions"]) > 4:
            ok = False
        for q in s["questions"]:
            if not (2 <= len(q["options"]) <= 4) or not (1 <= len(q["header"]) <= 12):
                ok = False
            for o in q["options"]:
                if len(o["label"].split()) > 5 or not o.get("description"):
                    ok = False
                if any(i not in tools for i in o.get("ids", [])):
                    ok = False
    check("screens fit picker limits", ok)
    check("screens in flow order", [x["id"] for x in screens_for(cat, "Sales, success, support")] == ["home", "about", "everyday", "tracked", "role-customers", "yours"])
    check("single screen lookup", [x["id"] for x in screens_for(cat, "Sales, success, support", "role")] == ["role-customers"])
    check("one role screen per role option", sorted(s["when"] for s in cat["screens"] if s["when"] != "always") ==
          sorted(o["label"] for s in cat["screens"] for q in s["questions"] if q["header"] == "Role" for o in q["options"]))

    # match
    m = match_answers(cat, ["Outlook (Microsoft 365)", "Slack", "Jira", "Confluence"])
    check("match picker labels", m["ids"] == ["microsoft-365", "slack", "atlassian"])
    m = match_answers(cat, ["ClickUp and Trello, smartsheet"])
    check("match free text lists", m["ids"] == ["clickup", "trello", "smartsheet"])
    m = match_answers(cat, ["A note-taker app"])
    check("match follow-up", m["followups"] and not m["ids"])
    m = match_answers(cat, ["Gmail and Google Calendar"])
    check("match keeps label before splitting", m["ids"] == ["gmail", "google-calendar"])
    m = match_answers(cat, ["Totally Made Up Tool"])
    check("match unknown", m["unknown"] == ["Totally Made Up Tool"])
    m = match_answers(cat, ["teams", "sharepoint", "MS Teams"])
    check("match aliases", m["ids"] == ["microsoft-365"])
    m = match_answers(cat, ["Gainsight"])
    check("fuzzy match never lands on a picker label", m["unknown"] == ["Gainsight"] and not m["followups"])
    m = match_answers(cat, ["Excel or Sheets only"])
    check("match no-tool answers", m["no_tool"] == ["Excel or Sheets only"] and not m["ids"])

    # diagnose
    for want, text in DIAGNOSIS_EXAMPLES:
        got = diagnose(text)
        check(f"diagnose {want}: {text[:28]}", got and got[0]["id"] == want)
    check("plan-gate ignores browser headers", all(d["id"] != "plan-gate" for d in diagnose("Upgrade-Insecure-Requests: 1 HTTP 403")))
    check("redact strips secrets", all(x not in redact("token=abc123secretvalue&code=4/0AbCdEf Bearer ghp_abcdefghijklmnopqrstuvwxyz1234 eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.sig_nature_x password: hunter22") for x in ("abc123secretvalue", "4/0AbCdEf", "ghp_abcdef", "eyJhbGci", "hunter22")))
    check("redact keeps plain errors", redact("AADSTS65001: Need admin approval") == "AADSTS65001: Need admin approval")
    leaky = 'Authorization: Basic dXNlcjpwYXNzd29yZA== refresh_token: rt123abc "password": "pw987" xapp-1-A0-123456789-abcdef'
    check("redact covers basic auth, colon keys, json, xapp", all(x not in redact(leaky) for x in ("dXNlcjpw", "rt123abc", "pw987", "xapp-1")))
    check("redact leaves invalid_token wording alone", "invalid_token: the access token has expired" in redact("invalid_token: the access token has expired"))
    check("redact flattens newlines", "\n" not in redact("line one\n## Fake heading"))
    m = match_answers(cat, ["Teams/Outlook", "Jira (cloud)", "We use Jira", "jria", "slakc", "none", "n/a", "Google Workspace", "O365"])
    fp = match_answers(cat, ["Other", "make sure it works", "we have a monday standup", "words", "something else", "our teams are busy"])
    check("match avoids everyday-word false positives", not fp["ids"])
    m2 = match_answers(cat, ["Loop", "Notion Calendar", "we use linear"])
    check("match prefers the right tool for near names", m2["ids"] == ["microsoft-365", "notion", "linear"])
    check("match handles slashes, notes, typos, and none", set(m["ids"]) >= {"microsoft-365", "atlassian", "slack", "gmail", "google-calendar", "google-drive"} and not m["unknown"])
    check("diagnose unknown returns nothing", diagnose("the vibes are off") == [])
    check("no em dashes in diagnoses", all("\u2014" not in json.dumps(d) for d in DIAGNOSES))

    with tempfile.TemporaryDirectory() as tmp:
        ws = Path(tmp) / "brain"
        (ws / SETUP).mkdir(parents=True)
        quiet = open(os.devnull, "w")
        old = sys.stdout
        try:
            sys.stdout = quiet
            cmd_plan(argparse.Namespace(workspace=str(ws), tools="Slack,Jira,Salesforce,Zendesk,Outlook (Microsoft 365)",
                                        surface="cowork", today="2026-10-05", print=False))
        finally:
            sys.stdout = old
        plan = (ws / PLAN_REL).read_text(encoding="utf-8")
        st, _ = parse_plan(ws / PLAN_REL)
        check("plan lists every tool", set(st) == {"slack", "atlassian", "salesforce", "zendesk", "microsoft-365"})
        order = list(st)
        check("plan puts one-click first and no-connector last", order[0] in ("microsoft-365", "slack") and order[-1] == "zendesk")
        check("plan has steps and log", "## Steps" in plan and "## Log" in plan and "2026-10-05 plan created" in plan)
        check("plan has no em dashes", "\u2014" not in plan)
        try:
            sys.stdout = quiet
            cmd_mark(argparse.Namespace(workspace=str(ws), tool="slack", status="connected", note=None, today="2026-10-05"))
            cmd_mark(argparse.Namespace(workspace=str(ws), tool="jira", status="needs-admin", note="Your site admin must authorize | this app", today="2026-10-07"))
        finally:
            sys.stdout = old
        check("mark keeps the date the plan was made", "Made on 2026-10-05" in (ws / PLAN_REL).read_text(encoding="utf-8"))
        try:
            sys.stdout = quiet
            cmd_plan(argparse.Namespace(workspace=str(ws), tools="Notion", surface=None, today="2026-10-06", print=False))
        finally:
            sys.stdout = old
        st, log = parse_plan(ws / PLAN_REL)
        check("mark sets status", st.get("slack") == "connected" and st.get("atlassian") == "needs-admin")
        check("re-plan keeps statuses and adds tools", st.get("slack") == "connected" and st.get("notion") == "to-do")
        check("log kept and pipes escaped", any("atlassian needs-admin: Your site admin must authorize / this app" in l for l in log))
        check("plan table still parses", len(st) == 6)
        try:
            sys.stdout = quiet
            sys.stderr, olderr = quiet, sys.stderr
            cmd_plan(argparse.Namespace(workspace=str(ws), tools="SAP Concur", surface=None, today="2026-10-06", print=False))
            cmd_mark(argparse.Namespace(workspace=str(ws), tool="other:SAP Concur", status="needs-admin", note=None, today="2026-10-06"))
            cmd_mark(argparse.Namespace(workspace=str(ws), tool="salesforce", status="failed", note="something went wrong", today="2026-10-06"))
        finally:
            sys.stdout, sys.stderr = old, olderr
        st, _ = parse_plan(ws / PLAN_REL)
        check("tools the catalog doesn't know stay in the plan", st.get("other:SAP Concur") == "needs-admin")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cmd_it_request(argparse.Namespace(workspace=str(ws), tools=None, name="Pat", write=False, personal=False, today="2026-10-06"))
        mail = buf.getvalue()
        check("IT email asks about tools the catalog doesn't know", "SAP Concur" in mail and "approved way to connect" in mail)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cmd_it_request(argparse.Namespace(workspace=str(ws), tools=None, name="Pat", write=False, personal=True, today="2026-10-06", assistant="Codex"))
        codex_mail = buf.getvalue()
        check("IT email names Claude by default, and another product with --assistant",
              "company's Claude account" in mail and "Claude's settings" in mail
              and "Claude" not in codex_mail and "personal Codex account" in codex_mail and "Codex's settings" in codex_mail)
        codex_both = ""
        for personal in (False, True):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                cmd_it_request(argparse.Namespace(workspace=str(ws), tools="gmail,microsoft-365,slack", name="Pat", write=False, personal=personal, today="2026-10-06", assistant="Codex"))
            codex_both += buf.getvalue()
        check("IT email for Codex never asks IT to set up Claude, personal version too",
              "claude" not in codex_both.lower() and codex_both.count("Gmail available for Codex in our ChatGPT workspace's settings (Workspace apps)") == 2)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cmd_it_request(argparse.Namespace(workspace=None, tools="gmail, microsoft 365, linear, box", name="Pat", write=False, personal=False, today="2026-10-06", assistant="Codex"))
        codex_admin = buf.getvalue()
        check("IT email for Codex leaves out Claude-only steps, addresses, and guides",
              "Claude" not in codex_admin and "claude.com" not in codex_admin and "https://mcp.box.com" in codex_admin)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cmd_it_request(argparse.Namespace(workspace=None, tools="google calendar, hubspot", name="Pat", write=False, personal=False, today="2026-10-06", assistant=None))
        cal_claude = buf.getvalue()
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cmd_it_request(argparse.Namespace(workspace=None, tools="google calendar, hubspot", name="Pat", write=False, personal=False, today="2026-10-06", assistant="Codex"))
        cal_codex = buf.getvalue()
        check("IT email spells out Google Calendar's steps when Gmail isn't in it, and Codex's leaves out Anthropic-only addresses",
              "Same as Gmail" not in cal_claude + cal_codex and "Google Workspace admin" in cal_claude
              and "Google Calendar available for Codex" in cal_codex and "anthropic" not in cal_codex.lower() and "mcp.hubspot.com/anthropic" in cal_claude)
        check("IT email for Codex asks about a plan OpenAI sells", "a ChatGPT Business or Enterprise workspace, which includes Codex" in codex_mail)
        check("IT email keeps unclear failures apart from approvals", "Also not working yet" in mail and mail.index("Salesforce", mail.index("What I")) > mail.index("Also not working yet"))
        m2 = match_answers(cat, ["sales force", "nothing really"])
        check("match joins split names and skips 'nothing really'", m2["ids"] == ["salesforce"] and not m2["unknown"])
        try:
            sys.stdout = quiet
            cmd_it_request(argparse.Namespace(workspace=str(ws), tools=None, name="Pat", write=True, personal=False))
        finally:
            sys.stdout = old
        reqs = list((ws / SETUP).glob("it-request-*.md"))
        req = reqs[0].read_text(encoding="utf-8") if reqs else ""
        check("it-request picks needs-admin tools", "Atlassian (Jira, Confluence, Loom)" in req and "Slack" not in req.split("What it will not do")[0].split("What I'm asking for")[1])
        check("it-request carries the error seen", "Error I saw: Your site admin must authorize" in req)
        check("it-request uses catalog admin text", "site admin completes first consent" in req)
        try:
            sys.stdout = quiet
            cmd_it_request(argparse.Namespace(workspace=str(ws), tools=None, name="Pat", write=True, personal=False))
        finally:
            sys.stdout = old
        check("second it-request gets a new name", len(list((ws / SETUP).glob("it-request-*.md"))) == 2)

        # mcp-json merge never clobbers
        mj = Path(tmp) / ".mcp.json"
        mj.write_text(json.dumps({"mcpServers": {"slack": {"type": "http", "url": "https://example.invalid/mine"}}}), encoding="utf-8")
        olderr = sys.stderr
        try:
            sys.stdout = quiet
            sys.stderr = quiet
            cmd_mcp_json(argparse.Namespace(tools="slack,linear,gmail,github,zendesk,asana,microsoft-365", output=str(mj), write=True, full_access=False, plugin=False))
            cmd_mcp_json(argparse.Namespace(tools="notion", output=str(mj), write=True, full_access=False, plugin=False))
        finally:
            sys.stdout = old
            sys.stderr = olderr
        conf = json.loads(mj.read_text(encoding="utf-8"))["mcpServers"]
        check("mcp-json keeps the user's entry", conf["slack"]["url"] == "https://example.invalid/mine")
        check("mcp-json prefers read-only", conf.get("linear", {}).get("url") == "https://mcp.linear.app/mcp/readonly")
        check("mcp-json skips directory-only and none", "gmail" not in conf and "zendesk" not in conf)
        check("mcp-json token comes from env, never inline", conf.get("github", {}).get("headers", {}).get("Authorization") == "Bearer ${GITHUB_PAT}")
        check("mcp-json skips tools that need the Claude account", "asana" not in conf and "microsoft-365" not in conf)
        check("mcp-json keeps every backup", len(list(Path(tmp).glob(".mcp.json.bak-*"))) == 2)
        bad = Path(tmp) / "bad.json"
        bad.write_text('{"mcpServers": null}', encoding="utf-8")
        try:
            sys.stdout = quiet
            sys.stderr = quiet
            cmd_mcp_json(argparse.Namespace(tools="linear", output=str(bad), write=True, full_access=False, plugin=False))
            ok_bad = False
        except SystemExit:
            ok_bad = True
        finally:
            sys.stdout = old
            sys.stderr = olderr
        check("mcp-json refuses an odd file instead of crashing", ok_bad and bad.read_text(encoding="utf-8") == '{"mcpServers": null}')
        # Windows PowerShell can save a byte-order mark, or the ANSI code page without -Encoding utf8
        bom_mj = Path(tmp) / "bom.json"
        bom_mj.write_bytes(b"\xef\xbb\xbf" + json.dumps({"mcpServers": {}}).encode("utf-8"))
        (ws / SETUP / "preferences.md").write_bytes(b"\xef\xbb\xbf# Preferences\n- note: caf\xe9 \x93quotes\x94\n- help first: Status updates\n")
        try:
            sys.stdout = quiet
            sys.stderr = quiet
            cmd_mcp_json(argparse.Namespace(tools="linear", output=str(bom_mj), write=True, full_access=False, plugin=False))
            bom_ok = "linear" in json.loads(bom_mj.read_text(encoding="utf-8"))["mcpServers"]
        except SystemExit:
            bom_ok = False
        finally:
            sys.stdout = old
            sys.stderr = olderr
        check("files saved by Windows PowerShell (byte-order mark, ANSI bytes) still read",
              bom_ok and read_help_first(ws) == ["Status updates"])
        quiet.close()

    # commands and tour
    labels = {o["label"] for s in cat["screens"] for q in s["questions"] if q["header"] in ("Help with", "New here?") for o in q["options"]}
    check("command helps match the Help with picker", all(set(c["helps"]) <= labels for c in cat["commands"]))
    check("command uses are known kinds", all(set(c["uses"]) <= set(cat["kinds"]) for c in cat["commands"]))
    check("every tool provides known kinds", all(set(c.get("provides", [])) <= set(cat["kinds"]) for c in cat["connectors"]))
    skill_md = HERE.parent / "SKILL.md"
    if skill_md.exists():
        sk = skill_md.read_text(encoding="utf-8")
        section = sk.split("\n## Commands", 1)[-1].split("\n## ", 1)[0]
        listed = set(re.findall(r"`(/[a-z-]+)`", section))
        check("tour covers exactly the SKILL.md commands", listed == {c["command"] for c in cat["commands"]})
        core_rows = set(re.findall(r"^\| `(/[a-z-]+)`", section, flags=re.M))
        check("SKILL.md's core table is exactly the eight core commands",
              core_rows == {c["command"] for c in cat["commands"] if c.get("core")} and len(core_rows) == 8)
    start, rows, reads, better = build_tour(cat, ["microsoft-365"], ["atlassian"], ["Meeting prep and notes"])
    check("tour starts with what they asked for", start and start[0]["cmd"]["command"] in ("/prep", "/debrief") and len(start) == 4)
    prep = next(r for r in rows if r["cmd"]["command"] == "/prep")
    check("tour names the live source", "Microsoft 365" in reads(prep))
    ps = next(r for r in rows if r["cmd"]["command"] == "/project-status")
    check("tour says what gets better", "Atlassian" in better(ps))
    cap = next(r for r in rows if r["cmd"]["command"] == "/capture")
    check("tour marks no-connector commands", "Nothing to connect" in reads(cap))
    check("help-first labels with commas stay whole",
          split_help("Meeting prep and notes, Yes, still ramping up", cat) == ["Meeting prep and notes", "Yes, still ramping up"])
    ramp, *_ = build_tour(cat, [], [], split_help("Yes, still ramping up", cat))
    check("someone new starts with /who and /explain", [r["cmd"]["command"] for r in ramp[:2]] == ["/who", "/explain"])
    start2, *_ = build_tour(cat, [], [], [])
    check("tour with nothing connected still has starters", len(start2) == 4 and all(r["cmd"].get("starter") for r in start2))
    core_cmds = {c["command"] for c in cat["commands"] if c.get("core")}
    every_pick = [split_help(x, cat) for x in ("", "Meeting prep and notes", "Tracking follow-ups", "A morning brief",
                                               "Status updates", "Yes, still ramping up", "Meeting prep and notes, A morning brief")]
    check("tour's starters come only from the core eight, for every help-with answer",
          all({r["cmd"]["command"] for r in build_tour(cat, [], [], hf)[0]} <= core_cmds for hf in every_pick))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        cmd_tour(argparse.Namespace(workspace=str(Path(tempfile.gettempdir()) / "no-such-workspace"), connected=None,
                                    help_first="Meeting prep and notes", write=False, json=False))
    page = buf.getvalue().split("There are ", 1)[0]
    shown = set(re.findall(r"\*\*(/[a-z-]+)\*\*", page))
    check("tour's core sections show exactly the core eight (meeting help no longer adds /slots)", shown == core_cmds and "/slots" not in page)

    class Stubborn:
        def reconfigure(self, **kw):
            raise ValueError("no")
    wrapped = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")
    try:
        utf8_console([io.StringIO(), None, Stubborn(), wrapped])
        survived = True
    except Exception:
        survived = False
    check("the UTF-8 console switch never crashes, and switches what it can", survived and wrapped.encoding.lower() == "utf-8")

    copies = markdown_copies(cat)
    check("markdown copies are current (run export-md)", all((HERE.parent / rel).exists() and (HERE.parent / rel).read_text(encoding="utf-8") == text for rel, text in copies.items()))
    check("markdown copies have no em dashes", all("\u2014" not in t for t in copies.values()))

    # plugin consistency, when running inside the plugin
    root = HERE.parents[2] if len(HERE.parents) > 2 else None
    if root and (root / ".claude-plugin" / "plugin.json").exists() and (root / ".mcp.json").exists():
        bundled = json.loads((root / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]
        want = {c["id"] for c in cat["connectors"] if c.get("bundled")}
        names = {"google calendar": "google-calendar"}
        got = {names.get(k, k) for k in bundled}
        check("plugin .mcp.json matches the bundled set", got == want)
        same = all((bundled[k].get("url", "") == mcp_url(tools[names.get(k, k)], True)) for k in bundled)
        check("plugin addresses match the catalog, read-only first", same)
        hooks = root / "hooks" / "hooks.json"
        check("plugin ships the ask-first hook", hooks.is_file() and "permissionDecision" in hooks.read_text(encoding="utf-8"))

    width = max(len(n) for n, _ in results)
    for n, ok in results:
        print(f"  {'ok  ' if ok else 'FAIL'}  {n}")
    passed = sum(ok for _, ok in results)
    print(f"\n{passed}/{len(results)} checks passed.")
    return 0 if passed == len(results) else 1


# ---------------------------------------------------------------- main

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Connect work tools to the second brain, and fix them when they don't connect.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("list", help="every known tool and how it connects")
    p.add_argument("--category")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("screens", help="setup questions, ready for a picker")
    p.add_argument("--role")
    p.add_argument("--screen", help="one screen: home, about, everyday, tracked, yours, or role (with --role)")
    p.add_argument("--text", action="store_true", help="add the numbered-list note for surfaces without a picker")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_screens)

    p = sub.add_parser("match", help="turn picker answers or tool names into tools")
    p.add_argument("answers", nargs="+")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_match)

    p = sub.add_parser("plan", help="write Setup/connection-plan.md")
    p.add_argument("--tools")
    p.add_argument("--surface", choices=SURFACES, help="default: the plan's existing surface, else cowork")
    p.add_argument("--workspace", default=".")
    p.add_argument("--today")
    p.add_argument("--print", action="store_true", help="print instead of writing")
    p.set_defaults(func=cmd_plan)

    p = sub.add_parser("mark", help="record how a connection went")
    p.add_argument("tool")
    p.add_argument("status")
    p.add_argument("--note")
    p.add_argument("--workspace", default=".")
    p.add_argument("--today")
    p.set_defaults(func=cmd_mark)

    p = sub.add_parser("diagnose", help="explain an error message")
    p.add_argument("text", nargs="*")
    p.add_argument("--stdin", action="store_true")
    p.add_argument("--tool")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_diagnose)

    p = sub.add_parser("it-request", help="one email to IT")
    p.add_argument("--tools")
    p.add_argument("--workspace", default=".")
    p.add_argument("--name")
    p.add_argument("--personal", action="store_true", help="lead with asking for an approved AI account")
    p.add_argument("--assistant", default="Claude", help="the AI product the email names (default: Claude), for example Codex")
    p.add_argument("--write", action="store_true")
    p.add_argument("--today", help="override today's date, YYYY-MM-DD")
    p.set_defaults(func=cmd_it_request)

    p = sub.add_parser("tour", help="what the connected tools unlock")
    p.add_argument("--workspace", default=".")
    p.add_argument("--connected", help="override: tools to treat as connected")
    p.add_argument("--help-first", help="comma list of the 'help with first' answers")
    p.add_argument("--write", action="store_true", help="save Setup/my-commands.md")
    p.add_argument("--json", action="store_true", help="picker payload for 'which one first?'")
    p.set_defaults(func=cmd_tour)

    p = sub.add_parser("mcp-json", help="Claude Code config")
    p.add_argument("--tools")
    p.add_argument("--output", default=".mcp.json")
    p.add_argument("--write", action="store_true")
    p.add_argument("--full-access", action="store_true", help="use full addresses instead of read-only ones")
    p.add_argument("--plugin", action="store_true", help="skip tools the plugin already lists")
    p.set_defaults(func=cmd_mcp_json)

    p = sub.add_parser("check", help="network test from this computer (uses the network)")
    p.add_argument("--tools")
    p.add_argument("--workspace", default=".")
    p.add_argument("--timeout", type=float, default=8.0)
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("export-md", help="refresh the markdown copies used when Python can't run")
    p.add_argument("--check", action="store_true", help="only report whether they are current")
    p.set_defaults(func=cmd_export_md)

    p = sub.add_parser("selftest", help="run the built-in tests")
    p.set_defaults(func=cmd_selftest)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
