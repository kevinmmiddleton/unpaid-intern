"""Builds the Unpaid Intern logo set as pure filled paths (no fonts, no strokes)."""
import math, os
import cairosvg, uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from shapely.geometry import Point, LineString, Polygon, MultiPolygon, box
from shapely.ops import unary_union
from shapely import affinity

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "..", "assets", "brand"))


def font_file(name):
    """Poppins (SIL Open Font License) from POPPINS_DIR, tools/brand/fonts, or the system font folder."""
    for d in (os.environ.get("POPPINS_DIR", ""), os.path.join(HERE, "fonts"), "/usr/share/fonts/truetype/google-fonts"):
        if d and os.path.isfile(os.path.join(d, name)):
            return os.path.join(d, name)
    raise SystemExit(f"Can't find {name}. Download Poppins from fonts.google.com into tools/brand/fonts/ (see tools/brand/README.md).")

INK, PINK, PAPER, YEL = "#16131F", "#FF8FC1", "#FFF8EF", "#FFE14D"
FONT = font_file("Poppins-Bold.ttf")
RES = 48

# ---------------------------------------------------------------- geometry helpers
def bez3(p0, p1, p2, p3, n=24):
    pts = []
    for i in range(n + 1):
        t = i / n
        x = (1-t)**3*p0[0] + 3*(1-t)**2*t*p1[0] + 3*(1-t)*t**2*p2[0] + t**3*p3[0]
        y = (1-t)**3*p0[1] + 3*(1-t)**2*t*p1[1] + 3*(1-t)*t**2*p2[1] + t**3*p3[1]
        pts.append((x, y))
    return pts

def bez2(p0, p1, p2, n=20):
    return [((1-t)**2*p0[0] + 2*(1-t)*t*p1[0] + t**2*p2[0], (1-t)**2*p0[1] + 2*(1-t)*t*p1[1] + t**2*p2[1]) for t in (i/n for i in range(n+1))]

def wave(start, c1, c2, end, s2=None, end2=None):
    """A cubic, optionally followed by a smooth cubic (S) like the draft's fold lines."""
    pts = bez3(start, c1, c2, end)
    if s2:
        r1 = (2*end[0]-c2[0], 2*end[1]-c2[1])
        pts += bez3(end, r1, s2, end2)[1:]
    return pts

def stroke(points, width):
    return LineString(points).buffer(width/2, resolution=RES, cap_style=1, join_style=1)

def rrect(x, y, w, h, r):
    return box(x + r, y + r, x + w - r, y + h - r).buffer(r, resolution=RES)

def to_path(geom, prec=1, tol=0.08):
    if geom.is_empty:
        return ""
    geom = geom.simplify(tol, preserve_topology=True)
    polys = geom.geoms if isinstance(geom, MultiPolygon) else [geom]
    parts = []
    for p in polys:
        for ring in [p.exterior, *p.interiors]:
            c = list(ring.coords)
            parts.append("M" + " L".join(f"{x:.{prec}f} {y:.{prec}f}" for x, y in c[:-1]) + "Z")
    return " ".join(parts)

# ---------------------------------------------------------------- the mark
LOBES = [(96, 78, 38), (68, 112, 34), (92, 142, 32), (110, 110, 36)]
LOBES += [(256 - x, y, r) for x, y, r in LOBES]

FOLDS_FULL = [
    wave((128, 42), (122, 54), (134, 64), (128, 78)),
    wave((62, 72), (68, 62), (78, 62), (82, 70), (94, 78), (100, 66)),
    wave((42, 136), (48, 128), (56, 128), (60, 136)),
    wave((76, 162), (82, 154), (90, 154), (94, 162), (104, 170), (110, 160)),
    wave((98, 46), (104, 42), (110, 46), (110, 54)),
    wave((152, 70), (158, 60), (168, 60), (172, 68), (184, 76), (192, 64)),
    wave((196, 132), (202, 124), (210, 124), (214, 132)),
    wave((146, 160), (152, 152), (160, 152), (164, 160), (174, 168), (180, 158)),
    wave((150, 48), (154, 44), (160, 46), (162, 52)),
]
FOLDS_SMALL = [FOLDS_FULL[0], FOLDS_FULL[1], FOLDS_FULL[3], FOLDS_FULL[5], FOLDS_FULL[7]]

def mark_geometry(small=False):
    o = 9 if small else 7
    fw = 8 if small else 6
    gw = 10 if small else 8
    fill = unary_union([Point(x, y).buffer(r, resolution=RES) for x, y, r in LOBES])
    outer = unary_union([Point(x, y).buffer(r + o, resolution=RES) for x, y, r in LOBES])
    folds = unary_union([stroke(f, fw) for f in (FOLDS_SMALL if small else FOLDS_FULL)]).intersection(fill)
    lenses = [(68, 96, 50, 38), (138, 96, 50, 38)]
    lens_fill = unary_union([rrect(x + gw/2, y + gw/2, w - gw, h - gw, 14 - gw/2) for x, y, w, h in lenses])
    frames = unary_union([rrect(x - gw/2, y - gw/2, w + gw, h + gw, 14 + gw/2).difference(rrect(x + gw/2, y + gw/2, w - gw, h - gw, 14 - gw/2)) for x, y, w, h in lenses])
    bridge = stroke(bez2((118, 112), (128, 103), (138, 112)), gw)
    temples = unary_union([stroke([(68, 112), (38, 102)], gw), stroke([(188, 112), (218, 102)], gw)])
    glasses = unary_union([frames, bridge, temples])
    glints = unary_union([stroke([(80, 125), (91, 107)], 5), stroke([(150, 125), (161, 107)], 5)])
    if small:
        glints = Polygon()
    folds = folds.difference(lens_fill.buffer(gw/2))
    ring = outer.difference(fill)
    return dict(outer=outer, fill=fill, ring=ring, folds=folds, lens_fill=lens_fill, glasses=glasses, glints=glints)

def mark_svg_group(g, mode="color"):
    if mode == "color":
        return "\n".join([
            f'<path fill="{INK}" d="{to_path(g["outer"])}"/>',
            f'<path fill="{PINK}" d="{to_path(g["fill"])}"/>',
            f'<path fill="{INK}" d="{to_path(g["folds"])}"/>',
            f'<path fill="{PAPER}" d="{to_path(g["lens_fill"])}"/>',
            f'<path fill="{PINK}" d="{to_path(g["glints"].intersection(g["lens_fill"]))}"/>' if not g["glints"].is_empty else "",
            f'<path fill="{INK}" d="{to_path(g["glasses"])}"/>',
        ])
    color = INK if mode == "ink" else PAPER
    one = unary_union([g["ring"], g["folds"], g["glasses"]])
    return f'<path fill="{color}" d="{to_path(one)}"/>'

# ---------------------------------------------------------------- the wordmark
class PolyPen(BasePen):
    def __init__(self, glyphset):
        super().__init__(glyphset); self.rings = []; self.cur = []
    def _moveTo(self, p): self.cur = [p]
    def _lineTo(self, p): self.cur.append(p)
    def _curveToOne(self, p1, p2, p3): self.cur += bez3(self.cur[-1], p1, p2, p3, 12)[1:]
    def _qCurveToOne(self, p1, p2): self.cur += bez2(self.cur[-1], p1, p2, 10)[1:]
    def _closePath(self):
        if len(self.cur) > 2: self.rings.append(self.cur)
        self.cur = []
    _endPath = _closePath

FONT_TT = TTFont(FONT)
GS = FONT_TT.getGlyphSet()
UPM = FONT_TT["head"].unitsPerEm
with open(FONT, "rb") as fh:
    HB_FACE = hb.Face(fh.read())
HB_FONT = hb.Font(HB_FACE)

def word_geometry(text, size, tracking=-0.02, embolden=0.010):
    buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
    hb.shape(HB_FONT, buf, {"kern": True})
    order = FONT_TT.getGlyphOrder()
    scale = size / UPM
    x = 0.0; shapes = []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        name = order[info.codepoint]
        pen = PolyPen(GS); GS[name].draw(pen)
        geom = Polygon()
        for ring in pen.rings:
            if len(ring) < 3: continue
            pg = Polygon(ring).buffer(0)
            geom = geom.symmetric_difference(pg)
        geom = affinity.scale(geom, xfact=scale, yfact=-scale, origin=(0, 0))
        geom = affinity.translate(geom, xoff=x + pos.x_offset * scale, yoff=0)
        shapes.append(geom)
        x += pos.x_advance * scale + tracking * size
    word = unary_union(shapes)
    # Embolden and round the corners a touch so it isn't stock Poppins.
    word = word.buffer(embolden * size, resolution=12, join_style=1).simplify(0.05)
    return word

def place(geom, x, y):
    minx, miny, maxx, maxy = geom.bounds
    return affinity.translate(geom, xoff=x - minx, yoff=y - maxy)  # y = baseline-ish bottom of bounds

# ---------------------------------------------------------------- compose files
def svg(view, body, title, bg=None):
    w, h = view[2], view[3]
    rect = f'<rect x="{view[0]}" y="{view[1]}" width="{w}" height="{h}" fill="{bg}"/>' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{" ".join(f"{v:g}" for v in view)}" role="img" aria-label="{title}">\n'
            f"<title>{title}</title>\n{rect}\n{body}\n</svg>\n")

def bounds_of(*geoms):
    u = unary_union([g for g in geoms if not g.is_empty])
    return u.bounds

def write(name, text):
    with open(os.path.join(OUT, name), "w") as fh:
        fh.write(text)

def build():
    full, small = mark_geometry(False), mark_geometry(True)
    mb = full["outer"].bounds  # mark bounds
    pad = 8
    mview = (mb[0] - pad, mb[1] - pad, mb[2] - mb[0] + 2 * pad, mb[3] - mb[1] + 2 * pad)
    write("mark.svg", svg(mview, f'<g id="mark">{mark_svg_group(full)}</g>', "Unpaid Intern"))
    write("mark-ink.svg", svg(mview, mark_svg_group(full, "ink"), "Unpaid Intern"))
    write("mark-paper.svg", svg(mview, mark_svg_group(full, "paper"), "Unpaid Intern", bg=INK))

    # words
    unpaid = word_geometry("unpaid", 52)
    intern = word_geometry("intern", 96, tracking=-0.025)
    # stacked wordmark: "unpaid" above "intern", left-aligned
    ib = intern.bounds; ub = unpaid.bounds
    intern_p = affinity.translate(intern, -ib[0], -ib[1] + 74)
    unpaid_p = affinity.translate(unpaid, -ub[0] + 6, -ub[1] + 6)
    upb = unpaid_p.bounds
    swipe = affinity.rotate(rrect(upb[0] - 12, upb[1] - 4, (upb[2] - upb[0]) + 24, (upb[3] - upb[1]) + 10, 11), -2, origin="center")
    wm_body = f'<path fill="{YEL}" d="{to_path(swipe)}"/>\n<path fill="{INK}" d="{to_path(unary_union([unpaid_p, intern_p]))}"/>'
    wb = bounds_of(swipe, unpaid_p, intern_p)
    wview = (wb[0] - 6, wb[1] - 6, wb[2] - wb[0] + 12, wb[3] - wb[1] + 12)
    write("wordmark-stacked.svg", svg(wview, wm_body, "Unpaid Intern"))

    # single line: "unpaid intern"
    line_un = word_geometry("unpaid", 64)
    line_in = word_geometry("intern", 64)
    lub = line_un.bounds
    line_un = affinity.translate(line_un, -lub[0], -lub[1])
    lub = line_un.bounds
    lib = line_in.bounds
    gap = 64 * 0.28
    # align on the x-height: both words share a baseline because they come from the same size
    line_in = affinity.translate(line_in, lub[2] + gap - lib[0], -lib[1] + (lub[1] - 0))
    # baseline align: compare bottoms of 'n' rather than descender 'p'; use the 'i' tops instead
    sw = affinity.rotate(rrect(-10, lub[1] - 2, lub[2] + 20, (lub[3] - lub[1]) * 0.86, 12), -2, origin="center")
    line_body = f'<path fill="{YEL}" d="{to_path(sw)}"/>\n<path fill="{INK}" d="{to_path(unary_union([line_un, line_in]))}"/>'
    lb = bounds_of(sw, line_un, line_in)
    write("wordmark-line.svg", svg((lb[0] - 6, lb[1] - 6, lb[2] - lb[0] + 12, lb[3] - lb[1] + 12), line_body, "Unpaid Intern"))

    # horizontal lockup: mark left, stacked wordmark right, vertically centered
    mark_h = mb[3] - mb[1]
    wm_h = wb[3] - wb[1]
    s = (mark_h * 0.86) / wm_h
    gap = 34
    def wm_group(dx, dy, sc):
        return f'<g transform="translate({dx:.2f} {dy:.2f}) scale({sc:.4f}) translate({-wb[0]:.2f} {-wb[1]:.2f})">{wm_body}</g>'
    wx = mb[2] + gap
    wy = mb[1] + (mark_h - wm_h * s) / 2
    lock_body = f'<g id="mark">{mark_svg_group(full)}</g>\n<g id="wordmark">{wm_group(wx, wy, s)}</g>'
    lview = (mb[0] - 16, mb[1] - 16, (wx + (wb[2] - wb[0]) * s) - mb[0] + 32, mark_h + 32)
    write("lockup-horizontal.svg", svg(lview, lock_body, "Unpaid Intern"))
    write("lockup-horizontal-on-paper.svg", svg(lview, lock_body, "Unpaid Intern", bg=PAPER))

    # stacked lockup: mark above, wordmark centered below
    mark_w = mb[2] - mb[0]
    s2 = (mark_w * 1.05) / (wb[2] - wb[0])
    wx2 = mb[0] + (mark_w - (wb[2] - wb[0]) * s2) / 2
    wy2 = mb[3] + 26
    st_body = f'<g id="mark">{mark_svg_group(full)}</g>\n<g id="wordmark">{wm_group(wx2, wy2, s2)}</g>'
    sview = (mb[0] - 24, mb[1] - 24, mark_w + 48, (wy2 + wm_h * s2) - mb[1] + 48)
    write("lockup-stacked.svg", svg(sview, st_body, "Unpaid Intern"))

    # app icon and favicon
    def icon(g, size=512, radius=112, frac=0.84):
        b = g["outer"].bounds; w = b[2] - b[0]; h = b[3] - b[1]
        sc = size * frac / w
        tx = (size - w * sc) / 2 - b[0] * sc
        ty = (size - h * sc) / 2 - b[1] * sc + size * 0.01
        return (f'<rect width="{size}" height="{size}" rx="{radius}" fill="{YEL}"/>\n'
                f'<g transform="translate({tx:.2f} {ty:.2f}) scale({sc:.4f})">{mark_svg_group(g)}</g>')
    write("app-icon.svg", svg((0, 0, 512, 512), icon(full), "Unpaid Intern"))
    write("favicon.svg", svg((0, 0, 512, 512), icon(small, frac=0.9, radius=96), "Unpaid Intern"))

    # banners: the logo and one plain line under it, in every size people need
    TAG = "A second brain for work."
    lock_w0 = (wx + (wb[2] - wb[0]) * s) - mb[0]
    st_w0, st_h0 = mark_w * 1.05, (wy2 + wm_h * s2) - mb[1]

    def banner(fname, W, H, layout, lock_h=None, lock_w=None, tag_size=None, sub_size=None, sub_lines=None):
        parts = []
        if layout == "horizontal":
            sc = (lock_h / mark_h) if lock_h else (lock_w / lock_w0)
            LW, LH = lock_w0 * sc, mark_h * sc
            body, ox, oy = lock_body, mb[0], mb[1]
        else:
            sc = (lock_h / st_h0) if lock_h else (lock_w / st_w0)
            LW, LH = st_w0 * sc, st_h0 * sc
            body, ox, oy = st_body, mb[0] - (st_w0 - mark_w) / 2, mb[1]
        tag = word_geometry(TAG, tag_size, tracking=-0.01, embolden=0.0)
        tb = tag.bounds
        lines = sub_lines or []
        subs = [word_geometry(t, sub_size, tracking=0, embolden=0.0) for t in lines]
        line_h = (sub_size or 0) * 1.45
        sub_h = (line_h * (len(subs) - 1) + sub_size * 0.95) if subs else 0
        g1, g2 = LH * (0.27 if layout == "horizontal" else 0.14), (tag_size * 0.75 if subs else 0)
        block_h = LH + g1 + (tb[3] - tb[1]) + g2 + sub_h
        top = (H - block_h) / 2
        lx = (W - LW) / 2
        parts.append(f'<g transform="translate({lx:.2f} {top:.2f}) scale({sc:.4f}) translate({-ox:.2f} {-oy:.2f})">{body}</g>')
        ty = top + LH + g1
        tag_p = affinity.translate(tag, (W - (tb[2] - tb[0])) / 2 - tb[0], ty - tb[1])
        sy = ty + (tb[3] - tb[1]) + g2
        parts.append(f'<path fill="{INK}" d="{to_path(tag_p)}"/>')
        if subs:
            # Align every line on a shared baseline grid using the font's cap height, not each line's bounds.
            ref = word_geometry("H", sub_size, embolden=0.0).bounds
            placed = []
            for i, g in enumerate(subs):
                gb = g.bounds
                placed.append(affinity.translate(g, (W - (gb[2] - gb[0])) / 2 - gb[0], sy + i * line_h - ref[1]))
            parts.append(f'<path fill="{INK}" fill-opacity="0.7" d="{to_path(unary_union(placed))}"/>')
        write(fname, svg((0, 0, W, H), "\n".join(parts), "Unpaid Intern: a second brain for work.", bg=PAPER))

    os.makedirs(os.path.join(OUT, "banners"), exist_ok=True)
    banner("social-card.svg", 1200, 630, "horizontal", lock_h=320, tag_size=46)
    banner("banners/link-preview-1200x630.svg", 1200, 630, "horizontal", lock_h=320, tag_size=46)
    banner("banners/github-social-1280x640.svg", 1280, 640, "horizontal", lock_h=320, tag_size=47)
    banner("banners/wide-1600x900.svg", 1600, 900, "horizontal", lock_w=900, tag_size=60)
    banner("banners/square-1080x1080.svg", 1080, 1080, "stacked", lock_h=560, tag_size=68)
    banner("banners/portrait-1080x1350.svg", 1080, 1350, "stacked", lock_h=720, tag_size=72)

    # PNG exports
    png = os.path.join(OUT, "png"); os.makedirs(png, exist_ok=True)
    for n in (1024, 512, 180):
        cairosvg.svg2png(url=os.path.join(OUT, "app-icon.svg"), write_to=os.path.join(png, f"app-icon-{n}.png"), output_width=n, output_height=n)
    for n in (64, 32, 16):
        cairosvg.svg2png(url=os.path.join(OUT, "favicon.svg"), write_to=os.path.join(png, f"favicon-{n}.png"), output_width=n, output_height=n)
    cairosvg.svg2png(url=os.path.join(OUT, "lockup-horizontal-on-paper.svg"), write_to=os.path.join(png, "lockup-horizontal.png"), output_width=1600)
    cairosvg.svg2png(url=os.path.join(OUT, "lockup-stacked.svg"), write_to=os.path.join(png, "lockup-stacked.png"), output_width=800)
    cairosvg.svg2png(url=os.path.join(OUT, "mark.svg"), write_to=os.path.join(png, "mark-1024.png"), output_width=1024)
    cairosvg.svg2png(url=os.path.join(OUT, "social-card.svg"), write_to=os.path.join(png, "social-card.png"), output_width=1200, output_height=630)
    bdir = os.path.join(OUT, "banners")
    for f in sorted(os.listdir(bdir)):
        if f.endswith(".svg"):
            w, h = (int(v) for v in f.rsplit("-", 1)[1][:-4].split("x"))
            stem = f[:-4]
            cairosvg.svg2png(url=os.path.join(bdir, f), write_to=os.path.join(bdir, f"{stem}.png"), output_width=w, output_height=h)
            cairosvg.svg2png(url=os.path.join(bdir, f), write_to=os.path.join(bdir, f"{stem}@2x.png"), output_width=w * 2, output_height=h * 2)
    print("built")

if __name__ == "__main__":
    build()
