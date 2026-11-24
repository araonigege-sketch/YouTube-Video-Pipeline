"""Build vo/vo.wav from the owner's recordings: drop the title read, splice in the re-recorded lines.

  python projects/giant-ships/vo/splice.py      (any cwd; inputs in vo/drive/: clean-header copies *.clean.wav
                                                 and their Whisper words *.heard.json)
Cuts land at the quietest 20 ms inside each pause; each insert is level-matched (RMS of speech) to the main read
and joined with 8 ms fades. Writes vo/vo.wav, vo/splice.json (the edit list) and, from the Whisper words of each
piece, ../words.whisper.json + ../words.json (mapped onto the script), so no re-transcription is needed.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

D = Path(__file__).resolve().parent
P = D.parent
sys.path.insert(0, str(P.parent.parent))
SR = 24000

# Inserts, in script order: (file stem, replace main from the quiet point in [a0, a1] to the quiet point in [b0, b1],
#                            pause before, pause after). Windows come from the Whisper word times of the main read.
INSERTS = [
    ("fix_1146", (32.12, 32.72), (36.95, 37.80), 0.12, 0.12),     # "And here's the funny part ... born in America."
    ("fix_1148", (115.24, 115.76), (125.88, 126.60), 0.12, 0.12),  # "So when a ship has a capacity of 24,346 ... boxes."
    ("fix_1229", (494.14, 494.36), (496.95, 497.58), 0.05, 0.16),  # "23,656 TEU" (MSC Isabella; the main read said 23,668)
]
TITLE_END = (3.80, 3.95)        # title "Why the world's biggest ships..." ends → "Hey there!"
LEAD = 0.2


def load(name):
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(D / "drive" / f"{name}.clean.wav"), "-ac", "1", "-ar", str(SR),
                          "-f", "s16le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(pcm, np.int16).astype(np.float32) / 32768.0


def quiet(x, a, b, win=0.02):
    i0, i1, w = int(a * SR), int(b * SR), int(win * SR)
    e = np.convolve(x[i0:i1] ** 2, np.ones(w) / w, "same")
    return (i0 + int(np.argmin(e))) / SR


def speech_rms(x):
    f = x[: len(x) // 480 * 480].reshape(-1, 480)
    r = np.sqrt((f ** 2).mean(1))
    return float(np.sqrt((r[r > r.max() * 0.1] ** 2).mean()))


def trim(x, thr=0.012, pad=0.06):
    idx = np.where(np.abs(x) > thr)[0]
    a, b = max(0, idx[0] - int(pad * SR)), min(len(x), idx[-1] + int(pad * SR))
    return x[a:b], a / SR


def fade(x, ms=8):
    n = int(ms / 1000 * SR)
    x = x.copy()
    x[:n] *= np.linspace(0, 1, n)
    x[-n:] *= np.linspace(1, 0, n)
    return x


main = load("main_1136")
ref = speech_rms(main)
heard_main = json.loads((D / "drive/main_1136.heard.json").read_text())
out = [np.zeros(int(LEAD * SR), np.float32)]
t, cur = LEAD, quiet(main, *TITLE_END)
edl, heard = [], []


def put_main(a, b):
    global t
    seg = fade(main[int(a * SR): int(b * SR)])
    edl.append({"src": "main_1136", "src_start": a, "src_end": b, "out_start": t})
    heard.extend({"w": w["w"], "s": round(t + w["s"] - a, 3), "e": round(t + w["e"] - a, 3)}
                 for w in heard_main if a - 0.05 <= w["s"] and w["e"] <= b + 0.05)
    out.append(seg)
    t += len(seg) / SR


for name, wa, wb, pre, post in INSERTS:
    a, b = quiet(main, *wa), quiet(main, *wb)
    put_main(cur, a)
    x, off = trim(load(name))
    x = fade(x * ref / speech_rms(x))
    seg = np.concatenate([np.zeros(int(pre * SR), np.float32), x, np.zeros(int(post * SR), np.float32)])
    edl.append({"src": name, "replaces": [a, b], "out_start": t + pre, "dur": len(x) / SR})
    heard.extend({"w": w["w"], "s": round(t + pre + w["s"] - off, 3), "e": round(t + pre + w["e"] - off, 3)}
                 for w in json.loads((D / "drive" / f"{name}.heard.json").read_text()))
    out.append(seg)
    t += len(seg) / SR
    cur = b
put_main(cur, len(main) / SR)

y = np.concatenate(out)
pcm = (np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes()
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-", "-c:a", "pcm_s16le",
                str(D / "vo.wav")], input=pcm, check=True)
(D / "splice.json").write_text(json.dumps({"cuts": edl, "duration": len(y) / SR}, indent=1))
heard.sort(key=lambda w: w["s"])
(P / "words.whisper.json").write_text(json.dumps(heard, indent=0))
from pipeline.align.whisper_align import map_to_script  # noqa: E402
words = map_to_script((D / "vo.txt").read_text(), heard)
(P / "words.json").write_text(json.dumps(words, indent=0))
print(f"vo.wav {len(y) / SR:.2f}s, {len(edl)} pieces, {len(words)} script words")
