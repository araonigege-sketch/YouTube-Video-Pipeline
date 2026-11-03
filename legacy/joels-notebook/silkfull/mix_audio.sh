#!/bin/bash
# Rebuild mix/audio.wav for the Silk Road episode. Run from pipeline/silkfull. Needs ../silk/vo/milly*.mp3 and ../silk/music/*.mp3
set -e; mkdir -p mix; M=../silk/music; V=../silk/vo; END=842.5
ffmpeg -v error -y -i $V/milly.mp3 -f lavfi -t 0.6 -i anullsrc=r=44100:cl=mono -i $V/milly2.mp3 -f lavfi -t 0.6 -i anullsrc=r=44100:cl=mono -i $V/milly3.mp3 \
 -filter_complex "[0]aresample=44100,aformat=channel_layouts=mono[a];[2]aresample=44100,aformat=channel_layouts=mono[b];[4]aresample=44100,aformat=channel_layouts=mono[c];[a][1][b][3][c]concat=n=5:v=0:a=1,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=44100[o]" -map "[o]" mix/voice.wav
python3 - <<PY
import subprocess
M="$M"; END=$END
segs=[("arid.mp3",0,201,0),("ibn.mp3",197,403,0),("eastern.mp3",399,531,8),("air.mp3",527,626,0),("resolve.mp3",621,END,0)]
inp=[];f=[];lab=[]
for i,(fn,a,b,o) in enumerate(segs):
    inp+=["-i",f"{M}/{fn}"]; d=b-a; ms=int(a*1000)
    f.append(f"[{i}]atrim={o}:{o+d},asetpts=PTS-STARTPTS,aresample=44100,aformat=channel_layouts=stereo,loudnorm=I=-20:TP=-2,aresample=44100,afade=t=in:d={0.5 if i==0 else 3.5},afade=t=out:st={d-4}:d=4,adelay={ms}|{ms}[m{i}]"); lab.append(f"[m{i}]")
f.append(f"{''.join(lab)}amix=inputs={len(lab)}:duration=longest:normalize=0,atrim=0:{END}[mus]")
subprocess.run(["ffmpeg","-v","error","-y",*inp,"-filter_complex",";".join(f),"-map","[mus]","mix/music.wav"],check=True)
PY
ffmpeg -v error -y -i mix/voice.wav -i mix/music.wav -filter_complex "[0]aformat=channel_layouts=stereo,apad=whole_dur=$END,asplit=2[v1][v2];[1]volume=0.42[mu];[mu][v2]sidechaincompress=threshold=0.02:ratio=6:attack=20:release=400[duck];[v1][duck]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[o]" -map "[o]" -ar 44100 mix/audio.wav
echo "mix/audio.wav ready"
