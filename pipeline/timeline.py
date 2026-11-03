"""Align scenes to the narration audio and build the shot timeline.

Each voice chunk covers several scenes. Scene boundaries are estimated from
character counts, then snapped to the nearest real pause (silencedetect) so
cuts land between sentences, not mid-word.
"""
from __future__ import annotations

from pathlib import Path

from .util import detect_silences, duration


def align_chunk(audio: Path, scenes: list[dict], offset: float, snap_window: float = 2.5) -> float:
    dur = duration(audio)
    sil = detect_silences(audio)
    lead = sil[0][1] if sil and sil[0][0] <= 0.05 else 0.0
    trail = sil[-1][0] if sil and sil[-1][1] >= dur - 0.05 else dur
    if trail <= lead:
        lead, trail = 0.0, dur
    span = trail - lead
    interior = [s for s in sil if s[0] > lead + 0.1 and s[1] < trail - 0.1]

    weights = [len(s["text"]) + 1 for s in scenes]
    total = sum(weights)
    cum = 0
    prev_cut = 0.0
    speech_start = lead
    for i, sc in enumerate(scenes):
        sc["speech0"] = offset + speech_start
        sc["t0"] = offset + prev_cut
        if i == len(scenes) - 1:
            sc["speech1"], sc["t1"] = offset + trail, offset + dur
            break
        cum += weights[i]
        est = lead + span * cum / total
        cands = [s for s in interior if (s[0] + s[1]) / 2 > prev_cut + 0.5 and abs((s[0] + s[1]) / 2 - est) <= snap_window]
        if cands:
            s0, s1 = min(cands, key=lambda s: abs((s[0] + s[1]) / 2 - est))
            speech_end, speech_start = s0, s1
            cut = max((s0 + s1) / 2, s1 - 0.15)
        else:
            speech_end = speech_start = cut = est
        sc["speech1"], sc["t1"] = offset + speech_end, offset + cut
        prev_cut = cut
    for sc in scenes:  # pauses inside each scene's speech, used to sync captions
        sc["pauses"] = [(offset + a, offset + b) for a, b in interior
                        if a > sc["speech0"] - offset + 0.05 and b < sc["speech1"] - offset - 0.05]
    return dur


def build_timeline(plan: dict, chunk_audio: dict[str, Path], fps: int, tail: float) -> dict:
    scenes_by_chunk: dict[str, list[dict]] = {}
    for sc in plan["scenes"]:
        scenes_by_chunk.setdefault(sc["chunk"], []).append(sc)
    offset = 0.0
    for ch in plan["voice_chunks"]:
        offset += align_chunk(chunk_audio[ch["id"]], scenes_by_chunk[ch["id"]], offset)
    narration = offset
    plan["scenes"][-1]["t1"] = narration + tail
    total = narration + tail

    # Frame-accurate shot boundaries: scene spans are contiguous, shots split them evenly.
    shots = []
    for sc in plan["scenes"]:
        f0, f1 = round(sc["t0"] * fps), round(sc["t1"] * fps)
        n = len(sc["shots"])
        for k, shot in enumerate(sc["shots"]):
            a = f0 + (f1 - f0) * k // n
            b = f0 + (f1 - f0) * (k + 1) // n
            shots.append({**shot, "scene": sc["id"], "frames": b - a, "start": a / fps})
    return {"narration_seconds": narration, "total_seconds": round(total * fps) / fps, "shots": shots}
