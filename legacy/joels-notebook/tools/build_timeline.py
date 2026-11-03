"""Map script -> timed shots, captions and overlays.
Usage: python3 build_timeline.py <projdir>
Needs in projdir: script.txt, words.json ([{w,s,e}] from TTS or whisper), beats.json, pools.json
Writes projdir/timeline.json
"""
import sys, json, re, math, difflib, pathlib

P = pathlib.Path(sys.argv[1])
MIN_SHOT, MAX_SHOT, TARGET = 2.6, 5.2, 4.0

def norm(t):
    t = t.lower().replace("’", "'").replace("‘", "'")
    return re.sub(r"[^a-z0-9%$']", "", t)

script = open(P / "script.txt", encoding="utf-8").read()
stoks = script.split()                      # display tokens (keep punctuation)
paras_end = set()                           # token index that ends a paragraph
idx = 0
for para in [p for p in script.split("\n\n") if p.strip()]:
    idx += len(para.split()); paras_end.add(idx - 1)
words = json.load(open(P / "words.json"))
sn, wn = [norm(t) for t in stoks], [norm(w["w"]) for w in words]

# align script tokens to spoken words
times = [None] * len(stoks)
for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, sn, wn, autojunk=False).get_opcodes():
    if tag == "equal":
        for k in range(i2 - i1):
            times[i1 + k] = (words[j1 + k]["s"], words[j1 + k]["e"])
    elif tag == "replace" and j2 > j1:      # e.g. "$144,000" vs "144,000" / "thirty-one"
        s, e = words[j1]["s"], words[j2 - 1]["e"]
        n = i2 - i1
        for k in range(n):
            times[i1 + k] = (s + (e - s) * k / n, s + (e - s) * (k + 1) / n)
# interpolate gaps
known = [i for i, t in enumerate(times) if t]
for i, t in enumerate(times):
    if t: continue
    prev = max([k for k in known if k < i], default=None); nxt = min([k for k in known if k > i], default=None)
    a = times[prev][1] if prev is not None else 0.0
    b = times[nxt][0] if nxt is not None else a + 0.3
    times[i] = (a, max(a, b))
matched = sum(1 for o in difflib.SequenceMatcher(None, sn, wn, autojunk=False).get_matching_blocks() for _ in range(o.size))
end_time = max(w["e"] for w in words)

# beats -> start token index
beats, pools = json.load(open(P / "beats.json")), json.load(open(P / "pools.json"))
ptr, starts = 0, []
for b in beats:
    a = [norm(t) for t in b["at"].split()]
    for i in range(ptr, len(sn)):
        if all(i + k < len(sn) and sn[i + k].startswith(a[k]) for k in range(len(a))):
            starts.append(i); ptr = i + 1; break
    else:
        raise SystemExit(f"anchor not found: {b['at']}")
# shots
shots, overlays, use_count = [], [], {}
for bi, b in enumerate(beats):
    t0 = 0.0 if bi == 0 else times[starts[bi]][0] - 0.08
    t1 = (times[starts[bi + 1]][0] - 0.08) if bi + 1 < len(beats) else end_time + 1.2
    d = t1 - t0
    n = max(1, math.ceil(d / MAX_SHOT)) if d > MAX_SHOT else 1
    pool = pools[str(bi)]
    for k in range(n):
        clip = pool[k % len(pool)]
        use = use_count.get(clip, 0); use_count[clip] = use + 1
        shots.append({"beat": bi, "clip": clip, "start": round(t0 + d * k / n, 3),
                      "dur": round(d / n, 3), "src_offset": 1.0 + 6.0 * use})
    if "overlay" in b:
        overlays.append({**b["overlay"], "start": round(t0 + 0.15, 3), "dur": round(d - 0.25, 3)})
# merge too-short shots into the previous one (keeps overlays intact)
merged = []
for s in shots:
    if merged and s["dur"] < MIN_SHOT * 0.6:
        merged[-1]["dur"] = round(merged[-1]["dur"] + s["dur"], 3)
    else:
        merged.append(s)
shots = merged

# captions: chunks of <= 5 words / 30 chars, break after punctuation
caps, cur = [], []
def flush():
    if cur:
        caps.append({"text": " ".join(stoks[i] for i in cur), "start": round(times[cur[0]][0], 3),
                     "end": round(times[cur[-1]][1], 3)})
        cur.clear()
for i, t in enumerate(stoks):
    cur.append(i)
    txt = " ".join(stoks[k] for k in cur)
    if re.search(r"[.?!,:;]$", t) or len(cur) >= 5 or len(txt) >= 30 or i in paras_end:
        flush()
flush()
for a, b in zip(caps, caps[1:]):            # hold each caption until the next one (max 0.6 s gap)
    a["end"] = round(min(b["start"], a["end"] + 0.6), 3)
caps[-1]["end"] = round(caps[-1]["end"] + 0.6, 3)

total = round(end_time + 1.2, 3)
json.dump({"duration": total, "shots": shots, "captions": caps, "overlays": overlays,
           "align": {"script_tokens": len(sn), "matched": matched}},
          open(P / "timeline.json", "w"), indent=1, ensure_ascii=False)
ds = [s["dur"] for s in shots]
print(f"duration {total}s | shots {len(shots)} (min {min(ds):.1f}, max {max(ds):.1f}, avg {sum(ds)/len(ds):.1f}) | "
      f"captions {len(caps)} | overlays {len(overlays)} | aligned {matched}/{len(sn)} tokens")
