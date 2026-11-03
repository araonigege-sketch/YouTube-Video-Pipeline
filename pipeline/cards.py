"""Locally rendered stills: text cards and draft placeholders (Pillow)."""
from __future__ import annotations

import textwrap
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .util import find_font


def _font(family: str, size: int, bold: bool = True):
    path = find_font(family, bold)
    try:
        return ImageFont.truetype(path, size) if path else ImageFont.load_default(size)
    except OSError:
        return ImageFont.load_default(size)


def _hex(c: str) -> tuple[int, int, int]:
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def render_card(text: str, out: Path, cfg: dict, kicker: str | None = None, size=None) -> Path:
    w, h = size or cfg["video"]["resolution"]
    cc = cfg["cards"]
    top, bottom = _hex(cc["bg_top"]), _hex(cc["bg_bottom"])
    t = np.linspace(0, 1, h)[:, None, None]
    grad = np.array(top) * (1 - t) + np.array(bottom) * t          # vertical gradient
    img = Image.fromarray(np.repeat(grad, w, axis=1).astype(np.uint8), "RGB")
    # soft radial glow
    glow = Image.new("L", (w, h), 0)
    ImageDraw.Draw(glow).ellipse((w * 0.15, h * 0.1, w * 0.85, h * 0.9), fill=40)
    glow = glow.filter(ImageFilter.GaussianBlur(h // 5))
    img = Image.composite(Image.new("RGB", (w, h), _hex(cc["accent"])), img, glow)

    d = ImageDraw.Draw(img)
    body_size = int(h * (0.075 if len(text) < 60 else 0.05))
    font = _font(cfg["captions"]["font"], body_size)
    wrap = max(12, int(w / (body_size * 0.55)) - 4)
    lines = textwrap.wrap(text, width=wrap)[:7]
    line_h = int(body_size * 1.25)
    block_h = line_h * len(lines)
    y = (h - block_h) // 2
    if kicker:
        kf = _font(cfg["captions"]["font"], int(h * 0.03))
        kw = d.textlength(kicker, font=kf)
        d.text(((w - kw) / 2, y - int(h * 0.08)), kicker, font=kf, fill=_hex(cc["accent"]))
    for line in lines:
        lw = d.textlength(line, font=font)
        d.text(((w - lw) / 2, y), line, font=font, fill=_hex(cc["text"]))
        y += line_h
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return out
