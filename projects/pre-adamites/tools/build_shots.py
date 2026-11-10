#!/usr/bin/env python3
"""Build film2/shots.js for the Case File player from the narration's word timings.

Each shot is anchored to the words it illustrates: ("anchor phrase", type, params). Strings in params that start
with "@" are other phrases, resolved to their time after the shot's anchor ("@phrase|+0.3" adds an offset).
Long still shots are split into a wide view and a closer detail so the frame changes every ~3-5 s.

  python3 tools/build_shots.py            # writes film2/shots.js and prints a pacing report
"""
import json, re, sys, os

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = json.load(open(f'{P}/vo/words.json'))
for i in range(1, len(W)):
    if W[i]['s'] < W[i - 1]['s']: W[i]['s'] = W[i - 1]['s']
norm = lambda s: re.sub(r"[^\w']", "", s.lower().replace('’', "'").replace('è', 'e').replace('ö', 'o'))
TOK = [norm(w['w']) for w in W]
SIZES = json.load(open(f'{P}/film2/img_sizes.json'))
NARR_END = W[-1]['e']
END = round(NARR_END + 3.6, 2)

def find(phrase, after):
    p = [norm(x) for x in phrase.split() if norm(x)]
    for i in range(len(TOK)):
        if W[i]['s'] >= after - 0.01 and TOK[i:i + len(p) - 1] == p[:-1] and i + len(p) - 1 < len(TOK) and TOK[i + len(p) - 1].startswith(p[-1]): return W[i]['s']
    raise SystemExit(f'phrase not found after {after:.1f}s: {phrase!r}')

# ---------------- layout helpers ----------------
def dims(img, h=None, maxw=1500, maxh=880):
    w0, h0 = SIZES[img]; ar = w0 / h0
    if h is None: h = maxh if ar < 1.25 else min(maxh, maxw / ar)
    return h, h * ar

def sheet(a, img, u=.5, v=.5, z=(1.0, 1.08), kind='print', arrive=(0, 1), h=None, **k):
    hh, ww = dims(img, h)
    x, y = k.pop('x', 960), k.pop('y', 545)
    fx, fy = x + (u - .5) * ww * .55, y + (v - .5) * hh * .55
    d = dict(img=img, h=hh, x=x, y=y, kind=kind, arrive=list(arrive) if arrive else None,
             cam=dict(z=list(z), x=[x, fx], y=[y, fy]), rot=k.pop('rot', 0), focus=[u, v], **k)
    return (a, 'sheet', d)

def card(a, text=None, lines=None, **k):
    d = dict(k)
    if text: d['text'] = text
    if lines: d['lines'] = [dict(text=l[0], at=l[1], **(l[2] if len(l) > 2 else {})) if isinstance(l, tuple) else dict(text=l) for l in lines]
    return (a, 'card', d)

def lst(a, title, sub, items, **k):
    return (a, 'list', dict(title=title, sub=sub, items=[dict(text=i[0], at=i[1], **(i[2] if len(i) > 2 else {})) for i in items], **k))

def compare(a, title, sub, cols, **k):
    return (a, 'compare', dict(title=title, sub=sub, cols=cols, **k))

def col(head, at, items=(), **k):
    return dict(head=head, at=at, items=[dict(text=i[0], at=i[1], **(i[2] if len(i) > 2 else {})) for i in items], **k)

def spread(a, items, **k):
    return (a, 'spread', dict(items=items, **k))

def it(img, at, x, y, h, rot=0, dir=(0, 1), cap=None):
    d = dict(img=img, at=at, x=x, y=y, h=dims(img, h)[0], rot=rot, dir=list(dir))
    if cap: d['cap'] = dict(lines=cap)
    return d

def tl(a, spans, markers=(), **k):
    return (a, 'timeline', dict(spans=spans, markers=[dict(m) for m in markers], **k))

def mk(bp, text, sub, at, **k): return dict(bp=bp, text=text, sub=sub, at=at, **k)

EU = lambda a, **k: (a, 'map_eu', k)
WORLD = lambda a, **k: (a, 'map_world', k)
zoom_to = lambda pin, z, world=True: None

def wcam(k, z0, z1):  # world-map camera centred on a pin
    px, py = json.load(open(f'{P}/film2/world.json'))['pins'][k] if False else (None, None)

# ---------------- the shot list ----------------
S = []
add = S.append
SIB = '1655'

# HOOK
add(sheet("Hey there!", 'sunday', .5, .4, (1.04, 1.14), strip='THE SUNDAY SCHOOL QUESTION'))
add(sheet("Adam and Eve have two sons", 'durer_ae', .5, .45, (1.0, 1.12), arrive=(1, 0)))
add(sheet("Cain kills Abel", 'durer_cain', .45, .3, (1.05, 1.25), arrive=(-1, 0)))
add(('So now there are three people on earth', 'tree', dict(g=dict(adam=None, eve=None, sons=None, kill=None), arrive=[0, 1], cam=dict(z=[1.0, 1.03], x=[960, 900], y=[540, 520]))))
add(sheet("Then Cain gets scared", 'cain_flight', .5, .35, (1.0, 1.15), arrive=(0, -1)))
add(card("He tells God", text='“Anyone who finds me will kill me!”', italic=True, size=78, cite=dict(text='GENESIS 4:14')))
add(card("Wait. Anyone?", lines=[('Anyone?', None, dict(size=120)), ('Who?', '@Who?', dict(size=120, red=True))], gap=170))
add(sheet("Then Cain gets married", 'family_cain', .62, .45, (1.0, 1.12), arrive=(1, 0), ring=[dict(u=.62, v=.42, at='@To who', rx=210, ry=170)]))
add(sheet("Then he builds a city", 'kasbah', .5, .5, (1.0, 1.1), stamp=dict(at='@For who', text='FOR WHO?', size=70, x=1330, y=820, onDesk=True)))
add(sheet("In 1655, a French scholar", 'pa_title', .5, .3, (1.08, 1.0), kind='page', strip='AMSTERDAM · 1655'))
add(sheet("named Isaac La Peyrère", 'pa_hand', .55, .05, (2.1, 1.7), kind='page', arrive=None, x=960, y=560, h=1000,
          underline=[dict(u0=.27, u1=.84, v=.033, at='@Isaac')]))
add(sheet("And his answer was", 'pa_hand', .6, .48, (1.12, 1.12), kind='page', arrive=None, x=960, y=560, h=1000,
          loupe=dict(u=.6, v=.483, at='@people before Adam', r=240, m=1.6),
          caption=dict(head='TRANSLATION', lines=['"the first men,', ' created before Adam"'], at='@people before Adam|+0.6', x=1290, y=640, size=26)))
add(EU("His book got burned", pins=[dict(k='amsterdam', name='Amsterdam', at='@His book|-0.1'), dict(k='paris', name='Paris', side='l', at='@burned', active=True)],
       routes=[dict(a='amsterdam', b='paris', at='@His book', dur=.8, bend=-.25)], stamps=[dict(k='paris', at='@burned|+0.2', text='BURNED', sub='PARIS · 1655', dx=-40, dy=74)],
       years=[['@His book', 1655]], cam=dict(z=[2.3, 2.1], x=[880, 840], y=[330, 380])))
add(sheet("He got arrested", 'brussels', .55, .45, (1.0, 1.07), arrive=(1, 0), stamp=dict(at='@arrested|+0.1', text='ARRESTED', sub='BRUSSELS · 1656', size=60, x=1350, y=780)))
add(EU("And he ended up in Rome", pins=[dict(k='amsterdam', name='Amsterdam', at=-1), dict(k='paris', name='Paris', side='l', at=-1), dict(k='brussels', name='Brussels', at='@And he ended'),
       dict(k='rome', name='Rome', at='@Rome', active=True)], routes=[dict(a='amsterdam', b='paris', at=-2, dur=.5, bend=-.25), dict(a='brussels', b='rome', at='@ended up', dur=1.0, bend=.12)],
       stamps=[dict(k='paris', at=-1, text='BURNED', sub='PARIS · 1655', dx=-40, dy=74)], years=[['@And he ended', 1656], ['@Rome', 1657]], cam=dict(z=[1.9, 1.22], x=[905, 1030], y=[400, 590])))
add(sheet("taking it all back", 'medal', .5, .5, (1.05, 1.16), kind='disc', arrive=(0, -1), x=840, h=1250, o=dict(r=.316, dx=.016, dy=-.016),
          stamp=dict(at='@Pope Alexander', text='RECANTED', sub='ROME · 1657', size=58, x=1440, y=800, onDesk=True)))
add(sheet("But here's the twist. Today", 'skull', .5, .45, (1.0, 1.1), arrive=(-1, 0)))
add(tl("long before the date tradition gave for Adam", [[0, 15000]], [mk(6000, 'Adam, by tradition', 'c. 6,000 yrs ago', '@long before', red=True, up=260)], sliver='@long before'))
add(tl("Hundreds of thousands of years before", [[0, 15000], ['@Hundreds', 305000]], [mk(6000, 'Adam, by tradition', 'c. 6,000 yrs ago', -1, red=True, up=260, until='@Hundreds'),
    mk(300000, 'Homo sapiens', 'earliest fossils · c. 300,000 yrs ago', '@Hundreds|+1.2', side='right', up=230)], sliver=-1))
add(sheet("So who were they?", 'hands', .5, .4, (1.0, 1.12), arrive=(0, 1)))
add(sheet("Does that mean Adam and Eve weren't", 'rembrandt_ae', .5, .45, (1.0, 1.1), arrive=(1, 0)))
add(spread("And what do Christians, Muslims and Jews", [it('bible_leaf', '@Christians', 480, 540, 760, -.03), it('quran_cle', '@Muslims', 960, 560, 560, .02, (0, -1)), it('torah_curtain', '@Jews', 1440, 540, 720, .03, (1, 0))]))
add(lst("In this video, we'll look at", 'In this file', 'WHAT WE’LL EXAMINE', [('What the Bible and the Qur’an say', '@what the Bible'), ('What the bones and the DNA show', '@what the bones'), ('How three faiths make it fit', '@how all three faiths')], y0=360, gap=190))
add(card("Let's get into it", kicker='CASE FILE NO. 1', text='Who were the humans before Adam and Eve?', size=74, stamp=dict(at='@into it|+0.1', text='OPEN', size=62, x=1450, y=820)))
# WHY IT MATTERS
add(card("Okay, first, why does this even matter?", text='Why does this matter?', size=96))
add(sheet("Because Adam isn't just a name", 'jesse', .5, .3, (1.0, 1.12), arrive=(1, 0)))
add(sheet("For Christians, Adam is where sin entered", 'fall', .5, .45, (1.0, 1.12), arrive=(-1, 0), strip='CHRISTIANITY'))
add(sheet("The apostle Paul builds", 'paul_flinck', .45, .35, (1.0, 1.12), arrive=(0, 1)))
add(sheet("For Muslims, Adam is the first human", 'quran_double', .5, .5, (1.0, 1.08), arrive=(1, 0), strip='ISLAM'))
add(sheet("He's the one God taught the names", 'naming', .5, .45, (1.0, 1.15), arrive=(0, -1)))
add(sheet("And for Jews, he's where the human story", 'torah_finials', .5, .5, (1.0, 1.1), arrive=(-1, 0), strip='JUDAISM'))
add(compare("So if there were people before Adam", 'Three faiths, one Adam', 'WHAT ADAM MEANS', [
    col('Christianity', '@So if there', [('where sin entered the world', '@So if there|+0.3')]), col('Islam', '@So if there|+0.6', [('the first human, the first prophet', '@So if there|+0.9')]),
    col('Judaism', '@So if there|+1.2', [('where the human story begins', '@So if there|+1.5')])], stamp=dict(at='@What exactly was Adam', text='WHAT WAS ADAM?', size=52)))
# GENESIS
add(sheet("Let's start with the story itself", 'di_paolo', .5, .5, (1.0, 1.1), arrive=(0, 1), strip='GENESIS 1–4'))
add(sheet("In Genesis, God forms a man", 'creation_adam', .45, .55, (1.0, 1.15), arrive=(1, 0)))
add(sheet("He puts him in a garden", 'bosch_paradise', .5, .5, (1.0, 1.1), arrive=(-1, 0)))
add(sheet("Then He makes a woman", 'creation_eve2', .5, .45, (1.0, 1.15), arrive=(0, -1)))
add(sheet("The man later names her Eve", 'cranach_paradise', .5, .5, (1.0, 1.1), arrive=(1, 0)))
add(sheet("They eat the forbidden fruit", 'durer_ae', .5, .3, (1.1, 1.3), arrive=None))
add(sheet("They get kicked out of Eden", 'durer_expulsion', .5, .45, (1.0, 1.12), arrive=(-1, 0)))
add(('They have two sons', 'tree', dict(g=dict(adam=-1, eve=-1, sons='@two sons|+0.2'), arrive=[0, 1], cam=dict(z=[1.0, 1.02], x=[960, 900], y=[540, 520]))))
add(sheet("And then Cain kills his brother", 'cranach_cain', .5, .4, (1.0, 1.14), arrive=(1, 0)))
add(sheet("God punishes Cain", 'kain_swan', .5, .45, (1.0, 1.12), arrive=(0, -1)))
add(sheet("And that's when Cain says this", 'giordano_cain', .5, .45, (1.0, 1.1), arrive=(-1, 0)))
add(card("“You have banished me", lines=[('“You have banished me from the land and from your presence;', None, dict(size=56, italic=True)), ('you have made me a homeless wanderer.', '@you have made', dict(size=56, italic=True)),
         ('Anyone who finds me will kill me!”', '@Anyone who finds', dict(size=64, italic=True, red=True))], gap=110, cite=dict(text='GENESIS 4:14', at='@Anyone who finds')))
add(sheet("Notice what God does next", 'castiglione', .5, .4, (1.0, 1.12), arrive=(1, 0)))
add(card("He doesn't say, “Relax", text='“Relax, Cain, there’s nobody out there.”', italic=True, size=70, stamp=dict(at='@Instead|-0.1', text='NOT IN THE TEXT', size=44)))
add(sheet("Instead, He puts a mark on Cain", 'cain_flight', .5, .3, (1.2, 1.4), arrive=None))
add(sheet("And then the story keeps going", 'bible_leaf', .5, .3, (1.0, 1.15), arrive=(0, 1)))
add(card("“So Cain left the Lord's presence", lines=[('“So Cain left the Lord’s presence and settled in the land of Nod, east of Eden.', None, dict(size=52, italic=True)),
         ('Cain had sexual relations with his wife…', '@Cain had sexual', dict(size=52, italic=True, red=True)), ('Then Cain founded a city, which he named Enoch.”', '@Then Cain founded', dict(size=52, italic=True, red=True))],
         gap=130, cite=dict(text='GENESIS 4:16–17', at='@Then Cain founded')))
add(('So, in a few sentences, we get a wife', 'tree', dict(g=dict(adam=-1, eve=-1, sons=-1, kill=-1, dim=-1, hi=-1, q=['@a wife nobody|-0.2', '@a wife nobody', '@and a city']), cam=dict(z=[1.0, .94], x=[800, 820], y=[560, 600]))))
add(sheet("And cities need people", 'kasbah', .3, .55, (1.15, 1.3), arrive=None))
add(sheet("Now, you might be thinking", 'jami', .5, .3, (1.0, 1.12), arrive=(1, 0)))
add(sheet("People have been asking about Cain's wife", 'family_cain', .62, .42, (1.1, 1.25), arrive=(0, 1)))
add(lst("And there are three main answers", 'Three answers', 'WHO WAS OUT THERE?', [('The family answer', '@three main|+0.2'), ('A wider population', '@three main|+0.6'), ('An older story, woven in', '@three main|+1.0')], y0=380, gap=200))
# THREE ANSWERS
add(lst("The first one is the family answer", 'Three answers', 'ANSWER 1', [('The family answer', -1, dict(red=True)), ('A wider population', -1, dict(dim=-1)), ('An older story, woven in', -1, dict(dim=-1))], y0=380, gap=200, arrive=None))
add(('A chapter later, Genesis says', 'tree', dict(g=dict(adam=-1, eve=-1, sons=-1, kill=-1, others='@other sons'), cam=dict(z=[1.0, .95], x=[900, 960], y=[540, 560]))))
add(sheet("So Cain married one of his sisters", 'family_cain', .4, .5, (1.0, 1.1), arrive=(1, 0)))
add(card("Yes, that sounds strange", text='Strange to us today.', size=90))
add(sheet("But in the story, the first family", 'jami', .5, .82, (1.05, 1.3), arrive=(0, 1)))
add(sheet("An ancient Jewish book called Jubilees", 'ethiopic', .5, .45, (1.0, 1.12), arrive=(-1, 0),
          caption=dict(lines=['Jubilees survives complete', 'only in Ge‘ez, the church', 'language of Ethiopia'], at='@Jubilees|+0.5', x=1250, y=720)))
add(card("even gives Cain's wife a name", kicker='CAIN’S WIFE, IN JUBILEES', lines=[('Awan', '@Awan', dict(size=170))], cite=dict(text='JUBILEES 4:9', at='@Awan')))
add(sheet("Islamic tradition tells a very similar story", 'jami', .5, .85, (1.25, 1.45), arrive=None, strip='ISLAMIC TRADITION'))
add(compare("Early Muslim commentators said Eve gave birth to twins", 'Twins every time', 'EARLY MUSLIM COMMENTATORS', [
    col('Cain', '@twins|+0.2', [('+ his twin sister', '@a boy and a girl')]), col('Abel', '@twins|+0.5', [('+ his twin sister', '@a boy and a girl|+0.3')])],
    stamp=dict(at='@Each son', text='SWAP', sub='EACH MARRIES THE OTHER’S TWIN', size=50, x=960, y=830, rot=-.04)))
add(sheet("And in their version", 'kain_doodt', .5, .45, (1.0, 1.15), arrive=(1, 0)))
add(lst("The second answer is simpler", 'Three answers', 'ANSWER 2', [('The family answer', -1, dict(dim=-1)), ('A wider population', -1, dict(red=True)), ('An older story, woven in', -1, dict(dim=-1))], y0=380, gap=200, arrive=None))
add(sheet("Maybe the story just assumes", 'eden_animals', .5, .5, (1.0, 1.12), arrive=(0, 1)))
add(lst("And the third answer comes from scholars", 'Three answers', 'ANSWER 3', [('The family answer', -1, dict(dim=-1)), ('A wider population', -1, dict(dim=-1)), ('An older story, woven in', -1, dict(red=True))], y0=380, gap=200, arrive=None))
add(sheet("They think the story of Cain might have started", 'bible_leaf', .5, .6, (1.1, 1.25), arrive=(1, 0)))
add(card("Later in the Bible, there's a group called the Kenites", kicker='LATER IN THE BIBLE', lines=[('the Kenites', None, dict(size=110)), ('named after Cain?', '@may come from Cain', dict(size=60, italic=True, red=True))], gap=150))
add(sheet("So the strangers and the city", 'hollar_eden', .5, .5, (1.0, 1.12), arrive=(-1, 0)))
add(card("And here's a fun detail", kicker='HEBREW', lines=[('עִיר', '@The Hebrew word', dict(size=150)), ('ʿîr · “city” · could be a small fortified settlement', '@can mean something', dict(size=40, mono=True))], gap=170))
add(sheet("Think less New York", 'kasbah', .5, .5, (1.0, 1.14), arrive=(0, 1)))
add(lst("So which one is right?", 'Three answers', 'THE TEXT DOESN’T SAY', [('The family answer', -1), ('A wider population', -1), ('An older story, woven in', -1)], y0=380, gap=200, arrive=None,
        stamp=dict(at='@Genesis doesn', text='OPEN QUESTION', size=52)))
add(sheet("But the questions were there", 'sunday', .3, .5, (1.1, 1.25), arrive=(0, 1)))
# LA PEYRERE AND PAUL
add(sheet("La Peyrère went with the second answer", 'pa_title', .5, .5, (1.0, 1.08), kind='page', strip='LA PEYRÈRE’S CLUE'))
add(sheet("And the first thing that made him suspicious", 'paul_met', .5, .3, (1.0, 1.12), arrive=(1, 0)))
add(sheet("It was in a letter from Paul", 'bible_epistle', .5, .25, (1.05, 1.25), arrive=(0, 1)))
add(card("In Romans chapter five", lines=[('“sin was in the world before the law was given”', '@Paul says sin', dict(size=58, italic=True)), ('“death reigned from Adam to Moses”', '@death ruled', dict(size=58, italic=True, red=True))],
         gap=150, cite=dict(text='ROMANS 5:13–14', at='@Paul says sin')))
add(sheet("La Peyrère read that and thought", 'pa_hand', .5, .5, (1.0, 1.08), kind='page', arrive=(1, 0), ring=[dict(u=.5, v=.49, at='@does that mean', rx=260, ry=60)]))
add(compare("Most readers, then and now", 'Reading Romans 5', 'TWO READINGS', [
    col('La Peyrère', '@Most readers|-0.1', [('people sinned before Adam', '@Most readers')]), col('Most readers', '@Most readers|+0.4', [('“the law” = the law of Moses', '@They say Paul'), ('death ruled even before Moses', '@death ruled even')])]))
add(sheet("So La Peyrère was pretty much on his own", 'pa_title', .5, .3, (1.1, 1.2), kind='page', arrive=None, stamp=dict(at='@easy to shoot down', text='DISMISSED', size=72, x=1000, y=500, rot=-.15)))
add(sheet("But he noticed something else", 'di_paolo', .3, .5, (1.15, 1.3), arrive=(0, 1)))
add(compare("Genesis tells the creation of humans twice", 'Two creation accounts', 'GENESIS 1 AND 2', [
    col('Genesis 1', '@In chapter one', [('humankind, male and female, all at once', '@In chapter one|+0.3')]), col('Genesis 2', '@Then in chapter two', [('one man, formed from the dust', '@He forms one man')])]))
add(card("So La Peyrère asked, what if", kicker='LA PEYRÈRE’S THEORY', lines=[('Two creations?', None, dict(size=96)), ('First: many peoples, everywhere.', '@First, God made', dict(size=54)), ('Later: Adam.', '@Then, later', dict(size=54, red=True))], gap=130))
add(card("And there's actually something in the Hebrew", kicker='HEBREW', lines=[('אָדָם · adam', None, dict(size=110)), ('a human being', '@can mean a human', dict(size=50)),
         ('all of humanity', '@It can mean all', dict(size=50)), ('the particular man named Adam', '@Or it can mean', dict(size=50, red=True))], gap=100))
add(compare("So you could read chapter one", 'One possible reading', 'GENESIS 1 AND 2', [col('Genesis 1', '@chapter one as', [('humanity in general', '@humanity in general')]), col('Genesis 2', '@and chapter two as', [('one man', '@about one man')])]))
add(sheet("But most scholars today read it differently", 'expulsion_rijks', .5, .45, (1.0, 1.12), arrive=(1, 0)))
add(sheet("Traditional readers usually see chapter two", 'di_paolo', .7, .5, (1.0, 1.2), arrive=(0, 1)))
add(sheet("Kind of like a movie", 'aerial', .5, .55, (1.0, 1.6), arrive=None))
add(card("So the two chapters don't prove", lines=[('Not proof of two creations.', None, dict(size=70)), ('Proof the question is old.', '@They just show', dict(size=70, red=True))], gap=150))
# USSHER
add(sheet("Okay, so now, when was Adam supposed to have lived?", 'ussher_annales', .5, .45, (1.0, 1.12), kind='page', arrive=(0, 1)))
add(sheet("In 1650, an Irish archbishop", 'ussher', .5, .3, (1.0, 1.15), arrive=(1, 0), strip='ARMAGH · 1650'))
add(sheet("He added up all the ages and generations", 'jesse_engr', .5, .45, (1.0, 1.15), arrive=(-1, 0)))
add(card("and he worked out that creation happened", kicker='USSHER’S CALCULATION', lines=[('4004 BC', '@4004', dict(size=160, red=True)), ('about six thousand years ago', '@about six', dict(size=56, italic=True))], gap=170))
add(sheet("For a long time, that date was even printed", 'ussher_old', .5, .4, (1.0, 1.12), arrive=(0, 1)))
add(card("But here's the thing. The Bible never", text='The Bible never gives Adam a date.', size=78, stamp=dict(at='@is a calculation', text='A CALCULATION', size=56)))
add(sheet("It depends on how you read those family trees", 'jesse', .5, .6, (1.1, 1.3), arrive=None))
add(sheet("And that matters a lot", 'excavation', .5, .5, (1.0, 1.1), arrive=(1, 0)))
# BONES
add(sheet("The bones.", 'skull', .45, .45, (1.1, 1.25), arrive=(0, 1)))
add(WORLD("In 2017, scientists published", pins=[dict(k='irhoud', name='Jebel Irhoud', side='l', at='@Morocco', active=True)], strip='MOROCCO · 2017', cam=dict(z=[1.3, 2.4], x=[900, 680], y=[520, 460])))
add(sheet("found at a place in Morocco", 'morocco', .5, .5, (1.0, 1.1), arrive=(1, 0)))
add(card("They belonged to early members", kicker='OUR OWN SPECIES', lines=[('Homo sapiens', '@Homo sapiens', dict(size=130, italic=True))]))
add(tl("And they were about three hundred thousand", [[0, 305000]], [mk(300000, 'Jebel Irhoud', 'c. 300,000 yrs ago', '@three hundred thousand', side='right', red=True, up=230)], sliver='@three hundred thousand'))
add(sheet("Now, you might be wondering", 'biface', .5, .5, (1.0, 1.12), arrive=(0, 1)))
add(('Some stones slowly soak up', 'battery', dict(charge='@Some stones', reset='@When a stone gets heated', again=None)))
add(sheet("So when scientists find flint tools", 'axe_cle', .5, .5, (1.0, 1.12), arrive=(1, 0)))
add(sheet("dropped into an ancient campfire", 'campfire', .5, .5, (1.0, 1.1), arrive=(0, 1)))
add(('they can measure how much energy', 'battery', dict(charge=-5, reset=-3, again='@they can measure')))
add(card("That's how they dated these fossils", lines=[('≈ 300,000 years', None, dict(size=120))], stamp=dict(at='@these fossils|+0.1', text='DATED', size=64)))
add(sheet("And the faces?", 'faces', .5, .5, (1.0, 1.12), arrive=(1, 0)))
add(sheet("The backs of the skulls", 'skull', .3, .4, (1.2, 1.35), arrive=None))
add(sheet("But if one of these people sat next to you on the bus", 'bus', .5, .5, (1.0, 1.12), arrive=(0, 1)))
add(WORLD("And our species wasn't alone", areas=[dict(k='neander', at='@Neanderthals', rx=210, ry=110, label='Neanderthals', ly=-130, col='#b3321d')],
          pins=[dict(k='denisova', name='Denisovans', at='@Denisovans', active=True)], cam=dict(z=[1.5, 1.4], x=[780, 820], y=[400, 380])))
add(spread("They were tough, cold-adapted people", [it('axe_cle', '@made tools', 560, 540, 600, -.03), it('campfire', '@used fire', 1360, 520, 560, .03, (1, 0))]))
add(WORLD("Further east lived a group", areas=[dict(k='neander', at=-1, rx=210, ry=110, label='Neanderthals', ly=-130)],
          pins=[dict(k='denisova', name='Denisova Cave', at='@called the Denisovans', active=True)], cam=dict(z=[1.4, 1.9], x=[820, 960], y=[380, 330])))
add(card("And no, these weren't failed attempts", lines=[('Not failed drafts.', None, dict(size=90)), ('Other branches of the human family.', '@They were other branches', dict(size=60, red=True))], gap=150))
add(WORLD("Here's where it gets wild", pins=[dict(k='africa', name='Africa', at='@moved out of Africa', side='b')],
          routes=[dict(a='africa', b='levant', at='@moved out', dur=1.0), dict(a='levant', b='europe', at='@they met these', dur=1.0), dict(a='levant', b='wasia', at='@they met these|+0.3', dur=1.0)],
          areas=[dict(k='neander', at='@they met these', rx=210, ry=110, label='Neanderthals', ly=-130)], cam=dict(z=[1.3, 1.4], x=[760, 760], y=[470, 430])))
add(card("So most people alive today", kicker='NEANDERTHAL DNA', lines=[('≈ 2%', '@About two percent', dict(size=170, red=True)), ('in people whose families come from outside Africa', '@About two percent|+0.4', dict(size=44, italic=True))], gap=150))
add(sheet("Some people, especially in places like Papua New Guinea", 'png', .5, .5, (1.0, 1.1), arrive=(1, 0), strip='PAPUA NEW GUINEA'))
add(sheet("So, in a way, a few of those ancient cousins", 'lab', .5, .5, (1.0, 1.12), arrive=(0, 1)))
add(sheet("And these early humans weren't just surviving", 'hands', .5, .5, (1.0, 1.05), arrive=(-1, 0)))
add(WORLD("On a small island in Indonesia called Muna", pins=[dict(k='muna', name='Muna', side='l', at='@Muna', active=True)], strip='MUNA, INDONESIA', cam=dict(z=[1.4, 2.6], x=[1100, 1230], y=[560, 640])))
add(sheet("someone once pressed their hand", 'hands', .45, .3, (1.2, 1.45), arrive=None))
add(tl("That handprint is at least sixty-seven thousand", [[0, 305000]], [mk(67000, 'Muna hand stencil', 'at least 67,000 yrs ago', '@sixty-seven', red=True, up=260), mk(6000, 'Adam, by tradition', 'c. 6,000', '@sixty-seven|+1.0', up=150, side='left')], sliver=-1))
add(card("When it was announced in January 2026", kicker='ANNOUNCED JANUARY 2026', text='The oldest dated rock art in the world.', size=74))
add(WORLD("The runner-up? A hand stencil in a cave in Spain", pins=[dict(k='maltravieso', name='Spain', side='l', at='@in Spain', active=True), dict(k='muna', name='Muna', side='l', at=-1)],
          areas=[dict(k='neander', at='@made by Neanderthals', rx=210, ry=110, label='Neanderthals?', ly=-130)], cam=dict(z=[1.3, 1.9], x=[900, 640], y=[480, 380])))
add(WORLD("And then there's Göbekli Tepe", pins=[dict(k='gobekli', name='Göbekli Tepe', at='@Göbekli', active=True)], strip='SOUTHERN TURKEY', cam=dict(z=[1.4, 2.5], x=[800, 790], y=[420, 400])))
add(sheet("Around eleven and a half thousand years ago", 'gobekli', .5, .5, (1.0, 1.12), arrive=(0, 1)))
add(tl("That's before writing", [[0, 15000]], [mk(11500, 'Göbekli Tepe', 'c. 11,500 yrs ago', '@before writing|-0.6', up=200), mk(5200, 'Writing', 'c. 3200 BC', '@before writing', up=120, side='right'),
    mk(5500, 'The wheel', 'c. 3500 BC', '@Before the wheel', up=330, side='left'), mk(6000, 'Adam, by tradition', 'Ussher: 4004 BC', '@thousands of years before', red=True, up=450)]))
add(sheet("It used to be called the world's first temple", 'gobekli_pillar', .5, .4, (1.0, 1.12), arrive=(1, 0)))
add(compare("Today, researchers argue", 'Göbekli Tepe', 'WHAT WAS IT?', [col('A place of worship?', '@mainly a place', []), col('A place to live and work?', '@or a place where', [])]))
add(sheet("Either way, someone was carving", 'gobekli_pillar', .5, .3, (1.25, 1.5), arrive=None))
# DNA
add(sheet("Now, for the evidence, it's hiding inside you", 'lab', .6, .4, (1.15, 1.3), arrive=(0, 1), strip='EXHIBIT: YOUR DNA'))
add(sheet("Everyone's DNA is a little bit different", 'faces', .5, .5, (1.05, 1.2), arrive=(1, 0)))
add(sheet("Imagine a giant bag of marbles", 'marbles', .5, .5, (1.0, 1.15), arrive=(0, 1)))
add(('If that bag had been filled from just two small jars', 'marbles', dict(a='@two small jars', b='@But if you see')))
add(('Human DNA looks like the second bag', 'marbles', dict(a=-3, b=-3, mark='@second bag')))
add(card("Our ancestors were always a group", text='Our ancestors were always a population, not one couple.', size=70, stamp=dict(at='@not one couple', text='A POPULATION', size=56)))
add(card("Now, a few researchers have built mathematical models", lines=[('One founding couple, far back in time?', None, dict(size=66)), ('can’t be completely ruled out', '@can\'t be completely', dict(size=54, italic=True))],
         gap=140, stamp=dict(at='@possibility, not', text='POSSIBILITY, NOT DISCOVERY', size=40)))
add(card("And wait, you might ask", lines=[('“Mitochondrial Eve”', '@Mitochondrial Eve', dict(size=80, italic=True)), ('“Y-chromosomal Adam”', '@Y-chromosomal Adam', dict(size=80, italic=True))], gap=150,
         stamp=dict(at='@Not really', text='NOT REALLY', size=60)))
add(card("Here's the trick. Think of surnames", text='Think of surnames.', size=100))
add(('In a lot of families, the surname gets passed', 'surnames', dict(grow=9)))
add(sheet("That doesn't mean only a few families ever existed", 'jesse_engr', .5, .6, (1.1, 1.25), arrive=(0, 1)))
add(('Y-chromosomal Adam is like the one man', 'surnames', dict(grow=.1, hi='@happened to survive')))
add(card("Mitochondrial Eve is the same idea", kicker='MITOCHONDRIAL EVE', text='The same idea, mother to daughter.', size=74))
add(compare("They weren't a couple", 'Not a couple', 'DNA NICKNAMES', [col('Y-chromosomal Adam', '@They weren', [('father → son', '@They weren|+0.2')]), col('Mitochondrial Eve', '@They weren|+0.3', [('mother → daughter', '@They weren|+0.5')])],
         stamp=dict(at='@tens of thousands', text='THOUSANDS OF YEARS APART', size=40, x=960, y=860, rot=-.03)))
add(sheet("Scientists just borrowed the names", 'durer_ae', .5, .5, (1.0, 1.08), arrive=(1, 0)))
add(card("So, here's where it gets interesting", lines=[('We can date the fossils.', '@We can date the fossils', dict(size=80)), ('We can’t date Adam.', '@We can\'t date Adam', dict(size=80, red=True))], gap=150))
add(tl("Science can tell us how old humanity is", [[0, 305000]], [mk(300000, 'Homo sapiens', 'c. 300,000 yrs ago', '@how old humanity', side='right', up=230), mk(150000, 'Adam?', 'where on the timeline?', '@where Adam fits', red=True, up=330)]))
add(card("So the real question isn't", lines=[('“Were there humans before Adam?”', None, dict(size=60, italic=True)), ('“Which Adam are we talking about?”', '@which Adam', dict(size=72, italic=True, red=True))], gap=150))
# TRADITIONAL
add(sheet("Alright. Let's start with the most traditional answer", 'creation_adam', .5, .5, (1.0, 1.1), arrive=(0, 1), strip='THE TRADITIONAL ANSWER'))
add(sheet("Many Christians, and lots of Muslims and Jews too", 'di_paolo', .5, .5, (1.0, 1.08), arrive=(1, 0)))
add(card("For them, the answer to", kicker='WHO WERE THE HUMANS BEFORE ADAM?', lines=[('Nobody.', '@Nobody', dict(size=150, red=True))]))
add(lst("And they have good reasons for believing it", 'Their reasons', 'THE TRADITIONAL CASE', [('One unbroken family line', '@good reasons|+0.3'), ('Jesus speaks of the beginning', '@good reasons|+0.7'), ('Paul: through one man', '@good reasons|+1.1'), ('Doubts about dating', '@good reasons|+1.5')], y0=330, gap=170))
add(sheet("The Bible's family trees run in one unbroken line", 'jesse', .5, .4, (1.0, 1.12), arrive=(0, 1)))
add(sheet("Jesus talks about God creating people", 'christ_teaching', .5, .45, (1.0, 1.12), arrive=(1, 0)))
add(sheet("And Paul's whole argument rests on one man", 'paul_flinck', .5, .35, (1.05, 1.18), arrive=(-1, 0)))
add(compare("In Romans and in First Corinthians", 'One man, one man', 'ROMANS 5 · 1 CORINTHIANS 15', [col('Adam', '@Adam,|-0.3', [('sin and death', '@sin and death')]), col('Christ', '@life comes', [('life', '@life comes|+0.2', dict(red=True))])]))
add(card("So these believers ask", text='If Adam was just a symbol, doesn’t the whole thing fall apart?', size=64, italic=True))
add(lst("They also question the dating methods", 'Their reasons', 'THE TRADITIONAL CASE', [('One unbroken family line', -1, dict(dim=-1)), ('Jesus speaks of the beginning', -1, dict(dim=-1)), ('Paul: through one man', -1, dict(dim=-1)), ('Doubts about dating', -1, dict(red=True))], y0=330, gap=170, arrive=None))
add(sheet("Scientists, including many who are believers", 'excavation', .5, .5, (1.05, 1.18), arrive=(0, 1)))
add(sheet("And the DNA evidence doesn't depend on fossils", 'lab', .4, .5, (1.0, 1.12), arrive=(1, 0)))
add(spread("That's why lots of thinkers in all three faiths", [it('bible_epistle', '@That\'s why lots', 480, 540, 760, -.03), it('quran_met', '@all three faiths', 960, 540, 480, .02, (0, -1)), it('torah_finials', '@another way', 1440, 540, 560, .03, (1, 0))]))
# JUDAISM
add(sheet("Take Judaism", 'torah_curtain', .5, .5, (1.0, 1.1), arrive=(0, 1), strip='JUDAISM'))
add(sheet("An ancient collection of rabbinic teaching", 'talmud', .5, .5, (1.0, 1.15), arrive=(1, 0)))
add(card("says God built worlds and destroyed them", text='“God built worlds and destroyed them before He made this one.”', size=66, italic=True, cite=dict(text='GENESIS RABBAH 3:7')))
add(card("The Talmud even talks about", kicker='THE TALMUD', lines=[('974 generations', None, dict(size=130, red=True)), ('planned before the world, never created', '@planned to create', dict(size=50, italic=True))], gap=160))
add(sheet("And later Jewish mystics", 'sefirot', .5, .5, (1.0, 1.15), arrive=(0, 1), kind='print'))
add(sheet("One world rises and ends", 'stars_cross', .5, .5, (1.0, 1.12), arrive=(1, 0)))
add(sheet("And here's my favourite part", 'buckland', .5, .5, (1.0, 1.1), arrive=(0, 1)))
add(card("In 1842, a respected rabbi", kicker='1842 · A SERMON ABOUT FOSSILS', text='Rabbi Israel Lipschitz', size=86))
add(sheet("People across Europe were digging up giant bones", 'buckland', .35, .45, (1.2, 1.4), arrive=None))
add(WORLD("and a frozen mammoth had turned up in Siberia", pins=[dict(k='siberia', name='Siberia', side='b', at='@Siberia', active=True)], cam=dict(z=[1.3, 2.0], x=[960, 1060], y=[400, 260])))
add(card("Lots of religious people were nervous", lines=[('Nervous?', None, dict(size=100)), ('Not Lipschitz.', '@Not Lipschitz', dict(size=100, red=True))], gap=160))
add(card("He basically said", text='“See? The rabbis told us. The world is older than Adam.”', size=66, italic=True, cite=dict(text='HIS POINT, IN SHORT')))
add(card("For him, science wasn't a threat", lines=[('Not a threat.', None, dict(size=90)), ('A confirmation.', '@It was a confirmation', dict(size=90, red=True))], gap=150))
# ISLAM
add(sheet("Islam has its own version of this puzzle", 'quran_aic', .5, .5, (1.0, 1.12), arrive=(0, 1), strip='ISLAM'))
add(sheet("In the second chapter of the Qur'an", 'quran_met', .5, .5, (1.0, 1.15), arrive=(1, 0)))
add(card("The Arabic word is khalifah", kicker='ARABIC', lines=[('خليفة', None, dict(size=150)), ('khalifah · a steward, a deputy', '@Think of it as', dict(size=50, mono=True))], gap=170))
add(card("And the angels ask a surprising question", text='“Will You place there someone who will cause corruption and shed blood, while we praise You?”', size=60, italic=True, cite=dict(text='QUR’AN 2:30', at='@Will You place')))
add(sheet("Wait. How did the angels know", 'castiglione', .5, .35, (1.05, 1.2), arrive=(0, 1)))
add(sheet("Some early Muslim commentators said", 'jami', .5, .4, (1.0, 1.12), arrive=(1, 0)))
add(card("Not humans, but jinn", kicker='JINN', lines=[('jinn', None, dict(size=150, italic=True)), ('made from smokeless fire, before humans', '@These are beings', dict(size=52, italic=True))], gap=170, cite=dict(text='QUR’AN 15:27', at='@These are beings')))
add(sheet("and some commentators said the jinn had filled", 'campfire', .5, .5, (1.05, 1.2), arrive=(0, 1), o=dict(tone='#c9b79a')))
add(card("To be clear, the jinn aren't cavemen", lines=[('Not cavemen.', None, dict(size=100)), ('A separate kind of being.', '@They\'re a completely', dict(size=64, red=True))], gap=150))
add(sheet("Other commentators explained it differently", 'quran_double', .5, .5, (1.05, 1.18), arrive=(1, 0)))
add(sheet("And there's an even bigger idea", 'milkyway', .5, .5, (1.0, 1.12), arrive=(0, 1)))
add(card("A report in Shia tradition", kicker='SHIA TRADITION · IMAM MUHAMMAD AL-BAQIR', lines=[('a thousand thousand worlds', '@a thousand thousand worlds', dict(size=72, italic=True)), ('a thousand thousand Adams', '@thousand Adams', dict(size=72, italic=True, red=True))], gap=150))
add(sheet("And we live in the last of those worlds", 'stars_cross', .5, .3, (1.15, 1.3), arrive=None))
add(sheet("Still, the Qur'an's main picture is clear", 'quran_cle', .5, .5, (1.0, 1.12), arrive=(0, 1)))
add(card("It says God created all people from a single soul", text='“created you from a single soul, and from it, its mate”', size=66, italic=True, cite=dict(text='QUR’AN 4:1')))
add(card("And it says God created Adam from dust", lines=[('created from dust', None, dict(size=80, italic=True)), ('“Be,” and he was.', '@and he was', dict(size=90, italic=True, red=True))], gap=150, cite=dict(text='QUR’AN 3:59')))
add(sheet("Most Muslim scholars today believe", 'naming', .5, .5, (1.0, 1.1), arrive=(1, 0)))
add(sheet("So the fossils raise real questions", 'skull', .5, .45, (1.0, 1.12), arrive=(0, 1)))
# WHAT MAKES ADAM SPECIAL
add(card("Which brings us to the big question", kicker='WHAT WOULD MAKE ADAM SPECIAL?', lines=[('His body?', '@His body', dict(size=70)), ('His language?', '@His language', dict(size=70)), ('His sense of right and wrong?', '@His sense', dict(size=70)), ('His relationship with God?', '@His relationship', dict(size=70, red=True))], gap=100, ytop=-110))
add(spread("Here's the catch. Archaeology can find", [it('biface', '@tools', 440, 540, 560, -.03), it('hands', '@paintings', 960, 540, 640, .02, (0, -1)), it('excavation', '@graves', 1470, 540, 420, .03, (1, 0))]))
add(card("But it can't dig up a soul", lines=[('It can’t dig up a soul.', None, dict(size=84)), ('Or tell us whether God spoke to someone.', '@And it can\'t tell', dict(size=56, italic=True, red=True))], gap=150))
add(sheet("And that's exactly where some believers say", 'castiglione', .5, .45, (1.0, 1.12), arrive=(1, 0)))
add(sheet("In 1950, Pope Pius the Twelfth", 'vatican', .5, .5, (1.0, 1.1), arrive=(0, 1), strip='VATICAN · 1950'))
add(card("He said Catholics were free to explore", kicker='HUMANI GENERIS, 1950', lines=[('The body: free to investigate.', '@free to explore', dict(size=66)), ('The soul: created directly by God.', '@as long as they', dict(size=66, red=True))], gap=150))
add(card("But he drew a line at the idea", text='One first couple, not many.', size=84, stamp=dict(at='@because he couldn', text='THE LINE', sub='ORIGINAL SIN', size=56)))
add(sheet("Protestant thinkers have gone in a few directions", 'paul_met', .5, .4, (1.0, 1.12), arrive=(0, 1)))
add(card("A famous English pastor named John Stott", kicker='JOHN STOTT · AFTER DEREK KIDNER', lines=[('Adam: a real man God chose from among existing humans', '@suggested that Adam', dict(size=60)), ('the first to bear God’s image', '@The first to bear', dict(size=56, italic=True, red=True))], gap=150))
add(card("Then, in 2021, the philosopher William Lane Craig", kicker='WILLIAM LANE CRAIG · 2021', lines=[('Adam and Eve were real…', '@argued that Adam', dict(size=64)), ('…but lived 750,000+ years ago', '@Maybe more than', dict(size=64, red=True)), ('Homo heidelbergensis?', '@Possibly part', dict(size=56, italic=True))], gap=120))
add(tl("That's a philosophical proposal", [[0, 900000]], [mk(300000, 'Homo sapiens', 'c. 300,000', '@That\'s a philosophical', up=160, side='right'), mk(750000, 'Craig’s Adam?', '750,000+ yrs ago', '@philosophical proposal|+0.4', red=True, up=300, side='right')],
    title='A founding pair in deep time?', sub='A PROPOSAL, NOT A FINDING'))
add(card("And in Islam, a scholar named Shoaib Ahmed Malik", kicker='SHOAIB AHMED MALIK · 2021 · AFTER AL-GHAZALI', lines=[('Humans evolved.', '@argued in 2021', dict(size=74)), ('Adam and Eve: a miracle, without parents.', '@Made directly|-0.3', dict(size=64, red=True))], gap=150))
add(sheet("and placed into a world where other humans already lived", 'faces', .5, .5, (1.0, 1.12), arrive=(1, 0)))
# SWAMIDASS
add(sheet("Now, the most surprising idea of all", 'lab', .5, .5, (1.05, 1.15), arrive=(0, 1)))
add(card("In 2019, a computational biologist", kicker='JOSHUA SWAMIDASS · 2019', lines=[('your genetic ancestors', '@Your genetic', dict(size=70)), ('your family-tree ancestors', '@family-tree ancestors', dict(size=70, red=True))], gap=150))
add(('Here\'s how it works. You have two parents', 'doubling', dict(gens=[['@two parents', 2], ['@Four grandparents', 4], ['@Eight great', 8], ['@Every generation back', 16], ['@Every generation back|+0.8', 32], ['@Go back far', 64]],
    caption=dict(text='more ancestors than people alive?', at='@more ancestors'))))
add(('Unless the same people show up', 'doubling', dict(gens=[[-1, 2], [-1, 4], [-1, 8], [-1, 16], [-1, 32], [-1, 64]], overlap='@again and again', caption=dict(text='the same people, again and again', at='@again and again'))))
add(card("But here's the twist. You don't get DNA", lines=[('family-tree ancestor', None, dict(size=66)), ('≠', None, dict(size=90, red=True)), ('DNA donor', None, dict(size=66))], gap=100))
add(card("like a game of telephone", text='Each generation, some DNA drops out.', size=70, stamp=dict(at='@without leaving', text='NO TRACE', size=60)))
add(WORLD("Using computer models, Swamidass argued", pins=[dict(k='middleeast', name='a couple, c. 6,000 yrs ago', at='@a couple living', active=True, fs=30)],
          routes=[dict(a='middleeast', b='europe', at='@could have ended', dur=.9), dict(a='middleeast', b='africa', at='@could have ended|+0.2', dur=.9), dict(a='middleeast', b='denisova', at='@could have ended|+0.4', dur=.9),
                  dict(a='middleeast', b='png', at='@could have ended|+0.6', dur=1.0), dict(a='middleeast', b='irhoud', at='@could have ended|+0.8', dur=.9)], cam=dict(z=[1.5, 1.05], x=[800, 900], y=[420, 470])))
add(sheet("Even if lots of other people lived alongside them", 'rembrandt_ae', .5, .5, (1.0, 1.1), arrive=(0, 1)))
add(compare("They wouldn't be the source of all our DNA", 'A genealogical Adam', 'SWAMIDASS’S POINT', [col('Not', '@They wouldn', [('the source of all our DNA', '@They wouldn|+0.2')]), col('But', '@But they could', [('in everyone’s family tree', '@But they could|+0.2', dict(red=True))])]))
add(lst("Now, does that prove Adam and Eve existed?", 'What it doesn’t show', 'NO PROOF EITHER WAY', [('where or when they lived', '@where or when', dict(mark='✗')), ('a miracle', '@made them by a miracle', dict(mark='✗')), ('that it fits Genesis or the Qur’an', '@theologians still', dict(mark='✗'))], y0=360, gap=190))
add(card("What it does show is this", lines=[('“everyone’s ancestor”', None, dict(size=70, italic=True)), ('≠', None, dict(size=90, red=True)), ('“the only person alive at the time”', '@the only person', dict(size=70, italic=True))], gap=110))
# EDEN QUESTIONS
add(sheet("There's one more way to look at all this", 'hollar_eden', .5, .5, (1.0, 1.1), arrive=(0, 1)))
add(sheet("What was the story of Adam trying to explain", 'cranach_paradise', .5, .45, (1.05, 1.18), arrive=(1, 0)))
add(lst("A lot of scholars point out", 'The big human questions', 'WHAT EDEN EXPLAINS', [('Why do we die?', '@Why do we die'), ('Why is work so hard?', '@Why is work'), ('Why does giving birth hurt?', '@Why does giving'), ('Why do we feel shame?', '@Why do we feel shame'), ('Why do we feel far from God?', '@far from God')], y0=300, gap=140))
add(sheet("Stories that explain", 'holbein_work', .5, .5, (1.0, 1.12), arrive=(0, 1)))
add(sheet("So maybe Genesis was answering those questions", 'ae_work', .5, .45, (1.0, 1.12), arrive=(1, 0)))
add(compare("That doesn't mean Adam has to be made up", 'Three ways to read Adam', 'BELIEVERS DIFFER', [col('A real man', '@Some believers think', [('told in a symbolic way', '@told in a symbolic')]), col('A stand-in', '@Others see him', [('for all of humanity', '@Others see him|+0.3')]),
    col('History', '@And others read it', [('straightforward', '@straightforward')])]))
add(sheet("But it does suggest we might be asking Genesis", 'rebuke', .5, .5, (1.0, 1.12), arrive=(0, 1)))
# DARK CHAPTER
add(card("Okay. Now there's a dark side to this story", kicker='A DARK CHAPTER', text='The idea is put to an ugly use.', size=76))
add(sheet("La Peyrère's idea didn't stay", 'pa_hand', .5, .4, (1.0, 1.1), kind='page', arrive=(1, 0), o=dict()))
add(card("They argued that if some humans came from Adam", kicker='THE 1800s CLAIM', text='“Maybe not everyone belonged to the same human family.”', size=66, italic=True))
add(sheet("In 1880, an American geologist named Alexander Winchell", 'winchell', .5, .4, (1.0, 1.12), kind='print', arrive=(0, 1), strip='1880'))
add(sheet("Even before the American Civil War", 'abolition_jug', .5, .5, (1.0, 1.12), arrive=(1, 0)))
add(card("After it, books like Winchell's", text='A scientific-sounding cover for segregation.', size=72, stamp=dict(at='@less human', text='FALSE', size=80)))
add(card("But here's the twist. The same science", lines=[('One species.', '@belongs to one species', dict(size=90)), ('Deep common roots.', '@We all share', dict(size=70)), ('Tiny differences between groups.', '@The genetic differences', dict(size=60, red=True))], gap=130))
add(sheet("Most of the variety actually exists within groups", 'faces', .5, .5, (1.05, 1.18), arrive=(0, 1)))
add(WORLD("And if you trace family trees back just a few thousand years", pins=[dict(k='middleeast', name='', at='@trace family trees', active=True)],
          routes=[dict(a='africa', b='europe', at='@trace family', dur=.8), dict(a='europe', b='denisova', at='@trace family|+0.3', dur=.8), dict(a='denisova', b='png', at='@trace family|+0.6', dur=.9),
                  dict(a='png', b='africa', at='@trace family|+0.9', dur=1.0), dict(a='irhoud', b='middleeast', at='@many of the same', dur=.7)], cam=dict(z=[1.05, 1.15], x=[900, 900], y=[480, 470])))
add(sheet("In the Book of Acts, Paul tells the thinkers of Athens", 'paul_athens', .5, .45, (1.0, 1.12), arrive=(1, 0), strip='ATHENS'))
add(card("“From one man he created all the nations", text='“From one man he created all the nations throughout the whole earth.”', size=68, italic=True, cite=dict(text='ACTS 17:26')))
add(sheet("And the Qur'an says God created all people from a single soul", 'quran_double', .5, .5, (1.0, 1.12), arrive=(0, 1)))
add(sheet("So on the question that matters most", 'milkyway', .5, .5, (1.0, 1.1), arrive=(1, 0)))
add(card("We're one human family", text='One human family.', size=110, stamp=dict(at='@one human family|+0.4', text='AGREED', sub='SCRIPTURE · SCIENCE', size=50)))
# CONCLUSION
add(card("So, in conclusion", text='Where does all of this leave us?', size=84))
V = lambda a, focus, **k: (a, 'verdict', dict(at=['@@Some things are about as certain', '@@Some things come down', '@@Some things are still being argued', '@@And some things no scientist'],
    items=[[dict(text='Our species: 300,000+ years old', at='@@People of our own species'), dict(text='Neanderthals and Denisovans: still in our DNA', at='@@Other kinds of humans'),
            dict(text='Art, burials, monuments long before 6,000 years ago', at='@@People were making art'), dict(text='A population, never one pair', at='@@And our ancestors were always')],
           [dict(text='Cain’s fear, wife and city: unexplained', at='@@Genesis mentions Cain'), dict(text='No date for Adam in the Bible', at='@@And the Bible never')],
           [dict(text='One founding couple, deep in time?', at='@@Could there have been'), dict(text='Which Adam?', at='@@And was Adam the first')],
           [dict(text='Did they have souls?', at='@@Did those earliest'), dict(text='The image of God', at='@@what does it mean to be made')]], focus=focus, focusAt=-1, **k))
def resolve_verdict(spec): return spec
add(V("Some things are about as certain as ancient history gets", 0))
add(tl("People of our own species were around", [[0, 305000]], [mk(300000, 'Homo sapiens', 'at least 300,000 yrs ago', '@People of our own', side='right', red=True, up=230)], sliver='@People of our own'))
add(WORLD("Other kinds of humans, like Neanderthals and Denisovans", areas=[dict(k='neander', at='@Neanderthals', rx=210, ry=110, label='Neanderthals', ly=-130)], pins=[dict(k='denisova', name='Denisovans', at='@Denisovans', active=True)], cam=dict(z=[1.4, 1.5], x=[820, 840], y=[390, 380])))
add(spread("People were making art, burying their dead", [it('hands', '@making art', 460, 540, 640, -.03), it('skull', '@burying their dead', 960, 560, 460, .02, (0, -1)), it('gobekli', '@building huge', 1450, 540, 460, .03, (1, 0))]))
add(V("And our ancestors were always a group, not a single pair", 0))
add(V("Some things come down to how you read the text", 1))
add(('Genesis mentions Cain\'s fear, his wife and his city', 'tree', dict(g=dict(adam=-1, eve=-1, sons=-1, kill=-1, dim=-1, hi=-1, q=['@Cain\'s fear', '@his wife', '@and his city']), cam=dict(z=[.94, .94], x=[820, 820], y=[600, 600]))))
add(sheet("Others see a wider world, or an older story woven in", 'hollar_eden', .3, .5, (1.1, 1.25), arrive=(0, 1)))
add(card("And the Bible never gives Adam a date", lines=[('4004 BC', None, dict(size=120)), ('a calculation, not a verse', '@a calculation, not', dict(size=60, italic=True, red=True))], gap=150))
add(V("Some things are still being argued about", 2))
add(lst("And was Adam the first human body", 'Which Adam?', 'STILL ARGUED', [('the first human body', '@the first human body'), ('a man God chose from among others', '@a man God chose'), ('a founding father long ago', '@a founding father'), ('a figure who stands for all of us', '@a figure who stands')], y0=330, gap=170))
add(V("And some things no scientist can ever reach", 3))
add(sheet("Did those earliest people have souls?", 'stars_cross', .5, .5, (1.0, 1.1), arrive=(0, 1)))
add(sheet("And what does it mean to be made in the image of God?", 'castiglione', .5, .45, (1.05, 1.18), arrive=(1, 0)))
add(card("So here's where I land", kicker='CASE NOTES', text='My verdict.', size=110))
add(sheet("Who were the ancient humans? They were us", 'faces', .5, .5, (1.0, 1.1), arrive=(0, 1)))
add(sheet("They made tools", 'biface', .5, .5, (1.0, 1.12), arrive=(1, 0)))
add(sheet("They painted", 'hands', .5, .4, (1.05, 1.2), arrive=(-1, 0)))
add(sheet("They mourned their dead", 'skull', .5, .45, (1.0, 1.1), arrive=(0, 1)))
add(sheet("And they very likely looked up at the night sky", 'milkyway', .5, .4, (1.0, 1.15), arrive=(0, -1)))
add(card("They weren't lesser beings", lines=[('Not lesser beings.', None, dict(size=90)), ('Part of the same story.', '@They were part', dict(size=80, red=True))], gap=150))
add(card("Were they before Adam?", lines=[('Were they before Adam?', None, dict(size=80)), ('Which Adam?', '@depends on which', dict(size=110, red=True))], gap=160))
add(tl("If Adam lived six thousand years ago", [[0, 15000], ['@There were humans long', 305000]], [mk(6000, 'Adam, by tradition', 'Ussher: 4004 BC', '@six thousand years ago', red=True, up=260, until='@There were humans long'),
    mk(300000, 'Homo sapiens', 'c. 300,000 yrs ago', '@There were humans long|+1.2', side='right', up=230)], sliver='@There were humans long|+1.5'))
add(('What our DNA makes really hard to believe', 'marbles', dict(a=-3, b=-3, mark='@just two people')))
add(lst("But that doesn't close the case on Adam", 'Still possible', 'CASE NOT CLOSED', [('a real Adam, chosen from among other humans', '@A real Adam', dict(size=50)), ('a founding couple in the deep past', '@A founding couple in the deep', dict(size=50)), ('a man whose family tree reached everyone alive', '@A man whose family', dict(size=50))], y0=380, gap=180))
add(card("Fossils and genes can't rule any of those out", text='Not ruled out. Not proven.', size=96, stamp=dict(at='@prove them either', text='UNRESOLVED', size=60)))
add(card("We can date the bones", lines=[('We can date the bones.', None, dict(size=84)), ('We can’t date Adam.', '@We can\'t date Adam', dict(size=84, red=True))], gap=150))
add(sheet("Whether he was the start of human life", 'di_paolo', .5, .5, (1.0, 1.12), arrive=(0, 1)))
add(card("So, what do you think?", kicker='YOUR VERDICT', lines=[('the very first human?', '@the very first', dict(size=64)), ('a man God chose from among others?', '@a man God chose', dict(size=64)), ('a figure who speaks for all of us?', '@a figure who speaks', dict(size=64)), ('Tell me in the comments.', '@Tell me in', dict(size=56, red=True, mono=True))], gap=110))
add(("And if you want me to open more files", 'endcard', dict(like='@hit like', share='@share it', sub='@and subscribe', press={'LIKE': '@hit like|+0.5', 'SHARE': '@share it|+0.5', 'SUBSCRIBE': '@and subscribe|+0.5'})))

# ---------------- resolve ----------------
TIME_KEYS = {'at', 'dim', 'hi', 'focusAt', 'charge', 'reset', 'again', 'a', 'b', 'sliver', 'adam', 'eve', 'sons', 'kill', 'strike', 'until', 'mark', 'overlap', 'others',
             'like', 'share', 'sub', 'q', 'gens', 'years', 'spans', 'press', 'LIKE', 'SHARE', 'SUBSCRIBE'}
def resolve(v, base, key=None):
    if isinstance(v, str) and v.startswith('@@'):  # anywhere in the narration (phrase must be unique)
        ph, _, off = v[2:].partition('|')
        return round(find(ph, 0) + (float(off) if off else 0), 3)
    if isinstance(v, str) and v.startswith('@'):
        ph, _, off = v[1:].partition('|')
        return round(find(ph, base - 0.3) + (float(off) if off else 0), 3)
    if key in TIME_KEYS and isinstance(v, int) and not isinstance(v, bool) and -10 <= v < 0:  # -1 = "already there" (relative to shot start)
        return 'REL%s' % v
    if isinstance(v, dict): return {k: resolve(x, base, k) for k, x in v.items()}
    if isinstance(v, list): return [resolve(x, base, key if key in ('gens', 'years', 'q', 'spans') else None) if not isinstance(x, list) else [resolve(y, base, key if key in ('gens', 'years', 'spans') else None) for y in x] for x in v]
    return v

def fix_rel(v, t0):
    if isinstance(v, str) and v.startswith('REL'): return round(t0 + float(v[3:]), 3)
    if isinstance(v, dict): return {k: fix_rel(x, t0) for k, x in v.items()}
    if isinstance(v, list): return [fix_rel(x, t0) for x in v]
    return v

shots, last = [], 0.0
for n, (anchor, typ, params) in enumerate(S):
    t_anchor = 0.0 if n == 0 else find(anchor, last)
    last = t_anchor
    d = resolve(params, t_anchor)
    shots.append(dict(id=n + 1, type=typ, anchor=anchor, t0=round(max(0, t_anchor - 0.15), 3), **d))
for i, s in enumerate(shots):
    s['t1'] = shots[i + 1]['t0'] if i + 1 < len(shots) else END
    for k in list(s.keys()):
        if k not in ('t0', 't1', 'id', 'type', 'anchor'): s[k] = fix_rel(s[k], s['t0'])
    if s['type'] == 'tree':  # None = appears at shot start in sequence
        g = s['g']; base = s['t0'] + .2
        for j, k in enumerate(['adam', 'eve', 'sons', 'kill']):
            if k in g and g[k] is None: g[k] = round(base + j * .45, 3)
    if s['type'] == 'card' and 'lines' in s:
        for L in s['lines']:
            if L.get('at') is None: L['at'] = round(s['t0'] + .25, 3)
    if s['type'] == 'battery' and s.get('again') is None: s.pop('again', None)
    if s['type'] == 'surnames': s['grow'] = s.get('grow', 5)

# split long still shots: wide, then a closer detail of the same object (no re-arrival)
out = []
for s in shots:
    dur = s['t1'] - s['t0']
    if s['type'] in ('sheet',) and dur > 5.6 and not s.get('loupe'):
        n = 2 if dur < 10.5 else 3
        cuts = [s['t0'] + dur * k / n for k in range(n + 1)]
        u, v = s.get('focus', [.5, .5]); details = [(u, v), (min(.8, u + .2), max(.25, v - .15)), (max(.2, u - .2), min(.75, v + .15))]
        for k in range(n):
            c = json.loads(json.dumps(s)); c['t0'], c['t1'] = round(cuts[k], 3), round(cuts[k + 1], 3)
            if k > 0:
                c['arrive'] = None; c.pop('strip', None)
                du, dv = details[k]; z1 = 1.35 + .1 * k
                fx, fy = c['x'] + (du - .5) * c['h'] * 0.5, c['y'] + (dv - .5) * c['h'] * .7
                c['cam'] = dict(z=[z1, z1 + .1], x=[fx, fx + (15 if k % 2 else -15)], y=[fy, fy])
            out.append(c)
    else:
        out.append(s)
# re-framing: in any stretch longer than ~5 s without a new beat, cut between a closer and a wider framing
BEAT_KEYS = ('at', 'like', 'share', 'sub', 'charge', 'reset', 'again', 'a', 'b', 'mark', 'hi', 'overlap', 'sliver')
def beat_times(o):
    r = []
    if isinstance(o, dict):
        for k, v in o.items():
            if k in BEAT_KEYS and isinstance(v, (int, float)) and not isinstance(v, bool): r.append(v)
            elif isinstance(v, (dict, list)): r += beat_times(v)
    elif isinstance(o, list):
        for v in o: r += beat_times(v)
    return r
PUNCH = {'card': [(960, 520), (960, 600)], 'list': [(760, 470), (900, 640)], 'compare': [(700, 500), (1220, 500)], 'timeline': [(1250, 520), (700, 560)],
         'tree': [(700, 560), (1000, 700)], 'verdict': [(560, 500), (1300, 500)], 'doubling': [(960, 520), (960, 760)], 'marbles': [(560, 600), (1360, 600)],
         'surnames': [(700, 520), (1100, 640)], 'battery': [(960, 520), (960, 600)], 'spread': [(600, 540), (1320, 540)], 'endcard': [(960, 560), (960, 560)]}
for s in out:
    if s['type'] in ('sheet',): continue
    ts = sorted(set([s['t0']] + [t for t in beat_times({k: v for k, v in s.items() if k not in ('t0', 't1')}) if s['t0'] + .3 < t < s['t1'] - .3] + [s['t1']]))
    cuts = []
    for a_, b_ in zip(ts, ts[1:]):
        if b_ - a_ > 5.0:
            n = int((b_ - a_) // 4.2)
            cuts += [round(a_ + (b_ - a_) * (k + 1) / (n + 1), 3) for k in range(n)]
    if not cuts: continue
    base = s.get('cam') or {'z': [1.0, 1.03], 'x': [960, 960], 'y': [540, 540]}
    bz, bx, by = base['z'][-1], base['x'][-1], base['y'][-1]
    rf = []
    for k, t in enumerate(sorted(cuts)):
        if k % 2 == 0:
            if s['type'].startswith('map'):
                px, py = bx + (80 if k % 4 == 0 else -80), by
            else:
                px, py = PUNCH.get(s['type'], [(960, 540)] * 2)[(k // 2) % 2]
            rf.append(dict(t=t, z=round(bz * 1.22, 3), x=px, y=py, dx=12))
        else:
            rf.append(dict(t=t, z=round(base['z'][0], 3), x=base['x'][0], y=base['y'][0], dx=-10))
    s['reframes'] = rf
for s in out:  # spreads: even spacing, each object fits its column
    if s['type'] == 'spread':
        n = len(s['items']); colw = 1640 / n
        for i, x in enumerate(s['items']):
            w0, h0 = SIZES[x['img']]; ar = w0 / h0
            x['h'] = round(min(x['h'], 760, (colw - 70) / ar), 1); x['x'] = round(140 + colw * (i + .5), 1); x['y'] = 540
for i, s in enumerate(out): s['id'] = i + 1

json.dump({'end': END}, open(f'{P}/film2/film.json', 'w'))
with open(f'{P}/film2/shots.js', 'w') as f:
    f.write('window.FILM=' + json.dumps({'end': END}) + ';\nwindow.SHOTS=' + json.dumps(out, ensure_ascii=False) + ';\n')

# pacing report
durs = [s['t1'] - s['t0'] for s in out]
print(f"{len(S)} authored shots -> {len(out)} on screen; end {END:.1f}s; mean {sum(durs) / len(durs):.2f}s; max {max(durs):.2f}s")
long = [(s['id'], s['type'], round(s['t1'] - s['t0'], 1), s['anchor'][:50]) for s in out if s['t1'] - s['t0'] > 7.5]
gaps = []
for s in out:
    extra = [r['t'] for r in s.get('reframes', [])]
    ts = sorted(set([s['t0']] + [t for t in beat_times({k: v for k, v in s.items() if k not in ('t0', 't1')}) + extra if s['t0'] < t < s['t1']] + [s['t1']]))
    gaps.append(max(b_ - a_ for a_, b_ in zip(ts, ts[1:])))
print(f"longest stretch without a visual change: {max(gaps):.1f}s; stretches over 5.5 s: {sum(g > 5.5 for g in gaps)}")
used = {}
for s in out:
    for k in [s.get('img')] + [x['img'] for x in s.get('items', []) if isinstance(x, dict) and 'img' in x]:
        if k: used.setdefault(k, []).append(round(s['t0']))
print('images used:', len(used))
