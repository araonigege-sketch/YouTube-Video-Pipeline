# Synthesized foley for the cold open (no outside recordings): paper, stamp, pen, type, whoosh.
import numpy as np, wave
from scipy.signal import butter, sosfilt
SR = 48000; DUR = 60.6
rng = np.random.default_rng(5)
L = np.zeros(int(SR * DUR)); R = np.zeros_like(L)
def bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], 'bandpass', fs=SR, output='sos'), x)
def lp(x, f, o=2): return sosfilt(butter(o, f, 'lowpass', fs=SR, output='sos'), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'highpass', fs=SR, output='sos'), x)
def put(t, x, gain_db, pan=0.0):
    i = int(t * SR); x = x * 10 ** (gain_db / 20); n = min(len(x), len(L) - i)
    if n <= 0: return
    L[i:i + n] += x[:n] * np.sqrt((1 - pan) / 2) * 1.414; R[i:i + n] += x[:n] * np.sqrt((1 + pan) / 2) * 1.414
def env(n, a, d):  # attack/decay in seconds
    t = np.arange(n) / SR; e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) / d); return e
def paper(dur=0.45, bright=1.0):
    n = int(SR * dur); x = rng.standard_normal(n)
    x = bp(x, 900 * bright, 7000 * bright)
    grain = lp(np.abs(rng.standard_normal(n)), 40) ; grain = 0.5 + grain / grain.max()
    t = np.arange(n) / SR; e = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.8 * np.exp(-t / (dur * 0.7))
    return x * e * grain / np.abs(x).max()
def stamp():
    n = int(SR * 0.45); t = np.arange(n) / SR
    f = 95 * np.exp(-t * 6) + 45; thump = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 0.07)
    click = lp(rng.standard_normal(n), 3500) * env(n, 0.0005, 0.012)
    body = bp(rng.standard_normal(n), 150, 900) * env(n, 0.001, 0.05)
    x = thump * 1.0 + click * 0.6 + body * 0.5
    return x / np.abs(x).max()
def pen(dur):
    n = int(SR * dur); x = bp(rng.standard_normal(n), 2500, 9000)
    t = np.arange(n) / SR; strokes = 0.55 + 0.45 * np.sin(2 * np.pi * 9 * t + rng.random() * 6) ** 2
    e = np.minimum(1, t / 0.04) * np.minimum(1, (dur - t) / 0.06)
    return x * strokes * e / np.abs(x).max()
def key():
    n = int(SR * 0.05); x = hp(rng.standard_normal(n), 2500) * env(n, 0.0003, 0.006)
    t = np.arange(n) / SR; ping = np.sin(2 * np.pi * 1800 * t) * env(n, 0.0005, 0.01) * 0.4
    y = x + ping; return y / np.abs(y).max()
def whoosh(dur, lo=200, hi=2500):
    n = int(SR * dur); x = rng.standard_normal(n); t = np.arange(n) / SR
    out = np.zeros(n); seg = 2048
    for s in range(0, n, seg):
        u = s / n; fc = lo + (hi - lo) * np.sin(np.pi * u)
        out[s:s + seg] = lp(x[s:s + seg], fc, 1)
    e = np.sin(np.pi * t / dur) ** 2; return out * e / np.abs(out).max()
def riser(dur):
    n = int(SR * dur); t = np.arange(n) / SR
    base = sum(np.sin(2 * np.pi * f * t * (1 + 0.15 * t / dur)) for f in (55, 82.5, 110)) / 3
    air = lp(rng.standard_normal(n), 900) * 0.3
    e = (t / dur) ** 1.5 * np.minimum(1, (dur - t) / 0.4); y = (base + air) * e; return y / np.abs(y).max()

# --- cue sheet (seconds, matched to film.html) ---
for t, g, p in [(0.0, -20, 0), (6.3, -21, .4), (11.6, -22, -.2), (15.1, -22, -.3), (16.25, -20, .3), (20.4, -21, 0),
                (21.6, -23, .5), (40.14, -21, 0), (51.08, -22, -.4), (52.71, -22, 0), (54.25, -22, .4)]:
    put(t, paper(), g, p)
put(2.35, paper(0.6, 0.8), -24, 0); put(9.55, paper(0.4, 0.8), -26, 0); put(28.3, paper(0.4, 0.8), -26, 0)
put(31.95, paper(0.4, 0.8), -26, 0); put(55.65, paper(0.5, 0.8), -25, 0); put(26.05, paper(0.35), -24, 0)
for t, p in [(4.0, -.3), (8.3, .4), (13.25, .4), (38.7, 0)]: put(t, stamp(), -12, p)
for t0, t1, g in [(2.8, 3.75, -28), (9.8, 10.9, -28), (33.0, 33.9, -26), (23.2, 23.7, -32), (28.2, 28.6, -32), (30.3, 30.6, -32)]:
    put(t0, pen(t1 - t0), g, 0)
for t0, text_len, rate in [(0.15, 16, .035), (15.3, 11, .055)]:
    for k in range(text_len): put(t0 + k * rate + rng.random() * .01, key(), -27, -.2 + .4 * rng.random())
put(35.5, whoosh(0.8), -26, .3)
put(45.4, riser(4.2), -24, 0)
put(55.6, whoosh(0.9, 150, 1500), -28, 0)
mix = np.stack([L, R], 1); peak = np.abs(mix).max(); mix = mix / max(peak, 1) * 0.98
with wave.open('audio/sfx.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype('<i2').tobytes())
print('sfx.wav', round(DUR, 1), 's, peak', round(peak, 3))
