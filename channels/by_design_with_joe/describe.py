"""YouTube description credits for a By Design With Joe episode: music (CC BY lines) + footage creators, from the edit actually used.

  python -m channels.by_design_with_joe.describe <project_dir>   → writes out/description.txt
Ready to paste into YouTube: title, CHAPTERS (0:00 Intro + every chapter card, timed from the narration),
the credits (music, footage, photos), then the three hashtags from episode.yaml `hashtags:`.
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
    ep = yaml.safe_load((P / "episode.yaml").read_text())
    lines = [ep.get("title", ""), "", "CHAPTERS", "0:00 Intro"]
    from pipeline.words import Words
    W = Words.load(P / "words.json")
    for s in edit["shots"]:
        if s.get("page") == "chapter":
            t = int(W.T(s["at"]) - a)
            lines.append(f"{t // 60}:{t % 60:02d} {s['title']}")
    lines += ["", "MUSIC"]
    if (P / "music.json").exists():
        seen = set()
        for t in json.loads((P / "music.json").read_text())["tracks"]:
            if t["end"] > a and t["start"] < b and t["title"] not in seen:
                seen.add(t["title"])
                lines.append(t["credit"])
    lines += ["", "FOOTAGE"]
    for who, pages in sorted(by_creator.items(), key=lambda kv: kv[0].lower()):
        lines.append(f"{who}: " + " ".join(pages))
    af = P / "media/archive/credits.json"
    if af.exists():
        arch = json.loads(af.read_text())
        # every archive image the edit references: photo pages, split backgrounds, portraits inside illustrations
        used_a = [Path(m).stem for m in re.findall(r"archive/[\w.-]+\.(?:jpg|jpeg|png)", (P / "edit.yaml").read_text())]
        if used_a:
            lines += ["", "PHOTOS"]
            for k in dict.fromkeys(used_a):
                if k in arch and arch[k].get('credit'):
                    line = f"{arch[k]['title']}: {arch[k]['credit']} {arch[k]['page']}".rstrip()
                    if line not in lines:                      # the same photo can be used from two downloads
                        lines.append(line)
    if any(str(s.get("src", "")).startswith("ai/") for s in edit["shots"]):
        lines += ["", "AI RECONSTRUCTIONS",
                  "A few shots of events no camera recorded are AI-generated reconstructions (fal.ai: Seedream 4 and Kling 2.1), "
                  "labelled \"AI reconstruction\" on screen. All other footage and photos are real."]
    for extra in edit.get("credits_extra", []):
        lines.append(extra)
    if ep.get("hashtags"):
        lines += ["", " ".join(ep["hashtags"])]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    P = Path(sys.argv[1])
    out = P / "out" / "description.txt"
    out.parent.mkdir(exist_ok=True)
    out.write_text(credits(P))
    print(out.read_text())
