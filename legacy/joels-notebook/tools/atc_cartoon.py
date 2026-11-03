"""ATC first minute in the cartoon-puppet style. Writes <out>/index.html and <out>/sfx.json.
Usage: python3 atc_cartoon.py <projdir> <outdir>
"""
import sys, json, html, pathlib, shutil
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from cartoon_kit import *

P = pathlib.Path(sys.argv[1]); OUT = pathlib.Path(sys.argv[2])
(OUT / "assets/js").mkdir(parents=True, exist_ok=True)
shutil.copy(pathlib.Path(__file__).resolve().parent.parent / "node_modules/gsap/dist/gsap.min.js", OUT / "assets/js/gsap.min.js")
for f in ("hyperframes.json", "meta.json"):
    shutil.copy(pathlib.Path(__file__).resolve().parent.parent / "smoketest" / f, OUT / f)
words = json.load(open(P / "words.json")); M = json.load(open(P / "map.json"))
c = Cartoon(words); T = c.T
END = round(T("never quite lets go", end=True) + 0.9, 2)
SK = dict(you=dict(skin="#B9784E", hair="#2A1C17", top=MUSTARD, pants=NAVY))

def chip(text, bg=CORAL, fg=CREAM, size=40):
    return (f'<div style="display:inline-block;background:{bg};color:{fg};font-family:\'Archivo Black\';font-size:{size}px;'
            f'padding:10px 26px;border:6px solid {INK};border-radius:18px;box-shadow:6px 6px 0 {INK}">{html.escape(text)}</div>')

def box(id_, x, y, inner, extra=""):
    return f'<div id="{id_}" class="abs" style="left:{x}px;top:{y}px;{extra}">{inner}</div>'

B = [0, T("You sit") - 0.1, T("You speak") - 0.12, T("You hold") - 0.1, T("And they pay") - 0.1, T("A typical") - 0.1,
     T("The ones at") - 0.1, T("You don't even") - 0.1, T("Just you") - 0.04, T("Small problem") - 0.1, T("Not because") - 0.1,
     T("The job you're picturing") - 0.1, T("What you're not") - 0.1, T("By the end") - 0.1, T("And you'll understand what") - 0.1,
     T("into their cars") - 0.12, END]
scenes = []

def scene(n, inner, bg=""):
    t0, t1 = B[n - 1], B[n]
    scenes.append(f'<div id="s{n}" class="clip scene" data-start="{t0:.3f}" data-duration="{t1 - t0:.3f}" data-track-index="2">{bg}{inner}</div>')
    if n > 1: c.sfx.append((t0, "whoosh"))
    return t0, t1

# 1. So you think you could be an ATC. It's an appealing thought.
t0, t1 = B[0], B[1]
inner = (c.char("you1", 330, 250, pose="chin", **SK["you"])
         + "".join(box(f"s1d{i}", x, y, f'<div style="width:{s}px;height:{s}px;border-radius:50%;background:{CREAM};border:6px solid {INK}"></div>')
                   for i, (x, y, s) in enumerate(((660, 230, 34), (712, 168, 46), (770, 104, 60))))
         + box("s1b", 800, 40, thought(700, 500) + box("s1tw", 250, 66, tower(170)) + box("s1pl", 410, 110, plane(170))))
scene(1, inner)
c.look("you1", 0.05, 8, -8)
for i, t in enumerate((0.15, 0.3, 0.45)): c.pop(f"#s1d{i}", t, 0.25, sfx=None)
c.pop("#s1b", 0.55); c.pop("#s1tw", 0.9, sfx=None)
c.tw("#s1pl", T("air traffic"), "x:-120,opacity:0", "x:0,opacity:1", 0.6, "power2.out", first=True)
c.face("you1", T("air traffic"), mouth="grin", brows="u"); c.blink("you1", 2.0)
c.face("you1", T("appealing"), mouth="smile", brows="n")

# 2. dim room, glowing scope
t0, t1 = B[1], B[2]
inner = (f'<div id="s2dim" class="abs" style="inset:0;background:#0B2329"></div>'
         f'<div class="abs" style="left:880px;top:120px;width:700px;height:640px;background:radial-gradient(circle, rgba(126,224,181,.28), rgba(126,224,181,0) 65%)"></div>'
         + c.char("you2", 360, 300, pose="hold", **SK["you"])
         + box("s2sc", 1010, 180, scope(440)) + box("s2sw", 1010, 180, sweep(440))
         + box("s2b0", 1110, 300, blip("DAL412")) + box("s2b1", 1260, 420, blip("UAL88")) + box("s2b2", 1080, 470, blip("AAL7"))
         + box("s2desk", 330, 640, desk(1260, 230)))
scene(2, inner)
c.tw("#s2dim", t0, "opacity:0", "opacity:.82", 0.5, "power1.out", first=True)
c.tw("#s2sw", t0, "rotation:0,transformOrigin:'50% 50%'", "rotation:600", t1 - t0, "none", first=True)
for i, d in enumerate((0.5, 1.0, 1.5)): c.pop(f"#s2b{i}", t0 + d, 0.3, sfx="blip")
c.look("you2", t0 + 0.2, 10, 2); c.face("you2", t0 + 0.2, mouth="flat"); c.blink("you2", t0 + 1.8)

# 3. calm, clipped, unbothered voice
t0, t1 = B[2], B[3]
inner = (c.char("you3", 250, 640, scale=1.55, pose="idle", headset=True, **SK["you"])
         + box("s3bub", 930, 110, bubble(860, 330, "left")
               + f'<div class="abs" style="left:50px;top:40px;width:760px;font-family:\'JetBrains Mono\';font-weight:700;font-size:44px;line-height:1.3;color:{INK}">DELTA 412, DESCEND AND MAINTAIN THREE THOUSAND.</div>')
         + box("s3c0", 960, 510, chip("CALM", NAVY)) + box("s3c1", 1210, 510, chip("CLIPPED", NAVY)) + box("s3c2", 1500, 510, chip("UNBOTHERED", CORAL)))
scene(3, inner)
c.face("you3", t0, mouth="smirk", half=1); c.pop("#s3bub", t0 + 0.15)
for i, w in enumerate(("calm", "clipped", "unbothered")): c.pop(f"#s3c{i}", T(w, after=t0), 0.3)
for k in range(4):
    c.face("you3", t0 + 0.3 + k * 0.28, mouth="o"); c.face("you3", t0 + 0.44 + k * 0.28, mouth="smirk")

# 4. hundreds of lives in your hands, pulse never moves
t0, t1 = B[3], B[4]
inner = (c.char("you4", 420, 250, pose="hold", **SK["you"])
         + box("s4pl", 440, 520, plane(260)) + box("s4c", 760, 470, chip("300 LIVES", CORAL, size=34))
         + box("s4hm", 1130, 270, heart_monitor(560)))
scene(4, inner)
c.face("you4", t0, mouth="smile", half=1); c.look("you4", t0, 0, -10)
c.pop("#s4pl", t0 + 0.2, 0.4); c.pop("#s4c", T("hundreds", after=t0), 0.3)
c.tw("#s4pl", t0 + 0.6, "y:0", "y:-22", 0.9, "sine.inOut"); c.tw("#s4pl", t0 + 1.5, "y:-22", "y:0", 0.9, "sine.inOut")
c.tw("#s4pl", t0 + 2.4, "y:0", "y:-22", 0.9, "sine.inOut")
c.pop("#s4hm", T("your pulse", after=t0) - 0.2, 0.35)
c.tw("#s4hm .ecg", T("your pulse", after=t0), "strokeDashoffset:900", "strokeDashoffset:0", 1.3, "none", first=True)
c.tw("#s4hm .ecg", T("your pulse", after=t0) + 1.35, "strokeDashoffset:900", "strokeDashoffset:0", 1.3, "none")

# 5. And they pay you for it. Really pay you.
t0, t1 = B[4], B[5]
xs = [140, 420, 700, 980, 1260, 1540, 1720, 280, 560, 1100, 1400, 840, 1640, 60]
inner = c.char("you5", 810, 250, pose="idle", **SK["you"]) + "".join(box(f"s5m{i}", x, -260, bill(190)) for i, x in enumerate(xs))
scene(5, inner)
c.face("you5", t0, mouth="smile", brows="n"); c.pose("you5", "cheer", T("pay you", after=t0), 0.35)
c.face("you5", T("pay you", after=t0), mouth="grin", brows="u")
for i, x in enumerate(xs):
    st = t0 + 0.2 + (i % 7) * 0.22 + (0.0 if i < 7 else 1.35)
    c.tw(f"#s5m{i}", st, f"y:0,rotation:{(i * 37) % 60 - 30}", f"y:1400,rotation:{(i * 53) % 180 - 90}", 1.9, "none", first=True)
c.sfx += [(T("pay you", after=t0), "cash"), (T("Really", after=t0), "cash")]

# 6. A typical ATC in America earns $144,000
t0, t1 = B[5], B[6]
mapsvg = svg(1060, 655, f'<path d="{M["nation"]}" fill="{CREAM}" stroke="{INK}" stroke-width="6"/><path d="{M["borders"]}" fill="none" stroke="{INK}" stroke-width="2" opacity=".35"/>', f'0 0 {M["w"]} {M["h"]}')
inner = (c.char("you6", 120, 250, pose="idle", headset=True, **SK["you"])
         + box("s6map", 700, 150, mapsvg)
         + box("s6st", 930, 330, f'<div style="background:{INK};border-radius:28px;padding:26px 54px 30px;text-align:center;box-shadow:10px 10px 0 rgba(0,0,0,.25)">'
               f'<div style="font-family:\'Archivo Black\';font-size:128px;line-height:1;color:{MUSTARD}">$144,000</div>'
               f'<div style="font-family:\'Archivo Black\';font-size:34px;color:{CREAM};margin-top:10px">TYPICAL CONTROLLER · PER YEAR</div></div>'))
scene(6, inner)
c.pop("#s6map", T("America", after=t0) - 0.15, 0.45); c.pose("you6", "point_r", T("America", after=t0) - 0.1)
c.pop("#s6st", T("$144,000", after=t0), 0.4, sfx="ding"); c.face("you6", T("$144,000", after=t0), mouth="grin", brows="u")

# 7. bars: 144k, 185k, 250k+
t0, t1 = B[6], B[7]
def bar(id_, x, h, col, label):
    return (box(id_, x, 860 - h, f'<div style="width:220px;height:{h}px;background:{col};border:8px solid {INK};border-bottom:none;border-radius:16px 16px 0 0"></div>')
            + box(id_ + "l", x - 20, 860 - h - 120, f'<div class="label" style="width:260px;text-align:center;font-size:72px">{label}</div>'))
inner = (c.char("you7", 230, 250, pose="point_r", **SK["you"])
         + bar("s7a", 760, 300, CREAM, "$144K") + bar("s7b", 1060, 385, MUSTARD, "$185K")
         + box("s7c", 1360, 860 - 385, f'<div style="width:220px;height:385px;background:{MUSTARD};border:8px solid {INK};border-bottom:none"></div>')
         + box("s7d", 1360, 860 - 520, f'<div style="width:220px;height:143px;background:{CORAL};border:8px solid {INK};border-radius:16px 16px 0 0;display:flex;align-items:center;justify-content:center;font-family:\'Archivo Black\';font-size:30px;color:{CREAM}">OVERTIME</div>')
         + box("s7dl", 1320, 860 - 520 - 120, '<div class="label" style="width:300px;text-align:center;font-size:72px">$250K+</div>')
         + "".join(box(f"s7f{i}", x, 884, f'<div class="label" style="width:280px;text-align:center;font-size:30px">{t}</div>')
                   for i, (x, t) in enumerate(((730, "TYPICAL"), (1030, "BUSY CENTERS"), (1330, "WITH OVERTIME")))))
scene(7, inner)
c.face("you7", t0, mouth="smile")
def grow(id_, t):
    c.tw(f"#{id_}", t, "scaleY:0,transformOrigin:'50% 100%'", "scaleY:1", 0.5, "back.out(1.4)", first=True); c.sfx.append((t, "pop"))
grow("s7a", t0 + 0.15); c.pop("#s7al", t0 + 0.5, 0.3, sfx=None); c.pop("#s7f0", t0 + 0.5, 0.3, sfx=None)
grow("s7b", T("$185,000", after=t0)); c.pop("#s7bl", T("$185,000", after=t0) + 0.3, 0.3, sfx=None); c.pop("#s7f1", T("$185,000", after=t0) + 0.3, 0.3, sfx=None)
grow("s7c", T("with enough", after=t0)); c.pop("#s7f2", T("with enough", after=t0) + 0.3, 0.3, sfx=None)
grow("s7d", T("past", after=t0)); c.pop("#s7dl", T("past", after=t0) + 0.3, 0.3, sfx="ding")
c.face("you7", T("past", after=t0), mouth="o", brows="u"); c.pose("you7", "cheer", T("past", after=t0) + 0.1)

# 8. no college degree
t0, t1 = B[7], B[8]
inner = (box("s8cap", 560, 250, cap(460)) + box("s8x", 570, 180, xmark(440))
         + c.char("you8", 1260, 250, pose="idle", **SK["you"]))
scene(8, inner)
c.pop("#s8cap", t0 + 0.1, 0.35)
c.tw("#s8x .x1", T("college", after=t0), "strokeDashoffset:490", "strokeDashoffset:0", 0.18, "power2.out", first=True)
c.tw("#s8x .x2", T("college", after=t0) + 0.18, "strokeDashoffset:490", "strokeDashoffset:0", 0.18, "power2.out", first=True)
c.sfx.append((T("college", after=t0), "stamp"))
c.pose("you8", "shrug", T("strictly", after=t0)); c.face("you8", T("strictly", after=t0), mouth="smirk", brows="u")

# 9. Just you, a headset, and nerves of steel.
t0, t1 = B[8], B[9]
plus = lambda id_, x: box(id_, x, 440, '<div class="label" style="font-size:120px">+</div>')
inner = (c.char("you9", 180, 250, scale=0.9, pose="idle", **SK["you"]) + plus("s9p0", 580, ) + box("s9hs", 700, 360, headset_icon(280))
         + plus("s9p1", 1030) + box("s9st", 1160, 380, steel(400)))
scene(9, inner)
c.pop("#you9", T("you", after=t0 + 0.05), 0.35, frm="scale:0.5,opacity:0", to="scale:0.9,opacity:1")
c.pop("#s9p0", T("a headset", after=t0) - 0.1, 0.25, sfx=None); c.pop("#s9hs", T("a headset", after=t0), 0.35)
c.pop("#s9p1", T("nerves", after=t0) - 0.25, 0.25, sfx=None); c.pop("#s9st", T("nerves", after=t0), 0.4, sfx="stamp")
c.pose("you9", "flex", T("nerves", after=t0)); c.face("you9", T("nerves", after=t0), mouth="grin", brows="a")

# 10. Small problem. You wouldn't last a week.
t0, t1 = B[9], B[10]
inner = (f'<div id="s10fl" class="abs" style="inset:0;background:{CORAL};opacity:0"></div>'
         + c.char("you10", 180, 250, pose="idle", **SK["you"]) + box("s10cal", 860, 300, calendar(w=920)))
scene(10, inner)
c.tw("#s10fl", t0 + 0.05, "opacity:0", "opacity:.75", 0.08, "none", first=True); c.tw("#s10fl", t0 + 0.13, "opacity:.75", "opacity:0", 0.3, "power1.out")
c.tw("#s10", t0 + 0.05, "x:0", "x:-18", 0.05, "none", first=True); c.tw("#s10", t0 + 0.1, "x:-18", "x:14", 0.06, "none"); c.tw("#s10", t0 + 0.16, "x:14", "x:0", 0.08, "none")
c.sfx.append((t0 + 0.05, "stamp"))
c.face("you10", t0 + 0.1, mouth="o", brows="u"); c.pop("#s10cal", t0 + 0.6, 0.35)
tw0 = T("last a week", after=t0)
for i in range(5):
    c.set(f"#s10cal .cx{i}", tw0 + i * 0.2, "opacity:1"); c.sfx.append((tw0 + i * 0.2, "tick"))
c.pose("you10", "head", tw0 + 0.2); c.face("you10", tw0 + 0.2, mouth="wavy", brows="w", sweat=1)

# 11. Not because you're weak. Because almost nobody can.
t0, t1 = B[10], B[11]
crowd_cols = [CORAL, MINT, "#8E7CC3", "#E58FB0", NAVY, "#5FA8D3", MUSTARD, CORAL, MINT, "#8E7CC3"]
skins = ["#F1C7A3", "#7A4B2E", "#D9A07A", "#B9784E", "#F1C7A3", "#7A4B2E", "#B9784E", "#D9A07A", "#F1C7A3", "#7A4B2E"]
crowd = "".join(c.char(f"k{i}", 40 + i * 182, 250, scale=0.5, pose="idle", skin=skins[i], top=crowd_cols[i],
                       style=("long" if i % 3 == 1 else "buzz" if i % 3 == 2 else "short"), hair=["#2A1C17", "#5B3A1E", "#111"][i % 3]) for i in range(10))
inner = c.char("you11", 810, 250, pose="idle", **SK["you"]) + f'<div id="s11crowd" class="abs" style="inset:0;opacity:0">{crowd}</div>'
scene(11, inner)
c.pose("you11", "flex", t0 + 0.15); c.face("you11", t0 + 0.15, mouth="grin", brows="a")
tb = T("Because almost", after=t0)
c.tw("#you11", tb - 0.05, "opacity:1", "opacity:0", 0.2, "power1.in", first=True)
c.tw("#s11crowd", tb, "opacity:0", "opacity:1", 0.2, "power1.out", first=True)
for i in range(10):
    c.pop(f"#k{i}", tb + i * 0.05, 0.3, sfx=None, frm="scale:0,opacity:0", to="scale:0.5,opacity:1")
tn = T("nobody", after=t0)
for j, i in enumerate([0, 9, 2, 7, 4, 1, 8, 3, 5]):
    c.face(f"k{i}", tn, mouth="wavy", brows="w")
    c.tw(f"#k{i}", tn - 0.05 + j * 0.045, "opacity:1,y:0", "opacity:0.18,y:40", 0.25, "power2.in")
c.face("k6", tn + 0.3, mouth="grin", brows="u")
c.tw("#k6", tn + 0.3, "scale:0.5", "scale:0.62", 0.3, "back.out(2)")

# 12. The job you're picturing... is real.
t0, t1 = B[11], B[12]
panel = lambda id_, x, inner, lab: box(id_, x, 170, f'<div style="width:760px;height:560px;background:{CREAM};border:8px solid {INK};border-radius:28px;position:relative;box-shadow:12px 12px 0 rgba(0,0,0,.25)">{inner}'
                                       f'<div style="position:absolute;left:0;right:0;bottom:30px;text-align:center;font-family:\'Archivo Black\';font-size:44px;color:{INK}">{lab}</div></div>')
inner = (panel("s12l", 150, box("s12hs", 110, 70, headset_icon(240)) + box("s12rg", 380, 80, chip("ROGER.", NAVY, size=44)), "THE CALM VOICE")
         + panel("s12r", 1010, box("s12pc", 40, 70, paycheck(680)), "SIX-FIGURE PAYCHECK")
         + box("s12st", 700, 340, stamp("REAL", "#2FA86B", 520)))
scene(12, inner)
c.pop("#s12l", T("the calm voice", after=t0), 0.4); c.pop("#s12r", T("six-figure", after=t0), 0.4)
c.pop("#s12st", T("is real", after=t0) + 0.1, 0.25, sfx="stamp", frm="scale:2.2,opacity:0,rotation:-25", to="scale:1,opacity:1,rotation:-12", ease="power3.in")

# 13. What you're not picturing is the thing underneath it.
t0, t1 = B[12], B[13]
cam = (f'<div id="s13cam" class="abs" style="left:0;top:0;width:1920px;height:1500px">'
       f'<div class="abs" style="left:0;top:470px;width:1920px;height:1030px;background:linear-gradient(#2C6FA3,#16385C);border-top:8px solid {INK}"></div>'
       + box("s13ice", 210, 170, iceberg(1500))
       + c.char("you13", 840, -340, scale=0.32, pose="idle", headset=True, **SK["you"])
       + box("s13t", 1060, 230, chip("WHAT YOU PICTURE", MUSTARD, INK, 34))
       + box("s13q", 880, 660, '<div class="label" style="font-size:220px">?</div>')
       + box("s13u", 700, 940, chip("WHAT'S UNDERNEATH", CORAL, CREAM, 44)) + '</div>')
inner = cam
scene(13, inner)
c.pop("#s13t", t0 + 0.3, 0.3)
c.tw("#s13cam", T("underneath", after=t0) - 0.9, "y:0", "y:-380", 1.4, "power2.inOut", first=True)
c.pop("#s13q", T("underneath", after=t0) - 0.1, 0.35); c.pop("#s13u", T("underneath", after=t0) + 0.2, 0.35, sfx=None)

# 14. salary isn't a reward. It's a warning label.
t0, t1 = B[13], B[14]
inner = (c.char("you14", 90, 250, pose="idle", **SK["you"])
         + box("s14pc", 560, 330, paycheck(900))
         + box("s14rw", 800, 170, chip("REWARD", MUSTARD, INK, 60)) + box("s14strike", 790, 214, f'<div style="width:360px;height:16px;background:{CORAL};border:5px solid {INK};border-radius:8px"></div>')
         + box("s14hz", 1130, 230, hazard_tag(500)))
scene(14, inner)
c.pop("#s14pc", t0 + 0.15, 0.4); c.face("you14", t0, mouth="smile")
c.pop("#s14rw", T("reward", after=t0) - 0.5, 0.3)
c.tw("#s14strike", T("reward", after=t0) + 0.15, "scaleX:0,transformOrigin:'0% 50%'", "scaleX:1", 0.25, "power2.out", first=True)
th = T("warning", after=t0)
c.pop("#s14hz", th - 0.15, 0.3, sfx="stamp", frm="scale:1.8,opacity:0,rotation:-40", to="scale:1,opacity:1,rotation:-9", ease="power3.in")
c.face("you14", th, mouth="wavy", brows="w", sweat=1); c.pose("you14", "head", th + 0.1)

# 15. what this job quietly does... follows them out of the tower
t0, t1 = B[14], B[15]
inner = (box("s15tw", 120, 860 - 594, tower(330))
         + c.char("you15", 420, 250, pose="slump", **SK["you"])
         + box("s15cl", 440, 30, cloud_storm(360)))
scene(15, inner)
c.face("you15", t0, mouth="frown", brows="w", bags=1)
tf = T("survive it", after=t0)
c.pop("#s15cl", T("quietly", after=t0), 0.4, sfx="thunder")
for k in range(6):
    c.tw("#s15cl .rain", T("quietly", after=t0) + k * 0.5, "y:0,opacity:1", "y:26,opacity:0", 0.5, "none", first=(k == 0))
c.walk("you15", tf, t1 - 0.1)
c.tw("#you15", tf, "x:0", f"x:{min(820, int((t1 - tf) * 190))}", t1 - tf, "none", first=True)
c.tw("#s15cl", tf, "x:0", f"x:{min(820, int((t1 - tf) * 190))}", t1 - tf, "none")

# 16. into their cars, into their marriages, and never quite lets go.
t0, t1 = B[15], B[16]
tm = T("into their marriages", after=t0) - 0.1; tg = T("never quite", after=t0)
partA = (f'<div id="s16a" class="abs" style="inset:0">'
         + "".join(box(f"s16r{i}", 200 + i * 420, 940, f'<div style="width:200px;height:16px;background:{CREAM};border-radius:8px;opacity:.6"></div>') for i in range(5))
         + box("s16car", 560, 545, car(760))
         + '<div class="abs" style="inset:0;clip-path:polygon(862px 619px,966px 619px,966px 681px,800px 681px)">'
         + c.char("you16a", 730, 234, scale=0.4, pose="idle", legs=False, **SK["you"]) + '</div>'
         + box("s16cla", 740, 250, cloud_storm(320)) + '</div>')
partB = (f'<div id="s16b" class="abs" style="inset:0;opacity:0">'
         + c.char("you16b", 470, 300, pose="slump", **SK["you"])
         + c.char("sp16", 1150, 300, pose="hold", skin="#F1C7A3", hair="#5B3A1E", top="#8E7CC3", pants=NAVY, style="long")
         + box("s16tab", 510, 600, table(900)) + box("s16clb", 450, -10, cloud_storm(400)) + '</div>')
scene(16, f'<div id="s16cam" class="abs" style="inset:0">{partA}{partB}</div>')
c.face("you16a", t0, mouth="frown", brows="w", bags=1); c.look("you16a", t0, 8)
for i in range(5):
    c.tw(f"#s16r{i}", t0, "x:0", "x:-900", tm - t0 + 0.2, "none", first=True)
c.tw("#s16car", t0, "y:0", "y:-6", 0.25, "sine.inOut", first=True); c.tw("#s16car", t0 + 0.25, "y:-6", "y:0", 0.25, "sine.inOut")
c.set("#s16a", tm, "opacity:0"); c.set("#s16b", tm, "opacity:1"); c.sfx.append((tm, "whoosh"))
c.face("you16b", tm, mouth="flat", brows="w", bags=1); c.look("you16b", tm, 0, 10)
c.face("sp16", tm, mouth="wavy", brows="w"); c.look("sp16", tm, -10)
for k in range(int((t1 - tm) / 0.5)):
    c.tw("#s16clb .rain", tm + k * 0.5, "y:0,opacity:1", "y:26,opacity:0", 0.5, "none", first=(k == 0))
c.tw("#s16clb", tg, "scale:1,transformOrigin:'50% 50%'", "scale:1.3", 1.2, "power2.inOut", first=True)
c.tw("#s16cam", tg, "scale:1,transformOrigin:'40% 40%'", "scale:1.1", t1 - tg, "sine.inOut", first=True)
c.sfx.append((tg, "thunder"))

# captions
tl_caps = [x for x in json.load(open(P / "timeline.json"))["captions"] if x["start"] < T("never quite lets go", end=True)]
caps = "".join(f'<div id="c{k}" class="clip capwrap" data-start="{x["start"]:.3f}" data-duration="{max(0.2, min(x["end"], END) - x["start"]):.3f}" data-track-index="5"><div class="cap">{html.escape(x["text"])}</div></div>' for k, x in enumerate(tl_caps))
for k, x in enumerate(tl_caps):
    c.js.append(f'tl.fromTo("#c{k} .cap",{{scale:0.88,opacity:0}},{{scale:1,opacity:1,duration:0.12,ease:"back.out(2)"}},{x["start"]:.3f});')
c.js.append(f'tl.fromTo("#fade",{{opacity:0}},{{opacity:1,duration:0.8,ease:"none"}},{END - 0.85:.3f});')

page = f'''<!doctype html>
<html lang="en"><head><meta charset="UTF-8" /><meta name="viewport" content="width=1920, height=1080" />
<script src="assets/js/gsap.min.js"></script><style>{CSS}
#fade{{position:absolute;inset:0;background:#000;opacity:0;z-index:60}}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{END:.3f}" data-width="1920" data-height="1080">
<div id="stage" class="clip" data-start="0" data-duration="{END:.3f}" data-track-index="0"><div class="dots"></div><div class="floor"></div></div>
{"".join(scenes)}
{caps}
<div id="fade"></div>
<audio id="vo" class="clip" src="assets/audio.wav" data-start="0" data-duration="{END:.3f}" data-track-index="9"></audio>
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(c.js)}
tl.to({{}},{{duration:{END:.3f}}},0);
window.__timelines["main"] = tl;
tl.seek(0);
</script></body></html>'''
(OUT / "index.html").write_text(page, encoding="utf-8")
json.dump({"end": END, "sfx": sorted(c.sfx)}, open(OUT / "sfx.json", "w"))
print("END", END, "scenes", len(scenes), "tweens", len(c.js), "sfx", len(c.sfx))
