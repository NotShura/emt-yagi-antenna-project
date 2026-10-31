# Assembly Guide — 4-Element 2.44 GHz Yagi-Uda Antenna
## Member 3: Step-by-Step Hardware Fabrication Instructions

> **Estimated Build Time:** 1.5 – 2 hours (with all materials and pre-computed dimensions)  
> **Skill Level Required:** Beginner — no soldering required for the zero-cost option

---

## 🔧 Before You Start

### Prerequisites
1. ✅ Run `dimension_calculator.py` to get your exact cutting blueprint
2. ✅ Run `visualize_antenna.py` to generate reference diagrams
3. ✅ Obtain optimized dimensions from Member 2's 4nec2/HFSS simulation (if available)
4. ✅ Print the protractor template from `output/protractor_template.png`

### Tools Needed
| Tool | Purpose | Substitute |
|------|---------|-----------|
| Wire cutter/pliers | Cut copper wire | Strong scissors (for thin wire) |
| Ruler (mm precision) | Measure element lengths | Printed ruler template |
| Marker/pen | Mark cutting positions | — |
| Hot glue gun | Mount elements on boom | Tape / cable ties |
| Soldering iron (optional) | Attach SMA connector | Not needed for passive mount |

---

## 📋 Step-by-Step Assembly

### STEP 1: Prepare the Boom

The boom is the central structural bar that holds all antenna elements parallel to each other.

**Material:** Wooden dowel, acrylic rod, PVC pipe, or rigid cardboard tube.

> ⚠️ **CRITICAL:** The boom must be **non-conductive** (no metal). Metal booms would distort the radiation pattern.

1. Cut the boom to the required length:
   - **Minimum:** See `boom_length_mm` from `antenna_dimensions.json`
   - **Recommended:** Add 15 mm margin on each end
2. Lay the boom flat on a table
3. Using a ruler, mark the mounting positions for all 4 elements starting from one end:

```
Boom Layout (marks from left end):

Position 0 mm         : Mark "R" (Reflector)
Position [refl_spacing] mm : Mark "D" (Driven Dipole) + "FEED"
Position [D + dir1]   mm : Mark "D1" (Director 1)
Position [D + dir2]   mm : Mark "D2" (Director 2)

  R            D              D1             D2
  │            │              │              │
  ├────────────┼──────────────┼──────────────┤
  │            │              │              │
  ▼            ▼              ▼              ▼
Mark         Mark           Mark           Mark
here         here           here           here
```

> **Exact values:** Run `dimension_calculator.py` and use the "Positions from left end of boom" section.

---

### STEP 2: Cut the Wire Elements

Using the cutting blueprint from `dimension_calculator.py`:

| Element | Cut Length | Notes |
|---------|-----------|-------|
| Reflector | See blueprint | Longest element |
| Driven Dipole | See blueprint | Cut into TWO equal halves (each arm) |
| Director 1 | See blueprint | Shorter than driven dipole |
| Director 2 | See blueprint | Shortest element |

**Procedure:**
1. Straighten the copper wire by rolling it on a flat surface with a flat object
2. Measure from one end using a ruler with mm precision
3. Mark the cut point with a marker
4. Cut cleanly with wire cutters (avoid crushing the wire)
5. File any sharp burrs with sandpaper or nail file
6. **Label each piece** immediately (use tape labels: R, D-left, D-right, D1, D2)

> 💡 **Tip:** Cut each wire ~1-2 mm longer than required. You can always trim, but you can't add.

---

### STEP 3: Mount Elements on the Boom

**Orientation:** All elements must be:
- **Perpendicular** to the boom (90° angle)
- **Parallel** to each other
- **Centered** on the boom (equal length extending on both sides)

**Mounting Method (choose one):**

#### Option A: Hot Glue (Recommended)
1. Apply a small bead of hot glue to the marked position on the boom
2. Press the center of the wire element onto the glue
3. Hold for 10 seconds until set
4. Verify alignment with a square or by eye against a grid
5. Repeat for all elements

#### Option B: Cable Ties
1. Drill or poke a small hole through the boom at each mark
2. Thread a cable tie through the hole
3. Place the wire element center on the mark
4. Tighten the cable tie around the wire and boom
5. Trim excess cable tie

#### Option C: Tape (Temporary/Quick)
1. Place wire at the marked position
2. Wrap electrical tape or masking tape around both wire and boom
3. Check alignment and adjust before finalizing

> ⚠️ **IMPORTANT for the Driven Dipole:** Do NOT mount it as a single wire. Mount the two arms separately with a **2-3 mm gap** at the center. This gap is the **feedpoint** where the coaxial cable connects.

```
Driven Dipole (top view):

    ←── Left Arm ──→  gap  ←── Right Arm ──→
    ════════════════  │  │  ════════════════
                      │  │
                      FEED
                      POINT
                   (2-3 mm gap)
```

---

### STEP 4: Build the Feedline & Balun

You have two options here:

#### Option A: SMA Coaxial Feed with Pawsey Stub Balun (Best Performance)

**What is a balun?** A dipole is a "balanced" antenna (both arms are symmetric), but a coaxial cable is "unbalanced" (the shield is grounded). Without a balun, current flows on the outside of the coax shield, distorting the pattern. The Pawsey stub balun fixes this.

**Construction:**
1. Take your RG174/RG316 coaxial cable with SMA connector
2. Strip ~5 mm of the outer jacket at the far end (antenna end)
3. Separate the center conductor and shield braid
4. Solder/attach the **center conductor** to one dipole arm
5. Solder/attach the **shield braid** to the other dipole arm
6. **For the balun:** Take a second piece of coax, length = λ/4 × velocity_factor:
   - RG174: See `balun_length_rg174_mm` from the calculator
   - RG316: See `balun_length_rg316_mm` from the calculator
7. Short-circuit one end of this stub (connect center to shield)
8. Connect the other end to the feedpoint in parallel with the feed coax
9. Tape/tie the stub back along the main feedline

```
Balun Diagram (side view):

         ←── Dipole Arm ──  ── Dipole Arm ──→
                           │
                      Center ─── Shield
                           │
              ┌────────────┤  Main feedline
              │            │  (to radio/SMA)
              │            │
    Stub ─────┘            │
    (λ/4 coax,             │
     shorted               │
     at bottom)            ▼
                        To ESP32 / radio
```

#### Option B: Passive Wave-Launcher Mount (Zero-Cost, No Soldering)

If you're using smartphones or don't want to solder:

1. Mount the driven dipole centered on the boom with the 2-3 mm gap
2. Place the smartphone (transmitter or receiver) directly at the feedpoint
3. The phone's internal antenna couples electromagnetically to the dipole
4. The parasitic reflector and directors still focus the signal

> This approach gives ~3-5 dB less gain than a proper coax feed but requires **zero additional components**.

---

### STEP 5: Build the FR4 Reflector Screen (Optional)

A copper-clad FR4 sheet behind the reflector element enhances the front-to-back ratio.

1. Cut the FR4 sheet to approximately λ × λ (≈ 123 mm × 123 mm)
2. Mount it **behind** the reflector element (on the opposite side from the directors)
3. It should be parallel to the reflector element and perpendicular to the boom
4. Spacing from reflector: ~5-10 mm

> **Budget alternative:** Aluminum foil glued to stiff cardboard works almost as well.

---

### STEP 6: Build the 360° Turntable Rig

This is the measurement platform that allows Member 4 to rotate the antenna in precise 10° increments.

**Materials:**
- Printed protractor template (from `output/protractor_template.png`)
- Stiff cardboard or plywood base (≥ 30 cm × 30 cm)
- A pivot point (nail, bolt, or pencil)

**Construction:**
1. Print the protractor template at 100% scale
2. Glue/tape the protractor onto the cardboard base
3. Poke a hole at the center of the protractor
4. Insert a nail/bolt as the pivot
5. Create a rotating arm that holds the antenna boom:
   - Attach the boom to a small platform (cardboard square)
   - Attach the platform to the pivot so it can freely rotate
6. Add a pointer/arrow on the rotating platform aligned with the boom axis
7. Mark "0°" on the base as the reference direction

```
Turntable (top view):

              0° (reference)
              │
     330° ────┼──── 30°
    /         │         \
  300°       ┌┼┐       60°
  │          │·│          │     · = pivot
  270° ──────┤·├────── 90°
  │          │·│          │
  240°       └┼┘       120°
    \         │         /
     210° ────┼──── 150°
              │
             180°

   Antenna boom sits on rotating platform above the protractor.
   Pointer indicates current bearing.
```

---

### STEP 7: Pre-Test Verification Checklist

Before handing off to Member 4 for measurements:

- [ ] All 4 elements are parallel to each other
- [ ] All elements are perpendicular to the boom (90°)
- [ ] Elements are centered on the boom (equal extension on each side)
- [ ] Element spacings match the blueprint (±1 mm tolerance)
- [ ] Element lengths match the blueprint (±1 mm tolerance)
- [ ] Driven dipole has a visible gap at the feedpoint
- [ ] Feedline/balun is attached (or passive mount is ready)
- [ ] Turntable rotates freely with clear degree markings
- [ ] Turntable pointer accurately indicates angle
- [ ] Boom is stable and doesn't wobble during rotation
- [ ] Antenna is mounted at a height that clears the turntable edges

---

## 📸 PPT Slide Content Suggestions

### Slide 10: Components List
- Photo of all cut wire elements laid out with labels
- Photo of boom material
- Photo of SMA connector / coax cable (if used)
- Photo of FR4 sheet or aluminum foil reflector
- Bill of Materials table with costs

### Slide 11: Assembly Steps
- Step-by-step photos of the build process
- Close-up of feedpoint gap
- Close-up of element mounting on boom
- Photo of balun construction (or passive mount)

### Slide 12: Physical Prototype Showcase
- Complete antenna on turntable rig
- Side-by-side comparison with the 3D visualization from `visualize_antenna.py`
- Photo with ruler showing dimensions match blueprint
- Photo of the turntable with visible degree markings

---

## ⚠️ Common Mistakes to Avoid

1. **Metal boom:** Using a metal rod as the boom will short-circuit the elements and destroy the radiation pattern. Use wood, plastic, or cardboard only.
2. **Crooked elements:** If elements aren't parallel, the pattern distorts. Use a right-angle guide.
3. **Wrong gap at feedpoint:** The driven dipole MUST have a gap at center. A continuous wire won't work as a dipole.
4. **Elements too loose:** Vibration or sagging changes element positions. Secure firmly.
5. **Nearby metal objects:** During measurement, keep metal objects (tables, chairs, laptops) at least 1 meter away.
6. **Indoor reflections:** Walls, floor, and ceiling cause multipath reflections. Measure outdoors if possible, or in the largest open room available.

---

> **Next:** After building the prototype, hand it off to **Member 4** for the 360° RSSI measurement sweep. Member 4 will generate the empirical CSV that Member 1's GUI will overlay against the theoretical and simulated patterns.
