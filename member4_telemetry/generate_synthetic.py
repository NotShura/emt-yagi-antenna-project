"""
Member 4 - Synthetic Noisy Telemetry Generator
==============================================
Produces a *placeholder* empirical radiation pattern so the rest of the
software pipeline (especially Member 1's Theory-vs-Sim-vs-Empirical overlay)
works immediately, before the physical antenna is built.

Method:
  1. Read the Lead's theoretical Yagi pattern (data/theoretical_pattern.csv).
     If it is not available yet, fall back to Member 2's simulated pattern,
     and if neither exists, synthesise a textbook Yagi pattern from scratch.
  2. Add measurement-like imperfections that a real 360 deg RSSI sweep shows:
       - Gaussian noise (a +/-1.5 dB measurement spread, 2-sigma),
       - a small random pointing/boresight bias,
       - 1 dB RSSI quantisation (ESP32 / Wi-Fi analysers report integer dBm),
       - a receiver noise floor the pattern cannot dip below.
  3. Write data/empirical_pattern.csv in the universal format
     (header angle_deg,gain_dBi; 36 rows, 0..350 deg in 10 deg steps,
     0 deg = main beam toward the directors, 180 deg = reflector side).

Once the real field sweep is done, serial_rssi_logger.py overwrites this
same file with measured data, so no other script has to change.

Usage:
    python member4_telemetry/generate_synthetic.py            # default seed
    python member4_telemetry/generate_synthetic.py --seed 7   # reproducible
    python member4_telemetry/generate_synthetic.py --sigma 1.0
"""

import os
import sys
import csv

import numpy as np

# Shared team config (repo root): constants + data/ file locations
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from emt_config import (
    PATTERN_STEP_DEG,
    THEORETICAL_CSV,
    SIMULATED_CSV,
    EMPIRICAL_CSV,
    ensure_data_dir,
    load_dimensions,
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================================
# SYNTHETIC-NOISE MODEL CONSTANTS
# ============================================================================
# "+/-1.5 dB Gaussian noise" (master context document, section 4.5) is read as
# a +/-1.5 dB spread, i.e. 2-sigma, so sigma = 0.75 dB.
NOISE_SPREAD_DB = 1.5          # peak-to-mean measurement spread (2 sigma)
NOISE_SIGMA_DB = NOISE_SPREAD_DB / 2.0

BORESIGHT_BIAS_SIGMA_DEG = 3.0 # random turntable / pointing misalignment
RSSI_QUANTISATION_DB = 1.0     # receivers report integer dBm
RECEIVER_FLOOR_DBI = -25.0     # pattern cannot be read below this relative level
DEFAULT_SEED = 42              # reproducible by default; override with --seed


# ============================================================================
# PATTERN SOURCE
# ============================================================================
def _read_pattern_csv(path):
    """Return (angles_deg, gains_dBi) as numpy arrays, or (None, None)."""
    if not os.path.exists(path):
        return None, None
    angles, gains = [], []
    with open(path, "r", newline="", encoding="ascii") as f:
        reader = csv.reader(f)
        header = next(reader, None)  # skip "angle_deg,gain_dBi"
        for row in reader:
            if len(row) < 2:
                continue
            angles.append(float(row[0]))
            gains.append(float(row[1]))
    if not angles:
        return None, None
    return np.array(angles), np.array(gains)


def _textbook_yagi_pattern(angles_deg):
    """
    Fallback analytical H-plane Yagi pattern if no CSV exists yet.

    A directive main lobe toward the directors (0 deg) plus a suppressed back
    lobe toward the reflector (180 deg), scaled to the simulated peak gain and
    front-to-back ratio from Member 2's dimensions (sensible defaults if that
    file is also missing).
    """
    dims = load_dimensions() or {}
    peak_dBi = float(dims.get("simulated_peak_directivity_dBi", 8.5))
    fb_dB = float(dims.get("simulated_front_to_back_dB", 21.0))

    theta = np.radians(angles_deg)
    # Main lobe: Gaussian-ish in power, HPBW ~ 80 deg -> sigma ~ 34 deg.
    sigma_main = np.radians(34.0)
    front = np.exp(-(theta ** 2) / (2.0 * sigma_main ** 2))
    # Wrap so angles near 360 also feed the front lobe.
    front += np.exp(-((theta - 2 * np.pi) ** 2) / (2.0 * sigma_main ** 2))
    # Back lobe toward the reflector, suppressed by the F/B ratio.
    sigma_back = np.radians(55.0)
    back = (10.0 ** (-fb_dB / 10.0)) * np.exp(
        -((theta - np.pi) ** 2) / (2.0 * sigma_back ** 2)
    )
    power = front + back
    power /= power.max()
    gains_dBi = peak_dBi + 10.0 * np.log10(np.clip(power, 1e-6, None))
    return gains_dBi


def load_base_pattern():
    """
    Pick the best available base pattern and return (angles, gains, source).

    Preference: Lead theory CSV -> Member 2 sim CSV -> textbook model.
    """
    angles = np.arange(0, 360, PATTERN_STEP_DEG, dtype=float)

    a, g = _read_pattern_csv(THEORETICAL_CSV)
    if a is not None:
        return a, g, "theoretical_pattern.csv (Lead)"

    a, g = _read_pattern_csv(SIMULATED_CSV)
    if a is not None:
        return a, g, "simulated_pattern.csv (Member 2)"

    return angles, _textbook_yagi_pattern(angles), "built-in textbook Yagi model"


# ============================================================================
# NOISE
# ============================================================================
def add_measurement_noise(angles, gains, rng, sigma_db=NOISE_SIGMA_DB):
    """Return a noisy copy of `gains` emulating a real RSSI sweep."""
    # 1) Random boresight/turntable misalignment: shift the whole curve a few
    #    degrees, then resample back onto the 10 deg grid (periodic).
    bias_deg = rng.normal(0.0, BORESIGHT_BIAS_SIGMA_DEG)
    shifted = np.interp(
        (angles + bias_deg) % 360.0,
        np.append(angles, 360.0),
        np.append(gains, gains[0]),
    )

    # 2) Additive Gaussian measurement noise.
    noisy = shifted + rng.normal(0.0, sigma_db, size=shifted.shape)

    # 3) Integer-dBm quantisation of the receiver.
    noisy = np.round(noisy / RSSI_QUANTISATION_DB) * RSSI_QUANTISATION_DB

    # 4) Receiver noise floor (relative to the measured peak).
    floor = noisy.max() + RECEIVER_FLOOR_DBI
    noisy = np.maximum(noisy, floor)
    return noisy


# ============================================================================
# OUTPUT
# ============================================================================
def write_empirical_csv(angles, gains, path=EMPIRICAL_CSV):
    ensure_data_dir()
    with open(path, "w", newline="", encoding="ascii") as f:
        writer = csv.writer(f)
        writer.writerow(["angle_deg", "gain_dBi"])
        for ang, gain in zip(angles, gains):
            writer.writerow([int(round(ang)), "{:.2f}".format(gain)])
    return path


def save_preview_plot(angles, base, noisy, source):
    """Polar overlay of the base pattern and the synthetic empirical one."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover - matplotlib always in reqs
        print("  (skipping preview plot: {})".format(exc))
        return None

    out_dir = os.path.join(SCRIPT_DIR, "output")
    os.makedirs(out_dir, exist_ok=True)

    theta = np.radians(np.append(angles, angles[0]))
    base_c = np.append(base, base[0])
    noisy_c = np.append(noisy, noisy[0])

    fig = plt.figure(figsize=(7, 7))
    ax = fig.add_subplot(111, projection="polar")
    ax.plot(theta, base_c, "--", lw=1.6, color="#1f77b4", label="Base pattern")
    ax.plot(theta, noisy_c, "-", lw=2.0, color="#d62728",
            label="Synthetic empirical")
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_title("Member 4 - Synthetic Empirical Pattern\n(base: {})".format(source),
                 pad=18, fontsize=10)
    ax.legend(loc="lower left", bbox_to_anchor=(-0.1, -0.1), fontsize=9)
    fig.tight_layout()
    path = os.path.join(out_dir, "synthetic_pattern_preview.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


# ============================================================================
# MAIN
# ============================================================================
def parse_args(argv):
    seed = DEFAULT_SEED
    sigma = NOISE_SIGMA_DB
    i = 0
    while i < len(argv):
        if argv[i] == "--seed" and i + 1 < len(argv):
            seed = int(argv[i + 1]); i += 2
        elif argv[i] == "--sigma" and i + 1 < len(argv):
            sigma = float(argv[i + 1]); i += 2
        else:
            i += 1
    return seed, sigma


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    seed, sigma = parse_args(argv)

    print("=" * 70)
    print("  MEMBER 4 - SYNTHETIC TELEMETRY GENERATOR")
    print("=" * 70)

    angles, base, source = load_base_pattern()
    print("  Base pattern : {}".format(source))
    print("  Points       : {} angles (0..350 deg, {} deg step)".format(
        len(angles), PATTERN_STEP_DEG))
    print("  Noise model  : sigma = {:.2f} dB (+/-{:.1f} dB 2-sigma spread),"
          " {:.0f} dB quantisation".format(sigma, 2 * sigma, RSSI_QUANTISATION_DB))
    print("  Seed         : {}".format(seed))

    rng = np.random.default_rng(seed)
    noisy = add_measurement_noise(angles, base, rng, sigma_db=sigma)

    csv_path = write_empirical_csv(angles, noisy)
    print("\n  Wrote : {}".format(csv_path))

    # Quick quality numbers so the user sees it worked.
    peak_idx = int(np.argmax(noisy))
    back_idx = int(np.argmin(np.abs(angles - 180.0)))
    fb = noisy[peak_idx] - noisy[back_idx]
    rms = float(np.sqrt(np.mean((noisy - base) ** 2)))
    print("  Peak  : {:.2f} dBi at {:.0f} deg".format(noisy[peak_idx], angles[peak_idx]))
    print("  F/B   : {:.1f} dB (0 deg vs 180 deg)".format(fb))
    print("  RMS vs base : {:.2f} dB".format(rms))

    preview = save_preview_plot(angles, base, noisy, source)
    if preview:
        print("  Preview : {}".format(preview))

    print("\n  Member 1's GUI overlay will now pick this up automatically.")
    print("  Replace it with serial_rssi_logger.py output after the field sweep.")
    print("=" * 70)


if __name__ == "__main__":
    main()
