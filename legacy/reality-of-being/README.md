# Video pipeline + ATC pilot: restore guide

Project: "Why You'd Never Survive a Week as an Air Traffic Controller" (Reality of Being channel), pilot v2.
Built 2026-11-02 in a Claude cloud session. Engine: HyperFrames 0.9.0 (HTML -> MP4) + FFmpeg.

## Layout
pipeline/tools/          the pipeline scripts (see "Tools")
pipeline/package.json    npm deps (gsap, d3-geo, topojson-client, us-atlas, world-atlas)
pipeline/smoketest/      hyperframes.json + meta.json copied into each build
pipeline/atc/            the ATC project: script.txt, beats.json (beat anchors, search queries, overlays),
                         pools.json (clip chosen per beat), words.json (word timings), timeline.json,
                         map.json, vo/ (alignment per recording), footage|extra/manifest.json (Pixabay sources)
Media (separate files on the backup page): ai/*.jpg|mp4 (OpenArt shots), newclips/*.mp4 (archival),
vo/voice.mp3 (narration only), vo/mix.mp3 (narration + ducked music), music/Anxiety.mp3

## Restore
1. Unpack: base64 -d kit.tar.gz.b64.txt > kit.tar.gz && tar xzf kit.tar.gz   (creates pipeline/)
2. cd pipeline && npm i && pip install pocketsphinx --break-system-packages
3. Put media back: ai/ -> pipeline/atc/ai/, newclips/ -> pipeline/atc/newclips/, voice.mp3 + mix.mp3 -> pipeline/atc/vo/,
   Anxiety.mp3 -> pipeline/atc/music/. The AI shots are .jpg in the backup: convert to .png names expected by pools
   (python3 -c "from PIL import Image;import glob;[Image.open(f).save(f[:-4]+'.png') for f in glob.glob('atc/ai/*.jpg')]")
4. python3 tools/refetch_pixabay.py atc        (re-downloads the Pixabay clips used)
5. Rebuild: mkdir -p atc/build/assets && ffmpeg -i atc/vo/mix.mp3 atc/build/assets/voice.wav
   python3 tools/build_timeline.py atc && python3 tools/make_bg.py atc && python3 tools/compose.py atc
6. Render: cd atc/build && HYPERFRAMES_NO_TELEMETRY=1 HYPERFRAMES_BROWSER_PATH=$(which google-chrome || which chromium) \
   npx -y hyperframes@0.9.0 render --quality delivery -o out.mp4

## Tools
- tts.py: ElevenLabs TTS per paragraph with word timestamps (instant clones blocked on current plan)
- align.py: PocketSphinx forced alignment of a recording to known script text (offline; numbers/acronyms expanded)
- asr_rough.py: rough transcript in 20 s chunks, to see what a recording covers
- fetch_footage.py: Pixabay video search per beat (video_type=film, throttled CDN downloads, 429 backoff)
- refetch_pixabay.py: restore only the Pixabay clips a project uses
- build_timeline.py: script tokens -> word times; beats -> shots (3-5 s, split long beats), captions (<=5 words), overlays
- make_bg.py: frame-exact cut of every shot into one silent 1080p30 bg.mp4 (clip ids: bNN_k Pixabay, xbNN_k extra,
  a:name archival, i:name AI still, v:name AI video; cached by source+mtime)
- compose.py: HyperFrames index.html: bg video with push-ins, yellow captions, stat cards, US map pops, people graphic, fade
- mapsvg.mjs: US map paths + city pins (add places in PLACES)

## Gotchas learned
- Local GSAP only (cdn.jsdelivr.net blocked in sandbox); set HYPERFRAMES_BROWSER_PATH; telemetry off.
- Pixabay CDN rate-limits parallel downloads; Pixabay Music blocks automation; Library of Congress needs browser UA.
- Archive.org: only public-domain collections; check licenseurl; older films cut every 2-3 s, so trim to single shots
  (ffmpeg select=gt(scene,0.3) to find cuts); crop out corner credits.
- AI video (PixVerse V6 image2video 720p, 70 credits) warps people after ~3 s: use first 3-4 s only.
- Render ~7 min per minute of video on 2 CPUs; run detached and poll render.log.

## Credits for the ATC video description
Music: "Anxiety" by Kevin MacLeod (incompetech.com), CC BY 3.0.
Archival: "America's Air Traffic Controllers" by Paul Williams, Internet Archive (public domain).
Tick YouTube's altered/synthetic content box (realistic AI people).
