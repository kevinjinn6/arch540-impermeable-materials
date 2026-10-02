"""
================================================================================
 ROOF AREA TO THE WALLS, PER SITE  --  writes map/data/roof-walls.json
================================================================================

WHY THIS EXISTS
  The City's 2015 building footprints were traced from air photos and follow
  the ROOF EDGE. The by-law measures a building to "the outside of the
  outermost walls" (Section 2, "Impermeable Materials"), and eaves are not
  walls. A Vancouver house roof overhangs by about 0.3-0.6 m, which is 11-22%
  of a typical roof's area. Measured to the roof edge, about 13,600 ordinary
  R1-1 sites read over the 50% building limit; to the walls at 0.45 m, under
  800. The web page shows both figures and tests against the walls.

WHAT IT DOES
  Reads map/data/buildings.geojson and map/data/lots.geojson (the published
  map data), shrinks every footprint inwards by EAVE_M, clips it to the
  sites, sums per site, and writes map/data/roof-walls.json:
      {"eave_m": 0.45, "n": 63031, "rw": {"R11-000000": 812.4, ...}}
  The page reads that file; map/rhino_site.py reads it too, so the drawing
  and the page agree to the square metre.

HOW TO RUN IT
     source .venv/bin/activate          (the geopandas environment)
     python map/roof_walls.py
  Takes about ten seconds. Re-run after buildings.py regenerates the data.
  (buildings.py can also write rw straight into lots.geojson; the page uses
  that when present and this file otherwise.)
================================================================================
"""

import json
import sys
import time
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

# ==============================================================================
#  CONFIGURATION
# ==============================================================================
EAVE_M = 0.45        # metres taken off every roof edge; same as map/index.html
UTM10N = 26910       # metres; the projection every area in this project uses
HERE = Path(__file__).resolve().parent
LOTS = HERE / "data" / "lots.geojson"
BUILDINGS = HERE / "data" / "buildings.geojson"
OUT = HERE / "data" / "roof-walls.json"
# ==============================================================================


def main():
    t0 = time.time()
    lots = gpd.read_file(LOTS).to_crs(UTM10N)
    bld = gpd.read_file(BUILDINGS).to_crs(UTM10N)
    lots["geometry"] = shapely.make_valid(lots.geometry.values)
    # Shrink first, clip second: a building cut by a lot line loses an eave
    # strip along its roof edge only, not along the lot line.
    bld["geometry"] = shapely.make_valid(bld.geometry.buffer(-EAVE_M, join_style=2).values)
    bld = bld[~bld.geometry.is_empty & (bld.geometry.area > 0)].reset_index(drop=True)
    pairs = gpd.sjoin(bld[["geometry"]], lots[["k", "geometry"]], how="inner", predicate="intersects")
    bi = pairs.index.values
    li = pairs["index_right"].values
    area = shapely.area(shapely.intersection(bld.geometry.values[bi], lots.geometry.values[li]))
    per = pd.Series(area).groupby(pairs["k"].values).sum()
    df = lots.set_index("k")[["A", "r", "sc"]].copy()
    # The allowance can only make a roof smaller, never larger.
    df["rw"] = np.minimum(per.reindex(df.index).fillna(0).values, df["r"].values).round(2)
    out = {"eave_m": EAVE_M,
           "source": "map/data/buildings.geojson (2015 footprints) shrunk inwards by eave_m, "
                     "clipped to map/data/lots.geojson, summed per site",
           "n": int(len(df)),
           "rw": {k: float(v) for k, v in df["rw"].items()}}
    OUT.write_text(json.dumps(out, separators=(",", ":")))
    ins = df[df["sc"] == 0]
    print(f"wrote {OUT.relative_to(HERE.parent)}  ({OUT.stat().st_size / 1e6:.2f} MB, {time.time() - t0:.0f} s)")
    print(f"ordinary sites over 50%: {int((ins.r / ins.A > 0.5).sum()):,} to the roof edge, "
          f"{int((ins.rw / ins.A > 0.5).sum()):,} to the walls at {EAVE_M} m")
    print(f"ordinary sites over 75%: {int((ins.r / ins.A > 0.75).sum()):,} to the roof edge, "
          f"{int((ins.rw / ins.A > 0.75).sum()):,} to the walls")
    print(f"eave share of all roof area: {1 - ins.rw.sum() / ins.r.sum():.1%}")


if __name__ == "__main__":
    sys.exit(main())
