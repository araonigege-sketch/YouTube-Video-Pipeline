"""Burned-in captions + chapter titles as an ASS subtitle file (rendered by libass)."""
from __future__ import annotations

import re
from pathlib import Path


def _t(sec: float) -> str:
    cs = max(0, round(sec * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _esc(s: str) -> str:
    return s.replace("\\", "/").replace("{", "(").replace("}", ")")


def _ass_color(hex_rgb: str, alpha: int = 0) -> str:
    c = hex_rgb.lstrip("#")
    return f"&H{alpha:02X}{c[4:6]}{c[2:4]}{c[0:2]}".upper()


def phrases(text: str, max_words: int) -> list[str]:
    out, cur = [], []
    for w in text.split():
        cur.append(w)
        hard = re.search(r"[.!?]['\"”’)]*$", w)
        soft = re.search(r"[,;:—–]['\"”’)]*$", w) and len(cur) >= max(3, max_words // 2)
        if len(cur) >= max_words or hard or soft:
            out.append(" ".join(cur))
            cur = []
    if cur:
        if out and len(cur) <= 2 and len(out[-1].split()) + len(cur) <= max_words + 2:
            out[-1] += " " + " ".join(cur)
        else:
            out.append(" ".join(cur))
    return out


def _timed_phrases(ps: list[str], a: float, b: float, pauses: list) -> list[tuple[float, float, str]]:
    """Spread phrases over [a, b] by length, snapping phrase breaks to real pauses.

    Pauses are matched in order to the phrase breaks they sit closest to, then each
    segment between anchors is filled proportionally to character count.
    """
    weights = [len(p) + 3 for p in ps]
    tot = sum(weights)
    est, acc = [], 0
    for w in weights[:-1]:
        acc += w
        est.append(a + (b - a) * acc / tot)
    # anchors: break index -> (speech_end, next_start)
    anchors: dict[int, tuple[float, float]] = {}
    last_i = -1
    for s0, s1 in pauses:
        mid = (s0 + s1) / 2
        cands = [i for i in range(last_i + 1, len(est)) if abs(est[i] - mid) < 1.5]
        if cands:
            i = min(cands, key=lambda i: abs(est[i] - mid))
            anchors[i], last_i = (s0, s1), i
    out, seg_start, i0 = [], a, 0
    keys = sorted(anchors) + [len(ps) - 1]
    for k in keys:
        seg_end = anchors[k][0] if k in anchors else b
        seg_w = weights[i0:k + 1]
        st, run = seg_start, 0
        for j, w in enumerate(seg_w):
            run += w
            en = seg_start + (seg_end - seg_start) * run / sum(seg_w)
            out.append((st, en, ps[i0 + j]))
            st = en
        if k in anchors:
            seg_start = anchors[k][1]
            out[-1] = (out[-1][0], anchors[k][1] - 0.05, out[-1][2])  # hold caption through the pause
        i0 = k + 1
    return out


def write_ass(plan: dict, cfg: dict, out: Path) -> None:
    w, h = cfg["video"]["resolution"]
    cap, chap = cfg["captions"], cfg["chapter_titles"]
    scale = h / 1080
    styles = [
        f"Style: Cap,{cap['font']},{int(cap['size'] * scale)},{_ass_color(cap['color'])},&H000000FF,"
        f"{_ass_color(cap['outline_color'])},&H64000000,-1,0,0,0,100,100,0,0,1,"
        f"{cap['outline'] * scale:.1f},{cap['shadow'] * scale:.1f},2,{int(160 * scale)},{int(160 * scale)},{int(cap['margin_v'] * scale)},1",
        f"Style: Chap,{chap['font']},{int(chap['size'] * scale)},{_ass_color(chap['color'])},&H000000FF,"
        f"&H00000000,&H96000000,-1,0,0,0,100,100,{chap['spacing']},0,1,0,{2 * scale:.1f},7,"
        f"{int(120 * scale)},{int(120 * scale)},{int(110 * scale)},1",
        f"Style: Kick,{chap['font']},{int(chap['size'] * 0.42 * scale)},{_ass_color(chap['accent'])},&H000000FF,"
        f"&H00000000,&H96000000,-1,0,0,0,100,100,6,0,1,0,{2 * scale:.1f},7,"
        f"{int(124 * scale)},{int(120 * scale)},{int(80 * scale)},1",
    ]
    events = []
    if cap.get("enabled", True):
        for sc in plan["scenes"]:
            ps = phrases(sc["text"], cap["max_words"])
            for s, e, p in _timed_phrases(ps, sc["speech0"], sc["speech1"], sc.get("pauses", [])):
                txt = p.upper() if cap.get("uppercase") else p
                events.append(f"Dialogue: 0,{_t(s)},{_t(e)},Cap,,0,0,0,,{_esc(txt)}")
    if chap.get("enabled", True):
        n = 0
        for sc in plan["scenes"]:
            if sc.get("chapter_start") and sc.get("chapter"):
                n += 1
                s, e = sc["t0"] + 0.4, sc["t0"] + 0.4 + chap["seconds"]
                fad = r"{\fad(600,700)}"
                events.append(f"Dialogue: 1,{_t(s)},{_t(e)},Kick,,0,0,0,,{fad}{_esc(chap['kicker'].format(n=n))}")
                events.append(f"Dialogue: 1,{_t(s)},{_t(e)},Chap,,0,0,0,,{fad}{_esc(sc['chapter'])}")
    out.write_text(
        "[Script Info]\nScriptType: v4.00+\n"
        f"PlayResX: {w}\nPlayResY: {h}\nWrapStyle: 0\nScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, "
        "Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        + "\n".join(styles)
        + "\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        + "\n".join(events) + "\n"
    )
