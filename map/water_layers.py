"""
================================================================================
 WHERE THE WATER GOES  --  writes the map's "Water" layers into map/data/
================================================================================

WHY THIS EXISTS
  The map's Water layers show where rain that a lot cannot soak up runs once
  it leaves the lot: the downhill paths it follows, the low spots where it
  ponds, and the parks it reaches. This script does the slow part once, from
  the ground heights. The page then only moves water along the paths it
  wrote, so the slider stays instant.

WHAT IT READS
  DEM_2013.tif          the City's 2013 bare-earth ground heights (0.5 m grid,
                        NAD83 / UTM 10N, -9999 = no data). Not committed.
  map/data/lots.geojson       the R1-1 sites (k key, A area, sc/cd/f flags)
  map/data/buildings.geojson  the 2015 footprints
  map/data/parks.geojson      the park outlines
  map/data/park-lots.json     sites that are park land (map/park_lots.py); like
                              the page, they send no water. Optional.

WHAT IT WRITES
  map/data/flow-paths.geojson  one line per stretch of downhill path, between
                               junctions. Feature id = its node number.
  map/data/low-spots.geojson   one outline per low spot (a hollow with no
                               outlet until it fills), with v its volume in m3
                               and d its deepest point in m.
  map/data/water.json          the network the page routes water through:
                               for every path and low spot, the next one
                               downhill, the R1-1 lot area that drains
                               straight into it, its volume (low spots), and
                               the park it lies in; and for every lot, the
                               first path or low spot its water enters (so
                               the page can draw the lot's route), and the
                               first park and low spot its water reaches.

THE METHOD (no hydrology numbers in here: those are on the page)
  1. Average the DEM to a coarser grid (CELL_M), and raise each 2015 house
     footprint so water runs around houses, not through them (the DEM is
     bare earth: the houses were taken out of it).
  2. "Priority-flood" (Barnes et al. 2014): flood the ground from the city's
     edge inwards, lowest ground first. Each cell drains to the neighbour
     that reached it, which is its lowest neighbour; a hollow fills up to its
     lip, and its cells drain out over that lip. Every cell ends up with one
     downhill neighbour, and every path ends at the city's edge (the shore).
  3. Add up, down every path, how much R1-1 lot area drains through each
     cell. Lot area is the measure because the page's water comes only from
     lots: each lot sends the same depth of water per m2 at a given slider
     setting, so water on a path = that depth x the lot area above it.
  4. Low spots: where the flooded surface stands above the ground by more
     than SPOT_MIN_DEPTH_M, joined into areas; kept if they hold at least
     SPOT_MIN_VOLUME_M3. Each one's volume is what it holds before it spills.
  5. Paths: cells with at least PATH_MIN_LOT_M2 of lot area above them,
     cut into stretches at every junction, low spot and park edge.

LIMITS (say these out loud next to any result)
  - Only ground and houses: no curbs at this grid size, no pipes, no culverts.
    A road embankment over a culvert reads as a dam, so a low spot can appear
    behind it that the culvert drains in reality.
  - 2013 ground, 2015 houses. Building sites dug in 2013 are holes in the
    ground model (Marine Gateway at SW Marine and Cambie reads 14 m deep);
    hollows deeper than SPOT_MAX_DEPTH_M are left out as built features.
  - The DEM is bare earth: the City removed the buildings and guessed the
    ground under them, and the guess often sags into a house-shaped bowl
    (about 350 of them). Ground under a 2015 house never counts as a low spot.
  - A low spot's storage counts only to POND_CAP_M deep, the City's limit
    for water standing beside roads and walks.
  - Low spots listed in NOT_LOW_SPOTS are left out by hand, as ground-model
    artifacts; their water runs on downhill as path.
  - Only water from R1-1 lots is routed; streets, lanes and other zones are
    not counted.

HOW TO RUN IT
     source .venv/bin/activate
     pip install tifffile imagecodecs pillow numba      (once)
     python map/water_layers.py
  About 5 minutes and 15 GB of memory. Re-run only if the DEM, the lots or a
  setting below changes.
================================================================================
"""

import heapq
import json
import sys
import time
from pathlib import Path

import numba
import numpy as np
import shapely
import tifffile
from PIL import Image, ImageDraw
from pyproj import Transformer

ROOT = Path(__file__).resolve().parent.parent
DEM_FILE = ROOT / "DEM_2013.tif"
DATA = ROOT / "map" / "data"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA   # where to write (default: map/data)

# ---- Settings ------------------------------------------------------------------
CELL_M = 2.0              # grid cell, m. The DEM's 0.5 m cells are averaged 4 x 4.
                          # Finer follows curbs better but takes 16x the memory.
HOUSE_RAISE_M = 2.0       # house footprints are raised this much, so water goes round
HOUSE_SHRINK_M = 0.75     # ...after shrinking each footprint by this much, so the
                          # 1.2 m side yards between houses stay open at a 2 m grid
SPOT_MIN_DEPTH_M = 0.05   # a cell is in a low spot if water would stand deeper than
                          # this (the DEM's own noise is about +/- 5 cm)
SKIP_UNDER_HOUSES = True # ground under a 2015 house cannot hold water: the DEM's guessed
                          # ground there sags into house-shaped bowls (see LIMITS)
SPOT_MAX_DEPTH_M = 3.0    # hollows deeper than this are taken as built features drained by
                          # pipes or pumps (pits, underpasses, tunnel portals), not ponds;
                          # (Kevin's call, 2026-10-09: the 2013 Marine Gateway dig read as a
                          # 14 m hole); None = keep them all
POND_CAP_M = 0.15         # count a low spot's storage only up to this depth (the City's limit
                          # for water standing beside roads and walks is 0.15 m, Engineering
                          # Design Manual 2026 p.151 and p.183; Kevin's call, 2026-10-09);
                          # None = its full depth
NOT_LOW_SPOTS = [         # low spots left out by hand: the one containing each point (longitude,
                          # latitude) is not a low spot; its water runs on downhill as path
    (-123.1639, 49.2206, "the south Kerrisdale plateau down to Southlands, by SW Marine Drive: "
                         "125 ha, 188,000 m3, the largest by far; taken as a ground-model artifact "
                         "(Kevin's call, 2026-10-11)"),
]
SPOT_MIN_VOLUME_M3 = 50.0 # a low spot must hold at least this much to be drawn and
                          # to count; smaller ones are treated as part of the path
PATH_MIN_LOT_M2 = 4000.0  # a path is drawn where at least this much R1-1 lot area
                          # drains through it: about ten lots
SIMPLIFY_M = 1.5          # drawn lines and outlines are smoothed to this, m
NOT_A_SITE_M2 = 150       # same rule as the page: smaller parcels are not assessed
PARK_LOTS_FILE = DATA / "park-lots.json"   # park land the page does not assess (Kevin's call,
                          # 2026-10-11); these send no water either. Missing = none
NODATA = -9999.0
SEA_M = -1.75             # the DEM paints the sea near the shore as a flat -1.8 m surface;
                          # at or below this is sea: water that reaches it has left the city

DEM_LEFT_X = 483639.1     # the DEM grid's top-left corner, UTM m (its own header)
DEM_TOP_Y = 5463000.43
DEM_CELL_M = 0.5


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ---- 1. The ground ------------------------------------------------------------
def read_ground():
    f = int(round(CELL_M / DEM_CELL_M))
    dem = tifffile.imread(DEM_FILE)
    h, w = (dem.shape[0] // f) * f, (dem.shape[1] // f) * f
    blocks = dem[:h, :w].reshape(h // f, f, w // f, f)
    valid = blocks > NODATA + 1
    n = valid.sum(axis=(1, 3))
    s = np.where(valid, blocks, 0).sum(axis=(1, 3), dtype=np.float64)
    del dem, blocks, valid
    z = np.full(n.shape, np.nan, dtype=np.float32)
    # a coarse cell counts as ground only if most of it is ground
    np.divide(s, n, out=z, where=n > f * f // 2, casting="unsafe")
    z[z <= SEA_M] = np.nan                       # the sea: the paths end at the shore
    return z


class Grid:
    """Turns longitude/latitude rings into pixel rings on the coarse grid."""
    def __init__(self, shape):
        self.shape = shape
        self.to_utm = Transformer.from_crs(4326, 26910, always_xy=True)
        self.to_ll = Transformer.from_crs(26910, 4326, always_xy=True)

    def px(self, ring_ll):
        x, y = self.to_utm.transform(*zip(*ring_ll))
        return [((xx - DEM_LEFT_X) / CELL_M, (DEM_TOP_Y - yy) / CELL_M) for xx, yy in zip(x, y)]

    def ll(self, cols, rows):
        """Pixel positions (cell centres at +0.5) back to longitude/latitude."""
        x = DEM_LEFT_X + (np.asarray(cols) + 0.5) * CELL_M
        y = DEM_TOP_Y - (np.asarray(rows) + 0.5) * CELL_M
        return self.to_ll.transform(x, y)


def polygons_of(geom):
    if geom["type"] == "Polygon":
        return [geom["coordinates"]]
    if geom["type"] == "MultiPolygon":
        return geom["coordinates"]
    return []


def burn(grid, features, value_of, shrink_m=0.0):
    """Draw polygons onto an integer grid; value_of(i, feature) gives each its number."""
    img = Image.new("I", (grid.shape[1], grid.shape[0]), 0)
    draw = ImageDraw.Draw(img)
    for i, f in enumerate(features):
        v = value_of(i, f)
        if not v:
            continue
        for rings in polygons_of(f["geometry"]):
            outer = grid.px(rings[0])
            if shrink_m:
                p = shapely.Polygon(outer).buffer(-shrink_m / CELL_M)
                if p.is_empty:
                    continue
                parts = p.geoms if p.geom_type == "MultiPolygon" else [p]
                for q in parts:
                    draw.polygon(list(q.exterior.coords), fill=v)
                continue
            draw.polygon(outer, fill=v)
            for hole in rings[1:]:
                draw.polygon(grid.px(hole), fill=0)
    return np.asarray(img, dtype=np.int32)


# ---- 2. Priority-flood: every cell's downhill neighbour -----------------------
@numba.njit(cache=True)
def priority_flood(z):
    """Returns recv (the cell each cell drains to, -1 = off the edge), the
    flooded surface, and the order cells were reached (downhill first)."""
    rows, cols = z.shape
    n = rows * cols
    zf = z.ravel()
    recv = np.full(n, -2, dtype=np.int64)          # -2 = not ground
    filled = np.full(n, np.nan, dtype=np.float32)
    order = np.empty(n, dtype=np.int64)
    k = 0
    heap = [(np.float32(0.0), np.int64(0))]
    heap.pop()
    pit = np.empty(n, dtype=np.int64)
    p0 = 0
    p1 = 0
    dr = np.array([-1, -1, -1, 0, 0, 1, 1, 1])
    dc = np.array([-1, 0, 1, -1, 1, -1, 0, 1])
    # seeds: ground cells on the grid's border or next to no-data (the shore and the city edge)
    for r in range(rows):
        for c in range(cols):
            i = r * cols + c
            if np.isnan(zf[i]):
                continue
            edge = r == 0 or c == 0 or r == rows - 1 or c == cols - 1
            if not edge:
                for d in range(8):
                    if np.isnan(zf[(r + dr[d]) * cols + c + dc[d]]):
                        edge = True
                        break
            if edge:
                recv[i] = -1
                filled[i] = zf[i]
                heapq.heappush(heap, (zf[i], np.int64(i)))
    while len(heap) > 0 or p0 < p1:
        if p0 < p1:
            i = pit[p0]
            p0 += 1
        else:
            i = heapq.heappop(heap)[1]
        order[k] = i
        k += 1
        r = i // cols
        c = i % cols
        for d in range(8):
            rr = r + dr[d]
            cc = c + dc[d]
            if rr < 0 or cc < 0 or rr >= rows or cc >= cols:
                continue
            j = rr * cols + cc
            if recv[j] != -2 or np.isnan(zf[j]):
                continue
            recv[j] = i
            if zf[j] <= filled[i]:
                filled[j] = filled[i]              # under the water line: part of a hollow
                pit[p1] = j
                p1 += 1
            else:
                filled[j] = zf[j]
                heapq.heappush(heap, (zf[j], np.int64(j)))
    return recv, filled.reshape(rows, cols), order[:k]


@numba.njit(cache=True)
def accumulate(order, recv, weight):
    acc = weight.copy()
    for t in range(len(order) - 1, -1, -1):
        i = order[t]
        if recv[i] >= 0:
            acc[recv[i]] += acc[i]
    return acc


@numba.njit(cache=True)
def label_regions(mask, rows, cols):
    """8-connected regions of a flat boolean mask; 0 = not in one."""
    lab = np.zeros(rows * cols, dtype=np.int32)
    stack = np.empty(rows * cols, dtype=np.int64)
    nxt = 0
    for s in range(rows * cols):
        if not mask[s] or lab[s]:
            continue
        nxt += 1
        lab[s] = nxt
        top = 0
        stack[top] = s
        top += 1
        while top:
            top -= 1
            i = stack[top]
            r = i // cols
            c = i % cols
            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    rr = r + dr
                    cc = c + dc
                    if rr < 0 or cc < 0 or rr >= rows or cc >= cols:
                        continue
                    j = rr * cols + cc
                    if mask[j] and not lab[j]:
                        lab[j] = nxt
                        stack[top] = j
                        top += 1
    return lab, nxt


# ---- 5. The network: stretches of path, low spots, and what drains where ------
@numba.njit(cache=True)
def first_node(order, recv, node_cell):
    """For every cell, the first path stretch or low spot its water reaches
    (itself, if it is in one); -1 = it reaches the shore without meeting one."""
    first = np.full(len(recv), -1, dtype=np.int64)
    for t in range(len(order)):              # downhill cells come first
        i = order[t]
        if node_cell[i] >= 0:
            first[i] = node_cell[i]
        elif recv[i] >= 0:
            first[i] = first[recv[i]]
    return first


@numba.njit(cache=True)
def cut_paths(recv, is_path, park):
    """Cut the path cells into stretches. A stretch begins where paths join or
    begin, or where the path crosses a park edge, and runs downhill until the
    next such place. Returns each cell's stretch (-1 = none) and the cells of
    every stretch in order, top to bottom, as one list with offsets."""
    n = len(recv)
    donors = np.zeros(n, dtype=np.int32)
    donor = np.full(n, -1, dtype=np.int64)
    for i in range(n):
        r = recv[i]
        if is_path[i] and r >= 0 and is_path[r]:
            donors[r] += 1
            donor[r] = i
    start = np.zeros(n, dtype=np.bool_)
    for i in range(n):
        if is_path[i] and (donors[i] != 1 or park[donor[i]] != park[i]):
            start[i] = True
    seg = np.full(n, -1, dtype=np.int64)
    cells = np.empty(int(is_path.sum()), dtype=np.int64)
    offsets = [0]
    m = 0
    s = 0
    for i in range(n):
        if not start[i]:
            continue
        j = i
        while True:
            seg[j] = s
            cells[m] = j
            m += 1
            r = recv[j]
            if r < 0 or not is_path[r] or start[r]:
                break
            j = r
        s += 1
        offsets.append(m)
    return seg, cells[:m], np.array(offsets, dtype=np.int64)


@numba.njit(cache=True)
def spot_down(start_cells, own, recv, node_cell):
    """The next node below each low spot. A low spot is not always one solid
    shape, so its water can leave it through shallow ground and come back in;
    the next node is the first one after the path's LAST visit to the spot."""
    out = np.full(len(start_cells), -1, dtype=np.int64)
    for q in range(len(start_cells)):
        i = start_cells[q]
        cand = -1
        while i >= 0:
            nc = node_cell[i]
            if nc == own[q]:
                cand = -1
            elif nc >= 0 and cand < 0:
                cand = nc
            i = recv[i]
        out[q] = cand
    return out


@numba.njit(cache=True)
def follow(outlets, recv, spot_node, park):
    """From each lot's outlet cell, walk downhill: the first low spot, the first
    park, and the number of cells walked before the park (-1 = none)."""
    k = len(outlets)
    to_spot = np.full(k, -1, dtype=np.int64)
    to_park = np.full(k, -1, dtype=np.int64)
    steps = np.full(k, -1, dtype=np.int64)
    for q in range(k):
        i = outlets[q]
        t = 0
        while i >= 0:
            if to_spot[q] < 0 and spot_node[i] >= 0:
                to_spot[q] = spot_node[i]
            if park[i] > 0:
                to_park[q] = park[i] - 1
                steps[q] = t
                break
            i = recv[i]
            t += 1
    return to_spot, to_park, steps


def upstream_first(down):
    """Node numbers ordered so that every node comes after all nodes draining
    into it. If odd shapes still leave a loop, it is cut (that node's water is
    sent off the map) and counted, so the page never goes round in circles."""
    n = len(down)
    cuts = 0
    while True:
        indeg = np.bincount(down[down >= 0], minlength=n)
        queue = list(np.flatnonzero(indeg == 0))
        out = []
        while queue:
            u = queue.pop()
            out.append(int(u))
            d = down[u]
            if d >= 0:
                indeg[d] -= 1
                if indeg[d] == 0:
                    queue.append(d)
        if len(out) == n:
            return out, cuts
        stuck = set(range(n)) - set(out)
        u, seen = next(iter(stuck)), set()
        while u not in seen:                 # walk down until a node repeats: that is the loop
            seen.add(u)
            u = int(down[u])
        down[u] = -1
        cuts += 1


def to_lonlat(geoms, grid):
    def f(xy):
        lon, lat = grid.to_ll.transform(xy[:, 0], xy[:, 1])
        return np.column_stack([lon, lat])
    return shapely.transform(geoms, f)


def utm_of(cells, cols):
    return np.column_stack([DEM_LEFT_X + (cells % cols + 0.5) * CELL_M,
                            DEM_TOP_Y - (cells // cols + 0.5) * CELL_M])


def spot_outlines(spot_cells, spot_of_cell, cols, K):
    """Each low spot's cells as one outline: rows of touching cells become
    boxes, and each spot's boxes are merged."""
    o = np.lexsort((spot_cells, spot_of_cell))       # by spot, then by cell (row, then column)
    c, s = spot_cells[o], spot_of_cell[o]
    new_run = np.ones(len(c), dtype=bool)
    new_run[1:] = (s[1:] != s[:-1]) | (c[1:] != c[:-1] + 1) | (c[1:] // cols != c[:-1] // cols)
    first = np.flatnonzero(new_run)
    last = np.r_[first[1:], len(c)] - 1
    x0 = DEM_LEFT_X + (c[first] % cols) * CELL_M
    x1 = DEM_LEFT_X + (c[last] % cols + 1) * CELL_M
    y1 = DEM_TOP_Y - (c[first] // cols) * CELL_M
    boxes = shapely.box(x0, y1 - CELL_M, x1, y1)
    owner = s[first]
    bounds = np.searchsorted(owner, np.arange(K + 1))
    return [shapely.union_all(boxes[bounds[k]:bounds[k + 1]]) for k in range(K)]


def write_geojson(path, geoms, props):
    feats = []
    for i, (g, p) in enumerate(zip(geoms, props)):
        geo = json.loads(shapely.to_geojson(shapely.set_precision(g, 1e-6)))
        feats.append({"type": "Feature", "id": i if "i" not in p else p["i"], "properties": p, "geometry": geo})
    path.write_text(json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":")))
    return path.stat().st_size


def main():
    if not DEM_FILE.exists():
        sys.exit(f"{DEM_FILE.name} not found in the project folder.")
    t0 = time.time()
    log(f"Reading {DEM_FILE.name} and averaging to {CELL_M:g} m…")
    z = read_ground()
    rows, cols = z.shape
    grid = Grid(z.shape)
    log(f"  {cols} x {rows} cells; {np.isfinite(z).mean():.0%} ground")

    log("Drawing lots, parks and houses onto the grid…")
    lots = json.load(open(DATA / "lots.geojson"))["features"]
    parks = json.load(open(DATA / "parks.geojson"))["features"]
    houses = json.load(open(DATA / "buildings.geojson"))["features"]
    park_lots = json.load(open(PARK_LOTS_FILE))["lots"] if PARK_LOTS_FILE.exists() else {}
    assessed = np.array([p["sc"] == 0 and not p.get("cd") and not p.get("f") and p["A"] >= NOT_A_SITE_M2
                         and p["k"] not in park_lots
                         for p in (f["properties"] for f in lots)])
    lot_id = burn(grid, lots, lambda i, f: i + 1).ravel()               # 0 = no lot
    park_id = burn(grid, parks, lambda i, f: i + 1).ravel()             # 0 = no park
    house = burn(grid, houses, lambda i, f: 1, HOUSE_SHRINK_M).ravel() > 0
    under_house = burn(grid, houses, lambda i, f: 1).ravel() > 0      # the full footprints
    zr = z.ravel().copy()
    zr[house & np.isfinite(zr)] += HOUSE_RAISE_M
    log(f"  {assessed.sum():,} assessed lots, {len(parks)} parks, {house.mean():.1%} of cells under houses")

    log("Flooding from the edge inwards (priority-flood)…")
    recv, filled, order = priority_flood(zr.reshape(rows, cols))
    filled = filled.ravel()
    log(f"  {len(order):,} ground cells routed")

    # Lot area per cell: a cell inside an assessed lot carries its own area.
    cell_area = CELL_M * CELL_M
    on_lot = lot_id > 0
    w = np.zeros(rows * cols, dtype=np.float64)
    w[on_lot] = np.where(assessed[lot_id[on_lot] - 1], cell_area, 0.0)
    acc = accumulate(order, recv, w)
    log(f"  {w.sum() / 1e6:.1f} km² of assessed lot area routed")

    log("Finding low spots…")
    depth = np.where(np.isfinite(filled), filled - zr, 0).astype(np.float32)
    pond = depth if not SKIP_UNDER_HOUSES else np.where(under_house, 0, depth)
    region, nreg = label_regions(pond > SPOT_MIN_DEPTH_M, rows, cols)
    held = depth if POND_CAP_M is None else np.minimum(depth, POND_CAP_M)
    vol = np.bincount(region, weights=held * cell_area, minlength=nreg + 1)
    keep = vol >= SPOT_MIN_VOLUME_M3
    if SPOT_MAX_DEPTH_M is not None:
        deepest_m = np.zeros(nreg + 1, dtype=np.float32)
        np.maximum.at(deepest_m, region, depth)
        log(f"  {(keep & (deepest_m > SPOT_MAX_DEPTH_M)).sum():,} hollows deeper than {SPOT_MAX_DEPTH_M} m left out as built features")
        keep &= deepest_m <= SPOT_MAX_DEPTH_M
    for lon, lat, why in NOT_LOW_SPOTS:
        x, y = grid.to_utm.transform(lon, lat)
        r = region[int((DEM_TOP_Y - y) / CELL_M) * cols + int((x - DEM_LEFT_X) / CELL_M)]
        if r and keep[r]:
            log(f"  left out by hand: {vol[r]:,.0f} m³, {why}")
        else:
            log(f"  NOT_LOW_SPOTS point {lon}, {lat} is in no low spot: check it ({why})")
        keep[r] = False
    keep[0] = False
    spot = np.where(keep[region], region, 0)
    log(f"  {nreg:,} hollows deeper than {SPOT_MIN_DEPTH_M} m; {keep.sum():,} hold ≥ {SPOT_MIN_VOLUME_M3:g} m³ "
        f"({vol[keep].sum():,.0f} m³ in all)")

    # Only the low spots big enough to count become nodes; the rest are treated as path.
    spot_ids = np.flatnonzero(keep)
    K = len(spot_ids)
    dense = np.full(nreg + 1, -1, dtype=np.int64)
    dense[spot_ids] = np.arange(K)
    spot_of = dense[region]                        # each cell's low spot, 0..K-1, or -1

    log("Cutting the paths into stretches…")
    is_path = (acc >= PATH_MIN_LOT_M2) & (spot_of < 0)
    seg, seg_cells, seg_off = cut_paths(recv, is_path, park_id)
    S = len(seg_off) - 1
    node_cell = np.where(seg >= 0, seg, np.where(spot_of >= 0, S + spot_of, -1))
    first = first_node(order, recv, node_cell)
    log(f"  {S:,} stretches of path, {K:,} low spots")

    # The network: for each node, the next one downhill, the lot area that drains
    # straight into it, its volume (low spots only) and the park it is in.
    down = np.full(S + K, -1, dtype=np.int64)
    last = seg_cells[seg_off[1:] - 1]
    nxt = recv[last]
    down[:S] = np.where(nxt >= 0, first[np.maximum(nxt, 0)], -1)
    spot_cells = np.flatnonzero(spot_of >= 0)
    sc_of = spot_of[spot_cells]
    dmax = np.zeros(K, dtype=np.float32)
    np.maximum.at(dmax, sc_of, depth[spot_cells])
    deepest = np.zeros(K, dtype=np.int64)
    o = np.lexsort((depth[spot_cells], sc_of))
    deepest[sc_of[o]] = spot_cells[o]                    # the last one written per spot is the deepest
    down[S:] = spot_down(deepest, S + np.arange(K), recv, node_cell)
    has = first >= 0
    a_local = np.bincount(first[has], weights=w[has], minlength=S + K)
    v_node = np.zeros(S + K)
    v_node[S:] = vol[spot_ids]
    park_node = np.full(S + K, -1, dtype=np.int64)
    park_node[:S] = park_id[seg_cells[seg_off[:-1]]] - 1
    park_node[S:] = park_id[deepest] - 1
    order_nodes, cuts = upstream_first(down)
    if cuts:
        log(f"  {cuts} loop(s) cut")
    lost = w[~has].sum()
    log(f"  {a_local.sum() / 1e6:.2f} km² of lot area drains into the network; "
        f"{lost / 1e6:.2f} km² reaches the shore without meeting a path or low spot")

    log("Where each lot's water goes…")
    lot_cells = np.flatnonzero(lot_id > 0)
    lid = lot_id[lot_cells] - 1
    o = np.lexsort((acc[lot_cells], lid))
    tail = np.r_[lid[o][1:] != lid[o][:-1], True]
    outlet = np.full(len(lots), -1, dtype=np.int64)
    outlet[lid[o][tail]] = lot_cells[o][tail]            # each lot's cell carrying the most water: where it leaves
    spot_node = np.where(spot_of >= 0, S + spot_of, -1)
    to_spot, to_park, steps = follow(outlet, recv, spot_node, park_id)
    reach = to_park >= 0
    log(f"  {reach[assessed].mean():.0%} of assessed lots' water reaches a park; "
        f"{(to_spot[assessed] >= 0).mean():.0%} meets a low spot on the way")

    log("Drawing the lines and outlines…")
    lines = []
    for k in range(S):
        cells = seg_cells[seg_off[k]:seg_off[k + 1]]
        if nxt[k] >= 0:
            cells = np.r_[cells, nxt[k]]                 # join each stretch to the one below it
        xy = utm_of(cells, cols)
        if len(xy) == 1:
            xy = np.vstack([xy, xy + 0.01])
        lines.append(shapely.LineString(xy))
    lines = to_lonlat(shapely.simplify(np.array(lines), SIMPLIFY_M), grid)
    outlines = to_lonlat(shapely.simplify(np.array(spot_outlines(spot_cells, sc_of, cols, K)), SIMPLIFY_M), grid)
    size_l = write_geojson(OUT / "flow-paths.geojson", lines, [{"i": k} for k in range(S)])
    size_s = write_geojson(OUT / "low-spots.geojson", outlines,
                           [{"i": S + k, "v": round(float(vol[spot_ids[k]]), 1), "d": round(float(dmax[k]), 2)}
                            for k in range(K)])
    m_per_step = CELL_M * 1.2                            # a walked step is straight or diagonal: about 1.2 cells on average
    water = {
        "made": time.strftime("%Y-%m-%d"),
        "settings": {"cell_m": CELL_M, "house_raise_m": HOUSE_RAISE_M, "spot_min_depth_m": SPOT_MIN_DEPTH_M,
                     "spot_min_volume_m3": SPOT_MIN_VOLUME_M3, "path_min_lot_m2": PATH_MIN_LOT_M2,
                     "skip_under_houses": SKIP_UNDER_HOUSES, "spot_max_depth_m": SPOT_MAX_DEPTH_M,
                     "pond_cap_m": POND_CAP_M, "sea_m": SEA_M,
                     "not_low_spots": [why for _, _, why in NOT_LOW_SPOTS]},
        "paths": S, "spots": K,
        "down": down.tolist(),
        "a": np.round(a_local).astype(int).tolist(),
        "v": np.round(v_node).astype(int).tolist(),
        "park": park_node.tolist(),
        "order": order_nodes,
        "lots": len(lots),
        "lot_node": np.where(outlet >= 0, first[np.maximum(outlet, 0)], -1).tolist(),
        "lot_spot": to_spot.tolist(),
        "lot_park": to_park.tolist(),
        "lot_park_m": np.where(reach, np.round(steps * m_per_step), -1).astype(int).tolist(),
    }
    (OUT / "water.json").write_text(json.dumps(water, separators=(",", ":")))
    log(f"Wrote flow-paths.geojson ({size_l / 1e6:.1f} MB), low-spots.geojson ({size_s / 1e6:.1f} MB), "
        f"water.json ({(OUT / 'water.json').stat().st_size / 1e6:.1f} MB) in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
