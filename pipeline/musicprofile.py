"""Objective profile of a music track, to pick beds without listening.

  python -m pipeline.musicprofile <file> [<file> ...]

Per track: duration, integrated loudness + loudness range (ffmpeg ebur128), estimated tempo
(spectral-flux autocorrelation), pulse strength (how regular the beat is), brightness (spectral
centroid), mid-range energy share (300–3000 Hz, where a voice sits: lower is kinder to narration),
and a 10-segment energy curve (to see builds, drops and quiet intros).
"""
from __future__ import annotations

import re
import subprocess
import sys

import numpy as np

SR = 22050


def _pcm(path: str) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0


def _loud(path: str) -> tuple[float, float]:
    err = subprocess.run(["ffmpeg", "-i", path, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", err)
    lra = re.findall(r"LRA:\s+([\d.]+) LU", err)
    return float(i[-1]), float(lra[-1])


def profile(path: str) -> dict:
    x = _pcm(path)
    n, hop = 2048, 512
    frames = np.lib.stride_tricks.sliding_window_view(x, n)[::hop] * np.hanning(n)
    S = np.abs(np.fft.rfft(frames, axis=1))
    f = np.fft.rfftfreq(n, 1 / SR)
    flux = np.maximum(0, np.diff(S, axis=0)).sum(1)
    flux = (flux - flux.mean()) / (flux.std() + 1e-9)
    fps = SR / hop
    ac = np.correlate(flux, flux, "full")[len(flux) - 1:]
    lags = np.arange(len(ac))
    lo, hi = int(fps * 60 / 180), int(fps * 60 / 60)
    k = lo + int(np.argmax(ac[lo:hi]))
    bpm = 60 * fps / k
    pulse = float(ac[k] / ac[0])
    cent = float((S * f).sum(1).mean() / (S.sum(1).mean() + 1e-9))
    mid = float(S[:, (f > 300) & (f < 3000)].sum() / (S.sum() + 1e-9))
    seg = np.array_split(x ** 2, 10)
    curve = [round(10 * np.log10(s.mean() + 1e-12), 1) for s in seg]
    I, LRA = _loud(path)
    return {"dur": round(len(x) / SR, 1), "lufs": I, "lra": LRA, "bpm": round(bpm, 1), "pulse": round(pulse, 2),
            "centroid_hz": round(cent), "voice_band": round(mid, 2), "curve_db": curve}


if __name__ == "__main__":
    for p in sys.argv[1:]:
        r = profile(p)
        print(f"{p.split('/')[-1]:28s} {r['dur']:6.1f}s  {r['lufs']:6.1f} LUFS  LRA {r['lra']:4.1f}  {r['bpm']:5.1f} bpm  "
              f"pulse {r['pulse']:.2f}  centroid {r['centroid_hz']:5d} Hz  voice-band {r['voice_band']:.2f}")
        print(" " * 30 + "energy " + " ".join(f"{v:5.1f}" for v in r["curve_db"]))
