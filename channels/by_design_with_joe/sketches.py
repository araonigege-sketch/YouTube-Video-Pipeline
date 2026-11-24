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
        if r.get("rule"):
            sh.line([(X - 10, y - size * 1.0), (X + r["rule"], y - size * 1.0)], "graphite", tr - 0.5, 0.45, w=4)
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
        # a route that leaves one edge of a world map and comes back on the other is drawn as separate strokes
        parts, cur = [], [pts[0]]
        for q in pts[1:]:
            if abs(q[0] - cur[-1][0]) > 600:
                parts.append(cur)
                cur = [q]
            else:
                cur.append(q)
        parts.append(cur)
        if len(parts) > 1:
            sh.lines([p_ for p_ in parts if len(p_) > 1], r.get("color", "blue"), tr, dur, w=r.get("w", 5.5), amp=0.8)
        else:
            sh.line(pts, r.get("color", "blue"), tr, dur, w=r.get("w", 5.5), amp=0.8)
        pts = parts[-1]
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
    if s.get("swarm"):
        import random as _r
        sw = s["swarm"]
        (lo0, la0), (lo1, la1) = sw["box"]
        gq = geo({**req, "points": {"a": [lo0, la0], "b": [lo1, la1]}, "routes": {}})
        (xa, ya), (xb, yb) = gq["points"]["a"], gq["points"]["b"]
        rnd = _r.Random(7)
        n = sw["n"]
        tsw = _at(c, sw["a"], t0)
        per = sw.get("dur", 4.0) / n
        marks = []
        for i in range(n):
            x = xa + (xb - xa) * rnd.random()
            y = ya + (yb - ya) * rnd.random()
            marks.append((x, y))
        marks.sort(key=lambda m: -m[1])
        cc = _pc(sw.get("color", "blue"))
        for i, (x, y) in enumerate(marks):
            mid = sh.id("sw")
            ang = rnd.uniform(-25, 25)
            sh.raw(f'<g id="{mid}" opacity="0" transform="translate({x:.0f},{y:.0f}) rotate({ang:.0f})">'
                   f'<path d="M-13,-4 L9,-4 L14,0 L9,4 L-13,4 Z" fill="{cc}" fill-opacity=".55" stroke="{cc}" stroke-width="2"/></g>')
            sh.show(f"#{mid}", tsw + per * i, 0.15)
        if sw.get("label"):
            sh.text(sw["label"], sw.get("lx", 1300), sw.get("ly", 900), sw.get("lcolor", "red"), tsw + sw.get("dur", 4.0) + 0.2,
                    size=sw.get("size", 110), weight=700)
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


# ---------------------------------------------------------------- economics
def p_scale(c, s, t0, t1):
    """Why ships got huge: cost per box falls as the ship grows (a hand-drawn curve, no invented numbers),
    then the one condition. Anchors: a_crew, a_fuel, a_cheaper, a_condition."""
    sh = Sheet(c, t0, t1, seed=s.get("seed", 21))
    X0, X1, Y0, Y1 = 300, 1250, 860, 260
    sh.lines([[(X0, Y1 - 20), (X0, Y0)], [(X0, Y0), (X1 + 40, Y0)]], "graphite", t0 + 0.2, 0.9, w=4)
    sh.text("cost per box", X0 - 20, Y1 - 50, "graphite", t0 + 0.8, size=52, weight=600)
    sh.text("ship size →", X1 + 40, Y0 + 70, "graphite", t0 + 1.2, size=52, weight=600, anchor="end")
    tc = _at(c, s.get("a_crew", 2.0), t0)
    sh.text("2× the ship ≠ 2× the crew", 1160, 330, "teal", tc, size=56, weight=700)
    tf = _at(c, s.get("a_fuel", 4.0), t0)
    sh.text("≠ 2× the fuel", 1340, 410, "teal", tf, size=56, weight=700)
    tch = _at(c, s.get("a_cheaper", 5.0), t0)
    import math
    curve = [(X0 + 40 + (X1 - X0 - 60) * u, Y1 + 60 + (Y0 - Y1 - 160) * (1 - math.exp(-3.2 * u)) / (1 - math.exp(-3.2)))
             for u in [k / 40 for k in range(41)]]
    sh.line(curve, "blue", tch, 2.2, w=6)
    sh.arrow((X1 - 260, Y0 - 230), (X1 - 40, Y0 - 140), "green", tch + 2.0, 0.7)
    sh.text("cheaper per box", X1 - 520, Y0 - 250, "green", tch + 2.3, size=58, weight=700)
    tq = _at(c, s.get("a_condition", 9.0), t0)
    _, (l, b, w) = sh.text("…only if it’s full of paying cargo", 360, 990, "red", tq, size=72, weight=700)
    sh.underline(l, l + w, b + 16, "red", tq + 1.6, 0.6, w=5)
    sh.finish()


def _loaves(sh, x, y, n_rows, n_cols, color, t, dur, gap=34):
    """Rows of little loaves (rounded ovals) drawn quickly as a block."""
    rid = sh.id("lv")
    body = "".join(f'<ellipse cx="{x + i * gap:.0f}" cy="{y + j * 22:.0f}" rx="14" ry="8" fill="{_pc(color)}" fill-opacity=".45" '
                   f'stroke="{_pc(color)}" stroke-width="2"/>' for j in range(n_rows) for i in range(n_cols))
    sh.raw(f'<g id="{rid}" clip-path="url(#{rid}c)">{body}</g><clipPath id="{rid}c"><rect id="{rid}r" x="{x - 20}" y="{y - 20}" '
           f'width="0" height="{n_rows * 22 + 30}"/></clipPath>')
    sh.c.tw(f'tl.to("#{rid}r",{{attr:{{width:{n_cols * gap + 20}}},duration:{dur:.2f},ease:"none"}},{t:.3f});')
    return rid


def _truck(sh, x, y, L, H, color, t, dur):
    """Side-view box truck, cab on the right: x,y = rear bottom of the body."""
    body = [(x, y), (x, y - H), (x + L, y - H), (x + L, y)]
    sh.line(body + [body[0]], color, t, dur * 0.35, w=4.4)
    cab = [(x + L + 8, y + 18), (x + L + 8, y - H * 0.62), (x + L + H * 0.45, y - H * 0.62), (x + L + H * 0.7, y - H * 0.2),
           (x + L + H * 0.7, y + 18)]
    sh.line(cab, color, t + dur * 0.36, dur * 0.25, w=4.4)
    sh.hatch(cab, color, t + dur * 0.6, dur * 0.2, "up", op=0.5, solid=0.2)
    for wx in (x + L * 0.18, x + L * 0.82, x + L + H * 0.45):
        sh.ring(wx, y + 26, 24, 24, "graphite", t + dur * 0.8, dur * 0.15, w=5)


def p_bakery(c, s, t0, t1):
    """The bakery maths: a big truck (1,000 loaves, $500) and a small van (100 loaves, $100), cost per loaf for each,
    then the truck with only 300 loaves. Anchors: a_truck, a_van, a_t1, a_v1, a_win, a_300, a_t2, a_deal."""
    sh = Sheet(c, t0, t1, seed=s.get("seed", 31))
    sh.text("Delivering bread", 120, 150, "graphite", t0 + 0.2, size=76, weight=700)
    tt = _at(c, s.get("a_truck", 1.0), t0)
    _truck(sh, 150, 560, 560, 260, "orange", tt, 2.0)
    _loaves(sh, 180, 330, 9, 15, "brown", tt + 1.6, 1.2)
    sh.text("1,000 loaves · $500 a trip", 150, 680, "orange", tt + 1.8, size=58, weight=700)
    tv = _at(c, s.get("a_van", 5.0), t0)
    _truck(sh, 1180, 560, 260, 170, "blue", tv, 1.6)
    _loaves(sh, 1205, 415, 3, 6, "brown", tv + 1.3, 0.7, gap=38)
    sh.text("100 loaves · $100 a trip", 1180, 680, "blue", tv + 1.5, size=58, weight=700)
    t1_ = _at(c, s.get("a_t1", 10.0), t0)
    _, (l1, b1, w1) = sh.text("$500 ÷ 1,000 = 50¢", 150, 800, "graphite", t1_, size=72, weight=700)
    tv1 = _at(c, s.get("a_v1", 14.0), t0)
    sh.text("$100 ÷ 100 = $1", 1180, 800, "graphite", tv1, size=72, weight=700)
    tw = _at(c, s.get("a_win", 17.0), t0)
    sh.ring(l1 + w1 - 70, b1 - 24, 95, 55, "green", tw)
    t300 = _at(c, s.get("a_300", 21.0), t0)
    sh.cross(180, 320, 700, 520, "red", t300 + 0.3, 0.7, w=6)
    sh.text("only 300 needed", 260, 300, "red", t300 + 0.9, size=64, weight=700, rot=-3)
    t2 = _at(c, s.get("a_t2", 26.0), t0)
    sh.line([(l1 - 8, b1 - 24), (l1 + w1 + 8, b1 - 30)], "red", t2 - 0.6, 0.4, w=6)
    _, (l2, b2, w2) = sh.text("$500 ÷ 300 ≈ $1.67", 150, 920, "red", t2, size=72, weight=700)
    td = _at(c, s.get("a_deal", 29.0), t0)
    sh.ring(1180 + 250, 800 - 24, 300, 70, "green", td)
    sh.text("better deal", 1500, 930, "green", td + 0.6, size=64, weight=700)
    sh.finish()


def _hull(x0, x1, top, h):
    L = x1 - x0
    return [(x0, top), (x0 + L * 0.02, top + h), (x1 - L * 0.06, top + h), (x1, top), (x0, top)]


def p_fill(c, s, t0, t1):
    """Two ships as capacity outlines, coloured in to how full they are.
    s.ships: [{label, cap, full, carried, color, a, af}], s.notes: [...] ; scale 24,000 TEU = 1300 px."""
    sh = Sheet(c, t0, t1, seed=s.get("seed", 41))
    px = 1150 / 24000
    X = 200
    for k, sp in enumerate(s["ships"]):
        y = 300 + 330 * k
        L = sp["cap"] * px
        ta = _at(c, sp["a"], t0)
        sh.text(sp["label"], X, y - 30, "graphite", ta, size=58, weight=700)
        hull = [(X, y), (X + L, y), (X + L - 40, y + 150), (X + 20, y + 150)]
        sh.line(hull + [hull[0]], sp.get("color", "blue"), ta + 0.4, 1.0, w=4.6)
        tf = _at(c, sp["af"], t0)
        fl = L * sp["full"]
        sh.hatch([(X + 4, y + 4), (X + fl, y + 4), (X + fl - 6, y + 146), (X + 22, y + 146)], sp.get("color", "blue"), tf, 1.2,
                 "right", op=0.65, solid=0.3)
        sh.text(f'{round(sp["full"] * 100)}% full', X + fl / 2, y + 220, sp.get("color", "blue"), tf + 0.8, size=54, weight=700, anchor="middle")
        sh.text(sp["carried"], X + L + 50, y + 95, "graphite", _at(c, sp.get("ac", sp["af"]), t0) + 0.4, size=64, weight=700)
    for n in s.get("notes", []):
        sh.text(n["t"], n.get("x", 300), n.get("y", 990), n.get("color", "red"), _at(c, n["a"], t0), size=n.get("size", 60),
                weight=700, rot=n.get("rot", 0))
    sh.finish()


def p_loops(c, s, t0, t1):
    """Two service loops with their ships: Asia–Europe (11 ships) and Asia–US West Coast (5 to 7).
    Anchors: a_left, a_right, a_note."""
    import math
    sh = Sheet(c, t0, t1, seed=s.get("seed", 51))
    for side, (cx, rx, ry, n, n_maybe, label, col, akey) in enumerate([
            (560, 380, 210, 11, 0, "East Asia ⇄ Europe", "violet", "a_left"),
            (1420, 260, 160, 5, 2, "Asia ⇄ U.S. West Coast", "orange", "a_right")]):
        ta = _at(c, s.get(akey, 1.0 + 6 * side), t0)
        cy = 540
        pts = [(cx + rx * math.cos(a), cy + ry * math.sin(a)) for a in [2 * math.pi * k / 72 for k in range(73)]]
        sh.line(pts, col, ta, 1.4, w=4.4)
        sh.text(label, cx, cy - ry - 50, col, ta + 0.2, size=54, weight=700, anchor="middle")
        tot = n + n_maybe
        for i in range(tot):
            a = 2 * math.pi * i / tot - math.pi / 2
            x, y = cx + rx * math.cos(a), cy + ry * math.sin(a)
            ang = math.degrees(a) + 90
            mid = sh.id("sp")
            dashed = ' stroke-dasharray="5 5" fill-opacity=".08"' if i >= n else ' fill-opacity=".55"'
            sh.raw(f'<g id="{mid}" opacity="0" transform="translate({x:.0f},{y:.0f}) rotate({ang:.0f})">'
                   f'<path d="M-24,-8 L16,-8 L26,0 L16,8 L-24,8 Z" fill="{_pc(col)}" stroke="{_pc(col)}" stroke-width="2.5"{dashed}/></g>')
            sh.show(f"#{mid}", ta + 1.4 + 0.18 * i, 0.2)
        num = f"{n} ships" if not n_maybe else f"{n}–{n + n_maybe} ships"
        sh.text(num, cx, cy + 26, col, ta + 1.6 + 0.18 * tot, size=84, weight=700, anchor="middle")
    tn = _at(c, s.get("a_note", 14.0), t0)
    sh.text("shorter trip → smaller savings", 960, 960, "red", tn, size=66, weight=700, anchor="middle")
    sh.finish()


def p_list(c, s, t0, t1):
    """A handwritten checklist, item by item, then a closing line. s.items: [{t, a}], s.end: {t, a}, s.title."""
    sh = Sheet(c, t0, t1, seed=s.get("seed", 61))
    if s.get("title"):
        _, (l, b, w) = sh.text(s["title"], 160, 170, "graphite", t0 + 0.2, size=76, weight=700)
        sh.underline(l, l + w, 190, "graphite", t0 + 1.0)
    cols = ["blue", "brown", "teal", "orange", "violet", "green"]
    for k, it in enumerate(s["items"]):
        y = 300 + 125 * k
        ta = _at(c, it["a"], t0)
        sh.lines([[(170, y - 30), (190, y - 8)], [(190, y - 8), (232, y - 62)]], cols[k % len(cols)], ta, 0.35, w=6)
        sh.text(it["t"], 270, y, cols[k % len(cols)], ta + 0.2, size=70, weight=700)
    if s.get("end"):
        e = s["end"]
        _, (l, b, w) = sh.text(e["t"], 160, 300 + 125 * len(s["items"]) + 40, "red", _at(c, e["a"], t0), size=76, weight=700)
        sh.underline(l, l + w, b + 18, "red", _at(c, e["a"], t0) + 1.4, 0.6, w=5)
    sh.finish()


# ---------------------------------------------------------------- canal and bridge
def _side_ship(sh, gid, x, y, L, color, t, dur, stack=True):
    """A small container ship in side view inside its own <g id=gid> (so it can be moved). Bow to the right."""
    sh.raw(f'<g id="{gid}">')
    hull = [(x, y - 40), (x + L, y - 40), (x + L - 30, y), (x + 14, y)]
    sh.line(hull + [hull[0]], color, t, dur * 0.5, w=4.2)
    sh.hatch(hull, color, t + dur * 0.5, dur * 0.3, "right", op=0.6, solid=0.3, pen=False)
    if stack:
        sh.raw(f'<rect x="{x + 22}" y="{y - 82}" width="{L * 0.18:.0f}" height="42" fill="{_pc("graphite")}" fill-opacity=".25" '
               f'stroke="{_pc("graphite")}" stroke-width="2.5"/>'
               f'<rect x="{x + L * 0.26:.0f}" y="{y - 74}" width="{L * 0.58:.0f}" height="34" fill="{_pc("orange")}" fill-opacity=".35" '
               f'stroke="{_pc("orange")}" stroke-width="2.5"/>')
    sh.raw("</g>")


def p_lock(c, s, t0, t1):
    """How a lock works, side view: the box, the ship sails in, gates close, water rises, ship lifted, then its size
    limit. Anchors: a_box, a_in, a_gates, a_water, a_lift, a_limit."""
    sh = Sheet(c, t0, t1, seed=s.get("seed", 71))
    B0, B1 = 640, 1280                 # chamber walls (x)
    low, high, floor = 760, 560, 900   # water levels (y)
    tb = _at(c, s.get("a_box", 0.4), t0)
    # concrete: low basin on the left, chamber, high basin on the right
    sh.lines([[(120, floor), (B0, floor)], [(B0, floor), (B1, floor)], [(B1, floor), (B1, high + 40)], [(B1, high + 40), (1800, high + 40)]],
             "graphite", tb, 1.4, w=5)
    sh.hatch([(B0, floor), (B0, floor + 30), (B1 + 30, floor + 30), (B1 + 30, high + 40), (B1, high + 40), (B1, floor)], "grey", tb + 1.3,
             0.6, "right", op=0.5, solid=0.2, pen=False)
    sh.text("a huge concrete box", B0 + 40, floor + 90, "graphite", tb + 1.2, size=54, weight=600)
    # water: low on the left + in the chamber, high on the right
    wid = sh.id("wl")
    sh.raw(f'<rect x="120" y="{low}" width="{B0 - 120}" height="{floor - low}" fill="{_pc("blue")}" fill-opacity=".18"/>'
           f'<rect x="{B1}" y="{high}" width="{1800 - B1}" height="{high + 40 - high}" fill="{_pc("blue")}" fill-opacity=".18"/>'
           f'<rect id="{wid}" x="{B0}" y="{low}" width="{B1 - B0}" height="{floor - low}" fill="{_pc("blue")}" fill-opacity=".22"/>')
    sh.line([(120, low), (B0, low)], "blue", tb + 0.6, 0.6, w=3)
    sh.line([(B1, high), (1800, high)], "blue", tb + 0.8, 0.6, w=3)
    # the ship, waiting low on the left
    ship = sh.id("shp")
    _side_ship(sh, ship, 170, low + 6, 400, "blue", tb + 1.6, 1.2)
    ti = _at(c, s.get("a_in", 4.0), t0)
    c.tw(f'tl.to("#{ship}",{{x:{B0 + 110 - 170},duration:2.0,ease:"sine.inOut"}},{ti:.3f});')
    tg = _at(c, s.get("a_gates", 5.5), t0)
    sh.line([(B0, low - 140), (B0, floor)], "red", tg, 0.45, w=7)
    sh.line([(B1, high - 60), (B1, floor)], "red", tg + 0.3, 0.45, w=7)
    tw = _at(c, s.get("a_water", 7.0), t0)
    c.tw(f'tl.to("#{wid}",{{attr:{{y:{high},height:{floor - high}}},duration:2.6,ease:"sine.inOut"}},{tw:.3f});')
    c.tw(f'tl.to("#{ship}",{{y:{high - low},duration:2.6,ease:"sine.inOut"}},{tw:.3f});')
    arr = sh.arrow((B0 - 60, low - 10), (B0 - 60, high + 10), "blue", tw + 0.3, 0.8, bend=0.0)
    tl = _at(c, s.get("a_lift", 9.5), t0)
    sh.text("lifted (or lowered)", B0 - 520, (low + high) / 2, "blue", tl, size=56, weight=700)
    tlim = _at(c, s.get("a_limit", 13.0), t0)
    sh.lines([[(B0 + 10, 300), (B1 - 10, 300)], [(B0 + 10, 282), (B0 + 10, 318)], [(B1 - 10, 282), (B1 - 10, 318)]], "red", tlim, 0.6, w=4)
    sh.text("size limit", (B0 + B1) / 2, 270, "red", tlim + 0.5, size=72, weight=700, anchor="middle")
    sh.finish()


def _whale(sh, x, y, w, color, t, dur):
    """A quick blue-whale doodle, head left, length w px."""
    h = w * 0.16
    body = [(x, y), (x + w * 0.1, y - h * 0.8), (x + w * 0.45, y - h), (x + w * 0.8, y - h * 0.5), (x + w * 0.9, y - h * 0.15),
            (x + w, y - h * 0.9), (x + w * 0.97, y), (x + w, y + h * 0.7), (x + w * 0.9, y + h * 0.1), (x + w * 0.6, y + h * 0.55),
            (x + w * 0.2, y + h * 0.55), (x, y)]
    sh.line(body, color, t, dur, w=4)
    sh.hatch(body, color, t + dur, 0.6, "right", op=0.45, solid=0.18, pen=False)


def p_fit(c, s, t0, t1):
    """Top-down: the new Panama locks' limit (370 m × 51.25 m) vs the MSC Irina (≈400 m × 61.3 m), to scale.
    Anchors: a_limit, a_ship, a_long, a_whale, a_wide, a_triton, a_irina_w, a_ten, a_closed."""
    sh = Sheet(c, t0, t1, seed=s.get("seed", 81))
    k = 1500 / 400                      # px per metre
    X, Yc = 200, 560
    Lm, Wm = 370 * k, 51.25 * k
    Ls, Ws = 400 * k, 61.3 * k
    ta = _at(c, s.get("a_limit", 0.6), t0)
    lock = [(X, Yc - Wm / 2), (X + Lm, Yc - Wm / 2), (X + Lm, Yc + Wm / 2), (X, Yc + Wm / 2)]
    sh.line(lock + [lock[0]], "graphite", ta, 1.3, w=5)
    sh.text("Panama limit: 370 m", X, Yc - Ws / 2 - 60, "graphite", ta + 0.7, size=56, weight=700)
    tsh = _at(c, s.get("a_ship", 3.0), t0)
    hull = [(X, Yc - Ws / 2), (X + Ls - 70, Yc - Ws / 2), (X + Ls, Yc), (X + Ls - 70, Yc + Ws / 2), (X, Yc + Ws / 2)]
    sh.line(hull + [hull[0]], "blue", tsh, 1.4, w=4.6)
    sh.hatch(hull, "blue", tsh + 1.3, 1.0, "right", op=0.35, solid=0.12, spacing=12)
    sh.text("MSC Irina: ≈ 400 m", X + 620, Yc + Ws / 2 + 70, "blue", tsh + 0.8, size=56, weight=700)
    tl = _at(c, s.get("a_long", 5.5), t0)
    sh.lines([[(X + Lm, Yc - Ws / 2 - 70), (X + Ls, Yc - Ws / 2 - 70)], [(X + Lm, Yc - Ws / 2 - 88), (X + Lm, Yc - Ws / 2 - 52)],
              [(X + Ls, Yc - Ws / 2 - 88), (X + Ls, Yc - Ws / 2 - 52)]], "red", tl, 0.6, w=4)
    sh.text("30 m too long", X + Ls, Yc - Ws / 2 - 105, "red", tl + 0.4, size=58, weight=700, anchor="end")
    tw = _at(c, s.get("a_whale", 8.0), t0)
    _whale(sh, X + Lm, Yc - Ws / 2 - 200, 30 * k, "teal", tw, 1.2)
    sh.text("≈ one blue whale", X + Lm - 30, Yc - Ws / 2 - 185, "teal", tw + 0.9, size=54, weight=700, anchor="end")
    tt = _at(c, s.get("a_triton", 11.0), t0)
    sh.lines([[(X - 60, Yc - Wm / 2), (X - 60, Yc + Wm / 2)], [(X - 76, Yc - Wm / 2), (X - 44, Yc - Wm / 2)],
              [(X - 76, Yc + Wm / 2), (X - 44, Yc + Wm / 2)]], "graphite", tt, 0.5, w=4)
    sh.text("51.2 m", X - 80, Yc + 18, "graphite", tt + 0.3, size=48, weight=700, anchor="end")
    sh.text("widest so far: Evergreen’s Triton", X, 930, "graphite", tt + 0.6, size=50, weight=600)
    ti = _at(c, s.get("a_irina_w", 14.0), t0)
    sh.lines([[(X + 120, Yc - Ws / 2), (X + 120, Yc + Ws / 2)], [(X + 104, Yc - Ws / 2), (X + 136, Yc - Ws / 2)],
              [(X + 104, Yc + Ws / 2), (X + 136, Yc + Ws / 2)]], "blue", ti, 0.5, w=4)
    sh.text("61.3 m", X + 140, Yc + 18, "blue", ti + 0.3, size=48, weight=700)
    tten = _at(c, s.get("a_ten", 16.0), t0)
    sh.ring(X + 120, Yc, 90, Ws / 2 + 30, "red", tten)
    sh.text("+10 m", X + 120, Yc + Ws / 2 + 90, "red", tten + 0.5, size=64, weight=700, anchor="middle")
    tc = _at(c, s.get("a_closed", 21.0), t0)
    sid = sh.id("st")
    sh.raw(f'<g id="{sid}" opacity="0" transform="translate(980,{Yc}) rotate(-8)"><rect x="-260" y="-80" width="520" height="150" rx="12" '
           f'fill="none" stroke="{_pc("red")}" stroke-width="10"/><text x="0" y="36" text-anchor="middle" font-family="Caveat" font-weight="700" '
           f'font-size="130" fill="{_pc("red")}">CLOSED</text></g>')
    c.tw(f'tl.fromTo("#{sid}",{{opacity:0,scale:1.4,transformOrigin:"50% 50%"}},{{opacity:1,scale:1,duration:0.35,ease:"power3.in"}},{tc:.3f});')
    sh.finish()


def p_bridge(c, s, t0, t1):
    """The Bayonne Bridge in side view, to scale in height. Stage 1: deck 151 ft over the water, ships growing taller.
    Stage 2 (re-entered later, `stage: 2`): the new road built 64 ft higher inside the arch → 215 ft.
    Anchors: stage 1 a_deck, a_plenty, a_grow, a_limit; stage 2 a_raise, a_cars, a_new."""
    sh = Sheet(c, t0, t1, seed=s.get("seed", 91))
    import math
    W0, W1, water = 260, 1660, 930
    ft = 2.55                           # px per foot
    old_y, new_y = water - 151 * ft, water - 215 * ft
    st2 = s.get("stage", 1) == 2
    quick = 0.05 if st2 else None
    tb = t0 + 0.2

    def dur(d):
        return quick if st2 else d

    # water, arch, hangers, old deck
    sh.line([(120, water), (1800, water)], "blue", tb, dur(0.7), w=3.4, pen=not st2)
    arch = [(W0 + (W1 - W0) * u, water - 60 - math.sin(math.pi * u) * 690) for u in [k / 40 for k in range(41)]]
    arch2 = [(x, y + 34) for x, y in arch]
    sh.line(arch, "graphite", tb + (0 if st2 else 0.6), dur(1.6), w=4.6, pen=not st2)
    sh.line(arch2, "graphite", tb + (0 if st2 else 1.5), dur(1.0), w=3, pen=not st2)
    deck_l, deck_r = 120, 1800
    sh.line([(deck_l, old_y), (deck_r, old_y)], "graphite", tb + (0 if st2 else 2.4), dur(0.8), w=6, pen=not st2)
    if not st2:
        sh.text("Bayonne Bridge, 1931", 120, 150, "graphite", tb + 0.2, size=72, weight=700)
        td = _at(c, s.get("a_deck", 2.5), t0)
        sh.lines([[(1730, water), (1730, old_y)], [(1712, water), (1748, water)], [(1712, old_y), (1748, old_y)]], "red", td, 0.6, w=4)
        sh.text("151 ft", 1720, (water + old_y) / 2, "red", td + 0.4, size=64, weight=700, anchor="end")
        tp = _at(c, s.get("a_plenty", 5.0), t0)
        s1 = sh.id("sa")
        _side_ship(sh, s1, 500, water + 2, 300, "green", tp, 1.0)
        sh.text("✓ plenty", 560, water - 140, "green", tp + 0.8, size=54, weight=700)
        tg = _at(c, s.get("a_grow", 7.5), t0)
        c.tw(f'tl.to("#{s1}",{{opacity:0.25,duration:0.4}},{tg:.3f});')
        # taller and taller ships beside the bridge: stack heights drawn as rising profiles
        for k, (h, col) in enumerate([(120, "orange"), (180, "orange"), (260, "red")]):
            x = 900 + k * 210
            prof = [(x, water), (x, water - h * ft), (x + 150, water - h * ft), (x + 150, water)]
            sh.line(prof, col, tg + 0.9 * k, 0.6, w=4.4)
            sh.hatch(prof, col, tg + 0.9 * k + 0.55, 0.4, "up", op=0.45, solid=0.18, pen=False)
        tl = _at(c, s.get("a_limit", 11.0), t0)
        sh.cross(1320, water - 270 * ft + 10, 1440, old_y - 20, "red", tl, 0.5, w=6)
        sh.text("max ≈ 10,000 TEU", 120, 250, "red", tl + 0.4, size=66, weight=700)
    else:
        sh.text("Raise the road, keep the arch", 120, 150, "graphite", tb, size=72, weight=700)
        tr = _at(c, s.get("a_raise", 1.0), t0)
        sh.line([(deck_l, new_y), (deck_r, new_y)], "green", tr, 1.4, w=7)
        sh.arrow((1700, old_y - 6), (1700, new_y + 10), "green", tr + 0.6, 0.6, bend=0.0)
        sh.text("+64 ft", 1690, (old_y + new_y) / 2 + 10, "green", tr + 0.9, size=60, weight=700, anchor="end")
        tc_ = _at(c, s.get("a_cars", 3.5), t0)
        for k in range(4):                         # cars still driving on the old road underneath
            cid = sh.id("car")
            sh.raw(f'<g id="{cid}" opacity="0"><rect x="0" y="{old_y - 22}" width="44" height="18" rx="6" fill="{_pc("graphite")}" '
                   f'fill-opacity=".6"/></g>')
            c.tw(f'tl.set("#{cid}",{{opacity:1}},{tc_ + k * 0.8:.3f});tl.fromTo("#{cid}",{{x:{deck_l - 60}}},{{x:{deck_r},duration:5,'
                 f'ease:"none"}},{tc_ + k * 0.8:.3f});')
        tn = _at(c, s.get("a_new", 10.0), t0)
        sh.lines([[(1790, water), (1790, new_y)], [(1772, water), (1808, water)], [(1772, new_y), (1808, new_y)]], "green", tn, 0.6, w=4)
        sh.text("215 ft", 1770, new_y - 20, "green", tn + 0.4, size=72, weight=700, anchor="end")
    sh.finish()
