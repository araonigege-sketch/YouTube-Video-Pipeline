"""ElevenLabs voiceover for an episode: one request per paragraph, stitched into vo/vo.wav + words.json.

  python -m pipeline.eleven <project_dir> [--voice ID] [--model eleven_v4] [--redo 12,14] [--gap 0.45]

Reads vo/vo.txt (paragraphs separated by blank lines). Each paragraph is generated with the paragraphs around it as
`previous_text` / `next_text` so the read flows, and cached in vo/parts/pNN.{mp3,json} keyed by a hash of its text and
settings: editing one paragraph (or `--redo N`) regenerates only that one. Word times come from ElevenLabs' own
character alignment, so no transcription is needed; `--verify` also runs Whisper and lists words it heard differently
(spot numbers and names read wrongly).
The API key is injected by the sandbox proxy (ELEVENLABS_API_KEY secret); never put it in files.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

import numpy as np
import requests

API = "https://api.elevenlabs.io/v1"
SR = 44100


def _key():
    return os.environ.get("ELEVENLABS_API_KEY", "proxy-injected")


def tts(text, voice, model, prev=None, nxt=None, settings=None):
    body = {"text": text, "model_id": model}
    if prev:
        body["previous_text"] = prev
    if nxt:
        body["next_text"] = nxt
    if settings:
        body["voice_settings"] = settings
    r = requests.post(f"{API}/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_192",
                      headers={"xi-api-key": _key()}, json=body, timeout=300)
    if r.status_code != 200:
        raise SystemExit(f"ElevenLabs {r.status_code}: {r.text[:400]}")
    return r.json()


def words_from_alignment(al, offset):
    """Characters + start/end times → [{w, s, e}] split on whitespace."""
    out, cur, s, e = [], "", None, None
    for ch, a, b in zip(al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]):
        if ch.isspace():
            if cur.strip():
                out.append({"w": cur, "s": round(offset + s, 3), "e": round(offset + e, 3)})
            cur, s = "", None
            continue
        if s is None:
            s = a
        cur, e = cur + ch, b
    if cur.strip():
        out.append({"w": cur, "s": round(offset + s, 3), "e": round(offset + e, 3)})
    return out


def decode(mp3: Path):
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp3), "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(pcm, np.int16).astype(np.float32) / 32768.0


def build(P: Path, voice, model, gap=0.45, lead=0.25, redo=(), settings=None):
    paras = [re.sub(r"\s+", " ", p).strip() for p in (P / "vo/vo.txt").read_text().split("\n\n") if p.strip()]
    parts = P / "vo/parts"
    parts.mkdir(parents=True, exist_ok=True)
    out = [np.zeros(int(lead * SR), np.float32)]
    t, words, used = lead, [], 0
    for i, text in enumerate(paras):
        prev = " ".join(paras[max(0, i - 2):i])[-1000:] or None
        nxt = paras[i + 1][:500] if i + 1 < len(paras) else None
        key = hashlib.sha1(json.dumps([text, prev, nxt, voice, model, settings]).encode()).hexdigest()[:12]
        mp3, js = parts / f"p{i:02d}.mp3", parts / f"p{i:02d}.json"
        meta = json.loads(js.read_text()) if js.exists() else {}
        if meta.get("key") != key or i in redo or not mp3.exists():
            d = tts(text, voice, model, prev, nxt, settings)
            mp3.write_bytes(base64.b64decode(d["audio_base64"]))
            meta = {"key": key, "text": text, "alignment": d["alignment"]}
            js.write_text(json.dumps(meta))
            used += len(text)
            print(f"  p{i:02d} generated ({len(text)} chars)")
        x = decode(mp3)
        words += words_from_alignment(meta["alignment"], t)
        out += [x, np.zeros(int(gap * SR), np.float32)]
        t += len(x) / SR + gap
    y = np.concatenate(out)
    pcm = (np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-",
                    "-c:a", "pcm_s16le", str(P / "vo/vo.wav")], input=pcm, check=True)
    from pipeline.align.whisper_align import map_to_script
    (P / "words.raw.json").write_text(json.dumps(words, indent=0))
    mapped = map_to_script((P / "vo/vo.txt").read_text(), words)
    (P / "words.json").write_text(json.dumps(mapped, indent=0))
    print(f"vo.wav {len(y) / SR:.2f}s, {len(paras)} paragraphs, {len(mapped)} words, {used} characters billed")
    return paras


def verify(P: Path):
    """Whisper the finished read and list words it heard differently from the script (by paragraph)."""
    from pipeline.align.whisper_align import transcribe, norm
    heard = transcribe(str(P / "vo/vo.wav"), "small.en")
    script = json.loads((P / "words.json").read_text())
    hn = [norm(w["w"]) for w in heard]
    issues = []
    for w in script:
        near = [hn[k] for k, h in enumerate(heard) if abs(h["s"] - w["s"]) < 0.6]
        if norm(w["w"]) and norm(w["w"]) not in near and not any(norm(w["w"]) in n or n in norm(w["w"]) for n in near if n):
            issues.append((w["s"], w["w"], near))
    for s, w, near in issues:
        print(f"  {int(s // 60)}:{s % 60:05.2f}  script {w!r}  heard {near}")
    print(f"{len(issues)} word(s) to listen to")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--voice", default=None)
    ap.add_argument("--model", default=None)
    ap.add_argument("--gap", type=float, default=0.45)
    ap.add_argument("--redo", default="")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    P = Path(a.project)
    import yaml
    ep = yaml.safe_load((P / "episode.yaml").read_text())
    tv = ep.get("tts", {})
    build(P, a.voice or tv["voice"], a.model or tv.get("model", "eleven_v4"), a.gap,
          redo={int(x) for x in a.redo.split(",") if x}, settings=tv.get("settings"))
    if a.verify:
        verify(P)
