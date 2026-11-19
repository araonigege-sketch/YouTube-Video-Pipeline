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


def ladder(c, s, t0, t1):
    """The licence ladder: rungs light bottom-up as each is named.
    s.rungs: [{t: "Private pilot", sub: "40 h minimum", a: "phrase", color: c3}, ...] (bottom first);
    s.lit: index of a rung already lit when the page opens (re-entering the ladder later in the episode)."""
    p = c.p
    gid = c.nid("ld")
    rungs = s["rungs"]
    n = len(rungs)
    top, bot, x0, x1 = 170, 900, 640, 1280
    step = (bot - top) / max(1, n - 1)
    rails = _line(f"{gid}r1", f"M{x0} {bot + 60} L{x0} {top - 50}", "rgba(244,242,238,.45)", 3) + \
        _line(f"{gid}r2", f"M{x1} {bot + 60} L{x1} {top - 50}", "rgba(244,242,238,.45)", 3)
    bars, labs = [], []
    for k, r in enumerate(rungs):
        y = bot - k * step
        col = p.get(r.get("color", "c1"), r.get("color", p["c1"]))
        bars.append(f'<rect id="{gid}b{k}" x="{x0}" y="{y - 9}" width="{x1 - x0}" height="18" rx="9" '
                    f'fill="rgba(255,255,255,.06)" stroke="rgba(255,255,255,.18)" stroke-width="1.5"/>')
        labs.append(f'<div id="{gid}l{k}" style="position:absolute;left:{x1 + 60}px;top:{y - 44}px;opacity:0">'
                    f'<div style="font-family:\'Inter Display\';font-weight:800;font-size:46px;color:{col}">{html.escape(r["t"])}</div>'
                    f'<div style="font-weight:600;font-size:24px;letter-spacing:.16em;text-transform:uppercase;color:#C9CCD1;margin-top:6px">'
                    f'{html.escape(r.get("sub", ""))}</div></div>'
                    f'<div id="{gid}n{k}" style="position:absolute;right:{1920 - x0 + 50}px;top:{y - 26}px;opacity:0;'
                    f'font-family:\'Inter Display\';font-weight:800;font-size:44px;color:{col}">{k + 1:02d}</div>')
    title = (f'<div style="position:absolute;left:0;right:0;top:64px;text-align:center;font-weight:600;font-size:28px;'
             f'letter-spacing:.3em;text-transform:uppercase;color:#C9CCD1">{html.escape(s.get("title", "THE LADDER"))}</div>')
    c.add(gid, t0, t1, c.stage() + _svg(rails + "".join(bars)) + "".join(labs) + title, z=10, cls="page")
    c.draw(f"#{gid}r1", t0 + 0.05, 0.8, 1)
    c.draw(f"#{gid}r2", t0 + 0.15, 0.8, 1)
    c.tw(f'tl.fromTo("#{gid} rect",{{opacity:0,scaleX:0.6,transformOrigin:"50% 50%"}},'
         f'{{opacity:1,scaleX:1,duration:0.45,stagger:0.08,ease:"power2.out"}},{t0 + 0.4:.3f});')
    prev = None
    for k, r in enumerate(rungs):
        col = p.get(r.get("color", "c1"), r.get("color", p["c1"]))
        if k <= s.get("lit", -1):
            ta = t0 + 0.6
        elif "a" in r:
            ta = c.t(r["a"], t0, 0.1)
        else:
            continue                      # not reached yet in this appearance: stays unlit
        c.tw(f'tl.to("#{gid}b{k}",{{attr:{{fill:"{col}",stroke:"{col}"}},fillOpacity:0.85,duration:0.45}},{ta:.3f});')
        c.rise(f"#{gid}l{k}", ta, 0.5, 14)
        c.rise(f"#{gid}n{k}", ta, 0.5, 14)
        if prev is not None:
            c.tw(f'tl.to("#{gid}l{prev}",{{opacity:0.45,duration:0.4}},{ta:.3f});')
        prev = k


def hours(c, s, t0, t1):
    """The 1,500-hour wall. A track from 0 to s.need (1500); Jake's hours (s.have, 250) fill in mint; the gap glows coral
    with its size; optional s.months: the gap then fills month by month (s.per_month hours each) from s.fill_at."""
    p = c.p
    gid = c.nid("hr")
    need, have = s.get("need", 1500), s.get("have", 250)
    X0, X1, Y = 200, 1720, 560
    W = X1 - X0
    xh = X0 + W * have / need
    track = (f'<rect x="{X0}" y="{Y - 26}" width="{W}" height="52" rx="26" fill="rgba(255,255,255,.05)" stroke="rgba(255,255,255,.16)"/>'
             f'<rect id="{gid}have" x="{X0}" y="{Y - 26}" width="{xh - X0}" height="52" rx="26" fill="{p["c3"]}" transform-origin="{X0} {Y}"/>'
             f'<rect id="{gid}gap" x="{xh + 6}" y="{Y - 26}" width="{X1 - xh - 6}" height="52" rx="26" fill="{p["c4"]}" fill-opacity=".22" '
             f'stroke="{p["c4"]}" stroke-width="2" stroke-dasharray="10 8"/>')
    months = ""
    if s.get("months"):
        m = s["months"]
        per = s.get("per_month", 80)
        for k in range(m):
            xa = xh + 6 + (X1 - xh - 6) * k / m
            wa = (X1 - xh - 6) / m - 4
            months += f'<rect class="{gid}m" x="{xa:.1f}" y="{Y - 22}" width="{wa:.1f}" height="44" rx="8" fill="{p["c1"]}" opacity="0"/>'
    ticks = "".join(f'<text x="{X0 + W * v / need:.0f}" y="{Y + 84}" fill="#9AA0A6" font-family="Inter" font-weight="600" font-size="26" '
                    f'text-anchor="middle">{v:,}</text>' for v in (0, 500, 1000, 1500))
    lab_have = (f'<div id="{gid}lh" style="position:absolute;left:{xh - 200}px;width:400px;top:{Y - 170}px;text-align:center;opacity:0">'
                f'<div style="font-family:\'Inter Display\';font-weight:900;font-size:78px;color:{p["c3"]}">{have:,}</div>'
                f'<div style="font-weight:600;font-size:24px;letter-spacing:.18em;color:#C9CCD1">HOURS NOW</div></div>')
    lab_need = (f'<div id="{gid}ln" style="position:absolute;left:{X1 - 300}px;width:400px;top:{Y - 170}px;text-align:center;opacity:0">'
                f'<div style="font-family:\'Inter Display\';font-weight:900;font-size:78px;color:{p["accent"]}">{need:,}</div>'
                f'<div style="font-weight:600;font-size:24px;letter-spacing:.18em;color:#C9CCD1">HOURS NEEDED</div></div>')
    gap = need - have
    lab_gap = (f'<div id="{gid}lg" style="position:absolute;left:{(xh + X1) / 2 - 300}px;width:600px;top:{Y + 120}px;text-align:center;opacity:0">'
               f'<div style="font-family:\'Inter Display\';font-weight:900;font-size:96px;color:{p["c4"]}">{gap:,}</div>'
               f'<div style="font-weight:600;font-size:26px;letter-spacing:.18em;color:#C9CCD1">{html.escape(s.get("gap_label", "HOURS STILL TO GO"))}</div></div>')
    lab_m = ""
    if s.get("months"):
        lab_m = (f'<div id="{gid}lm" style="position:absolute;left:0;right:0;top:{Y + 300}px;text-align:center;opacity:0;'
                 f'font-weight:700;font-size:40px;color:{p["c1"]}">{s.get("per_month", 80)} hours a month · {s["months"]} months</div>')
    c.add(gid, t0, t1, c.stage() + _svg(track + months + ticks) + lab_have + lab_need + lab_gap + lab_m, z=10, cls="page")
    c.tw(f'tl.fromTo("#{gid} svg",{{opacity:0}},{{opacity:1,duration:0.4}},{t0:.3f});')
    th = _at(c, s["have_at"], t0) if "have_at" in s else t0 + 0.3
    c.tw(f'tl.fromTo("#{gid}have",{{scaleX:0}},{{scaleX:1,duration:0.8,ease:"power3.out"}},{th:.3f});')
    c.rise(f"#{gid}lh", th, 0.5, 14, 0.3)
    tn = _at(c, s["need_at"], t0) if "need_at" in s else th + 1.2
    c.rise(f"#{gid}ln", tn, 0.5, 14)
    c.tw(f'tl.fromTo("#{gid}gap",{{opacity:0}},{{opacity:1,duration:0.5}},{tn:.3f});')
    tg = _at(c, s["gap_at"], t0) if "gap_at" in s else tn + 1.2
    c.rise(f"#{gid}lg", tg, 0.6, 18)
    if s.get("months"):
        tf = _at(c, s["fill_at"], t0) if "fill_at" in s else tg + 1.5
        dur = max(1.0, (c.t(s["fill_end"], tf, 0.0) - tf) if "fill_end" in s else 3.0)
        c.tw(f'tl.to("#{gid} .{gid}m",{{opacity:0.9,duration:0.12,stagger:{dur / s["months"]:.3f}}},{tf:.3f});')
        c.rise(f"#{gid}lm", tf, 0.5, 12)


def _at(c, x, base):
    """Anchor: number = seconds after base; "phrase" = when it is spoken (searching from base)."""
    return base + float(x) if isinstance(x, (int, float)) else c.t(x, base, 0.1)


def bars(c, s, t0, t1):
    """Vertical bar chart drawn bar by bar. s.items: [{label, value, text, a, color}], s.max, s.title, s.note."""
    p = c.p
    gid = c.nid("bc")
    items = s["items"]
    n = len(items)
    vmax = s.get("max") or max(it["value"] for it in items) * 1.15
    X0, X1, Y0, Y1 = 360, 1560, 860, 250
    slot = (X1 - X0) / n
    bw = min(220, slot * 0.56)
    base = f'<line x1="{X0 - 40}" y1="{Y0}" x2="{X1 + 40}" y2="{Y0}" stroke="rgba(244,242,238,.35)" stroke-width="2"/>'
    rects, labs = [], []
    for k, it in enumerate(items):
        col = p.get(it.get("color", "c1"), it.get("color", p["c1"]))
        h = (Y0 - Y1) * it["value"] / vmax
        x = X0 + slot * k + (slot - bw) / 2
        rects.append(f'<rect id="{gid}r{k}" x="{x:.0f}" y="{Y0 - h:.0f}" width="{bw:.0f}" height="{h:.0f}" rx="14" '
                     f'fill="{col}" fill-opacity=".88" style="transform-origin:{x + bw / 2:.0f}px {Y0}px"/>')
        labs.append(f'<div id="{gid}v{k}" style="position:absolute;left:{x - 60:.0f}px;width:{bw + 120:.0f}px;top:{Y0 - h - 92:.0f}px;'
                    f'text-align:center;opacity:0;font-family:\'Inter Display\';font-weight:900;font-size:60px;color:{col}">'
                    f'{html.escape(it.get("text", str(it["value"])))}</div>'
                    f'<div id="{gid}l{k}" style="position:absolute;left:{x - 80:.0f}px;width:{bw + 160:.0f}px;top:{Y0 + 22}px;'
                    f'text-align:center;opacity:0;font-weight:600;font-size:30px;letter-spacing:.08em;color:#C9CCD1">'
                    f'{html.escape(it["label"])}</div>')
    title = (f'<div id="{gid}t" style="position:absolute;left:0;right:0;top:90px;text-align:center;font-weight:600;font-size:30px;'
             f'letter-spacing:.24em;text-transform:uppercase;color:#C9CCD1;opacity:0">{html.escape(s.get("title", ""))}</div>')
    note = (f'<div id="{gid}n" style="position:absolute;left:0;right:0;top:965px;text-align:center;font-weight:500;font-size:24px;'
            f'letter-spacing:.12em;color:#8A9096;opacity:0">{html.escape(s.get("note", ""))}</div>')
    c.add(gid, t0, t1, c.stage() + _svg(base + "".join(rects)) + "".join(labs) + title + note, z=10, cls="page")
    c.rise(f"#{gid}t", t0, 0.5, 10, 0.1)
    c.tw(f'tl.fromTo("#{gid} line",{{opacity:0}},{{opacity:1,duration:0.4}},{t0:.3f});')
    for k, it in enumerate(items):
        ta = _at(c, it["a"], t0) if "a" in it else t0 + 0.5 + 0.7 * k
        c.tw(f'tl.fromTo("#{gid}r{k}",{{scaleY:0}},{{scaleY:1,duration:0.8,ease:"power3.out"}},{ta:.3f});')
        c.rise(f"#{gid}v{k}", ta, 0.5, 14, 0.45)
        c.rise(f"#{gid}l{k}", ta, 0.4, 8)
    for k, it in enumerate(items):
        if "dim_at" in it:
            c.tw(f'tl.to("#{gid}r{k},#{gid}v{k}",{{opacity:0.35,duration:0.4}},{_at(c, it["dim_at"], t0):.3f});')
    if s.get("note"):
        c.rise(f"#{gid}n", _at(c, s.get("note_at", 1.0), t0), 0.5, 8)


def timeline(c, s, t0, t1):
    """Horizontal timeline; points light left to right. s.points: [{t, sub, a, color}], s.title, s.total {t, sub, a}."""
    p = c.p
    gid = c.nid("tl")
    pts = s["points"]
    n = len(pts)
    X0, X1, Y = 230, 1690, 520
    xs = [X0 + (X1 - X0) * k / max(1, n - 1) for k in range(n)]
    track = f'<line x1="{X0}" y1="{Y}" x2="{X1}" y2="{Y}" stroke="rgba(244,242,238,.16)" stroke-width="6" stroke-linecap="round"/>'
    segs = "".join(_line(f"{gid}s{k}", f"M{xs[k]} {Y} L{xs[k + 1]} {Y}", p.get(pts[k + 1].get("color", "c1"), p["c1"]), 6)
                   for k in range(n - 1))
    dots = "".join(f'<circle id="{gid}d{k}" cx="{xs[k]:.0f}" cy="{Y}" r="18" fill="{p.get(pt.get("color", "c1"), p["c1"])}" '
                   f'style="transform-origin:{xs[k]:.0f}px {Y}px" opacity="0"/>' for k, pt in enumerate(pts))
    labs = "".join(
        f'<div id="{gid}l{k}" style="position:absolute;left:{xs[k] - 190:.0f}px;width:380px;top:{Y - 150}px;text-align:center;opacity:0">'
        f'<div style="font-family:\'Inter Display\';font-weight:900;font-size:66px;color:{p.get(pt.get("color", "c1"), p["c1"])}">{html.escape(pt["t"])}</div></div>'
        f'<div id="{gid}u{k}" style="position:absolute;left:{xs[k] - 190:.0f}px;width:380px;top:{Y + 46}px;text-align:center;opacity:0;'
        f'font-weight:600;font-size:26px;line-height:1.3;letter-spacing:.06em;color:#C9CCD1">{html.escape(pt.get("sub", ""))}</div>'
        for k, pt in enumerate(pts))
    title = (f'<div id="{gid}t" style="position:absolute;left:0;right:0;top:110px;text-align:center;font-weight:600;font-size:30px;'
             f'letter-spacing:.24em;text-transform:uppercase;color:#C9CCD1;opacity:0">{html.escape(s.get("title", ""))}</div>')
    total = ""
    if s.get("total"):
        tt = s["total"]
        total = (f'<div id="{gid}T" style="position:absolute;left:0;right:0;top:770px;text-align:center;opacity:0">'
                 f'<div style="font-family:\'Inter Display\';font-weight:900;font-size:110px;color:{p["accent"]}">{html.escape(tt["t"])}</div>'
                 f'<div style="font-weight:600;font-size:28px;letter-spacing:.22em;text-transform:uppercase;color:#E8E6E1;margin-top:8px">'
                 f'{html.escape(tt.get("sub", ""))}</div></div>')
    c.add(gid, t0, t1, c.stage() + _svg(track + segs + dots) + labs + title + total, z=10, cls="page")
    c.rise(f"#{gid}t", t0, 0.5, 10, 0.1)
    c.tw(f'tl.fromTo("#{gid} line",{{opacity:0}},{{opacity:1,duration:0.4}},{t0:.3f});')
    prev_t = t0
    for k, pt in enumerate(pts):
        ta = _at(c, pt["a"], prev_t - 0.5) if "a" in pt else t0 + 0.4 + 0.9 * k
        if k:
            c.draw(f"#{gid}s{k - 1}", ta - 0.35, 0.45, 1)
        c.tw(f'tl.fromTo("#{gid}d{k}",{{opacity:0,scale:0.2}},{{opacity:1,scale:1,duration:0.45,ease:"back.out(2)"}},{ta:.3f});')
        c.rise(f"#{gid}l{k}", ta, 0.5, 14)
        c.rise(f"#{gid}u{k}", ta, 0.5, 10, 0.15)
        prev_t = ta
    if s.get("total"):
        c.rise(f"#{gid}T", _at(c, s["total"]["a"], prev_t - 0.5) if "a" in s["total"] else prev_t + 1.0, 0.7, 20)
