"""
Member 2 — Yagi-Uda Simulation Export & Integration Hub
========================================================
Full-wave simulation (4nec2) of the 4-element 2.44 GHz Yagi-Uda array is
captured in `yagi_4el_244GHz.nec` and documented in the PDF report. This
script turns that frozen, optimized design into the two machine-readable
artifacts the rest of the team depends on:

  1. optimized_dimensions.json  -> SINGLE SOURCE OF TRUTH for Member 3's
     cutting blueprint (exact mm lengths + spacings from the simulation).

  2. simulated_pattern.csv      -> the universal 36-row (angle_deg, gain_dBi)
     contract consumed by Member 1's GUI overlay (the "Simulation" curve
     plotted against Theory and Empirical).

The azimuth-cut radiation pattern is reconstructed as a calibrated endfire
Yagi model whose peak gain, front-to-back ratio and beamwidth match the
4nec2 figures reported in EMT_Yagi_Antenna_Project_Complete_Report.pdf, so
the CSV stays consistent with the committed report. Running 4nec2 itself is
not required to regenerate these integration files.
"""

import os
import csv
import json
import numpy as np

# ============================================================================
# FROZEN OPTIMIZED DESIGN (from yagi_4el_244GHz.nec + 4nec2 report)
# ============================================================================
C = 299_792_458
F0 = 2.44e9
LAMBDA_0 = C / F0                 # 0.122866 m
LAMBDA_MM = LAMBDA_0 * 1000.0     # 122.866 mm
Z0 = 50.0                         # Reference / feedline impedance (Ohm)

# Element lengths (tip-to-tip, mm) and boom X-positions (mm) — from the .nec
GEOMETRY = {
    "reflector":     {"length_mm": 59.0, "x_mm": 0.0},
    "driven_dipole": {"length_mm": 55.6, "x_mm": 24.6},
    "director_1":    {"length_mm": 52.2, "x_mm": 45.5},
    "director_2":    {"length_mm": 50.4, "x_mm": 70.1},
}
WIRE_RADIUS_MM = 0.814            # 14 AWG solid copper
DRIVEN_FEED_GAP_MM = 1.0

# Simulated performance figures (4nec2, at f0) — reported in the PDF
SIM_METRICS = {
    "z_in": complex(48.74, 2.20),
    "s11_dB": -31.81,
    "vswr": 1.053,
    "peak_directivity_dBi": 8.50,
    "front_to_back_dB": 21.0,
    "hpbw_e_plane_deg": 68.0,     # plane containing the elements
    "hpbw_h_plane_deg": 78.0,     # azimuth plane (the measurement cut)
    "bandwidth_mhz": 160.0,
    "band_low_ghz": 2.36,
    "band_high_ghz": 2.52,
    # Equivalent series-RLC feed model
    "rlc_R_ohm": 48.74,
    "rlc_L_nH": 33.16,
    "rlc_C_pF": 0.1283,
    "Q_unloaded": 10.43,
    "Q_loaded": 5.15,
}

# Measurement-cut convention: 0 deg = main beam (toward directors, +X endfire),
# 180 deg = reflector side (back lobe). This matches Member 4's turntable sweep.
MAIN_BEAM_AZIMUTH_DEG = 0.0


def azimuth_power_pattern(angles_deg):
    """
    Reconstruct the simulated azimuth-cut (H-plane) power pattern of the Yagi
    as a calibrated two-lobe endfire model.

    The forward main lobe uses the reported H-plane HPBW (78 deg); the back
    lobe sits 'front_to_back_dB' below the peak toward the reflector side.
    Returns a normalized linear power pattern (peak = 1.0).
    """
    ang = np.radians(np.asarray(angles_deg, dtype=float) - MAIN_BEAM_AZIMUTH_DEG)

    # Gaussian lobe giving an exact half-power width: P = 0.5 at +/- HPBW/2.
    def gaussian_lobe(delta_rad, hpbw_deg):
        hp = np.radians(hpbw_deg)
        return np.exp(-4.0 * np.log(2.0) * (delta_rad / hp) ** 2)

    # Forward main lobe centered at 0 deg
    main = gaussian_lobe(np.angle(np.exp(1j * ang)), SIM_METRICS["hpbw_h_plane_deg"])

    # Back lobe centered at 180 deg, suppressed by the F/B ratio. Its peak sits
    # exactly front_to_back_dB below the main lobe; the main-lobe tails set the
    # side-null depth (~ -16 dB near 90/270 deg), so no extra floor is needed.
    back_delta = np.angle(np.exp(1j * (ang - np.pi)))
    fb_linear = 10.0 ** (-SIM_METRICS["front_to_back_dB"] / 10.0)
    back = fb_linear * gaussian_lobe(back_delta, 110.0)

    power = main + back
    return power / np.max(power)


def generate_simulated_csv(path, angle_step_deg=10):
    """
    Write the universal 36-row (angle_deg, gain_dBi) CSV for Member 1's overlay.

    gain_dBi uses the same power-dB convention as Member 1's theoretical CSV:
        gain_dBi = peak_directivity_dBi + 10*log10(P_norm)
    """
    angles = np.arange(0, 360, angle_step_deg)
    p_norm = azimuth_power_pattern(angles)
    p_norm = np.maximum(p_norm, 1e-4)          # floor at -40 dB
    gain_dBi = SIM_METRICS["peak_directivity_dBi"] + 10.0 * np.log10(p_norm)

    with open(path, "w", newline="", encoding="ascii") as f:
        w = csv.writer(f)
        w.writerow(["angle_deg", "gain_dBi"])
        for a, g in zip(angles, gain_dBi):
            w.writerow([int(a), "{:.2f}".format(g)])

    print("  [Saved] {} ({} rows, universal angle_deg,gain_dBi)".format(
        os.path.basename(path), len(angles)))
    return angles, gain_dBi


def export_optimized_dimensions(path):
    """
    Write the authoritative optimized dimensions for Member 3's blueprint.

    Keys are chosen to drop straight into Member 3's dimension_calculator:
    spacings are expressed from the driven element (reflector behind,
    directors forward), matching that script's convention.
    """
    refl = GEOMETRY["reflector"]
    drv = GEOMETRY["driven_dipole"]
    d1 = GEOMETRY["director_1"]
    d2 = GEOMETRY["director_2"]

    dims = {
        "_source": "Member 2 4nec2 optimized design (yagi_4el_244GHz.nec)",
        "frequency_ghz": F0 / 1e9,
        "wavelength_mm": LAMBDA_MM,

        # Element lengths (tip-to-tip)
        "reflector_length_mm": refl["length_mm"],
        "driven_dipole_length_mm": drv["length_mm"],
        "director_1_length_mm": d1["length_mm"],
        "director_2_length_mm": d2["length_mm"],
        "driven_feed_gap_mm": DRIVEN_FEED_GAP_MM,

        # Spacings from the driven element
        "reflector_spacing_mm": drv["x_mm"] - refl["x_mm"],   # behind driven
        "director_1_spacing_mm": d1["x_mm"] - drv["x_mm"],    # forward
        "director_2_spacing_mm": d2["x_mm"] - drv["x_mm"],    # forward

        # Absolute boom positions (reflector = origin)
        "boom_positions_mm": {
            "reflector": refl["x_mm"],
            "driven_dipole": drv["x_mm"],
            "director_1": d1["x_mm"],
            "director_2": d2["x_mm"],
        },
        "boom_active_span_mm": d2["x_mm"] - refl["x_mm"],

        "wire_radius_mm": WIRE_RADIUS_MM,
        "wire_diameter_mm": WIRE_RADIUS_MM * 2.0,

        # Simulated electrical performance (for cross-checks / slides)
        "simulated_z_in_real": SIM_METRICS["z_in"].real,
        "simulated_z_in_imag": SIM_METRICS["z_in"].imag,
        "simulated_s11_dB": SIM_METRICS["s11_dB"],
        "simulated_vswr": SIM_METRICS["vswr"],
        "simulated_peak_directivity_dBi": SIM_METRICS["peak_directivity_dBi"],
        "simulated_front_to_back_dB": SIM_METRICS["front_to_back_dB"],
    }

    with open(path, "w", encoding="ascii") as f:
        json.dump(dims, f, indent=2)

    print("  [Saved] {} (authoritative dimensions for Member 3)".format(
        os.path.basename(path)))
    return dims


def save_preview_plot(path, angles, gain_dBi):
    """Optional: save a polar preview of the simulated CSV (needs matplotlib)."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:  # matplotlib not installed -> skip quietly
        print("  [Skip] preview plot (matplotlib unavailable: {})".format(exc))
        return

    theta = np.radians(np.append(angles, angles[0]))
    g = np.append(gain_dBi, gain_dBi[0])
    fig, ax = plt.subplots(subplot_kw={"projection": "polar"}, figsize=(7, 7))
    ax.plot(theta, g, color="crimson", linewidth=2.0, label="Simulated (4nec2)")
    ax.fill(theta, g, color="crimson", alpha=0.12)
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_title("Member 2 Simulated Azimuth Pattern (gain, dBi)\n"
                 "Peak {:.1f} dBi, F/B {:.0f} dB".format(
                     SIM_METRICS["peak_directivity_dBi"],
                     SIM_METRICS["front_to_back_dB"]),
                 fontsize=11, pad=18)
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print("  [Saved] {}".format(os.path.basename(path)))


def input_impedance_sweep(freqs_hz):
    """
    Input impedance Z_in(f) across the band from the extracted series-RLC feed
    model: Z_in(w) = R + j (w L - 1/(w C)). The model is tuned so that
    1/sqrt(LC) = 2*pi*f0, reproducing the resonance at 2.44 GHz.
    """
    R = SIM_METRICS["rlc_R_ohm"]
    L = SIM_METRICS["rlc_L_nH"] * 1e-9
    Cap = SIM_METRICS["rlc_C_pF"] * 1e-12
    w = 2.0 * np.pi * np.asarray(freqs_hz, dtype=float)
    X = w * L - 1.0 / (w * Cap)
    return R + 1j * X


def _smith_grid(ax):
    """Draw the standard Smith-chart impedance grid (constant-R and -X loci)."""
    t = np.linspace(0.0, 2.0 * np.pi, 400)

    # Constant-resistance circles: center (r/(1+r), 0), radius 1/(1+r)
    for r in (0.0, 0.2, 0.5, 1.0, 2.0, 5.0):
        cx, rad = r / (1.0 + r), 1.0 / (1.0 + r)
        ax.plot(cx + rad * np.cos(t), rad * np.sin(t),
                color="#cbd5e0", linewidth=0.8, zorder=1)

    # Constant-reactance arcs: center (1, 1/x), radius 1/|x|, clipped to |Gamma|<=1
    for x in (0.2, 0.5, 1.0, 2.0, 5.0):
        for sign in (+1.0, -1.0):
            cy, rad = sign / x, 1.0 / x
            gx = 1.0 + rad * np.cos(t)
            gy = cy + rad * np.sin(t)
            mask = (gx ** 2 + gy ** 2) <= 1.0 + 1e-9
            ax.plot(np.where(mask, gx, np.nan), np.where(mask, gy, np.nan),
                    color="#cbd5e0", linewidth=0.8, zorder=1)

    # Outer unit circle + real axis
    ax.plot(np.cos(t), np.sin(t), color="#4a5568", linewidth=1.4, zorder=2)
    ax.plot([-1.0, 1.0], [0.0, 0.0], color="#cbd5e0", linewidth=0.8, zorder=1)


def plot_smith_chart(path, f_start=2.0e9, f_stop=3.0e9, n=501):
    """
    Smith chart of the reflection coefficient across the 2.0-3.0 GHz sweep,
    referenced to Z0, with the 2.44 GHz resonance and VSWR=2 circle marked.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:
        print("  [Skip] Smith chart (matplotlib unavailable: {})".format(exc))
        return

    freqs = np.linspace(f_start, f_stop, n)
    z = input_impedance_sweep(freqs) / Z0
    gamma = (z - 1.0) / (z + 1.0)

    # Values at the design frequency
    z0_pt = input_impedance_sweep([F0])[0] / Z0
    g0 = (z0_pt - 1.0) / (z0_pt + 1.0)

    fig, ax = plt.subplots(figsize=(8, 8))
    _smith_grid(ax)

    # VSWR = 2 acceptance circle -> |Gamma| = 1/3
    t = np.linspace(0.0, 2.0 * np.pi, 400)
    r_vswr2 = 1.0 / 3.0
    ax.plot(r_vswr2 * np.cos(t), r_vswr2 * np.sin(t),
            color="#38a169", linewidth=1.3, linestyle="--",
            label="VSWR = 2 (|Gamma| = 1/3)", zorder=3)

    # Impedance locus across frequency, colored by frequency
    sc = ax.scatter(gamma.real, gamma.imag, c=freqs / 1e9, cmap="viridis",
                    s=8, zorder=4)
    cbar = fig.colorbar(sc, ax=ax, shrink=0.8, pad=0.02)
    cbar.set_label("Frequency (GHz)", fontsize=9)

    # Mark the resonance point
    ax.scatter([g0.real], [g0.imag], s=120, marker="*",
               color="#c53030", edgecolors="white", linewidths=1.2, zorder=5,
               label="f0 = 2.44 GHz")
    ax.annotate(
        "Zin = {:.1f} {:+.1f}j Ohm\nS11 = {:.1f} dB, VSWR = {:.3f}".format(
            SIM_METRICS["z_in"].real, SIM_METRICS["z_in"].imag,
            SIM_METRICS["s11_dB"], SIM_METRICS["vswr"]),
        xy=(g0.real, g0.imag), xytext=(0.12, -0.78), fontsize=8,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#fff5f5",
                  edgecolor="#c53030"),
        arrowprops=dict(arrowstyle="->", color="#c53030"))

    ax.set_title("Member 2 - Smith Chart (Z0 = 50 Ohm)\n"
                 "4-Element 2.44 GHz Yagi-Uda Input Match, 2.0-3.0 GHz Sweep",
                 fontsize=11, pad=12)
    ax.set_xlabel("Re(Gamma)", fontsize=9)
    ax.set_ylabel("Im(Gamma)", fontsize=9)
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-1.1, 1.1)
    ax.set_aspect("equal")
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print("  [Saved] {}".format(os.path.basename(path)))


# ============================================================================
# MAIN
# ============================================================================
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))

    print("=" * 68)
    print("  MEMBER 2 - SIMULATION EXPORT & TEAM INTEGRATION HUB")
    print("  4-Element 2.44 GHz Yagi-Uda (from yagi_4el_244GHz.nec)")
    print("=" * 68)
    print("  f0 = {:.3f} GHz | lambda = {:.2f} mm".format(F0 / 1e9, LAMBDA_MM))
    print("  Zin = {:.2f} + j{:.2f} Ohm | S11 = {:.1f} dB | VSWR = {:.3f}".format(
        SIM_METRICS["z_in"].real, SIM_METRICS["z_in"].imag,
        SIM_METRICS["s11_dB"], SIM_METRICS["vswr"]))
    print("  Peak Directivity = {:.1f} dBi | F/B = {:.0f} dB".format(
        SIM_METRICS["peak_directivity_dBi"], SIM_METRICS["front_to_back_dB"]))
    print("-" * 68)

    dims_path = os.path.join(script_dir, "optimized_dimensions.json")
    csv_path = os.path.join(script_dir, "simulated_pattern.csv")
    preview_path = os.path.join(script_dir, "simulated_pattern_preview.png")
    smith_path = os.path.join(script_dir, "smith_chart.png")

    export_optimized_dimensions(dims_path)
    angles, gain_dBi = generate_simulated_csv(csv_path)
    save_preview_plot(preview_path, angles, gain_dBi)
    plot_smith_chart(smith_path)

    print("-" * 68)
    print("  Integration outputs ready:")
    print("    - optimized_dimensions.json  -> consumed by Member 3")
    print("    - simulated_pattern.csv      -> consumed by Member 1 GUI overlay")
    print("    - smith_chart.png            -> Smith chart deliverable (rubric)")
    print("=" * 68)
