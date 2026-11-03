# Video pipeline — operating guide for Claude

Several YouTube channels, each with its own look. One shared core, one folder per channel.
Hosted tools (vidIQ, OpenArt, ElevenLabs) make assets; Python + FFmpeg + HyperFrames
assemble them. Claude is the glue: it reads what a project needs, calls the tools, and
registers each result. **Read `docs/owner-brief.md` first**: it holds the owner's standing
instructions, channels and decisions from earlier sessions. The owner's standards apply to every channel:

- **Every shot must match its line.** Each shot is anchored to the words it illustrates.
- **Keep the screen changing.** Run `compose --check` and fix the retention warnings before rendering.
- **Best available source, always.** Highest-resolution footage and images; no anachronisms in history content.
- **Music per video, licence-checked:** follow `docs/music.md`. Record every track in `music.json`.
- **New look = model it on the owner's sample video.** Break the sample down (cut rhythm, shot types,
  captions, colour, music) into a channel folder, render a short test, get approval before a full episode.

## Two kinds of project

### A. Channel episodes (HyperFrames) — e.g. Joel's Notebook
`projects/<slug>/episode.yaml` names the channel; the channel's composer builds the video.

```
projects/<slug>/
  episode.yaml     title, channel, voice parts (+ script text per part), lexicon, strips, end anchor
  shots.yaml       the shot list as data: one entry per shot, `at:` = narration words where it starts
  custom.py        optional one-off pages for this episode (functions `name(c, t0, t1)`)
  words.json       word timings (from `align`)
  music.json       sectioned music with licence + credit per track
  ai/ vo/ music/   media
```
1. Voice: real narrator recordings into `vo/` with each part's script text, or generate TTS.
2. `python -m pipeline align <slug>` → words.json (PocketSphinx; paragraph-anchored fallback for loose reads).
3. Write `shots.yaml` (shot types and fields: `channels/<channel>/compose.py` docstring).
4. `python -m pipeline compose <slug> --check` → shot timings + retention warnings. Fix them.
5. Generate images and animations (prompt style and reference ids are in `channels/<channel>/channel.yaml`).
6. `python -m pipeline episode <slug> --until 90` → a test section; without `--until` → the full episode.
   Rendering runs at about 6 minutes per minute of video on 2 CPUs. Run it in the background.

### B. Stock-footage documentaries (FFmpeg) — `styles/*.yaml`, `projects/<slug>/project.yaml`
1. `python -m pipeline new <slug> --style documentary --title "..."`, write `script.md`
   (one paragraph = one scene; `[stock: …]` / `[image: …]` / `[card: …]` hints).
2. `plan` → `render --draft` (free placeholders) → fulfil requests (`status --pending`) → `render`.

| request | tool | then |
|---|---|---|
| `voice` / `vidiq` | `vidiq_voiceover_generate(script, voiceId)` → poll `vidiq_job_poll` | `fetch <slug> voice_cNN <audioUrl>` |
| `visual` / `stock` | `vidiq_generate_broll(query, orientation=landscape)` | `fetch <slug> vis_… <mp4> --credit "<name> (Pexels)" --source-url <page>` |
| `visual` / `image` | OpenArt text2image 16:9 2k, prompt = `prompt_full` | `fetch <slug> vis_… <url> --provider openart` |
| `music` | `vidiq_generate_music` → poll | `fetch <slug> music_bed <wav url>` |

## Sources and gotchas
- Stock: only 720p+ files (vidIQ often returns 640×360; search again instead).
- Wikimedia Commons rate-limits this sandbox's shared IP: send a descriptive User-Agent, honour
  `retry-after`, and don't run downloads in parallel. Licence is in `extmetadata` (LicenseShortName/LicenseUrl).
- Archive.org: only items whose `licenseurl` is public domain / CC0 / CC BY. Old films cut every
  2–3 s: trim to single shots and crop corner credits.
- PixVerse image2video warps people after about 3–4 s; the plate type holds the last frame after that.
- jsdelivr is blocked: GSAP and fonts come from `node_modules` (`npm install` in the repo root).
- API keys come from environment secrets (`ELEVENLABS_API_KEY`, `PIXABAY_API_KEY`); never ask for them in chat.

## Layout
- `pipeline/`: core: words.py (phrase→time), hf.py (HyperFrames builder + render), align/, mix.py,
  plus the stock-documentary engine (plan, timeline, render, captions).
- `channels/<name>/`: channel.yaml (look, rules, prompt style) + compose.py (page types).
- `styles/`: stock-documentary styles.
- `docs/`: policies (music).
- `legacy/`: the original Joel's Notebook and Reality of Being pipelines, kept for reference.
