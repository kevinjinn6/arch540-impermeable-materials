# Review C — R1-1 s.3.2.2.8 impermeable-materials tool

Reviewer persona: computational designer / software engineer who builds and audits rule-checking tools.
Repository reviewed read-only at `/Users/kevinjinn/Documents/Year 3/Arch 540/Assignment 1` (branch `stage2-policy-map`, HEAD 060d44e), 2026-10-01/02. Python used: 3.9.6 (the project's `.venv` is what `python3` resolves to on this machine). Scratch inputs, scripts and raw outputs: `scratchpad/reviewer-c/` (`make_and_run.py`, `jxa_parity.py`, `cases/*.json`, `adversarial-output.txt`, `clone/`).

---

## PART 1 — peer-review format

**1. What input I tried.**
Both shipped examples, the test suite both ways, `export_web_data.py --check`; then ~95 adversarial lots of my own (bowtie / clockwise / negative-width / zero-width rects and polygons, a polygon over a rect, a rect on a U-shaped lot, a lot in feet, strings for numbers, missing `outline` / `material` / `label` / `id`, duplicate ids, 36 material synonyms, wood at 600 / 601 mm and with string booleans, river rock at 5 / 4.99 / none / 0 / −1 cm, exactly 75.000 / 75.001 / 75.004 %, zone and use variants); the web page's self-check run headlessly in JavaScriptCore with 16 deliberately injected bugs; and a clean `git clone` to see what a classmate receives.

**2. Whether I understood the result, and whether I could match it to the source.**
Yes. The terminal report is readable and every classification names the passage it rests on. I matched the hand-worked example to exact decimal arithmetic (454.868 m², 75.5541 %, −3.336 m²; 60.2064 %; revised 73.5609 %, 8.664 m² spare — all agree with the tool and the extract), and both Section 2 definitions to the June 2026 PDF word for word (p.20 and p.31).

**3. What broke or confused me.**
A clean clone contains no `tool/`, `examples/`, extract or output — the whole W3 deliverable is uncommitted. Thirteen malformed inputs end in Python tracebacks. A lot 0.004 % over prints "75.00 % … FAIL, Over by 0.00 m²". "carport" and "porch" are reported as "not named in the by-law" although Section 2 names them. Two fully coincident rectangles (one with negative width) pass at exactly 75 % with no overlap warning. Eight of sixteen injected JavaScript bugs sail through the page's self-check.

**4. The one change I would make first.**
Commit `tool/`, `examples/`, `output/*.png|jpg`, `sources/r1-1-impermeable-extract.md` and the June 2026 `zoning-by-law-section-2.pdf` together with the updated README; then port the page's `validate()` into `check()` so bad input fails with a message instead of a traceback or a silent wrong number.

---

## PART 2 — full critique

### Findings

**F1 — CRITICAL — The tool is not in the repository.**
Evidence:
```
$ git status --short
 M README.md
 M map/index.html
?? examples/   ?? output/   ?? tool/
?? sources/r1-1-impermeable-extract.md   ?? sources/zoning-by-law-section-2.pdf
?? ARCH540_A1_WrapUp.pdf  ?? "test lot.3dm"  ?? "vancouver bylaw assignment 1.pages"  ?? .claude/
$ git ls-files | grep -c '^tool/\|^examples/\|^output/'      -> 0
$ git clone "<repo>" scratch/clone && cd clone && ls
README.md  assignment 1.qgz  buildings.py  docs  map  sources  stormwater.py  week-01
$ python3 tool/impermeable_check.py examples/3528-w-30th-ave.json
can't open file '.../clone/tool/impermeable_check.py': [Errno 2] No such file or directory   (exit 2)
$ python3 -m unittest tool/test_impermeable_check.py -v     -> FAILED (errors=1)
$ grep -c "tool/" README.md   (committed README, in the clone)  -> 0
```
`origin/HEAD -> origin/stage2-policy-map` has the same content, so the remote is equally empty of the tool.
Consequence: a peer reviewer who follows the README's "Run it in a terminal" gets a file-not-found error; the W3 and W4 deliverables exist only on this laptop.
Fix: `git add README.md tool examples output/*.png output/*.jpg sources/r1-1-impermeable-extract.md sources/zoning-by-law-section-2.pdf` and commit. Keep `test lot.3dm` (3.4 MB), the `.pages` file and `.claude/` out (add to `.gitignore`). `output/3528-w-30th-ave.3dm` (710 KB) is fine to track.

**F2 — MAJOR — The verdict is taken on unrounded floats but shown at 2 dp, so the report can say "75.00 % FAIL".**
Evidence (`tool/impermeable_check.py:434` `impermeable <= imp_limit + eps` with `eps = 1e-9`; `report()` lines 485–496 print `:5.2f` and `:,.2f`):
```
$ python3 tool/impermeable_check.py cases/72_75_004_pct_exact.json   # 20 × 15.0008 on 400 m²
   s.3.2.2.8  impermeable    300.02 m²  = 75.00%  (limit 75% = 300.00)  FAIL
              Over by 0.02 m².
$ python3 tool/impermeable_check.py cases/73_75_001_pct.json         # 20 × 15.0002
   s.3.2.2.8  impermeable    300.00 m²  = 75.00%  (limit 75% = 300.00)  FAIL
              Over by 0.00 m².
```
Exactly 75.000 % passes with margin 0.00 (cases 70, 03, 10, 80 — the `FixesFromReview` fix works). "0.1 + 0.2"-style dust cannot flip a verdict: dust at 450 m² is ~1e-13 m², far under `eps`; the exact-decimal recomputation of the demo lot agrees with the float result to 4 dp. The problem is presentation, not arithmetic.
Consequence: a user sees a number equal to the limit and a FAIL, with "Over by 0.00". The same happens in the web page (`displayOf`, `index.html:514–516`).
Fix: when `0 < -margin < 0.005 × …` print the margin to 4 dp and the percentage to 3–4 dp (or print "75.004 %"), and add one line to the report: "verdict uses unrounded areas". Pin it with a test on the 20 × 15.0008 lot.

**F3 — MAJOR — No input validation in the Python path: 13 malformed inputs crash with tracebacks, several others are accepted silently with wrong numbers.**
Crashes (file `tool/impermeable_check.py`):
| input | result |
|---|---|
| no `outline` / lot given as `area_m2` only | `KeyError: 'outline'` line 325 |
| 2-point lot, bowtie lot, zero-area lot | `ZeroDivisionError` line 428 |
| rect `["0","0","10","10"]` | `TypeError` in `polygon_area` line 258 |
| rect of 3 numbers | `ValueError: not enough values to unpack` line 277 |
| `frontage_m: "6.0"` | `TypeError '<'` line 350 |
| `height_mm: "900"` | `TypeError '>'` line 176 |
| `size_cm: "3"` | `TypeError '>='` line 233 |
| missing `material` / `label` / `id` | `KeyError` line 369 |
| `material: null` | `check()` succeeds, `report()` crashes line 467 |
Silent acceptances:
```
09_negative_width   rect [10,0,-10,15]  -> 150.00 m² IMPERMEABLE, no warning
11_duplicate_ids    two surfaces id "a" -> both listed, no warning
17_feet             50×120 "ft" lot      -> Site area 6,000.00 m², PASS (units ignored)
19_both_rect_and_polygon               -> rect used, polygon ignored, yet warns "polygon surfaces were not checked"
51_wood spaced="yes", on_grade="yes", impermeable_layer="no"  -> IMPERMEABLE "impermeable layer underneath"  ("no" is truthy)
52_wood spaced="false"                 -> treated as spaced ("false" is truthy)
63_river_rock size_cm 0 and -1          -> permeable ("River rock of -1 cm is under 5 cm")
87_site.area_m2: 1000 with 400 m² outline -> 400 used, key ignored silently
```
The web page already has a correct `validate()` (`tool/web/index.html:1320–1357`) that rejects duplicate ids, negative sizes, non-numbers and non-boolean conditions — so the two front ends accept different inputs, and only the browser one is safe.
Consequence: the CLI and Rhino paths can produce confident wrong answers (feet, negative width, string booleans) or stack traces for a landscape designer editing JSON by hand.
Fix: write `validate(example)` in Python mirroring the JS messages, call it first in `check()`, raise `ValueError`; have `__main__` catch it and print the message. Reject `size_cm <= 0`, `height_mm < 0`, zero-area lots, non-boolean conditions; add a `units` check or document "metres only" in the schema. Then export the JS `validate()` messages the same way the rules are exported, so they cannot drift.

**F4 — MAJOR — Overlap and containment checks miss real cases, so area is double-counted or counted outside the lot without warning.**
Evidence:
```
04_polygon_overlaps_rect   10×10 concrete rect + 10×10 brick polygon offset 5 m (25 m² shared)
   -> 200.00 m² counted, only the generic "Overlaps are checked between rectangles only" warning
80_negative_width_full_overlap   rect [10,0,-10,15] and rect [0,0,10,15] (identical footprint)
   -> 300.00 m² = 75.00% PASS, NO overlap warning     (rect_overlap, line 311–315, assumes w,d >= 0)
07_rect_inside_corners_but_outside_concave_lot   rect [0,0,20,4] on a U-shaped lot with a 10×10 notch
   -> 80.00 m² counted, no "outside the lot" warning   (point_in_polygon tests corners only, line 364)
01_bowtie_polygon   self-intersecting [[0,0],[10,10],[10,0],[0,10]]  -> 0.00 m², no warning
```
README (line 195–196) does admit "overlaps are only checked between rectangles", which I confirmed; the other three are undocumented.
Consequence: a designer who draws an L-shaped house as a polygon over a rect patio gets a double count and a generic warning; one who types width as a negative number can pass a failing design.
Fix: normalise rects (`x += w if w < 0; w = abs(w)`) or reject negatives; detect self-intersection (segment–segment test, O(n²) is fine); for overlap use a polygon-clipping area (Sutherland–Hodgman is ~25 lines and both shapes here are convex rects or small polygons), or at least sample edge midpoints for the containment test.

**F5 — MAJOR — Named building parts and obvious synonyms are classified with a false reason and the wrong class.**
Section 2, Impermeable Materials (June 2026, p.20): "…of all buildings, including carports, entries, porches and verandahs, asphalt, concrete, brick, stone, permeable pavers, and wood."
```
84_carport_wording
 carport   25.00  IMPERMEABLE  - Not named in the by-law. Counted as impermeable; the Director of Planning may accept it as permeable.
 porch / verandah / entry  -> same reason
   s.3.2.2.7  buildings  0.00 m²     (they are excluded from the building total)
40_synonyms
 house, garage, shed, driveway, concrete pavers, paving stones, turf, grass, mulch, crushed granite, decomposed granite, rubber mulch,
 artificial turf, pool, water, pond, green roof, tree  -> all "Not named in the by-law … Director may accept"
 lawn, soil, planting, garden -> not counted;   turf, grass -> IMPERMEABLE
```
`classify()` (`impermeable_check.py:198–246`) only recognises the literal word `building`; `NAMED_IMPERMEABLE` has no synonyms; `GROUND` has "lawn" but not "grass".
Consequence: the s.3.2.2.7 total under-counts whenever the user writes "house" or "garage"; the printed reason contradicts the by-law for carports and porches; "grass" and "lawn" get opposite verdicts; "concrete pavers" (concrete) gets the Director note that "permeable pavers" correctly does not.
Fix: a `BUILDING_PARTS = ("house","garage","carport","porch","verandah","entry","shed","accessory building","laneway house")` → class `building`; a small synonym map ("grass"→"lawn", "concrete pavers"/"paving stones"→"permeable pavers" or "concrete", "mulch"→"bark mulch", "artificial turf"→"synthetic turf"); and change the default reason to "Not one of the names this tool knows" — the by-law *does* name some of these.

**F6 — MAJOR — The web page's self-check proves JS = Python only on the cases it holds; 8 of 16 injected bugs pass it.**
Method: extracted the JS core (`index.html:281–548`) and the data block, ran `runParity()` in JavaScriptCore (`osascript -l JavaScript`; `jxa_parity.py`). Unmodified: `{"nc":133,"nl":74,"nf":2957,"nbad":0}` — matches the README's 133 / 74. Then one mutation at a time:
| mutation | detected? |
|---|---|
| river rock `>= 5` → `> 5` | yes (2 cases) |
| raised deck `> 600` → `>= 600` | yes (17) |
| 75 % `<=` → `<` | yes (1) |
| edge tolerance `tol²` → `tol` | yes (4) |
| GROUND never matched | yes (41) |
| "surfaces add up to more than the site" removed | yes (12) |
| wood `impermeable_layer` ignored | yes (27) |
| polygon warning removed | yes (1) |
| **building pass tested against the 75 % limit** | **no — 0 exported cases have `building_pass` False** |
| **`polygon_area` without `abs()`** | **no — no clockwise shape in any case** |
| **pavers counterfactual made case-sensitive** | **no** |
| **frontage `<` → `<=`** | **no — frontages are only 6.5, 15.2, None** |
| **site area `<` → `<=`** | **no — areas are only 200, 400, 602.04** |
| **overlap tolerance × 10** | **no** |
| **"duplex with secondary suite" dropped from S32_USES** | **no — never appears in a case** |
| **margin `eps` snap removed** | **no — the 10.2 × 29.7 lot from the unit tests is not exported** |
Also: parity cannot catch a Python bug — the export writes Python's answer as truth. And `sameValue` ignores keys present in `got` but absent in `expect` (fine) and uses a 1e-9 relative tolerance (fine).
Consequence: the sentence "It doesn't get the chance to do so silently" (README line 152) is stronger than the evidence. A port error in the 50 % test, in polygon orientation or in the boundary comparisons would ship unnoticed.
Fix: add to `fixed_check_cases()`: a building > 50 % lot; a clockwise polygon and a clockwise outline; `"Permeable Pavers"` in a lot; frontage 7.3; a 306 m² lot; `use: "duplex with secondary suite"`; the 10.2 × 29.7 lot; an overlap of 0.05 m². Make the unit-test lots and the exported lots literally the same list (import one from the other) so a new unit test is automatically a parity case.

**F7 — MAJOR — Claims about sources, versions and counts are out of date in four places.**
```
$ python3 -c "pypdf … sources/zoning-by-law-section-2.pdf"   -> 50 pages, header "City of Vancouver June 2026"
   Impermeable Materials on p.20 (extract & web say p.21); Deck p.11 (extract says p.12); Permeable p.31, Patio p.30 (match)
README.md:191-193            "The June 2026 PDF is not yet in the repo"            -> it is (untracked)
sources/r1-1-impermeable-extract.md:31-38   same, "Download it … save it here"     -> done, note not updated
sources/README.md row 2      "not yet stored in this repo … Download before W2 Friday" and the file is not registered
tool/web/index.html:557-559  PAGE_REF "p.21 (Nov 2025 consolidation)"; footer line 268-269 says Nov 2025
README.md:31, :44            "25 test cases"      $ python3 tool/test_impermeable_check.py -> "Ran 33 tests … OK"
extract row s.3.2.2.14       paraphrase in a column headed "Text (verbatim)"; the PDF reads "may increase the maximum area of impermeable materials for non-dwelling uses if: (a)… (b)…"
```
The wording of both Section 2 definitions does match the June 2026 PDF verbatim — the ‡ check the extract asks for has effectively been passed, but nobody wrote that down.
Consequence: the tool's provenance chain — the thing the brief grades — points at a version and page numbers that are not what is in the folder.
Fix: update the four places to "June 2026, p.20 / p.11 / p.30 / p.31", register the PDF in `sources/README.md`, make the s.3.2.2.14 row verbatim, and either drop the test count or assert it in a test.

**F8 — MAJOR (for the Rhino deliverable) — `rhino_draw.py` draws polygon surfaces as their bounding box, and labels every lot "W 30th Ave".**
`tool/rhino_draw.py:272–280`:
```python
pts = row["points"]
x0 = min(p[0] for p in pts) + ox; x1 = max(...); y0 = min(...); y1 = max(...)
doc.Objects.AddBrep(box(x0, y0, x1, y1, 0.01, top), …)
```
Case 20 (L-shaped `building` polygon, 120.00 m²) would be drawn as a 12 × 14 = 168 m² block labelled "120.00 m²". The web page extrudes the true outline (`index.html:917 prism(r.points…)`), so the two spatial outputs disagree for any non-rectangular surface. Line 316 hard-codes `"W 30th Ave  (street)"` for every example (the web derives it from the address, `streetName()`); line 296 `row["material"].lower()` raises on a non-string material that `check()` accepted.
Consequence: the README's "Surfaces are rectangles. Irregular shapes can be given as polygon" is true for the number and false for the drawing.
Fix: build the surface the way the lot is built (lines 253–255: `Polyline → CreatePlanarBreps`) and extrude with `Extrusion.Create` or `Brep.CreateFromOffsetFace`; take the street name from `site["address"]`.

**F9 — MINOR — Test suite: three tests cannot fail against the by-law, and several rule paths have no unit test.**
- `test_sums_do_not_depend_on_the_python_version` (`test_impermeable_check.py:237–244`) compares `add_up(vals)` with the identical left-to-right loop — tautological; it would pass even if `add_up` used `sum()` on Python ≤ 3.11 and tells you nothing about 3.12.
- `test_pervious_concrete_rests_on_the_impermeable_list` asserts `source == ic.S2_IMPERMEABLE` — the code's own constant.
- `test_no_third_category_exists` asserts a design decision, not a by-law reading.
- No unit test for: s.3.2.2.7 **FAIL** (`building_pass` False — nowhere in tests or exported cases); the "Surfaces add up to more than the site" warning; any polygon surface; `report()` when the provision does not apply; `height_mm` 601 (only 900); 305.99 / 306 m²; frontage 7.3; the 0.02 m edge tolerance (cases 81/82 show 1.9 cm silent, 2.1 cm warned — correct but untested); "deck" / "decking" / "wood deck" aliases; river rock with `impermeable_layer`; `use: "laneway house"` (only in the export).
- `test_small_lot_warnings_cite_the_relaxation_clause` unpacks `area, frontage = r["warnings"]`, coupling it to warning order.
- Only `test_demo_fails_because_of_the_pavers` checks a number computed independently of the code (the hand sum 454.868). The rest verify the author's reading; that is legitimate, but say so in the module docstring.
Fix: delete or rewrite the tautological test (e.g. assert `add_up` ≠ `sum` on a Kahan-sensitive vector, or just delete it); add the missing paths; make the demo test also assert `if_pavers_were_permeable_pct ≈ 0.6021` and the site area 602.04.

**F10 — MINOR — `report()` drops warnings when the provision does not apply; the web page shows them.**
```
83_not_assessed_drops_warnings  (zone RT-7, surface 5 m past the lot line)
 NOT ASSESSED. Zone is RT-7, not R1-1.          <- no WARNINGS block; report() returns at line 458
```
`index.html:676` renders `r.warnings` in the not-assessed branch. Fix: print warnings before the early return.

**F11 — MINOR — Web page delivery details.**
- No `<!DOCTYPE html>`; the file starts with `<meta charset="utf-8">`, so browsers render it in quirks mode.
- Libraries: `three.min.js` r128 from cdnjs.cloudflare.com, `OrbitControls.js` and `CSS2DRenderer.js` from cdn.jsdelivr.net (`index.html:277–279`), no `integrity` attributes. Offline: `initThree()` (`index.html:759–763`) detects `!window.THREE` and shows "The 3D drawing needs the three.js library…"; the schedule, verdict and passages still render — consistent with README line 202–203. The README's "needs an internet connection the first time" implies caching that nothing (no service worker) guarantees.
- 380 KB of generated JSON lives inside the 452 KB source file (`DATA:START … DATA:END`), so every regeneration is an unreadable diff. A sibling `data.js` (`<script src="data.js">` works from `file://`) would keep the page source reviewable.

**F12 — MINOR — Repository hygiene and reproducibility beyond F1.**
- Working tree 583 MB: `r11_stage2.geojson` 149 MB, `r11_stormwater.geojson` 112 MB, `cache/` 210 MB (`.gitignore` says 45 MB), `.venv` 176 MB, `map/data/` 50 MB — all ignored, correctly. But `map/index.html` is tracked and depends on the ignored `map/data/`, so the Stage 2 map is also dead from a clone.
- Untracked loose files that should be ignored or removed: `test lot.3dm` (3.4 MB), `vancouver bylaw assignment 1.pages`, `ARCH540_A1_WrapUp.pdf`, `.claude/`.
- `python3 -m unittest <absolute path>` fails with `ImportError` (unittest turns the path into a module name); the README form from the repo root works, as does `cd tool && python3 -m unittest test_impermeable_check`. Document "run from the repository root".
- `tool/__pycache__` is not created by these runs here, but `.gitignore` covers it.

**F13 — MINOR — Interpretation consistency, code vs extract vs by-law.**
- *Ordering of rules*: `building` → WOOD → NAMED_IMPERMEABLE → LISTED_BASE → NAMED_PERMEABLE → GROUND → default (lines 207–246). The sets are disjoint, so order is safe; "wood chips" correctly misses `WOOD`. Code matches extract.
- *Default-to-impermeable*: matches the extract ("anything not named… impermeable") and is a fair reading of "in the opinion of the Director of Planning". But see F5 for the wording.
- *"No impermeable layer" applied to every listed permeable*: code does what the extract says (flagged there as "awaiting confirmation"). The by-law sentence attaches "when placed or installed on grade with no associated layer…" to the whole list in one breath, so the extension is defensible — but then **"on grade" should also apply to gravel, river rock, chips and mulch**, and the code asks `on_grade` only for wood (line 185). Inconsistent application of one clause.
- *River rock default*: no size → impermeable + flag (matches extract). `size_cm` 0 or −1 → permeable (case 63): add `size > 0`.
- *Raised deck*: `height_mm > 600` → impermeable + flag; 600 → three-condition test (cases 53/54 confirm). Matches the Deck/Patio definitions (p.11, p.30: "generally … greater than 600 mm" / "no greater than 600 mm"). The extract lists "how a raised deck is measured" as unresolved, but the Impermeable Materials definition itself says **"The projected area of…"** (p.20) — that wording supports counting the deck's projected footprint and should be cited. `height_mm` negative is accepted (case 56); missing `height_mm` defaults to 0 (low) — reasonable, but undocumented in README's schema.
- *Use/zone gating*: `S32_USES` matches the four uses in s.3.2.2.1/2 (p.12). Multiplex → declined; I confirmed s.3.1 (pp.8–10) contains no "impermeab" or "coverage" text, so the message is accurate. Missing `zone` silently defaults to R1-1 (case 26) — acceptable but worth a note in the report header.
- *Min area / frontage*: flagged not enforced, citing s.3.2.2.9 and s.3.2.2.12 — both verified verbatim on p.13. Boundary 305.99 warns, 306.00 does not; 7.3 does not warn (cases 76/77/78). Correct.
- *Unassigned remainder*: printed as "(rest of lot)  lawn / planting  not counted" — the tool asserts a material the user never gave. Any forgotten driveway is a free pass. Suggest "not specified (assumed lawn/planting)" and a warning when the remainder exceeds, say, 30 %.
- *`if_pavers_were_permeable`*: subtracts only surfaces whose material normalises to "permeable pavers" (lines 416–417). "concrete pavers" are not in it (F5). Shown even when pavers are not decisive; "0.00 %" in the pavers-only case (86) reads oddly. Fine as a teaching device; label it "not a by-law result" in the report as the code comment already does.

### The five changes to make first
1. **Commit the deliverable** (F1): `tool/`, `examples/`, `output/*.png|jpg`, the extract, the June 2026 Section 2 PDF, the updated README; ignore the loose `.3dm`, `.pages`, `.claude/`.
2. **Validate input in Python** (F3): port `validate()` from the page into `impermeable_check.py`, call it first in `check()`, print a message instead of a traceback; reject negative/zero dimensions, non-numbers, string booleans, duplicate ids, degenerate lots.
3. **Make the limit legible** (F2): print unrounded margin and percentage when within 0.01 % of a limit so "75.00 % FAIL" cannot appear, in both report() and the page.
4. **Fix classification of building parts and synonyms** (F5): carport / porch / verandah / entry / house / garage → `building`; synonym map; honest default reason.
5. **Close the self-check and test blind spots** (F6, F9, F4): add the eight missing parity lots (building > 50 %, CW polygon, "Permeable Pavers", frontage 7.3, 306 m², duplex with suite, the 10.2 × 29.7 lot, a 0.05 m² overlap), make unit-test lots and exported lots one list, and handle negative-width / polygon overlaps.

### What is done well
The material table is the right architecture for a rule checker: every classification returns the by-law passage it rests on, the rule constants and every reason sentence are exported from Python so the page holds no second copy of a number or a quote, and the page's `pyFixed` tie-to-even port is validated against 2,957 Python-formatted numbers on every load — a genuinely careful piece of cross-language engineering. The hand-worked example is exactly reproducible: in exact decimal arithmetic I get 602.042564 m², 454.868 m², 75.5541 %, −3.336 m², 60.2064 %, and 73.5609 % / 8.664 m² for the revision, all of which the tool and the extract report correctly, and the two Section 2 definitions are quoted word for word from the June 2026 consolidation. The code is stdlib-only so the same function runs in Rhino, the terminal and (via export) the browser; the `add_up()` note about Python 3.12's compensated `sum()` and the `eps` margin fix with a pinned regression test show the author has already been bitten by, and fixed, exactly the kind of float issue reviewers look for. Interpretations are separated from source text and dated, including a recorded correction (s.3.2.2.12 vs s.3.2.2.9), and the tool declines what it does not cover (multiplex, other zones) in plain words rather than guessing. The weaknesses above are about hardening and completeness; the core operation does what it says, and I could verify that it does.
