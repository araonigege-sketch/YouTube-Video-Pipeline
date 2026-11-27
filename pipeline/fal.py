"""fal.ai generation (backup only: see channels/by_design_with_joe/STYLE.md). Queue API with the key injected by the proxy.

  python -m pipeline.fal <model> '<json args>' <out_path>      e.g.
  python -m pipeline.fal fal-ai/flux-pro/v1.1-ultra '{"prompt": "...", "aspect_ratio": "16:9"}' media/ai/x.jpg
  python -m pipeline.fal fal-ai/kling-video/v2.1/master/image-to-video '{"prompt": "...", "image_url": "..."}' media/ai/x.mp4

Writes the first image/video of the result to <out_path> and <out_path>.json (model, args, request id, source url)
so every generated shot is traceable. Local images given as "image_url": "file:<path>" are sent as data URIs.
"""
from __future__ import annotations

import base64
import json
import mimetypes
import sys
import time
from pathlib import Path

import requests

Q = "https://queue.fal.run"
H = {"Authorization": "Key proxy-injected", "Content-Type": "application/json"}   # the proxy swaps in the real key


def _inline(args: dict) -> dict:
    out = {}
    for k, v in args.items():
        if isinstance(v, str) and v.startswith("file:"):
            p = Path(v[5:])
            mt = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
            v = f"data:{mt};base64," + base64.b64encode(p.read_bytes()).decode()
        out[k] = v
    return out


def run(model: str, args: dict, timeout: float = 1800) -> dict:
    r = requests.post(f"{Q}/{model}", headers=H, json=_inline(args), timeout=120)
    r.raise_for_status()
    j = r.json()
    t0 = time.time()
    while True:
        s = requests.get(j["status_url"], headers=H, timeout=60).json()
        if s.get("status") == "COMPLETED":
            break
        if s.get("status") not in ("IN_QUEUE", "IN_PROGRESS") or time.time() - t0 > timeout:
            raise SystemExit(f"fal {model}: {s}")
        time.sleep(4)
    res = requests.get(j["response_url"], headers=H, timeout=60).json()
    res["_request_id"] = j["request_id"]
    return res


def first_url(res: dict) -> str:
    if res.get("video"):
        return res["video"]["url"]
    if res.get("images"):
        return res["images"][0]["url"]
    if res.get("image"):
        return res["image"]["url"]
    raise SystemExit(f"no media in result: {list(res)}")


def generate(model: str, args: dict, out: Path) -> Path:
    res = run(model, args)
    url = first_url(res)
    out.parent.mkdir(parents=True, exist_ok=True)
    data = requests.get(url, timeout=600).content
    out.write_bytes(data)
    meta = {"model": model, "args": {k: (v if not str(v).startswith("file:") else v) for k, v in args.items()},
            "request_id": res["_request_id"], "url": url, "generated": "fal.ai (AI-generated)"}
    Path(str(out) + ".json").write_text(json.dumps(meta, indent=1))
    print(f"{out} ({len(data) // 1024} KB) from {model}")
    return out


if __name__ == "__main__":
    generate(sys.argv[1], json.loads(sys.argv[2]), Path(sys.argv[3]))
