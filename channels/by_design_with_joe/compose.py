"""By Design With Joe composer (Mr. Davos blueprint): graded cinematic B-roll + sparse premium text + full-frame pages + drawn illustrations.

projects/<slug>/episode.yaml   title, channel: by_design_with_joe, voice
projects/<slug>/words.json     word timings (pipeline.align.whisper_align)
projects/<slug>/edit.yaml      the edit as data:

  range: [a, b]                     seconds of the narration to render (a test section or the whole video)
  shots:                            picture track; each runs until the next one starts
    - {at: "phrase" | seconds, src: broll/<id>.mp4, from: 2.0, move: push|pull|left|right|none, speed: 1.0}
    - {at: ..., page: chapter, n: 1, title: "WHAT PILOTS DO"}
    - {at: ..., page: roadmap, items: [{t: "...", a: "phrase"}, ...]}        numbered tiles that light in turn
    - {at: ..., page: define, term: "Checkride", phon: "/ˈtʃɛk.raɪd/", text: "..."}
    - {at: ..., page: split, src: broll/..., from: 0, title: "...", items: [{t: "...", v: "$93/hr", a: "phrase"}]}
    - {at: ..., page: illus, name: <function in channels/by_design_with_joe/illus.py>, ...its own fields}
  text:                             overlays on footage (sparse: numbers, key terms, names)
    - {at: "phrase", until: ">phrase" | dur: 3, kind: big, text: "150", sub: "PEOPLE ON BOARD"}
    - {at: ..., kind: label, text: "The *captain*", sub: "Left seat"}       *word* = accent colour
    - {at: ..., kind: questions, items: [{t: "...", a: "phrase"}]}
    - {at: ..., kind: quote, text: "...", who: "..."}
  music_dips: ["phrase", ...]       extra music dips (chapter cards dip automatically)

Owner rules enforced here: hard cuts only, no SFX, no subtitles, no clip used more than twice
(`check` also warns on shots longer than retention.max_shot outside pages), like & subscribe at the end.

  python -m channels.by_design_with_joe.compose <project_dir> [--check | --no-render | --remix]
"""
from __future__ import annotations

import html

from channels.by_design_with_joe.typo import esc
import json
import re
import sys
from pathlib import Path

import yaml

from pipeline.config import ROOT
from pipeline.hf import Composition, render
from pipeline.util import PipelineError, duration, ffmpeg, short_hash
from pipeline.words import Words

HERE = Path(__file__).resolve().parent
FONT_DIR = Path("/usr/share/fonts/opentype/inter")
FONTS = {"Inter-Medium.otf": 500, "Inter-SemiBold.otf": 600, "Inter-Bold.otf": 700,
         "InterDisplay-Bold.otf": 700, "InterDisplay-Black.otf": 900, "InterDisplay-Light.otf": 300}
PAGES = ("chapter", "roadmap", "define", "split", "illus", "photo", "black")


def load(P: Path):
    P = Path(P)
    ep = yaml.safe_load((P / "episode.yaml").read_text())
    edit = yaml.safe_load((P / ep.get("edit", "edit.yaml")).read_text())
    ch = yaml.safe_load((HERE / "channel.yaml").read_text())
    words = Words.load(P / "words.json")
    return ep, edit, ch, words


def resolve(words: Words, at, after=0.0, lead=0.0) -> float:
    if isinstance(at, (int, float)):
        return float(at)
    end = at.startswith(">")
    return words.T(at[1:] if end else at, after=max(0.0, after - 1.0), end=end) - lead


# ---------------------------------------------------------------- picture track
def plan_shots(edit, words, fps) -> list[dict]:
    a, b = edit["range"]
    shots, prev = [], 0.0
    for s in edit["shots"]:
        t = resolve(words, s["at"], prev, lead=0.06)
        shots.append({**s, "_t": t})
        prev = t
    for i in range(1, len(shots)):
        if shots[i]["_t"] <= shots[i - 1]["_t"]:
            raise PipelineError(f"shot {i} ({shots[i]['at']!r}) starts before shot {i - 1} ({shots[i - 1]['at']!r})")
    first = max((i for i, s in enumerate(shots) if s["_t"] <= a + 1e-6), default=0)
    out = []
    for i, s in enumerate(shots):
        if i < first or s["_t"] >= b - 0.01:
            continue
        t0 = max(a, s["_t"])
        if s["_t"] < a and "src" in s:               # range starts mid-shot: start the clip where the range begins
            s["from"] = float(s.get("from", 0)) + (a - s["_t"]) * float(s.get("speed", 1.0))
        out.append({**s, "t0": t0})
    for i, s in enumerate(out):
        s["t1"] = out[i + 1]["t0"] if i + 1 < len(out) else b
        s["f0"], s["f1"] = round((s["t0"] - a) * fps), round((s["t1"] - a) * fps)
        s.pop("_t", None)
    return out


def _grade(ch) -> str:
    g = ch["grade"]
    vf = f"eq=contrast={g['contrast']}:saturation={g['saturation']}:gamma={g['gamma']}"
    if g.get("sharpen"):
        vf += f",unsharp=5:5:{g['sharpen']}:5:5:0"
    if g.get("vignette"):
        vf += f",vignette=angle={g['vignette']}"
    return vf


def _motion(move: str, ch, secs: float) -> str:
    """scale/crop expressions for a slow camera move over the shot (applied after a cover-fit to 1920x1080)."""
    z, p = ch["motion"]["push"], ch["motion"]["pan"]
    T = f"(t/{secs:.3f})"
    if move == "push":
        return f"scale=w='trunc(1920*(1+{z}*{T})/2)*2':h=-2:eval=frame,crop=1920:1080"
    if move == "pull":
        return f"scale=w='trunc(1920*(1+{z}-{z}*{T})/2)*2':h=-2:eval=frame,crop=1920:1080"
    if move in ("left", "right"):
        W = int(1920 * (1 + p)) // 2 * 2
        dx = f"({W - 1920})*{T}" if move == "left" else f"({W - 1920})*(1-{T})"
        return f"scale={W}:-2,crop=1920:1080:x='{dx}':y='(ih-1080)/2'"
    return "null"


def _footage(P: Path, s: dict, n: int, fps: int, ch, clip: Path, width=1920):
    src = P / "media" / s["src"] if not str(s["src"]).startswith("/") else Path(s["src"])
    if not src.exists():
        raise PipelineError(f"missing footage {src}")
    speed = float(s.get("speed", 1.0))
    secs = n / fps
    need = secs * speed
    start = float(s.get("from", 0.0))
    d = duration(src)
    if start + need > d - 0.05:                      # never loop: start earlier, then slow down a little
        start = max(0.0, d - need - 0.05)
        if d - 0.05 < need:
            speed = max(0.6, (d - 0.1) / secs)
    pts = f"setpts={1 / speed:.4f}*PTS," if abs(speed - 1) > 0.01 else ""
    if width == 1920:
        fit = "scale=1920:1080:force_original_aspect_ratio=increase:flags=lanczos,crop=1920:1080"
        mv = _motion(s.get("move", "push"), ch, secs)
        tail = ""
    else:                                            # split screen: footage fills the left half, black panel right
        fit = f"scale={width}:1080:force_original_aspect_ratio=increase:flags=lanczos,crop={width}:1080"
        mv = "null"
        tail = f",pad=1920:1080:0:0:color={ch['palette']['stage']}"
    # look: night = day-for-night (darker, cooler, desaturated) for daylight shots the narration places at night
    look = (",eq=brightness=-0.1:saturation=0.55:gamma=0.9:contrast=1.06,colorbalance=rs=-0.12:gs=-0.02:bs=0.16:rm=-0.06:bm=0.1"
            ",vignette=angle=0.62") if s.get("look") == "night" else ""
    # tpad: if a source still runs short, hold its last frame so the timeline can never drift
    vf = f"{pts}fps={fps},{fit},{mv},{_grade(ch)}{look}{tail},tpad=stop_mode=clone:stop_duration=30,setsar=1,format=yuv420p"
    if s.get("box") and width == 1920:
        # news footage (owner: boxed, never full-screen): the clip in a framed window over a blurred, darkened copy
        bw, bh = 1400, 788
        vf = (f"{pts}fps={fps},split[a][b];"
              f"[a]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,boxblur=28:2,eq=brightness=-0.22:saturation=0.8[bg];"
              f"[b]scale={bw}:{bh}:force_original_aspect_ratio=decrease:flags=lanczos,eq=contrast=1.08:saturation=1.05,"
              f"pad=iw+6:ih+6:3:3:color=0xE8E6E1[fg];"
              f"[bg][fg]overlay=(W-w)/2:(H-h)/2-20,tpad=stop_mode=clone:stop_duration=30,setsar=1,format=yuv420p")
        ffmpeg(["-ss", f"{start:.3f}", "-i", src, "-filter_complex", vf, "-frames:v", n, "-an", "-c:v", "libx264", "-preset",
                "veryfast", "-crf", "14", "-r", fps, clip])
        return
    ffmpeg(["-ss", f"{start:.3f}", "-i", src, "-vf", vf, "-frames:v", n, "-an", "-c:v", "libx264", "-preset", "veryfast",
            "-crf", "14", "-r", fps, clip])


def build_base(P: Path, edit, ch, words, log=print) -> tuple[Path, list[dict]]:
    fps = ch["fps"]
    shots = plan_shots(edit, words, fps)
    out = P / "build/base"
    out.mkdir(parents=True, exist_ok=True)
    lines = []
    for i, s in enumerate(shots):
        n = s["f1"] - s["f0"]
        if n <= 0:
            raise PipelineError(f"shot {i} ({s['at']!r}) has no duration")
        clip = out / f"s{i:03d}.mp4"
        key = short_hash(s.get("src"), s.get("from"), s.get("move"), s.get("speed"), s.get("page"), n, ch["grade"],
                         ch["motion"], "v2", s.get("look"), s.get("box"))
        kf = clip.with_suffix(".key")
        if not (clip.exists() and kf.exists() and kf.read_text() == key):
            if s.get("page") == "split":
                _footage(P, s, n, fps, ch, clip, width=960)
            elif s.get("page"):
                ffmpeg(["-f", "lavfi", "-i", f"color=c={ch['palette']['stage']}:s=1920x1080:r={fps}", "-frames:v", n,
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p", clip])
            else:
                _footage(P, s, n, fps, ch, clip)
            kf.write_text(key)
        lines.append(f"file '{clip.name}'")
    (out / "list.txt").write_text("\n".join(lines) + "\n")
    base = P / "build/hf/assets/base.mp4"
    base.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg(["-f", "concat", "-safe", "0", "-i", out / "list.txt", "-c", "copy", base])
    log(f"base: {len(shots)} shots, {duration(base):.2f}s")
    return base, shots


# ---------------------------------------------------------------- overlay (HyperFrames)
def _mark(text: str, color: str) -> str:
    """*word* -> accent colour."""
    return re.sub(r"\*(.+?)\*", lambda m: f'<span style="color:{color}">{m.group(1)}</span>', esc(text))


class Joe(Composition):
    def __init__(self, words, out, ch, offset):
        super().__init__(words, out)
        self.W, self.H, self.FPS = 1920, 1080, ch["fps"]
        self.ch = ch
        self.p = ch["palette"]
        self.off = offset
        self.dips: list[float] = []

    def t(self, at, after=0.0, lead=0.0) -> float:
        return resolve(self.words, at, after + self.off, lead) - self.off

    def add(self, gid, t0, t1, inner, style="position:absolute;inset:0", z=20, cls="gfx"):
        self.els.append(self.clip_div(gid, t0, t1, inner, f"{style};z-index:{z}", cls))

    def rise(self, sel, t, d=0.5, y=26, delay=0.0):
        self.tw(f'tl.fromTo("{sel}",{{opacity:0,y:{y}}},{{opacity:1,y:0,duration:{d},ease:"power3.out"}},{t + delay:.3f});')

    def away(self, sel, t1, d=0.35):
        self.tw(f'tl.to("{sel}",{{opacity:0,duration:{d},ease:"power1.in"}},{max(0, t1 - d - 0.02):.3f});')

    # ---------- text over footage
    def big(self, g, t0, t1):
        gid = self.nid("bg")
        col = g.get("color", self.p["accent"])
        sub = f'<div class="big-sub">{_mark(g["sub"], self.p["accent"])}</div>' if g.get("sub") else ""
        pre = f'<div class="big-pre">{_mark(g["pre"], self.p["accent"])}</div>' if g.get("pre") else ""
        inner = (f'<div class="scrim"></div><div class="big-wrap">{pre}<div class="big" style="color:{col}">'
                 f'{esc(g["text"])}</div>{sub}</div>')
        self.add(gid, t0, t1, inner)
        self.tw(f'tl.fromTo("#{gid} .scrim",{{opacity:0}},{{opacity:1,duration:0.5}},{t0:.3f});')
        if pre:
            self.rise(f"#{gid} .big-pre", t0, 0.5)
        self.tw(f'tl.fromTo("#{gid} .big",{{opacity:0,scale:0.94,y:20}},{{opacity:1,scale:1,y:0,duration:0.7,ease:"power3.out"}},{t0 + 0.08:.3f});')
        if sub:
            self.rise(f"#{gid} .big-sub", t0, 0.5, 14, 0.3)
        self.away(f"#{gid}", t1)

    def label(self, g, t0, t1):
        gid = self.nid("lb")
        sub = f'<div class="lb-sub">{_mark(g["sub"], self.p["accent"])}</div>' if g.get("sub") else ""
        # "center" sits in the upper third: the bottom centre is where viewers' subtitles appear
        pos = {"left": "left:110px;bottom:120px", "center": "left:0;right:0;top:120px;text-align:center",
               "top": "left:110px;top:110px"}[g.get("pos", "left")]
        shade = "lb-shade lb-shade-top" if g.get("pos") in ("center", "top") else "lb-shade"
        inner = (f'<div class="{shade}"></div><div class="lb" style="position:absolute;{pos}">'
                 f'<div class="lb-bar" style="background:{g.get("color", self.p["accent"])}'
                 f'{";display:none" if g.get("pos") == "center" else ""}"></div>'
                 f'<div class="lb-text">{_mark(g["text"], self.p["accent"])}</div>{sub}</div>')
        self.add(gid, t0, t1, inner)
        self.tw(f'tl.fromTo("#{gid} .lb-shade",{{opacity:0}},{{opacity:1,duration:0.5}},{t0:.3f});')
        self.tw(f'tl.fromTo("#{gid} .lb-bar",{{scaleY:0}},{{scaleY:1,duration:0.4,ease:"power3.out"}},{t0:.3f});')
        self.rise(f"#{gid} .lb-text", t0, 0.55, 18, 0.08)
        if sub:
            self.rise(f"#{gid} .lb-sub", t0, 0.5, 12, 0.25)
        self.away(f"#{gid}", t1)

    def questions(self, g, t0, t1):
        gid = self.nid("qs")
        rows = "".join(f'<div class="q-row" id="{gid}r{k}"><span class="q-n">{k + 1:02d}</span>'
                       f'<span class="q-t">{_mark(it["t"], self.p["accent"])}</span></div>' for k, it in enumerate(g["items"]))
        self.add(gid, t0, t1, f'<div class="scrim-left"></div><div class="q-stack">{rows}</div>')
        self.tw(f'tl.fromTo("#{gid} .scrim-left",{{opacity:0}},{{opacity:1,duration:0.5}},{t0:.3f});')
        prev = None
        for k, it in enumerate(g["items"]):
            ta = self.t(it["a"], t0, 0.1) if "a" in it else t0 + 0.6 * k
            self.rise(f"#{gid}r{k}", ta, 0.5, 18)
            if prev is not None:   # earlier questions step back
                self.tw(f'tl.to("#{gid}r{prev}",{{opacity:0.38,duration:0.4}},{ta:.3f});')
            prev = k
        self.away(f"#{gid}", t1)

    def chips(self, g, t0, t1):
        """A row of pill chips over darkened footage, each appearing as it is spoken."""
        gid = self.nid("cp")
        cols = [self.p[k] for k in ("c1", "c2", "c3", "accent", "c4", "c5")]
        chips = "".join(f'<div class="chip" id="{gid}c{k}" style="--c:{cols[k % len(cols)]}">{esc(it["t"])}</div>'
                        for k, it in enumerate(g["items"]))
        self.add(gid, t0, t1, f'<div class="scrim"></div><div class="chip-row">{chips}</div>')
        self.tw(f'tl.fromTo("#{gid} .scrim",{{opacity:0}},{{opacity:1,duration:0.5}},{t0:.3f});')
        for k, it in enumerate(g["items"]):
            ta = self.t(it["a"], t0, 0.1) if "a" in it else t0 + 0.5 * k
            self.rise(f"#{gid}c{k}", ta, 0.45, 16)
        self.away(f"#{gid}", t1)

    def quote(self, g, t0, t1):
        gid = self.nid("qt")
        inner = (f'<div class="scrim"></div><div class="qt-wrap"><div class="qt-mark" style="color:{self.p["accent"]}">“</div>'
                 f'<div class="qt-text">{_mark(g["text"], self.p["accent"])}</div>'
                 f'<div class="qt-who">{esc(g.get("who", ""))}</div></div>')
        self.add(gid, t0, t1, inner)
        self.tw(f'tl.fromTo("#{gid} .scrim",{{opacity:0}},{{opacity:1,duration:0.5}},{t0:.3f});')
        self.rise(f"#{gid} .qt-mark", t0, 0.5)
        self.rise(f"#{gid} .qt-text", t0, 0.7, 20, 0.15)
        self.rise(f"#{gid} .qt-who", t0, 0.5, 10, 0.6)
        self.away(f"#{gid}", t1)

    # ---------- full-frame pages
    def stage(self, extra=""):
        return f'<div class="stage">{extra}<div class="grid"></div><div class="glow"></div></div>'

    def chapter(self, s, t0, t1):
        gid = self.nid("ch")
        n = s.get("n")
        num = f'<div class="ch-n">{n:02d}</div>' if n else ""
        inner = (self.stage() + f'<div class="ch-wrap">{num}<div class="ch-rule"></div>'
                 f'<div class="ch-title">{esc(s["title"])}</div></div>')
        self.add(gid, t0, t1, inner, z=10, cls="page")
        if n:
            self.rise(f"#{gid} .ch-n", t0, 0.5, 10, 0.1)
        self.tw(f'tl.fromTo("#{gid} .ch-rule",{{scaleX:0}},{{scaleX:1,duration:0.7,ease:"power3.inOut"}},{t0 + 0.15:.3f});')
        self.tw(f'tl.fromTo("#{gid} .ch-title",{{opacity:0,letterSpacing:"0.5em"}},'
                f'{{opacity:1,letterSpacing:"0.16em",duration:1.2,ease:"power3.out"}},{t0 + 0.25:.3f});')
        self.dips.append(t0)

    def roadmap(self, s, t0, t1):
        gid = self.nid("rm")
        cols = [self.p[k] for k in ("c1", "c2", "c3", "accent", "c4", "c5")]
        tiles = "".join(f'<div class="rm-tile" id="{gid}t{k}" style="--c:{cols[k % len(cols)]}"><div class="rm-n">{k + 1:02d}</div>'
                        f'<div class="rm-t">{esc(it["t"])}</div></div>' for k, it in enumerate(s["items"]))
        self.add(gid, t0, t1, self.stage() + f'<div class="rm-row">{tiles}</div>', z=10, cls="page")
        for k, it in enumerate(s["items"]):
            ta = self.t(it["a"], t0, 0.15) if "a" in it else t0 + 0.4 + 0.5 * k
            self.tw(f'tl.fromTo("#{gid}t{k}",{{opacity:0.0,y:30}},{{opacity:1,y:0,duration:0.55,ease:"power3.out"}},{ta:.3f});')
            self.tw(f'tl.fromTo("#{gid}t{k}",{{"--lit":0}},{{"--lit":1,duration:0.5}},{ta:.3f});')
            if k:
                self.tw(f'tl.to("#{gid}t{k - 1}",{{"--lit":0.25,duration:0.5}},{ta:.3f});')

    def define(self, s, t0, t1):
        gid = self.nid("df")
        inner = (f'<div class="df-page"><div class="df-term">{esc(s["term"])}</div>'
                 f'<div class="df-phon">{esc(s.get("phon", ""))}<span class="df-pos">{esc(s.get("pos", "noun"))}</span></div>'
                 f'<div class="df-rule"></div><div class="df-text">{esc(s["text"])}</div></div>')
        self.add(gid, t0, t1, inner, z=10, cls="page")
        self.rise(f"#{gid} .df-term", t0, 0.6, 18, 0.1)
        self.rise(f"#{gid} .df-phon", t0, 0.5, 10, 0.45)
        self.tw(f'tl.fromTo("#{gid} .df-rule",{{scaleX:0}},{{scaleX:1,duration:0.6,ease:"power3.inOut"}},{t0 + 0.6:.3f});')
        self.rise(f"#{gid} .df-text", t0, 0.6, 14, 0.9)

    def split(self, s, t0, t1):
        gid = self.nid("sp")
        rows = "".join(f'<div class="sp-row" id="{gid}r{k}"><span class="sp-t">{_mark(it["t"], self.p["accent"])}</span>'
                       f'<span class="sp-v">{esc(it.get("v", ""))}</span></div>' for k, it in enumerate(s["items"]))
        title = f'<div class="sp-title">{esc(s.get("title", ""))}</div>' if s.get("title") else ""
        self.add(gid, t0, t1, f'<div class="sp-panel">{title}<div class="sp-rows">{rows}</div></div>', z=10, cls="page")
        if title:
            self.rise(f"#{gid} .sp-title", t0, 0.5, 14, 0.1)
        for k, it in enumerate(s["items"]):
            ta = self.t(it["a"], t0, 0.1) if "a" in it else t0 + 0.5 + 0.6 * k
            self.rise(f"#{gid}r{k}", ta, 0.5, 16)

    def illus(self, s, t0, t1):
        # coloured-pencil pages (sketches.py) first: this channel's illustrations and maths are drawn in pencil
        from . import illus, sketches
        fn = getattr(sketches, s["name"], None) or getattr(illus, s["name"])
        fn(self, s, t0, t1)

    def photo(self, s, t0, t1):
        """Archive photo: sharp and framed over a blurred, darkened copy of itself, slow push, small credit line."""
        gid = self.nid("ph")
        src = self.asset(self.proj / "media" / s["src"])
        credit = s.get("credit") or self.archive_credit(s["src"])
        cap = f'<div class="ph-cap">{esc(s["caption"])}</div>' if s.get("caption") else ""
        z = s.get("zoom", 0.06)
        if s.get("frame") or s.get("bg") == "stage":
            # framed: sharp photo over a blurred copy (share-alike photos go on the plain stage, unmodified)
            bg = (self.stage() if s.get("bg") == "stage" else f'<div class="ph-bg" style="background-image:url({src})"></div>')
            inner = (bg + f'<div class="ph-frame"><img src="{src}"/></div>{cap}'
                     f'<div class="ph-credit">{esc(credit)}</div>')
            target = ".ph-frame"
        else:
            # default: full-bleed, slow push from a chosen focus point, credit on the image's lower edge
            origin = s.get("origin", "50% 50%")
            inner = (f'<div class="ph-fill"><img src="{src}" style="transform-origin:{origin};object-position:{origin}"/></div>'
                     f'<div class="ph-foot"></div>{cap}<div class="ph-credit ph-credit-fill">{esc(credit)}</div>')
            target = ".ph-fill img"
        self.add(gid, t0, t1, inner, z=10, cls="page")
        s0 = float(s.get("scale", 1.0))           # >1 opens already cropped toward `origin` (e.g. one person in a two-shot)
        self.tw(f'tl.fromTo("#{gid} {target}",{{scale:{s0}}},{{scale:{s0 + z},duration:{t1 - t0:.3f},ease:"none"}},{t0:.3f});')
        self.tw(f'tl.fromTo("#{gid} {target}",{{opacity:0}},{{opacity:1,duration:0.35}},{t0:.3f});')
        if cap:
            self.rise(f"#{gid} .ph-cap", t0, 0.5, 12, 0.3)

    def archive_credit(self, src: str) -> str:
        cf = self.proj / "media/archive/credits.json"
        if cf.exists():
            d = json.loads(cf.read_text()).get(Path(src).stem)
            if d:
                return "Photo: " + d["credit"]
        return ""

    def black(self, s, t0, t1):
        pass

    def newsbox(self, s, t0, t1):
        """Outlet tag under a boxed news clip or screenshot: `box: "BBC News · March 2021"`."""
        if not isinstance(s.get("box"), str):
            return
        gid = self.nid("nb")
        self.add(gid, t0, t1, f'<div class="nb-tag">{esc(s["box"])}</div>', z=15)
        self.rise(f"#{gid} .nb-tag", t0, 0.45, 10, 0.25)

    # ---------- like & subscribe (owner's rule), styled to the channel, no SFX
    def subscribe(self, t0, t1):
        gid = self.nid("cta")
        thumb = ('<svg viewBox="0 0 24 24" width="40" height="40"><path fill="currentColor" d="M2 21h4V9H2v12zm20-11c0-1.1-.9-2-2-2h-6.3l1-4.6v-.3c0-.4-.2-.8-.4-1.1L13.2 1 6.6 7.6C6.2 8 6 8.5 6 9v10c0 1.1.9 2 2 2h9c.8 0 1.5-.5 1.8-1.2l3-7.1c.1-.2.2-.5.2-.7v-2z"/></svg>')
        inner = (f'<div class="cta"><div class="cta-btn cta-like">{thumb}<span>Like</span></div>'
                 f'<div class="cta-btn cta-sub"><span>Subscribe</span></div></div>')
        self.add(gid, t0, t1, inner, z=40)
        self.rise(f"#{gid} .cta-like", t0, 0.5, 20)
        self.rise(f"#{gid} .cta-sub", t0, 0.5, 20, 0.15)
        self.tw(f'tl.to("#{gid} .cta-like",{{backgroundColor:"{self.p["accent"]}",color:"{self.p["ink"]}",duration:0.3}},{t0 + 1.2:.3f});')
        self.tw(f'tl.to("#{gid} .cta-sub",{{backgroundColor:"#E5262B",color:"#fff",duration:0.3}},{t0 + 1.8:.3f});')
        self.tw(f'tl.to("#{gid} .cta-sub span",{{innerText:"Subscribed",duration:0.01}},{t0 + 2.6:.3f});')
        self.away(f"#{gid}", t1)

    def css(self) -> str:
        p = self.p
        faces = "".join(f'@font-face{{font-family:"{"Inter Display" if n.startswith("InterDisplay") else "Inter"}";'
                        f'src:url(assets/fonts/{n});font-weight:{w};}}' for n, w in FONTS.items())
        from . import pencil
        return faces + pencil.css() + f"""
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#000;width:1920px;height:1080px;overflow:hidden;font-family:Inter,sans-serif;color:{p['text']}}}
#root{{position:relative;width:1920px;height:1080px;overflow:hidden}}
#base{{position:absolute;inset:0;width:1920px;height:1080px;object-fit:cover;z-index:1}}
.gfx,.page{{position:absolute;inset:0}}
.scrim{{position:absolute;inset:0;background:radial-gradient(ellipse at center,rgba(0,0,0,.62) 0%,rgba(0,0,0,.38) 55%,rgba(0,0,0,.2) 100%)}}
.scrim-left{{position:absolute;inset:0;background:linear-gradient(90deg,rgba(0,0,0,.72) 0%,rgba(0,0,0,.45) 45%,rgba(0,0,0,0) 75%)}}
.big-wrap{{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center}}
.big{{font-family:"Inter Display";font-weight:900;font-size:220px;line-height:1;letter-spacing:-0.035em;text-shadow:0 6px 40px rgba(0,0,0,.45)}}
.big-pre{{font-weight:600;font-size:34px;letter-spacing:.22em;text-transform:uppercase;color:{p['text']};opacity:.9;margin-bottom:22px}}
.big-sub{{font-weight:600;font-size:38px;letter-spacing:.22em;text-transform:uppercase;margin-top:26px;color:{p['text']}}}
.lb-shade{{position:absolute;left:0;right:0;bottom:0;height:420px;background:linear-gradient(0deg,rgba(0,0,0,.6),rgba(0,0,0,0))}}
.lb-shade-top{{top:0;bottom:auto;background:linear-gradient(180deg,rgba(0,0,0,.6),rgba(0,0,0,0))}}
.lb{{display:flex;flex-direction:column;gap:12px;padding-left:28px}}
.lb-bar{{position:absolute;left:0;top:6px;bottom:6px;width:5px;border-radius:3px;transform-origin:bottom}}
.lb-text{{font-family:"Inter Display";font-weight:700;font-size:64px;line-height:1.05;letter-spacing:-0.01em;text-shadow:0 3px 24px rgba(0,0,0,.5)}}
.lb-sub{{font-weight:600;font-size:28px;letter-spacing:.2em;text-transform:uppercase;color:{p['text']};opacity:.82}}
.q-stack{{position:absolute;left:130px;top:50%;transform:translateY(-50%);display:flex;flex-direction:column;gap:30px}}
.q-row{{display:flex;align-items:baseline;gap:28px;opacity:0}}
.q-n{{font-weight:600;font-size:26px;letter-spacing:.12em;color:{p['accent']}}}
.q-t{{font-family:"Inter Display";font-weight:700;font-size:60px;letter-spacing:-0.01em;text-shadow:0 3px 24px rgba(0,0,0,.5)}}
.qt-wrap{{position:absolute;left:220px;right:220px;top:50%;transform:translateY(-50%);text-align:center}}
.qt-mark{{font-family:"Inter Display";font-weight:900;font-size:160px;line-height:.6}}
.qt-text{{font-family:"Inter Display";font-weight:300;font-size:62px;line-height:1.25;margin-top:20px}}
.qt-who{{font-weight:600;font-size:28px;letter-spacing:.22em;text-transform:uppercase;margin-top:36px;opacity:.8}}
.stage{{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 30%,#16181D 0%,{p['stage']} 70%)}}
.grid{{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px);background-size:48px 48px}}
.glow{{position:absolute;left:55%;top:-20%;width:900px;height:900px;border-radius:50%;background:radial-gradient(circle,rgba(56,189,248,.07),transparent 65%)}}
.ch-wrap{{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center}}
.ch-n{{font-weight:600;font-size:30px;letter-spacing:.3em;color:{p['accent']};margin-bottom:26px}}
.ch-rule{{width:120px;height:2px;background:{p['accent']};margin-bottom:38px}}
.ch-title{{font-family:"Inter Display";font-weight:800;font-size:96px;letter-spacing:.16em;text-transform:uppercase;text-align:center;padding-left:.16em}}
.rm-row{{position:absolute;left:120px;right:120px;top:50%;transform:translateY(-50%);display:flex;gap:28px}}
.rm-tile{{--lit:0;flex:1;height:320px;border-radius:22px;padding:34px 30px;display:flex;flex-direction:column;justify-content:space-between;
  background:linear-gradient(180deg,rgba(255,255,255,.045),rgba(255,255,255,.015));border:1px solid rgba(255,255,255,.09);
  box-shadow:0 0 calc(var(--lit)*60px) calc(var(--lit)*2px) color-mix(in srgb,var(--c) 45%,transparent),inset 0 1px 0 rgba(255,255,255,.07);
  outline:2px solid color-mix(in srgb,var(--c) calc(var(--lit)*100%),transparent);outline-offset:-2px;opacity:0}}
.rm-n{{font-family:"Inter Display";font-weight:800;font-size:64px;color:var(--c)}}
.rm-t{{font-weight:600;font-size:36px;line-height:1.2}}
.df-page{{position:absolute;inset:0;background:{p['cream']};color:{p['ink']};display:flex;flex-direction:column;justify-content:center;padding-left:260px}}
.df-term{{font-family:"Inter Display";font-weight:800;font-size:128px;letter-spacing:-0.02em}}
.df-phon{{font-weight:500;font-size:40px;color:#6B6459;margin-top:18px}}
.df-pos{{font-style:italic;margin-left:28px;font-size:34px}}
.df-rule{{width:700px;height:3px;background:{p['ink']};margin:46px 0 40px;transform-origin:left}}
.df-text{{font-weight:500;font-size:46px;line-height:1.35;max-width:1250px}}
.sp-panel{{position:absolute;left:960px;top:0;width:960px;height:1080px;padding:150px 110px;display:flex;flex-direction:column}}
.sp-title{{font-weight:600;font-size:30px;letter-spacing:.24em;text-transform:uppercase;color:{p['muted']};margin-bottom:60px}}
.sp-rows{{display:flex;flex-direction:column;gap:44px}}
.sp-row{{display:flex;justify-content:space-between;align-items:baseline;border-bottom:1px solid rgba(255,255,255,.1);padding-bottom:26px;opacity:0}}
.sp-t{{font-family:"Inter Display";font-weight:700;font-size:48px;flex-shrink:0;margin-right:44px}}
.sp-v{{font-family:"Inter Display";font-weight:800;font-size:56px;color:{p['accent']};text-align:right;line-height:1.12}}
.chip-row{{position:absolute;left:100px;right:100px;top:50%;transform:translateY(-50%);display:flex;flex-wrap:wrap;justify-content:center;gap:26px}}
.chip{{opacity:0;padding:22px 40px;border-radius:999px;font-family:"Inter Display";font-weight:700;font-size:50px;color:var(--c);
  background:color-mix(in srgb,var(--c) 16%,rgba(10,11,13,.55));border:2px solid var(--c);box-shadow:0 10px 40px rgba(0,0,0,.35)}}
.ph-bg{{position:absolute;inset:-60px;background-size:cover;background-position:center;filter:blur(38px) brightness(.32) saturate(1.1)}}
.ph-frame{{position:absolute;left:50%;top:50%;width:1460px;height:900px;margin:-450px 0 0 -730px;display:flex;align-items:center;justify-content:center}}
.ph-frame img{{max-width:1460px;max-height:900px;border-radius:6px;box-shadow:0 30px 90px rgba(0,0,0,.6);outline:1px solid rgba(255,255,255,.12)}}
.ph-cap{{position:absolute;left:110px;bottom:70px;font-family:"Inter Display";font-weight:700;font-size:44px;text-shadow:0 3px 20px rgba(0,0,0,.7)}}
.ph-credit{{position:absolute;right:46px;bottom:30px;font-weight:500;font-size:19px;letter-spacing:.04em;color:rgba(244,242,238,.62)}}
.ph-fill{{position:absolute;inset:0;overflow:hidden;background:#000}}
.ph-fill img{{width:100%;height:100%;object-fit:cover;filter:contrast(1.04) saturate(1.06)}}
.ph-foot{{position:absolute;left:0;right:0;bottom:0;height:170px;background:linear-gradient(0deg,rgba(0,0,0,.55),rgba(0,0,0,0))}}
.ph-credit-fill{{font-size:21px;color:rgba(244,242,238,.82);text-shadow:0 2px 10px rgba(0,0,0,.8)}}
.nb-tag{{position:absolute;left:263px;top:946px;font-weight:600;font-size:24px;letter-spacing:.16em;text-transform:uppercase;
  color:rgba(244,242,238,.9);text-shadow:0 2px 12px rgba(0,0,0,.6)}}
.cta{{position:absolute;left:0;right:0;bottom:120px;display:flex;justify-content:center;gap:28px}}
.cta-btn{{display:flex;align-items:center;gap:16px;padding:22px 44px;border-radius:999px;font-weight:700;font-size:40px;
  background:rgba(20,22,26,.78);color:#fff;border:1px solid rgba(255,255,255,.18);box-shadow:0 10px 40px rgba(0,0,0,.4)}}
"""


TEXT_KINDS = ("big", "label", "questions", "quote", "chips")


def build_overlay(P, edit, ch, words, shots, log=print) -> tuple[Path, list[float]]:
    a, b = edit["range"]
    end = b - a
    c = Joe(words, P / "build/hf", ch, a)
    c.proj = P
    for s in shots:
        if s.get("box") and not s.get("page"):
            c.newsbox(s, s["t0"] - a, s["t1"] - a)
        if s.get("page"):
            if s["page"] not in PAGES:
                raise PipelineError(f"unknown page {s['page']}")
            getattr(c, s["page"])(s, s["t0"] - a, s["t1"] - a)
    for g in edit.get("text", []):
        if g["kind"] not in TEXT_KINDS:
            raise PipelineError(f"unknown text kind {g['kind']}")
        t0 = resolve(words, g["at"], 0.0, 0.05) - a
        t1 = (resolve(words, g["until"], t0 + a, 0.0) - a + 0.25) if "until" in g else t0 + g.get("dur", 3.0)
        t1 = min(t1, end)
        if t0 >= end or t1 <= max(t0, 0):
            continue
        getattr(c, g["kind"])(g, max(0.0, t0), t1)
    if ch.get("end_cta", True):
        mention = [w for w in words.words if a <= w["s"] < b and "subscrib" in w["w"].lower()]
        if mention:
            ts = float(mention[-1]["s"]) - 1.2 - a
            c.subscribe(ts, min(end, ts + 5.0))
    for d in edit.get("music_dips", []):
        c.dips.append(resolve(words, d, 0.0) - a)
    c.els.insert(0, f'<video id="base" class="clip" src="assets/base.mp4" muted data-start="0" data-duration="{end:.3f}"></video>')
    from . import pencil
    fonts = {**{n: FONT_DIR / n for n in FONTS}, **pencil.fonts()}
    path = c.write(c.css(), end, fonts=fonts)
    log(f"overlay: {len(edit.get('text', []))} text, {sum(1 for s in shots if s.get('page'))} pages, {len(c.js)} tweens")
    return path, c.dips


# ---------------------------------------------------------------- audio
def build_audio(P, ep, edit, ch, dips, log=print) -> Path:
    a, b = edit["range"]
    end = b - a
    au = ch["audio"]
    parts = P / "build/audio_parts"
    parts.mkdir(parents=True, exist_ok=True)
    vo = P / (ep["voice"][0]["file"] if isinstance(ep["voice"][0], dict) else ep["voice"][0])
    voice = parts / "voice.wav"
    ffmpeg(["-i", vo, "-ac", "2", "-ar", "48000", "-af", f"loudnorm=I={au['voice_lufs']}:TP=-1.5:LRA=11", parts / "voice_full.wav"])
    ffmpeg(["-ss", f"{a:.3f}", "-t", f"{end:.3f}", "-i", parts / "voice_full.wav", "-af", "apad", "-t", f"{end:.3f}", voice])
    out = P / "build/hf/assets/audio.wav"
    mj = P / "music.json"
    tracks = [t for t in json.loads(mj.read_text())["tracks"] if t["end"] > a and t["start"] < b] if mj.exists() else []
    if not tracks:
        ffmpeg(["-i", voice, "-c", "copy", out])
        log("audio: voice only (no music.json)")
        return out
    args, f, labs = [], [], []
    for i, t in enumerate(tracks):
        st, en = max(t["start"], a) - a, min(t["end"], b) - a
        d = en - st
        off = float(t.get("offset", 0)) + (max(a, t["start"]) - t["start"])
        ms = int(st * 1000)
        args += ["-stream_loop", "-1", "-i", P / t["file"]]
        fi = 1.0 if i == 0 else 3.5
        f.append(f"[{i}]atrim={off:.3f}:{off + d + 3.5:.3f},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,"
                 f"loudnorm=I={au['music_lufs']}:TP=-6,afade=t=in:d={fi},afade=t=out:st={max(0, d):.3f}:d=3.5,adelay={ms}|{ms}[m{i}]")
        labs.append(f"[m{i}]")
    # dips: music falls away just before a chapter card and returns with it
    vol = "1"
    for t in dips:
        g = 10 ** (au["dip_db"] / 20)
        vol = (f"if(between(t,{t - 0.9:.2f},{t + 0.6:.2f}),"
               f"{g:.3f}+(1-{g:.3f})*max(0,min(1,abs(t-{t - 0.15:.2f})/0.75)),{vol})")
    f.append(f"{''.join(labs)}amix=inputs={len(labs)}:duration=longest:normalize=0,atrim=0:{end:.3f},volume='{vol}':eval=frame[bed]")
    nv = len(tracks)
    f.append(f"[{nv}]asplit=2[v][sc];[bed][sc]sidechaincompress=threshold=0.04:ratio={au['duck_ratio']}:attack=40:release=600[duck];"
             f"[v][duck]amix=inputs=2:duration=first:normalize=0,loudnorm=I={au['master_lufs']}:TP=-1.5:LRA=11[o]")
    ffmpeg([*args, "-i", voice, "-filter_complex", ";".join(f), "-map", "[o]", "-t", f"{end:.3f}", "-ar", "48000", out])
    log(f"audio: voice + {len(tracks)} music section(s), {len(dips)} dip(s) → {out.name}")
    return out


# ---------------------------------------------------------------- checks
def check(P: Path, log=print) -> int:
    ep, edit, ch, words = load(P)
    shots = plan_shots(edit, words, ch["fps"])
    r = ch["retention"]
    warn = 0
    # multi-shot packages (e.g. DVIDS B-roll reels in media/pd/) are counted per shot inside the reel, not per file;
    # media/pd/shots.json holds each reel's scene cuts ({"file.mp4": [{"s": 0.0, "e": 10.9}, ...]})
    sj = P / "media/pd/shots.json"
    reels = json.loads(sj.read_text()) if sj.exists() else {}
    uses: dict[str, int] = {}
    for s in shots:
        if not s.get("src"):
            continue                                   # photos and split backgrounds count too
        key = s["src"]
        segs = reels.get(Path(key).name) if key.startswith("pd/") else None
        if segs:
            a = float(s.get("from", 0))
            b = a + (s["t1"] - s["t0"]) * float(s.get("speed", 1.0))
            seg = next((k for k, g in enumerate(segs) if g["s"] - 0.05 <= a < g["e"]), None)
            if seg is None or b > segs[seg]["e"] + 0.05:
                log(f"!  {s['t0']:7.2f}s  {key} from {a:.1f} to {b:.1f} crosses a scene cut in the reel")
                warn += 1
            key = f"{key}#{seg}"
        uses[key] = uses.get(key, 0) + 1
    for src, n in uses.items():
        if n > r["max_uses"]:
            log(f"!! {src} used {n}× (max {r['max_uses']})")
            warn += 1
    foot = 0.0
    for s in shots:
        d = s["t1"] - s["t0"]
        if s.get("page"):
            continue
        foot += d
        if d > r["max_shot"] and not s.get("hold"):
            log(f"!  {s['t0']:7.2f}s  {d:4.1f}s shot ({s['src']}) — longer than {r['max_shot']}s (add `hold: reason` to keep)")
            warn += 1
        if d < r["min_shot"] and not s.get("quick"):     # `quick: reason` = a deliberate rapid list ("your phone, your shoes…")
            log(f"!  {s['t0']:7.2f}s  {d:4.1f}s shot ({s['src']}) — very short")
            warn += 1
    a, b = edit["range"]
    log(f"{len(shots)} shots over {b - a:.1f}s, footage {100 * foot / (b - a):.0f}% of the time; {warn} warning(s)")
    return warn


def run(P: Path, do_render=True, log=print) -> Path:
    P = Path(P)
    ep, edit, ch, words = load(P)
    _, shots = build_base(P, edit, ch, words, log)
    _, dips = build_overlay(P, edit, ch, words, shots, log)
    build_audio(P, ep, edit, ch, dips, log)
    if not do_render:
        return P / "build/hf/index.html"
    a, b = edit["range"]
    out = P / "out" / f"{P.name}_{int(a)}-{int(b)}s.mp4"
    out.parent.mkdir(exist_ok=True)
    render(P / "build/hf", out, fps=ch["fps"], quality="high", log=log)
    log(f"rendered {out}")
    return out


if __name__ == "__main__":
    proj = Path(sys.argv[1])
    if "--check" in sys.argv:
        sys.exit(1 if check(proj) else 0)
    run(proj, do_render="--no-render" not in sys.argv)
