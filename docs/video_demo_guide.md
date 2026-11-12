# How to Film the Demo Video — A Follow-Along Script

*A shot-by-shot guide to recording the project demonstration. Open it, follow it
top to bottom, and you'll have a complete 5-minute demo video — even if you've
never presented the project before.*

> **This guide does NOT explain the project** (that's in
> [`complete_project_guide.md`](complete_project_guide.md)). This one is purely
> **"press record and do these things in this order."** For each scene it tells
> you: which slide to be on, what to click/type, and a line you can read aloud.

> 🆕 **You don't open any image files by hand.** Every picture the video needs is
> already bundled, in order, in one slideshow: **`docs/demo_slides.html`**. You
> just advance it with the arrow keys. Two slides in that deck are bright amber
> **"DO THIS NOW"** cue cards that tell you exactly when to switch to the terminal
> or the live dashboard. The deck *is* your teleprompter and your visuals in one.

---

## 0. What you're making

A **~5-minute screen-recorded video** that proves the project is a fully working,
validated antenna design — entirely in software. The story the video tells, in
order, is:

> **"Here's the antenna as a digital model → here's the physics computing it →
> here's the simulation → here's the measurement → and here's proof all three
> agree."**

That arc is the whole point. If a viewer sees three independent methods land on
the same answer, they believe it works. Your job is just to show that on screen.

---

## 1. Before you hit record (prep checklist)

Do all of this **first**, so recording is smooth and you never fumble.

- [ ] **Open a terminal** in the project's main folder.
- [ ] **Do one clean practice run** so files exist and nothing errors:
      `python run_pipeline.py` (wait for "PIPELINE SUMMARY ... ok").
- [ ] **Open the slideshow** `docs/demo_slides.html` in a browser and press **F**
      for fullscreen. This single file holds every image, in order — you won't
      open any PNGs by hand.
- [ ] **Have the dashboard command ready** to paste (for the one live moment):
      `python Electromagnetic-Theory-Member-1-main/antenna_gui.py`
- [ ] **Arrange two things you'll switch between:** the fullscreen slideshow and
      your terminal. (Later you briefly add the live dashboard.) Alt-Tab practice
      a couple of times so switching is clean on camera.
- [ ] **Pick a screen recorder:** OBS Studio (free), or Windows **Xbox Game Bar**
      (`Win + G` → record). Record at **1080p** if you can.
- [ ] **Check your mic** — do a 5-second test and play it back.
- [ ] **Close notifications / messaging apps** so nothing pops up mid-recording.
- [ ] If `python` can't find numpy, use the full path instead everywhere:
      `C:\Users\imamr\AppData\Local\Programs\Python\Python312\python.exe`

> 💡 **Tip:** You don't have to record it all in one take. Record each scene
> separately and stitch them, or just restart a scene if you flub a line.

### Slideshow controls (memorise these three)

| Key | Does |
|---|---|
| **→** or **Spacebar** | next slide |
| **←** | previous slide |
| **F** | toggle fullscreen · **C** toggles the captions off/on for a clean image |

The deck has **13 slides** and shows a progress bar + a "n / 13" counter so you
always know where you are.

---

## 2. The running order (your 5-minute map)

Each row is a slide in `demo_slides.html`. You simply advance through them; at the
two amber **cue** slides you switch away to do a live action, then come back.

| Slide | Scene | Time | What you do |
|---|---|---|---|
| 1 | Intro | 0:15 | Read the intro line |
| 2–3 | The digital antenna (CAD) | 0:45 | Talk over the two 3D renders |
| 4 ▶ | **CUE: terminal** | 0:30 | Switch to terminal, run the pipeline |
| 5–6 | Theory engine | 0:30 | Talk over the two theory plots |
| 7–8 | Full-wave simulation | 0:45 | Talk over the pattern + Smith chart |
| 9 | Virtual measurement | 0:45 | Talk over the sweep preview |
| 10 ▶ | **CUE: live dashboard** | 1:00 | Switch to the GUI, show the overlay live |
| 11 | Overlay (still backup) | — | Optional; skip if you showed it live |
| 12 | Verification numbers | 0:30 | Talk over the Friis/error plot |
| 13 | Closing | 0:10 | Read the closing line |
| | **Total** | **~5:00** | |

Running long? Trim the talking on slides 6 and 12 first.

---

## 3. Scene-by-scene script

Each scene below has three parts:
**📺 Slide** (where to be in the deck) · **🖱 Do this** (your action) ·
**🎙 Say this** (read aloud, or paraphrase in your own words).

---

### Scene 1 — Intro · Slide 1 (0:15)

**📺 Slide:** 1 (the title card).

**🖱 Do this:** Start recording with the fullscreen title slide showing.

**🎙 Say this:**
> "This is our 2.44 GHz directional antenna project. In the next few minutes I'll
> show you the antenna as a digital model, run the physics that predicts how it
> behaves, simulate it, measure it, and prove that all three independent methods
> agree. Let's start."

**➡ Press → for the next slide.**

---

### Scene 2 — The digital antenna / CAD · Slides 2–3 (0:45)

*This is the "how the CAD demonstrates the antenna" part.*

**📺 Slide:** 2, then 3.

**🖱 Do this:** Stay on slide 2 while you talk, then press → to slide 3.

**🎙 Say this (slide 2):**
> "For an antenna, the CAD model isn't a 3D drawing — it's a precise description of
> where each copper rod sits. Here's our antenna in 3D: one reflector at the back,
> the driven element, and two directors in front — four copper rods."

**🎙 Say this (slide 3):**
> "This is the same geometry with every rod's exact length and spacing labelled.
> These numbers are what every calculation and simulation runs on, so the picture
> and the maths are always the same antenna."

> **Point at the picture** as you name reflector / driven / directors — viewers
> remember what you point to.

**➡ Press → to the amber cue slide.**

---

### Scene 3 — Run the whole project · Slide 4 (CUE) (0:30)

**📺 Slide:** 4 — the amber **"DO THIS NOW: Switch to the TERMINAL"** card.

**🖱 Do this:** Alt-Tab to your terminal and run:
```bash
python run_pipeline.py
```
Let the "PIPELINE SUMMARY" with all the "ok"s appear. Then Alt-Tab back to the
slideshow and press → to slide 5.

**🎙 Say this:**
> "Everything is reproducible from one command. This regenerates the entire project
> in order — simulation, blueprint, physics engine, measurement, error analysis.
> Watch every step come back 'ok'. The whole toolchain works front to back."

> Let the summary table sit on screen for 2–3 seconds so viewers see all the ✓'s.

---

### Scene 4 — The theory engine · Slides 5–6 (0:30)

**📺 Slide:** 5 (polar), then 6 (3D).

**🎙 Say this (slide 5):**
> "First method: pure theory. We wrote our own electromagnetics code — no
> downloaded tools — that predicts the radiation pattern from first principles. A
> big lobe forward at zero degrees, almost nothing backward. That's a directional
> beam, and it's our 'ground truth' from the maths."

**🎙 Say this (slide 6):**
> "Here's that same prediction as a 3D shape — a beam pointing one way."

**➡ Press → to slide 7.**

---

### Scene 5 — The full-wave simulation · Slides 7–8 (0:45)

**📺 Slide:** 7 (pattern), then 8 (Smith chart).

**🎙 Say this (slide 7):**
> "Second method: a full-wave simulation. It uses completely different maths from
> our theory engine, so it's an independent second opinion — and it gives the same
> beam shape: forward lobe, suppressed back."

**🎙 Say this (slide 8):**
> "It also gives the electrical performance. This Smith chart shows the antenna is
> very well matched at 2.44 gigahertz, with low reflection — so it's efficient, not
> just directional."

**➡ Press → to slide 9.**

---

### Scene 6 — The virtual measurement · Slide 9 (0:45)

**📺 Slide:** 9 (the virtual-measurement sweep preview).

**🖱 Do this (optional):** Before this, you could Alt-Tab to the terminal and run
`python member4_telemetry/virtual_measurement.py` live, then come back — but the
slide alone is enough.

**🎙 Say this:**
> "Third method: the measurement. Because this is the software version of the
> project, we measure the antenna *inside the computer* — we run the simulated
> antenna through a virtual turntable sweep, adding the small imperfections a real
> measurement has: noise, reflections, pointing wobble. You can see it tracks the
> ideal pattern with realistic wiggles. And we label it honestly — it's a
> *simulated* measurement, not a lab reading."

> ⚠️ **Say the word "simulated" clearly here.** Never imply it's a physical
> measurement — the honesty is part of what makes the project credible.

**➡ Press → to the amber cue slide.**

---

### Scene 7 — The payoff: the live overlay · Slide 10 (CUE) + 11 (1:00) ⭐

*This is the most important scene. Slow down and let it land.*

**📺 Slide:** 10 — the amber **"DO THIS NOW: Switch to the LIVE DASHBOARD"** card.

**🖱 Do this:**
1. Alt-Tab to the terminal and launch:
   ```bash
   python Electromagnetic-Theory-Member-1-main/antenna_gui.py
   ```
2. Click **"Plot Overlay"** and let the three curves appear: **Theory**,
   **Simulation**, **Virtual Meas.**
3. If there are sliders, gently drag one to show the pattern responds live.
4. When done, Alt-Tab back to the slideshow. **Slide 11 is a still backup of the
   overlay** — show it for a beat, or press → straight past it to slide 12.

**🎙 Say this:**
> "Now the moment that ties it all together. Here are all three results on one
> graph — theory, simulation, and the virtual measurement. Look how they lie almost
> on top of each other: the same forward beam, the same deep null at the back.
> Three completely independent methods, one answer. [drag a slider] And it's fully
> interactive — change a parameter and the pattern updates in real time. That
> agreement is the proof the design works."

> If the live GUI is slow to open, just narrate over slide 11 (the still overlay)
> instead — the point lands either way.

---

### Scene 8 — The verification numbers · Slide 12 (0:30)

**📺 Slide:** 12 (the Friis / error plot).

**🎙 Say this:**
> "We don't just eyeball it — we quantify the agreement. The measured pattern
> differs from theory by only about one decibel on average, and the beam is roughly
> eleven decibels stronger forward than backward. Small error, strong directivity —
> the numbers confirm what the graph shows."

**➡ Press → to slide 13.**

---

### Scene 9 — Closing · Slide 13 (0:10)

**📺 Slide:** 13 (the closing card).

**🎙 Say this:**
> "So that's our antenna: designed as a digital model, predicted by our own physics
> code, confirmed by simulation, and validated by measurement — all three in
> agreement. Everything's in the repository and reproducible with one command.
> Thanks for watching."

Stop recording.

---

## 4. Commands cheat sheet (paste these during filming)

```bash
# Open the slideshow (your visuals + cue cards), then press F for fullscreen:
#   docs/demo_slides.html

# Slide 4 cue — run the whole project
python run_pipeline.py

# Scene 6 (optional) — regenerate the virtual measurement live
python member4_telemetry/virtual_measurement.py

# Slide 10 cue — launch the interactive dashboard
python Electromagnetic-Theory-Member-1-main/antenna_gui.py

# If plain `python` can't find numpy, swap it for:
# C:\Users\imamr\AppData\Local\Programs\Python\Python312\python.exe
```

> If you ever regenerate the plots, rebuild the deck so it shows the fresh images:
> `python docs/build_demo_slides.py`

---

## 5. "What proves what" — slide → claim map

If an evaluator asks *"where do you show X?"*, point here:

| The claim | Shown on | Scene |
|---|---|---|
| We modelled the real antenna geometry | slides 2–3 (3D CAD renders) | 2 |
| It all runs reproducibly | slide 4 cue → terminal pipeline | 3 |
| Theory predicts a directional beam | slides 5–6 | 4 |
| An independent simulation agrees | slide 7 | 5 |
| It's electrically well-matched | slide 8 (Smith chart) | 5 |
| We "measured" it (honestly labelled) | slide 9 | 6 |
| All three methods agree | slide 10 cue → live GUI (slide 11 backup) | 7 |
| The agreement is quantified | slide 12 (Friis plot) | 8 |

---

## 6. Recording & delivery tips

- **Keep it under the limits:** target ≤ 5 minutes and under ~75 MB. 1080p screen
  capture at a normal bitrate easily fits; if it's too big, export at 720p or
  shorten the talking on slides 6 and 12.
- **Split-screen looks great** for Scene 7: your webcam in a corner while the
  dashboard fills the screen.
- **Narrate slowly.** It always feels too slow while recording and just right on
  playback.
- **Let each slide breathe** — a few seconds minimum. Don't machine-gun the arrow key.
- **Press C** on a slide if you want the image totally clean (captions hidden) for
  a nicer shot.
- **If you also built the physical antenna:** insert a 15–20s clip of it on the
  turntable right after slide 9, and change Scene 6's wording from "virtual
  measurement" to "we also measured it for real." Otherwise, keep it software-only
  and honest.

---

## 7. Quick quality check before you submit

- [ ] Video is ≤ 5 min and opens/plays fine
- [ ] Audio is audible the whole way through
- [ ] The CAD renders were shown (slides 2–3)
- [ ] The pipeline ran with all "ok"s on screen (slide 4 cue)
- [ ] All three curves were visible together — live GUI or slide 11
- [ ] You said the word **"simulated"** about the measurement (slide 9)
- [ ] The error numbers appeared (slide 12)

> **If someone else is presenting:** hand them this file plus the open slideshow.
> Everything they need to say is in the 🎙 lines, and the deck's amber cue cards
> prompt the two live moments — they can read the lines verbatim and just follow
> the arrows.
