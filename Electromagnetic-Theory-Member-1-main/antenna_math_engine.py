# antenna_math_engine.py - analytical EM engine (Project Lead)
# 2.44 GHz dipole array + 4 element Yagi-Uda

import os
import sys
import csv
import warnings
import numpy as np
from scipy import integrate
from scipy.special import comb
from scipy.signal.windows import chebwin
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from emt_config import (C0, F0, LAMBDA, Z0, SWEEP_START_HZ, SWEEP_STOP_HZ,
                        PATTERN_STEP_DEG, THEORETICAL_CSV, SIMULATED_CSV,
                        ensure_data_dir, load_dimensions)

ETA0 = 120.0 * np.pi
MU0 = ETA0 / C0
K0 = 2.0 * np.pi / LAMBDA
L_DIPOLE = LAMBDA / 2.0


def out(name):
    return os.path.join(HERE, name)


# ---------------- radiation integrals ----------------

def dipole_current(z, L, Im=1.0, k=K0):
    return Im * np.sin(k * (L / 2 - np.abs(z)))


def vector_potential_Az(theta, L, r=1.0, Im=1.0, k=K0, n=2001):
    # A_z = mu0 e^(-jkr) / (4 pi r) * int I(z') e^(jkz' cos(theta)) dz'
    theta = np.atleast_1d(np.asarray(theta, dtype=float))
    z = np.linspace(-L / 2, L / 2, n)
    I = dipole_current(z, L, Im, k)
    phase = np.exp(1j * k * np.outer(np.cos(theta), z))
    integral = integrate.trapezoid(I * phase, z, axis=1)
    return MU0 * np.exp(-1j * k * r) / (4 * np.pi * r) * integral


def poynting_vector(E_theta, H_phi):
    return 0.5 * np.real(E_theta * np.conj(H_phi))


def dipole_far_fields(theta, L, r=1.0, Im=1.0, k=K0):
    theta = np.atleast_1d(np.asarray(theta, dtype=float))
    Az = vector_potential_Az(theta, L, r, Im, k)
    E_theta = 1j * k * C0 * Az * np.sin(theta)
    H_phi = E_theta / ETA0
    return {"A_z": Az, "E_theta": E_theta, "H_phi": H_phi,
            "W_r": poynting_vector(E_theta, H_phi)}


def dipole_radiated_power(L, Im=1.0, k=K0, r=100.0):
    th = np.linspace(1e-6, np.pi - 1e-6, 2001)
    W = dipole_far_fields(th, L, r, Im, k)["W_r"]
    P = 2 * np.pi * integrate.simpson(W * r ** 2 * np.sin(th), x=th)
    return float(P), float(2 * P / abs(Im) ** 2)    # P_rad, R_rad


def dipole_element_factor(cos_t, L, k=K0):
    # [cos(kh cos t) - cos(kh)] / sin t, any length
    cos_t = np.asarray(cos_t, dtype=float)
    sin_t = np.sqrt(np.clip(1 - cos_t ** 2, 0, 1))
    kh = k * L / 2
    with np.errstate(divide='ignore', invalid='ignore'):
        return np.where(sin_t > 1e-9, (np.cos(kh * cos_t) - np.cos(kh)) / sin_t, 0.0)


# ---------------- linear array ----------------

def element_factor(theta):
    theta = np.asarray(theta, dtype=float)
    s = np.sin(theta)
    with np.errstate(divide='ignore', invalid='ignore'):
        F = np.where(np.abs(s) > 1e-12, np.cos(0.5 * np.pi * np.cos(theta)) / s, 0.0)
    return np.abs(F)


def get_taper_weights(N, taper='uniform', sll_db=30.0):
    if taper == 'chebyshev':
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            w = chebwin(N, float(sll_db))
    elif taper == 'binomial':
        w = np.array([float(comb(N - 1, k)) for k in range(N)])
    else:
        w = np.ones(N)
    return w / np.max(np.abs(w))


def array_factor(theta, N=4, d=None, beta=0.0, taper='uniform', sll_db=30.0):
    # array along z (collinear), theta from the array axis
    if d is None:
        d = LAMBDA / 2
    psi = np.atleast_1d(K0 * d * np.cos(np.asarray(theta, dtype=float)) + beta)
    w = get_taper_weights(N, taper, sll_db)
    AF = np.abs(np.sum(w[:, None] * np.exp(1j * np.outer(np.arange(N), psi)), axis=0))
    AF = AF / np.sum(np.abs(w))
    if np.isscalar(theta):
        return float(AF[0])
    return AF


def total_pattern(theta, N=4, d=None, beta=0.0, taper='uniform', sll_db=30.0):
    return element_factor(theta) * array_factor(theta, N, d, beta, taper, sll_db)


def compute_directivity(N=4, d=None, beta=0.0, taper='uniform', sll_db=30.0):
    f = lambda th: total_pattern(th, N, d, beta, taper, sll_db) ** 2 * np.sin(th)
    P = 2 * np.pi * integrate.quad(f, 0, np.pi, limit=200)[0]
    th = np.linspace(0, np.pi, 20000)
    U_max = np.max(total_pattern(th, N, d, beta, taper, sll_db) ** 2)
    if P <= 1e-15:
        return 0.0, 1.0
    D = 4 * np.pi * U_max / P
    return float(10 * np.log10(D)), float(D)


def compute_hpbw(N=4, d=None, beta=0.0, taper='uniform', sll_db=30.0):
    th = np.linspace(1e-6, np.pi - 1e-6, 50000)
    pat = total_pattern(th, N, d, beta, taper, sll_db)
    i = int(np.argmax(pat))
    th_max = float(np.degrees(th[i]))
    if pat[i] < 1e-6:
        return None, th_max
    below = pat < pat[i] / np.sqrt(2)
    left = np.where(below[:i])[0]
    right = np.where(below[i:])[0]
    if len(left) == 0 or len(right) == 0:
        return None, th_max
    return float(np.degrees(th[i + right[0]] - th[left[-1]])), th_max


def compute_vswr(Z_in, Z0_ref=50.0):
    if abs(Z_in + Z0_ref) < 1e-12:
        return complex(1, 0), float('inf'), 0.0
    G = (Z_in - Z0_ref) / (Z_in + Z0_ref)
    g = abs(G)
    if g >= 1 - 1e-12:
        return G, float('inf'), 0.0
    return G, float((1 + g) / (1 - g)), float(20 * np.log10(max(g, 1e-12)))


# ---------------- induced EMF impedance ----------------

def mutual_impedance(L1, L2, rho, k=K0):
    # Z21 between parallel dipoles (referred to current maxima).
    # rho = wire radius gives the self impedance.
    h1, h2 = L1 / 2, L2 / 2
    n = int(max(2001, np.ceil(L2 / (rho / 100)) + 1))
    z = np.linspace(-h2, h2, n)
    R1 = np.sqrt(rho ** 2 + (z - h1) ** 2)
    R2 = np.sqrt(rho ** 2 + (z + h1) ** 2)
    R0 = np.sqrt(rho ** 2 + z ** 2)
    Ez = -1j * ETA0 / (4 * np.pi) * (np.exp(-1j * k * R1) / R1 + np.exp(-1j * k * R2) / R2
                                    - 2 * np.cos(k * h1) * np.exp(-1j * k * R0) / R0)
    return complex(-integrate.trapezoid(Ez * np.sin(k * (h2 - np.abs(z))), z))


def build_impedance_matrix(N=4, d=None):
    if d is None:
        d = LAMBDA / 2
    Z = np.zeros((N, N), dtype=complex)
    for m in range(N):
        Z[np.abs(np.subtract.outer(range(N), range(N))) == m] = (
            complex(73.13, 42.54) if m == 0 else mutual_impedance(L_DIPOLE, L_DIPOLE, m * d))
    return Z


def driving_point_impedance(N=4, d=None):
    # element 0 fed, the rest shorted
    Z = build_impedance_matrix(N, d)
    V = np.zeros(N)
    V[0] = 1
    return complex(1 / np.linalg.solve(Z, V)[0])


def active_impedance(N=4, d=None, beta=0.0, taper='uniform', sll_db=30.0):
    Z = build_impedance_matrix(N, d)
    I = get_taper_weights(N, taper, sll_db) * np.exp(1j * beta * np.arange(N))
    return (Z @ I) / I


# ---------------- planar array ----------------
# Nx x Ny grid in the x-y plane, half-wave dipoles parallel to x, broadside = z

def x_dipole_factor(theta, phi):
    c = np.sin(theta) * np.cos(phi)      # cos of angle from the x axis
    s = np.sqrt(np.clip(1 - c ** 2, 0, 1))
    with np.errstate(divide='ignore', invalid='ignore'):
        return np.abs(np.where(s > 1e-12, np.cos(0.5 * np.pi * c) / s, 0.0))


def planar_array_factor(theta, phi, Nx=4, Ny=4, dx=None, dy=None, beta_x=0.0, beta_y=0.0,
                        taper='uniform', sll_db=30.0):
    dx = LAMBDA / 2 if dx is None else dx
    dy = LAMBDA / 2 if dy is None else dy
    theta, phi = np.asarray(theta, dtype=float), np.asarray(phi, dtype=float)

    def af_1d(N, psi):
        w = get_taper_weights(N, taper, sll_db)
        n = np.arange(N).reshape((N,) + (1,) * psi.ndim)
        return np.abs(np.sum(w.reshape(n.shape) * np.exp(1j * n * psi), axis=0)) / np.sum(w)

    psi_x = K0 * dx * np.sin(theta) * np.cos(phi) + beta_x
    psi_y = K0 * dy * np.sin(theta) * np.sin(phi) + beta_y
    return af_1d(Nx, psi_x) * af_1d(Ny, psi_y)


def planar_pattern(theta, phi, **kw):
    return x_dipole_factor(theta, phi) * planar_array_factor(theta, phi, **kw)


def planar_steering_phases(theta0_deg, phi0_deg, dx=None, dy=None):
    # phases that put the main beam at (theta0, phi0)
    dx = LAMBDA / 2 if dx is None else dx
    dy = LAMBDA / 2 if dy is None else dy
    t0, p0 = np.radians(theta0_deg), np.radians(phi0_deg)
    return -K0 * dx * np.sin(t0) * np.cos(p0), -K0 * dy * np.sin(t0) * np.sin(p0)


def planar_directivity(n_theta=361, n_phi=721, **kw):
    th = np.linspace(0, np.pi, n_theta)
    ph = np.linspace(0, 2 * np.pi, n_phi)
    TH, PH = np.meshgrid(th, ph, indexing='ij')
    U = planar_pattern(TH, PH, **kw) ** 2
    P = integrate.simpson(integrate.simpson(U * np.sin(TH), x=th, axis=0), x=ph)
    i, j = np.unravel_index(np.argmax(U), U.shape)
    D = 4 * np.pi * U[i, j] / P
    return float(10 * np.log10(D)), float(D), float(np.degrees(th[i])), float(np.degrees(ph[j]))


# ---------------- Yagi-Uda ----------------
# elements along z, boom along x, directors at +x -> beam at phi = 0

YAGI_ELEMENTS = ("reflector", "driven_dipole", "director_1", "director_2")


def load_yagi_design(dims=None):
    if dims is None:
        dims = load_dimensions()
    if dims is None:
        raise FileNotFoundError("data/optimized_dimensions.json missing, run EMT_Member2/simulate_yagi.py")
    pos = dims["boom_positions_mm"]
    return {
        "names": YAGI_ELEMENTS,
        "lengths_m": np.array([dims[e + "_length_mm"] for e in YAGI_ELEMENTS]) / 1000,
        "x_m": np.array([pos[e] - pos["driven_dipole"] for e in YAGI_ELEMENTS]) / 1000,
        "radius_m": dims["wire_radius_mm"] / 1000,
        "feed_index": 1,
        "source": dims.get("_source", ""),
    }


def yagi_impedance_matrix(design, freq_hz=F0):
    k = 2 * np.pi * freq_hz / C0
    L, x = design["lengths_m"], design["x_m"]
    n = len(L)
    Z = np.zeros((n, n), dtype=complex)
    for i in range(n):
        for j in range(i, n):
            rho = design["radius_m"] if i == j else abs(x[i] - x[j])
            # convert from current-maximum to terminal current
            Z[i, j] = Z[j, i] = mutual_impedance(L[i], L[j], rho, k) / (
                np.sin(k * L[i] / 2) * np.sin(k * L[j] / 2))
    return Z


def solve_yagi(design=None, freq_hz=F0):
    if design is None:
        design = load_yagi_design()
    k = 2 * np.pi * freq_hz / C0
    V = np.zeros(len(design["lengths_m"]))
    V[design["feed_index"]] = 1.0
    I = np.linalg.solve(yagi_impedance_matrix(design, freq_hz), V)
    return {"design": design, "k": k, "I_base": I,
            "I_max": I / np.sin(k * design["lengths_m"] / 2),
            "Z_in": complex(1 / I[design["feed_index"]])}


def yagi_sum(cos_t, ux, sol):
    # E_theta = j eta e^(-jkr)/(2 pi r) * sum Im_n F_n e^(jk x_n ux),  ux = sin t cos phi
    d, k = sol["design"], sol["k"]
    return sum(Im * dipole_element_factor(cos_t, L, k) * np.exp(1j * k * x * ux)
               for Im, L, x in zip(sol["I_max"], d["lengths_m"], d["x_m"]))


def yagi_radiated_power(sol):
    th = np.linspace(0, np.pi, 181)
    ph = np.linspace(0, 2 * np.pi, 361)
    TH, PH = np.meshgrid(th, ph, indexing='ij')
    U = ETA0 / (8 * np.pi ** 2) * np.abs(yagi_sum(np.cos(TH), np.sin(TH) * np.cos(PH), sol)) ** 2
    return float(integrate.simpson(integrate.simpson(U * np.sin(TH), x=th, axis=0), x=ph))


def yagi_h_plane(angles_deg, sol, P_rad):
    phi = np.radians(np.asarray(angles_deg, dtype=float))
    U = ETA0 / (8 * np.pi ** 2) * np.abs(yagi_sum(np.zeros_like(phi), np.cos(phi), sol)) ** 2
    return 4 * np.pi * U / P_rad


def yagi_e_plane(angles_deg, sol, P_rad):
    # angle 0 = along boom, 90 = along the elements
    a = np.radians(np.asarray(angles_deg, dtype=float))
    U = ETA0 / (8 * np.pi ** 2) * np.abs(yagi_sum(np.sin(a), np.cos(a), sol)) ** 2
    return 4 * np.pi * U / P_rad


def cut_hpbw(angles_deg, p):
    n = len(p)
    step = angles_deg[1] - angles_deg[0]
    i0 = int(np.argmax(p))
    half = p[i0] / 2
    width = 0.0
    for s in (1, -1):
        for j in range(1, n // 2):
            a, b = p[(i0 + s * (j - 1)) % n], p[(i0 + s * j) % n]
            if b < half:
                width += (j - 1) + (a - half) / (a - b)
                break
        else:
            return None
    return float(width * step)


def yagi_metrics(design=None, freq_hz=F0):
    sol = solve_yagi(design, freq_hz)
    P_rad = yagi_radiated_power(sol)
    ang = np.arange(0, 360, 0.1)
    Dh = yagi_h_plane(ang, sol, P_rad)
    De = yagi_e_plane(ang, sol, P_rad)
    G, vswr, s11 = compute_vswr(sol["Z_in"], Z0)
    feed = sol["design"]["feed_index"]
    I_feed = sol["I_base"][feed]
    P_in = 0.5 * abs(I_feed) ** 2 * sol["Z_in"].real
    return {
        "sol": sol, "Z_in": sol["Z_in"], "Gamma": G, "vswr": vswr, "S11_dB": s11,
        "P_rad_W": P_rad, "P_in_W": P_in,
        "power_balance_pct": 100 * (P_rad - P_in) / P_in,
        "D0_dBi": float(10 * np.log10(max(Dh.max(), De.max()))),
        "front_to_back_dB": float(10 * np.log10(Dh[0] / Dh[len(ang) // 2])),
        "hpbw_h_deg": cut_hpbw(ang, Dh),
        "hpbw_e_deg": cut_hpbw(ang, De),
        "currents": [(nm, abs(i), np.degrees(np.angle(i)))
                     for nm, i in zip(YAGI_ELEMENTS, sol["I_base"] / I_feed)],
    }


def yagi_impedance_sweep(freqs, design=None):
    if design is None:
        design = load_yagi_design()
    return np.array([solve_yagi(design, f)["Z_in"] for f in freqs])


# ---------------- CSV ----------------

def write_pattern_csv(filename, angles, gain):
    with open(filename, 'w', newline='', encoding='ascii') as f:
        w = csv.writer(f)
        w.writerow(["angle_deg", "gain_dBi"])
        for a, g in zip(angles, gain):
            w.writerow([int(a), "{:.2f}".format(g)])
    print("  [Saved] {}".format(os.path.basename(filename)))


def generate_yagi_theoretical_csv(filename=THEORETICAL_CSV, design=None, freq_hz=F0, metrics=None):
    # H-plane cut, same convention as Member 2's csv (40 dB floor)
    if metrics is None:
        metrics = yagi_metrics(design, freq_hz)
    ang = np.arange(0, 360, PATTERN_STEP_DEG)
    D = yagi_h_plane(ang, metrics["sol"], metrics["P_rad_W"])
    D = np.maximum(D, D.max() * 1e-4)
    os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
    write_pattern_csv(filename, ang, 10 * np.log10(D))
    return ang, 10 * np.log10(D)


def generate_theoretical_csv(filename=out("ula_theoretical_pattern.csv"), N=4, d=None, beta=0.0):
    # ULA version (the team overlay uses the Yagi one)
    D0, _ = compute_directivity(N, d, beta)
    ang = np.arange(0, 360, 10)
    th = np.radians(ang)
    E = total_pattern(np.where(th <= np.pi, th, 2 * np.pi - th), N, d, beta)
    p = np.maximum((E / E.max()) ** 2, 1e-4)
    write_pattern_csv(filename, ang, 10 * np.log10(p) + D0)


# ---------------- plots ----------------

def full_circle(N, d, beta, taper='uniform'):
    th = np.linspace(0, 2 * np.pi, 3600)
    pat = total_pattern(np.where(th <= np.pi, th, 2 * np.pi - th), N, d, beta, taper)
    return th, pat / pat.max()


def polar_axes(ax):
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)


def plot_polar_pattern(N=4, d=None, beta=0.0, filename=out("radiation_pattern_polar.png")):
    d = LAMBDA / 2 if d is None else d
    th, pat = full_circle(N, d, beta)
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(8, 8))
    ax.plot(th, pat, color='royalblue', lw=2, label='Normalized |E(theta)|')
    ax.fill(th, pat, color='royalblue', alpha=0.15)
    ax.set_title("2.4 GHz Phased Array Radiation Pattern\nN={}, d={:.2f}*lambda, beta={:.1f} deg | f0=2.44 GHz"
                 .format(N, d / LAMBDA, np.degrees(beta)), fontsize=12, pad=20)
    polar_axes(ax)
    ax.set_rlabel_position(45)
    ax.legend(loc='lower right', fontsize=9)
    fig.tight_layout()
    fig.savefig(filename, dpi=150)
    plt.close(fig)
    print("  [Saved] {}".format(os.path.basename(filename)))


def plot_beam_steering(N=4, d=None, filename=out("beam_steering.png")):
    d = LAMBDA / 2 if d is None else d
    betas = np.linspace(-np.pi / 2, np.pi / 2, 7)
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(9, 8))
    for b, c in zip(betas, plt.cm.viridis(np.linspace(0, 1, len(betas)))):
        th, pat = full_circle(N, d, b)
        ax.plot(th, pat, color=c, lw=1.5, label="beta = {:+.0f} deg".format(np.degrees(b)))
    ax.set_title("Beam Steering vs Progressive Phase (beta)\nN={}, d={:.2f}*lambda | f0=2.44 GHz"
                 .format(N, d / LAMBDA), fontsize=12, pad=20)
    polar_axes(ax)
    ax.legend(loc='lower right', bbox_to_anchor=(1.30, -0.05), fontsize=8)
    fig.tight_layout()
    fig.savefig(filename, dpi=150)
    plt.close(fig)
    print("  [Saved] {}".format(os.path.basename(filename)))


def plot_vswr_s11_sweep(f_start=SWEEP_START_HZ, f_stop=SWEEP_STOP_HZ, nf=201,
                        filename=out("vswr_s11_sweep.png"), design=None):
    freqs = np.linspace(f_start, f_stop, nf)
    Zin = yagi_impedance_sweep(freqs, design)
    vswr = np.array([min(compute_vswr(z, Z0)[1], 10.0) for z in Zin])
    s11 = np.array([compute_vswr(z, Z0)[2] for z in Zin])
    f = freqs / 1e9
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7))
    ax1.plot(f, vswr, color='navy', lw=2, label='Yagi VSWR')
    ax1.axhline(2.0, color='red', ls='--', lw=1.2, label='VSWR = 2')
    ax1.set_ylim(1, 10)
    ax1.set_ylabel('VSWR')
    ax1.set_title('VSWR vs Frequency - 4 element Yagi')
    ax2.plot(f, s11, color='crimson', lw=2, label='S11')
    ax2.axhline(-9.54, color='blue', ls='--', lw=1.2, label='-9.54 dB (VSWR 2)')
    ax2.set_ylabel('S11 (dB)')
    ax2.set_title('S11 vs Frequency')
    for ax in (ax1, ax2):
        ax.axvline(F0 / 1e9, color='green', ls=':', lw=1.2, label='f0 = 2.44 GHz')
        ax.set_xlabel('Frequency (GHz)')
        ax.grid(True, ls=':', alpha=0.6)
        ax.legend(loc='upper right')
    fig.tight_layout()
    fig.savefig(filename, dpi=150)
    plt.close(fig)
    print("  [Saved] {}".format(os.path.basename(filename)))
    return freqs, Zin


def plot_yagi_patterns(m, filename=out("yagi_theory_vs_sim.png")):
    ang = np.arange(0, 360.5, 0.5)
    gh = 10 * np.log10(np.maximum(yagi_h_plane(ang, m["sol"], m["P_rad_W"]), 1e-12))
    ge = 10 * np.log10(np.maximum(yagi_e_plane(ang, m["sol"], m["P_rad_W"]), 1e-12))
    rmax = np.ceil(m["D0_dBi"] / 5) * 5 + 5
    rmin = rmax - 30
    fig, axes = plt.subplots(1, 2, subplot_kw={'projection': 'polar'}, figsize=(13, 6.5))
    titles = ["H-plane (azimuth, measured)\nHPBW {:.0f} deg, F/B {:.1f} dB".format(m["hpbw_h_deg"], m["front_to_back_dB"]),
              "E-plane\nHPBW {:.0f} deg".format(m["hpbw_e_deg"])]
    for ax, g, t in zip(axes, (gh, ge), titles):
        ax.plot(np.radians(ang), np.maximum(g, rmin), color='royalblue', lw=2, label='Theory')
        polar_axes(ax)
        ax.set_rlim(rmin, rmax)
        ax.set_rlabel_position(45)
        ax.set_title(t, fontsize=10, pad=14)
    if os.path.exists(SIMULATED_CSV):
        sim = np.genfromtxt(SIMULATED_CSV, delimiter=',', skip_header=1)
        a = np.append(sim[:, 0], 360)
        g = np.append(sim[:, 1], sim[0, 1])
        axes[0].plot(np.radians(a), np.maximum(g, rmin), 'o--', color='crimson', ms=3, lw=1.5, label='Simulated (Member 2)')
    for ax in axes:
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.06), ncol=2, fontsize=8)
    fig.suptitle("4 element Yagi-Uda, directivity in dBi (D0 = {:.2f} dBi)".format(m["D0_dBi"]), fontsize=12)
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    fig.savefig(filename, dpi=150)
    plt.close(fig)
    print("  [Saved] {}".format(os.path.basename(filename)))


def plot_3d_spherical_pattern(N=4, d=None, beta=0.0, taper='uniform',
                              filename=out("radiation_3d_spherical.png")):
    d = LAMBDA / 2 if d is None else d
    th = np.linspace(0, np.pi, 181)
    ph = np.linspace(0, 2 * np.pi, 361)
    TH, PH = np.meshgrid(th, ph)
    E = total_pattern(th, N, d, beta, taper)
    R = np.tile(E / E.max(), (ph.size, 1))
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    ax.plot_surface(R * np.sin(TH) * np.cos(PH), R * np.sin(TH) * np.sin(PH), R * np.cos(TH),
                    facecolors=plt.cm.jet(R ** 2), linewidth=0, antialiased=True,
                    alpha=0.85, rstride=2, cstride=2)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z (Array Axis)')
    ax.set_title("3D Spherical Radiation Pattern\nN={}, d={:.2f}*lambda, beta={:.0f} deg, Taper: {}  |  f0=2.44 GHz"
                 .format(N, d / LAMBDA, np.degrees(beta), taper), fontsize=11, pad=12)
    sm = plt.cm.ScalarMappable(cmap='jet')
    sm.set_array((R ** 2).ravel())
    fig.colorbar(sm, ax=ax, shrink=0.5, aspect=12, pad=0.1).set_label('Normalized Power', fontsize=9)
    fig.tight_layout()
    fig.savefig(filename, dpi=150)
    plt.close(fig)
    print("  [Saved] {}".format(os.path.basename(filename)))


def plot_planar_3d(Nx=4, Ny=4, theta0=0.0, phi0=0.0, taper='uniform',
                   filename=out("planar_array_3d.png")):
    bx, by = planar_steering_phases(theta0, phi0)
    th = np.linspace(0, np.pi, 181)
    ph = np.linspace(0, 2 * np.pi, 361)
    TH, PH = np.meshgrid(th, ph, indexing='ij')
    R = planar_pattern(TH, PH, Nx=Nx, Ny=Ny, beta_x=bx, beta_y=by, taper=taper)
    R = R / R.max()
    D0, _, tpk, ppk = planar_directivity(Nx=Nx, Ny=Ny, beta_x=bx, beta_y=by, taper=taper)
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    ax.plot_surface(R * np.sin(TH) * np.cos(PH), R * np.sin(TH) * np.sin(PH), R * np.cos(TH),
                    facecolors=plt.cm.jet(R ** 2), linewidth=0, antialiased=True,
                    alpha=0.85, rstride=2, cstride=2)
    ax.set_xlabel('X (dipole axis)')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z (broadside)')
    ax.set_box_aspect((1, 1, 1))
    ax.set_title("Planar Array {}x{}, d = 0.5 lambda, steered to theta={:.0f}, phi={:.0f} deg\n"
                 "D0 = {:.2f} dBi, peak at theta={:.1f}, phi={:.1f} deg"
                 .format(Nx, Ny, theta0, phi0, D0, tpk, ppk), fontsize=11, pad=12)
    fig.tight_layout()
    fig.savefig(filename, dpi=150)
    plt.close(fig)
    print("  [Saved] {}".format(os.path.basename(filename)))


def compare_tapers(N=4, d=None, beta=0.0, filename=out("taper_comparison.png")):
    d = LAMBDA / 2 if d is None else d
    fig, axes = plt.subplots(1, 3, subplot_kw={"projection": "polar"}, figsize=(15, 5))
    for ax, (tp, col, lbl) in zip(axes, [("uniform", "royalblue", "Uniform"),
                                        ("chebyshev", "crimson", "Dolph-Chebyshev (30 dB SLL)"),
                                        ("binomial", "forestgreen", "Binomial")]):
        th, pat = full_circle(N, d, beta, tp)
        ax.plot(th, pat, color=col, lw=2)
        ax.fill(th, pat, color=col, alpha=0.15)
        polar_axes(ax)
        ax.set_title(lbl, fontsize=10, pad=12)
    fig.suptitle("Amplitude Taper Comparison  |  N={}, d={:.2f}lambda, f0=2.44 GHz".format(N, d / LAMBDA),
                 fontsize=12, y=1.02)
    fig.tight_layout()
    fig.savefig(filename, dpi=150)
    plt.close(fig)
    print("  [Saved] {}".format(os.path.basename(filename)))


if __name__ == "__main__":
    N, d, beta = 4, LAMBDA / 2, 0.0

    print("=" * 60)
    print("ANTENNA MATH ENGINE  (f0 = {:.2f} GHz, lambda = {:.3f} cm)".format(F0 / 1e9, LAMBDA * 100))
    print("=" * 60)
    print("R_rad of lambda/2 dipole (Poynting) : {:.2f} Ohm".format(dipole_radiated_power(L_DIPOLE)[1]))

    print("\n-- {} element ULA, d = {:.2f} lambda --".format(N, d / LAMBDA))
    D0, _ = compute_directivity(N, d, beta)
    hpbw, peak = compute_hpbw(N, d, beta)
    Z = build_impedance_matrix(N, d)
    print("D0 = {:.2f} dBi, HPBW = {:.2f} deg at {:.1f} deg".format(D0, hpbw, peak))
    print("Z11 = {:.2f}, Z12 = {:.2f} Ohm".format(Z[0, 0], Z[0, 1]))
    print("Z_active = " + ", ".join("{:.1f}".format(z) for z in active_impedance(N, d, beta)))

    print("\n-- planar array, d = 0.5 lambda --")
    for nx, ny in ((4, 4), (8, 8)):
        print("{}x{} broadside: D0 = {:.2f} dBi".format(nx, ny, planar_directivity(Nx=nx, Ny=ny)[0]))
    bx, by = planar_steering_phases(30, 45)
    D0p, _, tpk, ppk = planar_directivity(Nx=4, Ny=4, beta_x=bx, beta_y=by)
    print("4x4 steered to (30, 45): beta_x = {:.1f}, beta_y = {:.1f} deg, peak at ({:.1f}, {:.1f}), D0 = {:.2f} dBi"
          .format(np.degrees(bx), np.degrees(by), tpk, ppk, D0p))

    print("\n-- Yagi-Uda (induced EMF) --")
    design = load_yagi_design()
    for nm, L, x in zip(design["names"], design["lengths_m"], design["x_m"]):
        print("{:<14s} L = {:5.1f} mm  x = {:+6.1f} mm".format(nm, L * 1000, x * 1000))
    m = yagi_metrics(design)
    for nm, mag, ph in m["currents"]:
        print("I {:<12s} {:.3f} at {:+.1f} deg".format(nm, mag, ph))
    print("Z_in = {:.2f} Ohm, VSWR = {:.3f}, S11 = {:.2f} dB".format(m["Z_in"], m["vswr"], m["S11_dB"]))
    print("D0 = {:.2f} dBi, F/B = {:.2f} dB".format(m["D0_dBi"], m["front_to_back_dB"]))
    print("HPBW H = {:.1f} deg, E = {:.1f} deg".format(m["hpbw_h_deg"], m["hpbw_e_deg"]))
    print("P_rad vs P_in difference = {:+.2f} %".format(m["power_balance_pct"]))

    print("\nsaving outputs...")
    ensure_data_dir()
    generate_yagi_theoretical_csv(metrics=m)
    plot_yagi_patterns(m)
    freqs, Zin = plot_vswr_s11_sweep(design=design)
    band = freqs[np.array([compute_vswr(z, Z0)[1] for z in Zin]) < 2]
    if band.size:
        print("VSWR < 2 from {:.3f} to {:.3f} GHz".format(band[0] / 1e9, band[-1] / 1e9))
    plot_polar_pattern(N, d, beta)
    plot_beam_steering(N, d)
    plot_3d_spherical_pattern(N, d, beta)
    compare_tapers(N, d, beta)
    plot_planar_3d(4, 4, theta0=30, phi0=45)
    print("done")
