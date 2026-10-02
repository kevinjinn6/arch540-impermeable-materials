"""Test cases for the s.3.2.2.8 check.

The brief asks for "a typical case, a boundary or conflicting case, and a case
with missing information or outside the tool's scope". Each test below states
the case, the by-law text it rests on, and the expected result, so it can be
checked by hand without trusting the code.

Tests marked [A], [B], [C] pin a defect found by one of the three outside
reviews of 2026-10-02 (docs/reviews/), so it stays fixed.

Run:   python3 -m unittest tool/test_impermeable_check.py -v
"""
import io
import os
import sys
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import impermeable_check as ic  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
EXAMPLES = os.path.join(HERE, "..", "examples")

SQUARE_20 = [[0, 0], [20, 0], [20, 20], [0, 20]]   # a 400 m2 test lot


def lot(surfaces, use="single detached house", **site):
    s = {"address": "test", "outline": SQUARE_20}
    s.update(site)
    return {"site": s, "use": use, "surfaces": surfaces}


def sf(id_, material, rect=None, **kw):
    s = {"id": id_, "label": id_, "material": material}
    if rect is not None:
        s["rect"] = rect
    s.update(kw)
    return s


def cls(**s):
    return ic.classify(s)[0]


def problems(example):
    try:
        ic.check(example)
    except ic.InputError as e:
        return str(e).split("\n")
    return []


# ==============================================================================
#  Typical case: the demo lot
# ==============================================================================

class TypicalCase(unittest.TestCase):
    """3528 W 30th Ave, as designed and as revised. The hand-worked table in
    sources/r1-1-impermeable-extract.md gives the same numbers."""

    def test_demo_fails_because_of_the_pavers(self):
        r = ic.check(ic.load(os.path.join(EXAMPLES, "3528-w-30th-ave.json")))
        # 294.40 + 40.00 + 7.368 + 20.70 + 92.40 = 454.868 m2 (hand sum)
        self.assertAlmostEqual(r["impermeable_m2"], 454.868, places=2)
        self.assertFalse(r["impermeable_pass"])
        self.assertAlmostEqual(r["margin_m2"], -3.336, places=2)
        # without the pavers counted it would look comfortable: 362.468 / 602.04
        self.assertAlmostEqual(r["if_pavers_were_permeable_pct"], 0.6021, places=3)
        self.assertTrue(r["building_pass"])            # 48.9% < 50%
        self.assertEqual(r["warnings"], [])

    def test_gravel_apron_fixes_it(self):
        r = ic.check(ic.load(os.path.join(EXAMPLES,
                                          "3528-w-30th-ave-gravel-apron.json")))
        self.assertTrue(r["impermeable_pass"])
        self.assertAlmostEqual(r["impermeable_m2"], 442.868, places=2)

    def test_pad_at_the_wobbly_lane_line_is_not_clipped(self):
        # [C] The City parcel line wanders 3.6 cm; the 2 cm tolerance band
        # absorbs it, so the pad is counted in full (92.40, not 92.36).
        r = ic.check(ic.load(os.path.join(EXAMPLES, "3528-w-30th-ave.json")))
        pad = [x for x in r["rows"] if x["id"] == "pad"][0]
        self.assertAlmostEqual(pad["area_m2"], 92.40, places=6)
        self.assertEqual(pad["outside_m2"], 0.0)

    def test_laneway_example_numbers(self):
        # examples/33ft-lot-laneway-house.json, hand sum in the extract:
        # buildings 42 + 100 + 4.5 = 146.5; pavers 24.964 (3.16 x 7.9 on the
        # lot; the 1.5 m apron in the lane is not counted) + 50.556; walks
        # 10.428 (12.228 - 1.8 under the porch) + 10.75; hot tub 4.5; turf 12;
        # the raised deck sits wholly on the courtyard pavers, so adds 0.
        r = ic.check(ic.load(os.path.join(EXAMPLES, "33ft-lot-laneway-house.json")))
        self.assertAlmostEqual(r["building_m2"], 146.5, places=6)
        self.assertAlmostEqual(r["impermeable_m2"], 259.698, places=3)
        self.assertTrue(r["impermeable_pass"])
        deck = [x for x in r["rows"] if x["id"] == "deck"][0]
        self.assertAlmostEqual(deck["area_m2"], 0.0, places=6)   # over the pavers
        self.assertTrue(any("Laneway house" in (x["flag"] or "") for x in r["rows"]))
        self.assertTrue(any("outside the lot" in w for w in r["warnings"]))


# ==============================================================================
#  Boundary cases
# ==============================================================================

class BoundaryCases(unittest.TestCase):

    def test_exactly_75_percent_passes(self):
        # "Maximum ... 75%": at the maximum is allowed. 300 of 400 m2.
        r = ic.check(lot([sf("a", "concrete", [0, 0, 20, 15])]))
        self.assertAlmostEqual(r["impermeable_pct"], 0.75)
        self.assertTrue(r["impermeable_pass"])

    def test_one_square_metre_over_fails(self):
        r = ic.check(lot([sf("a", "concrete", [0, 0, 20, 15.05])]))
        self.assertFalse(r["impermeable_pass"])

    def test_near_the_limit_the_report_shows_more_decimals(self):
        # [C] 300.02 of 400 m2 is 75.005%, which prints as "75.00%" at two
        # decimals next to FAIL. The report must not look self-contradictory.
        r = ic.check(lot([sf("a", "concrete", [0, 0, 20, 15.001]) ]))
        self.assertFalse(r["impermeable_pass"])
        self.assertTrue(r["near_limit"])
        text = ic.report(r)
        self.assertIn("75.0050%", text)
        self.assertIn("verdict uses unrounded areas", text)

    def test_exactly_at_the_limit_has_zero_margin_not_minus_zero(self):
        # 10.2 x 29.7 on a 10.2 x 39.6 lot is exactly 75%; float dust used to
        # make the margin about -6e-14 and the report say "Over by 0.00".
        r = ic.check({"site": {"address": "t", "outline": [[0, 0], [10.2, 0], [10.2, 39.6], [0, 39.6]]},
                      "surfaces": [sf("a", "concrete", [0, 0, 10.2, 29.7])]})
        self.assertTrue(r["impermeable_pass"])
        self.assertEqual(r["margin_m2"], 0.0)
        self.assertIn("0.000 m² of impermeable surface still available", ic.report(r))

    def test_building_counts_in_both_totals(self):
        # s.4.2.2: impermeable total includes building coverage.
        r = ic.check(lot([sf("h", "building", [0, 0, 10, 10])]))
        self.assertEqual(r["building_m2"], 100)
        self.assertEqual(r["impermeable_m2"], 100)

    def test_building_over_50_percent_fails_its_own_test(self):
        # [C] s.3.2.2.7. 220 of 400 m2 = 55%: buildings FAIL, impermeable PASS.
        r = ic.check(lot([sf("h", "building", [0, 0, 20, 11])]))
        self.assertFalse(r["building_pass"])
        self.assertTrue(r["impermeable_pass"])
        self.assertIn("buildings", ic.report(r))


# ==============================================================================
#  Wood: the conditions decide, not the name
# ==============================================================================

class WoodConflict(unittest.TestCase):
    """'wood' is impermeable; 'wood decking with spaced boards' on grade with
    no impermeable layer is permeable (author's reading of the conditions)."""

    def test_all_three_conditions_met_is_permeable(self):
        self.assertEqual(cls(material="wood decking", spaced=True,
                             on_grade=True, impermeable_layer=False), "permeable")

    def test_plain_wood_meeting_conditions_is_permeable_too(self):
        self.assertEqual(cls(material="wood", spaced=True, on_grade=True,
                             impermeable_layer=False), "permeable")

    def test_tight_boards_are_impermeable(self):
        self.assertEqual(cls(material="wood decking", spaced=False,
                             on_grade=True, impermeable_layer=False), "impermeable")

    def test_deck_over_membrane_is_impermeable(self):
        self.assertEqual(cls(material="wood decking", spaced=True,
                             on_grade=True, impermeable_layer=True), "impermeable")

    def test_conditions_not_stated_are_not_invented(self):
        # [B] A deck with no conditions used to be reported "boards not
        # spaced, not installed on grade" -- facts the user never gave.
        c, _, reason, flag = ic.classify({"material": "wood decking"})
        self.assertEqual(c, "impermeable")
        self.assertIn("not stated", reason)
        self.assertNotIn("boards not spaced", reason)
        self.assertIn("state spaced, on_grade and impermeable_layer", flag)

    def test_raised_deck_is_impermeable_and_flagged(self):
        c, _, _, flag = ic.classify({"material": "wood decking", "spaced": True,
                                     "on_grade": True, "impermeable_layer": False,
                                     "height_mm": 601})
        self.assertEqual(c, "impermeable")
        self.assertIn("confirm treatment with the City", flag)

    def test_low_platform_still_takes_the_three_condition_test(self):
        # Section 2 "Patio": no higher than 600 mm.
        self.assertEqual(cls(material="wood decking", spaced=True, on_grade=True,
                             impermeable_layer=False, height_mm=600), "permeable")

    def test_decking_aliases(self):
        for m in ("deck", "decking", "cedar deck", "composite decking", "timber deck"):
            self.assertEqual(cls(material=m, spaced=True, on_grade=True,
                                 impermeable_layer=False), "permeable", m)

    def test_raised_deck_prints_the_reading_note(self):
        r = ic.check(lot([sf("d", "wood decking", [0, 0, 3, 3], spaced=True,
                             on_grade=False, impermeable_layer=False, height_mm=900)]))
        self.assertTrue(any(n.startswith("AUTHOR'S READING") for n in r["notes"]))


# ==============================================================================
#  Buildings: Section 2's own words
# ==============================================================================

class BuildingVocabulary(unittest.TestCase):
    """Section 2, Impermeable Materials: "...all buildings, including carports,
    entries, porches and verandahs". [A] [C]"""

    def test_named_building_parts_are_buildings(self):
        for m in ("carport", "porch", "entry", "verandah", "veranda", "front porch"):
            self.assertEqual(cls(material=m), "building", m)

    def test_accessory_buildings_and_laneway_houses_are_buildings(self):
        for m in ("garage", "detached garage", "shed", "accessory building",
                  "laneway house", "coach house", "house", "duplex"):
            self.assertEqual(cls(material=m), "building", m)

    def test_garage_and_porch_count_in_the_50_percent_test(self):
        # [A] house 107.24 + porch 6 + garage 21.96 + laneway 36.48 = 171.68
        r = ic.check({"site": {"outline": [[0, 0], [10.06, 0], [10.06, 37.19], [0, 37.19]]},
                      "surfaces": [sf("h", "building", [1.2, 13, 7.66, 14]),
                                   sf("p", "porch", [3, 27, 3, 2]),
                                   sf("g", "garage", [1.2, 0.9, 3.6, 6.1]),
                                   sf("l", "laneway house", [5, 0.9, 4.8, 7.6])]})
        self.assertAlmostEqual(r["building_m2"], 171.68, places=6)

    def test_laneway_house_is_flagged_as_unresolved(self):
        c, _, _, flag = ic.classify({"material": "laneway house"})
        self.assertEqual(c, "building")
        self.assertIn("Section 11", flag)

    def test_no_director_note_on_a_structure(self):
        for m in ("porch", "garage", "carport", "laneway house"):
            self.assertNotIn("Director", ic.classify({"material": m})[2], m)


# ==============================================================================
#  Materials in neither list
# ==============================================================================

class MaterialsInNeitherList(unittest.TestCase):

    def test_pervious_concrete_is_impermeable_on_the_impermeable_list(self):
        c, source, reason, _ = ic.classify({"material": "pervious concrete"})
        self.assertEqual(c, "impermeable")
        self.assertEqual(source, ic.S2_IMPERMEABLE)
        self.assertIn("without qualification", reason)

    def test_synthetic_turf_is_impermeable_with_director_note(self):
        c, _, reason, _ = ic.classify({"material": "synthetic turf"})
        self.assertEqual(c, "impermeable")
        self.assertIn("Director of Planning may accept", reason)

    def test_artificial_turf_is_the_same_material(self):
        # [B] "artificial turf" used to be "unrecognised" while "synthetic
        # turf" was known.
        self.assertEqual(ic.canonical("Artificial Turf"), "synthetic turf")
        self.assertEqual(ic.classify({"material": "artificial turf"})[2],
                         ic.classify({"material": "synthetic turf"})[2])

    def test_a_typo_is_flagged_with_a_suggestion(self):
        # [B] "permable pavers" used to be explained as "the Director may
        # accept it as permeable" -- the opposite of the lesson.
        c, _, reason, flag = ic.classify({"material": "permable pavers"})
        self.assertEqual(c, "impermeable")
        self.assertNotIn("Director", reason)
        self.assertIn("Did you mean “permeable pavers”", flag)

    def test_an_unknown_word_is_flagged_without_a_false_suggestion(self):
        c, _, _, flag = ic.classify({"material": "window well"})
        self.assertEqual(c, "impermeable")
        self.assertIn("Unrecognised", flag)
        self.assertNotIn("Did you mean", flag)

    def test_pool_is_impermeable_without_a_director_note(self):
        # [A] A lined pool is not a candidate for the Director's opinion.
        for m in ("swimming pool", "pool", "hot tub", "pond"):
            c, _, reason, _ = ic.classify({"material": m})
            self.assertEqual(c, "impermeable", m)
            self.assertNotIn("may accept", reason, m)

    def test_no_third_category_exists(self):
        seen = {ic.classify({"material": m})[0]
                for m in ("synthetic turf", "rubber safety surfacing",
                          "pervious concrete", "decomposed granite", "anything else")}
        self.assertEqual(seen, {"impermeable"})


# ==============================================================================
#  Listed permeable materials and their conditions
# ==============================================================================

class ListedPermeableConditions(unittest.TestCase):

    def test_gravel_is_permeable(self):
        self.assertEqual(cls(material="gravel"), "permeable")
        self.assertEqual(cls(material="pea gravel"), "permeable")

    def test_gravel_over_plastic_is_impermeable(self):
        self.assertEqual(cls(material="gravel", impermeable_layer=True), "impermeable")

    def test_gravel_not_on_grade_is_impermeable(self):
        # [C] the on-grade condition is applied to every listed material, not
        # only wood, if the reading is to be consistent.
        self.assertEqual(cls(material="gravel", on_grade=False), "impermeable")

    def test_river_rock_needs_a_size(self):
        self.assertEqual(cls(material="river rock"), "impermeable")
        self.assertEqual(cls(material="river rock", size_cm=3), "permeable")
        self.assertEqual(cls(material="river rock", size_cm=4.99), "permeable")
        self.assertEqual(cls(material="river rock", size_cm=5), "impermeable")

    def test_river_rock_reason_names_the_size_given(self):
        c, _, reason, flag = ic.classify({"material": "river rock", "size_cm": 3})
        self.assertEqual(c, "permeable")
        self.assertIn("3 cm is under 5 cm", reason)
        self.assertIsNone(flag)

    def test_lawn_grass_and_planting_are_not_counted(self):
        # [C] "grass" and "lawn" used to get opposite verdicts.
        for m in ("lawn", "grass", "turf", "planting", "garden", "soil", "sod"):
            self.assertEqual(cls(material=m), "ground", m)


# ==============================================================================
#  Geometry: clip to the lot, count every square metre once
# ==============================================================================

class GeometryChecks(unittest.TestCase):

    def test_area_outside_the_lot_is_not_counted(self):
        # [A] a 3 x 10 strip with 5 m beyond the lot line: 15 m2 counted.
        r = ic.check(lot([sf("a", "concrete", [0, 15, 3, 10])]))
        self.assertAlmostEqual(r["impermeable_m2"], 15.0, places=6)
        self.assertTrue(any("outside the lot" in w for w in r["warnings"]))

    def test_slab_over_a_notch_in_a_concave_lot_is_clipped(self):
        # [C] corners inside, middle over the notch of a U-shaped lot.
        u = [[0, 0], [30, 0], [30, 10], [20, 10], [20, 4], [10, 4], [10, 10], [0, 10]]
        r = ic.check({"site": {"outline": u},
                      "surfaces": [sf("a", "asphalt", [0, 6, 30, 4])]})
        # the strip y 6..10 over x 10..20 is outside: 10 x 4 = 40 of 120
        self.assertAlmostEqual(r["impermeable_m2"], 80.0, places=6)

    def test_a_corner_inside_the_tolerance_band_is_not_clipped(self):
        # 1.9 cm past the lot line: inside the 2 cm band, counted in full.
        r = ic.check(lot([sf("a", "concrete", [0, 0, 20.019, 10])]))
        self.assertAlmostEqual(r["impermeable_m2"], 200.19, places=6)
        self.assertEqual(r["warnings"], [])

    def test_deck_over_patio_is_one_footprint(self):
        # [A] both impermeable, same rectangle: 20 m2, not 40.
        r = ic.check(lot([sf("p", "stone", [1, 1, 5, 4]),
                          sf("d", "wood decking", [1, 1, 5, 4], spaced=True,
                             on_grade=False, impermeable_layer=False, height_mm=1500)]))
        self.assertAlmostEqual(r["impermeable_m2"], 20.0, places=6)
        self.assertTrue(any("counted once" in n for n in r["notes"]))

    def test_polygon_over_rect_overlap_is_deducted(self):
        # [C] 10 x 10 rect and a 10 x 10 polygon offset 5 m: 175 m2, not 200.
        r = ic.check(lot([sf("a", "concrete", [0, 0, 10, 10]),
                          sf("b", "brick", polygon=[[5, 5], [15, 5], [15, 15], [5, 15]])]))
        self.assertAlmostEqual(r["impermeable_m2"], 175.0, places=6)

    def test_three_way_overlap_is_counted_once(self):
        # three 10 x 10 squares all covering the same 5 x 5 corner
        r = ic.check(lot([sf("a", "concrete", [0, 0, 10, 10]),
                          sf("b", "brick", [5, 5, 10, 10]),
                          sf("c", "stone", [5, 0, 10, 10])]))
        # by hand: a = 100; b adds 100 - 25 (shared with a) = 75; c adds
        # 100 - 50 (with a) - 50 (with b) + 25 (with both) = 25. Union = 200.
        self.assertAlmostEqual(r["impermeable_m2"], 200.0, places=6)

    def test_stricter_class_wins_the_overlap(self):
        # a house drawn over a gravel bed: the overlap is building, so the
        # permeable total loses it and the building total keeps it.
        r = ic.check(lot([sf("g", "gravel", [0, 0, 10, 10]),
                          sf("h", "building", [5, 5, 10, 10])]))
        self.assertAlmostEqual(r["building_m2"], 100.0, places=6)
        self.assertAlmostEqual(r["permeable_m2"], 75.0, places=6)

    def test_clockwise_polygon_has_positive_area(self):
        self.assertEqual(ic.polygon_area([[0, 0], [0, 10], [10, 10], [10, 0]]), 100)

    def test_triangulation_of_a_concave_polygon_keeps_its_area(self):
        L = [[0, 0], [12, 0], [12, 4], [4, 4], [4, 14], [0, 14]]
        self.assertAlmostEqual(ic.pieces_area(ic.triangulate(L)), ic.polygon_area(L), places=9)

    def test_convex_clip_of_two_squares(self):
        a = [[0, 0], [10, 0], [10, 10], [0, 10]]
        b = [[5, 5], [15, 5], [15, 15], [5, 15]]
        self.assertAlmostEqual(ic.polygon_area(ic.convex_clip(a, b)), 25.0, places=9)

    def test_rect_and_polygon_of_the_same_shape_agree(self):
        r1 = ic.check(lot([sf("a", "concrete", [2, 3, 7, 4])]))
        r2 = ic.check(lot([sf("a", "concrete", polygon=[[2, 3], [9, 3], [9, 7], [2, 7]])]))
        self.assertEqual(r1["impermeable_m2"], r2["impermeable_m2"])


# ==============================================================================
#  Input that cannot be checked gets a sentence, not a traceback
# ==============================================================================

class Validation(unittest.TestCase):

    def test_bowtie_polygon_is_refused_as_crossing_itself(self):
        p = problems(lot([sf("b", "concrete", polygon=[[0, 0], [10, 10], [10, 0], [0, 10]])]))
        self.assertTrue(any("crosses itself" in x for x in p), p)

    def test_negative_width_is_refused(self):
        # [B] [C] rect [10, 0, -10, 15] used to count 150 m2 silently.
        p = problems(lot([sf("a", "concrete", [10, 0, -10, 15])]))
        self.assertTrue(any("positive" in x for x in p), p)

    def test_numbers_in_quotes_are_refused(self):
        p = problems(lot([sf("a", "concrete", ["0", "0", "5", "5"])]))
        self.assertTrue(any("four numbers" in x for x in p), p)
        p = problems(lot([sf("d", "wood decking", [0, 0, 3, 3], height_mm="900")]))
        self.assertTrue(any("height_mm" in x for x in p), p)

    def test_string_booleans_are_refused(self):
        # [C] "no" is truthy; the old tool read impermeable_layer: "no" as yes.
        p = problems(lot([sf("d", "wood decking", [0, 0, 3, 3], spaced="yes")]))
        self.assertTrue(any("true or false" in x for x in p), p)

    def test_missing_material_is_refused(self):
        p = problems(lot([{"id": "a", "label": "a", "rect": [0, 0, 5, 5]}]))
        self.assertTrue(any("no “material”" in x for x in p), p)

    def test_wrong_geometry_key_gets_a_helpful_message(self):
        # [B] "rectangle" instead of "rect" used to raise KeyError: 'polygon'.
        p = problems(lot([{"id": "a", "label": "House", "material": "building",
                           "rectangle": [0, 0, 5, 5]}]))
        self.assertTrue(any("has no geometry" in x and "“rect”" in x for x in p), p)

    def test_both_rect_and_polygon_is_refused(self):
        p = problems(lot([sf("a", "concrete", [0, 0, 5, 5], polygon=[[0, 0], [1, 0], [1, 1]])]))
        self.assertTrue(any("Give only one" in x for x in p), p)

    def test_duplicate_ids_are_refused(self):
        p = problems(lot([sf("a", "concrete", [0, 0, 5, 5]), sf("a", "brick", [6, 6, 2, 2])]))
        self.assertTrue(any("used twice" in x for x in p), p)

    def test_missing_outline_is_refused(self):
        p = problems({"site": {"address": "t"}, "surfaces": []})
        self.assertTrue(any("outline" in x for x in p), p)

    def test_missing_label_and_id_default_quietly(self):
        r = ic.check(lot([{"material": "concrete", "rect": [0, 0, 5, 5]}]))
        self.assertEqual(r["rows"][0]["label"], "surface-1")

    def test_area_only_surface_is_counted_and_flagged(self):
        # [A] a surface from an area schedule, with no geometry.
        r = ic.check(lot([sf("h", "building", area_m2=120)]))
        self.assertEqual(r["building_m2"], 120)
        self.assertIn("without geometry", r["rows"][0]["flag"])

    def test_command_line_reports_problems_and_exits_2(self):
        bad = os.path.join(HERE, "..", "examples", "does-not-exist.json")
        buf = io.StringIO()
        with redirect_stdout(buf):
            status = ic.main(["prog", bad])
        self.assertEqual(status, 2)
        self.assertIn("Cannot find", buf.getvalue())


# ==============================================================================
#  Units
# ==============================================================================

class Units(unittest.TestCase):

    def test_feet_are_converted(self):
        # [B] a 33 x 122 ft lot is 374.1 m2, not 4,026.
        r = ic.check({"site": {"outline": [[0, 0], [33, 0], [33, 122], [0, 122]],
                               "units": "ft"},
                      "surfaces": [sf("h", "building", [4, 40, 25, 50])]})
        self.assertAlmostEqual(r["site_area_m2"], 33 * 122 * 0.3048 ** 2, places=6)
        self.assertAlmostEqual(r["building_m2"], 25 * 50 * 0.3048 ** 2, places=6)
        self.assertTrue(any("feet" in n for n in r["notes"]))

    def test_a_feet_sized_lot_typed_as_metres_is_warned(self):
        r = ic.check({"site": {"outline": [[0, 0], [33, 0], [33, 122], [0, 122]],
                               "frontage_m": 33}, "surfaces": []})
        self.assertTrue(any("in feet?" in w for w in r["warnings"]))


# ==============================================================================
#  Uses and scope
# ==============================================================================

class UsesAndScope(unittest.TestCase):

    def test_multiplex_is_not_assessed(self):
        for use in ("multiplex", "Multiple Dwelling", "multiple dwelling containing 4 dwelling units"):
            r = ic.check(lot([], use=use))
            self.assertFalse(r["applies"], use)
            self.assertIn("s.3.1", r["why_not"])

    def test_every_other_use_is_assessed(self):
        # [A] s.3.2: "All other uses not regulated by section 3.1".
        for use in ("infill", "multiple conversion dwelling", "duplex with secondary suite",
                    "Single_Detached_House", "principal dwelling unit with lock-off unit"):
            self.assertTrue(ic.check(lot([], use=use))["applies"], use)

    def test_non_dwelling_use_gets_the_director_note(self):
        r = ic.check(lot([], use="child day care facility"))
        self.assertTrue(r["applies"])
        self.assertTrue(any("s.3.2.2.14" in n for n in r["notes"]))

    def test_laneway_house_as_a_use_assesses_the_site(self):
        r = ic.check(lot([sf("l", "laneway house", [0, 0, 6, 7])], use="laneway house"))
        self.assertTrue(r["applies"])
        self.assertEqual(r["use"], "single detached house")
        self.assertTrue(any("accessory to a single detached house" in n for n in r["notes"]))

    def test_other_zone_is_not_assessed_but_warnings_still_print(self):
        # [C] the not-assessed report used to drop the warnings.
        r = ic.check(lot([sf("a", "concrete", [15, 15, 10, 10])], zone="RT-7"))
        self.assertFalse(r["applies"])
        self.assertIn("outside the lot", ic.report(r))

    def test_zone_written_in_lower_case_is_still_r1_1(self):
        self.assertTrue(ic.check(lot([], zone=" r1-1 "))["applies"])

    def test_small_lot_warnings_cite_the_relaxation_clause(self):
        r = ic.check({"site": {"address": "t", "frontage_m": 6.5,
                               "outline": [[0, 0], [10, 0], [10, 20], [0, 20]]},
                      "surfaces": []})
        area = [w for w in r["warnings"] if "s.3.2.2.1 " in w][0]
        frontage = [w for w in r["warnings"] if "s.3.2.2.2" in w][0]
        self.assertIn("s.3.2.2.9", area)
        self.assertNotIn("s.3.2.2.12", area)
        self.assertIn("s.3.2.2.12", frontage)


# ==============================================================================
#  s.3.2.2.13 parking area, and sites of several parcels
# ==============================================================================

class ParkingAndSites(unittest.TestCase):

    def test_four_or_fewer_spaces_are_not_a_parking_area(self):
        # Section 2, Parking Area: "does not include an area providing 4 or
        # fewer spaces accessory to a residential use".
        r = ic.check(lot([sf("p", "asphalt", [0, 0, 10, 10], parking=True)], parking_spaces=2))
        self.assertFalse(r["parking_applies"])
        self.assertTrue(any("s.3.2.2.13 does not apply" in n for n in r["notes"]))

    def test_more_than_four_spaces_takes_the_30_percent_test(self):
        # 130 of 400 m2 = 32.5% > 30%: FAIL under s.3.2.2.13
        r = ic.check(lot([sf("p", "asphalt", [0, 0, 13, 10], parking=True)], parking_spaces=5))
        self.assertTrue(r["parking_applies"])
        self.assertFalse(r["parking_pass"])
        self.assertIn("s.3.2.2.13", ic.report(r))

    def test_two_adjoining_parcels_make_one_site(self):
        # [A] Section 2, Site: "1 or more adjoining parcels"
        r = ic.check({"site": {"outlines": [[[0, 0], [10, 0], [10, 20], [0, 20]],
                                            [[10, 0], [20, 0], [20, 20], [10, 20]]]},
                      "surfaces": [sf("h", "building", [5, 5, 10, 10])]})
        self.assertEqual(r["site_area_m2"], 400)
        self.assertEqual(r["building_m2"], 100)      # straddles the parcel line
        self.assertTrue(any("adjoining parcels" in n for n in r["notes"]))


# ==============================================================================
#  The web page holds the Python tool's answers
# ==============================================================================

class WebPage(unittest.TestCase):
    """The browser version (tool/web/index.html) checks itself against answers
    this Python file produced. Those answers must be the current ones."""

    def test_web_page_data_is_current(self):
        import export_web_data as ew
        self.assertEqual(
            ew.current_block(), ew.block(ew.build()),
            "tool/web/data.js holds stale answers. Run: python3 tool/export_web_data.py")

    def test_the_tests_lots_are_the_exported_lots(self):
        # [C] the page's self-check must include every lot the tests use,
        # so a bug the tests would catch is also caught in the browser.
        import export_web_data as ew
        names = {c["name"] for c in ew.fixed_check_cases(ew.load_examples())
                 if "name" in c}
        for needed in ("building over 50%", "clockwise polygon", "pavers in capitals",
                       "frontage exactly 7.3", "site exactly 306", "duplex with suite",
                       "margin snaps to zero", "deck over patio", "strip past the lot line"):
            self.assertIn(needed, names)


if __name__ == "__main__":
    unittest.main()
