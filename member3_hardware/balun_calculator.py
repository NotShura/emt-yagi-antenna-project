"""
Member 3 — Balun Design Calculator
====================================
Calculates the exact dimensions for three types of balun/feed structures
suitable for the 2.44 GHz Yagi-Uda driven dipole:

  1. Quarter-Wave (λ/4) Pawsey Stub Balun
  2. Folded Balun (Bazooka Balun)
  3. Passive Wave-Launcher Cradle (zero-cost, no soldering)

Also computes impedance matching parameters including:
  - Reflection coefficient (Γ)
  - VSWR
  - Return loss (dB)
  - Mismatch loss (dB)
"""

import numpy as np
import json
import os

# ============================================================================
# CONSTANTS
# ============================================================================
C = 299_792_458       # Speed of light (m/s)
F0 = 2.44e9           # Center frequency (Hz)
LAMBDA_0 = C / F0     # Free-space wavelength (m)

# Coaxial cable properties
COAX_TYPES = {
    "RG174": {
        "Z0": 50.0,              # Characteristic impedance (Ω)
        "velocity_factor": 0.66, # VF for polyethylene dielectric
        "outer_diameter_mm": 2.8,
        "loss_dB_per_m_2GHz": 1.9,  # Approximate attenuation at 2 GHz
        "description": "Thin, flexible. Good for short runs."
    },
    "RG316": {
        "Z0": 50.0,
        "velocity_factor": 0.695,  # VF for PTFE dielectric
        "outer_diameter_mm": 2.5,
        "loss_dB_per_m_2GHz": 1.6,
        "description": "PTFE dielectric, lower loss. Slightly stiffer."
    },
    "RG58": {
        "Z0": 50.0,
        "velocity_factor": 0.66,
        "outer_diameter_mm": 5.0,
        "loss_dB_per_m_2GHz": 0.9,
        "description": "Thicker, lower loss. Harder to bend for balun."
    },
    "RG402": {
        "Z0": 50.0,
        "velocity_factor": 0.695,
        "outer_diameter_mm": 3.6,
        "loss_dB_per_m_2GHz": 1.1,
        "description": "Semi-rigid. Best performance but harder to work with."
    },
}

# Yagi-Uda antenna impedance estimates
YAGI_INPUT_IMPEDANCE = complex(25, -5)  # Typical 4-element Yagi
DIPOLE_FREE_SPACE_IMPEDANCE = complex(73, 42.5)


def compute_impedance_matching(z_in, z0=50.0):
    """
    Compute impedance matching parameters.
    
    Parameters
    ----------
    z_in : complex
        Input impedance of the antenna (Ω)
    z0 : float
        Characteristic impedance of the feedline (Ω)
    
    Returns
    -------
    dict with Γ, VSWR, return loss, mismatch loss
    """
    gamma = (z_in - z0) / (z_in + z0)
    gamma_mag = abs(gamma)
    gamma_phase_deg = np.degrees(np.angle(gamma))
    
    vswr = (1 + gamma_mag) / (1 - gamma_mag) if gamma_mag < 1 else float('inf')
    return_loss_dB = -20 * np.log10(gamma_mag) if gamma_mag > 0 else float('inf')
    mismatch_loss_dB = -10 * np.log10(1 - gamma_mag**2) if gamma_mag < 1 else float('inf')
    
    # Power delivered fraction
    power_delivered_pct = (1 - gamma_mag**2) * 100
    
    return {
        "z_in_real": z_in.real,
        "z_in_imag": z_in.imag,
        "z0": z0,
        "gamma_magnitude": gamma_mag,
        "gamma_phase_deg": gamma_phase_deg,
        "vswr": vswr,
        "return_loss_dB": return_loss_dB,
        "mismatch_loss_dB": mismatch_loss_dB,
        "power_delivered_pct": power_delivered_pct,
    }


def compute_pawsey_stub_balun(coax_type="RG174"):
    """
    Compute dimensions for a quarter-wave Pawsey stub balun.
    
    The Pawsey stub is a section of coax with its far end shorted (center
    conductor connected to shield). It presents a high impedance at the
    feedpoint, choking off unwanted currents on the outside of the shield.
    
    Parameters
    ----------
    coax_type : str
        Key from COAX_TYPES dict
    
    Returns
    -------
    dict with all balun dimensions and specs
    """
    coax = COAX_TYPES[coax_type]
    vf = coax["velocity_factor"]
    
    # Electrical wavelength in coax
    lambda_coax = LAMBDA_0 * vf
    
    # Quarter-wave stub length
    stub_length_m = lambda_coax / 4
    stub_length_mm = stub_length_m * 1000
    
    # Total coax needed: feedline + stub
    # Feedline length is application-dependent; assume 30 cm for short run
    feedline_length_mm = 300
    total_coax_mm = feedline_length_mm + stub_length_mm
    
    return {
        "type": "Pawsey Stub (λ/4 Shorted Stub)",
        "coax_type": coax_type,
        "coax_z0": coax["Z0"],
        "velocity_factor": vf,
        "coax_outer_diameter_mm": coax["outer_diameter_mm"],
        "coax_loss_dB_per_m": coax["loss_dB_per_m_2GHz"],
        "lambda_free_space_mm": LAMBDA_0 * 1000,
        "lambda_in_coax_mm": lambda_coax * 1000,
        "stub_length_mm": stub_length_mm,
        "stub_length_cm": stub_length_mm / 10,
        "feedline_length_mm": feedline_length_mm,
        "total_coax_needed_mm": total_coax_mm,
        "total_coax_needed_cm": total_coax_mm / 10,
        "description": coax["description"],
        "construction_notes": [
            f"1. Cut a piece of {coax_type} coax to {stub_length_mm:.1f} mm ({stub_length_mm/10:.2f} cm)",
            "2. At one end, strip the jacket and expose center conductor + shield",
            "3. SHORT the center conductor to the shield (solder or crimp)",
            "4. At the other end, connect in PARALLEL to the feedpoint coax",
            "5. Tape/cable-tie the stub back along the main feedline",
            "6. The stub blocks common-mode currents on the coax outer shield",
        ],
    }


def compute_bazooka_balun(coax_type="RG174"):
    """
    Compute dimensions for a sleeve (bazooka) balun.
    
    A bazooka balun uses a quarter-wave metal sleeve around the coax
    to choke shield currents. Simpler construction but needs a tube.
    """
    coax = COAX_TYPES[coax_type]
    vf = coax["velocity_factor"]
    lambda_coax = LAMBDA_0 * vf
    sleeve_length_mm = (lambda_coax / 4) * 1000
    
    # Sleeve should be slightly larger diameter than the coax
    min_sleeve_id_mm = coax["outer_diameter_mm"] + 1.0
    
    return {
        "type": "Bazooka (Sleeve) Balun",
        "coax_type": coax_type,
        "sleeve_length_mm": sleeve_length_mm,
        "sleeve_length_cm": sleeve_length_mm / 10,
        "min_sleeve_inner_diameter_mm": min_sleeve_id_mm,
        "sleeve_material": "Copper/brass tube or aluminum foil tube",
        "construction_notes": [
            f"1. Obtain a conductive tube (ID > {min_sleeve_id_mm:.1f} mm)",
            f"2. Cut the tube to {sleeve_length_mm:.1f} mm ({sleeve_length_mm/10:.2f} cm)",
            "3. Slide the tube over the coax, starting from the feedpoint",
            "4. Connect one end of the tube to the coax shield at the feedpoint",
            "5. Leave the other end of the tube open (NOT connected)",
            "6. The sleeve creates a high-impedance choke for shield currents",
        ],
    }


def compute_passive_mount():
    """
    Compute specifications for the zero-cost passive wave-launcher mount.
    
    No coax cable or soldering needed. The smartphone/ESP32 is placed
    directly at the dipole feedpoint and couples electromagnetically.
    """
    # Optimal coupling gap based on dipole arm width
    coupling_gap_mm = 3.0
    
    return {
        "type": "Passive Wave-Launcher Cradle (Zero-Cost)",
        "requires_soldering": False,
        "requires_coax": False,
        "requires_sma": False,
        "estimated_cost": 0,
        "coupling_gap_mm": coupling_gap_mm,
        "expected_gain_loss_dB": "3-5 dB less than direct coax feed",
        "construction_notes": [
            "1. Mount the driven dipole with a 3 mm center gap as normal",
            "2. Create a small cradle/holder at the feedpoint to hold the phone/ESP32",
            "3. Position the device's internal antenna aligned with the dipole gap",
            "4. The parasitic elements (reflector + directors) still function normally",
            "5. The device couples to the dipole via near-field electromagnetic induction",
            "6. This method trades ~3-5 dB of gain for zero-cost simplicity",
        ],
        "best_for": "Quick testing, zero budget, no soldering tools available",
    }


def print_balun_report():
    """Print a comprehensive balun design report."""
    
    print("=" * 72)
    print("  BALUN DESIGN REPORT — 2.44 GHz Yagi-Uda Feed Structure")
    print("=" * 72)
    print()
    
    # --- Impedance Matching ---
    print("─" * 72)
    print("  IMPEDANCE ANALYSIS")
    print("─" * 72)
    
    match_yagi = compute_impedance_matching(YAGI_INPUT_IMPEDANCE, 50.0)
    match_dipole = compute_impedance_matching(DIPOLE_FREE_SPACE_IMPEDANCE, 50.0)
    
    yagi_z_str = f"{match_yagi['z_in_real']:.1f} + j{match_yagi['z_in_imag']:.1f}"
    dipole_z_str = f"{match_dipole['z_in_real']:.1f} + j{match_dipole['z_in_imag']:.1f}"
    
    print(f"\n  {'Parameter':<30} {'Yagi-Uda':<20} {'Free Dipole':<20}")
    print(f"  {'─'*30} {'─'*20} {'─'*20}")
    print(f"  {'Z_in (Ω)':<30} {yagi_z_str:<20} {dipole_z_str:<20}")
    print(f"  {'|Γ|':<30} {match_yagi['gamma_magnitude']:<20.4f} {match_dipole['gamma_magnitude']:<20.4f}")
    print(f"  {'VSWR':<30} {match_yagi['vswr']:<20.3f} {match_dipole['vswr']:<20.3f}")
    print(f"  {'Return Loss (dB)':<30} {match_yagi['return_loss_dB']:<20.2f} {match_dipole['return_loss_dB']:<20.2f}")
    print(f"  {'Mismatch Loss (dB)':<30} {match_yagi['mismatch_loss_dB']:<20.3f} {match_dipole['mismatch_loss_dB']:<20.3f}")
    print(f"  {'Power Delivered (%)':<30} {match_yagi['power_delivered_pct']:<20.1f} {match_dipole['power_delivered_pct']:<20.1f}")
    print()
    
    # --- Balun Option 1: Pawsey Stub ---
    print("─" * 72)
    print("  OPTION 1: PAWSEY STUB BALUN (Recommended)")
    print("─" * 72)
    
    for coax_name in COAX_TYPES:
        pawsey = compute_pawsey_stub_balun(coax_name)
        print(f"\n  [{coax_name}] — {pawsey['description']}")
        print(f"    Velocity Factor:     {pawsey['velocity_factor']}")
        print(f"    λ in coax:           {pawsey['lambda_in_coax_mm']:.2f} mm")
        print(f"    Stub length (λ/4):   {pawsey['stub_length_mm']:.2f} mm ({pawsey['stub_length_cm']:.2f} cm)")
        print(f"    Coax outer ∅:        {pawsey['coax_outer_diameter_mm']} mm")
        print(f"    Loss:                {pawsey['coax_loss_dB_per_m']:.1f} dB/m at 2 GHz")
    
    print()
    print("  Construction Steps (using RG174):")
    pawsey_rg174 = compute_pawsey_stub_balun("RG174")
    for step in pawsey_rg174["construction_notes"]:
        print(f"    {step}")
    
    # --- Balun Option 2: Bazooka ---
    print()
    print("─" * 72)
    print("  OPTION 2: BAZOOKA (SLEEVE) BALUN")
    print("─" * 72)
    
    bazooka = compute_bazooka_balun("RG174")
    print(f"\n  Sleeve length:         {bazooka['sleeve_length_mm']:.2f} mm ({bazooka['sleeve_length_cm']:.2f} cm)")
    print(f"  Min sleeve inner ∅:   {bazooka['min_sleeve_inner_diameter_mm']:.1f} mm")
    print(f"  Sleeve material:       {bazooka['sleeve_material']}")
    print()
    print("  Construction Steps:")
    for step in bazooka["construction_notes"]:
        print(f"    {step}")
    
    # --- Option 3: Passive Mount ---
    print()
    print("─" * 72)
    print("  OPTION 3: PASSIVE WAVE-LAUNCHER (ZERO-COST)")
    print("─" * 72)
    
    passive = compute_passive_mount()
    print(f"\n  Requires soldering:    {passive['requires_soldering']}")
    print(f"  Requires coax cable:   {passive['requires_coax']}")
    print(f"  Requires SMA:          {passive['requires_sma']}")
    print(f"  Estimated cost:        ₹{passive['estimated_cost']}")
    print(f"  Coupling gap:          {passive['coupling_gap_mm']} mm")
    print(f"  Expected gain loss:    {passive['expected_gain_loss_dB']}")
    print(f"  Best for:              {passive['best_for']}")
    print()
    print("  Construction Steps:")
    for step in passive["construction_notes"]:
        print(f"    {step}")
    
    print()
    print("=" * 72)
    print("  RECOMMENDATION")
    print("=" * 72)
    print()
    print("  For best results:  Pawsey Stub with RG174 (₹90 per SMA pigtail)")
    print("  For zero cost:     Passive Wave-Launcher with smartphone")
    print("  For PPT content:   Show BOTH options to demonstrate understanding")
    print()


# ============================================================================
# MAIN
# ============================================================================
if __name__ == "__main__":
    print_balun_report()
    
    # Save all designs to JSON
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    designs = {
        "impedance_analysis": {
            "yagi": compute_impedance_matching(YAGI_INPUT_IMPEDANCE),
            "dipole": compute_impedance_matching(DIPOLE_FREE_SPACE_IMPEDANCE),
        },
        "pawsey_stub": {
            coax: compute_pawsey_stub_balun(coax)
            for coax in COAX_TYPES
        },
        "bazooka_balun": compute_bazooka_balun("RG174"),
        "passive_mount": compute_passive_mount(),
    }
    
    output_path = os.path.join(output_dir, "balun_designs.json")
    with open(output_path, "w") as f:
        json.dump(designs, f, indent=2, default=str)
    
    print(f"\n  Designs saved to: {output_path}")
