# ==============================================================================
# run_pipeline.py
# Regenerates every member's outputs in dependency order, from the repo root:
#
#   Member 2  simulate_yagi.py        -> data/optimized_dimensions.json
#                                        data/simulated_pattern.csv
#   Member 3  dimension_calculator.py -> cutting blueprint (reads the dimensions)
#             balun_calculator.py     -> balun designs
#             visualize_antenna.py    -> assembly diagrams + protractor
#   Lead      antenna_math_engine.py  -> data/theoretical_pattern.csv + plots
#   Member 4  virtual_measurement.py  -> data/empirical_pattern.csv (software
#                                        turntable sweep of the simulated antenna;
#                                        hardware-free "measurement" curve)
#             friis_link_budget.py    -> far-field distance + link budget + error
#   Member 2  build_pdf_report.py     -> PDF report (skipped if reportlab missing)
#   Demo      build_studio.py         -> antenna_studio/antenna_studio.html (live
#                                        3D Yagi designer, built from the CSVs above)
#
# Usage:
#   python run_pipeline.py            # regenerate everything
#   python run_pipeline.py --studio   # ...then open the Antenna Studio (demo app)
#   python run_pipeline.py --gui      # ...then open the matplotlib array dashboard
# ==============================================================================

import os
import sys
import time
import subprocess
import importlib.util

from emt_config import ROOT_DIR, DATA_DIR, EMPIRICAL_CSV

STEPS = [
    ("Member 2: simulation export", "EMT_Member2/simulate_yagi.py"),
    ("Member 3: cutting blueprint", "member3_hardware/dimension_calculator.py"),
    ("Member 3: balun designs", "member3_hardware/balun_calculator.py"),
    ("Member 3: assembly diagrams", "member3_hardware/visualize_antenna.py"),
    ("Lead: analytical EM engine", "Electromagnetic-Theory-Member-1-main/antenna_math_engine.py"),
    ("Member 4: virtual measurement", "member4_telemetry/virtual_measurement.py"),
    ("Member 4: Friis link budget", "member4_telemetry/friis_link_budget.py"),
    ("Member 2: PDF report", "EMT_Member2/build_pdf_report.py"),
    ("Demo: Antenna Studio build", "antenna_studio/build_studio.py"),
]
GUI = "Electromagnetic-Theory-Member-1-main/antenna_gui.py"
STUDIO_HTML = os.path.join(ROOT_DIR, "antenna_studio", "antenna_studio.html")


def run_step(label, script, env):
    print("\n" + "#" * 70)
    print("#  " + label + "  (" + script + ")")
    print("#" * 70, flush=True)
    start = time.time()
    args = [sys.executable, os.path.join(ROOT_DIR, script)]
    if script.endswith("build_studio.py"):
        args.append("--no-open")          # opened below only if --studio is given
    result = subprocess.run(args, cwd=ROOT_DIR, env=env)
    return result.returncode == 0, time.time() - start


def main():
    # Batch steps only save figures: use a non-interactive matplotlib backend
    env = dict(os.environ, MPLBACKEND="Agg", PYTHONIOENCODING="utf-8")
    have_reportlab = importlib.util.find_spec("reportlab") is not None

    summary = []
    for label, script in STEPS:
        if script.endswith("build_pdf_report.py") and not have_reportlab:
            summary.append((label, "skipped (pip install reportlab)", 0.0))
            continue
        ok, secs = run_step(label, script, env)
        summary.append((label, "ok" if ok else "FAILED", secs))
        if not ok:
            break

    print("\n" + "=" * 70)
    print("  PIPELINE SUMMARY")
    print("=" * 70)
    for label, status, secs in summary:
        print("  {:<32s} {:<34s} {:5.1f} s".format(label, status, secs))
    print("  Shared files in: {}".format(os.path.relpath(DATA_DIR, ROOT_DIR)))
    if not os.path.exists(EMPIRICAL_CSV):
        print("  data/empirical_pattern.csv not present yet (Member 4's field sweep)")
    print("=" * 70)

    if any(status == "FAILED" for _, status, _ in summary):
        sys.exit(1)

    if "--studio" in sys.argv[1:]:
        import webbrowser
        webbrowser.open("file:///" + STUDIO_HTML.replace(os.sep, "/"))
        print("  Opened the Antenna Studio in your browser.")

    if "--gui" in sys.argv[1:]:
        subprocess.run([sys.executable, os.path.join(ROOT_DIR, GUI)], cwd=ROOT_DIR)


if __name__ == "__main__":
    main()
