"""
Write the examples, and the Python tool's own answers, into the web page.

WHY THIS EXISTS
  The web page (tool/web/index.html) redoes the s.3.2.2.8 calculation in
  JavaScript, so it can run in a browser with nothing installed. Two copies of
  one calculation can drift apart. To stop that, this script runs the REAL
  Python operation (impermeable_check.py) over a set of cases and writes the
  answers into the page. Every time the page loads, it recomputes those same
  cases in JavaScript and says, at the bottom, whether it agrees.

  The lots the unit tests use are the lots exported here, so a bug the tests
  would catch in Python is also caught in the browser (review C, F6).

HOW TO RUN IT
     python3 tool/export_web_data.py          rewrite the data in the page
     python3 tool/export_web_data.py --check  only report whether it is current

  Run it after changing impermeable_check.py or anything in examples/.
  The unit tests fail if you forget (test_web_page_data_is_current).
"""

import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import impermeable_check as ic  # noqa: E402

PAGE = os.path.join(HERE, "web", "index.html")
DATA_FILE = os.path.join(HERE, "web", "data.js")   # the page loads this file
EXAMPLES = os.path.join(HERE, "..", "examples")

# The examples the page offers, in the order it offers them.
EXAMPLE_FILES = [
    ("as-designed", "3528-w-30th-ave.json"),
    ("revised", "3528-w-30th-ave-gravel-apron.json"),
    ("laneway", "33ft-lot-laneway-house.json"),
]

# Every material the page's dropdown offers: the table's own names, grouped.
MATERIAL_GROUPS = [
    ("Buildings", ["building", "house", "porch", "entry", "verandah", "carport",
                   "garage", "shed", "accessory building", "laneway house"]),
    ("Impermeable, named", ["asphalt", "concrete", "brick", "stone", "pavers",
                            "permeable pavers", "pervious concrete", "porous asphalt"]),
    ("Wood: the conditions decide", ["wood decking", "wood"]),
    ("Permeable, named", ["gravel", "river rock", "wood chips", "bark mulch"]),
    ("Not named in the by-law", ["synthetic turf", "rubber safety surfacing",
                                 "decomposed granite", "grass pavers",
                                 "resin-bound aggregate", "swimming pool", "hot tub", "pond"]),
    ("Not counted", ["lawn", "planting", "garden"]),
]
MATERIALS = [m for _, ms in MATERIAL_GROUPS for m in ms]

SQUARE_20 = [[0, 0], [20, 0], [20, 20], [0, 20]]


def load_examples():
    examples = {}
    for key, fn in EXAMPLE_FILES:
        with open(os.path.join(EXAMPLES, fn), encoding="utf-8") as f:
            examples[key] = json.load(f)
    return examples


def classify_cases():
    """Every material, every alias, and every condition that matters."""
    cases = []
    names = sorted(set(ic.known_names()) | set(MATERIALS))
    for m in names:
        cases.append({"material": m})
        if ic.canonical(m) in ic.NAMED_PERMEABLE:
            cases.append({"material": m, "impermeable_layer": True})
            cases.append({"material": m, "on_grade": False})
    for m in ("wood", "wood decking", "composite decking"):
        for spaced in (None, False, True):
            for on_grade in (None, False, True):
                for layer in (None, False, True):
                    for h in (0, 600, 601):
                        c = {"material": m, "height_mm": h}
                        if spaced is not None:
                            c["spaced"] = spaced
                        if on_grade is not None:
                            c["on_grade"] = on_grade
                        if layer is not None:
                            c["impermeable_layer"] = layer
                        cases.append(c)
    for size in (None, 0.5, 3, 4.99, 5, 7.5):
        c = {"material": "river rock"}
        if size is not None:
            c["size_cm"] = size
        cases.append(c)
    # names with stray capitals, spaces, underscores and typos
    cases += [{"material": "  Permeable Pavers "}, {"material": "GRAVEL"},
              {"material": "Building"}, {"material": "permeable_pavers"},
              {"material": "permable pavers"}, {"material": "Artificial Turf"},
              {"material": "window well"}, {"material": "concrete pavers"},
              {"material": "Detached Garage"}, {"material": "xyzzy"},
              {"material": ""}, {"material": "lawn / planting"}]
    return cases


def lot(surfaces, use="single detached house", name=None, **site):
    s = {"address": "test", "outline": SQUARE_20}
    s.update(site)
    ex = {"name": name or "test", "site": s, "use": use, "surfaces": surfaces}
    return ex


def sf(id_, material, rect=None, **kw):
    s = {"id": id_, "label": id_, "material": material}
    if rect is not None:
        s["rect"] = rect
    s.update(kw)
    return s


def fixed_check_cases(examples):
    """The unit-test lots, so the page is held to the same cases as the tests,
    plus the lots review C found missing from the page's self-check."""
    deck = dict(spaced=True, on_grade=False, impermeable_layer=False, height_mm=1500)
    return list(examples.values()) + [
        lot([sf("a", "concrete", [0, 0, 20, 15])], name="exactly 75%"),
        lot([sf("a", "concrete", [0, 0, 20, 15.05])], name="one over"),
        lot([sf("a", "concrete", [0, 0, 20, 15.001])], name="near the limit"),
        lot([sf("h", "building", [0, 0, 10, 10])], name="building in both totals"),
        lot([sf("h", "building", [0, 0, 20, 11])], name="building over 50%"),
        lot([], use="multiplex", name="multiplex"),
        lot([], use="Multiple Dwelling", name="multiple dwelling"),
        lot([], use="infill", name="infill"),
        lot([], use="child day care facility", name="non-dwelling use"),
        lot([], use="duplex with secondary suite", name="duplex with suite"),
        lot([], use="Single_Detached_House", name="use with underscores"),
        lot([sf("l", "laneway house", [0, 0, 6, 7])], use="laneway house", name="laneway use"),
        lot([], zone="RT-7", name="other zone"),
        lot([sf("a", "concrete", [15, 15, 10, 10])], zone="RT-7", name="other zone with warning"),
        lot([], zone=" r1-1 ", name="zone in lower case"),
        lot([sf("a", "stone", [0, 0, 5, 5]), sf("b", "concrete", [4, 4, 5, 5])], name="overlap"),
        lot([sf("a", "asphalt", [18, 18, 5, 5])], name="pad past the corner"),
        lot([sf("a", "concrete", [0, 15, 3, 10])], name="strip past the lot line"),
        lot([sf("p", "gravel", polygon=[[1, 1], [4, 1], [4, 4], [1, 3]])], name="polygon bed"),
        lot([sf("p", "gravel", polygon=[[1, 1], [1, 3], [4, 4], [4, 1]])], name="clockwise polygon"),
        lot([sf("a", "concrete", [0, 0, 20, 20]), sf("b", "brick", [0, 0, 20, 20])], name="two full slabs"),
        lot([], frontage_m=6.5, name="narrow lot"),
        lot([], frontage_m=7.3, name="frontage exactly 7.3"),
        {"name": "site exactly 306", "site": {"outline": [[0, 0], [17, 0], [17, 18], [0, 18]]}, "surfaces": []},
        {"name": "site just under 306", "site": {"outline": [[0, 0], [17, 0], [17, 17.99], [0, 17.99]]}, "surfaces": []},
        {"name": "margin snaps to zero", "site": {"outline": [[0, 0], [10.2, 0], [10.2, 39.6], [0, 39.6]]},
         "surfaces": [sf("a", "concrete", [0, 0, 10.2, 29.7])]},
        lot([sf("s", "asphalt", [0, 0, 1, 1])], outline=[[0, 0], [10, 0], [10, 20], [0, 20]], name="tiny pad"),
        lot([sf("p", "Permeable Pavers", [0, 0, 10, 10])], name="pavers in capitals"),
        lot([sf("p", "permeable pavers", [0, 0, 10, 10])], name="pavers only"),
        lot([sf("p", "stone", [1, 1, 5, 4]), sf("d", "wood decking", [1, 1, 5, 4], **deck)], name="deck over patio"),
        lot([sf("a", "concrete", [0, 0, 10, 10]),
             sf("b", "brick", polygon=[[5, 5], [15, 5], [15, 15], [5, 15]])], name="polygon over rect"),
        lot([sf("a", "concrete", [0, 0, 10, 10]), sf("b", "brick", [5, 5, 10, 10]),
             sf("c", "stone", [5, 0, 10, 10])], name="three-way overlap"),
        lot([sf("g", "gravel", [0, 0, 10, 10]), sf("h", "building", [5, 5, 10, 10])], name="building over gravel"),
        lot([sf("a", "concrete", [0, 0, 20.019, 10])], name="corner 1.9 cm out"),
        lot([sf("a", "concrete", [0, 0, 20.021, 10])], name="corner 2.1 cm out"),
        {"name": "U-shaped lot", "site": {"outline": [[0, 0], [30, 0], [30, 10], [20, 10], [20, 4], [10, 4], [10, 10], [0, 10]]},
         "surfaces": [sf("a", "asphalt", [0, 6, 30, 4])]},
        lot([sf("h", "building", [1.2, 13, 7.66, 14]), sf("p", "porch", [3, 27, 3, 2]),
             sf("g", "garage", [1.2, 0.9, 3.6, 6.1]), sf("l", "laneway house", [5, 0.9, 4.8, 7.6])],
            outline=[[0, 0], [10.06, 0], [10.06, 37.19], [0, 37.19]], name="garage and laneway"),
        lot([sf("h", "building", area_m2=120)], name="area only"),
        lot([sf("h", "building", area_m2=250), sf("p", "concrete", area_m2=200)], name="areas over the site"),
        lot([sf("d", "wood decking", [0, 0, 3, 3])], name="deck with nothing stated"),
        lot([sf("d", "wood decking", [0, 0, 3, 3], spaced=True, on_grade=True, impermeable_layer=False,
                height_mm=900)], name="raised deck"),
        lot([sf("r", "river rock", [0, 0, 3, 3])], name="river rock no size"),
        lot([sf("g", "gravel", [0, 0, 3, 3], impermeable_layer=True)], name="gravel over plastic"),
        lot([sf("t", "permable pavers", [0, 0, 3, 3])], name="typo"),
        lot([sf("t", "artificial turf", [0, 0, 3, 3])], name="alias"),
        lot([sf("w", "swimming pool", [0, 0, 4, 8]), sf("x", "hot tub", [5, 0, 2, 2])], name="pool"),
        {"name": "feet", "site": {"outline": [[0, 0], [33, 0], [33, 122], [0, 122]], "units": "ft"},
         "surfaces": [sf("h", "building", [4, 40, 25, 50])]},
        {"name": "feet typed as metres", "site": {"outline": [[0, 0], [33, 0], [33, 122], [0, 122]],
                                                  "frontage_m": 33}, "surfaces": []},
        lot([sf("p", "asphalt", [0, 0, 10, 10], parking=True)], parking_spaces=2, name="parking 2 spaces"),
        lot([sf("p", "asphalt", [0, 0, 13, 10], parking=True)], parking_spaces=5, name="parking 5 spaces"),
        {"name": "two parcels", "site": {"outlines": [[[0, 0], [10, 0], [10, 20], [0, 20]],
                                                      [[10, 0], [20, 0], [20, 20], [10, 20]]]},
         "surfaces": [sf("h", "building", [5, 5, 10, 10])]},
        lot([{"material": "concrete", "rect": [0, 0, 5, 5]}], name="no id or label"),
        lot([sf("h", "building", [0, 0, 10, 10])] + [sf(f"g{i}", "garden", [11, i * 2, 8, 2]) for i in range(4)],
            name="mostly garden"),
    ]


def invalid_cases():
    """Inputs the tool must refuse, with the sentences it must say."""
    return [
        lot([sf("b", "concrete", polygon=[[0, 0], [10, 10], [10, 0], [0, 10]])], name="bowtie"),
        lot([sf("a", "concrete", [10, 0, -10, 15])], name="negative width"),
        lot([sf("a", "concrete", [0, 0, 0, 5])], name="zero width"),
        lot([sf("a", "concrete", ["0", "0", "5", "5"])], name="strings"),
        lot([sf("a", "concrete", [0, 0, 5])], name="three numbers"),
        lot([sf("d", "wood decking", [0, 0, 3, 3], height_mm="900")], name="height in quotes"),
        lot([sf("d", "wood decking", [0, 0, 3, 3], spaced="yes")], name="string boolean"),
        lot([sf("r", "river rock", [0, 0, 3, 3], size_cm=0)], name="size zero"),
        lot([{"id": "a", "label": "a", "rect": [0, 0, 5, 5]}], name="no material"),
        lot([{"id": "a", "label": "a", "material": None, "rect": [0, 0, 5, 5]}], name="null material"),
        lot([{"id": "a", "label": "House", "material": "building", "rectangle": [0, 0, 5, 5]}], name="wrong key"),
        lot([sf("a", "concrete", [0, 0, 5, 5], polygon=[[0, 0], [1, 0], [1, 1]])], name="rect and polygon"),
        lot([sf("a", "concrete", [0, 0, 5, 5]), sf("a", "brick", [6, 6, 2, 2])], name="duplicate ids"),
        {"name": "no outline", "site": {"address": "t"}, "surfaces": []},
        {"name": "two-point lot", "site": {"outline": [[0, 0], [10, 0]]}, "surfaces": []},
        {"name": "flat lot", "site": {"outline": [[0, 0], [10, 0], [20, 0]]}, "surfaces": []},
        {"name": "bowtie lot", "site": {"outline": [[0, 0], [10, 10], [10, 0], [0, 10]]}, "surfaces": []},
        {"name": "no surfaces", "site": {"outline": SQUARE_20}},
        {"name": "frontage in quotes", "site": {"outline": SQUARE_20, "frontage_m": "6.0"}, "surfaces": []},
        {"name": "bad units", "site": {"outline": SQUARE_20, "units": "yards"}, "surfaces": []},
        lot([sf("a", "concrete", [0, 0, 5, 5], area_m2=25)], name="rect and area"),
        lot([sf("a", "concrete", area_m2=-3)], name="negative area"),
        {"name": "half spaces", "site": {"outline": SQUARE_20, "parking_spaces": 2.5}, "surfaces": []},
    ]


def random_check_cases(site, n=80, seed=540):
    """Random designs on the demo lot. Deterministic, so reruns match."""
    rng = random.Random(seed)
    uses = (["single detached house"] * 8 + ["duplex", "multiplex",
            "single detached house with secondary suite", "laneway house",
            "infill", "church"])
    names = ic.known_names() + MATERIALS + ["building"] * 4 + ["permeable pavers"] * 4 + \
        ["permable pavers", "window well", "Concrete", "Gravel "]
    out = []
    for i in range(n):
        surfaces = []
        for j in range(rng.randint(0, 9)):
            m = rng.choice(names)
            s = {"id": f"s{j}", "label": f"Surface {j}", "material": m}
            kind = rng.random()
            if kind < 0.7:
                s["rect"] = [round(rng.uniform(-2, 15), 2), round(rng.uniform(-2, 38), 2),
                             round(rng.uniform(0.5, 13), 2), round(rng.uniform(0.5, 24), 2)]
            elif kind < 0.9:
                cx, cy = rng.uniform(0, 15), rng.uniform(0, 39)
                k = rng.randint(3, 6)
                pts = []
                for t in range(k):
                    ang = 6.283185307179586 * (t + rng.uniform(0, 0.6)) / k
                    rad = rng.uniform(1.0, 6.0)
                    pts.append([round(cx + rad * __import__("math").cos(ang), 2),
                                round(cy + rad * __import__("math").sin(ang), 2)])
                if rng.random() < 0.3:
                    pts.reverse()
                s["polygon"] = pts
            else:
                s["area_m2"] = round(rng.uniform(1, 60), 1)
            if ic.canonical(m) in ic.WOOD or rng.random() < 0.2:
                if rng.random() < 0.8:
                    s["spaced"] = rng.random() < 0.6
                if rng.random() < 0.8:
                    s["on_grade"] = rng.random() < 0.7
                if rng.random() < 0.8:
                    s["impermeable_layer"] = rng.random() < 0.2
                s["height_mm"] = rng.choice([0, 150, 450, 600, 601, 750, 1200])
            if ic.canonical(m) == "river rock" and rng.random() < 0.8:
                s["size_cm"] = rng.choice([1, 2.5, 4, 5, 8])
            if rng.random() < 0.15:
                s["parking"] = True
            surfaces.append(s)
        site_i = dict(site)
        if rng.random() < 0.05:
            site_i["zone"] = "RT-7"
        if rng.random() < 0.3:
            site_i["parking_spaces"] = rng.choice([0, 1, 2, 4, 5, 6])
        out.append({"name": f"random {i}", "site": site_i,
                    "use": rng.choice(uses), "surfaces": surfaces})
    return out


ROW_KEYS = ("id", "label", "canonical", "area_m2", "gross_m2", "outside_m2", "overlap_m2",
            "class", "source", "reason", "flag", "parking")
RESULT_KEYS = ("applies", "why_not", "site_area_m2", "building_m2", "building_pct",
               "building_pass", "impermeable_m2", "impermeable_pct",
               "impermeable_pass", "impermeable_limit_m2", "margin_m2", "near_limit",
               "permeable_m2", "ground_m2", "unassigned_m2", "pavers_m2",
               "if_pavers_were_permeable_pct", "parking_m2", "parking_applies",
               "parking_pass", "warnings", "notes", "use")


def expected_check(result):
    """The parts of a check() result the page must reproduce."""
    e = {k: result[k] for k in RESULT_KEYS}
    e["rows"] = [{k: r[k] for k in ROW_KEYS} for r in result["rows"]]
    e["display"] = display(result)
    return e


def display(r):
    """The numbers exactly as the page prints them, formatted by Python.

    Mirrors the page's own choices: the margin is shown as a positive amount,
    "to spare" when it passes and "over by" when it fails; near the limit the
    page shows four decimals of percent and three of area.
    """
    m = r["margin_m2"]
    pd, ad = (4, 3) if r["near_limit"] else (2, 2)
    return {
        "site": f"{r['site_area_m2']:,.2f}",
        "impermeable": f"{r['impermeable_m2']:,.{ad}f}",
        "limit": f"{r['impermeable_limit_m2']:,.{ad}f}",
        "margin": f"{m:,.{ad}f}" if r["impermeable_pass"] else f"{-m:,.{ad}f}",
        "building": f"{r['building_m2']:,.{ad}f}",
        "impermeable_pct": f"{100 * r['impermeable_pct']:.{pd}f}",
        "building_pct": f"{100 * r['building_pct']:.{pd}f}",
        "unassigned": f"{r['unassigned_m2']:.2f}",
        "rows": [f"{x['area_m2']:.2f}" for x in r["rows"]],
        "shares": [f"{100 * x['area_m2'] / r['site_area_m2']:.1f}" for x in r["rows"]],
    }


def format_cases(seed=7):
    """Numbers of the kinds the page prints, each with Python's own formatting.

    Includes the values that exposed the old rounding bug, true ties (which
    Python rounds to even), negatives and minus zero, then ~1,700 areas, sums
    and percentages built from dimensions in 0.05 m steps, the way people type.
    """
    rng = random.Random(seed)
    fixed = [454.775, 0.675 * 1.0, 1.5 * 1.5 * 0.3, 454.865, 6.075, 1.35 * 4.5,
             0.125, 0.375, 0.625, 2.5, 1.005, 2.675, 1.015, -0.125, -1.005,
             -0.0, 0.0, 1e-9, -1e-9, 0.005, 0.015, 1234567.891, 302.94,
             0.75 * 602.0449, 999.995, 1000.005, 12.5, 0.1 + 0.2, 75.005, 300.004]
    vals = list(fixed)
    step = lambda: round(rng.randint(1, 400) * 0.05, 2)
    for _ in range(700):
        vals.append(step() * step())
    for _ in range(600):
        acc = 0.0
        for _ in range(rng.randint(2, 6)):
            acc += step() * step()
        vals.append(acc)
    for _ in range(400):
        vals.append(100 * (step() * step()) / (step() * step() + 300))
    cases = []
    for i, x in enumerate(vals):
        cases.append([x, 2, False, f"{x:.2f}"])
        if i % 2 == 0:
            cases.append([x, 2, True, f"{x:,.2f}"])
        if i % 5 == 0:
            cases.append([x, 1, False, f"{x:.1f}"])
        if i % 7 == 0:
            cases.append([x, 3, True, f"{x:,.3f}"])
            cases.append([x, 4, False, f"{x:.4f}"])
    g_vals = [0, 150, 600, 601, 900, 1200, 4.99, 0.5, 7.3, 6.5, 306.0, 3, 2.5,
              1e-05, 1234567, 0.0001, 75.0, 50.0, 12.25, 33, 10.06]
    g = [[x, f"{x:g}"] for x in g_vals]
    return {"fixed": cases, "g": g}


RULE_NAMES = (
    "VERSION", "IMPERMEABLE_LIMIT", "BUILDING_LIMIT", "PARKING_LIMIT", "PARKING_AREA_SPACES",
    "RAISED_DECK_MM", "MIN_SITE_AREA_M2", "MIN_FRONTAGE_M", "FEET_SUSPECT_AREA_M2",
    "FEET_SUSPECT_FRONTAGE_M", "FT_TO_M", "OVERLAP_TOLERANCE_M2", "EDGE_TOLERANCE_M",
    "NEAR_LIMIT_M2", "NEAR_LIMIT_PCT",
    "S2_IMPERMEABLE", "S2_PERMEABLE", "S2_DIRECTOR", "S426", "S2_LANEWAY", "S2_SITE",
    "S2_PARKING", "S32213", "S32214", "NOT_LISTED", "READING_CONDITIONS",
    "FOOTPRINT_NOTE", "BUILDINGS", "LANEWAY_FLAG", "NAMED_IMPERMEABLE", "NAMED_PERMEABLE",
    "LISTED_BASE_MATERIAL", "WATER", "NOT_NAMED_NOTES", "NOT_NAMED_DEFAULT",
    "UNKNOWN_DEFAULT", "GROUND", "GROUND_NOTE", "WOOD", "ALIASES", "CLASS_PRIORITY",
    "S31_WORDS", "DWELLING_USES")


def build():
    examples = load_examples()
    ccases = classify_cases()
    checks = (fixed_check_cases(examples) +
              random_check_cases(examples["as-designed"]["site"]))
    # The rule tables and the wording of every reason come straight from the
    # Python file, so the page never holds its own copy of a number or a
    # sentence. Only the decision logic is repeated in JavaScript.
    rules = {k: getattr(ic, k) for k in RULE_NAMES}
    return {
        "note": "Written by tool/export_web_data.py from impermeable_check.py. "
                "Do not edit by hand.",
        "rules": rules,
        "materials": MATERIALS,
        "material_groups": MATERIAL_GROUPS,
        "known_names": ic.known_names(),
        "examples": examples,
        "classify_cases": [{"input": c, "expect": list(ic.classify(c))} for c in ccases],
        "format_cases": format_cases(),
        "check_cases": [{"input": c, "expect": expected_check(ic.check(c))} for c in checks],
        "invalid_cases": [{"input": c, "expect": ic.validate(c)} for c in invalid_cases()],
        "suggest_cases": [{"input": n, "expect": ic.suggest(n)} for n in
                          ("permable pavers", "window well", "concrete", "gravle",
                           "artificial turf", "xyzzy", "", "lawn/planting", "decking",
                           "porch ", "Garage", "perm pavers", "pavement")],
    }


def block(data):
    """The contents of tool/web/data.js: one assignment the page reads.

    ASCII-only JSON, so there are no character-set surprises when the page is
    opened straight from disk, and "</" escaped so it can never close a tag.
    A separate file rather than a block inside index.html keeps the page's
    own source readable and its diffs small (review C, F11).
    """
    text = json.dumps(data, ensure_ascii=True, indent=None, separators=(",", ":"))
    text = text.replace("</", "<\\/")
    return ("// Written by tool/export_web_data.py from impermeable_check.py. "
            "Do not edit by hand.\n"
            f"window.TOOL_DATA = {text};\n")


def current_block():
    """What tool/web/data.js holds now, or "" if it does not exist yet."""
    if not os.path.exists(DATA_FILE):
        return ""
    with open(DATA_FILE, encoding="utf-8") as f:
        return f.read()


def main():
    check_only = "--check" in sys.argv
    new = block(build())
    old = current_block()
    if check_only:
        if old == new:
            print("web page data is current")
            return 0
        print("web page data is OUT OF DATE -- run: python3 tool/export_web_data.py")
        return 1
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        f.write(new)
    d = build()
    print(f"wrote {len(d['classify_cases'])} classification cases, "
          f"{len(d['check_cases'])} lot cases and {len(d['invalid_cases'])} refusals "
          f"into {os.path.relpath(DATA_FILE)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
