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
  surface spread outward from the nearest real ground, so the 3D view has no
  false cliff at the city boundary. The fill is invented, and it now reaches
  past the DEM's rectangle too, easing down to 0 m within FADE_M: before
  2026-10-11 the edge rows were repeated out there, which drew long streaks
  east of Boundary Road, and the 3D ground ended in a wall.

  map/data/relief/{z}/{x}/{y}.png  -- the SHADED RELIEF itself, drawn here
  rather than by MapLibre so it can stop exactly where the DEM's real ground
  stops (the city boundary): a see-through picture, dark on slopes facing away
  from the light and pale on slopes facing it, transparent elsewhere. It uses
  MapLibre's own hillshade arithmetic with the settings in RELIEF below, so it
  looks as the page's relief did, minus the invented ground outside the city.

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
DEM_FILE = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "DEM_2013.tif"   # or give its path
OUT_DIR = ROOT / "map" / "data" / "terrain"
RELIEF_DIR = ROOT / "map" / "data" / "relief"

# ---- Settings ------------------------------------------------------------------
MIN_ZOOM = 10        # whole-city view; below this the page draws no relief
MAX_ZOOM = 15        # finest tiles: about 3 m per pixel at Vancouver's latitude.
                     # MapLibre stretches these smoothly when you zoom in further.
TILE_PX = 256        # pixels per tile side, the web-map standard
VERTICAL_EXAGGERATION = 5   # heights are multiplied by this so gentle slopes show;
                            # 1 = true scale (too faint), higher = stronger relief
NODATA = -9999.0     # the DEM's "no data" value (outside the city)
EDGE_TRIM_M = 30     # the City's DEM ramps down to about 0 m over its last ~25 m wherever its
                     # ground reaches the edge of its rectangle (east of Boundary Road): that
                     # ramp drew a dark line in the relief and a wall in 3D, so this much of
                     # the rectangle's edge is treated as no data. No R1-1 lot is that close.
FADE_M = 1500        # past the DEM's rectangle the invented ground eases down to 0 m over this
                     # many metres, and tiles are made out that far: beyond them MapLibre's 3D
                     # ground is 0 m, so ending at 0 m leaves no wall at the edge
PAD_CELLS = 260      # each grid is extended by FADE_M plus this many cells of smooth fill on
                     # every side, more than a tile reaches past the area tiles are made for

# The shaded relief, as index.html drew it with MapLibre until 2026-10-11 (its RELIEF settings):
RELIEF = {
    "strength": 0.6,              # MapLibre's hillshade-exaggeration, 0-1
    "light_from_deg": 315,        # the light comes from the northwest, the cartographic convention
    "shadow": (40, 30, 20, 0.6),  # colour (0-255) and opacity of a slope facing away from the light
    "highlight": (255, 255, 255, 0.4),  # ... and of a slope facing it
}

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


def bilinear(grid, r, c):
    """Sample a grid at fractional rows r and columns c (clamped to the grid)."""
    c = np.clip(c, 0, grid.shape[1] - 1.001)
    r = np.clip(r, 0, grid.shape[0] - 1.001)
    c0, r0 = c.astype(int), r.astype(int)
    fc, fr = c - c0, r - r0
    return (grid[r0, c0] * (1 - fc) * (1 - fr) + grid[r0, c0 + 1] * fc * (1 - fr)
            + grid[r0 + 1, c0] * (1 - fc) * fr + grid[r0 + 1, c0 + 1] * fc * fr)


def hillshade(h, z, tile):
    """MapLibre 4.7's hillshade, worked out here (its hillshade_prepare and hillshade shaders):
    h = heights in metres for a tile plus a one-pixel ring, as in the terrain tiles. Returns
    the shade (0 = shadow colour, 1 = highlight colour) and the amount (0-1, how strongly it
    shows) of every pixel of the 256 x 256 tile."""
    tx, ty, n = tile
    # Slope from the 3 x 3 neighbours (a Sobel filter), scaled for the zoom as MapLibre does
    # (its shader reads every height divided by 4).
    h = h / 4.0
    a, b, c = h[:-2, :-2], h[:-2, 1:-1], h[:-2, 2:]
    d, f = h[1:-1, :-2], h[1:-1, 2:]
    g, hh, i = h[2:, :-2], h[2:, 1:-1], h[2:, 2:]
    zoom_exag = (z - 15) * 0.3 if z < 15 else 0.0
    scale = 2.0 ** (zoom_exag + (19.2562 - z))
    dx = np.clip(((c + f + f + i) - (a + d + d + g)) / scale, -1, 1)
    dy = np.clip(((g + hh + hh + i) - (a + b + b + c)) / scale, -1, 1)
    # Each pixel row's latitude, for the slope's north-south stretch on the web map.
    yrow = ty + (np.arange(TILE_PX) + 0.5) / TILE_PX
    lat = np.degrees(np.arctan(np.sinh(math.pi * (1 - 2 * yrow / n))))[:, None]
    slope = np.arctan(1.25 * np.hypot(dx, dy) / np.cos(np.radians(lat)))
    aspect = np.where(dx != 0, np.arctan2(dy, -dx), math.pi / 2 * np.where(dy > 0, 1.0, -1.0))
    k = RELIEF["strength"]
    azimuth = math.radians(RELIEF["light_from_deg"]) + math.pi
    base = 1.875 - k * 1.75
    half_pi = 0.5 * math.pi
    scaled = ((base ** slope - 1) / (base ** half_pi - 1)) * half_pi if k != 0.5 else slope
    shade = np.abs(np.mod((aspect + azimuth) / math.pi + 0.5, 2.0) - 1.0)
    return shade, np.sin(scaled) * min(1.0, k * 2)


# The relief tiles are 256-colour PNGs: SHADES steps from shadow to highlight, AMOUNTS steps of
# strength (finer near zero, where gentle slopes are). About a fifth the size of full colour.
SHADES, AMOUNTS = 8, 32


def relief_palette():
    """The 256 colours: shadow and highlight as premultiplied colours, mixed by the shade and
    scaled by the amount, as MapLibre's shader does; stored straight (not premultiplied)."""
    pre = lambda col: np.array([col[0] / 255 * col[3], col[1] / 255 * col[3], col[2] / 255 * col[3], col[3]])
    s, hl = pre(RELIEF["shadow"]), pre(RELIEF["highlight"])
    rgb, alpha = [], []
    for t in range(SHADES):
        for q in range(AMOUNTS):
            c = (s + (hl - s) * t / (SHADES - 1)) * (q / (AMOUNTS - 1)) ** 2
            a = c[3]
            rgb += [int(round(v / a * 255)) if a > 1e-6 else 0 for v in c[:3]]
            alpha.append(int(round(a * 255)))
    return rgb, bytes(alpha)


PALETTE = relief_palette()


def relief_image(shade, amount):
    idx = np.round(shade * (SHADES - 1)).astype(np.uint8) * AMOUNTS + \
          np.round(np.sqrt(np.clip(amount, 0, 1)) * (AMOUNTS - 1)).astype(np.uint8)
    im = Image.fromarray(idx)
    im.putpalette(PALETTE[0])
    return im


def main():
    if not DEM_FILE.exists():
        sys.exit(f"{DEM_FILE.name} not found in the project folder.")
    log(f"Reading {DEM_FILE.name} (1.9 GB)…")
    dem = tifffile.imread(DEM_FILE).astype(np.float32)
    dem[dem <= NODATA + 1] = np.nan
    t = int(EDGE_TRIM_M / DEM_CELL_M)
    dem[:t, :] = dem[-t:, :] = np.nan
    dem[:, :t] = dem[:, -t:] = np.nan
    rows, cols = dem.shape
    log(f"  {cols} x {rows} pixels at {DEM_CELL_M} m; {np.isnan(dem).mean():.0%} outside the city")

    # A pyramid of coarser grids (1 m, 2 m, 4 m, …), each the average of the
    # one below. Each zoom samples the grid just finer than its own pixel, so
    # the relief is neither jagged nor blurred.
    # Alongside each, the share of real (not filled) ground in each cell, for the relief's edge.
    levels, valid_levels, pads = {}, {}, {}
    cell, grid = DEM_CELL_M * 2, block_mean(dem, 2)
    valid = block_mean((~np.isnan(dem)).astype(np.float32), 2)
    del dem
    while True:
        pads[cell] = pad = math.ceil(FADE_M / cell) + PAD_CELLS
        levels[cell] = fill_empty(np.pad(grid, pad, constant_values=np.nan))
        valid_levels[cell] = np.pad(valid, pad, constant_values=0)
        log(f"  {cell:g} m grid ready")
        if cell >= 64:
            break
        grid = block_mean(grid, 2)
        valid = block_mean(valid, 2)
        cell *= 2

    to_utm = Transformer.from_crs("EPSG:3857", "EPSG:26910", always_xy=True)
    to_merc = Transformer.from_crs("EPSG:26910", "EPSG:3857", always_xy=True)
    # The DEM's corners on the web map, to know which tiles to make.
    xs, ys = to_merc.transform(
        [DEM_LEFT_X, DEM_LEFT_X + cols * DEM_CELL_M] * 2,
        [DEM_TOP_Y, DEM_TOP_Y, DEM_TOP_Y - rows * DEM_CELL_M, DEM_TOP_Y - rows * DEM_CELL_M])
    mx0, mx1, my0, my1 = min(xs), max(xs), min(ys), max(ys)
    dem_box = (DEM_LEFT_X, DEM_LEFT_X + cols * DEM_CELL_M, DEM_TOP_Y - rows * DEM_CELL_M, DEM_TOP_Y)
    # Terrain tiles reach FADE_M further (web-map metres are longer than real ones here).
    fade_merc = FADE_M / math.cos(math.radians(49.25))
    tx_box = (mx0 - fade_merc, mx1 + fade_merc, my0 - fade_merc, my1 + fade_merc)

    for d in (OUT_DIR, RELIEF_DIR):
        if d.exists():
            shutil.rmtree(d)
    relief_bytes = 0
    total_tiles = total_bytes = 0
    for z in range(MIN_ZOOM, MAX_ZOOM + 1):
        n = 2 ** z
        tile_m = WORLD_M / n                       # one tile's width on the web map, m
        px_ground = tile_m / TILE_PX * math.cos(math.radians(49.25))   # real metres per pixel here
        cell = max([c for c in levels if c <= px_ground] or [min(levels)])
        grid, vgrid, pad = levels[cell], valid_levels[cell], pads[cell]
        tx0 = int((tx_box[0] + WORLD_M / 2) // tile_m)
        tx1 = int((tx_box[1] + WORLD_M / 2) // tile_m)
        ty0 = int((WORLD_M / 2 - tx_box[3]) // tile_m)
        ty1 = int((WORLD_M / 2 - tx_box[2]) // tile_m)
        count = 0
        for tx in range(tx0, tx1 + 1):
            for ty in range(ty0, ty1 + 1):
                # The centre of every pixel in this tile, and a ring of one pixel around it
                # (the relief needs each pixel's neighbours), on the web map, then in UTM.
                i = (np.arange(-1, TILE_PX + 1) + 0.5) / TILE_PX
                px = -WORLD_M / 2 + (tx + i) * tile_m
                py = WORLD_M / 2 - (ty + i) * tile_m
                gx, gy = np.meshgrid(px, py)
                ux, uy = to_utm.transform(gx, gy)
                # Bilinear sample of the chosen grid (cell centres at half a cell in, after the pad).
                c = (ux - DEM_LEFT_X) / cell - 0.5 + pad
                r = (DEM_TOP_Y - uy) / cell - 0.5 + pad
                h_ring = bilinear(grid, r, c)
                # Past the DEM's rectangle, ease the invented ground down to 0 m.
                out = np.hypot(np.maximum(0, np.maximum(dem_box[0] - ux, ux - dem_box[1])),
                               np.maximum(0, np.maximum(dem_box[2] - uy, uy - dem_box[3])))
                t = np.clip(1 - out / FADE_M, 0, 1)
                h_ring = h_ring * (t * t * (3 - 2 * t))
                h = h_ring[1:-1, 1:-1]
                # The shaded relief, cut to the real ground.
                shade, amount = hillshade(h_ring * VERTICAL_EXAGGERATION, z, (tx, ty, n))
                amount *= np.clip(bilinear(vgrid, r, c)[1:-1, 1:-1] * 2 - 0.5, 0, 1)   # 0 outside, 1 inside, a soft pixel at the edge
                if amount.max() > 0.01:
                    rpath = RELIEF_DIR / str(z) / str(tx) / f"{ty}.png"
                    rpath.parent.mkdir(parents=True, exist_ok=True)
                    relief_image(shade, amount).save(rpath, optimize=True, transparency=PALETTE[1])
                    relief_bytes += rpath.stat().st_size
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
    lon3, lat3 = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True).transform(tx_box[:2], tx_box[2:])
    log(f"3D ground bounds:    [{lon3[0]:.5f}, {lat3[0]:.5f}, {lon3[1]:.5f}, {lat3[1]:.5f}]")
    log(f"Done: {total_tiles} tiles, {total_bytes / 1e6:.1f} MB in {OUT_DIR.relative_to(ROOT)}")
    log(f"      relief {relief_bytes / 1e6:.1f} MB in {RELIEF_DIR.relative_to(ROOT)}")
    log(f"Bounds for the page: [{lon[0]:.5f}, {lat[0]:.5f}, {lon[1]:.5f}, {lat[1]:.5f}]")


if __name__ == "__main__":
    main()
