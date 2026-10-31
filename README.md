# 2.4 GHz Directive Phased & Parasitic Antenna Array
### EC-3104 Electromagnetic Theory — Team Capstone Project

Design, computational modeling, and experimental validation of a 2.44 GHz
4-element Yagi-Uda array with real-time beamforming and null-steering. The
project is **~85% software** (custom CEM solver + interactive GUI + full-wave
simulation) and **~15% low-cost hardware** validation.

> Full background, rubric, timeline, and task split: see
> [`emt_project_master_context_handoff_document.md`](emt_project_master_context_handoff_document.md)
> and the plain-language overview in [`docs/project_explained_simply.md`](docs/project_explained_simply.md).

---

## Repository layout

| Folder | Owner | Contents |
|---|---|---|
| [`Electromagnetic-Theory-Member-1-main/`](Electromagnetic-Theory-Member-1-main/) | **Project Lead + Member 1** | Analytical EM engine (`antenna_math_engine.py`) and interactive beamforming GUI (`antenna_gui.py`) |
| [`EMT_Member2/`](EMT_Member2/) | **Member 2** | 4nec2 model (`yagi_4el_244GHz.nec`), simulation export (`simulate_yagi.py`), Smith chart, PDF report builder |
| [`member3_hardware/`](member3_hardware/) | **Member 3** | Cutting-dimension & balun calculators, 3D assembly diagrams, protractor template, assembly guide |
| `member4_telemetry/` | **Member 4** | *(to be added)* synthetic CSV generator, Friis link-budget, ESP32 RSSI firmware |
| [`docs/`](docs/) | Shared | Project explainer and supporting docs |

---

## Quick start

```bash
git clone <REPO_URL>
cd emt_project
pip install -r requirements.txt
```

Run any member's deliverable, e.g.:

```bash
python EMT_Member2/simulate_yagi.py                 # sim pattern + Smith chart + integration files
python Electromagnetic-Theory-Member-1-main/antenna_gui.py   # interactive dashboard
python member3_hardware/dimension_calculator.py     # cutting blueprint
```

> Member 2's PDF builder needs `reportlab` (included in `requirements.txt`).

---

## How the members' work connects (data contracts)

Everything integrates through two shared, machine-readable interfaces:

1. **Universal radiation-pattern CSV** — `angle_deg,gain_dBi`, 36 rows (0°–350° in 10° steps):
   - `theoretical_pattern.csv` — produced by the Lead's engine (Member 1 folder)
   - `simulated_pattern.csv` — produced by `EMT_Member2/simulate_yagi.py`
   - `empirical_pattern.csv` — produced by Member 4 from the RSSI sweep
   - Member 1's GUI overlays all three on one polar plot.

2. **Optimized dimensions** — `EMT_Member2/optimized_dimensions.json` is the
   **single source of truth** for element lengths/spacings. Member 3's
   `dimension_calculator.py` loads it automatically for the cutting blueprint.

If you change a design constant (frequency, element count, spacing), regenerate
the affected CSV/JSON so the other members stay in sync.

---

## Team workflow (how to contribute)

Each member works primarily in **their own folder**, so day-to-day changes rarely collide.

1. Get the latest before you start:
   ```bash
   git pull
   ```
2. Work on your own branch (recommended), named after your role:
   ```bash
   git checkout -b member2            # e.g. member1, member2, member3, member4, lead
   # ... edit files in your folder ...
   git add EMT_Member2/
   git commit -m "Member 2: add frequency-sweep smith chart"
   git push -u origin member2
   ```
3. Open a Pull Request on GitHub to merge your branch into `main` (lets the team review), **or** if your team prefers, push small changes straight to `main`:
   ```bash
   git checkout main && git pull && git push
   ```

### Ground rules
- **Only edit your own folder** unless you've agreed otherwise — it avoids merge conflicts.
- **Pull before you push.** If a push is rejected, run `git pull --rebase`, resolve, then push again.
- Don't commit `__pycache__/`, virtual envs, or editor files — they're already in `.gitignore`.
- Generated outputs (PNGs, CSVs, PDF) **are** tracked so the team sees results without re-running.

---

## Members & slide ownership

| Role | Focus | PPT slides |
|---|---|---|
| Project Lead | Analytical EM solver & integration | Title, Abstract, Working Principle, Math |
| Member 1 | Beamforming GUI & null-steering | Software Architecture, Beamforming Results |
| Member 2 | Full-wave simulation & S-parameters | Circuit Model, Design Steps, Sim Results |
| Member 3 | Hardware fabrication & mechanical rig | Components, Assembly, Prototype |
| Member 4 | Telemetry, field testing & video | Experimental Setup, Observations, Conclusion |
