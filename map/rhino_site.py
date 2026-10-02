"""
================================================================================
 R1-1 HARD SURFACE MAP  --  ONE SITE IN RHINO
================================================================================

Draws one R1-1 site from the map's own data (map/data/lots.geojson and
map/data/buildings.geojson), so what you see in Rhino is exactly what the web
map counted for that address:

  1. THE SITE, from the City parcel polygon, with its 2015 roof footprints
     clipped to the site line and raised to their recorded height (LiDAR
     where the City measured one, a placeholder where it did not).
     Inside each roof, a thinner line shows the eave allowance: the by-law
     measures a building to the outside of its WALLS, the air photo traced
     the ROOF EDGE, so the footprint is bigger than the by-law's building.
  2. THE AREA BAR beside the site: a copy of the site as a bar, the same
     width, the same area, so its depth is 100% of the site. Filled from
     the bottom: the roof measured to the walls (dark), then the eave strip
     (grey). Two lines cross it: 50% (s.3.2.2.7, the most all buildings may
     cover) and 75% (s.3.2.2.8, the most impermeable material of any kind,
     buildings included, per s.4.2.2). The gap between the roof and the 75%
     line is the room left for paving, patios and decks.

Nothing is computed here that the web page does not compute; this file
draws it. The numbers in the title block come straight from the data file.

HOW TO RUN IT
  In Rhino 8:  type  ScriptEditor , open this file, and press Run.
  Set ADDRESSES below to the civic address(es) you want, spelled the City's
  way ("3528 W 30TH AV", "1660 BLANCA ST"). The script draws only on layers
  under "R1-1 map" and replaces only named views starting "R1-1 map ".
  Anything else in your model is left alone.

  macOS may refuse Rhino access to your Documents folder the first time
  ("Operation not permitted"): allow it under System Settings > Privacy &
  Security > Files and Folders, then run again.
================================================================================
"""

import json
import math
import os
import sys

import Rhino
import Rhino.Geometry as rg
import System.Drawing as sd

# ==============================================================================
#  CONFIGURATION  --  change these, not the code below
# ==============================================================================

ADDRESSES = ["3528 W 30TH AV"]   # one or more civic addresses, the City's spelling
GAP_M = 8.0                      # space between sites drawn side by side

EAVE_M = 0.45
# The eave allowance, in metres, taken off every roof edge to estimate the
# building the by-law measures (outside of the outermost walls). 0.3-0.6 m is
# usual on a Vancouver house; 0.45 m is the middle. Set 0 to see the raw
# footprint. The web map uses the same number (EAVE_M in map/index.html).

BYLAW_MAX_BUILDING_RATIO = 0.50     # s.3.2.2.7: all buildings, 50% of the site
BYLAW_MAX_IMPERMEABLE_RATIO = 0.75  # s.3.2.2.8: impermeable materials, 75%

TEXT_M = 0.55                    # text height in metres, reads at lot scale
PLACEHOLDER_NOTE = "placeholder height"

COLOURS = {
    "site":     sd.Color.FromArgb(31, 31, 29),
    "roof":     sd.Color.FromArgb(61, 61, 58),
    "eave":     sd.Color.FromArgb(160, 160, 155),
    "eave_line": sd.Color.FromArgb(225, 225, 220),
    "headroom": sd.Color.FromArgb(40, 123, 193),
    "limit50":  sd.Color.FromArgb(217, 74, 72),
    "limit75":  sd.Color.FromArgb(205, 120, 0),
    "text":     sd.Color.FromArgb(31, 31, 29),
    "muted":    sd.Color.FromArgb(133, 132, 126),
}
ROOT = "R1-1 map"
LAYERS = ["Site", "Roofs 2015", "Eave allowance", "Area bar", "Limits",
          "Labels plan", "Labels 3D"]
VIEW_PREFIX = "R1-1 map "

# ==============================================================================
#  END OF CONFIGURATION
# ==============================================================================

# When run from the Rhino MCP connection the document arrives as __rhino_doc__;
# when run from Rhino's own script editor it is the active document.
doc = globals().get("__rhino_doc__") or Rhino.RhinoDoc.ActiveDoc

try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    HERE = globals().get("MAP_DIR", os.getcwd())
DATA_DIR = os.path.join(HERE, "data")


# ---- UTM zone 10 north, the projection the data was measured in -------------
# EPSG:26910. The same formulas the geospatial library uses, so the areas drawn
# here match the areas in the data file (Snyder, Map Projections, eq. 8-9..8-13).

def utm10(lon, lat):
    a, f = 6378137.0, 1 / 298.257222101            # GRS80 ellipsoid
    e2 = 2 * f - f * f
    ep2 = e2 / (1 - e2)
    k0, lon0 = 0.9996, math.radians(-123.0)
    phi, lam = math.radians(lat), math.radians(lon)
    n = a / math.sqrt(1 - e2 * math.sin(phi) ** 2)
    t = math.tan(phi) ** 2
    c = ep2 * math.cos(phi) ** 2
    aa = (lam - lon0) * math.cos(phi)
    m = a * ((1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256) * phi
             - (3 * e2 / 8 + 3 * e2 ** 2 / 32 + 45 * e2 ** 3 / 1024) * math.sin(2 * phi)
             + (15 * e2 ** 2 / 256 + 45 * e2 ** 3 / 1024) * math.sin(4 * phi)
             - (35 * e2 ** 3 / 3072) * math.sin(6 * phi))
    x = k0 * n * (aa + (1 - t + c) * aa ** 3 / 6
                  + (5 - 18 * t + t * t + 72 * c - 58 * ep2) * aa ** 5 / 120) + 500000.0
    y = k0 * (m + n * math.tan(phi) * (aa ** 2 / 2 + (5 - t + 9 * c + 4 * c * c) * aa ** 4 / 24
                                       + (61 - 58 * t + t * t + 600 * c - 330 * ep2) * aa ** 6 / 720))
    return x, y


# ---- data -------------------------------------------------------------------

def load_geojson(name):
    path = os.path.join(DATA_DIR, name)
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)["features"]


def load_roof_walls():
    """rw per site from data/roof-walls.json, the same figure the web page
    uses, so Rhino and the page agree to the square metre. None if absent."""
    path = os.path.join(DATA_DIR, "roof-walls.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def normalise(address):
    return " ".join(address.upper().replace(".", "").replace(",", " ").split())


def find_site(lots, address):
    want = normalise(address)
    hits = [f for f in lots if normalise(f["properties"].get("ad", "")) == want]
    if not hits:
        raise SystemExit(f"No R1-1 site in the map data is addressed “{address}”. "
                         "Spell it the City's way, e.g. “3528 W 30TH AV”, “1660 BLANCA ST”.")
    return hits[0]


def rings_of(geometry):
    """Outer rings only, as lists of (lon, lat). Holes in a lot or roof are rare
    and are ignored here; the area figures come from the data, not the drawing."""
    if geometry["type"] == "Polygon":
        return [geometry["coordinates"][0]]
    if geometry["type"] == "MultiPolygon":
        return [poly[0] for poly in geometry["coordinates"]]
    return []


def bbox(rings):
    xs = [p[0] for r in rings for p in r]
    ys = [p[1] for r in rings for p in r]
    return min(xs), min(ys), max(xs), max(ys)


def overlaps(b1, b2):
    return not (b1[2] < b2[0] or b2[2] < b1[0] or b1[3] < b2[1] or b2[3] < b1[1])


# ---- layers and attributes ---------------------------------------------------

def layer_index(name):
    full = f"{ROOT}::{name}" if name else ROOT
    idx = doc.Layers.FindByFullPath(full, -1)
    if idx >= 0:
        return idx
    layer = Rhino.DocObjects.Layer()
    if name:
        layer.Name = name
        layer.ParentLayerId = doc.Layers[layer_index(None)].Id
    else:
        layer.Name = ROOT
    return doc.Layers.Add(layer)


def clear_own_layers():
    prefix = ROOT + "::"
    for layer in list(doc.Layers):
        if layer.IsDeleted or not (layer.FullPath == ROOT or layer.FullPath.startswith(prefix)):
            continue
        for obj in doc.Objects.FindByLayer(layer) or []:
            doc.Objects.Delete(obj, True)


_materials = {}


def material_index(key, colour, transparency=0.0):
    if key in _materials:
        return _materials[key]
    name = f"{ROOT} {key}"
    idx = doc.Materials.Find(name, True)
    m = Rhino.DocObjects.Material()
    m.Name = name
    m.DiffuseColor = colour
    m.Transparency = transparency
    if idx >= 0:
        doc.Materials.Modify(m, idx, True)
    else:
        idx = doc.Materials.Add(m)
    _materials[key] = idx
    return idx


def attrs(layer, colour, name=None, mat=None, transparency=0.0):
    a = Rhino.DocObjects.ObjectAttributes()
    a.LayerIndex = layer_index(layer)
    a.ColorSource = Rhino.DocObjects.ObjectColorSource.ColorFromObject
    a.ObjectColor = colour
    if mat:
        a.MaterialSource = Rhino.DocObjects.ObjectMaterialSource.MaterialFromObject
        a.MaterialIndex = material_index(mat, colour, transparency)
    if name:
        a.Name = name
    return a


# ---- primitives --------------------------------------------------------------

def polyline(points, z=0.0):
    pts = [rg.Point3d(x, y, z) for x, y in points]
    if pts[0].DistanceTo(pts[-1]) > 1e-9:
        pts.append(pts[0])
    return rg.Polyline(pts)


def curve_of(points, z=0.0):
    return polyline(points, z).ToNurbsCurve()


def solid_from_curve(curve, z0, z1):
    faces = rg.Brep.CreatePlanarBreps(curve, 0.001)
    if not faces:
        return None
    if z1 - z0 <= 0:
        return faces[0]
    path = rg.LineCurve(rg.Point3d(0, 0, z0), rg.Point3d(0, 0, z1))
    return faces[0].Faces[0].CreateExtrusion(path, True) or faces[0]


def box(x0, y0, x1, y1, z0, z1):
    return rg.Box(rg.BoundingBox(rg.Point3d(x0, y0, z0), rg.Point3d(x1, y1, z1))).ToBrep()


ALIGN = {"left": Rhino.DocObjects.TextHorizontalAlignment.Left,
         "center": Rhino.DocObjects.TextHorizontalAlignment.Center,
         "right": Rhino.DocObjects.TextHorizontalAlignment.Right}


def add_text(text, pt, layer="Labels plan", colour=None, height=TEXT_M, align="left", facing="up"):
    if facing == "south":
        plane = rg.Plane(pt, rg.Vector3d.XAxis, rg.Vector3d.ZAxis)
    else:
        plane = rg.Plane(pt, rg.Vector3d.ZAxis)
    te = rg.TextEntity()
    te.PlainText = text
    te.Plane = plane
    te.TextHeight = height
    te.TextHorizontalAlignment = ALIGN[align]
    te.TextVerticalAlignment = Rhino.DocObjects.TextVerticalAlignment.Middle
    doc.Objects.AddText(te, attrs(layer, colour or COLOURS["text"]))


def add_line(p0, p1, layer, colour, name=None):
    doc.Objects.AddLine(rg.Line(p0, p1), attrs(layer, colour, name))


def inset(curve, distance):
    """The curve offset inwards by distance (the smaller of the two offsets)."""
    plane = rg.Plane.WorldXY
    best = None
    for sign in (1.0, -1.0):
        result = curve.Offset(plane, sign * distance, 0.001, rg.CurveOffsetCornerStyle.Sharp)
        if not result:
            continue
        for c in result:
            if not c.IsClosed:
                continue
            area = rg.AreaMassProperties.Compute(c)
            if area and (best is None or area.Area < best[0]):
                best = (area.Area, c)
    return best[1] if best else None


def place_right_labels(labels, x_edge):
    """Labels beside the bar, pushed apart so none overlap, each tied to its
    true level by a short leader."""
    labels = sorted(labels, key=lambda l: l[0])
    gap = TEXT_M * 1.25
    ys = [l[0] for l in labels]
    for i in range(1, len(ys)):
        if ys[i] - ys[i - 1] < gap:
            ys[i] = ys[i - 1] + gap
    for (y_true, text, colour), y in zip(labels, ys):
        add_line(rg.Point3d(x_edge + 0.3, y_true, 0), rg.Point3d(x_edge + 1.2, y, 0), "Labels plan", colour)
        add_text(text, rg.Point3d(x_edge + 1.5, y, 0), "Labels plan", colour, TEXT_M * 0.8)


def north_arrow(x, y):
    ink = COLOURS["text"]
    add_line(rg.Point3d(x, y, 0), rg.Point3d(x, y + 3.0, 0), "Labels plan", ink)
    add_line(rg.Point3d(x - 0.5, y + 2.2, 0), rg.Point3d(x, y + 3.0, 0), "Labels plan", ink)
    add_line(rg.Point3d(x + 0.5, y + 2.2, 0), rg.Point3d(x, y + 3.0, 0), "Labels plan", ink)
    add_text("N", rg.Point3d(x, y + 3.9, 0), "Labels plan", ink, TEXT_M, align="center")


# ---- one site -----------------------------------------------------------------

def draw_site(site, buildings, ox, walls=None):
    """Draw one site with its west edge at x = ox. Returns the extents drawn and
    the numbers shown, so the caller can frame views and print a summary."""
    p = site["properties"]
    A, r = float(p["A"]), float(p.get("r") or 0.0)
    # Roof to the walls: from the data if the pipeline or roof-walls.json has
    # it (the web page's figure), else from this drawing's own inset.
    rw_data = None
    if p.get("rw") is not None:
        rw_data = float(p["rw"])
    elif walls and p.get("k") in walls.get("rw", {}) and abs(float(walls.get("eave_m", EAVE_M)) - EAVE_M) < 1e-9:
        rw_data = float(walls["rw"][p["k"]])
    address = p.get("ad") or "R1-1 site"

    rings = rings_of(site["geometry"])
    utm_rings = [[utm10(lon, lat) for lon, lat in ring] for ring in rings]
    x0, y0, x1, y1 = bbox(utm_rings)
    shift = lambda pt: (pt[0] - x0 + ox, pt[1] - y0)
    lot_rings = [[shift(pt) for pt in ring] for ring in utm_rings]
    width, depth = x1 - x0, y1 - y0

    # The site outline, and a thin planar face so it reads in shaded views.
    lot_curves = [curve_of(ring) for ring in lot_rings]
    for ring, curve in zip(lot_rings, lot_curves):
        doc.Objects.AddPolyline(polyline(ring), attrs("Site", COLOURS["site"], address))
        face = solid_from_curve(curve, 0, 0)
        if face:
            doc.Objects.AddBrep(face, attrs("Site", sd.Color.FromArgb(236, 236, 232), None,
                                            mat="site-face"))

    # Roofs: every 2015 footprint whose box touches the site's, clipped to it.
    lonlat_box = bbox(rings)
    drawn_roof, drawn_wall, placeholders = 0.0, 0.0, 0
    for b in buildings:
        brings = rings_of(b["geometry"])
        if not brings or not overlaps(bbox(brings), lonlat_box):
            continue
        h = float(b["properties"].get("h") or 3.0)
        src = b["properties"].get("src", "")
        for bring in brings:
            bcurve = curve_of([shift(utm10(lon, lat)) for lon, lat in bring])
            for lot_curve in lot_curves:
                pieces = rg.Curve.CreateBooleanIntersection(lot_curve, bcurve, 0.001)
                for piece in pieces or []:
                    am = rg.AreaMassProperties.Compute(piece)
                    if not am or am.Area < 0.25:
                        continue
                    drawn_roof += am.Area
                    solid = solid_from_curve(piece, 0, h)
                    if solid:
                        name = f"roof {b['properties'].get('id')} ({'LiDAR' if src == 'L' else PLACEHOLDER_NOTE})"
                        doc.Objects.AddBrep(solid, attrs("Roofs 2015", COLOURS["roof"], name, mat="roof"))
                    if src != "L":
                        placeholders += 1
                    wall = inset(piece, EAVE_M) if EAVE_M > 0 else None
                    if wall:
                        wam = rg.AreaMassProperties.Compute(wall)
                        drawn_wall += wam.Area if wam else 0.0
                        # Drawn on top of the roof so it can be seen in plan.
                        wall.Translate(rg.Vector3d(0, 0, h + 0.02))
                        doc.Objects.AddCurve(wall, attrs("Eave allowance", COLOURS["eave_line"],
                                                         f"walls, {EAVE_M} m inside the roof edge"))
                    elif EAVE_M <= 0:
                        drawn_wall += am.Area

    # The numbers the map uses: the data file's A and r, and the eave estimate
    # scaled the same way the page scales it (walls = roof × drawn ratio).
    wall_ratio = (drawn_wall / drawn_roof) if drawn_roof > 0 else 1.0
    roof_wall = min(r, rw_data) if rw_data is not None else r * wall_ratio
    share_edge, share_wall = r / A, roof_wall / A
    cap50, cap75 = BYLAW_MAX_BUILDING_RATIO * A, BYLAW_MAX_IMPERMEABLE_RATIO * A
    headroom = cap75 - roof_wall
    over50 = roof_wall > cap50

    # The area bar: same width as the site, same area, so its depth is 100%.
    bx0 = ox + width + GAP_M * 0.5
    bar_w = max(width, 6.0)
    bar_d = A / bar_w
    unit = bar_d / A                            # metres of bar per m² of site
    def level(area_m2):
        return area_m2 * unit
    doc.Objects.AddPolyline(polyline([(bx0, 0), (bx0 + bar_w, 0), (bx0 + bar_w, bar_d), (bx0, bar_d)]),
                            attrs("Area bar", COLOURS["site"], "site area, as a bar"))
    if roof_wall > 0:
        doc.Objects.AddBrep(box(bx0, 0, bx0 + bar_w, level(roof_wall), 0, 0.02),
                            attrs("Area bar", COLOURS["roof"], "roof to the walls", mat="roof"))
    if r > roof_wall:
        doc.Objects.AddBrep(box(bx0, level(roof_wall), bx0 + bar_w, level(r), 0, 0.02),
                            attrs("Area bar", COLOURS["eave"], "eave strip", mat="eave"))
    if headroom > 0:
        doc.Objects.AddBrep(box(bx0, level(max(r, roof_wall)), bx0 + bar_w, level(cap75), 0, 0.01),
                            attrs("Area bar", COLOURS["headroom"], "room left for paving", mat="headroom",
                                  transparency=0.55))
    right = []                                  # labels for the bar's right side
    for cap, key, label in ((cap50, "limit50", f"50%  s.3.2.2.7  all buildings  {cap50:,.1f} m²"),
                            (cap75, "limit75", f"75%  s.3.2.2.8  impermeable materials  {cap75:,.1f} m²")):
        y = level(cap)
        add_line(rg.Point3d(bx0 - 0.6, y, 0), rg.Point3d(bx0 + bar_w + 0.6, y, 0), "Limits", COLOURS[key], label)
        right.append((y, label, COLOURS[key]))
    right.append((level(r), f"roof, 2015 footprint  {r:,.1f} m²  {share_edge * 100:.1f}%  (roof edge)", COLOURS["muted"]))
    if EAVE_M > 0:
        right.append((level(roof_wall), f"to the walls, {EAVE_M} m eave  {roof_wall:,.1f} m²  {share_wall * 100:.1f}%", COLOURS["text"]))
    place_right_labels(right, bx0 + bar_w)
    if headroom > 0:
        add_text(f"room left for paving, patios, decks  {headroom:,.1f} m²",
                 rg.Point3d(bx0 + bar_w * 0.5, (level(r) + level(cap75)) / 2, 0), "Labels plan",
                 COLOURS["headroom"], TEXT_M * 0.85, align="center")

    # Title block under the site
    status50 = ("OVER 50% even after the eave allowance: check" if over50
                else "within 50%" if r <= cap50
                else "roof edge over 50%, walls within: eave margin")
    lines = [
        address,
        f"Site {A:,.2f} m² (City parcel)   about {width:.1f} × {depth:.1f} m",
        f"Roof 2015: {r:,.1f} m² to the roof edge = {share_edge * 100:.1f}%;  about {roof_wall:,.1f} m² = {share_wall * 100:.1f}% to the walls at a {EAVE_M} m eave",
        f"s.3.2.2.7 buildings ≤ 50% ({cap50:,.1f} m²): {status50}",
        f"s.3.2.2.8 impermeable ≤ 75% ({cap75:,.1f} m²), buildings included (s.4.2.2): {max(headroom, 0):,.1f} m² left for paving, patios, decks, pavers",
        "Section 2: asphalt, concrete, brick, stone, permeable pavers and wood are impermeable; gravel, mulch and spaced decking on grade are not.",
        "Footprints are 2015 air-photo roofs; anything built since is missing. Not a compliance finding.",
    ]
    if placeholders:
        lines.append(f"{placeholders} roof(s) drawn at a placeholder height: the City has no measured height for them.")
    ty = -TEXT_M * 1.6
    for i, line in enumerate(lines):
        add_text(line, rg.Point3d(ox, ty - i * TEXT_M * 1.75, 0), "Labels plan",
                 COLOURS["text"] if i < 5 else COLOURS["muted"], TEXT_M * (1.1 if i == 0 else 0.8))

    # 3D label on the tallest roof
    add_text(f"{address}: roofs {share_edge * 100:.0f}% of the site (roof edge)",
             rg.Point3d(ox + width / 2, -1.0, 1.0), "Labels 3D", COLOURS["text"], TEXT_M * 1.2,
             align="center", facing="south")

    north_arrow(ox - 3.0, depth - 4.0)
    extent_x = bx0 + bar_w + 22.0
    summary = dict(address=address, A=A, r=r, share_edge=share_edge, roof_wall=roof_wall,
                   share_wall=share_wall, headroom=headroom, over50=over50,
                   drawn_roof=drawn_roof, placeholders=placeholders)
    frame = {
        "plan": [(ox - 4.5, ty - len(lines) * TEXT_M * 1.75 - 1, 0), (extent_x, max(depth, bar_d) + 2, 0)],
        "axon": [(ox - 1, -3, 0), (bx0 + bar_w + 5, max(depth, bar_d) + 2, 12)],
    }
    return extent_x, summary, frame


# ---- views -------------------------------------------------------------------

def _frame(vp, points, name, direction=None):
    corners = [rg.Point3d(*p) for p in points]
    bb = rg.BoundingBox(corners)
    c = bb.Center
    if direction is None:
        vp.SetCameraLocations(rg.Point3d(c.X, c.Y, 0), rg.Point3d(c.X, c.Y, 300))
        vp.CameraUp = rg.Vector3d.YAxis
        vp.ZoomBoundingBox(bb)
        doc.NamedViews.Add(name, vp.Id)
        return
    d = rg.Vector3d(*direction)
    d.Unitize()
    right = rg.Vector3d.CrossProduct(d, rg.Vector3d.ZAxis)
    right.Unitize()
    up = rg.Vector3d.CrossProduct(right, d)
    up.Unitize()
    vp.SetCameraLocations(c, c - d * 100.0)
    vp.CameraUp = up
    ok, left, rgt, bottom, top, near, far = vp.GetFrustum()
    tan_h, tan_v = rgt / near, top / near
    pts = [rg.Point3d(bb.Min.X, bb.Min.Y, bb.Min.Z), rg.Point3d(bb.Max.X, bb.Min.Y, bb.Min.Z),
           rg.Point3d(bb.Max.X, bb.Max.Y, bb.Min.Z), rg.Point3d(bb.Min.X, bb.Max.Y, bb.Min.Z),
           rg.Point3d(bb.Min.X, bb.Min.Y, bb.Max.Z), rg.Point3d(bb.Max.X, bb.Min.Y, bb.Max.Z),
           rg.Point3d(bb.Max.X, bb.Max.Y, bb.Max.Z), rg.Point3d(bb.Min.X, bb.Max.Y, bb.Max.Z)]
    dist = 0.0
    for _ in range(2):
        dist = 0.0
        for p in pts:
            v = p - c
            x, y, z = v * right, v * up, v * d
            dist = max(dist, abs(x) / tan_h - z, abs(y) / tan_v - z)
        dist *= 1.05
        cam = c - d * dist
        xs, ys = [], []
        for p in pts:
            v = p - cam
            dz = v * d
            xs.append((v * right) / dz)
            ys.append((v * up) / dz)
        c = c + right * ((max(xs) + min(xs)) / 2 * dist) + up * ((max(ys) + min(ys)) / 2 * dist)
    vp.SetCameraLocations(c, c - d * dist)
    vp.CameraUp = up
    doc.NamedViews.Add(name, vp.Id)


def save_views(frames, names):
    view = doc.Views.ActiveView
    if view is None:
        return
    vp = view.ActiveViewport
    for v in [v.Name for v in doc.NamedViews]:
        if v.startswith(VIEW_PREFIX):
            doc.NamedViews.Delete(doc.NamedViews.FindByName(v))
    for fr, nm in zip(frames, names):
        vp.ChangeToParallelProjection(True)
        _frame(vp, fr["plan"], f"{VIEW_PREFIX}Plan - {nm}")
        vp.ChangeToPerspectiveProjection(True, 35.0)
        _frame(vp, fr["axon"], f"{VIEW_PREFIX}Axon - {nm}", direction=(-0.42, 0.72, -0.56))


# ---- run ---------------------------------------------------------------------

def main():
    lots = load_geojson("lots.geojson")
    buildings = load_geojson("buildings.geojson")
    walls = load_roof_walls()
    clear_own_layers()
    ox, frames, names = 0.0, [], []
    for address in ADDRESSES:
        site = find_site(lots, address)
        extent, s, frame = draw_site(site, buildings, ox, walls)
        frames.append(frame)
        names.append(s["address"])
        print(f"{s['address']}: site {s['A']:,.2f} m²; roof {s['r']:,.1f} m² ({s['share_edge'] * 100:.1f}% roof edge, "
              f"{s['share_wall'] * 100:.1f}% to the walls at {EAVE_M} m); "
              f"{'OVER' if s['over50'] else 'within'} 50%; {s['headroom']:,.1f} m² left under 75%; "
              f"drawn roof {s['drawn_roof']:,.1f} m²; {s['placeholders']} placeholder height(s)")
        ox = extent + GAP_M
    save_views(frames, names)
    doc.Views.Redraw()
    return frames


if __name__ == "__main__" or globals().get("__rhino_doc__"):
    FRAMES = main()
