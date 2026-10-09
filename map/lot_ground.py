"""
================================================================================
 GROUND HEIGHT UNDER EVERY LOT CORNER  --  writes map/data/lot-ground.bin
================================================================================

WHY THIS EXISTS
  In the map's 3D view the lots are drawn by the page's own graphics code
  (so the slider can colour them), and MapLibre does not lay that kind of
  layer on its 3D ground. So each lot corner is given its ground height here,
  and the page lifts it to that height.

WHAT IT WRITES
  map/data/lot-ground.bin: one number per corner of every lot outline, in the
  order the page reads them (lots.geojson, feature by feature, polygon by
  polygon, ring by ring, point by point). Each is a 16-bit whole number of
  DECIMETRES (0.1 m) above sea level, little-endian. The page checks the
  count against lots.geojson and refuses a file that does not match.

  The heights come from the same 2 m grid as the finest terrain tiles
  (terrain_tiles.py), so the lots sit on the ground MapLibre draws.

HOW TO RUN IT
     source .venv/bin/activate
     python map/lot_ground.py
  About a minute and 12 GB of memory. Re-run whenever lots.geojson changes.
================================================================================
"""

import json

import numpy as np
import tifffile
from pyproj import Transformer

from terrain_tiles import DEM_CELL_M, DEM_FILE, DEM_LEFT_X, DEM_TOP_Y, NODATA, ROOT, block_mean, fill_empty, log

LOTS_FILE = ROOT / "map" / "data" / "lots.geojson"
OUT_FILE = ROOT / "map" / "data" / "lot-ground.bin"
GRID_M = 2.0          # sample the 2 m grid, as the finest terrain tiles do


def main():
    log(f"Reading {DEM_FILE.name}…")
    dem = tifffile.imread(DEM_FILE).astype(np.float32)
    dem[dem <= NODATA + 1] = np.nan
    f = int(round(GRID_M / DEM_CELL_M))
    grid = fill_empty(block_mean(block_mean(dem, 2), f // 2))
    del dem
    log(f"  {GRID_M:g} m grid ready")

    lots = json.load(open(LOTS_FILE))["features"]
    lon, lat = [], []
    for feat in lots:
        g = feat["geometry"]
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"] if g["type"] == "MultiPolygon" else []
        for rings in polys:
            for ring in rings:
                for x, y in ring:
                    lon.append(x)
                    lat.append(y)
    ux, uy = Transformer.from_crs("EPSG:4326", "EPSG:26910", always_xy=True).transform(lon, lat)
    c = np.clip((np.asarray(ux) - DEM_LEFT_X) / GRID_M - 0.5, 0, grid.shape[1] - 1.001)
    r = np.clip((DEM_TOP_Y - np.asarray(uy)) / GRID_M - 0.5, 0, grid.shape[0] - 1.001)
    c0, r0 = c.astype(int), r.astype(int)
    fc, fr = c - c0, r - r0
    h = (grid[r0, c0] * (1 - fc) * (1 - fr) + grid[r0, c0 + 1] * fc * (1 - fr)
         + grid[r0 + 1, c0] * (1 - fc) * fr + grid[r0 + 1, c0 + 1] * fc * fr)
    np.round(h * 10).astype("<i2").tofile(OUT_FILE)
    log(f"Done: {len(h):,} corners of {len(lots):,} lots, {h.min():.1f} to {h.max():.1f} m, "
        f"{OUT_FILE.stat().st_size / 1e6:.1f} MB in {OUT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
