# ==============================================================================
# emt_config.py
# Shared design constants and file locations for the whole team.
# ==============================================================================
# Every member's script imports this file so that:
#   - design-freeze constants (f0, lambda, Z0, ...) are defined in ONE place
#   - all files exchanged between members live in ONE folder: data/
#   - scripts work no matter which folder you run them from
#
# Usage from a script inside a member folder:
#     import os, sys
#     sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
#     from emt_config import F0, LAMBDA, THEORETICAL_CSV, load_dimensions
# ==============================================================================

import os
import json

# ------------------------------------------------------------------------------
# Design-freeze constants (master context document, section 5.1)
# ------------------------------------------------------------------------------
C0 = 299792458.0              # Speed of light in vacuum (m/s)
F0 = 2.44e9                   # Center frequency (Hz), Wi-Fi channel 7
LAMBDA = C0 / F0              # Free-space wavelength (m), ~0.12287 m
Z0 = 50.0                     # Feedline / reference impedance (Ohm)
SWEEP_START_HZ = 2.0e9        # Frequency sweep used for S11 / VSWR / Smith chart
SWEEP_STOP_HZ = 3.0e9
PATTERN_STEP_DEG = 10         # Universal CSV: 0..350 deg in 10 deg steps (36 rows)

# ------------------------------------------------------------------------------
# Shared file locations
# ------------------------------------------------------------------------------
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data")

# Member 2 -> Lead (engine) and Member 3 (blueprint)
DIMENSIONS_JSON = os.path.join(DATA_DIR, "optimized_dimensions.json")

# Universal radiation-pattern CSVs (angle_deg, gain_dBi), overlaid by Member 1
THEORETICAL_CSV = os.path.join(DATA_DIR, "theoretical_pattern.csv")   # Lead
SIMULATED_CSV = os.path.join(DATA_DIR, "simulated_pattern.csv")       # Member 2
EMPIRICAL_CSV = os.path.join(DATA_DIR, "empirical_pattern.csv")       # Member 4


def ensure_data_dir():
    """Create data/ if it does not exist yet."""
    os.makedirs(DATA_DIR, exist_ok=True)


def load_dimensions():
    """
    Load Member 2's optimized Yagi dimensions (data/optimized_dimensions.json).

    Returns the parsed dict, or None if the file has not been generated yet
    (run EMT_Member2/simulate_yagi.py or run_pipeline.py to create it).
    """
    if not os.path.exists(DIMENSIONS_JSON):
        return None
    with open(DIMENSIONS_JSON, "r", encoding="ascii") as f:
        return json.load(f)
