"""CLI: python -m pipeline <command> <project> ...

  new     <slug> --style documentary --title "..."   scaffold projects/<slug>/
  plan    <project>                                  parse script, write build/requests.json
  status  <project> [--json]                         list pending / done asset requests
  fetch   <project> <request_id> <url|path> [--credit ...] [--source-url ...]
  local   <project>                                  fulfil requests with local providers (cards, edge-tts)
  render  <project> [--draft]                        build the video (draft = placeholders for missing assets)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from .cards import render_card
from .config import ROOT, STYLES_DIR, load_project
from .plan import request_done, save_plan
from .render import render
from .util import PipelineError, fetch_to, read_json, write_json

PROJECTS = ROOT / "projects"

SCRIPT_TEMPLATE = """# {title}

<!-- One paragraph = one scene. Optional visual hints go on the line(s) above a paragraph:
     [stock: search query]   [image: prompt for an AI image]   [card: on-screen text]
     ## headings become YouTube chapters and on-screen chapter titles. -->

## Introduction
[stock: establishing shot that fits the topic]
Opening hook paragraph goes here.
"""


def _pdir(name: str) -> Path:
    p = Path(name)
    if not (p / "project.yaml").exists():
        p = PROJECTS / name
    if not (p / "project.yaml").exists():
        raise PipelineError(f"project not found: {name}")
    return p.resolve()


def cmd_new(a):
    pdir = PROJECTS / a.slug
    if pdir.exists():
        raise PipelineError(f"{pdir} already exists")
    if not (STYLES_DIR / f"{a.style}.yaml").exists():
        raise PipelineError(f"unknown style {a.style}")
    pdir.mkdir(parents=True)
    title = a.title or a.slug.replace("-", " ").title()
    (pdir / "project.yaml").write_text(
        f"slug: {a.slug}\ntitle: \"{title}\"\nstyle: {a.style}\n"
        "description: \"\"\n# overrides:            # any style key can be overridden per project\n"
        "#   voice: {voice_id: ...}\n")
    (pdir / "script.md").write_text(SCRIPT_TEMPLATE.format(title=title))
    print(f"created {pdir.relative_to(ROOT)} — write script.md, then run: python -m pipeline plan {a.slug}")


def _summary(cfg, reqs):
    pdir = cfg["dir"]
    rows = []
    for r in reqs:
        done = request_done(r, pdir)
        detail = r.get("text", r.get("prompt", ""))[:70].replace("\n", " ")
        rows.append((("✔" if done else "·"), r["id"], r["type"] + ("/" + r["kind"] if r.get("kind") else ""),
                     r["provider"], detail))
    return rows


def cmd_plan(a):
    cfg = load_project(_pdir(a.project))
    res = save_plan(cfg)
    plan, reqs = res["plan"], res["requests"]
    est = sum(s["est_seconds"] for s in plan["scenes"])
    pending = [r for r in reqs if not request_done(r, cfg["dir"])]
    print(f"{plan['title']}: {len(plan['scenes'])} scenes, ~{est / 60:.1f} min, "
          f"{sum(len(s['shots']) for s in plan['scenes'])} shots, {len(plan['voice_chunks'])} voice chunk(s)")
    print(f"requests: {len(reqs)} total, {len(pending)} pending")
    if res["stale"]:
        print(f"re-queued (content changed): {', '.join(res['stale'])}")
    by_prov = {}
    for r in pending:
        by_prov.setdefault(r["provider"], []).append(r)
    for prov, rs in by_prov.items():
        print(f"  {prov:8s} {len(rs)}")
    chars = sum(r["chars"] for r in pending if r["type"] == "voice" and r["provider"] == "vidiq")
    if chars:
        n_calls = sum(1 for r in pending if r["type"] == "voice" and r["provider"] == "vidiq")
        cost = sum(-(-r["chars"] // 1000) * 14 for r in pending if r["type"] == "voice" and r["provider"] == "vidiq")
        print(f"  est. vidIQ voice cost: {cost} credits ({chars} chars, {n_calls} call(s))")


def cmd_status(a):
    cfg = load_project(_pdir(a.project))
    reqs = read_json(cfg["dir"] / "build/requests.json")
    if reqs is None:
        raise PipelineError("no plan yet — run `plan` first")
    if a.json:
        pend = [r for r in reqs if not request_done(r, cfg["dir"])]
        print(json.dumps(pend if a.pending else reqs, indent=2, ensure_ascii=False))
        return
    rows = _summary(cfg, reqs)
    for row in rows:
        if a.pending and row[0] == "✔":
            continue
        print(f"{row[0]} {row[1]:16s} {row[2]:14s} {row[3]:8s} {row[4]}")
    n = sum(1 for r in rows if r[0] == "✔")
    print(f"\n{n}/{len(rows)} done")


def cmd_fetch(a):
    cfg = load_project(_pdir(a.project))
    pdir = cfg["dir"]
    reqs = read_json(pdir / "build/requests.json", [])
    r = next((x for x in reqs if x["id"] == a.request_id), None)
    if not r:
        raise PipelineError(f"no request {a.request_id}")
    sub = {"voice": "audio", "visual": "visuals", "music": "music"}[r["type"]]
    dest = fetch_to(a.source, pdir / "build" / sub / r["id"])
    r["file"] = str(dest.relative_to(pdir))
    r["fulfilled_by"] = a.provider or r["provider"]
    for k in ("credit", "source_url"):
        if getattr(a, k):
            r[k] = getattr(a, k)
    if a.meta:
        r["meta"] = json.loads(a.meta)
    write_json(pdir / "build/requests.json", reqs)
    print(f"{r['id']} -> {r['file']} ({dest.stat().st_size // 1024} KB)")


def cmd_local(a):
    cfg = load_project(_pdir(a.project))
    pdir = cfg["dir"]
    reqs = read_json(pdir / "build/requests.json")
    if reqs is None:
        reqs = save_plan(cfg)["requests"]
    n = 0
    for r in reqs:
        if request_done(r, pdir):
            continue
        if r["type"] == "visual" and r["kind"] == "card":
            p = render_card(r["prompt"], pdir / "build/visuals" / f"{r['id']}.png", cfg)
            r["file"], r["fulfilled_by"] = str(p.relative_to(pdir)), "local:card"
            n += 1
        elif r["type"] == "voice" and r["provider"] == "edge":
            try:
                import edge_tts
            except ImportError as e:
                raise PipelineError("pip install edge-tts to use the edge voice provider") from e
            p = pdir / "build/audio" / f"{r['id']}.mp3"
            p.parent.mkdir(parents=True, exist_ok=True)
            voice = r.get("voice_name") or "en-US-GuyNeural"
            asyncio.run(edge_tts.Communicate(r["text"], voice, rate=cfg["voice"].get("edge_rate", "+0%")).save(str(p)))
            r["file"], r["fulfilled_by"] = str(p.relative_to(pdir)), f"edge:{voice}"
            n += 1
    write_json(pdir / "build/requests.json", reqs)
    print(f"fulfilled {n} request(s) locally")


def cmd_render(a):
    cfg = load_project(_pdir(a.project))
    render(cfg, draft=a.draft)


# ---------- channel episodes (HyperFrames composers) ----------

def _episode(name: str) -> Path:
    p = Path(name)
    if not (p / "episode.yaml").exists():
        p = PROJECTS / name
    if not (p / "episode.yaml").exists():
        raise PipelineError(f"episode not found: {name} (needs episode.yaml)")
    return p.resolve()


def _composer(P: Path):
    import importlib
    import yaml
    ep = yaml.safe_load((P / "episode.yaml").read_text())
    mod = importlib.import_module(f"channels.{ep['channel'].replace('-', '_')}.compose")
    return ep, mod


def cmd_compose(a):
    P = _episode(a.project)
    ep, mod = _composer(P)
    mod.build(P, P / "build", until=a.until, check_only=a.check)


def cmd_align(a):
    from .align import align_episode
    P = _episode(a.project)
    ep, mod = _composer(P)
    if (P / "words.json").exists() and not a.force:
        raise PipelineError("words.json already exists — pass --force to re-align")
    align_episode(P, ep["voice"], mod.load_channel()["audio"].get("part_gap", 0.6), ep.get("lexicon"))


def cmd_episode_render(a):
    from .hf import render as hf_render
    from .mix import mix
    P = _episode(a.project)
    ep, mod = _composer(P)
    index = mod.build(P, P / "build", until=a.until)
    import re
    end = float(re.search(r'data-composition-id="main" data-start="0" data-duration="([\d.]+)"', index.read_text()).group(1))
    mix(P, ep["voice"], mod.load_channel()["audio"], end, P / "build/assets/audio.wav")
    out = P / "out" / (f"{P.name}_0-{int(end)}s.mp4" if a.until else f"{P.name}.mp4")
    out.parent.mkdir(exist_ok=True)
    hf_render(P / "build", out, quality=a.quality)
    print(f"rendered {out}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="pipeline", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("new"); p.add_argument("slug"); p.add_argument("--style", default="documentary"); p.add_argument("--title")
    p.set_defaults(fn=cmd_new)
    p = sp.add_parser("plan"); p.add_argument("project"); p.set_defaults(fn=cmd_plan)
    p = sp.add_parser("status"); p.add_argument("project"); p.add_argument("--json", action="store_true")
    p.add_argument("--pending", action="store_true"); p.set_defaults(fn=cmd_status)
    p = sp.add_parser("fetch"); p.add_argument("project"); p.add_argument("request_id"); p.add_argument("source")
    p.add_argument("--credit"); p.add_argument("--source-url"); p.add_argument("--provider"); p.add_argument("--meta")
    p.set_defaults(fn=cmd_fetch)
    p = sp.add_parser("local"); p.add_argument("project"); p.set_defaults(fn=cmd_local)
    p = sp.add_parser("render"); p.add_argument("project"); p.add_argument("--draft", action="store_true")
    p.set_defaults(fn=cmd_render)
    p = sp.add_parser("compose", help="channel episode: write build/index.html (or --check the shot list)")
    p.add_argument("project"); p.add_argument("--check", action="store_true"); p.add_argument("--until", type=float)
    p.set_defaults(fn=cmd_compose)
    p = sp.add_parser("align", help="channel episode: word-align the voice recordings to the script")
    p.add_argument("project"); p.add_argument("--force", action="store_true"); p.set_defaults(fn=cmd_align)
    p = sp.add_parser("episode", help="channel episode: compose + audio mix + HyperFrames render")
    p.add_argument("project"); p.add_argument("--until", type=float, help="render only the first N seconds")
    p.add_argument("--quality", default="looks", choices=["draft", "looks", "delivery", "standard", "high"])
    p.set_defaults(fn=cmd_episode_render)
    a = ap.parse_args(argv)
    try:
        a.fn(a)
    except PipelineError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
