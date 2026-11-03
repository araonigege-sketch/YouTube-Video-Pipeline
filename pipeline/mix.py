"""Episode audio: join voice parts, lay sectioned music under them, duck, write build/assets/audio.wav.

episode.yaml:   voice: [vo/part1.mp3, ...]
music.json:     {"tracks": [{"file": "music/x.mp3", "start": 0, "end": 201, "offset": 0,
                             "title": ..., "artist": ..., "license": ..., "license_url": ..., "source": ...}, ...]}
Levels come from the channel's `audio:` block (voice_lufs, music_lufs, music_gain, part_gap).
"""
from __future__ import annotations

import json
from pathlib import Path

from .util import PipelineError, ffmpeg


def mix(P: Path, voice_parts: list[str], audio_cfg: dict, end: float, out: Path, log=print) -> Path:
    P = Path(P)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.parent / "_mix"
    tmp.mkdir(exist_ok=True)
    from .util import duration
    gap = audio_cfg.get("part_gap", 0.6)
    parts, t = [], 0.0
    for v in voice_parts:            # only the parts that start before `end` are needed
        if t >= end:
            break
        p = P / (v["file"] if isinstance(v, dict) else v)
        if not p.exists():
            raise PipelineError(f"missing voice file: {p}")
        parts.append(p)
        t += duration(p) + gap
    args, chain = [], ""
    n = 0
    for i, p in enumerate(parts):
        args += ["-i", p]
        chain += f"[{n}]aresample=44100,aformat=channel_layouts=mono[a{n}];"
        n += 1
        if i < len(parts) - 1:
            args += ["-f", "lavfi", "-t", str(gap), "-i", "anullsrc=r=44100:cl=mono"]
            chain += f"[{n}]anull[a{n}];"
            n += 1
    chain += "".join(f"[a{k}]" for k in range(n)) + f"concat=n={n}:v=0:a=1,loudnorm=I={audio_cfg['voice_lufs']}:TP=-1.5:LRA=11,aresample=44100[o]"
    voice = tmp / "voice.wav"
    ffmpeg([*args, "-filter_complex", chain, "-map", "[o]", voice])

    mj = P / "music.json"
    tracks = json.loads(mj.read_text())["tracks"] if mj.exists() else []
    tracks = [t for t in tracks if t["start"] < end]
    if not tracks:
        log("no music.json tracks — voice only")
        ffmpeg(["-i", voice, "-af", f"aformat=channel_layouts=stereo,apad=whole_dur={end:.3f}", "-t", f"{end:.3f}", out])
        return out
    args, f, labels = [], [], []
    for i, t in enumerate(tracks):
        src = P / t["file"]
        if not src.exists():
            raise PipelineError(f"missing music file {src}")
        a, b, o = t["start"], min(t["end"], end), t.get("offset", 0)
        d = b - a
        ms = int(a * 1000)
        args += ["-i", src]
        f.append(f"[{i}]atrim={o}:{o + d},asetpts=PTS-STARTPTS,aresample=44100,aformat=channel_layouts=stereo,"
                 f"loudnorm=I={audio_cfg['music_lufs']}:TP=-2,aresample=44100,"
                 f"afade=t=in:d={0.5 if i == 0 else 3.5},afade=t=out:st={max(0, d - 4)}:d=4,adelay={ms}|{ms}[m{i}]")
        labels.append(f"[m{i}]")
    f.append(f"{''.join(labels)}amix=inputs={len(labels)}:duration=longest:normalize=0,apad,atrim=0:{end:.3f}[mus]")
    music = tmp / "music.wav"
    ffmpeg([*args, "-filter_complex", ";".join(f), "-map", "[mus]", music])
    ffmpeg(["-i", voice, "-i", music, "-filter_complex",
            f"[0]aformat=channel_layouts=stereo,apad=whole_dur={end:.3f},asplit=2[v1][v2];"
            f"[1]volume={audio_cfg['music_gain']}[mu];[mu][v2]sidechaincompress=threshold=0.02:ratio=6:attack=20:release=400[duck];"
            "[v1][duck]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[o]",
            "-map", "[o]", "-ar", "44100", "-t", f"{end:.3f}", out])
    log(f"audio: {len(parts)} voice part(s) + {len(tracks)} music track(s) → {out}")
    return out


def credits(P: Path) -> list[str]:
    mj = Path(P) / "music.json"
    if not mj.exists():
        return []
    out = []
    for t in json.loads(mj.read_text())["tracks"]:
        line = (f"Music: “{t.get('title', Path(t['file']).stem)}” by {t.get('artist', 'unknown')}, "
                f"licensed under {t.get('license', 'licence?')} ({t.get('license_url', '')}). Source: {t.get('source', '')}")
        if not t.get("licence_verified", True):
            line = "⚠ UNVERIFIED LICENCE — " + line
        out.append(line)
    return out
