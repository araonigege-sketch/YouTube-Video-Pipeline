"""YouTube description credits for a Mr. Davos episode: music (CC BY lines) + footage creators, from the edit actually used.

  python -m channels.mr_davos.describe <project_dir>   → writes out/description.txt (credits block; the owner writes the rest)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml


def credits(P: Path) -> str:
    edit = yaml.safe_load((P / "edit.yaml").read_text())
    a, b = edit["range"]
    used = []
    for s in edit["shots"]:
        src = s.get("src") or ""
        if src.startswith("broll/"):
            cid = Path(src).stem
            if cid not in used:
                used.append(cid)
    cr = json.loads((P / "media/broll/credits.json").read_text())
    by_creator: dict[str, list[str]] = {}
    for cid in used:
        c = cr.get(cid)
        if c:
            by_creator.setdefault(c["credit"], []).append(c["page"])
    lines = ["MUSIC"]
    if (P / "music.json").exists():
        seen = set()
        for t in json.loads((P / "music.json").read_text())["tracks"]:
            if t["end"] > a and t["start"] < b and t["title"] not in seen:
                seen.add(t["title"])
                lines.append(t["credit"])
    lines += ["", "FOOTAGE"]
    for who, pages in sorted(by_creator.items(), key=lambda kv: kv[0].lower()):
        lines.append(f"{who}: " + " ".join(pages))
    text = (P / "edit.yaml").read_text()
    nf = P / "media/nasa/nasa_meta.json"
    if nf.exists():
        meta = json.loads(nf.read_text())
        used_n = [Path(m).stem for m in re.findall(r"nasa/[\w.-]+\.mp4", text)]
        if used_n:
            lines += ["", "NASA FOOTAGE (public domain, courtesy of NASA)"]
            for k in dict.fromkeys(used_n):
                if k in meta:
                    lines.append(f"{meta[k]['title'].strip()} ({meta[k]['date']}): {meta[k]['page']}")
    wf = P / "media/news/news.json"
    if wf.exists():
        news = json.loads(wf.read_text())
        used_w = [Path(m).stem for m in re.findall(r"news/[\w.-]+\.mp4", text)]
        if used_w:
            lines += ["", "NEWS EXCERPTS (a few seconds each, shown in a frame for commentary and reporting)"]
            for k in dict.fromkeys(used_w):
                if k in news:
                    t = news[k]["title"].replace(" - CBS News", "")
                    lines.append(f"{news[k]['credit']}, “{t}” ({news[k]['date']}): {news[k]['page']}")
    af = P / "media/archive/credits.json"
    if af.exists():
        arch = json.loads(af.read_text())
        # every archive image the edit references: photo pages, split backgrounds, portraits inside illustrations
        used_a = [Path(m).stem for m in re.findall(r"archive/[\w.-]+\.(?:jpg|jpeg|png)", (P / "edit.yaml").read_text())]
        if used_a:
            lines += ["", "PHOTOS"]
            for k in dict.fromkeys(used_a):
                if k in arch:
                    lines.append(f"{arch[k]['title']}: {arch[k]['credit']} {arch[k]['page']}")
    for extra in edit.get("credits_extra", []):
        lines.append(extra)
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    P = Path(sys.argv[1])
    out = P / "out" / "description.txt"
    out.parent.mkdir(exist_ok=True)
    out.write_text(credits(P))
    print(out.read_text())
