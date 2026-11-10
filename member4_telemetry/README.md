# Member 4 — Telemetry, Field Testing & Video

RF telemetry and empirical validation for the 2.44 GHz Yagi-Uda array:
synthetic data so the software overlay works before the build, the link-budget
math for a valid far-field measurement, and the ESP32/phone RSSI toolkit for
the real 360° sweep.

## Contents

| File | Purpose |
|---|---|
| [`generate_synthetic.py`](generate_synthetic.py) | Reads the theoretical pattern, adds a realistic ±1.5 dB measurement noise model, and writes a **placeholder** `data/empirical_pattern.csv` so Member 1's overlay works immediately |
| [`friis_link_budget.py`](friis_link_budget.py) | Fraunhofer far-field distance `R = 2D²/λ`, Friis link budget (`Pr = Pt + Gt + Gr − FSPL`), and empirical-vs-theoretical error analysis (RMSE, F/B, HPBW) |
| [`esp32_rssi_logger/`](esp32_rssi_logger/) | Two ESP32 sketches (beacon TX + RSSI RX) and a PySerial logger that writes the **real** `data/empirical_pattern.csv` from a field sweep |
| `output/` | Generated preview/link-budget PNGs (created on first run) |

## How it plugs into the rest of the project

Everything is read/written through `emt_config.py`, like the other members:

```python
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from emt_config import THEORETICAL_CSV, EMPIRICAL_CSV
```

- **Reads** `data/theoretical_pattern.csv` (Lead) as the base for synthetic data,
  and `data/optimized_dimensions.json` (Member 2) for antenna geometry.
- **Writes** `data/empirical_pattern.csv` in the universal format: header
  `angle_deg,gain_dBi`, 36 rows from 0° to 350° in 10° steps, with
  **0° = main beam (toward the directors)** and 180° = reflector side.

Member 1's GUI picks the file up automatically in its overlay plot.

## Quick start

```bash
# 1. Software-first: placeholder empirical data + link budget (no hardware)
python member4_telemetry/generate_synthetic.py
python member4_telemetry/friis_link_budget.py

# 2. After the physical build: real field sweep (replaces the placeholder)
pip install pyserial
python member4_telemetry/esp32_rssi_logger/serial_rssi_logger.py --port COM5
#   ...or, with no ESP32, a phone Wi-Fi analyser:
python member4_telemetry/esp32_rssi_logger/serial_rssi_logger.py --manual

# 3. Re-run the error analysis against the real data
python member4_telemetry/friis_link_budget.py
```

`python run_pipeline.py` runs steps 1 automatically (synthetic data + link
budget); the real sweep in step 2 is run by hand during the build.

## Slides owned

13–15: Experimental Setup, Observations / Error Analysis, Conclusion.
