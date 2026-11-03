"""Synthesize simple cartoon SFX with ffmpeg and mix them (plus a voice/music track) into one wav.
Usage: python3 sfx_mix.py <base_audio> <sfx.json> <out.wav>   (sfx.json: {"end": seconds, "sfx": [[t, kind], ...]})
"""
import sys, json, subprocess, pathlib, tempfile
base, sfxf, out = sys.argv[1], sys.argv[2], sys.argv[3]
cfg = json.load(open(sfxf)); END = cfg["end"]
D = pathlib.Path(tempfile.mkdtemp())
SR = 44100
RECIPES = {  # kind: (ffmpeg lavfi source + filters, volume)
    "pop":     ("aevalsrc='0.8*sin(2*PI*(380+900*exp(-28*t))*t)*exp(-22*t)':d=0.16", 0.55),
    "blip":    ("aevalsrc='0.5*sin(2*PI*1320*t)*exp(-30*t)':d=0.12", 0.35),
    "ding":    ("aevalsrc='0.6*sin(2*PI*1568*t)*exp(-6*t)+0.3*sin(2*PI*2093*t)*exp(-7*t)':d=0.7", 0.45),
    "tick":    ("aevalsrc='0.7*sin(2*PI*2400*t)*exp(-80*t)':d=0.06", 0.5),
    "stamp":   ("aevalsrc='0.9*sin(2*PI*(70+60*exp(-20*t))*t)*exp(-14*t)':d=0.35", 0.9),
    "cash":    ("aevalsrc='0.5*sin(2*PI*2637*t)*exp(-9*t)+0.4*sin(2*PI*3136*t)*exp(-8*t)':d=0.5", 0.35),
    "whoosh":  ("anoisesrc=color=pink:d=0.38:a=0.6,bandpass=f=1400:w=1800,afade=t=in:d=0.16,afade=t=out:st=0.18:d=0.2", 0.22),
    "thunder": ("anoisesrc=color=brown:d=1.6:a=0.9,lowpass=f=260,afade=t=in:d=0.05,afade=t=out:st=0.3:d=1.3", 0.8),
}
for k, (src, _) in RECIPES.items():
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", src, "-ar", str(SR), "-ac", "1", str(D / f"{k}.wav")], check=True)
events = [(t, k) for t, k in cfg["sfx"] if k in RECIPES and 0 <= t < END]
inputs = ["-i", base] + sum((["-i", str(D / f"{k}.wav")] for _, k in events), [])
f = [f"[0:a]atrim=0:{END},afade=t=out:st={END - 1.0}:d=1.0[b]"]
labels = ["[b]"]
for i, (t, k) in enumerate(events, start=1):
    ms = int(t * 1000)
    f.append(f"[{i}:a]volume={RECIPES[k][1]},adelay={ms}|{ms}[e{i}]"); labels.append(f"[e{i}]")
f.append(f"{''.join(labels)}amix=inputs={len(labels)}:duration=first:normalize=0,alimiter=limit=0.95[o]")
subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(f), "-map", "[o]", "-ar", str(SR), out], check=True)
print("mixed", len(events), "sfx ->", out)
