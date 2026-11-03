"""Silk Road episode: one-off notebook pages used in the cold open (ported from silk_full.py demo_page)."""

def page_map(c, t0, t1):
    pid = c.nid("pg")
    route = "M240,700 C380,640 420,520 560,540 S760,700 900,620 S1120,420 1260,470 S1480,620 1640,520"
    mtn = "".join(f'<path d="M{x},{y} l40,-70 l40,70" stroke="{c.INK}" stroke-width="5" fill="none" stroke-linejoin="round"/>' for x, y in ((980, 420), (1040, 400), (1100, 430)))
    dunes = "".join(f'<path d="M{x},{y} q30,-24 60,0 q30,-24 60,0" stroke="{c.INK}" stroke-width="4" fill="none" opacity=".6"/>' for x, y in ((420, 760), (640, 470), (720, 760), (1300, 640), (1500, 700)))
    svg = (f'<svg class="abs" style="left:0;top:0" width="1920" height="1080" viewBox="0 0 1920 1080">{dunes}{mtn}'
           f'<path id="{pid}r" d="{route}" stroke="{c.RED}" stroke-width="9" fill="none" stroke-dasharray="22 18" stroke-linecap="round"/>'
           f'<path id="{pid}rm" d="{route}" stroke="{c.PAPER}" stroke-width="16" fill="none" stroke-dasharray="2400" stroke-dashoffset="0"/>'
           f'<circle cx="240" cy="700" r="16" fill="{c.INK}"/><circle cx="1640" cy="520" r="16" fill="{c.INK}"/></svg>')
    inner = (svg + c.hw("Central Asia", 250, 150, 96, c.INK, f"{pid}t") + f'<div id="{pid}u" class="abs rule2" style="left:250px;top:262px;width:520px"></div>'
             + c.hw("desert", 430, 790, 54) + c.hw("more desert", 610, 400, 54) + c.hw("mountains", 1040, 300, 54) + c.hw("…more desert", 1360, 720, 54)
             + c.hw("≈ 4 months", 760, 860, 110, c.RED, f"{pid}m"))
    c.els.append(c.page(t0, t1, inner, pid)); c.fade_in(f"#{pid}", t0)
    c.write_on(f"#{pid}t", t0 + 0.2, 0.7); c.tw(f'tl.fromTo("#{pid}u",{{scaleX:0,transformOrigin:"0% 50%"}},{{scaleX:1,duration:0.4}},{t0 + 0.8:.3f});')
    c.tw(f'tl.fromTo("#{pid}rm",{{strokeDashoffset:0}},{{strokeDashoffset:-2400,duration:{min(2.4, t1 - t0 - 0.6):.2f},ease:"power1.inOut"}},{t0 + 0.3:.3f});')
    c.write_on(f"#{pid}m", c.T("four months") - 0.05, 0.7)

def page_chain(c, t0, t1):
    pid = c.nid("pg"); xs = [260, 480, 700, 960, 1220, 1440, 1660]; figs = ""
    for k, x in enumerate(xs):
        far = k in (0, 6); me = k == 3
        figs += (f'<g id="{pid}f{k}" opacity="{0.35 if far else 1}"><circle cx="{x}" cy="500" r="{46 if me else 38}" fill="none" stroke="{c.INK}" stroke-width="6" {"stroke-dasharray=\"10 10\"" if far else ""}/>'
                 f'<path d="M{x},{546 if me else 538} L{x},{650} M{x - 50},{590} L{x + 50},{590} M{x},{650} L{x - 40},{720} M{x},{650} L{x + 40},{720}" stroke="{c.INK}" stroke-width="6" stroke-linecap="round" {"stroke-dasharray=\"10 10\"" if far else ""}/></g>')
        if k < 6:
            figs += f'<path class="{pid}ar" id="{pid}a{k}" d="M{x + 60},{560} L{xs[k + 1] - 60},{560} M{xs[k + 1] - 80},{545} L{xs[k + 1] - 60},{560} L{xs[k + 1] - 80},{575}" stroke="{c.INK}" stroke-width="5" fill="none" stroke-linecap="round" stroke-dasharray="400" stroke-dashoffset="400"/>'
    figs += f'<ellipse id="{pid}ring" cx="960" cy="590" rx="130" ry="190" fill="none" stroke="{c.RED}" stroke-width="7" stroke-dasharray="1100" stroke-dashoffset="1100"/>'
    inner = (f'<svg class="abs" style="left:0;top:0" width="1920" height="1080" viewBox="0 0 1920 1080">{figs}</svg>'
             + c.hw("Who he never met", 250, 150, 96, c.INK, f"{pid}t") + f'<div id="{pid}u" class="abs rule2" style="left:250px;top:262px;width:640px"></div>'
             + c.hw("our merchant", 860, 780, 60, c.RED, f"{pid}me") + c.hw("the maker", 170, 760, 54, c.INK, f"{pid}mk", "opacity:.7")
             + c.hw("the buyer", 1580, 760, 54, c.INK, f"{pid}by", "opacity:.7") + c.hw("?", 470, 380, 80, c.RED, f"{pid}q1") + c.hw("?", 1430, 380, 80, c.RED, f"{pid}q2"))
    c.els.append(c.page(t0, t1, inner, pid)); c.fade_in(f"#{pid}", t0)
    c.write_on(f"#{pid}t", t0 + 0.15, 0.7); c.tw(f'tl.fromTo("#{pid}u",{{scaleX:0,transformOrigin:"0% 50%"}},{{scaleX:1,duration:0.4}},{t0 + 0.75:.3f});')
    tm = c.T("made his goods"); tb = c.T("finally buys")
    for k in range(3): c.draw(f"#{pid}a{2 - k}", tm - 0.6 + k * 0.25, 0.3, 400)
    for k in range(3, 6): c.draw(f"#{pid}a{k}", tb - 0.9 + (k - 3) * 0.25, 0.3, 400)
    c.draw(f"#{pid}ring", t0 + 0.6, 0.6, 1100); c.write_on(f"#{pid}me", t0 + 1.0, 0.5)
    c.write_on(f"#{pid}mk", tm, 0.5); c.write_on(f"#{pid}by", tb, 0.5)
    c.tw(f'tl.fromTo("#{pid}q1",{{opacity:0,scale:0.4}},{{opacity:1,scale:1,duration:0.3,ease:"back.out(2)"}},{tm + 0.3:.3f});')
    c.tw(f'tl.fromTo("#{pid}q2",{{opacity:0,scale:0.4}},{{opacity:1,scale:1,duration:0.3,ease:"back.out(2)"}},{tb + 0.3:.3f});')

def page_list(c, t0, t1):
    pid = c.nid("pg"); items = ["silk", "spices", "gold", "glass", "everybody gets rich"]
    inner = c.hw("The story we're told", 250, 150, 96, c.INK, f"{pid}t") + f'<div id="{pid}u" class="abs rule2" style="left:250px;top:262px;width:760px"></div>'
    for k, it in enumerate(items):
        inner += c.hw(("☐ " if k < 4 else "→ ") + it, 330, 330 + k * 112, 80, c.INK if k < 4 else c.RED, f"{pid}i{k}")
        if k < 4: inner += c.hw("✓", 336, 318 + k * 112, 84, c.RED, f"{pid}c{k}", "opacity:0")
    inner += c.hw("a shopping list?", 1180, 640, 76, c.RED, f"{pid}sl", "transform:rotate(-6deg)")
    c.els.append(c.page(t0, t1, inner, pid)); c.fade_in(f"#{pid}", t0)
    c.write_on(f"#{pid}t", t0 + 0.2, 0.8); c.tw(f'tl.fromTo("#{pid}u",{{scaleX:0,transformOrigin:"0% 50%"}},{{scaleX:1,duration:0.4}},{t0 + 0.9:.3f});')
    ts = c.T("shopping list") - 0.6
    for k in range(5): c.write_on(f"#{pid}i{k}", ts + k * 0.32, 0.4)
    for k in range(4): c.tw(f'tl.set("#{pid}c{k}",{{opacity:1}},{ts + 1.8 + k * 0.18:.3f});')
    c.write_on(f"#{pid}sl", c.T("shopping list") + 0.2, 0.6)

def page_eastwest(c, t0, t1):
    pid = c.nid("pg")
    arr_w = f'M1500,470 C1200,420 760,420 430,470 M460,445 L430,470 L462,494'
    arr_e = f'M430,620 C760,670 1200,670 1500,620 M1470,596 L1500,620 L1468,646'
    inner = (f'<svg class="abs" style="left:0;top:0" width="1920" height="1080" viewBox="0 0 1920 1080">'
             f'<path id="{pid}w" d="{arr_w}" stroke="{c.RED}" stroke-width="9" fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="1300" stroke-dashoffset="1300"/>'
             f'<path id="{pid}e" d="{arr_e}" stroke="{c.INK}" stroke-width="9" fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="1300" stroke-dashoffset="1300"/></svg>'
             + c.hw("WEST", 150, 500, 88, c.INK, f"{pid}lw") + c.hw("EAST", 1560, 500, 88, c.INK, f"{pid}le")
             + c.hw("(Rome)", 170, 600, 56, c.INK, f"{pid}lr", "opacity:.75") + c.hw("(China)", 1575, 600, 56, c.INK, f"{pid}lc", "opacity:.75")
             + c.hw("silk", 880, 330, 84, c.RED, f"{pid}s") + c.hw("spices · gold · glass", 700, 690, 76, c.INK, f"{pid}g")
             + c.hw("A trade route.", 250, 150, 96, c.INK, f"{pid}t") + f'<div id="{pid}u" class="abs rule2" style="left:250px;top:262px;width:600px"></div>'
             + c.hw("goods in, goods out", 700, 850, 64, c.RED, f"{pid}gi"))
    c.els.append(c.page(t0, t1, inner, pid)); c.fade_in(f"#{pid}", t0)
    c.write_on(f"#{pid}lw", t0 + 0.1, 0.4); c.write_on(f"#{pid}le", t0 + 0.1, 0.4); c.write_on(f"#{pid}lr", t0 + 0.4, 0.4); c.write_on(f"#{pid}lc", t0 + 0.4, 0.4)
    c.draw(f"#{pid}w", c.T("Silk going") - 0.05, 0.9, 1300); c.write_on(f"#{pid}s", c.T("Silk going") + 0.2, 0.4)
    c.draw(f"#{pid}e", c.T("Spices") - 0.05, 0.9, 1300); c.write_on(f"#{pid}g", c.T("Spices") + 0.1, 1.0)
    c.write_on(f"#{pid}t", c.T("A trade route") - 0.05, 0.7); c.tw(f'tl.fromTo("#{pid}u",{{scaleX:0,transformOrigin:"0% 50%"}},{{scaleX:1,duration:0.35}},{c.T("A trade route") + 0.6:.3f});')
    c.write_on(f"#{pid}gi", c.T("Goods in") - 0.05, 0.8)
