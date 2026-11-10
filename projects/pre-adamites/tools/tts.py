#!/usr/bin/env python3
"""Narration with ElevenLabs, one paragraph per request, joined with controlled pauses.

Long single requests drift in pace and sometimes stumble; per-paragraph requests with the
neighbouring text as context keep the intonation continuous, and a bad paragraph can be
regenerated on its own (--only N).

  python3 tools/tts.py --voice <voice_id> --name <label> [--text vo/coldopen.txt] [--gap 0.6] [--only 3]
                       [--speed/--stability/--similarity/--style only to override the voice's saved settings]

Writes vo/<label>/pNN.mp3 + pNN.json (alignment), then vo/coldopen_<label>.mp3 and
vo/words_<label>.json (word timings on the joined track). Needs ffmpeg; the key comes from the
environment's network secret (the proxy injects it).
"""
import argparse, base64, json, os, subprocess, urllib.request

ap = argparse.ArgumentParser()
ap.add_argument('--voice', required=True); ap.add_argument('--name', required=True)
ap.add_argument('--text', default='vo/coldopen.txt'); ap.add_argument('--model', default='eleven_multilingual_v2')
# Default: the voice's own saved settings (owner, 2026-11-10: tuned stability/speed made voices sound worse).
ap.add_argument('--speed', type=float); ap.add_argument('--stability', type=float)
ap.add_argument('--similarity', type=float); ap.add_argument('--style', type=float)
ap.add_argument('--gap', type=float, default=0.6, help='silence between paragraphs, seconds')
ap.add_argument('--only', type=int, help='regenerate just this paragraph (1-based), then rejoin')
a = ap.parse_args()

paras = [p.strip() for p in open(a.text).read().split('\n\n') if p.strip()]
d = f'vo/{a.name}'; os.makedirs(d, exist_ok=True)

def tts(i):
    body = {"text": paras[i], "model_id": a.model}
    vs = {k: v for k, v in [("stability", a.stability), ("similarity_boost", a.similarity), ("style", a.style), ("speed", a.speed)] if v is not None}
    if vs: body["voice_settings"] = vs
    if i > 0: body["previous_text"] = paras[i - 1]
    if i + 1 < len(paras): body["next_text"] = paras[i + 1]
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{a.voice}/with-timestamps?output_format=mp3_44100_128",
        data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "xi-api-key": os.environ.get('ELEVENLABS_API_KEY', 'proxy')})
    r = json.load(urllib.request.urlopen(req, timeout=300))
    open(f'{d}/p{i + 1:02d}.mp3', 'wb').write(base64.b64decode(r['audio_base64']))
    json.dump(r['alignment'], open(f'{d}/p{i + 1:02d}.json', 'w'))

for i in range(len(paras)):
    if a.only is None or a.only == i + 1 or not os.path.exists(f'{d}/p{i + 1:02d}.mp3'):
        tts(i)

def dur(f): return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f]))

# decode each paragraph to WAV with the gap padded on, so timings and audio agree exactly
words, t, wavs, flags = [], 0.0, [], []
for i in range(len(paras)):
    f = f'{d}/p{i + 1:02d}.mp3'; w = f'{d}/p{i + 1:02d}.wav'; al = json.load(open(f'{d}/p{i + 1:02d}.json'))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f, '-ar', '44100', '-ac', '1', w], check=True)
    body = dur(w)
    cur, s, pe = '', None, None
    for c, t0, t1 in zip(al['characters'], al['character_start_times_seconds'], al['character_end_times_seconds']):
        if c.isspace():
            if cur: words.append({"w": cur, "s": round(t + s, 3), "e": round(t + pe, 3), "p": i + 1}); cur = ''
        else:
            if not cur: s = t0
            cur += c; pe = t1
    if cur: words.append({"w": cur, "s": round(t + s, 3), "e": round(t + pe, 3), "p": i + 1})
    last = i + 1 == len(paras)
    if not last:
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', w, '-af', f'apad=pad_dur={a.gap}', w + '.pad.wav'], check=True); os.replace(w + '.pad.wav', w)
    wavs.append(w); t += body + (0 if last else a.gap)
# crude stumble check: a word held unusually long mid-sentence, or a long silence inside a paragraph
for w0, w1 in zip(words, words[1:]):
    if w0['e'] - w0['s'] > 1.1 and w0['w'][-1] not in '.?!,:;"\u201d': flags.append(f"p{w0['p']} long word '{w0['w']}' at {w0['s']:.1f}s")
    if w0['p'] == w1['p'] and w1['s'] - w0['e'] > 1.3: flags.append(f"p{w0['p']} long pause after '{w0['w']}' at {w0['e']:.1f}s")
lst = f'{d}/join.txt'
with open(lst, 'w') as fh:
    for w in wavs: fh.write(f"file '{os.path.abspath(w)}'\n")
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-b:a', '160k', f'vo/coldopen_{a.name}.mp3'], check=True)
json.dump(words, open(f'vo/words_{a.name}.json', 'w'), indent=0)
total = dur(f'vo/coldopen_{a.name}.mp3')
print(f"{a.name}: {total:.1f} s, {len(words) / total * 60:.0f} words/min, {len(paras)} paragraphs")
for x in flags: print('  check:', x)
