"""By Design With Joe: coloured-pencil illustration pages (owner, 2026-11-24). Toolkit: pencil.py.

Each function draws one full-frame page on composition `c` between t0 and t1. Beats are anchored to the narration
(`a:` phrase or seconds after the page starts) and the page plays through to its end state (never cut inside one).

Colour meanings stay fixed through an episode (set per episode in the edit's `colors:` where needed);
defaults: graphite = axes and notes, blue = ships/sea, red = limits and warnings, green = money saved / good,
orange = America, violet = Europe, teal = Asia.
"""
from __future__ import annotations

from channels.by_design_with_joe.pencil import Sheet, text_width


def _at(c, x, base):
    """Anchor: number = seconds after base; "phrase" = when it is spoken (searching from base)."""
    return base + float(x) if isinstance(x, (int, float)) else c.t(x, base, 0.1)


def p_bars(c, s, t0, t1):
    """Pencil bar chart, bar by bar, each coloured in from the axis up.

    s.title, s.unit, s.max, s.items: [{label, value, text, color, a, note}], s.ring: index to circle at s.ring_at."""
    sh = Sheet(c, t0, t1, seed=s.get("seed", 3))
    items = s["items"]
    n = len(items)
    X0, X1, Y0, Y1 = 330, 1590, 870, 300
    vmax = s.get("max") or max(it["value"] for it in items) * 1.12
    slot = (X1 - X0) / n
    bw = min(250, slot * 0.52)
    ta = t0 + 0.25
    if s.get("title"):
        sh.text(s["title"], 160, 170, "graphite", ta, size=78, weight=700)
        ta += 0.9
    sh.line([(X0 - 50, Y0), (X1 + 40, Y0)], "graphite", ta, 0.7, w=4)
    if s.get("unit"):
        sh.text(s["unit"], X1 + 40, Y0 + 70, "grey", ta + 0.5, size=40, weight=500, anchor="end")
    for k, it in enumerate(items):
        tb = _at(c, it["a"], t0) if "a" in it else ta + 1.0 + 1.4 * k
        h = (Y0 - Y1) * it["value"] / vmax
        x = X0 + slot * k + (slot - bw) / 2
        color = it.get("color", "blue")
        dur = max(0.6, min(1.6, h / 380))
        sh.lines([[(x, Y0), (x, Y0 - h)], [(x, Y0 - h), (x + bw, Y0 - h)], [(x + bw, Y0 - h), (x + bw, Y0)]], color, tb, 0.7, w=4.2)
        sh.hatch([(x, Y0), (x, Y0 - h), (x + bw, Y0 - h), (x + bw, Y0)], color, tb + 0.72, dur, "up")
        sh.text(it.get("text", str(it["value"])), x + bw / 2, Y0 - h - 28, color, tb + 0.75 + dur, size=72, weight=700, anchor="middle")
        sh.text(it["label"], x + bw / 2, Y0 + 72, "graphite", tb + 0.2, size=50, weight=600, anchor="middle")
        if it.get("note"):
            sh.text(it["note"], x + bw / 2, Y0 + 124, "grey", tb + 0.5, size=36, weight=500, anchor="middle")
    if "ring" in s:
        k = s["ring"]
        it = items[k]
        h = (Y0 - Y1) * it["value"] / vmax
        x = X0 + slot * k + (slot - bw) / 2
        tr = _at(c, s["ring_at"], t0)
        sh.ring(x + bw / 2, Y0 - h - 50, bw * 0.75, 60, "red", tr)
    sh.finish()


def p_sum(c, s, t0, t1):
    """Handwritten maths on paper, line by line, like working it out on a notepad.

    s.rows: [{t: "$500 ÷ 1,000 =", r: "50¢", color, rcolor, a, ra, note}], s.title, s.box: index of the result to box,
    s.strike: [{row, a}] to cross a row's result out (e.g. a deal that stops being good)."""
    sh = Sheet(c, t0, t1, seed=s.get("seed", 5))
    rows = s["rows"]
    X, Y, LH = s.get("x", 260), s.get("y", 330), s.get("lh", 150)
    size = s.get("size", 84)
    ta = t0 + 0.2
    if s.get("title"):
        tid, (l, b, w) = sh.text(s["title"], X, 190, "graphite", ta, size=70, weight=700)
        sh.underline(l - 6, l + w + 10, 210, "graphite", ta + 0.9)
    res = {}
    for k, r in enumerate(rows):
        y = Y + LH * k
        tr = _at(c, r["a"], t0) if "a" in r else ta + 1.0 + 2.0 * k
        _, (l, b, w) = sh.text(r["t"], X, y, r.get("color", "graphite"), tr, size=size, weight=600)
        if r.get("r"):
            trr = _at(c, r["ra"], t0) if "ra" in r else tr + 0.15 + 0.055 * len(r["t"]) + 0.4
            xr = X + w + 30
            _, box = sh.text(r["r"], xr, y, r.get("rcolor", "blue"), trr, size=size + 6, weight=700)
            res[k] = (box, trr)
        if r.get("note"):
            tn = _at(c, r["na"], t0) if "na" in r else tr + 1.2
            sh.text(r["note"], s.get("note_x", 1380), y, r.get("ncolor", "grey"), tn, size=54, weight=500, rot=-2)
    for b in s.get("box", []):
        k, at = (b, None) if isinstance(b, int) else (b["row"], b.get("a"))
        (l, base, w), trr = res[k]
        tb = _at(c, at, t0) if at is not None else trr + 0.9
        sh.ring(l + w / 2, base - size * 0.32, w / 2 + 34, size * 0.62, s.get("box_color", "red"), tb)
    for st in s.get("strike", []):
        (l, base, w), _ = res[st["row"]]
        sh.line([(l - 10, base - size * 0.3), (l + w + 10, base - size * 0.36)], "red", _at(c, st["a"], t0), 0.4, w=6)
    sh.finish()


# ---------------------------------------------------------------- maps
import json as _json
import subprocess as _sp
from pathlib import Path as _Path

_GEO = _Path(__file__).resolve().parent / "geo.cjs"


def geo(req: dict) -> dict:
    """Project atlas shapes, points and routes with d3-geo (geo.cjs). Cached per request in build/.fontcache."""
    from pipeline.config import ROOT
    import hashlib
    key = hashlib.sha1(_json.dumps(req, sort_keys=True).encode()).hexdigest()[:16]
    f = ROOT / "build/.fontcache" / f"geo_{key}.json"
    if f.exists():
        return _json.loads(f.read_text())
    out = _sp.run(["node", str(_GEO)], input=_json.dumps(req), capture_output=True, text=True, check=True, cwd=str(ROOT)).stdout
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(out)
    return _json.loads(out)


def p_map(c, s, t0, t1):
    """Pencil map: land in soft graphite (wiped on), then places, routes and notes drawn on cue.

    s.topo/object (default world land-50m), s.borders: {topo, object} faint inner lines (e.g. US states),
    s.projection, s.fit [[lon0,lat0],[lon1,lat1]], s.box [x,y,w,h], s.title,
    s.places: [{name, ll, label, color, a, dx, dy, size, anchor, dot}],
    s.routes: [{legs: [[lon,lat] | "place name", ...], color, a, dur, w, label, lx, ly, la, lcolor, size, arrow}],
    s.notes: [{t, x, y, color, a, size, rot}], s.rings: [{place, r, color, a}]"""
    sh = Sheet(c, t0, t1, seed=s.get("seed", 11), camera=s.get("camera"))
    box = s.get("box", [80, 70, 1760, 940])
    pl = {p["name"]: p["ll"] for p in s.get("places", [])}
    routes = {}
    for k, r in enumerate(s.get("routes", [])):
        routes[str(k)] = [pl[x] if isinstance(x, str) else x for x in r["legs"]]
    req = {"topo": s.get("topo", "world-atlas/land-50m.json"), "object": s.get("object", "land"),
           "projection": s.get("projection", "mercator"), "fit": s.get("fit"), "box": box, "rotate": s.get("rotate"),
           "parallels": s.get("parallels"), "points": pl, "routes": routes, "step": s.get("step", 1.0)}
    g = geo(req)
    land = " ".join(g["shapes"])
    wipe = f"{sh.gid}wipe"
    inner = ""
    if s.get("borders"):
        b = s["borders"]
        gb = geo({**req, "topo": b["topo"], "object": b["object"], "points": {}, "routes": {}})
        inner = (f'<path d="{" ".join(gb["shapes"])}" stroke="#3A3630" stroke-opacity=".2" stroke-width="1.6" fill="none"/>')
    sh.raw(f'<clipPath id="{wipe}"><rect id="{wipe}r" x="0" y="0" width="0" height="1080"/></clipPath>'
           f'<g clip-path="url(#{wipe})"><path d="{land}" fill="#C9B48A" fill-opacity=".22" stroke="#3A3630" stroke-opacity=".55" '
           f'stroke-width="2.4"/>{inner}</g>')
    c.tw(f'tl.to("#{wipe}r",{{attr:{{width:1920}},duration:{s.get("wipe", 1.1):.2f},ease:"sine.inOut"}},{t0 + 0.05:.3f});')
    ta = t0 + 0.4
    if s.get("title"):
        sh.text(s["title"], s.get("title_x", 120), s.get("title_y", 150), "graphite", ta, size=72, weight=700)
    for p in s.get("places", []):
        if p.get("hidden"):
            continue
        x, y = g["points"][p["name"]]
        tp = _at(c, p["a"], t0) if "a" in p else ta + 0.6
        col = p.get("color", "graphite")
        if p.get("dot", True):
            sh.ring(x, y, 9, 9, col, tp, 0.35, w=4.5)
        if p.get("label"):
            sz = p.get("size", 46)
            sh.text(p["label"], x + p.get("dx", 18), y + p.get("dy", -16), col, tp + 0.3, size=sz, weight=600,
                    anchor=p.get("anchor", "start"))
    for k, r in enumerate(s.get("routes", [])):
        pts = [tuple(q) for q in g["routes"][str(k)]]
        tr = _at(c, r["a"], t0) if "a" in r else ta + 1.0 + 1.5 * k
        dur = r.get("dur", 2.0)
        sh.line(pts, r.get("color", "blue"), tr, dur, w=r.get("w", 5.5), amp=0.8)
        if r.get("arrow", True) and len(pts) > 3:
            e, q = pts[-1], pts[-4]
            import math as _m
            dx, dy = e[0] - q[0], e[1] - q[1]
            n = _m.hypot(dx, dy) or 1
            ux, uy = dx / n, dy / n
            hd = 20
            sh.lines([[(e[0] - ux * hd - uy * hd * .6, e[1] - uy * hd + ux * hd * .6), e],
                      [e, (e[0] - ux * hd + uy * hd * .6, e[1] - uy * hd - ux * hd * .6)]], r.get("color", "blue"), tr + dur, 0.25, w=5)
        if r.get("label"):
            sh.text(r["label"], r["lx"], r["ly"], r.get("lcolor", r.get("color", "blue")),
                    _at(c, r["la"], t0) if "la" in r else tr + dur * 0.6, size=r.get("size", 52), weight=700, rot=r.get("rot", 0))
    for rg in s.get("rings", []):
        x, y = g["points"][rg["place"]]
        sh.ring(x, y, rg.get("r", 40), rg.get("r", 40) * 0.8, rg.get("color", "red"), _at(c, rg["a"], t0))
    for n in s.get("notes", []):
        sh.text(n["t"], n["x"], n["y"], n.get("color", "graphite"), _at(c, n["a"], t0), size=n.get("size", 54),
                weight=n.get("weight", 600), rot=n.get("rot", 0), anchor=n.get("anchor", "start"))
    sh.finish()


# ---------------------------------------------------------------- ships and boxes
def _ship_side(sh, x0, x1, deck, color, t, dur, stacks=True, seed=0):
    """A container ship in side view (bow to the right), drawn and coloured in. Returns the time it finishes."""
    L = x1 - x0
    keel, hull_top = deck + L * 0.06, deck
    bow = [(x0 + L * 0.02, hull_top), (x0, hull_top - L * 0.004), (x0 + L * 0.03, keel), (x1 - L * 0.07, keel),
           (x1, hull_top - L * 0.012), (x1 - L * 0.012, hull_top)]
    sh.line(bow + [bow[0]], color, t, dur * 0.35, w=4.6)
    sh.hatch(bow, color, t + dur * 0.33, dur * 0.25, "right", op=0.7, solid=0.3)
    tt = t + dur * 0.6
    if stacks:
        top = deck - L * 0.1
        bx = x0 + L * 0.16          # bridge block near the stern third
        bridge = [(bx, deck), (bx, deck - L * 0.15), (bx + L * 0.035, deck - L * 0.15), (bx + L * 0.035, deck)]
        sh.line(bridge, "graphite", tt, dur * 0.12, w=3.6)
        cols = ["red", "blue", "orange", "green", "teal", "ochre"]
        xs = x0 + L * 0.06
        segs = []
        x = xs
        while x < x1 - L * 0.12:
            if bx - 2 <= x <= bx + L * 0.035:
                x = bx + L * 0.04
                continue
            w = L * 0.05
            segs.append((x, min(x + w, x1 - L * 0.11)))
            x += w + L * 0.006
        per = dur * 0.28 / max(1, len(segs))
        for k, (a, b) in enumerate(segs):
            ct = cols[(k * 7 + seed) % len(cols)]
            sh.hatch([(a, deck), (a, top), (b, top), (b, deck)], ct, tt + dur * 0.12 + per * k, per * 1.6, "up",
                     op=0.6, solid=0.25, pen=(k % 3 == 0), spacing=8)
        tt += dur * 0.4
    return tt


def p_stand(c, s, t0, t1):
    """The ship drawn lying on the water with its length, then stood on end beside the Eiffel Tower.
    s.length_m (400), s.tower_m (330), s.a_len, s.a_stand, s.a_tower."""
    import math
    sh = Sheet(c, t0, t1, seed=s.get("seed", 9))
    Lm, Tm = s.get("length_m", 400), s.get("tower_m", 330)
    G = 1000                                   # ground line
    L = 840                                    # ship length in px
    x0, deck = 520, 560
    x1 = x0 + L
    water = sh.line([(240, deck + L * 0.06), (1700, deck + L * 0.06)], "blue", t0 + 0.15, 0.7, w=3.2, op=0.6)
    sh.raw(f'<g id="{sh.gid}ship">')
    _ship_side(sh, x0, x1, deck, "blue", t0 + 0.5, 2.4)
    sh.raw("</g>")
    ta = _at(c, s.get("a_len", 1.8), t0)
    dim = sh.lines([[(x0, deck + 110), (x1, deck + 110)], [(x0, deck + 92), (x0, deck + 128)], [(x1, deck + 92), (x1, deck + 128)]],
                   "graphite", ta, 0.6, w=3)
    lid, _ = sh.text(f"{Lm} m", (x0 + x1) / 2, deck + 190, "blue", ta + 0.5, size=86, weight=700, anchor="middle")
    ts = _at(c, s.get("a_stand", 4.0), t0)
    gid = sh.gid
    for i in [water, *dim, lid]:
        c.tw(f'tl.to("#{i}",{{opacity:0,duration:0.35}},{ts - 0.1:.3f});')
    # stand it up: rotate about the stern bottom, stern lands on the ground at x=1180
    sx, sy = x0, deck + L * 0.06
    c.tw(f'tl.to("#{gid}ship",{{rotation:-90,svgOrigin:"{sx} {sy}",x:{1180 - sx},y:{G - sy},duration:1.1,ease:"power2.inOut"}},{ts:.3f});')
    sh.line([(180, G), (1740, G)], "graphite", ts + 0.2, 0.8, w=3.4)
    # the Eiffel Tower, to scale, on the left
    tt = _at(c, s.get("a_tower", 6.5), t0)
    H = L * Tm / Lm
    cx, base = 640, G
    top = base - H
    half = H * 0.21
    lft = [(cx - half, base), (cx - half * 0.55, base - H * 0.25), (cx - half * 0.22, base - H * 0.55), (cx - 6, top + H * 0.1)]
    rgt = [(cx + half, base), (cx + half * 0.55, base - H * 0.25), (cx + half * 0.22, base - H * 0.55), (cx + 6, top + H * 0.1)]
    arch = [(cx - half * 0.62, base), *[(cx + half * 0.62 * math.cos(a), base - H * 0.1 * math.sin(a)) for a in [math.pi * (1 - k / 12) for k in range(13)]]]
    d = 1.6
    sh.line(lft, "brown", tt, d * 0.3, w=4)
    sh.line(rgt, "brown", tt + d * 0.3, d * 0.3, w=4)
    sh.lines([[(cx - half * 0.62, base - H * 0.25), (cx + half * 0.62, base - H * 0.25)],
              [(cx - half * 0.28, base - H * 0.55), (cx + half * 0.28, base - H * 0.55)],
              [(cx, top + H * 0.1), (cx, top)]], "brown", tt + d * 0.6, d * 0.25, w=3.6)
    sh.line(arch, "brown", tt + d * 0.86, d * 0.18, w=3.4)
    sh.hatch([lft[0], lft[1], lft[2], lft[3], rgt[3], rgt[2], rgt[1], rgt[0]], "brown", tt + d, 0.8, "up", op=0.35, solid=0.12,
             spacing=12)
    sh.text(f"{Tm} m", cx - half - 30, base - H * 0.5, "brown", tt + d + 0.2, size=70, weight=700, anchor="end")
    sh.text(f"{Lm} m", 1180 + 140, G - L * 0.5, "blue", tt + d + 0.7, size=86, weight=700)
    # height guides: the tower's top carried across to the ship
    sh.line([(cx + 20, top), (1300, top)], "red", tt + d + 1.1, 0.6, w=3, op=0.7)
    sh.finish()


def _box(sh, x, y, w, h, color, t, dur, ribs=True, door=True):
    """A shipping container in side view, drawn then coloured in, with corrugation ribs."""
    sh.rect(x, y, w, h, color, t, dur * 0.45, w=4.4)
    sh.hatch([(x, y + h), (x, y), (x + w, y), (x + w, y + h)], color, t + dur * 0.45, dur * 0.35, "right", op=0.5, solid=0.22)
    if ribs:
        n = max(6, int(w / 28))
        rid = sh.id("rb")
        ln = "".join(f'<line x1="{x + w * k / n:.0f}" y1="{y + 8}" x2="{x + w * k / n:.0f}" y2="{y + h - 8}" stroke="{_pc(color)}" '
                     f'stroke-opacity=".4" stroke-width="2"/>' for k in range(1, n))
        sh.raw(f'<g id="{rid}" opacity="0">{ln}</g>')
        sh.show(f"#{rid}", t + dur * 0.75, 0.5)
    return t + dur


def _pc(name):
    from channels.by_design_with_joe.pencil import col
    return col(name)


def p_teu(c, s, t0, t1):
    """TEU explained: a 20-foot box = 1 TEU (on the back of a truck), then a 40-foot box = 2 TEU.
    Anchors: s.a_box, s.a_truck, s.a_forty, s.a_two."""
    sh = Sheet(c, t0, t1, seed=s.get("seed", 4))
    sh.text("TEU", 140, 170, "graphite", t0 + 0.15, size=96, weight=700)
    sh.text("= twenty-foot equivalent unit", 330, 168, "grey", t0 + 0.6, size=58, weight=500)
    tb = _at(c, s.get("a_box", 2.6), t0)
    # 20-foot box (one unit = 380 px)
    U, H = 380, 190
    bx, by = 260, 330
    _box(sh, bx, by, U, H, "orange", tb, 1.6)
    sh.lines([[(bx, by - 34), (bx + U, by - 34)], [(bx, by - 48), (bx, by - 20)], [(bx + U, by - 48), (bx + U, by - 20)]],
             "graphite", tb + 1.0, 0.5, w=3)
    sh.text("20 ft", bx + U / 2, by - 50, "graphite", tb + 1.3, size=54, anchor="middle")
    sh.text("= 1 TEU", bx + U + 230, by + H / 2 + 26, "orange", tb + 1.7, size=92, weight=700)
    # the truck it sits on
    tt = _at(c, s.get("a_truck", 6.0), t0)
    cy = by + H
    sh.lines([[(bx - 20, cy + 6), (bx + U + 30, cy + 6)], [(bx + U + 30, cy + 6), (bx + U + 30, cy - 20)]], "graphite", tt, 0.5, w=5)
    cab = [(bx + U + 40, cy + 30), (bx + U + 40, cy - 110), (bx + U + 120, cy - 110), (bx + U + 160, cy - 40), (bx + U + 160, cy + 30)]
    sh.line(cab, "red", tt + 0.45, 0.6, w=4.4)
    sh.hatch(cab, "red", tt + 1.0, 0.5, "up", op=0.5, solid=0.2)
    for wx in (bx + 40, bx + 110, bx + U - 30, bx + U + 110):
        sh.ring(wx, cy + 40, 28, 28, "graphite", tt + 1.2 + (wx - bx) / 2000, 0.3, w=5)
    # the 40-foot box below: two units long
    tf = _at(c, s.get("a_forty", 9.3), t0)
    fx, fy = 260, 720
    _box(sh, fx, fy, 2 * U, H, "blue", tf, 1.7)
    sh.lines([[(fx, fy + H + 34), (fx + 2 * U, fy + H + 34)], [(fx, fy + H + 20), (fx, fy + H + 48)],
              [(fx + 2 * U, fy + H + 20), (fx + 2 * U, fy + H + 48)]], "graphite", tf + 1.0, 0.5, w=3)
    sh.text("40 ft", fx + U, fy + H + 100, "graphite", tf + 1.3, size=54, anchor="middle")
    t2 = _at(c, s.get("a_two", 11.3), t0)
    sh.line([(fx + U, fy - 14), (fx + U, fy + H + 14)], "red", t2, 0.4, w=4)
    sh.text("1", fx + U / 2, fy + H / 2 + 26, "red", t2 + 0.3, size=80, weight=700, anchor="middle")
    sh.text("2", fx + U * 1.5, fy + H / 2 + 26, "red", t2 + 0.55, size=80, weight=700, anchor="middle")
    sh.text("= 2 TEU", fx + 2 * U + 50, fy + H / 2 + 26, "blue", t2 + 0.8, size=92, weight=700)
    sh.finish()
