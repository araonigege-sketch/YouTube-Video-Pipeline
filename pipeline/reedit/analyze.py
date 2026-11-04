"""Analyse an edited talking-head video: find every cut and label each shot as host or B-roll.

python -m pipeline.reedit.analyze <video> <out_dir>
Writes <out_dir>/analysis.json and <out_dir>/sheet_NN.jpg contact sheets (one tile per shot,
labelled with index, start time, length and class) so a human or Claude can check the labels.

Host detection: the host's shots come from one or a few camera setups that together fill much of
the runtime, so shots are grouped by visual similarity, and big recurring groups are "host".
A face detector (MediaPipe, when available) is a secondary signal. Labels are a first guess:
check the contact sheets and correct analysis.json before planning.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def probe(video: Path) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate:format=duration", "-of", "json", str(video)],
                         capture_output=True, text=True, check=True)
    j = json.loads(out.stdout)
    st = j["streams"][0]
    num, den = st["r_frame_rate"].split("/")
    return {"width": st["width"], "height": st["height"], "fps": float(num) / float(den),
            "duration": float(j["format"]["duration"])}


def detect_cuts(video: Path, threshold: float = 10.0) -> list[float]:
    """Hard cuts via ffmpeg scdet on a downscaled copy of the stream."""
    proc = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-i", str(video), "-an",
                           "-vf", f"scale=320:-2,scdet=threshold={threshold}", "-f", "null", "-"],
                          capture_output=True, text=True)
    cuts = [float(m) for m in re.findall(r"lavfi\.scd\.time:\s*([\d.]+)", proc.stderr)]
    out = []
    for c in sorted(cuts):  # merge flicker within 0.4 s
        if not out or c - out[-1] > 0.4:
            out.append(c)
    return out


MODEL = Path(__file__).resolve().parent / "models/blaze_face_short_range.tflite"
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite"
_det = None


def _detector():
    """MediaPipe face detector, or None if MediaPipe/its model/EGL is unavailable."""
    global _det
    if _det is None:
        try:
            from mediapipe.tasks.python import BaseOptions, vision
            if not MODEL.exists():
                MODEL.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run(["curl", "-sSL", "-m", "60", "-o", str(MODEL), MODEL_URL], check=True)
            _det = vision.FaceDetector.create_from_options(vision.FaceDetectorOptions(
                base_options=BaseOptions(model_asset_path=str(MODEL)), min_detection_confidence=0.75))
        except Exception:
            _det = False
    return _det or None


def frame_at(cap, t: float):
    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
    ok, fr = cap.read()
    return fr if ok else None


def face_ratio(frame) -> float:
    det = _detector()
    if det is None:
        return -1.0
    import mediapipe as mp
    h, w = frame.shape[:2]
    r = det.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
    return max((d.bounding_box.width * d.bounding_box.height / (w * h) for d in r.detections), default=0.0)


def signature(frame) -> np.ndarray:
    """Colour + layout fingerprint of a frame (HSV histogram + tiny grayscale thumbnail)."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1], None, [16, 8], [0, 180, 0, 256]).flatten()
    hist /= hist.sum() + 1e-9
    thumb = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (32, 18)).flatten().astype(np.float32) / 255
    return np.concatenate([hist * 4, thumb / np.linalg.norm(thumb + 1e-9)])


def group_setups(shots, sim=0.9):
    """Greedy grouping of shots whose fingerprints are close (same camera setup)."""
    groups = []
    for s in shots:
        for g in groups:
            if float(np.dot(s["_sig"], g["sig"]) / (np.linalg.norm(s["_sig"]) * np.linalg.norm(g["sig"]))) > sim:
                g["members"].append(s); break
        else:
            groups.append({"sig": s["_sig"], "members": [s]})
    return groups


def analyse(video: Path, out: Path, threshold: float = 10.0) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    info = probe(video)
    cuts = detect_cuts(video, threshold)
    bounds = [0.0] + cuts + [info["duration"]]
    cap = cv2.VideoCapture(str(video))
    shots = []
    for i, (a, b) in enumerate(zip(bounds, bounds[1:])):
        if b - a < 0.05:
            continue
        samples = [a + (b - a) * f for f in (0.2, 0.5, 0.8)]
        frames = [fr for t in samples if (fr := frame_at(cap, t)) is not None]
        ratios = [face_ratio(fr) for fr in frames]
        thumb = frame_at(cap, (a + b) / 2)
        shots.append({"i": len(shots), "start": round(a, 3), "end": round(b, 3), "dur": round(b - a, 3),
                      "face": [round(r, 4) for r in ratios], "_thumb": thumb,
                      "_sig": signature(thumb if thumb is not None else frames[0])})
    cap.release()
    total = info["duration"]
    for gi, g in enumerate(sorted(group_setups(shots), key=lambda g: -sum(m["dur"] for m in g["members"]))):
        gdur = sum(m["dur"] for m in g["members"])
        recurring = len(g["members"]) >= 3 and gdur >= 0.12 * total
        for m in g["members"]:
            m["setup"] = gi
            faces = sum(r > 0.01 for r in m["face"])
            m["kind"] = "host" if recurring or (m["face"] and faces == len(m["face"])) else "broll"
    for s in shots:
        s.pop("_sig", None)
    _sheets(shots, out)
    for s in shots:
        s.pop("_thumb", None)
    host = sum(s["dur"] for s in shots if s["kind"] == "host")
    result = {"video": str(video), **info, "cuts": len(cuts), "shots": shots,
              "summary": {"shots": len(shots), "host_seconds": round(host, 1),
                          "broll_seconds": round(info["duration"] - host, 1),
                          "broll_shots": sum(s["kind"] == "broll" for s in shots),
                          "avg_shot": round(info["duration"] / max(1, len(shots)), 2)}}
    (out / "analysis.json").write_text(json.dumps(result, indent=1))
    return result


def _sheets(shots, out: Path, cols=6, per_sheet=36):
    tw, th = 320, 180
    try:
        font = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Bold.otf", 18)
    except OSError:
        font = ImageFont.load_default()
    for n, k in enumerate(range(0, len(shots), per_sheet)):
        chunk = shots[k:k + per_sheet]
        rows = (len(chunk) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * tw, rows * th), "black")
        for j, s in enumerate(chunk):
            fr = s["_thumb"]
            img = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)).resize((tw, th)) if fr is not None else Image.new("RGB", (tw, th))
            d = ImageDraw.Draw(img)
            col = (80, 200, 120) if s["kind"] == "host" else (240, 170, 40)
            d.rectangle((0, 0, tw - 1, th - 1), outline=col, width=4)
            label = f"#{s['i']} {s['start']:.1f}s {s['dur']:.1f}s {s['kind'].upper()} g{s['setup']}"
            d.rectangle((0, th - 28, tw, th), fill=(0, 0, 0))
            d.text((8, th - 25), label, font=font, fill=col)
            sheet.paste(img, ((j % cols) * tw, (j // cols) * th))
        sheet.save(out / f"sheet_{n + 1:02d}.jpg", quality=82)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    r = analyse(Path(sys.argv[1]), Path(sys.argv[2]), float(sys.argv[3]) if len(sys.argv) > 3 else 10.0)
    print(json.dumps(r["summary"]))
