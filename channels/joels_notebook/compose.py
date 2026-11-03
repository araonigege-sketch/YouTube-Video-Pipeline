"""Joel's Notebook composer: shots.yaml -> HyperFrames build.

Shot types (one dict per shot in shots.yaml; `at` = first words of the narration
where the shot starts):
  plate     img, move (preset name or [s0,s1,x0,x1,y0,y1]), fx (dust|sand|embers),
            video (PixVerse clip; holds its last frame after), label (corner strip)
  notes     title, tsize, items[], paths[], strikes[], pops[], svg_static
  relay     title, tokens[], labels, items[], stretches
  map       title, nodes[], color, spread, route_at, items[], doodles
  converge  title, labels, center, col
  custom    page: name of a function in the project's custom.py
  end       closing card
Item anchors (`a`): number = seconds after shot start, "phrase" = when spoken,
">phrase" = when it ends. Colours: ink | red | paper | #hex; "{ink}" etc. in raw SVG.
"""
from __future__ import annotations

import html
import importlib.util
import math
import random
from pathlib import Path

import yaml

from pipeline.config import ROOT
from pipeline.hf import Composition
from pipeline.util import PipelineError

HERE = Path(__file__).resolve().parent

MOVES = {"in": (1.0, 1.12, 0, 0, 0, 0), "out": (1.14, 1.02, 0, 0, 0, 0), "L": (1.12, 1.12, 70, -70, 0, 0),
         "R": (1.12, 1.12, -70, 70, 0, 0), "up": (1.12, 1.12, 0, 0, 45, -45), "down": (1.12, 1.12, 0, 0, -45, 45),
         "inL": (1.04, 1.2, 0, 90, 0, 0), "inR": (1.04, 1.2, 0, -90, 0, 0), "inUp": (1.04, 1.2, 0, 0, 0, 60),
         "inDown": (1.04, 1.2, 0, 0, 0, -60)}
PAGE_TYPES = {"notes", "relay", "map", "converge", "custom", "end"}


def load_channel() -> dict:
    return yaml.safe_load((HERE / "channel.yaml").read_text())


class Notebook(Composition):
    def __init__(self, words, out, project_dir: Path, channel: dict):
        super().__init__(words, out)
        self.P = Path(project_dir)
        self.ch = channel
        pal = channel["palette"]
        self.INK, self.RED, self.PAPER, self.CREAM = pal["ink"], pal["red"], pal["paper"], pal["cream"]
        self.XF = channel["timing"]["crossfade"]
        self.SEAL = (
            f'<svg viewBox="0 0 200 200" width="170" height="170"><g fill="{self.RED}"><circle cx="100" cy="100" r="84"/>'
            + "".join(f'<circle cx="{100 + 86 * math.cos(a / 18 * 3.14159)}" cy="{100 + 86 * math.sin(a / 18 * 3.14159)}" r="9"/>'
                      for a in range(36))
            + f'</g><circle cx="100" cy="100" r="64" fill="none" stroke="{self.PAPER}" stroke-width="4" opacity=".8"/>'
            f'<text x="100" y="122" text-anchor="middle" font-family="EB Garamond" font-size="64" font-weight="700" '
            f'fill="{self.PAPER}">JN</text></svg>')

    # ---------- helpers ----------
    def col(self, c, default=None):
        c = c or default or "ink"
        return {"ink": self.INK, "red": self.RED, "paper": self.PAPER, "cream": self.CREAM}.get(c, c)

    def svgfmt(self, s: str) -> str:
        return s.replace("{ink}", self.INK).replace("{red}", self.RED).replace("{paper}", self.PAPER)

    def hw(self, text, x, y, size=72, color=None, id_=None, extra=""):
        idattr = f'id="{id_}" ' if id_ else ""
        return (f'<div {idattr}class="hw abs" style="left:{x}px;top:{y}px;font-size:{size}px;'
                f'color:{self.col(color)};{extra}">{text}</div>')

    def page(self, t0, t1, inner, pid):
        return self.clip_div(pid, t0, t1 + self.XF,
                             f'<div class="paper"></div>{inner}<div class="abs" style="right:70px;top:60px;opacity:.9">{self.SEAL}</div>',
                             "position:absolute;inset:0", "shot")

    def title_html(self, pid, text, t, size=96, x=250, y=150, color=None):
        w = int(len(text) * size * 0.40) + 20
        js_t = t + 0.15
        self.write_on(f"#{pid}t", js_t, min(1.0, 0.25 + len(text) * 0.035))
        self.tw(f'tl.fromTo("#{pid}u",{{scaleX:0,transformOrigin:"0% 50%"}},{{scaleX:1,duration:0.4}},{js_t + 0.6:.3f});')
        return (self.hw(html.escape(text), x, y, size, color, f"{pid}t")
                + f'<div id="{pid}u" class="abs rule2" style="left:{x}px;top:{y + size + 16}px;width:{w}px"></div>')

    @staticmethod
    def circ(cx, cy, rx, ry=None):
        ry = ry or rx
        return f"M{cx},{cy - ry} a{rx},{ry} 0 1,1 -1,0"

    def particles(self, kind, t0, t1, seed):
        r = random.Random(seed)
        pid = self.nid("pt")
        dots = []
        n = 34 if kind != "embers" else 26
        for i in range(n):
            x, y = r.randint(0, 1900), r.randint(60, 1040)
            s = r.choice((3, 4, 5, 6)) if kind != "sand" else r.choice((2, 3, 4))
            c = "#FFD9A0" if kind == "embers" else "#F6E7C8"
            dots.append(f'<i id="{pid}_{i}" style="position:absolute;left:{x}px;top:{y}px;width:{s}px;height:{s}px;'
                        f'border-radius:50%;background:{c};opacity:{r.uniform(.25, .7):.2f};box-shadow:0 0 {s * 2}px {c}"></i>')
            dx = r.randint(120, 320) * (1 if kind != "embers" else r.choice((-1, 1)) * 0.3)
            dy = r.randint(-40, 40) if kind != "embers" else -r.randint(160, 380)
            if kind == "sand":
                dx, dy = r.randint(500, 900), r.randint(-30, 30)
            self.tw(f'tl.fromTo("#{pid}_{i}",{{x:0,y:0}},{{x:{dx},y:{dy},duration:{t1 - t0 + self.XF:.3f},ease:"none"}},{t0:.3f});')
        return f'<div class="abs" style="inset:0;pointer-events:none">{"".join(dots)}</div>'

    def strip(self, text, t, t_out, left=70, top=70, size=64):
        sid = self.nid("st")
        self.els.append(self.clip_div(sid, t, t_out, f'<div class="strip" style="font-size:{size}px">{html.escape(text)}</div>',
                                      f"position:absolute;left:{left}px;top:{top}px;z-index:30"))
        self.tw(f'tl.fromTo("#{sid} .strip",{{x:-60,opacity:0}},{{x:0,opacity:1,duration:0.45,ease:"power3.out"}},{t:.3f});')
        self.fade_out(f"#{sid} .strip", t_out - 0.3)

    # ---------- shot types ----------
    def plate(self, t0, t1, img, move="in", fx=None, video=None, label=None, i=0):
        motion = MOVES[move] if isinstance(move, str) else tuple(move)
        ai = self.P / "ai"
        if video and (ai / video).exists():
            src = self.asset(ai / video)
            vlen = min(t1 - t0 + self.XF, 4.8)
            vid = self.nid("v")
            self.els.append(f'<video id="{vid}" class="clip shot vplate" src="{src}" muted '
                            f'data-start="{t0:.3f}" data-duration="{vlen:.3f}"></video>')
            self.fade_in(f"#{vid}", t0)
            self.tw(f'tl.fromTo("#{vid}",{{scale:1}},{{scale:1.05,duration:{vlen:.3f},ease:"none"}},{t0:.3f});')
            if t0 + vlen < t1 + self.XF - 0.2:
                last = self.asset(ai / video.replace(".mp4", "_last.jpg"))
                sid = self.nid("p")
                ts = t0 + vlen - self.XF
                self.els.append(self.clip_div(sid, ts, t1 + self.XF, f'<img class="plate" src="{last}">',
                                              "position:absolute;inset:0;overflow:hidden", "shot"))
                self.fade_in(f"#{sid}", ts)
                self.tw(f'tl.fromTo("#{sid} .plate",{{scale:1.05}},{{scale:1.12,duration:{t1 + self.XF - ts:.3f},ease:"none"}},{ts:.3f});')
        else:
            src = self.asset(ai / img)
            sid = self.nid("p")
            self.els.append(self.clip_div(sid, t0, t1 + self.XF, f'<img class="plate" src="{src}">',
                                          "position:absolute;inset:0;overflow:hidden", "shot"))
            if t0 > 0:
                self.fade_in(f"#{sid}", t0)
            self.kb(f"#{sid} .plate", t0, t1 + self.XF, motion)
        if fx:
            fid = self.nid("fx")
            self.els.append(self.clip_div(fid, t0, t1 + self.XF, self.particles(fx, t0, t1, i), "position:absolute;inset:0;z-index:5"))
            self.fade_in(f"#{fid}", t0)
        if label:
            self.strip(label, t0 + 0.4, min(t1, t0 + 4.2) + 0.2)

    def notes(self, t0, t1, title=None, items=(), paths=(), strikes=(), pops=(), tsize=96, svg_static=""):
        pid = self.nid("pg")
        inner = self.title_html(pid, title, t0, tsize) if title else ""
        svg = self.svgfmt(svg_static or "")
        for k, p in enumerate(paths):
            L = p.get("len", 1500)
            svg += (f'<path id="{pid}p{k}" d="{p["d"]}" stroke="{self.col(p.get("c"))}" stroke-width="{p.get("w", 7)}" '
                    f'fill="{p.get("fill", "none")}" stroke-linecap="round" stroke-linejoin="round" '
                    f'stroke-dasharray="{L}" stroke-dashoffset="{L}"/>')
            self.draw(f"#{pid}p{k}", self.at(p.get("a", 0.3), t0), p.get("dur", 0.6), L)
        for k, s in enumerate(strikes):
            svg += (f'<path id="{pid}s{k}" d="M{s["x"]},{s["y"]} q{s["w"] / 2},-10 {s["w"]},4" stroke="{self.col(s.get("c"), "red")}" '
                    f'stroke-width="8" fill="none" stroke-linecap="round" stroke-dasharray="{s["w"] + 40}" stroke-dashoffset="{s["w"] + 40}"/>')
            self.draw(f"#{pid}s{k}", self.at(s["a"], t0), 0.35, s["w"] + 40)
        if svg:
            inner = f'<svg class="abs" style="left:0;top:0" width="1920" height="1080" viewBox="0 0 1920 1080">{svg}</svg>' + inner
        for k, it in enumerate(items):
            rot = f'transform:rotate({it["rot"]}deg);' if it.get("rot") else ""
            op = f'opacity:{it["op"]};' if it.get("op") else ""
            inner += self.hw(html.escape(it["t"]), it["x"], it["y"], it.get("s", 72), it.get("c"), f"{pid}i{k}", rot + op)
            self.write_on(f"#{pid}i{k}", self.at(it.get("a", 0.4), t0), it.get("d", min(1.1, 0.2 + len(it["t"]) * 0.04)))
        for k, p in enumerate(pops):
            inner += f'<div id="{pid}o{k}" class="abs" style="left:{p["x"]}px;top:{p["y"]}px">{self.svgfmt(p["html"])}</div>'
            self.pop(f"#{pid}o{k}", self.at(p["a"], t0))
        self.els.append(self.page(t0, t1, inner, pid))
        self.fade_in(f"#{pid}", t0)
        return pid

    def relay(self, t0, t1, title, tokens, labels=None, items=(), stretches=None):
        pid = self.nid("pg")
        xs = [260 + k * 233 for k in range(7)]
        figs = ""
        for x in xs:
            figs += (f'<circle cx="{x}" cy="470" r="36" fill="none" stroke="{self.INK}" stroke-width="6"/>'
                     f'<path d="M{x},506 L{x},620 M{x - 52},560 L{x + 52},560 M{x},620 L{x - 38},700 M{x},620 L{x + 38},700" '
                     f'stroke="{self.INK}" stroke-width="6" stroke-linecap="round" fill="none"/>')
        if stretches is not None:
            for k in range(6):
                a, b = xs[k] + 14, xs[k + 1] - 14
                y = 742 + (k % 2) * 14
                figs += (f'<path id="{pid}r{k}" d="M{a},{y} L{b},{y} M{a + 14},{y - 10} L{a},{y} L{a + 14},{y + 10} '
                         f'M{b - 14},{y - 10} L{b},{y} L{b - 14},{y + 10}" stroke="{self.RED if k % 2 else self.INK}" '
                         f'stroke-width="5" fill="none" stroke-linecap="round" stroke-dasharray="700" stroke-dashoffset="700"/>')
                self.draw(f"#{pid}r{k}", self.at(stretches, t0) + k * 0.12, 0.3, 700)
        inner = (f'<svg class="abs" style="left:0;top:0" width="1920" height="1080" viewBox="0 0 1920 1080">{figs}</svg>'
                 + self.title_html(pid, title, t0))
        if labels:
            inner += (self.hw(labels[0], 150, 800, 60, "ink", f"{pid}l0", "opacity:.75")
                      + self.hw(labels[1], 1560, 800, 60, "ink", f"{pid}l1", "opacity:.75"))
            self.write_on(f"#{pid}l0", t0 + 0.4, 0.4)
            self.write_on(f"#{pid}l1", t0 + 0.4, 0.4)
        for k, tk in enumerate(tokens):
            c = self.col(tk.get("c"), "red")
            ta = self.at(tk["a"], t0)
            dur = tk.get("dur", 6.0)
            y = tk.get("y", 380)
            inner += (f'<div id="{pid}k{k}" class="abs hw" style="left:0;top:{y}px;font-size:{tk.get("s", 54)}px;color:{c};'
                      f'border:4px solid {c};border-radius:12px;background:{self.PAPER};padding:2px 16px 8px;margin:0;'
                      f'transform:translateX(-50%)">{html.escape(tk["t"])}</div>')
            seq = xs[::-1] if tk.get("dir", "w") == "w" else xs
            self.tw(f'tl.fromTo("#{pid}k{k}",{{x:{seq[0]},opacity:0}},{{x:{seq[0]},opacity:1,duration:0.25}},{ta:.3f});')
            hop = dur / 6
            for j in range(6):
                self.tw(f'tl.fromTo("#{pid}k{k}",{{x:{seq[j]}}},{{x:{seq[j + 1]},duration:{hop * 0.6:.3f},ease:"power2.inOut"}},'
                        f'{ta + 0.25 + j * hop:.3f});')
            if tk.get("fade", True) and ta + 0.25 + 5 * hop + hop * 0.6 + 0.3 < t1:
                self.fade_out(f"#{pid}k{k}", ta + 0.25 + 5 * hop + hop * 0.6 + 0.15)
        for k, it in enumerate(items):
            inner += self.hw(html.escape(it["t"]), it["x"], it["y"], it.get("s", 64), it.get("c"), f"{pid}i{k}",
                             f'transform:rotate({it.get("rot", 0)}deg)')
            self.write_on(f"#{pid}i{k}", self.at(it["a"], t0), it.get("d", min(1.0, 0.2 + len(it["t"]) * 0.04)))
        self.els.append(self.page(t0, t1, inner, pid))
        self.fade_in(f"#{pid}", t0)

    def map(self, t0, t1, title, nodes, color=None, spread=False, route_at=None, items=(), doodles=True):
        pid = self.nid("pg")
        color = self.col(color)
        svg = ""
        if doodles:
            svg += "".join(f'<path d="M{x},{y} l34,-60 l34,60" stroke="{self.INK}" stroke-width="4" fill="none" opacity=".45" '
                           f'stroke-linejoin="round"/>' for x, y in ((1220, 330), (1268, 316), (1316, 336)))
            svg += "".join(f'<path d="M{x},{y} q26,-20 52,0 q26,-20 52,0" stroke="{self.INK}" stroke-width="4" fill="none" '
                           f'opacity=".4"/>' for x, y in ((1000, 760), (1300, 700), (700, 780)))
        pts = [(n["x"], n["y"]) for n in nodes]
        for k in range(1, len(pts)):
            (x0, y0), (x1, y1) = pts[k - 1], pts[k]
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2 - 60
            svg += (f'<path id="{pid}g{k - 1}" d="M{x0},{y0} Q{mx},{my} {x1},{y1}" stroke="{color}" stroke-width="8" fill="none" '
                    f'stroke-linecap="round" stroke-dasharray="2000" stroke-dashoffset="2000"/>')
            ta = (self.at(route_at, t0) + (k - 1) * 0.25) if route_at is not None else self.at(nodes[k]["a"], t0) - 0.5
            self.draw(f"#{pid}g{k - 1}", ta, 0.55, 2000)
        for k, n in enumerate(nodes):
            ta = self.at(n["a"], t0)
            if spread:
                svg += f'<circle id="{pid}b{k}" cx="{n["x"]}" cy="{n["y"]}" r="70" fill="{self.RED}" opacity="0"/>'
                self.tw(f'tl.fromTo("#{pid}b{k}",{{attr:{{r:6}},opacity:0.55}},{{attr:{{r:{n.get("r", 70)}}},opacity:0.28,'
                        f'duration:1.4,ease:"power2.out"}},{ta:.3f});')
            svg += (f'<circle id="{pid}c{k}" cx="{n["x"]}" cy="{n["y"]}" r="15" fill="{self.RED if spread else self.INK}" opacity="0"/>')
            self.tw(f'tl.fromTo("#{pid}c{k}",{{opacity:0,attr:{{r:4}}}},{{opacity:1,attr:{{r:15}},duration:0.3,ease:"back.out(3)"}},{ta:.3f});')
        inner = (f'<svg class="abs" style="left:0;top:0" width="1920" height="1080" viewBox="0 0 1920 1080">{svg}</svg>'
                 + self.title_html(pid, title, t0))
        for k, n in enumerate(nodes):
            ta = self.at(n["a"], t0)
            lx, ly = n["x"] + n.get("dx", -60), n["y"] + n.get("dy", 28)
            inner += self.hw(html.escape(n["n"]), lx, ly, n.get("s", 56), "ink", f"{pid}n{k}")
            self.write_on(f"#{pid}n{k}", ta + 0.1, 0.45)
            if n.get("date"):
                inner += self.hw(html.escape(str(n["date"])), lx, ly + 58, 46, "red", f"{pid}d{k}")
                self.write_on(f"#{pid}d{k}", ta + 0.35, 0.35)
        for k, it in enumerate(items):
            inner += self.hw(html.escape(it["t"]), it["x"], it["y"], it.get("s", 64), it.get("c", "red"), f"{pid}i{k}",
                             f'transform:rotate({it.get("rot", 0)}deg)')
            self.write_on(f"#{pid}i{k}", self.at(it["a"], t0), it.get("d", 0.7))
        self.els.append(self.page(t0, t1, inner, pid))
        self.fade_in(f"#{pid}", t0)

    def converge(self, t0, t1, title, labels, center, col=None, extra=()):
        col = col or "ink"
        cx, cy = 960, 620
        paths, items = [], []
        dirs = [(-1, 0, "Persia"), (0.2, 1, "India"), (1, 0, "China"), (0, -1, "the steppe"), (-0.75, 0.65, ""), (0.8, -0.6, "")]
        offs = {"Persia": (-20, -80), "China": (-120, -80), "India": (25, 0), "the steppe": (30, -10)}
        for k, (dx, dy, lab) in enumerate(dirs):
            n = math.hypot(dx, dy)
            ux, uy = dx / n, dy / n
            x0, y0 = cx + ux * 470, cy + uy * 300
            x1, y1 = cx + ux * 140, cy + uy * 95
            ang = math.atan2(y1 - y0, x1 - x0)
            hx1, hy1 = x1 - 26 * math.cos(ang - 0.5), y1 - 26 * math.sin(ang - 0.5)
            hx2, hy2 = x1 - 26 * math.cos(ang + 0.5), y1 - 26 * math.sin(ang + 0.5)
            a = self.at(labels[0], t0) + k * 0.22 - t0
            paths.append(dict(d=f"M{x0:.0f},{y0:.0f} L{x1:.0f},{y1:.0f} M{hx1:.0f},{hy1:.0f} L{x1:.0f},{y1:.0f} L{hx2:.0f},{hy2:.0f}",
                              a=a, c=col, w=7, len=800, dur=0.45))
            if lab and labels[1]:
                items.append(dict(t=lab, x=x0 + offs[lab][0], y=y0 + offs[lab][1], s=56, a=a + 0.2))
        ring = dict(d=self.circ(cx, cy, 120, 80), a=0.3, c=col, w=7, len=900, dur=0.7)
        items.append(dict(t=center, x=cx - 70, y=cy - 34, s=60, c="red", a=0.6))
        return self.notes(t0, t1, title, items=items + list(extra), paths=[ring] + paths)

    def end_card(self, t0, end):
        inner = (self.hw("See you in the next one.", 330, 360, 130, "ink", "endt")
                 + self.hw("Joel’s Notebook", 560, 560, 96, "red", "ends")
                 + f'<div id="endseal" class="abs" style="left:1440px;top:520px;transform:scale(1.6)">{self.SEAL}</div>')
        self.els.append(self.clip_div("endc", t0, end, '<div class="paper"></div>' + inner, "position:absolute;inset:0;z-index:20"))
        self.fade_in("#endc", t0, 0.4)
        self.write_on("#endt", t0 + 0.2, 1.0)
        self.write_on("#ends", t0 + 1.2, 0.6)
        self.tw(f'tl.fromTo("#endseal",{{opacity:0,scale:3,rotation:-25}},{{opacity:1,scale:1.6,rotation:-8,duration:0.35,'
                f'ease:"power3.in"}},{t0 + 1.9:.3f});')

    # ---------- CSS ----------
    def css(self):
        INK, RED, PAPER = self.INK, self.RED, self.PAPER
        cap = self.ch["captions"]
        return f"""
@font-face{{font-family:"Caveat";src:url("assets/fonts/caveat-700.woff2") format("woff2");font-weight:700}}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1920px;height:1080px;overflow:hidden;background:#000}}
#root{{position:relative;width:100%;height:100%;overflow:hidden;font-family:{cap['font']},sans-serif}}
.abs{{position:absolute}}
.shot{{position:absolute;inset:0;overflow:hidden}}
.vplate,.plate{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}
.paper{{position:absolute;inset:0;background:
  linear-gradient(90deg, transparent 176px, {RED}88 176px, {RED}88 180px, transparent 180px, transparent 188px, {RED}88 188px, {RED}88 192px, transparent 192px),
  repeating-linear-gradient(180deg, transparent 0 62px, #9CB4CC55 62px 64px),
  radial-gradient(ellipse at 50% 45%, {PAPER} 55%, #E2D2B0 100%)}}
.hw{{font-family:"Caveat",cursive;font-weight:700;line-height:1;white-space:nowrap;padding:0.3em 0.25em 0.25em 0.2em;margin:-0.3em 0 0 -0.2em}}
.rule2{{height:12px;border-top:4px solid {RED};border-bottom:4px solid {RED}}}
.strip{{font-family:"Caveat",cursive;font-weight:700;color:{INK};background:rgba(246,235,217,.9);padding:10px 34px 16px;border-bottom:4px double {RED};
  box-shadow:0 0 0 2px rgba(0,0,0,.05),0 8px 24px rgba(0,0,0,.35);white-space:nowrap}}
#vig{{position:absolute;inset:0;z-index:15;pointer-events:none;background:radial-gradient(ellipse at 50% 50%, rgba(0,0,0,0) 55%, rgba(0,0,0,.45) 100%)}}
.capwrap{{position:absolute;left:0;right:0;bottom:60px;display:flex;justify-content:center;z-index:40}}
.cap{{color:#fff;font-weight:800;font-size:{cap['size']}px;line-height:1.15;text-align:center;max-width:1500px;
 text-shadow:3px 3px 0 #000,-3px 3px 0 #000,3px -3px 0 #000,-3px -3px 0 #000,0 3px 0 #000,0 -3px 0 #000,3px 0 0 #000,-3px 0 0 #000,0 6px 16px rgba(0,0,0,.6)}}
#fade{{position:absolute;inset:0;background:#000;opacity:0;z-index:60}}
"""


# ================= episode build =================

def shot_times(c: Notebook, shots: list[dict], end: float) -> list[tuple[float, float]]:
    starts, prev = [], -1.0
    lead = c.ch["timing"]["shot_lead"]
    for k, s in enumerate(shots):
        t = 0.0 if k == 0 else c.T(s["at"], after=prev + 0.3) - lead
        starts.append(t)
        prev = t
    return list(zip(starts, starts[1:] + [end]))


def check(shots, times, channel, words) -> list[str]:
    """Retention warnings: shot length, image reuse, sparse long pages."""
    r = channel["retention"]
    warns, last_seen = [], {}
    for k, (s, (t0, t1)) in enumerate(zip(shots, times)):
        d = t1 - t0
        kind = s["type"]
        where = f"shot {k} @{t0:6.1f}s ({kind}: {s['at']!r})"
        if d < r["min_shot"]:
            warns.append(f"{where} only {d:.1f}s on screen")
        limit = r["max_page"] if kind in PAGE_TYPES else r["max_plate"]
        if d > limit and kind != "end":
            warns.append(f"{where} runs {d:.1f}s (limit {limit:.0f}s) — split it or add a beat")
        if kind in PAGE_TYPES and d > r["max_page"] * 0.7:
            beats = sorted([t0] + [words.at(x.get("a", 0.4), t0) for key in ("items", "paths", "strikes", "pops", "tokens", "nodes")
                                   for x in s.get(key, []) if isinstance(x, dict) and "a" in x] + [t1])
            gap = max((b - a for a, b in zip(beats, beats[1:])), default=d)
            if gap > r["page_beat_gap"] * 1.5:
                warns.append(f"{where} has a {gap:.1f}s stretch with nothing new appearing")
        if kind == "plate":
            img = s.get("video") or s["img"]
            if img in last_seen and t0 - last_seen[img] < r["reuse_gap"]:
                warns.append(f"{where} reuses {img} only {t0 - last_seen[img]:.0f}s after its last use")
            last_seen[img] = t1
    return warns


def build(project_dir: Path, out: Path, until: float | None = None, check_only=False, log=print) -> Path | None:
    from pipeline.words import Words
    P = Path(project_dir)
    channel = load_channel()
    words = Words.load(P / "words.json")
    ep = yaml.safe_load((P / "episode.yaml").read_text())
    shots = yaml.safe_load((P / ep.get("shots", "shots.yaml")).read_text())
    c = Notebook(words, out, P, channel)
    end = ep.get("end") or {}
    last = words.T(end["anchor"], after=end.get("after", 0), end=True) if end.get("anchor") else words.words[-1]["e"]
    END = round(last + channel["timing"]["end_hold"], 2)
    times = shot_times(c, shots, END)

    warns = check(shots, times, channel, words)
    if check_only:
        for k, (s, (t0, t1)) in enumerate(zip(shots, times)):
            log(f"{k:3d} {t0:7.2f} {t1 - t0:5.2f}  {s['type']:8s} {s['at']}")
        log(f"END {END}  shots {len(shots)}")
    for w in warns:
        log("⚠ " + w)
    if check_only:
        return None

    stop = min(END, until) if until else END
    custom = None
    if (P / "custom.py").exists():
        spec = importlib.util.spec_from_file_location("episode_custom", P / "custom.py")
        custom = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(custom)
    for k, (s, (t0, t1)) in enumerate(zip(shots, times)):
        if t0 >= stop:
            break
        args = {k2: v for k2, v in s.items() if k2 not in ("at", "type")}
        kind = s["type"]
        if kind == "plate":
            c.plate(t0, t1, args["img"], args.get("move", "in"), args.get("fx"), args.get("video"), args.get("label"), k)
        elif kind == "notes":
            c.notes(t0, t1, **args)
        elif kind == "relay":
            c.relay(t0, t1, **args)
        elif kind == "map":
            c.map(t0, t1, **args)
        elif kind == "converge":
            a = args["labels"]
            c.converge(t0, t1, args["title"], (a[0], a[1]), args["center"], args.get("col"))
        elif kind == "custom":
            if not custom or not hasattr(custom, args["page"]):
                raise PipelineError(f"custom page {args['page']!r} not defined in custom.py")
            getattr(custom, args["page"])(c, t0, t1)
        elif kind == "end":
            c.end_card(t0, END)
        else:
            raise PipelineError(f"unknown shot type {kind!r} in shot {k}")
    # free-floating label strips: {text, at, until_shot, left, top, size, lead}
    for st in ep.get("strips", []):
        t = c.T(st["at"]) - st.get("lead", 0.1)
        if t >= stop:
            continue
        t_out = times[st["until_shot"]][1] + st.get("tail", 0.1)
        c.strip(st["text"], t, t_out, st.get("left", 70), st.get("top", 70), st.get("size", 64))

    cap = channel["captions"]
    layers = '<div id="vig"></div>' + c.captions(cap["max_words"], cap["max_chars"], until=stop) + '<div id="fade"></div>'
    c.tw(f'tl.fromTo("#fade",{{opacity:0}},{{opacity:1,duration:0.7,ease:"none"}},{stop - 0.75:.3f});')
    font = ROOT / "node_modules/@fontsource/caveat/files/caveat-latin-700-normal.woff2"
    path = c.write(c.css(), stop, layers, fonts={"caveat-700.woff2": font})
    log(f"composed {len(shots)} shots → {path} ({stop:.1f}s, {len(c.els)} elements, {len(c.js)} tweens)")
    return path
