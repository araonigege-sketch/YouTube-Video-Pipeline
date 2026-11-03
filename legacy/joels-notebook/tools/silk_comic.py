"""Joel's Notebook motion comic: Silk Road opening. Writes <out>/index.html.
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
END = round(T("the end", end=True) + 1.1, 2)
INK = "#2A2733"; RED = "#B3261E"; PAPER = "#F3E9D2"; CREAM = "#F6EBD9"
XF = 0.45  # cross-dissolve length

# shot list: anchor phrase, kind, asset, motion (scale0,scale1,x0,x1,y0,y1)
SHOTS = [
    ("Picture", "plate", dict(video="v_s1.mp4", img="v_s1_last.jpg"), (1.0, 1.08, 0, -40, 0, 0), "dust"),
    ("He's got a camel", "plate", dict(img="s2.jpg"), (1.12, 1.04, 60, -60, 0, 0), "dust"),
    ("and he's spent", "page_map", {}, None, None),
    ("lethal terrain", "plate", dict(img="s4.jpg"), (1.06, 1.16, 0, 0, 0, -20), "sand"),
    ("Now ask yourself", "plate", dict(img="s5.jpg"), (1.02, 1.16, 0, -30, 0, 20), "dust"),
    ("What's on that camel", "plate", dict(img="s6.jpg"), (1.15, 1.05, 0, 0, -20, 20), None),
    ("Almost everyone says", "plate", dict(img="s7.jpg"), (1.0, 1.1, -30, 30, 0, 0), None),
    ("But here's the thing", "plate", dict(img="s8.jpg"), (1.1, 1.0, -70, 70, 0, 0), "dust"),
    ("never met the person", "page_chain", {}, None, None),
    ("And what he was really", "plate", dict(video="v_s10.mp4", img="v_s10_last.jpg"), (1.0, 1.1, 0, 0, 0, -10), "embers"),
    ("So the story we all", "page_list", {}, None, None),
    ("The Silk Road was", "plate", dict(video="v_s12.mp4", img="v_s12_last.jpg"), (1.0, 1.08, 0, -60, 0, 0), "dust"),
    ("Silk going one way", "page_eastwest", {}, None, None),
    ("China sold silk", "plate", dict(img="s15.jpg"), (1.06, 1.0, 0, 0, 0, 0), None),
    ("everybody got rich", "plate", dict(img="s16.jpg"), (1.0, 1.12, 0, 0, 0, -15), "embers"),
]
starts = [0.0] + [T(a) - 0.12 for a, *_ in SHOTS[1:]]
ends = starts[1:] + [END]
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

for i, (anchor, kind, asset, motion, fx) in enumerate(SHOTS):
    t0, t1 = starts[i], ends[i]
    if kind == "plate":
        vid = asset.get("video")
        if vid and (P / "ai" / vid).exists():
            shutil.copy(P / "ai" / vid, OUT / "assets/img" / vid)
            vlen = min(t1 - t0 + XF, 4.6)
            vidid = nid("v")
            els.append(f'<video id="{vidid}" class="clip shot vplate" src="assets/img/{vid}" muted data-start="{t0:.3f}" data-duration="{vlen:.3f}"></video>')
            fade_in(f"#{vidid}", t0); js.append(f'tl.fromTo("#{vidid}",{{scale:1}},{{scale:1.05,duration:{vlen:.3f},ease:"none"}},{t0:.3f});')
            if t0 + vlen < t1 + XF - 0.2:
                sid = nid("p"); shutil.copy(P / "ai" / asset["img"], OUT / "assets/img" / asset["img"])
                ts = t0 + vlen - XF
                els.append(clip_div(sid, ts, t1 + XF, f'<img class="plate" src="assets/img/{asset["img"]}">', "position:absolute;inset:0;overflow:hidden", "shot"))
                fade_in(f"#{sid}", ts); kb(f"#{sid} .plate", ts, t1 + XF, motion)
        else:
            if not (P / "ai" / asset["img"]).exists(): asset = dict(img=asset["img"].replace("v_", "").replace("_last", ""))
            sid = nid("p"); shutil.copy(P / "ai" / asset["img"], OUT / "assets/img" / asset["img"])
            els.append(clip_div(sid, t0, t1 + XF, f'<img class="plate" src="assets/img/{asset["img"]}">', "position:absolute;inset:0;overflow:hidden", "shot"))
            if i: fade_in(f"#{sid}", t0)
            kb(f"#{sid} .plate", t0, t1 + XF, motion)
        if fx:
            fid = nid("fx"); els.append(clip_div(fid, t0, t1 + XF, particles(fx, t0, t1, i), "position:absolute;inset:0;z-index:5"))
            fade_in(f"#{fid}", t0)
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

# labels in the notebook strip style
strip("c. 800 CE  ·  Central Asia", T("year 800") - 0.1, starts[1] + 0.2)
strip("Silk?", T("says silk") - 0.1, ends[6] + 0.1, left=70, top=820, size=84)
strip("never saw China", T("never saw China") - 0.1, ends[7] + 0.1, left=70, top=820, size=64)
strip("“a roll of expensive cloth”", T("a roll") - 0.2, ends[9] + 0.2, left=70, top=820, size=58)
strip("China  →  Rome", T("China sold") - 0.1, ends[13] + 0.1, left=70, top=70, size=64)

# The End? card
te = T("the end") - 0.15
els.append(clip_div("endc", te, END, f'<div class="paper"></div>' + hw("The End", 560, 330, 230, INK, "endt") + hw("?", 1330, 290, 280, RED, "endq")
                    + f'<div class="abs" style="right:70px;top:60px">{SEAL}</div>', "position:absolute;inset:0;z-index:20"))
fade_in("#endc", te, 0.25); write_on("#endt", te + 0.1, 0.55)
js.append(f'tl.fromTo("#endq",{{opacity:0,scale:2,rotation:-20}},{{opacity:1,scale:1,rotation:8,duration:0.35,ease:"power3.in"}},{te + 0.75:.3f});')

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
