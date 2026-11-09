# Owner brief — read before any new work

Standing instructions from the channel owner (Olumide Akinlaja, GitHub `araonigege-sketch`).
Update this file whenever the owner gives new standing instructions.

## Channels
| Channel | Style | Voice | Status |
|---|---|---|---|
| Joel's Notebook | Illustrated motion comic (history): graphic-novel plates + notebook pages, maps, relay graphics. `channels/joels_notebook/` | Milly (real narrator, recordings supplied by the owner) | Ported; Silk Road episode rebuilt as the reference (`projects/silk-road`). Live episode: https://youtu.be/-Ad9sfLDGGA |
| Reality of Being | Footage + stat cards + US maps (ATC pilot, 3:20) | ElevenLabs TTS | Legacy pipeline in `legacy/reality-of-being`; not ported yet |
| Talking-head re-edits | Owner's already-edited talking-head videos (several niches, **different hosts**). Keep the voiceover and host footage; replace the weak B-roll with better, line-matched footage; add captions, text callouts, lower thirds, graphics, maps, music and SFX. Source videos have no burned-in text. | The host's own voice | Starting: owner uploads videos + scripts to Google Drive and can give a **reference video per host** — each host gets their own look |
| ↳ Nora Hart (home fixes) | Look: `channels/home_howto` (bright, white cards, lemon accent, Outfit, word-highlight captions) — **approved** on the garbage-disposal test. Split screens are restyled as **two rounded panels on a clean background** (Nora left, new B-roll right). **No OpenArt / AI imagery for this host** — real footage, original close-ups and code-drawn diagrams only. | Her own recording | Garbage disposal: **delivered** 2026-11-04 (`projects/garbage-disposal-smell`). Grout without bleach: rendered 2026-11-09 (`projects/grout-without-bleach`) |
| Others | To come. **Every channel gets its own distinct look.** | | |

## How the owner wants videos made
- **Every channel has its own look.** For a new channel or format the owner usually sends a **sample video to model it on**.
  Break it down (cut rhythm, average shot length, shot types, captions, colour/texture, graphics, music
  mood and level, sound effects), build a channel folder from it, render a short test, and get approval
  before making a full episode.
- **Visual quality decides the result.** Always use the best images and footage available, and make each one
  **match the narration exactly** (no generic filler, no anachronisms in history).
- **Keep the screen changing** to hold retention and avoid boredom: about one new shot every 5–6 s, with
  something new appearing at least every ~3 s on graphic pages. Fix every `compose --check` warning.
- **Never cover the host's face while they narrate.** Instruction cards go on the B-roll side of a split screen,
  or as a compact card beside a full-frame host. (Enforced in `pipeline/reedit/compose.py::protect_host`;
  big centred cards over the host stop the build.) Owner feedback, 2026-11-04: it happened twice on the
  garbage-disposal video.
- **Thumbnails: the owner makes them himself from now on (2026-11-09). Do not make thumbnails** unless asked.
  Earlier Nora style, for reference only: Nora on the right, chest-up, calm closed-mouth "trust me" look at camera; 1–3 words in
  heavy condensed yellow (#FFE11A, Anton) with a thick black outline + drop shadow; the problem object on the left
  with a thick yellow curved arrow; optional white-divider split. Built from her real footage (cut-out via MediaPipe,
  expression picked by face blendshapes), template `channels/home_howto/thumbnail_template.html`.
- **Every video ends with a like & subscribe prompt** (animated like/subscribe buttons). Added automatically on
  the host's own "subscribe" line, or in the last seconds if they don't say it (`end_cta` in the channel file).
  Joel's Notebook's end card needs its own in-style version when the next episode is built.
- **Use maps and visual elements** (timelines, stat cards, diagrams) wherever they help viewers follow and keep watching.
- **Voice:** either a real narrator the owner supplies (Milly for Joel's Notebook) or TTS. The vidIQ "George"
  voice (`JBFqnCBsd6RMkjVDRZzb`, "Warm, Captivating Storyteller") was approved as "perfect" for TTS narration.
  ElevenLabs is available (key in env `ELEVENLABS_API_KEY`).
- **Scripts:** the owner usually writes them; Claude may write some, decided channel by channel.
- **Music:** chosen per video to suit the voice, pace and mood (sectioned by mood). Must be free to use with
  no copyright risk: follow `docs/music.md` (Wikimedia Commons first, licence verified on the file page).
  If the right free track can't be obtained, leave music out rather than use something doubtful.
- **Sources available:** Wikimedia Commons, Pixabay (`PIXABAY_API_KEY`), Internet Archive, Pexels (via vidIQ),
  Library of Congress, OpenArt (images/video), vidIQ (voice, music, b-roll, research). The owner can grant
  access to a collection of free short movie clips: ask for it when needed, and check each clip's licence.

## Practicalities
- API keys live in the environment's secrets, never in chat or in the repository.
- Code lives on GitHub. Media (images, recordings, renders) is not committed: back it up before a session ends.
  Silk Road media: the owner's kit page (private link held by the owner) has the illustrations, PixVerse clips and Milly's recordings.
- The cloud sandbox blocks some hosts (YouTube, jsdelivr, incompetech); Wikimedia rate-limits it. Use vidIQ
  `video_watch` to analyse a YouTube sample when the file can't be downloaded.
- Credits: vidIQ voice 14/1000 chars, music 25/track, b-roll 1/search, video_watch 25; OpenArt Seedream 4.5
  image2image 15, Kling 3 Omni image 10, PixVerse V6 image2video 70. Mention costs before big spends.
