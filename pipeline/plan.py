"""Turn a parsed script into a production plan + an asset request list.

build/plan.json      scenes, their shots, voice chunks
build/requests.json  every asset the render needs, with provider + prompt + target.
                     A request is "done" when its `file` exists. Hosted requests
                     (vidiq/openart) are fulfilled by Claude via MCP tools, then
                     registered with `python -m pipeline fetch`.
"""
from __future__ import annotations

import math
from pathlib import Path

from .script import parse_script
from .util import read_json, short_hash, write_json

VISUAL_PROVIDERS = {"stock": "vidiq", "image": "openart", "card": "local"}


def build_plan(cfg: dict) -> tuple[dict, list[dict]]:
    pdir: Path = cfg["dir"]
    vis, voice = cfg["visuals"], cfg["voice"]
    parsed = parse_script((pdir / "script.md").read_text(), vis["default_kind"])

    scenes = []
    for sc in parsed["scenes"]:
        est = len(sc["text"].split()) / voice["wpm"] * 60
        n = max(len(sc["hints"]), math.ceil(est / vis["max_shot_seconds"]), 1)
        shots = []
        for k in range(n):
            if sc["hints"]:
                hint = sc["hints"][k % len(sc["hints"])]
                variant = k // len(sc["hints"])
                source = "hint"
                if hint["kind"] == "card" and variant > 0:  # never repeat a text card; fill with footage
                    hint = {"kind": vis["default_kind"], "prompt": sc["text"]}
                    source = "narration"
            else:
                hint = {"kind": vis["default_kind"], "prompt": sc["text"]}
                variant, source = k, "narration"
            shots.append({"id": f"{sc['id']}_{k + 1}", "kind": hint["kind"], "prompt": hint["prompt"],
                          "variant": variant, "prompt_source": source})
        scenes.append({**sc, "est_seconds": round(est, 2), "shots": shots})

    # Group scenes into voice chunks (fewer TTS calls; vidIQ bills per started 1000 chars).
    chunks, cur, cur_len = [], [], 0
    for sc in scenes:
        if cur and cur_len + len(sc["text"]) + 2 > voice["max_chunk_chars"]:
            chunks.append(cur)
            cur, cur_len = [], 0
        cur.append(sc)
        cur_len += len(sc["text"]) + 2
    if cur:
        chunks.append(cur)
    voice_chunks = []
    for i, group in enumerate(chunks, 1):
        cid = f"voice_c{i:02d}"
        for sc in group:
            sc["chunk"] = cid
        voice_chunks.append({"id": cid, "scenes": [s["id"] for s in group]})

    plan = {"title": cfg["project"].get("title") or parsed["title"], "scenes": scenes, "voice_chunks": voice_chunks}

    # ---- requests ----
    reqs = []
    for ch in voice_chunks:
        text = "\n\n".join(s["text"] for s in scenes if s["chunk"] == ch["id"])
        reqs.append({"id": ch["id"], "type": "voice", "provider": voice["provider"],
                     "voice_id": voice.get("voice_id"), "voice_name": voice.get("voice_name"),
                     "text": text, "chars": len(text)})
    for sc in scenes:
        for i, shot in enumerate(sc["shots"]):
            shot_secs = sc["est_seconds"] / len(sc["shots"])
            r = {"id": f"vis_{shot['id']}", "type": "visual", "kind": shot["kind"],
                 "provider": VISUAL_PROVIDERS[shot["kind"]], "variant": shot["variant"],
                 "prompt": shot["prompt"], "prompt_source": shot["prompt_source"], "scene": sc["id"]}
            if shot["kind"] == "stock":
                r["orientation"] = "landscape"
                r["min_seconds"] = max(3, math.ceil(shot_secs))
            elif shot["kind"] == "image":
                r["prompt_full"] = f"{shot['prompt']}, {vis['image_style']}"
                r["aspect_ratio"] = "16:9"
            reqs.append(r)
    if cfg["music"].get("enabled", True):
        reqs.append({"id": "music_bed", "type": "music", "provider": cfg["music"]["provider"],
                     "prompt": cfg["music"]["prompt"], "duration_seconds": 180})

    for r in reqs:
        r["key"] = short_hash(r["type"], r.get("text"), r.get("voice_id"), r.get("prompt"),
                              r.get("variant"), r.get("kind"))
    return plan, reqs


def merge_requests(old: list[dict], new: list[dict], pdir: Path) -> tuple[list[dict], list[str]]:
    """Keep fulfilment info for requests whose content didn't change."""
    by_id = {r["id"]: r for r in old}
    stale = []
    for r in new:
        prev = by_id.get(r["id"])
        if not prev or not prev.get("file"):
            continue
        if prev.get("key") == r["key"]:
            for k in ("file", "source_url", "credit", "fulfilled_by", "meta"):
                if k in prev:
                    r[k] = prev[k]
        else:
            stale.append(r["id"])
    return new, stale


def save_plan(cfg: dict) -> dict:
    pdir: Path = cfg["dir"]
    plan, reqs = build_plan(cfg)
    reqs, stale = merge_requests(read_json(pdir / "build/requests.json", []), reqs, pdir)
    write_json(pdir / "build/plan.json", plan)
    write_json(pdir / "build/requests.json", reqs)
    return {"plan": plan, "requests": reqs, "stale": stale}


def request_done(r: dict, pdir: Path) -> bool:
    return bool(r.get("file")) and (pdir / r["file"]).exists()
