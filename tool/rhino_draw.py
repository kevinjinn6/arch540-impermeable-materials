"""
================================================================================
 R1-1 s.3.2.2.8 -- RHINO VISUALIZATION
================================================================================

Draws one or more examples in Rhino, side by side:

  1. THE LOT, from the City's parcel polygon. Every surface in the design sits
     on it, coloured by what the BY-LAW calls it -- not by what the material
     sounds like. Permeable pavers come out graphite, like concrete. A raised
     deck floats at its stated height; a surface that crosses the lot line
     is outlined in red beyond it, because that part is not counted.
  2. THE COVERAGE COLUMN beside each lot. Each counted surface is a block
     whose height is its share of the site -- the share the by-law counts,
     after clipping to the lot and after overlaps. The 75% limit is an
     orange plane. If the column pokes through the plane, the design fails.

The calculation itself is in impermeable_check.py. This file only draws it,
so the numbers in Rhino are the same numbers the terminal prints.

HOW TO RUN IT
  In Rhino 8:  type  ScriptEditor , open this file, and press Run.
  It clears and redraws only its own layers, under "R1-1 s.3.2.2.8", and
  replaces only its own named views (the ones starting "R1-1 ").
  Anything else in your model is left alone.
  Two named views are saved for each example: "R1-1 Plan - ..." (read the
  surfaces) and "R1-1 Axon - ..." (read the column). Double-click one in the
  Named Views panel to jump to it.

  macOS: if Rhino reports "Operation not permitted" when opening the examples,
  allow Rhino to access your Documents folder in System Settings >
  Privacy & Security > Files and Folders. See README.

TO DRAW A DIFFERENT EXAMPLE
  Put its .json file in examples/ and add its name to EXAMPLES below.
================================================================================
"""

import importlib
import os
import sys
import textwrap

import Rhino
import Rhino.Geometry as rg
import System.Drawing as sd

# ==============================================================================
#  CONFIGURATION
# ==============================================================================

EXAMPLES = [
    "3528-w-30th-ave.json",               # as designed: fails
    "3528-w-30th-ave-gravel-apron.json",  # revised: passes
    "33ft-lot-laneway-house.json",        # a 33 ft lot: porch, laneway, overlaps
]

SPACING_M = 110.0         # distance between lots drawn side by side
BUILDING_HEIGHT_M = 7.0   # massing only, for legibility -- not a claim
SLAB_M = 0.12             # thickness of paving, so it reads in 3D
COLUMN_SCALE_M = 16.0     # the coverage column is this tall at 100% of site
COLUMN_SIZE_M = 6.0       # footprint of the column
COLUMN_GAP_M = 44.0       # gap between the lot and its column (clear of the plan frame)
TEXT_M = 0.7              # plan label text height
CALLOUT_BELOW_M = 4.5     # surfaces narrower than this get a callout instead
CALLOUT_LINES = 3         # ... and so does any label longer than this many lines

# Palette carried over from the W1 prototype (week-01/prompt-b-high-context).
COLOURS = {
    "building": sd.Color.FromArgb(38, 52, 86),      # survey-ink navy
    "impermeable": sd.Color.FromArgb(78, 80, 84),   # graphite
    "permeable": sd.Color.FromArgb(104, 132, 62),   # moss green
    "ground": sd.Color.FromArgb(226, 230, 218),     # near-white: nothing drawn here
    "lot": sd.Color.FromArgb(20, 20, 20),
    "setback": sd.Color.FromArgb(120, 120, 120),
    "limit": sd.Color.FromArgb(204, 85, 0),         # burnt orange
    "limit50": sd.Color.FromArgb(90, 90, 90),
    "pass": sd.Color.FromArgb(46, 125, 50),
    "fail": sd.Color.FromArgb(198, 40, 40),
    "text": sd.Color.FromArgb(25, 25, 25),
    "outside": sd.Color.FromArgb(198, 40, 40),
}

ROOT = "R1-1 s.3.2.2.8"
VIEW_PREFIX = "R1-1 "
LAYERS = ["Lot", "Ground", "Building", "Impermeable", "Permeable",
          "Outside lot", "Setbacks", "Coverage column", "Limit", "Labels plan",
          "Labels 3D"]

# ==============================================================================
#  END OF CONFIGURATION
# ==============================================================================

# When run from the Rhino MCP connection the document arrives as __rhino_doc__;
# when run from Rhino's own script editor it is the active document.
doc = globals().get("__rhino_doc__") or Rhino.RhinoDoc.ActiveDoc

try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    HERE = globals().get("TOOL_DIR", os.getcwd())
EXAMPLE_DIR = os.path.join(HERE, "..", "examples")

sys.path.insert(0, HERE)
import impermeable_check as ic  # noqa: E402
importlib.reload(ic)            # pick up edits without restarting Rhino


# ---- layers, materials, attributes -------------------------------------------

def layer_index(name):
    """Find or create ROOT::name, and return its index."""
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
    """Delete objects on every layer under ROOT, and nothing else."""
    prefix = ROOT + "::"
    for layer in list(doc.Layers):
        if layer.IsDeleted or not (layer.FullPath == ROOT
                                   or layer.FullPath.startswith(prefix)):
            continue
        for obj in doc.Objects.FindByLayer(layer) or []:
            doc.Objects.Delete(obj, True)
    for layer in list(doc.Layers):
        if (not layer.IsDeleted and layer.FullPath.startswith(prefix)
                and layer.Name not in LAYERS):
            doc.Layers.Delete(layer.Index, True)


_materials = {}


def material_index(key, colour, transparency=0.0):
    """Shaded mode fills surfaces from the render material, not the object
    colour, so each class gets a plain material of its own colour."""
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

def box(x0, y0, x1, y1, z0, z1):
    return rg.Box(rg.BoundingBox(rg.Point3d(x0, y0, z0),
                                 rg.Point3d(x1, y1, z1))).ToBrep()


def prism(points, z0, z1):
    """A solid with the given plan outline (a list of (x, y)) from z0 to z1.
    Works for any simple polygon, not only rectangles."""
    pts = [rg.Point3d(x, y, z0) for x, y in points]
    pts.append(pts[0])
    curve = rg.Polyline(pts).ToNurbsCurve()
    faces = rg.Brep.CreatePlanarBreps(curve, 0.001)
    if not faces:
        return None
    if z1 - z0 <= 0:
        return faces[0]
    path = rg.LineCurve(rg.Point3d(0, 0, z0), rg.Point3d(0, 0, z1))
    solid = faces[0].Faces[0].CreateExtrusion(path, True)
    return solid or faces[0]


ALIGN = {"left": Rhino.DocObjects.TextHorizontalAlignment.Left,
         "center": Rhino.DocObjects.TextHorizontalAlignment.Center,
         "right": Rhino.DocObjects.TextHorizontalAlignment.Right}


def add_text(text, pt, layer="Labels plan", colour=None, height=TEXT_M,
             align="center", facing="up", along=None):
    """Text centred vertically on pt.
    facing="up"    lies flat, for reading in plan
    facing="south" stands upright facing the lane, for reading in 3D
    along          optional baseline direction for flat text, e.g. (0, 1)
    """
    if facing == "south":
        plane = rg.Plane(pt, rg.Vector3d.XAxis, rg.Vector3d.ZAxis)
    elif along:
        x = rg.Vector3d(along[0], along[1], 0)
        plane = rg.Plane(pt, x, rg.Vector3d.CrossProduct(rg.Vector3d.ZAxis, x))
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


def add_outline(points, z, layer, colour, name=None):
    pts = [rg.Point3d(x, y, z) for x, y in points]
    pts.append(pts[0])
    doc.Objects.AddPolyline(rg.Polyline(pts), attrs(layer, colour, name))


def dim_string(p0, p1, offset, text=None):
    """A dimension string like a drawing's: dimension line, extension lines,
    45-degree ticks and the length, all at a size that reads at lot scale.
    offset is the (x, y) shift from the measured edge to the dimension line."""
    ink = COLOURS["text"]
    ox, oy = offset
    q0 = rg.Point3d(p0.X + ox, p0.Y + oy, 0)
    q1 = rg.Point3d(p1.X + ox, p1.Y + oy, 0)
    L = "Labels plan"
    add_line(q0, q1, L, ink)
    n = (ox ** 2 + oy ** 2) ** 0.5 or 1.0
    ux, uy = ox / n, oy / n                       # unit vector away from edge
    for p, q in ((p0, q0), (p1, q1)):
        add_line(rg.Point3d(p.X + ux * 0.4, p.Y + uy * 0.4, 0),
                 rg.Point3d(q.X + ux * 0.6, q.Y + uy * 0.6, 0), L, ink)
        add_line(rg.Point3d(q.X - 0.35, q.Y - 0.35, 0),
                 rg.Point3d(q.X + 0.35, q.Y + 0.35, 0), L, ink)
    length = p0.DistanceTo(p1)
    label = text or f"{length:.2f} m"
    mid = rg.Point3d((q0.X + q1.X) / 2 + ux * 0.9, (q0.Y + q1.Y) / 2 + uy * 0.9, 0)
    dx, dy = q1.X - q0.X, q1.Y - q0.Y
    along = (dx / length, dy / length) if length else None
    if along and along[0] < 0 or (along and abs(along[0]) < 1e-9 and along[1] < 0):
        along = (-along[0], -along[1])
    add_text(label, mid, L, ink, TEXT_M, along=along)


# ---- one example -------------------------------------------------------------

CLASS_LAYER = {"building": "Building", "impermeable": "Impermeable",
               "permeable": "Permeable", "ground": "Ground"}
CLASS_WORD = {"building": "IMPERMEABLE (building)", "impermeable": "IMPERMEABLE",
              "permeable": "permeable", "ground": "not counted"}


STREET_WORDS = ("ave", "avenue", "st", "street", "dr", "drive", "rd", "road", "blvd",
                "boulevard", "cres", "crescent", "way", "pl", "place", "hwy", "highway")


def street_name(site):
    """The street to write at the top of the plan. site["street"] if given;
    else '3528 W 30th Ave' -> 'W 30th Ave'; anything that does not look like
    a civic address (e.g. '33 ft lot') is just 'street'."""
    if site.get("street"):
        return str(site["street"])
    parts = str(site.get("address") or "").split()
    if (len(parts) >= 2 and parts[0][0].isdigit()
            and any(w.lower().strip(".,") in STREET_WORDS for w in parts[1:])):
        return " ".join(parts[1:])
    return "street"


def draw(result, example, ox):
    """Draw one checked example with its lot's origin at x = ox."""
    site = example["site"]
    outlines = ic._site_outlines(site)
    all_pts = [(x + ox, y) for o in outlines for x, y in o]
    xs = [p[0] for p in all_pts]
    ys = [p[1] for p in all_pts]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)

    # -- lot line(s) and the ground inside them (nothing drawn there: not counted)
    for o in outlines:
        shifted = [(x + ox, y) for x, y in o]
        add_outline(shifted, 0, "Lot", COLOURS["lot"], "lot line")
        ground = prism(shifted, 0, 0)
        if ground:
            doc.Objects.AddBrep(ground, attrs("Ground", COLOURS["ground"],
                                              "no surface drawn: not counted", "ground"))

    # -- yards, for orientation only (not part of this provision)
    sb = COLOURS["setback"]
    for y, label in ((maxy - 4.9, "front yard 4.9 m  s.3.2.2.4  (orientation only)"),
                     (miny + 10.7, "rear yard 10.7 m  s.3.2.2.6  (orientation only)")):
        add_line(rg.Point3d(minx, y, 0.03), rg.Point3d(maxx, y, 0.03),
                 "Setbacks", sb, label)
        add_text(label, rg.Point3d(minx - 5.4, y, 0.03), "Setbacks", sb,
                 TEXT_M * 0.7, "right")

    # -- the surfaces, coloured by by-law class
    callouts = []
    for row in result["rows"]:
        if row["points"] is None:
            continue                       # an area from a schedule: column only
        pts = [(x + ox, y) for x, y in row["points"]]
        cls = row["class"]
        pxs = [p[0] for p in pts]
        pys = [p[1] for p in pts]
        x0, x1, y0, y1 = min(pxs), max(pxs), min(pys), max(pys)
        z0 = 0.01
        if cls != "building" and row["canonical"] in ic.WOOD:
            z0 = 0.01 + (example["surfaces"][row["order"]].get("height_mm", 0) or 0) / 1000.0
        top = BUILDING_HEIGHT_M if cls == "building" else z0 + SLAB_M
        solid = prism(pts, z0, top)
        if solid:
            doc.Objects.AddBrep(solid, attrs(CLASS_LAYER[cls], COLOURS[cls], row["label"], cls))
        if row["outside_m2"] > ic.OVERLAP_TOLERANCE_M2:
            add_outline(pts, top + 0.02, "Outside lot", COLOURS["outside"],
                        f"{row['label']}: {row['outside_m2']:.2f} m² outside the lot, not counted")

        head = f"{row['label']}  {row['area_m2']:.2f} m²"
        if row["outside_m2"] > ic.OVERLAP_TOLERANCE_M2 or row["overlap_m2"] > ic.OVERLAP_TOLERANCE_M2:
            head += f"  (drawn {row['gross_m2']:.2f})"
        body = f"{row['material']}\n{CLASS_WORD[cls]}"
        if row["overlap_m2"] > ic.OVERLAP_TOLERANCE_M2:
            body += f"\n{row['overlap_m2']:.2f} m² under another surface: counted once"
        if row["outside_m2"] > ic.OVERLAP_TOLERANCE_M2:
            body += f"\n{row['outside_m2']:.2f} m² outside the lot: not counted"
        if row["flag"]:
            body += "\n! " + textwrap.shorten(row["flag"], 64, placeholder="\u2026")
        centre = rg.Point3d((x0 + x1) / 2, (y0 + y1) / 2, top + 0.05)
        text = head + "\n" + body
        nlines = text.count("\n") + 1

        if min(x1 - x0, y1 - y0) < CALLOUT_BELOW_M or nlines > CALLOUT_LINES:
            callouts.append((centre, text, nlines))
        else:
            ink = (sd.Color.White if cls in ("building", "impermeable")
                   else COLOURS["text"])
            add_text(text, centre, colour=ink)

    if any(r["canonical"] == "permeable pavers" for r in result["rows"]):
        add_text("Section 2 names “permeable pavers” as an impermeable material",
                 rg.Point3d((minx + maxx) / 2, miny - 1.5, 0.05), colour=COLOURS["fail"],
                 height=TEXT_M * 0.7)

    # narrow surfaces and long labels: to the side of the lot, with a leader
    # line, spaced down the side so no two labels overlap
    side_x = maxx + 1.2
    line_h = TEXT_M * 0.8 * 1.75      # Rhino's line spacing, with some air
    next_top = None
    for centre, text, nlines in sorted(callouts, key=lambda c: -c[0].Y):
        block_h = nlines * line_h
        ty = centre.Y
        if next_top is not None and ty + block_h / 2 > next_top:
            ty = next_top - block_h / 2
        next_top = ty - block_h / 2 - line_h * 0.8
        tip = rg.Point3d(side_x, ty, centre.Z)
        add_line(centre, tip, "Labels plan", COLOURS["text"])
        add_text(text, rg.Point3d(side_x + 0.3, ty, centre.Z), colour=COLOURS["text"],
                 height=TEXT_M * 0.8, align="left")

    # -- dimensions of the lot
    dim_string(rg.Point3d(minx, maxy, 0), rg.Point3d(maxx, maxy, 0), (0, 2.2))
    dim_string(rg.Point3d(minx, miny, 0), rg.Point3d(minx, maxy, 0), (-3.4, 0))

    # -- street and lane, so the orientation is legible
    street = street_name(site)
    add_text(street if street == "street" else f"{street}  (street)",
             rg.Point3d((minx + maxx) / 2, maxy + 5.6, 0), height=TEXT_M * 1.3)
    add_text("lane", rg.Point3d((minx + maxx) / 2, miny - 3.2, 0),
             height=TEXT_M * 1.3)

    # -- title block: what is real and what is drawn for the example
    title = f"{result['address']}\n{result['name']}"
    add_text(title, rg.Point3d((minx + maxx) / 2, miny - 7.0, 0), height=TEXT_M * 1.6)
    real = ("Lot: City parcel " + site["site_id"] if site.get("site_id")
            else "Lot: illustrative dimensions")
    add_text(f"{real}.  Design: illustrative.  Yards shown for orientation; not checked.\n"
             f"Colours are what the by-law counts, not what the material is.",
             rg.Point3d((minx + maxx) / 2, miny - 10.0, 0), height=TEXT_M * 0.8,
             colour=COLOURS["setback"])

    col_x = maxx + COLUMN_GAP_M
    col_y = miny + 2.0
    draw_column(result, col_x, col_y)

    s_ = COLUMN_SIZE_M
    top = COLUMN_SCALE_M + 5.5
    plan = [(minx - 11.0, miny - 12.0, 0.0), (maxx + 16.0, maxy + 6.5, 0.0)]
    axon = [
        (minx - 5.0, miny - 12.0, 0.0), (maxx, miny - 12.0, 0.0),      # title
        (minx - 5.0, maxy + 6.5, 0.0), (maxx, maxy + 6.5, 0.0),        # street
        (minx, miny, BUILDING_HEIGHT_M), (maxx, maxy, BUILDING_HEIGHT_M),
        (col_x - 16.0, col_y, COLUMN_SCALE_M * 0.75),                  # limit label
        (col_x, col_y - 5.5, 0.0), (col_x + s_ + 12.0, col_y, 0.0),
        (col_x, col_y, top), (col_x + s_, col_y + s_, top),
        (col_x + s_ + 12.0, col_y, COLUMN_SCALE_M * 0.6),              # block labels
    ]
    return {"plan": plan, "axon": axon}


def draw_column(result, cx, cy):
    """The stacked coverage column and the 75% limit plane."""
    site = result["site_area_m2"]
    H = COLUMN_SCALE_M
    s = COLUMN_SIZE_M
    L3 = "Labels 3D"

    # 100% of the site, as a wire outline, so the scale is readable
    frame = rg.BoundingBox(rg.Point3d(cx, cy, 0), rg.Point3d(cx + s, cy + s, H))
    for edge in frame.GetEdges():
        add_line(edge.From, edge.To, "Coverage column", COLOURS["setback"])
    add_text(f"100% of site  {site:,.2f} m²", rg.Point3d(cx + s + 1.2, cy, H),
             L3, COLOURS["setback"], TEXT_M * 0.85, "left", "south")

    # counted surfaces stacked bottom-up; building first, pavers last, so
    # the block that surprises people is the one that crosses the line.
    # Heights are the COUNTED area: clipped to the lot, overlaps removed.
    order = sorted([r for r in result["rows"]
                    if r["class"] in ("building", "impermeable") and r["area_m2"] > 0],
                   key=lambda r: (r["class"] != "building",
                                  r["canonical"] == "permeable pavers"))
    z = 0.0
    labels = []
    for r in order:
        h = r["area_m2"] / site * H
        doc.Objects.AddBrep(box(cx, cy, cx + s, cy + s, z, z + h),
                            attrs("Coverage column", COLOURS[r["class"]],
                                  f"column: {r['label']}", r["class"]))
        add_line(rg.Point3d(cx, cy - 0.01, z + h), rg.Point3d(cx + s, cy - 0.01, z + h),
                 "Coverage column", sd.Color.White)
        labels.append([z + h / 2, z + h / 2,
                       f"{r['label']}  {r['area_m2']:.2f} m²  "
                       f"{100 * r['area_m2'] / site:.1f}%"])
        z += h

    gap = TEXT_M * 1.25
    for i in range(1, len(labels)):
        labels[i][1] = max(labels[i][1], labels[i - 1][1] + gap)
    for mid, zl, text in labels:
        tx = cx + s + 1.2
        if abs(zl - mid) > 0.05:
            add_line(rg.Point3d(cx + s, cy, mid), rg.Point3d(tx - 0.2, cy, zl),
                     L3, COLOURS["text"])
        add_text(text, rg.Point3d(tx, cy, zl), L3, COLOURS["text"],
                 TEXT_M * 0.85, "left", "south")

    # the limits
    for share, label, colour, key, pad, alpha in (
            (ic.IMPERMEABLE_LIMIT, "s.3.2.2.8 limit", COLOURS["limit"], "limit", 2.0, 0.45),
            (ic.BUILDING_LIMIT, "s.3.2.2.7 buildings", COLOURS["limit50"], "limit50", 1.2, 0.55)):
        zl = share * H
        plane = rg.Brep.CreateFromCornerPoints(
            rg.Point3d(cx - pad, cy - pad, zl), rg.Point3d(cx + s + pad, cy - pad, zl),
            rg.Point3d(cx + s + pad, cy + s + pad, zl), rg.Point3d(cx - pad, cy + s + pad, zl),
            0.001)
        doc.Objects.AddBrep(plane, attrs("Limit", colour, label, key, alpha))
        add_line(rg.Point3d(cx - pad, cy - pad, zl), rg.Point3d(cx + s + pad, cy - pad, zl),
                 "Limit", colour, label)
        bfail = key == "limit50" and not result["building_pass"]
        add_text(f"{label}  {100 * share:g}%  =  {share * site:,.2f} m²"
                 + ("   FAIL" if bfail else ""),
                 rg.Point3d(cx - pad - 0.5, cy - pad, zl), L3,
                 COLOURS["fail"] if bfail else colour,
                 TEXT_M * (0.9 if key == "limit" else 0.75), "right", "south")

    # verdict above the stack
    ok = result["impermeable_pass"]
    m = result["margin_m2"]
    verdict = (f"{100 * result['impermeable_pct']:.2f}%  PASS\n{m:,.2f} m² to spare"
               if ok else
               f"{100 * result['impermeable_pct']:.2f}%  FAIL\nover by {-m:,.2f} m²")
    add_text(verdict, rg.Point3d(cx + s / 2, cy, max(z, H) + 3.6), L3,
             COLOURS["pass" if ok else "fail"], TEXT_M * 1.9, facing="south")

    if result["pavers_m2"] > 0:
        add_text(f"If pavers counted as permeable: "
                 f"{100 * result['if_pavers_were_permeable_pct']:.2f}%\n"
                 f"They don’t. Section 2 names them impermeable.",
                 rg.Point3d(cx + s / 2, cy - 4.5, 0.05), "Labels 3D", COLOURS["text"],
                 TEXT_M * 0.85)


# ---- views -------------------------------------------------------------------

def _frame(vp, points, name, direction=None):
    """Place the camera so the given points exactly fill the view, then save."""
    corners = [rg.Point3d(*p) for p in points]
    bb = rg.BoundingBox(corners)
    c = bb.Center

    if direction is None:                       # parallel plan view
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

    for _ in range(2):
        dist = 0.0
        for p in corners:
            v = p - c
            x, y, z = v * right, v * up, v * d
            dist = max(dist, abs(x) / tan_h - z, abs(y) / tan_v - z)
        dist *= 1.05
        cam = c - d * dist
        xs, ys = [], []
        for p in corners:
            v = p - cam
            depth = v * d
            xs.append((v * right) / depth)
            ys.append((v * up) / depth)
        mid_x, mid_y = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
        c = c + right * (mid_x * dist) + up * (mid_y * dist)

    vp.SetCameraLocations(c, c - d * dist)
    vp.CameraUp = up
    doc.NamedViews.Add(name, vp.Id)


def save_views(boxes, names):
    """A Plan and an Axon per example, under names starting VIEW_PREFIX.
    Only views with that prefix are replaced; the user's own are left alone."""
    view = doc.Views.ActiveView
    if view is None:
        return
    vp = view.ActiveViewport
    for v in [v.Name for v in doc.NamedViews]:
        if v.startswith(VIEW_PREFIX):
            doc.NamedViews.Delete(doc.NamedViews.FindByName(v))

    for box_, nm in zip(boxes, names):
        vp.ChangeToParallelProjection(True)
        _frame(vp, box_["plan"], f"{VIEW_PREFIX}Plan - {nm}")
        vp.ChangeToPerspectiveProjection(True, 35.0)
        _frame(vp, box_["axon"], f"{VIEW_PREFIX}Axon - {nm}", direction=(-0.42, 0.72, -0.56))


# ---- run ---------------------------------------------------------------------

def main():
    clear_own_layers()
    results, boxes, names = [], [], []
    for i, name in enumerate(EXAMPLES):
        example = ic.load(os.path.join(EXAMPLE_DIR, name))
        try:
            result = ic.check(example)
        except ic.InputError as e:
            print(f"{name}: cannot be checked:\n{e}")
            continue
        if not result["applies"]:
            print(f"{name}: s.3.2.2.8 does not apply -- {result['why_not']}")
            continue
        boxes.append(draw(result, example, i * SPACING_M))
        names.append(example.get("view_name") or f"{i + 1}")
        results.append(result)
        print(ic.report(result))

    # north arrow beside the first lot
    na = rg.Point3d(-8.0, 42.0, 0)
    add_line(na, rg.Point3d(na.X, na.Y + 3.5, 0), "Labels plan", COLOURS["text"], "north")
    add_line(rg.Point3d(na.X - 0.8, na.Y + 2.5, 0), rg.Point3d(na.X, na.Y + 3.5, 0),
             "Labels plan", COLOURS["text"])
    add_line(rg.Point3d(na.X + 0.8, na.Y + 2.5, 0), rg.Point3d(na.X, na.Y + 3.5, 0),
             "Labels plan", COLOURS["text"])
    add_text("N", rg.Point3d(na.X, na.Y + 4.6, 0), height=TEXT_M * 1.5)

    if boxes:
        save_views(boxes, names)
    doc.Views.Redraw()
    return results


if __name__ == "__main__":
    main()
