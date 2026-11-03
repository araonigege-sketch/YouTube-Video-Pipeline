"""Render: align -> shot clips -> concat -> captions -> audio mix -> final MP4 + metadata."""
from __future__ import annotations

import time
from pathlib import Path

from .captions import write_ass
from .cards import render_card
from .package import write_metadata
from .plan import request_done, save_plan
from .timeline import build_timeline
from .util import PipelineError, duration, ffmpeg, has_video_stream, read_json, short_hash, write_json

MOTIONS = ["zoom_in", "pan_right", "zoom_out", "pan_left"]


def _look_filter(cfg: dict) -> str:
    lk = cfg.get("look") or {}
    parts = []
    if lk.get("saturation", 1) != 1 or lk.get("contrast", 1) != 1 or lk.get("brightness", 0):
        parts.append(f"eq=saturation={lk.get('saturation', 1)}:contrast={lk.get('contrast', 1)}"
                     f":brightness={lk.get('brightness', 0)}")
    if lk.get("vignette"):
        parts.append(f"vignette=angle={lk['vignette']}")
    if lk.get("grain"):
        parts.append(f"noise=alls={lk['grain']}:allf=t")
    return ",".join(parts)


def _zoompan(motion: str, frames: int, w: int, h: int, fps: int) -> str:
    n = max(frames - 1, 1)
    p = f"(on/{n})"
    ease = f"(0.5-0.5*cos(PI*{p}))"
    cx, cy = "(iw-iw/zoom)/2", "(ih-ih/zoom)/2"
    z, x, y = {
        "zoom_in": (f"1+0.12*{ease}", cx, cy),
        "zoom_out": (f"1.12-0.12*{ease}", cx, cy),
        "pan_right": ("1.10", f"(iw-iw/zoom)*{ease}", cy),
        "pan_left": ("1.10", f"(iw-iw/zoom)*(1-{ease})", cy),
    }[motion]
    return (f"scale={w * 2}:{h * 2}:force_original_aspect_ratio=increase,crop={w * 2}:{h * 2},"
            f"zoompan=z='{z}':x='{x}':y='{y}':d=1:s={w}x{h}:fps={fps}")


def render_shot(src: Path, out: Path, frames: int, idx: int, cfg: dict, draft: bool) -> None:
    w, h = cfg["video"]["resolution"]
    fps = cfg["video"]["fps"]
    look = _look_filter(cfg)
    motion = MOTIONS[idx % len(MOTIONS)]
    key = short_hash(str(src), src.stat().st_mtime, frames, motion, look, w, h, fps, draft)
    meta = out.with_suffix(".json")
    if out.exists() and (read_json(meta, {}) or {}).get("key") == key:
        return
    secs = frames / fps
    enc = ["-an", "-c:v", "libx264", "-preset", "ultrafast" if draft else "veryfast",
           "-crf", "23" if draft else "18", "-pix_fmt", "yuv420p", "-r", str(fps), "-frames:v", str(frames)]
    is_video = src.suffix.lower() in {".mp4", ".mov", ".webm", ".mkv"} and has_video_stream(src)
    if is_video:
        sd = duration(src)
        pre = ["-stream_loop", "-1"] if sd < secs + 0.6 else ["-ss", f"{min(0.5, sd - secs):.2f}"]
        vf = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps={fps},setsar=1"
        ffmpeg([*pre, "-i", src, "-vf", vf + (f",{look}" if look else ""), *enc, out])
    else:
        vf = _zoompan(motion, frames, w, h, fps) + ",setsar=1"
        ffmpeg(["-loop", "1", "-framerate", fps, "-i", src, "-vf", vf + (f",{look}" if look else ""), *enc, out])
    write_json(meta, {"key": key})


def _resolve_assets(cfg: dict, reqs: list[dict], plan: dict, draft: bool) -> tuple[dict, dict, Path | None, list[str]]:
    pdir: Path = cfg["dir"]
    build = pdir / "build"
    missing, voices, visuals = [], {}, {}
    music = None
    by_id = {r["id"]: r for r in reqs}
    for r in reqs:
        if r["type"] == "visual" and r["kind"] == "card" and not request_done(r, pdir):
            path = render_card(r["prompt"], build / "visuals" / f"{r['id']}.png", cfg)
            r["file"], r["fulfilled_by"] = str(path.relative_to(pdir)), "local:card"
    for r in reqs:
        done = request_done(r, pdir)
        if not done:
            missing.append(r["id"])
        if r["type"] == "voice":
            if done:
                voices[r["id"]] = pdir / r["file"]
            elif draft:
                est = sum(s["est_seconds"] for s in plan["scenes"] if s["chunk"] == r["id"])
                p = build / "draft" / f"{r['id']}.wav"
                p.parent.mkdir(parents=True, exist_ok=True)
                ffmpeg(["-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", f"{est:.2f}", p])
                voices[r["id"]] = p
        elif r["type"] == "visual":
            if done:
                visuals[r["id"]] = pdir / r["file"]
            elif draft:
                visuals[r["id"]] = render_card(
                    r["prompt"][:160], build / "draft" / f"{r['id']}.png", cfg,
                    kicker=f"DRAFT · {r['kind'].upper()} · {r['id']}")
        elif r["type"] == "music" and done:
            music = pdir / r["file"]
    write_json(build / "requests.json", list(by_id.values()))
    return voices, visuals, music, missing


def render(cfg: dict, draft: bool = False, log=print) -> Path:
    t_start = time.time()
    pdir: Path = cfg["dir"]
    build = pdir / "build"
    res = save_plan(cfg)
    plan, reqs = res["plan"], res["requests"]
    voices, visuals, music, missing = _resolve_assets(cfg, reqs, plan, draft)
    if missing and not draft:
        raise PipelineError(f"{len(missing)} asset(s) not ready: {', '.join(missing[:12])}"
                            f"{' …' if len(missing) > 12 else ''}\nRun `status`, or render with --draft.")
    if missing:
        log(f"draft: {len(missing)} missing asset(s) replaced with placeholders")

    fps = cfg["video"]["fps"]
    tl = build_timeline(plan, voices, fps, cfg["video"]["tail_seconds"])
    write_json(build / "timeline.json", {"scenes": plan["scenes"], **tl})
    total = tl["total_seconds"]
    log(f"timeline: {len(plan['scenes'])} scenes, {len(tl['shots'])} shots, {total:.1f}s")

    # 1. shot clips
    clip_dir = build / "clips"
    clip_dir.mkdir(parents=True, exist_ok=True)
    lines = []
    for i, shot in enumerate(tl["shots"]):
        out = clip_dir / f"{shot['id']}.mp4"
        render_shot(visuals[f"vis_{shot['id']}"], out, shot["frames"], i, cfg, draft)
        lines.append(f"file 'clips/{out.name}'")
        if (i + 1) % 10 == 0:
            log(f"  clips {i + 1}/{len(tl['shots'])}")
    (build / "concat.txt").write_text("\n".join(lines) + "\n")
    ffmpeg(["-f", "concat", "-safe", "0", "-i", "concat.txt", "-c", "copy", "video.mp4"], cwd=build)

    # 2. narration track
    order = [voices[c["id"]] for c in plan["voice_chunks"]]
    ins, fl = [], ""
    for i, p in enumerate(order):
        ins += ["-i", p]
        fl += f"[{i}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[a{i}];"
    fl += "".join(f"[a{i}]" for i in range(len(order))) + f"concat=n={len(order)}:v=0:a=1[out]"
    ffmpeg([*ins, "-filter_complex", fl, "-map", "[out]", build / "narration.wav"])

    # 3. captions
    write_ass(plan, cfg, build / "captions.ass")

    # 4. final mix + burn-in
    out_dir = pdir / "out"
    out_dir.mkdir(exist_ok=True)
    final = out_dir / f"{cfg['project']['slug']}{'_draft' if draft else ''}.mp4"
    mcfg, loud = cfg["music"], cfg["audio"]["loudness_lufs"]
    args = ["-i", "video.mp4", "-i", "narration.wav"]
    fc = (f"[0:v]subtitles=captions.ass[v];"
          f"[1:a]apad=whole_dur={total:.3f}[nar];")
    if music:
        args += ["-stream_loop", "-1", "-i", str(music.resolve())]
        fade_out = max(0.0, total - 4)
        fc += (f"[2:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
               f"atrim=0:{total:.3f},volume={mcfg['volume_db']}dB,"
               f"afade=t=in:d=2,afade=t=out:st={fade_out:.2f}:d=4[mus];"
               "[nar]asplit=2[nar1][sc];"
               f"[mus][sc]sidechaincompress=threshold={mcfg['duck_threshold']}:ratio={mcfg['duck_ratio']}"
               ":attack=40:release=700[duck];"
               "[nar1][duck]amix=inputs=2:duration=first:normalize=0,")
    else:
        fc += "[nar]"
    fc += f"loudnorm=I={loud}:TP=-1.5:LRA=11,aresample=48000[a]"
    ffmpeg([*args, "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}",
            "-c:v", "libx264", "-preset", "ultrafast" if draft else cfg["video"]["preset"],
            "-crf", "26" if draft else str(cfg["video"]["crf"]), "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", final.resolve()], cwd=build)

    write_metadata(cfg, plan, reqs, tl, final, missing)
    log(f"rendered {final.relative_to(pdir.parent.parent)} ({duration(final):.1f}s) in {time.time() - t_start:.0f}s")
    return final
