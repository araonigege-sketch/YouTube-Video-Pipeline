"""Write upload-ready metadata: chapters, description draft, stock credits, QA notes."""
from __future__ import annotations

from pathlib import Path

from .util import ts, write_json


def chapters(plan: dict) -> tuple[list[tuple[float, str]], list[str]]:
    chs = [(sc["t0"], sc["chapter"]) for sc in plan["scenes"] if sc.get("chapter_start") and sc.get("chapter")]
    warnings = []
    if chs and chs[0][0] > 0.5:
        chs.insert(0, (0.0, "Intro"))
    if chs:
        chs[0] = (0.0, chs[0][1])
    if len(chs) < 3:
        warnings.append("YouTube needs at least 3 chapters for them to show (have %d)." % len(chs))
    for (a, n1), (b, _) in zip(chs, chs[1:]):
        if b - a < 10:
            warnings.append(f"Chapter '{n1}' is {b - a:.1f}s; YouTube requires >= 10s.")
    return chs, warnings


def write_metadata(cfg: dict, plan: dict, reqs: list[dict], tl: dict, final: Path, missing: list[str]) -> None:
    pdir: Path = cfg["dir"]
    chs, warnings = chapters(plan)
    credits = sorted({r["credit"] for r in reqs if r.get("credit")})
    proj = cfg["project"]
    md = [f"# {plan['title']}", "", f"File: `{final.name}` · {ts(tl['total_seconds'])}", ""]
    md += ["## Description (draft)", "", proj.get("description", "").strip() or "_(write or generate a description)_", ""]
    if chs:
        md += ["Chapters:"] + [f"{ts(t)} {name}" for t, name in chs] + [""]
    if credits:
        md += ["Footage credits:"] + [f"- {c}" for c in credits] + [""]
    md += ["## QA", ""]
    md += [f"- ⚠️ {w}" for w in warnings]
    md += [f"- ⚠️ DRAFT: {len(missing)} placeholder asset(s)" ] if missing else []
    md += [f"- Narration {tl['narration_seconds']:.1f}s, {len(tl['shots'])} shots, "
           f"avg shot {tl['total_seconds'] / max(1, len(tl['shots'])):.1f}s"]
    (pdir / "out" / "metadata.md").write_text("\n".join(md) + "\n")
    write_json(pdir / "out" / "chapters.json", [{"t": round(t, 2), "title": n} for t, n in chs])
