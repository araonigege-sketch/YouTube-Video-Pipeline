"""Load a project's config: style profile (styles/<name>.yaml) + project.yaml overrides."""
from __future__ import annotations

import copy
from pathlib import Path

import yaml

from .util import PipelineError

ROOT = Path(__file__).resolve().parent.parent
STYLES_DIR = ROOT / "styles"


def deep_merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def load_style(name: str) -> dict:
    path = STYLES_DIR / f"{name}.yaml"
    if not path.exists():
        avail = ", ".join(p.stem for p in STYLES_DIR.glob("*.yaml"))
        raise PipelineError(f"unknown style '{name}' (available: {avail})")
    style = yaml.safe_load(path.read_text()) or {}
    if parent := style.pop("extends", None):
        style = deep_merge(load_style(parent), style)
    return style


def load_project(pdir: Path) -> dict:
    pfile = pdir / "project.yaml"
    if not pfile.exists():
        raise PipelineError(f"{pdir} is not a project (no project.yaml)")
    proj = yaml.safe_load(pfile.read_text()) or {}
    cfg = deep_merge(load_style(proj.get("style", "documentary")), proj.get("overrides") or {})
    cfg["project"] = proj
    cfg["dir"] = pdir
    return cfg
