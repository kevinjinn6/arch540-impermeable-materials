# Review A — R1-1 s.3.2.2.8 impermeable-materials tool
Reviewer persona: Vancouver landscape architect preparing DP applications under the Zoning and Development By-law.
Repository reviewed read-only at: /Users/kevinjinn/Documents/Year 3/Arch 540/Assignment 1 (working tree, branch stage2-policy-map).
All by-law quotations below are extracted with pypdf from the PDFs in sources/; page numbers are the printed page numbers in those PDFs.

## PART 1 — class peer-review format

1. **What input I tried.** Both shipped examples, the 33-test suite, and nine inputs of my own: a 33 ft lot with house + front porch + detached garage + laneway house; a 50 ft corner lot with pool, hot tub, porous-asphalt drive and artificial turf; a raised deck over a stone patio plus a driveway running 4 m into the lane and a roof drawn with eaves; a duplex on an irregular two-parcel polygon with polygon surfaces; a gravel drive on compacted base, green roof, river rock, mulch on fabric, retaining wall; three malformed files; and seven `use` variants.

2. **Did I understand the result and could I match it to the source?** Yes for the shipped example: every number in the terminal, the Rhino plan and the hand-worked table reconciles to 0.01 m², and s.3.2.2.7/.8 (schedule p.12), s.4.2.2 (p.16) and the two Section 2 definitions (p.20, p.31 of the June 2026 PDF) say what the tool says they say, word for word. But the repo cites Section 2 to a "November 2025" copy it says is not in the repo, while the June 2026 PDF sits in sources/ and two of the four page numbers are wrong for it.

3. **What broke or confused me.** A front porch, a detached garage and a laneway house all came back "Not named in the by-law… the Director of Planning may accept it as permeable" and were left out of the 50% building test, though Section 2 names porches in the building clause. A driveway crossing the lot line was counted at full area including the part in the lane. A raised deck over a patio was double-counted into a FAIL. Three plausible input mistakes crash with Python tracebacks.

4. **The one change I would make first.** Teach the classifier the building clause of Section 2 — porches, entries, verandahs, carports, accessory buildings, laneway houses are "all buildings", not unlisted materials — and clip or refuse any surface that leaves the site.

---

## PART 2 — full critique

### A. Weaknesses (numbered, with severity, evidence, consequence, fix)

**1. Buildings other than "the house" are misclassified and dropped from the s.3.2.2.7 test. — CRITICAL**
Evidence: `tool/impermeable_check.py` L207 recognises a building only when `material == "building"`; anything else unrecognised falls to L244-246 and is labelled with `NOT_NAMED_DEFAULT` (L145-146): "Not named in the by-law. Counted as impermeable; the Director of Planning may accept it as permeable." My test T1 (house 107.24 + porch 6.00 + garage 21.96 + laneway house 36.48 m²) reported "s.3.2.2.7 buildings 107.24 m² = 28.66%"; the correct building total is 171.68 m² = 45.9%. Section 2 p.20: "Impermeable Materials: The projected area of the outside of the outermost walls of all buildings, including carports, entries, porches and verandahs…". Section 2 p.1-2 defines Accessory Building; p.22 defines Laneway House as "A detached dwelling unit constructed in the rear yard…".
Why it matters: nearly every R1-1 application has a porch and a garage or laneway house. Telling an applicant the Director might accept a porch or a garage as permeable is not a conservative error, it is a wrong statement of the by-law, and the 50% coverage figure is understated by up to 17 points on an ordinary lot.
Fix: add a building-vocabulary set ("accessory building", "garage", "shed", "laneway house", "porch", "verandah", "entry", "carport") that returns class `building`; flag the laneway house separately (see 8); remove the Director note from anything that is a structure.

**2. Area outside the site is counted toward the site's total. — MAJOR**
Evidence: L361 computes `polygon_area(pts)` before the inside test at L364-367, which only appends a warning. Probe: a 3 × 10 m concrete strip with 5 m beyond the lot line returned `impermeable_m2 = 30.0`. T3 "Driveway incl. lane crossing" counted 39.00 m² when 27.00 m² lies inside the lot.
Why it matters: lane aprons and boulevard crossings are on every site plan; s.3.2.2.8 is "75% of the site area" and the City measures what is on the site. The tool inflates the total exactly where applicants draw to the curb.
Fix: clip each surface to the site outline (rectangle-vs-polygon clipping is small without shapely; or reject the surface with a hard error instead of a soft warning).

**3. Overlapping surfaces are double-counted and still produce a verdict. — MAJOR**
Evidence: L374-386 warns on overlap but L392-393 sums every row. T3: patio 20.00 and raised deck 20.00 on the same rectangle both counted; "walls" 107.24 and "roof incl. eaves" 134.67 both counted as building; the verdict read "Over by 44.71 m²", of which 130 m² of the total is duplicated area. Section 2's measure is a "projected area", which is a single plan projection, not a sum of layers.
Why it matters: a main-floor deck over a basement-level patio is the standard Vancouver rear-yard section. The tool fails a design that the by-law may pass.
Fix: for surfaces of the same counted class, subtract pairwise rectangle overlaps (already computed at L379) from the total, or withhold the verdict ("cannot assess: overlapping surfaces") rather than print FAIL.

**4. Plausible inputs crash with tracebacks. — MAJOR**
Evidence: missing `"label"` → `KeyError: 'label'` at L369; a surface with `"area_m2"` instead of geometry → `KeyError: 'polygon'` at L284; `"height_mm": "900"` → `TypeError` at L176. The README (L138) offers the tool "for a reviewer who doesn't have Rhino"; an applicant typing JSON by hand will hit all three.
Fix: validate each surface up front (required keys, numeric fields, non-negative width/depth) and print one plain-language error naming the surface.

**5. The "on grade / no impermeable layer" condition is presented as the definition when it is the author's extension — and the quotation is cut to hide the join. — MAJOR**
Evidence: Section 2 p.31 reads in full: "Materials including gravel, river rock less than 5 cm in size, wood chips, bark mulch, wood decking with spaced boards and other materials which, in the opinion of the Director of Planning, have fully permeable characteristics when placed or installed on grade with no associated layer of impermeable material, such as plastic sheeting, that would impede the movement of water directly to the soil below." The "when placed or installed on grade…" clause most naturally modifies "have fully permeable characteristics" in the Director's-opinion limb. The tool's quotation at L98-101 elides exactly that limb ("wood decking with spaced boards ... when placed or installed on grade"), so the condition appears to govern the named list. The extract itself (L91-98) calls this an extension "awaiting the author's confirmation", yet the tool prints as fact "Raised deck (1500 mm, over 600 mm) is not on grade, so the spaced-decking exception cannot apply" (L177-180) and "Gravel over an impermeable layer does not meet the Permeable Materials definition" (L224-226).
Why it matters: whether a spaced-board deck 1.2 m over lawn counts is one of the two or three live arguments at the DBSC counter for this clause. An applicant relying on the tool would concede the point before it was argued. The conservative answer may be prudent, but it must be labelled as a reading, with the alternative stated.
Fix: quote the sentence whole; mark the three-condition test and the gravel-over-plastic rule "author's reading, stricter than the plain grammar; the City may read the on-grade condition as applying only to Director-approved materials"; keep the raised-deck flag.

**6. Pools and hot tubs get the "Director may accept it as permeable" note. — MAJOR**
Evidence: T2 "Swimming pool … Not named in the by-law. Counted as impermeable; the Director of Planning may accept it as permeable." Section 2 mentions "Swimming Pool" only as a Cultural and Recreational use (p.10), never as a material.
Why it matters: no applicant will plead that a pool is permeable, and the note invites exactly that. The by-law is silent on water bodies; the tool should say so, not point at a relaxation that does not exist for them.
Fix: a "water" group (swimming pool, hot tub, pond) → impermeable with "Not a listed material; a water-filled structure is not a candidate for the Director's permeability opinion; confirm treatment with the City."

**7. The building footprint instruction drops "projected area" and says nothing about cantilevers, bays or basements. — MAJOR**
Evidence: L108-110: "Outside face of the outermost walls. Measure it to include carports, entries, porches and verandahs". Section 2 p.20 says "The projected area of the outside of the outermost walls". Schedule s.4.3.1 p.16: "No portion of the basement or cellar may project horizontally beyond the perimeter of the first storey, including entries, porches and verandahs."
Why it matters: "projected" is the operative word for an upper-storey cantilever or bay window; those go in. Eaves are not walls; they stay out (my T3 "roof incl. eaves" should not be enterable as building). The hand-worked example and both drawings never say which storey the 12.8 × 23.0 rectangle represents.
Fix: quote "projected area"; instruct: plan projection of every storey's exterior walls including cantilevers and bays, plus porches/entries/verandahs/carports; exclude eaves and gutters; note s.4.3.1 so the basement never governs.

**8. Use scope is narrower than s.3.2 and the laneway-house question is raised but cannot be answered from the sources provided. — MAJOR**
Evidence: `S32_USES` L66-67 is four strings; L340-342 declines everything else. Schedule p.12: "3.2 Other Uses — All other uses not regulated by section 3.1 of this schedule are subject to the following regulations." So s.3.2.2.8 governs infill, multiple conversion dwelling, child day care facility conversion dwelling (s.2.2.15), community care class A (s.2.2.11 "subject to the regulations… that apply to single detached house"), etc.; the tool reports "outside the s.3.2 uses this tool assesses" for all of them. `use: "laneway house"` is also declined, but a laneway house never stands alone — the site still carries a single detached house and still faces s.3.2.2.8; the only question is whether the laneway footprint counts. s.2.2.4 p.5: "Laneway house is regulated by Section 11 of this by-law and sections 3 and 4 of this schedule do not apply." Section 11 is not in sources/, so `docs/regulation-shortlist.md` L84-86 raises the question and nothing in the repo can close it.
Fix: assess every non-s.3.1 use (with s.3.2.2.14 noted for non-dwelling uses); add the Section 11 laneway-house PDF to sources/ and resolve the footprint question from its text, then flag it in output rather than refusing the whole site.

**9. The Section 2 version statement is wrong throughout, and the pages cited are for a different edition. — MAJOR (for a brief that grades version visibility)**
Evidence: `sources/zoning-by-law-section-2.pdf` is present and prints "City of Vancouver June 2026" on all 50 pages. Yet `README.md` L191-193 ("The June 2026 PDF is not yet in the repo"), `sources/r1-1-impermeable-extract.md` L24-27 ("Nov 2025 ‡") and L31-38, `sources/README.md` L13 ("not yet stored in this repo"), and `tool/web/index.html` L268-269 ("Section 2 Definitions, November 2025 consolidation") all say otherwise. Checked against the PDF actually present: Impermeable Materials is p.20 (cited p.21); Deck is p.11 (cited p.12); Permeable Materials p.31 and Patio p.30 are correct. The wording of all four matches verbatim.
Fix: re-cite the four rows to the June 2026 pages, rewrite the register row, delete the ‡ caveat, fix the web footer.

**10. The W2–W3 work is not committed. — MAJOR (process)**
Evidence: `git status --porcelain` shows `tool/`, `examples/`, `output/`, `sources/r1-1-impermeable-extract.md` and `sources/zoning-by-law-section-2.pdf` as untracked; `git ls-files` confirms HEAD (060d44e) contains none of them. A peer who clones the repository to file issues gets the W1 prototypes and `stormwater.py`, not the tool this README describes.
Fix: commit them (the PDF is a by-law, fine to track; `output/*.3dm` may need Git LFS or exclusion).

**11. "Site" is never defined or discussed; the tool silently equates site with one City parcel polygon. — MINOR/MAJOR**
Evidence: Section 2 p.43: "Site — An area of land consisting of 1 or more adjoining parcels or lots abutting on a street not being a lane, but does not include a strata lot or a leasehold parcel…". README L194 says only "Site area is the City's parcel polygon, not a legal survey." T4 (two parcels drawn as one polygon) was accepted without comment.
Why it matters: duplex and multiplex sites are often two consolidated 25 ft or 33 ft lots; the City's parcel polygon is one lot. The legal survey, not the polygon, fixes the denominator of every percentage.
Fix: quote the Site definition in the extract; accept a list of parcel polygons and union them; keep the survey caveat.

**12. The demonstration house cannot be built under s.3.2.1.1. — MINOR (declared synthetic, but it drives the pedagogy)**
Evidence: footprint 12.8 × 23.0 = 294.4 m² on 602.04 m² = 48.9% coverage. Schedule p.12: "3.2.1.1 The maximum floor space ratio is 0.60" → 361.2 m² of floor area; s.4.1.1(a) p.14 counts "all floors". One storey at that footprint is FSR 0.49; two storeys 0.98. A 0.60 FSR house on this lot has a footprint nearer 150 m², and then the same hardscape gives ≈ 51%, not 75.55%.
Why it matters: the tool's headline ("FAIL by 3.34 m²") is tuned by an impossible house. A practitioner's question is where 75% actually binds — small lots, duplexes, large parking pads — and the example does not show that.
Fix: rebuild the example around a 0.60 FSR footprint and let the pavers plus a pool or a second parking pad produce the breach.

**13. Rhino draws polygon surfaces as their bounding boxes and hard-codes the street name. — MINOR**
Evidence: `tool/rhino_draw.py` L273-279 takes min/max of the points and calls `box(x0, y0, x1, y1, 0.01, top)`; L316 writes "W 30th Ave  (street)" for every example.
Fix: build a planar Brep from the polygon; take the street name from `site["address"]`.

**14. s.3.2.2.13 is paraphrased loosely and the reason it rarely applies to houses is lost. — MINOR**
Evidence: extract L124-125 "(30% of a site used as a parking area)". Schedule p.13: "Except where the principal use of the site is a parking area, the maximum site coverage for any portion of the site used as a parking area is 30%." Section 2 p.30 "Parking Area … does not include an area providing 4 or fewer spaces accessory to a residential use" — `week-01/prompt-b-high-context/HANDOFF.md` L96 recorded this correctly; the W3 extract dropped it.
Fix: restore the exact clause and the 4-space exclusion so a user knows when the 30% test is live.

**15. Smaller correctness and robustness items. — MINOR**
- L333: a missing `use` silently becomes "single detached house"; say so in the report.
- L364: inside test uses corners only; a slab spanning a notch in a concave lot passed unflagged in my probe.
- L462/L467: labels longer than 18 characters run into the material column (visible in T2/T3 output).
- Unassigned remainder is "not counted" with no threshold warning; a plan that omits hardscape passes silently.
- Multiplex message (L337-339) "s.3.1 … sets no impermeability limit" is a correct reading of this schedule's silence, but s.4 "All uses in this district are subject to the following regulations" (p.14) still applies, and other instruments (Sewer and Watercourse By-law, multiplex guidelines) can impose permeability conditions; soften to "this schedule sets no numeric limit for s.3.1 uses".
- README L31/L44 say "25 test cases"; 33 run.

### B. What a permit reviewer measures that the tool cannot know (for the Unresolved section)
Outermost-wall projection per storey vs. the roof; porches and covered entries (Section 2 p.14 definition); cantilevers and bays ("projected area"); basement perimeter (s.4.3.1); window wells and sunken entries (s.4.3.2 allows them — they are lowered ground, usually hard-surfaced); exterior stairs and landings; retaining walls (a 300 mm wall is a wall, not a surface — but its top is impermeable); garages, sheds, laneway houses (Section 11); pools and hot tubs; the legal survey vs. the parcel polygon and the Section 2 "Site" definition; the 4-space exclusion before s.3.2.2.13 is live; and s.3.2.2.14, which is the only relaxation and is for non-dwelling uses — there is no relaxation for a house, so the tool's PASS/FAIL really is binary for dwellings, which is worth saying out loud.

### C. Ranked: five changes that would most strengthen the tool against the by-law
1. Make the classifier speak Section 2's building clause: porches, entries, verandahs, carports, accessory buildings and laneway houses are buildings; remove the Director note from structures and water bodies (items 1, 6).
2. Geometric integrity before any verdict: clip to the site, net out same-class overlaps or withhold the verdict, validate input (items 2, 3, 4).
3. Quote the Permeable Materials sentence whole and label the on-grade/no-layer test as the author's stricter reading, with the alternative reading stated; quote "projected area" for buildings and reference s.4.3.1 (items 5, 7).
4. Close the version gap with the PDF already in the folder: re-cite pages to June 2026, fix README, register and web footer, and commit tool/, examples/, output/, the extract and the PDF (items 9, 10).
5. Widen the use scope to every non-s.3.1 use, add Section 11 to sources/ and answer the laneway-footprint question from its text, and cite the Section 2 "Site" definition with multi-parcel input (items 8, 11).

### D. What the project does well
The core insight is right and is the thing practitioners actually get wrong: Section 2 p.20 does name "permeable pavers" as impermeable and p.31 does make "wood decking with spaced boards" the only wood that escapes, and the tool decides wood by its conditions rather than its name, which is how a reviewer thinks. The three verified clauses (s.3.2.2.7, s.3.2.2.8, s.4.2.2) are quoted verbatim with the right pages; the hand-worked table in the extract reconciles to the code to the square metre; the 602.04 m² site area matches the City parcel record (I checked it against map/data/lots.geojson); exactly-at-the-limit passes, as "maximum" requires; the Rhino column and the web page give the same numbers as the terminal, and the page's self-check against 133 material cases and 74 lots is a genuinely good discipline. The register separates by-law from guidance from strategy and records retrieval routes honestly. The limitations are stated rather than hidden. What is missing is not care, it is vocabulary and geometry: the tool knows one building and one kind of lot line, and a real application has several of each.
