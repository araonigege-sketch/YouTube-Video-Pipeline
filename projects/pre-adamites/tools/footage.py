#!/usr/bin/env python3
"""Extract graded frame sequences for every footage shot in film2/shots.js (only the seconds each shot uses).
House grade: slightly lifted and warm, softer contrast, a little less saturation, fine grain, gentle vignette.
  python3 tools/footage.py --src <dir holding footage/>
"""
import argparse, json, os, subprocess
ap = argparse.ArgumentParser(); ap.add_argument('--src', required=True); a = ap.parse_args()
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = json.load(open(f'{P}/tools/footage.json'))
S = json.loads(open(f'{P}/film2/shots.js').read().split('window.SHOTS=', 1)[1].rstrip().rstrip(';'))
GRADE = ("scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
         "eq=contrast=0.94:saturation=0.82:brightness=0.015:gamma=1.03,colorbalance=rs=0.035:gs=0.01:bs=-0.04:rm=0.02:bm=-0.02,"
         "noise=alls=5:allf=t,vignette=angle=PI/5")
import shutil
MAN = f'{P}/film2/vid/manifest.json'; os.makedirs(f'{P}/film2/vid', exist_ok=True)
man = json.load(open(MAN)) if os.path.exists(MAN) else {}
cur = {s['clip']: [s['src'], s['start'], s['speed'], s['frames']] for s in S if s['type'] == 'footage'}
for d in os.listdir(f'{P}/film2/vid'):  # a folder made for another cut of the shot list is stale
    if d != 'manifest.json' and man.get(d) != cur.get(d): shutil.rmtree(f'{P}/film2/vid/{d}')
done = 0
for s in S:
    if s['type'] != 'footage': continue
    d = f"{P}/film2/vid/{s['clip']}"
    if os.path.exists(f"{d}/{s['frames']:04d}.jpg"): continue
    os.makedirs(d, exist_ok=True)
    src = os.path.join(a.src, REG[s['src']]['file'])
    speed = s.get('speed', 1.0)
    vf = f"setpts=PTS/{speed}," if speed != 1 else ""
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(s.get('start', 0)), '-i', src, '-vf', vf + GRADE + ',fps=30', '-frames:v', str(s['frames']), '-q:v', '3', f'{d}/%04d.jpg'], check=True)
    n = len(os.listdir(d))
    if n < s['frames']: print(f"  note: {s['clip']} has {n} of {s['frames']} frames (clip shorter); last frame holds")
    done += 1
json.dump(cur, open(MAN, 'w'))
print(f'extracted {done} footage shot(s)')
