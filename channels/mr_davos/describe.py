"""YouTube description credits for a Mr. Davos episode: music (CC BY lines) + footage creators, from the edit actually used.

  python -m channels.mr_davos.describe <project_dir>   → writes out/description.txt (credits block; the owner writes the rest)
"""
from __future__ import annotations

import json
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
    for extra in edit.get("credits_extra", []):
        lines.append(extra)
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    P = Path(sys.argv[1])
    out = P / "out" / "description.txt"
    out.parent.mkdir(exist_ok=True)
    out.write_text(credits(P))
    print(out.read_text())
