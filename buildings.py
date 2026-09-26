"""
================================================================================
 VANCOUVER R1-1 STORMWATER  --  Stage 2, Part 1: EXISTING BUILDINGS
================================================================================

WHAT THIS SCRIPT DOES
  1. Reads the Stage 1 output (r11_stormwater.geojson -- every R1-1 parcel).
     Run stormwater.py first if you don't have it.
  2. Downloads the City's 2015 building footprints (cached, like Stage 1).
  3. Merges parcels into zoning SITES where they share a civic address AND
     adjoin (s.2 of the Zoning and Development By-law: a site is one or more
     adjoining parcels). Stage 1's numbers are recomputed for merged sites.
  4. Clips every building to the site lines. A building that crosses a
     lot line is split, and each lot gets only the part standing on it.
  5. Adds up the roof area on every site, and flags lots whose roofs cover
     more than CHECK_DATA_ROOF_SHARE of the lot as "check data".
  6. For each soil holding depth, works out how much of the lot must stay
     permeable to handle the design storm -- and whether the roofs that are
     already there make that impossible.
  7. Sets aside sites that are not ordinary residential lots -- anything over
     SCOPE_MAX_SITE_M2 after merging (parks, schools, golf courses) and
     rights-of-way. They stay in the files, marked, but are left out of
     every statistic.
  8. Writes (one row per SITE; most sites are a single parcel):
       r11_stage2.geojson        every site, full detail, every field
       map/data/lots.geojson     what the web map needs, and nothing else
       map/data/buildings.geojson  the building outlines the map draws

HOW TO RUN IT
     source .venv/bin/activate
     python buildings.py

  First run downloads the footprints (~80 MB). Later runs use cache/.

TO CHANGE THE NUMBERS
  Everything is in the CONFIGURATION block below. You should not need to
  touch anything after "END OF CONFIGURATION".

--------------------------------------------------------------------------------
 CAVEATS
--------------------------------------------------------------------------------
 1. The footprints are from 2015 and the City no longer updates them.
    Anything built or demolished since then is wrong here.
 2. Roofs only. Driveways, patios and walks are NOT in any City dataset,
    so "today" in this script means "roofs only". Real hard surface today
    is higher.
 3. ROOF AREA IS LIKELY A SLIGHT OVERESTIMATE. The footprints were traced
    from air photos, so they follow the ROOF EDGE, eaves included. The by-law
    measures building coverage to the outside of the walls and excludes
    eaves (typically 0.3-0.6 m overhang on a house). So roof_area_m2 here
    will usually be a little larger than the by-law's building area.
 4. ZONING SITES. Parcels sharing an address and adjoining are treated as
    one zoning site, per the Section 2 definition of Site. (E.g. 4010 Victoria Drive is
    two parcels and one house.) The impermeable limits apply to the site, so
    roof area and every percentage is computed on the merged site.
    Limits of this rule: the parcel data has no legal "site" field, so the
    shared civic address is a stand-in for it. Parcels that share an address
    but do NOT adjoin are kept separate and flagged "shared address, not
    adjoining - check". Adjoining lots with DIFFERENT addresses that are in
    fact one site are not detected. Section 2 also says a site abuts a street
    that is not a lane; that is not checked.
 5. RUNOFF_COEFF here is 0.85. Stage 1 (stormwater.py) used 0.9, so the
    Stage 1 volume fields carried along in r11_stage2.geojson (a_runoff_*,
    b_runoff_*, a_gap_* ...) were computed at 0.9. The NEW fields this script
    adds all use 0.85. Don't mix them in one sum.
 6. The 48 mm standard is aspirational for R1-1, not a legal requirement
    (see stormwater.py, caveat 1).
 7. BUILDING HEIGHTS ARE FOR 3D MODELS ONLY. No calculation uses them.
    Where a 2015 building is at least half covered by a 2009 LiDAR outline,
    it takes that building's measured AVERAGE height (2009 -- anything built
    or raised since is wrong). Otherwise it gets a placeholder: 3 m under
    40 m2 (garages, sheds), 8.5 m above. Every building records which it is
    (height_source), so a model can show real and placeholder heights apart.
    The 2009 heights look low (median 5.0 m) -- check a house you know.
================================================================================
"""

import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

# Stage 1's download function -- same portal, same cache folder, same checks.
from stormwater import fetch

# ==============================================================================
#  CONFIGURATION  --  change these numbers, not the code below
# ==============================================================================

# ---- RAINFALL AND HYDROLOGY --------------------------------------------------

DESIGN_RAINFALL_MM = 48      # Rain City daily standard: mm of rain in 24 hours
                             # that a lot should manage on site.

RUNOFF_COEFF = 0.85          # Share of rain that runs off hard surfaces.
                             # 0.85 = 85% runs off, 15% is lost to wetting,
                             # evaporation and cracks.
                             # NOTE: Stage 1 used 0.9. See caveat 5 above.

D_EFF_OPTIONS_MM = [30, 48, 75, 285]
# Soil holding depth: how many mm of water the permeable ground can soak up
# and hold before it starts shedding water too.
#   30  = compacted lawn
#   48  = break-even (holds exactly the rain that falls on it, nothing more)
#   75  = good soil
#   285 = rain garden (150 mm ponding + 450 mm soil at 30% voids)
#
# Anything BELOW the design rainfall (e.g. 30) cannot even hold the rain that
# lands on itself, so no lot can meet the standard at that depth, whatever
# its roofs. Those lots are flagged "not achievable" and get blank areas,
# not negative ones.

# ---- BUILDINGS ---------------------------------------------------------------

CHECK_DATA_ROOF_SHARE = 0.90
# Lots whose roofs cover more than this share of the lot (0.90 = 90%) are
# flagged check_data = true and listed at the end of the run. A house cannot
# lawfully cover that much of an R1-1 lot, so a number this high usually
# means the data is off (an out-of-date footprint, a mis-drawn parcel, or one
# site recorded as several parcels). They are kept in, but flagged.
#
# How buildings are counted: each footprint is CLIPPED to the parcel lines.
# A building crossing a lot line is split between the lots it stands on.
# Only R1-1 parcels are clipped against, so any part of a building standing
# on a non-R1-1 lot is simply not counted here.

# ---- WHAT COUNTS AS AN ORDINARY LOT -------------------------------------------

SCOPE_MAX_SITE_M2 = 2000
# Sites bigger than this (measured AFTER merging) are "Outside scope (large
# site)": parks, schools, golf courses and institutions that happen to be
# zoned R1-1. They are drawn grey on the map and left out of every count,
# total and pass/fail figure. Rights-of-way (Stage 1's developable_parcel =
# false) are set aside the same way, as "not a lot".

# ---- BUILDING HEIGHTS (for 3D models only -- no calculation uses them) --------

HEIGHT_DATASET = "building-footprints-2009"
# The City's 2009 footprints, measured from LiDAR, are the only City data
# with a height per building. Their outlines were traced separately from the
# 2015 ones, so the two are matched by overlap.

HEIGHT_FIELD = "avght_m"
# Which 2009 height to use:
#   "avght_m" = average height of the roof (right for simple block models)
#   "hgt_agl" = height to the highest point, the ridge (right for silhouettes)

HEIGHT_MIN_MATCH_SHARE = 0.5
# A 2015 building takes the 2009 height only if at least this share of its
# outline (0.5 = half) is covered by 2009 LiDAR buildings. Where several
# 2009 buildings overlap it, their heights are averaged, weighted by overlap.
# Raise this to be stricter: a house rebuilt since 2009 on the same spot can
# still overlap its old outline and inherit the old height.

PLACEHOLDER_HEIGHT_M = 8.5        # no 2009 match, and 40 m2 or bigger
PLACEHOLDER_SMALL_HEIGHT_M = 3.0  # no 2009 match, and smaller than below
SMALL_BUILDING_M2 = 40            # under this = garage or shed

# ---- ZONING SITES ------------------------------------------------------------

ADJOIN_TOLERANCE_M = 0.1
# Two parcels "adjoin" if their outlines come within this distance of each
# other along a shared line. Parcel lines in the City data are drawn
# separately, so neighbours can be a few centimetres apart or overlap
# slightly; 0.1 m absorbs that without joining lots across a lane.

MIN_SHARED_EDGE_M = 1.0
# ...and only if that shared line is at least this long. Two lots that touch
# at a single corner point do not share an edge, so they are not adjoining.

SHARED_ADDRESS_FLAG = "shared address, not adjoining - check"
# The label put on parcels that share an address with a parcel they do NOT
# adjoin. They are kept as separate sites.

# ---- FOR REPORTING -----------------------------------------------------------

OLYMPIC_POOL_M3 = 2500       # one Olympic pool, for turning m3 into something
                             # people can picture: 50 x 25 x 2 m.

CHECK_ADDRESS = ("1349", "E 13TH AV")
# A lot to print every number for, as a check. (civic number, street name)
# spelled the way the City's parcel data spells it.

RANDOM_LOTS = 10             # how many random lots to list for aerial checks
RANDOM_SEED = 540            # change this to get a different random 10

# ---- BROWSER FILES -----------------------------------------------------------

SIMPLIFY_M = 0.3
# Outlines are simplified by up to this many metres before going to the
# browser. 0.3 m is invisible at street zoom and removes most of the points
# on curved lot lines. Areas are always computed on the FULL geometry first.

COORD_DECIMALS = 6           # decimal places of latitude/longitude kept in the
                             # browser files. 6 decimals = about 0.1 m.

# ---- FILES -------------------------------------------------------------------

FOOTPRINT_DATASET = "building-footprints-2015"
HERE = Path(__file__).resolve().parent
STAGE1_FILE = HERE / "r11_stormwater.geojson"
OUTPUT_FILE = HERE / "r11_stage2.geojson"
WEB_DIR = HERE / "map" / "data"
WEB_LOTS = WEB_DIR / "lots.geojson"
WEB_BUILDINGS = WEB_DIR / "buildings.geojson"

WGS84 = 4326     # degrees -- what the portal and web maps use
UTM10N = 26910   # metres -- all areas are computed in this

# ==============================================================================
#  END OF CONFIGURATION
# ==============================================================================


# ------------------------------------------------------------------------------
#  THE WATER BALANCE
#
#  The permeable part must hold the rain landing on it AND the runoff from
#  the hard part:
#
#       Perm x D_eff  >=  Perm x P  +  Imperv x P x C,   Imperv = A - Perm
#
#  Solve for the smallest Perm:
#
#       Perm_min = A x P x C / (D_eff - P + P x C)
#
#  Perm_min fits on the lot (Perm_min <= A) only when D_eff >= P. Below that
#  the formula still gives a positive number, but a number BIGGER than the lot
#  -- e.g. 30 mm lawn gives 1.79 x the lot. So the test is D_eff >= P, not
#  just "is the denominator positive". This is the same gate Stage 1 uses.
# ------------------------------------------------------------------------------

def achievable(d_eff):
    """Can any lot meet the storm at this soil depth?"""
    return d_eff >= DESIGN_RAINFALL_MM


def perm_min_m2(lot_area, d_eff):
    """Smallest permeable area that handles the design storm, or None."""
    if not achievable(d_eff):
        return None
    P, C = DESIGN_RAINFALL_MM, RUNOFF_COEFF
    return lot_area * P * C / (d_eff - P + P * C)


def selftest():
    """Check the formula against the water balance before trusting it."""
    ok = True
    P, C, A = DESIGN_RAINFALL_MM, RUNOFF_COEFF, 400.0
    for d in D_EFF_OPTIONS_MM:
        pm = perm_min_m2(A, d)
        if pm is None:
            continue
        incoming = pm * P + (A - pm) * P * C     # mm x m2
        capacity = pm * d
        if abs(incoming - capacity) > 1e-6:
            print(f"  SELFTEST FAILED at D_eff={d}: in {incoming} vs cap {capacity}")
            ok = False
    if achievable(DESIGN_RAINFALL_MM) and abs(perm_min_m2(A, P) - A) > 1e-9:
        print("  SELFTEST FAILED: at D_eff = P the whole lot must be permeable")
        ok = False
    return ok


def dkey(d):
    """Field-name suffix for a soil depth, e.g. 75 -> '_d75'."""
    return f"_d{d:g}"


def add_stormwater_fields(df):
    """Add perm_min / max_imperv / roof_blocks for every soil depth."""
    for d in D_EFF_OPTIONS_MM:
        k = dkey(d)
        if achievable(d):
            pm = df["lot_area_m2"].map(lambda a: perm_min_m2(a, d))
            mi = (df["lot_area_m2"] - pm).clip(lower=0)
            df["perm_min_m2" + k] = pm.round(2)
            df["max_imperv_m2" + k] = mi.round(2)
            # Strictly greater: a lot whose roofs EXACTLY equal the allowance
            # can still comply by keeping all its ground permeable.
            df["roof_blocks" + k] = df["roof_area_m2"] > mi + 1e-9
            df["achievable" + k] = True
        else:
            df["perm_min_m2" + k] = None
            df["max_imperv_m2" + k] = None
            df["roof_blocks" + k] = None
            df["achievable" + k] = False
    return df


# ------------------------------------------------------------------------------
#  MERGE PARCELS INTO ZONING SITES
# ------------------------------------------------------------------------------

def adjoin(a, b):
    """True if two parcel shapes share an edge (not just a corner).

    Grow one parcel by the tolerance and measure how much of the other it
    overlaps. A shared edge L metres long gives an overlap of about
    L x tolerance; a corner touch gives almost none.
    """
    if a.distance(b) > ADJOIN_TOLERANCE_M:
        return False
    overlap = a.buffer(ADJOIN_TOLERANCE_M).intersection(b).area
    return overlap >= ADJOIN_TOLERANCE_M * MIN_SHARED_EDGE_M


def group_adjoining(geoms):
    """Split a list of shapes into groups that are connected edge-to-edge.

    Returns a list of lists of positions, e.g. [[0, 1], [2]] means shapes 0
    and 1 adjoin (directly or through each other) and shape 2 stands alone.
    """
    n = len(geoms)
    group = list(range(n))            # each shape starts in its own group

    def root(i):
        while group[i] != i:
            i = group[i]
        return i

    for i in range(n):
        for j in range(i + 1, n):
            if root(i) != root(j) and adjoin(geoms[i], geoms[j]):
                group[root(j)] = root(i)
    out = {}
    for i in range(n):
        out.setdefault(root(i), []).append(i)
    return list(out.values())


def close_gaps(geom):
    """The site outline without the internal parcel lines.

    The union of two neighbouring parcels can keep a hairline gap between
    them. Growing by the tolerance and shrinking back closes it; mitred
    corners keep the outer corners square.
    """
    t = ADJOIN_TOLERANCE_M
    return geom.buffer(t, join_style=2).buffer(-t, join_style=2)


def build_sites(parcels):
    """One row per zoning site. Most sites are one parcel, unchanged.

    New fields on every row:
      site_key     the site's id: the parcel_id for a single parcel,
                   "SITE-" + the first parcel_id for a merged site
      parcel_ids   the Stage 1 parcel_id(s) that make up the site
      n_parcels    how many parcels
      merged_site  true if more than one parcel was merged
      site_flag    SHARED_ADDRESS_FLAG, or empty
    """
    import stormwater as s1   # Stage 1's own lot measuring and by-law rules
    from shapely.ops import unary_union

    parcels = parcels.copy()
    parcels["site_key"] = parcels["parcel_id"]
    parcels["site_flag"] = None
    keep = []                 # rows passed through as single-parcel sites
    merged_rows = []

    counts = parcels["address"].value_counts()
    shared = set(counts[counts > 1].index)
    for addr, grp in parcels[parcels["address"].isin(shared)].groupby("address"):
        grp = grp.sort_values("parcel_id")
        parts = group_adjoining(list(grp.geometry))
        if len(parts) > 1:
            # Some of this address's parcels are not next to the others.
            parcels.loc[grp.index, "site_flag"] = SHARED_ADDRESS_FLAG
        for part in parts:
            if len(part) == 1:
                continue
            rows = grp.iloc[part]
            exact = unary_union(list(rows.geometry))
            w, d, rect = s1.lot_dimensions(exact)
            ids = [x for x in rows["site_id"] if x]
            rec = s1.compute_parcel(exact.area, w, d, rect,
                                    site_id=ids[0] if ids else None)
            rec.update({
                "site_key": "SITE-" + rows["parcel_id"].iloc[0],
                "parcel_id": None,
                "site_id": ",".join(ids) or None,
                "address": addr,
                "tax_coord": ",".join(sorted(set(
                    x for x in rows["tax_coord"] if x))) or None,
                "parcel_ids": ",".join(rows["parcel_id"]),
                "n_parcels": len(rows),
                "merged_site": True,
                "site_flag": rows["site_flag"].iloc[0],
                "geometry": close_gaps(exact),
            })
            merged_rows.append(rec)
            parcels = parcels.drop(rows.index)

    parcels["parcel_ids"] = parcels["parcel_id"]
    parcels["n_parcels"] = 1
    parcels["merged_site"] = False
    merged = gpd.GeoDataFrame(merged_rows, geometry="geometry", crs=parcels.crs)
    sites = pd.concat([parcels, merged], ignore_index=True)
    # Stage 1 left an absent Scenario B as null; merged rows follow suit.
    return gpd.GeoDataFrame(sites, geometry="geometry", crs=parcels.crs)


# ------------------------------------------------------------------------------
#  JOIN BUILDINGS TO SITES
# ------------------------------------------------------------------------------

def clip_buildings(fp, parcels):
    """Cut every footprint along the parcel lines.

    Returns one row per (building, parcel) piece, with the piece's area.
    A building wholly inside one lot gives one piece; a building crossing a
    lot line gives one piece per lot. Parts of buildings that stand on no
    R1-1 parcel produce no piece at all.
    """
    pieces = gpd.overlay(fp[["object_id", "geometry"]],
                         parcels[["site_key", "geometry"]],
                         how="intersection", keep_geom_type=True)
    pieces["area_m2"] = pieces.geometry.area
    return pieces


def add_roof_fields(parcels, pieces):
    """roof_area_m2, building_count, roof_share and check_data per parcel."""
    roof = pieces.groupby("site_key")["area_m2"].sum()
    # Count a building on a lot only if a real part of it stands there.
    # Lot lines and footprints never line up perfectly, so many buildings
    # overlap next door by a few square centimetres. Their AREA is still
    # added (it is tiny); they just don't count as another building.
    real = pieces[pieces["area_m2"] >= 1.0]
    count = real.groupby("site_key")["object_id"].nunique()
    parcels["roof_area_m2"] = parcels["site_key"].map(roof).fillna(0).round(2)
    parcels["building_count"] = (parcels["site_key"].map(count)
                                 .fillna(0).astype(int))
    parcels["roof_share"] = (parcels["roof_area_m2"]
                             / parcels["lot_area_m2"]).round(4)
    parcels["check_data"] = parcels["roof_share"] > CHECK_DATA_ROOF_SHARE
    return parcels


# ------------------------------------------------------------------------------
#  MAIN
# ------------------------------------------------------------------------------

def main():
    print("=" * 78)
    print(" STAGE 2, PART 1 -- EXISTING BUILDINGS ON R1-1 LOTS")
    print("=" * 78)
    if not selftest():
        sys.exit("Self-tests failed -- refusing to produce output.")

    if not STAGE1_FILE.exists():
        sys.exit(f"{STAGE1_FILE.name} not found. Run stormwater.py first.")

    print("\nSTEP 1  Loading")
    parcels = gpd.read_file(STAGE1_FILE).to_crs(UTM10N)
    print(f"  {len(parcels):,} R1-1 parcels from Stage 1")
    n_parcels = len(parcels)
    fp = fetch(FOOTPRINT_DATASET).to_crs(UTM10N)
    print(f"  {len(fp):,} building footprints citywide (2015)")

    # A few footprints can be invalid (self-touching rings); make_valid fixes
    # them without changing their area in any meaningful way.
    bad = ~fp.geometry.is_valid
    if bad.any():
        fp.loc[bad, "geometry"] = fp.loc[bad, "geometry"].make_valid()
        print(f"  repaired {int(bad.sum())} invalid footprint shapes")

    print("\nSTEP 2  Merging parcels into zoning sites")
    parcels = build_sites(parcels)
    m = parcels[parcels["merged_site"]]
    print(f"  {len(m):,} merged sites, made from {int(m['n_parcels'].sum()):,} "
          f"parcels (same address, adjoining)")
    print(f"  {int(parcels['site_flag'].notna().sum()):,} rows flagged "
          f"'{SHARED_ADDRESS_FLAG}'")
    print(f"  {n_parcels:,} parcels -> {len(parcels):,} sites")

    print("\nSTEP 3  Clipping every building to the site lines")
    pieces = clip_buildings(fp, parcels)
    ids = set(pieces["object_id"])
    fp["area_m2"] = fp.geometry.area
    on_r11 = fp[fp["object_id"].isin(ids)].copy()
    split = pieces[pieces["area_m2"] >= 1.0].groupby("object_id").size()
    print(f"  {len(on_r11):,} buildings stand at least partly on R1-1 parcels")
    print(f"  {int((split > 1).sum()):,} of them cross a lot line by 1 m2 or "
          f"more and are split")
    counted = pieces["area_m2"].sum()
    print(f"  {counted:,.0f} of their {on_r11['area_m2'].sum():,.0f} m2 stands "
          f"on R1-1 parcels and is counted")

    print("\nSTEP 4  Roof area per site")
    parcels = add_roof_fields(parcels, pieces)
    parcels = add_stormwater_fields(parcels)
    parcels["scope"] = "in"
    parcels.loc[parcels["lot_area_m2"] > SCOPE_MAX_SITE_M2, "scope"] = "large site"
    parcels.loc[~parcels["developable_parcel"].astype(bool), "scope"] = "not a lot"
    for k, v in parcels["scope"].value_counts().items():
        print(f"  scope = {k:<12} {v:>7,} sites")

    # ---- Write ----------------------------------------------------------
    print("\nSTEP 5  Writing files")
    parcels.to_crs(WGS84).to_file(OUTPUT_FILE, driver="GeoJSON")
    print(f"  {OUTPUT_FILE.name:28s} {OUTPUT_FILE.stat().st_size / 1e6:6.1f} MB"
          f"  (full detail, all Stage 1 fields kept or recomputed)")

    write_web(parcels)
    print("\n  Building heights (3D models only)")
    on_r11 = add_heights(on_r11)
    write_web_buildings(on_r11)

    summary(parcels)
    check_data_list(parcels)
    check_lot(fp, parcels)
    random_lots(parcels)


def write_web(p):
    """The one small file the map loads.

    Short property names keep the file small -- 64,000 lots x long names
    was most of the old file's size. What each one means:
      k   site_key            ad  address
      A   site area, m2       r   roof area on the site, m2
      sc  0 = ordinary lot, 1 = outside scope (large site), 2 = not a lot
      m   1 = merged site     f   1 = shared address, not adjoining
      cd  1 = check data (roofs over CHECK_DATA_ROOF_SHARE)
    Everything else the map shows is worked out in the page from A and r,
    using the numbers in the page's own CONFIGURATION block.
    """
    import json
    WEB_DIR.mkdir(parents=True, exist_ok=True)
    g = p[["geometry"]].copy()
    g["geometry"] = g.geometry.simplify(SIMPLIFY_M, preserve_topology=True)
    g = g.to_crs(WGS84)
    code = {"in": 0, "large site": 1, "not a lot": 2}
    feats = []
    for (_, r), geom in zip(p.iterrows(), g.geometry):
        props = {"k": r["site_key"], "ad": r["address"] or "",
                 "A": round(float(r["lot_area_m2"]), 2),
                 "r": round(float(r["roof_area_m2"]), 2),
                 "sc": code[r["scope"]]}
        if r["merged_site"]:
            props["m"] = 1
        if r["site_flag"]:
            props["f"] = 1
        if r["check_data"]:
            props["cd"] = 1
        feats.append({"type": "Feature", "properties": props,
                      "geometry": round_coords(geom.__geo_interface__)})
    with open(WEB_LOTS, "w") as fh:
        json.dump({"type": "FeatureCollection", "features": feats}, fh,
                  separators=(",", ":"))
    print(f"  map/data/{WEB_LOTS.name:14s} {WEB_LOTS.stat().st_size / 1e6:6.1f} MB"
          f"  (simplified {SIMPLIFY_M} m, {COORD_DECIMALS} decimals)")


def add_heights(b):
    """height_m and height_source for every building, from 2009 LiDAR or a placeholder."""
    h09 = fetch(HEIGHT_DATASET).to_crs(UTM10N)
    bad = ~h09.geometry.is_valid
    h09.loc[bad, "geometry"] = h09.loc[bad, "geometry"].make_valid()
    h09 = h09[h09[HEIGHT_FIELD].notna() & (h09[HEIGHT_FIELD] > 0)]
    ov = gpd.overlay(b[["object_id", "geometry"]], h09[[HEIGHT_FIELD, "geometry"]],
                     how="intersection", keep_geom_type=True)
    ov["ov"] = ov.geometry.area
    ov["wh"] = ov[HEIGHT_FIELD] * ov["ov"]
    g = ov.groupby("object_id")[["wh", "ov"]].sum()
    b = b.copy()
    share = (b["object_id"].map(g["ov"]).fillna(0) / b["area_m2"]).clip(upper=1)
    lidar = b["object_id"].map(g["wh"] / g["ov"])
    matched = share >= HEIGHT_MIN_MATCH_SHARE
    small = b["area_m2"] < SMALL_BUILDING_M2
    placeholder = small.map({True: PLACEHOLDER_SMALL_HEIGHT_M,
                             False: PLACEHOLDER_HEIGHT_M})
    b["height_m"] = lidar.where(matched, placeholder).round(1)
    b["height_source"] = matched.map({True: "lidar_2009", False: "placeholder"})
    b["lidar_match_share"] = share.round(3)
    n = len(b)
    print(f"    2009 LiDAR height ({HEIGHT_FIELD}, >= "
          f"{HEIGHT_MIN_MATCH_SHARE:.0%} matched) {int(matched.sum()):>8,} "
          f"({matched.mean():.0%})  median {b.loc[matched, 'height_m'].median():.1f} m")
    print(f"    placeholder {PLACEHOLDER_HEIGHT_M:g} m (>= {SMALL_BUILDING_M2} m2)"
          f"             {int((~matched & ~small).sum()):>8,}")
    print(f"    placeholder {PLACEHOLDER_SMALL_HEIGHT_M:g} m (< {SMALL_BUILDING_M2} m2)"
          f"               {int((~matched & small).sum()):>8,}")
    print(f"    total buildings                             {n:>8,}")
    return b


def write_web_buildings(b):
    """The building outlines the map draws on top of the lots.

    Each building is drawn WHOLE, even where it crosses a lot line -- only
    the roof NUMBERS are split between lots, not the picture. Properties:
      id  the City's object_id for the footprint
      a   the footprint's full area, m2
      h   height in metres, for 3D models only (see add_heights)
      src L = measured by 2009 LiDAR, P = placeholder
    """
    import json
    g = b[["object_id", "area_m2", "height_m", "height_source", "geometry"]].copy()
    g["geometry"] = g.geometry.simplify(SIMPLIFY_M, preserve_topology=True)
    g = g.to_crs(WGS84)
    feats = [{"type": "Feature",
              "properties": {"id": int(r["object_id"]), "a": round(float(r["area_m2"]), 1),
                             "h": float(r["height_m"]),
                             "src": "L" if r["height_source"] == "lidar_2009" else "P"},
              "geometry": round_coords(r.geometry.__geo_interface__)}
             for _, r in g.iterrows()]
    with open(WEB_BUILDINGS, "w") as fh:
        json.dump({"type": "FeatureCollection", "features": feats}, fh,
                  separators=(",", ":"))
    print(f"  map/data/{WEB_BUILDINGS.name:14s} "
          f"{WEB_BUILDINGS.stat().st_size / 1e6:6.1f} MB  ({len(feats):,} outlines)")


def round_coords(gj):
    """Round every coordinate to COORD_DECIMALS places."""
    def rnd(c):
        if isinstance(c[0], (int, float)):
            return [round(c[0], COORD_DECIMALS), round(c[1], COORD_DECIMALS)]
        return [rnd(x) for x in c]
    if gj["type"] == "GeometryCollection":
        # make_valid can leave stray lines; keep only the polygon parts.
        polys = [x for x in gj["geometries"] if x["type"] in ("Polygon", "MultiPolygon")]
        coords = []
        for x in polys:
            coords += [x["coordinates"]] if x["type"] == "Polygon" else list(x["coordinates"])
        return {"type": "MultiPolygon", "coordinates": rnd(coords)}
    return {"type": gj["type"], "coordinates": rnd(list(gj["coordinates"]))}


def summary(p):
    print("\n" + "=" * 78)
    print(" SUMMARY")
    print("=" * 78)
    large = p[p["scope"] == "large site"]
    merged_large = large[large["merged_site"]]
    print(f"  Set aside, not in any figure below:")
    print(f"    outside scope (large site, over {SCOPE_MAX_SITE_M2:,} m2)  "
          f"{len(large):>7,}  ({len(merged_large):,} of them merged sites)")
    print(f"    not a lot (rights-of-way, from Stage 1)      "
          f"{int((p['scope'] == 'not a lot').sum()):>7,}")
    print(f"\n  Largest merged sites (for checking -- all outside scope "
          f"unless marked):")
    for _, r in p[p["merged_site"]].nlargest(10, "lot_area_m2").iterrows():
        print(f"    {str(r['address']):<24}{r['lot_area_m2']:>12,.0f} m2  "
              f"{r['n_parcels']:>3} parcels  scope: {r['scope']}")
    p = p[p["scope"] == "in"]
    print(f"\n  ORDINARY R1-1 LOTS (sites up to {SCOPE_MAX_SITE_M2:,} m2)")
    print(f"  merged sites among them            "
          f"{int(p['merged_site'].sum()):>8,}")
    print(f"  shared address, not adjoining      "
          f"{int(p['site_flag'].notna().sum()):>8,}")
    has = p["building_count"] > 0
    print(f"  ordinary lots                      {len(p):>8,}")
    print(f"  with at least one building        {int(has.sum()):>8,}")
    print(f"  with no footprint at all          {int((~has).sum()):>8,}")
    print(f"  roofs over {CHECK_DATA_ROOF_SHARE:.0%} of the lot         "
          f"{int(p['check_data'].sum()):>8,}  (flagged check_data, listed below)")
    print(f"  median roof share (lots with roofs)"
          f"{p.loc[has, 'roof_share'].median():>8.1%}")

    print(f"\n  Lots where the ROOFS ALONE already exceed the hard surface the")
    print(f"  {DESIGN_RAINFALL_MM} mm storm allows (C = {RUNOFF_COEFF}):")
    print(f"    {'soil depth':>12}  {'max hard surface':>17}  {'roof_blocks':>12}")
    for d in D_EFF_OPTIONS_MM:
        k = dkey(d)
        if not achievable(d):
            print(f"    {d:>9g} mm  {'--':>17}  {'n/a':>12}  "
                  f"not achievable: soil holds less than the rain")
            continue
        share = 1 - perm_min_m2(1.0, d)
        n = int(p["roof_blocks" + k].sum())
        print(f"    {d:>9g} mm  {share:>16.1%}  {n:>12,}  "
              f"({n / len(p):.1%} of ordinary lots)")


def check_data_list(p):
    """Every lot flagged check_data, worst first."""
    flag = p[p["check_data"] & (p["scope"] == "in")].sort_values(
        "roof_share", ascending=False)
    print("\n" + "=" * 78)
    print(f" CHECK DATA: {len(flag)} lots with roofs over "
          f"{CHECK_DATA_ROOF_SHARE:.0%} of the lot")
    print("=" * 78)
    pts = flag.geometry.representative_point().to_crs(WGS84)
    for (_, r), pt in zip(flag.iterrows(), pts):
        note = (f"  merged site of {r['n_parcels']} parcels" if r["merged_site"]
                else f"  {r['site_flag']}" if r["site_flag"] else "")
        print(f"  {str(r['address']):<24}{r['lot_area_m2']:>8,.1f} m2 lot "
              f"{r['roof_area_m2']:>8,.1f} m2 roof {r['roof_share']:>6.1%}"
              f"   {pt.y:.6f}, {pt.x:.6f}{note}")


def check_lot(fp, parcels):
    """Every number for CHECK_ADDRESS -- even if it is not in R1-1."""
    num, street = CHECK_ADDRESS
    print("\n" + "=" * 78)
    print(f" CHECK LOT: {num} {street}")
    print("=" * 78)
    hit = parcels[parcels["address"] == f"{num} {street}"]
    if len(hit):
        lot = hit.iloc[0]
        in_r11 = True
    else:
        # Not in R1-1. Build its numbers the same way, from the raw parcel
        # layer, so the roof arithmetic can still be checked.
        raw = fetch("property-parcel-polygons",
                    select="site_id,civic_number,streetname,tax_coord")
        raw = raw[(raw["civic_number"] == num) & (raw["streetname"] == street)]
        if raw.empty:
            print("  not found in the City's parcel data")
            return
        raw = raw.to_crs(UTM10N).copy()
        raw["site_key"] = "CHECK"
        raw["address"] = f"{num} {street}"
        raw["lot_area_m2"] = raw.geometry.area
        mine = clip_buildings(fp, raw)
        lot = add_stormwater_fields(add_roof_fields(raw, mine)).iloc[0]
        in_r11 = False
        print("  NOTE: this lot is NOT in R1-1, so it is not in the output")
        print("  files. Numbers below use the same method, for checking only.")

    if in_r11:
        mine = clip_buildings(fp, hit.iloc[[0]])
    whole = fp.set_index("object_id").geometry.area
    P, C = DESIGN_RAINFALL_MM, RUNOFF_COEFF
    A = lot["lot_area_m2"]
    c = lot.geometry.representative_point()
    ll = gpd.GeoSeries([c], crs=UTM10N).to_crs(WGS84).iloc[0]
    print(f"  location            {ll.y:.6f}, {ll.x:.6f}")
    print(f"  lot_area_m2         {A:,.2f}")
    for _, b in mine.iterrows():
        print(f"    building {b['object_id']}: {b['area_m2']:,.2f} m2 on this "
              f"lot, of {whole[b['object_id']]:,.2f} m2 in total")
    print(f"  roof_area_m2        {lot['roof_area_m2']:,.2f}  "
          f"({int(lot['building_count'])} buildings)")
    print(f"  roof_share          {lot['roof_share']:.4f}  "
          f"= {lot['roof_area_m2']:,.2f} / {A:,.2f}")
    if in_r11:
        print(f"  Scenario A max impermeable (75%)   "
              f"{lot['a_impermeable_max_m2']:,.2f} m2")
        print(f"  Scenario B like-build estimate     "
              f"{lot['b_impermeable_likebuild_m2_est']} m2")
    for d in D_EFF_OPTIONS_MM:
        k = dkey(d)
        print(f"\n  soil holding depth {d:g} mm")
        if not achievable(d):
            print(f"    perm_min = {A:,.2f} x {P} x {C} / ({d} - {P} + {P}x{C})"
                  f" = {A * P * C / (d - P + P * C):,.2f} m2"
                  f" -- bigger than the lot")
            print(f"    NOT ACHIEVABLE: {d} mm < {P} mm")
            continue
        den = d - P + P * C
        print(f"    perm_min_m2    = {A:,.2f} x {P} x {C} / "
              f"({d} - {P} + {P * C:g}) = {A * P * C:,.1f} / {den:g} "
              f"= {lot['perm_min_m2' + k]:,.2f}")
        print(f"    max_imperv_m2  = {A:,.2f} - {lot['perm_min_m2' + k]:,.2f} "
              f"= {lot['max_imperv_m2' + k]:,.2f}")
        print(f"    roof_blocks    = {lot['roof_area_m2']:,.2f} > "
              f"{lot['max_imperv_m2' + k]:,.2f} -> {bool(lot['roof_blocks' + k])}")


def random_lots(p):
    """Random ordinary lots with buildings, for checking against aerials."""
    print("\n" + "=" * 78)
    print(f" {RANDOM_LOTS} RANDOM LOTS (seed {RANDOM_SEED}) -- check roofs "
          f"against aerial photos")
    print("=" * 78)
    pool = p[(p["building_count"] > 0) & (p["scope"] == "in")
             & p["address"].notna()]
    pick = pool.sample(RANDOM_LOTS, random_state=RANDOM_SEED)
    pts = pick.geometry.representative_point().to_crs(WGS84)
    print(f"  {'address':<24}{'lot m2':>8}{'roof m2':>9}{'share':>7}"
          f"{'bldgs':>6}   lat, lon")
    for (_, r), pt in zip(pick.iterrows(), pts):
        print(f"  {r['address']:<24}{r['lot_area_m2']:>8,.0f}"
              f"{r['roof_area_m2']:>9,.1f}{r['roof_share']:>7.0%}"
              f"{r['building_count']:>6}   {pt.y:.6f}, {pt.x:.6f}")


if __name__ == "__main__":
    main()
