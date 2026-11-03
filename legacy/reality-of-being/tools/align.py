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
    if re.fullmatch(r"(19|20)\d\d", core): return year(int(core))
    if re.fullmatch(r"\d[\d,]*", core): return n2w(int(core.replace(",", "")))
    if re.fullmatch(r"[A-Z]{2,4}", core): return list(core.lower())
    return [w for w in re.split(r"[-\u2013]", core.lower()) if w]

audio, textf, outf = sys.argv[1], sys.argv[2], sys.argv[3]
offset = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
toks = open(textf, encoding="utf-8").read().split()
sp, owner = [], []
for i, t in enumerate(toks):
    for w in spoken(t):
        sp.append(w); owner.append(i)

d = Decoder(samprate=16000)
# unknown words: borrow a pronunciation by splitting into known parts, else drop from alignment
def lookup(w):
    try: return d.lookup_word(w)
    except Exception: return None
fixed_sp, fixed_owner = [], []
for w, o in zip(sp, owner):
    if lookup(w):
        fixed_sp.append(w); fixed_owner.append(o); continue
    parts = None
    for k in range(2, len(w) - 1):
        a, b = w[:k], w[k:]
        if lookup(a) and lookup(b): parts = [a, b]; break
    if w.endswith("'s") and lookup(w[:-2]): parts = [w[:-2]]
    if parts:
        d.add_word(w, " ".join(lookup(p) for p in parts), True); fixed_sp.append(w); fixed_owner.append(o)
    else:
        print("OOV dropped:", w, file=sys.stderr)
sp, owner = fixed_sp, fixed_owner

tmp = tempfile.mktemp(suffix=".wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", audio, "-ar", "16000", "-ac", "1", tmp], check=True)
with wave.open(tmp) as w: data = w.readframes(w.getnframes())
os.remove(tmp)
d.set_align_text(" ".join(sp))
d.start_utt(); d.process_raw(data, full_utt=True); d.end_utt()
d.set_alignment(); d.start_utt(); d.process_raw(data, full_utt=True); d.end_utt()
segs = [s for s in d.get_alignment() if s.name not in ("<sil>", "<s>", "</s>", "[NOISE]")]
if len(segs) != len(sp):
    raise SystemExit(f"alignment mismatch: {len(segs)} segments vs {len(sp)} words")
times = {}
for o, s in zip(owner, segs):
    a, b = s.start / 100 + offset, (s.start + s.duration) / 100 + offset
    times[o] = (min(times[o][0], a), max(times[o][1], b)) if o in times else (a, b)
out = []
for i, t in enumerate(toks):
    if i in times: out.append({"w": t, "s": round(times[i][0], 3), "e": round(times[i][1], 3)})
json.dump(out, open(outf, "w"), ensure_ascii=False)
print(f"aligned {len(out)}/{len(toks)} tokens, last word ends {out[-1]['e']:.2f}s")
