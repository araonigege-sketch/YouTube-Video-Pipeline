"""Where the recorded voiceover differs from the script: words Whisper heard that the script doesn't have
(and the reverse), with timestamps. Numbers are flagged first, because they usually also appear on screen.

  python -m pipeline.align.vo_diff <project_dir>        (needs words.whisper.json from whisper_align)
"""
from __future__ import annotations

import difflib
import json
import re
import sys
from pathlib import Path

from .whisper_align import norm


def diff(P: Path) -> list[dict]:
    P = Path(P)
    ep = __import__("yaml").safe_load((P / "episode.yaml").read_text())
    v = ep["voice"][0]
    script = (P / (v["text"] if isinstance(v, dict) else "vo/vo.txt")).read_text().split()
    heard = json.loads((P / "words.json").with_suffix(".whisper.json").read_text())
    a, b = [norm(t) for t in script], [norm(h["w"]) for h in heard]
    out = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        said = " ".join(h["w"] for h in heard[j1:j2])
        wrote = " ".join(script[i1:i2])
        if norm(said.replace(" ", "")) == norm(wrote.replace(" ", "")):
            continue                                     # only spacing differs ("21 ,471" vs "21,471")
        t = heard[j1]["s"] if j2 > j1 else (heard[j1 - 1]["e"] if j1 else 0.0)
        out.append({"t": round(t, 1), "script": wrote, "heard": said,
                    "number": bool(re.search(r"\d", wrote + said))})
    return out


if __name__ == "__main__":
    rows = diff(Path(sys.argv[1]))
    for r in sorted(rows, key=lambda r: (not r["number"], r["t"])):
        m, s = divmod(r["t"], 60)
        print(f"{'NUMBER ' if r['number'] else '       '}{int(m)}:{s:04.1f}  script: {r['script']!r:40}  heard: {r['heard']!r}")
