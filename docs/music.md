# Music policy

Pick the music for each video, not for each channel. It must fit the narration's
voice, pace and mood, section by section. Every track must be free to use with no
copyright risk, and its licence is recorded in the project so the credit lands in
the YouTube description automatically.

## Allowed licences
| Licence | OK? | Notes |
|---|---|---|
| Public domain / CC0 | yes | No credit needed (credit anyway when the artist is known). |
| CC BY (3.0 / 4.0) | yes | Credit required: title, artist, licence, link. Most Kevin MacLeod tracks. |
| CC BY-SA | yes, with care | Credit + share-alike. Fine for a background bed in a video. |
| CC BY-NC / CC BY-ND | **no** | NC conflicts with monetised channels; ND forbids edits (trimming and looping count). |
| Generated (vidIQ `generate_music`) | yes | Royalty-free original; record the prompt and job id. |
| "Free" with no stated licence, YouTube rips, "no copyright music" channels | **no** | Unverifiable, a common source of Content ID claims. |

Check the licence on the file's own page (Wikimedia Commons file page, the
`licenseurl` metadata on archive.org). Don't rely on a third-party list.

## Sources (in order of preference)
1. **Wikimedia Commons** (`commons.wikimedia.org`): every file has a machine-readable licence. Kevin MacLeod and many other composers are there.
2. **Internet Archive** (`archive.org`): only items whose `licenseurl` is CC BY / CC0 / public domain.
3. **incompetech.com** (Kevin MacLeod, CC BY 4.0).
4. **vidIQ generated music**: when nothing fits, or for a custom mood or length.
   (Pixabay Music blocks automated downloads.)

## Choosing tracks
- Split the video into its mood sections (hook, rise, revelation, dark turn, resolution)
  and give each section its own track, crossfaded 3–4 s apart.
- Match the tempo to the read: slow, sparse beds under a measured narrator; avoid busy percussion
  under dense information. Keep melodies out of the voice's frequency range (no lead vocals; avoid solo instruments that sit on top of the voice).
- Bed level: about −18 to −20 dB under the voice, ducked further while the narrator speaks.
- Don't reuse a track in two videos of the same channel within a few weeks.
- Record in `music.json` per project: title, artist, source URL, licence, licence URL, the section it covers, and the credit line.
