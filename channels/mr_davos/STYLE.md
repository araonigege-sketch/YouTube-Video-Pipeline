# Mr. Davos — editing style

Faceless, narrated, premium documentary look. Modelled on three Millionaire Problems videos
("The Economics of Owning a Casino / an Airport / an Offshore Oil Rig", broken down with vidIQ
`video_watch` on 2026-11-19), adjusted by the owner's own rules. **Where they differ, the owner's rules win.**

The owner supplies the **script and voiceover** for every episode. The edit is built to fit them.

## Owner's rules (non-negotiable)
1. **B-roll is cinematic and premium, or it isn't used.** Long shots, aerials, drone flyovers, skylines,
   slow push-ins, golden-hour exteriors, anything that looks like a film. It must still match its line.
   Rather fewer clips than one weak one.
2. **Sources:** Pexels first (searched via vidIQ `generate_broll`, then upgraded to the 1080p/1440p/4K
   rendition with `pipeline/reedit/pexels.py`). Pixabay only when the clip is genuinely as good. News and
   public archives when the story needs real events, people or institutions.
3. **Change the B-roll every 3–4 s**, unless there is a strong reason to hold (a reveal, a breath, a
   sweeping establishing shot).
4. **No clip more than twice** in an episode. Keep a clip ledger across episodes, too.
5. **Up to ~70% cinematic B-roll** for episode 1. The final ratio gets decided after it.
6. **On-screen text: clean and premium, never cluttered.** Highlight only important concepts and numbers.
   **No subtitles.**
7. **No distracting whooshes** or swish SFX on transitions or text.
8. **Illustrations drawn with CineCode**, using its richer multi-colour palettes. Illustrations are
   fewer here than in finance, used where they explain something footage can't. **Never cut away
   in the middle of an illustration.** It plays through to its end state before the next shot.
9. **Music:** Kevin MacLeod (CC BY, via Internet Archive / Wikimedia Commons) when a premium-sounding bed
   exists. Otherwise vidIQ `generate_music`. Licence and credit recorded per `docs/music.md`.

## Look (from the references)
- **Cuts:** ~95% hard cuts. No decorative transitions, glitches, lens flares or wipes.
  Only exception: a soft dissolve between archival stills.
- **Rhythm:** wide aerial or skyline establishing shot, then mid or detail shots, then the next wide.
  Pair sweeping scale shots with tight macro inserts for contrast.
- **Grade:** crisp, natural contrast, slightly rich saturation. Warm golden-hour highlights on land and cool teal on water.
  Light edge vignette. No added film grain or letterboxing. Lift news and archival clips' contrast so
  they sit with the stock.
- **Holds:** 4–6 s on wide establishing shots at section starts. 5–7 s on full-screen graphics so they read.

## On-screen text
- One clean sans family (Inter-style), bold or heavy for key words, regular for supporting labels.
- **White** for labels and **one accent colour for key numbers**. The references use yellow-gold (`#FACC15`).
  Mr. Davos' exact accent gets set in the test render.
- Short: 1–6 words per text moment. Every 15–25 s at most, only on numbers, key terms and names.
- Placement: centred for big numbers and years (over slightly darkened B-roll), lower-left for labels.
- Motion: a short fade with a slight upward slide or scale (about 12–16 frames). No typewriter or bouncing effects.

## Signature devices to use
- **Chapter cards:** full-frame near-black (`#0B0B0B`–`#181818`), bold uppercase white title with a subtle
  tracking-in. A brief music dip just before the card.
- **Big centred number** over darkened B-roll for the episode's headline figures.
- **Split screen:** footage on the left half and a black panel on the right that builds a short stacked list
  (costs, steps, comparisons) line by line.
- **Definition card:** cream background, the term, its phonetic spelling and a one-line definition, for key jargon.
- **CineCode illustrations** for mechanisms, flows, maps and comparisons, in multi-colour on a consistent
  canvas. They animate fully before cutting away.

## Structure
- **Cold open:** straight into the premise on a cinematic hero shot in the first 3 seconds. No logo bumper.
- Body split into chapters (chapter cards as above).
- End on a strong final image and the closing line, then the **like & subscribe end prompt** (owner's
  standing rule, confirmed for this channel 2026-11-19), styled to match: clean, white and accent, no SFX.

## Audio
- Voiceover upfront, dry and clear.
- Music: ambient, cinematic, minimal pulse; no lead melody over the voice. Sectioned by mood,
  crossfaded 3–4 s apart, about 16–20 dB under the voice and ducked while it speaks.
- Music drops to near-silence for 0.5–1 s before big chapter turns, then comes back.
- Master at −14 LUFS.

## Decided 2026-11-19
- Accent: yellow-gold `#FACC15` with an Inter-style sans, to be confirmed on the first test render.
- The soft low hits the references use under chapter cards and numbers stay **off**.
- B-roll share: about 65–70%.

## Built devices (channels/mr_davos)
Text over footage: `big` (headline number), `label` (lower-left key term), `questions` (stack that steps back),
`chips` (list spoken item by item), `quote`. Pages: `chapter`, `roadmap` (numbered tiles = the chapters), `define`
(cream dictionary card), `split` (footage left, black list right), `photo` (framed archive photo over its own blur,
credit line), `illus` → `cockpit`, `ladder` (re-enter with `lit:`), `hours` (gap, optional month-by-month fill),
`bars`, `timeline`. Illustrations play to their end state: never cut inside one.

## Sourcing notes (learned on ep1)
- Shots are previewed on contact sheets (`python -m pipeline.broll sheet`) before download; every in-point is checked
  on a mid-frame sheet of the built base before the full render.
- Some Pexels clips serve 720p video under an `hd_1920_1080` filename: always check the downloaded height.
- Split-screen backgrounds need a clip at least as long as the page (the builder now holds the last frame instead
  of drifting, but a frozen frame is not premium).
