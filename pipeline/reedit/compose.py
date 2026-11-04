"""Re-edit composer: original talking-head video + new B-roll + graphics + captions + music.

projects/<slug>/reedit.yaml   source video, channel (look), script, words
projects/<slug>/edit.yaml     the edit as data:
  range: [start, end]          seconds of the original to produce (a test section or the whole video)
  shots:                       picture track; each runs until the next one starts
    - {at: 0 | "phrase", src: orig | path, from: seconds-in-source, move: push|pull|none}
  graphics:                    overlays, each starts at a phrase (or seconds) — see GRAPHICS below
  sfx: true                    whoosh/pop on graphic entrances
Steps: build base.mp4 (FFmpeg) -> HyperFrames composition (base + graphics + captions + audio) -> render.
"""
from __future__ import annotations

import html
import json
import math
from pathlib import Path

import yaml

from ..config import ROOT
from ..hf import Composition, render
from ..util import PipelineError, duration, ffmpeg, short_hash
from ..words import Words

FPS = 25


def load(P: Path):
    P = Path(P)
    meta = yaml.safe_load((P / "reedit.yaml").read_text())
    edit = yaml.safe_load((P / meta.get("edit", "edit.yaml")).read_text())
    ch = yaml.safe_load((ROOT / "channels" / meta["channel"] / "channel.yaml").read_text())
    words = Words.load(P / "words.json")
    return meta, edit, ch, words


def resolve(words: Words, at, after=0.0, lead=0.0):
    if isinstance(at, (int, float)):
        return float(at)
    end = at.startswith(">")
    return words.T(at[1:] if end else at, after=max(0.0, after - 1.0), end=end) - lead


# ---------------------------------------------------------------- base picture
ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "15", "-pix_fmt", "yuv420p"]
SHARPEN = "unsharp=5:5:0.9:5:5:0.0"


def _zoom(move: str, z: float, secs: float) -> str:
    return {"push": f"1+{z}*t/{secs:.3f}", "pull": f"1+{z}-{z}*t/{secs:.3f}", "none": "1"}[move]


def _src(P: Path, src, src_orig: Path) -> Path:
    return src_orig if (src or "orig") == "orig" else P / src


_BOUNDS: dict = {}


def _orig_segment(P: Path, src_orig: Path, start: float, secs: float) -> tuple[Path, float, list, str]:
    """For B-roll taken from the original edit: never run past the end of the original shot that
    contains `start` (that would show the next, unrelated shot). Returns (source, start, loop args, extra filter)."""
    key = str(P)
    if key not in _BOUNDS:
        aj = P / "build/analysis/analysis.json"
        _BOUNDS[key] = [(sh["start"], sh["end"]) for sh in json.loads(aj.read_text())["shots"]] if aj.exists() else []
    # reuse times were often read off rounded labels: snap a time just before a cut onto the shot it was meant for
    nxt = next((a0 for a0, _ in _BOUNDS[key] if 0 < a0 - start <= 0.15), None)
    if nxt is not None:
        start = nxt
    if any(abs(a0 - start) < 0.02 for a0, _ in _BOUNDS[key]):
        start += 1.0 / FPS   # skip the boundary frame itself
    shot = next(((a0, b0) for a0, b0 in _BOUNDS[key] if a0 - 0.01 <= start < b0), None)
    if not shot:
        return src_orig, start, [], ""
    avail = shot[1] - start - 0.08
    if avail >= secs or avail <= 0.2:
        return src_orig, start, [], ""     # (start may have been snapped)
    seg = P / "build/segments" / f"seg_{start:.2f}_{avail:.2f}.mp4"
    if not seg.exists():
        seg.parent.mkdir(parents=True, exist_ok=True)
        ffmpeg(["-ss", f"{start:.3f}", "-i", src_orig, "-t", f"{avail:.3f}", "-an", *ENC, seg])
    k = min(secs / avail, 1.6)
    slow = f"setpts={k:.3f}*PTS," if k > 1.02 else ""
    if avail * k < secs + 0.05:
        slow += "tpad=stop_mode=clone:stop_duration=60,"   # hold the last frame instead of a visible loop
    return seg, 0.0, [], slow


def _fit_stock(src: Path, start: float, secs: float) -> tuple[float, list, str]:
    """Fit a stock clip to a shot without visible loops: move the start earlier if needed,
    then slow it down (max 1.6x), and only loop as a last resort."""
    d = duration(src)
    if start + secs <= d - 0.05:
        return start, [], ""
    start = max(0.0, d - secs - 0.05)
    avail = d - start - 0.05
    if avail >= secs:
        return start, [], ""
    k = min(secs / max(avail, 0.1), 1.6)
    slow = f"setpts={k:.3f}*PTS," if k > 1.02 else ""
    if avail * k < secs + 0.05:
        slow += "tpad=stop_mode=clone:stop_duration=60,"
    return start, [], slow


def _full_clip(P, s, n, src_orig, clip, ch):
    src = _src(P, s.get("src"), src_orig)
    is_orig = (s.get("src") or "orig") == "orig"
    start = float(s.get("from", s["t0"] if is_orig else 0.0))
    secs = n / FPS
    z = ch["motion"]["host_push" if s.get("host") else "broll_push"]
    zexpr = _zoom(s.get("move", "push"), z, secs)
    slow = ""
    if is_orig and not s.get("host"):
        src, start, loop, slow = _orig_segment(P, src_orig, start, secs)
    elif not is_orig:
        start, loop, slow = _fit_stock(src, start, secs)
    else:
        loop = []
    if not loop and duration(src) < start + secs + 0.1:
        loop = ["-stream_loop", "-1"]
    sharpen = f",{SHARPEN}" if s.get("sharpen", is_orig and not s.get("host")) else ""
    vf = (f"{slow}scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps={FPS},"
          f"scale=w='trunc(1920*({zexpr})/2)*2':h=-2:eval=frame,crop=1920:1080{sharpen},setsar=1")
    ffmpeg([*loop, "-ss", f"{start:.3f}", "-i", src, "-vf", vf, "-frames:v", n, "-an", *ENC, "-r", FPS, clip])


def _split_assets(P: Path, ch) -> tuple[Path, Path, dict]:
    """Background with soft panel shadows + rounded-corner mask (Pillow), cached per look."""
    from PIL import Image, ImageDraw, ImageFilter
    sp = ch.get("split", {})
    m, gap, r = sp.get("margin", 70), sp.get("gap", 40), sp.get("radius", 36)
    W, H = (1920 - 2 * m - gap) // 2 // 2 * 2, (1080 - 2 * m) // 2 * 2
    geo = {"w": W, "h": H, "x1": m, "x2": m + W + gap, "y": m}
    d = P / "build/split"
    d.mkdir(parents=True, exist_ok=True)
    bg, mask = d / "bg.png", d / "mask.png"
    top, bot = sp.get("bg_top", "#F7F5F0"), sp.get("bg_bottom", "#ECE8E0")
    hx = lambda c: tuple(int(c.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    img = Image.new("RGB", (1920, 1080), hx(top))
    t, b2 = hx(top), hx(bot)
    px = ImageDraw.Draw(img)
    for y in range(1080):
        f = y / 1079
        px.line([(0, y), (1919, y)], fill=tuple(int(t[k] + (b2[k] - t[k]) * f) for k in range(3)))
    sh = Image.new("L", (1920, 1080), 0)
    ds = ImageDraw.Draw(sh)
    for x in (geo["x1"], geo["x2"]):
        ds.rounded_rectangle((x, m + 14, x + W, m + H + 14), r, fill=110)
    sh = sh.filter(ImageFilter.GaussianBlur(22))
    img = Image.composite(Image.new("RGB", (1920, 1080), (40, 40, 40)), img, sh)
    img.save(bg)
    mk = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mk).rounded_rectangle((0, 0, W - 1, H - 1), r, fill=255)
    mk.save(mask)
    return bg, mask, geo


def _split_clip(P, s, n, src_orig, clip, ch):
    """Two rounded panels on a clean background: host (left half of the original) | new B-roll."""
    bg, mask, g = _split_assets(P, ch)
    W, H = g["w"], g["h"]
    secs = n / FPS
    host_from = float(s.get("from", s["t0"]))
    r = s["right"]
    rsrc = _src(P, r.get("src"), src_orig)
    r_is_orig = (r.get("src") or "orig") == "orig"
    rfrom = float(r.get("from", 0.0))
    rslow = ""
    rloop = []
    if r_is_orig:
        rsrc, rfrom, rloop, rslow = _orig_segment(P, src_orig, rfrom, secs)
    else:
        rfrom, rloop, rslow = _fit_stock(rsrc, rfrom, secs)
    if not rloop and duration(rsrc) < rfrom + secs + 0.1:
        rloop = ["-stream_loop", "-1"]
    zr = _zoom(r.get("move", "push"), ch["motion"]["broll_push"], secs)
    sharpen = f",{SHARPEN}" if r.get("sharpen", r_is_orig) else ""
    hx = s.get("host_crop_x", 0)   # where the host sits in the original split frame (left half by default)
    fx = float(r.get("focus", 0.5))  # horizontal focus of the B-roll crop: 0 = left edge, 1 = right edge
    fc = (f"[1:v]fps={FPS},crop=960:1080:{hx}:0,scale={W}:-2,crop={W}:{H},format=rgba[h];"
          f"[2:v]{rslow}fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}:(iw-ow)*{fx}:(ih-oh)/2,"
          f"scale=w='trunc({W}*({zr})/2)*2':h=-2:eval=frame,crop={W}:{H}{sharpen},format=rgba[b];"
          f"[3:v]format=gray,split=2[m1][m2];[h][m1]alphamerge[hm];[b][m2]alphamerge[bm];"
          f"[0:v][hm]overlay={g['x1']}:{g['y']}:shortest=1[t];[t][bm]overlay={g['x2']}:{g['y']}:shortest=1,setsar=1,format=yuv420p[o]")
    ffmpeg(["-loop", "1", "-framerate", FPS, "-i", bg,
            "-ss", f"{host_from:.3f}", "-i", src_orig,
            *rloop, "-ss", f"{rfrom:.3f}", "-i", rsrc,
            "-loop", "1", "-framerate", FPS, "-i", mask,
            "-filter_complex", fc, "-map", "[o]", "-frames:v", n, "-an", *ENC, "-r", FPS, clip])


def build_base(P: Path, meta, edit, ch, words, log=print) -> tuple[Path, list[dict]]:
    a, b = edit["range"]
    shots, prev = [], a - 1
    for s in edit["shots"]:
        t = resolve(words, s["at"], prev, lead=0.08) if not isinstance(s["at"], (int, float)) else float(s["at"])
        shots.append({**s, "t0": max(a, t)})
        prev = t
    for i, s in enumerate(shots):
        s["t1"] = shots[i + 1]["t0"] if i + 1 < len(shots) else b
    _orig_segment(P, P / meta["source"]["file"], 0.0, 0.0)   # loads the original's shot boundaries
    bounds = _BOUNDS.get(str(P), [])
    for i, s in enumerate(shots):
        if (s.get("src") or "orig") == "orig" and (s.get("host") or s.get("split")) and i + 1 < len(shots):
            frm = float(s.get("from", s["t0"]))
            src_end = next((b0 for a0, b0 in bounds if a0 - 0.01 <= frm < b0), None)
            if src_end is not None:
                cap = s["t0"] + (src_end - frm) - 0.5 / FPS
                if s["t1"] > cap + 0.01 and cap > s["t0"] + 0.3:
                    s["t1"] = shots[i + 1]["t0"] = cap
    out = P / "build/base"
    out.mkdir(parents=True, exist_ok=True)
    src_orig = P / meta["source"]["file"]
    lines = []
    for i, s in enumerate(shots):
        f0, f1 = round((s["t0"] - a) * FPS), round((s["t1"] - a) * FPS)
        n = f1 - f0
        if n <= 0:
            raise PipelineError(f"shot {i} ({s['at']!r}) has no duration — check its anchor order")
        clip = out / f"s{i:03d}.mp4"
        key = short_hash(s.get("src"), s.get("from"), s.get("move"), s.get("host"), s.get("split"), s.get("right"),
                         s.get("sharpen"), n, ch["motion"], ch.get("split"), "clamp-v3")
        meta_f = clip.with_suffix(".key")
        if not (clip.exists() and meta_f.exists() and meta_f.read_text() == key):
            if s.get("split"):
                _split_clip(P, s, n, src_orig, clip, ch)
            else:
                _full_clip(P, s, n, src_orig, clip, ch)
            meta_f.write_text(key)
        lines.append(f"file '{clip.name}'")
        s["frames"] = n
    (out / "list.txt").write_text("\n".join(lines) + "\n")
    base = P / "build/hf/assets/base.mp4"
    base.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg(["-f", "concat", "-safe", "0", "-i", out / "list.txt", "-c", "copy", base])
    log(f"base: {len(shots)} shots, {duration(base):.2f}s")
    return base, shots


# ---------------------------------------------------------------- graphics
class Overlay(Composition):
    def __init__(self, words, out, ch, offset):
        super().__init__(words, out)
        self.ch = ch
        self.off = offset          # composition time = original time - offset
        self.sfx: list[tuple[float, str]] = []
        p = ch["palette"]
        self.INK, self.ACC, self.GOOD, self.WARN, self.MUTED = p["ink"], p["accent"], p["good"], p["warn"], p["muted"]

    def t(self, at, after=0.0, lead=0.0):
        return resolve(self.words, at, after + self.off, lead) - self.off

    def box(self, gid, t0, t1, inner, style):
        self.els.append(self.clip_div(gid, t0, t1, inner, style + ";z-index:30", "gfx"))

    def enter(self, sel, t0, frm="y:40,opacity:0", d=0.45, sfx="whoosh"):
        self.tw(f'tl.fromTo("{sel}",{{{frm}}},{{x:0,y:0,scale:1,opacity:1,duration:{d},ease:"back.out(1.6)"}},{t0:.3f});')
        if sfx:
            self.sfx.append((t0, sfx))

    def leave(self, sel, t1, d=0.3):
        self.tw(f'tl.to("{sel}",{{opacity:0,y:-20,duration:{d},ease:"power2.in"}},{t1 - d - 0.02:.3f});')

    # --- graphic types ---
    def checklist(self, g, t0, t1):
        gid = self.nid("ck")
        items = "".join(f'<div class="ck-item" id="{gid}i{k}"><span class="ck-box">{"✓" if g.get("ticks") else str(k + 1)}</span>{html.escape(it["t"])}</div>'
                        for k, it in enumerate(g["items"]))
        title = f'<div class="ck-title">{html.escape(g["title"])}</div>' if g.get("title") else ""
        pos = "left:90px;top:120px" if g.get("pos", "left") == "left" else "right:90px;top:120px"
        self.box(gid, t0, t1, f'<div class="card ck">{title}{items}</div>', f"position:absolute;{pos}")
        self.enter(f"#{gid} .card", t0, "x:-60,opacity:0")
        for k, it in enumerate(g["items"]):
            ta = self.t(it["a"], t0) if "a" in it else t0 + 0.3 + 0.35 * k
            self.enter(f"#{gid}i{k}", max(t0 + 0.2, ta - 0.1), "x:-30,opacity:0", 0.35, "pop")
        self.leave(f"#{gid} .card", t1)

    def badge(self, g, t0, t1):
        gid = self.nid("bd")
        self.box(gid, t0, t1, f'<div class="badge">{html.escape(g["text"])}</div>', "position:absolute;right:90px;top:90px")
        self.enter(f"#{gid} .badge", t0, "scale:0.4,opacity:0", 0.4, "pop")
        self.leave(f"#{gid} .badge", t1)

    def circle(self, g, t0, t1):
        gid = self.nid("cr")
        x, y, r = g["x"], g["y"], g["r"]
        L = int(2 * math.pi * r) + 40
        svg = (f'<svg width="1920" height="1080" viewBox="0 0 1920 1080" style="position:absolute;left:0;top:0">'
               f'<circle id="{gid}c" cx="{x}" cy="{y}" r="{r}" fill="none" stroke="{self.ACC}" stroke-width="12" '
               f'stroke-linecap="round" stroke-dasharray="{L}" stroke-dashoffset="{L}" transform="rotate(-90 {x} {y})"/></svg>')
        lab = (f'<div class="label" style="position:absolute;left:{g.get("lx", x + r + 30)}px;top:{g.get("ly", y - 40)}px">'
               f'{html.escape(g["label"])}</div>') if g.get("label") else ""
        self.box(gid, t0, t1, svg + lab, "position:absolute;inset:0")
        self.draw(f"#{gid}c", t0, 0.6, L)
        self.sfx.append((t0, "whoosh"))
        if lab:
            self.enter(f"#{gid} .label", t0 + 0.4, "x:-30,opacity:0", 0.4, None)
        self.leave(f"#{gid}", t1)

    def lower_third(self, g, t0, t1):
        gid = self.nid("lt")
        inner = (f'<div class="lt"><div class="lt-bar"></div><div><div class="lt-name">{html.escape(g["name"])}</div>'
                 f'<div class="lt-sub">{html.escape(g.get("sub", ""))}</div></div></div>')
        self.box(gid, t0, t1, inner, "position:absolute;left:90px;bottom:200px")
        self.enter(f"#{gid} .lt", t0, "x:-80,opacity:0", 0.5)
        self.leave(f"#{gid} .lt", t1)

    def statement(self, g, t0, t1):
        gid = self.nid("st")
        lines = "".join(f'<div class="st-line" id="{gid}l{k}" style="{"color:" + self.ACC if k == len(g["lines"]) - 1 else ""}">{html.escape(l)}</div>'
                        for k, l in enumerate(g["lines"]))
        self.box(gid, t0, t1, f'<div class="st-wrap"><div class="card st">{lines}</div></div>', "position:absolute;inset:0")
        self.enter(f"#{gid} .card", t0, "scale:0.85,opacity:0")
        for k in range(1, len(g["lines"])):
            self.enter(f"#{gid}l{k}", t0 + 0.45 * k, "y:20,opacity:0", 0.35, "pop")
        self.leave(f"#{gid} .card", t1)

    def tag(self, g, t0, t1):
        gid = self.nid("tg")
        col = self.WARN if g.get("tone") == "warn" else self.INK
        self.box(gid, t0, t1, f'<div class="tag" style="border-left:12px solid {col}">{html.escape(g["text"])}</div>',
                 "position:absolute;left:90px;top:110px")
        self.enter(f"#{gid} .tag", t0, "x:-60,opacity:0")
        self.leave(f"#{gid} .tag", t1)

    def compare(self, g, t0, t1):
        gid = self.nid("cp")
        def col(c, k):
            return (f'<div class="cmp-col" id="{gid}c{k}"><div class="cmp-h">{html.escape(c["title"])}</div>'
                    f'<div class="cmp-b">{html.escape(c["text"])}</div></div>')
        inner = f'<div class="cmp-wrap"><div class="card cmp">{col(g["left"], 0)}<div class="cmp-vs">vs</div>{col(g["right"], 1)}</div></div>'
        self.box(gid, t0, t1, inner, "position:absolute;inset:0")
        self.enter(f"#{gid} .card", t0, "scale:0.9,opacity:0")
        if g.get("pick"):
            k = 0 if g["pick"]["side"] == "left" else 1
            tp = self.t(g["pick"]["at"], t0)
            self.tw(f'tl.to("#{gid}c{k}",{{backgroundColor:"{self.ACC}",scale:1.04,duration:0.35,ease:"back.out(2)"}},{tp:.3f});')
            self.tw(f'tl.to("#{gid}c{1 - k}",{{opacity:0.45,duration:0.35}},{tp:.3f});')
            self.sfx.append((tp, "pop"))
        self.leave(f"#{gid} .card", t1)

    def timer(self, g, t0, t1):
        gid = self.nid("tm")
        self.box(gid, t0, t1, f'<div class="timer"><span class="tm-dot"></span><span id="{gid}v">0:00</span>'
                 f'<span class="tm-of">/ {html.escape(g.get("of", "2:00"))}</span></div>', "position:absolute;right:90px;top:90px")
        self.enter(f"#{gid} .timer", t0, "scale:0.5,opacity:0", 0.4, "pop")
        speed = float(g.get("speed", 1.0))   # screen time can be compressed: show real routine time
        for sec in range(1, int((t1 - t0) * speed) + 1):
            self.tw(f'tl.set("#{gid}v",{{textContent:"{sec // 60}:{sec % 60:02d}"}},{t0 + sec / speed:.3f});')
        self.tw(f'tl.fromTo("#{gid} .tm-dot",{{opacity:1}},{{opacity:0.25,duration:0.5,repeat:{max(1, int((t1 - t0) / 1.0))},yoyo:true,ease:"sine.inOut"}},{t0:.3f});')
        self.leave(f"#{gid} .timer", t1)

    def step(self, g, t0, t1):
        gid = self.nid("sp")
        bgc = self.WARN if g.get("tone") == "warn" else self.GOOD
        self.box(gid, t0, t1, f'<div class="step"><span class="sp-n" style="background:{bgc}">{g["n"]}</span>{html.escape(g["text"])}</div>',
                 "position:absolute;left:90px;top:110px")
        self.enter(f"#{gid} .step", t0, "x:-60,opacity:0")
        self.leave(f"#{gid} .step", t1)

    def alert(self, g, t0, t1):
        gid = self.nid("al")
        self.box(gid, t0, t1, f'<div class="alert">⚠ {html.escape(g["text"])}</div>', "position:absolute;left:0;right:0;top:120px;display:flex;justify-content:center")
        self.enter(f"#{gid} .alert", t0, "scale:0.6,opacity:0", 0.35, "pop")
        self.leave(f"#{gid} .alert", t1)

    def title(self, g, t0, t1):
        gid = self.nid("tt")
        sub = f'<div class="tt-sub">{html.escape(g["sub"])}</div>' if g.get("sub") else ""
        self.box(gid, t0, t1, f'<div class="tt-wrap"><div class="tt">{html.escape(g["text"])}</div>{sub}</div>',
                 "position:absolute;inset:0")
        self.enter(f"#{gid} .tt", t0, "scale:1.6,opacity:0", 0.45, "whoosh")
        if sub:
            self.enter(f"#{gid} .tt-sub", t0 + 0.3, "y:20,opacity:0", 0.35, None)
        self.leave(f"#{gid} .tt-wrap", t1)

    def cards(self, g, t0, t1):
        """N columns, each appearing on its own cue; optional mark (✓ / ✗) per column on a later cue."""
        gid = self.nid("cd")
        cols = ""
        for k, c in enumerate(g["cols"]):
            cols += (f'<div class="cd-col" id="{gid}c{k}"><div class="cd-h">{html.escape(c["title"])}</div>'
                     f'<div class="cd-b">{html.escape(c.get("text", ""))}</div>'
                     f'<div class="cd-mark" id="{gid}m{k}">{c.get("mark", "")}</div></div>')
        title = f'<div class="cd-title">{html.escape(g["title"])}</div>' if g.get("title") else ""
        self.box(gid, t0, t1, f'<div class="cmp-wrap"><div class="card cd">{title}<div class="cd-row">{cols}</div></div></div>',
                 "position:absolute;inset:0")
        self.enter(f"#{gid} .card", t0, "scale:0.9,opacity:0")
        for k, c in enumerate(g["cols"]):
            if "a" in c:
                self.enter(f"#{gid}c{k}", self.t(c["a"], t0), "y:30,opacity:0", 0.35, "pop")
            if c.get("mark") and "ma" in c:
                ok = c["mark"] == "✓"
                self.tw(f'tl.fromTo("#{gid}m{k}",{{scale:0,opacity:0}},{{scale:1,opacity:1,duration:0.3,ease:"back.out(2.5)"}},{self.t(c["ma"], t0):.3f});')
                self.tw(f'tl.set("#{gid}m{k}",{{backgroundColor:"{self.GOOD if ok else self.WARN}"}},{t0:.3f});')
                self.sfx.append((self.t(c["ma"], t0), "pop"))
        self.leave(f"#{gid} .card", t1)

    def disposal(self, g, t0, t1):
        """Top-down cutaway: spinning plate with two swivel lugs, grind ring, food flung outward."""
        gid = self.nid("dp")
        cx, cy, R = 760, 540, 330
        teeth = "".join(
            f'<path d="M{cx + (R) * math.cos(a):.0f},{cy + R * math.sin(a):.0f} L{cx + (R - 34) * math.cos(a + 0.05):.0f},{cy + (R - 34) * math.sin(a + 0.05):.0f} '
            f'L{cx + R * math.cos(a + 0.1):.0f},{cy + R * math.sin(a + 0.1):.0f}" fill="#8A969C"/>'
            for a in [k * 2 * math.pi / 60 for k in range(60)])
        bits = "".join(f'<circle class="{gid}bit" cx="{cx}" cy="{cy}" r="9" fill="#C9A227"/>' for _ in range(10))
        svg = (f'<svg width="1920" height="1080" viewBox="0 0 1920 1080" style="position:absolute;left:0;top:0">'
               f'<circle cx="{cx}" cy="{cy}" r="{R + 30}" fill="#DDE2E4"/>'
               f'<g id="{gid}ring">{teeth}<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="#6B777D" stroke-width="10"/></g>'
               f'<g id="{gid}plate">'
               f'<circle cx="{cx}" cy="{cy}" r="{R - 70}" fill="#B9C3C7" stroke="#6B777D" stroke-width="8"/>'
               + "".join(f'<circle cx="{cx + 70 * math.cos(a):.0f}" cy="{cy + 70 * math.sin(a):.0f}" r="22" fill="#56636A"/>' for a in (0, 2.1, 4.2))
               + f'<rect x="{cx + 120}" y="{cy - 22}" width="110" height="44" rx="14" fill="{self.ACC}" stroke="{self.INK}" stroke-width="5"/>'
               f'<rect x="{cx - 230}" y="{cy - 22}" width="110" height="44" rx="14" fill="{self.ACC}" stroke="{self.INK}" stroke-width="5"/>'
               f'</g>{bits}'
               f'<g id="{gid}x" opacity="0"><line x1="{cx - 150}" y1="{cy - 150}" x2="{cx + 150}" y2="{cy + 150}" stroke="{self.WARN}" stroke-width="26" stroke-linecap="round"/>'
               f'<line x1="{cx + 150}" y1="{cy - 150}" x2="{cx - 150}" y2="{cy + 150}" stroke="{self.WARN}" stroke-width="26" stroke-linecap="round"/></g></svg>')
        labels = ""
        for k, lb in enumerate(g.get("labels", [])):
            labels += (f'<div class="dg-lab" id="{gid}l{k}" style="left:{lb.get("x", 1180)}px;top:{lb.get("y", 260 + 130 * k)}px">'
                       f'<span class="dg-dot" style="background:{self.ACC}"></span>{html.escape(lb["t"])}</div>')
        head = f'<div class="dg-head">{html.escape(g.get("title", "Inside the disposal"))}</div>'
        self.box(gid, t0, t1, f'<div class="dg-bg"></div>{svg}{head}{labels}', "position:absolute;inset:0")
        self.enter(f"#{gid}", t0, "opacity:0", 0.4)
        spin = self.t(g["spin"], t0) if g.get("spin") else t0 + 0.5
        self.tw(f'tl.fromTo("#{gid}plate",{{rotation:0,svgOrigin:"{cx} {cy}"}},{{rotation:{int((t1 - spin) * 540)},svgOrigin:"{cx} {cy}",duration:{max(0.5, t1 - spin):.3f},ease:"power1.in"}},{spin:.3f});')
        if g.get("no_blades"):
            tx = self.t(g["no_blades"], t0)
            self.tw(f'tl.fromTo("#{gid}x",{{opacity:0,scale:0.4,svgOrigin:"{cx} {cy}"}},{{opacity:1,scale:1,duration:0.3,ease:"back.out(2)"}},{tx:.3f});')
            self.tw(f'tl.to("#{gid}x",{{opacity:0,duration:0.3}},{tx + 1.6:.3f});')
            self.sfx.append((tx, "pop"))
        if g.get("fling"):
            tf = self.t(g["fling"], t0)
            for k in range(10):
                ang = k * 2 * math.pi / 10 + 0.3
                self.tw(f'tl.fromTo("#{gid} .{gid}bit:nth-of-type({k + 1})",{{attr:{{cx:{cx},cy:{cy}}},opacity:1}},'
                        f'{{attr:{{cx:{cx + (R - 30) * math.cos(ang):.0f},cy:{cy + (R - 30) * math.sin(ang):.0f}}},duration:0.6,ease:"power2.out",'
                        f'repeat:{max(1, int((t1 - tf) / 1.2))},repeatDelay:0.6}},{tf + k * 0.05:.3f});')
        else:
            self.tw(f'tl.set("#{gid} .{gid}bit",{{opacity:0}},{t0:.3f});')
        for k, lb in enumerate(g.get("labels", [])):
            self.enter(f"#{gid}l{k}", self.t(lb["a"], t0), "x:40,opacity:0", 0.35, "pop")
        self.leave(f"#{gid}", t1)

    def trap(self, g, t0, t1):
        """U-trap side view: water seal blocks sewer gas; optional 'dry' cue drains it and lets gas through."""
        gid = self.nid("tp")
        pipe = "M520,180 L520,640 Q520,840 760,840 Q1000,840 1000,640 L1000,560 L1500,560"
        water = "M560,520 L560,640 Q560,800 760,800 Q960,800 960,640 L960,520"
        svg = (f'<svg width="1920" height="1080" viewBox="0 0 1920 1080" style="position:absolute;left:0;top:0">'
               f'<path d="{pipe}" fill="none" stroke="#C7CED1" stroke-width="110" stroke-linecap="round" stroke-linejoin="round"/>'
               f'<path id="{gid}w" d="{water}" fill="none" stroke="#5DADE2" stroke-width="80" stroke-linecap="round" opacity="0.9"/>'
               f'<path d="{pipe}" fill="none" stroke="{self.INK}" stroke-width="8" stroke-opacity=".25"/>'
               + "".join(f'<circle class="{gid}gas" cx="1450" cy="560" r="16" fill="#8DB255" opacity="0"/>' for _ in range(6))
               + '</svg>')
        labels = ""
        for k, lb in enumerate(g.get("labels", [])):
            labels += (f'<div class="dg-lab" id="{gid}l{k}" style="left:{lb["x"]}px;top:{lb["y"]}px">'
                       f'<span class="dg-dot" style="background:{lb.get("c", self.ACC)}"></span>{html.escape(lb["t"])}</div>')
        head = f'<div class="dg-head">{html.escape(g.get("title", "The bend under your sink"))}</div>'
        self.box(gid, t0, t1, f'<div class="dg-bg"></div>{svg}{head}{labels}', "position:absolute;inset:0")
        self.enter(f"#{gid}", t0, "opacity:0", 0.4)
        # gas puffs drift in from the sewer side and stop at the water (or pass when dry)
        dry = self.t(g["dry"], t0) if g.get("dry") else None
        for k in range(6):
            st = t0 + 0.6 + k * 0.5
            self.tw(f'tl.fromTo("#{gid} .{gid}gas:nth-of-type({k + 1})",{{attr:{{cx:1450,cy:560}},opacity:0.9}},'
                    f'{{attr:{{cx:1010,cy:560}},opacity:0.2,duration:1.4,ease:"sine.in",repeat:3,repeatDelay:1.6}},{st:.3f});')
        if dry:
            self.tw(f'tl.to("#{gid}w",{{opacity:0,duration:1.0}},{dry:.3f});')
            for k in range(6):
                self.tw(f'tl.fromTo("#{gid} .{gid}gas:nth-of-type({k + 1})",{{attr:{{cx:1450,cy:560}},opacity:0.9}},'
                        f'{{attr:{{cx:520,cy:180}},opacity:0.9,duration:2.2,ease:"none"}},{dry + 0.8 + k * 0.35:.3f});')
        for k, lb in enumerate(g.get("labels", [])):
            self.enter(f"#{gid}l{k}", self.t(lb["a"], t0), "x:40,opacity:0", 0.35, "pop")
        self.leave(f"#{gid}", t1)

    # --- captions with the spoken word highlighted ---
    def word_captions(self, a, b):
        cap = self.ch["captions"]
        out = []
        groups, cur = [], []
        ws = [w for w in self.words.words if a <= w["s"] < b]
        for w in ws:
            cur.append(w)
            txt = " ".join(x["w"] for x in cur)
            if w["w"][-1] in ".?!,;:" or len(cur) >= cap["max_words"] or len(txt) >= cap["max_chars"]:
                groups.append(cur); cur = []
        if cur:
            groups.append(cur)
        for k, g in enumerate(groups):
            s = g[0]["s"] - self.off
            e = (groups[k + 1][0]["s"] if k + 1 < len(groups) else g[-1]["e"] + 0.4) - self.off
            e = min(e, g[-1]["e"] - self.off + 0.6)
            spans = "".join(f'<span id="cw{k}_{j}">{html.escape(w["w"])}</span> ' for j, w in enumerate(g))
            out.append(f'<div id="cg{k}" class="clip capwrap" data-start="{s:.3f}" data-duration="{max(0.2, e - s):.3f}">'
                       f'<div class="cap">{spans.strip()}</div></div>')
            self.tw(f'tl.fromTo("#cg{k} .cap",{{opacity:0,y:10}},{{opacity:1,y:0,duration:0.12}},{s:.3f});')
            for j, w in enumerate(g):
                ws_ = w["s"] - self.off
                self.tw(f'tl.set("#cw{k}_{j}",{{color:"{self.ACC}"}},{ws_:.3f});')
                if j + 1 < len(g):
                    self.tw(f'tl.set("#cw{k}_{j}",{{color:"#FFFFFF"}},{g[j + 1]["s"] - self.off:.3f});')
        return "".join(out)

    def css(self):
        p, ty, cap = self.ch["palette"], self.ch["type"], self.ch["captions"]
        return f"""
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1920px;height:1080px;overflow:hidden;background:#000}}
#root{{position:relative;width:100%;height:100%;overflow:hidden;font-family:{ty['font']},sans-serif;font-weight:{ty['weight']};color:{p['ink']}}}
#base{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}
.card{{background:{p['card']};border-radius:26px;box-shadow:0 18px 50px rgba(0,0,0,.28),0 2px 6px rgba(0,0,0,.12)}}
.ck{{padding:30px 40px 34px;min-width:560px}}
.ck-title{{font-size:38px;color:{p['muted']};letter-spacing:.5px;margin-bottom:14px}}
.ck-item{{display:flex;align-items:center;gap:20px;font-size:52px;line-height:1.25;margin-top:12px}}
.ck-box{{display:inline-flex;align-items:center;justify-content:center;width:62px;height:62px;border-radius:18px;background:{p['accent']};font-size:38px;color:{p['ink']};flex:none}}
.badge{{background:{p['accent']};color:{p['ink']};font-size:46px;padding:16px 32px;border-radius:999px;box-shadow:0 12px 30px rgba(0,0,0,.3)}}
.label{{background:{p['card']};font-size:44px;padding:12px 26px;border-radius:16px;box-shadow:0 12px 30px rgba(0,0,0,.3)}}
.lt{{display:flex;align-items:center;gap:22px;background:{p['card']};padding:22px 38px 24px 26px;border-radius:22px;box-shadow:0 14px 40px rgba(0,0,0,.3)}}
.lt-bar{{width:12px;height:92px;border-radius:6px;background:{p['accent']}}}
.lt-name{{font-size:56px;line-height:1.05}}
.lt-sub{{font-size:38px;color:{p['muted']};margin-top:6px}}
.st-wrap,.cmp-wrap,.tt-wrap{{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;padding-bottom:120px}}
.st{{padding:40px 70px;text-align:center}}
.st-line{{font-size:110px;line-height:1.05}}
.tag{{background:{p['card']};font-size:48px;padding:20px 34px;border-radius:18px;box-shadow:0 12px 30px rgba(0,0,0,.3);white-space:nowrap}}
.cmp{{display:flex;align-items:stretch;gap:26px;padding:34px}}
.cmp-col{{width:600px;padding:30px 34px;border-radius:20px;background:#F3F5F6}}
.cmp-h{{font-size:58px;margin-bottom:10px}}
.cmp-b{{font-size:42px;color:{p['muted']};line-height:1.25}}
.cmp-vs{{align-self:center;font-size:44px;color:{p['muted']}}}
.timer{{display:flex;align-items:center;gap:16px;background:rgba(31,42,48,.92);color:#fff;font-size:64px;padding:14px 32px;border-radius:22px;
  font-variant-numeric:tabular-nums;box-shadow:0 12px 30px rgba(0,0,0,.3)}}
.tm-dot{{width:22px;height:22px;border-radius:50%;background:{p['warn']}}}
.tm-of{{font-size:34px;opacity:.6}}
.step{{display:flex;align-items:center;gap:22px;background:{p['card']};font-size:48px;padding:18px 34px 20px 20px;border-radius:20px;box-shadow:0 12px 30px rgba(0,0,0,.3)}}
.sp-n{{display:inline-flex;align-items:center;justify-content:center;width:70px;height:70px;border-radius:50%;background:{p['good']};color:#fff;font-size:44px}}
.alert{{background:{p['warn']};color:#fff;font-size:52px;padding:18px 40px;border-radius:999px;box-shadow:0 12px 30px rgba(0,0,0,.35)}}
.tt{{font-size:150px;line-height:1;color:#fff;letter-spacing:2px;text-transform:uppercase;
  text-shadow:0 6px 0 {p['ink']},0 14px 40px rgba(0,0,0,.6)}}
.tt-sub{{margin-top:22px;background:{p['accent']};color:{p['ink']};font-size:42px;padding:10px 28px;border-radius:999px}}
.cd{{padding:34px 40px}}
.cd-title{{font-size:46px;margin:0 0 20px 6px}}
.cd-row{{display:flex;gap:24px}}
.cd-col{{position:relative;width:440px;padding:28px 30px 34px;border-radius:20px;background:#F3F5F6}}
.cd-h{{font-size:56px;margin-bottom:10px}}
.cd-b{{font-size:38px;color:{p['muted']};line-height:1.25}}
.cd-mark{{position:absolute;right:-14px;top:-14px;width:70px;height:70px;border-radius:50%;color:#fff;font-size:44px;
  display:flex;align-items:center;justify-content:center;opacity:0;box-shadow:0 8px 20px rgba(0,0,0,.25)}}
.dg-bg{{position:absolute;inset:0;background:linear-gradient(#F7F5F0,#ECE8E0)}}
.dg-head{{position:absolute;left:90px;top:70px;font-size:60px}}
.dg-lab{{position:absolute;display:flex;align-items:center;gap:16px;background:{p['card']};font-size:46px;padding:14px 28px;border-radius:18px;
  box-shadow:0 10px 26px rgba(0,0,0,.18)}}
.dg-dot{{width:22px;height:22px;border-radius:50%;flex:none}}
.capwrap{{position:absolute;left:0;right:0;bottom:{cap['bottom']}px;display:flex;justify-content:center;z-index:40}}
.cap{{color:#fff;font-size:{cap['size']}px;line-height:1.15;text-align:center;max-width:1500px;
 text-shadow:3px 3px 0 #000,-3px 3px 0 #000,3px -3px 0 #000,-3px -3px 0 #000,0 3px 0 #000,0 -3px 0 #000,3px 0 0 #000,-3px 0 0 #000,0 8px 18px rgba(0,0,0,.55)}}
"""


GRAPHICS = ("checklist", "badge", "circle", "lower_third", "statement", "tag", "compare", "timer", "step", "alert", "title",
            "cards", "disposal", "trap")


def build_overlay(P, meta, edit, ch, words, log=print, out: Path | None = None):
    a, b = edit["range"]
    out = out or P / "build/hf"
    c = Overlay(words, out, ch, a)
    for g in edit.get("graphics", []):
        if g["type"] not in GRAPHICS:
            raise PipelineError(f"unknown graphic type {g['type']}")
        t0 = resolve(c.words, g["at"], 0.0, 0.05) - c.off   # absolute lookup, so range renders match the full edit
        if "until" in g:
            t1 = (b - a) if g["until"] == "end" else c.t(g["until"], t0, lead=0.1)
        else:
            t1 = t0 + g.get("dur", 3.0)
        t1 = min(t1, b - a)
        if t0 >= b - a or t1 <= t0 or t1 <= 0:
            continue
        getattr(c, g["type"])(g, t0, t1)
    end = b - a
    base_tag = f'<video id="base" class="clip" src="assets/base.mp4" muted data-start="0" data-duration="{end:.3f}"></video>'
    c.els.insert(0, base_tag)
    caps = c.word_captions(a, b)
    path = c.write(c.css(), end, caps)
    (out / "sfx.json").write_text(json.dumps(c.sfx))
    log(f"overlay: {len(edit.get('graphics', []))} graphics, {len(c.sfx)} sfx cues, {len(c.js)} tweens")
    return path, c.sfx


# ---------------------------------------------------------------- audio
def _sfx_files(d: Path):
    d.mkdir(parents=True, exist_ok=True)
    whoosh, pop = d / "whoosh.wav", d / "pop.wav"
    if not whoosh.exists():   # band-passed noise swelling and fading: a soft air whoosh
        ffmpeg(["-f", "lavfi", "-i", "anoisesrc=color=pink:duration=0.45:amplitude=0.6:seed=7",
                "-af", "highpass=f=500,lowpass=f=5000,afade=t=in:d=0.18,afade=t=out:st=0.2:d=0.25,volume=0.9", whoosh])
    if not pop.exists():      # short descending sine blip
        ffmpeg(["-f", "lavfi", "-i", "aevalsrc='0.6*sin(2*PI*(700-500*t/0.09)*t)*exp(-t*35)':s=44100:d=0.12", pop])
    return {"whoosh": whoosh, "pop": pop}


def _music_bed(P: Path, a: float, end: float) -> Path | None:
    """Lay the music.json tracks (each over [start, end] of the original timeline) into one bed with crossfades."""
    mj = P / "music.json"
    if not mj.exists():
        return None
    tracks = [t for t in json.loads(mj.read_text())["tracks"] if t["end"] > a and t["start"] < a + end]
    if not tracks:
        return None
    args, f, labs = [], [], []
    for i, t in enumerate(tracks):
        st, en = max(t["start"], a) - a, min(t["end"], a + end) - a
        d = en - st
        ms = int(st * 1000)
        args += ["-stream_loop", "-1", "-i", P / t["file"]]
        fi = 0.5 if i == 0 else 3.0
        f.append(f"[{i}]atrim={t.get('offset', 0)}:{t.get('offset', 0) + d:.3f},asetpts=PTS-STARTPTS,aresample=44100,"
                 f"aformat=channel_layouts=stereo,afade=t=in:d={fi},afade=t=out:st={max(0, d - 3):.3f}:d=3,adelay={ms}|{ms}[m{i}]")
        labs.append(f"[m{i}]")
    f.append(f"{''.join(labs)}amix=inputs={len(labs)}:duration=longest:normalize=0,apad,atrim=0:{end:.3f}[o]")
    out = P / "build/audio_parts/music_bed.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg([*args, "-filter_complex", ";".join(f), "-map", "[o]", out])
    return out


def build_audio(P, meta, edit, ch, sfx_cues, music: Path | None, log=print) -> Path:
    a, b = edit["range"]
    end = b - a
    aud = ch["audio"]
    out = P / "build/hf/assets/audio.wav"
    tmp = P / "build/audio_parts"
    tmp.mkdir(parents=True, exist_ok=True)
    src = P / meta["source"]["file"]
    voice = tmp / "voice.wav"
    ffmpeg(["-ss", f"{a:.3f}", "-t", f"{end:.3f}", "-i", src, "-vn", "-ac", "2", "-ar", "44100",
            "-af", f"loudnorm=I={aud['voice_lufs']}:TP=-1.5:LRA=11", voice])
    if music is None:
        music = _music_bed(P, a, end)
    inputs, chains, mixes = ["-i", voice], [], ["[v1]"]
    chains.append("[0]anull[v1]")
    n = 1
    if music and music.exists():
        chains[0] = "[0]asplit=2[v1][sc]"
        inputs += ["-stream_loop", "-1", "-i", music]
        chains.append(f"[{n}]atrim=0:{end:.3f},aresample=44100,aformat=channel_layouts=stereo,"
                      f"loudnorm=I={aud['music_lufs']}:TP=-3,volume={aud['music_gain']},"
                      f"afade=t=in:d=1.5,afade=t=out:st={max(0, end - 2.5):.2f}:d=2.5[mu];"
                      "[mu][sc]sidechaincompress=threshold=0.03:ratio=5:attack=30:release=500[duck]")
        mixes.append("[duck]")
        n += 1
    if edit.get("sfx", True) and sfx_cues:
        files = _sfx_files(P / "build/sfx")
        for t, kind in sfx_cues:
            inputs += ["-i", files[kind]]
            ms = int(max(0, t) * 1000)
            chains.append(f"[{n}]volume={aud['sfx_db']}dB,adelay={ms}|{ms},aformat=channel_layouts=stereo[x{n}]")
            mixes.append(f"[x{n}]")
            n += 1
    fc = ";".join(chains) + f";{''.join(mixes)}amix=inputs={len(mixes)}:duration=first:normalize=0,alimiter=limit=0.95[o]"
    ffmpeg([*inputs, "-filter_complex", fc, "-map", "[o]", "-t", f"{end:.3f}", "-ar", "44100", out])
    log(f"audio: voice + {'music + ' if music else ''}{len(sfx_cues)} sfx → {out.name}")
    return out


def qa_cuts(P: Path, shots: list[dict], a: float, log=print) -> list[float]:
    """Every hard cut in the base picture should be a planned shot change. Anything else is a flash
    frame, a reused clip running into its neighbour, or a visible loop."""
    from .analyze import detect_cuts
    base = P / "build/hf/assets/base.mp4"
    planned, f = [], 0
    for s in shots:
        planned.append(f / FPS)
        f += s["frames"]
    cuts = detect_cuts(base, threshold=12.0)
    stray = [c for c in cuts if min(abs(c - p) for p in planned) > 0.12]
    for c in stray:
        log(f"⚠ unplanned cut at {a + c:7.2f}s (composition {c:.2f}s)")
    log(f"QA: {len(cuts)} cuts detected, {len(planned)} planned, {len(stray)} unplanned")
    return stray


def run(P: Path, music: Path | None = None, do_render=True, log=print) -> Path:
    P = Path(P)
    meta, edit, ch, words = load(P)
    _, shots = build_base(P, meta, edit, ch, words, log)
    stray = qa_cuts(P, shots, edit["range"][0], log)
    if stray and not edit.get("allow_stray_cuts"):
        raise PipelineError(f"{len(stray)} unplanned cut(s) in the base picture — fix before rendering")
    _, sfx = build_overlay(P, meta, edit, ch, words, log)
    build_audio(P, meta, edit, ch, sfx, music, log)
    if not do_render:
        return P / "build/hf/index.html"
    a, b = edit["range"]
    out = P / "out" / f"{P.name}_{int(a)}-{int(b)}s.mp4"
    out.parent.mkdir(exist_ok=True)
    render(P / "build/hf", out, fps=FPS, quality="looks", log=log)
    log(f"rendered {out}")
    return out


def remix(P: Path, music: Path | None, log=print) -> Path:
    """Rebuild the audio (voice + music + sfx) and swap it into the rendered video — no re-render."""
    P = Path(P)
    meta, edit, ch, words = load(P)
    sfx = [tuple(x) for x in json.loads((P / "build/hf/sfx.json").read_text())]
    audio = build_audio(P, meta, edit, ch, sfx, music, log)
    a, b = edit["range"]
    video = P / "out" / f"{P.name}_{int(a)}-{int(b)}s.mp4"
    tmp = video.with_suffix(".remix.mp4")
    ffmpeg(["-i", video, "-i", audio, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-movflags", "+faststart", tmp])
    tmp.replace(video)
    log(f"remixed audio into {video}")
    return video


if __name__ == "__main__":
    import sys
    m = Path(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] != "-" else None
    if "--remix" in sys.argv:
        remix(Path(sys.argv[1]), m)
    else:
        run(Path(sys.argv[1]), m, do_render="--no-render" not in sys.argv)
