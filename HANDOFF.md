# Project Handoff — 2.44 GHz Yagi-Uda Antenna (EC-3104)

**Prepared for:** Project Lead & team
**As of:** 2026-11-03
**Project Lead:** mohima31 (Mohi), took over from NotShura
**Original handover:** NotShura (former lead) implemented the initial Lead, Member 1, Member 2, and Member 3 software parts

This is the current state of the project. The source is in this repo, already
committed to `main` (git). See [`README.md`](README.md) for structure, setup,
and the team workflow, and the full brief in
[`emt_project_master_context_handoff_document.md`](emt_project_master_context_handoff_document.md).

---

## ✅ Done (software complete & integrated)

### Project Lead — `Electromagnetic-Theory-Member-1-main/antenna_math_engine.py` — 100%
- Radiation integrals from first principles: I(z) → A_z → E_θ, H_φ → Poynting
  vector → P_rad / R_rad (λ/2 check: 73.13 Ω vs textbook 73.08 Ω).
- N-element ULA: element factor, array factor with tapers, D₀ and HPBW
  (taper-aware), induced-EMF Z matrix, Z_in from the full [Z][I]=[V] solve,
  active (scan) impedance.
- **4-element Yagi solver** reading `data/optimized_dimensions.json`: general
  induced-EMF Z for unequal lengths (wire-radius self terms), parasitic
  currents, 3D far field, D₀ 9.47 dBi, F/B 10.5 dB, HPBW 80° (H) / 58° (E),
  Z_in 30.1 + j0.9 Ω, VSWR < 2 from 2.41–2.59 GHz (physics-based sweep).
  Poynting-integrated P_rad matches circuit input power within 0.12 %.
- Writes the Yagi H-plane theory to `data/theoretical_pattern.csv`, plus
  `yagi_theory_vs_sim.png` comparing it with Member 2's pattern.

### Member 1 — `Electromagnetic-Theory-Member-1-main/antenna_gui.py`
- Interactive GUI (`antenna_gui.py`): **live 2D polar + live 3D spherical**
  patterns, sliders (N, d/λ, β), Dolph-Chebyshev/Binomial tapers, Schelkunoff
  null-steering, and the Theory-vs-Sim-vs-Empirical overlay.
- Fixed a latent crash in the GUI's import-fallback path.
- Overlay reads all CSVs from `data/`; "Update Theory CSV" regenerates the Yagi theory.
- Lead owns slides 1–4 (Title, Abstract, Working Principle, Math); Member 1
  owns slides 5–6 (Architecture, Beamforming).

### Member 2 — `EMT_Member2/` — 100%
- `yagi_4el_244GHz.nec` 4nec2 model (2.0–3.0 GHz sweep, center feed, free space).
- `simulate_yagi.py`: exports the integration files + Smith chart + pattern preview.
- **Smith chart added** (`smith_chart.png`) — was missing, is rubric-required — and
  embedded into the regenerated PDF report.
- S₁₁/VSWR plot, RLC circuit model, full PDF report (slides 7–9).

### Member 3 — `member3_hardware/` — software side 100%
- `dimension_calculator.py` (now auto-loads Member 2's optimized dimensions),
  `balun_calculator.py`, `visualize_antenna.py` (3D/2D diagrams + protractor),
  `assembly_guide.md`, BOM. Owns slides 10–12.

### Cross-member integration
- All shared files live in `data/`; constants and paths are defined once in
  `emt_config.py`; no more copied CSVs; every script runs from any folder.
- Member 2 → `data/optimized_dimensions.json` is the **single source of truth**
  for element lengths/spacings; the Lead's Yagi solver and Member 3 read it.
- Member 2 → `data/simulated_pattern.csv` and Lead → `data/theoretical_pattern.csv`
  feed Member 1's overlay.
- `python run_pipeline.py` regenerates everything in dependency order.
- One `requirements.txt` at the root.

---

## ⏳ Pending

| Item | Owner | Notes |
|---|---|---|
| Synthetic CSV generator, Friis link-budget, ESP32 RSSI firmware | **Member 4** | Software not started; `member4_telemetry/README.md` describes the interface |
| `data/empirical_pattern.csv` (real 360° RSSI sweep) | **Member 4** | Needs the physical build first |
| Review theory vs 4nec2 differences (Z_in 30 vs 49 Ω, F/B 10.5 vs 21 dB) | **Lead + Member 2** | Main lobes agree; induced EMF assumes sinusoidal currents, so some gap is expected — worth one slide sentence |
| Physical Yagi build + balun + turntable + field measurements | **Members 3 & 4** | Deferred to final days by design (software-first plan) |
| Second full-wave solver (openEMS / HFSS) | **Member 2** | Optional; only 4nec2 done so far |
| Add teammates to the GitHub repo | Repo owner | Repo exists (private); add `NotShura` and the rest of the team as collaborators |

---

## How to run (after `pip install -r requirements.txt`)

```bash
python run_pipeline.py                                         # everything, in order
python Electromagnetic-Theory-Member-1-main/antenna_math_engine.py   # Lead: theory CSV + plots
python Electromagnetic-Theory-Member-1-main/antenna_gui.py     # interactive dashboard
python EMT_Member2/simulate_yagi.py                            # sim pattern + Smith chart + integration files
python EMT_Member2/build_pdf_report.py                         # rebuild Member 2 PDF (needs reportlab)
python member3_hardware/dimension_calculator.py                # cutting blueprint
python member3_hardware/visualize_antenna.py                   # assembly diagrams + protractor
```

Tested with: Python 3.14, numpy 2.4.6, scipy 1.18.0, matplotlib 3.11.0 (Anaconda)
for the pipeline; reportlab 5.0.1 (Python 3.12) for the PDF.

---

## Shared repo
The project is on GitHub as `mohima31/emt_project` (private). The owner adds
**`NotShura`** and the rest of the team under *Settings → Collaborators*; each
member then runs `git clone https://github.com/mohima31/emt_project.git`.
