# Response to the three outside reviews of the map (2026-10-02)

The tool under review was the live map at
<https://kevinjinn6.github.io/arch540-impermeable-materials/>, byte-identical
to `map/index.html` at commit 54ada95 on `origin/main`, with the repository
as published there. Three reviewers read it cold, without the author in the
room, each from a different seat:

| | Lens | Report |
|---|---|---|
| A | Zoning plan checker / development permit reviewer | [`reviews/2026-10-02-map-review-a-permit-practice.md`](reviews/2026-10-02-map-review-a-permit-practice.md) |
| B | Design critic and educator, outside guest at the final review | [`reviews/2026-10-02-map-review-b-studio-crit.md`](reviews/2026-10-02-map-review-b-studio-crit.md) |
| C | Computational designer / geospatial engineer | [`reviews/2026-10-02-map-review-c-computational.md`](reviews/2026-10-02-map-review-c-computational.md) |

All three reproduced the page's numbers exactly before criticising it. Their
findings are answered one by one below. First, what they agreed on and what
changed.

## The five themes, and what changed

| Theme | Raised by | What the live page did | What the rebuilt page does |
|---|---|---|---|
| **The 13,594 "potential exceedances" are an eave artefact.** The 2015 footprints trace the roof edge; the by-law measures walls. 9,725 of the 13,594 sit between 50% and 55%. | A1, B3, C1 | Printed the count in 22 px amber, outlined 13,594 real addresses, clustered them citywide, and said POTENTIAL EXCEEDANCE in the popup. | Measures every roof both ways. A 0.45 m eave allowance is taken off for the by-law test (`map/data/roof-walls.json`, `map/roof_walls.py`); both figures are shown on every lot. Over 50% to the walls: 769 assessed sites, outlined and clustered in amber as *check*, never *exceedance*; the author kept the circles. The sensitivity is stated in the notes. |
| **The definitions the README says the tool is for were not in the tool.** | A3, B1, B8 | No passage, page, link or the word "paver" anywhere. | s.3.2.2.7, s.3.2.2.8 and s.4.2.2 quoted at the top with pages; Section 2's Impermeable Materials, Permeable Materials and Site verbatim under *What counts*; links to the City PDFs; every surface in a lot's schedule names the passage it rests on. |
| **The slider was a parameter sweep that could not cross the limit.** | B2, B5, B7, C2 | One hypothetical share, 0–75%, applied to every lot; the only computation was the storm formula, which is linear in area and so independent of the lot data. | The operation is per lot: room = 0.75 × site − roofs to the walls. The slider adds square metres of a named material to every lot; lots whose room runs out turn purple, and a tick on the slider marks the selected lot's own room. Switching the material from concrete to permeable pavers changes nothing; switching to gravel never crosses. The storm figures now use each lot's own share, so roofs and water finally meet. |
| **The by-law and the Rain City Strategy were separated in the repo but not on the page.** | A5, B6, B7, C4 | "During a design storm" with no attribution; a "~40% soil full" tick on the same scale as "75% bylaw maximum"; the water card between the two rule boxes. | The storm card sits last, tagged *Not the by-law*, names the Strategy as a Council policy, states that R1-1 has no retention requirement, and lists 85% runoff and 75 mm soil as this page's assumptions. No hydrology mark on the by-law control. |
| **The package the brief asks for was not published.** | A10, B4, C3, C10 | No Rhino, no skill, no example screenshot, no tests, Section 2 PDF absent, README not in the wrap-up's order, unpinned dependencies, data tracked against `.gitignore`. | `map/rhino_site.py` draws any lot from the map's data; `skill/SKILL.md`; README rewritten to the five wrap-up headings with the live link at the top and the worked example; `map/check_data.py` run by the Pages workflow; `requirements.txt` pinned; `.gitignore` corrected; Section 2 PDF in `sources/`. The page screenshot and the commit are still Kevin's (below). |

## What else changed

- **Opens honestly.** The slider opens at 0 m² added (roofs only) and the map
  opens on the README's example lot with its card filled in; the title says
  "impermeable materials", not "hardscape" (A4).
- **Honours the pipeline's own flags.** Parcels flagged `cd` (roof over 90%)
  or `f` (shared address, not adjoining), and parcels under 150 m², are grey
  and *not assessed*; the sixteen purple "roof alone exceeds 75%" sites, twelve
  of them sub-minimum slivers, are gone (A2, A9, C5). Parcels under the 306 m²
  minimum site area of s.3.2.2.1 are assessed but say so on the card.
- **Every printed number is built from the CONFIGURATION constants** (C4); the
  materials table carries the passage each material rests on, so adding a
  material is one line.
- **Simpler drawing code.** The building-reveal shader is gone; roofs are a
  plain MapLibre layer fetched only when the map is close enough to show them
  (C6, C7). The lot shader uses `highp` and carries each lot's own roof share
  and area, so the colour is per lot.
- **Address search** gives a keyboard route to every result (C9); the panel's
  small text is darker (contrast ≥ 4.5:1); errors in the basemap, the library
  or the data replace the loading text instead of hanging (C8).
- **Rhino.** `map/rhino_site.py` draws the site from the City parcel, its 2015
  roofs raised to their recorded heights with the eave allowance inside each,
  and an *area bar* beside the site marked at 50% and 75%. It reads the same
  roof-to-walls figure as the page, so the two agree to the square metre.

## Finding by finding

**Review A (permit practice)**

| # | Finding | Response |
|---|---|---|
| A1 | Most "potential exceedances" lie inside the method's upward bias | **Changed.** Eave allowance; both figures shown; the word *exceedance* removed; flagged sites say *check* with the year in the same card. The tolerance-band idea became a measured second figure rather than a band, which A also offered. |
| A2 | Data-quality flags discarded; artefacts drawn as the severest class | **Changed.** `cd`, `f` and parcels under 150 m² are grey, "Check data", not assessed. |
| A3 | Definitions absent; Section 2 PDF not in the package | **Changed.** Verbatim on the page with pages and links; PDF in `sources/`. Deck (p.11) and the "on grade" condition are in the materials table and the notes. |
| A4 | Opens at the maximum, titled as a survey, "hardscape" | **Changed.** Opens at 0 m² on the example lot; "impermeable materials" throughout. |
| A5 | Rain City not attributed on the page | **Changed.** Storm card tagged, attributed, assumptions listed; no hydrology mark on the by-law slider. |
| A6 | Rounding contradicts the flag (50.0% "exceedance") | **Changed.** No flag depends on a rounded figure; the walls figure is the test and reads well clear of 50% for the sites outlined. |
| A7 | "May not exceed 50%" is true only for s.3.2 uses; laneway houses under Section 11 | **Changed.** Notes say s.3.2 uses; laneway houses named as counted-but-unchecked (Section 11 not in the repo). |
| A8 | "Excludes eaves" is an inference | **Changed in wording.** The page and the extract say the walls reading rests on Section 2's "outermost walls" and that Section 10 (projections) has not been checked. |
| A9 | Scope leaks: empty addresses, Cassiar Connector, sub-306 m² parcels | **Partly.** Under-150 m² parcels not assessed; sub-306 labelled; empty-address lots stay (the by-law applies to them) but the card says "no civic address in the parcel data". Changing `sc` in the pipeline is Kevin's call (below). |
| A10 | Package completeness | **Changed**, except the page screenshot and the commit, which are Kevin's. |

**Review B (studio crit)**

| # | Finding | Response |
|---|---|---|
| B1 | The tool contains none of the knowledge it claims to teach | **Changed.** See theme 2. |
| B2 | The slider is a parameter sweep, not an operation | **Changed.** The per-lot schedule in the card is the Section 2 classification B asked for; the slider is now square metres of a named material with a visible fail state. |
| B3 | The 50% apparatus: wrong rule, wrong data, wrong year | **Changed.** Demoted to one line of context citywide and a *check* outline at street zoom; the headline is s.3.2.2.8. |
| B4 | Required deliverables absent | **Changed**, except the screenshot and the commit. |
| B5 | Scope runs against the brief | **Partly.** The page now opens on one lot and the city is the context, as B proposed. The citywide layer stays: it is what makes the pavers lesson visible at scale (concrete and pavers give the same map). Kevin may still cut it. |
| B6 | The page disclaims itself more than it explains | **Changed.** Most hedges went with the image they hedged; the ones left name a specific assumption. |
| B7 | Lot drawing semantics contradict the by-law | **Partly.** The author kept the previous visual language (blue permeable, red impermeable growing from the south edge, amber circles when zoomed out); purple now means over 75%, houses no longer vanish, the red share is each lot's own, and the legend calls the split a diagram. |
| B8 | Nothing lets a user check a result against the source | **Changed.** Passages with pages on the page; "check by hand" arithmetic on every card; the README's example reproduces on a calculator. |

**Review C (computational)**

| # | Finding | Response |
|---|---|---|
| C1 | Exceedance count dominated by the eave artefact | **Changed.** C's own table (13,595 → 2,593 → 804 → 249 at 0 / 0.3 / 0.45 / 0.6 m) matches ours (13,594 → 2,482 → 777 → 242, the difference being `make_valid` and clipping order). 0.45 m is the default and is one constant in three files. |
| C2 | The water card is independent of the lot data | **Changed.** Each lot's own share (roofs to the walls plus the added surface) goes into the balance, so the roofs now move the water figures; the formula and constants are unchanged. |
| C3 | Not reproducible: unpinned, data vs `.gitignore`, no manifest, no tests | **Partly.** `requirements.txt` pinned; `.gitignore` corrected; `map/check_data.py` pins the published figures and runs before every deploy. A pipeline-written manifest is in the staged `buildings.py` change (below), not yet applied. |
| C4 | CONFIGURATION contract does not hold | **Changed** on the page: every string is templated. The three copies of the hydrology constants remain (`stormwater.py` 0.9/30 mm is Stage 1's and documented as such). |
| C5 | Scope flags admit non-lots; sparse flags unused | **Changed** on the page (see A2, A9). Pipeline-side `sc` changes are Kevin's. |
| C6 | Shader edge cases | **Changed.** `highp`; the reveal logic is gone; the bbox-height split is named as a diagram in the legend. An area-true split would need per-lot slicing on every slider move and was not attempted. |
| C7 | Phone performance | **Partly.** Footprints fetched only at zoom ≥ 14 and their properties dropped after parsing; the README states the compressed size. The files themselves are unchanged (regenerating them is blocked, below). |
| C8 | Error handling covers one failure mode | **Changed.** Library, basemap and data failures each replace the loading text; a footprint failure is announced in the legend. |
| C9 | Accessibility | **Partly.** Address search; darker small text. The red/blue pair stays by the author's choice; no hatch pattern was added. |
| C10 | Vintage and documentation drift | **Changed** in the README and notes; the 2009 heights are now used (by the Rhino drawing). |

## Spot checks

The page's arithmetic was run outside a browser in JavaScriptCore over the
real data and compared with an independent Python computation. Every figure
agreed:

| Setting | Lots over 75% | Rain held | Overflow |
|---|---:|---:|---:|
| Roofs only (to the walls) | 1 | 93.7% | 19,312 m³ |
| + 60 m² concrete per lot | 157 | 81.4% | 169,909 m³ |
| + 90 m² concrete | 1,374 | 73.1% | 276,264 m³ |
| + 120 m² concrete | 10,944 | 64.2% | 390,601 m³ |
| + 90 m² gravel | 1 | 93.7% | 19,312 m³ |

62,188 lots assessed; 13,581 over 50% to the roof edge, 769 to the walls.
3528 W 30th Ave: site 602.04, roofs 280.40 (46.6%), to the walls 237.22
(39.4%), room 214.31 m²; with the illustrative schedule 319.22 m² = 53.0%,
PASS by 132.31 m²; if the pavers were permeable, 45.5%. The Rhino drawing
prints the same figures. `map/check_data.py` passes on the published data.

The page itself was not screenshotted: no browser could be driven from the
session (headless Chrome hangs on this machine). It was opened in Kevin's
browser from a local server for him to look at.

## One change that could not be made here

The reviewers' first fix was to compute the eave-corrected roof area inside
`buildings.py` and write it into `lots.geojson`. The session's permission
layer refused to overwrite the tracked `buildings.py` and to regenerate
`map/data/`, and that refusal was respected. Instead:

- `map/roof_walls.py` computes the same figure from the published footprints
  into a separate `map/data/roof-walls.json`, which the page and the Rhino
  script read; the page falls back to the roof edge, and says so, if the
  file is missing.
- A patched `buildings.py` that adds `EAVE_M`, a second clip with the
  allowance taken off, `roof_wall_m2` / `rw` in `lots.geojson` and a printed
  comparison, is kept outside the repository for Kevin to apply when he
  regenerates the data. Its diff is in the appendix.

## After the author's own review (2026-10-02)

Kevin's requests, applied the same day: the previous visual language kept
(blue permeable, red impermeable, amber outlines and amber cluster circles);
purple for over 75%; a purple tick on the slider at the selected lot's room,
with the track blue up to it and purple past it, answering "why does the
slider go past what the City allows?" (the 75% is of each lot's site area,
not of the slider; passing the tick is how a lot fails); an area bar in the
lot card, the site as 100% marked at 50% and 75%; the legend reduced to six
swatches with two or three words each; the notes and the lot's arithmetic
moved behind disclosures; every paragraph in the panel shortened. Permeable
pavers re-verified against By-law 13670 (2023) and the City's stated reason,
and the page now says so in one line.

## Still for Kevin

1. **Reconcile the two histories and commit.** `origin/main` (8 commits,
   rewritten history) holds the published map and data; the local branch
   `stage2-policy-map` holds this work on the older history. The simplest
   route is a fresh branch from `origin/main` with these files copied over.
   Nothing has been committed by the session.
2. **Confirm three defaults** that are the author's to set: the 0.45 m eave
   allowance (0.3 m gives 2,482 sites over 50%, 0.6 m gives 242); the map
   opening on 3528 W 30th Ave rather than the 1300 block of E 17th; and the
   *not assessed* rule (flagged parcels and parcels under 150 m²).
3. **Apply the pipeline change** (appendix) when regenerating, or keep
   `map/roof_walls.py` as the source of `rw`.
4. **Screenshot the page** on the example lot for the README (the comment
   marks the spot) and for the class slide; write the Purpose in your own
   words (≤ 150 words).
5. **Decide about `tool/`**, the single-lot checker from the earlier rebuild:
   keep it as the companion the README now describes, or remove it and the
   two sentences that mention it.
6. **Peer review.** Classmates' reviews arrive as GitHub issues; responses by
   2026-10-09.

## Appendix: the staged `buildings.py` change

Kept at the session scratchpad as `buildings.patched.py`; the same text as this diff. Apply it to `buildings.py` from `origin/main`, run the pipeline, then `map/check_data.py` (update its expected figures from what `buildings.py` prints).

```diff
--- buildings.py (origin/main 54ada95)
+++ buildings.py (staged)
@@ -44,11 +44,16 @@
  2. Roofs only. Driveways, patios and walks are NOT in any City dataset,
     so "today" in this script means "roofs only". Real hard surface today
     is higher.
- 3. ROOF AREA IS LIKELY A SLIGHT OVERESTIMATE. The footprints were traced
-    from air photos, so they follow the ROOF EDGE, eaves included. The by-law
-    measures building coverage to the outside of the walls and excludes
-    eaves (typically 0.3-0.6 m overhang on a house). So roof_area_m2 here
-    will usually be a little larger than the by-law's building area.
+ 3. ROOF AREA IS AN OVERESTIMATE OF THE BY-LAW'S BUILDING AREA. The
+    footprints were traced from air photos, so they follow the ROOF EDGE,
+    eaves included. The by-law measures a building to "the outside of the
+    outermost walls" (Section 2, "Impermeable Materials"); eaves are not
+    walls. A house roof overhangs by about 0.3-0.6 m, which is 11-22% of a
+    typical roof's area. So every footprint is ALSO measured with an eave
+    allowance taken off (EAVE_M, default 0.45 m): roof_wall_m2 / rw. Both
+    numbers are kept; the map shows both. Measured to the roof edge, about
+    13,600 ordinary sites read over 50%; to the walls at 0.45 m, under 800.
+    The air photo cannot tell which is right for any one house.
  4. ZONING SITES. Parcels sharing an address and adjoining are treated as
     one zoning site, per the Section 2 definition of Site. (E.g. 4010 Victoria Drive is
     two parcels and one house.) The impermeable limits apply to the site, so
@@ -113,6 +118,17 @@
 
 # ---- BUILDINGS ---------------------------------------------------------------
 
+EAVE_M = 0.45
+# The eave allowance, in metres. The 2015 footprints were traced from air
+# photos and follow the ROOF EDGE. The by-law measures a building to "the
+# outside of the outermost walls" (Section 2, "Impermeable Materials"), and
+# a Vancouver house roof overhangs its walls by about 0.3-0.6 m. Every
+# footprint is shrunk inwards by this much, then clipped to the site, to
+# estimate the building area the by-law would measure:
+#     roof_area_m2  /  r    the roof edge, as traced        (an upper bound)
+#     roof_wall_m2  /  rw   the roof edge less the eave      (the estimate)
+# Set 0 to turn the allowance off (rw then equals r).
+
 CHECK_DATA_ROOF_SHARE = 0.90
 # Lots whose roofs cover more than this share of the lot (0.90 = 90%) are
 # flagged check_data = true and listed at the end of the run. A house cannot
@@ -407,24 +423,38 @@
 #  JOIN BUILDINGS TO SITES
 # ------------------------------------------------------------------------------
 
-def clip_buildings(fp, parcels):
+def clip_buildings(fp, parcels, inset_m=0.0):
     """Cut every footprint along the parcel lines.
 
     Returns one row per (building, parcel) piece, with the piece's area.
     A building wholly inside one lot gives one piece; a building crossing a
     lot line gives one piece per lot. Parts of buildings that stand on no
     R1-1 parcel produce no piece at all.
+
+    inset_m > 0 first shrinks every footprint inwards by that much (the eave
+    allowance, see EAVE_M) and drops any that vanish. The shrink happens
+    BEFORE the clip, so a building cut by a lot line loses an eave strip
+    along its roof edge only, not along the lot line.
     """
-    pieces = gpd.overlay(fp[["object_id", "geometry"]],
+    fp = fp[["object_id", "geometry"]]
+    if inset_m > 0:
+        fp = fp.copy()
+        fp["geometry"] = fp.geometry.buffer(-inset_m, join_style=2).make_valid()
+        fp = fp[~fp.geometry.is_empty & (fp.geometry.area > 0)]
+    pieces = gpd.overlay(fp,
                          parcels[["site_key", "geometry"]],
                          how="intersection", keep_geom_type=True)
     pieces["area_m2"] = pieces.geometry.area
     return pieces
 
 
-def add_roof_fields(parcels, pieces):
-    """roof_area_m2, building_count, roof_share and check_data per parcel."""
+def add_roof_fields(parcels, pieces, wall_pieces=None):
+    """roof_area_m2, roof_wall_m2, building_count, roof_share, roof_wall_share
+    and check_data per parcel. wall_pieces are the footprints clipped after
+    the eave allowance (EAVE_M); without them roof_wall_m2 = roof_area_m2."""
     roof = pieces.groupby("site_key")["area_m2"].sum()
+    wall = (wall_pieces.groupby("site_key")["area_m2"].sum()
+            if wall_pieces is not None else roof)
     # Count a building on a lot only if a real part of it stands there.
     # Lot lines and footprints never line up perfectly, so many buildings
     # overlap next door by a few square centimetres. Their AREA is still
@@ -436,6 +466,11 @@
                                  .fillna(0).astype(int))
     parcels["roof_share"] = (parcels["roof_area_m2"]
                              / parcels["lot_area_m2"]).round(4)
+    parcels["roof_wall_m2"] = parcels["site_key"].map(wall).fillna(0).round(2)
+    # The eave allowance can only make a building smaller, never larger.
+    parcels["roof_wall_m2"] = parcels[["roof_wall_m2", "roof_area_m2"]].min(axis=1)
+    parcels["roof_wall_share"] = (parcels["roof_wall_m2"]
+                                  / parcels["lot_area_m2"]).round(4)
     parcels["check_data"] = parcels["roof_share"] > CHECK_DATA_ROOF_SHARE
     return parcels
 
@@ -489,9 +524,22 @@
     counted = pieces["area_m2"].sum()
     print(f"  {counted:,.0f} of their {on_r11['area_m2'].sum():,.0f} m2 stands "
           f"on R1-1 parcels and is counted")
+
+    print(f"\nSTEP 3b Clipping again with the {EAVE_M} m eave allowance taken off")
+    wall_pieces = clip_buildings(fp, parcels, inset_m=EAVE_M) if EAVE_M > 0 else None
+    if wall_pieces is not None:
+        print(f"  {wall_pieces['area_m2'].sum():,.0f} m2 to the walls, against "
+              f"{pieces['area_m2'].sum():,.0f} m2 to the roof edge "
+              f"({(1 - wall_pieces['area_m2'].sum() / pieces['area_m2'].sum()):.1%} is eave)")
 
     print("\nSTEP 4  Roof area per site")
-    parcels = add_roof_fields(parcels, pieces)
+    parcels = add_roof_fields(parcels, pieces, wall_pieces)
+    ordinary = parcels[(parcels["lot_area_m2"] <= SCOPE_MAX_SITE_M2)
+                       & parcels["developable_parcel"].astype(bool)]
+    print(f"  roofs over 50% of the site: {int((ordinary['roof_share'] > 0.5).sum()):,} sites "
+          f"to the roof edge, {int((ordinary['roof_wall_share'] > 0.5).sum()):,} to the walls")
+    print(f"  roofs over 75% of the site: {int((ordinary['roof_share'] > 0.75).sum()):,} sites "
+          f"to the roof edge, {int((ordinary['roof_wall_share'] > 0.75).sum()):,} to the walls")
     parcels = add_stormwater_fields(parcels)
     parcels["scope"] = "in"
     parcels.loc[parcels["lot_area_m2"] > SCOPE_MAX_SITE_M2, "scope"] = "large site"
@@ -522,12 +570,13 @@
     Short property names keep the file small -- 64,000 lots x long names
     was most of the old file's size. What each one means:
       k   site_key            ad  address
-      A   site area, m2       r   roof area on the site, m2
+      A   site area, m2       r   roof area on the site, m2 (roof edge)
+      rw  roof area less the EAVE_M eave allowance, m2 (the by-law estimate)
       sc  0 = ordinary lot, 1 = outside scope (large site), 2 = not a lot
       m   1 = merged site     f   1 = shared address, not adjoining
       cd  1 = check data (roofs over CHECK_DATA_ROOF_SHARE)
-    Everything else the map shows is worked out in the page from A and r,
-    using the numbers in the page's own CONFIGURATION block.
+    Everything else the map shows is worked out in the page from A, r and
+    rw, using the numbers in the page's own CONFIGURATION block.
     """
     import json
     WEB_DIR.mkdir(parents=True, exist_ok=True)
@@ -540,6 +589,7 @@
         props = {"k": r["site_key"], "ad": r["address"] or "",
                  "A": round(float(r["lot_area_m2"]), 2),
                  "r": round(float(r["roof_area_m2"]), 2),
+                 "rw": round(float(r["roof_wall_m2"]), 2),
                  "sc": code[r["scope"]]}
         if r["merged_site"]:
             props["m"] = 1
```

