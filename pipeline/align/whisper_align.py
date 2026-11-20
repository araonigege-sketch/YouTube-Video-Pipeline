"""Word timings from Whisper (faster-whisper), mapped onto the exact script tokens.

More accurate than the PocketSphinx paragraph fallback on long, natural reads (sentence ends within
~0.1 s instead of up to seconds). Script tokens that Whisper didn't hear (or heard differently) get
times interpolated between their matched neighbours.

  python -m pipeline.align.whisper_align <audio> <script.txt> <out words.json> [--model small.en]
"""
from __future__ import annotations

import difflib
import json
import re
import sys
from pathlib import Path

NUM = {"0": "zero", "1": "one", "2": "two", "3": "three", "4": "four", "5": "five", "6": "six", "7": "seven",
       "8": "eight", "9": "nine"}


def norm(t: str) -> str:
    return re.sub(r"[^a-z0-9]", "", t.lower().replace("’", "'"))


def transcribe(audio: str, model: str = "small.en") -> list[dict]:
    import subprocess

    import numpy as np
    from faster_whisper import WhisperModel
    # decode with ffmpeg (avoids PyAV version mismatches)
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", audio, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    samples = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768.0
    m = WhisperModel(model, device="cpu", compute_type="int8")
    segs, _ = m.transcribe(samples, word_timestamps=True, beam_size=5, vad_filter=False, language="en")
    out = []
    for s in segs:
        for w in s.words or []:
            out.append({"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3)})
    return out


def map_to_script(script: str, heard: list[dict]) -> list[dict]:
    toks = script.split()
    a = [norm(t) for t in toks]
    b = [norm(h["w"]) for h in heard]
    times: list[tuple[float, float] | None] = [None] * len(toks)
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                times[i1 + k] = (heard[j1 + k]["s"], heard[j1 + k]["e"])
        elif tag == "replace" and j2 > j1:
            # e.g. "1,500" vs "1,500" / "fifteen hundred": spread the heard span over the script tokens
            s0, e0 = heard[j1]["s"], heard[j2 - 1]["e"]
            n = i2 - i1
            for k in range(n):
                times[i1 + k] = (s0 + (e0 - s0) * k / n, s0 + (e0 - s0) * (k + 1) / n)
    # interpolate gaps
    known = [i for i, t in enumerate(times) if t]
    for i, t in enumerate(times):
        if t:
            continue
        prv = max((k for k in known if k < i), default=None)
        nxt = min((k for k in known if k > i), default=None)
        s = times[prv][1] if prv is not None else 0.0
        e = times[nxt][0] if nxt is not None else s + 0.3
        span = (nxt if nxt is not None else i + 1) - (prv if prv is not None else -1) - 1
        pos = i - (prv if prv is not None else -1) - 1
        st = s + (e - s) * pos / max(1, span)
        times[i] = (st, st + (e - s) / max(1, span))
    words = [{"w": t, "s": round(x[0], 3), "e": round(max(x[1], x[0] + 0.05), 3)} for t, x in zip(toks, times)]
    matched = sum(1 for tag, i1, i2, *_ in sm.get_opcodes() if tag == "equal" for _ in range(i2 - i1))
    print(f"matched {matched}/{len(toks)} script tokens exactly", file=sys.stderr)
    return words


if __name__ == "__main__":
    audio, script, out = sys.argv[1:4]
    model = sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else "small.en"
    cache = Path(out).with_suffix(".whisper.json")
    heard = json.loads(cache.read_text()) if cache.exists() else transcribe(audio, model)
    cache.write_text(json.dumps(heard))
    words = map_to_script(Path(script).read_text(), heard)
    Path(out).write_text(json.dumps(words, ensure_ascii=False))
    print(f"{len(words)} words, ends {words[-1]['e']:.2f}s")
