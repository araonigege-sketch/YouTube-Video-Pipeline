"""Typography for on-screen text: curly quotes and apostrophes, then HTML-escape."""
from __future__ import annotations

import html
import re


def smart(s: str) -> str:
    s = str(s)
    s = re.sub(r"(?<=\w)'(?=\w)", "\u2019", s)                 # it's, don't
    s = re.sub(r"(?<=[\w.,!?])'", "\u2019", s)                 # veterans', closing single quote
    s = re.sub(r"'(?=\d)", "\u2019", s)                     # '90s
    s = re.sub(r"'", "\u2018", s)                               # any remaining: opening single quote
    s = re.sub(r'(^|[\s(\[{\u2014\-])"', "\\1\u201c", s)       # opening double quote
    s = s.replace('"', "\u201d")                                # closing double quote
    return s


def esc(s) -> str:
    return html.escape(smart(s))
