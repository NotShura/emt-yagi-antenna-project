"""
Member 3 — 3D Antenna Assembly Visualizer
==========================================
Generates a 3D visualization of the complete 4-element Yagi-Uda antenna
assembly including:
  - All wire elements (reflector, driven dipole, directors)
  - The boom structure
  - Element labels and dimensions
  - Balun stub illustration
  - Coordinate axes with direction indicators

Outputs:
  - Interactive 3D matplotlib plot
  - Saved PNG images (side view, top view, perspective view)
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Line3DCollection
import json
import os

# Try to load computed dimensions, fall back to computing them
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DIMS_FILE = os.path.join(SCRIPT_DIR, "antenna_dimensions.json")

if os.path.exists(DIMS_FILE):
    with open(DIMS_FILE, "r") as f:
        dims = json.load(f)
else:
    # Compute from scratch if JSON not found
    from dimension_calculator import compute_dimensions
    dims = compute_dimensions()
    # Convert numpy types
    for k, v in dims.items():
        if hasattr(v, 'item'):
            dims[k] = v.item()


def create_3d_visualization():
    """Create a detailed 3D visualization of the Yagi-Uda antenna assembly."""
    
    fig = plt.figure(figsize=(16, 10))
    fig.patch.set_facecolor('#1a1a2e')
    ax = fig.add_subplot(111, projection='3d')
    ax.set_facecolor('#1a1a2e')
    
    # ── Element positions along Z-axis (boom direction) ──
    # Boom runs along Z, elements extend along X, everything centered at Y=0
    
    reflector_z = 0.0
    driven_z = dims["reflector_spacing_mm"]
    director1_z = driven_z + dims["director_1_spacing_mm"]
    director2_z = driven_z + dims["director_2_spacing_mm"]
    
    elements = [
        {
            "name": "Reflector",
            "z": reflector_z,
            "half_length": dims["reflector_length_mm"] / 2,
            "color": "#ff6b6b",
            "linewidth": 4,
        },
        {
            "name": "Driven Dipole",
            "z": driven_z,
            "half_length": dims["driven_dipole_length_mm"] / 2,
            "color": "#ffd93d",
            "linewidth": 5,
        },
        {
            "name": "Director 1",
            "z": director1_z,
            "half_length": dims["director_1_length_mm"] / 2,
            "color": "#6bcb77",
            "linewidth": 3.5,
        },
        {
            "name": "Director 2",
            "z": director2_z,
            "half_length": dims["director_2_length_mm"] / 2,
            "color": "#4d96ff",
            "linewidth": 3.5,
        },
    ]
    
    # ── Draw the boom ──
    boom_z = [reflector_z - 5, director2_z + 5]
    ax.plot([0, 0], [0, 0], boom_z, color='#8d8d8d', linewidth=8,
            alpha=0.6, solid_capstyle='round', label='Boom')
    
    # ── Draw each element ──
    for elem in elements:
        x_vals = [-elem["half_length"], elem["half_length"]]
        y_vals = [0, 0]
        z_vals = [elem["z"], elem["z"]]
        
        ax.plot(x_vals, y_vals, z_vals,
                color=elem["color"],
                linewidth=elem["linewidth"],
                solid_capstyle='round',
                label=f'{elem["name"]} ({elem["half_length"]*2:.1f} mm)')
        
        # Add element endpoints (wire tips)
        ax.scatter([-elem["half_length"], elem["half_length"]],
                   [0, 0], [elem["z"], elem["z"]],
                   color=elem["color"], s=30, zorder=5)
        
        # Add dimension annotation
        ax.text(elem["half_length"] + 3, 0, elem["z"],
                f'{elem["half_length"]*2:.1f} mm',
                color=elem["color"], fontsize=8, fontweight='bold',
                ha='left', va='center')
    
    # ── Draw the feedpoint (gap in driven dipole) ──
    gap = 2  # mm gap at center
    ax.scatter([0], [0], [driven_z], color='#ffd93d', s=100,
               marker='o', zorder=10, edgecolors='white', linewidths=1.5)
    ax.text(0, -5, driven_z, 'FEED\nPOINT', color='#ffd93d',
            fontsize=8, fontweight='bold', ha='center', va='top')
    
    # ── Draw the balun stub ──
    balun_length = dims.get("balun_length_rg174_mm", 20)
    # Balun runs downward (-Y direction) from feedpoint
    ax.plot([0, 0], [0, -balun_length/3], [driven_z, driven_z],
            color='#e8a87c', linewidth=3, linestyle='--', label=f'Balun stub ({balun_length:.1f} mm)')
    ax.plot([0, 0], [-balun_length/3, -balun_length/3], [driven_z, driven_z - balun_length/3],
            color='#e8a87c', linewidth=3, linestyle='--')
    
    # ── Draw spacing annotations ──
    annotation_x = -max(e["half_length"] for e in elements) - 10
    spacings = [
        (reflector_z, driven_z, f'{dims["reflector_spacing_mm"]:.1f} mm'),
        (driven_z, director1_z, f'{dims["director_1_spacing_mm"]:.1f} mm'),
        (director1_z, director2_z, f'{dims["director_2_spacing_mm"] - dims["director_1_spacing_mm"]:.1f} mm'),
    ]
    
    for z1, z2, label in spacings:
        mid_z = (z1 + z2) / 2
        ax.plot([annotation_x, annotation_x], [0, 0], [z1, z2],
                color='#cccccc', linewidth=1, linestyle=':')
        ax.text(annotation_x - 3, 0, mid_z, label,
                color='#cccccc', fontsize=7, ha='right', va='center')
    
    # ── Draw signal direction arrow ──
    arrow_z_start = director2_z + 10
    arrow_z_end = director2_z + 25
    ax.quiver(0, 0, arrow_z_start, 0, 0, 15,
              color='#00ff88', arrow_length_ratio=0.4, linewidth=2)
    ax.text(0, 0, arrow_z_end + 5, 'Main Beam\nDirection →',
            color='#00ff88', fontsize=9, fontweight='bold',
            ha='center', va='bottom')
    
    # ── Axis labels and formatting ──
    ax.set_xlabel('Element Length (mm)', color='white', fontsize=10, labelpad=10)
    ax.set_ylabel('Y (mm)', color='white', fontsize=10, labelpad=10)
    ax.set_zlabel('Boom Axis (mm)', color='white', fontsize=10, labelpad=10)
    
    ax.set_title('4-Element 2.44 GHz Yagi-Uda Antenna Assembly\n'
                 'Member 3 — Hardware Blueprint Visualization',
                 color='white', fontsize=14, fontweight='bold', pad=20)
    
    # Style the axes
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    ax.tick_params(axis='z', colors='white')
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    ax.xaxis.pane.set_edgecolor('#333333')
    ax.yaxis.pane.set_edgecolor('#333333')
    ax.zaxis.pane.set_edgecolor('#333333')
    ax.grid(True, alpha=0.2, color='#555555')
    
    # Legend
    legend = ax.legend(loc='upper left', fontsize=8,
                       facecolor='#2a2a4e', edgecolor='#555555',
                       labelcolor='white')
    
    # Set viewing angle
    ax.view_init(elev=20, azim=-60)
    
    return fig, ax


def create_2d_side_view():
    """Create a clean 2D side-view engineering diagram."""
    
    fig, ax = plt.subplots(figsize=(14, 6))
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#16213e')
    
    # Element positions along X (boom) and heights along Y
    reflector_x = 0.0
    driven_x = dims["reflector_spacing_mm"]
    director1_x = driven_x + dims["director_1_spacing_mm"]
    director2_x = driven_x + dims["director_2_spacing_mm"]
    
    elements = [
        ("Reflector", reflector_x, dims["reflector_length_mm"], "#ff6b6b"),
        ("Driven Dipole", driven_x, dims["driven_dipole_length_mm"], "#ffd93d"),
        ("Director 1", director1_x, dims["director_1_length_mm"], "#6bcb77"),
        ("Director 2", director2_x, dims["director_2_length_mm"], "#4d96ff"),
    ]
    
    # Draw boom
    ax.plot([reflector_x - 3, director2_x + 3], [0, 0],
            color='#8d8d8d', linewidth=10, solid_capstyle='round',
            alpha=0.5, zorder=1)
    ax.text((reflector_x + director2_x) / 2, -4, 'BOOM',
            color='#8d8d8d', fontsize=9, ha='center', fontweight='bold')
    
    # Draw elements
    for name, x, length, color in elements:
        half = length / 2
        # Vertical line representing the element
        ax.plot([x, x], [-half, half], color=color, linewidth=4,
                solid_capstyle='round', zorder=3)
        
        # Endpoints
        ax.scatter([x, x], [-half, half], color=color, s=40, zorder=4)
        
        # Label above
        ax.text(x, half + 4, f'{name}\n{length:.1f} mm',
                color=color, fontsize=8, fontweight='bold',
                ha='center', va='bottom')
    
    # Feedpoint marker
    ax.scatter([driven_x], [0], color='white', s=120, marker='*', zorder=5)
    ax.text(driven_x, -dims["driven_dipole_length_mm"]/2 - 6,
            'FEED', color='#ffd93d', fontsize=8,
            ha='center', fontweight='bold')
    
    # Spacing annotations (below boom)
    annotation_y = -max(e[2] for e in elements) / 2 - 12
    spacings = [
        (reflector_x, driven_x, dims["reflector_spacing_mm"]),
        (driven_x, director1_x, dims["director_1_spacing_mm"]),
        (director1_x, director2_x, dims["director_2_spacing_mm"] - dims["director_1_spacing_mm"]),
    ]
    
    for x1, x2, dist in spacings:
        mid = (x1 + x2) / 2
        ax.annotate('', xy=(x2, annotation_y), xytext=(x1, annotation_y),
                     arrowprops=dict(arrowstyle='<->', color='#cccccc', lw=1.5))
        ax.text(mid, annotation_y - 3, f'{dist:.1f} mm',
                color='#cccccc', fontsize=8, ha='center', va='top')
    
    # Signal direction arrow
    ax.annotate('', xy=(director2_x + 20, 0),
                xytext=(director2_x + 8, 0),
                arrowprops=dict(arrowstyle='->', color='#00ff88', lw=3))
    ax.text(director2_x + 25, 0, 'Main Beam\nDirection',
            color='#00ff88', fontsize=9, fontweight='bold',
            va='center')
    
    # Title
    ax.set_title('Yagi-Uda Antenna — Side View Engineering Diagram\n'
                 f'f₀ = {dims["frequency_ghz"]:.3f} GHz  |  λ = {dims["wavelength_cm"]:.2f} cm  |  '
                 f'Boom = {dims["boom_length_mm"]:.1f} mm',
                 color='white', fontsize=13, fontweight='bold', pad=15)
    
    ax.set_xlabel('Boom Axis (mm)', color='white', fontsize=10)
    ax.set_ylabel('Element Length Axis (mm)', color='white', fontsize=10)
    ax.tick_params(colors='white')
    ax.spines['bottom'].set_color('#555555')
    ax.spines['left'].set_color('#555555')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.15, color='#555555')
    
    return fig, ax


def create_protractor_template():
    """Generate a printable 360° protractor template for the turntable rig."""
    
    fig, ax = plt.subplots(figsize=(10, 10))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    
    # Draw concentric circles
    for r in [0.3, 0.5, 0.7, 0.85, 1.0]:
        circle = plt.Circle((0, 0), r, fill=False, color='#cccccc',
                             linewidth=0.5 if r != 1.0 else 2)
        ax.add_patch(circle)
    
    # Draw degree markings
    for angle in range(0, 360, 10):
        rad = np.radians(angle)
        
        # Major tick (every 10°)
        inner_r = 0.88 if angle % 30 == 0 else 0.92
        outer_r = 1.0
        
        ax.plot([inner_r * np.cos(rad), outer_r * np.cos(rad)],
                [inner_r * np.sin(rad), outer_r * np.sin(rad)],
                color='black', linewidth=1.5 if angle % 30 == 0 else 0.8)
        
        # Degree labels (every 10°)
        label_r = 1.08
        ax.text(label_r * np.cos(rad), label_r * np.sin(rad),
                f'{angle}°', fontsize=7 if angle % 30 != 0 else 9,
                ha='center', va='center', fontweight='bold' if angle % 30 == 0 else 'normal',
                color='black')
    
    # Minor ticks (every 5°)
    for angle in range(0, 360, 5):
        if angle % 10 != 0:
            rad = np.radians(angle)
            ax.plot([0.95 * np.cos(rad), 1.0 * np.cos(rad)],
                    [0.95 * np.sin(rad), 1.0 * np.sin(rad)],
                    color='#888888', linewidth=0.5)
    
    # Cardinal direction labels
    cardinals = [(0, 'E (0°)'), (90, 'N (90°)'), (180, 'W (180°)'), (270, 'S (270°)')]
    for angle, label in cardinals:
        rad = np.radians(angle)
        ax.text(1.22 * np.cos(rad), 1.22 * np.sin(rad), label,
                fontsize=11, fontweight='bold', ha='center', va='center',
                color='#e63946',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='#fff1f1',
                          edgecolor='#e63946', alpha=0.9))
    
    # Center crosshairs
    ax.plot([-0.05, 0.05], [0, 0], color='red', linewidth=1)
    ax.plot([0, 0], [-0.05, 0.05], color='red', linewidth=1)
    ax.scatter([0], [0], color='red', s=20, zorder=10)
    ax.text(0, -0.1, 'CENTER\nPIVOT', fontsize=7, ha='center',
            va='top', color='red', fontweight='bold')
    
    # Title
    ax.set_title('360° Protractor Template — Azimuthal Measurement Rig\n'
                 'Print at 100% scale on A4 paper | Mark every 10° for RSSI sweep',
                 fontsize=12, fontweight='bold', pad=20)
    
    ax.set_xlim(-1.4, 1.4)
    ax.set_ylim(-1.4, 1.4)
    ax.set_aspect('equal')
    ax.axis('off')
    
    return fig, ax


# ============================================================================
# MAIN: Generate all visualizations
# ============================================================================
if __name__ == "__main__":
    output_dir = os.path.join(SCRIPT_DIR, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    print("Generating 3D antenna assembly visualization...")
    fig3d, _ = create_3d_visualization()
    fig3d.savefig(os.path.join(output_dir, "antenna_3d_assembly.png"),
                  dpi=200, bbox_inches='tight', facecolor=fig3d.get_facecolor())
    print(f"  Saved: {os.path.join(output_dir, 'antenna_3d_assembly.png')}")
    
    print("Generating 2D side-view engineering diagram...")
    fig2d, _ = create_2d_side_view()
    fig2d.savefig(os.path.join(output_dir, "antenna_side_view.png"),
                  dpi=200, bbox_inches='tight', facecolor=fig2d.get_facecolor())
    print(f"  Saved: {os.path.join(output_dir, 'antenna_side_view.png')}")
    
    print("Generating protractor template...")
    fig_prot, _ = create_protractor_template()
    fig_prot.savefig(os.path.join(output_dir, "protractor_template.png"),
                     dpi=300, bbox_inches='tight', facecolor='white')
    print(f"  Saved: {os.path.join(output_dir, 'protractor_template.png')}")
    
    print("\nAll visualizations generated successfully!")
    print(f"Output directory: {output_dir}")
    
    plt.show()
