"""
================================================================================
 LAND THAT IS NOT R1-1  --  writes map/data/not-r11.geojson
================================================================================

WHY THIS EXISTS
  The map holds only R1-1 sites, so land in other zones (apartments, shops,
  duplex districts, industry) is simply blank. Blank reads as missing data.
  This file is the city's land minus the R1-1 zoning districts; the page draws
  it as a light grey wash labelled "Not R1-1", so the blanks read as outside
  this study.

WHAT IT READS
  cache/zoning-districts-and-labels-*.geojson   the R1-1 zoning districts (City
                                                open data, cached by buildings.py)
  cache/local-area-boundary.geojson              the city's 22 local areas (City
                                                open data "local-area-boundary");
                                                downloaded here if missing. Their
                                                union is the city's land.

WHAT IT WRITES
  map/data/not-r11.geojson   one MultiPolygon: the city's land outside R1-1.

HOW TO RUN IT
     source .venv/bin/activate          (the geopandas environment)
     python map/not_r11.py
  Takes a few seconds. Re-run if the zoning changes.
================================================================================
"""

import json
import urllib.request
from pathlib import Path

import numpy as np
import shapely
from pyproj import Transformer

# ==============================================================================
#  CONFIGURATION
# ==============================================================================
ROOT = Path(__file__).resolve().parent.parent
ZONING = sorted((ROOT / "cache").glob("zoning-districts-and-labels-*.geojson"))
AREAS = ROOT / "cache" / "local-area-boundary.geojson"
AREAS_URL = ("https://opendata.vancouver.ca/api/explore/v2.1/catalog/datasets/"
             "local-area-boundary/exports/geojson")
OUT = ROOT / "map" / "data" / "not-r11.geojson"
SIMPLIFY_M = 2.0     # outlines are smoothed to this, m: finer than a lot, small file
SLIVER_M2 = 200      # pieces smaller than this (slivers between two outlines) are dropped
UTM10N = 26910       # metres; the projection every area in this project uses
# ==============================================================================


def to_metres(geom):
    to_m = Transformer.from_crs(4326, UTM10N, always_xy=True)
    return shapely.transform(geom, lambda xy: np.column_stack(to_m.transform(xy[:, 0], xy[:, 1])))


def to_lonlat(geom):
    to_ll = Transformer.from_crs(UTM10N, 4326, always_xy=True)
    return shapely.transform(geom, lambda xy: np.column_stack(to_ll.transform(xy[:, 0], xy[:, 1])))


def read(path):
    """A GeoJSON file's polygons, merged into one shape, in metres."""
    geoms = [shapely.geometry.shape(f["geometry"]) for f in json.load(open(path))["features"]]
    return to_metres(shapely.union_all(geoms))


def main():
    if not ZONING:
        raise SystemExit("No zoning file in cache/: run buildings.py first.")
    if not AREAS.exists():
        print(f"Downloading the local areas from {AREAS_URL}")
        AREAS.write_bytes(urllib.request.urlopen(AREAS_URL).read())
    land = read(AREAS)
    r11 = read(ZONING[-1])
    rest = shapely.difference(land, r11).simplify(SIMPLIFY_M)
    parts = [g for g in getattr(rest, "geoms", [rest]) if g.area >= SLIVER_M2]
    rest = shapely.MultiPolygon(parts)
    print(f"City land {land.area / 1e6:.1f} km², R1-1 {r11.area / 1e6:.1f} km², "
          f"not R1-1 {rest.area / 1e6:.1f} km² in {len(parts)} pieces")

    rest = shapely.set_precision(to_lonlat(rest), 1e-6)
    OUT.write_text(json.dumps({"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {}, "geometry": json.loads(shapely.to_geojson(rest))}]},
        separators=(",", ":")))
    print(f"Wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1e3:.0f} KB)")


if __name__ == "__main__":
    main()
