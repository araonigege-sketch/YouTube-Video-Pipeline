"""Contact sheet of candidate B-roll clips: three frames per clip, labelled with id, size and length.

python -m pipeline.reedit.candsheet <clip_dir> <out.jpg> [ids...]
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def _probe(p: Path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration",
                          "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout.split()
    w, h = out[0].split(",")[:2]
    return int(w), int(h), float(out[-1].strip(","))


def _frame(p: Path, t: float, w=280, h=158) -> Image.Image:
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(p), "-frames:v", "1", "-vf", f"scale={w}:{h}",
                        "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
    from io import BytesIO
    try:
        return Image.open(BytesIO(r.stdout)).convert("RGB")
    except Exception:
        return Image.new("RGB", (w, h))


def sheet(clips: list[Path], out: Path):
    tw, th, lab = 280, 158, 26
    try:
        font = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Bold.otf", 18)
    except OSError:
        font = ImageFont.load_default()
    cols = 2   # two clips per row, three frames each
    rows = (len(clips) + cols - 1) // cols
    img = Image.new("RGB", (cols * (3 * tw + 12), rows * (th + lab)), "black")
    d = ImageDraw.Draw(img)
    for k, c in enumerate(clips):
        x0, y0 = (k % cols) * (3 * tw + 12), (k // cols) * (th + lab)
        try:
            w, h, dur = _probe(c)
        except Exception:
            continue
        for j, f in enumerate((0.15, 0.5, 0.85)):
            img.paste(_frame(c, dur * f), (x0 + j * tw, y0 + lab))
        col = (120, 220, 140) if h >= 1080 else (240, 170, 40) if h >= 720 else (240, 80, 80)
        d.text((x0 + 6, y0 + 3), f"{c.stem}  {w}x{h}  {dur:.0f}s", font=font, fill=col)
    img.save(out, quality=80)


if __name__ == "__main__":
    src = Path(sys.argv[1])
    ids = sys.argv[3:]
    clips = [src / f"{i}.mp4" for i in ids] if ids else sorted(src.glob("*.mp4"))
    sheet([c for c in clips if c.exists()], Path(sys.argv[2]))
