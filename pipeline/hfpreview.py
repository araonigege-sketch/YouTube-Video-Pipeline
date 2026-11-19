"""Screenshot a HyperFrames build at chosen times (fast design QA, no render).

  python -m pipeline.hfpreview <build_dir> <out.jpg> <t1> [<t2> ...] [--cols 3] [--scale 0.4]

Seeks the GSAP timeline (window.__timelines.main) and the base <video> to each time, then tiles the frames.
"""
from __future__ import annotations

import sys
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def shots(build: Path, times: list[float], scale=0.4) -> list[Image.Image]:
    import subprocess
    import tempfile
    tmp = Path(tempfile.mkdtemp())
    subprocess.run(["node", str(Path(__file__).parent / "js/hfshots.cjs"), str(build), str(tmp), *[str(t) for t in times]],
                   check=True, cwd=str(Path(__file__).parent.parent))
    return [Image.open(tmp / f"f_{t:.2f}.jpg").convert("RGB").resize((int(1920 * scale), int(1080 * scale))) for t in times]


def sheet(imgs, times, out: Path, cols=3):
    w, h = imgs[0].size
    rows = (len(imgs) + cols - 1) // cols
    S = Image.new("RGB", (cols * w + (cols - 1) * 6, rows * (h + 30)), "white")
    d = ImageDraw.Draw(S)
    try:
        f = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Bold.otf", 20)
    except OSError:
        f = ImageFont.load_default()
    for k, (im, t) in enumerate(zip(imgs, times)):
        x, y = (k % cols) * (w + 6), (k // cols) * (h + 30)
        d.text((x + 4, y + 4), f"{t:.2f}s", font=f, fill="black")
        S.paste(im, (x, y + 30))
    S.save(out, quality=85)


if __name__ == "__main__":
    args = sys.argv[1:]
    cols = int(args[args.index("--cols") + 1]) if "--cols" in args else 3
    scale = float(args[args.index("--scale") + 1]) if "--scale" in args else 0.4
    args = [a for i, a in enumerate(args) if a not in ("--cols", "--scale") and (i == 0 or args[i - 1] not in ("--cols", "--scale"))]
    build, out, times = Path(args[0]), Path(args[1]), [float(x) for x in args[2:]]
    sheet(shots(build, times, scale), times, out, cols)
    print(out)
