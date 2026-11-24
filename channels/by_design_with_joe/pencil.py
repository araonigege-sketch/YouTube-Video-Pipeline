"""Coloured-pencil drawing kit for By Design With Joe (owner, 2026-11-24: illustrations and the maths in CineCode's
coloured pencils). Grammar from CineCode's `dataviz` style: warm cream paper, every mark drawn by a visible pencil,
graphite-grain strokes, coloured-in hatching, handwritten notes (Caveat) pinned to the marks.

A `Sheet` collects marks for one full-frame page and turns them into HTML/SVG plus GSAP tweens on the composer's
timeline. The pencil's path is precomputed here at frame rate, so seeking the timeline is deterministic.

    sh = Sheet(c, t0, t1)
    sh.line([(x, y), ...], "blue", t, dur)          # pencil stroke, drawn on
    sh.hatch([(x, y), ...], "red", t, dur, "up")    # coloured-in polygon (hatching), revealed in a direction
    sh.text("55 million", x, y, "graphite", t, size=72)   # handwriting, written on
    sh.ring(cx, cy, rx, ry, "red", t)               # un-closed annotation ring
    sh.finish()

Pencils (each concept keeps one colour through an episode): see PENCILS.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageFont

from channels.by_design_with_joe.typo import esc, smart
from pipeline.config import ROOT

PAPER = "#F2EBDC"
PENCILS = {
    "graphite": "#3A3630",
    "blue": "#2C5FB0",
    "red": "#CC3838",
    "green": "#2D8A57",
    "orange": "#E57D22",
    "violet": "#6F4FB4",
    "teal": "#16909A",
    "ochre": "#D9A520",
    "brown": "#8A5B3A",
    "pink": "#D2508A",
    "grey": "#9A9288",
}
CAVEAT = {w: ROOT / f"node_modules/@fontsource/caveat/files/caveat-latin-{w}-normal.woff2" for w in (400, 500, 600, 700)}
_CACHE = ROOT / "build/.fontcache"


def col(name: str) -> str:
    return PENCILS.get(name, name)


def _ttf(weight: int) -> Path:
    out = _CACHE / f"caveat-{weight}.ttf"
    if not out.exists():
        from fontTools.ttLib import TTFont
        out.parent.mkdir(parents=True, exist_ok=True)
        f = TTFont(str(CAVEAT[weight]))
        f.flavor = None
        f.save(str(out))
    return out


_FONTS: dict = {}


def text_width(s: str, size: float, weight: int = 600) -> float:
    key = (round(size), weight)
    if key not in _FONTS:
        _FONTS[key] = ImageFont.truetype(str(_ttf(weight)), round(size))
    return _FONTS[key].getlength(smart(s))


def paper(path: Path, seed: int = 7) -> Path:
    """Warm cream paper: soft mottling, fine fibre, a faint dot grid and a gentle edge falloff (made once)."""
    if path.exists():
        return path
    import numpy as np
    rng = np.random.default_rng(seed)
    W, H = 1920, 1080
    base = np.array([0xF2, 0xEB, 0xDC], np.float32)
    low = rng.normal(0, 1, (H // 60 + 2, W // 60 + 2)).astype(np.float32)
    low = np.array(Image.fromarray(low).resize((W, H), Image.BICUBIC), np.float32) * 2.2
    fib = rng.normal(0, 1, (H, W)).astype(np.float32)
    fib = np.array(Image.fromarray(fib).resize((W // 2, H // 2), Image.BILINEAR).resize((W, H), Image.BILINEAR), np.float32) * 2.6
    streak = np.array(Image.fromarray(rng.normal(0, 1, (H // 2, W // 14)).astype(np.float32)).resize((W, H), Image.BICUBIC),
                      np.float32) * 1.2
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    fall = -np.clip(r - 0.55, 0, None) ** 2 * 26
    img = base[None, None, :] + (low + fib + streak + fall)[..., None] * np.array([1.0, 1.0, 1.05], np.float32)
    dots = ((xx % 48 == 24) & (yy % 48 == 24)) | ((xx % 48 == 25) & (yy % 48 == 24)) | ((xx % 48 == 24) & (yy % 48 == 25))
    img[dots] -= np.array([26, 26, 22], np.float32)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(path)
    return path


def ease_sine(u: float) -> float:
    return -(math.cos(math.pi * max(0.0, min(1.0, u))) - 1) / 2


def _len(pts) -> list[float]:
    acc = [0.0]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        acc.append(acc[-1] + math.hypot(x1 - x0, y1 - y0))
    return acc


def _at_len(pts, acc, L):
    if L <= 0:
        return pts[0]
    for k in range(1, len(acc)):
        if acc[k] >= L:
            u = (L - acc[k - 1]) / max(1e-6, acc[k] - acc[k - 1])
            return (pts[k - 1][0] + (pts[k][0] - pts[k - 1][0]) * u, pts[k - 1][1] + (pts[k][1] - pts[k - 1][1]) * u)
    return pts[-1]


def densify(pts, step=14.0):
    out = [pts[0]]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / step))
        for k in range(1, n + 1):
            out.append((x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n))
    return out


def wobble(pts, amp=1.6, seed=0, step=14.0):
    """Hand tremor: a smooth perpendicular drift along the line (the SVG filter adds the fine grain)."""
    rnd = random.Random(seed)
    d = densify(pts, step)
    ph1, ph2 = rnd.uniform(0, 6.28), rnd.uniform(0, 6.28)
    acc = _len(d)
    out = []
    for k, (x, y) in enumerate(d):
        if 0 < k < len(d) - 1:
            dx, dy = d[k + 1][0] - d[k - 1][0], d[k + 1][1] - d[k - 1][1]
        elif k == 0 and len(d) > 1:
            dx, dy = d[1][0] - x, d[1][1] - y
        else:
            dx, dy = x - d[k - 1][0], y - d[k - 1][1]
        n = math.hypot(dx, dy) or 1
        o = amp * (math.sin(acc[k] / 95 + ph1) * 0.7 + math.sin(acc[k] / 37 + ph2) * 0.3)
        out.append((x - dy / n * o, y + dx / n * o))
    return out


def path_d(pts) -> str:
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def arc_pts(cx, cy, rx, ry, a0, a1, n=48):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * k / n), cy + ry * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]


def bezier(p0, p1, p2, n=40):
    return [((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0],
             (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1]) for u in (k / n for k in range(n + 1))]


def _pencil_svg(gid: str) -> str:
    """The pencil prop, tip at (0,0), body toward the lower right. Lead/body colour set by CSS var --pc."""
    return (f'<div id="{gid}pen" class="pen" style="--pc:{PENCILS["graphite"]}">'
            '<svg width="520" height="520" viewBox="-20 -20 520 520" style="position:absolute;left:-20px;top:-20px;overflow:visible">'
            '<g class="pen-shadow" transform="translate(16,20)" opacity=".18"><path d="M0,0 L34,-12 L470,300 L440,340 L-10,30 Z" fill="#2a2016"/></g>'
            '<g transform="rotate(36)">'
            '<path d="M0,0 L58,-17 L58,17 Z" fill="#E8C690"/>'                       # sharpened wood cone
            '<path d="M58,-17 Q52,0 58,17 L58,17 Z" fill="#D6AE73"/>'
            '<path d="M0,0 L19,-5.6 L19,5.6 Z" fill="var(--pc)"/>'                   # lead
            '<rect x="58" y="-17" width="440" height="34" fill="var(--pc)"/>'        # hex body
            '<rect x="58" y="-17" width="440" height="11" fill="#fff" opacity=".22"/>'
            '<rect x="58" y="6" width="440" height="11" fill="#000" opacity=".16"/>'
            '</g></svg></div>')


class Sheet:
    def __init__(self, c, t0: float, t1: float, seed: int = 1, camera: list | None = None):
        self.c, self.t0, self.t1 = c, t0, t1
        self.gid = c.nid("pn")
        self.svg: list[str] = []
        self.html: list[str] = []
        self.moves: list[tuple] = []      # (t_start, t_end, kind, data, colour)
        self.rnd = random.Random(seed)
        self.n = 0
        self.camera = camera or []        # [(t, scale, x, y), ...]: slow pushes over the sheet

    def id(self, p="m"):
        self.n += 1
        return f"{self.gid}{p}{self.n}"

    # ---------- marks
    def line(self, pts, color, t, dur=0.8, w=4.2, amp=1.4, pen=True, op=0.92):
        """A pencil stroke drawn on from its first point to its last."""
        pts = wobble(pts, amp, self.rnd.randint(0, 9999))
        i = self.id("l")
        cc = col(color)
        self.svg.append(f'<path id="{i}" d="{path_d(pts)}" stroke="{cc}" stroke-width="{w}" stroke-opacity="{op}" fill="none" '
                        f'pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"/>')
        self.c.tw(f'tl.to("#{i}",{{strokeDashoffset:0,duration:{dur:.3f},ease:"sine.inOut"}},{t:.3f});')
        if pen:
            self.moves.append((t, t + dur, "path", pts, cc))
        return i

    def lines(self, polys, color, t, dur, **kw):
        """Several strokes in sequence within [t, t+dur] (e.g. a box's edges), split by length."""
        L = [max(1.0, _len(p)[-1]) for p in polys]
        tot = sum(L) + 0.0001
        gap = 0.06
        tt = t
        ids = []
        for p, l in zip(polys, L):
            d = max(0.12, (dur - gap * (len(polys) - 1)) * l / tot)
            ids.append(self.line(p, color, tt, d, **kw))
            tt += d + gap
        return ids

    def rect(self, x, y, bw, bh, color, t, dur=0.9, **kw):
        return self.lines([[(x, y + bh), (x, y)], [(x, y), (x + bw, y)], [(x + bw, y), (x + bw, y + bh)], [(x + bw, y + bh), (x, y + bh)]],
                          color, t, dur, **kw)

    def hatch(self, poly, color, t, dur=1.0, direction="up", spacing=9, op=0.62, w=3.0, angle=-38, pen=True, solid=0.18):
        """Colour a polygon in with pencil hatching, revealed in `direction` (up/down/right/left)."""
        i = self.id("h")
        cc = col(color)
        xs, ys = [p[0] for p in poly], [p[1] for p in poly]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        pad = 40
        # hatch lines across the bounding box at an angle, slightly irregular
        a = math.radians(angle)
        dx, dy = math.cos(a), math.sin(a)
        nx, ny = -dy, dx
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        R = math.hypot(x1 - x0, y1 - y0) / 2 + pad
        hl = []
        k = -R
        while k <= R:
            off = k + self.rnd.uniform(-1.6, 1.6)
            px, py = cx + nx * off, cy + ny * off
            a0 = (px - dx * R, py - dy * R)
            a1 = (px + dx * R, py + dy * R)
            hl.append(f'M{a0[0]:.1f},{a0[1]:.1f} L{a1[0]:.1f},{a1[1]:.1f}')
            k += spacing * self.rnd.uniform(0.85, 1.15)
        clip = f"{i}c"
        reveal = f"{i}r"
        if direction == "up":
            r0 = f'x="{x0 - pad}" y="{y1 + pad}" width="{x1 - x0 + 2 * pad}" height="0"'
            to = f'{{attr:{{y:{y0 - pad},height:{y1 - y0 + 2 * pad}}},duration:{dur:.3f},ease:"none"}}'
        elif direction == "down":
            r0 = f'x="{x0 - pad}" y="{y0 - pad}" width="{x1 - x0 + 2 * pad}" height="0"'
            to = f'{{attr:{{height:{y1 - y0 + 2 * pad}}},duration:{dur:.3f},ease:"none"}}'
        elif direction == "left":
            r0 = f'x="{x1 + pad}" y="{y0 - pad}" width="0" height="{y1 - y0 + 2 * pad}"'
            to = f'{{attr:{{x:{x0 - pad},width:{x1 - x0 + 2 * pad}}},duration:{dur:.3f},ease:"none"}}'
        else:
            r0 = f'x="{x0 - pad}" y="{y0 - pad}" width="0" height="{y1 - y0 + 2 * pad}"'
            to = f'{{attr:{{width:{x1 - x0 + 2 * pad}}},duration:{dur:.3f},ease:"none"}}'
        shape = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in poly) + " Z"
        self.svg.append(f'<clipPath id="{clip}"><path d="{shape}"/></clipPath>'
                        f'<clipPath id="{reveal}"><rect id="{reveal}x" {r0}/></clipPath>'
                        f'<g clip-path="url(#{reveal})"><g clip-path="url(#{clip})">'
                        f'<path d="{shape}" fill="{cc}" fill-opacity="{solid}" stroke="none"/>'
                        f'<path d="{" ".join(hl)}" stroke="{cc}" stroke-width="{w}" stroke-opacity="{op}" fill="none"/></g></g>')
        self.c.tw(f'tl.to("#{reveal}x",{to},{t:.3f});')
        if pen:
            self.moves.append((t, t + dur, "zig", (x0, y0, x1, y1, direction), cc))
        return i

    def text(self, s, x, y, color, t, size=64, weight=600, anchor="start", dur=None, pen=True, rot=0.0, op=1.0, cls=""):
        """Handwriting, written on left to right. (x, y) = baseline start (or centre/end with anchor)."""
        i = self.id("t")
        cc = col(color)
        wdt = text_width(s, size, weight)
        left = x - (wdt / 2 if anchor == "middle" else wdt if anchor == "end" else 0)
        top = y - size * 0.98
        if dur is None:
            dur = max(0.35, min(2.2, 0.055 * len(s) + 0.2))
        self.html.append(f'<div id="{i}" class="hw {cls}" style="left:{left:.0f}px;top:{top:.0f}px;font-size:{size}px;font-weight:{weight};'
                         f'color:{cc};opacity:{op};transform:rotate({rot}deg);clip-path:inset(-40% 100% -40% -12%)">{esc(s)}</div>')
        self.c.tw(f'tl.to("#{i}",{{clipPath:"inset(-40% -14% -40% -12%)",duration:{dur:.3f},ease:"none"}},{t:.3f});')
        if pen:
            self.moves.append((t, t + dur, "write", (left, y, wdt, size), cc))
        return i, (left, y, wdt)

    def ring(self, cx, cy, rx, ry, color, t, dur=0.7, w=4.0):
        """An un-closed hand-drawn ring around a mark."""
        a0 = self.rnd.uniform(-2.4, -1.9)
        pts = arc_pts(cx, cy, rx, ry, a0, a0 + 2 * math.pi * 0.93, 60)
        pts = [(x + self.rnd.uniform(-0.8, 0.8), y + self.rnd.uniform(-0.8, 0.8)) for x, y in pts]
        return self.line(pts, color, t, dur, w=w, amp=2.2)

    def arrow(self, p0, p1, color, t, dur=0.7, bend=0.18, w=4.0, head=22):
        mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        ctrl = (mx - dy * bend, my + dx * bend)
        pts = bezier(p0, ctrl, p1)
        ex, ey = pts[-1][0] - pts[-3][0], pts[-1][1] - pts[-3][1]
        n = math.hypot(ex, ey) or 1
        ux, uy = ex / n, ey / n
        h1 = (p1[0] - ux * head - uy * head * 0.6, p1[1] - uy * head + ux * head * 0.6)
        h2 = (p1[0] - ux * head + uy * head * 0.6, p1[1] - uy * head - ux * head * 0.6)
        a = self.line(pts, color, t, dur * 0.8, w=w)
        b = self.lines([[h1, p1], [p1, h2]], color, t + dur * 0.8, dur * 0.25, w=w)
        return [a, *b]

    def underline(self, x0, x1, y, color, t, dur=0.45, w=4.5):
        return self.line([(x0, y), ((x0 + x1) / 2, y + self.rnd.uniform(-2, 3)), (x1, y - self.rnd.uniform(0, 4))], color, t, dur, w=w)

    def cross(self, x0, y0, x1, y1, color, t, dur=0.5, w=5):
        return self.lines([[(x0, y0), (x1, y1)], [(x1, y0), (x0, y1)]], color, t, dur, w=w)

    def raw(self, svg: str):
        self.svg.append(svg)

    def raw_html(self, h: str):
        self.html.append(h)

    def show(self, sel: str, t: float, d=0.4):
        self.c.tw(f'tl.fromTo("{sel}",{{opacity:0}},{{opacity:1,duration:{d}}},{t:.3f});')

    def dim(self, sel: str, t: float, to=0.3, d=0.4):
        self.c.tw(f'tl.to("{sel}",{{opacity:{to},duration:{d}}},{t:.3f});')

    # ---------- the pencil
    def _pen_track(self, fps=30):
        """Frame-rate keyframes (x, y, lift, colour) for the pencil over the whole sheet."""
        mv = sorted(self.moves, key=lambda m: m[0])
        # drop moves that overlap the previous one (the pencil can only draw one mark at a time)
        keep, end = [], -1e9
        for m in mv:
            if m[0] >= end - 0.02:
                keep.append(m)
                end = m[1]
        if not keep:
            return []

        def pos(m, u):
            kind, data = m[2], m[3]
            if kind == "path":
                acc = _len(data)
                return _at_len(data, acc, acc[-1] * ease_sine(u))
            if kind == "write":
                left, base, wdt, size = data
                x = left + wdt * u
                return (x, base - size * 0.28 + math.sin(u * wdt / size * 9.5) * size * 0.16)
            x0, y0, x1, y1, d = data          # zig: colouring in, sweeping across the reveal edge
            sweeps = max(2, int((x1 - x0 if d in ("up", "down") else y1 - y0) / 60) + 3)
            ph = abs(math.sin(u * sweeps * math.pi))
            if d == "up":
                return (x0 + (x1 - x0) * ph, y1 - (y1 - y0) * u)
            if d == "down":
                return (x0 + (x1 - x0) * ph, y0 + (y1 - y0) * u)
            if d == "left":
                return (x1 - (x1 - x0) * u, y0 + (y1 - y0) * ph)
            return (x0 + (x1 - x0) * u, y0 + (y1 - y0) * ph)

        t_in = max(self.t0, keep[0][0] - 0.5)
        frames = []
        f = int(math.floor(t_in * fps))
        f_end = int(math.ceil(min(self.t1, keep[-1][1] + 1.0) * fps))
        rest = (1960.0, 1160.0)
        k = 0
        last = rest
        while f <= f_end:
            t = f / fps
            while k + 1 < len(keep) and t >= keep[k + 1][0] - 0.35:
                last = pos(keep[k], 1.0)
                k += 1
            m = keep[k]
            if t < m[0]:                           # travelling (lifted) to the next mark's start
                start = pos(m, 0.0)
                src = last if (k > 0 or t > t_in + 1e-6) else rest
                if k == 0 and last == rest:
                    src = rest
                span = max(0.05, m[0] - max(t_in if k == 0 else keep[k - 1][1], m[0] - 0.35))
                u = ease_sine(1 - (m[0] - t) / span)
                x, y = src[0] + (start[0] - src[0]) * u, src[1] + (start[1] - src[1]) * u
                lift = 1 - u * 0.8 if k == 0 else 0.6 * math.sin(math.pi * u) + 0.2 * (1 - u)
                frames.append((t, x, y, max(0.0, lift), m[4]))
            elif t <= m[1]:
                u = (t - m[0]) / max(1e-6, m[1] - m[0])
                x, y = pos(m, u)
                frames.append((t, x, y, 0.0, m[4]))
                last = (x, y)
            else:                                  # after the last mark: hover, then leave to the lower right
                if k == len(keep) - 1:
                    u = ease_sine(min(1.0, (t - m[1]) / 0.9))
                    e = pos(m, 1.0)
                    frames.append((t, e[0] + (rest[0] - e[0]) * u, e[1] + (rest[1] - e[1]) * u, 0.3 + 0.7 * u, m[4]))
                else:
                    e = pos(m, 1.0)
                    frames.append((t, e[0], e[1], 0.25, m[4]))
            f += 1
        return frames

    def finish(self, title: str | None = None, extra_svg: str = ""):
        c, gid = self.c, self.gid
        pp = c.asset(paper(ROOT / "build/.fontcache/paper.png"))
        filt = (f'<defs><filter id="{gid}f" x="-2%" y="-2%" width="104%" height="104%">'
                '<feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed="4" result="w"/>'
                '<feDisplacementMap in="SourceGraphic" in2="w" scale="2.4" xChannelSelector="R" yChannelSelector="G" result="d"/>'
                '<feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="11" result="g"/>'
                '<feColorMatrix in="g" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 3.4 0 0 0 -0.62" result="ga"/>'
                '<feComposite in="d" in2="ga" operator="in"/></filter></defs>')
        svg = (f'<svg class="pn-svg" viewBox="0 0 1920 1080" width="1920" height="1080" style="position:absolute;inset:0;overflow:visible" '
               f'fill="none" stroke-linecap="round" stroke-linejoin="round">{filt}<g filter="url(#{gid}f)">{"".join(self.svg)}</g>{extra_svg}</svg>')
        inner = (f'<div class="pn-paper" style="background-image:url({pp})"></div>'
                 f'<div class="pn-cam" id="{gid}cam">{svg}<div class="pn-html" style="filter:url(#{gid}f)">{"".join(self.html)}</div>'
                 f'{_pencil_svg(gid)}</div>')
        c.add(gid, self.t0, self.t1, inner, z=10, cls="page")
        for t, sc, x, y in self.camera:
            c.tw(f'tl.to("#{gid}cam",{{scale:{sc},x:{x},y:{y},duration:{max(0.2, t[1] - t[0]) if isinstance(t, tuple) else 1.2:.3f},'
                 f'ease:"sine.inOut"}},{(t[0] if isinstance(t, tuple) else t):.3f});')
        fr = self._pen_track()
        if fr:
            pen = f"#{gid}pen"
            js = ",".join(f"[{t:.4f},{x:.1f},{y:.1f},{l:.2f}]" for t, x, y, l, _ in fr)
            # one tween per frame would be heavy: a single proxy tween + onUpdate that looks up the frame
            colours = []
            for t, *_r, cc in fr:
                if not colours or colours[-1][1] != cc:
                    colours.append((t, cc))
            cj = ",".join(f'[{t:.4f},"{cc}"]' for t, cc in colours)
            c.tw(f'(function(){{const F=[{js}],C=[{cj}],el=document.querySelector("{pen}"),sh=el.querySelector(".pen-shadow");'
                 f'const o={{t:{fr[0][0]:.4f}}};'
                 f'tl.fromTo(o,{{t:{fr[0][0]:.4f}}},{{t:{fr[-1][0]:.4f},duration:{fr[-1][0] - fr[0][0]:.4f},ease:"none",onUpdate(){{'
                 f'let i=Math.min(F.length-1,Math.max(0,Math.round((o.t-F[0][0])*30)));const f=F[i];'
                 f'const s=1+f[3]*0.05;el.style.transform=`translate(${{f[1]}}px,${{f[2]}}px) scale(${{s}})`;'
                 f'sh.setAttribute("transform",`translate(${{16+f[3]*26}},${{20+f[3]*30}})`);sh.style.opacity=0.2-f[3]*0.08;'
                 f'let cc=C[0][1];for(const k of C){{if(k[0]<=o.t)cc=k[1];}}el.style.setProperty("--pc",cc);'
                 f'}}}},{fr[0][0]:.4f});}})();')
            c.tw(f'tl.set("{pen}",{{opacity:1}},{fr[0][0]:.4f});tl.set("{pen}",{{opacity:0}},{min(self.t1, fr[-1][0] + 0.05):.4f});')
        return gid


def css() -> str:
    faces = "".join(f'@font-face{{font-family:"Caveat";src:url(assets/fonts/caveat-{w}.woff2);font-weight:{w};}}' for w in CAVEAT)
    return faces + """
.pn-paper{position:absolute;inset:0;background-size:cover}
.pn-cam{position:absolute;inset:0;transform-origin:50% 50%}
.pn-html{position:absolute;inset:0}
.hw{position:absolute;font-family:Caveat,cursive;line-height:1.2;white-space:nowrap;transform-origin:left bottom}
.pen{position:absolute;left:0;top:0;width:0;height:0;opacity:0;transform-origin:0 0;z-index:5;will-change:transform}
"""


def fonts() -> dict:
    return {f"caveat-{w}.woff2": p for w, p in CAVEAT.items()}
