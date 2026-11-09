"""Which lots each low spot's water covers, for the Water view's red "flooded lots".

Reads map/data/low-spots.geojson (from water_layers.py) and map/data/lots.geojson, and writes
map/data/spot-lots.json: { "<low spot id>": ["<lot k>", ...] }. A lot counts when the low
spot's outline covers at least MIN_M2 of it. The map draws these lots in red whenever their
low spot floods (fills to 15 cm) in the storm on the Water card.

Run after water_layers.py:  .venv/bin/python map/spot_lots.py   (a few seconds)
"""
import json
import math
from pathlib import Path

from shapely import STRtree
from shapely.geometry import shape
from shapely.ops import transform

MIN_M2 = 4.0          # one 2 m DEM cell: less than that is a sliver along a lot line

DATA = Path(__file__).resolve().parent / "data"
LAT0 = 49.25          # Vancouver: degrees -> metres, good to well under 1% across the city
KX = 111_320 * math.cos(math.radians(LAT0))
KY = 110_574


def metres(g):
    return transform(lambda x, y, z=None: (x * KX, y * KY), g)


def main():
    lots = json.loads((DATA / "lots.geojson").read_text())["features"]
    spots = json.loads((DATA / "low-spots.geojson").read_text())["features"]
    lot_geoms = [metres(shape(f["geometry"])).buffer(0) for f in lots]
    keys = [f["properties"]["k"] for f in lots]
    tree = STRtree(lot_geoms)
    out, touched = {}, set()
    for f in spots:
        g = metres(shape(f["geometry"])).buffer(0)
        hit = [keys[i] for i in tree.query(g, predicate="intersects")
               if lot_geoms[i].intersection(g).area >= MIN_M2]
        if hit:
            out[str(f["id"])] = hit
            touched.update(hit)
    (DATA / "spot-lots.json").write_text(json.dumps(out, separators=(",", ":")))
    print(f"{len(out)} of {len(spots)} low spots cover a lot; {len(touched)} lots in all.")


if __name__ == "__main__":
    main()
