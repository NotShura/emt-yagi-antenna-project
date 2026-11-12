/*
 * yagi_engine.js
 * ==============
 * Live Yagi-Uda solver for the Antenna Studio. A direct JavaScript port of the
 * Project Lead's Python engine (antenna_math_engine.py: mutual_impedance,
 * yagi_impedance_matrix, solve_yagi, yagi_sum, yagi_radiated_power,
 * yagi_h_plane, yagi_e_plane, cut_hpbw, yagi_metrics), so the browser shows
 * exactly the same physics as the theory CSV - just fast enough to run on
 * every slider movement.
 *
 * Method: induced-EMF (King) mutual impedance between parallel thin dipoles,
 * a full N x N complex impedance matrix, Z I = V with only the driven element
 * fed, then the far field as the sum of every rod's re-radiated field.
 *
 * Geometry convention (same as the Python engine): rods along z, boom along x,
 * directors toward +x, so the main beam points at phi = 0 in the H-plane.
 *
 * Works in the browser (window.YagiEngine) and in Node (module.exports).
 */
(function (root) {
  "use strict";

  var C0 = 299792458.0;
  var ETA0 = 120.0 * Math.PI;
  var TWO_PI = 2.0 * Math.PI;

  // ---------------------------------------------------------------------------
  // Mutual impedance between two parallel dipoles (referred to current maxima).
  // rho = wire radius gives the self impedance. Trapezoid rule, same sample
  // count rule as the Python engine.
  // ---------------------------------------------------------------------------
  function mutualImpedance(L1, L2, rho, k) {
    var h1 = L1 / 2, h2 = L2 / 2;
    var n = Math.max(2001, Math.ceil(L2 / (rho / 100)) + 1);
    var dz = (2 * h2) / (n - 1);
    var c = Math.cos(k * h1);
    var K = ETA0 / (4 * Math.PI);
    var rho2 = rho * rho;
    var sr = 0, si = 0, last = n - 1;
    // The integrand is even in z (R1 and R2 swap under z -> -z, R0 and the
    // current weight are symmetric), so integrate one half and count each
    // mirrored sample twice. Same trapezoid sum, half the work.
    for (var i = 0; 2 * i <= last; i++) {
      var z = -h2 + i * dz;
      var R1 = Math.sqrt(rho2 + (z - h1) * (z - h1));
      var R2 = Math.sqrt(rho2 + (z + h1) * (z + h1));
      var R0 = Math.sqrt(rho2 + z * z);
      // sum of e^{-jkR}/R terms: (ar + j ai)
      var ar = Math.cos(k * R1) / R1 + Math.cos(k * R2) / R2 - 2 * c * Math.cos(k * R0) / R0;
      var ai = -(Math.sin(k * R1) / R1 + Math.sin(k * R2) / R2 - 2 * c * Math.sin(k * R0) / R0);
      // Ez = -j K (ar + j ai) = K (ai - j ar)
      var w = Math.sin(k * (h2 - Math.abs(z)));
      var wt = (i === 0) ? 0.5 : 1.0;
      var mult = (2 * i === last) ? 1 : 2;
      sr += mult * wt * K * ai * w;
      si += mult * wt * (-K * ar) * w;
    }
    return { re: -sr * dz, im: -si * dz };
  }

  // Complex Gaussian elimination with partial pivoting. A is n x n of {re,im},
  // b is length n of {re,im}. Returns x.
  function solveComplex(A, b) {
    var n = b.length, i, j, r;
    var Mr = [], Mi = [];
    for (i = 0; i < n; i++) {
      Mr.push(new Float64Array(n + 1));
      Mi.push(new Float64Array(n + 1));
      for (j = 0; j < n; j++) { Mr[i][j] = A[i][j].re; Mi[i][j] = A[i][j].im; }
      Mr[i][n] = b[i].re; Mi[i][n] = b[i].im;
    }
    for (var col = 0; col < n; col++) {
      var piv = col, best = -1;
      for (r = col; r < n; r++) {
        var mag = Mr[r][col] * Mr[r][col] + Mi[r][col] * Mi[r][col];
        if (mag > best) { best = mag; piv = r; }
      }
      if (piv !== col) {
        var t = Mr[piv]; Mr[piv] = Mr[col]; Mr[col] = t;
        t = Mi[piv]; Mi[piv] = Mi[col]; Mi[col] = t;
      }
      var pr = Mr[col][col], pi = Mi[col][col];
      var den = pr * pr + pi * pi;
      for (r = col + 1; r < n; r++) {
        // f = M[r][col] / pivot
        var fr = (Mr[r][col] * pr + Mi[r][col] * pi) / den;
        var fi = (Mi[r][col] * pr - Mr[r][col] * pi) / den;
        for (j = col; j <= n; j++) {
          Mr[r][j] -= fr * Mr[col][j] - fi * Mi[col][j];
          Mi[r][j] -= fr * Mi[col][j] + fi * Mr[col][j];
        }
      }
    }
    var x = new Array(n);
    for (i = n - 1; i >= 0; i--) {
      var sr = Mr[i][n], si = Mi[i][n];
      for (j = i + 1; j < n; j++) {
        sr -= Mr[i][j] * x[j].re - Mi[i][j] * x[j].im;
        si -= Mr[i][j] * x[j].im + Mi[i][j] * x[j].re;
      }
      var ar = Mr[i][i], ai = Mi[i][i], d2 = ar * ar + ai * ai;
      x[i] = { re: (sr * ar + si * ai) / d2, im: (si * ar - sr * ai) / d2 };
    }
    return x;
  }

  // Memo of impedance terms. While one slider is dragged most rod pairs keep
  // the same (L1, L2, distance, k), so only the terms that actually changed
  // are re-integrated. Results are bit-identical to recomputing everything.
  var zCache = new Map();
  function cachedMutual(L1, L2, rho, k) {
    var key = L1 + "|" + L2 + "|" + rho + "|" + k;
    var v = zCache.get(key);
    if (v === undefined) {
      if (zCache.size > 4000) { zCache.clear(); }
      v = mutualImpedance(L1, L2, rho, k);
      zCache.set(key, v);
    }
    return v;
  }

  // ---------------------------------------------------------------------------
  // Solve the array: impedance matrix (terminal currents), currents, Z_in.
  // design = { lengths: [m...], x: [m...], radius: m, feed: index }
  // ---------------------------------------------------------------------------
  function solve(design, freqHz) {
    var k = TWO_PI * freqHz / C0;
    var L = design.lengths, x = design.x, n = L.length;
    var Z = [], i, j;
    for (i = 0; i < n; i++) { Z.push(new Array(n)); }
    for (i = 0; i < n; i++) {
      for (j = i; j < n; j++) {
        var rho = (i === j) ? design.radius : Math.abs(x[i] - x[j]);
        var zm = cachedMutual(L[i], L[j], rho, k);
        var s = Math.sin(k * L[i] / 2) * Math.sin(k * L[j] / 2);
        var zt = { re: zm.re / s, im: zm.im / s };
        Z[i][j] = zt; Z[j][i] = zt;
      }
    }
    var V = [];
    for (i = 0; i < n; i++) { V.push({ re: i === design.feed ? 1 : 0, im: 0 }); }
    var Ib = solveComplex(Z, V);
    var Imax = Ib.map(function (c, idx) {
      var s = Math.sin(k * L[idx] / 2);
      return { re: c.re / s, im: c.im / s };
    });
    var If = Ib[design.feed], d = If.re * If.re + If.im * If.im;
    return {
      design: design, k: k, freq: freqHz,
      Ibase: Ib, Imax: Imax,
      Zin: { re: If.re / d, im: -If.im / d }
    };
  }

  // Sum of every rod's field: S = sum Im_n F_n(cos t) e^{j k x_n ux}
  // Returns |S|^2. F_n is the finite-length dipole factor.
  function fieldPower(sol, cosT, sinT, ux) {
    var d = sol.design, k = sol.k, Sr = 0, Si = 0;
    if (sinT <= 1e-9) { return 0; }
    for (var n = 0; n < d.lengths.length; n++) {
      var kh = k * d.lengths[n] / 2;
      var F = (Math.cos(kh * cosT) - Math.cos(kh)) / sinT;
      var ph = k * d.x[n] * ux;
      var cr = Math.cos(ph), ci = Math.sin(ph);
      var Ir = sol.Imax[n].re * F, Ii = sol.Imax[n].im * F;
      Sr += Ir * cr - Ii * ci;
      Si += Ir * ci + Ii * cr;
    }
    return Sr * Sr + Si * Si;
  }

  var U_SCALE = ETA0 / (8 * Math.PI * Math.PI);

  function simpsonWeights(n, h) {
    var w = new Float64Array(n);
    for (var i = 0; i < n; i++) {
      w[i] = (i === 0 || i === n - 1) ? 1 : (i % 2 === 1 ? 4 : 2);
      w[i] *= h / 3;
    }
    return w;
  }

  // Total radiated power by 2D Simpson integration over the sphere. Uses the
  // phi -> -phi symmetry of the array (integrate 0..pi, double it), which is
  // exactly equal to the Python 0..2pi Simpson on the same 1-degree grid.
  function radiatedPower(sol, nTheta, nPhiHalf) {
    nTheta = nTheta || 181;
    nPhiHalf = nPhiHalf || 181;
    var d = sol.design, k = sol.k, N = d.lengths.length, n, j;
    var wt = simpsonWeights(nTheta, Math.PI / (nTheta - 1));
    var wp = simpsonWeights(nPhiHalf, Math.PI / (nPhiHalf - 1));
    var cosPhi = new Float64Array(nPhiHalf);
    for (j = 0; j < nPhiHalf; j++) { cosPhi[j] = Math.cos(Math.PI * j / (nPhiHalf - 1)); }
    var kh = new Float64Array(N), cKh = new Float64Array(N), kx = new Float64Array(N);
    for (n = 0; n < N; n++) {
      kh[n] = k * d.lengths[n] / 2; cKh[n] = Math.cos(kh[n]); kx[n] = k * d.x[n];
    }
    var Fr = new Float64Array(N), Fi = new Float64Array(N);
    // The field depends on cos(theta) only through cos(kh cos t), which is even,
    // so rows theta and pi - theta are identical: do half the sphere and mirror.
    var odd = nTheta % 2 === 1, mid = (nTheta - 1) / 2, iMax = odd ? mid : nTheta - 1;
    var total = 0;
    for (var i = 0; i <= iMax; i++) {
      var th = Math.PI * i / (nTheta - 1);
      var ct = Math.cos(th), st = Math.sin(th);
      if (st <= 1e-9) { continue; }
      for (n = 0; n < N; n++) {   // each rod's element factor is fixed along this row
        var F = (Math.cos(kh[n] * ct) - cKh[n]) / st;
        Fr[n] = sol.Imax[n].re * F; Fi[n] = sol.Imax[n].im * F;
      }
      var inner = 0;
      for (j = 0; j < nPhiHalf; j++) {
        var ux = st * cosPhi[j], Sr = 0, Si = 0;
        for (n = 0; n < N; n++) {
          var ph = kx[n] * ux, c = Math.cos(ph), s = Math.sin(ph);
          Sr += Fr[n] * c - Fi[n] * s;
          Si += Fr[n] * s + Fi[n] * c;
        }
        inner += wp[j] * (Sr * Sr + Si * Si);
      }
      var mult = odd ? (i === mid ? 1 : 2) : 1;
      total += mult * wt[i] * inner * st;
    }
    return 2 * U_SCALE * total;
  }

  // Directivity (linear) along the H-plane: theta = 90 deg, angle = phi.
  function hPlane(sol, Prad, anglesDeg) {
    return anglesDeg.map(function (a) {
      var p = a * Math.PI / 180;
      return 4 * Math.PI * U_SCALE * fieldPower(sol, 0, 1, Math.cos(p)) / Prad;
    });
  }

  // E-plane: angle 0 = along the boom, 90 = along the rods.
  function ePlane(sol, Prad, anglesDeg) {
    return anglesDeg.map(function (a) {
      var r = a * Math.PI / 180;
      var ct = Math.sin(r), st = Math.sqrt(Math.max(0, 1 - ct * ct));
      return 4 * Math.PI * U_SCALE * fieldPower(sol, ct, st, Math.cos(r)) / Prad;
    });
  }

  // Half-power beamwidth of a periodic cut (port of cut_hpbw).
  function cutHpbw(step, p) {
    var n = p.length, i0 = 0, j, s;
    for (j = 1; j < n; j++) { if (p[j] > p[i0]) { i0 = j; } }
    var half = p[i0] / 2, width = 0;
    for (var pass = 0; pass < 2; pass++) {
      s = pass === 0 ? 1 : -1;
      var found = false;
      for (j = 1; j < Math.floor(n / 2); j++) {
        var a = p[((i0 + s * (j - 1)) % n + n) % n];
        var b = p[((i0 + s * j) % n + n) % n];
        if (b < half) { width += (j - 1) + (a - half) / (a - b); found = true; break; }
      }
      if (!found) { return null; }
    }
    return width * step;
  }

  function vswr(Zin, Z0) {
    var nr = Zin.re - Z0, ni = Zin.im, dr = Zin.re + Z0, di = Zin.im;
    var d = dr * dr + di * di;
    var gr = (nr * dr + ni * di) / d, gi = (ni * dr - nr * di) / d;
    var g = Math.sqrt(gr * gr + gi * gi);
    if (g >= 1 - 1e-12) { return { gamma: g, vswr: Infinity, s11: 0 }; }
    return { gamma: g, vswr: (1 + g) / (1 - g), s11: 20 * Math.log10(Math.max(g, 1e-12)) };
  }

  // ---------------------------------------------------------------------------
  // Everything the Studio displays, in one call.
  // opts.step  : angle step (deg) for the cuts (Python uses 0.1)
  // opts.nTheta/nPhiHalf : Simpson grid for P_rad (default 181 x 181 = 1 deg)
  // ---------------------------------------------------------------------------
  function analyse(design, freqHz, opts) {
    opts = opts || {};
    var step = opts.step || 0.5;
    var sol = solve(design, freqHz);
    var Prad = radiatedPower(sol, opts.nTheta, opts.nPhiHalf);
    var ang = [];
    for (var a = 0; a < 360 - 1e-9; a += step) { ang.push(a); }
    var Dh = hPlane(sol, Prad, ang);
    var De = ePlane(sol, Prad, ang);
    var maxH = Math.max.apply(null, Dh), maxE = Math.max.apply(null, De);
    var back = Dh[Math.round(180 / step)];
    var m = vswr(sol.Zin, 50);
    var If = sol.Ibase[design.feed];
    var fmag = Math.sqrt(If.re * If.re + If.im * If.im), fph = Math.atan2(If.im, If.re);
    var currents = sol.Ibase.map(function (c) {
      return {
        mag: Math.sqrt(c.re * c.re + c.im * c.im) / fmag,
        phaseDeg: (Math.atan2(c.im, c.re) - fph) * 180 / Math.PI
      };
    });
    return {
      sol: sol, Prad: Prad, angles: ang, step: step,
      Dh: Dh, De: De,
      gainDbi: 10 * Math.log10(Math.max(maxH, maxE)),
      fbDb: 10 * Math.log10(Dh[0] / back),
      hpbwH: cutHpbw(step, Dh),
      hpbwE: cutHpbw(step, De),
      Zin: sol.Zin, vswr: m.vswr, s11Db: m.s11,
      currents: currents
    };
  }

  // Normalised 3D power pattern on a (theta, phi) grid for the 3D beam mesh.
  function pattern3d(sol, nTheta, nPhi) {
    var out = new Float64Array(nTheta * nPhi), max = 0;
    for (var i = 0; i < nTheta; i++) {
      var th = Math.PI * i / (nTheta - 1), ct = Math.cos(th), st = Math.sin(th);
      for (var j = 0; j < nPhi; j++) {
        var ph = TWO_PI * j / (nPhi - 1);
        var u = fieldPower(sol, ct, st, st * Math.cos(ph));
        out[i * nPhi + j] = u;
        if (u > max) { max = u; }
      }
    }
    for (var q = 0; q < out.length; q++) { out[q] /= (max || 1); }
    return out;
  }

  // Build a Yagi from the Studio's few, meaningful controls.
  // Default values reproduce the optimized 4-element design exactly.
  function buildDesign(p) {
    var mm = 1e-3, s = p.spacingScale;
    var lengths = [p.reflectorMm * mm, p.drivenMm * mm];
    var xs = [-p.reflectorGapMm * s * mm, 0];
    var gaps = p.directorGapsMm;   // [driven->D1, D1->D2, then repeat last]
    var x = 0;
    for (var i = 0; i < p.directors; i++) {
      var g = i < gaps.length ? gaps[i] : gaps[gaps.length - 1];
      x += g * s;
      lengths.push((p.director1Mm - p.directorTaperMm * i) * mm);
      xs.push(x * mm);
    }
    return { lengths: lengths, x: xs, radius: p.radiusMm * mm, feed: 1 };
  }

  var api = {
    C0: C0, ETA0: ETA0,
    mutualImpedance: mutualImpedance, solve: solve, radiatedPower: radiatedPower,
    hPlane: hPlane, ePlane: ePlane, cutHpbw: cutHpbw, vswr: vswr,
    analyse: analyse, pattern3d: pattern3d, buildDesign: buildDesign
  };
  if (typeof module !== "undefined" && module.exports) { module.exports = api; }
  else { root.YagiEngine = api; }
})(this);
