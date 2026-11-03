"""Joel's Notebook motion comic: full Silk Road episode. Writes <out>/index.html.
Usage: python3 silk_comic.py <projdir> <outdir>
projdir needs words.json, ai/<plates>, music+voice mix at <out>/assets/audio.wav (made separately).
"""
import sys, json, html, pathlib, shutil, random
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from cartoon_kit import Cartoon

P = pathlib.Path(sys.argv[1]); OUT = pathlib.Path(sys.argv[2]); ROOT = pathlib.Path(__file__).resolve().parent.parent
for d in ("assets/js", "assets/fonts", "assets/img"): (OUT / d).mkdir(parents=True, exist_ok=True)
shutil.copy(ROOT / "node_modules/gsap/dist/gsap.min.js", OUT / "assets/js/gsap.min.js")
shutil.copy(ROOT / "node_modules/@fontsource/caveat/files/caveat-latin-700-normal.woff2", OUT / "assets/fonts/caveat-700.woff2")
for f in ("hyperframes.json", "meta.json"): shutil.copy(ROOT / "smoketest" / f, OUT / f)

words = json.load(open(P / "words.json")); c = Cartoon(words); T = c.T; js = c.js
END = round(T("in the next one", after=820, end=True) + 5.2, 2)
INK = "#2A2733"; RED = "#B3261E"; PAPER = "#F3E9D2"; CREAM = "#F6EBD9"
XF = 0.45  # cross-dissolve length

els, n_el = [], [0]

def nid(p="e"):
    n_el[0] += 1; return f"{p}{n_el[0]}"

def clip_div(id_, t0, t1, inner, style="", cls=""):
    return f'<div id="{id_}" class="clip {cls}" data-start="{t0:.3f}" data-duration="{t1 - t0:.3f}" style="{style}">{inner}</div>'

def fade_in(sel, t, d=XF):
    js.append(f'tl.fromTo("{sel}",{{opacity:0}},{{opacity:1,duration:{d},ease:"power1.inOut"}},{t:.3f});')

def kb(sel, t0, t1, m):
    s0, s1, x0, x1, y0, y1 = m
    js.append(f'tl.fromTo("{sel}",{{scale:{s0},x:{x0},y:{y0}}},{{scale:{s1},x:{x1},y:{y1},duration:{t1 - t0:.3f},ease:"none"}},{t0:.3f});')

def particles(kind, t0, t1, seed):
    r = random.Random(seed); pid = nid("pt"); dots = []
    n = 34 if kind != "embers" else 26
    for i in range(n):
        x, y = r.randint(0, 1900), r.randint(60, 1040); s = r.choice((3, 4, 5, 6)) if kind != "sand" else r.choice((2, 3, 4))
        col = "#FFD9A0" if kind == "embers" else "#F6E7C8"
        dots.append(f'<i id="{pid}_{i}" style="position:absolute;left:{x}px;top:{y}px;width:{s}px;height:{s}px;border-radius:50%;background:{col};opacity:{r.uniform(.25, .7):.2f};box-shadow:0 0 {s * 2}px {col}"></i>')
        dx = r.randint(120, 320) * (1 if kind != "embers" else r.choice((-1, 1)) * 0.3)
        dy = r.randint(-40, 40) if kind != "embers" else -r.randint(160, 380)
        if kind == "sand": dx, dy = r.randint(500, 900), r.randint(-30, 30)
        js.append(f'tl.fromTo("#{pid}_{i}",{{x:0,y:0}},{{x:{dx},y:{dy},duration:{t1 - t0 + XF:.3f},ease:"none"}},{t0:.3f});')
    return f'<div class="abs" style="inset:0;pointer-events:none">{"".join(dots)}</div>'

def strip(text, t, t_out, left=70, top=70, size=64):
    sid = nid("st")
    els.append(clip_div(sid, t, t_out, f'<div class="strip" style="font-size:{size}px">{html.escape(text)}</div>',
                        f"position:absolute;left:{left}px;top:{top}px;z-index:30"))
    js.append(f'tl.fromTo("#{sid} .strip",{{x:-60,opacity:0}},{{x:0,opacity:1,duration:0.45,ease:"power3.out"}},{t:.3f});')
    js.append(f'tl.to("#{sid} .strip",{{opacity:0,duration:0.3}},{t_out - 0.3:.3f});')

def write_on(sel, t, d=0.6):
    js.append(f'tl.fromTo("{sel}",{{clipPath:"inset(0 100% 0 0)"}},{{clipPath:"inset(0 0% 0 0)",duration:{d},ease:"none"}},{t:.3f});')

def draw(sel, t, d=0.8, length=2000):
    js.append(f'tl.fromTo("{sel}",{{strokeDashoffset:{length}}},{{strokeDashoffset:0,duration:{d},ease:"power1.inOut"}},{t:.3f});')

def hw(text, x, y, size=72, color=INK, id_=None, extra=""):
    return f'<div {f"id={chr(34)}{id_}{chr(34)}" if id_ else ""} class="hw abs" style="left:{x}px;top:{y}px;font-size:{size}px;color:{color};{extra}">{text}</div>'

SEAL = (f'<svg viewBox="0 0 200 200" width="170" height="170"><g fill="{RED}"><circle cx="100" cy="100" r="84"/>'
        + "".join(f'<circle cx="{100 + 86 * __import__("math").cos(a / 18 * 3.14159)}" cy="{100 + 86 * __import__("math").sin(a / 18 * 3.14159)}" r="9"/>' for a in range(36))
        + f'</g><circle cx="100" cy="100" r="64" fill="none" stroke="{PAPER}" stroke-width="4" opacity=".8"/>'
        f'<text x="100" y="122" text-anchor="middle" font-family="EB Garamond" font-size="64" font-weight="700" fill="{PAPER}">JN</text></svg>')

def page(t0, t1, inner, pid):
    return clip_div(pid, t0, t1 + XF, f'<div class="paper"></div>{inner}<div class="abs" style="right:70px;top:60px;opacity:.9">{SEAL}</div>', "position:absolute;inset:0", "shot")

def demo_page(kind, t0, t1):
    if False: pass
    elif kind == "page_map":
        pid = nid("pg")
        route = "M240,700 C380,640 420,520 560,540 S760,700 900,620 S1120,420 1260,470 S1480,620 1640,520"
        mtn = "".join(f'<path d="M{x},{y} l40,-70 l40,70" stroke="{INK}" stroke-width="5" fill="none" stroke-linejoin="round"/>' for x, y in ((980, 420), (1040, 400), (1100, 430)))
        dunes = "".join(f'<path d="M{x},{y} q30,-24 60,0 q30,-24 60,0" stroke="{INK}" stroke-width="4" fill="none" opacity=".6"/>' for x, y in ((420, 760), (640, 470), (720, 760), (1300, 640), (1500, 700)))
        svg = (f'<svg class="abs" style="left:0;top:0" width="1920" height="1080" viewBox="0 0 1920 1080">{dunes}{mtn}'
               f'<path id="{pid}r" d="{route}" stroke="{RED}" stroke-width="9" fill="none" stroke-dasharray="22 18" stroke-linecap="round"/>'
               f'<path id="{pid}rm" d="{route}" stroke="{PAPER}" stroke-width="16" fill="none" stroke-dasharray="2400" stroke-dashoffset="0"/>'
               f'<circle cx="240" cy="700" r="16" fill="{INK}"/><circle cx="1640" cy="520" r="16" fill="{INK}"/></svg>')
        inner = (svg + hw("Central Asia", 250, 150, 96, INK, f"{pid}t") + f'<div id="{pid}u" class="abs rule2" style="left:250px;top:262px;width:520px"></div>'
                 + hw("desert", 430, 790, 54) + hw("more desert", 610, 400, 54) + hw("mountains", 1040, 300, 54) + hw("…more desert", 1360, 720, 54)
                 + hw("≈ 4 months", 760, 860, 110, RED, f"{pid}m"))
        els.append(page(t0, t1, inner, pid)); fade_in(f"#{pid}", t0)
        write_on(f"#{pid}t", t0 + 0.2, 0.7); js.append(f'tl.fromTo("#{pid}u",{{scaleX:0,transformOrigin:"0% 50%"}},{{scaleX:1,duration:0.4}},{t0 + 0.8:.3f});')
        js.append(f'tl.fromTo("#{pid}rm",{{strokeDashoffset:0}},{{strokeDashoffset:-2400,duration:{min(2.4, t1 - t0 - 0.6):.2f},ease:"power1.inOut"}},{t0 + 0.3:.3f});')
        write_on(f"#{pid}m", T("four months") - 0.05, 0.7)
    elif kind == "page_chain":
        pid = nid("pg"); xs = [260, 480, 700, 960, 1220, 1440, 1660]; figs = ""
        for k, x in enumerate(xs):
            far = k in (0, 6); me = k == 3
            figs += (f'<g id="{pid}f{k}" opacity="{0.35 if far else 1}"><circle cx="{x}" cy="500" r="{46 if me else 38}" fill="none" stroke="{INK}" stroke-width="6" {"stroke-dasharray=\"10 10\"" if far else ""}/>'
                     f'<path d="M{x},{546 if me else 538} L{x},{650} M{x - 50},{590} L{x + 50},{590} M{x},{650} L{x - 40},{720} M{x},{650} L{x + 40},{720}" stroke="{INK}" stroke-width="6" stroke-linecap="round" {"stroke-dasharray=\"10 10\"" if far else ""}/></g>')
            if k < 6:
                figs += f'<path class="{pid}ar" id="{pid}a{k}" d="M{x + 60},{560} L{xs[k + 1] - 60},{560} M{xs[k + 1] - 80},{545} L{xs[k + 1] - 60},{560} L{xs[k + 1] - 80},{575}" stroke="{INK}" stroke-width="5" fill="none" stroke-linecap="round" stroke-dasharray="400" stroke-dashoffset="400"/>'
        figs += f'<ellipse id="{pid}ring" cx="960" cy="590" rx="130" ry="190" fill="none" stroke="{RED}" stroke-width="7" stroke-dasharray="1100" stroke-dashoffset="1100"/>'
        inner = (f'<svg class="abs" style="left:0;top:0" width="1920" height="1080" viewBox="0 0 1920 1080">{figs}</svg>'
                 + hw("Who he never met", 250, 150, 96, INK, f"{pid}t") + f'<div id="{pid}u" class="abs rule2" style="left:250px;top:262px;width:640px"></div>'
                 + hw("our merchant", 860, 780, 60, RED, f"{pid}me") + hw("the maker", 170, 760, 54, INK, f"{pid}mk", "opacity:.7")
                 + hw("the buyer", 1580, 760, 54, INK, f"{pid}by", "opacity:.7") + hw("?", 470, 380, 80, RED, f"{pid}q1") + hw("?", 1430, 380, 80, RED, f"{pid}q2"))
        els.append(page(t0, t1, inner, pid)); fade_in(f"#{pid}", t0)
        write_on(f"#{pid}t", t0 + 0.15, 0.7); js.append(f'tl.fromTo("#{pid}u",{{scaleX:0,transformOrigin:"0% 50%"}},{{scaleX:1,duration:0.4}},{t0 + 0.75:.3f});')
        tm = T("made his goods"); tb = T("finally buys")
        for k in range(3): draw(f"#{pid}a{2 - k}", tm - 0.6 + k * 0.25, 0.3, 400)
        for k in range(3, 6): draw(f"#{pid}a{k}", tb - 0.9 + (k - 3) * 0.25, 0.3, 400)
        draw(f"#{pid}ring", t0 + 0.6, 0.6, 1100); write_on(f"#{pid}me", t0 + 1.0, 0.5)
        write_on(f"#{pid}mk", tm, 0.5); write_on(f"#{pid}by", tb, 0.5)
        js.append(f'tl.fromTo("#{pid}q1",{{opacity:0,scale:0.4}},{{opacity:1,scale:1,duration:0.3,ease:"back.out(2)"}},{tm + 0.3:.3f});')
        js.append(f'tl.fromTo("#{pid}q2",{{opacity:0,scale:0.4}},{{opacity:1,scale:1,duration:0.3,ease:"back.out(2)"}},{tb + 0.3:.3f});')
    elif kind == "page_list":
        pid = nid("pg"); items = ["silk", "spices", "gold", "glass", "everybody gets rich"]
        inner = hw("The story we're told", 250, 150, 96, INK, f"{pid}t") + f'<div id="{pid}u" class="abs rule2" style="left:250px;top:262px;width:760px"></div>'
        for k, it in enumerate(items):
            inner += hw(("☐ " if k < 4 else "→ ") + it, 330, 330 + k * 112, 80, INK if k < 4 else RED, f"{pid}i{k}")
            if k < 4: inner += hw("✓", 336, 318 + k * 112, 84, RED, f"{pid}c{k}", "opacity:0")
        inner += hw("a shopping list?", 1180, 640, 76, RED, f"{pid}sl", "transform:rotate(-6deg)")
        els.append(page(t0, t1, inner, pid)); fade_in(f"#{pid}", t0)
        write_on(f"#{pid}t", t0 + 0.2, 0.8); js.append(f'tl.fromTo("#{pid}u",{{scaleX:0,transformOrigin:"0% 50%"}},{{scaleX:1,duration:0.4}},{t0 + 0.9:.3f});')
        ts = T("shopping list") - 0.6
        for k in range(5): write_on(f"#{pid}i{k}", ts + k * 0.32, 0.4)
        for k in range(4): js.append(f'tl.set("#{pid}c{k}",{{opacity:1}},{ts + 1.8 + k * 0.18:.3f});')
        write_on(f"#{pid}sl", T("shopping list") + 0.2, 0.6)
    elif kind == "page_eastwest":
        pid = nid("pg")
        arr_w = f'M1500,470 C1200,420 760,420 430,470 M460,445 L430,470 L462,494'
        arr_e = f'M430,620 C760,670 1200,670 1500,620 M1470,596 L1500,620 L1468,646'
        inner = (f'<svg class="abs" style="left:0;top:0" width="1920" height="1080" viewBox="0 0 1920 1080">'
                 f'<path id="{pid}w" d="{arr_w}" stroke="{RED}" stroke-width="9" fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="1300" stroke-dashoffset="1300"/>'
                 f'<path id="{pid}e" d="{arr_e}" stroke="{INK}" stroke-width="9" fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="1300" stroke-dashoffset="1300"/></svg>'
                 + hw("WEST", 150, 500, 88, INK, f"{pid}lw") + hw("EAST", 1560, 500, 88, INK, f"{pid}le")
                 + hw("(Rome)", 170, 600, 56, INK, f"{pid}lr", "opacity:.75") + hw("(China)", 1575, 600, 56, INK, f"{pid}lc", "opacity:.75")
                 + hw("silk", 880, 330, 84, RED, f"{pid}s") + hw("spices · gold · glass", 700, 690, 76, INK, f"{pid}g")
                 + hw("A trade route.", 250, 150, 96, INK, f"{pid}t") + f'<div id="{pid}u" class="abs rule2" style="left:250px;top:262px;width:600px"></div>'
                 + hw("goods in, goods out", 700, 850, 64, RED, f"{pid}gi"))
        els.append(page(t0, t1, inner, pid)); fade_in(f"#{pid}", t0)
        write_on(f"#{pid}lw", t0 + 0.1, 0.4); write_on(f"#{pid}le", t0 + 0.1, 0.4); write_on(f"#{pid}lr", t0 + 0.4, 0.4); write_on(f"#{pid}lc", t0 + 0.4, 0.4)
        draw(f"#{pid}w", T("Silk going") - 0.05, 0.9, 1300); write_on(f"#{pid}s", T("Silk going") + 0.2, 0.4)
        draw(f"#{pid}e", T("Spices") - 0.05, 0.9, 1300); write_on(f"#{pid}g", T("Spices") + 0.1, 1.0)
        write_on(f"#{pid}t", T("A trade route") - 0.05, 0.7); js.append(f'tl.fromTo("#{pid}u",{{scaleX:0,transformOrigin:"0% 50%"}},{{scaleX:1,duration:0.35}},{T("A trade route") + 0.6:.3f});')
        write_on(f"#{pid}gi", T("Goods in") - 0.05, 0.8)


# ================= full-episode engines =================
MV = {"in": (1.0, 1.12, 0, 0, 0, 0), "out": (1.14, 1.02, 0, 0, 0, 0), "L": (1.12, 1.12, 70, -70, 0, 0), "R": (1.12, 1.12, -70, 70, 0, 0),
      "up": (1.12, 1.12, 0, 0, 45, -45), "down": (1.12, 1.12, 0, 0, -45, 45), "inL": (1.04, 1.2, 0, 90, 0, 0), "inR": (1.04, 1.2, 0, -90, 0, 0),
      "inUp": (1.04, 1.2, 0, 0, 0, 60), "inDown": (1.04, 1.2, 0, 0, 0, -60)}

def at(x, t0):
    if isinstance(x, str):
        end = x.startswith(">"); ph = x[1:] if end else x
        return T(ph, after=t0 - 1.5, end=end)
    return t0 + x

def plate(t0, t1, img, m="in", fx=None, video=None, i=0):
    motion = MV[m] if isinstance(m, str) else m
    if video and (P / "ai" / video).exists():
        shutil.copy(P / "ai" / video, OUT / "assets/img" / video)
        vlen = min(t1 - t0 + XF, 4.8); vidid = nid("v")
        els.append(f'<video id="{vidid}" class="clip shot vplate" src="assets/img/{video}" muted data-start="{t0:.3f}" data-duration="{vlen:.3f}"></video>')
        fade_in(f"#{vidid}", t0); js.append(f'tl.fromTo("#{vidid}",{{scale:1}},{{scale:1.05,duration:{vlen:.3f},ease:"none"}},{t0:.3f});')
        if t0 + vlen < t1 + XF - 0.2:
            last = video.replace(".mp4", "_last.jpg"); sid = nid("p"); shutil.copy(P / "ai" / last, OUT / "assets/img" / last)
            ts = t0 + vlen - XF
            els.append(clip_div(sid, ts, t1 + XF, f'<img class="plate" src="assets/img/{last}">', "position:absolute;inset:0;overflow:hidden", "shot"))
            fade_in(f"#{sid}", ts); js.append(f'tl.fromTo("#{sid} .plate",{{scale:1.05}},{{scale:1.12,duration:{t1 + XF - ts:.3f},ease:"none"}},{ts:.3f});')
    else:
        sid = nid("p"); shutil.copy(P / "ai" / img, OUT / "assets/img" / img)
        els.append(clip_div(sid, t0, t1 + XF, f'<img class="plate" src="assets/img/{img}">', "position:absolute;inset:0;overflow:hidden", "shot"))
        if t0 > 0: fade_in(f"#{sid}", t0)
        kb(f"#{sid} .plate", t0, t1 + XF, motion)
    if fx:
        fid = nid("fx"); els.append(clip_div(fid, t0, t1 + XF, particles(fx, t0, t1, i), "position:absolute;inset:0;z-index:5"))
        fade_in(f"#{fid}", t0)

def title_html(pid, text, t, size=96, x=250, y=150, color=INK):
    w = int(len(text) * size * 0.40) + 20
    js_t = t + 0.15; write_on(f"#{pid}t", js_t, min(1.0, 0.25 + len(text) * 0.035))
    js.append(f'tl.fromTo("#{pid}u",{{scaleX:0,transformOrigin:"0% 50%"}},{{scaleX:1,duration:0.4}},{js_t + 0.6:.3f});')
    return hw(html.escape(text), x, y, size, color, f"{pid}t") + f'<div id="{pid}u" class="abs rule2" style="left:{x}px;top:{y + size + 16}px;width:{w}px"></div>'

def circ(cx, cy, rx, ry=None):
    ry = ry or rx
    return f"M{cx},{cy - ry} a{rx},{ry} 0 1,1 -1,0"

def notes(t0, t1, title=None, items=(), paths=(), strikes=(), pops=(), tsize=96, svg_static=""):
    """items: dict(t,x,y,s,c,a,d,rot,op)  paths: dict(d,a,c,w,len,dur,dash)  strikes: dict(x,y,w,a,c)  pops: dict(html,x,y,a)"""
    pid = nid("pg"); inner = ""
    if title: inner += title_html(pid, title, t0, tsize)
    svg = svg_static
    for k, p in enumerate(paths):
        L = p.get("len", 1500); dash = f'stroke-dasharray="{L}" stroke-dashoffset="{L}"'
        svg += f'<path id="{pid}p{k}" d="{p["d"]}" stroke="{p.get("c", INK)}" stroke-width="{p.get("w", 7)}" fill="{p.get("fill", "none")}" stroke-linecap="round" stroke-linejoin="round" {dash}/>'
        draw(f"#{pid}p{k}", at(p.get("a", 0.3), t0), p.get("dur", 0.6), L)
    for k, s in enumerate(strikes):
        svg += f'<path id="{pid}s{k}" d="M{s["x"]},{s["y"]} q{s["w"] / 2},-10 {s["w"]},4" stroke="{s.get("c", RED)}" stroke-width="8" fill="none" stroke-linecap="round" stroke-dasharray="{s["w"] + 40}" stroke-dashoffset="{s["w"] + 40}"/>'
        draw(f"#{pid}s{k}", at(s["a"], t0), 0.35, s["w"] + 40)
    if svg: inner = f'<svg class="abs" style="left:0;top:0" width="1920" height="1080" viewBox="0 0 1920 1080">{svg}</svg>' + inner
    for k, it in enumerate(items):
        rot = f'transform:rotate({it["rot"]}deg);' if it.get("rot") else ""
        op = f'opacity:{it["op"]};' if it.get("op") else ""
        inner += hw(html.escape(it["t"]), it["x"], it["y"], it.get("s", 72), it.get("c", INK), f"{pid}i{k}", rot + op)
        write_on(f"#{pid}i{k}", at(it.get("a", 0.4), t0), it.get("d", min(1.1, 0.2 + len(it["t"]) * 0.04)))
    for k, p in enumerate(pops):
        inner += f'<div id="{pid}o{k}" class="abs" style="left:{p["x"]}px;top:{p["y"]}px">{p["html"]}</div>'
        js.append(f'tl.fromTo("#{pid}o{k}",{{opacity:0,scale:0.3}},{{opacity:1,scale:1,duration:0.35,ease:"back.out(2)"}},{at(p["a"], t0):.3f});')
    els.append(page(t0, t1, inner, pid)); fade_in(f"#{pid}", t0)
    return pid

def relay(t0, t1, title, tokens, labels=None, items=(), stretches=None):
    pid = nid("pg"); xs = [260 + k * 233 for k in range(7)]; figs = ""
    for k, x in enumerate(xs):
        figs += (f'<circle cx="{x}" cy="470" r="36" fill="none" stroke="{INK}" stroke-width="6"/>'
                 f'<path d="M{x},506 L{x},620 M{x - 52},560 L{x + 52},560 M{x},620 L{x - 38},700 M{x},620 L{x + 38},700" stroke="{INK}" stroke-width="6" stroke-linecap="round" fill="none"/>')
    if stretches is not None:
        for k in range(6):
            a, b = xs[k] + 14, xs[k + 1] - 14; y = 742 + (k % 2) * 14
            figs += f'<path id="{pid}r{k}" d="M{a},{y} L{b},{y} M{a + 14},{y - 10} L{a},{y} L{a + 14},{y + 10} M{b - 14},{y - 10} L{b},{y} L{b - 14},{y + 10}" stroke="{RED if k % 2 else INK}" stroke-width="5" fill="none" stroke-linecap="round" stroke-dasharray="700" stroke-dashoffset="700"/>'
            draw(f"#{pid}r{k}", at(stretches, t0) + k * 0.12, 0.3, 700)
    inner = f'<svg class="abs" style="left:0;top:0" width="1920" height="1080" viewBox="0 0 1920 1080">{figs}</svg>' + title_html(pid, title, t0)
    if labels:
        inner += hw(labels[0], 150, 800, 60, INK, f"{pid}l0", "opacity:.75") + hw(labels[1], 1560, 800, 60, INK, f"{pid}l1", "opacity:.75")
        write_on(f"#{pid}l0", t0 + 0.4, 0.4); write_on(f"#{pid}l1", t0 + 0.4, 0.4)
    for k, tk in enumerate(tokens):
        col = tk.get("c", RED); ta = at(tk["a"], t0); dur = tk.get("dur", 6.0); y = tk.get("y", 380)
        inner += (f'<div id="{pid}k{k}" class="abs hw" style="left:0;top:{y}px;font-size:{tk.get("s", 54)}px;color:{col};border:4px solid {col};border-radius:12px;'
                  f'background:{PAPER};padding:2px 16px 8px;margin:0;transform:translateX(-50%)">{html.escape(tk["t"])}</div>')
        seq = xs[::-1] if tk.get("dir", "w") == "w" else xs
        js.append(f'tl.fromTo("#{pid}k{k}",{{x:{seq[0]},opacity:0}},{{x:{seq[0]},opacity:1,duration:0.25}},{ta:.3f});')
        hop = dur / 6
        for j in range(6):
            js.append(f'tl.fromTo("#{pid}k{k}",{{x:{seq[j]}}},{{x:{seq[j + 1]},duration:{hop * 0.6:.3f},ease:"power2.inOut"}},{ta + 0.25 + j * hop:.3f});')
        if tk.get("fade", True) and ta + 0.25 + 5 * hop + hop * 0.6 + 0.3 < t1:
            js.append(f'tl.to("#{pid}k{k}",{{opacity:0,duration:0.3}},{ta + 0.25 + 5 * hop + hop * 0.6 + 0.15:.3f});')
    for k, it in enumerate(items):
        inner += hw(html.escape(it["t"]), it["x"], it["y"], it.get("s", 64), it.get("c", INK), f"{pid}i{k}", f'transform:rotate({it.get("rot", 0)}deg)')
        write_on(f"#{pid}i{k}", at(it["a"], t0), it.get("d", min(1.0, 0.2 + len(it["t"]) * 0.04)))
    els.append(page(t0, t1, inner, pid)); fade_in(f"#{pid}", t0)

def mapp(t0, t1, title, nodes, color=INK, spread=False, route_at=None, items=(), doodles=True):
    pid = nid("pg"); svg = ""
    if doodles:
        svg += "".join(f'<path d="M{x},{y} l34,-60 l34,60" stroke="{INK}" stroke-width="4" fill="none" opacity=".45" stroke-linejoin="round"/>' for x, y in ((1220, 330), (1268, 316), (1316, 336)))
        svg += "".join(f'<path d="M{x},{y} q26,-20 52,0 q26,-20 52,0" stroke="{INK}" stroke-width="4" fill="none" opacity=".4"/>' for x, y in ((1000, 760), (1300, 700), (700, 780)))
    pts = [(n["x"], n["y"]) for n in nodes]
    segs = []
    for k in range(1, len(pts)):
        (x0, y0), (x1, y1) = pts[k - 1], pts[k]; mx, my = (x0 + x1) / 2, (y0 + y1) / 2 - 60
        segs.append(f"M{x0},{y0} Q{mx},{my} {x1},{y1}")
    for k, d in enumerate(segs):
        svg += f'<path id="{pid}g{k}" d="{d}" stroke="{color}" stroke-width="8" fill="none" stroke-linecap="round" stroke-dasharray="2000" stroke-dashoffset="2000"/>'
        ta = at(route_at, t0) + k * 0.25 if route_at is not None else at(nodes[k + 1]["a"], t0) - 0.5
        draw(f"#{pid}g{k}", ta, 0.55, 2000)
    for k, n in enumerate(nodes):
        ta = at(n["a"], t0)
        if spread:
            svg += f'<circle id="{pid}b{k}" cx="{n["x"]}" cy="{n["y"]}" r="70" fill="{RED}" opacity="0"/>'
            js.append(f'tl.fromTo("#{pid}b{k}",{{attr:{{r:6}},opacity:0.55}},{{attr:{{r:{n.get("r", 70)}}},opacity:0.28,duration:1.4,ease:"power2.out"}},{ta:.3f});')
        svg += f'<circle id="{pid}c{k}" cx="{n["x"]}" cy="{n["y"]}" r="15" fill="{RED if spread else INK}" opacity="0"/>'
        js.append(f'tl.fromTo("#{pid}c{k}",{{opacity:0,attr:{{r:4}}}},{{opacity:1,attr:{{r:15}},duration:0.3,ease:"back.out(3)"}},{ta:.3f});')
    inner = f'<svg class="abs" style="left:0;top:0" width="1920" height="1080" viewBox="0 0 1920 1080">{svg}</svg>' + title_html(pid, title, t0)
    for k, n in enumerate(nodes):
        ta = at(n["a"], t0); lx, ly = n["x"] + n.get("dx", -60), n["y"] + n.get("dy", 28)
        inner += hw(html.escape(n["n"]), lx, ly, n.get("s", 56), INK, f"{pid}n{k}"); write_on(f"#{pid}n{k}", ta + 0.1, 0.45)
        if n.get("date"):
            inner += hw(html.escape(n["date"]), lx, ly + 58, 46, RED, f"{pid}d{k}"); write_on(f"#{pid}d{k}", ta + 0.35, 0.35)
    for k, it in enumerate(items):
        inner += hw(html.escape(it["t"]), it["x"], it["y"], it.get("s", 64), it.get("c", RED), f"{pid}i{k}", f'transform:rotate({it.get("rot", 0)}deg)')
        write_on(f"#{pid}i{k}", at(it["a"], t0), it.get("d", 0.7))
    els.append(page(t0, t1, inner, pid)); fade_in(f"#{pid}", t0)

def converge(t0, t1, title, labels, center, col=INK, extra=()):
    cx, cy = 960, 620; paths = []; items = []
    dirs = [(-1, 0, "Persia"), (0.2, 1, "India"), (1, 0, "China"), (0, -1, "the steppe"), (-0.75, 0.65, ""), (0.8, -0.6, "")]
    import math
    for k, (dx, dy, lab) in enumerate(dirs):
        n = math.hypot(dx, dy); ux, uy = dx / n, dy / n
        x0, y0 = cx + ux * 470, cy + uy * 300; x1, y1 = cx + ux * 140, cy + uy * 95
        ang = math.atan2(y1 - y0, x1 - x0); hx1, hy1 = x1 - 26 * math.cos(ang - 0.5), y1 - 26 * math.sin(ang - 0.5); hx2, hy2 = x1 - 26 * math.cos(ang + 0.5), y1 - 26 * math.sin(ang + 0.5)
        paths.append(dict(d=f"M{x0:.0f},{y0:.0f} L{x1:.0f},{y1:.0f} M{hx1:.0f},{hy1:.0f} L{x1:.0f},{y1:.0f} L{hx2:.0f},{hy2:.0f}", a=labels[0], c=col, w=7, len=800, dur=0.45))
        paths[-1]["a"] = at(labels[0], t0) + k * 0.22 - t0
        if lab and labels[1]:
            off = {"Persia": (-20, -80), "China": (-120, -80), "India": (25, 0), "the steppe": (30, -10)}[lab]
            items.append(dict(t=lab, x=x0 + off[0], y=y0 + off[1], s=56, a=paths[-1]["a"] + 0.2))
    ring = dict(d=circ(cx, cy, 120, 80), a=0.3, c=col, w=7, len=900, dur=0.7)
    items.append(dict(t=center, x=cx - 70, y=cy - 34, s=60, c=RED, a=0.6))
    return notes(t0, t1, title, items=items + list(extra), paths=[ring] + paths)


# ================= SHOT LIST =================
def Pl(img, m="in", fx=None, video=None, strip_=None): return ("plate", dict(img=img, m=m, fx=fx, video=video, strip=strip_))
CROP_N07 = (1.5, 1.58, 400, 420, 200, 215); CROP_N24 = (1.3, 1.38, 250, 270, 110, 130)
SHOTS = [
    ("Picture", *Pl("s1.jpg", (1.0, 1.08, 0, -40, 0, 0), "dust", "v_s1.mp4")),
    ("He's got a camel", *Pl("s2.jpg", (1.12, 1.04, 60, -60, 0, 0), "dust")),
    ("and he's spent", "demo", "page_map"),
    ("lethal terrain", *Pl("s4.jpg", (1.06, 1.16, 0, 0, 0, -20), "sand")),
    ("Now ask yourself", *Pl("s5.jpg", (1.02, 1.16, 0, -30, 0, 20), "dust")),
    ("What's on that camel", *Pl("s6.jpg", (1.15, 1.05, 0, 0, -20, 20))),
    ("Almost everyone says", *Pl("s7.jpg", (1.0, 1.1, -30, 30, 0, 0))),
    ("But here's the thing", *Pl("s8.jpg", (1.1, 1.0, -70, 70, 0, 0), "dust")),
    ("never met the person", "demo", "page_chain"),
    ("And what he was really", *Pl("s10.jpg", (1.0, 1.1, 0, 0, 0, -10), "embers", "v_s10.mp4")),
    ("So the story we all", "demo", "page_list"),
    ("The Silk Road was", *Pl("s12.jpg", (1.0, 1.08, 0, -60, 0, 0), "dust", "v_s12.mp4")),
    ("Silk going one way", "demo", "page_eastwest"),
    ("China sold silk", *Pl("s15.jpg", (1.06, 1.0, 0, 0, 0, 0))),
    ("everybody got rich", *Pl("s16.jpg", (1.0, 1.12, 0, 0, 0, -15), "embers")),
    # P2
    ("And look, on the surface", *Pl("s7.jpg", "R")),
    ("Spices did move", *Pl("n01.jpg", "inR", "dust")),
    ("But as the actual explanation", "notes", dict(title="But how did it physically work?", tsize=88,
        pops=[dict(html=f'<div class="hw" style="font-size:260px;color:{RED}">?</div>', x=860, y=420, a="physically")])),
    # P3
    ("Because here's the problem", *Pl("s12.jpg", "out", "dust")),
    ("Nobody actually travelled", "notes", dict(title="Who travelled the whole road?", items=[
        dict(t="Nobody.", x=700, y=430, s=170, c=RED, a=0.35), dict(t="(not the whole thing)", x=720, y=650, s=64, a="Not the whole")])),
    ("There was no merchant", *Pl("n03.jpg", "inL", None, None, "Chang’an, China")),
    ("rode all the way", *Pl("n04.jpg", "in", None, None, "the Mediterranean")),
    ("That journey was thousands", "map", dict(title="Thousands of miles", nodes=[
        dict(n="the Mediterranean", x=330, y=560, a=0.1, dx=-80), dict(n="Chang’an", x=1640, y=560, a=0.9, dx=-80)],
        items=[dict(t="4,000+ miles", x=820, y=600, s=84, a=1.2)])),
    ("deserts that kill you", *Pl("s4.jpg", "inUp", "sand")),
    ("mountains that kill you", *Pl("n06.jpg", "R", None, None, "the Pamirs")),
    ("and bandit territory", *Pl("n07.jpg", CROP_N07)),
    ("No single person did it", *Pl("n11.jpg", "out", "dust")),
    # P4
    ("So how did a bolt", *Pl("s15.jpg", "in")),
    ("It got passed", *Pl("n09.jpg", "in", None, "v_n09.mp4")),
    ("who carried it a few", *Pl("n10.jpg", "inR", "dust")),
    ("That trader sold it", *Pl("n13.jpg", "L", "dust")),
    ("Imagine a bucket brigade", "relay", dict(title="A bucket brigade", tokens=[dict(t="silk", a=0.9, dur=6.5)], labels=("Rome", "China"),
        items=[dict(t="the silk moved…", x=600, y=860, s=64, c=RED, a="The silk moved"), dict(t="the people didn’t", x=1060, y=860, s=64, a="The people mostly")],
        stretches="The people mostly")),
    ("Each one only knew", *Pl("n58.jpg", "in", "dust")),
    # P5
    ("And once you see", *Pl("n11.jpg", "inL")),
    ("Because if goods are", "relay", dict(title="Thousands of strangers", tokens=[dict(t="silk", a=0.3, dur=6)], labels=("west", "east"),
        items=[dict(t="who never meet", x=1150, y=290, s=64, c=RED, a="who never meet"), dict(t="the relay itself!", x=700, y=860, s=72, c=RED, a="relay itself")])),
    ("What else got passed", *Pl("s10.jpg", "in", "embers", "v_s10.mp4")),
    # P6
    ("So to understand what", *Pl("n16.jpg", "inR", "dust")),
    ("Because the Silk Road wasn't", *Pl("n11.jpg", "up", "dust")),
    ("It was a chain of oasis", "map", dict(title="The Silk Road", route_at="chain of oasis", nodes=[
        dict(n="Merv", x=560, y=600, a="Merv", dx=-40), dict(n="Bukhara", x=830, y=500, a="Bukhara", dx=-70),
        dict(n="Samarkand", x=1070, y=430, a="Samarkand", dx=-60, dy=-110), dict(n="Kashgar", x=1460, y=520, a="Kashgar", dx=-60)],
        items=[dict(t="a chain of oasis cities", x=700, y=760, s=72, a="chain of oasis", d=1.0)])),
    ("And these weren't just", *Pl("n14.jpg", "inUp", None, None, "Samarkand, c. 800")),
    ("These were the whole engine", *Pl("n15.jpg", "in", "dust")),
    # P7
    ("Think about what one", *Pl("s8.jpg", "inR", "dust")),
    ("for purely geographic", "converge", dict(title="Where the routes converge", labels=("routes have to converge", True), center="water")),
    ("Which means every few weeks", *Pl("n16.jpg", "L")),
    ("A man from Persia", *Pl("n17.jpg", "in")),
    ("A man from India", *Pl("n18.jpg", "in")),
    ("A man from China", *Pl("n19.jpg", "in")),
    ("A man from the steppe", *Pl("n20.jpg", "in")),
    ("All of them stuck", *Pl("n21.jpg", "inR", "embers")),
    ("waiting out the weather", *Pl("n22.jpg", "L", "sand")),
    # P8
    ("Now here's the thing nobody", "notes", dict(title="Not on the shopping list", items=[
        dict(t="silk · spices · gold · glass", x=330, y=360, s=72, a=0.4, op=.8), dict(t="IDEAS", x=760, y=520, s=200, c=RED, a="They carried ideas")],
        strikes=[dict(x=320, y=410, w=780, a="haggle")])),
    ("A Persian trader mentions", *Pl("n23.jpg", "in", "embers")),
    ("An Indian trader explains", *Pl("n24.jpg", CROP_N24)),
    ("for nothing, for zero", "notes", dict(paths=[dict(d="M960,300 C1110,300 1130,700 960,700 C790,700 810,300 960,300", a=0.05, c=RED, w=16, len=1400, dur=0.7)],
        items=[dict(t="shunya = “empty”", x=700, y=760, s=72, a=0.5)])),
    ("A Chinese trader describes", *Pl("n25.jpg", "inR")),
    ("A monk travelling", *Pl("n26.jpg", "in", "embers", "v_n26.mp4")),
    ("None of these things", *Pl("s6.jpg", "in")),
    ("But every single one", "relay", dict(title="Passed hand to hand", tokens=[
        dict(t="prayer", a=0.4, dur=7, y=300), dict(t="0", a=1.4, dur=7, y=380, c=INK), dict(t="paper", a=2.4, dur=7, y=300), dict(t="the Buddha", a=3.4, dur=7, y=380, c=INK)],
        items=[dict(t="town to town, mind to mind", x=560, y=860, s=72, c=RED, a="town to town, mind")])),
    # P9
    ("Silk is a luxury", *Pl("s7.jpg", "inL")),
    ("Now compare that", "notes", dict(title="Silk vs. everything else", items=[
        dict(t="silk", x=380, y=420, s=110, a=0.3), dict(t="= a fabric", x=330, y=560, s=64, a=0.7, op=.8), dict(t="vs.", x=860, y=450, s=90, c=RED, a=1.0),
        dict(t="?", x=1300, y=360, s=240, c=RED, a=1.3)])),
    ("Paper, the technology", *Pl("n29.jpg", "inL", None, None, "Baghdad, c. 800")),
    ("and eventually reached Europe", "map", dict(title="How paper travelled", nodes=[
        dict(n="China", x=1650, y=560, a=0.1, date="c. 100 CE"), dict(n="Samarkand", x=1180, y=440, a=0.6, date="c. 750"),
        dict(n="Baghdad", x=880, y=600, a=1.1, date="794"), dict(n="Spain", x=320, y=560, a=1.6, date="c. 1100s"),
        dict(n="Europe: printing press", x=600, y=440, a=2.2, date="c. 1450", dx=-150, dy=-120)])),
    ("it made the printing", *Pl("n28.jpg", "inR", None, None, "Europe, c. 1450")),
    ("The concept of zero", *Pl("n30.jpg", "inL", None, None, "Baghdad’s House of Wisdom")),
    ("Gunpowder moved west", *Pl("n31.jpg", "in", "embers", "v_n31.mp4")),
    ("Whole religions moved", *Pl("n32.jpg", "L")),
    ("carried by monks", *Pl("n26.jpg", "R", "embers")),
    ("Later, Islam spread", *Pl("n33.jpg", "inUp", "dust")),
    # P10
    ("So picture the real cargo", *Pl("s6.jpg", "inUp")),
    ("Not bolts of cloth", "notes", dict(title="The real cargo", svg_static=(
        f'<rect x="300" y="380" width="520" height="340" rx="60" fill="#E9D9B8" stroke="{INK}" stroke-width="7"/>'
        f'<path d="M300,550 L820,550 M560,380 L560,720" stroke="{INK}" stroke-width="6" stroke-dasharray="18 12"/>'
        f'<path d="M820,450 L1000,400 M820,520 L1000,540 M820,610 L1000,680 M820,680 L1000,820" stroke="{INK}" stroke-width="4" opacity=".55"/>'),
        items=[dict(t="bolts of cloth", x=1020, y=260, s=60, a=0.05, op=.75), dict(t="letters & scripts", x=1020, y=360, s=64, a="alphabet"),
               dict(t="0 1 2 3 …", x=1020, y=500, s=72, c=RED, a="The math"), dict(t="paper", x=1020, y=640, s=72, a="The paper this"),
               dict(t="faith", x=1020, y=780, s=72, c=RED, a="The faith")],
        strikes=[dict(x=1010, y=300, w=380, a=0.7)])),
    ("All of it moving quietly", *Pl("n35.jpg", "in", "dust")),
    ("hidden inside what looked", *Pl("s2.jpg", "L")),
    # P11
    ("The silk, it turns out", *Pl("s5.jpg", "in", "dust")),
    ("It was the thing valuable", *Pl("n09.jpg", "inL")),
    ("But the desert crossing", *Pl("n36.jpg", "in", None, "v_n36.mp4")),
    # P12
    ("So now the question", "notes", dict(title="So what was it FOR?", items=[
        dict(t="the most important things…", x=330, y=400, s=72, a="the most important"), dict(t="…were the things nobody was trading", x=420, y=520, s=72, c=RED, a="things nobody")])),
    ("What was really being exchanged", *Pl("n37.jpg", "in", "embers")),
    # P13
    ("And here's where it turns", *Pl("n38.jpg", "inR", "embers")),
    # P14
    ("We love to imagine", *Pl("n39.jpg", "in", "embers")),
    ("humanity coming together", *Pl("n13.jpg", "inUp", "dust")),
    ("And there's a sliver", "notes", dict(title="The warm story", items=[
        dict(t="peaceful exchange", x=330, y=360, s=72, a=0.2), dict(t="sharing wisdom", x=330, y=460, s=72, a=0.5), dict(t="humanity united", x=330, y=560, s=72, a=0.8),
        dict(t="→ money.", x=1050, y=470, s=130, c=RED, a="money in it")],
        strikes=[dict(x=320, y=410, w=520, a="not why"), dict(x=320, y=510, w=440, a=">not why"), dict(x=320, y=610, w=480, a="crossed those")])),
    ("Cold, hard profit", *Pl("n40.jpg", "in")),
    ("The exchange of ideas", *Pl("s16.jpg", "out", "embers")),
    ("none of it was the goal", "notes", dict(title="The goal vs. the result", items=[
        dict(t="the goal: profit", x=330, y=380, s=80, a=0.1), dict(t="the byproduct: everything else", x=330, y=500, s=80, c=RED, a=0.6, d=0.8),
        dict(t="an accident of greed", x=700, y=680, s=88, a="An accident", rot=-3)])),
    # P15
    ("And honestly, that's the more", *Pl("n55.jpg", "inR")),
    ("the cross-pollination", *Pl("n16.jpg", "inUp", "dust")),
    ("happened not because anyone", *Pl("n21.jpg", "L", "embers")),
    ("Proximity did the work", "notes", dict(title="Proximity did the work.", tsize=110, paths=[
        dict(d=circ(880, 600, 110), a=0.5, w=7, len=800), dict(d=circ(1040, 600, 110), a=0.8, c=RED, w=7, len=800)])),
    ("You put a Buddhist", *Pl("n42.jpg", "in", "embers", "v_n42.mp4")),
    ("and ideas leak", "notes", dict(title="…and ideas leak", paths=[
        dict(d=circ(cx, cy, 150), a=0.1 + k * 0.15, c=(INK if k % 2 == 0 else RED), w=6, len=1200, dur=0.5)
        for k, (cx, cy) in enumerate(((850, 470), (1070, 470), (850, 680), (1070, 680)))],
        items=[dict(t="Buddhist", x=520, y=330, s=60, a=0.2), dict(t="Zoroastrian", x=1180, y=330, s=60, a=0.35), dict(t="Muslim", x=560, y=790, s=60, a=0.5),
               dict(t="Confucian", x=1200, y=790, s=60, a=0.65), dict(t="?!", x=920, y=530, s=100, c=RED, a=1.0)])),
    ("Belief is contagious", *Pl("n42.jpg", "inL", "embers")),
    # P16
    ("But proximity cuts both ways", *Pl("n22.jpg", "R", "sand")),
    ("The same chain that carried", "notes", dict(title="Proximity cuts both ways", items=[
        dict(t="paper ✓", x=330, y=380, s=80, a="carried paper"), dict(t="mathematics ✓", x=330, y=490, s=80, a="mathematics"),
        dict(t="…and the thing that would break it", x=330, y=640, s=80, c=RED, a="the thing that")])),
    ("In the 1340s", *Pl("n44.jpg", "inR", None, None, "the 1340s")),
    ("A disease", *Pl("n57.jpg", "in")),
    ("Fleas on the rats", *Pl("n45.jpg", "in")),
    ("the bacterium", "notes", dict(title="Yersinia pestis", items=[
        dict(t="the bacterium behind the Black Death", x=330, y=300, s=58, a=0.4, op=.85),
        dict(t="rat", x=360, y=520, s=110, a=0.5), dict(t="flea", x=820, y=520, s=110, a=0.9), dict(t="people", x=1270, y=520, s=110, c=RED, a=1.3)],
        paths=[dict(d="M560,590 L760,590 M735,570 L760,590 L735,610", a=0.7, len=400, dur=0.3), dict(d="M1030,590 L1230,590 M1205,570 L1230,590 L1205,610", a=1.1, len=400, dur=0.3)])),
    # P17
    ("And think about why", *Pl("n57.jpg", "L")),
    ("The convergence of routes", "converge", dict(title="The same machine", labels=(0.3, False), center="plague", col=RED)),
    ("Every feature that made", "map", dict(title="How it travelled", spread=True, color=RED, nodes=[
        dict(n="Issyk-Kul", x=1500, y=440, a=0.3, date="1338"), dict(n="Caffa", x=1020, y=370, a=1.6, date="1346"),
        dict(n="Constantinople", x=900, y=480, a=2.6, date="1347", dx=-150), dict(n="Alexandria", x=940, y=700, a=3.4, date="1347"),
        dict(n="Sicily", x=650, y=580, a=4.2, date="1347", dx=-90), dict(n="Paris", x=500, y=470, a=5.0, date="1348", dx=-70),
        dict(n="England", x=360, y=380, a=5.8, date="1348", dx=40, dy=-30)],
        items=[dict(t="an idea or an infection?", x=1150, y=780, s=68, a="distinguish", rot=-2)])),
    ("So the same roads", *Pl("n47.jpg", "inUp", None, None, "Europe, 1348")),
    ("a third of everyone", "notes", dict(title="The cost", items=[
        dict(t="≈ 1 in 3 people in Europe", x=330, y=400, s=96, c=RED, a=0.2),
        dict(t="+ tens of millions across Asia", x=330, y=560, s=76, a="tens of millions"), dict(t="and the Middle East", x=380, y=660, s=76, a="Middle East")])),
    # P18
    ("The Silk Road's greatest strength", "notes", dict(items=[
        dict(t="greatest strength", x=300, y=260, s=96, a=0.3), dict(t="=", x=900, y=390, s=120, c=RED, a="and its greatest"),
        dict(t="greatest catastrophe", x=900, y=510, s=96, a="catastrophe"), dict(t="Connection.", x=520, y=700, s=170, c=RED, a="Connection")])),
    # P19
    ("So let's go all the way", *Pl("s1.jpg", "in", "dust", "v_s1.mp4")),
    ("What was the Silk Road really", *Pl("s10.jpg", "inR", "embers")),
    # P20
    ("Not silk", "notes", dict(title="What it really moved", items=[
        dict(t="silk", x=380, y=400, s=120, a=0.2), dict(t="= just the excuse", x=700, y=430, s=84, c=RED, a="just the excuse")],
        strikes=[dict(x=370, y=470, w=230, a="Silk was just")])),
    ("What the Silk Road actually", *Pl("n49.jpg", "in", None, "v_n49.mp4")),
    ("the far-flung corners", *Pl("n15.jpg", "out")),
    ("where something that entered", "relay", dict(title="One network", labels=("one end", "the other"), tokens=[
        dict(t="an idea", a="an idea", dur=5, y=260, dir="e", c=INK), dict(t="a technology", a="a technology", dur=5, y=340, dir="e", c=INK),
        dict(t="a faith", a="a faith", dur=5, y=260, dir="e", c=INK), dict(t="a disease", a="a disease", dur=5, y=340, dir="e")])),
    ("It wasn't a road for goods", *Pl("n49.jpg", "inR")),
    ("information highway", "notes", dict(items=[dict(t="the world’s first", x=420, y=330, s=96, a=0.0),
        dict(t="information highway", x=420, y=470, s=140, c=RED, a=0.4)])),
    ("the best of us", *Pl("n32.jpg", "R")),
    ("the worst of us", *Pl("n44.jpg", "L")),
    # P21
    ("And honestly, that's the part", *Pl("n54.jpg", "in", "dust")),
    ("Because we think of this", *Pl("n14.jpg", "L", "dust")),
    ("But the Silk Road was just", "notes", dict(title="We never stopped building it", svg_static="", paths=[
        dict(d="M250,600 L1700,600", a=0.2, w=7, len=1500, dur=0.8)] + [dict(d=f"M{x},575 L{x},625", a=a, w=7, len=60, dur=0.2) for x, a in ((330, 0.4), (750, "the printing press"), (1170, "the telegraph"), (1590, "the internet"))],
        items=[dict(t="Silk Road", x=240, y=470, s=64, a=0.5), dict(t="c. 100 BCE", x=250, y=650, s=50, c=RED, a=0.7),
               dict(t="printing press", x=620, y=470, s=64, a="the printing press"), dict(t="c. 1450", x=690, y=650, s=50, c=RED, a="the printing press"),
               dict(t="telegraph", x=1070, y=470, s=64, a="the telegraph"), dict(t="1840s", x=1120, y=650, s=50, c=RED, a="the telegraph"),
               dict(t="internet", x=1500, y=470, s=64, a="the internet"), dict(t="1990s", x=1540, y=650, s=50, c=RED, a="the internet")])),
    ("And every single time, we tell", *Pl("n50.jpg", "inL")),
    ("Trade. News.", "notes", dict(title="One specific, valuable thing", items=[
        dict(t="trade", x=380, y=420, s=100, a=0.0), dict(t="news", x=800, y=420, s=100, a="News"), dict(t="cat videos", x=1180, y=420, s=100, c=RED, a="Cat")])),
    ("And every single time, the truth", *Pl("n52.jpg", "in")),
    ("The thing we think we're", *Pl("n51.jpg", "inUp")),
    ("What actually moves is everything", "notes", dict(title="What actually moves:", items=[dict(t="EVERYTHING", x=560, y=470, s=190, c=RED, a="everything")],
        paths=[dict(d="M1000,350 C1500,350 1520,720 1000,720 C470,720 450,350 1000,350", a=0.9, c=INK, w=6, len=2400, dur=0.6)])),
    ("Ideas we didn't mean", *Pl("n23.jpg", "R", "embers")),
    ("Beliefs that reshape", *Pl("n33.jpg", "L", "dust")),
    ("And, eventually, something", *Pl("n45.jpg", "out")),
    ("riding the network", *Pl("n57.jpg", "inUp")),
    # P22
    ("The merchant thought he was", *Pl("s5.jpg", "inR", "dust")),
    ("He was actually carrying", *Pl("n35.jpg", "R", "dust")),
    ("None of them did", *Pl("n13.jpg", "R")),
    ("they stitched humanity", *Pl("n55.jpg", "L")),
    ("with all the wonder", *Pl("n49.jpg", "out")),
    # P23
    ("We've been doing the same", *Pl("n51.jpg", "L")),
    ("We just use faster camels", *Pl("n56.jpg", "R", "dust")),
    # P24
    ("So that's the Silk Road", *Pl("n54.jpg", "R", "dust")),
    ("the first time our species", *Pl("n35.jpg", "inL", "dust")),
    ("that you don't get to choose", "relay", dict(title="Down the line", labels=None, tokens=[
        dict(t="the good", a="The good comes", dur=4.5, y=300, c=INK), dict(t="the bad", a="The bad comes", dur=4.5, y=380)],
        items=[dict(t="the same road does both", x=560, y=860, s=72, c=RED, a="The same road does")])),
    ("So let me hand it to you", "notes", dict(title="Which one reshaped the world most?", tsize=84, svg_static="".join(
        f'<rect x="{x}" y="380" width="330" height="250" rx="18" fill="none" stroke="{INK}" stroke-width="6"/>' for x in (240, 620, 1000, 1380)),
        items=[dict(t="paper", x=310, y=460, s=84, a="the paper,"), dict(t="zero", x=710, y=460, s=84, a="the zero"),
               dict(t="the faiths", x=1030, y=460, s=76, a="the faiths"), dict(t="the plague", x=1405, y=460, s=76, c=RED, a="the plague"),
               dict(t="↓ tell me in the comments", x=560, y=720, s=80, c=RED, a="drop it")])),
    ("If digging under", *Pl("n49.jpg", "inL", None, None, "Subscribe to Joel’s Notebook")),
    ("I'll see you in the next", "end", {}),
]

# ================= build =================
starts, prev = [], -1.0
for k, (anchor, kind, args) in enumerate(SHOTS):
    t = 0.0 if k == 0 else T(anchor, after=prev + 0.3) - 0.12
    starts.append(t); prev = t
ends = starts[1:] + [END]
CHECK = "--check" in sys.argv
for k, (anchor, kind, args) in enumerate(SHOTS):
    t0, t1 = starts[k], ends[k]
    if CHECK: print(f"{k:3d} {t0:7.2f} {t1 - t0:5.2f} {'!!' if t1 - t0 < 1.4 or t1 - t0 > 11 else '  '} {kind:8s} {anchor}")
    if kind == "plate":
        plate(t0, t1, args["img"], args["m"], args["fx"], args["video"], k)
        if args.get("strip"): strip(args["strip"], t0 + 0.4, min(t1, t0 + 4.2) + 0.2)
    elif kind == "demo": demo_page(args, t0, t1)
    elif kind == "notes": notes(t0, t1, **args)
    elif kind == "relay": relay(t0, t1, **args)
    elif kind == "map": mapp(t0, t1, **args)
    elif kind == "converge":
        a = args["labels"]; converge(t0, t1, args["title"], (a[0], a[1]), args["center"], args.get("col", INK))
    elif kind == "end":
        inner = (hw("See you in the next one.", 330, 360, 130, INK, "endt") + hw("Joel’s Notebook", 560, 560, 96, RED, "ends")
                 + f'<div id="endseal" class="abs" style="left:1440px;top:520px;transform:scale(1.6)">{SEAL}</div>')
        els.append(clip_div("endc", t0, END, f'<div class="paper"></div>' + inner, "position:absolute;inset:0;z-index:20"))
        fade_in("#endc", t0, 0.4); write_on("#endt", t0 + 0.2, 1.0); write_on("#ends", t0 + 1.2, 0.6)
        js.append(f'tl.fromTo("#endseal",{{opacity:0,scale:3,rotation:-25}},{{opacity:1,scale:1.6,rotation:-8,duration:0.35,ease:"power3.in"}},{t0 + 1.9:.3f});')

# demo-section strips
strip("c. 800 CE  ·  Central Asia", T("year 800") - 0.1, starts[1] + 0.2)
strip("Silk?", T("says silk") - 0.1, ends[6] + 0.1, left=70, top=820, size=84)
strip("never saw China", T("never saw China") - 0.1, ends[7] + 0.1, left=70, top=820, size=64)
strip("“a roll of expensive cloth”", T("a roll") - 0.2, ends[9] + 0.2, left=70, top=820, size=58)
strip("China  →  Rome", T("China sold") - 0.1, ends[13] + 0.1, left=70, top=70, size=64)
# captions (white, black outline)
caps, cur = [], []
for i, w in enumerate(words):
    cur.append(i)
    txt = " ".join(words[k]["w"] for k in cur)
    if w["w"][-1] in ".?!,;:" or len(cur) >= 5 or len(txt) >= 32:
        caps.append(cur); cur = []
if cur: caps.append(cur)
cap_html = ""
for k, ids in enumerate(caps):
    s = words[ids[0]]["s"]; e = words[caps[k + 1][0]]["s"] if k + 1 < len(caps) else words[ids[-1]]["e"] + 0.5
    e = min(e, words[ids[-1]]["e"] + 0.6)
    cap_html += f'<div id="cp{k}" class="clip capwrap" data-start="{s:.3f}" data-duration="{max(0.2, e - s):.3f}"><div class="cap">{html.escape(" ".join(words[i]["w"] for i in ids))}</div></div>'
    js.append(f'tl.fromTo("#cp{k} .cap",{{opacity:0,y:8}},{{opacity:1,y:0,duration:0.15}},{s:.3f});')
js.append(f'tl.fromTo("#fade",{{opacity:0}},{{opacity:1,duration:0.7,ease:"none"}},{END - 0.75:.3f});')

CSS = f"""
@font-face{{font-family:"Caveat";src:url("assets/fonts/caveat-700.woff2") format("woff2");font-weight:700}}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1920px;height:1080px;overflow:hidden;background:#000}}
#root{{position:relative;width:100%;height:100%;overflow:hidden;font-family:Montserrat,sans-serif}}
.abs{{position:absolute}}
.shot{{position:absolute;inset:0;overflow:hidden}}
.vplate{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}
.plate{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}
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
.cap{{color:#fff;font-weight:800;font-size:54px;line-height:1.15;text-align:center;max-width:1500px;
 text-shadow:3px 3px 0 #000,-3px 3px 0 #000,3px -3px 0 #000,-3px -3px 0 #000,0 3px 0 #000,0 -3px 0 #000,3px 0 0 #000,-3px 0 0 #000,0 6px 16px rgba(0,0,0,.6)}}
#fade{{position:absolute;inset:0;background:#000;opacity:0;z-index:60}}
"""
page_html = f'''<!doctype html>
<html lang="en"><head><meta charset="UTF-8" /><meta name="viewport" content="width=1920, height=1080" />
<script src="assets/js/gsap.min.js"></script><style>{CSS}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{END:.3f}" data-width="1920" data-height="1080">
{"".join(els)}
<div id="vig"></div>
{cap_html}
<div id="fade"></div>
<audio id="vo" class="clip" src="assets/audio.wav" data-start="0" data-duration="{END:.3f}"></audio>
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(js)}
tl.to({{}},{{duration:{END:.3f}}},0);
window.__timelines["main"] = tl;
tl.seek(0);
</script></body></html>'''
(OUT / "index.html").write_text(page_html, encoding="utf-8")
print("END", END, "shots", len(SHOTS), "elements", len(els), "tweens", len(js))
