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
- `EMT_Member2/yagi_3d_structure.png` and `member3_hardware/visualize_antenna.py`
  — 3D renders for the slides.

## 4. How to run it

```bash
python run_pipeline.py          # regenerates all three CSVs + plots
python run_pipeline.py --gui    # ...then opens the overlay dashboard
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

## 5. Slide/video mapping (what replaces the hardware deliverables)

| Rubric item (was hardware) | Software replacement |
|---|---|
| Components | 3D CAD render + dimension/BOM table (virtual components) |
| Assembly | Annotated 3D geometry showing lengths & spacings |
| Prototype demo | Full-wave simulation: pattern, VSWR/S₁₁, Smith chart |
| Experimental data | Virtual turntable sweep → the "measurement" curve |
| Demo video | Screen recording of the GUI overlay + simulation walkthrough |

## 6. The honesty rules (important — this is graded)

1. **Label it as simulated.** The curve is "Virtual Measurement," never
   "measured in lab." The GUI legend and the provenance file already say so.
2. **State the reason plainly** in the report: *"physical build omitted due to
   component/time constraints; the design is validated across two independent
   solvers and a simulated measurement."* Evaluators respect an honest, reasoned
   gap far more than a vague or faked one.
3. **Do not invent lab photos or claim a physical sweep happened.**

> Reminder: our evaluators **strongly expect** a physical prototype, so this stays
> the backup. Even a rough same-day local build (copper wire + stick + two phones,
> no delivery needed) would recover marks this path cannot. Use this plan only if
> the build truly isn't possible in time.
