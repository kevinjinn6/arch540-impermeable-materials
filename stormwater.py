"""
================================================================================
 VANCOUVER R1-1 STORMWATER GAP ANALYSIS  --  Stage 1
================================================================================

WHAT THIS SCRIPT DOES
  1. Downloads two datasets from the City of Vancouver open data portal
     (and caches them, so re-running is fast and doesn't re-hit the API).
  2. Finds every parcel that sits inside an R1-1 zoning district.
  3. Reprojects everything to UTM Zone 10N so that areas are in real metres.
  4. For each parcel, works out how much of it may be paved under two
     development scenarios, how much rain runs off as a result, and how far
     that is from what the Rain City Strategy would want.
  5. Writes one GeoJSON file, and prints a summary.

HOW TO RUN IT
     source .venv/bin/activate
     python stormwater.py

  First run downloads ~54 MB and takes a couple of minutes.
  Later runs read from the cache/ folder and take well under a minute.

TO CHANGE THE NUMBERS
  Everything you would want to adjust is in the CONFIGURATION block below.
  You should not need to touch anything after the line that says
  "END OF CONFIGURATION". Every constant has a plain-language comment.

--------------------------------------------------------------------------------
 IMPORTANT CAVEATS -- please read before quoting any number this produces
--------------------------------------------------------------------------------

 1. THE 48 mm STANDARD IS ASPIRATIONAL FOR R1-1, NOT A LEGAL REQUIREMENT.
    All R1-1 housing forms sit within 1.0 FSR, which routes them onto the
    City's "small site" pathway: a detention tank sized from a lookup table
    (roughly 3,400-7,200 L, equivalent to only ~6-8 mm spread over the site),
    with no 48 mm requirement and no impervious-area calculation at all.
    The older "retain 24 mm / treat 48 mm" rule was removed from the Zoning
    and Development By-law effective 1 January 2024.
    So the "gap" this tool reports is the distance between what R1-1 actually
    demands and what Rain City aspires to. That is a meaningful policy
    finding, but it is NOT a finding that anyone is breaking a rule.

 2. THE CITY'S OWN EQUATION HAS NO RUNOFF COEFFICIENT.
    Vancouver's Green Infrastructure Sizing and Modelling Guide states the
    standard as:  Design Storm Volume = 48 mm x Impervious Contributing Area.
    This script applies RUNOFF_COEFF anyway, consistently on both sides of
    the comparison, because that was the specified design. Set RUNOFF_COEFF
    to 1.0 to reproduce the City's bare equation.
    Note also that the City's published coefficients (0.95 roofs/pavement,
    0.70 one-and-two-family, 0.85 multiplex) are Rational Method PEAK FLOW
    coefficients. Using them in a VOLUME equation is a known approximation.

 3. "IMPERMEABLE MATERIALS" IS DEFINED MORE BROADLY THAN YOU MIGHT EXPECT.
    Section 2 of the by-law counts permeable pavers and wood decking as
    impermeable. This matters for a landscape designer: a permeable paver
    driveway does not help you under s.3.2.2.8.

 4. SCENARIO B IS A GEOMETRIC ESTIMATE, NOT A BY-LAW FIGURE.
    Section 3.1 (multiplex) sets no impermeability limit and no site coverage
    limit at all. The envelope computed here is derived from setbacks and
    building-size caps. Fields carrying this estimate are suffixed "_est".

 5. THINGS THIS SCRIPT CANNOT SEE, WHICH WOULD CHANGE SCENARIO B:
      - Multiplex requires rear vehicular access (s.2.2.7). Lane-less parcels
        cannot host one. The parcel data has no lane attribute, so every
        parcel is treated as eligible. This OVERSTATES Scenario B.
      - The rear setback has two values (s.3.1.2.8): 10.7 m normally, but
        0.9 m for a courtyard configuration. Only the 10.7 m case is modelled.
        See SETBACK_REAR_M below. This UNDERSTATES Scenario B on deep lots.
      - A zoning "site" is not the same thing as a parcel. It may combine
        several adjoining parcels, and it excludes strata lots.
      - Corner-lot frontage is the shortest street boundary, or the Director's
        decision (s.10.26.1). It is not inferable from geometry alone.

 BY-LAW SECTIONS REFERENCED (R1-1 District Schedule, June 2026 consolidation):
      s.3.1        Multiplex. No impermeability or site coverage regulation.
      s.3.1.2.8    Rear yard: 0.9 m courtyard configuration, else 10.7 m.
      s.3.1.2.9    Maximum building depth 19.8 m.
      s.3.1.2.10   Maximum building width 17.4 m.
      s.3.2        "Other Uses" -- a residual catch-all section, which is
                   where the single-detached / duplex limits actually live.
      s.3.2.2.7    Maximum building site coverage 50% of site area.
      s.3.2.2.8    Maximum area of impermeable materials 75% of site area.

================================================================================
"""

import hashlib
import json
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import Polygon

# ==============================================================================
#  CONFIGURATION  --  change these numbers, not the code below
# ==============================================================================

# ---- RAINFALL AND HYDROLOGY --------------------------------------------------

DESIGN_RAINFALL_MM = 48.0
# The Rain City Strategy daily design standard, in millimetres.
# This is the depth of rain, in a 24-hour period, that a site is expected to
# manage on site rather than send to the sewer.

RUNOFF_COEFF = 0.9
# What fraction of rain landing on a hard surface actually runs off, rather
# than evaporating or soaking into cracks. 0.9 means 90% runs off.
# Applied consistently to BOTH the runoff volume AND the compliance threshold.
# Set to 1.0 to reproduce the City's own equation, which uses no coefficient.

D_EFF_MM = 30.0
# "Effective retention depth": how many millimetres of rain the PERMEABLE part
# of the lot can soak up and hold before it starts shedding water too.
#    30  = plain turf sitting on compacted glacial till (a poor sponge)
#   285  = rain garden, 150 mm of surface ponding + 450 mm of soil at 30%
#          porosity  (150 + 450x0.30 = 285)
#
# CAUTION ON BOTH NUMBERS:
#   30 mm is only defensible if the till is Hydrologic Soil Group D. On HSG C
#   soils the City's own table suggests 163-312 mm, and every result for turf
#   flips from "impossible" to "comfortable". This single number drives the
#   headline finding, so it is worth being sure of.
#   285 mm omits the drain rock layer the City's Equation 4 includes; a full
#   rain garden section is nearer 405-465 mm.

# ---- WHAT COUNTS AS PAVED ----------------------------------------------------

SEC_3_2_FOOTPRINT_RATIO = 0.50   # s.3.2.2.7 -- max building site coverage
SEC_3_2_IMPERMEABLE_RATIO = 0.75  # s.3.2.2.8 -- max impermeable materials

HARDSCAPE_RATIO = SEC_3_2_IMPERMEABLE_RATIO - SEC_3_2_FOOTPRINT_RATIO
# Driveway, walkways, patio -- everything hard that is not the building itself,
# as a fraction of the lot. This works out to 0.25, and it is not invented:
# it is exactly what section 3.2's own two numbers imply (75% total impermeable
# minus 50% building coverage). Using the same figure for the multiplex
# scenario is what makes the two scenarios comparable -- both are then
# "building + the same hardscape habit".
#
# It is DERIVED from the two constants above rather than typed as 0.25, so
# that if you change either of them this follows automatically instead of
# quietly disagreeing with them. To use a different hardscape allowance,
# replace this line with a plain number, e.g.  HARDSCAPE_RATIO = 0.30

# ---- MULTIPLEX BUILDING ENVELOPE (s.3.1) -------------------------------------
# Used to estimate how big a multiplex could physically be. All in metres.

SETBACK_FRONT_M = 4.9    # s.3.1.2.6 -- distance from the front property line
SETBACK_SIDE_M = 1.2     # s.3.1.2.7 -- each side, so 2.4 m comes off the width
SETBACK_REAR_M = 10.7    # s.3.1.2.8 -- the NON-courtyard value.
                         # Set this to 0.9 to model a courtyard configuration
                         # instead; that is the other value the by-law allows.
MAX_BUILDING_DEPTH_M = 19.8   # s.3.1.2.9
MAX_BUILDING_WIDTH_M = 17.4   # s.3.1.2.10

# ---- PARCEL SELECTION AND QUALITY FLAGS --------------------------------------

ZONING_DISTRICT = "R1-1"
# The zoning district to analyse. The portal spells it exactly like this.

JOIN_PREDICATE = "inside_point"
# How a parcel is decided to be "in" R1-1. Options:
#   "inside_point" -- a point guaranteed to lie inside the parcel falls inside
#                     an R1-1 polygon (63,946 parcels). This is the
#                     conventional choice and gives each parcel exactly one
#                     zone.
#   "intersects"   -- any overlap at all counts (64,768, i.e. +822 parcels that
#                     straddle a district boundary and are partly in other
#                     zones).
#
# A note on the name: this is often called a "centroid" join, but the code
# uses representative_point(), not the true centroid. For an L-shaped or
# crescent-shaped lot the true centroid can fall OUTSIDE the lot entirely,
# which would drop the parcel or assign it to a neighbouring zone.
# representative_point() is guaranteed to land inside. The option is named
# for what the code actually does.

OUTSIZED_LOT_THRESHOLD_M2 = 2000.0
# Parcels bigger than this are FLAGGED, not deleted. They are kept in the
# GeoJSON with is_outsized = true, and the summary reports totals both with
# and without them.
# Why this matters: Stanley Park is zoned R1-1. So are Queen Elizabeth Park and
# Fraserview Golf Course. The 750 parcels above 2,000 m2 are 35% of all R1-1
# land, and none of them will ever be a multiplex. Left in, they dominate the
# citywide total.

# ---- MINIMUM SITE SIZE, PER SCENARIO -----------------------------------------
# These are NOT the same for the two scenarios, and that asymmetry is real --
# the by-law sets different floors for a multiplex than for a house.

# Scenario B, multiplex (s.3.1). ALL THREE must be met. Fall below any one of
# them and section 3.1 is simply unavailable, at any unit count -- so the
# Scenario B fields are set to null rather than given a misleading number.
MIN_SITE_AREA_B_M2 = 306.0    # s.3.1.2.3(a) -- lowest tier, 3-4 units
MIN_FRONTAGE_B_M = 10.0       # s.3.1.2.3(b)
MIN_SITE_DEPTH_B_M = 30.4     # s.3.1.2.4(b)

# Scenario A, single detached / duplex (s.3.2). LOWER frontage floor.
MIN_SITE_AREA_A_M2 = 306.0    # s.3.2.2.1
MIN_FRONTAGE_A_M = 7.3        # s.3.2.2.2  -- note 7.3, NOT 10.0
# s.3.2.2.12 expressly permits building on lots narrower than 7.3 m that were
# on record as of 24 June 2014. Vancouver has many. So parcels below the
# Scenario A floors are FLAGGED and KEPT, never nulled -- excluding them would
# discard lots that can lawfully be built on.

# ---- DATA QUALITY (not a zoning rule) ----------------------------------------

MAX_ASPECT_RATIO = 10.0
# Longest side divided by shortest. Above this a "parcel" is a sliver: a lane,
# a right-of-way, a strip of road allowance. The worst offender in the R1-1 set
# is 6.1 m wide and 311.8 m long -- a perfect rectangle, so the rectangularity
# check waves it through, but it is not a lot anyone could build on.
# A parcel also fails this test if it has no site_id at all.
# This is a DATA-QUALITY judgement, deliberately kept separate from the zoning
# minimums above, so the two reasons never get confused in the output.

RECTANGULARITY_FLAG = 0.95
# A lot scores 1.0 if it is a perfect rectangle, less if it is irregular.
# Below this threshold the setback envelope (which assumes a rectangle) is
# unreliable, and the parcel is flagged is_irregular.

# ---- DATA SOURCE -------------------------------------------------------------

PORTAL = "https://opendata.vancouver.ca/api/explore/v2.1/catalog/datasets"
# Verified working endpoint. NO API KEY IS NEEDED.
# The anonymous quota is 15,000 requests per day and this script uses 2.
# (Sending an invalid key returns 401, so we deliberately send no auth header.)
# The /exports/ endpoint has no record cap. The /records/ endpoint is capped at
# 10,000 rows and could never retrieve the 99,701-parcel dataset.

PARCEL_DATASET = "property-parcel-polygons"
ZONING_DATASET = "zoning-districts-and-labels"

# Both paths are anchored to the folder this script lives in, NOT to whatever
# folder your terminal happens to be in. So the script works the same whether
# you run it from here or from somewhere else.
HERE = Path(__file__).resolve().parent
CACHE_DIR = HERE / "cache"    # downloaded files land here, reused on re-run
OUTPUT_FILE = HERE / "r11_stormwater.geojson"
SUMMARY_CSV = HERE / "r11_stormwater_summary.csv"
# The same numbers as the GeoJSON but with the map shapes stripped out, so it
# opens straight in Excel. One row per parcel.

TOP_N_PARCELS = 5
# How many of the worst parcels to list by address at the end of the run.

WGS84 = 4326    # what the portal gives us: degrees of latitude / longitude
UTM10N = 26910  # what we need: metres. Areas MUST be computed in this CRS.

TRACE_PARCEL_INDEX = 0
# Print every intermediate value for one parcel, as a worked example.
# 0 = the first parcel in the output. Change to inspect a different one.

# ==============================================================================
#  END OF CONFIGURATION
# ==============================================================================


# ------------------------------------------------------------------------------
#  STEP 1 -- Get the data, using a local cache so we only download once
# ------------------------------------------------------------------------------

def fetch(dataset, where=None, select=None):
    """Download a dataset as GeoJSON, or reuse the cached copy if we have one.

    `where` filters rows on the server, so we only transfer what we need.
    """
    CACHE_DIR.mkdir(exist_ok=True)

    # The cache filename has to depend on the FILTER, not just the dataset.
    # Otherwise changing ZONING_DISTRICT from "R1-1" to something else would
    # silently hand you back the old R1-1 file under the new name -- which
    # would look like it worked and be completely wrong.
    # The 8-character tag is just a fingerprint of the query.
    tag = ""
    if where or select:
        fingerprint = f"{where}|{select}"
        tag = "-" + hashlib.md5(fingerprint.encode()).hexdigest()[:8]
    cache_file = CACHE_DIR / f"{dataset}{tag}.geojson"

    if cache_file.exists() and cache_file.stat().st_size > 0:
        print(f"  using cached {cache_file.name}  "
              f"({cache_file.stat().st_size / 1e6:.1f} MB)")
        return gpd.read_file(cache_file)

    params = {}
    if where:
        params["where"] = where
    if select:
        params["select"] = select

    url = f"{PORTAL}/{dataset}/exports/geojson"
    print(f"  downloading {dataset} ...")
    # Note: no Authorization header. This portal 401s on an invalid key,
    # and anonymous access is allowed at this volume.
    response = requests.get(url, params=params, timeout=600)
    response.raise_for_status()

    # Check the download is actually usable BEFORE it becomes the cache.
    # A half-finished download, or a valid-but-empty response from a typo in
    # a filter, would otherwise be saved and then silently reused forever --
    # and an empty result would overwrite your good output file with nothing.
    try:
        payload = json.loads(response.content)
    except json.JSONDecodeError:
        raise SystemExit(
            f"  The download of {dataset} was not valid JSON "
            f"({len(response.content) / 1e6:.1f} MB received). It was probably\n"
            f"  cut short. Nothing has been cached -- just run the script again."
        )

    n = len(payload.get("features", []))
    if n == 0:
        raise SystemExit(
            f"  {dataset} came back with ZERO features.\n"
            f"  The filter was: {where!r}\n"
            f"  That usually means a typo in ZONING_DISTRICT. Nothing has been\n"
            f"  cached and your previous output file is untouched."
        )

    # Write to a temporary name first, then rename. A rename is atomic, so
    # the cache file either doesn't exist or is complete -- never half-written.
    temp_file = cache_file.with_suffix(".geojson.part")
    temp_file.write_bytes(response.content)
    temp_file.replace(cache_file)
    print(f"  saved {cache_file.name}  "
          f"({len(response.content) / 1e6:.1f} MB, {n:,} features)")
    return gpd.read_file(cache_file)


# ------------------------------------------------------------------------------
#  STEP 2 -- Measure each lot's width and depth
# ------------------------------------------------------------------------------

def lot_dimensions(geom):
    """Return (width_m, depth_m, rectangularity) for one parcel.

    Real parcels are not axis-aligned rectangles, so we fit the tightest
    possible rotated rectangle around each one and measure that.
      - depth  = the LONGER side (Vancouver lots are deep and narrow)
      - width  = the SHORTER side, i.e. the street frontage
      - rectangularity = how much of that rectangle the real lot actually
        fills. 1.0 is a perfect rectangle; 0.6 is an odd wedge-shaped lot.

    We deliberately do NOT try to work out which end is the front. It does not
    matter: front and rear setbacks both come off the same (depth) axis, so
    their sum is all we need, and the by-law says corner-lot frontage is the
    Director's call anyway -- it is not inferable from geometry.
    """
    try:
        mrr = geom.minimum_rotated_rectangle
    except Exception:
        return (0.0, 0.0, 0.0)

    if not isinstance(mrr, Polygon) or mrr.is_empty or mrr.area <= 0:
        return (0.0, 0.0, 0.0)

    pts = list(mrr.exterior.coords)[:5]
    if len(pts) < 4:
        return (0.0, 0.0, 0.0)

    def seglen(a, b):
        return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5

    side_a = seglen(pts[0], pts[1])
    side_b = seglen(pts[1], pts[2])

    width = min(side_a, side_b)
    depth = max(side_a, side_b)
    rectangularity = geom.area / mrr.area if mrr.area > 0 else 0.0
    return (width, depth, rectangularity)


def multiplex_envelope_m2(width_m, depth_m):
    """Biggest multiplex footprint that fits, in square metres.

    Two things constrain it, and we apply BOTH, axis by axis:
      1. the setbacks eat into the lot from every edge
      2. s.3.1.2.9 / s.3.1.2.10 cap the building at 19.8 m x 17.4 m regardless

    On a standard Vancouver lot (about 10 m x 37 m) the DEPTH CAP is what
    binds, not the rear setback:  37.2 - 4.9 - 10.7 = 21.6 m available, but
    the by-law caps the building at 19.8 m. So we get 19.8, not 21.6.
    """
    buildable_width = width_m - (2 * SETBACK_SIDE_M)
    buildable_depth = depth_m - SETBACK_FRONT_M - SETBACK_REAR_M

    # Clamp each axis independently against its cap, then multiply.
    final_width = min(buildable_width, MAX_BUILDING_WIDTH_M)
    final_depth = min(buildable_depth, MAX_BUILDING_DEPTH_M)

    # A lot too narrow or too shallow to fit anything gets zero, not a
    # negative number.
    return max(final_width, 0.0) * max(final_depth, 0.0)


# ------------------------------------------------------------------------------
#  STEP 3 -- The hydrology
# ------------------------------------------------------------------------------
#
#  The water balance we are solving, on one lot:
#
#      Perm * D_eff   >=   I * P * C   +   Perm * P
#      -------------       ---------       --------
#      what the            runoff from     rain landing
#      permeable part      the paved       directly on the
#      can hold            part            permeable part
#
#  where  A = lot area, I = impermeable area, Perm = A - I,
#         P = design rainfall, C = runoff coefficient, D_eff = retention depth.
#
#  Rearranged to find the smallest permeable area that still balances:
#
#      Perm_min = A * P * C / (D_eff - P + P*C)
#      I_max    = A - Perm_min
#
#  Sanity check built into this file: at C = 1.0 this must collapse to the
#  simpler A * (1 - P/D_eff). Run with --selftest to verify.
#
#  FEASIBILITY: if D_eff <= P, the permeable surface cannot even absorb the
#  rain falling directly on itself, so NO amount of paving is acceptable --
#  not even zero. At the default D_eff = 30 and P = 48, that is the case.
#  We report this as infeasible rather than emitting a negative area.
#  (Note the denominator is still POSITIVE at D_eff = 30: 30 - 48 + 43.2 =
#  25.2. So checking the denominator's sign is not enough; we test D_eff > P
#  explicitly.)
# ------------------------------------------------------------------------------

def is_feasible(d_eff_mm=None, rainfall_mm=None):
    """Can ANY amount of paving comply, on a lot with this soil?

    The real question is whether the permeable area the storm demands will
    even fit on the lot:  Perm_min <= A.  That reduces cleanly:

        A*P*C / (D - P + P*C)  <=  A
             P*C               <=  D - P + P*C
               0               <=  D - P
               D               >=  P

    So the gate is D_eff >= P, with equality INCLUDED. At D_eff exactly equal
    to P the formula returns Perm_min = A and I_max = 0 -- finite, defined,
    and a genuine answer: you may pave nothing, and paving nothing complies.

    The actual singularity is elsewhere. The denominator vanishes at
    D_eff = P*(1 - C), which is 4.8 mm at the shipped settings -- far below
    the gate, so it is never reached in practice. Guarded anyway.
    """
    d_eff = D_EFF_MM if d_eff_mm is None else d_eff_mm
    rain = DESIGN_RAINFALL_MM if rainfall_mm is None else rainfall_mm
    return d_eff >= rain


def singularity_mm(rainfall_mm=None, coeff=None):
    """D_eff at which the denominator hits zero: P*(1 - C)."""
    rain = DESIGN_RAINFALL_MM if rainfall_mm is None else rainfall_mm
    c = RUNOFF_COEFF if coeff is None else coeff
    return rain * (1.0 - c)


def min_permeable_m2(lot_area_m2, d_eff_mm=None, rainfall_mm=None, coeff=None):
    """Smallest permeable area that can still absorb the design storm.

    Returns None when the soil cannot manage the storm at all.
    """
    d_eff = D_EFF_MM if d_eff_mm is None else d_eff_mm
    rain = DESIGN_RAINFALL_MM if rainfall_mm is None else rainfall_mm
    c = RUNOFF_COEFF if coeff is None else coeff

    if not is_feasible(d_eff, rain):
        return None

    denominator = d_eff - rain + (rain * c)
    if denominator <= 0:
        # Only reachable at the singularity itself (D = P*(1-C)), or with
        # C = 0 and D = P, where the numerator is zero too. A zero numerator
        # means no runoff to absorb, so no permeable area is required.
        if rain * c == 0:
            return 0.0
        return None
    return lot_area_m2 * rain * c / denominator


def compliant_impermeable_m2(lot_area_m2, **kw):
    """The most you may pave and still manage the design storm on site."""
    perm = min_permeable_m2(lot_area_m2, **kw)
    if perm is None:
        return None
    return max(lot_area_m2 - perm, 0.0)


def d_eff_required_mm(impermeable_fraction, rainfall_mm=None, coeff=None):
    """THE HEADLINE OUTPUT.

    Turn the question around: given that the by-law lets you pave this
    fraction of the lot, how absorbent would the remaining garden have to be
    for that to actually work?

        D_required = P * (1 + C * i / (1 - i))

    At the s.3.2.2.8 ceiling of 75%, with P=48 and C=0.9, this comes to
    177.6 mm. That is the retention depth the by-law implicitly demands.
    Plain turf on till offers about 30 mm. That shortfall is the finding.
    """
    rain = DESIGN_RAINFALL_MM if rainfall_mm is None else rainfall_mm
    c = RUNOFF_COEFF if coeff is None else coeff
    if impermeable_fraction >= 1.0:
        return float("inf")
    return rain * (1.0 + c * impermeable_fraction / (1.0 - impermeable_fraction))


def runoff_volume_m3(impermeable_area_m2, rainfall_mm=None, coeff=None):
    """Cubic metres of water shed by a paved area in the design storm.

    This is the ONE place millimetres become metres. Everything else in this
    file stays in mm, so there is a single conversion to get wrong.
    """
    rain = DESIGN_RAINFALL_MM if rainfall_mm is None else rainfall_mm
    c = RUNOFF_COEFF if coeff is None else coeff
    return impermeable_area_m2 * (rain / 1000.0) * c


# ------------------------------------------------------------------------------
#  Self-test -- proves the algebra before trusting any output
# ------------------------------------------------------------------------------

def selftest():
    print("SELF-TEST")
    ok = True

    # 1. At C = 1.0 the general formula must reduce to A*(1 - P/D_eff).
    #    The test depths scale with DESIGN_RAINFALL_MM so that this test still
    #    means something if you change the design storm. (They must all stay
    #    above it, or there is nothing to compare against -- see feasibility.)
    print("\n  1. At C=1.0, does I_max reduce to A*(1 - P/D_eff)?")
    for mult in (2.0, 3.0, 6.0, 9.0):
        d = DESIGN_RAINFALL_MM * mult
        got = compliant_impermeable_m2(374.0, d_eff_mm=d, coeff=1.0)
        want = 374.0 * (1.0 - DESIGN_RAINFALL_MM / d)
        if got is None:
            match = False
            print(f"       D_eff={d:>6.1f}  got None (infeasible) "
                  f"  want {want:>9.4f}   FAIL")
        else:
            match = abs(got - want) < 1e-9
            print(f"       D_eff={d:>6.1f}  got {got:>9.4f}   "
                  f"want {want:>9.4f}   {'OK' if match else 'FAIL'}")
        ok &= match

    # 2. d_eff_required must round-trip: feed it back, get the ceiling out.
    print(f"\n  2. Does d_eff_required({SEC_3_2_IMPERMEABLE_RATIO:g}) "
          f"round-trip back to {SEC_3_2_IMPERMEABLE_RATIO:.0%}?")
    d_req = d_eff_required_mm(SEC_3_2_IMPERMEABLE_RATIO)
    rt = compliant_impermeable_m2(374.0, d_eff_mm=d_req)
    if rt is None:
        match = False
        print(f"       d_eff_required = {d_req:.4f} mm, but round-trip is "
              f"infeasible   FAIL")
    else:
        back = rt / 374.0
        match = abs(back - SEC_3_2_IMPERMEABLE_RATIO) < 1e-9
        print(f"       d_eff_required({SEC_3_2_IMPERMEABLE_RATIO:g}) "
              f"= {d_req:.4f} mm")
        print(f"       feeding that back gives i = {back:.9f}   "
              f"{'OK' if match else 'FAIL'}")
    ok &= match

    # 3. Feasibility must track D_eff > P, and NOT the denominator's sign.
    #    Tested with EXPLICIT values, not the config globals. Asking
    #    is_feasible() to agree with (D_EFF_MM > DESIGN_RAINFALL_MM) would just
    #    restate the function's own body back at itself -- a test that can
    #    never fail, and therefore tests nothing.
    print(f"\n  3. Does the feasibility gate track D_eff >= P?")
    cases = [
        (30.0, 48.0, False, "turf on till: cannot absorb its own rain"),
        (47.9, 48.0, False, "just under: still infeasible"),
        (48.0, 48.0, True, "EQUAL: complies, but only at zero coverage"),
        (49.0, 48.0, True, "barely over: feasible"),
        (285.0, 48.0, True, "rain garden: comfortably absorbs the storm"),
    ]
    for d, p_mm, want, why in cases:
        got = is_feasible(d, p_mm)
        hit = got == want
        ok &= hit
        print(f"       D_eff={d:>6.1f} P={p_mm:>5.1f} -> {str(got):<5} "
              f"(want {str(want):<5}) {'OK  ' if hit else 'FAIL'} {why}")

    # 3b. The gate must agree with the condition it actually stands for:
    #     Perm_min <= A. Checked numerically, not by restating the formula.
    print(f"\n  3b. Does the gate agree with Perm_min <= A?")
    agree = True
    for d in (20.0, 40.0, 47.0, 48.0, 60.0, 300.0):
        denom = d - 48.0 + 48.0 * 0.9
        perm = 400.0 * 48.0 * 0.9 / denom if denom > 0 else float("inf")
        expect = perm <= 400.0
        got = is_feasible(d, 48.0)
        agree &= (got == expect)
    ok &= agree
    print(f"       agreement across D_eff 20..300 mm: "
          f"{'OK' if agree else 'FAIL'}")

    # 3c. At D_eff == P exactly, I_max must be exactly zero -- the distinct
    #     third state, neither infeasible nor a normal positive allowance.
    print(f"\n  3c. At D_eff == P exactly, is I_max exactly 0?")
    edge = compliant_impermeable_m2(400.0, d_eff_mm=48.0, rainfall_mm=48.0)
    hit = edge is not None and abs(edge) < 1e-9
    ok &= hit
    print(f"       I_max = {edge}   {'OK' if hit else 'FAIL'}")
    print(f"       singularity is at P*(1-C) = "
          f"{singularity_mm():.1f} mm, far below the gate.")

    # 4. Envelope: each axis must be clamped against its own cap.
    #    On a standard Vancouver lot the DEPTH cap should bind, not the
    #    setbacks. Compared against the constants, not against literals, so
    #    this keeps testing the real behaviour if you edit the setbacks.
    std_w, std_d = 10.06, 37.19
    setback_depth = std_d - SETBACK_FRONT_M - SETBACK_REAR_M
    want_depth = min(setback_depth, MAX_BUILDING_DEPTH_M)
    want_width = min(std_w - 2 * SETBACK_SIDE_M, MAX_BUILDING_WIDTH_M)
    print(f"\n  4. On a standard {std_w} x {std_d} m lot, is each axis clamped")
    print(f"     against its own cap?")
    env = multiplex_envelope_m2(std_w, std_d)
    match = abs(env - max(want_width, 0) * max(want_depth, 0)) < 1e-9
    ok &= match
    print(f"       setbacks allow depth {setback_depth:.2f} m, "
          f"cap is {MAX_BUILDING_DEPTH_M:g} m -> use {want_depth:.2f} m")
    print(f"       envelope {env:.2f} m2  "
          f"(= {want_width:.2f} x {want_depth:.2f})   "
          f"{'OK' if match else 'FAIL'}")
    if abs(want_depth - MAX_BUILDING_DEPTH_M) < 1e-9:
        print(f"       ^ the depth CAP binds here, not the rear setback.")

    print(f"\n  {'ALL SELF-TESTS PASSED' if ok else 'SELF-TESTS FAILED'}")
    return ok


# ------------------------------------------------------------------------------
#  STEP 4 -- Per-parcel calculation
# ------------------------------------------------------------------------------

def non_parcel_reason(site_id, width_m, depth_m):
    """Is this row a real lot, or an artefact of the parcel dataset?

    Returns a reason string if it is NOT a developable parcel, else None.
    This is a DATA-QUALITY test, not a zoning one -- the reasons are kept in
    a separate field from the by-law minimums so the two never blur together.
    """
    reasons = []

    # No site_id at all. 862 rows citywide have none; the City describes these
    # as Crown land, and they include road and lane allowances.
    if site_id is None or (isinstance(site_id, float) and site_id != site_id):
        reasons.append("no site_id")
    elif str(site_id).strip() in ("", "nan", "None"):
        reasons.append("no site_id")

    # Long thin slivers. A lot 6 m wide and 300 m long is a right-of-way.
    if width_m > 0:
        ratio = depth_m / width_m
        if ratio > MAX_ASPECT_RATIO:
            reasons.append(f"aspect ratio {ratio:.0f}:1")
    else:
        reasons.append("zero width")

    return "; ".join(reasons) if reasons else None


def multiplex_ineligible_reason(lot_area, width, depth):
    """Why section 3.1 is unavailable on this lot, or None if it is available.

    All three floors must be cleared. Below any one of them a multiplex
    cannot be built at ANY unit count, so Scenario B has no meaning here.
    """
    fails = []
    if lot_area < MIN_SITE_AREA_B_M2:
        fails.append(f"area {lot_area:,.0f} < {MIN_SITE_AREA_B_M2:,.0f} m2")
    if width < MIN_FRONTAGE_B_M:
        fails.append(f"frontage {width:.1f} < {MIN_FRONTAGE_B_M:.1f} m")
    if depth < MIN_SITE_DEPTH_B_M:
        fails.append(f"depth {depth:.1f} < {MIN_SITE_DEPTH_B_M:.1f} m")
    if not fails:
        return None
    return "below multiplex minimum (" + "; ".join(fails) + ")"


def compute_parcel(lot_area, width, depth, rectangularity, site_id=None):
    """All the numbers for one parcel, as a plain dictionary."""
    r = {}

    r["lot_area_m2"] = round(lot_area, 2)
    r["lot_width_m"] = round(width, 2)
    r["lot_depth_m"] = round(depth, 2)
    r["rectangularity"] = round(rectangularity, 4)
    r["is_irregular"] = bool(rectangularity < RECTANGULARITY_FLAG)
    r["is_outsized"] = bool(lot_area > OUTSIZED_LOT_THRESHOLD_M2)

    # ---- IS THIS EVEN A LOT? (data quality, not zoning) ----
    np_reason = non_parcel_reason(site_id, width, depth)
    r["developable_parcel"] = bool(np_reason is None)
    r["non_parcel_reason"] = np_reason

    # ---- SCENARIO A: single detached / duplex, s.3.2 ----
    # Both tiers are real by-law numbers.
    #
    # The s.3.2 floors are recorded as FLAGS, not exclusions. s.3.2.2.12
    # expressly allows building on lots narrower than 7.3 m that were on
    # record as of 24 June 2014, and Vancouver has a great many of those --
    # so nulling them would throw away lots that can lawfully be built on.
    r["a_below_area_min"] = bool(lot_area < MIN_SITE_AREA_A_M2)
    r["a_below_frontage_min"] = bool(width < MIN_FRONTAGE_A_M)

    a_footprint = SEC_3_2_FOOTPRINT_RATIO * lot_area      # s.3.2.2.7
    a_impermeable = SEC_3_2_IMPERMEABLE_RATIO * lot_area  # s.3.2.2.8

    if not r["developable_parcel"]:
        # Not a lot at all -- no scenario applies.
        a_impermeable = None
        for f in ("a_footprint_max_m2", "a_impermeable_max_m2",
                  "a_implied_hardscape_m2", "a_runoff_volume_m3"):
            r[f] = None
    else:
        r["a_footprint_max_m2"] = round(a_footprint, 2)
        r["a_impermeable_max_m2"] = round(a_impermeable, 2)
        r["a_implied_hardscape_m2"] = round(a_impermeable - a_footprint, 2)
        r["a_runoff_volume_m3"] = round(runoff_volume_m3(a_impermeable), 3)

    # ---- SCENARIO B: multiplex, s.3.1 ----
    # The legal tier is real; the envelope and like-build tiers are estimates.
    # b_eligible is a ZONING verdict and nothing else. The data-quality verdict
    # lives in developable_parcel. Keeping them apart is what lets the summary
    # report the effect of each filter separately -- if this were one combined
    # flag, the two filtered totals would be identical and the non-parcel
    # filter would look like it had done nothing.
    b_reason = multiplex_ineligible_reason(lot_area, width, depth)
    r["b_eligible"] = bool(b_reason is None)
    r["b_ineligible_reason"] = b_reason

    # Publishing a Scenario B number needs BOTH verdicts to pass.
    b_publish = r["b_eligible"] and r["developable_parcel"]

    b_envelope = multiplex_envelope_m2(width, depth)
    b_legal = lot_area                       # s.3.1 sets NO cap. This is it.
    b_likebuild = min(b_envelope + (HARDSCAPE_RATIO * lot_area), lot_area)

    # Always retained, never nulled, so the citywide total can be reported
    # unfiltered as well as filtered without recomputing anything.
    r["b_unregulated_exposure_raw_m2"] = round(b_legal - b_likebuild, 2)

    if not b_publish:
        b_legal = b_likebuild = None
        for f in ("b_footprint_envelope_m2_est", "b_impermeable_legal_max_m2",
                  "b_impermeable_likebuild_m2_est", "b_runoff_volume_legal_m3",
                  "b_runoff_volume_likebuild_m3_est",
                  "b_unregulated_exposure_m2"):
            r[f] = None
    else:
        r["b_footprint_envelope_m2_est"] = round(b_envelope, 2)
        r["b_impermeable_legal_max_m2"] = round(b_legal, 2)
        r["b_impermeable_likebuild_m2_est"] = round(b_likebuild, 2)
        r["b_runoff_volume_legal_m3"] = round(runoff_volume_m3(b_legal), 3)
        r["b_runoff_volume_likebuild_m3_est"] = round(
            runoff_volume_m3(b_likebuild), 3)
        # The paving section 3.1 permits but nobody has budgeted for.
        r["b_unregulated_exposure_m2"] = round(b_legal - b_likebuild, 2)

    # ---- THE RAIN CITY COMPARISON ----
    # Named "aspirational" on purpose: R1-1 is not legally held to 48 mm.
    #
    # THREE STATES, not two. They must be styled differently on a map:
    #   infeasible     -- D_eff < P. No coverage complies, not even zero.
    #   zero_coverage  -- D_eff == P exactly. Complies, but only at 0% paved.
    #   normal         -- D_eff > P. A real, positive allowance exists.
    compliant = compliant_impermeable_m2(lot_area)
    r["feasible"] = bool(compliant is not None)
    r["buildable"] = bool(compliant is not None and compliant > 0)
    r["compliance_state"] = (
        "infeasible" if compliant is None
        else ("zero_coverage" if compliant <= 0 else "normal"))

    if compliant is None:
        # No paving ratio works on this soil. Emit nulls, not negatives.
        r["infeasible_reason"] = (
            f"D_EFF_MM ({D_EFF_MM:g}) < DESIGN_RAINFALL_MM "
            f"({DESIGN_RAINFALL_MM:g}): the permeable surface cannot store "
            f"even the rain falling directly on it, so the permeable area "
            f"the storm demands exceeds the whole lot."
        )
        for f in ("raincity_aspirational_impermeable_m2",
                  "a_gap_m2", "a_gap_volume_m3",
                  "b_gap_legal_m2", "b_gap_volume_legal_m3",
                  "b_gap_likebuild_m2_est", "b_gap_volume_likebuild_m3_est"):
            r[f] = None
    else:
        r["infeasible_reason"] = None
        r["raincity_aspirational_impermeable_m2"] = round(compliant, 2)

        # A gap only exists where the scenario itself exists. Where a scenario
        # was nulled above, its gap stays null too -- rather than silently
        # becoming zero, which would read as "no problem here".
        if a_impermeable is None:
            r["a_gap_m2"] = r["a_gap_volume_m3"] = None
        else:
            a_gap = max(a_impermeable - compliant, 0.0)
            r["a_gap_m2"] = round(a_gap, 2)
            r["a_gap_volume_m3"] = round(runoff_volume_m3(a_gap), 3)

        if b_legal is None:
            for f in ("b_gap_legal_m2", "b_gap_volume_legal_m3",
                      "b_gap_likebuild_m2_est",
                      "b_gap_volume_likebuild_m3_est"):
                r[f] = None
        else:
            b_gap_legal = max(b_legal - compliant, 0.0)
            r["b_gap_legal_m2"] = round(b_gap_legal, 2)
            r["b_gap_volume_legal_m3"] = round(
                runoff_volume_m3(b_gap_legal), 3)

            b_gap_like = max(b_likebuild - compliant, 0.0)
            r["b_gap_likebuild_m2_est"] = round(b_gap_like, 2)
            r["b_gap_volume_likebuild_m3_est"] = round(
                runoff_volume_m3(b_gap_like), 3)

    # How absorbent the garden would have to be, at the s.3.2.2.8 ceiling.
    # If you ever set SEC_3_2_IMPERMEABLE_RATIO to 1.0 (pave everything) the
    # answer is mathematically infinite. JSON has no way to write infinity,
    # so we emit null instead of producing a file no other tool can open.
    d_req = d_eff_required_mm(SEC_3_2_IMPERMEABLE_RATIO)
    if d_req == float("inf"):
        r["d_eff_required_at_3_2_mm"] = None
        r["d_eff_shortfall_mm"] = None
    else:
        r["d_eff_required_at_3_2_mm"] = round(d_req, 2)
        r["d_eff_shortfall_mm"] = round(d_req - D_EFF_MM, 2)

    return r


# ------------------------------------------------------------------------------
#  MAIN
# ------------------------------------------------------------------------------

def main():
    print("=" * 78)
    print(" VANCOUVER R1-1 STORMWATER GAP ANALYSIS")
    print("=" * 78)

    if not selftest():
        sys.exit("Self-tests failed -- refusing to produce output.")

    # ---- Load -----------------------------------------------------------
    print(f"\nSTEP 1  Loading data (no API key needed; 2 requests, "
          f"quota is 15,000/day)")
    zoning = fetch(ZONING_DATASET,
                   where=f'zoning_district="{ZONING_DISTRICT}"')
    parcels = fetch(PARCEL_DATASET,
                    select="site_id,civic_number,streetname,tax_coord")
    print(f"  {len(zoning):,} {ZONING_DISTRICT} zoning polygons")
    print(f"  {len(parcels):,} parcels citywide")

    # ---- Reproject ------------------------------------------------------
    # This must happen BEFORE any area is computed. Areas in WGS84 come out
    # in square degrees, which is meaningless.
    print(f"\nSTEP 2  Reprojecting {WGS84} (degrees) -> {UTM10N} (metres)")
    zoning = zoning.to_crs(UTM10N)
    parcels = parcels.to_crs(UTM10N)

    # ---- Select R1-1 parcels -------------------------------------------
    print(f"\nSTEP 3  Selecting parcels in {ZONING_DISTRICT} "
          f"(rule: {JOIN_PREDICATE})")
    zone_only = zoning[["geometry"]].copy()

    if JOIN_PREDICATE == "inside_point":
        probe = parcels.copy()
        probe["geometry"] = parcels.geometry.representative_point()
        hit = gpd.sjoin(probe, zone_only, predicate="within", how="inner")
    elif JOIN_PREDICATE == "intersects":
        hit = gpd.sjoin(parcels, zone_only, predicate="intersects",
                        how="inner")
    else:
        sys.exit(f"JOIN_PREDICATE must be 'inside_point' or 'intersects', "
                 f"not {JOIN_PREDICATE!r}")

    # sjoin can return a parcel more than once if it touches two zone
    # polygons, so take the unique set.
    r11 = parcels.loc[sorted(set(hit.index))].copy()
    print(f"  {len(r11):,} parcels are in {ZONING_DISTRICT}")

    # ---- Compute --------------------------------------------------------
    print(f"\nSTEP 4  Computing both scenarios for each parcel")
    r11["lot_area_m2"] = r11.geometry.area

    # Sort before numbering. The portal does not guarantee a stable row order
    # between downloads, so without this a parcel could get a different
    # parcel_id each time you refresh the cache -- which would break any
    # comparison you tried to make between two runs.
    r11 = r11.sort_values(
        ["tax_coord", "site_id", "civic_number", "streetname"],
        na_position="last", kind="mergesort",
    )

    rows = []
    for i, (idx, parcel) in enumerate(r11.iterrows()):
        width, depth, rect = lot_dimensions(parcel.geometry)
        rec = compute_parcel(parcel["lot_area_m2"], width, depth, rect,
                             site_id=parcel.get("site_id"))

        # Identity. site_id is NOT reliable as a key: 862 parcels citywide
        # have none at all, and 28 values repeat across up to 6 rows. So we
        # mint our own sequential id and keep site_id alongside as an
        # attribute.
        #
        # What parcel_id is and is not: it is unique within a run, and stable
        # between runs as long as the City's data has not changed (because we
        # sorted first). It is NOT a City identifier, and if the City adds or
        # removes parcels the numbering after that point will shift. Use
        # tax_coord or site_id if you need to join to another City dataset.
        rec = {
            "parcel_id": f"R11-{i:06d}",
            "site_id": parcel.get("site_id"),
            "address": " ".join(
                str(parcel.get(f) or "").strip()
                for f in ("civic_number", "streetname")).strip() or None,
            "tax_coord": parcel.get("tax_coord"),
            **rec,
        }
        rows.append(rec)

        if (i + 1) % 10000 == 0:
            print(f"    {i + 1:,} / {len(r11):,}")

    out = gpd.GeoDataFrame(pd.DataFrame(rows),
                           geometry=list(r11.geometry),
                           crs=UTM10N)

    # ---- Worked example -------------------------------------------------
    trace(out, TRACE_PARCEL_INDEX)

    # ---- Write ----------------------------------------------------------
    # Written in WGS84 because that is what the GeoJSON standard specifies
    # and what QGIS / web maps expect. Every AREA in the file was computed
    # in UTM 10N, which is what matters.
    print(f"\nSTEP 5  Writing output files")
    out.to_crs(WGS84).to_file(OUTPUT_FILE, driver="GeoJSON")
    print(f"  {OUTPUT_FILE.name}  "
          f"({OUTPUT_FILE.stat().st_size / 1e6:.1f} MB, {len(out):,} features)")

    # Same rows, same numbers, minus the map shapes -- this is the one to
    # open in Excel. Dropping the geometry column is what makes it a plain
    # spreadsheet rather than a GIS file.
    out.drop(columns="geometry").to_csv(SUMMARY_CSV, index=False)
    print(f"  {SUMMARY_CSV.name}  "
          f"({SUMMARY_CSV.stat().st_size / 1e6:.1f} MB, {len(out):,} rows)")

    summary(out)
    worst_parcels(out, TOP_N_PARCELS)


def trace(out, i):
    """Print every intermediate value for one parcel, as a worked example."""
    if i >= len(out):
        return
    p = out.iloc[i]
    A = p["lot_area_m2"]
    P, C, D = DESIGN_RAINFALL_MM, RUNOFF_COEFF, D_EFF_MM

    print("\n" + "=" * 78)
    print(f" WORKED EXAMPLE -- parcel {p['parcel_id']}  "
          f"({p['address'] or 'no address'})")
    print("=" * 78)
    print(f"  INPUTS       P = {P:g} mm   C = {C:g}   D_eff = {D:g} mm")
    print(f"  GEOMETRY     lot area        {A:>12,.2f} m2")
    print(f"               width x depth   {p['lot_width_m']:>6.2f} x "
          f"{p['lot_depth_m']:.2f} m")
    print(f"               rectangularity  {p['rectangularity']:>12.4f}"
          f"   (irregular: {p['is_irregular']})")
    print(f"               outsized lot    {str(p['is_outsized']):>12}")

    print(f"\n  SCENARIO A -- s.3.2 \"Other Uses\" (single detached / duplex)")
    print(f"    footprint      {SEC_3_2_FOOTPRINT_RATIO:.2f} x {A:,.2f}"
          f"{'':>10} = {p['a_footprint_max_m2']:>12,.2f} m2   [s.3.2.2.7]")
    print(f"    impermeable    {SEC_3_2_IMPERMEABLE_RATIO:.2f} x {A:,.2f}"
          f"{'':>10} = {p['a_impermeable_max_m2']:>12,.2f} m2   [s.3.2.2.8]")
    print(f"    hardscape      difference of the two"
          f"{'':>5} = {p['a_implied_hardscape_m2']:>12,.2f} m2")
    print(f"    runoff         {p['a_impermeable_max_m2']:,.2f} x "
          f"{P:g}/1000 x {C:g} = {p['a_runoff_volume_m3']:>10,.3f} m3")

    print(f"\n  SCENARIO B -- multiplex, s.3.1  (envelope is an ESTIMATE)")
    bw = p["lot_width_m"] - 2 * SETBACK_SIDE_M
    bd = p["lot_depth_m"] - SETBACK_FRONT_M - SETBACK_REAR_M
    # A lot can be too narrow or too shallow for the setbacks to leave
    # anything at all. Show 0.00, not a negative building dimension.
    fw = max(min(bw, MAX_BUILDING_WIDTH_M), 0.0)
    fd = max(min(bd, MAX_BUILDING_DEPTH_M), 0.0)
    print(f"    width after sides   {p['lot_width_m']:.2f} - 2x"
          f"{SETBACK_SIDE_M:g} = {bw:>7.2f} m"
          f"  -> use {fw:.2f} (max {MAX_BUILDING_WIDTH_M:g})")
    print(f"    depth after f+r     {p['lot_depth_m']:.2f} - "
          f"{SETBACK_FRONT_M:g} - {SETBACK_REAR_M:g} = {bd:>4.2f} m"
          f"  -> use {fd:.2f} (max {MAX_BUILDING_DEPTH_M:g})")
    if bw < 0 or bd < 0:
        print(f"    (this lot is too small for the setbacks -- nothing fits)")
    print(f"    envelope       {'':>26} = "
          f"{p['b_footprint_envelope_m2_est']:>12,.2f} m2")
    print(f"    legal max      s.3.1 sets no cap -> lot  = "
          f"{p['b_impermeable_legal_max_m2']:>12,.2f} m2")
    print(f"    like-build     envelope + {HARDSCAPE_RATIO:g} x lot  = "
          f"{p['b_impermeable_likebuild_m2_est']:>12,.2f} m2")
    print(f"    UNREGULATED EXPOSURE  legal - likebuild = "
          f"{p['b_unregulated_exposure_m2']:>12,.2f} m2")

    print(f"\n  RAIN CITY COMPARISON  (aspirational -- see caveat 1 at top)")
    print(f"    feasibility    is D_eff ({D:g}) > P ({P:g})?"
          f"{'':>7} {str(p['feasible']):>12}")
    if p["feasible"]:
        denom = D - P + P * C
        perm = A * P * C / denom
        print(f"    denominator    {D:g} - {P:g} + {P:g}x{C:g}"
              f"{'':>9} = {denom:>12,.4f}")
        print(f"    Perm_min       {A:,.2f} x {P:g} x {C:g} / {denom:.4f}"
              f" = {perm:>12,.2f} m2")
        print(f"    I_max          {A:,.2f} - {perm:,.2f}"
              f"{'':>7} = "
              f"{p['raincity_aspirational_impermeable_m2']:>12,.2f} m2")
        # The gap is clamped at zero: a lot that is allowed to pave LESS than
        # the standard permits has no gap, not a negative one. Show the raw
        # difference honestly when the clamp bites, rather than printing a
        # subtraction whose two operands do not give the answer shown.
        raw_gap = (p["a_impermeable_max_m2"]
                   - p["raincity_aspirational_impermeable_m2"])
        if raw_gap < 0:
            print(f"    gap (A)        {p['a_impermeable_max_m2']:,.2f} - "
                  f"{p['raincity_aspirational_impermeable_m2']:,.2f}"
                  f"{'':>2} = {raw_gap:>12,.2f} m2")
            print(f"                   negative, so the gap is recorded as "
                  f"{p['a_gap_m2']:,.2f}:")
            print(f"                   the s.3.2 ceiling is already within "
                  f"what this soil can absorb.")
        else:
            print(f"    gap (A)        {p['a_impermeable_max_m2']:,.2f} - "
                  f"{p['raincity_aspirational_impermeable_m2']:,.2f}"
                  f"{'':>2} = {p['a_gap_m2']:>12,.2f} m2")
        print(f"    gap vol (A)    {'':>26} = "
              f"{p['a_gap_volume_m3']:>12,.3f} m3")
    else:
        denom = D - P + P * C
        print(f"    NO. {p['infeasible_reason']}")
        print(f"    (denominator is {denom:.2f}, still positive -- which is")
        print(f"     why feasibility tests D_eff > P, not the denominator.)")
        print(f"    All gap fields are null for this parcel, not negative.")

    print(f"\n  THE HEADLINE NUMBER")
    d_req = p["d_eff_required_at_3_2_mm"]
    if d_req is None:
        print(f"    Undefined: SEC_3_2_IMPERMEABLE_RATIO is 100%, which would")
        print(f"    need infinite retention depth.")
    else:
        print(f"    At the s.3.2.2.8 ceiling of "
              f"{SEC_3_2_IMPERMEABLE_RATIO:.0%} impermeable, the garden would")
        print(f"    need to retain  {P:g} x (1 + {C:g} x "
              f"{SEC_3_2_IMPERMEABLE_RATIO:g}/{1-SEC_3_2_IMPERMEABLE_RATIO:g})"
              f"  =  {d_req:,.2f} mm")
        print(f"    You have specified               "
              f"   {D:>8,.2f} mm")
        short = p["d_eff_shortfall_mm"]
        # Sign matters: a negative "shortfall" is a surplus, and calling it a
        # shortfall would invert the finding.
        if short > 0:
            print(f"    SHORTFALL                        "
                  f"   {short:>8,.2f} mm")
        else:
            print(f"    SURPLUS                          "
                  f"   {abs(short):>8,.2f} mm   (this soil is sufficient)")
    print("=" * 78)


def worst_parcels(out, n=5):
    """List the n worst parcels in plain language, with street addresses.

    Which measure counts as "worst" depends on the settings:
      - when the soil can manage the storm, we rank by gap volume, i.e. the
        cubic metres of runoff nobody has accounted for;
      - when it cannot (every gap is blank), there is no gap to rank, so we
        fall back to unregulated exposure -- the square metres of paving
        s.3.1 permits beyond a realistic build. The heading says which.
    """
    print("\n" + "=" * 78)
    print(f" THE {n} WORST ORDINARY LOTS -- go and look at these")
    print("=" * 78)

    # Which column means "worst" depends on whether the soil can cope at all.
    if bool(out["feasible"].any()):
        rank_col = "b_gap_volume_legal_m3"
        unit = "m3"
        measure = "of runoff beyond what the site can absorb"
        basis = out[out["feasible"]]
        print(f"\n Ranked by runoff the site cannot absorb, under the multiplex")
        print(f" scenario at its legal ceiling -- which is the whole lot paved,")
        print(f" because s.3.1 sets no impermeability limit at all.")
    else:
        rank_col = "b_unregulated_exposure_m2"
        unit = "m2"
        measure = "of paving s.3.1 permits but nothing accounts for"
        basis = out
        print(f"\n At D_EFF_MM = {D_EFF_MM:g} no parcel can absorb the design "
              f"storm, so")
        print(f" there are no gap volumes to rank. Ranking instead by the "
              f"paving")
        print(f" s.3.1 permits beyond a realistic build.")

    # Parks and golf courses are zoned R1-1 and dwarf everything by raw area,
    # so they would fill this entire list and none of them is a site you can
    # go and look at. Rank the ordinary lots, and mention the giants after.
    # Rights-of-way and lots too small for a multiplex are excluded outright:
    # the first are not lots, the second cannot host the scenario being ranked.
    ordinary = basis[~basis["is_outsized"]
                     & basis["developable_parcel"]
                     & basis["b_eligible"]]

    print()
    for rank, (_, p) in enumerate(ordinary.nlargest(n, rank_col).iterrows(), 1):
        print(f" {rank}. {p['address'] or '(no civic address on file)'}")
        print(f"      {p[rank_col]:,.1f} {unit} {measure}")
        print(f"      lot is {p['lot_area_m2']:,.0f} m2 "
              f"({p['lot_width_m']:.1f} m wide x {p['lot_depth_m']:.1f} m deep)")
        print(f"      parcel_id {p['parcel_id']}"
              + (f", site_id {p['site_id']}" if p["site_id"] else ""))
        if p["is_irregular"]:
            print(f"      NOTE: irregular shape (rectangularity "
                  f"{p['rectangularity']:.2f}) -- the envelope estimate is "
                  f"rough here")
        print()

    # Name the giants explicitly so it is obvious what was set aside and why.
    giants = basis[basis["is_outsized"]].nlargest(3, rank_col)
    if len(giants) > 0:
        print(f" Set aside as OUTSIZED (over "
              f"{OUTSIZED_LOT_THRESHOLD_M2:,.0f} m2) -- parks and institutions,")
        print(f" not development sites, but they top any ranking by raw area:")
        for _, p in giants.iterrows():
            print(f"   - {p['address'] or '(no address)'}  "
                  f"{p['lot_area_m2'] / 1e4:,.1f} ha  "
                  f"({p[rank_col]:,.0f} {unit})")
        print(f" Filter is_outsized = FALSE in the CSV to reproduce the list "
              f"above.")
    print("=" * 78)


def summary(out):
    """Citywide totals."""
    print("\n" + "=" * 78)
    print(" CITYWIDE SUMMARY")
    print("=" * 78)

    dev = out[~out["is_outsized"]]   # the developable subset

    print(f"\n PARAMETERS   P = {DESIGN_RAINFALL_MM:g} mm    "
          f"C = {RUNOFF_COEFF:g}    D_eff = {D_EFF_MM:g} mm    "
          f"hardscape = {HARDSCAPE_RATIO:g}")
    print(f"              rear setback = {SETBACK_REAR_M:g} m "
          f"(non-courtyard), join = {JOIN_PREDICATE}")

    print(f"\n PARCEL COUNTS")
    print(f"   {ZONING_DISTRICT} parcels, all               "
          f"{len(out):>12,}")
    print(f"   outsized (> {OUTSIZED_LOT_THRESHOLD_M2:,.0f} m2), flagged "
          f"{int(out['is_outsized'].sum()):>12,}")
    print(f"   developable (the rest)         {len(dev):>12,}")
    print(f"   not a real parcel (data qual.) "
          f"{int((~out['developable_parcel']).sum()):>12,}")
    print(f"   eligible for s.3.1 multiplex   "
          f"{int(out['b_eligible'].sum()):>12,}")

    # Three states, not two -- they are meant to be styled separately on a map.
    print(f"\n COMPLIANCE STATE (field: compliance_state)")
    labels = {
        "infeasible": f"infeasible     D_eff < P, nothing complies",
        "zero_coverage": f"zero_coverage  D_eff = P exactly, 0% paved only",
        "normal": f"normal         a positive allowance exists",
    }
    for state, label in labels.items():
        n = int((out["compliance_state"] == state).sum())
        print(f"   {label:<48}{n:>12,}")

    # Irregular lots, reported BOTH ways on purpose. The all-parcels figure is
    # badly skewed by the parks: Stanley Park is both huge and irregular, so it
    # alone drags the area share from 9% to 32%. The developable row is the one
    # that tells you whether the rectangle assumption is safe.
    print(f"\n IRREGULAR LOTS (rectangularity < {RECTANGULARITY_FLAG}) -- where "
          f"the setback envelope is least reliable")
    for label, sub in (("all parcels", out), ("developable only", dev)):
        n_ir = int(sub["is_irregular"].sum())
        ir_area = sub.loc[sub["is_irregular"], "lot_area_m2"].sum()
        print(f"   {label:<22} {n_ir:>10,}  "
              f"({100 * n_ir / len(sub):>5.2f}% of parcels, "
              f"{100 * ir_area / sub['lot_area_m2'].sum():>5.2f}% of area)")

    print(f"\n LOT AREA")
    print(f"   all parcels                    "
          f"{out['lot_area_m2'].sum() / 1e6:>12,.2f} km2")
    print(f"   developable only               "
          f"{dev['lot_area_m2'].sum() / 1e6:>12,.2f} km2")
    print(f"   median lot                     "
          f"{dev['lot_area_m2'].median():>12,.1f} m2")

    def tot(df, col):
        return df[col].sum(skipna=True) if col in df else 0.0

    print(f"\n IMPERMEABLE AREA CEILINGS        "
          f"{'all parcels':>16}{'developable':>18}")
    for label, col in [
        ("A  footprint      s.3.2.2.7", "a_footprint_max_m2"),
        ("A  impermeable    s.3.2.2.8", "a_impermeable_max_m2"),
        ("A  hardscape      implied  ", "a_implied_hardscape_m2"),
        ("B  envelope       EST      ", "b_footprint_envelope_m2_est"),
        ("B  legal max      s.3.1    ", "b_impermeable_legal_max_m2"),
        ("B  like-build     EST      ", "b_impermeable_likebuild_m2_est"),
    ]:
        print(f"   {label}    {tot(out, col) / 1e6:>13,.3f} km2"
              f"{tot(dev, col) / 1e6:>14,.3f} km2")

    # ---- The three-way exposure figure ----
    # Computed from the RAW column, which is never nulled, so all three rows
    # come from the same arithmetic and differ only in which rows are counted.
    raw = "b_unregulated_exposure_raw_m2"
    elig = dev[dev["b_eligible"]]
    both = dev[dev["b_eligible"] & dev["developable_parcel"]]

    print(f"\n UNREGULATED EXPOSURE  (s.3.1 legal ceiling minus like-build)")
    print(f"   Developable land only, i.e. lots at or under "
          f"{OUTSIZED_LOT_THRESHOLD_M2:,.0f} m2.\n")
    print(f"   {'basis':<42}{'parcels':>10}{'exposure':>14}")
    print(f"   {'-' * 66}")
    print(f"   {'1. unfiltered':<42}{len(dev):>10,}"
          f"{tot(dev, raw) / 1e6:>11,.3f} km2")
    print(f"   {'2. s.3.1 minimums applied':<42}{len(elig):>10,}"
          f"{tot(elig, raw) / 1e6:>11,.3f} km2")
    print(f"   {'3. minimums + non-parcel filter':<42}{len(both):>10,}"
          f"{tot(both, raw) / 1e6:>11,.3f} km2")
    print(f"\n   Row 3 is the defensible figure: real lots, large enough for a")
    print(f"   multiplex. Rows 1 and 2 are shown so the effect of each filter")
    print(f"   is visible rather than buried.")

    print(f"\n WHAT EACH FILTER REMOVED")
    npf = dev[~dev["developable_parcel"]]
    print(f"   non-parcels (data quality, not zoning)"
          f"{len(npf):>16,}{npf['lot_area_m2'].sum() / 1e6:>11,.3f} km2 of land")
    if len(npf):
        # Bucketed, not one line per distinct ratio -- otherwise this prints
        # twenty near-identical rows and buries the shape of the problem.
        no_id = npf["non_parcel_reason"].str.contains("no site_id", na=False)
        sliver = npf["non_parcel_reason"].str.contains("aspect", na=False)
        print(f"      no site_id{'':<27}{int(no_id.sum()):>10,}")
        print(f"      sliver (aspect > {MAX_ASPECT_RATIO:g}:1)"
              f"{'':<17}{int(sliver.sum()):>10,}")
        print(f"      both reasons{'':<25}"
              f"{int((no_id & sliver).sum()):>10,}")
    below = dev[~dev["b_eligible"]]
    print(f"   below s.3.1 minimums (zoning)         "
          f"{len(below):>16,}"
          f"{below['lot_area_m2'].sum() / 1e6:>11,.3f} km2 of land")
    print(f"   overlap (fails both tests)            "
          f"{int((~dev['b_eligible'] & ~dev['developable_parcel']).sum()):>16,}")

    print(f"\n SCENARIO A FLOORS -- flagged, never excluded")
    print(f"   s.3.2.2.12 permits building on sub-{MIN_FRONTAGE_A_M:g} m lots on "
          f"record as of")
    print(f"   24 June 2014, so these lots are kept with their numbers intact.")
    print(f"   below {MIN_SITE_AREA_A_M2:,.0f} m2 area (s.3.2.2.1)      "
          f"{int(dev['a_below_area_min'].sum()):>16,}")
    print(f"   below {MIN_FRONTAGE_A_M:g} m frontage (s.3.2.2.2)     "
          f"{int(dev['a_below_frontage_min'].sum()):>16,}")

    print(f"\n RAIN CITY GAP VOLUME  (aspirational benchmark, not a rule)")
    if bool((~out["feasible"]).all()):
        print(f"\n   NOT COMPUTABLE AT D_EFF_MM = {D_EFF_MM:g}.")
        print(f"   Every parcel is infeasible: a surface that holds "
              f"{D_EFF_MM:g} mm cannot")
        print(f"   absorb a {DESIGN_RAINFALL_MM:g} mm storm landing on itself, "
              f"so no amount of")
        print(f"   paving -- including none at all -- meets the standard.")
        print(f"   This is a real finding, not an error.")
        print(f"\n   To get gap volumes, raise D_EFF_MM above "
              f"{DESIGN_RAINFALL_MM:g} mm. For reference,")
        print(f"   the by-law's own {SEC_3_2_IMPERMEABLE_RATIO:.0%} ceiling "
              f"implicitly requires "
              f"{d_eff_required_mm(SEC_3_2_IMPERMEABLE_RATIO):.1f} mm.")
    else:
        for label, col in [
            ("A  single detached / duplex", "a_gap_volume_m3"),
            ("B  multiplex, legal max    ", "b_gap_volume_legal_m3"),
            ("B  multiplex, like-build   ", "b_gap_volume_likebuild_m3_est"),
        ]:
            print(f"   {label}    {tot(out, col):>13,.0f} m3"
                  f"{tot(dev, col):>14,.0f} m3")

    print(f"\n THE HEADLINE NUMBER")
    d_req = d_eff_required_mm(SEC_3_2_IMPERMEABLE_RATIO)
    if d_req == float("inf"):
        print(f"   Undefined: SEC_3_2_IMPERMEABLE_RATIO is 100%, which would "
              f"require")
        print(f"   infinite retention depth.")
    else:
        print(f"   At the s.3.2.2.8 ceiling of "
              f"{SEC_3_2_IMPERMEABLE_RATIO:.0%} impermeable, every "
              f"{ZONING_DISTRICT} lot")
        print(f"   would need its garden to retain   {d_req:>8,.1f} mm")
        print(f"   Specified retention depth          {D_EFF_MM:>8,.1f} mm")
        if d_req > D_EFF_MM:
            print(f"   SHORTFALL                          "
                  f"{d_req - D_EFF_MM:>8,.1f} mm   "
                  f"({d_req / D_EFF_MM:.1f}x short)")
        else:
            print(f"   SURPLUS                            "
                  f"{D_EFF_MM - d_req:>8,.1f} mm   "
                  f"(this soil already meets the ceiling)")

    print(f"\n REMINDERS")
    print(f"   - 48 mm is NOT a legal requirement for R1-1. See caveat 1.")
    print(f"   - Scenario B envelope is a geometric estimate, not a by-law "
          f"figure.")
    print(f"   - Multiplex needs rear lane access (s.2.2.7); not modelled, "
          f"so B is overstated.")
    print(f"   - Courtyard rear setback (0.9 m) not modelled; B understated "
          f"on deep lots.")
    print("=" * 78)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    main()
