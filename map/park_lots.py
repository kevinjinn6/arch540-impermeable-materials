"""
================================================================================
 LOTS THAT ARE PARK LAND  --  writes map/data/park-lots.json
================================================================================

WHY THIS EXISTS
  Some park land is zoned R1-1, so the City's parcels put a few dozen "lots"
  inside parks (Ravine Park, Renfrew Ravine, Bates Park, Rosemary Brown
  Park...) with no building on them; they are not house lots. Kevin's call,
  2026-10-11: take them out of the count, like the other grey lots.

WHAT IT DOES
  Reads map/data/lots.geojson and map/data/parks.geojson (the City's park
  outlines), and lists every site with more than PARK_SHARE of its area
  inside a park AND no 2015 roof on it, with the park's name (a site with a
  building stays a lot: the park outline may simply run over a house):
      {"share": 0.5, "n": 156, "lots": {"R11-000123": "Ravine Park", ...}}
  The page reads that file and draws those lots as not assessed ("park
  land"). The park layer is drawn over them, so on the map they read green.

HOW TO RUN IT
     source .venv/bin/activate          (the geopandas environment)
     python map/park_lots.py
  Takes a few seconds. Re-run if lots.geojson or parks.geojson changes.
================================================================================
"""

import json
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapely

# ==============================================================================
#  CONFIGURATION
# ==============================================================================
PARK_SHARE = 0.5     # a site more than half inside a park is park land
UTM10N = 26910       # metres; the projection every area in this project uses
HERE = Path(__file__).resolve().parent
LOTS = HERE / "data" / "lots.geojson"
PARKS = HERE / "data" / "parks.geojson"
OUT = HERE / "data" / "park-lots.json"
NOT_A_SITE_M2 = 150  # same rule as the page, for the report below only
# ==============================================================================


def main():
    lots = gpd.read_file(LOTS).to_crs(UTM10N)
    parks = gpd.read_file(PARKS).to_crs(UTM10N)
    lots["geometry"] = shapely.make_valid(lots.geometry.values)
    parks["geometry"] = shapely.make_valid(parks.geometry.values)
    pairs = gpd.sjoin(lots[["k", "geometry"]], parks[["n", "geometry"]], how="inner", predicate="intersects")
    li = pairs.index.values
    pi = pairs["index_right"].values
    pairs["inside"] = shapely.area(shapely.intersection(lots.geometry.values[li], parks.geometry.values[pi]))
    # A site touching two parks: add both shares, name the park holding most of it.
    pairs = pairs.sort_values("inside", ascending=False)
    per = pairs.groupby("k").agg(inside=("inside", "sum"), park=("n", "first"))
    area = lots.set_index("k").geometry.area
    per["share"] = per["inside"] / area.reindex(per.index).values
    roof = lots.set_index("k")["r"].astype(float).reindex(per.index).fillna(0)
    built = per[(per["share"] > PARK_SHARE) & (roof > 0)]
    hit = per[(per["share"] > PARK_SHARE) & (roof == 0)]
    OUT.write_text(json.dumps({"share": PARK_SHARE,
                               "source": "map/data/lots.geojson sites with no roof and more than `share` inside map/data/parks.geojson",
                               "n": int(len(hit)),
                               "lots": {k: n for k, n in hit["park"].items()}}, separators=(",", ":")))
    p = lots.set_index("k")
    assessed = (p["sc"] == 0) & ~p.get("cd", pd.Series(0, index=p.index)).fillna(0).astype(bool) \
        & ~p.get("f", pd.Series(0, index=p.index)).fillna(0).astype(bool) & (p["A"] >= NOT_A_SITE_M2)
    print(f"wrote {OUT.relative_to(HERE.parent)}: {len(hit)} sites more than {PARK_SHARE:.0%} inside a park, "
          f"no roof; {int(assessed.reindex(hit.index).sum())} of them were counted as house lots")
    for k in built.index[assessed.reindex(built.index).values]:
        print(f"  still a house lot (has a roof): {p.at[k, 'ad'] or k}, {built.at[k, 'park']}")


if __name__ == "__main__":
    sys.exit(main())
