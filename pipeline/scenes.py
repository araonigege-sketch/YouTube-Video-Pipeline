"""Scene cuts for multi-shot reels (NASA/DVIDS resource reels, news packages).

    python -m pipeline.scenes projects/<slug>/media/nasa [--thresh 0.32] [--min 0.8]

Writes <dir>/shots.json: {"file.mp4": [{"s": 0.0, "e": 10.9}, ...]}. The Mr. Davos check uses it to count
"no clip more than twice" per scene inside a reel (not per file) and to warn when a shot's in-point crosses a cut.
Existing entries are kept, so the command can be re-run after new downloads.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


def cuts(path: Path, thresh: float) -> list[float]:
    out = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-an", "-vf",
                          f"scale=320:-2,select='gt(scene,{thresh})',showinfo", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    return [float(m) for m in re.findall(r"pts_time:([\d.]+)", out)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--thresh", type=float, default=0.32)
    ap.add_argument("--min", type=float, default=0.8, help="merge scenes shorter than this into the previous one")
    a = ap.parse_args()
    d = Path(a.dir)
    sj = d / "shots.json"
    db = json.loads(sj.read_text()) if sj.exists() else {}
    for f in sorted(d.glob("*.mp4")):
        if f.name in db:
            continue
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                                   capture_output=True, text=True).stdout.strip())
        pts = [0.0] + [t for t in cuts(f, a.thresh) if 0 < t < dur] + [dur]
        segs = []
        for s, e in zip(pts, pts[1:]):
            if segs and e - s < a.min:
                segs[-1]["e"] = round(e, 3)
            else:
                segs.append({"s": round(s, 3), "e": round(e, 3)})
        db[f.name] = segs
        sj.write_text(json.dumps(db, indent=0))
        print(f"{f.name}: {len(segs)} scenes", flush=True)


if __name__ == "__main__":
    main()
