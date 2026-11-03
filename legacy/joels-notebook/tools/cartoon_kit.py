"""Cartoon puppet kit for HyperFrames: rigged characters (HTML divs + SVG faces), props, tween helpers.
Characters are front-facing puppets with big heads, flat colour, bold ink outlines; arms bend at the elbow.
All motion is emitted as GSAP timeline code (fromTo with explicit start values, so any seek is deterministic).
"""
import json, re

INK = "#1B1A24"; CREAM = "#F6EBD9"; CORAL = "#E9674B"; MUSTARD = "#F3B23C"; MINT = "#7EE0B5"
WALL = "#1F5864"; WALL_D = "#163F48"; FLOOR = "#12333B"; NAVY = "#2D3A63"; STEEL = "#9FB1BD"

POSES = {
    "idle":   dict(aL=8, fL=0, aR=-8, fR=0, lL=2, lR=-2),
    "point_r": dict(aL=8, fL=0, aR=-95, fR=-5, lL=2, lR=-2),
    "point_l": dict(aL=95, fL=5, aR=-8, fR=0, lL=2, lR=-2),
    "cheer":  dict(aL=150, fL=15, aR=-150, fR=-15, lL=4, lR=-4),
    "shrug":  dict(aL=30, fL=108, aR=-30, fR=-108, lL=2, lR=-2),
    "hold":   dict(aL=-12, fL=-95, aR=12, fR=95, lL=2, lR=-2),
    "head":   dict(aL=158, fL=55, aR=-158, fR=-55, lL=4, lR=-4),
    "flex":   dict(aL=95, fL=88, aR=-95, fR=-88, lL=6, lR=-6),
    "chin":   dict(aL=8, fL=0, aR=42, fR=126, lL=2, lR=-2),
    "slump":  dict(aL=4, fL=0, aR=-4, fR=0, lL=0, lR=0),
}
MOUTHS = ["smile", "grin", "flat", "wavy", "o", "smirk", "frown"]
BROWS = ["n", "w", "a", "u"]


def head_svg(skin, hair, style="short", headset=False):
    p = []
    p.append(f'<ellipse cx="22" cy="140" rx="17" ry="24" fill="{skin}" stroke="{INK}" stroke-width="6"/>')
    p.append(f'<ellipse cx="238" cy="140" rx="17" ry="24" fill="{skin}" stroke="{INK}" stroke-width="6"/>')
    if style == "long":
        p.append(f'<path d="M14,150 C6,60 70,14 130,14 C192,14 256,60 246,150 L250,232 C238,240 222,238 216,226 L40,226 C34,238 18,240 10,232 Z" fill="{hair}" stroke="{INK}" stroke-width="6"/>')
    p.append(f'<ellipse cx="130" cy="132" rx="112" ry="102" fill="{skin}" stroke="{INK}" stroke-width="6"/>')
    if style == "short":
        p.append(f'<path d="M20,122 C14,52 70,18 130,18 C192,18 248,52 240,122 C228,98 210,86 184,80 C160,94 118,98 92,86 C68,86 40,98 20,122 Z" fill="{hair}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>')
    elif style == "long":
        p.append(f'<path d="M20,128 C16,50 76,20 130,20 C190,20 246,52 240,128 C214,84 168,74 130,78 C96,76 52,88 20,128 Z" fill="{hair}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>')
    elif style == "buzz":
        p.append(f'<path d="M30,100 C40,44 90,28 130,28 C176,28 222,46 230,100 C200,80 160,74 130,74 C100,74 60,80 30,100 Z" fill="{hair}" stroke="{INK}" stroke-width="5"/>')
    for cx in (92, 168):
        p.append(f'<circle cx="{cx}" cy="140" r="24" fill="#fff" stroke="{INK}" stroke-width="5"/>')
    p.append(f'<circle class="pup" cx="92" cy="144" r="9" fill="{INK}"/><circle class="pup pup2" cx="168" cy="144" r="9" fill="{INK}"/>')
    p.append(f'<g class="half" opacity="0"><path d="M68,141 A24,24 0 0 1 116,141 Z" fill="{skin}" stroke="{INK}" stroke-width="5"/><path d="M144,141 A24,24 0 0 1 192,141 Z" fill="{skin}" stroke="{INK}" stroke-width="5"/></g>')
    p.append(f'<g class="lid" opacity="0"><circle cx="92" cy="140" r="25" fill="{skin}"/><circle cx="168" cy="140" r="25" fill="{skin}"/><path d="M70,142 Q92,152 114,142 M146,142 Q168,152 190,142" stroke="{INK}" stroke-width="5" fill="none" stroke-linecap="round"/></g>')
    p.append('<g class="bags" opacity="0" stroke="#6E4E86" stroke-width="5" fill="none" stroke-linecap="round"><path d="M72,172 Q92,184 112,172"/><path d="M148,172 Q168,184 188,172"/></g>')
    brows = {"n": "M70,104 Q92,96 114,104 M146,104 Q168,96 190,104",
             "w": "M70,110 L114,96 M146,96 L190,110",
             "a": "M70,96 L114,112 M146,112 L190,96",
             "u": "M70,92 Q92,80 114,92 M146,92 Q168,80 190,92"}
    for k, d in brows.items():
        p.append(f'<path class="br br-{k}" opacity="{1 if k == "n" else 0}" d="{d}" stroke="{INK}" stroke-width="8" fill="none" stroke-linecap="round"/>')
    p.append(f'<path d="M126,158 Q138,168 128,176" stroke="{INK}" stroke-width="4" fill="none" stroke-linecap="round"/>')
    mouths = {"smile": f'<path d="M104,192 Q130,212 156,192" stroke="{INK}" stroke-width="6" fill="none" stroke-linecap="round"/>',
              "grin": f'<path d="M100,188 Q130,228 160,188 Z" fill="#7A1F2B" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/><path d="M106,192 L154,192" stroke="#fff" stroke-width="7"/>',
              "flat": f'<path d="M110,200 L150,200" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>',
              "wavy": f'<path d="M104,202 q13,-9 26,0 q13,9 26,0" stroke="{INK}" stroke-width="6" fill="none" stroke-linecap="round"/>',
              "o": f'<ellipse cx="130" cy="200" rx="13" ry="17" fill="#7A1F2B" stroke="{INK}" stroke-width="5"/>',
              "smirk": f'<path d="M110,200 Q140,206 158,188" stroke="{INK}" stroke-width="6" fill="none" stroke-linecap="round"/>',
              "frown": f'<path d="M106,208 Q130,190 154,208" stroke="{INK}" stroke-width="6" fill="none" stroke-linecap="round"/>'}
    for k, svg in mouths.items():
        p.append(f'<g class="m m-{k}" opacity="{1 if k == "smile" else 0}">{svg}</g>')
    p.append(f'<path class="sweat" opacity="0" d="M226,64 C212,90 212,104 226,106 C240,104 240,90 226,64 Z" fill="#8FD3FF" stroke="{INK}" stroke-width="4"/>')
    if headset:
        p.append(f'<path d="M20,124 C16,-4 244,-4 240,124" stroke="#2B2A33" stroke-width="16" fill="none" stroke-linecap="round"/>')
        p.append(f'<rect x="0" y="108" width="34" height="62" rx="12" fill="#2B2A33" stroke="{INK}" stroke-width="5"/><rect x="226" y="108" width="34" height="62" rx="12" fill="#2B2A33" stroke="{INK}" stroke-width="5"/>')
        p.append(f'<path d="M240,160 Q236,214 168,212" stroke="{INK}" stroke-width="7" fill="none" stroke-linecap="round"/><circle cx="166" cy="212" r="10" fill="#2B2A33" stroke="{INK}" stroke-width="4"/>')
    return f'<svg class="face" viewBox="-6 -6 272 252" width="326" height="302">{"".join(p)}</svg>'


class Cartoon:
    def __init__(self, words):
        self.words = words
        self.norm = [self._n(w["w"]) for w in words]
        self.js, self.sfx, self.state = [], [], {}

    @staticmethod
    def _n(t):
        return re.sub(r"[^a-z0-9$%]", "", t.lower().replace("’", "'"))

    def T(self, phrase, after=0.0, end=False):
        """Start (or end) time of the first occurrence of phrase at/after `after`."""
        a = [self._n(x) for x in phrase.split()]
        for i in range(len(self.norm)):
            if self.words[i]["s"] + 1e-6 < after: continue
            if all(i + k < len(self.norm) and self.norm[i + k].startswith(a[k]) for k in range(len(a))):
                return self.words[i + len(a) - 1]["e"] if end else self.words[i]["s"]
        raise KeyError(phrase)

    # ---------- characters ----------
    def char(self, cid, x, y, scale=1.0, skin="#B9784E", hair="#2A1C17", top=MUSTARD, pants=NAVY,
             style="short", headset=False, pose="idle", legs=True):
        self.state[cid] = dict(POSES[pose]); self.state[cid]["look"] = 0
        p = POSES[pose]
        leg = lambda side, lx: (f'<div class="leg leg{side}" style="left:{lx}px;background:{pants}"><div class="shoe"></div></div>')
        arm = lambda side, ax: (f'<div class="arm arm{side}" style="left:{ax}px;background:{top}"><div class="fore" style="background:{top}">'
                                 f'<div class="hand" style="background:{skin}"></div></div></div>')
        html = (f'<div id="{cid}" class="char" style="left:{x}px;top:{y}px">'
                + ((leg("L", 92) + leg("R", 150)) if legs else "")
                + f'<div class="torso" style="background:{top}"><svg viewBox="0 0 176 215" width="164" height="203"><path d="M66,8 Q88,40 110,8" stroke="{INK}" stroke-width="5" fill="none"/><path d="M76,30 L74,70 M100,30 L102,70" stroke="{INK}" stroke-width="4" stroke-linecap="round"/><path d="M40,150 L136,150" stroke="{INK}" stroke-width="4" opacity=".5"/></svg></div>'
                + arm("L", 34) + arm("R", 220)
                + f'<div class="head">{head_svg(skin, hair, style, headset)}</div></div>')
        self.js.append(f'gsap.set("#{cid}",{{scale:{scale},transformOrigin:"50% 100%"}});')
        for k, sel in (("aL", ".armL"), ("aR", ".armR"), ("lL", ".legL"), ("lR", ".legR")):
            self.js.append(f'gsap.set("#{cid} {sel}",{{rotation:{p[k]},transformOrigin:"50% 23px"}});')
        self.js.append(f'gsap.set("#{cid} .armL .fore",{{rotation:{p["fL"]},transformOrigin:"50% 21px"}});')
        self.js.append(f'gsap.set("#{cid} .armR .fore",{{rotation:{p["fR"]},transformOrigin:"50% 21px"}});')
        return html

    def pose(self, cid, pose, t, d=0.35, ease="power2.inOut"):
        new = POSES[pose] if isinstance(pose, str) else pose
        cur = self.state[cid]
        for k, sel in (("aL", ".armL"), ("aR", ".armR"), ("fL", ".armL .fore"), ("fR", ".armR .fore"),
                       ("lL", ".legL"), ("lR", ".legR")):
            if k in new and new[k] != cur[k]:
                self.js.append(f'tl.fromTo("#{cid} {sel}",{{rotation:{cur[k]}}},{{rotation:{new[k]},duration:{d},ease:"{ease}",immediateRender:false}},{t:.3f});')
                cur[k] = new[k]

    def walk(self, cid, t0, t1, step=0.32, amp=16):
        n = max(1, int((t1 - t0) / step))
        for i in range(n):
            a = amp if i % 2 == 0 else -amp
            self.pose(cid, dict(lL=a, lR=-a, aL=8 - a * 0.6, aR=-8 - a * 0.6), t0 + i * step, d=step, ease="sine.inOut")
        self.pose(cid, dict(lL=2, lR=-2, aL=8, aR=-8), t0 + n * step, d=0.2)

    def face(self, cid, t, mouth=None, brows=None, half=None, bags=None, sweat=None):
        if mouth:
            for m in MOUTHS:
                self.js.append(f'tl.set("#{cid} .m-{m}",{{opacity:{1 if m == mouth else 0}}},{t:.3f});')
        if brows:
            for b in BROWS:
                self.js.append(f'tl.set("#{cid} .br-{b}",{{opacity:{1 if b == brows else 0}}},{t:.3f});')
        for cls, v in (("half", half), ("bags", bags), ("sweat", sweat)):
            if v is not None:
                self.js.append(f'tl.set("#{cid} .{cls}",{{opacity:{v}}},{t:.3f});')

    def look(self, cid, t, dx, dy=0, d=0.2):
        cur = self.state[cid]["look"]
        self.js.append(f'tl.fromTo("#{cid} .pup",{{attr:{{cy:144}},x:{cur}}},{{x:{dx},attr:{{cy:{144 + dy}}},duration:{d},immediateRender:false}},{t:.3f});')
        self.state[cid]["look"] = dx

    def blink(self, cid, t):
        self.js.append(f'tl.set("#{cid} .lid",{{opacity:1}},{t:.3f});tl.set("#{cid} .lid",{{opacity:0}},{t + 0.12:.3f});')

    # ---------- generic motion ----------
    def pop(self, sel, t, d=0.35, sfx="pop", frm="scale:0,opacity:0", to="scale:1,opacity:1", ease="back.out(1.8)"):
        self.js.append(f'tl.fromTo("{sel}",{{{frm}}},{{{to},duration:{d},ease:"{ease}"}},{t:.3f});')
        if sfx: self.sfx.append((t, sfx))

    def tw(self, sel, t, frm, to, d=0.4, ease="power2.inOut", first=False):
        ir = "" if first else ",immediateRender:false"
        self.js.append(f'tl.fromTo("{sel}",{{{frm}}},{{{to},duration:{d},ease:"{ease}"{ir}}},{t:.3f});')

    def set(self, sel, t, props):
        self.js.append(f'tl.set("{sel}",{{{props}}},{t:.3f});')


# ---------- props (pure SVG strings) ----------
def svg(w, h, body, vb=None):
    return f'<svg viewBox="{vb or f"0 0 {w} {h}"}" width="{w}" height="{h}">{body}</svg>'

def tower(w=300):
    b = (f'<path d="M110,170 L190,170 L176,520 L124,520 Z" fill="{CREAM}" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
         f'<path d="M124,250 L176,250 M122,330 L178,330 M120,410 L180,410" stroke="{INK}" stroke-width="4" opacity=".35"/>'
         f'<path d="M50,90 L250,90 L226,170 L74,170 Z" fill="{MINT}" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
         f'<path d="M100,90 L104,170 M150,90 L150,170 M200,90 L196,170" stroke="{INK}" stroke-width="5"/>'
         f'<path d="M40,90 L260,90 L240,62 L60,62 Z" fill="{CORAL}" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
         f'<path d="M150,62 L150,14" stroke="{INK}" stroke-width="6"/><circle cx="150" cy="12" r="9" fill="{CORAL}" stroke="{INK}" stroke-width="5"/>'
         f'<rect x="96" y="512" width="108" height="20" rx="4" fill="{WALL_D}" stroke="{INK}" stroke-width="6"/>')
    return svg(w, w * 540 / 300, b, "0 0 300 540")

def plane(w=260, flip=False):
    b = (f'<g transform="{"scale(-1,1) translate(-260,0)" if flip else ""}">'
         f'<path d="M20,70 Q30,48 70,48 L210,48 Q248,50 252,64 Q248,80 210,82 L70,82 Q30,82 20,70 Z" fill="{CREAM}" stroke="{INK}" stroke-width="6"/>'
         f'<path d="M120,62 L80,10 L104,10 L160,60 Z M120,72 L84,120 L108,120 L162,74 Z" fill="{STEEL}" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
         f'<path d="M30,52 L14,18 L34,18 L56,50 Z" fill="{CORAL}" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
         f'<path d="M226,56 Q240,58 244,64 L226,64 Z" fill="{INK}"/>'
         + "".join(f'<circle cx="{x}" cy="62" r="4" fill="{INK}"/>' for x in range(90, 210, 18)) + '</g>')
    return svg(w, w * 130 / 260, b, "0 0 260 130")

def bill(w=180):
    b = (f'<rect x="4" y="4" width="252" height="112" rx="10" fill="#8FD18A" stroke="{INK}" stroke-width="6"/>'
         f'<rect x="20" y="18" width="220" height="84" rx="6" fill="none" stroke="#2E7D4F" stroke-width="4"/>'
         f'<circle cx="130" cy="60" r="30" fill="#BFEBB8" stroke="#2E7D4F" stroke-width="4"/>'
         f'<text x="130" y="74" text-anchor="middle" font-family="Archivo Black" font-size="40" fill="#2E7D4F">$</text>')
    return svg(w, w * 120 / 260, b, "0 0 260 120")

def scope(w=440):
    rings = "".join(f'<circle cx="220" cy="220" r="{r}" fill="none" stroke="{MINT}" stroke-width="3" opacity=".55"/>' for r in (60, 120, 180))
    b = (f'<circle cx="220" cy="220" r="214" fill="#1E2A2C" stroke="{INK}" stroke-width="8"/>'
         f'<circle cx="220" cy="220" r="196" fill="#0F2B22" stroke="#3A4A4A" stroke-width="6"/>' + rings +
         f'<path d="M220,24 L220,416 M24,220 L416,220" stroke="{MINT}" stroke-width="2" opacity=".4"/>')
    return svg(w, w, b, "0 0 440 440")

def sweep(w=440):
    b = (f'<defs><linearGradient id="sw" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{MINT}" stop-opacity="0"/><stop offset="1" stop-color="{MINT}" stop-opacity=".55"/></linearGradient></defs>'
         f'<path d="M220,220 L220,26 A194,194 0 0 1 356,82 Z" fill="url(#sw)"/><path d="M220,220 L220,26" stroke="{MINT}" stroke-width="5"/>')
    return svg(w, w, b, "0 0 440 440")

def blip(label):
    return (f'<svg viewBox="0 0 150 40" width="150" height="40"><circle cx="10" cy="20" r="8" fill="{MINT}"/>'
            f'<text x="26" y="27" font-family="JetBrains Mono" font-size="20" font-weight="700" fill="{MINT}">{label}</text></svg>')

def desk(w=1260, h=230):
    b = (f'<rect x="4" y="30" width="{w - 8}" height="{h - 34}" rx="16" fill="#2E3B44" stroke="{INK}" stroke-width="8"/>'
         f'<rect x="4" y="4" width="{w - 8}" height="44" rx="12" fill="#3E4E59" stroke="{INK}" stroke-width="8"/>'
         + "".join(f'<circle cx="{x}" cy="120" r="14" fill="{c}" stroke="{INK}" stroke-width="5"/>' for x, c in ((80, CORAL), (130, MUSTARD), (180, MINT), (w - 180, MINT), (w - 130, MUSTARD), (w - 80, CORAL)))
         + f'<rect x="{w / 2 - 160}" y="96" width="320" height="50" rx="8" fill="#1E2A2C" stroke="{INK}" stroke-width="5"/>')
    return svg(w, h, b)

def bubble(w, h, tail="left"):
    tx = 70 if tail == "left" else w - 110
    b = (f'<path d="M30,10 L{w - 30},10 Q{w - 10},10 {w - 10},30 L{w - 10},{h - 70} Q{w - 10},{h - 50} {w - 30},{h - 50} L{tx + 60},{h - 50} '
         f'L{tx + (0 if tail == "left" else 90)},{h - 6} L{tx + 30},{h - 50} L30,{h - 50} Q10,{h - 50} 10,{h - 70} L10,30 Q10,10 30,10 Z" '
         f'fill="{CREAM}" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>')
    return svg(w, h, b)

def thought(w=620, h=440):
    b = (f'<path d="M140,330 C60,340 30,260 80,220 C30,170 80,90 160,110 C180,40 290,30 330,80 C380,20 500,40 500,120 C580,130 600,240 530,270 C560,340 470,380 420,340 C380,390 260,390 230,340 C200,360 160,350 140,330 Z" '
         f'fill="{CREAM}" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>')
    return svg(w, h, b, "0 0 620 400")

def heart_monitor(w=520):
    b = (f'<rect x="4" y="4" width="512" height="300" rx="22" fill="#2E3B44" stroke="{INK}" stroke-width="8"/>'
         f'<rect x="28" y="28" width="464" height="200" rx="10" fill="#0F2B22" stroke="{INK}" stroke-width="5"/>'
         f'<path class="ecg" d="M28,130 L130,130 L150,130 L165,80 L182,180 L198,130 L300,130 L320,130 L335,80 L352,180 L368,130 L492,130" fill="none" stroke="{MINT}" stroke-width="6" stroke-linejoin="round" stroke-dasharray="900" stroke-dashoffset="900"/>'
         f'<text x="40" y="282" font-family="Archivo Black" font-size="46" fill="{MINT}">72</text>'
         f'<text x="128" y="282" font-family="JetBrains Mono" font-size="26" font-weight="700" fill="{CREAM}">BPM · STEADY</text>'
         f'<path d="M440,250 C430,238 410,246 418,262 L440,282 L462,262 C470,246 450,238 440,250 Z" fill="{CORAL}"/>')
    return svg(w, w * 310 / 520, b, "0 0 520 310")

def cap(w=360):
    b = (f'<path d="M180,30 L350,100 L180,170 L10,100 Z" fill="#2B2A33" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>'
         f'<path d="M80,130 L80,200 Q180,250 280,200 L280,130 L180,170 Z" fill="#3B3A45" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>'
         f'<path d="M300,110 L300,210" stroke="{MUSTARD}" stroke-width="7"/><circle cx="300" cy="216" r="12" fill="{MUSTARD}" stroke="{INK}" stroke-width="4"/>')
    return svg(w, w * 260 / 360, b, "0 0 360 260")

def xmark(w=420, color=CORAL):
    b = (f'<path class="x1" d="M40,40 L380,380" stroke="{color}" stroke-width="48" stroke-linecap="round" stroke-dasharray="490" stroke-dashoffset="490"/>'
         f'<path class="x2" d="M380,40 L40,380" stroke="{color}" stroke-width="48" stroke-linecap="round" stroke-dasharray="490" stroke-dashoffset="490"/>')
    return svg(w, w, b, "0 0 420 420")

def headset_icon(w=260):
    b = (f'<path d="M40,150 C30,20 230,20 220,150" stroke="#2B2A33" stroke-width="22" fill="none" stroke-linecap="round"/>'
         f'<rect x="12" y="130" width="62" height="96" rx="20" fill="#2B2A33" stroke="{INK}" stroke-width="7"/>'
         f'<rect x="186" y="130" width="62" height="96" rx="20" fill="#2B2A33" stroke="{INK}" stroke-width="7"/>'
         f'<path d="M216,220 Q214,260 150,262" stroke="{INK}" stroke-width="9" fill="none" stroke-linecap="round"/><circle cx="146" cy="262" r="13" fill="{CORAL}" stroke="{INK}" stroke-width="5"/>')
    return svg(w, w * 280 / 260, b, "0 0 260 280")

def steel(w=300):
    b = (f'<rect x="6" y="40" width="288" height="200" rx="14" fill="{STEEL}" stroke="{INK}" stroke-width="8"/>'
         f'<path d="M20,60 L120,60" stroke="#fff" stroke-width="8" opacity=".6" stroke-linecap="round"/>'
         + "".join(f'<circle cx="{x}" cy="{y}" r="9" fill="#7A8B96" stroke="{INK}" stroke-width="4"/>' for x in (34, 266) for y in (68, 212))
         + f'<text x="150" y="132" text-anchor="middle" font-family="Archivo Black" font-size="38" fill="{INK}">NERVES</text>'
           f'<text x="150" y="180" text-anchor="middle" font-family="Archivo Black" font-size="30" fill="{INK}">OF STEEL</text>')
    return svg(w, w * 250 / 300, b, "0 0 300 250")

def calendar(days=("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"), w=900):
    cells = ""
    for i, d in enumerate(days):
        x = 20 + i * 122
        cells += (f'<rect x="{x}" y="90" width="110" height="130" rx="10" fill="#fff" stroke="{INK}" stroke-width="6"/>'
                  f'<text x="{x + 55}" y="128" text-anchor="middle" font-family="Archivo Black" font-size="24" fill="{INK}">{d}</text>'
                  f'<path class="cx cx{i}" d="M{x + 22},{150} L{x + 88},{205} M{x + 88},{150} L{x + 22},{205}" stroke="{CORAL}" stroke-width="12" stroke-linecap="round" opacity="0"/>')
    b = (f'<rect x="6" y="6" width="{888}" height="236" rx="18" fill="{CREAM}" stroke="{INK}" stroke-width="8"/>'
         f'<rect x="6" y="6" width="888" height="70" rx="18" fill="{CORAL}" stroke="{INK}" stroke-width="8"/>'
         f'<text x="450" y="56" text-anchor="middle" font-family="Archivo Black" font-size="36" fill="{CREAM}">WEEK 1</text>' + cells)
    return svg(w, w * 250 / 900, b, "0 0 900 250")

def paycheck(w=900, amount="$144,000"):
    b = (f'<rect x="6" y="6" width="888" height="388" rx="16" fill="#E9F3DF" stroke="{INK}" stroke-width="8"/>'
         f'<rect x="30" y="30" width="840" height="340" rx="8" fill="none" stroke="#7FAF6E" stroke-width="4" stroke-dasharray="14 10"/>'
         f'<text x="60" y="96" font-family="Archivo Black" font-size="34" fill="#2E5D3A">U.S. FEDERAL PAYROLL</text>'
         f'<text x="60" y="180" font-family="JetBrains Mono" font-size="28" font-weight="700" fill="{INK}">PAY TO THE ORDER OF:  YOU</text>'
         f'<rect x="520" y="210" width="330" height="90" rx="10" fill="#fff" stroke="{INK}" stroke-width="6"/>'
         f'<text x="685" y="272" text-anchor="middle" font-family="Archivo Black" font-size="52" fill="{INK}">{amount}</text>'
         f'<path d="M60,320 Q120,280 170,316 T290,312" stroke="{INK}" stroke-width="5" fill="none"/>')
    return svg(w, w * 400 / 900, b, "0 0 900 400")

def hazard_tag(w=520):
    stripes = "".join(f'<path d="M{x},20 L{x + 40},20 L{x - 20},120 L{x - 60},120 Z" fill="{INK}"/>' for x in range(40, 560, 80))
    b = (f'<defs><clipPath id="hz"><rect x="10" y="10" width="500" height="120" rx="14"/></clipPath></defs>'
         f'<rect x="10" y="10" width="500" height="250" rx="18" fill="{MUSTARD}" stroke="{INK}" stroke-width="8"/>'
         f'<g clip-path="url(#hz)">{stripes}</g><rect x="10" y="10" width="500" height="120" rx="14" fill="none" stroke="{INK}" stroke-width="8"/>'
         f'<text x="260" y="222" text-anchor="middle" font-family="Archivo Black" font-size="72" fill="{INK}">WARNING</text>'
         f'<circle cx="480" cy="44" r="14" fill="{CREAM}" stroke="{INK}" stroke-width="5"/>')
    return svg(w, w * 270 / 520, b, "0 0 520 270")

def stamp(text, color="#2FA86B", w=520):
    b = (f'<rect x="10" y="10" width="500" height="180" rx="22" fill="none" stroke="{color}" stroke-width="16"/>'
         f'<text x="260" y="140" text-anchor="middle" font-family="Archivo Black" font-size="110" fill="{color}">{text}</text>')
    return svg(w, w * 200 / 520, b, "0 0 520 200")

def cloud_storm(w=420):
    b = (f'<path d="M90,170 C30,170 20,100 80,90 C80,30 170,20 200,60 C240,10 340,30 330,100 C400,100 400,180 330,180 Z" fill="#3A3F52" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>'
         f'<path d="M110,90 q20,-20 40,0 q20,20 40,0 q20,-20 40,0" stroke="#5A6078" stroke-width="7" fill="none" stroke-linecap="round"/>'
         + "".join(f'<path class="rain" d="M{x},200 L{x - 12},236" stroke="#8FD3FF" stroke-width="7" stroke-linecap="round"/>' for x in (120, 180, 240, 300)))
    return svg(w, w * 250 / 420, b, "0 0 420 250")

def car(w=760):
    b = (f'<path d="M40,250 L40,180 Q44,150 90,140 L200,130 L280,60 Q300,44 330,44 L520,44 Q556,44 576,70 L640,140 L700,150 Q730,156 730,190 L730,250 Z" fill="{CORAL}" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
         f'<path d="M300,70 L410,70 L410,140 L236,140 Z" fill="{MINT}" fill-opacity=".28" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
         f'<path d="M440,70 L540,70 Q556,70 566,84 L612,140 L440,140 Z" fill="{MINT}" fill-opacity=".28" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
         f'<circle cx="190" cy="252" r="56" fill="#2B2A33" stroke="{INK}" stroke-width="9"/><circle cx="190" cy="252" r="22" fill="{STEEL}"/>'
         f'<circle cx="580" cy="252" r="56" fill="#2B2A33" stroke="{INK}" stroke-width="9"/><circle cx="580" cy="252" r="22" fill="{STEEL}"/>')
    return svg(w, w * 320 / 760, b, "0 0 760 320")

def table(w=900):
    b = (f'<rect x="10" y="10" width="880" height="54" rx="12" fill="#B07A4F" stroke="{INK}" stroke-width="8"/>'
         f'<rect x="80" y="60" width="40" height="190" fill="#8E5E3B" stroke="{INK}" stroke-width="7"/>'
         f'<rect x="780" y="60" width="40" height="190" fill="#8E5E3B" stroke="{INK}" stroke-width="7"/>'
         f'<ellipse cx="300" cy="14" rx="90" ry="20" fill="#fff" stroke="{INK}" stroke-width="6"/><ellipse cx="600" cy="14" rx="90" ry="20" fill="#fff" stroke="{INK}" stroke-width="6"/>')
    return svg(w, w * 260 / 900, b, "0 0 900 260")

def iceberg(w=1500):
    b = (f'<path d="M560,300 L660,150 L720,190 L780,110 L880,230 L940,300 Z" fill="#F4FBFF" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>'
         f'<path d="M380,300 L1120,300 L1260,520 L1180,760 L960,900 L600,880 L360,720 L260,500 Z" fill="#BFE3F2" stroke="{INK}" stroke-width="8" stroke-linejoin="round" opacity=".95"/>'
         f'<path d="M520,420 L640,560 M900,400 L1000,600 M700,700 L820,800" stroke="#8CC3DA" stroke-width="8" stroke-linecap="round"/>')
    return svg(w, w * 920 / 1500, b, "0 0 1500 920")


CSS = f"""
:root{{--ink:{INK}}}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1920px;height:1080px;overflow:hidden;background:{WALL}}}
#root{{position:relative;width:100%;height:100%;overflow:hidden;font-family:Montserrat,sans-serif}}
#stage{{position:absolute;inset:0;background:radial-gradient(ellipse 900px 620px at 50% 46%, #2A7280 0%, {WALL} 62%, {WALL_D} 100%)}}
#stage .floor{{position:absolute;left:0;right:0;top:860px;bottom:0;background:{FLOOR};border-top:8px solid {INK}}}
#stage .floor::before{{content:"";position:absolute;left:0;right:0;top:0;height:10px;background:#1C4952}}
#stage .dots{{position:absolute;inset:0 0 220px 0;background-image:radial-gradient(#2E6E7A 2px, transparent 2.5px);background-size:44px 44px;opacity:.55}}
.scene{{position:absolute;inset:0;overflow:hidden}}
.abs{{position:absolute}}
.char{{position:absolute;width:300px;height:620px}}
.leg{{position:absolute;top:392px;width:58px;height:208px;border:6px solid {INK};border-radius:29px}}
.shoe{{position:absolute;left:-18px;top:160px;width:86px;height:42px;background:#2B2A33;border:6px solid {INK};border-radius:40px 40px 12px 12px}}
.torso{{position:absolute;left:62px;top:205px;width:176px;height:215px;border:6px solid {INK};border-radius:72px 72px 30px 30px;overflow:hidden}}
.arm{{position:absolute;top:220px;width:46px;height:128px;border:6px solid {INK};border-radius:23px}}
.fore{{position:absolute;left:-4px;top:88px;width:42px;height:120px;border:6px solid {INK};border-radius:21px}}
.hand{{position:absolute;left:-12px;top:80px;width:54px;height:54px;border:6px solid {INK};border-radius:50%}}
.head{{position:absolute;left:-13px;top:-66px;width:326px;height:302px}}
.label{{font-family:"Archivo Black",sans-serif;color:{CREAM};-webkit-text-stroke:0;text-shadow:4px 4px 0 {INK},-3px 3px 0 {INK},3px -3px 0 {INK},-3px -3px 0 {INK},0 4px 0 {INK}}}
.capwrap{{position:absolute;left:0;right:0;bottom:56px;display:flex;justify-content:center;z-index:50}}
.cap{{color:#FFD60A;font-weight:900;font-size:58px;line-height:1.1;text-align:center;max-width:1500px;
 text-shadow:3px 3px 0 #000,-3px 3px 0 #000,3px -3px 0 #000,-3px -3px 0 #000,0 3px 0 #000,0 -3px 0 #000,3px 0 0 #000,-3px 0 0 #000,0 6px 18px rgba(0,0,0,.6)}}
"""
