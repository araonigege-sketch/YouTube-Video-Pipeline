# Joel's Notebook motion-comic pipeline: restore guide

Episode: "The Silk Road Didn't Trade Silk. It Traded Something Else" (14:02, delivered 2 Nov 2026)

## Folder layout to recreate
pipeline/
  package.json            -> `npm install` (gsap, @fontsource/caveat, d3-geo, topojson-client, atlases)
  smoketest/              -> hyperframes.json + meta.json (copied into every build)
  tools/                  -> all pipeline scripts (this archive)
  silk/ai/                -> demo plates s1 s2 s4 s5 s6 s7 s8 s10 s12 s15 s16 .jpg, v_s1/v_s10/v_s12 .mp4 (kit page)
  silk/vo/                -> milly.mp3, milly2.mp3, milly3.mp3 (kit page)
  silk/music/             -> arid, ibn, eastern, air, resolve .mp3 (archive.org, URLs below)
  silkfull/               -> this archive's silkfull/ + ai/ (copy demo plates and videos in too)

After restoring videos, regenerate each last frame:
  for v in ai/v_*.mp4; do ffmpeg -y -sseof -0.1 -i $v -frames:v 1 -update 1 -q:v 2 ${v%.mp4}_last.jpg; done

## Rebuild the episode
cd pipeline/silkfull
./mix_audio.sh                                   # voice + sectioned music, ducked -> mix/audio.wav
mkdir -p build/assets && cp mix/audio.wav build/assets/audio.wav
python3 ../tools/silk_full.py . build --check    # prints every shot, start time, duration
python3 ../tools/silk_full.py . build
HYPERFRAMES_NO_TELEMETRY=1 HYPERFRAMES_BROWSER_PATH=/usr/bin/google-chrome HYPERFRAMES_RENDER_DETACHED=1 \
  setsid nohup npx -y hyperframes@0.9.0 render build -o build/out.mp4 --fps 30 > build/render.log 2>&1 &
# ~80 min on 2 CPUs; poll render.log for "Render complete"; then compress:
ffmpeg -i build/out.mp4 -c:v libx264 -preset veryfast -crf 21 -c:a aac -b:a 192k -movflags +faststart final.mp4

## How the style works (silk_full.py)
- SHOTS list: (anchor phrase, kind, args). Anchor = first word(s) of the narration where the shot starts.
- Kinds: plate (Ken Burns still, optional PixVerse video + last-frame continuation, particles dust/sand/embers, label strip),
  notes (notebook page: title, timed handwriting items, drawn SVG paths, strikes, pops), relay (stick-figure chain with
  tokens passed hand to hand), map (nodes + route draw, optional red "spread" mode), converge (arrows into an oasis), end card.
- Item anchors: a number = seconds after shot start; a phrase = when that word is spoken; ">phrase" = when it ends.
- Captions: white with black outline, max 5 words / 32 chars, break at punctuation.

## Voice alignment
- align.py: PocketSphinx forced alignment for a whole file (works for most recordings).
- align_chunks.py: robust fallback for long or loosely read recordings. Anchors each paragraph by rough ASR, force-aligns
  per paragraph, and falls back to ASR word matching. Used for Milly part 2.
- Parts are joined with 0.6 s gaps: part 2 offset 400.64 s, part 3 offset 678.63 s (see words.json).

## AI generation (OpenArt connector)
- Stills: Seedream 4.5, image2image, 2K, 16:9, 15 credits. Style suffix: "Western graphic novel illustration, clean confident
  black ink outlines, cel shading with hard shadow tones, <palette>. No text, no lettering, no watermark."
- Reference images: merchant portrait (OpenArt id ITS5bK5aYABuVKshrBxO) for merchant shots; caravan panorama
  (WFcHW8sxFntx3OEOcNT6) as the style reference for everything else ("In the same illustration style as image1.").
- All prompts: silkfull/images.py. Generation ids: silkfull/ids.json.
- Video: PixVerse V6 (model id pixverseV6) image2video, 720p, 5 s, no audio, 70 credits. Parallel limits: ~4 images, 2 videos.
- Watch for anachronisms (blue tiled domes before 1400, Western wagons, modern digits, glass lanterns, logos).

## Music (Kevin MacLeod, CC BY 4.0; credit in the YouTube description)
https://archive.org/download/Kevin-MacLeod_Vadodara_2014_FullAlbum/  -> "Vadodara/Kevin MacLeod - 15 - Ibn Al-Noor.mp3", "- 10 - Eastern Thought.mp3"
https://archive.org/download/Kevin-MacLeod_Ossuary_2015_FullAlbum/   -> "Ossuary/Kevin MacLeod - 06 - Ossuary 6 - Air.mp3", "- 07 - Ossuary 7 - Resolve.mp3"
"Arid Foothills" (arid.mp3) is also on archive.org (Kevin MacLeod collection).
Sections: Arid 0-201 s, Ibn Al-Noor 197-403, Eastern Thought 399-531, Ossuary 6 Air 527-626 (plague), Ossuary 7 Resolve 621-end.

## Keys
No API keys are stored here. Paste them again when asked, and rotate any key that was shared in chat.
