# ==============================================================================
# antenna_math_engine.py
# 2.4 GHz Phased Array Antenna - Analytical Electromagnetics Engine
# Project Lead: Analytical EM Modeling & Theoretical Pattern Generator
# ==============================================================================
# Pure ASCII implementation: No unicode characters used anywhere.
# Compliant with Python 3.12+, Windows, numpy, scipy, and matplotlib.
#
# Contents
#   1.  Constants (shared with the team via emt_config.py)
#   2.  Radiation integrals: I(z) -> A_z -> E_theta, H_phi -> Poynting -> P_rad
#   3.  N-element ULA: element factor, tapers, array factor, total pattern
#   4.  Directivity D0 and HPBW of the ULA
#   5.  VSWR / Gamma / S11
#   6.  Induced EMF mutual impedance, impedance matrix, Z_in, active impedance
#   7.  4-element Yagi-Uda solver (reads Member 2's data/optimized_dimensions.json)
#   8.  Plots and the universal theoretical CSV (data/theoretical_pattern.csv)
# ==============================================================================

import os
import sys
import csv
import warnings
import numpy as np
from scipy import integrate
from scipy.special import comb as scipy_comb
from scipy.signal.windows import chebwin
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
import matplotlib.pyplot as plt

# Shared team config (repo root): constants + data/ file locations
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(SCRIPT_DIR))
from emt_config import (C0, F0, LAMBDA, Z0, SWEEP_START_HZ, SWEEP_STOP_HZ,
                        PATTERN_STEP_DEG, THEORETICAL_CSV, SIMULATED_CSV,
                        ensure_data_dir, load_dimensions)

# ------------------------------------------------------------------------------
# 1. Physical Constants & Design Parameters (2.44 GHz ISM Band)
# ------------------------------------------------------------------------------
ETA0 = 120.0 * np.pi          # Intrinsic impedance of free space (approx 376.73 Ohm)
MU0 = ETA0 / C0               # Permeability of free space (H/m), eta0 = mu0 * c
K0 = 2.0 * np.pi / LAMBDA     # Free-space wavenumber (rad/m)
L_DIPOLE = LAMBDA / 2.0       # Resonant half-wave dipole length (m)


def _out(name):
    """Path for a generated plot inside this folder (independent of the cwd)."""
    return os.path.join(SCRIPT_DIR, name)


# ------------------------------------------------------------------------------
# 2. Radiation Integrals: Thin-Wire Dipole from First Principles
# ------------------------------------------------------------------------------
def dipole_current(z, L, Im=1.0, k=K0):
    """
    Sinusoidal current distribution on a center-fed thin-wire dipole:
        I(z) = Im * sin(k * (L/2 - |z|)),   -L/2 <= z <= L/2

    Parameters:
        z  : float or np.ndarray  Position along the wire (m).
        L  : float                Total dipole length (m).
        Im : complex              Current maximum (A).
        k  : float                Wavenumber (rad/m).
    """
    return Im * np.sin(k * (0.5 * L - np.abs(z)))


def vector_potential_Az(theta, L, r=1.0, Im=1.0, k=K0, num_pts=2001):
    """
    Far-zone magnetic vector potential of a z-directed dipole, evaluated by
    numerically integrating the current over the wire (the radiation integral):

        A_z(r, theta) = mu0 * exp(-j k r) / (4 pi r)
                        * integral_{-L/2}^{L/2} I(z') exp(j k z' cos(theta)) dz'

    Parameters:
        theta   : float or np.ndarray  Angle from the wire axis (rad).
        L       : float                Dipole length (m).
        r       : float                Observation distance (m), far field.
        Im      : complex              Current maximum (A).
        k       : float                Wavenumber (rad/m).
        num_pts : int                  Integration points along the wire.

    Returns:
        np.ndarray (complex)  A_z in Wb/m.
    """
    theta_arr = np.atleast_1d(np.asarray(theta, dtype=float))
    z = np.linspace(-0.5 * L, 0.5 * L, num_pts)
    I_z = dipole_current(z, L, Im=Im, k=k)
    phase = np.exp(1j * k * np.outer(np.cos(theta_arr), z))        # (M, P)
    radiation_integral = integrate.trapezoid(I_z[None, :] * phase, z, axis=1)
    return MU0 * np.exp(-1j * k * r) / (4.0 * np.pi * r) * radiation_integral


def dipole_far_fields(theta, L, r=1.0, Im=1.0, k=K0):
    """
    Far-zone fields of a dipole derived from the vector potential A_z:
        A_theta = -A_z sin(theta)
        E_theta = -j omega A_theta = j omega A_z sin(theta)
        H_phi   = E_theta / eta0
        W_r     = (1/2) Re(E_theta * conj(H_phi))   (time-average Poynting vector)

    Returns:
        dict with keys 'A_z', 'E_theta' (V/m), 'H_phi' (A/m), 'W_r' (W/m^2).
    """
    theta_arr = np.atleast_1d(np.asarray(theta, dtype=float))
    omega = k * C0
    A_z = vector_potential_Az(theta_arr, L, r=r, Im=Im, k=k)
    E_theta = 1j * omega * A_z * np.sin(theta_arr)
    H_phi = E_theta / ETA0
    return {
        "A_z": A_z,
        "E_theta": E_theta,
        "H_phi": H_phi,
        "W_r": poynting_vector(E_theta, H_phi),
    }


def poynting_vector(E_theta, H_phi):
    """
    Radial time-average Poynting vector W_av = (1/2) Re(E x H*) for far-zone
    fields (E_theta x H_phi points along +r).

    Returns:
        np.ndarray  Power density (W/m^2).
    """
    return 0.5 * np.real(np.asarray(E_theta) * np.conj(np.asarray(H_phi)))


def dipole_radiated_power(L, Im=1.0, k=K0, r=100.0, num_theta=2001):
    """
    Total radiated power found by integrating the Poynting vector over a
    far-field sphere of radius r:
        P_rad = integral_0^{2 pi} integral_0^{pi} W_r r^2 sin(theta) dtheta dphi

    Returns:
        tuple: (P_rad_W, R_rad_ohm)
            R_rad is referred to the current maximum: P_rad = |Im|^2 R_rad / 2.
    """
    theta = np.linspace(1e-6, np.pi - 1e-6, num_theta)
    W_r = dipole_far_fields(theta, L, r=r, Im=Im, k=k)["W_r"]
    P_rad = 2.0 * np.pi * integrate.simpson(W_r * r ** 2 * np.sin(theta), x=theta)
    R_rad = 2.0 * P_rad / (abs(Im) ** 2)
    return float(P_rad), float(R_rad)


def dipole_element_factor(cos_theta, L, k=K0):
    """
    Closed-form result of the radiation integral for a dipole of any length:
        F(theta) = [cos(k L/2 cos(theta)) - cos(k L/2)] / sin(theta)
    so that E_theta = j eta0 Im exp(-j k r) / (2 pi r) * F(theta).

    Parameters:
        cos_theta : float or np.ndarray  cos of the angle from the wire axis.
        L         : float                Dipole length (m).
    """
    c = np.asarray(cos_theta, dtype=float)
    s = np.sqrt(np.clip(1.0 - c ** 2, 0.0, 1.0))
    kh = 0.5 * k * L
    with np.errstate(divide='ignore', invalid='ignore'):
        F = np.where(s > 1e-9, (np.cos(kh * c) - np.cos(kh)) / s, 0.0)
    return F


# ------------------------------------------------------------------------------
# 3. Element Factor: Half-Wave Dipole
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
        # with sidelobe attenuation = at dB. Its "< 45 dB" warning concerns
        # spectral analysis only, not array synthesis, so it is silenced.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
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

    The array axis is the z-axis (theta measured from it), i.e. a collinear
    array of z-directed dipoles, as in the pattern-multiplication examples of
    Balanis ch. 6. The physical 4-element prototype is modeled separately by
    the Yagi-Uda solver in section 7.

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
# 3c. Total Radiation Pattern (Pattern Multiplication Theorem)
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
# 4. Directivity Computation via Numerical Quadrature
# ------------------------------------------------------------------------------
def compute_directivity(N=4, d=None, beta=0.0, taper='uniform', sll_db=30.0):
    """
    Computes maximum directivity D0 using solid-angle radiation integration.
    D0 = 4 * pi * U_max / P_rad
    where P_rad = 2 * pi * integral_0^pi |E_total(theta)|^2 * sin(theta) d(theta)

    Parameters:
        N      : int              Number of elements.
        d      : float, optional  Inter-element spacing in meters.
        beta   : float, optional  Progressive phase shift in radians.
        taper  : str              Amplitude taper: 'uniform'|'chebyshev'|'binomial'
        sll_db : float            Chebyshev SLL target (dB).

    Returns:
        tuple: (D0_dBi, D0_linear)
            D0_dBi    : Directivity in dBi
            D0_linear : Directivity as dimensionless linear power ratio
    """
    if d is None:
        d = LAMBDA / 2.0

    def integrand(th):
        E = total_pattern(th, N=N, d=d, beta=beta, taper=taper, sll_db=sll_db)
        return (E ** 2) * np.sin(th)

    # High-precision numerical integration over polar angle theta in [0, pi]
    integral_val, _ = integrate.quad(integrand, 0.0, np.pi, limit=200)
    P_rad = 2.0 * np.pi * integral_val

    # Find peak radiation intensity U_max
    theta_dense = np.linspace(0.0, np.pi, 20000)
    E_dense = total_pattern(theta_dense, N=N, d=d, beta=beta, taper=taper, sll_db=sll_db)
    U_max = np.max(E_dense ** 2)

    if P_rad <= 1e-15:
        return 0.0, 1.0

    D0_linear = (4.0 * np.pi * U_max) / P_rad
    D0_dBi = 10.0 * np.log10(max(D0_linear, 1e-12))
    return float(D0_dBi), float(D0_linear)


# ------------------------------------------------------------------------------
# 4b. Half-Power Beamwidth (HPBW)
# ------------------------------------------------------------------------------
def compute_hpbw(N=4, d=None, beta=0.0, taper='uniform', sll_db=30.0):
    """
    Computes Half-Power Beamwidth (HPBW) in degrees.
    Locates the angular separation between the 3 dB points (|E| = max / sqrt(2)).

    Parameters:
        N      : int              Number of elements.
        d      : float, optional  Inter-element spacing in meters.
        beta   : float, optional  Progressive phase shift in radians.
        taper  : str              Amplitude taper: 'uniform'|'chebyshev'|'binomial'
        sll_db : float            Chebyshev SLL target (dB).

    Returns:
        tuple: (hpbw_deg, theta_max_deg)
            hpbw_deg      : HPBW in degrees (or None if unresolved)
            theta_max_deg : Angle of main lobe peak in degrees
    """
    if d is None:
        d = LAMBDA / 2.0

    theta_dense = np.linspace(1e-6, np.pi - 1e-6, 50000)
    pat = total_pattern(theta_dense, N=N, d=d, beta=beta, taper=taper, sll_db=sll_db)
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
# 5. Transmission Line & Reflection Parameters (VSWR, Gamma, S11)
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
# 6. Mutual Impedance via Induced EMF Method (Fully Vectorized NumPy)
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


def mutual_impedance_general(L1, L2, rho, k=K0, min_pts=2001):
    """
    Induced EMF mutual impedance between two parallel, side-by-side dipoles of
    ARBITRARY lengths L1, L2 at separation rho (referred to the current maxima).
    Setting rho = wire radius gives the self-impedance of a finite-thickness
    dipole (classical induced EMF self-impedance).

    Near field of dipole 1 on the axis of dipole 2 (h1 = L1/2):
        Ez21(z) = -j eta0 Im1 / (4 pi) * [ exp(-j k R1)/R1 + exp(-j k R2)/R2
                                         - 2 cos(k h1) exp(-j k R0)/R0 ]
        R1 = sqrt(rho^2 + (z - h1)^2), R2 = sqrt(rho^2 + (z + h1)^2),
        R0 = sqrt(rho^2 + z^2)
    and
        Z21 = -(1 / (Im1 Im2)) * integral_{-h2}^{h2} Ez21(z) I2(z) dz

    Parameters:
        L1, L2  : float  Lengths of dipole 1 and 2 (m).
        rho     : float  Center-to-center separation, or wire radius for self (m).
        k       : float  Wavenumber (rad/m), lets the solver sweep frequency.
        min_pts : int    Minimum integration points (refined for small rho).

    Returns:
        complex  Z21 (Ohm), referred to the current maxima.
    """
    h1 = 0.5 * L1
    h2 = 0.5 * L2
    # Resolve the 1/R peaks: keep dz well below rho
    num_pts = int(max(min_pts, np.ceil(L2 / (rho / 100.0)) + 1))
    z = np.linspace(-h2, h2, num_pts)

    R1 = np.sqrt(rho ** 2 + (z - h1) ** 2)
    R2 = np.sqrt(rho ** 2 + (z + h1) ** 2)
    R0 = np.sqrt(rho ** 2 + z ** 2)
    G = (np.exp(-1j * k * R1) / R1 + np.exp(-1j * k * R2) / R2
         - 2.0 * np.cos(k * h1) * np.exp(-1j * k * R0) / R0)
    Ez = -1j * (ETA0 / (4.0 * np.pi)) * G
    I2 = np.sin(k * (h2 - np.abs(z)))

    return complex(-integrate.trapezoid(Ez * I2, z))


def build_impedance_matrix(N=4, d=None):
    """
    Constructs the N x N mutual impedance matrix [Z] using vectorized
    NumPy operations for all inter-element separations.

    Elements are half-wave dipoles placed side by side (parallel) at spacing d.

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
# 6b. Driving-Point and Active Impedance
# ------------------------------------------------------------------------------
def driving_point_impedance(N=4, d=None):
    """
    Computes the input impedance of element 0 when it is the only driven
    element and all other elements are short-circuited parasites.

    Solves the full circuit equations [V] = [Z][I] with V = [1, 0, ..., 0],
    so coupling between every pair of elements (including parasite-to-parasite)
    is included:  Z_in = V_0 / I_0.

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
    V = np.zeros(N, dtype=complex)
    V[0] = 1.0
    I = np.linalg.solve(Z, V)
    return complex(V[0] / I[0])


def active_impedance(N=4, d=None, beta=0.0, taper='uniform', sll_db=30.0):
    """
    Active (scan) impedance of every element of a fully driven phased array:
        Z_act_n = sum_m Z_nm * I_m / I_n,   I_m = w_m * exp(j * m * beta)

    This is the impedance each feed actually sees while the beam is steered,
    and it changes with beta because of mutual coupling.

    Returns:
        np.ndarray (complex, shape (N,))  Active impedance of each element (Ohm).
    """
    if d is None:
        d = LAMBDA / 2.0

    Z = build_impedance_matrix(N=N, d=d)
    w = get_taper_weights(N, taper=taper, sll_db=sll_db)
    I = w * np.exp(1j * beta * np.arange(N))
    return (Z @ I) / I


# ------------------------------------------------------------------------------
# 7. Yagi-Uda Solver (the physical prototype)
# ------------------------------------------------------------------------------
# Geometry convention (same as Member 2 and Member 4's turntable):
#   - elements are parallel to z, spaced along the boom (x-axis)
#   - directors point to +x, so the main beam is at phi = 0 deg
#   - the azimuth (H-plane, theta = 90 deg) cut is the measured pattern
YAGI_ELEMENTS = ("reflector", "driven_dipole", "director_1", "director_2")


def load_yagi_design(dims=None):
    """
    Builds the Yagi geometry from Member 2's data/optimized_dimensions.json.

    Returns:
        dict: names, lengths_m, x_m (boom position relative to the driven
              element), radius_m, feed_index, source
    """
    if dims is None:
        dims = load_dimensions()
    if dims is None:
        raise FileNotFoundError(
            "data/optimized_dimensions.json not found - run "
            "EMT_Member2/simulate_yagi.py (or run_pipeline.py) first.")

    pos = dims["boom_positions_mm"]
    x_drv = pos["driven_dipole"]
    return {
        "names": YAGI_ELEMENTS,
        "lengths_m": np.array([dims[n + "_length_mm"] for n in YAGI_ELEMENTS]) * 1e-3,
        "x_m": np.array([pos[n] - x_drv for n in YAGI_ELEMENTS]) * 1e-3,
        "radius_m": dims["wire_radius_mm"] * 1e-3,
        "feed_index": YAGI_ELEMENTS.index("driven_dipole"),
        "source": dims.get("_source", "data/optimized_dimensions.json"),
    }


def yagi_impedance_matrix(design, freq_hz=F0):
    """
    Full Yagi impedance matrix from the induced EMF method, referred to the
    element terminals (center): Z_mn = Z_mn(max) / (sin(k h_m) sin(k h_n)).

    Diagonal terms use the wire radius as the separation (self-impedance).
    """
    k = 2.0 * np.pi * freq_hz / C0
    L = design["lengths_m"]
    x = design["x_m"]
    n_el = len(L)
    Z = np.zeros((n_el, n_el), dtype=complex)
    for m in range(n_el):
        for p in range(m, n_el):
            rho = design["radius_m"] if m == p else abs(x[m] - x[p])
            Z_max = mutual_impedance_general(L[m], L[p], rho, k=k)
            Z[m, p] = Z[p, m] = Z_max / (np.sin(0.5 * k * L[m]) * np.sin(0.5 * k * L[p]))
    return Z


def solve_yagi(design=None, freq_hz=F0, v_feed=1.0):
    """
    Solves the Yagi circuit equations [V] = [Z][I]: only the driven element is
    fed (V = v_feed); the reflector and directors are shorted parasites.

    Returns:
        dict: Z (matrix), I_base (terminal currents), I_max (current maxima),
              Z_in, k, freq_hz, design
    """
    if design is None:
        design = load_yagi_design()
    k = 2.0 * np.pi * freq_hz / C0
    Z = yagi_impedance_matrix(design, freq_hz)
    V = np.zeros(len(design["lengths_m"]), dtype=complex)
    V[design["feed_index"]] = v_feed
    I_base = np.linalg.solve(Z, V)
    I_max = I_base / np.sin(0.5 * k * design["lengths_m"])
    return {
        "Z": Z,
        "I_base": I_base,
        "I_max": I_max,
        "Z_in": complex(v_feed / I_base[design["feed_index"]]),
        "k": k,
        "freq_hz": freq_hz,
        "design": design,
    }


def _yagi_array_sum(cos_theta, u_x, sol):
    """
    sum_n Im_n F_n(theta) exp(j k x_n u_x), with u_x = sin(theta) cos(phi).
    E_theta = j eta0 exp(-j k r) / (2 pi r) times this sum.
    """
    design = sol["design"]
    k = sol["k"]
    S = 0.0
    for Im, L, x in zip(sol["I_max"], design["lengths_m"], design["x_m"]):
        S = S + Im * dipole_element_factor(cos_theta, L, k=k) * np.exp(1j * k * x * u_x)
    return S


def yagi_far_fields(theta, phi, sol, r=1.0):
    """
    Far-zone E_theta, H_phi and Poynting vector of the solved Yagi.

    Parameters:
        theta, phi : float or np.ndarray  Spherical angles (rad), broadcastable.
        sol        : dict                 Result of solve_yagi().
        r          : float                Observation distance (m).

    Returns:
        dict with keys 'E_theta', 'H_phi', 'W_r', 'U' (radiation intensity W/sr).
    """
    th = np.asarray(theta, dtype=float)
    ph = np.asarray(phi, dtype=float)
    S = _yagi_array_sum(np.cos(th), np.sin(th) * np.cos(ph), sol)
    E_theta = 1j * ETA0 * np.exp(-1j * sol["k"] * r) / (2.0 * np.pi * r) * S
    H_phi = E_theta / ETA0
    W_r = poynting_vector(E_theta, H_phi)
    return {"E_theta": E_theta, "H_phi": H_phi, "W_r": W_r, "U": W_r * r ** 2}


def yagi_radiated_power(sol, n_theta=181, n_phi=361):
    """P_rad = integral of the radiation intensity U over the full sphere (W)."""
    theta = np.linspace(0.0, np.pi, n_theta)
    phi = np.linspace(0.0, 2.0 * np.pi, n_phi)
    TH, PH = np.meshgrid(theta, phi, indexing='ij')
    U = yagi_far_fields(TH, PH, sol)["U"]
    inner = integrate.simpson(U * np.sin(TH), x=theta, axis=0)
    return float(integrate.simpson(inner, x=phi))


def yagi_h_plane(angles_deg, sol, P_rad):
    """Directivity (linear) in the azimuth / H-plane cut, phi = angle, theta = 90 deg."""
    phi = np.radians(np.asarray(angles_deg, dtype=float))
    S = _yagi_array_sum(np.zeros_like(phi), np.cos(phi), sol)
    U = ETA0 / (8.0 * np.pi ** 2) * np.abs(S) ** 2
    return 4.0 * np.pi * U / P_rad


def yagi_e_plane(angles_deg, sol, P_rad):
    """
    Directivity (linear) in the E-plane (the x-z plane containing the elements
    and the boom). angle = 0 deg is along the boom toward the directors,
    90 deg is along the element tips.
    """
    alpha = np.radians(np.asarray(angles_deg, dtype=float))
    S = _yagi_array_sum(np.sin(alpha), np.cos(alpha), sol)
    U = ETA0 / (8.0 * np.pi ** 2) * np.abs(S) ** 2
    return 4.0 * np.pi * U / P_rad


def _cut_hpbw(angles_deg, power):
    """
    Half-power beamwidth of a periodic 360-degree cut sampled on a uniform
    grid. Walks outward from the peak and interpolates the -3 dB crossings.
    """
    p = np.asarray(power, dtype=float)
    n = len(p)
    step = float(angles_deg[1] - angles_deg[0])
    i0 = int(np.argmax(p))
    half = 0.5 * p[i0]

    def crossing(direction):
        for j in range(1, n // 2):
            p_prev = p[(i0 + direction * (j - 1)) % n]
            p_cur = p[(i0 + direction * j) % n]
            if p_cur < half:
                return (j - 1) + (p_prev - half) / (p_prev - p_cur)
        return None

    right, left = crossing(+1), crossing(-1)
    if right is None or left is None:
        return None
    return float((right + left) * step)


def yagi_metrics(design=None, freq_hz=F0):
    """
    Complete theoretical figures of merit for the Yagi at freq_hz.

    Returns:
        dict: Z_in, Gamma, vswr, S11_dB, D0_dBi, front_to_back_dB,
              hpbw_h_deg, hpbw_e_deg, P_rad_W, P_in_W, power_balance_pct,
              currents (normalized |I| and phase per element), sol
    """
    sol = solve_yagi(design, freq_hz)
    design = sol["design"]
    P_rad = yagi_radiated_power(sol)

    angles = np.arange(0.0, 360.0, 0.1)
    D_h = yagi_h_plane(angles, sol, P_rad)
    D_e = yagi_e_plane(angles, sol, P_rad)

    Gamma, vswr, S11_dB = compute_vswr(sol["Z_in"], Z0_ref=Z0)

    # Power balance: circuit input power (induced EMF) vs Poynting-integrated P_rad
    I_feed = sol["I_base"][design["feed_index"]]
    P_in = 0.5 * abs(I_feed) ** 2 * sol["Z_in"].real

    I_norm = sol["I_base"] / I_feed
    return {
        "Z_in": sol["Z_in"],
        "Gamma": Gamma,
        "vswr": vswr,
        "S11_dB": S11_dB,
        "D0_dBi": float(10.0 * np.log10(max(D_h.max(), D_e.max()))),
        "front_to_back_dB": float(10.0 * np.log10(D_h[0] / D_h[len(angles) // 2])),
        "hpbw_h_deg": _cut_hpbw(angles, D_h),
        "hpbw_e_deg": _cut_hpbw(angles, D_e),
        "P_rad_W": P_rad,
        "P_in_W": float(P_in),
        "power_balance_pct": float(100.0 * (P_rad - P_in) / P_in),
        "currents": [(name, float(abs(i)), float(np.degrees(np.angle(i))))
                     for name, i in zip(design["names"], I_norm)],
        "sol": sol,
    }


def yagi_impedance_sweep(freqs_hz, design=None):
    """Input impedance Z_in(f) of the Yagi, re-solving the full system at each f."""
    if design is None:
        design = load_yagi_design()
    return np.array([solve_yagi(design, f)["Z_in"] for f in freqs_hz])


# ------------------------------------------------------------------------------
# 8. Pattern Plotting Routines (plt.close() non-interactive mode)
# ------------------------------------------------------------------------------
def plot_polar_pattern(N=4, d=None, beta=0.0, filename=_out("radiation_pattern_polar.png")):
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
    print("  [Saved] {}".format(os.path.basename(filename)))


def plot_beam_steering(N=4, d=None, filename=_out("beam_steering.png")):
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
    print("  [Saved] {}".format(os.path.basename(filename)))


def plot_vswr_s11_sweep(f_start=SWEEP_START_HZ, f_stop=SWEEP_STOP_HZ, nf=201,
                        filename=_out("vswr_s11_sweep.png"), design=None):
    """
    Frequency sweep of the 4-element Yagi's VSWR and Return Loss S11 across
    2.0 GHz - 3.0 GHz. Z_in(f) comes from re-solving the induced EMF circuit
    equations at every frequency (element lengths and spacings held fixed).

    Returns:
        tuple: (freqs_hz, Z_in array)
    """
    freqs = np.linspace(f_start, f_stop, nf)
    Z_in = yagi_impedance_sweep(freqs, design)
    vswr_list = []
    s11_list = []
    for z in Z_in:
        _, vswr_val, s11_val = compute_vswr(z, Z0_ref=Z0)
        vswr_list.append(min(vswr_val, 10.0))
        s11_list.append(s11_val)
    vswr_arr = np.array(vswr_list)

    freq_ghz = freqs / 1e9
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7))

    ax1.plot(freq_ghz, vswr_arr, color='navy', linewidth=2.0, label='Yagi VSWR (induced EMF)')
    ax1.axhline(y=2.0, color='red', linestyle='--', linewidth=1.2, label='VSWR = 2.0 Threshold')
    ax1.axvline(x=F0 / 1e9, color='green', linestyle=':', linewidth=1.2, label='f0 = {:.2f} GHz'.format(F0 / 1e9))
    ax1.set_xlabel('Frequency (GHz)')
    ax1.set_ylabel('VSWR')
    ax1.set_title('VSWR vs Frequency - 4-Element Yagi (Theory)')
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
    print("  [Saved] {}".format(os.path.basename(filename)))
    return freqs, Z_in


def plot_yagi_patterns(metrics, filename=_out("yagi_theory_vs_sim.png"), floor_db=-30.0):
    """
    H-plane and E-plane theoretical Yagi patterns (dBi). The H-plane panel
    also overlays Member 2's simulated CSV when data/simulated_pattern.csv exists.
    """
    sol = metrics["sol"]
    P_rad = metrics["P_rad_W"]
    angles = np.arange(0.0, 360.5, 0.5)
    g_h = 10.0 * np.log10(np.maximum(yagi_h_plane(angles, sol, P_rad), 1e-12))
    g_e = 10.0 * np.log10(np.maximum(yagi_e_plane(angles, sol, P_rad), 1e-12))
    r_max = np.ceil(metrics["D0_dBi"] / 5.0) * 5.0 + 5.0
    r_min = r_max + floor_db

    fig, axes = plt.subplots(1, 2, subplot_kw={'projection': 'polar'}, figsize=(13, 6.5))
    panels = [
        (axes[0], g_h, "H-plane / azimuth (measured cut)\nHPBW {:.0f} deg, F/B {:.1f} dB".format(
            metrics["hpbw_h_deg"], metrics["front_to_back_dB"])),
        (axes[1], g_e, "E-plane (plane of the elements)\nHPBW {:.0f} deg".format(
            metrics["hpbw_e_deg"])),
    ]
    for ax, g, title in panels:
        ax.plot(np.radians(angles), np.maximum(g, r_min), color='royalblue',
                linewidth=2.0, label='Theory (induced EMF)')
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_rlim(r_min, r_max)
        ax.set_rlabel_position(45)
        ax.set_title(title, fontsize=10, pad=14)

    if os.path.exists(SIMULATED_CSV):
        sim = np.genfromtxt(SIMULATED_CSV, delimiter=',', skip_header=1)
        ang_s = np.append(sim[:, 0], sim[0, 0] + 360.0)
        g_s = np.append(sim[:, 1], sim[0, 1])
        axes[0].plot(np.radians(ang_s), np.maximum(g_s, r_min), color='crimson',
                     linestyle='--', marker='o', markersize=3, linewidth=1.5,
                     label='Member 2 simulated')
    for ax in axes:
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.06), ncol=2, fontsize=8)

    fig.suptitle("4-Element 2.44 GHz Yagi-Uda - Theoretical Directivity (dBi), "
                 "D0 = {:.2f} dBi".format(metrics["D0_dBi"]), fontsize=12)
    fig.tight_layout(rect=(0.0, 0.03, 1.0, 0.95))
    fig.savefig(filename, dpi=150)
    plt.close(fig)
    print("  [Saved] {}".format(os.path.basename(filename)))


# ------------------------------------------------------------------------------
# 8b. Theoretical CSV Generators: Universal 36-Row Format
# ------------------------------------------------------------------------------
def generate_yagi_theoretical_csv(filename=THEORETICAL_CSV, design=None, freq_hz=F0,
                                  metrics=None):
    """
    Writes the team's theoretical pattern CSV from the Yagi solver: the
    azimuth (H-plane) directivity in dBi at 0, 10, ..., 350 deg, with 0 deg
    toward the directors. Same convention as Member 2's simulated CSV
    (floored at 40 dB below the peak), so Member 1 can overlay them directly.

    Returns:
        tuple: (angles_deg, gain_dBi)
    """
    if metrics is None:
        metrics = yagi_metrics(design, freq_hz)
    angles_deg = np.arange(0, 360, PATTERN_STEP_DEG)
    D = yagi_h_plane(angles_deg, metrics["sol"], metrics["P_rad_W"])
    D = np.maximum(D, D.max() * 1e-4)
    gain_dBi = 10.0 * np.log10(D)

    if os.path.dirname(filename):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, mode='w', newline='', encoding='ascii') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["angle_deg", "gain_dBi"])
        for ang, g in zip(angles_deg, gain_dBi):
            writer.writerow([int(ang), "{:.2f}".format(g)])

    print("  [Saved] {} ({} rows, Yagi H-plane theory)".format(
        os.path.basename(filename), len(angles_deg)))
    return angles_deg, gain_dBi


def generate_theoretical_csv(filename=_out("ula_theoretical_pattern.csv"), N=4, d=None, beta=0.0):
    """
    Generates a 36-row pattern CSV for the N-element ULA:
    angle_deg,gain_dBi
    0,-12.3
    10,-10.1
    ...
    350,-11.2

    The pattern is normalized to 0 dBi relative peak and then offset by D0 (dBi)
    to provide absolute theoretical directive gain. For the team's overlay of
    the physical antenna use generate_yagi_theoretical_csv() instead.
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

    print("  [Saved] {} (36 rows, 0 to 350 deg in 10 deg steps)".format(os.path.basename(filename)))


# ------------------------------------------------------------------------------
# 3D Spherical Radiation Pattern Plot (Gap 1 fix)
# ------------------------------------------------------------------------------
def plot_3d_spherical_pattern(N=4, d=None, beta=0.0, taper='uniform',
                              filename=_out("radiation_3d_spherical.png")):
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
    print("  [Saved] {}".format(os.path.basename(filename)))


def _compare_tapers(N=4, d=None, beta=0.0, filename=_out("taper_comparison.png")):
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
    fig.savefig(filename, dpi=150)
    plt.close(fig)
    print("  [Saved] {}".format(os.path.basename(filename)))


# ------------------------------------------------------------------------------
# 9. Main Execution Routine
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

    # 0. Radiation integral check: A_z -> E, H -> Poynting -> R_rad of lambda/2 dipole
    P_hw, R_hw = dipole_radiated_power(L_DIPOLE)
    print("  R_rad (lambda/2, from Poynting integration) : {:.2f} Ohm  (textbook 73.08)".format(R_hw))

    print("-" * 65)
    print("  [A] N-ELEMENT UNIFORM LINEAR ARRAY (beamforming model)")
    print("  Array Elements (N)  : {}".format(N_elements))
    print("  Element Spacing (d) : {:.2f} lambda = {:.3f} cm".format(d_spacing / LAMBDA, d_spacing * 1e2))
    print("  Progressive Phase   : {:.1f} deg".format(float(np.degrees(beta_phase))))

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
    Z_mat = build_impedance_matrix(N=N_elements, d=d_spacing)
    Z11 = Z_mat[0, 0]
    Z12 = Z_mat[0, 1]
    print("  Z_11 (Self)         : {:+.2f} {:+.2f}j Ohm".format(Z11.real, Z11.imag))
    print("  Z_12 (Mutual)       : {:+.2f} {:+.2f}j Ohm".format(Z12.real, Z12.imag))
    Z_act = active_impedance(N_elements, d_spacing, beta_phase)
    print("  Z_active (all fed)  : " + ", ".join(
        "{:.1f}{:+.1f}j".format(z.real, z.imag) for z in Z_act) + " Ohm")

    # 4. Yagi-Uda (the physical prototype)
    print("-" * 65)
    print("  [B] 4-ELEMENT YAGI-UDA (physical prototype, induced EMF solver)")
    design = load_yagi_design()
    print("  Geometry source     : {}".format(design["source"]))
    for name, L, x in zip(design["names"], design["lengths_m"], design["x_m"]):
        print("    {:<14s} L = {:5.1f} mm ({:.3f} lambda), x = {:+6.1f} mm".format(
            name, L * 1e3, L / LAMBDA, x * 1e3))
    ym = yagi_metrics(design)
    print("  Element currents (relative to driven):")
    for name, mag, ph in ym["currents"]:
        print("    {:<14s} |I| = {:.3f}, angle = {:+7.1f} deg".format(name, mag, ph))
    print("  Z_in (driven)       : {:+.2f} {:+.2f}j Ohm".format(ym["Z_in"].real, ym["Z_in"].imag))
    print("  VSWR / S11          : {:.3f} / {:.2f} dB  ({})".format(
        ym["vswr"], ym["S11_dB"], 'MATCHED (< 2.0)' if ym["vswr"] < 2.0 else 'NEEDS MATCHING'))
    print("  Directivity (D0)    : {:.2f} dBi".format(ym["D0_dBi"]))
    print("  Front-to-Back       : {:.2f} dB".format(ym["front_to_back_dB"]))
    print("  HPBW H / E plane    : {:.1f} / {:.1f} deg".format(ym["hpbw_h_deg"], ym["hpbw_e_deg"]))
    print("  Power balance       : P_rad (Poynting) vs P_in (circuit) differ by {:+.2f} %".format(
        ym["power_balance_pct"]))
    print("=" * 65)

    # 5. Save CSV & Plots
    print("\nGenerating deliverables...")
    ensure_data_dir()
    generate_yagi_theoretical_csv(THEORETICAL_CSV, metrics=ym)
    plot_yagi_patterns(ym)
    freqs, Z_sweep = plot_vswr_s11_sweep(design=design)
    vswr_sweep = np.array([compute_vswr(z, Z0)[1] for z in Z_sweep])
    band = freqs[vswr_sweep < 2.0]
    if band.size:
        print("  VSWR < 2 band       : {:.3f} - {:.3f} GHz".format(band[0] / 1e9, band[-1] / 1e9))
    else:
        print("  VSWR < 2 band       : none in 2.0 - 3.0 GHz")
    plot_polar_pattern(N=N_elements, d=d_spacing, beta=beta_phase)
    plot_beam_steering(N=N_elements, d=d_spacing)
    plot_3d_spherical_pattern(N=N_elements, d=d_spacing, beta=beta_phase, taper='uniform')

    # Also generate a comparison of all three tapers on one polar plot
    _compare_tapers(N_elements, d_spacing, beta_phase)

    print("\nAll tasks completed successfully. Output files generated.")
    print("=" * 65)
