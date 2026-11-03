"""Write the HyperFrames composition (build/index.html) from timeline.json.
Usage: python3 compose.py <projdir>
Expects build/assets/bg.mp4 and build/assets/voice.(wav|mp3); copies gsap from pipeline/node_modules.
"""
import sys, json, html, pathlib, shutil

P = pathlib.Path(sys.argv[1]); B = P / "build"
tl = json.load(open(P / "timeline.json")); M = json.load(open(P / "map.json"))
(B / "assets" / "js").mkdir(parents=True, exist_ok=True)
shutil.copy(pathlib.Path(__file__).resolve().parent.parent / "node_modules/gsap/dist/gsap.min.js", B / "assets/js/gsap.min.js")
voice = next(f.name for f in (B / "assets").iterdir() if f.stem == "voice")
T = tl["duration"]; f3 = lambda x: f"{x:.3f}"
el, js = [], []

# background footage (one cut-together track) + gentle push-in per shot
el.append(f'<div id="bgwrap"><video id="bg" class="clip" src="assets/bg.mp4" muted data-start="0" '
          f'data-duration="{f3(T)}" data-track-index="0"></video></div>')
for i, s in enumerate(tl["shots"]):
    a, b = (1.0, 1.06) if i % 2 == 0 else (1.06, 1.0)
    js.append(f'tl.fromTo("#bgwrap",{{scale:{a}}},{{scale:{b},duration:{f3(s["dur"])},ease:"none",immediateRender:false}},{f3(s["start"])});')
el.append('<div id="shade"></div><div id="fade"></div>')
js.append(f'tl.fromTo("#fade",{{opacity:0}},{{opacity:1,duration:0.9,ease:"none"}},{f3(T - 1.0)});')
el.append(f'<audio id="vo" class="clip" src="assets/{voice}" data-start="0" data-duration="{f3(T)}" data-track-index="9"></audio>')

PERSON = ('<svg viewBox="0 0 40 80" class="p"><circle cx="20" cy="12" r="11"/>'
          '<path d="M4 34q0-10 10-10h12q10 0 10 10v22h-7v24h-18v-24h-7z"/></svg>')
for k, o in enumerate(tl["overlays"]):
    oid, s, d = f"ov{k}", o["start"], o["dur"]
    attrs = f'id="{oid}" class="clip ov" data-start="{f3(s)}" data-duration="{f3(d)}" data-track-index="3"'
    if o["type"] == "stat":
        el.append(f'<div {attrs}><div class="stat"><div class="big">{html.escape(o["big"])}</div>'
                  f'<div class="bar"></div><div class="small">{html.escape(o["small"])}</div></div></div>')
        js += [f'tl.fromTo("#{oid} .stat",{{opacity:0,scale:0.85,y:30}},{{opacity:1,scale:1,y:0,duration:0.35,ease:"back.out(1.6)"}},{f3(s)});',
               f'tl.fromTo("#{oid} .bar",{{scaleX:0}},{{scaleX:1,duration:0.4,ease:"power3.out"}},{f3(s + 0.2)});',
               f'tl.to("#{oid} .stat",{{opacity:0,y:-20,duration:0.25,ease:"power2.in"}},{f3(s + d - 0.3)});']
    elif o["type"] == "map":
        place = o["place"]
        pin = "" if place == "usa" else (
            f'<g class="pin" transform="translate({M["pins"][place][0]},{M["pins"][place][1]})">'
            f'<circle class="ring" r="30"/><circle class="dot" r="20"/></g>')
        el.append(f'<div {attrs}><div class="mapcard"><svg viewBox="0 0 {M["w"]} {M["h"]}" class="map">'
                  f'<path class="nation{" hl" if place == "usa" else ""}" d="{M["nation"]}"/>'
                  f'<path class="borders" d="{M["borders"]}"/>{pin}</svg>'
                  f'<div class="maplabel">{html.escape(o["label"])}</div></div></div>')
        js += [f'tl.fromTo("#{oid} .mapcard",{{opacity:0,scale:0.92}},{{opacity:1,scale:1,duration:0.4,ease:"power3.out"}},{f3(s)});',
               f'tl.fromTo("#{oid} .maplabel",{{opacity:0,x:-30}},{{opacity:1,x:0,duration:0.35,ease:"power3.out"}},{f3(s + 0.5)});',
               f'tl.to("#{oid} .mapcard",{{opacity:0,duration:0.25}},{f3(s + d - 0.3)});']
        if place == "usa":
            js.append(f'tl.fromTo("#{oid} .nation",{{fill:"#1d2a3a"}},{{fill:"#ffd60a",duration:0.6,ease:"power2.out"}},{f3(s + 0.35)});')
        else:
            js += [f'tl.fromTo("#{oid} .dot",{{y:-60,opacity:0}},{{y:0,opacity:1,duration:0.45,ease:"bounce.out"}},{f3(s + 0.35)});',
                   f'tl.fromTo("#{oid} .ring",{{scale:0.5,opacity:0.9,transformOrigin:"50% 50%"}},{{scale:2.6,opacity:0,duration:1.1,ease:"power2.out"}},{f3(s + 0.8)});',
                   f'tl.fromTo("#{oid} .ring",{{scale:0.5,opacity:0.9,transformOrigin:"50% 50%"}},{{scale:2.6,opacity:0,duration:1.1,ease:"power2.out",immediateRender:false}},{f3(s + 1.9)});']
    elif o["type"] == "people":
        n, gone = o["total"], o["gone"]
        icons = "".join(f'<span class="pi{" gone" if i >= n - gone else ""}">{PERSON}</span>' for i in range(n))
        label = f"{n} start" if gone == 0 else f"{n - gone} of {n} left"
        el.append(f'<div {attrs}><div class="people"><div class="row">{icons}</div><div class="plabel">{label}</div></div></div>')
        js += [f'tl.fromTo("#{oid} .people",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.3,ease:"power3.out"}},{f3(s)});',
               f'tl.fromTo("#{oid} .pi",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.25,stagger:0.05,ease:"power2.out"}},{f3(s + 0.1)});',
               f'tl.fromTo("#{oid} .plabel",{{opacity:0}},{{opacity:1,duration:0.3}},{f3(s + 0.9 + 0.12 * gone)});',
               f'tl.to("#{oid} .people",{{opacity:0,duration:0.25}},{f3(s + d - 0.3)});']
        if gone:
            js.append(f'tl.to("#{oid} .gone",{{opacity:0.18,y:24,duration:0.35,stagger:0.12,ease:"power2.in"}},{f3(s + 0.7)});')

for k, c in enumerate(tl["captions"]):
    d = max(0.2, c["end"] - c["start"])
    el.append(f'<div id="c{k}" class="clip capwrap" data-start="{f3(c["start"])}" data-duration="{f3(d)}" '
              f'data-track-index="5"><div class="cap">{html.escape(c["text"])}</div></div>')
    js.append(f'tl.fromTo("#c{k} .cap",{{scale:0.88,opacity:0}},{{scale:1,opacity:1,duration:0.14,ease:"back.out(2)"}},{f3(c["start"])});')

OUT = """<!doctype html>
<html lang="en"><head><meta charset="UTF-8" /><meta name="viewport" content="width=1920, height=1080" />
<script src="assets/js/gsap.min.js"></script>
<style>
:root{--cap:#ffd60a;--ink:#fff;--bgc:#000}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1920px;height:1080px;overflow:hidden;background:var(--bgc)}
#root{position:relative;width:100%;height:100%;font-family:Montserrat,sans-serif;overflow:hidden}
#bgwrap{position:absolute;inset:0;transform-origin:50% 50%}
#bg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
#fade{position:absolute;inset:0;background:#000;opacity:0;z-index:30}
#shade{position:absolute;left:0;right:0;bottom:0;height:420px;background:linear-gradient(to top,rgba(0,0,0,.55),rgba(0,0,0,0));z-index:2}
.capwrap{position:absolute;left:0;right:0;bottom:120px;display:flex;justify-content:center;z-index:20}
.cap{color:var(--cap);font-weight:900;font-size:66px;line-height:1.1;text-align:center;max-width:1500px;
 text-shadow:3px 3px 0 #000,-3px 3px 0 #000,3px -3px 0 #000,-3px -3px 0 #000,0 3px 0 #000,0 -3px 0 #000,3px 0 0 #000,-3px 0 0 #000,0 6px 18px rgba(0,0,0,.7)}
.ov{position:absolute;inset:0;z-index:10;display:flex;justify-content:center}
.stat{margin-top:150px;display:flex;flex-direction:column;align-items:center;background:rgba(8,10,14,.72);padding:34px 70px 40px;border-radius:18px;height:fit-content}
.big{font-family:'League Gothic',Oswald,sans-serif;font-size:210px;line-height:.9;color:var(--ink)}
.bar{width:100%;height:10px;background:var(--cap);margin:14px 0 18px;transform-origin:0 50%}
.small{font-family:Inter,sans-serif;font-weight:700;font-size:40px;color:#e8e8e8}
.mapcard{margin-top:70px;position:relative;width:1180px;height:760px;background:rgba(8,12,18,.84);border-radius:22px;padding:40px}
.map{width:1100px;height:680px}
.nation{fill:#1d2a3a;stroke:#9fb3c8;stroke-width:2}
.borders{fill:none;stroke:#5f7590;stroke-width:1}
.dot{fill:var(--cap);stroke:#000;stroke-width:3}
.ring{fill:none;stroke:var(--cap);stroke-width:4}
.maplabel{position:absolute;left:60px;bottom:44px;font-family:Inter,sans-serif;font-weight:900;font-size:54px;color:var(--ink);
 background:#000;padding:8px 22px;border-left:10px solid var(--cap)}
.people{margin-top:170px;display:flex;flex-direction:column;align-items:center;background:rgba(8,10,14,.72);padding:40px 60px;border-radius:18px;height:fit-content}
.row{display:flex;gap:26px}
.pi .p{width:70px;height:140px;fill:var(--ink)}
.pi.gone .p{fill:#ff4d4d}
.plabel{margin-top:24px;font-family:Inter,sans-serif;font-weight:900;font-size:56px;color:var(--cap)}
</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="__T__" data-width="1920" data-height="1080">
__EL__
</div>
<script>
const tl = gsap.timeline({ paused: true });
__JS__
window.__timelines["main"] = tl;
tl.seek(0);
</script></body></html>
"""
(B / "index.html").write_text(OUT.replace("__T__", f3(T)).replace("__EL__", "\n".join(el)).replace("__JS__", "\n".join(js)),
                              encoding="utf-8")
for f in ("hyperframes.json", "meta.json"):
    src = pathlib.Path(__file__).resolve().parent.parent / "smoketest" / f
    if src.exists() and not (B / f).exists(): shutil.copy(src, B / f)
print("index.html written:", len(el), "elements,", len(js), "tweens")
