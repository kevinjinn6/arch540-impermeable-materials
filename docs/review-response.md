# Response to the three outside reviews of 2026-10-02

Three reviewers who had not seen the project read the repository cold on
2026-10-02 and wrote the reports in [`reviews/`](reviews/): a Vancouver
permit-practice review (A), a studio-crit review (B) and a computational
review (C). This file lists every finding, what changed in response, and what
was left as the author's decision or is still open. The rebuilt tool is
version `2026-10-02` (printed by `impermeable_check.py`).

**Verification of the rebuild.** 74 unit tests pass (`python3 -m unittest
tool/test_impermeable_check.py`), 29 of them pinning a reviewer's finding and
marked `[A]`, `[B]` or `[C]`. The web page's JavaScript was run against the
Python tool's answers in JavaScriptCore: 447 material cases, 136 lots, 23
refused inputs and 3,458 printed numbers, no disagreements. `rhino_draw.py`
was run in Rhino 8 and drew all three examples (260 objects on its own layers,
six named views) with the same numbers as the terminal. All three reviewers'
own test inputs were re-run on the rebuilt tool (see "Spot checks" below).

---

## What changed, by theme

| Theme | Before | After (2026-10-02) | Findings |
|---|---|---|---|
| Section 2's building clause | only the word `building` was a building; a porch, garage or laneway house was "not named in the by-law, the Director may accept it as permeable" and left out of the 50% test | `BUILDINGS` vocabulary: porch, entry, verandah, carport, garage, shed, accessory building, laneway house, house, duplex, roof; all count in both totals; laneway house flagged (Section 11 not in repo) | A1, A8, C5 |
| Area outside the lot | counted in full, with a warning | clipped to the lot line and reported; a 2 cm band absorbs parcel-line wobble | A2, C4 |
| Overlapping surfaces | both counted, with a warning (rectangles only) | every square metre counted once, in the stricter class; exact for any simple polygons (triangle clipping with inclusion–exclusion); the report shows drawn / outside / under → counted | A3, C4 |
| Input validation | 13 kinds of plausible mistake crashed with a traceback; negative widths, string booleans and feet passed silently | `validate()` in Python mirrors the page; 23 refusal messages in plain words; `"units": "ft"` accepted; feet-sized lots questioned | A4, B4, B5, B14, C3 |
| Material names | exact match only; a typo got the Director note (inverting the lesson); "artificial turf" unknown while "synthetic turf" known | alias table; unknown names flagged "Unrecognised … did you mean …?"; pools and hot tubs impermeable without a Director note | A6, B6, C5 |
| Wood with unstated conditions | "boards not spaced, not installed on grade" (facts the user never gave) | "spacing not stated …", counted as wood, flagged | B7 |
| The author's reading | the Permeable Materials quote was cut so the on-grade/no-layer condition looked like the definition | full sentence quoted; every result that relies on the reading prints "AUTHOR'S READING" with the alternative; the condition now applied consistently (on grade for gravel too) | A5, C13 |
| Building footprint instruction | "outside face of the outermost walls" | "projected area …", every storey, cantilevers and bays in, eaves out, s.4.3.1 | A7 |
| Use scope | four uses assessed, everything else refused | every non-s.3.1 use assessed (s.3.2 is "all other uses"); s.3.2.2.14 note for non-dwelling uses; `use: laneway house` assesses the site | A8 |
| Section 2 citations | "Nov 2025", p.21 and p.12, "June 2026 PDF not in the repo" | June 2026 throughout; p.20 and p.11; register row written; web footer fixed | A9, B3, C7 |
| Near the limit | "75.00% FAIL, over by 0.00 m²" | four decimals of percent and three of area whenever two would round to the limit | C2 |
| Not-assessed report | dropped the warnings | prints them | C10 |
| s.3.2.2.13 | paraphrased, 4-space exclusion lost | quoted; Parking Area definition quoted; 30% test runs only above 4 spaces, otherwise says why not | A14 |
| Site definition | not quoted; one parcel assumed | quoted; `outlines` accepts adjoining parcels | A11 |
| Rhino drawing | polygons drawn as bounding boxes; street name hard-coded; user's "Plan…" views deleted; whole lot filled as "lawn / planting" | true polygons extruded; street from the address; only `R1-1 …` views replaced; ground drawn near-white as "no surface drawn: not counted"; title block says what is real and what is illustrative; raised decks float at their height; area outside the lot outlined in red | A13, B9, B10, C8 |
| Web page | 380 KB data block inside the page; no doctype; no lot input; wood conditions as checkboxes; surprise told in a sentence | `data.js` beside the page; proper document; lot width × depth input; tri-state "not stated / yes / no"; a "what if pavers were permeable" toggle that re-draws the bar and column; "Copy result as text"; notes and refusals shown | B11, B12, B13, C11 |
| Self-check blind spots | 8 of 16 injected bugs undetected; test lots and exported lots were different lists | the unit-test lots are the exported lots (a test asserts it); the eight missing cases added; refusal messages and suggestions also checked | C6, C9 |
| README | "Week 3 of 4, not a finished submission"; no Purpose / How to use / Source / Example / Skill headings; "25 test cases" | the brief's five headings; Source as a table; 74 tests; repo map complete; precursor demoted | B1, B2, B3, C7, C12 |
| Reusable skill | not started | `skill/SKILL.md` | brief W4 |
| Reviews as evidence | — | `docs/reviews/`, this file, `[A][B][C]` tests | B18 |

## Finding by finding

### Review A — permit practice

| # | Finding | Response |
|---|---|---|
| 1 | Porch, garage, laneway house misclassified, dropped from 50% test | **Fixed.** Building vocabulary; test `BuildingVocabulary`. A's T1 now reports 171.68 m² of buildings (was 107.24). |
| 2 | Area outside the site counted | **Fixed.** Clipped and reported; A's T3 driveway counts 27.06 m², not 39.00. |
| 3 | Overlaps double-counted into a verdict | **Fixed.** Counted once, stricter class; A's T3 deck over patio is one footprint. |
| 4 | Tracebacks on plausible input | **Fixed.** `validate()`; `InputError`; CLI exits 2 with sentences. |
| 5 | On-grade / no-layer condition presented as the definition; quote cut | **Fixed as a disclosure, kept as a reading.** Full sentence quoted; "AUTHOR'S READING" note with the alternative in every result that relies on it. The stricter reading stays, pending the author. |
| 6 | Pools get the Director note | **Fixed.** `WATER` group, impermeable, no Director note. |
| 7 | "Projected area", cantilevers, eaves, s.4.3.1 missing from the footprint instruction | **Fixed.** `FOOTPRINT_NOTE`; s.4.3.1 quoted in the extract. |
| 8 | Use scope too narrow; laneway house question unanswerable from the repo | **Fixed in scope**; **open on Section 11.** All non-s.3.1 uses assessed; laneway footprint counted and flagged. Section 11 still needs to be downloaded and read. |
| 9 | Section 2 version and pages wrong | **Fixed** in the extract, register, README and web page. |
| 10 | W2–W3 work not committed | **Open: Kevin's action.** Nothing was committed in this session; see "Still for Kevin" below. |
| 11 | "Site" undefined; one parcel assumed | **Fixed.** Definition quoted; `outlines` accepted. |
| 12 | Demo house implausible for FSR | **Left, disclosed.** The 294 m² footprint is a lawful single-storey; the extract now says so. A second, more ordinary example (33 ft lot with laneway house) was added instead of redesigning the demo, so the hand-worked table and figures stay valid. |
| 13 | Rhino bounding boxes; hard-coded street | **Fixed.** |
| 14 | s.3.2.2.13 paraphrased; 4-space exclusion lost | **Fixed.** |
| 15 | Smaller items (missing `use` default, concave-lot corner test, long labels, unassigned remainder, multiplex wording, test count) | **Fixed**: concave lots clipped exactly; labels truncated to the column; a note when more than half the lot is undrawn; "no numeric limit in this schedule"; counts corrected. Missing `use` still defaults to single detached house, as before. |

### Review B — studio crit

| # | Finding | Response |
|---|---|---|
| 1 | The tool is not in the public repository; remote main presents the map | **Open: Kevin's decision.** See below. |
| 2 | README not in the brief's structure, a week stale | **Fixed.** Five headings. The Purpose paragraph is Kevin's W1 wording with a comment asking him to review it, since the brief says he writes it himself. |
| 3 | False statements in README (test count, PDF presence, pages) | **Fixed.** |
| 4 | No CLI validation | **Fixed.** |
| 5 | Feet pass as metres | **Fixed.** Warning, and `"units": "ft"`. |
| 6 | Exact-match materials; typo inverts the lesson | **Fixed.** Aliases; "Unrecognised … did you mean". |
| 7 | Wood with no conditions reported with invented facts | **Fixed.** |
| 8 | The 3D does not earn its third dimension | **Partly addressed; the design choice is left to Kevin.** The column now shows counted (clipped, de-duplicated) areas, raised decks float at their height, and the 50% plane is darker. Replacing the column with a storm-volume solid (the W1 shortlist's own idea) is a hydrology framing choice and is listed below for Kevin. |
| 9 | Drawing does not separate real from invented | **Fixed.** Title block; ground near-white and labelled "no surface drawn: not counted"; yards labelled "orientation only". |
| 10 | Script deletes the user's named views | **Fixed.** Only `R1-1 …` views are replaced. |
| 11 | The surprise is told, not experienced | **Fixed.** "What if permeable pavers were permeable?" toggle re-colours the plan, re-draws the bar and column, and labels the result "Not the by-law". |
| 12 | No way to enter your own lot without JSON | **Fixed.** Width × depth × address fields. |
| 13 | No printable result | **Fixed.** "Copy result as text". |
| 14 | Negative dimensions accepted on the CLI | **Fixed.** |
| 15 | Pervious concrete presented as a reading | **Fixed as disclosure.** The reason now says "author's decision; the Director could be asked". |
| 16 | Second project and loose files in the repo | **Partly.** README demotes the precursor to one section. Moving `stormwater.py`, `buildings.py` and `map/` to a folder or another repository is Kevin's call, because the remote main currently presents the map as the tool. Loose files (`test lot.3dm`, the `.pages` file, the brief PDF) are not touched. |
| 17 | Author voice and review status uncertain | **Partly.** Decisions in the extract are dated and attributed; items added on 2026-10-02 are marked as awaiting the author's confirmation, which is true. The missing third prompt approach in `docs/prompt-comparison.md` is not addressed here. |
| 18 | Revision evidence not in version control | **Open: Kevin's action.** Commit. |

### Review C — computational

| # | Finding | Response |
|---|---|---|
| F1 | Tool not in the repository | **Open: Kevin's action.** |
| F2 | "75.00% FAIL, over by 0.00" | **Fixed.** `near_limit`; test `test_near_the_limit_the_report_shows_more_decimals`. |
| F3 | No validation; silent wrong answers | **Fixed.** 23 refusal cases exported and checked in the page too. |
| F4 | Overlap/containment misses | **Fixed.** Exact clipping for any simple polygon; bow-ties refused. |
| F5 | Building parts and synonyms misclassified | **Fixed.** |
| F6 | 8 of 16 injected bugs undetected by the page's self-check | **Fixed.** The eight lots added; the test lots are the exported lots; refusals and suggestions checked. |
| F7 | Stale version / count claims | **Fixed.** |
| F8 | Rhino bounding boxes; hard-coded street; `.lower()` on a non-string | **Fixed.** |
| F9 | Tautological tests, untested paths | **Fixed.** The tautologies are gone; s.3.2.2.7 FAIL, over-assignment, polygons, not-applicable report, 601 mm, 306 m², 7.3 m, the 2 cm band, aliases and river rock with a layer all have tests. |
| F10 | Not-assessed report drops warnings | **Fixed.** |
| F11 | No doctype; data block inside the page; CDN scripts | **Fixed** for the first two. The three.js scripts still load from CDNs without integrity hashes; the page works offline except for the drawing. |
| F12 | Hygiene | **Partly.** See B16. |
| F13 | Interpretation consistency: on-grade for all listed materials; river rock `size > 0`; negative heights | **Fixed.** |

## Spot checks on the reviewers' own inputs

| Input | Before | After |
|---|---|---|
| A T1, house + porch + garage + laneway | buildings 107.24 m² (28.66%); porch and garage "Director may accept as permeable" | buildings 171.68 m² (45.89%); laneway flagged |
| A T3, deck over patio, driveway into lane | "Over by 44.71 m²" FAIL from double counting | 48.47% PASS; deck counted once; 11.94 m² of driveway outside the lot not counted |
| A T2, pool and hot tub | pool "Director may accept it as permeable" | pool impermeable, "passes no water to the soil" |
| A T8, `height_mm: "900"`, negative width | `TypeError` | two sentences, exit 2 |
| B feet lot, 33 × 122 | 4,026 m², PASS, silent | same, plus "Are these dimensions in feet?" |
| B "permable pavers" | "the Director may accept it as permeable" | "Did you mean permeable pavers?" |
| B deck with no conditions | "boards not spaced, not installed on grade" | "spacing not stated, on-grade not stated, layer below not stated" |
| B `rectangle` key | `KeyError: 'polygon'` | "has no geometry. Give rect …" |
| C 72, 300.02 of 400 m² | "75.00% FAIL, over by 0.02" | "75.0050% FAIL, over by 0.020 m², verdict uses unrounded areas" |
| C 80, negative-width twin rectangles | 75% PASS, no overlap warning | refused: "width and depth must be positive" |
| C 07, slab over a notch in a U-shaped lot | 80 m² counted, no warning | 40.16 m² counted, 39.84 outside |
| C 01, bow-tie polygon | 0.00 m², no warning | refused: "crosses itself" |
| C 83, RT-7 lot with a surface outside | warnings dropped | warnings printed under NOT ASSESSED |

## Still for Kevin

These were raised by the reviews and are decisions or actions only the author
can take. None of them was done in this session.

1. **Commit and publish.** `tool/`, `examples/`, `output/`, `skill/`,
   `docs/reviews/`, this file, the extract and
   `sources/zoning-by-law-section-2.pdf` are untracked on this machine.
   The remote `main` is eight commits ahead of the local branches, its README
   says "The interactive map is the current tool", and GitHub Pages deploys
   `map/`. A classmate assigned this repository at 1:30 pm on 2026-10-02 will
   review the map, not this tool. Decide which tool is the submission, make
   the README on `main` match, and either publish `tool/web/` with Pages or
   remove the map's Pages link. Local `main` and `origin/main` also have
   different histories (an identity-scrub rewrite), so reconcile before
   pushing.
2. **Write the Purpose** in your own words (the brief requires it; 150 words
   or fewer). The current paragraph is your W1 text with a comment on it.
3. **Confirm or reject the 2026-10-02 readings** in
   `sources/r1-1-impermeable-extract.md` §2: the building vocabulary, the
   laneway house counted and flagged, pools without a Director note, the
   on-grade condition applied to gravel and rock, the unknown-name flag. Each
   is marked "(2026-10-02)" and "awaits the author's confirmation".
4. **Download Section 11** (`bylaws.vancouver.ca/zoning/zoning-by-law-section-11.pdf`)
   and read s.11.24 (laneway houses) to close the laneway-footprint question.
5. **Decide what the 3D column carries.** Reviewer B's point stands: the
   column is a bar chart. Your W1 shortlist proposed extruding the design
   storm's runoff volume on the impermeable area. That brings the 48 mm Rain
   City figure into the by-law tool, which you have kept apart so far; it is
   your call.
6. **Tidy the repository**: `precursor/` or a second repository for
   `stormwater.py`, `buildings.py` and `map/`; remove or ignore
   `test lot.3dm`, the `.pages` file and the brief PDF.
7. ~~Regenerate `output/*.png`~~ Done on 2026-10-02: `output/` holds the six
   views captured from Rhino 8 with the rebuilt script, `all-views.jpg`, and
   the `.3dm` of all three examples. The 2026-09-24 renders are superseded.
