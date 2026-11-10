# Project Status Summary — 2.4 GHz Yagi-Uda Antenna Array
**Course:** EC-3104 Electromagnetic Theory  
**Deadline:** 15 Nov 2026 (report) · 16 Nov 2026 (showcase)  
**Last updated:** 7 Nov 2026  

---

## What This Project Is

A 5-member team capstone to **design, simulate, build, and test a 4-element 2.44 GHz Yagi-Uda antenna** with real-time beamforming and null-steering.

- **~85% Software** — Custom Python CEM solver + interactive GUI + 4nec2 full-wave simulation  
- **~15% Hardware** — Low-cost copper-wire prototype + ESP32/smartphone RSSI measurements  
- **Budget:** ₹850 (or ₹400 with smartphones instead of ESP32s)

---

## Architecture — How Everything Connects

```
EMT_Member2/simulate_yagi.py
    ├──► data/optimized_dimensions.json ──► Lead engine (Yagi solver)
    │                                  └──► member3_hardware (blueprint)
    └──► data/simulated_pattern.csv ──┐
Lead antenna_math_engine.py            │
    └──► data/theoretical_pattern.csv ──┼──► Member 1 GUI overlay
Member 4 (RSSI sweep)                  │
    └──► data/empirical_pattern.csv ──┘    ← Member 4 (synthetic now; real after sweep)
```

All shared files live in `data/`. Constants and paths defined once in `emt_config.py`.

---

## Overall Completion: ~85%

| Component               | Owner    | Lines | Status         |
|--------------------------|----------|-------|----------------|
| Analytical EM Solver     | Lead     | 638   | ✅ 100%        |
| Beamforming GUI          | Member 1 | 634   | ✅ 100%        |
| Full-wave Sim + PDF      | Member 2 | 817   | ✅ 100%        |
| Hardware Blueprints (SW) | Member 3 | 1,382 | ✅ 100%        |
| Telemetry & Testing (SW) | Member 4 | 807   | ✅ 100%        |
| Integration / Pipeline   | Shared   | 153   | ✅ 95%         |
| Physical Build           | M3 + M4  | —     | ❌ Not started |
| PPT + Demo Video         | All      | —     | ❌ Not started |

**Total Python code written:** 4,048 lines across 11 files (+138 lines ESP32 Arduino) · **Zero TODOs or stubs found**

---

## Detailed Breakdown

### ✅ Lead — `Electromagnetic-Theory-Member-1-main/antenna_math_engine.py` (638 lines)

Fully implements from first principles:
- **Radiation integrals:** I(z) → A_z → E_θ, H_φ → Poynting vector → P_rad / R_rad  
- **Validation:** λ/2 dipole gives R_rad = 73.13 Ω (textbook: 73.08 Ω)  
- **N-element ULA:** Array factor with Dolph-Chebyshev & Binomial tapers  
- **Directivity & HPBW:** Full-sphere numerical integration  
- **Mutual impedance:** Induced-EMF method, Z matrix for unequal-length elements  
- **4-element Yagi solver:** Reads `optimized_dimensions.json`, solves [Z][I]=[V] for parasitic currents, computes 3D far field  
- **Results:** D₀ = 9.47 dBi, F/B = 10.5 dB, HPBW = 80°(H)/58°(E), Z_in = 30.1+j0.9 Ω  
- **VSWR sweep:** VSWR < 2 from 2.41–2.59 GHz  
- **Planar array:** Nx×Ny beam steering  
- **Output:** `data/theoretical_pattern.csv` + comparison plots  

---

### ✅ Member 1 — `Electromagnetic-Theory-Member-1-main/antenna_gui.py` (634 lines)

Interactive matplotlib + tkinter dashboard:
- Live **2D polar** + **3D spherical** radiation patterns  
- Sliders: N elements, d/λ spacing, β phase shift  
- Taper selection: Uniform / Chebyshev 30 dB / Binomial  
- **Schelkunoff null-steering** with polynomial root placement  
- **Theory vs Sim vs Empirical overlay** from `data/` CSVs  
- "Update Theory CSV" button re-runs Yagi solver live  
- Array mode switching: Linear ULA / Planar NxN  

---

### ✅ Member 2 — `EMT_Member2/` (817 lines total)

**`simulate_yagi.py` (354 lines):**
- Frozen 4nec2 geometry + simulated metrics  
- Writes `data/optimized_dimensions.json` (single source of truth)  
- Writes `data/simulated_pattern.csv` (36-row azimuth cut)  
- Smith chart with impedance locus, VSWR=2 circle, resonance marker  
- S₁₁/VSWR dual-axis frequency sweep  
- RLC equivalent circuit model  
- 3D wireframe structure visualization  

**`build_pdf_report.py` (463 lines):**
- Professional 5-section PDF via reportlab  
- Embeds all generated PNGs  
- IEEE-style slide content for slides 7–9  

**Simulated metrics:** Z_in = 48.74+j2.2 Ω, S₁₁ = −31.81 dB, VSWR = 1.053, D₀ = 8.50 dBi, F/B = 21 dB, BW = 160 MHz

**Generated outputs:** `smith_chart.png`, `s11_vswr_response.png`, `radiation_pattern_polar.png`, `circuit_schematic_detailed.png`, `yagi_3d_structure.png`, `yagi_antenna_blueprint.png`, `simulated_pattern_preview.png`, PDF report

---

### ✅ Member 3 — `member3_hardware/` (1,382 lines total)

**`dimension_calculator.py` (367 lines):**
- Auto-loads Member 2's optimized dimensions (with textbook fallbacks)  
- Computes cutting blueprint with wire specs, balun lengths, far-field distance  
- Formatted workshop output with ASCII boom diagram  
- BOM with cost estimates  

**`balun_calculator.py` (350 lines):**
- Three feed options: Pawsey stub, bazooka/sleeve, passive wave-launcher  
- Impedance matching analysis: Γ, VSWR, return loss, mismatch loss  
- Supports RG174, RG316, RG58, RG402 coax types  

**`visualize_antenna.py` (375 lines):**
- 3D assembly diagram with element labels, boom, feedpoint, balun stub  
- 2D side-view engineering drawing with spacing annotations  
- Printable 360° protractor template (5° minor / 10° major ticks)  

**`assembly_guide.md` (290 lines):**
- Step-by-step physical build instructions  
- Tools needed, common mistakes, pre-test checklist  

**Generated outputs:** `antenna_3d_assembly.png`, `antenna_side_view.png`, `protractor_template.png`, `balun_designs.json`, `antenna_dimensions.json`

---

### ✅ Member 4 — `member4_telemetry/` (807 Python + 138 Arduino lines)

Software complete and wired into the pipeline. Only the real field sweep
(needs the physical antenna) and the demo video remain.

| File | Purpose | Status |
|---|---|---|
| `generate_synthetic.py` (264) | Reads theoretical pattern, adds a realistic ±1.5 dB noise model (Gaussian + boresight bias + 1 dB RSSI quantisation + RX floor) → placeholder `data/empirical_pattern.csv` + preview PNG | ✅ Done |
| `friis_link_budget.py` (314) | Fraunhofer distance `R = 2D²/λ`, Friis link budget, empirical-vs-theory error analysis (RMSE, F/B, HPBW) + figure | ✅ Done |
| `esp32_rssi_logger/beacon_tx.ino` (68) | ESP32 SoftAP + UDP beacon on channel 7 (≈2.442 GHz) | ✅ Done |
| `esp32_rssi_logger/rssi_rx.ino` (70) | ESP32 RSSI receiver streaming `RSSI,<dBm>` over serial | ✅ Done |
| `esp32_rssi_logger/serial_rssi_logger.py` (229) | 360° sweep logger: `--port` (ESP32), `--manual` (phone analyser), `--dummy` → writes the universal-format CSV | ✅ Done |
| `data/empirical_pattern.csv` | Real 360° RSSI measurement data | ⏳ Placeholder (synthetic) until field sweep |

**Verified:** `python run_pipeline.py` runs all 8 steps `ok`; empirical CSV = 36 rows, universal format; peak F/B ≈ 11 dB vs theory 10.5 dB, pattern-shape RMSE ≈ 1.0 dB.

---

### ✅ Integration Layer

| File | Lines | Purpose |
|---|---|---|
| `emt_config.py` | 60 | Design constants (f₀=2.44 GHz, λ, Z₀=50 Ω) + shared paths + `load_dimensions()` |
| `run_pipeline.py` | 80 | Runs all scripts in dependency order: M2 → M3 → Lead → PDF. Supports `--gui` |
| `requirements.txt` | 11 | numpy ≥1.26, scipy ≥1.12, matplotlib ≥3.8, reportlab ≥4.0 |

**Data contracts:**
- Universal CSV format: `angle_deg,gain_dBi` — 36 rows (0°–350° in 10° steps)  
- `data/optimized_dimensions.json` is the single source of truth for antenna geometry  

---

## Known Discrepancy: Analytical vs Full-Wave

| Parameter | Lead (Induced EMF) | Member 2 (4nec2 MoM) | Reason |
|---|---|---|---|
| Z_in | 30.1 + j0.9 Ω | 48.74 + j2.2 Ω | Sinusoidal current assumption vs actual MoM currents |
| D₀ | 9.47 dBi | 8.50 dBi | Same — back/side lobes sensitive to current accuracy |
| F/B | 10.5 dB | 21.0 dB | Back lobe most affected |

Main lobe shapes agree well. This is expected and worth one slide sentence.

---

## What Remains To Do

### 🔴 Critical (Blocks Submission)

| # | Task | Owner | Est. Effort |
|---|---|---|---|
| ~~1~~ | ~~Write `generate_synthetic.py`~~ — ✅ done | Member 4 | — |
| ~~2~~ | ~~Write `friis_link_budget.py`~~ — ✅ done | Member 4 | — |
| 3 | Physical Yagi build — cut wire, mount on boom, attach balun | Members 3+4 | ~3 hours |
| 4 | 360° RSSI field sweep → `data/empirical_pattern.csv` (logger ✅ ready) | Member 4 | ~2 hours |
| 5 | Record 5-minute demo video (< 75 MB) | Member 4 | ~2 hours |
| 6 | Create 15-slide PPT per rubric | All | ~3 hours |

### 🟡 Medium Priority

| # | Task | Owner |
|---|---|---|
| ~~7~~ | ~~ESP32 RSSI firmware~~ — ✅ done (`esp32_rssi_logger/`, + `--manual` phone mode) | Member 4 |
| 8 | Add one slide sentence explaining analytical vs MoM differences | Lead + M2 |

### 🟢 Optional / Nice-to-Have

| # | Task | Owner |
|---|---|---|
| 9 | Second full-wave solver (openEMS / HFSS) | Member 2 |
| 10 | Add teammates as GitHub collaborators | Repo owner |

---

## How To Run

```bash
pip install -r requirements.txt

# Run everything in dependency order
python run_pipeline.py              # add --gui to open dashboard at the end

# Or run individual scripts
python EMT_Member2/simulate_yagi.py                            # sim pattern + Smith chart
python Electromagnetic-Theory-Member-1-main/antenna_math_engine.py   # theory CSV + plots
python Electromagnetic-Theory-Member-1-main/antenna_gui.py     # interactive dashboard
python member3_hardware/dimension_calculator.py                 # cutting blueprint
python member3_hardware/balun_calculator.py                     # balun designs
python member3_hardware/visualize_antenna.py                    # assembly diagrams
python EMT_Member2/build_pdf_report.py                         # PDF report (needs reportlab)
```

**Tested with:** Python 3.14, numpy 2.4.6, scipy 1.18.0, matplotlib 3.11.0, reportlab 5.0.1

---

## Slide Ownership

| Slides | Owner | Topic |
|---|---|---|
| 1–4 | Lead | Title, Abstract, Working Principle, Math |
| 5–6 | Member 1 | Software Architecture, Beamforming Results |
| 7–9 | Member 2 | Circuit Model, Design Steps, Sim Results |
| 10–12 | Member 3 | Components, Assembly, Prototype |
| 13–15 | Member 4 | Experimental Setup, Observations, Conclusion |

---

## Timeline

⏰ **9 days remaining** until report submission (15 Nov)  
⏰ **10 days remaining** until evaluation showcase (16 Nov)  
📊 **~12–15 hours** of work left — easily achievable  

The software-first strategy worked. All computation is solid, and **Member 4's code is now complete** (synthetic data + link budget + ESP32/phone sweep logger, all wired into `run_pipeline.py`). Critical path is now purely physical: **build → measurements (run the ready logger) → video → PPT.**

