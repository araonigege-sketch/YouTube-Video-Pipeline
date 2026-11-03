"""Word-level alignment of narration recordings to their script (PocketSphinx, offline).

For each voice part: try whole-file forced alignment (align.py); if the read is loose
or long and that fails, fall back to paragraph-anchored alignment (align_chunks.py).
Parts are joined with the channel's part gap, so the result matches the audio mix.

episode.yaml:
  voice:
    - {file: vo/part1.mp3, text: vo/part1.txt}   # or just "vo/part1.mp3" (text = same name .txt)
  lexicon: {bukhara: "B UW K AA R AH"}           # optional ARPABET pronunciations
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from ..util import PipelineError, duration, ffmpeg

HERE = Path(__file__).resolve().parent


def _parts(P: Path, voice: list) -> list[tuple[Path, Path]]:
    out = []
    for v in voice:
        f = v["file"] if isinstance(v, dict) else v
        t = v.get("text") if isinstance(v, dict) else None
        audio = P / f
        text = P / t if t else audio.with_suffix(".txt")
        if not audio.exists():
            raise PipelineError(f"missing recording {audio}")
        if not text.exists():
            raise PipelineError(f"missing script text for {audio.name}: {text}")
        out.append((audio, text))
    return out


def align_episode(P: Path, voice: list, gap: float, lexicon: dict | None = None, log=print) -> Path:
    P = Path(P)
    env = dict(os.environ)
    if lexicon:
        lx = P / "build/lexicon.json"
        lx.parent.mkdir(parents=True, exist_ok=True)
        lx.write_text(json.dumps(lexicon))
        env["ALIGN_LEXICON"] = str(lx)
    words, offset = [], 0.0
    vo_dir = P / "build/align"
    vo_dir.mkdir(parents=True, exist_ok=True)
    for i, (audio, text) in enumerate(_parts(P, voice), 1):
        out = vo_dir / f"w{i}.json"
        cmd = [sys.executable, str(HERE / "align.py"), str(audio), str(text), str(out), f"{offset:.3f}"]
        proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
        method = "forced"
        if proc.returncode != 0:
            wav = Path(tempfile.mktemp(suffix=".wav"))
            ffmpeg(["-i", audio, "-ar", "16000", "-ac", "1", wav])
            cmd = [sys.executable, str(HERE / "align_chunks.py"), str(wav), str(text), str(out), f"{offset:.3f}"]
            proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
            wav.unlink(missing_ok=True)
            method = "paragraph-anchored"
            if proc.returncode != 0:
                raise PipelineError(f"alignment failed for {audio.name}:\n{proc.stderr[-1500:]}")
        part = json.loads(out.read_text())
        log(f"{audio.name}: {len(part)} words, {method} ({proc.stdout.strip().splitlines()[-1]})")
        words += part
        offset += duration(audio) + gap
    dest = P / "words.json"
    dest.write_text(json.dumps(words, ensure_ascii=False))
    log(f"words.json: {len(words)} timed words, narration ends {words[-1]['e']:.2f}s")
    return dest
