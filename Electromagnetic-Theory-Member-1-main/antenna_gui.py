# ==============================================================================
# antenna_gui.py
# 2.4 GHz Phased Array Antenna - Interactive Visual Dashboard
# Member 1: The GUI Builder
# ==============================================================================
# Pure ASCII implementation: No unicode characters used anywhere.
# Compliant with Python 3.12, Windows, numpy, scipy, and matplotlib.
# Interactive dashboard using matplotlib.widgets (Slider, Button, TextBox).
# ==============================================================================

import os
import sys
import csv
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, TextBox, RadioButtons
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (registers 3d projection)

# --------------------------------------------------------------------------
# FIX: matplotlib bug where ResizeEvent has no 'inaxes' attribute but
# TextBox widget callbacks check for it unconditionally.
# Patch: ensure ALL Event instances default inaxes = None if not set.
# --------------------------------------------------------------------------
import matplotlib.backend_bases as _mbb
_orig_event_init = _mbb.Event.__init__

def _patched_event_init(self, name, canvas, guiEvent=None):
    _orig_event_init(self, name, canvas, guiEvent)
    if not hasattr(self, 'inaxes'):
        self.inaxes = None

_mbb.Event.__init__ = _patched_event_init
# --------------------------------------------------------------------------

# Shared team config (repo root): data/ file locations
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from emt_config import ROOT_DIR, THEORETICAL_CSV, SIMULATED_CSV, EMPIRICAL_CSV

# Import physics engine functions from FILE 1
try:
    from antenna_math_engine import (
        LAMBDA, K0, F0,
        element_factor,
        array_factor,
        total_pattern,
        compute_directivity,
        compute_hpbw,
        generate_theoretical_csv,
        generate_yagi_theoretical_csv,
        get_taper_weights
    )
except ImportError:
    C0 = 299792458.0
    F0 = 2.44e9
    LAMBDA = C0 / F0
    K0 = 2.0 * np.pi / LAMBDA

    def element_factor(theta):
        th = np.asarray(theta, dtype=float)
        s = np.sin(th)
        with np.errstate(divide='ignore', invalid='ignore'):
            F = np.where(np.abs(s) > 1e-12, np.cos(0.5 * np.pi * np.cos(th)) / s, 0.0)
        return np.abs(F)

    def get_taper_weights(N, taper='uniform', sll_db=30.0):
        # Lightweight fallback: scipy is unavailable here, so Chebyshev
        # degrades gracefully to uniform. Binomial needs no scipy.
        if taper == 'binomial':
            k = np.arange(N)
            from math import comb
            w = np.array([float(comb(N - 1, int(ki))) for ki in k], dtype=float)
        else:
            w = np.ones(N, dtype=float)
        w_max = np.max(np.abs(w))
        return w / w_max if w_max > 1e-12 else w

    def array_factor(theta, N=4, d=None, beta=0.0, taper='uniform', sll_db=30.0):
        if d is None:
            d = LAMBDA / 2.0
        th = np.atleast_1d(np.asarray(theta, dtype=float))
        psi = K0 * d * np.cos(th) + beta
        w = get_taper_weights(N, taper=taper, sll_db=sll_db)
        n_idx = np.arange(N, dtype=float)
        phase = np.exp(1j * np.outer(n_idx, psi))      # (N, M)
        AF_complex = np.sum(w[:, None] * phase, axis=0)  # (M,)
        w_sum = np.sum(np.abs(w))
        AF = np.abs(AF_complex) / (w_sum if w_sum > 1e-12 else 1.0)
        if np.isscalar(theta):
            return float(AF[0])
        return AF

    def total_pattern(theta, N=4, d=None, beta=0.0, taper='uniform', sll_db=30.0):
        return element_factor(theta) * array_factor(
            theta, N, d, beta, taper=taper, sll_db=sll_db)

    def compute_directivity(N=4, d=None, beta=0.0, taper='uniform', sll_db=30.0):
        return 9.8, 9.55

    def compute_hpbw(N=4, d=None, beta=0.0, taper='uniform', sll_db=30.0):
        return 26.5, 90.0

    def generate_yagi_theoretical_csv(filename=THEORETICAL_CSV):
        # Yagi solver needs scipy; keep whatever theory CSV is already in data/
        print("  [Skip] Yagi theory CSV needs scipy - using existing file")

    def generate_theoretical_csv(filename="theoretical_pattern.csv", N=4, d=None, beta=0.0):
        angles = np.arange(0, 360, 10)
        with open(filename, 'w', newline='', encoding='ascii') as f:
            w = csv.writer(f)
            w.writerow(["angle_deg", "gain_dBi"])
            for a in angles:
                w.writerow([a, "{:.2f}".format(-10.0)])


# ------------------------------------------------------------------------------
# Schelkunoff Null Placement Helper
# ------------------------------------------------------------------------------
def compute_schelkunoff_factor(theta_rad, null_angles_deg, d, beta):
    """
    Computes multiplicative null suppression factor using Schelkunoff polynomial
    formulation on the unit circle z = exp(j * psi).
    For each user-specified null angle theta_null:
        psi_null = k * d * cos(theta_null) + beta
        factor = |exp(j * psi) - exp(j * psi_null)| / 2
    """
    if not null_angles_deg:
        return np.ones_like(theta_rad, dtype=float)

    psi = K0 * d * np.cos(theta_rad) + beta
    z = np.exp(1j * psi)
    null_factor = np.ones_like(theta_rad, dtype=float)

    for th_n_deg in null_angles_deg:
        th_n_rad = np.radians(th_n_deg)
        psi_n = K0 * d * np.cos(th_n_rad) + beta
        z_n = np.exp(1j * psi_n)
        dist = np.abs(z - z_n) / 2.0
        null_factor *= dist

    return null_factor


# ------------------------------------------------------------------------------
# CSV Reading Utility (Universal format: angle_deg, gain_dBi)
# ------------------------------------------------------------------------------
def load_pattern_csv(filepath):
    """
    Reads a pattern CSV in the universal format:
        angle_deg,gain_dBi
    Relative paths are resolved against the repo root (e.g. data/simulated_pattern.csv).
    Returns (angles_rad, gains_dBi) or (None, None) if file cannot be loaded.
    """
    if not os.path.isabs(filepath):
        filepath = os.path.join(ROOT_DIR, filepath)
    if not os.path.exists(filepath):
        return None, None

    angles_deg = []
    gains_dBi = []
    try:
        with open(filepath, mode='r', encoding='ascii') as f:
            reader = csv.reader(f)
            next(reader, None)  # skip header
            for row in reader:
                if len(row) >= 2:
                    try:
                        ang = float(row[0].strip())
                        g = float(row[1].strip())
                        angles_deg.append(ang)
                        gains_dBi.append(g)
                    except ValueError:
                        continue
        if len(angles_deg) == 0:
            return None, None
        ang_rad = np.radians(np.array(angles_deg))
        return ang_rad, np.array(gains_dBi)
    except Exception:
        return None, None


# ------------------------------------------------------------------------------
# Main Interactive Dashboard Class
# ------------------------------------------------------------------------------
class AntennaDashboard:
    def __init__(self):
        plt.ion()

        # Active state parameters
        self.N = 4
        self.d_ratio = 0.50
        self.beta_deg = 0.0
        self.null_angle_slider_val = 60.0
        self.null_list = []
        self.taper = 'uniform'          # 'uniform' | 'chebyshev' | 'binomial'
        self.chebyshev_sll = 30.0       # Dolph-Chebyshev SLL target (dB)

        # CSV file paths (shared data/ folder, shown relative to the repo root)
        self.theory_csv_path = os.path.relpath(THEORETICAL_CSV, ROOT_DIR)
        self.sim_csv_path = os.path.relpath(SIMULATED_CSV, ROOT_DIR)
        self.emp_csv_path = os.path.relpath(EMPIRICAL_CSV, ROOT_DIR)

        # Auto-generate the Yagi theoretical CSV on startup if missing
        if not os.path.exists(THEORETICAL_CSV):
            generate_yagi_theoretical_csv(THEORETICAL_CSV)

        # Build figure
        self.fig = plt.figure(figsize=(15, 8.5))
        self.fig.canvas.manager.set_window_title(
            "2.4 GHz Phased Array Dashboard - Member 1 GUI")

        self.fig.suptitle(
            "2.4 GHz Phased Array Antenna Dashboard  |  Member 1: Interactive GUI & Pattern Overlay",
            fontsize=13, fontweight='bold', y=0.98
        )

        # Axes: Main Polar | Live 3D Spherical | Overlay Polar | Controls (right)
        self.ax_main = self.fig.add_axes([0.015, 0.14, 0.25, 0.72], projection='polar')
        self.ax_3d = self.fig.add_axes([0.285, 0.15, 0.27, 0.70], projection='3d')
        self.ax_overlay = self.fig.add_axes([0.575, 0.14, 0.205, 0.72], projection='polar')

        self.ax_main.set_theta_zero_location('N')
        self.ax_main.set_theta_direction(-1)
        self.ax_main.set_title("Interactive Beamformer & Null Synthesis", fontsize=10, pad=12)

        self.ax_overlay.set_theta_zero_location('N')
        self.ax_overlay.set_theta_direction(-1)
        self.ax_overlay.set_title("Validation: Theory vs Sim vs Empirical", fontsize=10, pad=12)

        # ------------------------------------------------------------------
        # Sliders (right panel, x = 0.80 to 0.96)
        # ------------------------------------------------------------------
        slider_color = 'lightsteelblue'

        ax_sN = self.fig.add_axes([0.80, 0.88, 0.16, 0.025], facecolor=slider_color)
        self.slider_N = Slider(ax_sN, 'Elements N', 2, 16, valinit=self.N, valstep=1)

        ax_sd = self.fig.add_axes([0.80, 0.83, 0.16, 0.025], facecolor=slider_color)
        self.slider_d = Slider(ax_sd, 'd/lambda', 0.25, 1.00, valinit=self.d_ratio, valstep=0.01)

        ax_sb = self.fig.add_axes([0.80, 0.78, 0.16, 0.025], facecolor=slider_color)
        self.slider_beta = Slider(ax_sb, 'Phase beta(deg)', -180.0, 180.0,
                                  valinit=self.beta_deg, valstep=1.0)

        ax_sn = self.fig.add_axes([0.80, 0.70, 0.16, 0.025], facecolor='peachpuff')
        self.slider_null = Slider(ax_sn, 'Null Angle(deg)', 0.0, 350.0,
                                  valinit=self.null_angle_slider_val, valstep=1.0)

        # Null buttons
        ax_badd = self.fig.add_axes([0.80, 0.65, 0.075, 0.032])
        self.btn_add_null = Button(ax_badd, 'Add Null',
                                   color='lightblue', hovercolor='deepskyblue')

        ax_bclr = self.fig.add_axes([0.885, 0.65, 0.075, 0.032])
        self.btn_clear_null = Button(ax_bclr, 'Clear Nulls',
                                     color='lightcoral', hovercolor='salmon')

        # Amplitude Taper RadioButtons
        self.fig.text(0.80, 0.62, "Amplitude Taper:", fontsize=8, fontweight='bold')
        ax_taper = self.fig.add_axes([0.80, 0.52, 0.16, 0.09], facecolor='lightyellow')
        self.radio_taper = RadioButtons(
            ax_taper,
            labels=('Uniform', 'Chebyshev 30dB', 'Binomial'),
            active=0
        )
        for lbl in self.radio_taper.labels:
            lbl.set_fontsize(8)

        # ------------------------------------------------------------------
        # CSV Overlay Section
        # ------------------------------------------------------------------
        self.fig.text(0.80, 0.50, "Load & Compare CSVs:", fontsize=9, fontweight='bold')

        ax_tt = self.fig.add_axes([0.855, 0.44, 0.105, 0.03])
        self.txt_theory = TextBox(ax_tt, 'Theory: ', initial=self.theory_csv_path)

        ax_ts = self.fig.add_axes([0.855, 0.38, 0.105, 0.03])
        self.txt_sim = TextBox(ax_ts, 'Sim:    ', initial=self.sim_csv_path)

        ax_te = self.fig.add_axes([0.855, 0.32, 0.105, 0.03])
        self.txt_emp = TextBox(ax_te, 'Empiric:', initial=self.emp_csv_path)

        ax_bov = self.fig.add_axes([0.80, 0.25, 0.16, 0.038])
        self.btn_overlay = Button(ax_bov, 'Plot Overlay',
                                  color='palegreen', hovercolor='limegreen')

        ax_brc = self.fig.add_axes([0.80, 0.19, 0.16, 0.035])
        self.btn_recalc = Button(ax_brc, 'Update Theory CSV',
                                 color='thistle', hovercolor='violet')

        # ------------------------------------------------------------------
        # Metrics Info Box
        # ------------------------------------------------------------------
        self.info_text = self.fig.text(
            0.80, 0.04,
            "Metrics:\nD0: -- dBi\nHPBW: -- deg\nNulls: None",
            fontsize=8.5,
            family='monospace',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='whitesmoke', edgecolor='silver')
        )

        # Connect callbacks
        self.slider_N.on_changed(self.on_slider_update)
        self.slider_d.on_changed(self.on_slider_update)
        self.slider_beta.on_changed(self.on_slider_update)
        self.slider_null.on_changed(self.on_null_slider_change)
        self.btn_add_null.on_clicked(self.on_add_null)
        self.btn_clear_null.on_clicked(self.on_clear_nulls)
        self.btn_overlay.on_clicked(self.on_plot_overlay)
        self.btn_recalc.on_clicked(self.on_update_theory_csv)
        self.radio_taper.on_clicked(self.on_taper_change)

        # Initial draw
        self.update_main_plot()
        self.on_plot_overlay(None)

    # --------------------------------------------------------------------------
    # Callbacks
    # --------------------------------------------------------------------------
    def on_slider_update(self, val):
        self.N = int(self.slider_N.val)
        self.d_ratio = float(self.slider_d.val)
        self.beta_deg = float(self.slider_beta.val)
        self.update_main_plot()

    def on_null_slider_change(self, val):
        self.null_angle_slider_val = float(self.slider_null.val)

    def on_add_null(self, event):
        val = round(self.null_angle_slider_val, 1)
        if val not in self.null_list:
            self.null_list.append(val)
        self.update_main_plot()

    def on_clear_nulls(self, event):
        self.null_list = []
        self.update_main_plot()

    def on_update_theory_csv(self, event):
        # The overlay validates the physical Yagi, so regenerate its theory
        # curve from the latest data/optimized_dimensions.json
        generate_yagi_theoretical_csv(THEORETICAL_CSV)
        self.on_plot_overlay(None)

    # --------------------------------------------------------------------------
    # Taper Callback
    # --------------------------------------------------------------------------
    def on_taper_change(self, label):
        taper_map = {
            'Uniform':          'uniform',
            'Chebyshev 30dB':   'chebyshev',
            'Binomial':         'binomial',
        }
        self.taper = taper_map.get(label, 'uniform')
        self.update_main_plot()

    # --------------------------------------------------------------------------
    # Main Plot Update
    # --------------------------------------------------------------------------
    def update_main_plot(self):
        self.ax_main.cla()
        self.ax_main.set_theta_zero_location('N')
        self.ax_main.set_theta_direction(-1)

        d_m = self.d_ratio * LAMBDA
        beta_rad = np.radians(self.beta_deg)

        theta = np.linspace(0.0, 2.0 * np.pi, 3600)
        theta_eval = np.where(theta <= np.pi, theta, 2.0 * np.pi - theta)

        pat = total_pattern(theta_eval, N=self.N, d=d_m, beta=beta_rad, taper=self.taper)

        # Apply Schelkunoff nulls
        if self.null_list:
            null_w = compute_schelkunoff_factor(theta_eval, self.null_list, d_m, beta_rad)
            pat = pat * null_w

        max_p = np.max(pat)
        if max_p > 1e-12:
            pat = pat / max_p

        self.ax_main.plot(theta, pat, color='royalblue', linewidth=2.0, label='Array Pattern |E|')
        self.ax_main.fill(theta, pat, color='royalblue', alpha=0.15)

        # Mark null directions
        for n_ang in self.null_list:
            rad = np.radians(n_ang)
            self.ax_main.plot([rad, rad], [0.0, 1.0], color='crimson',
                              linestyle='--', linewidth=1.5)
            self.ax_main.scatter([rad], [1.0], color='crimson', s=35, zorder=5)

        # Metrics
        D0_dBi, _ = compute_directivity(N=self.N, d=d_m, beta=beta_rad, taper=self.taper)
        hpbw, th_max = compute_hpbw(N=self.N, d=d_m, beta=beta_rad, taper=self.taper)
        hpbw_str = "{:.1f} deg".format(hpbw) if hpbw is not None else "N/A"
        null_str = (", ".join(["{:.0f} deg".format(n) for n in self.null_list])
                    if self.null_list else "None")

        self.info_text.set_text(
            "Array Metrics:\n"
            "Frequency: {:.2f} GHz\n"
            "D0:        {:.2f} dBi\n"
            "HPBW:      {}\n"
            "Main Beam: {:.1f} deg\n"
            "Nulls:     {}".format(F0 / 1e9, D0_dBi, hpbw_str, th_max, null_str)
        )

        self.ax_main.set_title(
            "Interactive Pattern\nN={}, d={:.2f}*lambda, beta={:.0f} deg".format(
                self.N, self.d_ratio, self.beta_deg),
            fontsize=10, pad=12
        )
        self.ax_main.set_rlabel_position(45)
        self.ax_main.legend(loc='lower right', fontsize=8)

        # Refresh the live 3D spherical pattern with the same parameters
        self.update_3d_plot(d_m, beta_rad)

        self.fig.canvas.draw_idle()

    # --------------------------------------------------------------------------
    # Live 3D Spherical Radiation Pattern
    # --------------------------------------------------------------------------
    def update_3d_plot(self, d_m, beta_rad):
        """
        Redraws the 3D spherical radiation surface for the current N, d, beta,
        taper and active nulls. Uses a coarse mesh so it stays responsive while
        sliders are dragged. The ULA pattern is phi-independent, so the flat
        theta pattern (including Schelkunoff nulls) is revolved about the z-axis.
        """
        self.ax_3d.cla()

        # Coarse mesh for live responsiveness
        theta_vals = np.linspace(0.0, np.pi, 73)        # elevation
        phi_vals = np.linspace(0.0, 2.0 * np.pi, 73)    # azimuth
        THETA, PHI = np.meshgrid(theta_vals, phi_vals)

        E_flat = total_pattern(theta_vals, N=self.N, d=d_m,
                               beta=beta_rad, taper=self.taper)

        # Apply the same Schelkunoff nulls used on the 2D pattern (phi-independent)
        if self.null_list:
            E_flat = E_flat * compute_schelkunoff_factor(
                theta_vals, self.null_list, d_m, beta_rad)

        E_max = np.max(E_flat)
        if E_max > 1e-12:
            E_flat = E_flat / E_max
        R = np.tile(E_flat, (phi_vals.size, 1))

        X = R * np.sin(THETA) * np.cos(PHI)
        Y = R * np.sin(THETA) * np.sin(PHI)
        Z = R * np.cos(THETA)

        intensity = R ** 2
        facecolors = plt.cm.jet(intensity / (np.max(intensity) + 1e-12))

        self.ax_3d.plot_surface(X, Y, Z, facecolors=facecolors, linewidth=0,
                                antialiased=True, alpha=0.9, rstride=1, cstride=1)

        self.ax_3d.set_title(
            "Live 3D Spherical Pattern\nTaper: {}".format(self.taper),
            fontsize=10, pad=8)
        self.ax_3d.set_xlabel('X', fontsize=8)
        self.ax_3d.set_ylabel('Y', fontsize=8)
        self.ax_3d.set_zlabel('Z (axis)', fontsize=8)
        self.ax_3d.tick_params(labelsize=6)
        # Keep the lobe centered and proportional
        try:
            self.ax_3d.set_box_aspect((1, 1, 1))
        except Exception:
            pass
        self.ax_3d.set_xlim(-1, 1)
        self.ax_3d.set_ylim(-1, 1)
        self.ax_3d.set_zlim(-1, 1)

    # --------------------------------------------------------------------------
    # Overlay Plot
    # --------------------------------------------------------------------------
    def on_plot_overlay(self, event):
        self.ax_overlay.cla()
        self.ax_overlay.set_theta_zero_location('N')
        self.ax_overlay.set_theta_direction(-1)
        self.ax_overlay.set_rlabel_position(45)

        theory_file = self.txt_theory.text.strip()
        sim_file = self.txt_sim.text.strip()
        emp_file = self.txt_emp.text.strip()

        plots_count = 0

        def overlay_csv(filepath, color, style, label):
            ang, gain = load_pattern_csv(filepath)
            if ang is None:
                return 0
            g_lin = 10.0 ** (gain / 20.0)
            max_g = np.max(g_lin)
            if max_g > 1e-12:
                g_lin /= max_g
            ang_loop = np.append(ang, ang[0])
            g_loop = np.append(g_lin, g_lin[0])
            self.ax_overlay.plot(ang_loop, g_loop, color=color,
                                 linestyle=style, linewidth=2.0, label=label)
            return 1

        plots_count += overlay_csv(theory_file, 'blue', '-', 'Theory')
        plots_count += overlay_csv(sim_file, 'red', '--', 'Simulation')
        plots_count += overlay_csv(emp_file, 'darkgreen', ':', 'Empirical')

        if plots_count == 0:
            self.ax_overlay.set_title(
                "No CSV Files Found\nClick 'Update Theory CSV' first",
                fontsize=9, pad=12)
        else:
            self.ax_overlay.set_title(
                "Overlay Comparison ({} source(s))".format(plots_count),
                fontsize=10, pad=12)
            self.ax_overlay.legend(loc='lower right', fontsize=8)

        self.fig.canvas.draw_idle()


# ------------------------------------------------------------------------------
# Entry Point
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("  2.4 GHz Antenna Array Dashboard  (Member 1 - GUI)")
    print("  Matplotlib Interactive Widgets Interface")
    print("  Close the window to exit.")
    print("=" * 60)
    dashboard = AntennaDashboard()
    plt.show(block=True)
