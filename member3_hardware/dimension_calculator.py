"""
Member 3 — Yagi-Uda Antenna Dimension Calculator & Blueprint Generator
========================================================================
Computes all physical dimensions for the 4-element 2.44 GHz Yagi-Uda
parasitic array from electromagnetic first principles. Generates:
  1. Exact millimeter cutting lengths for all wire elements
  2. Inter-element spacings on the boom
  3. Balun (Pawsey stub) dimensions
  4. Coaxial feedline specifications
  5. Far-field measurement distance
  6. Complete Bill of Materials
"""

import os
import sys
import json
import numpy as np

# Shared team config (repo root): constants + data/ file locations
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from emt_config import C0 as C, F0, Z0 as Z0_COAX, load_dimensions

# ============================================================================
# DESIGN FREEZE CONSTANTS (from Master Context Document)
# ============================================================================
LAMBDA_0 = C / F0        # Free-space wavelength (m) ≈ 0.12287 m
WIRE_GAUGE_AWG = 14      # 14 AWG solid copper wire
WIRE_DIAMETER_MM = 1.628 # 14 AWG ≈ 1.628 mm diameter

# ============================================================================
# YAGI-UDA ELEMENT DESIGN RULES
# ============================================================================
# Standard Yagi-Uda design ratios (well-established from NBS Technical Note 688
# and Balanis "Antenna Theory" Chapter 10). These are starting-point ratios;
# Member 2's simulation will fine-tune them.

# Element lengths as fractions of λ
REFLECTOR_LENGTH_RATIO   = 0.482    # Slightly > λ/2 to act as inductive reflector
DRIVEN_DIPOLE_RATIO      = 0.473    # ≈ λ/2 with shortening for finite wire diameter
DIRECTOR_1_LENGTH_RATIO  = 0.451    # Slightly < λ/2 for capacitive director
DIRECTOR_2_LENGTH_RATIO  = 0.442    # Even shorter for tighter beam

# Element spacings from the driven element (fractions of λ)
REFLECTOR_SPACING_RATIO  = 0.20     # Reflector behind driven element
DIRECTOR_1_SPACING_RATIO = 0.15     # Director 1 in front of driven element
DIRECTOR_2_SPACING_RATIO = 0.35     # Director 2 further in front

# Balun: quarter-wave Pawsey stub
BALUN_LENGTH_RATIO = 0.25           # λ/4

# Velocity factor for RG174/RG316 coax (PTFE dielectric)
COAX_VELOCITY_FACTOR = 0.66         # Typical for RG174
COAX_VELOCITY_FACTOR_RG316 = 0.695  # Typical for RG316


def load_member2_optimized():
    """
    Load Member 2's 4nec2-optimized dimensions if available.

    Member 2 (full-wave simulation) is the authoritative source for element
    lengths and spacings. This reads the shared data/optimized_dimensions.json
    and returns it as a dict, or None if not found.
    """
    try:
        return load_dimensions()
    except Exception:
        return None


def compute_dimensions():
    """
    Compute all physical dimensions for the 4-element Yagi-Uda array.

    Element lengths and spacings come from Member 2's optimized 4nec2 design
    when available (optimized_dimensions.json); otherwise they fall back to
    standard textbook Yagi-Uda ratios as a starting point.

    Returns a dictionary with all computed values.
    """
    results = {}
    m2 = load_member2_optimized()
    results["dimension_source"] = (
        m2["_source"] if m2 else "Textbook Yagi-Uda ratios (Member 2 sim not found)"
    )

    # --- Wavelength ---
    results["frequency_ghz"] = F0 / 1e9
    results["wavelength_m"] = LAMBDA_0
    results["wavelength_cm"] = LAMBDA_0 * 100
    results["wavelength_mm"] = LAMBDA_0 * 1000
    results["half_wavelength_mm"] = (LAMBDA_0 / 2) * 1000

    # --- Element Lengths (total tip-to-tip) ---
    if m2:
        results["reflector_length_mm"] = m2["reflector_length_mm"]
        results["driven_dipole_length_mm"] = m2["driven_dipole_length_mm"]
        results["director_1_length_mm"] = m2["director_1_length_mm"]
        results["director_2_length_mm"] = m2["director_2_length_mm"]
    else:
        results["reflector_length_mm"] = REFLECTOR_LENGTH_RATIO * LAMBDA_0 * 1000
        results["driven_dipole_length_mm"] = DRIVEN_DIPOLE_RATIO * LAMBDA_0 * 1000
        results["director_1_length_mm"] = DIRECTOR_1_LENGTH_RATIO * LAMBDA_0 * 1000
        results["director_2_length_mm"] = DIRECTOR_2_LENGTH_RATIO * LAMBDA_0 * 1000

    # Each dipole arm = half of total length (for driven element)
    results["driven_arm_length_mm"] = results["driven_dipole_length_mm"] / 2

    # --- Element Spacings (from driven element, along boom) ---
    if m2:
        results["reflector_spacing_mm"] = m2["reflector_spacing_mm"]
        results["director_1_spacing_mm"] = m2["director_1_spacing_mm"]
        results["director_2_spacing_mm"] = m2["director_2_spacing_mm"]
    else:
        results["reflector_spacing_mm"] = REFLECTOR_SPACING_RATIO * LAMBDA_0 * 1000
        results["director_1_spacing_mm"] = DIRECTOR_1_SPACING_RATIO * LAMBDA_0 * 1000
        results["director_2_spacing_mm"] = DIRECTOR_2_SPACING_RATIO * LAMBDA_0 * 1000
    
    # Total boom length = reflector-to-last-director distance
    results["boom_length_mm"] = (
        results["reflector_spacing_mm"] + results["director_2_spacing_mm"]
    )
    # Add some margin for mounting
    results["boom_length_with_margin_mm"] = results["boom_length_mm"] + 30  # 15mm each end
    
    # --- Balun (Quarter-Wave Pawsey Stub) ---
    # The balun is made from coaxial cable, so we need the electrical λ/4
    # accounting for the velocity factor of the coax
    results["balun_length_free_space_mm"] = BALUN_LENGTH_RATIO * LAMBDA_0 * 1000
    results["balun_length_rg174_mm"] = (
        BALUN_LENGTH_RATIO * LAMBDA_0 * COAX_VELOCITY_FACTOR * 1000
    )
    results["balun_length_rg316_mm"] = (
        BALUN_LENGTH_RATIO * LAMBDA_0 * COAX_VELOCITY_FACTOR_RG316 * 1000
    )
    
    # --- Wire Specifications ---
    results["wire_gauge_awg"] = WIRE_GAUGE_AWG
    results["wire_diameter_mm"] = WIRE_DIAMETER_MM
    results["wire_cross_section_sqmm"] = np.pi * (WIRE_DIAMETER_MM / 2) ** 2
    
    # Total wire needed (all 4 elements + some extra for bending/mounting)
    total_element_wire = (
        results["reflector_length_mm"]
        + results["driven_dipole_length_mm"]
        + results["director_1_length_mm"]
        + results["director_2_length_mm"]
    )
    results["total_wire_needed_mm"] = total_element_wire
    results["total_wire_needed_cm"] = total_element_wire / 10
    # Add 20% margin for errors, bends, and mounting tabs
    results["total_wire_with_margin_mm"] = total_element_wire * 1.2
    results["total_wire_with_margin_cm"] = total_element_wire * 1.2 / 10
    
    # --- FR4 Reflector Screen (Optional) ---
    # Reflector screen should be at least λ × λ for effective reflection
    results["fr4_reflector_width_mm"] = LAMBDA_0 * 1000
    results["fr4_reflector_height_mm"] = LAMBDA_0 * 1000
    
    # --- Far-Field Distance (Fraunhofer Region) ---
    # R > 2D²/λ, where D is the largest antenna dimension
    D = max(results["reflector_length_mm"], results["boom_length_mm"]) / 1000  # convert to m
    results["far_field_distance_m"] = (2 * D**2) / LAMBDA_0
    results["far_field_distance_cm"] = results["far_field_distance_m"] * 100
    # Practical minimum: at least 3λ for reasonable measurements
    practical_min = 3 * LAMBDA_0
    results["practical_min_distance_m"] = max(results["far_field_distance_m"], practical_min)
    results["practical_min_distance_cm"] = results["practical_min_distance_m"] * 100
    
    # --- Impedance Estimates ---
    # A half-wave dipole in free space has Z_in ≈ 73 + j42.5 Ω
    # A Yagi-Uda driven element typically has lower impedance due to mutual coupling
    results["free_space_dipole_impedance"] = complex(73, 42.5)
    results["estimated_yagi_input_impedance"] = complex(25, -5)  # Typical for 4-element Yagi
    results["target_feed_impedance"] = Z0_COAX
    
    # Reflection coefficient Γ
    z_in = results["estimated_yagi_input_impedance"]
    gamma = (z_in - Z0_COAX) / (z_in + Z0_COAX)
    results["reflection_coefficient_mag"] = abs(gamma)
    results["vswr_estimated"] = (1 + abs(gamma)) / (1 - abs(gamma))
    
    # --- Turntable Specifications ---
    results["turntable_diameter_mm"] = 300  # 30 cm diameter protractor
    results["angular_step_deg"] = 10
    results["total_measurement_points"] = 360 // 10  # = 36
    
    return results


def print_cutting_blueprint(dims):
    """Print a formatted cutting blueprint for workshop use."""
    
    print("=" * 72)
    print("  4-ELEMENT 2.44 GHz YAGI-UDA ANTENNA — CUTTING BLUEPRINT")
    print("  Generated for Member 3 Hardware Fabrication")
    print("=" * 72)
    print()
    
    print(f"  Dimension Source:  {dims.get('dimension_source', 'n/a')}")
    print(f"  Center Frequency:  {dims['frequency_ghz']:.3f} GHz")
    print(f"  Free-Space λ:      {dims['wavelength_mm']:.2f} mm  ({dims['wavelength_cm']:.2f} cm)")
    print(f"  Half-Wavelength:   {dims['half_wavelength_mm']:.2f} mm")
    print(f"  Wire:              {dims['wire_gauge_awg']} AWG solid copper")
    print(f"                     (∅ {dims['wire_diameter_mm']:.3f} mm)")
    print()
    
    print("─" * 72)
    print("  ELEMENT CUTTING LENGTHS (tip-to-tip)")
    print("─" * 72)
    print(f"  {'Element':<20} {'Length (mm)':<15} {'Length (cm)':<15} {'Ratio (×λ)'}")
    print(f"  {'─'*20} {'─'*15} {'─'*15} {'─'*10}")
    print(f"  {'Reflector':<20} {dims['reflector_length_mm']:<15.2f} {dims['reflector_length_mm']/10:<15.2f} {REFLECTOR_LENGTH_RATIO:.3f}")
    print(f"  {'Driven Dipole':<20} {dims['driven_dipole_length_mm']:<15.2f} {dims['driven_dipole_length_mm']/10:<15.2f} {DRIVEN_DIPOLE_RATIO:.3f}")
    print(f"  {'  (each arm)':<20} {dims['driven_arm_length_mm']:<15.2f} {dims['driven_arm_length_mm']/10:<15.2f} {'—'}")
    print(f"  {'Director 1':<20} {dims['director_1_length_mm']:<15.2f} {dims['director_1_length_mm']/10:<15.2f} {DIRECTOR_1_LENGTH_RATIO:.3f}")
    print(f"  {'Director 2':<20} {dims['director_2_length_mm']:<15.2f} {dims['director_2_length_mm']/10:<15.2f} {DIRECTOR_2_LENGTH_RATIO:.3f}")
    print()
    print(f"  Total wire needed: {dims['total_wire_needed_cm']:.1f} cm")
    print(f"  With 20% margin:  {dims['total_wire_with_margin_cm']:.1f} cm")
    print()
    
    print("─" * 72)
    print("  ELEMENT SPACINGS ALONG BOOM (from Driven Dipole)")
    print("─" * 72)
    print(f"  {'Element':<20} {'Distance (mm)':<15} {'Distance (cm)':<15} {'Direction'}")
    print(f"  {'─'*20} {'─'*15} {'─'*15} {'─'*15}")
    print(f"  {'Reflector':<20} {dims['reflector_spacing_mm']:<15.2f} {dims['reflector_spacing_mm']/10:<15.2f} {'← BEHIND'}")
    print(f"  {'Driven Dipole':<20} {'0.00':<15} {'0.00':<15} {'(REFERENCE)'}")
    print(f"  {'Director 1':<20} {dims['director_1_spacing_mm']:<15.2f} {dims['director_1_spacing_mm']/10:<15.2f} {'→ FORWARD'}")
    print(f"  {'Director 2':<20} {dims['director_2_spacing_mm']:<15.2f} {dims['director_2_spacing_mm']/10:<15.2f} {'→ FORWARD'}")
    print()
    print(f"  Total boom length: {dims['boom_length_mm']:.2f} mm ({dims['boom_length_mm']/10:.2f} cm)")
    print(f"  With end margins:  {dims['boom_length_with_margin_mm']:.2f} mm ({dims['boom_length_with_margin_mm']/10:.2f} cm)")
    print()
    
    print("─" * 72)
    print("  BOOM LAYOUT DIAGRAM (not to scale)")
    print("─" * 72)
    print()
    print("  Signal Direction ──────────────────────────────────────▶")
    print()
    r_pos = 0
    d_pos = dims['reflector_spacing_mm']
    d1_pos = d_pos + dims['director_1_spacing_mm']
    d2_pos = d_pos + dims['director_2_spacing_mm']
    print(f"  R              D              D1             D2")
    print(f"  │              │              │              │")
    print(f"  ├──────────────┼──────────────┼──────────────┤  ← BOOM")
    print(f"  │              │              │              │")
    print(f"  │          FEED POINT         │              │")
    print(f"  │          (coax here)        │              │")
    print()
    print(f"  Positions from left end of boom:")
    print(f"    Reflector:     0.00 mm")
    print(f"    Driven Dipole: {dims['reflector_spacing_mm']:.2f} mm")
    print(f"    Director 1:    {d1_pos:.2f} mm")
    print(f"    Director 2:    {d2_pos:.2f} mm")
    print()
    
    print("─" * 72)
    print("  BALUN (QUARTER-WAVE PAWSEY STUB)")
    print("─" * 72)
    print(f"  Free-space λ/4:   {dims['balun_length_free_space_mm']:.2f} mm")
    print(f"  RG174 coax λ/4:   {dims['balun_length_rg174_mm']:.2f} mm  (VF = {COAX_VELOCITY_FACTOR})")
    print(f"  RG316 coax λ/4:   {dims['balun_length_rg316_mm']:.2f} mm  (VF = {COAX_VELOCITY_FACTOR_RG316})")
    print()
    print("  NOTE: The balun is made from coaxial cable folded back along the")
    print("        feedline. Its length must account for the velocity factor")
    print("        of the specific coax type used.")
    print()
    
    print("─" * 72)
    print("  IMPEDANCE & MEASUREMENT NOTES")
    print("─" * 72)
    print(f"  Free-space dipole Z_in:  {dims['free_space_dipole_impedance']} Ω")
    print(f"  Estimated Yagi Z_in:     {dims['estimated_yagi_input_impedance']} Ω")
    print(f"  Target feed impedance:   {dims['target_feed_impedance']:.0f} Ω")
    print(f"  Est. |Γ| (mismatch):     {dims['reflection_coefficient_mag']:.3f}")
    print(f"  Est. VSWR:               {dims['vswr_estimated']:.2f}")
    print()
    print(f"  Fraunhofer far-field:    R > {dims['far_field_distance_cm']:.1f} cm")
    print(f"  Practical test distance: ≥ {dims['practical_min_distance_cm']:.1f} cm")
    print(f"                           (Use {max(1.0, dims['practical_min_distance_m']):.1f} m for safety)")
    print()
    
    print("─" * 72)
    print("  TURNTABLE RIG")
    print("─" * 72)
    print(f"  Protractor diameter:     {dims['turntable_diameter_mm']} mm")
    print(f"  Angular step:            {dims['angular_step_deg']}°")
    print(f"  Total measurements:      {dims['total_measurement_points']} points (0° to 350°)")
    print()
    
    print("=" * 72)
    print("  END OF CUTTING BLUEPRINT")
    print("=" * 72)


def generate_bill_of_materials(dims):
    """Print a detailed Bill of Materials."""
    
    print()
    print("=" * 72)
    print("  BILL OF MATERIALS (BOM)")
    print("=" * 72)
    print()
    print(f"  {'#':<4} {'Item':<45} {'Qty':<6} {'Est. Cost (₹)'}")
    print(f"  {'─'*4} {'─'*45} {'─'*6} {'─'*14}")
    
    items = [
        ("1", "14 AWG solid-core copper wire (1 m)", "1 m", "₹50"),
        ("2", "ESP32-WROOM-32 dev board (TX beacon)", "1", "₹225"),
        ("3", "ESP32-WROOM-32 dev board (RX logger)", "1", "₹225"),
        ("2a", "  OR: Use 2 smartphones (₹0)", "—", "₹0"),
        ("4", "SMA female connector + RG174 pigtail", "2", "₹180"),
        ("5", "Copper-clad FR4 sheet (10×10 cm)", "1", "₹80"),
        ("6", "Wooden/acrylic boom (8 cm × 1 cm × 1 cm)", "1", "₹40"),
        ("7", "360° protractor (printed or purchased)", "1", "₹20"),
        ("8", "Cable ties / tape / hot glue", "—", "₹30"),
    ]
    
    for item in items:
        print(f"  {item[0]:<4} {item[1]:<45} {item[2]:<6} {item[3]}")
    
    print()
    print(f"  {'TOTAL (with ESP32s):':<55} ₹850")
    print(f"  {'TOTAL (with smartphones):':<55} ₹400")
    print(f"  {'TOTAL (minimal — wire + boom only):':<55} ₹120")
    print()
    print("  Notes:")
    print("  • ESP32 boards can be replaced by smartphones running Wi-Fi Analyzer")
    print("  • FR4 sheet is optional (cardboard + aluminum foil works too)")
    print("  • SMA connectors optional if using passive wave-launcher mount")
    print()


# ============================================================================
# MAIN EXECUTION
# ============================================================================
if __name__ == "__main__":
    dims = compute_dimensions()
    print_cutting_blueprint(dims)
    generate_bill_of_materials(dims)
    
    # Save dimensions to a JSON file for other scripts to consume
    import json
    
    # Convert complex numbers to strings for JSON serialization
    json_dims = {}
    for k, v in dims.items():
        if isinstance(v, complex):
            json_dims[k] = {"real": v.real, "imag": v.imag}
        elif isinstance(v, np.floating):
            json_dims[k] = float(v)
        elif isinstance(v, np.integer):
            json_dims[k] = int(v)
        else:
            json_dims[k] = v
    
    import os
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_dir, "antenna_dimensions.json")
    
    with open(output_path, "w") as f:
        json.dump(json_dims, f, indent=2)
    
    print(f"\n  Dimensions saved to: {output_path}")
