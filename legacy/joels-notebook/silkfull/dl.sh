#!/bin/bash
# usage: dl.sh id url [id url ...]  -> ai/<id>.jpg resized to 2560 wide
cd /home/claude/pipeline/silkfull
while [ $# -gt 1 ]; do
  curl -sSL -o ai/$1_raw.jpg "$2" && ffmpeg -v error -y -i ai/$1_raw.jpg -vf scale=2560:-2 -q:v 3 ai/$1.jpg && rm ai/$1_raw.jpg && echo "ok $1"
  shift 2
done
