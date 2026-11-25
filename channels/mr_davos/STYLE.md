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

## Lessons from ep3 (owner feedback, 2026-11-20)
- **Check the voiceover against the script before building.** Run `python -m pipeline.align.vo_diff <project>` after
  alignment and report every real mismatch to the owner (numbers first: they also appear on screen). Never let the
  aligner paper over a spoken number that differs from the script.
- **"Never more than twice" counts the footage, not the file.** Clips from the same Pexels shoot (same person, same
  horse, same town, same aerial run) read as the same footage: count them together. Photos follow the same rule.
- **A wrong person is worse than no person.** When the line describes a specific role (an agent, a pilot, a fisherman),
  never cut to a civilian stand-in. Use real footage of that role (public-domain government video, licensed clips),
  a real photo, an illustration, or a neutral establishing shot instead.

## Standing decisions (owner, 2026-11-23): the premium bar
The airline-pilot episode (80%+ retention, approved untouched) is the standard. People come for the information but
only stay if the visuals match. **If a shot doesn't match its line and doesn't look like a premium choice, it doesn't go in.**

**Visuals**
- The opening minutes decide retention: no placeholder landscapes there. Lead with the real subject.
- Every shot must show the thing being said: a real border wall for "the US-Mexico border", a real coastline patrol for
  "coastlines", a burning vehicle (ideally with responders) for "an SUV caught fire", stranded people for "people
  stranded in the desert", seniors/veterans for "retirement". Generic open ground, paths and skies are not acceptable stand-ins.
- Introduce people with a look-alike: "Meet Jordan, 26, warehouse worker" shows someone who fits. (Missed with Daniel in ep2.)
- Banned: generic gavel/judge stock for courts. Use cinematic courthouse or courtroom shots instead.
- Pages that hold a while (split screens, long illustrations next to footage) need the most interesting footage, not filler.
- Archive photos run **full-screen** (2048 px CBP/Flickr renditions), slow push, attribution on the image's lower edge.
  The small framed box is only for share-alike photos and images too small to fill the frame.
- No clip used in two different episodes (check `python -m pipeline.broll ledger`). Inside an episode, "max twice"
  counts the shoot, not the file; photos count too.

**Sources, in order**
1. Public-domain government footage and photos (DVIDS reels the owner downloads into Drive; CBP and other agency Flickr).
2. The owner's Movie Clips folder in Drive (film B-roll; picture only, never their audio; skip anything under 720p).
3. Pexels / Pixabay for scenery and objects. Never as a stand-in for a specific role.
4. News reels and news footage: **sparingly, inside a framed box** (not full-screen), credited.

**On-screen text**
- Clean and sparse. Nothing in the bottom-centre caption zone: viewers' subtitles live there.
  No sentence-style lines along the bottom; key concepts only, lower-left labels or upper third.
- Curly apostrophes and quotes everywhere (automatic in the composer).

**Process**
- Run `python -m pipeline.align.vo_diff` after alignment and report every spoken-vs-script mismatch before building.
- Review in-point contact sheets for meaning, not just framing, before rendering.

## Lessons from ep4 (CEO, 2026-11-23)
- Named people: when Wikimedia/Flickr rate-limit this sandbox (429 + retry-after 600 for hours), ask the owner early;
  they will supply portraits. Owner-supplied photos carry no on-screen credit (source unknown) and are listed as such.
- Check every supplied portrait against a second known photo of the same person before using it. If one doesn't clearly
  match, ask the owner instead of silently dropping it (ep4: a Furner photo looked different; the owner confirmed it).
- Owner-supplied photos need no credit, on screen or in the description (owner, 2026-11-23).
- One good two-shot can serve twice: full frame for the handover, then `scale:` + `origin:` to open cropped on one face.
- Portraits inside illustrations (versus cards) get their credit line on the card; describe.py lists them too.
- New pages: `doors` (three routes, re-entered per chapter), `dots` (n people, one chosen), `versus` (two cards + photo reveal).

## Owner review of ep4 (2026-11-23): approved as premium, two misses to fix in every future episode
- **News moments get news visuals.** When the script reports a news event (a scandal, a resignation, a firing, a recall)
  or cites an outlet ("CNBC reported…"), show a news reel or a news screenshot/headline from that outlet. Put it **in a
  framed box**, not full-screen, for a few seconds. Ep4 missed this at ~8:44 (Huang resigning, "CNBC reported that the
  board had decided he had to go"): generic B-roll ran where a boxed CNBC clip or headline belonged. Plan these moments
  when reading the script, and ask the owner for the reel or screenshot if this sandbox can't reach the source.
- **Weak portrait of a famous person → ask the owner.** The ep4 Steve Jobs photo (Flickr, dim stage shot) was not good
  enough. If the best licensed photo of a named person isn't premium, ask the owner early for better ones instead of using it.

## Lessons from ep5 (Astronaut, 2026-11-25)
- **Boxed news in practice:** `page: news` puts a clip in a framed box over a blurred copy of itself, with a source line
  under the box ("CBS NEWS · 4 APR 2023") from `media/news/news.json`. CBS News pages carry an HLS `contentUrl`; fetch the
  picture only (we never use their audio) and keep each excerpt to a few seconds. describe.py lists every excerpt.
- **Agency footage beats stock for real people and places.** NASA's media library (images-api.nasa.gov) is public domain
  and has 4K reels of the exact people named in the script. Use Pexels/Pixabay only for generic lines.
- **Long agency reels are many shots.** Run `python -m pipeline.scenes <media dir>` so the check counts reuse per scene
  (per minute inside single takes longer than 90 s). Add manual cuts where soft fades fool the detector.
- **Agency reels hide slates.** Titles, info cards, "FUN FACT" captions and end logos sit between shots. Check every
  in-point frame, not just the first, and keep shots off scene boundaries (the check warns).
- **Illustration holds follow the words.** Reveal each step on the first phrase that states it (the $0 bar on "don’t pay",
  not on the later "they get paid"); a still illustration over about 5 s needs a reason in the narration.
- New illustrations: `funnel` (log-scaled selection stages), `tries` (n attempts, failures crossed, the win in gold).
