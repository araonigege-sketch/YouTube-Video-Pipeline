"""Forced-align known script text to a recording with PocketSphinx (offline, model bundled with the package).
Usage: python3 align.py <audio> <text.txt> <out_words.json> [time_offset]
Output: [{w, s, e}] with one entry per *script* token (punctuation kept), times in seconds (+offset).
Numbers, symbols and acronyms are expanded to spoken words for alignment, then mapped back.
"""
import sys, json, re, wave, subprocess, tempfile, os
from pocketsphinx import Decoder

ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()
def n2w(n):
    if n < 20: return [ONES[n]]
    if n < 100: return [TENS[n // 10]] + ([ONES[n % 10]] if n % 10 else [])
    if n < 1000: return [ONES[n // 100], "hundred"] + (n2w(n % 100) if n % 100 else [])
    if n < 1_000_000: return n2w(n // 1000) + ["thousand"] + (n2w(n % 1000) if n % 1000 else [])
    return n2w(n // 1_000_000) + ["million"] + (n2w(n % 1_000_000) if n % 1_000_000 else [])
def year(n):
    return n2w(n // 100) + (n2w(n % 100) if n % 100 >= 10 else ["oh"] + n2w(n % 100) if n % 100 else ["hundred"]) \
        if not (2000 <= n < 2010) else ["two", "thousand"] + (n2w(n % 100) if n % 100 else [])

def spoken(tok):
    t = tok.replace("’", "'").replace("‘", "'")
    core = re.sub(r"^[^\w$]+|[^\w%+]+$", "", t)
    m = re.fullmatch(r"\$([\d,]+)\+?", core)
    if m: return n2w(int(m.group(1).replace(",", ""))) + ["dollars"]
    m = re.fullmatch(r"(\d+)%", core)
    if m: return n2w(int(m.group(1))) + ["percent"]
    m = re.fullmatch(r"(1\d)(\d)0s", core)
    if m:
        tens = {"2": "twenties", "3": "thirties", "4": "forties", "5": "fifties", "6": "sixties", "7": "seventies", "8": "eighties", "9": "nineties"}
        return n2w(int(m.group(1))) + [tens.get(m.group(2), "hundreds")]
    if re.fullmatch(r"(1[0-9]|20)\d\d", core): return year(int(core))
    if re.fullmatch(r"\d[\d,]*", core): return n2w(int(core.replace(",", "")))
    if re.fullmatch(r"[A-Z]{2,4}", core): return list(core.lower())
    return [w for w in re.split(r"[-\u2013]", core.lower()) if w]

d = Decoder(samprate=16000)
EXTRA = {"zoroastrian": "Z AO R OW AE S T R IY AH N", "caravanserai": "K AE R AH V AE N S ER AY", "emptiest": "EH M P T IY IH S T",
         "bukhara": "B UW K AA R AH", "kashgar": "K AE SH G AA R", "samarkand": "S AE M ER K AE N D", "merv": "M ER V",
         "byproduct": "B AY P R AA D AH K T", "telegraph": "T EH L AH G R AE F"}
for _w, _ph in EXTRA.items():
    try:
        if not d.lookup_word(_w): d.add_word(_w, _ph, True)
    except Exception:
        d.add_word(_w, _ph, True)
# unknown words: borrow a pronunciation by splitting into known parts, else drop from alignment
def lookup(w):
    try: return d.lookup_word(w)
    except Exception: return None
