"""Marketing images for the Unpaid Intern GitHub page. All text is outlined, so the SVGs need no fonts."""
import os
import cairosvg, uharfbuzz as hb
from fontTools.ttLib import TTFont
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely import affinity
import build_logo as bl

OUT = os.path.join(bl.OUT, "marketing")
os.makedirs(OUT, exist_ok=True)
INK, PINK, PAPER, YEL, WHITE = bl.INK, bl.PINK, bl.PAPER, bl.YEL, "#FFFFFF"
FONTS = {"bold": "Poppins-Bold.ttf", "medium": "Poppins-Medium.ttf", "regular": "Poppins-Regular.ttf"}
_F = {}

def font(kind):
    if kind not in _F:
        path = bl.font_file(FONTS[kind])
        tt = TTFont(path)
        with open(path, "rb") as fh:
            face = hb.Face(fh.read())
        _F[kind] = (tt, tt.getGlyphSet(), tt["head"].unitsPerEm, hb.Font(face), tt.getGlyphOrder())
    return _F[kind]

def shape(text, size, kind):
    tt, gs, upm, hbf, order = font(kind)
    buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
    hb.shape(hbf, buf, {"kern": True})
    return buf, size / upm

def measure(text, size, kind="regular"):
    buf, sc = shape(text, size, kind)
    return sum(p.x_advance for p in buf.glyph_positions) * sc

_cache = {}
def text_geom(text, size, kind="regular", embolden=0.0):
    key = (text, size, kind, embolden)
    if key in _cache:
        return _cache[key]
    tt, gs, upm, hbf, order = font(kind)
    buf, sc = shape(text, size, kind)
    x = 0.0; shapes = []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        pen = bl.PolyPen(gs); gs[order[info.codepoint]].draw(pen)
        g = Polygon()
        for ring in pen.rings:
            if len(ring) >= 3:
                g = g.symmetric_difference(Polygon(ring).buffer(0))
        if not g.is_empty:
            g = affinity.scale(g, xfact=sc, yfact=-sc, origin=(0, 0))
            shapes.append(affinity.translate(g, xoff=x + pos.x_offset * sc))
        x += pos.x_advance * sc
    geom = unary_union(shapes) if shapes else Polygon()
    if embolden and not geom.is_empty:
        geom = geom.buffer(embolden * size, resolution=8, join_style=1)
    _cache[key] = geom
    return geom

def text_path(text, size, kind, x, baseline, fill=INK, opacity=None, align="left"):
    """Place text with its baseline at y=baseline (font coordinates put the baseline at 0)."""
    g = text_geom(text, size, kind)
    w = measure(text, size, kind)
    dx = x if align == "left" else (x - w / 2 if align == "center" else x - w)
    g = affinity.translate(g, xoff=dx, yoff=baseline)
    op = f' fill-opacity="{opacity}"' if opacity is not None else ""
    return f'<path fill="{fill}"{op} d="{bl.to_path(g)}"/>', w

def wrap(text, size, kind, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if cur and measure(t, size, kind) > width:
            lines.append(cur); cur = w
        else:
            cur = t
    if cur:
        lines.append(cur)
    # No one-word last lines.
    if len(lines) >= 2 and len(lines[-1].split()) == 1 and len(lines[-2].split()) >= 3:
        prev = lines[-2].split()
        cand = prev[-1] + " " + lines[-1]
        if measure(cand, size, kind) <= width:
            lines[-2] = " ".join(prev[:-1]); lines[-1] = cand
    return lines

def card(x, y, w, h, fill=WHITE, r=22, shadow=7, stroke=3):
    s = []
    s.append(f'<rect x="{x + shadow}" y="{y + shadow}" width="{w}" height="{h}" rx="{r}" fill="{INK}"/>')
    s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{INK}" stroke-width="{stroke}"/>')
    return "\n".join(s)

def chip(label, x, y, fill, size=19):
    w = measure(label, size, "bold") + 28
    h = size * 1.75
    t, _ = text_path(label, size, "bold", x + 14, y + h * 0.69)
    return f'<rect x="{x}" y="{y}" width="{w:.1f}" height="{h:.1f}" rx="{h/2:.1f}" fill="{fill}" stroke="{INK}" stroke-width="2.5"/>\n{t}', h

MARK = bl.mark_geometry(False)
MB = MARK["outer"].bounds

def mark_at(x, y, height):
    sc = height / (MB[3] - MB[1])
    return f'<g transform="translate({x:.1f} {y:.1f}) scale({sc:.4f}) translate({-MB[0]:.1f} {-MB[1]:.1f})">{bl.mark_svg_group(MARK)}</g>', (MB[2] - MB[0]) * sc

def header(W, title, subtitle, top=56, margin=64):
    parts = []
    m, mw = mark_at(margin, top, 92)
    parts.append(m)
    tx = margin + mw + 26
    tsize = min(50, 50 * (W - tx - margin) / measure(title, 50, "bold"))
    t, _ = text_path(title, tsize, "bold", tx, top + 50); parts.append(t)
    ssize = min(23, 23 * (W - tx - margin) / measure(subtitle, 23, "regular"))
    s, _ = text_path(subtitle, ssize, "regular", tx, top + 86, opacity=0.72); parts.append(s)
    return "\n".join(parts), top + 92

def save(name, W, H, body, title):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="{title}">\n<title>{title}</title>\n'
           f'<rect width="{W}" height="{H}" fill="{PAPER}"/>\n{body}\n</svg>\n')
    p = os.path.join(OUT, f"{name}.svg")
    open(p, "w").write(svg)
    cairosvg.svg2png(url=p, write_to=os.path.join(OUT, f"{name}.png"), output_width=W * 2, output_height=H * 2)

# ---------------------------------------------------------------- 1. every command
GROUPS = [
    ("Every morning", YEL, [
        ("/briefing", "What's due, what's on fire, and what changed overnight."),
        ("/pulse", "Only what changed since the last brief."),
        ("/week", "The week ahead, collisions included.")]),
    ("Meetings", PINK, [
        ("/prep", "Walk in with the last decision, the open question, and the right doc."),
        ("/debrief", "Paste the transcript. Get notes, decisions, and follow-ups."),
        ("/who", "Who someone is, what they own, and what's open between you."),
        ("/slots", "Meeting times that respect your calendar. You send them.")]),
    ("Follow-ups", YEL, [
        ("/capture", "Any promise, with an owner and a date."),
        ("/triage", "Your inbox, sorted into groups. Nothing gets deleted."),
        ("/close", "What moved, what's open, and tomorrow's first move.")]),
    ("Status", PINK, [
        ("/project-status", "The table you used to rebuild before every one-on-one. One paste."),
        ("/gofer", "The legwork on your plate: what deserves today, and what can wait.")]),
    ("Writing", PINK, [
        ("/draft", "A message in your voice. You hit send."),
        ("/redline", "A skeptic reads it before your exec does."),
        ("/write-epic", "Messy notes in, a clean ticket out.")]),
    ("Thinking", YEL, [
        ("/explain", "Anything, explained like you're new."),
        ("/bro", "Say that again, in plain words."),
        ("/quick", "The short version."),
        ("/grill", "Pokes holes in a plan, starting with your own past decisions."),
        ("/study", "Quizzes you from your own notes."),
        ("/learn", "A 101 on any topic, from your own sources.")]),
    ("Keeping the record", PINK, [
        ("/new-project", "A home for every project."),
        ("/decision", "The decision and the why, so nobody relitigates it."),
        ("/sync-kb", "Files everything in your inbox."),
        ("/kb-lint", "Finds what's gone stale."),
        ("/tidy", "Merges duplicates, fixes fuzzy dates, archives what's done.")]),
    ("Setup", YEL, [
        ("/setup", "Guided setup. Mostly clicking."),
        ("/connect", "Add a tool, or fix one that won't connect.")]),
]

def commands():
    W, margin, gap, cols = 1600, 64, 30, 4
    colw = (W - 2 * margin - (cols - 1) * gap) / cols
    pad, inner = 26, None
    inner = colw - 2 * pad
    head, y0 = header(W, "Everything your intern can do", "Type the command, or just ask in plain words. All 28 are free.")
    parts = [head]
    y = y0 + 44
    for ri, row in enumerate((GROUPS[:4], GROUPS[4:])):
        # measure
        layouts = []
        for name, color, items in row:
            h = pad + 33 + 16
            rows = []
            for cmd, desc in items:
                lines = wrap(desc, 18, "regular", inner)
                rows.append((cmd, lines))
                h += 30 + len(lines) * 25 + 16
            h += pad - 16
            layouts.append((name, color, rows, h))
        rh = max(l[3] for l in layouts)
        for i, (name, color, rows, _) in enumerate(layouts):
            x = margin + i * (colw + gap)
            parts.append(card(x, y, colw, rh))
            c, ch = chip(name, x + pad, y + pad, color)
            parts.append(c)
            cy = y + pad + ch + 22
            for cmd, lines in rows:
                t, _ = text_path(cmd, 25, "bold", x + pad, cy + 20); parts.append(t)
                cy += 32
                for ln in lines:
                    t, _ = text_path(ln, 18, "regular", x + pad, cy + 15, opacity=0.78); parts.append(t)
                    cy += 25
                cy += 16
        if ri == 1:
            x = margin + 3 * (colw + gap)
            note = wrap("Works in Cowork, Claude Code, and claude.ai. Company locked down? There's a no-install kit.", 17, "medium", inner)
            ny = y + rh - pad - len(note) * 24 + 14
            for ln in note:
                t, _ = text_path(ln, 17, "medium", x + pad, ny, opacity=0.6); parts.append(t)
                ny += 24
        y += rh + gap + 8
    f, _ = text_path("The only intern who should be unpaid.", 20, "medium", W - margin, y + 22, opacity=0.6, align="right")
    parts.append(f)
    H = int(y + 56)
    save("commands", W, H, "\n".join(parts), "Every Unpaid Intern command, grouped: every morning, meetings, follow-ups, status, writing, thinking, keeping the record, and setup.")

# ---------------------------------------------------------------- 2. a sample morning brief
BRIEF = [
    ("Needs you", PINK, [
        "Hollis asked twice about the launch date. Want a reply drafted?",
        "Pricing review at 2:00. The open question is annual discounts. The one-pager is in 2-Projects/pricing-refresh.",
    ]),
    ("Waiting on others", YEL, [
        "Security review notes from Sam, 6 business days. Want a nudge drafted?",
    ]),
    ("Due today", YEL, [
        "Send the revised timeline to the launch group.",
    ]),
    ("Tomorrow", PINK, [
        "One-on-one with your manager. Your status table is one command away: /project-status.",
    ]),
    ("New names", YEL, [
        "Nadia and Theo came up in yesterday's planning call. Who are they? Or drop your org chart in 1-Inbox.",
    ]),
]

def brief():
    W, margin = 1200, 64
    head, y0 = header(W, "Your day, sorted", "What /briefing hands you before your first meeting.")
    parts = [head]
    x, y, w = margin, y0 + 44, W - 2 * margin
    pad = 40
    inner = w - 2 * pad - 30
    # measure
    blocks = [(name, color, [wrap(it, 22, "regular", inner) for it in items]) for name, color, items in BRIEF]
    card_index = len(parts)
    m, mw = mark_at(x + pad, y + pad, 50)
    parts.append(m)
    t, _ = text_path("Unpaid Intern", 24, "bold", x + pad + mw + 16, y + pad + 22); parts.append(t)
    t, _ = text_path("/briefing  \u00b7  Tuesday, October 13, 8:30 AM", 18, "regular", x + pad + mw + 16, y + pad + 48, opacity=0.6); parts.append(t)
    cy = y + pad + 64 + 26
    for name, color, lines_all in blocks:
        c, ch = chip(name.upper(), x + pad, cy, color, size=16)
        parts.append(c)
        cy += ch + 14
        for lines in lines_all:
            parts.append(f'<circle cx="{x + pad + 8}" cy="{cy + 13}" r="5" fill="{INK}"/>')
            for ln in lines:
                t, _ = text_path(ln, 22, "regular", x + pad + 30, cy + 21); parts.append(t)
                cy += 32
            cy += 14
        cy += 18
    h = cy - 18 + pad - y
    parts.insert(card_index, card(x, y, w, h))
    H = int(y + h + 64)
    save("sample-brief", W, H, "\n".join(parts), "A sample morning brief from Unpaid Intern, with what needs you, what you're waiting on, what's due today, and tomorrow.")

# ---------------------------------------------------------------- 3. the folder
FOLDERS = [
    ("1-Inbox", PINK, "Drop anything here: transcripts, PDFs, screenshots, exports. Messy is fine."),
    ("2-Projects", YEL, "One folder per project: where it stands, what was decided, and the sources."),
    ("3-Areas", YEL, "The ongoing parts of your job with no end date."),
    ("4-Reference", YEL, "The glossary, the people you work with, and clean notes from meetings and docs."),
    ("5-Archive", WHITE, "Finished projects and filed drops. Nothing is ever deleted."),
    ("Memory", PINK, "Follow-ups, decisions, meetings, and a daily log your intern keeps up to date."),
    ("Setup", WHITE, "Your preferences, what your intern may do, and your connected tools."),
]

def folder_icon(x, y, w, h, fill):
    tab = bl.rrect(x, y, w * 0.45, h * 0.4, 6)
    body = bl.rrect(x, y + h * 0.18, w, h * 0.82, 8)
    shape_ = unary_union([tab, body])
    return f'<path fill="{fill}" stroke="{INK}" stroke-width="3" stroke-linejoin="round" d="{bl.to_path(shape_)}"/>'

def folder():
    W, margin = 1200, 64
    head, y0 = header(W, "Build your second brain", "Plain files you own, laid out the way most second-brain systems are.")
    parts = [head]
    x, y, w = margin, y0 + 44, W - 2 * margin
    pad = 36
    rowh = 78
    namew = 205
    h = pad * 2 + 44 + rowh * len(FOLDERS) - 18
    parts.append(card(x, y, w, h))
    fi = folder_icon(x + pad, y + pad - 6, 40, 31, WHITE)
    t, _ = text_path("Second Brain", 26, "bold", x + pad + 56, y + pad + 20)
    parts += [fi, t]
    cy = y + pad + 44
    for name, color, desc in FOLDERS:
        parts.append(folder_icon(x + pad + 24, cy + 8, 46, 36, color))
        tt, _ = text_path(name, 24, "bold", x + pad + 90, cy + 36); parts.append(tt)
        lines = wrap(desc, 19, "regular", w - 2 * pad - 90 - namew)
        ly = cy + 36 - (len(lines) - 1) * 13
        for ln in lines:
            tt, _ = text_path(ln, 19, "regular", x + pad + 90 + namew, ly, opacity=0.78); parts.append(tt)
            ly += 26
        cy += rowh
    H = int(y + h + 64)
    save("your-folder", W, H, "\n".join(parts), "Build your second brain: one folder with Inbox, Projects, Areas, Reference, Archive, Memory, and Setup.")

# ---------------------------------------------------------------- 4. /who, for people who are new
WHO_ROWS = [
    ("Role", "Director of Pricing on the Revenue team. Reports to Felix Abara."),
    ("Owns", "List prices and discount bands."),
    ("Last talked", "The pricing review, Tuesday, October 6."),
    ("Open", "You owe Hollis the pricing one-pager, due Friday. Hollis owes you the discount model, waiting 4 business days."),
    ("Projects", "Pricing refresh, launch v2."),
    ("Source", "Your org chart screenshot, October 6."),
]

def who():
    W, margin = 1200, 64
    head, y0 = header(W, "Your onboarding buddy is busy. Your intern isn't.", "Ask /who about anyone. Drop in your org chart and it learns who reports to whom.")
    parts = [head]
    x, y, w = margin, y0 + 44, W - 2 * margin
    pad = 40
    card_index = len(parts)
    # the question, as a chat bubble on the right
    q = "/who is Hollis?"
    qw = measure(q, 24, "bold") + 48
    bx = x + w - pad - qw
    parts.append(f'<rect x="{bx:.1f}" y="{y + pad}" width="{qw:.1f}" height="52" rx="26" fill="{PINK}" stroke="{INK}" stroke-width="3"/>')
    t, _ = text_path(q, 24, "bold", bx + 24, y + pad + 35); parts.append(t)
    cy = y + pad + 52 + 30
    mw = 50  # a plain initials avatar: the brain is the intern, not Hollis
    parts.append(f'<circle cx="{x + pad + 25}" cy="{cy + 25}" r="25" fill="{YEL}" stroke="{INK}" stroke-width="3"/>')
    t, _ = text_path("HQ", 20, "bold", x + pad + 25 - measure("HQ", 20, "bold") / 2, cy + 32)
    parts.append(t)
    t, _ = text_path("Hollis Quint", 30, "bold", x + pad + mw + 16, cy + 34); parts.append(t)
    cy += 50 + 26
    labw = 150
    for lab, val in WHO_ROWS:
        lines = wrap(val, 22, "regular", w - 2 * pad - labw)
        t, _ = text_path(lab, 20, "bold", x + pad, cy + 21, opacity=0.6); parts.append(t)
        for ln in lines:
            t, _ = text_path(ln, 22, "regular", x + pad + labw, cy + 21); parts.append(t)
            cy += 32
        cy += 14
    h = cy - y + pad - 14
    parts.insert(card_index, card(x, y, w, h))
    H = int(y + h + 64)
    save("who", W, H, "\n".join(parts), "Asking /who is Hollis? Unpaid Intern answers with their role, who they report to, what they own, the last time you talked, and what's open between you.")

# ---------------------------------------------------------------- 5. the core eight
CORE = [
    ("/briefing", "What needs you today, what you're waiting on, and what's coming tomorrow.", "Start of day"),
    ("/prep", "Walk into any meeting with the last decision and the open question.", "Before a meeting"),
    ("/debrief", "Hand it the transcript or your notes. Get decisions and follow-ups with owners and dates.", "After a meeting"),
    ("/who", "Who someone is, what they own, and what's open between you.", "A name you don't know"),
    ("/capture", "Any promise, yours or theirs, with an owner and a date.", "Anytime"),
    ("/explain", "Any acronym, doc, or engineering note, explained like you're new.", "New jargon"),
    ("/project-status", "Your status table, built from your own records and ready to paste.", "Before your one-on-one"),
    ("/close", "What moved, what's still open, and tomorrow's first move.", "End of day"),
]

def core():
    W, margin, gap, cols = 1600, 64, 28, 4
    colw = (W - 2 * margin - (cols - 1) * gap) / cols
    pad = 26
    inner = colw - 2 * pad
    head, y0 = header(W, "Start with these 8 daily habits", "One for every part of your day. Type the command, or just ask in plain words.")
    parts = [head]
    y = y0 + 44
    for r in range(2):
        row = CORE[r * cols:(r + 1) * cols]
        lays = [(cmd, wrap(desc, 20, "regular", inner), tag) for cmd, desc, tag in row]
        rh = pad + 38 + max(len(l[1]) for l in lays) * 28 + 22 + 34 + pad
        for i, (cmd, lines, tag) in enumerate(lays):
            x = margin + i * (colw + gap)
            parts.append(card(x, y, colw, rh))
            t, _ = text_path(cmd, 30, "bold", x + pad, y + pad + 28); parts.append(t)
            cy = y + pad + 38 + 22
            for ln in lines:
                t, _ = text_path(ln, 20, "regular", x + pad, cy, opacity=0.8); parts.append(t)
                cy += 28
            c, _ = chip(tag, x + pad, y + rh - pad - 33, YEL if r == 0 else PINK, size=17)
            parts.append(c)
        y += rh + gap + 8
    f, _ = text_path("19 more when you want them, like /grill, /gofer, /week, and /draft.", 20, "medium", margin, y + 22, opacity=0.65)
    parts.append(f)
    f2, _ = text_path("The only intern who should be unpaid.", 20, "medium", W - margin, y + 22, opacity=0.65, align="right")
    parts.append(f2)
    H = int(y + 60)
    save("core", W, H, "\n".join(parts), "The eight core Unpaid Intern commands, in the order of a workday: briefing at the start of the day, prep before a meeting, debrief after it, who for a name you don't know, capture anytime, explain for new jargon, project-status before your one-on-one, and close at the end of the day.")

# ---------------------------------------------------------------- 6. the hero: your pile in, finished work out
PILE = [
    ("Transcript", "Pricing sync: “no backfill before Q1”", -3.0),
    ("Email", "Re: launch date?? (Hollis, 2nd ask)", 2.5),
    ("Calendar", "2:00 Pricing review", 2.0),
    ("Jira", "PRICE-142: annual discount tiers", -2.0),
    ("Confluence", "Launch v2 runbook", -2.5),
    ("Google Doc", "Pricing one-pager (draft)", 3.0),
    ("To-do", "chase Sam re: security notes", 1.5),
    ("You", "“okay so… who is Marco?”", -1.5),
]
DESK = [
    ("Morning briefing", "What needs you today, and what can wait."),
    ("Meeting prep", "The last decision and the open question."),
    ("Status update", "Ready to paste into your one-on-one notes."),
    ("Requirements", "Messy notes in, a clean ticket out."),
    ("Email replies", "Drafted in your voice. You hit send."),
    ("Follow-ups and statuses", "Owners and dates, kept current."),
]

def hero():
    W, margin = 1600, 64
    head, y0 = header(W, "Hand it to your intern. Get back to work.",
                      "Connect your tools or paste things in. Either way, it turns what you have into what you need next.")
    parts = [head]
    y = y0 + 48
    lw, mid = 650, 150
    rw = W - 2 * margin - lw - mid
    # left: the pile, as tilted notes in two columns
    nw, nh, gx, gy = 300, 104, 26, 22
    c, ch = chip("What you already have", margin, y, WHITE, size=19)
    parts.append(c)
    ny0 = y + ch + 26
    fills = [PINK, YEL, WHITE, YEL, WHITE, PINK, YEL, PINK]
    for i, (kind, snip, rot) in enumerate(PILE):
        col, row = i % 2, i // 2
        nx = margin + 8 + col * (nw + gx) + (12 if row % 2 else 0)
        ny = ny0 + row * (nh + gy)
        cx, cy = nx + nw / 2, ny + nh / 2
        g = [card(nx, ny, nw, nh, fill=fills[i], r=14, shadow=5, stroke=2.5)]
        t, _ = text_path(kind.upper(), 15, "bold", nx + 20, ny + 34, opacity=0.62); g.append(t)
        lines = wrap(snip, 19, "medium", nw - 40)
        ly = ny + 64
        for ln in lines[:2]:
            t, _ = text_path(ln, 19, "medium", nx + 20, ly); g.append(t)
            ly += 26
        parts.append(f'<g transform="rotate({rot} {cx:.1f} {cy:.1f})">' + "\n".join(g) + "</g>")
    left_bottom = ny0 + 4 * (nh + gy) - gy
    # right: what lands on your desk
    rx = margin + lw + mid
    pad = 34
    rows = [(name, wrap(desc, 20, "regular", rw - 2 * pad - 30)) for name, desc in DESK]
    rh_needed = pad + 40 + 24 + sum(30 + len(l) * 28 + 18 for _, l in rows) + pad - 18
    top = y
    h = max(rh_needed, left_bottom - top)
    parts.append(card(rx, top, rw, h))
    c, ch = chip("What lands on your desk", rx + pad, top + pad, PINK, size=19)
    parts.append(c)
    cy = top + pad + ch + 24
    for name, lines in rows:
        parts.append(f'<circle cx="{rx + pad + 8:.1f}" cy="{cy + 12:.1f}" r="6" fill="{INK}"/>')
        t, _ = text_path(name, 23, "bold", rx + pad + 28, cy + 20); parts.append(t)
        cy += 30
        for ln in lines:
            t, _ = text_path(ln, 20, "regular", rx + pad + 28, cy + 18, opacity=0.78); parts.append(t)
            cy += 28
        cy += 18
    # middle: the intern, and an arrow
    mx = margin + lw + mid / 2
    my = top + h / 2
    m, mw = mark_at(mx - 52, my - 70, 76)
    parts.append(m)
    parts.append(f'<path d="M{mx - 26:.1f} {my + 26:.1f} L{mx + 30:.1f} {my + 26:.1f} M{mx + 14:.1f} {my + 10:.1f} L{mx + 32:.1f} {my + 26:.1f} L{mx + 14:.1f} {my + 42:.1f}" fill="none" stroke="{INK}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>')
    H = int(max(top + h, left_bottom) + 64)
    save("hero", W, H, "\n".join(parts),
         "Hand it to your intern, get back to work. On the left, what you already have: a meeting transcript, email, calendar, a Jira ticket, a Confluence page, a Google Doc, a to-do list, and your own brain dump. On the right, what Unpaid Intern turns it into: a morning briefing, meeting prep, a status update, requirements, email replies drafted for you to send, and follow-ups and statuses kept current.")

# ---------------------------------------------------------------- 7. the inbox: if you can save it, your intern can read it
DROPS = [
    ("standup-10-06.txt", "The meeting transcript"),
    ("vendor-terms.pdf", "The PDF legal sent"),
    ("thread.png", "A screenshot of a Slack thread"),
    ("q4-plan.pptx", "The deck someone shared five minutes before the meeting"),
]
FILED = [
    ("Launch v2", "Two decisions and the new date, with the source noted."),
    ("Follow-ups", "Three new ones, each with an owner and a date."),
    ("Glossary", "Two acronyms it wants you to confirm."),
    ("People", "Asks who Dana Kim is. Never guesses."),
    ("5-Archive", "Your originals, untouched. Nothing is deleted."),
]

def file_icon(x, y, w, h, fill):
    ear = w * 0.32
    d = f"M{x} {y + 5} Q{x} {y} {x + 5} {y} L{x + w - ear} {y} L{x + w} {y + ear} L{x + w} {y + h - 5} Q{x + w} {y + h} {x + w - 5} {y + h} L{x + 5} {y + h} Q{x} {y + h} {x} {y + h - 5} Z"
    fold = f"M{x + w - ear} {y} L{x + w - ear} {y + ear} L{x + w} {y + ear}"
    return (f'<path d="{d}" fill="{fill}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'
            f'<path d="{fold}" fill="none" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>')

def inbox():
    W, margin = 1200, 64
    head, y0 = header(W, "If you can save it, your intern can read it", "Put the inbox on your desktop. Drop things in all day. Then say \u201cfile my inbox.\u201d")
    parts = [head]
    top = y0 + 44
    lw, mid = 420, 196
    rw = W - 2 * margin - lw - mid
    pad = 34
    # left: what you dropped in
    lx = margin
    left = []
    c, ch = chip("1-Inbox", lx + pad, top + pad, PINK, size=19)
    left.append(c)
    cy = top + pad + ch + 26
    for name, desc in DROPS:
        left.append(file_icon(lx + pad, cy, 30, 38, WHITE))
        t, _ = text_path(name, 21, "bold", lx + pad + 46, cy + 17); left.append(t)
        lines = wrap(desc, 18, "regular", lw - 2 * pad - 46)
        ly = cy + 42
        for ln in lines:
            t, _ = text_path(ln, 18, "regular", lx + pad + 46, ly, opacity=0.75); left.append(t)
            ly += 25
        cy = max(cy + 56, ly) + 14
    lh = cy - top + pad - 14
    # right: where it went
    rx = margin + lw + mid
    right = []
    c, ch = chip("Where it went", rx + pad, top + pad, YEL, size=19)
    right.append(c)
    cy = top + pad + ch + 26
    for name, desc in FILED:
        right.append(f'<circle cx="{rx + pad + 8:.1f}" cy="{cy + 12:.1f}" r="6" fill="{INK}"/>')
        t, _ = text_path(name, 21, "bold", rx + pad + 28, cy + 19); right.append(t)
        cy += 30
        for ln in wrap(desc, 18, "regular", rw - 2 * pad - 28):
            t, _ = text_path(ln, 18, "regular", rx + pad + 28, cy + 16, opacity=0.78); right.append(t)
            cy += 25
        cy += 16
    rh = cy - top + pad - 16
    h = max(lh, rh)
    parts.append(card(lx, top, lw, h)); parts += left
    parts.append(card(rx, top, rw, h)); parts += right
    # middle: the ask, and an arrow
    mx = margin + lw + mid / 2
    my = top + h / 2
    q = "file my inbox"
    qs = 17
    qw = measure(q, qs, "bold") + 28
    parts.append(f'<rect x="{mx - qw / 2:.1f}" y="{my - 62:.1f}" width="{qw:.1f}" height="38" rx="19" fill="{PINK}" stroke="{INK}" stroke-width="2.5"/>')
    t, _ = text_path(q, qs, "bold", mx - qw / 2 + 14, my - 37); parts.append(t)
    parts.append(f'<path d="M{mx - 30:.1f} {my + 6:.1f} L{mx + 30:.1f} {my + 6:.1f} M{mx + 14:.1f} {my - 10:.1f} L{mx + 32:.1f} {my + 6:.1f} L{mx + 14:.1f} {my + 22:.1f}" fill="none" stroke="{INK}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>')
    H = int(top + h + 64)
    save("inbox", W, H, "\n".join(parts),
         "If you can save it, your intern can read it. Four files dropped in the inbox, a transcript, a PDF from legal, a screenshot of a Slack thread, and a deck, become two decisions on the project page, three follow-ups with owners and dates, two acronyms to confirm, a question about a new name, and the originals moved to the archive untouched.")

if __name__ == "__main__":
    commands(); brief(); folder(); who(); core(); hero(); inbox(); print("built")
