#!/usr/bin/env python3
"""Build, check, and package Unpaid Intern. Standard library only; run from anywhere.

    python3 tools/build.py            regenerate the derived files (plugin config, hook, markdown copies)
    python3 tools/build.py --check    fail if any derived file is stale (CI runs this)
    python3 tools/build.py --test     run every self-test: brain.py, connect.py, and the hook rules
    python3 tools/build.py --dist     regenerate, test, then write the release files to dist/

The repo root is the plugin. The skill lives in skills/unpaid-intern/. Derived files are committed,
so the plugin installs straight from GitHub; this script keeps them in sync with their sources.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = "unpaid-intern"
SKILL = ROOT / "skills" / NAME
SCRIPTS = SKILL / "scripts"
DIST = ROOT / "dist"
BUNDLED_ORDER = ["gmail", "google-calendar", "slack", "atlassian", "notion"]
SERVER_NAMES = {"google-calendar": "google calendar"}

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hook_rules  # noqa: E402


def mcp_json() -> str:
    cat = json.loads((SKILL / "connectors" / "catalog.json").read_text(encoding="utf-8"))
    by = {c["id"]: c for c in cat["connectors"]}
    bundled = {c["id"] for c in cat["connectors"] if c.get("bundled")}
    if set(BUNDLED_ORDER) != bundled:
        raise SystemExit(f"Bundled connectors changed. Update BUNDLED_ORDER in tools/build.py: {sorted(bundled)}")
    servers = {}
    for i in BUNDLED_ORDER:
        entry = dict(by[i]["mcp"])
        if by[i].get("readonly_url"):          # read-only address first; full access is opt-in
            entry["url"] = by[i]["readonly_url"]
        servers[SERVER_NAMES.get(i, i)] = entry
    return json.dumps({"mcpServers": servers}, indent=2) + "\n"


OPENAI_INTERFACE = {
    "displayName": "Unpaid Intern",
    "shortDescription": "A second brain for work, in plain files you own.",
    "longDescription": ("Hand it your meeting transcripts, docs, tickets, and email, and it hands back your morning briefing, "
                        "prep for your next meeting, a status update ready to paste, and every follow-up with an owner and a date. "
                        "It drafts; you decide what goes out."),
    "developerName": "Kevin Middleton",
    "category": "Productivity",
    "capabilities": ["Read", "Write"],
    "websiteURL": "https://github.com/kevinmmiddleton/unpaid-intern",
    "defaultPrompt": ["Set me up", "Brief me", "Prep me for my next meeting"],
    "brandColor": "#FF8FC1",
    "composerIcon": "./assets/brand/png/app-icon-180.png",
    "logo": "./assets/brand/png/app-icon-512.png",
    "screenshots": ["./assets/brand/marketing/hero.png", "./assets/brand/marketing/sample-brief.png", "./assets/brand/marketing/core.png"],
}


def portable_manifest() -> str:
    """Root plugin.json in the Agent Plugins format, for Codex and ChatGPT. Identity comes from .claude-plugin/plugin.json."""
    cp = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    out = {"$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"}
    for k in ("name", "version", "description", "author", "homepage", "repository", "license", "keywords"):
        if k in cp:
            out[k] = cp[k]
    out["extensions"] = {"com.openai": {"interface": OPENAI_INTERFACE}}
    return json.dumps(out, indent=2) + "\n"


def portable_mcp_json() -> str:
    """Root mcp.json for Codex and ChatGPT: the pre-listed connectors that need no Claude-specific sign-in (fixed URL, no Claude OAuth client)."""
    servers = json.loads(mcp_json())["mcpServers"]
    keep = {n: {"type": "streamable-http", "url": e["url"]} for n, e in servers.items() if e.get("url") and "oauth" not in e}
    return json.dumps({"$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json", "mcpServers": keep}, indent=2) + "\n"


MARKETPLACE = "unpaid-intern"   # install as unpaid-intern@unpaid-intern, straight from this repo


def marketplace_json() -> str:
    """Claude Code marketplace: this repo installs itself (/plugin marketplace add kevinmmiddleton/unpaid-intern)."""
    cp = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    out = {
        "name": MARKETPLACE,
        "description": OPENAI_INTERFACE["shortDescription"],
        "owner": cp["author"],
        "plugins": [{"name": cp["name"], "source": "./", "description": cp["description"], "homepage": cp["repository"]}],
    }
    return json.dumps(out, indent=2) + "\n"


def codex_marketplace_json() -> str:
    """Codex marketplace: the same, in the .agents layout (codex plugin marketplace add kevinmmiddleton/unpaid-intern)."""
    cp = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    out = {
        "name": MARKETPLACE,
        "interface": {"displayName": OPENAI_INTERFACE["displayName"]},
        "plugins": [{
            "name": cp["name"],
            "source": {"source": "local", "path": "./"},
            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            "category": OPENAI_INTERFACE["category"],
        }],
    }
    return json.dumps(out, indent=2) + "\n"


def derived() -> dict[str, str]:
    return {
        ".mcp.json": mcp_json(),
        ".claude-plugin/marketplace.json": marketplace_json(),
        ".agents/plugins/marketplace.json": codex_marketplace_json(),
        "plugin.json": portable_manifest(),
        "mcp.json": portable_mcp_json(),
        "hooks/hooks.json": hook_rules.hooks_json(),
    }


def run(cmd: list[str]) -> int:
    print("$", " ".join(cmd if cmd[0] != sys.executable else ["python3", *cmd[1:]]), flush=True)
    return subprocess.call(cmd, cwd=ROOT)


def write_derived() -> None:
    for rel, text in derived().items():
        p = ROOT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists() or p.read_text(encoding="utf-8") != text:
            with open(p, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
            print("wrote", rel)
    run([sys.executable, str(SCRIPTS / "connect.py"), "export-md"])


def check() -> int:
    bad = [rel for rel, text in derived().items()
           if not (ROOT / rel).exists() or (ROOT / rel).read_text(encoding="utf-8") != text]
    for rel in bad:
        print("stale:", rel)
    rc = run([sys.executable, str(SCRIPTS / "connect.py"), "export-md", "--check"])
    version_rc = check_versions()
    if bad or rc or version_rc:
        print("Run: python3 tools/build.py   (then commit the changes)")
        return 1
    print("derived files are current")
    return 0


def check_versions() -> int:
    pj = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
    skill = re.search(r'^\s+version:\s*"?([\d.]+)"?', (SKILL / "SKILL.md").read_text(encoding="utf-8"), re.M)
    sv = skill.group(1) if skill else "?"
    if pj != sv:
        print(f"version mismatch: plugin.json {pj}, SKILL.md {sv}")
        return 1
    return 0


def test() -> int:
    rc = 0
    rc |= run([sys.executable, str(SCRIPTS / "brain.py"), "selftest"])
    rc |= run([sys.executable, str(SCRIPTS / "connect.py"), "selftest"])
    rc |= hook_rules.selftest()
    rc |= check_frontmatter()
    print("ALL TESTS PASSED" if rc == 0 else "SOME TESTS FAILED")
    return 1 if rc else 0


def check_frontmatter() -> int:
    """Skill and command frontmatter: required fields, limits, and no em dashes in user-facing copy."""
    problems = []
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        problems.append("SKILL.md has no frontmatter")
    else:
        fm = m.group(1)
        name = re.search(r"^name:\s*(\S+)", fm, re.M)
        desc = re.search(r'^description:\s*"(.*)"\s*$', fm, re.M)
        if not name or name.group(1) != NAME:
            problems.append("SKILL.md name must be " + NAME)
        if not desc or len(desc.group(1)) > 1024:
            problems.append(f"SKILL.md description missing or over 1024 characters ({len(desc.group(1)) if desc else 0})")
    for p in sorted((ROOT / "commands").glob("*.md")):
        t = p.read_text(encoding="utf-8")
        if not t.startswith("---\n") or "\ndescription:" not in t.split("\n---", 2)[0]:
            problems.append(f"commands/{p.name} needs frontmatter with a description")
    for p in [ROOT / "README.md", ROOT / "CONNECTORS.md", SKILL / "SKILL.md", *sorted((SKILL / "references").glob("*.md")),
              *sorted((ROOT / "commands").glob("*.md"))]:
        if "—" in p.read_text(encoding="utf-8"):
            problems.append(f"{p.relative_to(ROOT)} has an em dash")
    for msg in problems:
        print("  FAIL ", msg)
    print(f"frontmatter and copy checks: {'ok' if not problems else str(len(problems)) + ' problem(s)'}")
    return 1 if problems else 0


# ---------------------------------------------------------------- release files

PLUGIN_EXCLUDE = ("dist/", "tools/", "evals/", ".github/", ".git/", "assets/brand/png/")


def _readme_marketing() -> set:
    """Marketing images the README shows. Only these ship in the .plugin, so its README still renders."""
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    return set(re.findall(r'(assets/brand/marketing/[\w.-]+\.png)', text))


def _zip_tree(zf: zipfile.ZipFile, base: Path, arc_prefix: str, exclude=()) -> None:
    for p in sorted(base.rglob("*")):
        rel = p.relative_to(base).as_posix()
        if p.is_dir() or "__pycache__" in rel or p.name in (".DS_Store", ".gitignore", ".gitattributes") or rel.endswith(".pyc"):
            continue
        readme_png = rel in ("assets/brand/banners/github-social-1280x640.png",)  # the README's hero image
        if any(rel.startswith(x) for x in exclude) or (rel.startswith("assets/brand/banners/") and rel.endswith(".png") and not readme_png):
            continue
        if exclude and rel.startswith("assets/brand/marketing/") and rel not in _readme_marketing():
            continue
        info = zipfile.ZipInfo(arc_prefix + rel, date_time=(2026, 1, 1, 0, 0, 0))
        info.external_attr = (0o755 if os.access(p, os.X_OK) else 0o644) << 16
        info.compress_type = zipfile.ZIP_DEFLATED
        zf.writestr(info, p.read_bytes())


def dist() -> int:
    write_derived()
    if test():
        return 1
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    # 1. Cowork plugin file: the repo, minus build tooling and heavy images
    with zipfile.ZipFile(DIST / f"{NAME}.plugin", "w") as zf:
        _zip_tree(zf, ROOT, "", PLUGIN_EXCLUDE)
    # 2. Skill upload for claude.ai and Claude Desktop: one top-level folder
    with zipfile.ZipFile(DIST / f"{NAME}.zip", "w") as zf:
        _zip_tree(zf, SKILL, f"{NAME}/")
        info = zipfile.ZipInfo(f"{NAME}/LICENSE", date_time=(2026, 1, 1, 0, 0, 0))
        zf.writestr(info, (ROOT / "LICENSE").read_bytes())
    # 3. No-install kit: instructions plus a ready-made Second Brain folder
    kit = f"{NAME}-no-install-kit"
    with tempfile.TemporaryDirectory() as tmp:
        k = Path(tmp) / kit
        k.mkdir()
        for p in (SKILL / "extras" / "no-install-kit").glob("*.md"):
            shutil.copy(p, k / p.name)
        shutil.copy(SKILL / "assets" / "lesson-101.html", k / "lesson-101.html")  # the /learn template, for a Project upload
        subprocess.check_call([sys.executable, str(SCRIPTS / "brain.py"), "init", str(k / "Second Brain")],
                              stdout=subprocess.DEVNULL)
        with zipfile.ZipFile(DIST / f"{kit}.zip", "w") as zf:
            _zip_tree(zf, k, f"{kit}/")
    for p in sorted(DIST.iterdir()):
        print(f"  {p.name:40} {p.stat().st_size // 1024:>6} KB")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--check", action="store_true", help="fail if derived files are stale")
    g.add_argument("--test", action="store_true", help="run every self-test")
    g.add_argument("--dist", action="store_true", help="build release files into dist/")
    a = ap.parse_args()
    if a.check:
        return check()
    if a.test:
        return test()
    if a.dist:
        return dist()
    write_derived()
    return 0


if __name__ == "__main__":
    sys.exit(main())
