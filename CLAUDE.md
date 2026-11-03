# Faceless video pipeline — operating guide for Claude

Python + FFmpeg builds the video. Hosted AI tools (vidIQ, OpenArt MCP) make the
assets. Claude is the glue: it reads the pending requests, calls the MCP tools,
and registers each result with `fetch`. The pipeline never calls those APIs itself.

## Workflow for one video

1. `python -m pipeline new <slug> --style documentary --title "..."`
2. Write `projects/<slug>/script.md` (format: see `pipeline/script.py` docstring).
   Optionally draft it with `vidiq_generate_script` (1 credit/min), then edit it
   into scenes and add `[stock: ...]` / `[image: ...]` / `[card: ...]` hints.
3. `python -m pipeline plan <slug>`, which prints the counts and an estimated voice cost.
4. `python -m pipeline render <slug> --draft` to check pacing with placeholders (free).
5. Fulfil the pending requests (`python -m pipeline status <slug> --pending`, or `--json`):

| request | tool | then |
|---|---|---|
| `voice` / provider `vidiq` | `vidiq_voiceover_generate(script=text, voiceId=voice_id)`, then poll `vidiq_job_poll` | `fetch <slug> voice_cNN <audioUrl> --provider vidiq:<voice>` |
| `voice` / provider `edge` | none: `python -m pipeline local <slug>` | |
| `visual` / kind `stock` | `vidiq_generate_broll(query, orientation=landscape, minDurationSeconds=min_seconds)` | `fetch <slug> vis_… <mp4> --credit "<Photographer> (Pexels)" --source-url <page>` |
| `visual` / kind `image` | OpenArt `kling-3-omni` text2image, `aspectRatio: 16:9`, `resolution: 2k`, prompt = `prompt_full` | `fetch <slug> vis_… <image url> --provider openart` |
| `visual` / kind `card` | none: rendered locally | |
| `music` | `vidiq_generate_music(prompt, durationSeconds=…)`, then poll | `fetch <slug> music_bed <wav url>` |

6. `python -m pipeline render <slug>` → `out/<slug>.mp4` + `out/metadata.md`
   (chapters, footage credits, QA warnings).

## Rules of thumb
- **Stock clip choice:** only pick MP4 links that are 720p or better (`hd_1280_720`, `hd_1920_1080`, …).
  vidIQ often returns `640_360` files; search again with a different query instead of using one.
  Avoid clips with visible modern objects in history content (cars, phones, signage).
- When `prompt_source` is `narration`, the "prompt" is the narration itself:
  write a short, concrete visual search query from it. Don't paste the sentence in.
- Never reuse the same clip in two shots of one scene; for `variant > 0`, pick a different search result.
- Always pass `--credit` for Pexels clips (attribution is required); it ends up in metadata.md.
- vidIQ voice bills 14 credits per *started* 1000 chars per call. The planner already
  packs scenes into chunks of up to 4800 chars, so send each chunk as one call.
- Signed URLs (vidIQ voice) expire after about 12 h, so fetch them right away.
- Editing script.md and re-running `plan` keeps every asset whose text or prompt didn't
  change and re-queues only the changed ones (shown as "re-queued").

## Layout
- `styles/*.yaml`: one file per video style/niche (`extends:` another style to inherit from it).
- `projects/<slug>/project.yaml`: title, style, per-project `overrides:`.
- `projects/<slug>/build/`: plan.json, requests.json, timeline.json, audio/, visuals/, clips/ (cached).
- `projects/<slug>/out/`: final MP4 + metadata.
