"""
================================================================================
 R1-1 IMPERMEABLE MATERIALS CHECK  --  s.3.2.2.8
================================================================================

THE ONE OPERATION THIS TOOL PERFORMS
  Given a lot and the surfaces a design puts on it, decide which surfaces the
  by-law counts as impermeable, measure the part of each that is on the lot,
  count every square metre once, add them up, and compare the total with the
  limit in s.3.2.2.8.

  s.3.2.2.8   "Maximum area of impermeable materials   75% of the site area"
  s.4.2.2     "The maximum area of impermeable materials includes site
               coverage for all buildings."
  s.3.2.2.7   "Maximum site coverage for all buildings   50% of the site area"
              (checked alongside, because the house is part of both totals)
  s.3.2.2.13  Parking area: 30% of the site -- only when the Section 2
              definition of "parking area" is met (more than 4 spaces).

  Source text, verbatim with page references: sources/r1-1-impermeable-extract.md

WHY THIS IS WORTH A TOOL
  The limit is one line. The definition behind it is the trap. Section 2 names
  "permeable pavers" as an IMPERMEABLE material. A designer who swaps an
  asphalt pad for permeable pavers to help drainage gains nothing against this
  limit. This tool makes that visible on a real lot.

HOW TO RUN IT
     python3 tool/impermeable_check.py examples/3528-w-30th-ave.json

  No extra packages. It uses only what ships with Python, so the same file
  also runs inside Rhino (tool/rhino_draw.py imports it) and is ported line
  for line to JavaScript in tool/web/index.html.

WHAT CHANGED ON 2026-10-02 (after three outside reviews, docs/reviews/)
  - Section 2's building clause is in the vocabulary: porches, entries,
    verandahs, carports, garages, sheds and laneway houses are BUILDINGS.
  - Every surface is clipped to the lot. Area outside the lot is not counted.
  - Overlapping surfaces are counted once, as the stricter class. A raised
    deck over a patio is one footprint, not two.
  - Input is validated first. A mistake gets a sentence, not a traceback.
  - Material names are matched through an alias table, and an unknown name
    is flagged with a suggestion instead of being explained away.
  - Wood with unstated conditions says "not stated", not "boards not spaced".
  - The Permeable Materials sentence is quoted whole, and the on-grade /
    no-layer test is labelled as the author's reading, with the alternative.
  - Any use outside s.3.1 is assessed (s.3.2 is "all other uses"), with the
    s.3.2.2.14 note for non-dwelling uses.
  - Feet are accepted ("units": "ft") and a feet-sized lot typed as metres
    is warned about.

WHAT IT DOES NOT DO  (scope, stated so nobody mistakes it for a permit check)
  - A multiplex (s.3.1) is not assessed: that section sets no numeric limit.
  - It does not check yards, height, FSR, or Section 11 (laneway houses).
  - Areas come from the geometry you give it. It does not read drawings.
  - "Site area" here is the City's parcel polygon, not a legal survey.
  - It cannot know what the Director of Planning will accept.
================================================================================
"""

import json
import math
import sys

VERSION = "2026-10-02"

# ==============================================================================
#  CONFIGURATION  --  the numbers the by-law sets
# ==============================================================================

IMPERMEABLE_LIMIT = 0.75   # s.3.2.2.8 -- impermeable materials, share of site
BUILDING_LIMIT = 0.50      # s.3.2.2.7 -- building site coverage, share of site
PARKING_LIMIT = 0.30       # s.3.2.2.13 -- site used as a parking area
PARKING_AREA_SPACES = 4    # Section 2 "Parking Area": 4 or fewer spaces
                           # accessory to a residential use are NOT a parking
                           # area, so s.3.2.2.13 does not apply to them.

RAISED_DECK_MM = 600
# Section 2 defines a "Deck" as a platform generally more than 600 mm above
# grade, and a "Patio" as one no higher than 600 mm. A raised Deck is not "on
# grade", so it cannot use the permeable exception for spaced decking.

MIN_SITE_AREA_M2 = 306.0   # s.3.2.2.1 -- flagged, not enforced (see below)
MIN_FRONTAGE_M = 7.3       # s.3.2.2.2 -- flagged, not enforced
# A lot below these floors is flagged and still assessed, because the by-law
# gives two ways past them:
#   s.3.2.2.9   the Director of Planning may reduce the minimum site area and
#               frontage for a dwelling use
#   s.3.2.2.12  for sites under 7.3 m wide, the side yard is reduced to permit
#               a single detached house on a lot on record as of June 24, 2014,
#               if the use was previously approved under issued permits

# A lot this big, or this wide, was probably typed in feet. Warned, not refused.
FEET_SUSPECT_AREA_M2 = 1500.0
FEET_SUSPECT_FRONTAGE_M = 30.0
FT_TO_M = 0.3048

# Anything smaller than this is treated as rounding, not a real area.
OVERLAP_TOLERANCE_M2 = 0.01

# The City's parcel lines are not perfectly straight -- the rear line of the
# demo lot wanders 3.6 cm across its width -- so a pad drawn to the nominal
# lane line would otherwise lose a few hundredths of a square metre as
# "outside the lot". A band this wide around the lot line still counts as on
# the lot.
EDGE_TOLERANCE_M = 0.02

# Verdicts are decided on unrounded areas. When a design is closer to the
# limit than the two decimals the report prints, the report shows more.
NEAR_LIMIT_M2 = 0.005
NEAR_LIMIT_PCT = 0.01      # percentage points: 75.005% prints as "75.00%"

# ==============================================================================
#  THE SOURCE TEXT  --  verbatim, with the page it is printed on
#  Zoning and Development By-law No. 3575: Section 2 Definitions and the R1-1
#  District Schedule, both the June 2026 consolidation (sources/*.pdf).
# ==============================================================================

S2_IMPERMEABLE = ("Section 2, Impermeable Materials (p.20): “The projected area "
                  "of the outside of the outermost walls of all buildings, "
                  "including carports, entries, porches and verandahs, asphalt, "
                  "concrete, brick, stone, permeable pavers, and wood.”")
S2_PERMEABLE = ("Section 2, Permeable Materials (p.31): “Materials including "
                "gravel, river rock less than 5 cm in size, wood chips, bark "
                "mulch, wood decking with spaced boards and other materials "
                "which, in the opinion of the Director of Planning, have fully "
                "permeable characteristics when placed or installed on grade "
                "with no associated layer of impermeable material, such as "
                "plastic sheeting, that would impede the movement of water "
                "directly to the soil below.”")
S2_DIRECTOR = ("Section 2, Permeable Materials (p.31): an unlisted material is "
               "permeable only if, “in the opinion of the Director of Planning”, "
               "it has “fully permeable characteristics when placed or "
               "installed on grade with no associated layer of impermeable "
               "material”")
S426 = ("R1-1 s.4.2.2 (p.16): “The maximum area of impermeable materials "
        "includes site coverage for all buildings.”")
S2_LANEWAY = ("Section 2, Laneway House (p.22): “A detached dwelling unit "
              "constructed in the rear yard of a site on which is situated a "
              "Single Detached House ...”; R1-1 s.2.2.4 (p.5): “Laneway house "
              "is regulated by Section 11 of this by-law and sections 3 and 4 "
              "of this schedule do not apply.”")
S2_SITE = ("Section 2, Site (p.43): “An area of land consisting of 1 or more "
           "adjoining parcels or lots abutting on a street not being a lane, "
           "but does not include a strata lot or a leasehold parcel ...”")
S2_PARKING = ("Section 2, Parking Area (p.30): “An open area of land ... used "
              "or intended to be used to provide space for the parking or "
              "storage of motor vehicles ... but does not include an area "
              "providing 4 or fewer spaces accessory to a residential use”")
S32213 = ("R1-1 s.3.2.2.13 (p.13): “Except where the principal use of the site "
          "is a parking area, the maximum site coverage for any portion of the "
          "site used as a parking area is 30%.”")
S32214 = ("R1-1 s.3.2.2.14 (p.13): “The Director of Planning may increase the "
          "maximum area of impermeable materials for non-dwelling uses if: (a) "
          "there is a demonstrated need ... and (b) the Director of Planning "
          "considers the intent of this schedule ...”")
NOT_LISTED = "Not a Section 2 listed material"

# ------------------------------------------------------------------------------
#  The author's reading, stated once so every result can point at it.
# ------------------------------------------------------------------------------
READING_CONDITIONS = (
    "AUTHOR'S READING. The words “when placed or installed on grade with no "
    "associated layer of impermeable material” are applied to every material "
    "in the Permeable Materials list, not only to the Director's-opinion "
    "limb they sit in. Under this reading a spaced-board deck is permeable "
    "only on grade with nothing impermeable below, and gravel over plastic "
    "sheeting is impermeable. The plain grammar can also be read the other "
    "way: the named materials qualify unconditionally, and only unlisted "
    "materials must meet the condition. This tool takes the stricter reading; "
    "a permit reviewer may take the other. Argue it at the counter, not "
    "after.")

# ==============================================================================
#  THE MATERIAL TABLE  --  Section 2 definitions, as decided by the author
# ==============================================================================
#
#  Every classification names the text it rests on. Five kinds of entry:
#
#  1. BUILDINGS          Section 2 says "all buildings, including carports,
#                        entries, porches and verandahs". Garages, sheds and
#                        laneway houses are buildings too (Section 2 defines
#                        Accessory Building and Laneway House).
#  2. NAMED IMPERMEABLE  Section 2 "Impermeable Materials" names these.
#  3. NAMED PERMEABLE    Section 2 "Permeable Materials" names these, and
#                        (author's reading) only when installed on grade
#                        with no impermeable layer below.
#  4. GROUND             Lawn and planting. Not an installed material; not
#                        counted. An interpretation.
#  5. NOT NAMED          Neither list. Counted IMPERMEABLE: the by-law treats
#                        an unlisted material as permeable only if the
#                        Director of Planning is of that opinion. Water-filled
#                        structures (pools) are impermeable with no Director
#                        note: nothing about a pool shell passes water to soil.
#
#  Wood is handled separately (see classify_wood), because "wood" appears in
#  BOTH definitions. The conditions decide it, not the material name.
#
#  Names are matched after trimming, lower-casing and collapsing spaces, and
#  then through ALIASES. A name that still matches nothing is flagged, with
#  the closest known name as a suggestion.

FOOTPRINT_NOTE = ("Measured as the projected area of the outside of the "
                  "outermost walls: every storey's exterior walls projected to "
                  "the ground, including cantilevers and bay windows, plus "
                  "carports, entries, porches and verandahs. Eaves are not "
                  "walls and are left out. A basement may not project beyond "
                  "the first storey (s.4.3.1).")

BUILDINGS = {
    "building": FOOTPRINT_NOTE,
    "house": FOOTPRINT_NOTE,
    "principal building": FOOTPRINT_NOTE,
    "duplex": FOOTPRINT_NOTE,
    "accessory building": "An accessory building is a building (Section 2, "
                          "Accessory Building, p.1). It counts in both totals.",
    "garage": "A garage is an accessory building. It counts in both totals.",
    "shed": "A shed is an accessory building. It counts in both totals.",
    "carport": "Section 2 names carports as part of the building area.",
    "porch": "Section 2 names entries, porches and verandahs as part of the "
             "building area, covered or not (Section 2, Entry, Porch and "
             "Verandah, p.14).",
    "entry": "Section 2 names entries, porches and verandahs as part of the "
             "building area.",
    "verandah": "Section 2 names entries, porches and verandahs as part of the "
                "building area.",
    "laneway house": "A laneway house is a building on the site, so Section 2's "
                     "“all buildings” reaches it. Counted here in both totals.",
    "roof": "A roof sits on a building. Enter the building's wall projection "
            "(eaves left out), not the roof edge. Counted as a building.",
    "green roof": "A green roof sits on a building. Enter the building's wall "
                  "projection, not the roof. Counted as a building; the "
                  "planting on top does not change the projected area below.",
}
LANEWAY_FLAG = ("Laneway house: s.2.2.4 sends it to Section 11, which is not "
                "in this repository, so whether its footprint counts toward "
                "this site's 75% is unresolved. Counted here. Confirm with "
                "the City.")

NAMED_IMPERMEABLE = {
    "asphalt": "",
    "concrete": "",
    "brick": "",
    "stone": "",
    "permeable pavers": "Named explicitly as IMPERMEABLE, despite the name. "
                        "Swapping a hard surface for pavers gains nothing "
                        "against s.3.2.2.8.",
    "pavers": "Every kind of paver is impermeable under Section 2: concrete "
              "and stone pavers are concrete and stone, and permeable pavers "
              "are named outright.",
}

NAMED_PERMEABLE = {
    "gravel": "",
    "river rock": "",          # decided by its size; see classify()
    "wood chips": "",
    "bark mulch": "",
}

# Permeable versions of materials the Impermeable list names outright. They
# are not "unlisted": the list names concrete and asphalt without any
# qualification, and names permeable pavers too, so a permeable version of a
# listed material gets no exception. The author's decision, 2026-09-24.
LISTED_BASE_MATERIAL = {
    "pervious concrete": "“Concrete” is listed without qualification, "
                         "and permeable pavers are named as impermeable, so "
                         "a permeable version of concrete gets no exception. "
                         "(Author's decision; the Director could be asked.)",
    "porous asphalt": "“Asphalt” is listed without qualification; "
                      "same reasoning as pervious concrete. (Author's "
                      "decision; the Director could be asked.)",
}

# Water-filled structures. Not named in either list, and not a candidate for
# the Director's permeability opinion: a lined shell passes no water to soil.
WATER = {
    "swimming pool": "A pool is not a listed material, and a lined shell "
                     "passes no water to the soil. Counted as impermeable. "
                     "Confirm with the City how the pool deck is measured.",
    "hot tub": "Not a listed material; a tub passes no water to the soil. "
               "Counted as impermeable.",
    "pond": "Not a listed material. A lined pond passes no water to the "
            "soil. Counted as impermeable; an unlined pond could be put to "
            "the Director.",
}

# Known materials that neither list names, with the reasoning for each.
NOT_NAMED_NOTES = {
    "synthetic turf": "",
    "rubber safety surfacing": "Poured-in-place rubber over concrete or "
                               "asphalt is effectively impermeable anyway.",
    "decomposed granite": "Compacted decomposed granite sheds most water; "
                          "whether it is “fully permeable” is the Director's "
                          "call.",
    "grass pavers": "Open-cell pavers planted with grass are not “permeable "
                    "pavers” by name, and not in either list.",
    "resin-bound aggregate": "",
}
NOT_NAMED_DEFAULT = ("Not named in the by-law. Counted as impermeable; the "
                     "Director of Planning may accept it as permeable.")
UNKNOWN_DEFAULT = ("Not one of the names this tool knows. Counted as "
                   "impermeable until it is identified.")

# Natural ground is not an installed "material" in the sense of either
# definition, and nothing in the Impermeable list covers it. Treated as not
# counting toward the limit. This is an interpretation.
GROUND = ("lawn", "grass", "turf", "planting", "planting bed", "garden",
          "soil", "lawn / planting", "vegetable garden", "trees", "meadow")
GROUND_NOTE = ("Natural ground, not an installed material. Not in the "
               "Impermeable list, so not counted. (Interpretation; the "
               "Section 2 lists only name installed materials.)")

WOOD = ("wood", "wood decking", "wood deck", "deck", "decking", "timber",
        "boardwalk")

# Other spellings people use, mapped to the names above.
ALIASES = {
    "detached garage": "garage", "attached garage": "garage",
    "laneway": "laneway house", "lane way house": "laneway house",
    "coach house": "laneway house",
    "verandah ": "verandah", "veranda": "verandah", "front porch": "porch",
    "covered porch": "porch", "entry porch": "entry", "front entry": "entry",
    "dwelling": "building", "principal dwelling": "building",
    "main house": "house", "residence": "house", "footprint": "building",
    "building footprint": "building", "accessory structure": "accessory building",
    "paver": "pavers", "paving": "pavers", "paving stones": "stone",
    "flagstone": "stone", "flagstones": "stone", "slate": "stone",
    "granite": "stone", "natural stone": "stone", "stone slabs": "stone",
    "concrete pavers": "concrete", "concrete paver": "concrete",
    "interlocking pavers": "pavers", "interlocking paving": "pavers",
    "permeable paver": "permeable pavers", "permeable paving": "permeable pavers",
    "porous pavers": "permeable pavers", "pervious pavers": "permeable pavers",
    "permeable interlocking pavers": "permeable pavers",
    "brick pavers": "brick", "bricks": "brick", "clay pavers": "brick",
    "poured concrete": "concrete", "concrete slab": "concrete",
    "exposed aggregate": "concrete", "stamped concrete": "concrete",
    "cement": "concrete", "blacktop": "asphalt", "tarmac": "asphalt",
    "permeable concrete": "pervious concrete", "porous concrete": "pervious concrete",
    "permeable asphalt": "porous asphalt", "pervious asphalt": "porous asphalt",
    "crushed gravel": "gravel", "pea gravel": "gravel", "crushed rock": "gravel",
    "crushed stone": "gravel", "crushed granite": "gravel",
    "drain rock": "river rock", "river stone": "river rock", "cobbles": "river rock",
    "woodchips": "wood chips", "wood chip": "wood chips", "wood mulch": "wood chips",
    "mulch": "bark mulch", "bark": "bark mulch",
    "artificial turf": "synthetic turf", "artificial grass": "synthetic turf",
    "astroturf": "synthetic turf", "rubber mulch": "rubber safety surfacing",
    "rubber surfacing": "rubber safety surfacing", "turf block": "grass pavers",
    "turfstone": "grass pavers", "grass block pavers": "grass pavers",
    "pool": "swimming pool", "spa": "hot tub", "water feature": "pond",
    "lawn/planting": "lawn / planting", "planting beds": "planting bed",
    "garden bed": "planting bed", "shrubs": "planting", "groundcover": "planting",
    "sod": "lawn",
    "wood decking with spaced boards": "wood decking", "spaced decking": "wood decking",
    "cedar deck": "wood decking", "cedar decking": "wood decking",
    "composite decking": "decking", "composite deck": "decking",
    "timber deck": "wood decking", "wooden deck": "wood decking",
}

CLASS_PRIORITY = {"building": 0, "impermeable": 1, "permeable": 2, "ground": 3}
# When two surfaces overlap, the square metre is counted once, in the class
# with the lower number here: a deck over a patio is one impermeable
# footprint; a house drawn over a path is building.


# ==============================================================================
#  NAMES
# ==============================================================================

def normalise(name):
    """Trim, lower-case, turn underscores and hyphens into spaces, and
    collapse runs of spaces, so “Permeable  Pavers” and “permeable_pavers”
    are the same word."""
    text = str(name if name is not None else "")
    text = text.replace("_", " ").replace("-", " ").replace("/", " / ")
    words = text.lower().split()
    return " ".join(words)


def known_names():
    """Every name the table knows, canonical and alias, for suggestions."""
    names = set(BUILDINGS) | set(NAMED_IMPERMEABLE) | set(NAMED_PERMEABLE)
    names |= set(LISTED_BASE_MATERIAL) | set(WATER) | set(NOT_NAMED_NOTES)
    names |= set(GROUND) | set(WOOD) | set(ALIASES)
    return sorted(n.strip() for n in names)


def canonical(name):
    """The table name a material name resolves to."""
    m = normalise(name)
    return ALIASES.get(m, m)


def edit_distance(a, b):
    """Levenshtein distance: how many single-letter edits turn a into b.
    Written as a plain loop so the web page can do exactly the same."""
    prev = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        cur = [i] + [0] * len(b)
        for j in range(1, len(b) + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        prev = cur
    return prev[len(b)]


def suggest(name):
    """The closest known name, if it is close enough to be a likely typo."""
    m = normalise(name)
    if not m:
        return None
    best, best_d = None, None
    for cand in known_names():
        d = edit_distance(m, cand)
        if best_d is None or d < best_d or (d == best_d and cand < best):
            best, best_d = cand, d
    limit = max(2, len(m) // 3)
    if best is not None and best_d <= limit:
        return canonical(best)
    return None


# ==============================================================================
#  CLASSIFICATION
# ==============================================================================

def _stated(s, key):
    """True / False if the design states a condition, None if it does not."""
    v = s.get(key)
    if v is None:
        return None
    return bool(v)


def classify_wood(s):
    """A wood surface is PERMEABLE only if ALL THREE hold:
         - the boards are spaced
         - it is installed on grade
         - there is no impermeable layer underneath
    Otherwise it is IMPERMEABLE under the general "wood" in Section 2.
    A condition the design does not state is not assumed either way: the
    surface is counted impermeable and flagged "not stated".

    A raised Deck (over 600 mm) is not on grade, so it is impermeable, and
    flagged: the by-law does not say clearly how a raised deck is measured.
    A low platform (600 mm or less, a "Patio") takes the three-condition test.
    """
    height = s.get("height_mm", 0) or 0
    if height > RAISED_DECK_MM:
        return ("impermeable", S2_IMPERMEABLE,
                f"Raised deck ({height:g} mm, over {RAISED_DECK_MM} mm) is not "
                f"on grade, so the spaced-decking exception cannot apply "
                f"(author's reading, see the note at the end).",
                "Raised deck – confirm treatment with the City.")

    spaced = _stated(s, "spaced")
    on_grade = _stated(s, "on_grade")
    layer = _stated(s, "impermeable_layer")

    failed = []
    unstated = []
    if spaced is False:
        failed.append("boards not spaced")
    elif spaced is None:
        unstated.append("spacing not stated")
    if on_grade is False:
        failed.append("not installed on grade")
    elif on_grade is None:
        unstated.append("on-grade not stated")
    if layer is True:
        failed.append("impermeable layer underneath")
    elif layer is None:
        unstated.append("layer below not stated")

    if failed:
        return ("impermeable", S2_IMPERMEABLE,
                "Counts as “wood”: " + ", ".join(failed) + ".", None)
    if unstated:
        return ("impermeable", S2_IMPERMEABLE,
                "Counts as “wood” until confirmed: " + ", ".join(unstated) + ".",
                "Wood: state spaced, on_grade and impermeable_layer to test "
                "the spaced-decking exception.")
    return ("permeable", S2_PERMEABLE,
            "Spaced boards, on grade, nothing impermeable below: meets the "
            "spaced-decking exception (author's reading of the conditions).",
            None)


def classify(s):
    """Return (class, source, reason, flag) for one surface.

    class is one of "building", "impermeable", "permeable", "ground".
    Buildings are impermeable too; they are kept separate only so the
    s.3.2.2.7 building-coverage test can be run on them.
    """
    m = canonical(s.get("material", ""))

    if m in BUILDINGS:
        flag = LANEWAY_FLAG if m == "laneway house" else None
        return ("building", S426 if m == "building" else S2_IMPERMEABLE,
                BUILDINGS[m], flag)

    if m in WOOD:
        return classify_wood(s)

    if m in NAMED_IMPERMEABLE:
        return ("impermeable", S2_IMPERMEABLE, NAMED_IMPERMEABLE[m], None)

    if m in LISTED_BASE_MATERIAL:
        return ("impermeable", S2_IMPERMEABLE, LISTED_BASE_MATERIAL[m], None)

    if m in NAMED_PERMEABLE:
        # The "on grade, no impermeable layer" condition is applied to every
        # listed material (author's reading, READING_CONDITIONS). Loose
        # materials are taken to be on grade unless the design says otherwise.
        if _stated(s, "impermeable_layer") is True:
            return ("impermeable", S2_PERMEABLE,
                    f"{m.capitalize()} over an impermeable layer does not meet "
                    f"the Permeable Materials definition (author's reading).",
                    None)
        if _stated(s, "on_grade") is False:
            return ("impermeable", S2_PERMEABLE,
                    f"{m.capitalize()} not installed on grade (a planter, a "
                    f"roof, a slab) does not meet the Permeable Materials "
                    f"definition (author's reading).", None)
        if m == "river rock":
            size = s.get("size_cm")
            if size is None:
                return ("impermeable", S2_PERMEABLE,
                        "River rock is permeable only under 5 cm, and no size "
                        "was given.", "Give the stone size (size_cm) to confirm.")
            if size >= 5:
                return ("impermeable", S2_PERMEABLE,
                        f"River rock of {size:g} cm is not under 5 cm.", None)
            return ("permeable", S2_PERMEABLE,
                    f"River rock of {size:g} cm is under 5 cm, so it is listed "
                    f"as permeable.", None)
        return ("permeable", S2_PERMEABLE, NAMED_PERMEABLE[m], None)

    if m in GROUND:
        return ("ground", NOT_LISTED, GROUND_NOTE, None)

    if m in WATER:
        return ("impermeable", NOT_LISTED, WATER[m], None)

    if m in NOT_NAMED_NOTES:
        note = NOT_NAMED_NOTES[m]
        return ("impermeable", S2_DIRECTOR,
                NOT_NAMED_DEFAULT + (" " + note if note else ""), None)

    guess = suggest(m)
    flag = (f"Unrecognised material “{s.get('material', '')}”. Did you mean "
            f"“{guess}”?" if guess else
            f"Unrecognised material “{s.get('material', '')}”. Check the "
            f"spelling, or add it to the material table.")
    return ("impermeable", NOT_LISTED, UNKNOWN_DEFAULT, flag)


# ==============================================================================
#  GEOMETRY  --  plain arithmetic, no geometry library
#
#  Every surface is cut into triangles, the lot is cut into triangles, and
#  triangles are clipped against each other. Triangles are convex, so the
#  clipping is exact and simple, and summing the pieces gives the exact area
#  of "this surface, on this lot" and "this surface, under that one".
# ==============================================================================

def signed_area(pts):
    """Shoelace formula. Positive for counter-clockwise, negative for
    clockwise. The sign is how orientation is detected."""
    n = len(pts)
    twice = 0.0
    for i in range(n):   # a plain loop, not sum(): see add_up()
        twice += pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1]
    return twice / 2.0


def polygon_area(pts):
    """Area of a simple polygon from its corner points, whichever way round."""
    return abs(signed_area(pts))


def add_up(values):
    """Add numbers left to right, the same way on every Python version.

    From Python 3.12, sum() of floats uses compensated addition, so the same
    design could print a different area on a newer Python than an older one,
    and than the web page. A plain loop gives one answer everywhere.
    """
    total = 0.0
    for v in values:
        total += v
    return total


def rect_points(r):
    """[x, y, width, depth] -> the four corners, counter-clockwise."""
    x, y, w, d = r
    return [[x, y], [x + w, y], [x + w, y + d], [x, y + d]]


def ccw(pts):
    """The same polygon, counter-clockwise."""
    return list(pts) if signed_area(pts) >= 0 else list(reversed(pts))


def _cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _segments_cross(p1, p2, p3, p4):
    """True if segment p1-p2 properly crosses segment p3-p4."""
    d1 = _cross(p3, p4, p1)
    d2 = _cross(p3, p4, p2)
    d3 = _cross(p1, p2, p3)
    d4 = _cross(p1, p2, p4)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)) and \
        d1 != 0 and d2 != 0 and d3 != 0 and d4 != 0


def is_simple(pts):
    """True if no two non-adjacent edges cross. A bow-tie is not simple."""
    n = len(pts)
    for i in range(n):
        for j in range(i + 1, n):
            if abs(i - j) in (1, n - 1):
                continue
            if _segments_cross(pts[i], pts[(i + 1) % n], pts[j], pts[(j + 1) % n]):
                return False
    return True


def _point_in_triangle(p, a, b, c):
    d1 = _cross(a, b, p)
    d2 = _cross(b, c, p)
    d3 = _cross(c, a, p)
    return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))


def triangulate(pts):
    """Cut a simple polygon into triangles by ear clipping.

    Works for any simple polygon, convex or not. Collinear corners (the
    wobbles in a City parcel line) are dropped as zero-area ears. Each
    triangle comes back counter-clockwise.
    """
    poly = ccw(pts)
    idx = list(range(len(poly)))
    tris = []
    guard = 0
    while len(idx) > 3 and guard < 10000:
        guard += 1
        found = False
        for k in range(len(idx)):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            a, b, c = poly[i0], poly[i1], poly[i2]
            turn = _cross(a, b, c)
            if abs(turn) <= 1e-9:          # collinear: a zero-area ear
                idx.pop(k)
                found = True
                break
            if turn < 0:                   # reflex corner: not an ear
                continue
            inside = False
            for j in idx:
                if j in (i0, i1, i2):
                    continue
                if _point_in_triangle(poly[j], a, b, c):
                    inside = True
                    break
            if inside:
                continue
            tris.append([a, b, c])
            idx.pop(k)
            found = True
            break
        if not found:                      # numerical trouble: fan the rest
            for k in range(1, len(idx) - 1):
                tris.append([poly[idx[0]], poly[idx[k]], poly[idx[k + 1]]])
            idx = idx[:3]
            break
    if len(idx) == 3:
        a, b, c = poly[idx[0]], poly[idx[1]], poly[idx[2]]
        if abs(_cross(a, b, c)) > 1e-9:
            tris.append([a, b, c])
    return [t for t in tris if polygon_area(t) > 1e-12]


def convex_clip(subject, clip):
    """Sutherland-Hodgman: the part of convex polygon `subject` inside convex
    polygon `clip`. Both counter-clockwise. Returns [] if nothing is left."""
    out = list(subject)
    n = len(clip)
    for i in range(n):
        if not out:
            break
        a, b = clip[i], clip[(i + 1) % n]
        inp = out
        out = []
        for k in range(len(inp)):
            p, q = inp[k - 1], inp[k]
            p_in = _cross(a, b, p) >= 0
            q_in = _cross(a, b, q) >= 0
            if q_in:
                if not p_in:
                    out.append(_intersect(p, q, a, b))
                out.append(q)
            elif p_in:
                out.append(_intersect(p, q, a, b))
    return out if len(out) >= 3 and polygon_area(out) > 1e-12 else []


def _intersect(p, q, a, b):
    """Where segment p-q crosses the infinite line a-b."""
    dpq = (q[0] - p[0], q[1] - p[1])
    dab = (b[0] - a[0], b[1] - a[1])
    den = dpq[0] * dab[1] - dpq[1] * dab[0]
    if den == 0:
        return list(q)
    t = ((a[0] - p[0]) * dab[1] - (a[1] - p[1]) * dab[0]) / den
    return [p[0] + t * dpq[0], p[1] + t * dpq[1]]


def pieces_area(pieces):
    return add_up(polygon_area(p) for p in pieces)


def intersect_pieces(a_pieces, b_pieces):
    """The pieces of A that lie inside B. Each result is convex."""
    out = []
    for p in a_pieces:
        for q in b_pieces:
            r = convex_clip(p, q)
            if r:
                out.append(r)
    return out


def area_inside_union(pieces, others):
    """Area of `pieces` that lies inside at least one of `others`
    (each a list of convex pieces). Inclusion-exclusion, visiting only the
    combinations that actually overlap."""
    total = [0.0]

    def rec(current, start, sign):
        for k in range(start, len(others)):
            inter = intersect_pieces(current, others[k])
            if not inter:
                continue
            a = pieces_area(inter)
            if a <= 1e-12:
                continue
            total[0] += sign * a
            rec(inter, k + 1, -sign)

    rec(pieces, 0, 1.0)
    return max(total[0], 0.0)


def offset_polygon(pts, d):
    """The polygon pushed outward by d metres (miter corners, capped). Used
    to give the lot line its tolerance band."""
    poly = ccw(pts)
    n = len(poly)
    out = []
    for i in range(n):
        p0, p1, p2 = poly[i - 1], poly[i], poly[(i + 1) % n]
        n1 = _outward_normal(p0, p1)
        n2 = _outward_normal(p1, p2)
        sx, sy = n1[0] + n2[0], n1[1] + n2[1]
        L2 = sx * sx + sy * sy
        if L2 < 0.25:                     # a near-reversal: cap the miter
            out.append([p1[0] + n1[0] * d, p1[1] + n1[1] * d])
        else:
            k = 2.0 * d / L2
            out.append([p1[0] + sx * k, p1[1] + sy * k])
    return out


def _outward_normal(a, b):
    """Unit normal pointing out of a counter-clockwise polygon's edge a-b."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.sqrt(dx * dx + dy * dy)
    if L == 0:
        return (0.0, 0.0)
    return (dy / L, -dx / L)


# ==============================================================================
#  INPUT CHECKING  --  a mistake gets a sentence, not a traceback
# ==============================================================================

class InputError(ValueError):
    """The design file cannot be checked as written. str(err) lists why."""


def _is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _is_point(p):
    return isinstance(p, (list, tuple)) and len(p) == 2 and _is_num(p[0]) and _is_num(p[1])


def validate(example):
    """Return a list of problems, in plain words. Empty means it can be run."""
    problems = []
    if not isinstance(example, dict):
        return ["The design must be a JSON object with “site” and “surfaces”."]
    site = example.get("site")
    if not isinstance(site, dict):
        problems.append("“site” is missing. It needs an “outline”: the lot's "
                        "corners in metres, e.g. [[0,0],[15.2,0],[15.2,39.6],[0,39.6]].")
        site = {}
    outlines = _site_outlines(site)
    if outlines is None:
        problems.append("“site.outline” is missing or not a list of corner "
                        "points. Give at least three [x, y] pairs in metres, or "
                        "“outlines” as a list of such polygons for a site of "
                        "several parcels.")
    else:
        for k, o in enumerate(outlines):
            where = "“site.outline”" if len(outlines) == 1 else f"“site.outlines[{k}]”"
            if not isinstance(o, (list, tuple)) or len(o) < 3 or not all(_is_point(p) for p in o):
                problems.append(f"{where} needs at least three [x, y] number pairs.")
                continue
            if not is_simple(o):
                problems.append(f"{where} crosses itself (a bow-tie). List the "
                                f"corners in order around the lot.")
            elif polygon_area(o) <= 1e-9:
                problems.append(f"{where} has no area. Its corners are in a line "
                                f"or repeat.")
    units = str(site.get("units", example.get("units", "m"))).strip().lower()
    if units not in ("m", "ft", "metres", "meters", "feet"):
        problems.append(f"“units” must be “m” or “ft”, not “{units}”.")
    fr = site.get("frontage_m")
    if fr is not None and not _is_num(fr):
        problems.append("“site.frontage_m” must be a number, not text in quotes.")
    ps = site.get("parking_spaces", example.get("parking_spaces"))
    if ps is not None and (not _is_num(ps) or ps < 0 or int(ps) != ps):
        problems.append("“parking_spaces” must be a whole number of spaces.")

    surfaces = example.get("surfaces")
    if not isinstance(surfaces, list):
        problems.append("“surfaces” is missing or not a list. Use [] for an empty lot.")
        surfaces = []
    seen = set()
    for i, s in enumerate(surfaces):
        tag = f"surface {i + 1}"
        if not isinstance(s, dict):
            problems.append(f"{tag} is not an object.")
            continue
        label = s.get("label", s.get("id", tag))
        tag = f"“{label}”"
        sid = s.get("id", s.get("label", f"surface-{i + 1}"))
        if sid in seen:
            problems.append(f"{tag}: the id “{sid}” is used twice. Ids must be unique.")
        seen.add(sid)
        mat = s.get("material")
        if not isinstance(mat, str) or not mat.strip():
            problems.append(f"{tag} has no “material”. Give the material as a word, "
                            f"e.g. “concrete”, “permeable pavers”, “building”.")
        kinds = [k for k in ("rect", "polygon", "area_m2") if k in s]
        if len(kinds) == 0:
            problems.append(f"{tag} has no geometry. Give “rect”: [x, y, width, depth], "
                            f"or “polygon”: [[x, y], ...], or “area_m2” from an area "
                            f"schedule (counted, but not drawn or checked for overlap).")
        elif len(kinds) > 1:
            problems.append(f"{tag} gives {' and '.join(kinds)}. Give only one.")
        elif kinds[0] == "rect":
            r = s["rect"]
            if not (isinstance(r, (list, tuple)) and len(r) == 4 and all(_is_num(v) for v in r)):
                problems.append(f"{tag}: “rect” must be four numbers [x, y, width, depth] "
                                f"in metres.")
            elif r[2] <= 0 or r[3] <= 0:
                problems.append(f"{tag}: width and depth must be positive numbers "
                                f"(got {r[2]:g} and {r[3]:g}).")
        elif kinds[0] == "polygon":
            p = s["polygon"]
            if not (isinstance(p, (list, tuple)) and len(p) >= 3 and all(_is_point(q) for q in p)):
                problems.append(f"{tag}: “polygon” needs at least three [x, y] number pairs.")
            elif not is_simple(p):
                problems.append(f"{tag}: the polygon crosses itself. List the corners "
                                f"in order around the shape.")
            elif polygon_area(p) <= 1e-9:
                problems.append(f"{tag}: the polygon has no area.")
        else:
            a = s["area_m2"]
            if not _is_num(a) or a <= 0:
                problems.append(f"{tag}: “area_m2” must be a positive number.")
        for key in ("spaced", "on_grade", "impermeable_layer", "parking"):
            if key in s and s[key] is not None and not isinstance(s[key], bool):
                problems.append(f"{tag}: “{key}” must be true or false (no quotes), "
                                f"not {json.dumps(s[key])}.")
        if "height_mm" in s and s["height_mm"] is not None:
            if not _is_num(s["height_mm"]) or s["height_mm"] < 0:
                problems.append(f"{tag}: “height_mm” must be a number of millimetres, "
                                f"zero or more.")
        if "size_cm" in s and s["size_cm"] is not None:
            if not _is_num(s["size_cm"]) or s["size_cm"] <= 0:
                problems.append(f"{tag}: “size_cm” must be a positive number of "
                                f"centimetres.")
    return problems


def _site_outlines(site):
    """The lot as a list of polygons (usually one), or None if absent."""
    if "outlines" in site and isinstance(site["outlines"], list) and site["outlines"]:
        return site["outlines"]
    if "outline" in site:
        return [site["outline"]]
    return None


# ==============================================================================
#  THE OPERATION
# ==============================================================================

S31_WORDS = ("multiplex", "multiple dwelling")
# s.3.1 governs "multiple dwelling containing no more than 8 dwelling units".
# Everything else in the district is "other uses", s.3.2.

DWELLING_USES = ("single detached house", "single detached house with secondary suite",
                 "duplex", "duplex with secondary suite", "infill",
                 "infill single detached house", "infill duplex",
                 "multiple conversion dwelling", "principal dwelling unit with lock off unit",
                 "seniors supportive or independent living housing")
NON_DWELLING_EXAMPLES = ("child day care facility", "church", "community care facility",
                         "school", "neighbourhood grocery store", "urban farm")


def _scale(v, f):
    return v * f


def check(example):
    """Run s.3.2.2.8 (and s.3.2.2.7, s.3.2.2.13) on one example.
    Returns a plain dict. Raises InputError if the design cannot be read."""
    problems = validate(example)
    if problems:
        raise InputError("\n".join(problems))

    site = example["site"]
    warnings = []   # things that may make the answer wrong
    notes = []      # readings and facts the answer rests on

    units = str(site.get("units", example.get("units", "m"))).strip().lower()
    f = FT_TO_M if units in ("ft", "feet") else 1.0
    if f != 1.0:
        notes.append(f"Dimensions were given in feet and converted at "
                     f"{FT_TO_M} m per foot.")

    outlines = [[[_scale(p[0], f), _scale(p[1], f)] for p in o] for o in _site_outlines(site)]
    site_area = add_up(polygon_area(o) for o in outlines)
    if len(outlines) > 1:
        notes.append(f"The site is {len(outlines)} adjoining parcels treated as one "
                     f"zoning site. {S2_SITE}")
    # the lot cut into triangles, twice: exactly, and with its tolerance band
    site_pieces = []
    band_pieces = []
    for o in outlines:
        site_pieces += triangulate(o)
        band_pieces += triangulate(offset_polygon(o, EDGE_TOLERANCE_M))

    # ---- does the provision even apply? ------------------------------------
    applies = True
    why_not = None
    zone = str(site.get("zone", "R1-1")).strip().upper()
    use = normalise(example.get("use", "single detached house")) or "single detached house"
    if zone != "R1-1":
        applies, why_not = False, f"Zone is {zone}, not R1-1."
    elif any(w in use for w in S31_WORDS):
        applies, why_not = False, ("A multiplex (multiple dwelling of 3 to 8 units) "
                                   "is regulated by s.3.1, which sets no numeric "
                                   "impermeability or site-coverage limit. s.3.2.2.8 "
                                   "does not apply to it. Other instruments, or "
                                   "conditions of approval, may still address "
                                   "permeability.")
    elif use == "laneway house":
        notes.append("A laneway house is accessory to a single detached house on "
                     "the same site, so the SITE is assessed under s.3.2 as a "
                     "single detached house. The laneway footprint is counted as "
                     "a building and flagged.")
        use = "single detached house"
    elif use not in DWELLING_USES:
        if "dwelling" in use or "house" in use or "duplex" in use:
            warnings.append(f"Use “{use}” is not one this tool recognises. It is "
                            f"assessed under s.3.2, which governs “all other uses "
                            f"not regulated by section 3.1”.")
        else:
            notes.append(f"Use “{use}” is a non-dwelling use. It is assessed under "
                         f"s.3.2 (“all other uses”), and the Director of Planning "
                         f"may increase the impermeable maximum for it. {S32214}")

    frontage = site.get("frontage_m")
    if frontage is not None:
        frontage = _scale(frontage, f)
    if site_area < MIN_SITE_AREA_M2:
        warnings.append(f"Site is {site_area:,.2f} m², under the s.3.2.2.1 "
                        f"minimum of {MIN_SITE_AREA_M2:g} m². Assessed "
                        f"anyway: under s.3.2.2.9 the Director of Planning may "
                        f"reduce the minimum site area.")
    if frontage is not None and frontage < MIN_FRONTAGE_M:
        warnings.append(f"Frontage {frontage:g} m is under the s.3.2.2.2 "
                        f"minimum of {MIN_FRONTAGE_M:g} m. Assessed anyway: "
                        f"under s.3.2.2.9 the Director of Planning may reduce "
                        f"it, and s.3.2.2.12 provides for a single detached "
                        f"house on a narrower lot on record as of June 24, "
                        f"2014, if the use was previously approved.")
    if f == 1.0 and (site_area > FEET_SUSPECT_AREA_M2 or
                     (frontage is not None and frontage > FEET_SUSPECT_FRONTAGE_M)):
        warnings.append(f"Site is {site_area:,.0f} m²"
                        + (f" and {frontage:g} m wide" if frontage is not None else "")
                        + ". That is very large for an R1-1 lot. Are these "
                        "dimensions in feet? If so add \"units\": \"ft\" to the site.")

    # ---- classify and measure each surface ---------------------------------
    rows = []
    relied_on_reading = False
    for i, s in enumerate(example["surfaces"]):
        sid = s.get("id", s.get("label", f"surface-{i + 1}"))
        label = s.get("label", str(sid))
        cls, source, reason, flag = classify(s)
        if "author's reading" in reason:
            relied_on_reading = True
        if "rect" in s:
            pts = rect_points([_scale(v, f) for v in s["rect"]])
        elif "polygon" in s:
            pts = ccw([[_scale(p[0], f), _scale(p[1], f)] for p in s["polygon"]])
        else:
            pts = None
        if pts is not None:
            gross = polygon_area(pts)
            own_pieces = triangulate(pts)
            # Within the tolerance band around the lot line? Then it is on the
            # lot, in full. Beyond it? Then clip to the exact lot line.
            in_band = pieces_area(intersect_pieces(own_pieces, band_pieces))
            if gross - in_band <= OVERLAP_TOLERANCE_M2:
                inside_pieces, inside, outside = own_pieces, gross, 0.0
            else:
                inside_pieces = intersect_pieces(own_pieces, site_pieces)
                inside = pieces_area(inside_pieces)
                outside = gross - inside
                warnings.append(f"{outside:,.2f} m² of “{label}” lies outside the "
                                f"lot and is not counted (s.3.2.2.8 is a share of "
                                f"the site area).")
        else:
            gross = _scale(_scale(s["area_m2"], f), f)
            inside_pieces = None
            inside, outside = gross, 0.0
            flag = (flag + " " if flag else "") + ("Area given without geometry: "
                                                   "counted as given, not drawn, not "
                                                   "checked against the lot or other "
                                                   "surfaces.")
        rows.append({
            "id": sid, "label": label, "material": s.get("material", ""),
            "canonical": canonical(s.get("material", "")),
            "class": cls, "source": source, "reason": reason, "flag": flag,
            "points": pts, "pieces": inside_pieces,
            "gross_m2": gross, "outside_m2": outside,
            "overlap_m2": 0.0, "area_m2": inside,   # area_m2 becomes the net below
            "parking": bool(s.get("parking", False)),
            "order": i,
        })

    # ---- count every square metre once, in the stricter class ---------------
    order = sorted(rows, key=lambda r: (CLASS_PRIORITY[r["class"]], r["order"]))
    placed = []     # rows already counted, with geometry
    for r in order:
        if r["pieces"] is None:
            continue
        others = [p["pieces"] for p in placed]
        covered = area_inside_union(r["pieces"], others) if others else 0.0
        if covered > OVERLAP_TOLERANCE_M2:
            r["overlap_m2"] = covered
            under = []
            for p in placed:
                ov = pieces_area(intersect_pieces(r["pieces"], p["pieces"]))
                if ov > OVERLAP_TOLERANCE_M2:
                    under.append(f"“{p['label']}” ({ov:,.2f} m²)")
            notes.append(f"“{r['label']}” overlaps {', '.join(under)}. That area "
                         f"is counted once, with the surface counted first (the "
                         f"stricter class), not twice.")
        r["area_m2"] = max(r["gross_m2"] - r["outside_m2"] - r["overlap_m2"], 0.0)
        placed.append(r)

    # ---- totals -------------------------------------------------------------
    def total(*classes):
        return add_up(r["area_m2"] for r in rows if r["class"] in classes)

    building = total("building")
    impermeable = total("building", "impermeable")   # s.4.2.2
    permeable = total("permeable")
    ground = total("ground")
    assigned = add_up(r["area_m2"] for r in rows)
    unassigned = site_area - assigned
    if unassigned < -OVERLAP_TOLERANCE_M2:
        warnings.append(f"Surfaces add up to {assigned:,.2f} m², more than "
                        f"the {site_area:,.2f} m² site. Some area given without "
                        f"geometry is probably counted twice.")
    if unassigned > 0.5 * site_area and rows:
        notes.append(f"{unassigned:,.2f} m² of the lot ({100 * unassigned / site_area:.0f}%) "
                     f"has no surface drawn on it and is taken to be lawn or "
                     f"planting. A driveway or walk left off the plan would pass "
                     f"unnoticed here.")

    imp_limit = IMPERMEABLE_LIMIT * site_area
    bld_limit = BUILDING_LIMIT * site_area
    # "Maximum" means exactly at the limit passes; a hair of tolerance so that
    # floating-point dust never turns 75.000% into a fail.
    eps = 1e-9
    margin = imp_limit - impermeable
    if abs(margin) <= eps:
        margin = 0.0
    near_limit = (abs(margin) < NEAR_LIMIT_M2
                  or abs(bld_limit - building) < NEAR_LIMIT_M2
                  or abs(100 * impermeable / site_area - 100 * IMPERMEABLE_LIMIT) < NEAR_LIMIT_PCT
                  or abs(100 * building / site_area - 100 * BUILDING_LIMIT) < NEAR_LIMIT_PCT)

    # The misconception this tool exists to correct: what the designer would
    # expect if permeable pavers were permeable. NOT a by-law result.
    pavers = add_up(r["area_m2"] for r in rows if r["canonical"] == "permeable pavers")

    # ---- s.3.2.2.13, parking area -------------------------------------------
    spaces = site.get("parking_spaces", example.get("parking_spaces"))
    parking_rows = [r for r in rows if r["parking"]]
    parking_m2 = add_up(r["area_m2"] for r in parking_rows)
    parking_applies = spaces is not None and spaces > PARKING_AREA_SPACES
    parking_pass = None
    if parking_applies:
        parking_pass = parking_m2 <= PARKING_LIMIT * site_area + eps
        notes.append(f"{spaces:g} parking spaces: more than {PARKING_AREA_SPACES}, so the "
                     f"parking surfaces are a Parking Area and s.3.2.2.13 applies. "
                     f"{S32213}")
    elif parking_rows:
        count = (f"{spaces:g} parking space" + ("" if spaces == 1 else "s")
                 if spaces is not None else "an unstated number of parking spaces")
        notes.append(f"Parking surfaces serve {count}. "
                     f"{PARKING_AREA_SPACES} or fewer spaces accessory to a "
                     f"residential use are not a Parking Area (Section 2, p.30), so "
                     f"the 30% limit in s.3.2.2.13 does not apply.")

    if relied_on_reading:
        notes.append(READING_CONDITIONS)

    return {
        "version": VERSION,
        "name": example.get("name", ""),
        "address": site.get("address", ""),
        "use": use,
        "applies": applies,
        "why_not": why_not,
        "site_area_m2": site_area,
        "rows": rows,
        "building_m2": building,
        "building_pct": building / site_area,
        "building_limit_m2": bld_limit,
        "building_pass": building <= bld_limit + eps,
        "impermeable_m2": impermeable,
        "impermeable_pct": impermeable / site_area,
        "impermeable_limit_m2": imp_limit,
        "impermeable_pass": impermeable <= imp_limit + eps,
        "margin_m2": margin,
        "near_limit": near_limit,
        "permeable_m2": permeable,
        "ground_m2": ground,
        "unassigned_m2": max(unassigned, 0.0),
        "pavers_m2": pavers,
        "if_pavers_were_permeable_pct": (impermeable - pavers) / site_area,
        "parking_m2": parking_m2,
        "parking_applies": parking_applies,
        "parking_pass": parking_pass,
        "parking_limit_m2": PARKING_LIMIT * site_area,
        "warnings": warnings,
        "notes": notes,
    }


# ==============================================================================
#  PLAIN-LANGUAGE REPORT
# ==============================================================================

def _fit(text, width):
    text = str(text)
    return text if len(text) <= width else text[:width - 1] + "…"


def report(r):
    out = []
    line = "=" * 78
    out.append(line)
    out.append(f" {r['address']}  --  {r['name']}")
    out.append(line)

    if not r["applies"]:
        out.append(f"\n NOT ASSESSED. {r['why_not']}")
        if r["warnings"]:
            out.append("\n WARNINGS")
            for w in r["warnings"]:
                out.append(f"   - {w}")
        out.append(line)
        return "\n".join(out)

    pct_fmt = ".4f" if r["near_limit"] else ".2f"
    m2_fmt = ",.3f" if r["near_limit"] else ",.2f"

    out.append(f" Site area {r['site_area_m2']:,.2f} m² (parcel polygon)   "
               f"use: {r['use']}\n")
    out.append(f" {'surface':<22}{'material':<20}{'area m²':>9}  counts as")
    out.append(" " + "-" * 76)
    label = {"building": "IMPERMEABLE (building)", "impermeable": "IMPERMEABLE",
             "permeable": "permeable", "ground": "not counted"}
    for row in r["rows"]:
        out.append(f" {_fit(row['label'], 21):<22}{_fit(row['material'], 19):<20}"
                   f"{row['area_m2']:>9,.2f}  {label[row['class']]}")
        if row["canonical"] != normalise(row["material"]) and row["canonical"]:
            out.append(f"   {'':<20}= “{row['canonical']}” in the by-law's words")
        if row["outside_m2"] > OVERLAP_TOLERANCE_M2 or row["overlap_m2"] > OVERLAP_TOLERANCE_M2:
            parts = [f"drawn {row['gross_m2']:,.2f}"]
            if row["outside_m2"] > OVERLAP_TOLERANCE_M2:
                parts.append(f"outside the lot {row['outside_m2']:,.2f}")
            if row["overlap_m2"] > OVERLAP_TOLERANCE_M2:
                parts.append(f"under another surface {row['overlap_m2']:,.2f}")
            out.append(f"   {'':<20}({', '.join(parts)} → counted {row['area_m2']:,.2f})")
        if row["reason"]:
            out.append(f"   {'':<20}- {row['reason']}")
        if row["flag"]:
            out.append(f"   {'':<20}! {row['flag']}")
    if r["unassigned_m2"] > 0.005:
        out.append(f" {'(rest of lot)':<22}{'no surface drawn':<20}"
                   f"{r['unassigned_m2']:>9,.2f}  not counted (taken as lawn / planting)")

    def verdict(ok):
        return "PASS" if ok else "FAIL"

    out.append("\n RESULT")
    out.append(f"   s.3.2.2.7  buildings    {r['building_m2']:>8{m2_fmt}} m²  "
               f"= {100 * r['building_pct']:5{pct_fmt}}%  "
               f"(limit {100 * BUILDING_LIMIT:g}% = "
               f"{r['building_limit_m2']:{m2_fmt}})  {verdict(r['building_pass'])}")
    out.append(f"   s.3.2.2.8  impermeable  {r['impermeable_m2']:>8{m2_fmt}} m²  "
               f"= {100 * r['impermeable_pct']:5{pct_fmt}}%  "
               f"(limit {100 * IMPERMEABLE_LIMIT:g}% = "
               f"{r['impermeable_limit_m2']:{m2_fmt}})  "
               f"{verdict(r['impermeable_pass'])}")
    m = r["margin_m2"]
    if r["impermeable_pass"]:
        out.append(f"              {m:{m2_fmt}} m² of impermeable surface still "
                   f"available.")
    else:
        out.append(f"              Over by {-m:{m2_fmt}} m². Reduce the impermeable "
                   f"total by at least that much: remove it, plant it, or")
        out.append(f"              change it to a listed permeable material.")
    if r["near_limit"]:
        out.append("              (Closer to the limit than two decimals show. The "
                   "verdict uses unrounded areas.)")
    if r["parking_applies"]:
        out.append(f"   s.3.2.2.13 parking area {r['parking_m2']:>8,.2f} m²  "
                   f"= {100 * r['parking_m2'] / r['site_area_m2']:5.2f}%  "
                   f"(limit {100 * PARKING_LIMIT:g}% = "
                   f"{r['parking_limit_m2']:,.2f})  {verdict(r['parking_pass'])}")

    if r["pavers_m2"] > 0:
        out.append(f"\n WHY THIS SURPRISES PEOPLE")
        out.append(f"   {r['pavers_m2']:,.2f} m² of this design is permeable "
                   f"pavers. If pavers counted as permeable,")
        out.append(f"   the total would be "
                   f"{100 * r['if_pavers_were_permeable_pct']:.2f}%. They do "
                   f"not: Section 2 names them as impermeable.")

    if r["warnings"]:
        out.append("\n WARNINGS")
        for w in r["warnings"]:
            out.append(f"   - {w}")
    if r["notes"]:
        out.append("\n NOTES")
        for n in r["notes"]:
            out.append(f"   - {n}")
    out.append(line)
    return "\n".join(out)


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main(argv):
    if len(argv) < 2:
        print("usage: python3 tool/impermeable_check.py examples/<file>.json")
        return 2
    status = 0
    for p in argv[1:]:
        try:
            example = load(p)
        except FileNotFoundError:
            print(f"Cannot find {p}. Paths are relative to where you run the command.")
            status = 2
            continue
        except json.JSONDecodeError as e:
            print(f"{p} is not valid JSON: {e.msg} at line {e.lineno}, column {e.colno}.")
            status = 2
            continue
        try:
            print(report(check(example)))
        except InputError as e:
            print(f"Cannot check {p}:")
            for problem in str(e).split("\n"):
                print(f"   - {problem}")
            status = 2
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv))
