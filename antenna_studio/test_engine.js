/*
 * test_engine.js - checks the browser Yagi solver against the Python engine.
 *
 * Usage:  node antenna_studio/test_engine.js <py_ref.json>
 *
 * The reference JSON is produced by antenna_studio/make_reference.py, which
 * runs antenna_math_engine.yagi_metrics on the same designs. Every metric and
 * every point of the 36-angle H-plane cut must agree within tolerance.
 */
"use strict";
var fs = require("fs");
var path = require("path");
var E = require(path.join(__dirname, "yagi_engine.js"));

var refPath = process.argv[2];
if (!refPath) { console.error("usage: node test_engine.js <py_ref.json>"); process.exit(2); }
var ref = JSON.parse(fs.readFileSync(refPath, "utf8"));

var TOL_DB = 0.05;      // dB tolerance on gains / cuts
var TOL_DEG = 0.5;      // beamwidth tolerance (deg)
var TOL_OHM = 0.05;     // impedance tolerance (ohm)
var failures = 0;

function check(label, a, b, tol) {
  var ok = (a === null && b === null) || Math.abs(a - b) <= tol;
  if (!ok) { failures++; }
  return (ok ? "ok  " : "FAIL") + " " + label + " js=" + (a === null ? "null" : a.toFixed(3)) +
    " py=" + (b === null ? "null" : b.toFixed(3));
}

Object.keys(ref).forEach(function (name) {
  var r = ref[name], p = r.params;
  var design = E.buildDesign(p);
  var t0 = Date.now();
  var a = E.analyse(design, p.freqGHz * 1e9, { step: 0.1 });
  var ms = Date.now() - t0;
  var h36 = E.hPlane(a.sol, a.Prad, Array.from({ length: 36 }, function (_, i) { return i * 10; }))
    .map(function (d) { return 10 * Math.log10(d); });
  var worst = 0;
  h36.forEach(function (v, i) { worst = Math.max(worst, Math.abs(v - r.h36[i])); });
  if (worst > TOL_DB) { failures++; }
  console.log("\n[" + name + "]  (" + ms + " ms full-accuracy solve)");
  console.log("  " + check("gain dBi ", a.gainDbi, r.gain, TOL_DB));
  console.log("  " + check("F/B dB   ", a.fbDb, r.fb, TOL_DB));
  console.log("  " + check("HPBW deg ", a.hpbwH, r.hpbwH, TOL_DEG));
  console.log("  " + check("Zin re   ", a.Zin.re, r.Zin[0], TOL_OHM));
  console.log("  " + check("Zin im   ", a.Zin.im, r.Zin[1], TOL_OHM));
  console.log("  " + (worst <= TOL_DB ? "ok  " : "FAIL") + " 36-pt H-plane cut, worst diff = " +
    worst.toFixed(4) + " dB");
});

console.log("\n" + (failures === 0 ? "ALL CHECKS PASSED" : failures + " CHECK(S) FAILED"));
process.exit(failures === 0 ? 0 : 1);
