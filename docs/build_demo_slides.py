"""
build_demo_slides.py
====================
Builds ONE self-contained slideshow (docs/demo_slides.html) for the demo video:
the title card, the "switch to the Studio / terminal" cue cards, the closing
card, and backup stills for when the live Antenna Studio can't run.

Why: during recording you just press the Right arrow / Spacebar instead of
hunting for files. The images are embedded (base64), so the file works offline,
can be moved or shared, and never breaks from a bad path.

Run it from the repo root:
    python docs/build_demo_slides.py
Then open docs/demo_slides.html in a browser and press F (or the toolbar) for
fullscreen. Controls: Right/Space = next, Left = previous, F = fullscreen,
C = toggle captions.

Re-run this script any time the plots are regenerated to refresh the deck.
"""

import os
import base64
import html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "demo_slides.html")

# ----------------------------------------------------------------------------
# Slide deck definition — order matches docs/video_demo_guide.md
# The video is now driven by the live Antenna Studio; this deck only carries
# the title, the two "switch now" cue cards, the closing card, and BACKUP
# stills to use if the live app can't run on the recording machine.
# Each slide is a dict:
#   kind : "title" | "cue" | "image" | "closing" | "divider"
#   For image slides: scene, title, caption, img (path relative to repo root)
# ----------------------------------------------------------------------------
BACKUP = "Backup &mdash; use only if the live Studio can't run"
SLIDES = [
    {"kind": "title",
     "title": "2.44 GHz Yagi-Uda Antenna",
     "subtitle": "Modelled in 3D, solved live, measured and validated",
     "foot": "A directional Wi-Fi antenna made from four copper rods"},

    {"kind": "cue",
     "title": "Switch to the Antenna Studio",
     "cmd": "python run_pipeline.py --studio\n(or double-click antenna_studio/antenna_studio.html)",
     "caption": "Scenes 2&ndash;6 happen live in the Studio: the 3D antenna, the experiments and the virtual measurement. Come back here for Scene 7."},

    {"kind": "cue",
     "title": "Switch to the terminal",
     "cmd": "python run_pipeline.py\nnode antenna_studio/test_engine.js antenna_studio/py_ref.json",
     "caption": "Scene 7: everything rebuilds with one command, and the live app is checked against our Python engine (ALL CHECKS PASSED)."},

    {"kind": "closing",
     "title": "Modelled &rarr; Solved live &rarr; Measured &rarr; Validated",
     "subtitle": "Theory, an independent simulation and the measurement agree.",
     "foot": "Thanks for watching"},

    {"kind": "divider",
     "title": "Backup slides",
     "subtitle": "Only for the case where the live Studio can&rsquo;t run on the recording machine."},

    {"kind": "image", "scene": BACKUP,
     "title": "The Antenna Studio",
     "caption": "Live 3D antenna with its beam, rod currents, polar pattern, readouts and the five design controls.",
     "img": "antenna_studio/studio_preview.png"},

    {"kind": "image", "scene": BACKUP,
     "title": "The antenna as a 3D model",
     "caption": "Four copper rods: reflector (back), driven element, and two directors (front), with exact dimensions.",
     "img": "member3_hardware/output/antenna_3d_assembly.png"},

    {"kind": "image", "scene": BACKUP,
     "title": "Theory: a forward beam",
     "caption": "Our own physics engine's prediction: a big lobe at 0&deg;, little leaking backward.",
     "img": "Electromagnetic-Theory-Member-1-main/radiation_pattern_polar.png"},

    {"kind": "image", "scene": BACKUP,
     "title": "Independent simulation: well matched",
     "caption": "Smith chart from the full-wave simulation: low reflection at 2.44 GHz.",
     "img": "EMT_Member2/smith_chart.png"},

    {"kind": "image", "scene": BACKUP,
     "title": "Virtual measurement (simulated)",
     "caption": "A software turntable sweep of the simulated antenna, with realistic noise. Not lab data.",
     "img": "member4_telemetry/output/virtual_measurement_preview.png"},

    {"kind": "image", "scene": BACKUP,
     "title": "Theory vs simulation",
     "caption": "The two independent methods give the same pattern.",
     "img": "Electromagnetic-Theory-Member-1-main/yagi_theory_vs_sim.png"},
]


def data_uri(path):
    full = os.path.join(ROOT, path)
    if not os.path.exists(full):
        print("  [MISSING] {} - slide will show a placeholder".format(path))
        return None
    with open(full, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return "data:image/png;base64," + b64


def render_slide(i, s):
    n = i + 1
    total = len(SLIDES)
    counter = '<div class="counter">{} / {}</div>'.format(n, total)

    if s["kind"] == "title":
        return (
            '<section class="slide title" data-i="{i}">'
            '{c}'
            '<div class="wrap">'
            '<div class="kicker">PROJECT DEMONSTRATION</div>'
            '<h1>{t}</h1>'
            '<div class="subtitle">{sub}</div>'
            '<div class="foot">{foot}</div>'
            '</div></section>'
        ).format(i=i, c=counter, t=s["title"], sub=s["subtitle"], foot=s["foot"])

    if s["kind"] == "cue":
        return (
            '<section class="slide cue" data-i="{i}">'
            '{c}'
            '<div class="wrap">'
            '<div class="cue-badge">&#9654; DO THIS NOW</div>'
            '<h2>{t}</h2>'
            '<pre class="cmd">{cmd}</pre>'
            '<div class="caption">{cap}</div>'
            '</div></section>'
        ).format(i=i, c=counter, t=s["title"],
                 cmd=html.escape(s["cmd"]), cap=s["caption"])

    if s["kind"] == "divider":
        return (
            '<section class="slide closing" data-i="{i}">'
            '{c}'
            '<div class="wrap">'
            '<h2>{t}</h2>'
            '<div class="foot">{sub}</div>'
            '</div></section>'
        ).format(i=i, c=counter, t=s["title"], sub=s["subtitle"])

    if s["kind"] == "closing":
        return (
            '<section class="slide closing" data-i="{i}">'
            '{c}'
            '<div class="wrap">'
            '<h2 class="closing-h">{t}</h2>'
            '<div class="subtitle">{sub}</div>'
            '<div class="foot">{foot}</div>'
            '</div></section>'
        ).format(i=i, c=counter, t=s["title"], sub=s["subtitle"], foot=s["foot"])

    # image slide
    uri = data_uri(s["img"])
    if uri is None:
        media = '<div class="missing">Image not found:<br>{}</div>'.format(s["img"])
    else:
        media = '<img src="{}" alt="{}">'.format(uri, s.get("title", ""))
    return (
        '<section class="slide image" data-i="{i}">'
        '{c}'
        '<div class="scene">{scene}</div>'
        '<div class="stage">{media}</div>'
        '<div class="capbar">'
        '<div class="cap-title">{title}</div>'
        '<div class="caption">{cap}</div>'
        '</div></section>'
    ).format(i=i, c=counter, scene=s.get("scene", ""), media=media,
             title=s.get("title", ""), cap=s.get("caption", ""))


HTML_TMPL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Antenna Demo Slides</title>
<style>
  :root {{
    --bg: #0b0f14; --panel: #121820; --ink: #e8edf2; --muted: #93a1b0;
    --accent: #4aa3ff; --amber: #ffb64a; --green: #46d39a;
  }}
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; height: 100%; background: var(--bg); color: var(--ink);
    font-family: "Segoe UI", -apple-system, Roboto, Helvetica, Arial, sans-serif; }}
  #deck {{ position: fixed; inset: 0; }}
  .slide {{ position: absolute; inset: 0; display: none; flex-direction: column;
    align-items: center; justify-content: center; padding: 3vh 4vw; }}
  .slide.active {{ display: flex; }}

  /* progress bar */
  #bar {{ position: fixed; top: 0; left: 0; height: 4px; background: var(--accent);
    width: 0; transition: width .2s ease; z-index: 10; }}
  .counter {{ position: fixed; bottom: 14px; right: 18px; color: var(--muted);
    font-size: 14px; letter-spacing: .5px; z-index: 5; }}

  /* image slides */
  .slide.image {{ justify-content: flex-start; }}
  .scene {{ color: var(--accent); font-size: clamp(13px, 1.6vw, 18px);
    font-weight: 600; letter-spacing: .4px; margin: 1vh 0 1.2vh; text-align: center; }}
  .stage {{ flex: 1; width: 100%; display: flex; align-items: center;
    justify-content: center; min-height: 0; }}
  .stage img {{ max-width: 100%; max-height: 72vh; object-fit: contain;
    border-radius: 10px; background: #fff; box-shadow: 0 10px 40px rgba(0,0,0,.5); }}
  .capbar {{ width: min(1100px, 92vw); text-align: center; padding: 1.4vh 0 0.6vh; }}
  .cap-title {{ font-size: clamp(18px, 2.4vw, 30px); font-weight: 700; margin-bottom: 6px; }}
  .caption {{ color: var(--muted); font-size: clamp(13px, 1.5vw, 18px); line-height: 1.5; }}
  .missing {{ color: var(--amber); font-size: 20px; text-align: center; padding: 40px;
    border: 2px dashed var(--amber); border-radius: 10px; }}

  /* title + closing */
  .wrap {{ text-align: center; max-width: 1000px; }}
  .kicker {{ color: var(--accent); letter-spacing: 3px; font-size: clamp(12px,1.4vw,16px);
    font-weight: 700; margin-bottom: 18px; }}
  h1 {{ font-size: clamp(34px, 6vw, 76px); line-height: 1.05; margin: 0 0 18px; }}
  .subtitle {{ color: var(--ink); font-size: clamp(18px, 2.6vw, 30px); opacity: .9; }}
  .foot {{ color: var(--muted); font-size: clamp(14px, 1.7vw, 20px); margin-top: 26px; }}
  .closing-h {{ font-size: clamp(26px, 4.4vw, 56px); line-height: 1.15; margin: 0 0 16px;
    color: var(--green); }}
  h2 {{ font-size: clamp(28px, 4.6vw, 58px); margin: 0 0 20px; }}

  /* cue slides */
  .slide.cue {{ background:
    radial-gradient(1200px 600px at 50% 30%, rgba(255,182,74,.10), transparent 60%); }}
  .cue-badge {{ display: inline-block; background: var(--amber); color: #1a1205;
    font-weight: 800; letter-spacing: 1px; padding: 8px 16px; border-radius: 999px;
    font-size: clamp(13px,1.6vw,17px); margin-bottom: 22px; }}
  .cmd {{ background: #05080c; color: var(--green); border: 1px solid #243041;
    border-radius: 10px; padding: 18px 22px; font-size: clamp(15px, 2vw, 26px);
    font-family: "Cascadia Code", Consolas, monospace; display: inline-block;
    margin: 6px 0 20px; }}

  body.nocap .scene, body.nocap .capbar {{ display: none; }}
  body.nocap .stage img {{ max-height: 92vh; }}

  #hint {{ position: fixed; bottom: 12px; left: 18px; color: #4c5a68; font-size: 12.5px;
    z-index: 5; }}
</style>
</head>
<body>
<div id="bar"></div>
<div id="deck">
{slides}
</div>
<div id="hint">&larr; &rarr; / Space &middot; F fullscreen &middot; C captions</div>
<script>
  const slides = Array.from(document.querySelectorAll('.slide'));
  let idx = 0;
  const bar = document.getElementById('bar');
  function show(n) {{
    idx = Math.max(0, Math.min(slides.length - 1, n));
    slides.forEach((s, i) => s.classList.toggle('active', i === idx));
    bar.style.width = ((idx) / (slides.length - 1) * 100) + '%';
  }}
  function next() {{ show(idx + 1); }}
  function prev() {{ show(idx - 1); }}
  document.addEventListener('keydown', (e) => {{
    if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') {{ e.preventDefault(); next(); }}
    else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {{ e.preventDefault(); prev(); }}
    else if (e.key === 'Home') {{ show(0); }}
    else if (e.key === 'End') {{ show(slides.length - 1); }}
    else if (e.key.toLowerCase() === 'f') {{
      if (!document.fullscreenElement) document.documentElement.requestFullscreen();
      else document.exitFullscreen();
    }}
    else if (e.key.toLowerCase() === 'c') {{ document.body.classList.toggle('nocap'); }}
  }});
  document.addEventListener('click', (e) => {{
    // click right half = next, left half = previous
    if (e.clientX > window.innerWidth * 0.35) next(); else prev();
  }});
  show(0);
</script>
</body>
</html>
"""


def main():
    print("Building demo slideshow ({} slides)...".format(len(SLIDES)))
    body = "\n".join(render_slide(i, s) for i, s in enumerate(SLIDES))
    doc = HTML_TMPL.format(slides=body)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(doc)
    size_mb = os.path.getsize(OUT) / 1e6
    print("Wrote {} ({:.1f} MB)".format(os.path.relpath(OUT, ROOT), size_mb))
    print("Open it in a browser and press F for fullscreen.")


if __name__ == "__main__":
    main()
