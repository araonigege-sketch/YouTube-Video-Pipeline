"""Mr. Davos illustrations, drawn in code (CineCode dark-keynote grammar, multi-colour per the owner).

Each function draws one full-frame illustration page on the composition `c` between t0 and t1
(composition seconds). Illustrations play through uninterrupted: every beat is anchored to the
narration with `c.t("phrase", t0)`, so something new appears every few seconds without cutting away.

Grammar: near-black stage + hairline grid; line work draws on (stroke-dash), surfaces fill with a
soft tint of their colour; each concept keeps one colour through the episode (captain = accent gold,
first officer = c1 sky, pilot flying = c3 mint, pilot monitoring = c2 violet, warnings = c4 coral).
"""
from __future__ import annotations

import html


def _svg(inner: str) -> str:
    return (f'<svg viewBox="0 0 1920 1080" width="1920" height="1080" style="position:absolute;inset:0" '
            f'fill="none" stroke-linecap="round" stroke-linejoin="round">{inner}</svg>')


def _line(id_, d, color, w=3, op=1.0):
    return (f'<path id="{id_}" d="{d}" stroke="{color}" stroke-width="{w}" stroke-opacity="{op}" '
            f'pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"/>')


def _cockpit_shell(g: str, p: dict, drawn: bool) -> tuple[str, list[str]]:
    """Top-down cockpit: nose shell, windshield, panel, centre pedestal, two seats. Returns svg + ids to draw."""
    W = "rgba(244,242,238,.55)"
    parts = [
        (f"{g}sh", "M560 930 L560 450 Q560 170 960 140 Q1360 170 1360 450 L1360 930", W, 3),
        (f"{g}ws", "M650 420 Q675 245 960 222 Q1245 245 1270 420", p["c1"], 3),
        (f"{g}wd1", "M800 262 L815 410", p["c1"], 2),
        (f"{g}wd2", "M1120 262 L1105 410", p["c1"], 2),
        (f"{g}pn", "M660 450 L1260 450 Q1280 450 1280 470 L1280 505 Q1280 525 1260 525 L660 525 Q640 525 640 505 "
                   "L640 470 Q640 450 660 450 Z", W, 2.5),
        (f"{g}pd", "M915 545 L1005 545 Q1020 545 1020 560 L1020 800 Q1020 815 1005 815 L915 815 Q900 815 900 800 "
                   "L900 560 Q900 545 915 545 Z", W, 2.5),
    ]
    out, ids = [], []
    for id_, d, col, w in parts:
        if drawn:
            out.append(f'<path id="{id_}" d="{d}" stroke="{col}" stroke-width="{w}"/>')
        else:
            out.append(_line(id_, d, col, w))
            ids.append(id_)
    # instrument screens on the panel (small rounded rects)
    for k, x in enumerate((690, 800, 1010, 1120)):
        out.append(f'<rect class="{g}scr" x="{x}" y="465" width="90" height="45" rx="7" fill="{p["c1"]}" fill-opacity=".14" '
                   f'stroke="{p["c1"]}" stroke-opacity=".5" stroke-width="1.5"/>')
    # seats
    for side, x in (("L", 700), ("R", 1050)):
        out.append(f'<g id="{g}seat{side}"><rect x="{x}" y="575" width="170" height="215" rx="44" '
                   f'fill="rgba(255,255,255,.03)" stroke="{W}" stroke-width="2.5"/>'
                   f'<rect x="{x + 30}" y="805" width="110" height="46" rx="20" fill="rgba(255,255,255,.03)" stroke="{W}" stroke-width="2.5"/></g>')
    return "".join(out), ids


def _stripes(n: int, color: str) -> str:
    return "".join(f'<span style="display:inline-block;width:46px;height:9px;border-radius:3px;background:{color};'
                   f'margin-right:10px"></span>' for _ in range(n))


def _seat_label(gid, side, name, sub, stripes, color):
    pos = "right:1440px;text-align:right" if side == "L" else "left:1440px"
    return (f'<div id="{gid}lab{side}" style="position:absolute;{pos};top:575px;width:520px;opacity:0">'
            f'<div style="font-family:\'Inter Display\';font-weight:800;font-size:54px;letter-spacing:.06em;color:{color}">{html.escape(name)}</div>'
            f'<div style="margin:16px 0 18px">{_stripes(stripes, color)}</div>'
            f'<div style="font-weight:600;font-size:26px;letter-spacing:.18em;text-transform:uppercase;color:#C9CCD1;white-space:nowrap">{html.escape(sub)}</div></div>')


def _light_seat(c, gid, side, color, t):
    sel = f"#{gid}seat{side} rect"
    c.tw(f'tl.to("{sel}",{{attr:{{stroke:"{color}"}},fill:"{color}",fillOpacity:0.2,duration:0.5,ease:"power2.out"}},{t:.3f});')
    c.tw(f'tl.fromTo("#{gid}glow{side}",{{opacity:0,scale:0.6}},{{opacity:1,scale:1,duration:0.8,ease:"power2.out"}},{t:.3f});')


def cockpit(c, s, t0, t1):
    """Who sits where. phase: seats (captain, first officer, coffee gag) | swap (pilot flying / monitoring trade places)."""
    p = c.p
    gid = c.nid("ck")
    phase = s.get("phase", "seats")
    drawn = phase != "seats"
    shell, ids = _cockpit_shell(gid, p, drawn)
    glows = "".join(f'<div id="{gid}glow{side}" style="position:absolute;left:{x - 140}px;top:540px;width:450px;height:450px;'
                    f'border-radius:50%;background:radial-gradient(circle,{col}33 0%,transparent 62%);opacity:0"></div>'
                    for side, x, col in (("L", 700, p["accent"]), ("R", 1050, p["c1"])))
    labels = (_seat_label(gid, "L", "CAPTAIN", s.get("cap_sub", "In command · final call"), 4, p["accent"])
              + _seat_label(gid, "R", "FIRST OFFICER", s.get("fo_sub", "The co-pilot"), 3, p["c1"]))
    extra = ""
    if phase == "seats":
        # coffee cup by the right seat, struck out in coral
        extra = (f'<g transform="translate(1270 600)"><g id="{gid}cup" opacity="0">'
                 f'<path d="M0 0 L70 0 L62 78 Q60 90 48 90 L22 90 Q10 90 8 78 Z" fill="rgba(255,255,255,.06)" stroke="#E9E4DA" stroke-width="3"/>'
                 f'<path d="M70 18 Q100 18 98 42 Q96 62 66 60" stroke="#E9E4DA" stroke-width="3"/>'
                 f'<path d="M22 -18 Q14 -32 24 -44 M44 -18 Q36 -32 46 -44" stroke="#E9E4DA" stroke-width="2.5" stroke-opacity=".7"/></g></g>'
                 + _line(f"{gid}x1", "M1250 585 L1385 705", p["c4"], 7) + _line(f"{gid}x2", "M1385 585 L1250 705", p["c4"], 7))
    badges = ""
    if phase == "swap":
        badges = "".join(
            f'<div style="position:absolute;left:{x}px;top:885px;width:0;display:flex;justify-content:center">'
            f'<div id="{gid}b{k}" style="opacity:0;padding:14px 28px;border-radius:999px;background:{col}26;border:2px solid {col};'
            f'color:{col};font-weight:700;font-size:25px;letter-spacing:.16em;white-space:nowrap">{txt}</div></div>'
            for k, (x, col, txt) in enumerate(((785, p["c3"], "PILOT FLYING"), (1135, p["c2"], "PILOT MONITORING"))))
        badges += (f'<div id="{gid}nf" style="position:absolute;left:0;right:0;top:70px;text-align:center;opacity:0;'
                   f'font-weight:600;font-size:28px;letter-spacing:.3em;color:#C9CCD1">NEXT FLIGHT</div>')
    inner = c.stage() + glows + _svg(shell + extra) + labels + badges
    c.add(gid, t0, t1, inner, z=10, cls="page")

    if phase == "seats":
        for k, id_ in enumerate(ids):
            c.draw(f"#{id_}", t0 + 0.05 + 0.12 * k, 0.9, 1)
        c.tw(f'tl.fromTo("#{gid} .{gid}scr",{{opacity:0}},{{opacity:1,duration:0.4,stagger:0.08}},{t0 + 0.6:.3f});')
        c.tw(f'tl.fromTo("#{gid}seatL,#{gid}seatR",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.5,stagger:0.1}},{t0 + 0.5:.3f});')
        tc = c.t(s.get("cap_at", "captain"), t0, 0.1)
        _light_seat(c, gid, "L", p["accent"], tc)
        c.rise(f"#{gid}labL", tc, 0.6, 18, 0.1)
        tf = c.t(s.get("fo_at", "first officer"), t0, 0.1)
        _light_seat(c, gid, "R", p["c1"], tf)
        c.rise(f"#{gid}labR", tf, 0.6, 18, 0.1)
        tcf = c.t(s.get("cup_at", "hold the coffee"), t0, 0.1)
        c.tw(f'tl.fromTo("#{gid}cup",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.45,ease:"power2.out"}},{tcf:.3f});')
        tx = c.t(s.get("x_at", "coffee"), tcf, 0.0) + 0.35
        c.draw(f"#{gid}x1", tx, 0.25, 1)
        c.draw(f"#{gid}x2", tx + 0.2, 0.25, 1)
    else:
        c.tw(f'tl.fromTo("#{gid} svg",{{opacity:0}},{{opacity:1,duration:0.45}},{t0:.3f});')
        _light_seat(c, gid, "L", p["accent"], t0)
        _light_seat(c, gid, "R", p["c1"], t0)
        c.tw(f'tl.fromTo("#{gid}labL,#{gid}labR",{{opacity:0}},{{opacity:0.55,duration:0.5}},{t0:.3f});')
        ta = c.t(s.get("fly_at", "One flies"), t0 - 0.5, 0.1)
        tb = c.t(s.get("mon_at", "monitors"), ta, 0.1)
        tn = c.t(s.get("next_at", "next flight"), tb, 0.1)
        tsw = c.t(s.get("swap_at", "swap"), tn, 0.15)
        c.tw(f'tl.fromTo("#{gid}b0",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.5,ease:"power3.out"}},{ta:.3f});')
        c.tw(f'tl.fromTo("#{gid}b1",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.5,ease:"power3.out"}},{tb:.3f});')
        c.rise(f"#{gid}nf", tn, 0.5, 10)
        # the badges trade seats along an arc
        c.tw(f'tl.to("#{gid}b0",{{keyframes:[{{x:175,y:-70,duration:0.45,ease:"power2.out"}},{{x:350,y:0,duration:0.45,ease:"power2.in"}}]}},{tsw:.3f});')
        c.tw(f'tl.to("#{gid}b1",{{keyframes:[{{x:-175,y:70,duration:0.45,ease:"power2.out"}},{{x:-350,y:0,duration:0.45,ease:"power2.in"}}]}},{tsw:.3f});')
