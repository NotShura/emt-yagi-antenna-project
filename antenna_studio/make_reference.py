"""
make_reference.py
=================
Runs the Project Lead's Python engine (antenna_math_engine.yagi_metrics) on a
set of Yagi designs and writes antenna_studio/py_ref.json. The browser solver
(yagi_engine.js) is then checked against it:

    python antenna_studio/make_reference.py
    node   antenna_studio/test_engine.js antenna_studio/py_ref.json

The designs are built with the same rules as the Studio's controls
(yagi_engine.js -> buildDesign), so this proves the live app shows exactly the
same physics as the theory CSV, not an approximation of it.
"""
import os
import sys
import json

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "Electromagnetic-Theory-Member-1-main"))
import antenna_math_engine as ame  # noqa: E402

BASE = dict(reflectorMm=59.0, drivenMm=55.6, director1Mm=52.2, directorTaperMm=1.8,
            directors=2, reflectorGapMm=24.6, directorGapsMm=[20.9, 24.6],
            spacingScale=1.0, radiusMm=0.814, freqGHz=2.44)

CASES = {
    "default": {},
    "f2.30": {"freqGHz": 2.30},
    "dir5": {"directors": 5},
    "dir0": {"directors": 0},
    "refl54": {"reflectorMm": 54.0},
    "spacing0.7": {"spacingScale": 0.7},
}


def build(p):
    """Python twin of yagi_engine.js buildDesign()."""
    mm, s = 1e-3, p["spacingScale"]
    lengths = [p["reflectorMm"] * mm, p["drivenMm"] * mm]
    xs = [-p["reflectorGapMm"] * s * mm, 0.0]
    gaps, x = p["directorGapsMm"], 0.0
    for i in range(p["directors"]):
        x += (gaps[i] if i < len(gaps) else gaps[-1]) * s
        lengths.append((p["director1Mm"] - p["directorTaperMm"] * i) * mm)
        xs.append(x * mm)
    return {"names": ("rod",) * len(lengths), "lengths_m": np.array(lengths),
            "x_m": np.array(xs), "radius_m": p["radiusMm"] * mm, "feed_index": 1}


def main():
    out = {}
    for name, change in CASES.items():
        p = dict(BASE)
        p.update(change)
        m = ame.yagi_metrics(build(p), p["freqGHz"] * 1e9)
        dh = ame.yagi_h_plane(np.arange(0, 360, 10), m["sol"], m["P_rad_W"])
        out[name] = {
            "params": p, "gain": m["D0_dBi"], "fb": m["front_to_back_dB"],
            "hpbwH": m["hpbw_h_deg"], "Zin": [m["Z_in"].real, m["Z_in"].imag],
            "vswr": m["vswr"], "h36": list(10 * np.log10(dh)),
        }
        print("  {:11s} gain {:6.2f} dBi  F/B {:6.2f} dB  VSWR {:5.2f}".format(
            name, m["D0_dBi"], m["front_to_back_dB"], m["vswr"]))
    path = os.path.join(HERE, "py_ref.json")
    with open(path, "w", encoding="ascii") as f:
        json.dump(out, f, indent=1)
    print("  Wrote {}".format(os.path.relpath(path, ROOT)))


if __name__ == "__main__":
    main()
