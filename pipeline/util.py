"""Shared helpers: ffmpeg/ffprobe wrappers, JSON IO, downloads, fonts."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import ssl
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path


class PipelineError(RuntimeError):
    pass


def ffmpeg(args: list[str], cwd: Path | None = None, quiet: bool = True) -> None:
    cmd = ["ffmpeg", "-hide_banner", "-nostdin", "-y"]
    if quiet:
        cmd += ["-loglevel", "error"]
    cmd += [str(a) for a in args]
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise PipelineError(f"ffmpeg failed:\n  {' '.join(cmd)}\n{proc.stderr[-3000:]}")


def duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True,
    )
    try:
        return float(out.stdout.strip())
    except ValueError as e:
        raise PipelineError(f"could not read duration of {path}: {out.stderr}") from e


def has_video_stream(path: Path) -> bool:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=codec_name", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True,
    )
    return bool(out.stdout.strip())


def detect_silences(path: Path, noise_db: float = -35, min_dur: float = 0.25) -> list[tuple[float, float]]:
    """Return [(start, end), ...] silent spans, via ffmpeg silencedetect."""
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostdin", "-i", str(path),
         "-af", f"silencedetect=noise={noise_db}dB:d={min_dur}", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    spans, start = [], None
    for line in proc.stderr.splitlines():
        if m := re.search(r"silence_start: (-?[\d.]+)", line):
            start = max(0.0, float(m.group(1)))
        elif (m := re.search(r"silence_end: ([\d.]+)", line)) and start is not None:
            spans.append((start, float(m.group(1))))
            start = None
    if start is not None:  # silence runs to end of file
        spans.append((start, duration(path)))
    return spans


def read_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text())


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    tmp.replace(path)


def short_hash(*parts) -> str:
    return hashlib.sha1(json.dumps(parts, sort_keys=True).encode()).hexdigest()[:10]


_EXT_BY_TYPE = {
    "audio/mpeg": ".mp3", "audio/mp3": ".mp3", "audio/wav": ".wav", "audio/x-wav": ".wav",
    "audio/wave": ".wav", "video/mp4": ".mp4", "video/quicktime": ".mov", "video/webm": ".webm",
    "image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp",
}


def fetch_to(src: str, target_stem: Path) -> Path:
    """Download a URL (or copy a local file) to target_stem + detected extension."""
    target_stem.parent.mkdir(parents=True, exist_ok=True)
    for old in target_stem.parent.glob(target_stem.name + ".*"):
        old.unlink()
    if not re.match(r"^https?://", src):
        p = Path(src).expanduser()
        if not p.exists():
            raise PipelineError(f"no such file: {src}")
        dest = target_stem.with_suffix(p.suffix.lower())
        shutil.copyfile(p, dest)
        return dest
    cafile = next((os.environ[k] for k in ("SSL_CERT_FILE", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE")
                   if os.environ.get(k) and Path(os.environ[k]).exists()), None)
    ctx = ssl.create_default_context(cafile=cafile)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler(), urllib.request.HTTPSHandler(context=ctx))
    req = urllib.request.Request(src, headers={"User-Agent": "faceless-pipeline/0.1"})
    try:
        with opener.open(req, timeout=180) as resp:
            ctype = (resp.headers.get_content_type() or "").lower()
            ext = Path(urllib.parse.urlparse(src).path).suffix.lower()
            if ext not in {".mp3", ".wav", ".mp4", ".mov", ".webm", ".png", ".jpg", ".jpeg", ".webp", ".m4a"}:
                ext = _EXT_BY_TYPE.get(ctype, ".bin")
            dest = target_stem.with_suffix(ext)
            with open(dest, "wb") as f:
                shutil.copyfileobj(resp, f)
    except (urllib.error.URLError, OSError) as e:
        host = urllib.parse.urlparse(src).hostname
        raise PipelineError(f"download failed from {host}: {getattr(e, 'reason', e)}\n"
                            "  (if a proxy/firewall blocks this host, download the file manually and pass its local path)") from e
    if dest.stat().st_size == 0:
        raise PipelineError(f"downloaded file is empty: {src}")
    return dest


def find_font(family: str, bold: bool = True) -> str | None:
    pattern = f"{family}:bold" if bold else family
    try:
        out = subprocess.run(["fc-match", "-f", "%{file}", pattern], capture_output=True, text=True)
        return out.stdout.strip() or None
    except FileNotFoundError:
        return None


def ts(seconds: float) -> str:
    """YouTube-style timestamp m:ss / h:mm:ss."""
    s = int(seconds)
    h, m, s = s // 3600, (s % 3600) // 60, s % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
