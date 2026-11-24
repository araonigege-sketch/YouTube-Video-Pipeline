"""Build vo/vo.wav from the owner's Drive recordings: drop the title read, splice in the re-recorded lines.

  python projects/giant-ships/vo/splice.py      (run from the repo root; inputs in vo/drive/, clean-header copies)
Cuts land at the quietest 20 ms inside each pause; each insert is level-matched (RMS of speech) to the main read
and joined with 8 ms fades. Writes vo/vo.wav + vo/splice.json (the edit list, for word-time remapping).
"""
import json
import subprocess
from pathlib import Path

import numpy as np

D = Path(__file__).resolve().parent
SR = 24000


def load(name):
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(D / "drive" / name), "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(pcm, np.int16).astype(np.float32) / 32768.0


def quiet(x, a, b, win=0.02):
    """Time of the quietest window between a and b (seconds)."""
    i0, i1, w = int(a * SR), int(b * SR), int(win * SR)
    seg = x[i0:i1]
    e = np.convolve(seg ** 2, np.ones(w) / w, "same")
    return (i0 + int(np.argmin(e))) / SR


def speech_rms(x):
    f = x[: len(x) // 480 * 480].reshape(-1, 480)
    r = np.sqrt((f ** 2).mean(1))
    return float(np.sqrt((r[r > r.max() * 0.1] ** 2).mean()))


def trim(x, thr=0.012, pad=0.06):
    f = np.abs(x)
    idx = np.where(f > thr)[0]
    a = max(0, idx[0] - int(pad * SR))
    b = min(len(x), idx[-1] + int(pad * SR))
    return x[a:b]


def fade(x, ms=8):
    n = int(ms / 1000 * SR)
    x = x.copy()
    x[:n] *= np.linspace(0, 1, n)
    x[-n:] *= np.linspace(1, 0, n)
    return x


main = load("main_1136.clean.wav")
ref = speech_rms(main)
fix1 = trim(load("fix_1146.clean.wav"))
fix2 = trim(load("fix_1148.clean.wav"))
fix1 *= ref / speech_rms(fix1)
fix2 *= ref / speech_rms(fix2)

# cut points (seconds in the main read), from the Whisper word times in vo/drive/main_1136.heard.json
c0 = quiet(main, 3.80, 3.95)                     # title "Why the world's biggest ships..." ends → "Hey there!"
a1, b1 = quiet(main, 32.12, 32.72), quiet(main, 36.95, 37.80)    # "And here's the funny part ... born in America."
a2, b2 = quiet(main, 115.24, 115.76), quiet(main, 125.88, 126.60)  # "So when a ship has a capacity of 24,346 ... boxes."
lead = 0.2                                      # breath before "Hey there"
parts = [
    ("main", c0, a1), ("fix_1146", 0, len(fix1) / SR), ("main", b1, a2), ("fix_1148", 0, len(fix2) / SR), ("main", b2, len(main) / SR),
]
src = {"main": main, "fix_1146": fix1, "fix_1148": fix2}
gap = np.zeros(int(0.12 * SR), np.float32)       # inserts are trimmed tight: give them back a short natural pause
out = [np.zeros(int(lead * SR), np.float32)]
edl, t = [], lead
for name, a, b in parts:
    seg = fade(src[name][int(a * SR): int(b * SR)])
    if name != "main":
        seg = np.concatenate([gap, seg, gap])
        edl.append({"src": name, "src_start": a, "src_end": b, "out_start": t + len(gap) / SR, "pad": len(gap) / SR})
    else:
        edl.append({"src": name, "src_start": a, "src_end": b, "out_start": t})
    out.append(seg)
    t += len(seg) / SR
y = np.concatenate(out)
pcm = (np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes()
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-", "-c:a", "pcm_s16le", str(D / "vo.wav")],
               input=pcm, check=True)
(D / "splice.json").write_text(json.dumps({"cuts": edl, "duration": len(y) / SR}, indent=1))
print(json.dumps(edl, indent=1), f"\nvo.wav {len(y) / SR:.2f}s")
