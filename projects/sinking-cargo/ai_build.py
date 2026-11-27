"""Build the fal.ai backup shots listed in ai_shots.yaml (stills first, review, then videos).

  python projects/sinking-cargo/ai_build.py stills [name ...]
  python projects/sinking-cargo/ai_build.py videos [name ...]
Outputs media/ai/<name>_still.jpg and media/ai/<name>.mp4 (+ .json provenance). Runs up to 4 at once.
"""
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

P = Path(__file__).resolve().parent
sys.path.insert(0, str(P.parent.parent))
from pipeline.fal import generate  # noqa: E402

cfg = yaml.safe_load((P / "ai_shots.yaml").read_text())
what = sys.argv[1]
names = sys.argv[2:] or list(cfg["shots"])
AI = P / "media/ai"


def one(n):
    s = cfg["shots"][n]
    try:
        if what == "stills":
            generate("fal-ai/bytedance/seedream/v4/text-to-image",
                     {"prompt": s["still"] + " " + cfg["style"], "image_size": {"width": 2560, "height": 1440}},
                     AI / f"{n}_still.jpg")
        else:
            generate("fal-ai/kling-video/v2.1/master/image-to-video",
                     {"prompt": s["motion"], "image_url": f"file:{AI / (n + '_still.jpg')}", "duration": "5",
                      "negative_prompt": "blur, distort, morphing, warping, text, logo, cartoon", "cfg_scale": 0.5},
                     AI / f"{n}.mp4")
    except BaseException as e:   # noqa: BLE001
        print(f"FAILED {n}: {e}", flush=True)


with ThreadPoolExecutor(4) as ex:
    list(ex.map(one, names))
