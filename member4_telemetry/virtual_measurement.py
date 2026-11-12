"""
Member 4 - Virtual Measurement (software turntable sweep)
=========================================================
SOFTWARE-ONLY FALLBACK. When the physical antenna cannot be built or measured
in time, this script stands in for the real 360 deg field sweep by performing a
*virtual measurement* of the full-wave-simulated antenna.

It is NOT a lab measurement and must never be presented as one. It is the
simulated antenna (Member 2's full-wave / method-of-moments pattern) put through
a software model of a real turntable range, so the resulting curve looks and
behaves like a measured RSSI sweep (ripple, receiver noise, quantisation,
pointing error) while remaining fully traceable to the simulation.

Pipeline role
-------------
Device under test (DUT)  : data/simulated_pattern.csv  (full-wave MoM, Member 2)
                           -> falls back to theoretical_pattern.csv, then a
                              textbook Yagi model, if the sim CSV is absent.
Output                   : data/empirical_pattern.csv  (universal angle_deg,gain_dBi)
Provenance stamp         : data/empirical_pattern.provenance.txt

Member 1's GUI overlay and friis_link_budget.py then pick up the CSV unchanged,
so the Theory vs Simulation vs "Measurement" overlay works with zero other edits.

Measurement-range model (per 10 deg step, 0..350 deg)
-----------------------------------------------------
  received_dBi(angle) = DUT_gain(angle - pointing_bias)       # true pattern
                      + multipath_ripple(angle)               # residual reflections
                      + thermal_noise ~ N(0, sigma)           # receiver noise
  then integer-dBm quantisation and a receiver noise floor.

All impairments are small and physically motivated; the peak and front-to-back
ratio stay within a few tenths of a dB of the simulation, which is exactly what
a clean indoor/anechoic measurement of this design would show.

Usage
-----
    python member4_telemetry/virtual_measurement.py              # default seed
    python member4_telemetry/virtual_measurement.py --seed 7     # reproducible
    python member4_telemetry/virtual_measurement.py --sigma 0.6  # noise std (dB)
    python member4_telemetry/virtual_measurement.py --force      # replace a REAL sweep

If data/empirical_pattern.csv already holds a physical measurement (stamped by
serial_rssi_logger.py), this script leaves it alone unless --force is given.
"""

import os
import sys
import csv
import datetime

import numpy as np

# Shared team config (repo root): constants + data/ file locations
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from emt_config import (
    PATTERN_STEP_DEG,
    THEORETICAL_CSV,
    SIMULATED_CSV,
    EMPIRICAL_CSV,
    DATA_DIR,
    ensure_data_dir,
    load_dimensions,
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================================
# VIRTUAL-RANGE MODEL CONSTANTS  (physically motivated, deliberately mild)
# ============================================================================
THERMAL_NOISE_SIGMA_DB = 0.5     # receiver thermal/read noise, 1-sigma (dB)
MULTIPATH_RIPPLE_DB = 0.6        # amplitude of residual reflection ripple (dB)
MULTIPATH_CYCLES = 3.5           # ripple cycles around the full 360 deg sweep
POINTING_BIAS_SIGMA_DEG = 2.0    # turntable / boresight misalignment (deg)
RSSI_QUANTISATION_DB = 1.0       # receivers report integer dBm
RECEIVER_FLOOR_DBI = -25.0       # dynamic range below the measured peak
DEFAULT_SEED = 2440              # reproducible by default (nod to 2.44 GHz)


# ============================================================================
# DEVICE-UNDER-TEST PATTERN (what we "measure")
# ============================================================================
def _read_pattern_csv(path):
    """Return (angles_deg, gains_dBi) as numpy arrays, or (None, None)."""
    if not os.path.exists(path):
        return None, None
    angles, gains = [], []
    with open(path, "r", newline="", encoding="ascii") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header "angle_deg,gain_dBi"
        for row in reader:
            if len(row) < 2:
                continue
            angles.append(float(row[0]))
            gains.append(float(row[1]))
    if not angles:
        return None, None
    return np.array(angles), np.array(gains)


def _textbook_yagi_pattern(angles_deg):
    """Analytical H-plane Yagi pattern used only if no CSV exists yet."""
    dims = load_dimensions() or {}
    peak_dBi = float(dims.get("simulated_peak_directivity_dBi", 8.5))
    fb_dB = float(dims.get("simulated_front_to_back_dB", 21.0))

    theta = np.radians(angles_deg)
    sigma_main = np.radians(34.0)
    front = np.exp(-(theta ** 2) / (2.0 * sigma_main ** 2))
    front += np.exp(-((theta - 2 * np.pi) ** 2) / (2.0 * sigma_main ** 2))
    sigma_back = np.radians(55.0)
    back = (10.0 ** (-fb_dB / 10.0)) * np.exp(
        -((theta - np.pi) ** 2) / (2.0 * sigma_back ** 2)
    )
    power = front + back
    power /= power.max()
    return peak_dBi + 10.0 * np.log10(np.clip(power, 1e-6, None))


def load_dut_pattern():
    """
    Load the device-under-test pattern we virtually measure.

    Preference: Member 2 full-wave SIMULATED CSV  (the honest choice: we are
    "measuring" the simulated antenna) -> Lead theory CSV -> textbook model.
    Returns (angles, gains_dBi, source_label).
    """
    angles = np.arange(0, 360, PATTERN_STEP_DEG, dtype=float)

    a, g = _read_pattern_csv(SIMULATED_CSV)
    if a is not None:
        return a, g, "simulated_pattern.csv (Member 2 full-wave MoM)"

    a, g = _read_pattern_csv(THEORETICAL_CSV)
    if a is not None:
        return a, g, "theoretical_pattern.csv (Lead analytical engine)"

    return angles, _textbook_yagi_pattern(angles), "built-in textbook Yagi model"


# ============================================================================
# VIRTUAL RANGE: turn the DUT pattern into a "measured" sweep
# ============================================================================
def virtual_turntable_sweep(angles, dut_gains, rng, sigma_db=THERMAL_NOISE_SIGMA_DB):
    """
    Emulate a 360 deg turntable RSSI sweep of the DUT in a software range.

    Returns the "measured" gain array (dBi) on the same angle grid.
    """
    # 1) Turntable / boresight pointing bias: the whole pattern is offset by a
    #    small random angle, then resampled back onto the 10 deg grid (periodic).
    bias_deg = rng.normal(0.0, POINTING_BIAS_SIGMA_DEG)
    measured = np.interp(
        (angles + bias_deg) % 360.0,
        np.append(angles, 360.0),
        np.append(dut_gains, dut_gains[0]),
    )

    # 2) Residual multipath ripple: a low-order sinusoid vs angle with a random
    #    phase, standing in for weak reflections off the range walls/floor.
    phase = rng.uniform(0.0, 2.0 * np.pi)
    ripple = MULTIPATH_RIPPLE_DB * np.sin(
        MULTIPATH_CYCLES * np.radians(angles) + phase
    )
    measured = measured + ripple

    # 3) Receiver thermal / read noise: independent Gaussian per angle.
    measured = measured + rng.normal(0.0, sigma_db, size=measured.shape)

    # 4) Integer-dBm quantisation of the receiver readout.
    measured = np.round(measured / RSSI_QUANTISATION_DB) * RSSI_QUANTISATION_DB

    # 5) Receiver noise floor relative to the measured peak (finite dynamic range).
    floor = measured.max() + RECEIVER_FLOOR_DBI
    measured = np.maximum(measured, floor)
    return measured


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


def write_provenance(source, seed, sigma, metrics):
    """
    Write a plain-text provenance stamp next to the CSV so the overlay data is
    never mistaken for a physical lab measurement.
    """
    ensure_data_dir()
    path = os.path.join(DATA_DIR, "empirical_pattern.provenance.txt")
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "empirical_pattern.csv - PROVENANCE",
        "=" * 52,
        "TYPE : VIRTUAL MEASUREMENT (software turntable sweep).",
        "       NOT a physical lab measurement. Generated because the",
        "       hardware prototype was unavailable within the timeline.",
        "",
        "Device under test (DUT) : {}".format(source),
        "Generator  : member4_telemetry/virtual_measurement.py",
        "Generated  : {}".format(stamp),
        "Seed       : {} (reproducible)".format(seed),
        "",
        "Range model impairments applied to the DUT pattern:",
        "  - thermal/read noise  : sigma = {:.2f} dB".format(sigma),
        "  - multipath ripple    : +/-{:.2f} dB, {:.1f} cycles/360deg".format(
            MULTIPATH_RIPPLE_DB, MULTIPATH_CYCLES),
        "  - pointing bias       : sigma = {:.1f} deg".format(POINTING_BIAS_SIGMA_DEG),
        "  - RSSI quantisation   : {:.0f} dB".format(RSSI_QUANTISATION_DB),
        "  - receiver floor      : peak {:.0f} dB".format(RECEIVER_FLOOR_DBI),
        "",
        "Resulting metrics:",
        "  peak        : {:.2f} dBi at {:.0f} deg".format(
            metrics["peak_dBi"], metrics["peak_angle"]),
        "  front/back  : {:.1f} dB (0 deg vs 180 deg)".format(metrics["fb_dB"]),
        "  RMS vs DUT  : {:.2f} dB".format(metrics["rms_db"]),
    ]
    with open(path, "w", encoding="ascii") as f:
        f.write("\n".join(lines) + "\n")
    return path


def save_preview_plot(angles, dut, measured, source):
    """Polar overlay of the DUT pattern and the virtual measurement."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:
        print("  (skipping preview plot: {})".format(exc))
        return None

    out_dir = os.path.join(SCRIPT_DIR, "output")
    os.makedirs(out_dir, exist_ok=True)

    theta = np.radians(np.append(angles, angles[0]))
    dut_c = np.append(dut, dut[0])
    meas_c = np.append(measured, measured[0])

    fig = plt.figure(figsize=(7, 7))
    ax = fig.add_subplot(111, projection="polar")
    ax.plot(theta, dut_c, "--", lw=1.6, color="#1f77b4",
            label="DUT (full-wave simulation)")
    ax.plot(theta, meas_c, "-", lw=2.0, color="#d62728",
            label="Virtual measurement")
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_title(
        "Member 4 - Virtual Measurement (software turntable sweep)\n"
        "DUT: {}".format(source), pad=18, fontsize=10)
    ax.legend(loc="lower left", bbox_to_anchor=(-0.1, -0.1), fontsize=9)
    fig.tight_layout()
    path = os.path.join(out_dir, "virtual_measurement_preview.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


# ============================================================================
# MAIN
# ============================================================================
def parse_args(argv):
    seed, sigma = DEFAULT_SEED, THERMAL_NOISE_SIGMA_DB
    i = 0
    while i < len(argv):
        if argv[i] == "--seed" and i + 1 < len(argv):
            seed = int(argv[i + 1]); i += 2
        elif argv[i] == "--sigma" and i + 1 < len(argv):
            sigma = float(argv[i + 1]); i += 2
        else:
            i += 1
    return seed, sigma


def existing_measurement_type():
    """Return the TYPE line of the current provenance stamp, or None."""
    path = os.path.join(DATA_DIR, "empirical_pattern.provenance.txt")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="ascii", errors="replace") as f:
        for line in f:
            if line.startswith("TYPE"):
                return line.split(":", 1)[1].strip()
    return None


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    seed, sigma = parse_args(argv)

    # Never overwrite a real field sweep (serial_rssi_logger.py stamps it
    # PHYSICAL). This keeps run_pipeline.py safe to re-run after a measurement.
    existing = existing_measurement_type()
    if existing and existing.startswith("PHYSICAL") and "--force" not in argv:
        print("=" * 70)
        print("  MEMBER 4 - VIRTUAL MEASUREMENT: skipped")
        print("  data/empirical_pattern.csv holds a real measurement:")
        print("    {}".format(existing))
        print("  Keeping it. Use --force to replace it with a virtual sweep.")
        print("=" * 70)
        return

    print("=" * 70)
    print("  MEMBER 4 - VIRTUAL MEASUREMENT (software-only fallback)")
    print("  A software turntable sweep of the full-wave-simulated antenna.")
    print("  NOTE: this is a simulated measurement, NOT physical lab data.")
    print("=" * 70)

    angles, dut, source = load_dut_pattern()
    print("  DUT pattern  : {}".format(source))
    print("  Points       : {} angles (0..350 deg, {} deg step)".format(
        len(angles), PATTERN_STEP_DEG))
    print("  Range model  : noise sigma={:.2f} dB, multipath +/-{:.2f} dB,"
          " pointing {:.1f} deg".format(
              sigma, MULTIPATH_RIPPLE_DB, POINTING_BIAS_SIGMA_DEG))
    print("  Seed         : {}".format(seed))

    rng = np.random.default_rng(seed)
    measured = virtual_turntable_sweep(angles, dut, rng, sigma_db=sigma)

    csv_path = write_empirical_csv(angles, measured)

    peak_idx = int(np.argmax(measured))
    back_idx = int(np.argmin(np.abs(angles - 180.0)))
    metrics = {
        "peak_dBi": float(measured[peak_idx]),
        "peak_angle": float(angles[peak_idx]),
        "fb_dB": float(measured[peak_idx] - measured[back_idx]),
        "rms_db": float(np.sqrt(np.mean((measured - dut) ** 2))),
    }
    prov_path = write_provenance(source, seed, sigma, metrics)

    print("\n  Wrote : {}".format(csv_path))
    print("  Stamp : {}".format(prov_path))
    print("  Peak  : {:.2f} dBi at {:.0f} deg".format(
        metrics["peak_dBi"], metrics["peak_angle"]))
    print("  F/B   : {:.1f} dB (0 deg vs 180 deg)".format(metrics["fb_dB"]))
    print("  RMS vs DUT : {:.2f} dB".format(metrics["rms_db"]))

    preview = save_preview_plot(angles, dut, measured, source)
    if preview:
        print("  Preview : {}".format(preview))

    print("\n  Member 1's GUI overlay and friis_link_budget.py pick this up")
    print("  automatically as the 'Measurement' curve (Theory vs Sim vs Meas).")
    print("=" * 70)


if __name__ == "__main__":
    main()
