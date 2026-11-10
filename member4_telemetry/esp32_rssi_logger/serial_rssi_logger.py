"""
Member 4 - 360 deg Field-Sweep RSSI Logger
===========================================
Records one RSSI reading per 10 deg turntable step and writes the real
data/empirical_pattern.csv (same universal format the synthetic generator
uses, so it transparently replaces the placeholder).

Three input modes:
  --port COMx   Read live "RSSI,<dBm>" lines from the ESP32 (rssi_rx.ino)
                over USB serial; averages a short burst at each angle.
  --manual      Type the dBm shown by a phone Wi-Fi analyser at each angle
                (zero-purchase option; no ESP32 needed).
  --dummy       No hardware: synthesise a plausible sweep for a dry run.

For every step the script prompts you to point the antenna's main beam at
the given angle (0 deg = main beam toward the directors) and press Enter.
After all 36 angles it converts dBm to normalized dBi (anchoring the
strongest direction to the simulated peak gain) and saves the CSV.

Usage:
    python serial_rssi_logger.py --port COM5
    python serial_rssi_logger.py --port /dev/ttyUSB0 --dwell 3
    python serial_rssi_logger.py --manual
    python serial_rssi_logger.py --dummy
"""

import os
import sys
import csv
import time

# emt_config lives two levels up: member4_telemetry/esp32_rssi_logger/ -> root
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)
from emt_config import PATTERN_STEP_DEG, EMPIRICAL_CSV, ensure_data_dir, load_dimensions

ANGLES = list(range(0, 360, PATTERN_STEP_DEG))   # 0..350, 36 steps
DEFAULT_BAUD = 115200
DEFAULT_DWELL_S = 2.0        # seconds of RSSI samples to average per angle


# ----------------------------------------------------------------------------
# Input modes
# ----------------------------------------------------------------------------
def read_serial_sweep(port, baud, dwell_s):
    """Live ESP32 capture. Returns list of dBm (one per angle) or None."""
    try:
        import serial  # pyserial
    except ImportError:
        print("  pyserial not installed ('pip install pyserial').")
        print("  Falling back to --manual entry.\n")
        return None

    try:
        ser = serial.Serial(port, baud, timeout=1.0)
    except Exception as exc:
        print("  Could not open {}: {}".format(port, exc))
        print("  Falling back to --manual entry.\n")
        return None

    time.sleep(2.0)       # let the board reset after the port opens
    ser.reset_input_buffer()
    readings = []
    try:
        for ang in ANGLES:
            input("  Rotate main beam to {:3d} deg, then press Enter...".format(ang))
            samples = []
            t_end = time.time() + dwell_s
            while time.time() < t_end:
                line = ser.readline().decode("ascii", "ignore").strip()
                if line.startswith("RSSI,"):
                    val = line.split(",", 1)[1]
                    try:
                        samples.append(float(val))
                    except ValueError:
                        pass   # "NaN" dropped sample
            if samples:
                avg = sum(samples) / len(samples)
                print("      {:3d} deg : {:6.1f} dBm  ({} samples)".format(
                    ang, avg, len(samples)))
            else:
                avg = float("nan")
                print("      {:3d} deg : no samples (check link)".format(ang))
            readings.append(avg)
    finally:
        ser.close()
    return readings


def read_manual_sweep():
    """Type the dBm from a phone Wi-Fi analyser at each angle."""
    print("  Manual entry - type the dBm value shown by your Wi-Fi analyser.")
    print("  (Press Enter alone to repeat the previous value.)\n")
    readings = []
    last = -60.0
    for ang in ANGLES:
        while True:
            raw = input("  {:3d} deg  dBm = ".format(ang)).strip()
            if raw == "":
                readings.append(last)
                break
            try:
                last = float(raw)
                readings.append(last)
                break
            except ValueError:
                print("      not a number, try again.")
    return readings


def read_dummy_sweep():
    """Synthetic sweep for a no-hardware dry run (reuses generate_synthetic)."""
    print("  --dummy: generating a synthetic sweep (no hardware).")
    import numpy as np
    dims = load_dimensions() or {}
    peak = float(dims.get("simulated_peak_directivity_dBi", 8.5))
    fb = float(dims.get("simulated_front_to_back_dB", 21.0))
    rng = np.random.default_rng()
    out = []
    for ang in ANGLES:
        th = np.radians(ang)
        front = np.exp(-(((ang if ang <= 180 else ang - 360) / 34.0) ** 2) / 2.0)
        back = 10 ** (-fb / 10.0) * np.exp(-(((ang - 180) / 55.0) ** 2) / 2.0)
        power = max(front + back, 1e-6)
        dbi = peak + 10 * np.log10(power)
        # pretend RSSI ~ dBi - 55 dBm offset + noise
        out.append(dbi - 55.0 + float(rng.normal(0, 0.75)))
    return out


# ----------------------------------------------------------------------------
# Conversion + output
# ----------------------------------------------------------------------------
def dbm_to_normalized_dbi(dbm_list):
    """
    Convert relative RSSI (dBm) to normalized dBi gain.

    RSSI is relative, so we anchor the strongest measured direction to the
    simulated peak directivity and keep every other angle relative to it.
    Missing (NaN) samples are filled with the running minimum.
    """
    import math
    vals = [v for v in dbm_list if not (isinstance(v, float) and math.isnan(v))]
    if not vals:
        raise SystemExit("No valid RSSI samples recorded - nothing to write.")
    peak_ref = float((load_dimensions() or {}).get(
        "simulated_peak_directivity_dBi", 8.5))
    rssi_max = max(vals)
    floor = min(vals)
    out = []
    for v in dbm_list:
        if isinstance(v, float) and math.isnan(v):
            v = floor
        out.append((v - rssi_max) + peak_ref)
    return out


def write_empirical_csv(gains_dbi, path=EMPIRICAL_CSV):
    ensure_data_dir()
    with open(path, "w", newline="", encoding="ascii") as f:
        w = csv.writer(f)
        w.writerow(["angle_deg", "gain_dBi"])
        for ang, g in zip(ANGLES, gains_dbi):
            w.writerow([ang, "{:.2f}".format(g)])
    return path


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def parse_args(argv):
    opts = {"port": None, "baud": DEFAULT_BAUD, "dwell": DEFAULT_DWELL_S,
            "manual": False, "dummy": False}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--port" and i + 1 < len(argv):
            opts["port"] = argv[i + 1]; i += 2
        elif a == "--baud" and i + 1 < len(argv):
            opts["baud"] = int(argv[i + 1]); i += 2
        elif a == "--dwell" and i + 1 < len(argv):
            opts["dwell"] = float(argv[i + 1]); i += 2
        elif a == "--manual":
            opts["manual"] = True; i += 1
        elif a == "--dummy":
            opts["dummy"] = True; i += 1
        else:
            i += 1
    return opts


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    opts = parse_args(argv)

    print("=" * 70)
    print("  MEMBER 4 - 360 deg FIELD-SWEEP RSSI LOGGER")
    print("=" * 70)
    print("  {} angles, {} deg step. 0 deg = main beam toward directors.\n".format(
        len(ANGLES), PATTERN_STEP_DEG))

    if opts["dummy"]:
        dbm = read_dummy_sweep()
    elif opts["manual"]:
        dbm = read_manual_sweep()
    elif opts["port"]:
        dbm = read_serial_sweep(opts["port"], opts["baud"], opts["dwell"])
        if dbm is None:
            dbm = read_manual_sweep()
    else:
        print("  No mode chosen. Use --port COMx, --manual, or --dummy.")
        print("  Example: python serial_rssi_logger.py --port COM5\n")
        return

    gains = dbm_to_normalized_dbi(dbm)
    path = write_empirical_csv(gains)

    peak_i = max(range(len(gains)), key=lambda k: gains[k])
    back_i = ANGLES.index(180) if 180 in ANGLES else 0
    print("\n  Wrote : {}".format(path))
    print("  Peak  : {:.2f} dBi at {} deg".format(gains[peak_i], ANGLES[peak_i]))
    print("  F/B   : {:.1f} dB (0 deg vs 180 deg)".format(gains[0] - gains[back_i]))
    print("\n  This replaces the synthetic CSV. Member 1's overlay and")
    print("  friis_link_budget.py error analysis now use real data.")
    print("=" * 70)


if __name__ == "__main__":
    main()
