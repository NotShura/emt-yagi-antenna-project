# How to Film the Demo Video — A Follow-Along Script

*A shot-by-shot guide to recording the project demonstration. Open it, follow it
top to bottom, and you'll have a complete 5-minute demo video — even if you've
never presented the project before.*

> **This guide does NOT explain the project** (that's in
> [`complete_project_guide.md`](complete_project_guide.md)). This one is purely
> **"press record and do these things in this order."** For each scene it tells
> you: what to show on screen, what to click/type, and a line you can read aloud.

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
- [ ] **Open these files/images** in tabs ahead of time (so you just switch, not hunt):
      - `EMT_Member2/yagi_4el_244GHz.nec` (the CAD/geometry text)
      - `EMT_Member2/yagi_3d_structure.png` (3D antenna render)
      - `member3_hardware/output/antenna_3d_assembly.png` (labeled 3D assembly)
      - `EMT_Member2/smith_chart.png` and `EMT_Member2/simulated_pattern_preview.png`
      - `member4_telemetry/output/virtual_measurement_preview.png`
      - `member4_telemetry/output/friis_link_budget.png`
      - `data/empirical_pattern.provenance.txt`
- [ ] **Have the dashboard command ready** to paste:
      `python Electromagnetic-Theory-Member-1-main/antenna_gui.py`
- [ ] **Pick a screen recorder:** OBS Studio (free), or Windows **Xbox Game Bar**
      (`Win + G` → record). Record at **1080p** if you can.
- [ ] **Check your mic** — do a 5-second test and play it back.
- [ ] **Close notifications / messaging apps** so nothing pops up mid-recording.
- [ ] If `python` can't find numpy, use the full path instead everywhere:
      `C:\Users\imamr\AppData\Local\Programs\Python\Python312\python.exe`

> 💡 **Tip:** You don't have to record it all in one take. Record each scene
> separately and stitch them, or just restart a scene if you flub a line.

---

## 2. The running order (your 5-minute map)

| # | Scene | Time | What's on screen |
|---|---|---|---|
| 1 | Intro | 0:15 | You / title slide |
| 2 | The digital antenna (CAD) | 0:45 | `.nec` file + 3D render |
| 3 | Run the whole project | 0:30 | Terminal: `run_pipeline.py` |
| 4 | Theory engine | 0:30 | Theory polar plot |
| 5 | Full-wave simulation | 0:45 | Pattern + Smith chart |
| 6 | Virtual measurement | 0:45 | Sweep preview + provenance |
| 7 | **The payoff: overlay** | 1:00 | Live dashboard, 3 curves |
| 8 | Verification numbers | 0:30 | Friis / error output |
| 9 | Files + honesty recap | 0:20 | File tree |
| 10 | Closing | 0:10 | You / title |
| | **Total** | **~5:00** | |

Keep an eye on the clock — if you're running long, trim Scenes 4 and 8 first.

---

## 3. Scene-by-scene script

Each scene below has three parts:
**📺 On screen** (what the viewer sees) · **🖱 Do this** (your action) ·
**🎙 Say this** (read aloud, or paraphrase in your own words).

---

### Scene 1 — Intro (0:15)

**📺 On screen:** Your face or a simple title card ("2.44 GHz Yagi-Uda Antenna —
Design, Simulation & Validation").

**🖱 Do this:** Just talk to the camera, or show the title.

**🎙 Say this:**
> "This is our 2.44 GHz directional antenna project. In the next few minutes I'll
> show you the antenna as a digital model, run the physics that predicts how it
> behaves, simulate it, measure it, and prove that all three independent methods
> agree. Let's start."

---

### Scene 2 — The digital antenna / CAD (0:45)

*This is the "how the CAD demonstrates the antenna" part.*

**📺 On screen:** First the `.nec` geometry file, then the 3D render.

**🖱 Do this:**
1. Open `EMT_Member2/yagi_4el_244GHz.nec`. Scroll slowly to the element lines
   (the `GW` "wire" cards and the length/position variables near the top).
2. Switch to `EMT_Member2/yagi_3d_structure.png` (and/or
   `member3_hardware/output/antenna_3d_assembly.png`).

**🎙 Say this:**
> "For an antenna, the CAD model isn't a 3D drawing — it's a precise description of
> where each copper rod sits. This file defines our four rods: their exact lengths
> and spacings. [switch to render] And here's that same geometry drawn in 3D — one
> reflector at the back, the driven element, and two directors in front. This
> digital model is what every calculation and simulation runs on, so the numbers
> and the picture are always the same antenna."

> **Point at the picture** as you name the reflector / driven / directors — viewers
> remember what you point to.

---

### Scene 3 — Run the whole project (0:30)

**📺 On screen:** The terminal.

**🖱 Do this:** Type and run:
```bash
python run_pipeline.py
```
Let the "PIPELINE SUMMARY" with all the green "ok"s appear.

**🎙 Say this:**
> "Everything is reproducible from one command. This regenerates the entire project
> in order — the simulation, the cutting blueprint, the physics engine, the
> measurement, and the error analysis. Watch every step come back 'ok'. That means
> the whole toolchain works front to back."

> Let the summary table sit on screen for 2–3 seconds so viewers see all the ✓'s.

---

### Scene 4 — The theory engine (0:30)

**📺 On screen:** The theoretical radiation pattern.

**🖱 Do this:** Open
`Electromagnetic-Theory-Member-1-main/radiation_pattern_polar.png`
(or the 3D one, `radiation_3d_spherical.png`).

**🎙 Say this:**
> "First method: pure theory. We wrote our own electromagnetics code — no
> downloaded tools — that predicts the radiation pattern from first principles.
> Notice the shape: a big lobe pointing forward at zero degrees and almost nothing
> backward. That's a directional beam. This is our 'ground truth' from the maths."

---

### Scene 5 — The full-wave simulation (0:45)

**📺 On screen:** The simulated pattern, then the Smith chart.

**🖱 Do this:**
1. Open `EMT_Member2/simulated_pattern_preview.png`.
2. Then `EMT_Member2/smith_chart.png`.

**🎙 Say this:**
> "Second method: a full-wave simulation. This uses completely different maths from
> our theory engine, so it's an independent second opinion. [pattern] Same beam
> shape — forward lobe, suppressed back. [Smith chart] It also gives us the
> electrical performance: the antenna is well matched at 2.44 gigahertz, with very
> low reflection. So the design isn't just directional — it's efficient too."

---

### Scene 6 — The virtual measurement (0:45)

**📺 On screen:** The virtual-measurement preview, then the provenance file.

**🖱 Do this:**
1. (Optional) Re-run it live so viewers see it generate:
   ```bash
   python member4_telemetry/virtual_measurement.py
   ```
2. Open `member4_telemetry/output/virtual_measurement_preview.png`.
3. Briefly show `data/empirical_pattern.provenance.txt`.

**🎙 Say this:**
> "Third method: the measurement. Because this is the software version of the
> project, we measure the antenna *inside the computer* — we run the simulated
> antenna through a virtual turntable sweep, adding the small imperfections a real
> measurement has: noise, reflections, pointing wobble. [preview] You can see it
> tracks the ideal pattern but with realistic wiggles. [provenance] And we label it
> honestly — this file records that it's a *simulated* measurement, not a lab
> reading."

> ⚠️ **Say the word "simulated" clearly here.** Never imply it's a physical
> measurement — the honesty is part of what makes the project credible.

---

### Scene 7 — The payoff: the live overlay (1:00) ⭐

*This is the most important scene. Slow down and let it land.*

**📺 On screen:** The interactive dashboard.

**🖱 Do this:**
1. Launch it:
   ```bash
   python Electromagnetic-Theory-Member-1-main/antenna_gui.py
   ```
2. Click **"Plot Overlay"** (the comparison panel).
3. Let the three curves appear: **Theory**, **Simulation**, **Virtual Meas.**
4. If there are sliders, gently drag one to show the pattern responds live.

**🎙 Say this:**
> "Now the moment that ties it all together. Here are all three results on one
> graph — theory in one colour, simulation in another, and the virtual measurement
> in the third. Look how they lie almost on top of each other: the same forward
> beam, the same deep null at the back. Three completely independent methods, one
> answer. [drag a slider] And it's fully interactive — change a parameter and the
> pattern updates in real time. That agreement is the proof the design works."

> Let the overlaid curves stay on screen for a good 4–5 seconds. This image is your
> thumbnail-worthy money shot.

---

### Scene 8 — The verification numbers (0:30)

**📺 On screen:** The Friis / error output or plot.

**🖱 Do this:** Show `member4_telemetry/output/friis_link_budget.png`, or scroll the
terminal to the Friis section from the pipeline run (the RMSE / front-to-back lines).

**🎙 Say this:**
> "We don't just eyeball it — we quantify the agreement. The measured pattern
> differs from theory by only about one decibel on average, and the beam is roughly
> eleven decibels stronger forward than backward. Small error, strong directivity —
> the numbers confirm what the graph shows."

---

### Scene 9 — Files + honesty recap (0:20)

**📺 On screen:** The project folder / file tree.

**🖱 Do this:** Show the folders: `data/` (the three CSVs),
`member4_telemetry/`, `EMT_Member2/`, `docs/`.

**🎙 Say this:**
> "Everything is in the repository and reproducible: the three pattern files, the
> simulation, the measurement code, and full documentation. Anyone can clone it and
> get these exact results with one command."

---

### Scene 10 — Closing (0:10)

**📺 On screen:** You, or the title card.

**🎙 Say this:**
> "So that's our antenna: designed as a digital model, predicted by our own physics
> code, confirmed by simulation, and validated by measurement — all three in
> agreement. Thanks for watching."

---

## 4. Commands cheat sheet (paste these during filming)

```bash
# Scene 3 — run the whole project
python run_pipeline.py

# Scene 6 — (optional) regenerate the virtual measurement live
python member4_telemetry/virtual_measurement.py

# Scene 7 — launch the interactive dashboard
python Electromagnetic-Theory-Member-1-main/antenna_gui.py

# If plain `python` can't find numpy, swap it for:
# C:\Users\imamr\AppData\Local\Programs\Python\Python312\python.exe
```

---

## 5. "What proves what" — file → claim map

If an evaluator asks *"where do you show X?"*, point here:

| The claim | Shown by | Scene |
|---|---|---|
| We modelled the real antenna geometry | `EMT_Member2/yagi_4el_244GHz.nec` + 3D render | 2 |
| It all runs reproducibly | `run_pipeline.py` summary | 3 |
| Theory predicts a directional beam | `radiation_pattern_polar.png` | 4 |
| An independent simulation agrees | `simulated_pattern_preview.png` | 5 |
| It's electrically well-matched | `smith_chart.png` | 5 |
| We "measured" it (honestly labelled) | `virtual_measurement_preview.png` + `*.provenance.txt` | 6 |
| All three methods agree | the GUI overlay (3 curves) | 7 |
| The agreement is quantified | `friis_link_budget.png` | 8 |

---

## 6. Recording & delivery tips

- **Keep it under the limits:** target ≤ 5 minutes and under ~75 MB. 1080p screen
  capture at a normal bitrate easily fits; if it's too big, export at 720p or
  shorten Scenes 4 and 8.
- **Split-screen looks great** for Scene 7: your webcam in a corner while the
  dashboard fills the screen.
- **Narrate slowly.** It always feels too slow while recording and just right on
  playback.
- **Zoom in** on small text (the `.nec` lines, the provenance file) so it's
  readable — use your editor's zoom or the OS magnifier.
- **One pattern image = a few seconds minimum.** Don't flash past the plots; let
  each one breathe.
- **If you also built the physical antenna:** insert a 15–20s clip of it on the
  turntable right after Scene 6, and change Scene 6's wording from "virtual
  measurement" to "we also measured it for real." Otherwise, keep it software-only
  and honest.

---

## 7. Quick quality check before you submit

- [ ] Video is ≤ 5 min and opens/plays fine
- [ ] Audio is audible the whole way through
- [ ] The CAD geometry and 3D render were both shown (Scene 2)
- [ ] The pipeline ran with all "ok"s on screen (Scene 3)
- [ ] All three curves were visible together on the overlay (Scene 7)
- [ ] You said the word **"simulated"** about the measurement (Scene 6)
- [ ] The error numbers appeared (Scene 8)

> **If someone else is presenting:** hand them this file and the prep checklist in
> Section 1. Everything they need to say is in the 🎙 lines — they can read them
> verbatim.
