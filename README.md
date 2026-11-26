# Jury Nullification — Big Brown Bear Project

> **Copyright (c) 2026 6700XT <6700XTdude@gmail.com>. All rights reserved.**  
> Master repository holding the locked **Big Brown Bear** spoken-word dark-comedy animatic, local 2D cartoon animation & SFX pipeline, and the open-source **Dynamic Token Wrapping (DTW)** white paper & CLI (*In memoriam George Carlin*).

---

## Master Cuts (`1280x720 @ 24fps`, `64.51s` Waveform-Locked)

* **`bigbrownbear_animatic_master.mp4`** — Gritty muted tavern color + glowing neon signs, untouched master voice recording (`Recording (6).m4a`, `57.51s`), and synced stereo Cartoon SFX bed.
* **`bigbrownbear_animatic_sincity_master.mp4`** — *"Sin City"* film-noir B&W edition across characters, wood, and clothes, keeping vivid selective color strictly on glowing neon signs (**`WIENER TUESDAY'S`** + neon hot dog, **`OKLAHOMA`**, bar neons) and the patron's playful rosy blush & floating pink hearts.

---

## Locked Waveform Timeline (`0.00s` Audio Drift)

`Recording (6).m4a` (`57.51s`) is never cut or time-stretched. Following the `3.00s` silent title card, the **Wiener Tuesday's** establishing shot rides the recording's natural `0.00s–2.64s` intro room breath so spoken dialogue hits frame-accurately at `05.64s`:

| Video Time | Audio Time | Cut ID | Beat / Visual Action |
| :---: | :---: | :--- | :--- |
| `00.00s – 03.00s` | *(pre-roll)* | `OPEN_CARD` | Title card: **`THE BARTENDER VS BIG BROWN BEAR`** |
| `03.00s – 05.64s` | `00.00s – 02.64s` | `1A_EXTERIOR` | **`WIENER TUESDAY'S`** neon + blinking hot dog, streetlamp moths, bear entering |
| `05.64s – 10.98s` | `02.64s – 07.98s` | `S1` | Bear enters bar and demands a beer (wall specks scrubbed clean) |
| `10.98s – 16.10s` | `07.98s – 13.10s` | `S2` | Bartender deadpan refusal #1 |
| `16.10s – 22.24s` | `13.10s – 19.24s` | `S3` | Bear flexes & threatens to beat everyone up |
| `22.24s – 26.85s` | `19.24s – 23.85s` | `S4` | Bartender deadpan refusal #2 (glass inspection) |
| `26.85s – 29.05s` | `23.85s – 26.05s` | `S5_5A` | Wide bar brawl toss + crash SFX |
| `29.05s – 30.40s` | `26.05s – 27.40s` | `S5_5B` | Two-shot: bear lunges up to the fancy woman at the bar |
| `30.40s – 31.85s` | `27.40s – 28.85s` | `S5_5C_GROWL` | Low-angle solo looking straight up at the towering growling bear |
| `31.85s – 33.80s` | `28.85s – 30.80s` | `S5_5D_LADY` | Woman solo: frightened gasp -> playful rosy blush & flutter -> grandiose faint swoon |
| `33.80s – 35.45s` | `30.80s – 32.45s` | `S5_5E_GULP` | `0.80x` consumption + X-ray stomach bubble + cartoon gulp SFX |
| `35.45s – 36.75s` | `32.45s – 33.75s` | `S5_5F_STOOL` | **`OKLAHOMA`** sputtering neon, falling white feather & spinning empty red stool |
| `36.75s – 41.16s` | `33.75s – 38.16s` | `S6` | Bear calmly returns to counter asking for his beer (held pre-slam) |
| `41.16s – 46.37s` | `38.16s – 43.37s` | `S7` | Bartender single bartop slam: *"we don't serve narcotic addicts"* (frozen pre-flies) |
| `46.37s – 54.36s` | `43.37s – 51.36s` | `S8` | Indignant bear clutches chest: *"Narcotic addict? Ha!..."* |
| `54.36s – 58.31s` | `51.36s – 55.31s` | `S9_9A` | Authentic Clip 7 bartender close-up: jaw drops strictly on *"'Well, that was a barbiturate.'"* |
| `58.31s – 60.51s` | `55.31s – 57.51s` | `S9_9B` | Pun lands: bear gets dizzy spiral eyes and crashes flat onto the floor |
| `60.51s – 64.51s` | *(tail pad)* | `END_CARD` | End card: **`FIN / MON SAFE WORD, C'EST OKLAHOMA.`** |

---

## Rebuilding Locally

```powershell
# Rebuilds SFX bed + both Color and Sin City master MP4s:
.\render_timeline.bat
```

## Repository Contents

* `bigbrownbear_animatic_master.mp4` & `bigbrownbear_animatic_sincity_master.mp4`: Final master renders.
* `bigbrownbear_timing_manifest.json`: Waveform-locked sequence & multi-shot manifest (`+150ms` lip-sync open / `-100ms` close spec).
* `assemble_animatic.py`: Master FFmpeg + vectorized Sin City selective-color pipeline.
* `animate_shots_local.py`: Local 2D cartoon animator (neon voltage sputter, moths, falling feather, spinning stool, growl low-angle, diva blush/swoon, and syllable-locked bartender jaw).
* `build_cartoon_sfx.py`: Deterministic stereo 44.1kHz Cartoon SFX synthesizer (`seed = 6700`).
* `WHITE_PAPER_DYNAMIC_TOKEN_WRAPPING.md` & `token_wrapper.py`: Open-source DTW white paper and reference CLI.
* `STORYBOARD_AND_VISUAL_SCRIPT.md`, `DIRECTOR_FEEDBACK_AND_REDACTIONS.md`, `PROJECT_RECORDS_BIG_BROWN_BEAR.md`: Production records & IP audit.

---

## License

Copyright (c) 2026 6700XT <6700XTdude@gmail.com>. All rights reserved. (`token_wrapper.py` and DTW white paper released under repository `LICENSE`.)
