#!/usr/bin/env python3
"""Final audio for the full episode: narration + sectioned music + foley generated from the shot list.

Levels follow the Finance pipeline (owner-approved): music normalised to -17 LUFS, bed gain 0.12 x 0.63
(owner, 2026-11-10: "music may be too loud" -> 4 dB lower than the sample), dipping to 70% under speech;
effects at least 6 dB under the voice, cut to 40% under speech, never two within 0.12 s; master -14 LUFS.

  python3 tools/mix.py --narration <narration.wav> --music-dir <dir> --out <mix.wav>
"""
import argparse, json, os, subprocess, sys
import numpy as np
from scipy.signal import butter, sosfilt

ap = argparse.ArgumentParser()
ap.add_argument('--narration', required=True); ap.add_argument('--music-dir', required=True); ap.add_argument('--out', required=True)
ap.add_argument('--music-gain', type=float, default=0.12 * 0.63); ap.add_argument('--sfx-gain', type=float, default=0.25)
a = ap.parse_args()
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 48000
shots = json.loads(open(f'{P}/film2/shots.js').read().split('window.SHOTS=', 1)[1].rstrip().rstrip(';'))
END = json.load(open(f'{P}/film2/film.json'))['end']
N = int(END * SR) + SR

def load(path, start=0.0, dur=None, norm=None):
    af = []
    if norm: af.append(f'loudnorm=I={norm}:TP=-2:LRA=11')
    cmd = ['ffmpeg', '-v', 'error', '-ss', str(start), '-i', path] + (['-t', str(dur)] if dur else []) + (['-af', ','.join(af)] if af else []) + ['-ac', '2', '-ar', str(SR), '-f', 'f32le', '-']
    x = np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, dtype=np.float32).reshape(-1, 2)
    return x.copy()

# ---- narration and speech mask
voice = load(a.narration)
V = np.zeros((N, 2), np.float32); V[:len(voice)] = voice[:N]
mono = np.abs(V[:, 0]); hop = 480
env = np.sqrt(np.convolve(mono[:len(mono) // hop * hop].reshape(-1, hop).mean(1) ** 2, np.ones(3) / 3, 'same'))
speech = (env > 10 ** (-45 / 20)).astype(float)
def smooth(mask, att, rel, look):  # per-10ms mask -> per-sample gain envelope with attack/release and look-ahead
    sh = int(look / .01); m = np.concatenate([mask[sh:], np.zeros(sh)]); out = np.zeros_like(m); g = 0.0
    a_, r_ = 1 - np.exp(-.01 / att), 1 - np.exp(-.01 / rel)
    for i, v in enumerate(m): g += (v - g) * (a_ if v > g else r_); out[i] = g
    return np.repeat(out, hop)[:N] if len(out) * hop >= N else np.pad(np.repeat(out, hop), (0, N - len(out) * hop))
sp = smooth(speech, .03, .25, .1)

# ---- music: sections with 3 s crossfades
PLAN = [(0, 124, '01_hook', 0), (121, 293, '02_genesis', 0), (290, 455, '03_scholar', 0), (452, 627, '04_deeptime', 0), (624, 799, '05_dna', 0),
        (796, 973, '06_faiths', 0), (970, 1141, '02_genesis', 0), (1138, 1271, '06_faiths', 40), (1268, 1388, '05_dna', 50), (1385, 1450, '07_questions', 0),
        (1447, 1505, '08_dark', 0), (1502, 1558, '07_questions', 70), (1555, 1731, '09_verdict', 0), (1728, END, '01_hook', 0)]
M = np.zeros((N, 2), np.float32); XF = 3.0
for i, (t0, t1, name, off) in enumerate(PLAN):
    x = load(f'{a.music_dir}/music_{name}.wav', off, t1 - t0, norm=-17)
    n = min(len(x), int((t1 - t0) * SR)); x = x[:n]
    fi = int((XF if i else 1.0) * SR); fo = int((XF if i + 1 < len(PLAN) else 3.0) * SR)
    ramp = np.ones(n); ramp[:fi] = np.linspace(0, 1, fi) ** .7
    if n > fo: ramp[-fo:] *= np.linspace(1, 0, fo) ** .7
    else: ramp *= np.linspace(1, 0, n)
    s = int(t0 * SR); M[s:s + n] += x * ramp[:, None]
M *= a.music_gain * (1 - .30 * sp)[:, None]

# ---- foley from the shot list (synthesized, as approved for the cold-open test)
rng = np.random.default_rng(5)
def bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], 'bandpass', fs=SR, output='sos'), x)
def lp(x, f, o=2): return sosfilt(butter(o, f, 'lowpass', fs=SR, output='sos'), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'highpass', fs=SR, output='sos'), x)
def env_(n, at, d): t = np.arange(n) / SR; return np.minimum(1, t / max(at, 1e-4)) * np.exp(-np.maximum(0, t - at) / d)
def paper(dur=.45, bright=1.0):
    n = int(SR * dur); x = bp(rng.standard_normal(n), 900 * bright, 7000 * bright)
    grain = lp(np.abs(rng.standard_normal(n)), 40); grain = .5 + grain / grain.max(); t = np.arange(n) / SR
    e = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** .8 * np.exp(-t / (dur * .7)); y = x * e * grain; return y / np.abs(y).max()
def stamp_s():
    n = int(SR * .45); t = np.arange(n) / SR; f = 95 * np.exp(-t * 6) + 45
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_(n, .002, .07) + .6 * lp(rng.standard_normal(n), 3500) * env_(n, .0005, .012) + .5 * bp(rng.standard_normal(n), 150, 900) * env_(n, .001, .05)
    return y / np.abs(y).max()
def pen(dur):
    n = int(SR * dur); x = bp(rng.standard_normal(n), 2500, 9000); t = np.arange(n) / SR
    y = x * (.55 + .45 * np.sin(2 * np.pi * 9 * t + rng.random() * 6) ** 2) * np.minimum(1, t / .04) * np.minimum(1, (dur - t) / .06); return y / np.abs(y).max()
def key():
    n = int(SR * .05); x = hp(rng.standard_normal(n), 2500) * env_(n, .0003, .006); t = np.arange(n) / SR
    y = x + .4 * np.sin(2 * np.pi * 1800 * t) * env_(n, .0005, .01); return y / np.abs(y).max()
def whoosh(dur, lo=200, hi=2500):
    n = int(SR * dur); x = rng.standard_normal(n); out = np.zeros(n); seg = 2048
    for s in range(0, n, seg): u = s / n; out[s:s + seg] = lp(x[s:s + seg], lo + (hi - lo) * np.sin(np.pi * u), 1)
    y = out * np.sin(np.pi * np.arange(n) / n) ** 2; return y / np.abs(y).max()

FX = np.zeros(N, np.float32); last = [-1.0]
def put(t, y, db):
    if t is None or not isinstance(t, (int, float)) or t < 0 or t >= END: return
    if abs(t - last[0]) < .12: return
    last[0] = t; i = int(t * SR); n = min(len(y), N - i); FX[i:i + n] += (y[:n] * 10 ** (db / 20)).astype(np.float32)
events = []
for s in shots:
    if s.get('arrive') and s['type'] in ('sheet', 'card', 'list', 'compare', 'timeline', 'tree', 'frame', 'page'): events.append((s['t0'], 'paper'))
    for it in s.get('items', []) if s['type'] == 'spread' else []: events.append((it['at'], 'paper'))
    st = s.get('stamp');
    if st and isinstance(st.get('at'), (int, float)) and s['t0'] <= st['at'] < s['t1']: events.append((st['at'], 'stamp'))
    for st in s.get('stamps', []):
        if isinstance(st.get('at'), (int, float)) and s['t0'] <= st['at'] < s['t1']: events.append((st['at'], 'stamp'))
    for r in s.get('routes', []):
        if isinstance(r.get('at'), (int, float)) and s['t0'] <= r['at'] < s['t1']: events.append((r['at'], ('pen', r.get('dur', 1))))
    for u in s.get('underline', []) + s.get('ring', []): events.append((u['at'], ('pen', .7)))
    if s.get('loupe'): events.append((s['loupe']['at'], 'whoosh'))
    if s.get('strip'): events.append((s['t0'] + .1, ('type', len(s['strip']))))
    if s['type'] in ('map_eu', 'map_world', 'map') and s['t0'] > 0: events.append((s['t0'], 'paper2'))
for t, kind in sorted(events, key=lambda e: e[0]):
    if kind == 'paper': put(t, paper(), -18)
    elif kind == 'paper2': put(t, paper(.6, .8), -21)
    elif kind == 'stamp': put(t, stamp_s(), -10)
    elif kind == 'whoosh': put(t, whoosh(.8), -22)
    elif kind[0] == 'pen': put(t, pen(min(1.2, kind[1])), -24)
    elif kind[0] == 'type':
        for k in range(min(kind[1], 24)): last[0] = -1; put(t + k * .035, key(), -25)
FX = FX * a.sfx_gain * 4 * (1 - .6 * sp)  # gain 0.25 overall (x4 compensates the per-event dB above), 40% under speech
FX2 = np.stack([FX, FX], 1)

mix = V + M + FX2
peak = float(np.abs(mix).max()); mix = mix / max(1.0, peak / .98)
tmp = a.out + '.raw.wav'
import wave
with wave.open(tmp, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(mix[:int(END * SR)], -1, 1) * 32767).astype('<i2').tobytes())
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmp, '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-ar', str(SR), a.out], check=True); os.remove(tmp)
print(f'mixed {END:.1f}s -> {a.out}; {len(events)} foley events; pre-master peak {peak:.2f}')
