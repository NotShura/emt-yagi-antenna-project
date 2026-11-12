# What To Do Next — The Hardware, Explained Simply

*A follow-along guide for the physical part of the 2.44 GHz Yagi-Uda antenna project.*

> **Who this is for:** anyone on the team (or a curious friend) who wants to
> build and test the antenna, even with zero background on the project. No prior
> knowledge assumed. If a word looks scary, there's a plain-English version next
> to it.

---

## 1. The project in 60 seconds

We're building a **directional Wi-Fi antenna**. A normal antenna sprays signal in
every direction like a bare light bulb. Ours focuses the 2.44 GHz Wi-Fi signal
into a **beam**, like a torch — stronger in the direction it points, weaker
everywhere else.

The design is a **Yagi-Uda** antenna (the same "fishbone" shape as old rooftop TV
aerials). It's just **4 metal rods on a stick**:

```
   signal shoots this way  ───────────────▶

   R          D          D1         D2
   │          │          │          │        R  = Reflector  (bounces signal forward)
   ├──────────┼──────────┼──────────┤        D  = Driven element (the only one with a wire)
   │          │          │          │        D1 = Director 1  (pulls the beam forward)
          (coax plugs                         D2 = Director 2  (pulls it further)
           in here)
```

Only the **Driven element (D)** is connected to anything. The other three are
just bits of wire — they shape the beam purely by sitting nearby (physics calls
this "parasitic coupling"; think of it as the rods passing the signal along like
a bucket chain).

**The whole experiment:** build it, slowly spin it in a circle while measuring how
strong the signal is at each angle, and show that the real-world result matches
the physics we calculated in software. That "signal strength vs angle" graph
(a **radiation pattern**) is the trophy.

---

## 2. Where we are right now

The project is **~85% software, ~15% hardware**, and **all the software is done**:

- ✅ The physics math engine, the interactive viewer, the full-wave simulation,
  the cutting blueprints, and the telemetry/logging code are all written, tested,
  and talk to each other correctly.
- ⬜ **What's left is purely physical** — and that's what this guide covers.

So you're not coding anything new. You're doing three hands-on jobs:

| # | Job | Time | Tools |
|---|---|---|---|
| **A** | **Build** the antenna (cut wire, glue to a stick) | ~1.5 h | ruler, cutter, glue |
| **B** | **Measure** it (spin it, log signal at each angle) | ~2 h | 2 smartphones |
| **C** | **Show the result** (one command overlays real vs theory) | ~5 min | laptop |
| **D** | **Film + slides** (5-min video, 3 slides) | ~3 h | phone camera |

---

## 3. What to buy

Nothing expensive — **two smartphones you already own, a bit of copper wire, and a
non-metal stick.** Everything else is tape and a printed page.

- **Copper wire** — ~1 m of stiff 14 AWG (1.6 mm) solid core, for the 4 rods
- **A non-metal boom** — wooden dowel, bamboo skewer, acrylic rod or cardboard tube
- **Tape / hot glue / cable ties** — to hold the rods down
- **A printed 360° protractor** — one A4 page (the software makes it, see Part B)
- **2 smartphones** — one as the signal source, one as the meter

> ⚠️ **The stick must not be metal.** Metal near the rods bends the beam and ruins
> the measurement, like a smudge on a camera lens.

No soldering, RF cables or ESP32 needed — an optional ESP32 logger lives in
`member4_telemetry/esp32_rssi_logger/`, but the phone path replaces it entirely.

---

## 4. Before you touch any wire: print your blueprint

Everything you cut comes from numbers the software already calculated. Generate
your personal cheat-sheet and diagrams first:

```bash
python member3_hardware/dimension_calculator.py   # prints exact cut lengths + shopping list
python member3_hardware/visualize_antenna.py      # makes diagrams + the protractor to print
```

> 💡 **Which Python?** This project needs `numpy`/`scipy`/`matplotlib`. On this
> machine the interpreter that has them is **Python 3.12**:
> `C:\Users\imamr\AppData\Local\Programs\Python\Python312\python.exe`.
> If `python ...` complains "No module named numpy", use that full path instead,
> or run `pip install -r requirements.txt` first.

The diagrams land in `member3_hardware/output/` — print
`protractor_template.png` for Part B.

---

## 5. Full parts list 🧰

Everything the build touches, grouped by job. No soldering and no electronics
beyond your two phones.

**The antenna**
- ~1 m of 14 AWG (1.6 mm) solid copper wire — the 4 rods
- A non-metal boom ~8–10 cm long (wood, bamboo, acrylic or cardboard)
- Hot glue, tape or cable ties to fix the rods on
- A few sticky labels to mark each rod (R, D-left, D-right, D1, D2)

**Measuring it**
- 2 smartphones — one sharing a 2.4 GHz hotspot (the source), one running a free
  Wi-Fi Analyzer app (the meter)
- A laptop to run the logger and the plots
- A box or stand to prop the phones at a steady height

**The turntable**
- The printed 360° protractor (from `visualize_antenna.py`)
- A stiff base — cardboard or plywood, ~30 × 30 cm
- A pivot through the centre — a nail, bolt or pencil
- A small card platform on the pivot to carry the antenna, with a pointer for the angle

**Tools you borrow, not keep**
- Wire cutter or strong scissors, a mm ruler, a marker
- Sandpaper or a nail file to smooth the cut wire ends
- A set square (or the corner of a book) to keep rods straight
- A printer for the protractor

**Optional:** a ~10 cm square of aluminium foil on cardboard behind the reflector
rod sharpens the front-to-back ratio.

---

## Part A — Build the antenna 🔧

You're making **4 straight rods** and sticking them on the boom at **4 marked
spots**. That's genuinely it.

### A0. Getting the copper wire

The blueprint is tuned for **~1.6 mm (14 AWG) solid copper wire** — stiff, single
strand, about as thick as a paperclip.

**Where to get it:**
- Any **hardware / electrical shop** — ask for "14 AWG" or "1.5 sq mm solid copper
  house wire" (sold by the metre, a few rupees).
- A **leftover piece of house mains wiring** — strip the plastic sheath off and the
  single solid copper core inside is almost exactly right.
- An **old thick copper earth/ground wire** from scrap electrical bits.

**If 1.6 mm isn't available — substitutes that still work fine:**
- Anything **solid copper between ~1.0 and 2.0 mm** (roughly 12–18 AWG). The exact
  thickness barely changes the tuning; your ±1–2 mm cut tolerance already covers it.
- **Enamelled "magnet" wire** works if it's thick enough — scrape the enamel off the
  ends where it matters.
- **Brass or even aluminium rod** of similar thickness works electrically; copper is
  just the easiest to cut and shape.

**What to avoid:**
- ❌ **Stranded wire** (lots of thin strands) — it won't hold a straight shape.
- ❌ **Steel** (e.g. a coat hanger) — it's magnetic and a poor conductor; the pattern
  suffers.
- ❌ **Very thin wire** (phone-charger cores, < 0.8 mm) — too floppy to stay straight.

> 💡 If you use a noticeably different diameter, you *can* re-run
> `dimension_calculator.py` after changing `WIRE_DIAMETER_MM` near the top, but for
> a student demo it's not worth it — the lengths shift by well under a millimetre.

### A1. Cut the rods to these lengths

(These are the exact numbers from the blueprint — tip to tip.)

| Rod | Cut length | Easy way to remember |
|---|---|---|
| **Reflector (R)** | **59.0 mm** | the longest |
| **Driven (D)** | **55.6 mm** | cut as **two 27.8 mm arms** (see A3) |
| **Director 1 (D1)** | **52.2 mm** | |
| **Director 2 (D2)** | **50.4 mm** | the shortest |

> Measure twice, cut once. Being off by 1–2 mm is fine; off by 5 mm will visibly
> shift your result.

### A2. Mark the boom and glue the rods on

Measure these distances from **one end** of the boom and mark them. Then glue each
rod **crossways** (perpendicular), centred on its mark, all **parallel** to each
other and lying **flat in the same plane**:

| Spot from the left end | Rod |
|---|---|
| 0 mm | Reflector |
| 24.6 mm | Driven |
| 45.5 mm | Director 1 |
| 70.1 mm | Director 2 |

Leave ~15 mm of spare boom past each end so nothing hangs off the edge
(total boom ≈ 10 cm).

### A3. The feed gap — no wiring needed

The **Driven** element is **two 27.8 mm arms with a ~1 mm gap in the middle** (not
one continuous rod). On the phone path there is **nothing to solder and no cable to
connect** — you just leave the little gap:

```
      arm 1              arm 2
   ──────────── ) ( ────────────
                ^^
          tiny gap here
```

That's it for the electrical side. In Part B you simply place the **measuring
phone right at this gap** — the copper rods focus the signal onto it passively,
so the phone's own Wi-Fi radio does the receiving. No coax, no balun, no solder.

> 📖 **Want the careful, step-by-step build version** (boom prep, mounting,
> common mistakes)? That's already written: see
> [`member3_hardware/assembly_guide.md`](../member3_hardware/assembly_guide.md).
> It also documents an optional soldered coax feed — you can ignore that part for
> the phone path. This section is the quick overview; that file is the full recipe.

---

## Part B — Measure the radiation pattern 📡

**The idea:** keep a Wi-Fi signal coming from a fixed spot, point your antenna at
it, then **rotate the antenna 10° at a time through a full circle (36 steps)** and
write down how strong the signal is each time. Strong when pointed at the source,
weak when pointed away = proof it's directional.

### B1. Set up the "shooting range"

```
  [ Signal source ]                          [ Your Yagi + meter ]
   phone sharing a      ~1.5 metres           measuring phone at the
   2.4 GHz hotspot    ◀───────────────▶       feed gap, on the printed
                                              protractor turntable
```

- Put the **source phone** (sharing a 2.4 GHz hotspot) about **1.5 m away**. Why
  1.5 m? The physics says you must be at least the **far-field distance** away for
  a valid reading — the script computes it (`R > 2D²/λ`, only ~8 cm here, but 1.5 m
  gives comfortable margin).
- Tape your antenna onto the **printed protractor** so you can rotate it in neat
  10° steps. **0° = the direction the directors point** (the main beam).
- Keep both at the same height, with a clear line of sight, away from big metal
  objects and walls as much as you can.

### B2. Record the 36 readings

Run the logger in **manual mode** and follow its prompts — it walks you from 0° to
350° and writes the result file automatically at the end:

```bash
# Type the dBm your Wi-Fi Analyzer app shows at each angle
python member4_telemetry/esp32_rssi_logger/serial_rssi_logger.py --manual

# Just rehearsing, no antenna built yet? Generate a realistic fake sweep:
python member4_telemetry/esp32_rssi_logger/serial_rssi_logger.py --dummy
```

At each angle it waits for you to rotate the antenna and press **Enter**. Read the
signal strength (a negative number like `-46 dBm`) off a free **Wi-Fi Analyzer**
app on the measuring phone and type it in.

When it finishes, it saves your real measurements to `data/empirical_pattern.csv`.
That one file is the bridge back to the software — **it automatically replaces the
virtual (simulated) measurement everyone's been using.** It also stamps the file
as a *physical* measurement, so:

- re-running `run_pipeline.py` later **won't overwrite your real data** (the
  virtual-measurement step sees the stamp and skips itself), and
- the Antenna Studio will label your curve **"Measured (phone sweep)"** instead of
  "Virtual measurement".

---

## Part C — See your result (the payoff) 🎯

Two commands turn your 36 numbers into the money shot:

```bash
# 1) Compare your real pattern against the theory (prints error numbers + a plot)
python member4_telemetry/friis_link_budget.py

# 2) Rebuild and open the Antenna Studio with YOUR data on it
python antenna_studio/build_studio.py
```

The **Antenna Studio** opens in your browser. On its polar plot ("Radiation
pattern, seen from above") your data appears as **green dots labelled "Measured
(phone sweep)"**, on top of the copper live curve, the cyan theory and the pink
simulation. If your green dots make a **big lobe near 0°** and a **dent near
180°**, congratulations — you built a working directional antenna and it agrees
with the physics. 🎉 (What every part of the Studio means: `video_demo_guide.md`,
Section 2.)

`friis_link_budget.py` also prints how close you got: a **front-to-back ratio**
(how much stronger the front is than the back) and an **RMSE** (average
disagreement with theory, in dB — small is good).

> It's normal for the real curve to be a bit lumpier than theory — reflections off
> walls and furniture add wiggles. As long as the main beam points the right way,
> that's a success and a great thing to explain on your slides.

---

## Part D — Film it and finish the slides 🎬

- **Video (≤ 5 min, < 75 MB):** follow [`video_demo_guide.md`](video_demo_guide.md).
  With real hardware, add a 15–20 s clip of you turning the copper antenna on the
  protractor, then show your green "Measured" dots in the Studio. Say "we measured
  it for real" instead of "simulated measurement".
- **Slides 13–15 (your section):** Experimental Setup (the 1.5 m range photo),
  Observations (your overlay graph + the front-to-back number), and Conclusion
  (did real life match the math? by how much?).

---

## Quick checklist

- [ ] Gathered every component (Section 5 — wire, boom, tape/glue, protractor, pivot, 2 phones)
- [ ] Printed the blueprint + protractor (Part 4)
- [ ] Cut 4 rods: 59.0 / 55.6 / 52.2 / 50.4 mm
- [ ] Glued them at 0 / 24.6 / 45.5 / 70.1 mm on a **non-metal** boom
- [ ] Driven element split into two 27.8 mm arms with a small gap
- [ ] Source placed ~1.5 m away, antenna on the protractor, 0° = toward directors
- [ ] Logged 36 readings → `data/empirical_pattern.csv` written
- [ ] Ran `friis_link_budget.py` and rebuilt the Studio (`antenna_studio/build_studio.py`)
- [ ] Recorded the video + did slides 13–15

## One-page command cheat sheet

```bash
# (use the Python 3.12 full path if plain 'python' can't find numpy)

# Before building:
python member3_hardware/dimension_calculator.py     # cut lengths + BOM
python member3_hardware/visualize_antenna.py         # diagrams + protractor to print

# After building, measure (phone path — type dBm at each angle):
python member4_telemetry/esp32_rssi_logger/serial_rssi_logger.py --manual

# See the result:
python member4_telemetry/friis_link_budget.py        # real vs theory, numbers + plot
python antenna_studio/build_studio.py                # Studio with your "Measured" curve

# Safe to re-run everything later - your real data is kept:
python run_pipeline.py --studio
```

---

**Need more detail on any step?**
- Full build recipe → [`member3_hardware/assembly_guide.md`](../member3_hardware/assembly_guide.md)
- Optional ESP32 route (not needed for the phone path) → [`member4_telemetry/esp32_rssi_logger/README.md`](../member4_telemetry/esp32_rssi_logger/README.md)
- The project in plain words → [`docs/project_explained_simply.md`](project_explained_simply.md)
- Current status & what's done → [`PROJECT_STATUS.md`](../PROJECT_STATUS.md)
