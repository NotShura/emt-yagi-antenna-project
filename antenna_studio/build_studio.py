"""
build_studio.py
===============
Builds the Yagi-Uda Antenna Studio: ONE self-contained HTML file
(antenna_studio/antenna_studio.html) that runs fully offline.

It inlines:
  - vendor/three.min.js        (3D rendering, Three.js r128, MIT)
  - yagi_engine.js             (the live solver; a verified port of the
                                Python engine, see test_engine.js)
  - data/optimized_dimensions.json -> the design the controls reset to
  - data/theoretical_pattern.csv, simulated_pattern.csv,
    empirical_pattern.csv      -> the reference curves on the polar plot

Usage (from the repo root):
    python antenna_studio/build_studio.py           # build, then open it
    python antenna_studio/build_studio.py --no-open # build only
"""
import os
import sys
import csv
import json
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from emt_config import THEORETICAL_CSV, SIMULATED_CSV, EMPIRICAL_CSV, load_dimensions  # noqa: E402

TEMPLATE = os.path.join(HERE, "studio_template.html")
THREE_JS = os.path.join(HERE, "vendor", "three.min.js")
ENGINE_JS = os.path.join(HERE, "yagi_engine.js")
OUT = os.path.join(HERE, "antenna_studio.html")


def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def read_pattern(path):
    angles, gains = [], []
    if os.path.exists(path):
        with open(path, "r", newline="", encoding="ascii") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) >= 2:
                    angles.append(float(row[0]))
                    gains.append(float(row[1]))
    return {"a": angles, "g": gains}


def defaults_from_dimensions():
    """Map Member 2's optimized design onto the Studio's controls."""
    d = load_dimensions()
    if d is None:
        raise SystemExit("data/optimized_dimensions.json missing - run "
                         "python EMT_Member2/simulate_yagi.py (or run_pipeline.py) first.")
    return {
        "freqGHz": d["frequency_ghz"],
        "reflectorMm": d["reflector_length_mm"],
        "drivenMm": d["driven_dipole_length_mm"],
        "director1Mm": d["director_1_length_mm"],
        "directorTaperMm": round(d["director_1_length_mm"] - d["director_2_length_mm"], 4),
        "directors": 2,
        "reflectorGapMm": d["reflector_spacing_mm"],
        "directorGapsMm": [d["director_1_spacing_mm"],
                           round(d["director_2_spacing_mm"] - d["director_1_spacing_mm"], 4)],
        "radiusMm": d["wire_radius_mm"],
    }


def safe_script(js):
    # never let a library close our <script> tag early
    return js.replace("</script", "<\\/script")


def build():
    data = {
        "defaults": defaults_from_dimensions(),
        "refs": {
            "theory": read_pattern(THEORETICAL_CSV),
            "sim": read_pattern(SIMULATED_CSV),
            "meas": read_pattern(EMPIRICAL_CSV),
        },
    }
    html = read(TEMPLATE)
    for marker, content in (("/*__THREE__*/", safe_script(read(THREE_JS))),
                            ("/*__ENGINE__*/", safe_script(read(ENGINE_JS))),
                            ("/*__DATA__*/null", json.dumps(data))):
        if marker not in html:
            raise SystemExit("template marker {} not found".format(marker))
        html = html.replace(marker, content, 1)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print("  Built {} ({:.1f} MB)".format(os.path.relpath(OUT, ROOT), os.path.getsize(OUT) / 1e6))
    return OUT


if __name__ == "__main__":
    path = build()
    if "--no-open" not in sys.argv[1:]:
        webbrowser.open("file:///" + path.replace(os.sep, "/"))
        print("  Opened in your browser.")
