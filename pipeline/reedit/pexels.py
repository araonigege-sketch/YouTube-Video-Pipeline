"""Download Pexels clips at the best resolution available (vidIQ often links the 640/720p file).

python -m pipeline.reedit.pexels <out_dir> <mp4_url> [<mp4_url> ...]
Saves <out_dir>/<pexels_id>.mp4. For older clips the 1080p file sits at a predictable name
(<id>-hd_1920_1080_<fps>fps.mp4); try that (and 2048/2560/UHD variants) before the given link.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

V = "https://videos.pexels.com/video-files"


def _ok(url: str) -> bool:
    r = subprocess.run(["curl", "-sSIL", "-m", "20", "-o", "/dev/null", "-w", "%{http_code}", url], capture_output=True, text=True)
    return r.stdout.strip() == "200"


def _scan_new(url: str) -> str | None:
    """Newer clips: each rendition has its own file id, usually within a few of the linked one."""
    m = re.search(r"video-files/(\d+)/(\d+)_(\d+)_(\d+)_(\d+)fps\.mp4", url)
    if not m:
        return None
    vid, fid, w, h, fps = m.groups()
    fid, ar = int(fid), int(w) / int(h)
    sizes = dict.fromkeys([(1920, 1080), (round(1080 * ar / 2) * 2, 1080), (2048, 1080), (2560, 1440), (round(1440 * ar / 2) * 2, 1440)])
    for d in sorted(range(-25, 26), key=abs):
        for W, H in sizes:
            c = f"{V}/{vid}/{fid + d}_{W}_{H}_{fps}fps.mp4"
            if d and _ok(c):
                return c
    return None


def candidates(url: str) -> list[str]:
    m = re.search(r"video-files/(\d+)/(\d+)[-_].*?(\d+)fps\.mp4", url)
    if not m:
        return [url]
    vid, fid, fps = m.groups()
    out = []
    for f in dict.fromkeys([fps, "25", "30", "24", "60", "50"]):
        for size in ("hd_1920_1080", "hd_2048_1080", "uhd_2560_1440"):
            out.append(f"{V}/{vid}/{vid}-{size}_{f}fps.mp4")
    return out + [url]


def fetch(url: str, out_dir: Path) -> Path | None:
    vid = re.search(r"video-files/(\d+)/", url).group(1)
    dest = out_dir / f"{vid}.mp4"
    if dest.exists():
        return dest
    new = _scan_new(url)
    for c in ([new] if new else []) + candidates(url):
        if _ok(c):
            subprocess.run(["curl", "-sSL", "-m", "300", "-o", str(dest), c], check=True)
            return dest
    return None


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    for u in sys.argv[2:]:
        p = fetch(u, out)
        if not p:
            print(f"FAILED {u}")
            continue
        wh = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                             "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout.strip()
        print(f"{p.name} {wh}")
