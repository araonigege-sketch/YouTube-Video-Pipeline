#!/usr/bin/env python3
"""Pacing pass for vidIQ voiceover blocks, matching the Finance pipeline's approved settings.

Per block: silences longer than 0.42 s are shortened to 0.42 s, start/end trimmed to 0.08 s,
tempo x1.05 with pitch kept, mono 48 kHz. Blocks are joined with a 0.55 s gap after a 0.5 s lead-in.

  python3 tools/vo_pace.py --out vo/narration.wav block01.mp3 block02.mp3 ...
Prints each block's start time on the joined track (for alignment and shot timing).
"""
import argparse, subprocess, tempfile, os

ap = argparse.ArgumentParser()
ap.add_argument('blocks', nargs='+'); ap.add_argument('--out', required=True)
ap.add_argument('--max-pause', type=float, default=0.42); ap.add_argument('--edge', type=float, default=0.08)
ap.add_argument('--tempo', type=float, default=1.05); ap.add_argument('--gap', type=float, default=0.55)
ap.add_argument('--lead', type=float, default=0.5); ap.add_argument('--threshold', default='-42dB')
ap.add_argument('--keep', help='folder to keep each paced block (bNNN.wav) and starts.json')
a = ap.parse_args()

def dur(f): return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f]))
tmp = tempfile.mkdtemp(); parts = []; t = a.lead; starts = []
lead = os.path.join(tmp, 'lead.wav'); subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=mono', '-t', str(a.lead), lead], check=True)
gap = os.path.join(tmp, 'gap.wav'); subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=mono', '-t', str(a.gap), gap], check=True)
parts.append(lead)
for i, b in enumerate(a.blocks):
    o = os.path.join(tmp, f'b{i:03d}.wav')
    af = (f"silenceremove=start_periods=1:start_silence={a.edge}:start_threshold={a.threshold}:"
          f"stop_periods=-1:stop_duration={a.max_pause}:stop_silence={a.max_pause}:stop_threshold={a.threshold},"
          f"areverse,silenceremove=start_periods=1:start_silence={a.edge}:start_threshold={a.threshold},areverse,"
          f"atempo={a.tempo}")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', b, '-af', af, '-ac', '1', '-ar', '48000', o], check=True)
    starts.append(round(t, 3)); t += dur(o)
    parts.append(o)
    if i + 1 < len(a.blocks): parts.append(gap); t += a.gap
lst = os.path.join(tmp, 'list.txt')
open(lst, 'w').write(''.join(f"file '{p}'\n" for p in parts))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c:a', 'pcm_s16le', a.out], check=True)
if a.keep:
    import json, shutil
    os.makedirs(a.keep, exist_ok=True)
    for i in range(len(a.blocks)): shutil.copy(os.path.join(tmp, f'b{i:03d}.wav'), os.path.join(a.keep, f'b{i + 1:02d}.wav'))
    json.dump(starts, open(os.path.join(a.keep, 'starts.json'), 'w'))
print('block starts:', starts); print(f'total {dur(a.out):.2f} s -> {a.out}')
