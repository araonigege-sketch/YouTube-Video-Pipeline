"""Parse script.md into chapters and scenes.

Format:
    # Video title
    ## Chapter name                      -> YouTube chapter + on-screen chapter title
    [stock: query]                       -> visual hint(s) for the next paragraph
    [image: prompt]                      -> AI image (Ken Burns motion)
    [card: text]                         -> locally rendered text card (dates, quotes)
    [visual: idea]                       -> use the style's default visual kind
    Narration paragraph...               -> one scene (blank line ends it)
    <!-- comments are ignored -->
"""
from __future__ import annotations

import re

HINT_RE = re.compile(r"^\[(stock|image|card|visual)\s*:\s*(.+?)\]\s*$", re.I)


def clean_text(s: str) -> str:
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)        # markdown links
    s = re.sub(r"(\*\*|__|\*|_|`)", "", s)                 # emphasis
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def parse_script(text: str, default_kind: str) -> dict:
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    title, chapter = None, None
    scenes: list[dict] = []
    buf: list[str] = []
    hints: list[dict] = []
    new_chapter = False

    def flush():
        nonlocal buf, hints, new_chapter
        if not buf:
            return
        scenes.append({
            "id": f"s{len(scenes) + 1:03d}",
            "chapter": chapter,
            "chapter_start": new_chapter,
            "text": clean_text(" ".join(buf)),
            "hints": hints,
        })
        buf, hints, new_chapter = [], [], False

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            flush()
        elif line.startswith("## "):
            flush()
            chapter, new_chapter = line[3:].strip(), True
        elif line.startswith("# "):
            flush()
            title = line[2:].strip()
        elif m := HINT_RE.match(line):
            flush()  # a hint after text starts a new scene
            kind = m.group(1).lower()
            hints.append({"kind": default_kind if kind == "visual" else kind, "prompt": m.group(2).strip()})
        else:
            buf.append(line)
    flush()
    if not scenes:
        raise ValueError("script has no narration paragraphs")
    return {"title": title, "scenes": scenes}
