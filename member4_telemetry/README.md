# Member 4 — Telemetry, Field Testing & Video

*Folder reserved — nothing implemented yet.*

Planned contents (see the master context document, section 4.5):

- Synthetic noisy CSV generator (theoretical Yagi pattern + ±1.5 dB Gaussian noise)
- Fraunhofer distance and Friis link-budget calculator
- ESP32 / smartphone RSSI logger for the 360° turntable sweep

## How it plugs into the rest of the project

Write results to the shared folder through `emt_config.py`, like the other members:

```python
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from emt_config import THEORETICAL_CSV, EMPIRICAL_CSV
```

- **Read** `data/theoretical_pattern.csv` as the base for the synthetic dataset.
- **Write** `data/empirical_pattern.csv` in the universal format: header
  `angle_deg,gain_dBi`, 36 rows from 0 to 350 in 10° steps, with
  **0° = main beam (toward the directors)** and 180° = reflector side.

Member 1's GUI picks the file up automatically in its overlay plot.
