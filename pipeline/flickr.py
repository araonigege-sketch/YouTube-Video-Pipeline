"""Fetch the largest public rendition of a Flickr photo (the API search results only link the 1024 px "_b" file).

  python -m pipeline.flickr <photo page url> <out.jpg>
Reads the photo's sizes pages (o, k, h, l, b) and downloads the biggest one offered. Sends a descriptive User-Agent
(Flickr answers 429 to curl's default).
"""
from __future__ import annotations

import re
import subprocess
import sys

UA = "youtube-video-pipeline/1.0 (documentary research; github araonigege-sketch)"


def _get(url: str) -> str:
    return subprocess.run(["curl", "-sL", "-m", "60", "-A", UA, url], capture_output=True, text=True).stdout


def best(page: str) -> str | None:
    page = page.rstrip("/")
    for size in ("o", "6k", "5k", "4k", "3k", "k", "h", "l", "b"):
        html = _get(f"{page}/sizes/{size}/")
        m = re.search(r'<img src="(https://live\.staticflickr\.com/[^"]+?_(?:' + size + r'|[a-z0-9]+)\.(?:jpg|png))"', html)
        if m and f"_{size}." in m.group(1) or (m and size == "o"):
            return m.group(1)
    return None


if __name__ == "__main__":
    page, out = sys.argv[1], sys.argv[2]
    u = best(page)
    if not u:
        sys.exit(f"no rendition found for {page}")
    subprocess.run(["curl", "-sL", "-m", "120", "-A", UA, "-o", out, u], check=True)
    from PIL import Image
    print(out, Image.open(out).size, u)
