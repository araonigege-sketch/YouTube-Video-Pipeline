"""Generate a voiceover per paragraph with ElevenLabs (with timestamps), stitch, and emit a word timeline.
Usage: python3 tts.py <script.txt> <voice_id> <outdir> [gap_seconds]
Writes outdir/voice.wav, outdir/words.json ([{w,s,e,para}]), outdir/paras.json
"""
import sys, json, base64, os, subprocess, wave, pathlib, urllib.request

script, voice, outdir = sys.argv[1], sys.argv[2], pathlib.Path(sys.argv[3])
gap = float(sys.argv[4]) if len(sys.argv) > 4 else 0.45
key = open(os.path.expanduser("~/.secrets/elevenlabs_key")).read().strip()
outdir.mkdir(parents=True, exist_ok=True)
paras = [p.strip() for p in open(script, encoding="utf-8").read().split("\n\n") if p.strip()]
SR = 44100

def tts(i):
    cache = outdir / f"p{i:02d}.json"
    if cache.exists():
        return json.load(open(cache))
    body = {
        "text": paras[i],
        "model_id": "eleven_multilingual_v2",
        "previous_text": paras[i - 1] if i > 0 else None,
        "next_text": paras[i + 1] if i + 1 < len(paras) else None,
    }
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_128",
        data=json.dumps(body).encode(), headers={"xi-api-key": key, "Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req, timeout=180))
    json.dump(d, open(cache, "w"))
    return d

def words_from(al):
    ch, st, en = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
    out, cur, s, e = [], "", 0, 0
    for c, t0, t1 in zip(ch, st, en):
        if c.isspace():
            if cur: out.append((cur, s, e)); cur = ""
        else:
            if not cur: s = t0
            cur += c; e = t1
    if cur: out.append((cur, s, e))
    return out

pcm, words, meta, t = bytearray(), [], [], 0.0
for i in range(len(paras)):
    d = tts(i)
    mp3 = outdir / f"p{i:02d}.mp3"; mp3.write_bytes(base64.b64decode(d["audio_base64"]))
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp3), "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    dur = len(raw) / 2 / SR
    for w, s, e in words_from(d["alignment"]):
        words.append({"w": w, "s": round(t + s, 3), "e": round(t + e, 3), "para": i})
    meta.append({"i": i, "start": round(t, 3), "dur": round(dur, 3), "text": paras[i]})
    pcm += raw
    t += dur
    if i + 1 < len(paras):
        pcm += b"\x00\x00" * int(gap * SR); t += gap
    print(f"para {i}: {dur:.2f}s, {len(paras[i].split())} words", flush=True)

with wave.open(str(outdir / "voice.wav"), "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(bytes(pcm))
json.dump(words, open(outdir / "words.json", "w"), indent=0, ensure_ascii=False)
json.dump(meta, open(outdir / "paras.json", "w"), indent=1, ensure_ascii=False)
print(f"TOTAL {t:.2f}s, {len(words)} words")
