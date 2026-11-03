"""Cut every shot from its source clip (frame-exact) and join them into one silent 1080p30 background track.
Usage: python3 make_bg.py <projdir>   (reads timeline.json; clip ids 'bNN_k' -> footage/, 'xbNN_k' -> extra/)
Writes projdir/build/assets/bg.mp4
"""
import sys, json, pathlib, subprocess, concurrent.futures as cf

P = pathlib.Path(sys.argv[1]); FPS = 30
tl = json.load(open(P / "timeline.json"))
seg_dir = P / "build" / "segs"; seg_dir.mkdir(parents=True, exist_ok=True)
(P / "build" / "assets").mkdir(parents=True, exist_ok=True)

def src(clip):
    """'bNN_k' Pixabay, 'xbNN_k' extra Pixabay, 'a:name' archival (newclips/), 'i:name' AI still (ai/*.png),
    'v:name' AI video (ai/*.mp4)."""
    if clip.startswith("a:"): return P / "newclips" / f"{clip[2:]}.mp4"
    if clip.startswith("i:"): return P / "ai" / f"{clip[2:]}.png"
    if clip.startswith("v:"): return P / "ai" / f"{clip[2:]}.mp4"
    return P / "extra" / f"{clip[1:]}.mp4" if clip.startswith("x") else P / "footage" / f"{clip}.mp4"

def length(f):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                                capture_output=True, text=True).stdout.strip())

jobs = []
for i, s in enumerate(tl["shots"]):
    f0 = round(s["start"] * FPS) if i else 0
    f1 = round((s["start"] + s["dur"]) * FPS) if i + 1 < len(tl["shots"]) else round(tl["duration"] * FPS)
    n = f1 - f0
    f = src(s["clip"]); L = 1e9 if f.suffix == ".png" else length(f)
    need = n / FPS
    off = s["src_offset"] if s["src_offset"] + need < L - 0.2 else max(0.0, (L - need) / 2)
    if s["clip"].startswith(("v:", "a:")):
        off = 0.0                                   # AI clips drift late; archival clips are pre-trimmed
    # if the clip is shorter than the shot, slow it down to fit (never freeze)
    speed = min(1.0, (L - 0.2) / need) if need > L - 0.2 else 1.0
    jobs.append((i, f, off, n, speed))

def cut(job):
    import hashlib
    i, f, off, n, speed = job
    key = hashlib.md5(f"{f}|{f.stat().st_mtime_ns}|{off:.3f}|{n}|{speed:.4f}".encode()).hexdigest()[:10]
    out = seg_dir / f"s{i:03d}_{key}.mp4"
    if out.exists(): return out                      # unchanged shot: reuse the cut from last build
    vf = (f"setpts=PTS/{speed}," if speed < 1 else "") + \
         f"scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps={FPS},format=yuv420p"
    inp = ["-loop", "1", "-framerate", str(FPS), "-i", str(f)] if f.suffix == ".png" else ["-ss", f"{off:.3f}", "-i", str(f)]
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inp, "-an", "-vf", vf,
                    "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
                    "-g", "30", str(out)], check=True)
    return out

with cf.ThreadPoolExecutor(2) as ex:
    outs = list(ex.map(cut, jobs))
lst = seg_dir / "list.txt"
lst.write_text("".join(f"file '{o.name}'\n" for o in outs))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
                str(P / "build" / "assets" / "bg.mp4")], check=True)
print("bg.mp4", length(P / "build" / "assets" / "bg.mp4"), "s vs timeline", tl["duration"])
