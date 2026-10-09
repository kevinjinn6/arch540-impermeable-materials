"""
================================================================================
 GROUND ELEVATION TILES FOR THE SHADED RELIEF  --  writes map/data/terrain/
================================================================================

WHY THIS EXISTS
  The map shows the lie of the land as a soft shaded relief, so a reader can
  see which lots sit on a slope, a ridge or a hollow. The relief is drawn by
  MapLibre itself from ground heights, so its light direction and strength
  can be changed in map/index.html without re-running this script.

WHAT IT READS
  DEM_2013.tif in the project folder: the City of Vancouver's 2013 digital
  elevation model. A 0.5 m grid of BARE-EARTH ground heights in metres (the
  buildings have been removed), NAD83 / UTM zone 10N, -9999 = no data
  (outside the city). It is 1.9 GB and is NOT committed; only the tiles are.

WHAT IT WRITES
  map/data/terrain/{z}/{x}/{y}.png  -- standard web-map tiles, 256 x 256 px,
  zoom MIN_ZOOM to MAX_ZOOM, in the "Terrain-RGB" encoding MapLibre reads:
      height (m) = -10000 + (R * 65536 + G * 256 + B) * 0.1

  THE HEIGHTS IN THE TILES ARE EXAGGERATED. Every height is multiplied by
  VERTICAL_EXAGGERATION before it is written, because Vancouver's ground is
  gentle (most residential streets slope 2-8%) and at true scale MapLibre's
  relief is too faint to see. To read a real height from a tile, divide by
  VERTICAL_EXAGGERATION. The tiles are a picture: no figure uses them.

  Outside the city the DEM is empty. Those pixels are filled with a smooth
  surface spread outward from the nearest real ground, so the relief has no
  false cliff at the city boundary. The fill is invented: it is drawn only to
  keep the edge clean, and it is flat-looking on purpose.

HOW TO RUN IT
     source .venv/bin/activate
     pip install tifffile imagecodecs pillow      (once)
     python map/terrain_tiles.py
  Takes about a minute and 12 GB of memory (the whole DEM is read at
  once). Re-run only if the DEM or the zoom range changes.
================================================================================
"""

import math
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import tifffile
from PIL import Image
from pyproj import Transformer

ROOT = Path(__file__).resolve().parent.parent
DEM_FILE = ROOT / "DEM_2013.tif"
OUT_DIR = ROOT / "map" / "data" / "terrain"

# ---- Settings ------------------------------------------------------------------
MIN_ZOOM = 10        # whole-city view; below this the page draws no relief
MAX_ZOOM = 15        # finest tiles: about 3 m per pixel at Vancouver's latitude.
                     # MapLibre stretches these smoothly when you zoom in further.
TILE_PX = 256        # pixels per tile side, the web-map standard
VERTICAL_EXAGGERATION = 5   # heights are multiplied by this so gentle slopes show;
                            # 1 = true scale (too faint), higher = stronger relief
NODATA = -9999.0     # the DEM's "no data" value (outside the city)

# The DEM's grid, from its own header (GeoTIFF tags):
DEM_LEFT_X = 483639.1      # UTM easting of the grid's left edge, m
DEM_TOP_Y = 5463000.43     # UTM northing of the grid's top edge, m
DEM_CELL_M = 0.5           # one DEM pixel is 0.5 m x 0.5 m

# Web-map maths: the Earth's circumference on the web-map sphere, m
WORLD_M = 2 * math.pi * 6378137.0


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def block_mean(a, f):
    """Average f x f blocks of pixels, ignoring empty (NaN) ones.
    A block with no ground at all stays empty."""
    h, w = (a.shape[0] // f) * f, (a.shape[1] // f) * f
    b = a[:h, :w].reshape(h // f, f, w // f, f)
    valid = ~np.isnan(b)
    n = valid.sum(axis=(1, 3))
    s = np.where(valid, b, 0).sum(axis=(1, 3), dtype=np.float64)
    out = np.full(n.shape, np.nan, dtype=np.float32)
    np.divide(s, n, out=out, where=n > 0, casting="unsafe")
    return out


def blur3(a):
    """Average each pixel with its 8 neighbours (edges repeat)."""
    p = np.pad(a, 1, mode="edge")
    return sum(p[i:i + a.shape[0], j:j + a.shape[1]] for i in range(3) for j in range(3)) / 9


def fill_empty(a):
    """Fill empty pixels with a smooth surface spread from the nearest ground.
    Coarse-to-fine: halve the grid until nothing is empty, then work back up,
    filling each level from the one above and smoothing only the filled pixels
    so no steps show in the relief."""
    empty = np.isnan(a)
    if not empty.any():
        return a
    small = fill_empty(block_mean(np.pad(a, ((0, a.shape[0] % 2), (0, a.shape[1] % 2)), mode="edge"), 2))
    up = np.repeat(np.repeat(small, 2, axis=0), 2, axis=1)[:a.shape[0], :a.shape[1]]
    out = np.where(empty, up, a)
    for _ in range(4):
        out = np.where(empty, blur3(out), a)
    return out.astype(np.float32)


def main():
    if not DEM_FILE.exists():
        sys.exit(f"{DEM_FILE.name} not found in the project folder.")
    log(f"Reading {DEM_FILE.name} (1.9 GB)…")
    dem = tifffile.imread(DEM_FILE).astype(np.float32)
    dem[dem <= NODATA + 1] = np.nan
    rows, cols = dem.shape
    log(f"  {cols} x {rows} pixels at {DEM_CELL_M} m; {np.isnan(dem).mean():.0%} outside the city")

    # A pyramid of coarser grids (1 m, 2 m, 4 m, …), each the average of the
    # one below. Each zoom samples the grid just finer than its own pixel, so
    # the relief is neither jagged nor blurred.
    levels = {}
    cell, grid = DEM_CELL_M * 2, block_mean(dem, 2)
    del dem
    while True:
        levels[cell] = fill_empty(grid)
        log(f"  {cell:g} m grid ready")
        if cell >= 64:
            break
        grid = block_mean(grid, 2)
        cell *= 2

    to_utm = Transformer.from_crs("EPSG:3857", "EPSG:26910", always_xy=True)
    to_merc = Transformer.from_crs("EPSG:26910", "EPSG:3857", always_xy=True)
    # The DEM's corners on the web map, to know which tiles to make.
    xs, ys = to_merc.transform(
        [DEM_LEFT_X, DEM_LEFT_X + cols * DEM_CELL_M] * 2,
        [DEM_TOP_Y, DEM_TOP_Y, DEM_TOP_Y - rows * DEM_CELL_M, DEM_TOP_Y - rows * DEM_CELL_M])
    mx0, mx1, my0, my1 = min(xs), max(xs), min(ys), max(ys)

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    total_tiles = total_bytes = 0
    for z in range(MIN_ZOOM, MAX_ZOOM + 1):
        n = 2 ** z
        tile_m = WORLD_M / n                       # one tile's width on the web map, m
        px_ground = tile_m / TILE_PX * math.cos(math.radians(49.25))   # real metres per pixel here
        cell = max([c for c in levels if c <= px_ground] or [min(levels)])
        grid = levels[cell]
        tx0 = int((mx0 + WORLD_M / 2) // tile_m)
        tx1 = int((mx1 + WORLD_M / 2) // tile_m)
        ty0 = int((WORLD_M / 2 - my1) // tile_m)
        ty1 = int((WORLD_M / 2 - my0) // tile_m)
        count = 0
        for tx in range(tx0, tx1 + 1):
            for ty in range(ty0, ty1 + 1):
                # The centre of every pixel in this tile, on the web map, then in UTM.
                i = (np.arange(TILE_PX) + 0.5) / TILE_PX
                px = -WORLD_M / 2 + (tx + i) * tile_m
                py = WORLD_M / 2 - (ty + i) * tile_m
                gx, gy = np.meshgrid(px, py)
                ux, uy = to_utm.transform(gx, gy)
                # Bilinear sample of the chosen grid (cell centres at half a cell in).
                c = (ux - DEM_LEFT_X) / cell - 0.5
                r = (DEM_TOP_Y - uy) / cell - 0.5
                c = np.clip(c, 0, grid.shape[1] - 1.001)
                r = np.clip(r, 0, grid.shape[0] - 1.001)
                c0, r0 = c.astype(int), r.astype(int)
                fc, fr = c - c0, r - r0
                h = (grid[r0, c0] * (1 - fc) * (1 - fr) + grid[r0, c0 + 1] * fc * (1 - fr)
                     + grid[r0 + 1, c0] * (1 - fc) * fr + grid[r0 + 1, c0 + 1] * fc * fr)
                # Terrain-RGB: 0.1 m steps from -10,000 m, after exaggerating.
                v = np.round((h * VERTICAL_EXAGGERATION + 10000) * 10).astype(np.int64)
                rgb = np.stack([v // 65536, (v // 256) % 256, v % 256], axis=-1).astype(np.uint8)
                path = OUT_DIR / str(z) / str(tx) / f"{ty}.png"
                path.parent.mkdir(parents=True, exist_ok=True)
                Image.fromarray(rgb).save(path, optimize=True)
                total_bytes += path.stat().st_size
                count += 1
        total_tiles += count
        log(f"  zoom {z}: {count} tiles from the {cell:g} m grid")

    # The extent, for the page's source "bounds" (so it asks for no tiles outside).
    lon, lat = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True).transform([mx0, mx1], [my0, my1])
    log(f"Done: {total_tiles} tiles, {total_bytes / 1e6:.1f} MB in {OUT_DIR.relative_to(ROOT)}")
    log(f"Bounds for the page: [{lon[0]:.5f}, {lat[0]:.5f}, {lon[1]:.5f}, {lat[1]:.5f}]")


if __name__ == "__main__":
    main()
