"""Robust forced alignment for long recordings: anchor each paragraph with rough ASR, then force-align paragraph by paragraph.
Usage: python3 align_chunks.py <audio16k.wav> <text.txt> <out_words.json> [offset]
"""
import sys, json, wave, re, difflib
sys.path.insert(0, __import__("os").path.dirname(__file__))
from align_lib import spoken, d as D
from pocketsphinx import Decoder

audio, textf, outf = sys.argv[1], sys.argv[2], sys.argv[3]
offset = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
with wave.open(audio) as w: data = w.readframes(w.getnframes())
SR = 16000; dur = len(data) / 2 / SR
paras = [p.split() for p in open(textf, encoding="utf-8").read().split("\n\n") if p.strip()]

# 1) rough ASR with word times
asr = Decoder(samprate=SR); hyp = []
step = SR * 2 * 20
for k in range(0, len(data), step):
    asr.start_utt(); asr.process_raw(data[k:k + step], full_utt=True); asr.end_utt()
    for seg in asr.seg():
        wd = re.sub(r"\(\d+\)$", "", seg.word)
        if wd.startswith("<") or wd.startswith("["): continue
        hyp.append((wd, k / 2 / SR + seg.start_frame / 100))
hw = [h[0] for h in hyp]

# 2) anchor each paragraph start: best fuzzy match of its first 8 spoken words after previous anchor
anchors = [0.0]; pos = 0
for p in paras[1:]:
    target = [w for t in p[:10] for w in spoken(t)][:8]
    best, bi = 0, None
    for i in range(pos, len(hw) - 2):
        r = difflib.SequenceMatcher(None, target, hw[i:i + len(target) + 2]).ratio()
        if r > best: best, bi = r, i
    anchors.append(hyp[bi][1] - 0.25 if bi is not None and best > 0.45 else None)
    if bi is not None: pos = bi + 1
    print(f"anchor {len(anchors) - 1}: {anchors[-1]} (match {best:.2f}) :: {' '.join(p[:6])}")
# fill missing anchors proportionally by word count
n = [len(p) for p in paras]
for i, a in enumerate(anchors):
    if a is None:
        prev = max(j for j in range(i) if anchors[j] is not None); nxt = next((j for j in range(i + 1, len(anchors)) if anchors[j] is not None), None)
        t1 = anchors[nxt] if nxt else dur
        anchors[i] = anchors[prev] + (t1 - anchors[prev]) * sum(n[prev:i]) / sum(n[prev:nxt or len(n)])

# 3) force-align each paragraph inside its window
out = []
for i, p in enumerate(paras):
    a = max(0.0, anchors[i]); b = anchors[i + 1] + 0.35 if i + 1 < len(paras) else dur
    seg = data[int(a * SR) * 2:int(b * SR) * 2]
    sp, owner = [], []
    for k, t in enumerate(p):
        for w in spoken(t):
            try: ok = D.lookup_word(w)
            except Exception: ok = None
            if ok: sp.append(w); owner.append(k)
    times = {}
    try:
        D.set_align_text(" ".join(sp)); D.start_utt(); D.process_raw(seg, full_utt=True); D.end_utt()
        D.set_alignment(); D.start_utt(); D.process_raw(seg, full_utt=True); D.end_utt()
        segs = [s for s in D.get_alignment() if s.name not in ("<sil>", "<s>", "</s>", "[NOISE]")]
        assert len(segs) == len(sp)
        for o, s in zip(owner, segs):
            t0, t1 = a + s.start / 100, a + (s.start + s.duration) / 100
            times[o] = (min(times[o][0], t0), max(times[o][1], t1)) if o in times else (t0, t1)
        status = "ok"
    except Exception as e:
        status = "ASR-MATCH"
        # use rough-ASR word times where script words match, interpolate the rest
        idx = [j for j, h in enumerate(hyp) if a - 0.5 <= h[1] <= b + 0.3]
        hw_p = [hw[j] for j in idx]
        sm = difflib.SequenceMatcher(None, sp, hw_p, autojunk=False)
        st = [None] * len(sp)
        for blk in sm.get_matching_blocks():
            for q in range(blk.size): st[blk.a + q] = hyp[idx[blk.b + q]][1]
        known = [(q, t) for q, t in enumerate(st) if t is not None]
        pts = [(-1, a)] + known + [(len(sp), b)]
        for (q0, t0), (q1, t1) in zip(pts, pts[1:]):
            for q in range(q0 + 1, q1): st[q] = t0 + (t1 - t0) * (q - q0) / (q1 - q0)
        for q, o in enumerate(owner):
            t0 = st[q]; t1 = st[q + 1] if q + 1 < len(st) else b
            t1 = min(t1, t0 + 1.2)
            times[o] = (min(times[o][0], t0), max(times[o][1], t1)) if o in times else (t0, t1)
        for k, t in enumerate(p):  # tokens with no spoken lookup: borrow neighbour
            if k not in times:
                prv = max([x for x in times if x < k], default=None)
                times[k] = (times[prv][1], times[prv][1] + 0.2) if prv is not None else (a, a + 0.2)
        status += f" {len(known)}/{len(sp)} matched"
    for k, t in enumerate(p):
        if k in times: out.append({"w": t, "s": round(times[k][0] + offset, 3), "e": round(times[k][1] + offset, 3)})
    print(f"para {i}: {a:.2f}-{b:.2f} {status}")
json.dump(out, open(outf, "w"), ensure_ascii=False)
print(f"aligned {len(out)} tokens, ends {out[-1]['e']:.2f}")
