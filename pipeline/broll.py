"""B-roll candidate pool for footage-led channels: search, judge on a contact sheet, then fetch the best rendition.

Candidates live in projects/<slug>/build/cands/cands.json; previews (small mp4s) next to it.
Chosen clips go to projects/<slug>/media/broll/<id>.mp4 and are credited in media/broll/credits.json.

  python -m pipeline.broll pixabay <slug> "<query>" [--n 12] [--min-h 1080]
      Pixabay API search (key: env PIXABAY_API_KEY). Skips low-quality/AI clips and anything under --min-h.
  python -m pipeline.broll pexels <slug> <tag> <mp4_url> "<photographer>" [<mp4_url> "<photographer>" ...]
      Register Pexels clips found with vidIQ `find_broll` (it returns 4 per search). <tag> labels the search.
  python -m pipeline.broll sheet <slug> <out.jpg> [ids...|--tag TAG]
      Three frames per candidate, labelled id / source size / length, for picking by eye.
  python -m pipeline.broll get <slug> <id> [<id> ...]
      Download the best rendition (Pexels: 1080p+ via pexels.py; Pixabay: large/medium) and record the credit.
  python -m pipeline.broll ledger [--scan] [--channel <name>]
      Clips already used by this channel's episodes (never repeat a clip across episodes).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from .config import ROOT

UA = {"User-Agent": "video-pipeline/1.0 (broll fetcher)"}


def _p(slug: str) -> Path:
    return ROOT / "projects" / slug


def _db(P: Path) -> tuple[Path, dict]:
    f = P / "build/cands/cands.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    return f, (json.loads(f.read_text()) if f.exists() else {})


def _dl(url: str, out: Path) -> bool:
    out.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["curl", "-sSL", "-m", "300", "-A", UA["User-Agent"], "-o", str(out), "-w", "%{http_code}", url],
                       capture_output=True, text=True)
    ok = r.stdout.strip() == "200" and out.exists() and out.stat().st_size > 10000
    if not ok:
        out.unlink(missing_ok=True)
    return ok


def pixabay(slug: str, query: str, n: int = 12, min_h: int = 1080):
    P = _p(slug)
    f, db = _db(P)
    q = urllib.parse.urlencode({"key": os.environ["PIXABAY_API_KEY"], "q": query[:100], "per_page": max(3, min(200, n * 2)),
                                "video_type": "film", "safesearch": "true", "order": "popular"})
    with urllib.request.urlopen(urllib.request.Request(f"https://pixabay.com/api/videos/?{q}", headers=UA), timeout=60) as r:
        hits = json.load(r)["hits"]
    added = 0
    for h in hits:
        if added >= n:
            break
        if h.get("isLowQuality") or h.get("isAiGenerated"):
            continue
        v = h["videos"]
        best = max((x for x in v.values() if x.get("url") and x.get("width")), key=lambda x: x["width"] * x["height"])
        if best["height"] < min_h:
            continue
        cid = f"px{h['id']}"
        if cid in db:
            continue
        prev = P / "build/cands" / f"{cid}.mp4"
        if not _dl(v["tiny"]["url"] or v["small"]["url"], prev):
            continue
        db[cid] = {"src": "pixabay", "tag": query, "w": best["width"], "h": best["height"], "dur": h["duration"],
                   "url": best["url"], "page": h["pageURL"], "credit": f"{h['user']} (Pixabay)"}
        added += 1
    f.write_text(json.dumps(db, indent=1))
    print(f"pixabay {query!r}: +{added} ({len(hits)} hits)")


def pexels(slug: str, tag: str, pairs: list[str]):
    P = _p(slug)
    f, db = _db(P)
    for url, who in zip(pairs[::2], pairs[1::2]):
        m = re.search(r"video-files/(\d+)/", url)
        if not m:
            print("skip (not a Pexels file url):", url)
            continue
        cid = f"pe{m.group(1)}"
        if cid in db:
            continue
        prev = P / "build/cands" / f"{cid}.mp4"
        if not _dl(url, prev):
            print("preview failed:", cid)
            continue
        db[cid] = {"src": "pexels", "tag": tag, "url": url, "page": f"https://www.pexels.com/video/{m.group(1)}/",
                   "credit": f"{who} (Pexels)"}
    f.write_text(json.dumps(db, indent=1))
    print(f"pexels {tag!r}: {len(db)} candidates in pool")


def sheet(slug: str, out: str, ids: list[str], tag: str | None = None):
    from .reedit.candsheet import sheet as mk
    P = _p(slug)
    _, db = _db(P)
    if tag:
        ids = [k for k, v in db.items() if v.get("tag") == tag]
    ids = ids or list(db)
    mk([P / "build/cands" / f"{i}.mp4" for i in ids if (P / "build/cands" / f"{i}.mp4").exists()], Path(out))
    print(f"sheet: {len(ids)} clips -> {out}")


def get(slug: str, ids: list[str]):
    from .reedit.pexels import fetch
    P = _p(slug)
    _, db = _db(P)
    dest = P / "media/broll"
    cf = dest / os.environ.get("BROLL_CREDITS", "credits.json")   # parallel workers write separate files, merged after
    credits = json.loads(cf.read_text()) if cf.exists() else {}
    for cid in ids:
        c = db[cid]
        out = dest / f"{cid}.mp4"
        if not out.exists():
            if c["src"] == "pexels":
                (dest / "_pexels").mkdir(parents=True, exist_ok=True)
                got = fetch(c["url"], dest / "_pexels")
                if got:
                    got.rename(out)
            elif not _dl(c["url"], out):
                got = None
            if not out.exists():
                print("download failed:", cid)
                continue
        w, h = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                               "-of", "csv=p=0", str(out)], capture_output=True, text=True).stdout.strip().split(",")[:2]
        credits[cid] = {"credit": c["credit"], "page": c["page"], "w": int(w), "h": int(h)}
        print(f"{cid}: {w}x{h}{'  <-- below 1080p' if int(h) < 1080 else ''}")
    cf.write_text(json.dumps(credits, indent=1))


def _channel(project: Path) -> str | None:
    ep = project / "episode.yaml"
    if not ep.exists():
        return None
    m = re.search(r"^channel:\s*([\w-]+)", ep.read_text(), re.M)
    return m.group(1).replace("-", "_") if m else None


def ledger(scan: bool = False, channel: str | None = None):
    """Clip ids used by every Mr. Davos-style project (edit.yaml `src: broll/<id>`).

    `channel` limits the ledger to one channel's episodes: the cross-episode "no clip twice" rule is per channel
    (By Design With Joe may reuse Mr. Davos clips, owner 2026-11-24)."""
    used: dict[str, list[str]] = {}
    want = channel.replace("-", "_") if channel else None
    for ep in sorted((ROOT / "projects").glob("*/edit.yaml")):
        if want and _channel(ep.parent) != want:
            continue
        txt = ep.read_text()
        for cid in sorted(set(re.findall(r"broll/((?:pe|px|ar|nw)[\w-]+)", txt))):
            used.setdefault(cid, []).append(ep.parent.name)
    for k, v in sorted(used.items()):
        print(k, ", ".join(v))
    return used


def main(argv=None):
    ap = argparse.ArgumentParser(prog="broll")
    sp = ap.add_subparsers(dest="cmd", required=True)
    a = sp.add_parser("pixabay"); a.add_argument("slug"); a.add_argument("query"); a.add_argument("--n", type=int, default=12)
    a.add_argument("--min-h", type=int, default=1080)
    a = sp.add_parser("pexels"); a.add_argument("slug"); a.add_argument("tag"); a.add_argument("pairs", nargs="+")
    a = sp.add_parser("sheet"); a.add_argument("slug"); a.add_argument("out"); a.add_argument("ids", nargs="*"); a.add_argument("--tag")
    a = sp.add_parser("get"); a.add_argument("slug"); a.add_argument("ids", nargs="+")
    a = sp.add_parser("ledger"); a.add_argument("--scan", action="store_true"); a.add_argument("--channel")
    a = ap.parse_args(argv)
    if a.cmd == "pixabay":
        pixabay(a.slug, a.query, a.n, a.min_h)
    elif a.cmd == "pexels":
        pexels(a.slug, a.tag, a.pairs)
    elif a.cmd == "sheet":
        sheet(a.slug, a.out, a.ids, a.tag)
    elif a.cmd == "get":
        get(a.slug, a.ids)
    else:
        ledger(a.scan, a.channel)


if __name__ == "__main__":
    main()
