# ==============================================================================
# antenna_math_engine.py
# 2.4 GHz Phased Array Antenna - Analytical Electromagnetics Engine
# Project Lead: Analytical EM Modeling & Theoretical Pattern Generator
# ==============================================================================
# Pure ASCII implementation: No unicode characters used anywhere.
# Compliant with Python 3.12, Windows, numpy, scipy, and matplotlib.
# ==============================================================================

import os
import csv
import numpy as np
from scipy import integrate
from scipy.special import comb as scipy_comb
from scipy.signal.windows import chebwin
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
import matplotlib.pyplot as plt

# ------------------------------------------------------------------------------
# 1. Physical Constants & Design Parameters (2.44 GHz ISM Band)
# ------------------------------------------------------------------------------
C0 = 299792458.0              # Speed of light in vacuum (m/s)
ETA0 = 120.0 * np.pi          # Intrinsic impedance of free space (approx 376.73 Ohm)
F0 = 2.44e9                   # Center frequency: 2.44 GHz
LAMBDA = C0 / F0              # Free-space wavelength (m) ~= 0.122866 m (12.29 cm)
K0 = 2.0 * np.pi / LAMBDA     # Free-space wavenumber (rad/m)
L_DIPOLE = LAMBDA / 2.0       # Resonant half-wave dipole length (m)
Z0 = 50.0                     # System reference characteristic impedance (Ohm)


# ------------------------------------------------------------------------------
# 2. Element Factor: Half-Wave Dipole
# ------------------------------------------------------------------------------
def element_factor(theta):
    """
    Computes far-field element radiation pattern F(theta) for a z-directed
    half-wave dipole of length L = lambda / 2.
    Formula: F(theta) = cos((pi/2) * cos(theta)) / sin(theta)

    Parameters:
        theta : float or np.ndarray
            Elevation angle in radians measured from dipole axis (z-axis).

    Returns:
        np.ndarray or float
            Normalized element field magnitude pattern (0.0 to 1.0).
    """
    theta_arr = np.asarray(theta, dtype=float)
    s = np.sin(theta_arr)
    # Handle singularity at theta = 0 and theta = pi using L'Hopital limit (-> 0)
    with np.errstate(divide='ignore', invalid='ignore'):
        F = np.where(
            np.abs(s) > 1e-12,
            np.cos(0.5 * np.pi * np.cos(theta_arr)) / s,
            0.0
        )
    return np.abs(F)


# ------------------------------------------------------------------------------
# 3a. Amplitude Taper Weight Generators
# ------------------------------------------------------------------------------
def get_taper_weights(N, taper='uniform', sll_db=30.0):
    """
    Returns a real-valued amplitude excitation weight vector of length N.

    Parameters:
        N       : int    Number of elements.
        taper   : str    'uniform'   - equal weights (default)
                         'chebyshev' - Dolph-Chebyshev, minimizes HPBW for given SLL
                         'binomial'  - maximally smooth, no sidelobes, wide beam
        sll_db  : float  Target sidelobe attenuation in dB for Chebyshev taper (e.g. 30.0).

    Returns:
        np.ndarray of shape (N,), dtype float64, normalized so max(w) = 1.0
    """
    if taper == 'chebyshev':
        # scipy.signal.chebwin(N, at) returns Dolph-Chebyshev window of length N
        # with sidelobe attenuation = at dB
        w = chebwin(N, float(sll_db))
    elif taper == 'binomial':
        # Binomial weights: C(N-1, k) for k = 0..N-1 -> no sidelobes, wide beam
        k_vals = np.arange(N)
        w = np.array([float(scipy_comb(N - 1, k, exact=False)) for k in k_vals],
                     dtype=float)
    else:
        # Uniform excitation
        w = np.ones(N, dtype=float)

    # Normalize so peak weight = 1.0
    w_max = np.max(np.abs(w))
    if w_max > 1e-12:
        w = w / w_max
    return w


# ------------------------------------------------------------------------------
# 3b. Array Factor: N-Element ULA with Amplitude Tapering
# ------------------------------------------------------------------------------
def array_factor(theta, N=4, d=None, beta=0.0, taper='uniform', sll_db=30.0):
    """
    Computes normalized Array Factor AF(theta) for an N-element ULA.
    Supports uniform excitation AND amplitude-tapered excitation
    (Dolph-Chebyshev, Binomial) for sidelobe-level (SLL) control.

    Weighted AF formulation:
        AF(theta) = sum_{n=0}^{N-1} w_n * exp(j * n * psi)
        psi = k * d * cos(theta) + beta

    For uniform taper (all w_n = 1/N), this reduces to the closed-form:
        AF(psi) = sin(N*psi/2) / (N * sin(psi/2))

    Parameters:
        theta   : float or np.ndarray  Observation angle (radians).
        N       : int                  Number of array elements.
        d       : float, optional      Inter-element spacing (m). Default = lambda/2.
        beta    : float, optional      Progressive phase shift (radians).
        taper   : str                  'uniform' | 'chebyshev' | 'binomial'
        sll_db  : float                Chebyshev sidelobe attenuation (dB). Default = 30.

    Returns:
        np.ndarray or float  Normalized Array Factor magnitude (0.0 to 1.0).
    """
    if d is None:
        d = LAMBDA / 2.0

    theta_arr = np.asarray(theta, dtype=float)
    psi = K0 * d * np.cos(theta_arr) + beta   # progressive phase per element
    weights = get_taper_weights(N, taper=taper, sll_db=sll_db)

    # Vectorized weighted sum: AF[theta] = sum_n w[n] * exp(j*n*psi[theta])
    n_idx = np.arange(N, dtype=float)          # shape (N,)
    psi_arr = np.atleast_1d(psi)
    # psi_arr shape: (M,), n shape: (N,) -> outer product -> (N, M)
    phase_matrix = np.exp(1j * np.outer(n_idx, psi_arr))   # (N, M)
    w_col = weights[:, np.newaxis]                          # (N, 1)
    AF_complex = np.sum(w_col * phase_matrix, axis=0)       # (M,)

    # Normalize by coherent sum of weights so peak = 1.0 (preserves angle variation for scalars)
    w_sum = np.sum(np.abs(weights))
    AF_mag = np.abs(AF_complex) / (w_sum if w_sum > 1e-12 else 1.0)

    if np.isscalar(theta):
        return float(AF_mag[0])
    return AF_mag


# ------------------------------------------------------------------------------
# 4. Total Radiation Pattern (Pattern Multiplication Theorem)
# ------------------------------------------------------------------------------
def total_pattern(theta, N=4, d=None, beta=0.0, taper='uniform', sll_db=30.0):
    """
    Total field pattern via Pattern Multiplication Theorem:
    E_total(theta) = Element_Factor(theta) * Array_Factor(theta; taper)

    Parameters:
        theta   : float or np.ndarray  Observation angle (radians).
        N       : int                  Number of array elements.
        d       : float, optional      Inter-element spacing (m). Default = lambda/2.
        beta    : float, optional      Progressive phase shift (radians).
        taper   : str                  Amplitude taper: 'uniform'|'chebyshev'|'binomial'
        sll_db  : float                Chebyshev SLL target (dB). Default = 30.

    Returns:
        np.ndarray or float  Normalized total field magnitude pattern.
    """
    if d is None:
        d = LAMBDA / 2.0

    ef = element_factor(theta)
    af = array_factor(theta, N=N, d=d, beta=beta, taper=taper, sll_db=sll_db)
    return ef * af


# ------------------------------------------------------------------------------
# 5. Directivity Computation via Numerical Quadrature
# ------------------------------------------------------------------------------
def compute_directivity(N=4, d=None, beta=0.0):
    """
    Computes maximum directivity D0 using solid-angle radiation integration.
    D0 = 4 * pi * U_max / P_rad
    where P_rad = 2 * pi * integral_0^pi |E_total(theta)|^2 * sin(theta) d(theta)

    Parameters:
        N    : int
            Number of elements.
        d    : float, optional
            Inter-element spacing in meters.
        beta : float, optional
            Progressive phase shift in radians.

    Returns:
        tuple: (D0_dBi, D0_linear)
            D0_dBi    : Directivity in dBi
            D0_linear : Directivity as dimensionless linear power ratio
    """
    if d is None:
        d = LAMBDA / 2.0

    def integrand(th):
        E = total_pattern(th, N=N, d=d, beta=beta)
        return (E ** 2) * np.sin(th)

    # High-precision numerical integration over polar angle theta in [0, pi]
    integral_val, _ = integrate.quad(integrand, 0.0, np.pi, limit=200)
    P_rad = 2.0 * np.pi * integral_val

    # Find peak radiation intensity U_max
    theta_dense = np.linspace(0.0, np.pi, 20000)
    E_dense = total_pattern(theta_dense, N=N, d=d, beta=beta)
    U_max = np.max(E_dense ** 2)

    if P_rad <= 1e-15:
        return 0.0, 1.0

    D0_linear = (4.0 * np.pi * U_max) / P_rad
    D0_dBi = 10.0 * np.log10(max(D0_linear, 1e-12))
    return float(D0_dBi), float(D0_linear)


# ------------------------------------------------------------------------------
# 6. Half-Power Beamwidth (HPBW)
# ------------------------------------------------------------------------------
def compute_hpbw(N=4, d=None, beta=0.0):
    """
    Computes Half-Power Beamwidth (HPBW) in degrees.
    Locates the angular separation between the 3 dB points (|E| = max / sqrt(2)).

    Parameters:
        N    : int
            Number of elements.
        d    : float, optional
            Inter-element spacing in meters.
        beta : float, optional
            Progressive phase shift in radians.

    Returns:
        tuple: (hpbw_deg, theta_max_deg)
            hpbw_deg      : HPBW in degrees (or None if unresolved)
            theta_max_deg : Angle of main lobe peak in degrees
    """
    if d is None:
        d = LAMBDA / 2.0

    theta_dense = np.linspace(1e-6, np.pi - 1e-6, 50000)
    pat = total_pattern(theta_dense, N=N, d=d, beta=beta)
    idx_max = int(np.argmax(pat))
    peak_val = pat[idx_max]
    theta_max_deg = float(np.degrees(theta_dense[idx_max]))

    if peak_val < 1e-6:
        return None, theta_max_deg

    half_power_level = peak_val / np.sqrt(2.0)

    # Search left of peak
    left_part = pat[:idx_max]
    left_cross = np.where(left_part < half_power_level)[0]

    # Search right of peak
    right_part = pat[idx_max:]
    right_cross = np.where(right_part < half_power_level)[0]

    if len(left_cross) > 0 and len(right_cross) > 0:
        idx_left = left_cross[-1]
        idx_right = idx_max + right_cross[0]
        th_left = theta_dense[idx_left]
        th_right = theta_dense[idx_right]
        hpbw_deg = float(np.degrees(th_right - th_left))
        return hpbw_deg, theta_max_deg
    else:
        return None, theta_max_deg


# ------------------------------------------------------------------------------
# 7. Transmission Line & Reflection Parameters (VSWR, Gamma, S11)
# ------------------------------------------------------------------------------
def compute_vswr(Z_in, Z0_ref=50.0):
    """
    Calculates reflection coefficient Gamma, VSWR, and Return Loss S11 (dB)
    for a given complex input impedance Z_in referenced to Z0_ref.

    Parameters:
        Z_in   : complex
            Complex driving-point input impedance (Ohm).
        Z0_ref : float, optional
            Transmission-line reference impedance (default = 50.0 Ohm).

    Returns:
        tuple: (Gamma, vswr, S11_dB)
            Gamma   : Complex reflection coefficient
            vswr    : Voltage Standing Wave Ratio (dimensionless, >= 1.0)
            S11_dB  : Return loss / input reflection coefficient in dB
    """
    denom = Z_in + Z0_ref
    if abs(denom) < 1e-12:
        return complex(1.0, 0.0), float('inf'), 0.0

    Gamma = (Z_in - Z0_ref) / denom
    mag_Gamma = float(np.abs(Gamma))

    if mag_Gamma >= 1.0 - 1e-12:
        vswr = float('inf')
        S11_dB = 0.0
    else:
        vswr = float((1.0 + mag_Gamma) / (1.0 - mag_Gamma))
        S11_dB = float(20.0 * np.log10(max(mag_Gamma, 1e-12)))

    return Gamma, vswr, S11_dB


# ------------------------------------------------------------------------------
# 8. Mutual Impedance via Induced EMF Method (Fully Vectorized NumPy)
# ------------------------------------------------------------------------------
def mutual_impedance_emf(d_sep, L_elem=None, num_pts=2000):
    """
    Computes mutual impedance Z12 between two parallel half-wave dipoles
    separated by distance d_sep using the classical Induced EMF formulation.
    Fully vectorized over the dipole axial coordinate z: NO Python for-loops.

    Integral formulation:
        Z12 = - (1 / I0^2) * integral_{-L/2}^{L/2} Ez12(z) * I2(z) dz
    where for half-wave dipoles (k * L / 2 = pi / 2):
        Ez12(z) = -j * (eta0 * I0 / (4*pi)) * [ exp(-j*k*R1)/R1 + exp(-j*k*R2)/R2 ]
        R1 = sqrt(d^2 + (z - L/2)^2),  R2 = sqrt(d^2 + (z + L/2)^2)
        I2(z) = I0 * sin(k * (L/2 - |z|))

    Parameters:
        d_sep   : float
            Inter-element distance in meters.
        L_elem  : float, optional
            Dipole physical length in meters (default = lambda / 2).
        num_pts : int, optional
            Number of discretization points for integration.

    Returns:
        complex
            Mutual impedance Z12 (Ohm).
    """
    if L_elem is None:
        L_elem = LAMBDA / 2.0

    if d_sep < 1e-6:
        # Self-impedance of thin half-wave dipole: 73.13 + j42.54 Ohm
        return complex(73.13, 42.54)

    half_L = 0.5 * L_elem
    z = np.linspace(-half_L, half_L, num_pts)
    dz = L_elem / (num_pts - 1)

    R1 = np.sqrt(d_sep ** 2 + (z - half_L) ** 2)
    R2 = np.sqrt(d_sep ** 2 + (z + half_L) ** 2)

    # Vectorized computation of electric field Ez along dipole 2
    G = (np.exp(-1j * K0 * R1) / R1) + (np.exp(-1j * K0 * R2) / R2)
    Ez = -1j * (ETA0 / (4.0 * np.pi)) * G

    # Sinusoidal current distribution on dipole 2
    Iz = np.sin(K0 * (half_L - np.abs(z)))

    # Vectorized numerical integration via trapezoidal rule
    integrand = Ez * Iz
    Z12 = -float(dz) * (0.5 * integrand[0] + np.sum(integrand[1:-1]) + 0.5 * integrand[-1])

    return complex(Z12)


def build_impedance_matrix(N=4, d=None):
    """
    Constructs the N x N mutual impedance matrix [Z] using vectorized
    NumPy operations for all inter-element separations.

    Parameters:
        N : int
            Number of array elements.
        d : float, optional
            Inter-element spacing in meters (default = lambda / 2).

    Returns:
        np.ndarray (shape: (N, N), dtype: complex128)
            The complete mutual impedance matrix.
    """
    if d is None:
        d = LAMBDA / 2.0

    # Pairwise index difference matrix: |i - j|
    i_indices = np.arange(N)
    dist_multipliers = np.abs(i_indices[:, None] - i_indices[None, :])

    # Distinct separation values
    unique_mults = np.unique(dist_multipliers)
    z_cache = {}
    for m in unique_mults:
        if m == 0:
            z_cache[0] = complex(73.13, 42.54)
        else:
            z_cache[m] = mutual_impedance_emf(m * d)

    # Map back into the NxN matrix
    Z_matrix = np.zeros((N, N), dtype=complex)
    for m, z_val in z_cache.items():
        Z_matrix[dist_multipliers == m] = z_val

    return Z_matrix


# ------------------------------------------------------------------------------
# 9. Driving-Point Impedance
# ------------------------------------------------------------------------------
def driving_point_impedance(N=4, d=None):
    """
    Computes driving-point active input impedance of the array feed element
    accounting for mutual coupling and parasitic loading from neighboring elements.

    Parameters:
        N : int
            Number of elements.
        d : float, optional
            Inter-element spacing in meters (default = lambda / 2).

    Returns:
        complex
            Active input impedance Z_in (Ohm).
    """
    if d is None:
        d = LAMBDA / 2.0

    Z = build_impedance_matrix(N=N, d=d)
    Zin = Z[0, 0]

    # Active driving impedance contribution from mutual coupling
    for n in range(1, N):
        if abs(Z[n, n]) > 1e-12:
            Zin -= (Z[0, n] * Z[n, 0]) / Z[n, n]

    return complex(Zin)


# ------------------------------------------------------------------------------
# 10. Pattern Plotting Routines (plt.close() non-interactive mode)
# ------------------------------------------------------------------------------
def plot_polar_pattern(N=4, d=None, beta=0.0, filename="radiation_pattern_polar.png"):
    """
    Generates and saves a 2D normalized polar radiation pattern plot (full 360 deg).
    """
    if d is None:
        d = LAMBDA / 2.0

    theta_rad = np.linspace(0.0, 2.0 * np.pi, 3600)
    theta_eval = np.where(theta_rad <= np.pi, theta_rad, 2.0 * np.pi - theta_rad)

    pat = total_pattern(theta_eval, N=N, d=d, beta=beta)
    max_p = np.max(pat)
    if max_p > 1e-12:
        pat = pat / max_p

    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(8, 8))
    ax.plot(theta_rad, pat, color='royalblue', linewidth=2.0, label='Normalized |E(theta)|')
    ax.fill(theta_rad, pat, color='royalblue', alpha=0.15)

    d_over_lam = d / LAMBDA
    beta_deg = float(np.degrees(beta))
    title_str = (
        "2.4 GHz Phased Array Radiation Pattern\n"
        "N={}, d={:.2f}*lambda, beta={:.1f} deg | f0=2.44 GHz".format(N, d_over_lam, beta_deg)
    )
    ax.set_title(title_str, fontsize=12, pad=20)
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_rlabel_position(45)
    ax.legend(loc='lower right', fontsize=9)
    fig.tight_layout()

    fig.savefig(filename, dpi=150)
    plt.close(fig)
    print("  [Saved] {}".format(filename))


def plot_beam_steering(N=4, d=None, filename="beam_steering.png"):
    """
    Plots a family of radiation patterns for beta ranging from -90 to +90 deg.
    Demonstrates electronic beam scanning capability.
    """
    if d is None:
        d = LAMBDA / 2.0

    theta_rad = np.linspace(0.0, 2.0 * np.pi, 3600)
    theta_eval = np.where(theta_rad <= np.pi, theta_rad, 2.0 * np.pi - theta_rad)

    beta_list = np.linspace(-np.pi / 2.0, np.pi / 2.0, 7)
    colors = plt.cm.viridis(np.linspace(0.0, 1.0, len(beta_list)))

    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(9, 8))

    for beta_val, col in zip(beta_list, colors):
        pat = total_pattern(theta_eval, N=N, d=d, beta=beta_val)
        max_p = np.max(pat)
        if max_p > 1e-12:
            pat = pat / max_p
        beta_d = float(np.degrees(beta_val))
        ax.plot(theta_rad, pat, color=col, linewidth=1.5, label="beta = {:+.0f} deg".format(beta_d))

    d_over_lam = d / LAMBDA
    title_str = (
        "Beam Steering vs Progressive Phase (beta)\n"
        "N={}, d={:.2f}*lambda | f0=2.44 GHz".format(N, d_over_lam)
    )
    ax.set_title(title_str, fontsize=12, pad=20)
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.legend(loc='lower right', bbox_to_anchor=(1.30, -0.05), fontsize=8)
    fig.tight_layout()

    fig.savefig(filename, dpi=150)
    plt.close(fig)
    print("  [Saved] {}".format(filename))


def plot_vswr_s11_sweep(f_start=2.0e9, f_stop=3.0e9, nf=201, filename="vswr_s11_sweep.png"):
    """
    Frequency sweep showing VSWR and Return Loss S11 across 2.0 GHz - 3.0 GHz.
    """
    freqs = np.linspace(f_start, f_stop, nf)
    vswr_list = []
    s11_list = []

    for f in freqs:
        reactance_approx = 42.54 * (f - F0) / 0.05e9
        Z_elem = complex(73.13, reactance_approx)
        _, vswr_val, s11_val = compute_vswr(Z_elem, Z0_ref=50.0)
        vswr_list.append(min(vswr_val, 10.0))
        s11_list.append(s11_val)

    freq_ghz = freqs / 1e9
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7))

    ax1.plot(freq_ghz, vswr_list, color='navy', linewidth=2.0, label='Array Element VSWR')
    ax1.axhline(y=2.0, color='red', linestyle='--', linewidth=1.2, label='VSWR = 2.0 Threshold')
    ax1.axvline(x=F0 / 1e9, color='green', linestyle=':', linewidth=1.2, label='f0 = {:.2f} GHz'.format(F0 / 1e9))
    ax1.set_xlabel('Frequency (GHz)')
    ax1.set_ylabel('VSWR')
    ax1.set_title('VSWR vs Frequency')
    ax1.set_ylim([1.0, 10.0])
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='upper right')

    ax2.plot(freq_ghz, s11_list, color='crimson', linewidth=2.0, label='S11 Return Loss')
    ax2.axhline(y=-9.54, color='blue', linestyle='--', linewidth=1.2, label='S11 = -9.54 dB (VSWR 2:1)')
    ax2.axvline(x=F0 / 1e9, color='green', linestyle=':', linewidth=1.2, label='f0 = {:.2f} GHz'.format(F0 / 1e9))
    ax2.set_xlabel('Frequency (GHz)')
    ax2.set_ylabel('S11 (dB)')
    ax2.set_title('S11 Return Loss vs Frequency')
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc='lower right')

    fig.tight_layout()
    fig.savefig(filename, dpi=150)
    plt.close(fig)
    print("  [Saved] {}".format(filename))


# ------------------------------------------------------------------------------
# 11. Theoretical CSV Generator: Universal 36-Row Format
# ------------------------------------------------------------------------------
def generate_theoretical_csv(filename="theoretical_pattern.csv", N=4, d=None, beta=0.0):
    """
    Generates theoretical pattern CSV with exactly 36 rows:
    angle_deg,gain_dBi
    0,-12.3
    10,-10.1
    ...
    350,-11.2

    The pattern is normalized to 0 dBi relative peak and then offset by D0 (dBi)
    to provide absolute theoretical directive gain.
    """
    if d is None:
        d = LAMBDA / 2.0

    D0_dBi, _ = compute_directivity(N=N, d=d, beta=beta)

    angles_deg = np.arange(0, 360, 10)  # Exactly 36 angles: 0, 10, ..., 350
    theta_rad = np.radians(angles_deg)

    theta_eval = np.where(theta_rad <= np.pi, theta_rad, 2.0 * np.pi - theta_rad)
    E_vals = total_pattern(theta_eval, N=N, d=d, beta=beta)
    max_E = np.max(E_vals)

    if max_E > 1e-12:
        norm_power = (E_vals / max_E) ** 2
    else:
        norm_power = np.zeros_like(E_vals)

    norm_power = np.maximum(norm_power, 1e-4)
    relative_gain_dB = 10.0 * np.log10(norm_power)
    gain_dBi = relative_gain_dB + D0_dBi

    with open(filename, mode='w', newline='', encoding='ascii') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["angle_deg", "gain_dBi"])
        for ang, g in zip(angles_deg, gain_dBi):
            writer.writerow([int(ang), "{:.2f}".format(g)])

    print("  [Saved] {} (36 rows, 0 to 350 deg in 10 deg steps)".format(filename))


# ------------------------------------------------------------------------------
# 3D Spherical Radiation Pattern Plot (Gap 1 fix)
# ------------------------------------------------------------------------------
def plot_3d_spherical_pattern(N=4, d=None, beta=0.0, taper='uniform',
                              filename="radiation_3d_spherical.png"):
    """
    Renders the full 3D spherical radiation pattern of the array by rotating
    the azimuthally-symmetric ULA pattern around the array axis (z-axis).
    Uses Matplotlib mpl_toolkits.mplot3d -- no extra dependencies required.

    Parameters:
        N        : int    Number of elements.
        d        : float  Inter-element spacing (m). Default = lambda/2.
        beta     : float  Progressive phase shift (radians).
        taper    : str    Amplitude taper: 'uniform' | 'chebyshev' | 'binomial'
        filename : str    Output PNG filename.
    """
    if d is None:
        d = LAMBDA / 2.0

    # Build spherical coordinate grids
    theta_vals = np.linspace(0.0, np.pi, 181)       # elevation: 0 to 180 deg
    phi_vals   = np.linspace(0.0, 2.0 * np.pi, 361) # azimuth:   0 to 360 deg
    THETA, PHI = np.meshgrid(theta_vals, phi_vals)   # shape (361, 181)

    # Pattern is phi-independent for a ULA along z-axis: evaluate on flat theta
    E_flat = total_pattern(theta_vals, N=N, d=d, beta=beta, taper=taper)
    E_max  = np.max(E_flat)
    if E_max > 1e-12:
        E_flat = E_flat / E_max
    # Broadcast to full (phi, theta) surface
    R = np.tile(E_flat, (phi_vals.size, 1))          # shape (361, 181)

    # Convert spherical (R, theta, phi) -> Cartesian (X, Y, Z)
    X = R * np.sin(THETA) * np.cos(PHI)
    Y = R * np.sin(THETA) * np.sin(PHI)
    Z = R * np.cos(THETA)

    # Color the surface by radiation intensity (power = R^2)
    intensity = R ** 2
    facecolors = plt.cm.jet(intensity / np.max(intensity + 1e-12))

    fig = plt.figure(figsize=(10, 8))
    ax  = fig.add_subplot(111, projection='3d')
    ax.plot_surface(X, Y, Z, facecolors=facecolors, linewidth=0,
                   antialiased=True, alpha=0.85, rstride=2, cstride=2)

    # Axis labels and styling
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z (Array Axis)')
    d_lam = d / LAMBDA
    ax.set_title(
        "3D Spherical Radiation Pattern\n"
        "N={}, d={:.2f}*lambda, beta={:.0f} deg, Taper: {}  |  f0=2.44 GHz".format(
            N, d_lam, float(np.degrees(beta)), taper),
        fontsize=11, pad=12
    )

    # Add a colorbar indicating power level
    mappable = plt.cm.ScalarMappable(cmap='jet')
    mappable.set_array(intensity.ravel())
    cbar = fig.colorbar(mappable, ax=ax, shrink=0.5, aspect=12, pad=0.1)
    cbar.set_label('Normalized Power', fontsize=9)

    fig.tight_layout()
    fig.savefig(filename, dpi=150)
    plt.close(fig)
    print("  [Saved] {}".format(filename))


def _compare_tapers(N=4, d=None, beta=0.0):
    """Save a 3-panel polar comparison of uniform, Chebyshev, binomial tapers."""
    if d is None:
        d = LAMBDA / 2.0
    theta_rad = np.linspace(0.0, 2.0 * np.pi, 3600)
    theta_eval = np.where(theta_rad <= np.pi, theta_rad, 2.0 * np.pi - theta_rad)
    fig, axes = plt.subplots(1, 3, subplot_kw={"projection": "polar"}, figsize=(15, 5))
    specs = [
        ("uniform",   "royalblue",  "Uniform (No Taper)"),
        ("chebyshev", "crimson",    "Dolph-Chebyshev (30 dB SLL)"),
        ("binomial",  "forestgreen","Binomial (Max Smooth)"),
    ]
    for ax, (tp, col, lbl) in zip(axes, specs):
        pat = total_pattern(theta_eval, N=N, d=d, beta=beta, taper=tp)
        pat_max = np.max(pat)
        if pat_max > 1e-12:
            pat = pat / pat_max
        ax.plot(theta_rad, pat, color=col, linewidth=2.0)
        ax.fill(theta_rad, pat, color=col, alpha=0.15)
        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)
        ax.set_title(lbl, fontsize=10, pad=12)
    fig.suptitle(
        "Amplitude Taper Comparison  |  N={}, d={:.2f}lambda, f0=2.44 GHz".format(
            N, d / LAMBDA),
        fontsize=12, y=1.02)
    fig.tight_layout()
    fig.savefig("taper_comparison.png", dpi=150)
    plt.close(fig)
    print("  [Saved] taper_comparison.png")

# ------------------------------------------------------------------------------
# 12. Main Execution Routine
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    N_elements = 4
    d_spacing = LAMBDA / 2.0
    beta_phase = 0.0

    print("=" * 65)
    print("  2.4 GHz PHASED ARRAY ANTENNA - ANALYTICAL EM ENGINE")
    print("  Project Lead (The Math Brain) - Analytical Deliverable")
    print("=" * 65)
    print("  Operating Frequency : {:.3f} GHz".format(F0 / 1e9))
    print("  Wavelength (lambda) : {:.3f} cm ({:.6f} m)".format(LAMBDA * 1e2, LAMBDA))
    print("  Element Length      : {:.3f} cm (Half-wave Dipole)".format(L_DIPOLE * 1e2))
    print("  Array Elements (N)  : {}".format(N_elements))
    print("  Element Spacing (d) : {:.2f} lambda = {:.3f} cm".format(d_spacing / LAMBDA, d_spacing * 1e2))
    print("  Progressive Phase   : {:.1f} deg".format(float(np.degrees(beta_phase))))
    print("-" * 65)

    # 1. Directivity
    D0_dBi, D0_linear = compute_directivity(N_elements, d_spacing, beta_phase)
    print("  Directivity (D0)    : {:.3f} dBi  (Linear: {:.3f})".format(D0_dBi, D0_linear))

    # 2. HPBW
    hpbw_deg, theta_peak = compute_hpbw(N_elements, d_spacing, beta_phase)
    if hpbw_deg is not None:
        print("  HPBW (3 dB)         : {:.2f} deg".format(hpbw_deg))
        print("  Main Lobe Peak      : theta = {:.2f} deg".format(theta_peak))
    else:
        print("  HPBW (3 dB)         : Could not be resolved")

    # 3. Impedance Matrix
    print("-" * 65)
    print("  Computing Mutual Impedance Matrix via Induced EMF method...")
    Z_mat = build_impedance_matrix(N=N_elements, d=d_spacing)
    Z11 = Z_mat[0, 0]
    Z12 = Z_mat[0, 1]
    print("  Z_11 (Self)         : {:+.2f} {:+.2f}j Ohm".format(Z11.real, Z11.imag))
    print("  Z_12 (Mutual)       : {:+.2f} {:+.2f}j Ohm".format(Z12.real, Z12.imag))

    # 4. Driving-Point Impedance & VSWR
    Z_in = driving_point_impedance(N=N_elements, d=d_spacing)
    print("  Z_in (Active Feed)  : {:+.2f} {:+.2f}j Ohm".format(Z_in.real, Z_in.imag))

    Gamma, vswr, S11 = compute_vswr(Z_in, Z0_ref=Z0)
    print("  |Gamma|             : {:.4f}, Angle = {:.1f} deg".format(
        abs(Gamma), float(np.degrees(np.angle(Gamma)))))
    print("  VSWR                : {:.3f}  ({})".format(
        vswr, 'MATCHED (< 2.0)' if vswr < 2.0 else 'NEEDS MATCHING'))
    print("  S11 Return Loss     : {:.2f} dB".format(S11))
    print("=" * 65)

    # 5. Save CSV & Plots
    print("\nGenerating deliverables...")
    generate_theoretical_csv("theoretical_pattern.csv", N=N_elements, d=d_spacing, beta=beta_phase)
    plot_polar_pattern(N=N_elements, d=d_spacing, beta=beta_phase, filename="radiation_pattern_polar.png")
    plot_beam_steering(N=N_elements, d=d_spacing, filename="beam_steering.png")
    plot_vswr_s11_sweep(filename="vswr_s11_sweep.png")

    plot_3d_spherical_pattern(N=N_elements, d=d_spacing, beta=beta_phase,

                              taper='uniform', filename="radiation_3d_spherical.png")

    # Also generate a comparison of all three tapers on one polar plot

    _compare_tapers(N_elements, d_spacing, beta_phase)

    print("\nAll tasks completed successfully. Output files generated.")
    print("=" * 65)
