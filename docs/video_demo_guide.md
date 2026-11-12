# How to Film the Demo Video — A Follow-Along Script

*A complete, plain-language script for recording the project demo. Follow it top
to bottom and you'll have a polished ~5-minute video, even if you've never
presented this project before.*

> **This guide does not re-explain the whole project** (that's
> [`complete_project_guide.md`](complete_project_guide.md)). It tells you exactly
> what to show, what to click, what to say, and **what every part of the screen
> means**, so you can explain it confidently instead of just pointing at things.

---

## 0. What you're making, and the one tool you'll use

The star of the video is the **Yagi-Uda Antenna Studio**, a live app that opens
in your web browser:

![Antenna Studio](../antenna_studio/studio_preview.png)

It is not a slideshow of pictures. Every number and every curve on that screen is
**calculated live** by our antenna physics solver, the moment you move a slider:

- you see the antenna in **3D** and can spin it around,
- each copper rod **glows** with the electric current flowing in it,
- the **radiation beam** is drawn around the antenna in 3D,
- the **polar plot** and the **four readouts** update instantly,
- and a **virtual measurement** physically turns the antenna on a turntable and
  records its pattern point by point.

**The story your video tells:**

> "Here is our antenna as a live digital model → here's how its shape creates a
> beam → watch what happens when we change the design → watch us measure it →
> and here's proof that our theory, an independent simulation and the
> measurement all agree."

> **Why a browser app?** The earlier matplotlib dashboard redrew everything on
> each slider tick and lagged by seconds. It also showed a generic phased array,
> not our Yagi. The Studio runs the same physics about 10× faster (an update takes
> roughly 10–20 ms), shows *our* antenna, and only has the five controls that
> matter. The old dashboard still exists for curious users but **is not used in
> this video**.

---

## 1. Before you hit record (prep checklist)

- [ ] **Open a terminal** in the project's main folder.
- [ ] **Regenerate everything and open the Studio:**
      ```bash
      python run_pipeline.py --studio
      ```
      Wait for **9 steps all "ok"**; the Studio then opens in your browser.
      (Next time you can also just double-click
      `antenna_studio/antenna_studio.html`. It works offline.)
- [ ] In the browser press **F11** (fullscreen) and **Ctrl+0** (100% zoom).
- [ ] **Rehearse the experiments in Section 4** once, then press
      **"Reset to our design"** so you start clean.
- [ ] Open the **slide deck** `docs/demo_slides.html` in a second browser tab
      (title card, cue cards, closing card, backups).
- [ ] **Screen recorder:** OBS Studio (free) or Windows **Xbox Game Bar**
      (`Win + G`). Record at **1080p**.
- [ ] **Mic check:** record 5 seconds and play it back.
- [ ] **Close notifications**, chat apps and extra browser tabs (they slow the 3D).
- [ ] If `python` can't find numpy, use
      `C:\Users\imamr\AppData\Local\Programs\Python\Python312\python.exe` instead.

> 💡 **Record scene by scene.** If you fumble a line, just redo that scene and
> stitch the clips together afterwards.

---

## 2. Know your instrument — a tour of the Studio screen

Read this once before filming. It's what lets you *explain* the screen rather
than just show it. Everything here is also what an evaluator might ask about.

### 2.1 The header (top strip)

- **"Solved 4 rods in 10.9 ms"**: every time anything changes, the app re-solves
  the antenna physics from scratch. This number proves it's live, and shows how
  long it took. Point at it once in the video. It's a quiet flex.

### 2.2 The 3D view (big left panel)

| What you see | What it means |
|---|---|
| **Copper rods** labelled *Reflector, Driven, D1, D2…* | The antenna itself, at its exact real lengths and spacings. |
| **Pale bar** they sit on | The **boom**. It's non-metal (wood/plastic), so it doesn't disturb the signal. |
| **Small bright dot** in the middle of the *Driven* rod | The **feed point**, the only place the radio signal is connected. Note the small gap there. |
| **How brightly each rod glows** | How much **current** is flowing in that rod. The driven rod is fed; the others glow because they *pick up* energy from it. |
| **Translucent balloon shape** around the antenna | The **3D radiation beam**: how strong the signal is in every direction. A big bulge one way means a strong beam that way. |
| **Ring with tick marks** on the floor | The **turntable**, marked every 10°. It's used by the virtual measurement. |

**Mouse:** drag to spin the view, scroll to zoom. (Spinning is harmless. It only
moves the camera, not the antenna.)

### 2.3 "Current on each rod" panel (inside the 3D view, top right)

Each row shows a rod's current as a **bar** (size) and a pair of numbers like
**"0.58 at −106°"**:

- **0.58**: this rod carries 58% of the driven rod's current.
- **−106°**: its current is **delayed** relative to the driven rod. Think of it
  as "how late this rod is in the wave."

**Why it matters:** the rods' waves add together. Because each rod's current is
delayed by just the right amount, the waves **arrive in step toward the directors**
(and add up → strong beam) and **out of step toward the reflector** (and cancel
→ weak back). This panel is literally the mechanism that creates the beam.

### 2.4 The radiation pattern (polar plot, top right)

This is the 3D beam **seen from directly above**, flattened onto a circle.

- **Around the edge (0°…330°):** directions around the antenna. **0° (top, in
  copper) is where the directors point**, i.e. the front. **180°** is straight
  behind.
- **Rings (10, 0, −10, −20 dBi):** signal strength. **Further from the centre =
  stronger.** Each ring is 5 dB apart (every 3 dB means *double* the power).
- **The curve's shape:** a big lobe at the top = the forward beam; a small lobe
  at the bottom = what leaks backward.

**The four curves (the legend chips underneath):**

| Chip | Line | What it is |
|---|---|---|
| **Live design** | thick copper, shaded | Whatever design is set on the sliders **right now**, calculated live. |
| **Theory** | thin cyan | Our own physics engine's prediction for **our design** (2.44 GHz). |
| **Simulation** | dashed pink | The independent full-wave simulation of **our design**. |
| **Virtual measurement** | green dots | The measured pattern of **our design** (software measurement). |

Click a chip to hide or show that curve.

> If a real phone sweep has been done (see `hardware_next_steps.md`), the green
> chip reads **"Measured (phone sweep)"** instead. The app names it from the
> data's provenance stamp, so the label is always honest. Adjust your narration
> accordingly ("we measured it for real").

> 🔑 **Key idea to say out loud:** the cyan, pink and green references are our
> validated design and **never move**. The copper line is the live design. At our
> design they all lie on top of each other, which is the validation. When you move a
> slider, the copper line **breaks away** from them, so viewers can see exactly
> what changed.

### 2.5 The four readouts (below the polar plot)

| Readout | Plain meaning | Our design | Colour code |
|---|---|---|---|
| **Peak gain** (dBi) | How much stronger the beam is than an antenna that spreads power equally everywhere. Higher = more focused. | **9.5 dBi** (≈ 9× stronger in the beam direction) | — |
| **Front-to-back** (dB) | Forward strength minus backward strength. Higher = less signal wasted behind. | **10.5 dB** | green ≥ 10, amber 5–10, red < 5 |
| **Beamwidth** (°) | How wide the main beam is (measured where power drops to half). Smaller = tighter beam. | **80°** | — |
| **Feed match (VSWR)** | How well the antenna accepts power from the cable. 1.0 is perfect; **below 2** is good; high means power bounces back and is wasted. | **1.66** (impedance 30.1 + j0.9 Ω) | green < 2, amber 2–3, red > 3 |

### 2.6 The five controls (bottom strip)

Each slider changes **one physical thing** about the antenna. Here's what it
does, what you'll see, and why (all numbers below come from the solver):

#### Frequency (2.20–2.70 GHz, ours = 2.44)
- **What it is:** the radio frequency fed into the antenna (Wi-Fi channel).
- **What you'll see:** across the **whole Wi-Fi band (2.40–2.48 GHz)** almost
  nothing changes (gain stays 9.3–9.6 dBi), so it's a robust Wi-Fi antenna. Go far
  outside and it falls apart: at **2.30 GHz** front-to-back drops to 3.8 dB and
  VSWR jumps to 4.7. At **2.20 GHz the beam actually flips and points
  backward.**
- **Why:** a rod's behaviour depends on its length *compared to the wavelength*.
  Changing frequency changes every rod's *electrical* length at once. Far enough
  off, the "mirror" and "lens" rods swap roles.

#### Directors (0–6, ours = 2)
- **What it is:** how many shorter "lens" rods sit in front.
- **What you'll see:** every extra director adds gain and narrows the beam, but
  each one helps less than the last:

  | Directors | 0 | 1 | 2 (ours) | 3 | 4 | 5 | 6 |
  |---|---|---|---|---|---|---|---|
  | Gain (dBi) | 6.6 | 8.3 | **9.5** | 10.0 | 10.8 | 11.1 | 11.5 |
  | Beamwidth | 127° | 96° | **80°** | 73° | 66° | 62° | 59° |

- **Why:** each director re-radiates a slightly delayed copy of the wave, which
  pulls the beam further forward, like adding lenses to a torch. The antenna also
  gets longer (the camera zooms out automatically to fit it).

#### Reflector length (50–68 mm, ours = 59.0)
- **What it is:** the length of the back rod.
- **What you'll see:** shorten it toward the driven rod's 55.6 mm and the back lobe
  grows (front-to-back 4.3 dB at 55.6 mm). Go **shorter than the driven rod
  (50 mm) and the beam flips backward**. Longer than 59 mm improves front-to-back
  slightly (12.6 dB at 62 mm) but *lowers* the gain. 59 mm is the balance.
- **Why:** a rod **longer** than resonance acts like a **mirror**; **shorter** acts
  like a **lens**. A short reflector becomes a lens pointing the wrong way.

#### Director length (44–60 mm, ours = 52.2)
- **What it is:** the length of the first director (each later one is 1.8 mm
  shorter).
- **What you'll see:** shorter directors give a wider, weaker beam (8.0 dBi, 101°
  at 44 mm). Longer ones focus it more (9.9 dBi, 70° at 55.6 mm), but the feed
  match gets worse fast (VSWR 10.6 at 57 mm). Make them **longer than the driven
  rod (60 mm) and they turn into mirrors: the beam flips backward.**
- **Why:** same rule. Shorter than resonance = lens, longer = mirror.

#### Spacing (60–160 %, ours = 100 %)
- **What it is:** stretches or squeezes every gap between rods at once.
- **What you'll see:** squeezed to 60% the front-to-back looks great (17.3 dB) but
  **VSWR shoots to 5.0**, so most of the power would bounce back down the cable.
  Stretched to 160% the longer antenna gains a little (10.0 dBi, beam narrows from
  80° to 71°) with a good match.
- **Why:** closer rods couple more strongly, which shapes the beam harder but drags
  the driven rod's impedance far from the 50 Ω cable. **This is the classic
  antenna trade-off**, and why our design is a balance, not "maximum everything."

### 2.7 Buttons and toggles (bottom right)

| Control | What it does |
|---|---|
| **Run virtual measurement** | Locks the sliders and turns the antenna on the turntable in 10° steps (0°→350°, about 8 seconds). A green **signal source** appears; at each step the received strength is plotted as a white-ringed green dot on the polar plot. It adds realistic measurement imperfections (noise, small reflections, pointing error, 1 dB readout steps), then reports the measured front-to-back and how far it is from the model. Press again to stop early. |
| **Reset to our design** | Puts every slider back to our real antenna (2.44 GHz, 2 directors, 59.0 / 52.2 mm, 100%). |
| **3D beam** | Shows or hides the balloon-shaped beam (hide it to see the rods clearly). |
| **Animate currents** | Makes each rod's glow pulse with its current. The pulses **ripple from the driven rod toward the directors**: you can literally see the wave travelling forward along the antenna. |

---

## 3. The running order (your 5-minute map)

| # | Scene | Time | Where |
|---|---|---|---|
| 1 | Intro | 0:15 | Deck slide 1 (title) |
| 2 | Meet the antenna in 3D | 0:40 | Studio |
| 3 | Read the instrument + validation | 0:45 | Studio |
| 4 | **Live design experiments** ⭐ | 1:50 | Studio |
| 5 | Watch the currents travel | 0:15 | Studio |
| 6 | Live virtual measurement | 0:35 | Studio |
| 7 | Proof it's real physics | 0:30 | Terminal (deck cue slide 3) |
| 8 | Closing | 0:10 | Deck closing slide |
| | **Total** | **~5:00** | |

Running long? Trim experiment 4d first, then shorten Scene 7.

---

## 4. Scene-by-scene script

Each scene has: **📺 On screen** · **🖱 Do this** · **🎙 Say this** (read aloud
or paraphrase) · **👀 What viewers should notice**.

---

### Scene 1 — Intro (0:15)

**📺** Deck slide 1, the title card.

**🎙**
> "This is our 2.44 gigahertz Yagi-Uda antenna: a directional Wi-Fi antenna made
> from four copper rods. Instead of showing you pictures, I'll show you the antenna
> running live in our own physics solver: we'll change its design, measure it,
> and prove the results are real."

**🖱** Switch to the Studio tab (deck slide 2 reminds you).

---

### Scene 2 — Meet the antenna in 3D (0:40)

**📺** The Studio at our design. Make sure "3D beam" is on and "Animate currents"
is off.

**🖱** Slowly drag in the 3D view to spin it once. Then untick **3D beam** for a
few seconds to show the bare rods, and tick it back on.

**🎙**
> "This is our antenna as a live 3D model, built from its exact dimensions. At the
> back is the reflector, then the driven rod. That's the only rod connected to
> the radio, at this small feed point. In front are two directors, all on a
> non-metal boom. [beam back on] This balloon is the radiation beam: how strong
> the signal is in every direction. See how it bulges forward, toward the
> directors, and barely leaks backward. That's what makes it directional."

**👀** The big lobe on the director side, the small lobe behind the reflector.

---

### Scene 3 — Read the instrument, and the validation (0:45)

**📺** Point (with the mouse) at the polar plot, the readouts, then the rod panel.

**🎙**
> "On the right is the same beam seen from above. 0° is straight ahead. The further
> the curve is from the centre, the stronger the signal. The copper line is
> calculated live; the cyan line is our theory engine, the pink dashes are an
> independent simulation, and the green dots are our measurement. All three sit
> right on top of the live curve, so three independent methods give the same
> antenna.
>
> Our design gives 9.5 dBi of gain, about nine times stronger than an antenna
> that spreads power evenly. The front is 10.5 dB stronger than the back, the beam
> is 80° wide, and the VSWR of 1.66 means it accepts power from the cable well.
>
> And this panel shows why. Only the driven rod is fed; the others pick up current
> from it. Each one's current is delayed by a different amount, so their waves add
> up toward the front and cancel toward the back."

**👀** All four curves overlapping; the header "Solved … in … ms".

---

### Scene 4 — Live design experiments ⭐ (1:50)

*The heart of the video. Move sliders **slowly** and narrate what changes. After
each experiment, put that slider back (or press **Reset to our design**).*

#### 4a. More directors (0:30)
**🖱** Drag **Directors** from 2 up to 6, one notch at a time. Then back to 2.

**🎙**
> "Let's add directors. Each one sharpens the beam: gain goes from 9.5 to 10, to
> 10.8… up to 11.5 dBi with six, and the beam narrows from 80° to 59°. But notice
> each director adds less than the last, which is diminishing returns. And the antenna
> keeps getting longer and heavier. Two directors is a good balance for a compact
> antenna."

**👀** The copper polar curve becomes a narrow spike *inside* the fixed reference
curves; the 3D beam stretches forward; the camera zooms out to fit the longer
antenna.

#### 4b. Break the reflector (0:25)
**🖱** Drag **Reflector length** slowly down from 59 to 50 mm. Then back to 59.

**🎙**
> "The reflector works because it's slightly longer than the driven rod, which makes it act
> like a mirror. Watch what happens as I shorten it: the back lobe grows, the
> front-to-back turns amber, then red… and below the driven rod's length the
> beam flips completely and points backward. A rod shorter than resonance acts
> like a lens instead of a mirror."

**👀** The 3D beam swings to the reflector side; front-to-back goes green → amber
→ red (−0.7 dB at 50 mm).

#### 4c. Frequency: works across Wi-Fi, fails outside (0:35)
**🖱** Drag **Frequency** slowly from 2.40 to 2.48 GHz (say the first line), then
down to 2.20 GHz (second line). Then press **Reset to our design**.

**🎙**
> "Across the whole Wi-Fi band, 2.40 to 2.48 gigahertz, the pattern barely moves and
> the gain stays around 9.5 dBi, so it's a solid Wi-Fi antenna. But go far outside:
> at 2.3 gigahertz the back lobe returns and the VSWR goes red, meaning power bounces back to
> the radio. At 2.2 the beam actually turns around. The rods' electrical lengths
> have changed, so the mirror and the lenses have swapped jobs."

**👀** The VSWR readout turning amber/red; the beam reversing at 2.20 GHz; the
director bars in the current panel shrinking.

#### 4d. The trade-off: spacing (0:20) *(optional — cut if running long)*
**🖱** Drag **Spacing** down to 60 %, then back to 100 %.

**🎙**
> "Squeeze the rods together and front-to-back looks even better, 17 dB, but
> look at the VSWR: 5. Most of the power would bounce back down the cable. That's
> the real engineering trade-off, and why our design is a balance rather than
> maxing out one number."

---

### Scene 5 — Watch the currents travel (0:15)

**🖱** Press **Reset to our design**. Tick **Animate currents**. Leave it 5 seconds,
then untick it.

**🎙**
> "Here each rod pulses with its current. Watch the pulse ripple from the driven
> rod forward through the directors. That travelling wave is literally the beam
> being launched forward."

---

### Scene 6 — Live virtual measurement (0:35)

**🖱** At our design, press **Run virtual measurement** and let it run to the end
(about 8 seconds).

**🎙**
> "Now let's measure it. A signal source sits in a fixed spot, and the antenna turns on
> the turntable in 10° steps, exactly like a real measurement. At each step we
> record the received signal; the green dots build the pattern live, with
> realistic noise and reflections added. [when it finishes] The measured
> front-to-back is about 11 dB, within about 1.7 dB of the model on average.
> Since we didn't have the physical antenna in time, this is a *simulated*
> measurement, and the app labels it that way."

**👀** The antenna turning, the source on the right, dots appearing in sequence,
the green summary line at the end.

> ⚠️ **Always say "simulated measurement".** Never imply it's physical lab data.

---

### Scene 7 — Proof it's real physics, not an animation (0:30)

**📺** Deck cue slide 3, then your terminal.

**🖱** Run:
```bash
python run_pipeline.py
node antenna_studio/test_engine.js antenna_studio/py_ref.json
```
Let both finish on screen ("9 steps ok", then "ALL CHECKS PASSED").

**🎙**
> "Everything is reproducible with one command. And the app isn't an animation: it
> runs the same induced-EMF method-of-moments maths as our Python engine. This
> test runs both on six different designs and compares them, and they agree to
> within 0.0000 dB on every point. The browser is showing real physics, just
> fast."

---

### Scene 8 — Closing (0:10)

**📺** Deck closing slide.

**🎙**
> "So that's our antenna: modelled in 3D, solved live, redesigned in real time,
> measured, and validated against theory and an independent simulation. Thanks
> for watching."

---

## 5. If something goes off-script

| Problem | Fix |
|---|---|
| You dragged the wrong slider | Press **Reset to our design**. Everything snaps back. |
| The 3D view feels slow | Close other tabs/apps, untick **3D beam**, make sure the browser is not zoomed. |
| The 3D view is blank (no WebGL) | Use another browser (Chrome/Edge), or switch to the **backup slides** at the end of `docs/demo_slides.html`. |
| You lost the camera angle | Refresh the page (F5). It resets to the default view. |
| Measurement started by accident | Press the same button again (**Stop measurement**). |

---

## 6. Questions an evaluator might ask (and honest answers)

**"Is the 3D app a real simulation or just an animation?"**
> Real. It solves the induced-EMF mutual impedances, the full current matrix and
> the far field from scratch on every change. `test_engine.js` checks it against
> our Python engine on six designs and they match to 0.0000 dB.

**"Why didn't you just use 6 directors for maximum gain?"**
> Diminishing returns (+0.4 dB for the sixth one), a much longer antenna, and a
> worse match. Two directors gives 9.5 dBi in a 10 cm package.

**"Why does the beam flip when the reflector is short?"**
> A rod longer than resonance behaves like a mirror, a shorter one like a lens. A
> too-short reflector becomes a lens pointing backward.

**"Your gain says 9.5 dBi. What does 'dBi' mean?"**
> Decibels compared with an ideal antenna that radiates equally in all directions.
> +9.5 dB is roughly 9× the power in the beam direction.

**"Is the measurement real?"**
> It's a simulated measurement: our solver's pattern put through a model of a real
> turntable range with noise, reflections and pointing error. It is labelled as
> simulated everywhere. A physical sweep with two phones would replace it (see
> `hardware_next_steps.md`).

**"Why is the VSWR 1.66 and not 1.0?"**
> No real antenna is perfectly matched. At 1.66 only about 6% of the power is
> reflected (the usual "good" threshold of VSWR 2 reflects about 11%). A small
> matching network could push it closer to 1.

---

## 7. "What proves what" — map for evaluators

| Claim | Shown by | Scene |
|---|---|---|
| We modelled the real geometry | Studio 3D view (exact lengths/spacings) | 2 |
| The beam is directional | 3D balloon + polar lobe at 0° | 2–3 |
| Theory, simulation and measurement agree | Polar plot: copper, cyan, pink, green overlap | 3 |
| We understand *why* it works | Rod-current panel + animated currents | 3, 5 |
| We understand the design trade-offs | Live experiments 4a–4d | 4 |
| We can measure it | Live virtual measurement | 6 |
| It's reproducible | `run_pipeline.py` all "ok" | 7 |
| The live app is real physics | `test_engine.js`: ALL CHECKS PASSED | 7 |

---

## 8. Quick quality check before you submit

- [ ] Video ≤ 5 min and under ~75 MB (export at 720p if it's too big)
- [ ] Audio clear throughout
- [ ] You spun the 3D antenna and named the rods (Scene 2)
- [ ] You pointed out the overlapping curves = validation (Scene 3)
- [ ] At least three live experiments with narration (Scene 4)
- [ ] The virtual measurement ran to completion and you said **"simulated"** (Scene 6)
- [ ] "ALL CHECKS PASSED" was visible (Scene 7)

> **If someone else is presenting:** give them this guide and have them read
> Section 2 once. That section is what lets them explain the screen instead of
> just showing it. Every line they need to say is in the 🎙 blocks.
