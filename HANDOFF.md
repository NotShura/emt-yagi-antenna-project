# Project Handoff — 2.44 GHz Yagi-Uda Antenna (EC-3104)

**Prepared for:** Project Lead & team
**As of:** 2026-10-31
**Contributor:** NotShura (implemented the Lead, Member 1, Member 2, and Member 3 software parts)

This is the current state of the project. The source is in this repo, already
committed to `main` (git). See [`README.md`](README.md) for structure, setup,
and the team workflow, and the full brief in
[`emt_project_master_context_handoff_document.md`](emt_project_master_context_handoff_document.md).

---

## ✅ Done (software complete & integrated)

### Project Lead + Member 1 — `Electromagnetic-Theory-Member-1-main/`
- Analytical EM engine (`antenna_math_engine.py`): element factor, N-element
  array factor with amplitude tapering, induced-EMF mutual impedance matrix
  (Z₁₁/Z₁₂), driving-point impedance, directivity D₀, HPBW, VSWR/S₁₁.
- Interactive GUI (`antenna_gui.py`): **live 2D polar + live 3D spherical**
  patterns, sliders (N, d/λ, β), Dolph-Chebyshev/Binomial tapers, Schelkunoff
  null-steering, and the Theory-vs-Sim-vs-Empirical overlay.
- Fixed a latent crash in the GUI's import-fallback path.
- Owns slides 1–6 (Title, Abstract, Working Principle, Math, Architecture, Beamforming).

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
- Member 2 → `simulated_pattern.csv` (universal `angle_deg,gain_dBi`, 36 rows) feeds
  Member 1's overlay; a copy is already in the Member 1 folder.
- Member 2 → `optimized_dimensions.json` is the **single source of truth** for
  element lengths/spacings; Member 3 reads it automatically.

---

## ⏳ Pending

| Item | Owner | Notes |
|---|---|---|
| Synthetic CSV generator, Friis link-budget, ESP32 RSSI firmware | **Member 4** | Software not started |
| `empirical_pattern.csv` (real 360° RSSI sweep) | **Member 4** | Needs the physical build first |
| H_φ field + Poynting-vector functions in the engine | **Lead** | Minor; abstract mentions them but code doesn't expose them yet |
| Physical Yagi build + balun + turntable + field measurements | **Members 3 & 4** | Deferred to final days by design (software-first plan) |
| Second full-wave solver (openEMS / HFSS) | **Member 2** | Optional; only 4nec2 done so far |
| Push to the shared GitHub repo | Lead to create repo + add `NotShura` | Local `main` is ready to push |

---

## How to run (after `pip install -r requirements.txt`)

```bash
python Electromagnetic-Theory-Member-1-main/antenna_gui.py     # interactive dashboard
python EMT_Member2/simulate_yagi.py                            # sim pattern + Smith chart + integration files
python EMT_Member2/build_pdf_report.py                         # rebuild Member 2 PDF (needs reportlab)
python member3_hardware/dimension_calculator.py                # cutting blueprint
python member3_hardware/visualize_antenna.py                   # assembly diagrams + protractor
```

Tested with: numpy 2.4.6, matplotlib 3.11.0 (Anaconda) for the simulation/plots;
reportlab 5.0.1 (Python 3.12) for the PDF.

---

## Getting this into the shared repo
1. Create an **empty** GitHub repo (no README/.gitignore — this repo already has them).
2. Add collaborator **`NotShura`** (and the rest of the team).
3. Owner of the local copy runs:
   ```bash
   git remote add origin <REPO_URL>
   git push -u origin main
   ```
All committed work (now including this handoff) lands on `main`.
