"""
Member 4 - Fraunhofer Far-Field Distance, Friis Link Budget & Error Analysis
============================================================================
Three jobs, all needed for the experimental-setup and observations slides:

  1. Far-field (Fraunhofer) distance  R_ff = 2 D^2 / lambda
     - the minimum TX-RX separation for a valid radiation-pattern measurement,
       where D is the largest dimension of the antenna under test.

  2. Friis transmission link budget
         Pr = Pt + Gt + Gr - FSPL,   FSPL(dB) = 20 log10(4 pi R / lambda)
     - the received power expected at the measurement distance, used to pick a
       sensible TX power and confirm the RSSI sits above the receiver floor.

  3. Error analysis (empirical vs theoretical)
     - once data/empirical_pattern.csv exists (synthetic or real), compare it
       with the Lead's theoretical pattern: RMSE, peak/F-B error, HPBW error.

Reads geometry from data/optimized_dimensions.json and patterns from the
shared data/ CSVs. Prints a formatted report and saves a link-budget +
error-overlay figure to member4_telemetry/output/.

Usage:
    python member4_telemetry/friis_link_budget.py
    python member4_telemetry/friis_link_budget.py --pt 15 --range 1.5
"""

import os
import sys
import csv

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from emt_config import (
    C0, F0, LAMBDA,
    THEORETICAL_CSV, EMPIRICAL_CSV,
    load_dimensions,
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================================
# DEFAULTS (overridable from the command line)
# ============================================================================
DEFAULT_PT_DBM = 15.0        # typical ESP32 / Wi-Fi TX power (~32 mW)
DEFAULT_RX_SENS_DBM = -90.0  # typical 2.4 GHz receiver sensitivity floor
# Measurement range: set to None to auto-use the Fraunhofer distance.
DEFAULT_RANGE_M = None


# ============================================================================
# 1. FAR-FIELD DISTANCE
# ============================================================================
def antenna_largest_dimension_m(dims):
    """
    Largest physical dimension D of the Yagi (metres).

    For a Yagi this is the larger of the boom length and the longest element.
    Falls back to ~0.59*lambda (a lambda/2 reflector) if dimensions are missing.
    """
    if not dims:
        return 0.59 * LAMBDA
    boom = float(dims.get("boom_active_span_mm", 70.1)) / 1000.0
    elems_mm = [
        dims.get("reflector_length_mm", 59.0),
        dims.get("driven_dipole_length_mm", 55.6),
        dims.get("director_1_length_mm", 52.2),
        dims.get("director_2_length_mm", 50.4),
    ]
    longest_elem = max(float(x) for x in elems_mm) / 1000.0
    return max(boom, longest_elem)


def fraunhofer_distance_m(D_m):
    """R_ff = 2 D^2 / lambda (metres)."""
    return 2.0 * D_m ** 2 / LAMBDA


# ============================================================================
# 2. FRIIS LINK BUDGET
# ============================================================================
def free_space_path_loss_dB(range_m):
    """FSPL(dB) = 20 log10(4 pi R / lambda)."""
    return 20.0 * np.log10(4.0 * np.pi * range_m / LAMBDA)


def friis_received_power_dBm(pt_dbm, gt_dbi, gr_dbi, range_m):
    """Pr(dBm) = Pt + Gt + Gr - FSPL."""
    return pt_dbm + gt_dbi + gr_dbi - free_space_path_loss_dB(range_m)


# ============================================================================
# 3. PATTERN ERROR ANALYSIS
# ============================================================================
def _read_pattern_csv(path):
    if not os.path.exists(path):
        return None, None
    angles, gains = [], []
    with open(path, "r", newline="", encoding="ascii") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if len(row) < 2:
                continue
            angles.append(float(row[0]))
            gains.append(float(row[1]))
    if not angles:
        return None, None
    return np.array(angles), np.array(gains)


def _hpbw_deg(angles, gains):
    """
    Half-power beamwidth (deg) about the main beam at 0 deg.

    Finds where the pattern first drops 3 dB below peak on each side of the
    peak, using linear interpolation on the 10 deg grid.
    """
    peak = gains.max()
    half = peak - 3.0
    # Unwrap angles to +/-180 centred near the peak for a clean search.
    ang = np.where(angles > 180.0, angles - 360.0, angles)
    order = np.argsort(ang)
    ang, g = ang[order], gains[order]

    peak_i = int(np.argmax(g))

    def cross(indices):
        prev_a, prev_g = ang[peak_i], g[peak_i]
        for i in indices:
            if g[i] <= half:
                # interpolate between prev point and this one
                frac = (prev_g - half) / (prev_g - g[i]) if prev_g != g[i] else 0.0
                return prev_a + frac * (ang[i] - prev_a)
            prev_a, prev_g = ang[i], g[i]
        return None

    right = cross(range(peak_i + 1, len(ang)))
    left = cross(range(peak_i - 1, -1, -1))
    if right is None or left is None:
        return None
    return abs(right - left)


def error_metrics(theory_path=THEORETICAL_CSV, emp_path=EMPIRICAL_CSV):
    """Compare empirical vs theoretical pattern; return a dict or None."""
    ta, tg = _read_pattern_csv(theory_path)
    ea, eg = _read_pattern_csv(emp_path)
    if ta is None or ea is None:
        return None

    # Resample empirical onto the theory angles (periodic interpolation).
    eg_on_t = np.interp(ta % 360.0, np.append(ea, 360.0), np.append(eg, eg[0]))

    # Normalise both to their own peak so we compare *shape* (RSSI is relative).
    t_norm = tg - tg.max()
    e_norm = eg_on_t - eg_on_t.max()

    rmse = float(np.sqrt(np.mean((e_norm - t_norm) ** 2)))
    max_err = float(np.max(np.abs(e_norm - t_norm)))

    def fb(angles, gains):
        peak_i = int(np.argmax(gains))
        back_i = int(np.argmin(np.abs(angles - 180.0)))
        return gains[peak_i] - gains[back_i]

    return {
        "angles": ta,
        "theory_norm": t_norm,
        "emp_norm": e_norm,
        "rmse_db": rmse,
        "max_err_db": max_err,
        "fb_theory_db": fb(ta, tg),
        "fb_emp_db": fb(ta, eg_on_t),
        "hpbw_theory_deg": _hpbw_deg(ta, tg),
        "hpbw_emp_deg": _hpbw_deg(ta, eg_on_t),
    }


# ============================================================================
# REPORT + PLOT
# ============================================================================
def save_figure(dims, D_m, r_ff, pt_dbm, gt, gr, rx_sens, err):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover
        print("  (skipping figure: {})".format(exc))
        return None

    out_dir = os.path.join(SCRIPT_DIR, "output")
    os.makedirs(out_dir, exist_ok=True)

    fig = plt.figure(figsize=(12, 5))

    # Left: received power vs range, with Fraunhofer + sensitivity markers.
    ax1 = fig.add_subplot(1, 2, 1)
    ranges = np.linspace(0.2, 5.0, 300)
    pr = friis_received_power_dBm(pt_dbm, gt, gr, ranges)
    ax1.plot(ranges, pr, color="#1f77b4", lw=2, label="Received power Pr")
    ax1.axhline(rx_sens, color="#d62728", ls="--", lw=1.4,
                label="RX sensitivity {:.0f} dBm".format(rx_sens))
    ax1.axvline(r_ff, color="#2ca02c", ls=":", lw=1.6,
                label="Fraunhofer R_ff = {:.2f} m".format(r_ff))
    ax1.set_xlabel("TX-RX separation R (m)")
    ax1.set_ylabel("Received power (dBm)")
    ax1.set_title("Friis Link Budget (Pt = {:.0f} dBm)".format(pt_dbm))
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=8)

    # Right: theory vs empirical normalized pattern (if available).
    ax2 = fig.add_subplot(1, 2, 2, projection="polar")
    if err is not None:
        th = np.radians(np.append(err["angles"], err["angles"][0]))
        t = np.append(err["theory_norm"], err["theory_norm"][0])
        e = np.append(err["emp_norm"], err["emp_norm"][0])
        ax2.plot(th, t, "--", color="#1f77b4", lw=1.6, label="Theory")
        ax2.plot(th, e, "-", color="#d62728", lw=2.0, label="Empirical")
        ax2.set_theta_zero_location("N")
        ax2.set_theta_direction(-1)
        ax2.set_title("Normalized pattern\nRMSE = {:.2f} dB".format(err["rmse_db"]),
                      fontsize=10, pad=16)
        ax2.legend(loc="lower left", bbox_to_anchor=(-0.1, -0.1), fontsize=8)
    else:
        ax2.set_title("No empirical pattern yet\n(run generate_synthetic.py)",
                      fontsize=10)

    fig.tight_layout()
    path = os.path.join(out_dir, "friis_link_budget.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def parse_args(argv):
    pt = DEFAULT_PT_DBM
    rng = DEFAULT_RANGE_M
    rx = DEFAULT_RX_SENS_DBM
    i = 0
    while i < len(argv):
        if argv[i] == "--pt" and i + 1 < len(argv):
            pt = float(argv[i + 1]); i += 2
        elif argv[i] == "--range" and i + 1 < len(argv):
            rng = float(argv[i + 1]); i += 2
        elif argv[i] == "--rx-sens" and i + 1 < len(argv):
            rx = float(argv[i + 1]); i += 2
        else:
            i += 1
    return pt, rng, rx


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    pt_dbm, range_m, rx_sens = parse_args(argv)

    dims = load_dimensions()
    gain_dbi = float((dims or {}).get("simulated_peak_directivity_dBi", 8.5))

    print("=" * 70)
    print("  MEMBER 4 - FAR-FIELD DISTANCE & FRIIS LINK BUDGET")
    print("=" * 70)
    print("  f0 = {:.3f} GHz   lambda = {:.2f} mm   c = {:.0f} m/s".format(
        F0 / 1e9, LAMBDA * 1000.0, C0))

    # --- 1. Far-field distance -------------------------------------------
    D_m = antenna_largest_dimension_m(dims)
    r_ff = fraunhofer_distance_m(D_m)
    print("\n  [1] Fraunhofer far-field distance")
    print("      Largest antenna dimension D = {:.1f} mm".format(D_m * 1000.0))
    print("      R_ff = 2 D^2 / lambda        = {:.3f} m".format(r_ff))
    print("      -> measure at R >= {:.2f} m (use ~{:.1f} m for margin)".format(
        r_ff, max(1.5, round(r_ff + 0.5, 1))))

    # --- 2. Link budget ---------------------------------------------------
    r_used = range_m if range_m is not None else max(r_ff, 1.5)
    fspl = free_space_path_loss_dB(r_used)
    pr = friis_received_power_dBm(pt_dbm, gain_dbi, gain_dbi, r_used)
    margin = pr - rx_sens
    print("\n  [2] Friis link budget at R = {:.2f} m".format(r_used))
    print("      Pt (TX power)        = {:+7.1f} dBm".format(pt_dbm))
    print("      Gt (TX antenna gain) = {:+7.1f} dBi".format(gain_dbi))
    print("      Gr (RX antenna gain) = {:+7.1f} dBi".format(gain_dbi))
    print("      FSPL = 20log10(4 pi R / lambda) = {:7.1f} dB".format(fspl))
    print("      ----------------------------------------")
    print("      Pr (received power)  = {:+7.1f} dBm".format(pr))
    print("      Link margin over {:.0f} dBm RX = {:+.1f} dB  [{}]".format(
        rx_sens, margin, "OK" if margin > 0 else "TOO WEAK"))

    # --- 3. Error analysis ------------------------------------------------
    err = error_metrics()
    print("\n  [3] Empirical vs theoretical pattern")
    if err is None:
        print("      No comparison yet - need both data/theoretical_pattern.csv")
        print("      and data/empirical_pattern.csv (run the Lead engine and")
        print("      generate_synthetic.py or the field sweep first).")
    else:
        print("      Pattern-shape RMSE        = {:.2f} dB".format(err["rmse_db"]))
        print("      Max angular error         = {:.2f} dB".format(err["max_err_db"]))
        print("      Front/back  theory {:.1f} dB  vs  empirical {:.1f} dB".format(
            err["fb_theory_db"], err["fb_emp_db"]))
        if err["hpbw_theory_deg"] and err["hpbw_emp_deg"]:
            print("      HPBW        theory {:.0f} deg  vs  empirical {:.0f} deg".format(
                err["hpbw_theory_deg"], err["hpbw_emp_deg"]))

    fig = save_figure(dims, D_m, r_ff, pt_dbm, gain_dbi, gain_dbi, rx_sens, err)
    if fig:
        print("\n  Figure : {}".format(fig))
    print("=" * 70)


if __name__ == "__main__":
    main()
