# Software-Only Fallback — Plan & How to Present It Honestly

*What we do if the physical antenna can't be built/measured in time.*

> **Status:** implemented and runnable today. The whole pipeline produces a
> Theory vs Simulation vs **Virtual-Measurement** overlay with no hardware.

---

## 1. The idea in one line

Instead of cutting copper and spinning it with a phone, we **measure the antenna
inside the computer**: design it as a CAD/geometry model, run a full-wave
simulation, and perform a *virtual turntable sweep* to produce the "measured"
radiation pattern.

## 2. The three curves (the validation story)

| Curve | Where it comes from | Method |
|---|---|---|
| **Theory** | Lead's `antenna_math_engine.py` | Analytical array theory + induced-EMF |
| **Simulation** | Member 2 `simulate_yagi.py` from `yagi_4el_244GHz.nec` | Full-wave / Method of Moments |
| **Virtual Measurement** | `member4_telemetry/virtual_measurement.py` | Software turntable sweep of the simulated antenna |

Theory and Simulation use **genuinely different maths**, so their agreement is a
real cross-check — exactly how antenna engineers validate a design before
building it. The virtual measurement then shows what a clean real-world sweep of
that design would look like (ripple, receiver noise, quantisation, pointing error).

Current result: all three peak at **0°** (main beam toward the directors) with a
**~10–11 dB front-to-back ratio**, and the virtual measurement sits ~1.2 dB RMS
from theory — a realistic, believable spread.

## 3. What is "CAD" here

For antennas, "CAD" = the **geometry model the simulator solves**, not a
mechanical drawing. It already exists:

- `EMT_Member2/yagi_4el_244GHz.nec` — the NEC geometry (4 wires, lengths,
  spacings, feed, copper loading). **This is the antenna CAD model.**
- **The Antenna Studio** (`antenna_studio/antenna_studio.html`) — the same
  geometry as a live, rotatable 3D model whose physics is re-solved as you change
  it. This is what the demo video shows.
- `EMT_Member2/yagi_3d_structure.png` and `member3_hardware/visualize_antenna.py`
  — static 3D renders for the slides.

## 4. How to run it

```bash
python run_pipeline.py            # regenerates all three CSVs + plots + the Studio
python run_pipeline.py --studio   # ...then opens the Antenna Studio
```

Just the measurement leg:

```bash
python member4_telemetry/virtual_measurement.py          # default seed (2440)
python member4_telemetry/virtual_measurement.py --seed 7 # reproducible variant
```

Outputs:
- `data/empirical_pattern.csv` — the virtual-measurement curve (universal format)
- `data/empirical_pattern.provenance.txt` — a stamp recording it is simulated
- `member4_telemetry/output/virtual_measurement_preview.png` — polar preview

The Studio also has its own **"Run virtual measurement"** button that performs
the same kind of sweep live on screen (the antenna turns on a turntable and the
points appear one by one). That's the version to show in the video.

> If someone later does a real phone sweep, `serial_rssi_logger.py` stamps the
> CSV as a *physical* measurement. After that this script will not overwrite it
> (use `--force` if you really want to), and the Studio labels the curve
> "Measured" instead of "Virtual measurement".

## 5. Slide/video mapping (what replaces the hardware deliverables)

| Rubric item (was hardware) | Software replacement |
|---|---|
| Components | Studio 3D view + dimension/BOM table (virtual components) |
| Assembly | Studio 3D view (rotate it) + annotated 3D geometry with lengths & spacings |
| Prototype demo | The Studio itself: live 3D antenna, beam, gain/F-B/VSWR, plus the Smith chart |
| Experimental data | Live virtual turntable sweep in the Studio → the "measurement" curve |
| Demo video | Screen recording of the Studio, scripted in `video_demo_guide.md` |

## 6. The honesty rules (important — this is graded)

1. **Label it as simulated.** The curve is "Virtual measurement," never
   "measured in lab." The Studio's legend, its measurement summary ("Simulated
   measurement, not lab data") and the provenance file already say so.
2. **State the reason plainly** in the report: *"physical build omitted due to
   component/time constraints; the design is validated across two independent
   solvers and a simulated measurement."* Evaluators respect an honest, reasoned
   gap far more than a vague or faked one.
3. **Do not invent lab photos or claim a physical sweep happened.**

> Reminder: our evaluators **strongly expect** a physical prototype, so this stays
> the backup. Even a rough same-day local build (copper wire + stick + two phones,
> no delivery needed) would recover marks this path cannot. Use this plan only if
> the build truly isn't possible in time.
