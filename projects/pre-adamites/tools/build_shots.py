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
    w0, h0 = SIZES[img]; ar = w0 / h0
    arr = list(arrive) if arrive else None
    for key in ('x', 'y', 'rot', 'o'): pass
    if kind == 'page':
        k.pop('x', None); k.pop('y', None); k.pop('h', None)
        return (a, 'page', dict(img=img, arrive=arr, zoom=[min(z), min(1.04, max(z))], focus=[u, v], **k))
    if kind == 'disc':
        hh = k.pop('h', None) or 1000
        return (a, 'sheet', dict(img=img, h=hh, x=k.pop('x', 960), y=k.pop('y', 540), kind='disc', arrive=arr, cam=dict(z=[1.0, 1.06], x=[960, 960], y=[540, 540]), focus=[u, v], **k))
    k.pop('x', None); k.pop('y', None); k.pop('rot', None)
    o = k.pop('o', {}) or {}
    mode = 'cover' if 1.25 <= ar <= 2.3 else 'fit'
    if mode == 'cover':
        cam_ = dict(z=[1.0 + (min(z) - 1) * .6, 1.0 + (max(z) - 1) * 1.2], u=[.5, u], v=[.5, v])
        if z[0] > z[1]: cam_['z'] = cam_['z'][::-1]
    elif min(z) >= 1.2:  # an authored close-up of a portrait image: a 16:9 window on the asked-for detail
        mode = 'cover'; cam_ = dict(z=[max(1.0, min(z) - .2), max(z) - .2], u=[u, u], v=[v, v])
    else:
        cam_ = dict(z=[.965, 1.0], u=[.5, .5], v=[.5, .5])
    d = dict(img=img, mode=mode, arrive=arr, cam=cam_, focus=[u, v], **k)
    if o.get('tone'): d['tone'] = o['tone']
    return (a, 'frame', d)

def fx(a, clip, u=.5, v=.5, z=(1.0, 1.08), arrive=None, bleed=True, **k):
    """moving footage: frames in film2/vid/<clip>/ (see tools/footage.py)"""
    return (a, 'footage', dict(clip=clip, bleed=bleed, arrive=list(arrive) if arrive else None, cam=dict(z=list(z), u=[.5, u], v=[.5, v]), **k))

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

def _map(a, world, **k):
    k.pop('cam', None)
    fit = k.pop('fit', None) or sorted({p['k'] for p in k.get('pins', [])} | {r['a'] for r in k.get('routes', [])} | {r['b'] for r in k.get('routes', [])} | {st['k'] for st in k.get('stamps', [])})
    return (a, 'map', dict(world=world, fit=fit, **k))
EU = lambda a, **k: _map(a, False, **k)
WORLD = lambda a, **k: _map(a, True, **k)

# ---------------- the shot list (tools/shotlist_v3.py) ----------------
S = []
add = S.append
exec(open(f'{P}/tools/shotlist_v3.py').read())

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
        if not s.get('text') and s['lines'] and s['lines'][0]['at'] > s['t0'] + .8: s['lines'][0]['at'] = round(s['t0'] + .25, 3)  # never a card without its headline
    if s['type'] == 'battery' and s.get('again') is None: s.pop('again', None)
    if s['type'] == 'surnames':
        if 'growTo' in s: s['grow'] = round(max(1.0, s.pop('growTo') - s['t0'] - .3), 2)
        s['grow'] = s.get('grow', 5)

OBJECTS = {'biface', 'lev_core', 'lev_core2', 'quran_aic', 'sefirot', 'abolition_jug', 'hands', 'celestial_globe', 'venus', 'gobekli_pillar', 'skull'}  # objects: detail stays on the object's centre
# split long image shots into a wide view and close details (crops always stay inside the image)
out = []
for s in shots:
    s['_use'] = s['id']
    dur = s['t1'] - s['t0']
    small = s['type'] == 'frame' and s.get('mode') == 'fit' and (lambda w, h: (w if w / h < 16 / 9 else h * 16 / 9))(*SIZES[s['img']]) < 1150  # too small for any close-up
    if s['type'] in ('frame', 'page', 'footage') and dur > 5.4 and not s.get('loupe') and not small:
        n = max(2, int(round(dur / 4.2)))
        cuts = [s['t0'] + dur * k / n for k in range(n + 1)]
        u, v = s.get('focus', [.5, .5]); details = [(u, v), (u, v), (min(.75, u + .18), max(.3, v - .14)), (max(.25, u - .18), min(.7, v + .14)), (u, v)]
        for k in range(n):
            c = json.loads(json.dumps(s)); c['t0'], c['t1'] = round(cuts[k], 3), round(cuts[k + 1], 3)
            if k > 0:
                c['arrive'] = None; c.pop('strip', None); c.pop('stamp', None) if c.get('stamp', {}).get('at', 0) < c['t0'] - 1 else None
                du, dv = details[min(k, 4)]
                if c['type'] == 'page':  # a document: closer view of the same page, still whole on screen
                    c['zoom'] = [1.0, 1.03]; c['type'] = 'frame'; c['mode'] = 'cover'; c['tone'] = '#efe6d2'
                    c['cam'] = dict(z=[2.0, 2.15], u=[du, du], v=[dv, dv + .02])
                elif c['type'] == 'frame':
                    if s.get('detail'): du, dv = s['detail'][min(k, len(s['detail'])) - 1]  # authored crop points (faces, inscriptions)
                    elif s.get('mode') == 'fit' and s['img'] not in OBJECTS: du, dv = (max(.32, u - .14), .27) if k % 2 else (min(.68, u + .14), .38)  # portrait artworks: the heads and upper third, never a blind centre crop
                    w0, h0 = SIZES[s['img']]; base = w0 if w0 / h0 < 16 / 9 else h0 * 16 / 9  # source pixels across a cover window at z=1
                    zz = min(1.55 if s.get('mode') == 'cover' else 1.25, base / 1150)  # never enlarge past ~1.7x on screen
                    if s.get('mode') == 'fit' and zz >= 1.0: zz = max(zz, 1.12)  # a 16:9 window on a portrait is already a close-up
                    if zz < 1.12:  # too small for a close-up: stay whole, a gentle push from a different side
                        c['cam'] = dict(z=[1.0, 1.05], u=[.5, .5], v=[.5, .5]) if s.get('mode') == 'fit' else dict(z=[1.04, 1.12], u=[du, du], v=[dv, dv])
                    else:
                        c['mode'] = 'cover'; c['cam'] = dict(z=[zz, zz + .1], u=[du, du + (.03 if k % 2 else -.03)], v=[dv, dv])
                else:
                    c['cam'] = dict(z=[1.12, 1.2], u=[du, du], v=[dv, dv])
            out.append(c)
    else:
        out.append(s)
BEAT_KEYS = ('at', 'like', 'share', 'sub', 'charge', 'reset', 'again', 'a', 'b', 'mark', 'hi', 'overlap', 'sliver', 'adam', 'eve', 'sons', 'kill', 'others', 'dim', 'until', 'strike')
def beat_times(o):
    r = []
    if isinstance(o, dict):
        for k, v in o.items():
            if k in BEAT_KEYS and isinstance(v, (int, float)) and not isinstance(v, bool): r.append(v)
            elif k == 'gens' and isinstance(v, list): r += [g[0] for g in v if isinstance(g, list) and isinstance(g[0], (int, float))]
            elif k == 'q' and isinstance(v, list): r += [x for x in v if isinstance(x, (int, float))]
            elif isinstance(v, (dict, list)): r += beat_times(v)
    elif isinstance(o, list):
        for v in o: r += beat_times(v)
    return r
# cards only: a gentle closer framing on long holds (the whole card stays in frame at z <= 1.12)
for s in out:
    if s['type'] != 'card': continue
    ts = sorted(set([s['t0']] + [t for t in beat_times({k: v for k, v in s.items() if k not in ('t0', 't1')}) if s['t0'] + .3 < t < s['t1'] - .3] + [s['t1']]))
    cuts = []
    for a_, b_ in zip(ts, ts[1:]):
        if b_ - a_ > 5.0:
            n = int((b_ - a_) // 4.2); cuts += [round(a_ + (b_ - a_) * (k + 1) / (n + 1), 3) for k in range(n)]
    if cuts: s['reframes'] = [dict(t=t, z=1.12 if k % 2 == 0 else 1.0, x=960, y=540, dx=0) for k, t in enumerate(sorted(cuts))]
for s in out:  # spreads: even spacing, each object fits its column
    if s['type'] == 'spread':
        n = len(s['items']); colw = 1640 / n
        for i, x in enumerate(s['items']):
            w0, h0 = SIZES[x['img']]; ar = w0 / h0
            x['h'] = round(min(x['h'], 760, (colw - 70) / ar), 1); x['x'] = round(140 + colw * (i + .5), 1); x['y'] = 540
        if s['items'] and s['items'][0]['at'] > s['t0'] + .5: s['items'][0]['at'] = round(s['t0'] + .2, 3)  # never an empty desk
for i, s in enumerate(out): s['id'] = i + 1
# footage: each on-screen piece gets its own graded frame folder; split pieces continue the same clip; a clip too
# short for its shot starts earlier and, if it must, plays slower (never below 0.6x)
FDUR = json.load(open(f'{P}/tools/footage_dur.json'))
groups = {}
for s in out:
    if s['type'] == 'footage': groups.setdefault(s['_use'], []).append(s)
for g in groups.values():
    key = g[0]['clip']; cd = FDUR[key]; T0, T1 = g[0]['t0'], g[-1]['t1']; D = T1 - T0
    st = float(g[0].get('start', 0))
    if cd - st - .1 < D: st = max(0.0, cd - .1 - D)
    speed = round(max(.6, min(1.0, (cd - st - .1) / D)), 3)
    for s in g:
        s['src'] = key; s['clip'] = f"{key}_{s['id']}"; s['frames'] = int(-(-(s['t1'] - s['t0']) * 30 // 1)) + 1
        s['start'] = round(st + (s['t0'] - T0) * speed, 3); s['speed'] = speed

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
    if s['type'] == 'surnames' and s['grow'] > .5: extra += [s['t0'] + .3 + s['grow'] * k / 7 for k in range(1, 8)]  # a generation every grow/7 s
    ts = sorted(set([s['t0']] + [t for t in beat_times({k: v for k, v in s.items() if k not in ('t0', 't1')}) + extra if s['t0'] < t < s['t1']] + [s['t1']]))
    gaps.append((max(b_ - a_ for a_, b_ in zip(ts, ts[1:])), s['id'], s['type'], s['anchor'][:48]))
bad = sorted([g for g in gaps if g[0] > 5.5], reverse=True)
print(f"longest stretch without a visual change: {max(gaps)[0]:.1f}s; stretches over 5.5 s: {len(bad)}")
for g in bad[:40]: print(f"   {g[0]:.1f}s #{g[1]} {g[2]} '{g[3]}'")
slow = []
for s in out:
    if s['type'] in ('card', 'list', 'compare'):
        ats = [L['at'] for L in s.get('lines', [])] + [x['at'] for x in s.get('items', [])] + [c['at'] for c in s.get('cols', [])]
        first = min(ats) if ats else s['t0']
        if (s.get('text') is None and not s.get('title')) and first - s['t0'] > .8: slow.append((round(first - s['t0'], 1), s['id'], s['anchor'][:48]))
print('cards/charts whose content starts late:', len(slow)); [print('   ', x) for x in slow]
lost = []
for s in out:
    if s['type'] in ('endcard', 'verdict'): continue  # the verdict board is filled across several shots
    for t in beat_times({k: v for k, v in s.items() if k not in ('t0', 't1', 'cam', 'reframes')}):
        if t >= s['t1'] - .2 and not any(o['_use'] == s['_use'] and o['t0'] <= t < o['t1'] - .2 for o in out): lost.append((s['id'], s['type'], round(t - s['t1'], 2), s['anchor'][:48]))
print('timed elements that never show (at/after shot end):', len(lost)); [print('   ', x) for x in lost]
INTEGRAL = {'pa_title', 'pa_hand', 'hands', 'skull'}  # the title page and the two key pieces of evidence, recalled in the verdict
uses = {}
for s in out:
    keys = [s.get('img'), s.get('clip')] + [x['img'] for x in s.get('items', []) if isinstance(x, dict) and 'img' in x]
    for k in keys:
        if k: uses.setdefault(k, set()).add(s['_use'])
over = {k: len(v) for k, v in uses.items() if len(v) > 2 and k not in INTEGRAL}
print('images/clips used more than twice:', over if over else 'none')
