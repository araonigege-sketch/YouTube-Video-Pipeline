"""HyperFrames composition builder shared by every channel.

A channel composer subclasses Composition, adds its own page types, and calls
`write()` to produce build/index.html (+ assets). Everything visible is a GSAP
tween on one paused timeline, so renders are deterministic.
"""
from __future__ import annotations

import html
import shutil
import subprocess
from pathlib import Path

from .config import ROOT
from .util import PipelineError
from .words import Words

NODE = ROOT / "node_modules"


class Composition:
    W, H, FPS = 1920, 1080, 30

    def __init__(self, words: Words, out: Path):
        self.words = words
        self.out = Path(out)
        self.els: list[str] = []
        self.js: list[str] = []
        self._n = 0
        self._assets: set[str] = set()
        for d in ("assets/js", "assets/fonts", "assets/img"):
            (self.out / d).mkdir(parents=True, exist_ok=True)

    # ---- timing ----
    def T(self, phrase, after=0.0, end=False):
        return self.words.T(phrase, after, end)

    def at(self, x, t0):
        return self.words.at(x, t0)

    # ---- elements ----
    def nid(self, prefix="e") -> str:
        self._n += 1
        return f"{prefix}{self._n}"

    @staticmethod
    def clip_div(id_, t0, t1, inner, style="", cls=""):
        return (f'<div id="{id_}" class="clip {cls}" data-start="{t0:.3f}" data-duration="{t1 - t0:.3f}" '
                f'style="{style}">{inner}</div>')

    def asset(self, src: Path, sub="img") -> str:
        """Copy a media file into build/assets/<sub>/ once; return its relative path."""
        src = Path(src)
        if not src.exists():
            raise PipelineError(f"missing media: {src}")
        rel = f"assets/{sub}/{src.name}"
        if rel not in self._assets:
            shutil.copy(src, self.out / rel)
            self._assets.add(rel)
        return rel

    # ---- tweens ----
    def tw(self, code: str):
        self.js.append(code)

    def fade_in(self, sel, t, d=0.45):
        self.js.append(f'tl.fromTo("{sel}",{{opacity:0}},{{opacity:1,duration:{d},ease:"power1.inOut"}},{t:.3f});')

    def fade_out(self, sel, t, d=0.3):
        self.js.append(f'tl.to("{sel}",{{opacity:0,duration:{d}}},{t:.3f});')

    def kb(self, sel, t0, t1, m):
        """Ken Burns: m = (scale0, scale1, x0, x1, y0, y1)."""
        s0, s1, x0, x1, y0, y1 = m
        self.js.append(f'tl.fromTo("{sel}",{{scale:{s0},x:{x0},y:{y0}}},'
                       f'{{scale:{s1},x:{x1},y:{y1},duration:{t1 - t0:.3f},ease:"none"}},{t0:.3f});')

    def write_on(self, sel, t, d=0.6):
        self.js.append(f'tl.fromTo("{sel}",{{clipPath:"inset(0 100% 0 0)"}},'
                       f'{{clipPath:"inset(0 0% 0 0)",duration:{d},ease:"none"}},{t:.3f});')

    def draw(self, sel, t, d=0.8, length=2000):
        self.js.append(f'tl.fromTo("{sel}",{{strokeDashoffset:{length}}},'
                       f'{{strokeDashoffset:0,duration:{d},ease:"power1.inOut"}},{t:.3f});')

    def pop(self, sel, t, d=0.35):
        self.js.append(f'tl.fromTo("{sel}",{{opacity:0,scale:0.3}},{{opacity:1,scale:1,duration:{d},ease:"back.out(2)"}},{t:.3f});')

    # ---- captions ----
    def captions(self, max_words=5, max_chars=32, until=None) -> str:
        out = []
        for k, (s, e, txt) in enumerate(self.words.caption_groups(max_words, max_chars)):
            if until is not None and s >= until:
                break
            out.append(f'<div id="cp{k}" class="clip capwrap" data-start="{s:.3f}" data-duration="{e - s:.3f}">'
                       f'<div class="cap">{html.escape(txt)}</div></div>')
            self.js.append(f'tl.fromTo("#cp{k} .cap",{{opacity:0,y:8}},{{opacity:1,y:0,duration:0.15}},{s:.3f});')
        return "".join(out)

    # ---- output ----
    def write(self, css: str, end: float, layers_after: str = "", audio: str | None = "assets/audio.wav",
              fonts: dict[str, Path] | None = None) -> Path:
        gsap = NODE / "gsap/dist/gsap.min.js"
        if not gsap.exists():
            raise PipelineError("node_modules missing — run `npm install` in the repo root")
        shutil.copy(gsap, self.out / "assets/js/gsap.min.js")
        for name, path in (fonts or {}).items():
            shutil.copy(path, self.out / "assets/fonts" / name)
        for f in ("hyperframes.json", "meta.json"):
            shutil.copy(ROOT / "pipeline/hf_template" / f, self.out / f)
        audio_tag = (f'<audio id="vo" class="clip" src="{audio}" data-start="0" data-duration="{end:.3f}"></audio>'
                     if audio else "")
        page = f'''<!doctype html>
<html lang="en"><head><meta charset="UTF-8" /><meta name="viewport" content="width={self.W}, height={self.H}" />
<script src="assets/js/gsap.min.js"></script><style>{css}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{end:.3f}" data-width="{self.W}" data-height="{self.H}">
{"".join(self.els)}
{layers_after}
{audio_tag}
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(self.js)}
tl.to({{}},{{duration:{end:.3f}}},0);
window.__timelines["main"] = tl;
tl.seek(0);
</script></body></html>'''
        (self.out / "index.html").write_text(page, encoding="utf-8")
        return self.out / "index.html"


def render(build: Path, out: Path, fps: int = 30, quality: str = "standard", log=print) -> Path:
    """Render a HyperFrames build dir to MP4 with the local Chromium (blocking)."""
    import os
    env = dict(os.environ, HYPERFRAMES_NO_TELEMETRY="1")
    for cand in ("/opt/pw-browsers/chromium", shutil.which("google-chrome") or "", shutil.which("chromium") or ""):
        if cand and Path(cand).exists():
            env.setdefault("HYPERFRAMES_BROWSER_PATH", cand)
            break
    cmd = ["npx", "-y", "hyperframes@0.9.7", "render", str(build), "-o", str(out), "--fps", str(fps),
           "--quality", quality]
    log("rendering: " + " ".join(cmd))
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if proc.returncode != 0 or not Path(out).exists():
        raise PipelineError(f"hyperframes render failed:\n{proc.stdout[-2000:]}\n{proc.stderr[-2000:]}")
    return Path(out)
