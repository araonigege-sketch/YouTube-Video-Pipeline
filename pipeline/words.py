"""Word timings: find when a phrase is spoken.

words.json is a list of {"w": token, "s": start, "e": end} in seconds, one entry per
script token (punctuation attached), as written by the aligner.
"""
from __future__ import annotations

import json
import re
from pathlib import Path


def _norm(t: str) -> str:
    return re.sub(r"[^a-z0-9$%]", "", t.lower().replace("’", "'"))


class Words:
    def __init__(self, words: list[dict]):
        self.words = words
        self.norm = [_norm(w["w"]) for w in words]

    @classmethod
    def load(cls, path: Path) -> "Words":
        return cls(json.loads(Path(path).read_text()))

    def __len__(self):
        return len(self.words)

    def find(self, phrase: str, after: float = 0.0) -> int:
        """Index of the first word of `phrase` spoken at or after `after` seconds."""
        a = [_norm(x) for x in phrase.split()]
        a = [x for x in a if x]
        for i in range(len(self.norm)):
            if self.words[i]["s"] + 1e-6 < after:
                continue
            if all(i + k < len(self.norm) and self.norm[i + k].startswith(a[k]) for k in range(len(a))):
                return i
        raise KeyError(f"phrase not found in narration (after {after:.1f}s): {phrase!r}")

    def T(self, phrase: str, after: float = 0.0, end: bool = False) -> float:
        """Start time of `phrase` (or end time of its last word when end=True)."""
        i = self.find(phrase, after)
        n = len([x for x in phrase.split() if _norm(x)])
        return self.words[i + n - 1]["e"] if end else self.words[i]["s"]

    def at(self, x, t0: float) -> float:
        """Resolve an anchor: number = seconds after t0; "phrase" = when it starts; ">phrase" = when it ends."""
        if isinstance(x, str):
            end = x.startswith(">")
            return self.T(x[1:] if end else x, after=t0 - 1.5, end=end)
        return t0 + float(x)

    def caption_groups(self, max_words: int = 5, max_chars: int = 32) -> list[tuple[float, float, str]]:
        """Split narration into caption chunks, breaking at punctuation."""
        groups, cur = [], []
        for i, w in enumerate(self.words):
            cur.append(i)
            txt = " ".join(self.words[k]["w"] for k in cur)
            if w["w"][-1] in ".?!,;:" or len(cur) >= max_words or len(txt) >= max_chars:
                groups.append(cur)
                cur = []
        if cur:
            groups.append(cur)
        out = []
        for k, ids in enumerate(groups):
            s = self.words[ids[0]]["s"]
            e = self.words[groups[k + 1][0]]["s"] if k + 1 < len(groups) else self.words[ids[-1]]["e"] + 0.5
            e = min(e, self.words[ids[-1]]["e"] + 0.6)
            out.append((s, max(s + 0.2, e), " ".join(self.words[i]["w"] for i in ids)))
        return out
