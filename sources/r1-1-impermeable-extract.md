# Source extract — R1-1 s.3.2.2.8, impermeable materials

The curated source for the tool in `tool/`. Every claim the tool makes points
back to a row here, and every row here points to a page in a PDF that is in
this folder.

The brief asks for three things to stay apart, so this file keeps them apart:

1. **Source** — what the by-law says, quoted verbatim, with its page.
2. **Interpretation** — how the tool reads it, and who decided.
3. **Unresolved** — what the text does not settle.

Then two hand-worked examples, so the code can be checked without trusting it.

**Documents.** Zoning and Development By-law No. 3575, City of Vancouver.
Both consolidations print "June 2026" on every page.

| File in this folder | Pages | Downloaded |
|---|---|---|
| `zoning-by-law-district-schedule-r1-1.pdf` | 17 | 2026-09-21, in a browser from `bylaws.vancouver.ca/zoning/zoning-by-law-district-schedule-r1-1.pdf` |
| `zoning-by-law-section-2.pdf` | 50 | 2026-10-01, in a browser from `bylaws.vancouver.ca/zoning/zoning-by-law-section-2.pdf` |

*Revision note, 2026-10-02.* Until this date the Section 2 rows cited a
November 2025 copy and said the June 2026 PDF was not in the repository. It
is, and has been compared line by line: the four definitions quoted below are
word for word the same in both consolidations, but two page numbers differed
(Impermeable Materials is p.20, not p.21; Deck is p.11, not p.12). All page
numbers below are the printed page numbers of the June 2026 PDFs. The error
was found by all three outside reviews in `docs/reviews/`.

---

## 1. Source

### R1-1 District Schedule

| Ref | Page | Text (verbatim) |
|---|---|---|
| s.3.2 | p.12 | "All other uses not regulated by section 3.1 of this schedule are subject to the following regulations." |
| s.3.2.2.1 | p.12 | "Minimum site area for duplex, duplex with secondary suite, single detached house, and single detached house with secondary suite — 306 m²" |
| s.3.2.2.2 | p.12 | "Minimum site frontage for duplex, duplex with secondary suite, single detached house, and single detached house with secondary suite — 7.3 m" |
| s.3.2.2.7 | p.12 | "Maximum site coverage for all buildings — 50% of the site area" |
| s.3.2.2.8 | p.12 | "Maximum area of impermeable materials — 75% of the site area" |
| s.3.2.2.9 | p.13 | "The Director of Planning may reduce the minimum site area and minimum site frontage for a building containing a dwelling use if the Director of Planning is satisfied with the liveability of the dwelling units." |
| s.3.2.2.12 | p.13 | "For sites less than 7.3 m in width, the minimum side yard width will be reduced to permit the construction of a single detached house on an existing lot that was on record in the Land Title Office as of June 24, 2014, if the use was previously approved under issued development or building permits." |
| s.3.2.2.13 | p.13 | "Except where the principal use of the site is a parking area, the maximum site coverage for any portion of the site used as a parking area is 30%." |
| s.3.2.2.14 | p.13 | "The Director of Planning may increase the maximum area of impermeable materials for non-dwelling uses if: (a) there is a demonstrated need for increased paved or otherwise impermeable surface area to the satisfaction of the Director of Planning; and (b) the Director of Planning considers the intent of this schedule and all applicable Council policies and guidelines." |
| s.2.2.4 | p.5 | "Laneway house is regulated by Section 11 of this by-law and sections 3 and 4 of this schedule do not apply." |
| s.2.2.13(c) | p.6 | accessory buildings are permitted outright if, among other things, "the total floor area of all accessory buildings, measured to the extreme outer limits of the building, does not exceed 48 m²" |
| s.3.1 | pp.8–10 | Multiple dwelling of up to 8 units. The section contains no impermeability and no site-coverage regulation (checked: neither word appears in it). |
| s.4 | p.14 | "All uses in this district are subject to the following regulations." |
| s.4.2.2 | p.16 | "The maximum area of impermeable materials includes site coverage for all buildings." |
| s.4.3.1 | p.16 | "No portion of the basement or cellar may project horizontally beyond the perimeter of the first storey, including entries, porches and verandahs." |

### Section 2, Definitions

| Term | Page | Text (verbatim) |
|---|---|---|
| Impermeable Materials | p.20 | "The projected area of the outside of the outermost walls of all buildings, including carports, entries, porches and verandahs, asphalt, concrete, brick, stone, permeable pavers, and wood." |
| Permeable Materials | p.31 | "Materials including gravel, river rock less than 5 cm in size, wood chips, bark mulch, wood decking with spaced boards and other materials which, in the opinion of the Director of Planning, have fully permeable characteristics when placed or installed on grade with no associated layer of impermeable material, such as plastic sheeting, that would impede the movement of water directly to the soil below." |
| Accessory Building | pp.1–2 | "A building: (a) the use or intended use of which is ancillary to that of the principal building situated on the same site ... or (b) that is ancillary to the principal use being made of the site ..." |
| Deck | p.11 | "A platform providing useable outdoor space that: (a) projects from a building and is generally supported on posts; (b) is accessed from within the building, and may also be accessed from grade; (c) generally has a surface height, at any point, greater than 600 mm above grade; and (d) is not enclosed, except for a required guard." |
| Entry, Porch and Verandah | p.14 | "A platform located at an entrance to a building that: (a) projects from the building or is recessed into the building; (b) is covered by a roof or floor above to provide weather protection; (c) may be supported on posts; (d) is at grade or has stairs from grade; and (e) is open, other than with a required guard, on at least 1 side, except for covered porches above the first storey." |
| Grade | p.18 | "The elevation of the surface of the ground at any point on a site." |
| Laneway House | p.22 | "A detached dwelling unit constructed in the rear yard of a site on which is situated a Single Detached House, Single Detached House with Secondary Suite, or Child Day Care Facility, but does not include Infill Single Detached House." |
| Parking Area | p.30 | "An open area of land other than a street or lane, used or intended to be used to provide space for the parking or storage of motor vehicles, and includes parking spaces, loading spaces, manoeuvring aisles and other areas providing access to parking or loading spaces, but does not include an area providing 4 or fewer spaces accessory to a residential use ..." |
| Patio | p.30 | "A platform providing useable outdoor space that: (a) is not enclosed; and (b) generally has a surface height, at any point, no greater than 600 mm above finished grade." |
| Site | p.43 | "An area of land consisting of 1 or more adjoining parcels or lots abutting on a street not being a lane, but does not include a strata lot or a leasehold parcel created under section 99(1)(k) of the Land Title Act (British Columbia)." |

Section 2 does **not** define "site coverage", "lot", "swimming pool" (as a
structure), "eave" or "cantilever". Where the tool needs those words it says
so and marks the reading as its own.

---

## 2. Interpretation

Every item below is a decision, not a quotation. Each says who decided and
when. Items marked **(2026-10-02)** were added or changed in response to the
three outside reviews in `docs/reviews/`; they are the tool's current
behaviour and await the author's confirmation.

### What counts, and how much

**The limit includes the house.** s.4.2.2 says so directly. The building
counts in both the 50% test and the 75% test. *(Author, 2026-09-24.)*

**"All buildings" means all of them.** *(2026-10-02.)* Section 2's
Impermeable Materials definition starts with "all buildings, including
carports, entries, porches and verandahs". The tool therefore treats a porch,
entry, verandah, carport, garage, shed, accessory building and laneway house
as a **building**: counted in the 50% test and the 75% test, with no
suggestion that the Director might accept it as permeable. Before this date
only the word "building" was recognised and a porch fell through to "not
named in the by-law".

**A building's area is its projected area.** *(2026-10-02.)* The definition
says "the projected area of the outside of the outermost walls". The tool's
instruction is: every storey's exterior walls projected to the ground,
including cantilevers and bay windows, plus carports, entries, porches and
verandahs; eaves are not walls and are left out; a basement may not project
beyond the first storey (s.4.3.1). The tool counts whatever footprint it is
given; it cannot see a drawing.

**Every square metre is counted once.** *(2026-10-02.)* "Projected area" is
one plan projection, not a sum of layers. Where two surfaces overlap, the
overlap is counted once, with the stricter class (building before
impermeable before permeable before ground). A raised deck over a stone
patio is one impermeable footprint; a house drawn over a path is building.
Before this date the overlap was added twice and a warning printed.

**Only the part on the lot counts.** *(2026-10-02.)* s.3.2.2.8 is a share of
the *site* area, so the part of a driveway that lies in the lane, or a slab
that crosses a side lot line, is clipped off and reported. A band 2 cm wide
around the lot line still counts as on the lot, because the City's parcel
polygons wobble by that much (the demo lot's rear line wanders 3.6 cm).

**At the limit passes.** "Maximum" means exactly 75.00% is allowed; 75.01%
is not. The verdict is decided on unrounded areas; when a design is closer
to the limit than two decimals show, the report prints four. *(Author,
2026-09-24; precision added 2026-10-02.)*

### The material table

**Wood is decided by its conditions, not its name.** "Wood" is in the
Impermeable list; "wood decking with spaced boards" is in the Permeable
list. The specific wording is read as an exception to the general one. A
wood surface is **permeable only if all three hold**: the boards are spaced,
it is installed on grade, and there is no impermeable layer underneath (slab,
membrane, plastic sheeting). Otherwise it is impermeable. *(Author,
2026-09-24.)* **A condition the design does not state is not assumed
either way** *(2026-10-02)*: the surface is counted as wood and flagged
"spacing not stated", rather than reported as "boards not spaced", which
asserted a fact the user never gave.

**A raised deck is impermeable, and flagged.** A Deck in the Section 2 sense
is more than 600 mm above grade, so it is not "on grade" and cannot take the
exception. The tool counts it impermeable and prints *"Raised deck – confirm
treatment with the City."* A low platform (a Patio, 600 mm or less) still
takes the three-condition test. *(Author, 2026-09-24.)*

**The on-grade / no-layer condition is applied to every listed permeable
material, and this is the author's stricter reading.** The condition sits at
the end of the Permeable Materials sentence. Read by its grammar, "when
placed or installed on grade with no associated layer of impermeable
material" most naturally qualifies "have fully permeable characteristics" in
the Director's-opinion limb, so the named materials (gravel, river rock, wood
chips, bark mulch, spaced decking) would qualify unconditionally. The tool
applies the condition to the named materials as well — gravel over plastic
sheeting is impermeable, gravel in a raised planter is impermeable, a spaced
deck on a membrane is impermeable — because that is how a permit reviewer is
likely to read the intent, and because applying it to decking but not to
gravel would be inconsistent. **The tool now says so in every result that
relies on it, and states the alternative reading.** *(Author, 2026-09-24;
labelled and widened to "on grade" for all listed materials, 2026-10-02,
review A item 5 and review C F13.)*

**River rock needs a size.** The list says "less than 5 cm". With no size
given the tool counts it impermeable and asks; at 5 cm or more, impermeable.

**Anything not named in the Permeable list counts as impermeable.** The
by-law treats an unlisted material as permeable only if the Director of
Planning is of that opinion, so the tool cannot assume it. There is **no
third "discretion" category**; the pass/fail verdict is the same either way.
*(Author, 2026-09-24.)*

- *Pervious concrete / porous asphalt* → impermeable. "Concrete" and
  "asphalt" are listed without qualification, and permeable pavers are named
  as impermeable, so a permeable version of a listed material gets no
  exception. The result says this is the author's decision and that the
  Director could be asked.
- *Synthetic turf, rubber safety surfacing, decomposed granite, grass
  pavers, resin-bound aggregate* → impermeable, with the note *"Not named in
  the by-law. Counted as impermeable; the Director of Planning may accept it
  as permeable."*
- *Swimming pool, hot tub, pond* *(2026-10-02)* → impermeable, **without**
  the Director note: a lined shell passes no water to the soil, so it is not
  a candidate for the permeability opinion. Confirm with the City how the
  pool deck is measured.
- *Any other word* *(2026-10-02)* → impermeable, flagged **"Unrecognised
  material"**, with the closest known name offered ("permable pavers" → "Did
  you mean permeable pavers?"). Before this date a typo was explained with
  the Director note, which inverted the lesson the tool exists to teach.

**Other spellings are mapped, not guessed.** *(2026-10-02.)* An alias table
turns "artificial turf" into synthetic turf, "detached garage" into garage,
"paving stones" into stone, "concrete pavers" into concrete, "mulch" into
bark mulch, and so on. Every paver is impermeable under Section 2: concrete
and stone pavers are concrete and stone, and permeable pavers are named
outright.

**Lawn, planting and natural ground are not counted.** Neither list names
them. They are not installed materials in the sense of either definition,
and nothing in the Impermeable list covers them. Site area not covered by
any surface is treated the same way, and the report says so in those words
("no surface drawn — not counted"), with a note when more than half the lot
is undrawn, because a driveway left off the plan would otherwise pass
unnoticed. A strict reading of "anything not named in the Permeable list is
impermeable" would make lawn impermeable and fail every lot; that is not
taken to be the intent. *(Author, 2026-09-24; wording 2026-10-02.)*

**Why permeable pavers are on the impermeable list.** *(2026-10-02, verified
against the amending by-law.)* The word is not a drafting slip. The original
impermeability regulations of 2000 (Policy Report RTS 00291, 20 March 2000,
referring RS-schedule amendments to public hearing) defined permeable
materials as gravel, river rock, wood chips, bark mulch "and other materials
which, in the opinion of the Director of Planning, have fully permeable
characteristics when in place installed on grade with no associated layer of
impermeable material (such as plastic sheeting)"; pavers were not named either
way. By-law No. 13670, enacted 26 April 2023, "in the definition of
Impermeable Materials, adds 'permeable pavers,' after 'stone,'" (s.2(a),
`sources/zoning-by-law-13670-2023-amendments.pdf`). The City's reason is
stated in its own guidelines (RM-7A Guidelines, April 2025, p.16–17, repeated
three times): "Open parking spaces should be paved with pavers that are
permeable to reduce stormwater sewer loads. However, since most permeable
pavers lose their permeability over time, parking areas with permeable pavers
are counted as impermeable surface." So the by-law counts the material by
what it does after years of silt, not by what it does on the day it is laid.
The only route out is the Director's opinion under "Permeable Materials",
which the tool cannot predict.

### Which sites and uses

**Every use outside s.3.1 is assessed.** *(2026-10-02.)* s.3.2 opens "All
other uses not regulated by section 3.1", so s.3.2.2.8 reaches infill,
multiple conversion dwellings, child day care conversions and the rest, not
only the four dwelling uses named in s.3.2.2.1. For a non-dwelling use the
result notes s.3.2.2.14, the only relaxation of this limit, which is for
non-dwelling uses only: **for a house, PASS/FAIL is binary.** Before this date
the tool declined every use but four.

**A multiplex is not assessed.** s.3.1 sets no numeric impermeability or
site-coverage limit (checked: the words do not appear in pp.8–10). The tool
says so and stops. s.4 still applies to all uses, and other instruments or
conditions of approval may address permeability, so the message says "no
numeric limit in this schedule", not "no limit".

**A laneway house is a building on the site, counted and flagged.**
*(2026-10-02.)* s.2.2.4 sends the laneway house itself to Section 11 and
switches off sections 3 and 4 of the schedule *for it*; the site still
carries a single detached house and still faces s.3.2.2.8, and Section 2's
"all buildings" reaches every building on the site. Section 11 is not in this
repository, so whether it says anything different about the laneway footprint
is unresolved. The tool counts it and flags it.

**A lot below the s.3.2.2.1 area or s.3.2.2.2 frontage floor is flagged, and
still assessed.** s.3.2.2.9 lets the Director reduce both; s.3.2.2.12
provides for a single detached house on a lot under 7.3 m wide that was on
record as of June 24, 2014. *Correction, 2026-09-24:* the tool first cited
s.3.2.2.12 alone, and for site area as well; s.3.2.2.12 is a side-yard
clause about width.

**A site may be more than one parcel.** *(2026-10-02.)* Section 2 defines a
Site as "1 or more adjoining parcels". The tool accepts a list of parcel
outlines and treats their total as the site area. It does not check that the
site abuts a street that is not a lane, or that no parcel is a strata lot.

**s.3.2.2.13 applies only to a Parking Area in the Section 2 sense.**
*(2026-10-02.)* Section 2 excludes "an area providing 4 or fewer spaces
accessory to a residential use", so a house's driveway is not a parking area
and the 30% limit does not apply to it. The tool runs the 30% test only when
told the site has more than 4 spaces, and otherwise says why it did not.

**Feet are accepted and a feet-sized lot is questioned.** *(2026-10-02.)* A
design may say `"units": "ft"`. Without it, a lot over 1,500 m² or 30 m wide
is flagged "are these dimensions in feet?", because a 33 × 122 ft lot typed
as metres is 4,026 m² and passes everything.

---

### Measuring buildings from the City's footprints (the map)

**Roof edge is not the wall.** *(2026-10-02, awaits the author's confirmation.)*
The City's 2015 building footprints are "the generalized outermost exterior
outline of main building components generated from … 2015 orthophotos": they
follow the roof edge. Section 2 measures a building as "the projected area of
the outside of the outermost walls". Eaves are not walls. The map therefore
measures every roof twice: as traced, and with an eave allowance of 0.45 m
taken off all round before the footprint is clipped to the site (a Vancouver
house roof overhangs by about 0.3–0.6 m; 0.45 m is the middle). The by-law
tests use the walls figure; both are shown. The allowance changes the citywide
picture entirely: 13,594 ordinary sites read over 50% to the roof edge, 2,482
at 0.3 m, 777 at 0.45 m, 242 at 0.6 m. Section 10 of the by-law governs
projections and has not been read; the air photo cannot tell which figure is
right for any one house, so a site over 50% to the walls is marked "check",
never "exceedance".

**Which parcels are assessed.** *(2026-10-02, awaits the author's confirmation.)*
A site is parcels sharing a civic address and an edge (Section 2, "Site").
Sites over 2,000 m² and road allowances were already outside scope (the
author's 2026-09-25 decision). The map also leaves unassessed, drawn grey:
parcels the pipeline flagged (roof over 90% of the parcel; shared address but
not adjoining) and parcels under 150 m², which are strata remnants or data
faults rather than sites. Parcels under the 306 m² minimum site area of
s.3.2.2.1 are assessed, and the card says they are below it: an existing
small lot, or part of a larger site.

## 3. Unresolved

- **The on-grade / no-layer condition.** Which limb of the Permeable
  Materials sentence it governs. The tool takes the stricter reading and
  says so; the City may take the other.
- **Raised decks.** Whether the City measures a raised deck's projected area
  or the ground surface beneath it. The "projected area" wording supports
  counting the deck; flagged, not settled.
- **Laneway house footprint.** Whether Section 11 (not in this repository)
  changes how a laneway house counts toward the site's 75%. Counted and
  flagged.
- **Unlisted materials, including pervious concrete.** Only the Director of
  Planning can accept one as permeable. The tool cannot know that opinion in
  advance.
- **Pools and hot tubs.** Not named anywhere as a material. Counted as
  impermeable on the physical argument, not on a quotation.
- **Site area.** The tool uses the City's parcel polygon. A permit uses the
  legal survey, which may differ slightly.
- **Building footprint.** The tool counts whatever footprint it is given.
  An architect's gross floor footprint, a roof-edge footprint and the Section
  2 "projected area of the outside of the outermost walls" are three
  different numbers; the result says which one it wants.
- **Not checked at all:** yards, height, FSR, Section 11, and anything the
  Director of Planning may relax.

---

- **The eave allowance.** 0.45 m is a typical overhang, not a measurement
  of any one house. For a permit the building is measured from the survey or
  the building permit drawings; the map's figure is an estimate either way.
- **Section 10 (projections) and Section 11 (laneway houses)** are not in the
  repository; both bear on what the footprint of a building includes.

## 4. Hand-worked example A — 3528 W 30th Ave, as designed

Checkable with a calculator and this page, without trusting the code.

Site area: **602.04 m²** (City parcel polygon, site_id 006141498).
Limit: 0.75 × 602.04 = **451.53 m²** (s.3.2.2.8).

| Surface | Dimensions | Area m² | Counts? | Because |
|---|---|---:|---|---|
| House | 12.80 × 23.00 | 294.40 | yes | s.4.2.2; Impermeable Materials, "all buildings" |
| Parking pad, permeable pavers | 12.00 × 7.70 | 92.40 | **yes** | Impermeable Materials names "permeable pavers" |
| Rear patio, stone | 10.00 × 4.00 | 40.00 | yes | Impermeable Materials, "stone" |
| Side walk, concrete | 0.90 × 23.00 | 20.70 | yes | Impermeable Materials, "concrete" |
| Front walk, concrete | 1.50 × 4.912 | 7.37 | yes | Impermeable Materials, "concrete" |
| Rear deck, spaced boards on grade, no layer | 2.80 × 4.00 | 11.20 | no | Permeable Materials, "wood decking with spaced boards" (author's reading of the conditions) |
| Rest of lot, lawn and planting | — | 135.97 | no | named in neither list; not an installed material |
| **Impermeable total** | | **454.87** | | |

454.87 − 451.53 = **3.34 m² over. FAIL.**

Without the pavers counted, the total would be 454.87 − 92.40 = 362.47 m²,
or **60.21%**. That is the number a designer expects, and it is wrong.

**Revised:** turn the first 1.00 m of the pad, at the lane, into gravel
(12.00 × 1.00 = 12.00 m², listed permeable). Impermeable total
454.87 − 12.00 = 442.87 m² = **73.56%. PASS**, 8.66 m² to spare.

The house is drawn as a single-storey 294 m² footprint (48.9% of the lot),
which is lawful but unusual; it was chosen to put the design near the 75%
line. The lot is real; the design is illustrative.

## 5. Hand-worked example B — a 33 ft lot with a laneway house

`examples/33ft-lot-laneway-house.json`. An illustrative 10.06 × 37.19 m lot
(33 × 122 ft), **374.13 m²**; limit 0.75 × 374.13 = **280.60 m²**. This
example exercises the 2026-10-02 rules: building vocabulary, clipping at the
lane, overlaps, an area from a schedule, an alias, and the parking note.

| Surface | Drawn m² | Adjustment | Counted m² | Class | Because |
|---|---:|---|---:|---|---|
| House | 8.00 × 12.50 = 100.00 | — | 100.00 | building | "all buildings" |
| Front porch | 3.00 × 1.50 = 4.50 | — | 4.50 | building | "including ... porches" |
| Laneway house | 6.00 × 7.00 = 42.00 | — | 42.00 | building, flagged | a building on the site; Section 11 unresolved |
| Parking pad + lane apron, permeable pavers | 3.16 × 9.40 = 29.70 | 3.16 × 1.50 = 4.74 lies in the lane, not counted | 24.96 | impermeable | "permeable pavers"; share of the *site* |
| Courtyard, permeable pavers | 7.66 × 6.60 = 50.56 | — | 50.56 | impermeable | "permeable pavers" |
| Raised deck, 900 mm, over the courtyard | 3.00 × 3.00 = 9.00 | wholly over the courtyard pavers: counted there | 0.00 | impermeable, flagged | a Deck is not on grade; one projected area |
| Front walk, concrete | 1.20 × 10.19 = 12.23 | 1.20 × 1.50 = 1.80 under the porch, counted as building | 10.43 | impermeable | "concrete" |
| Side walk, concrete | 0.86 × 12.50 = 10.75 | — | 10.75 | impermeable | "concrete" |
| Hot tub, from the area schedule | 4.50 | no geometry: counted as given | 4.50 | impermeable, flagged | not a listed material; passes no water to soil |
| Play area, "artificial turf" | 3.00 × 4.00 = 12.00 | alias of synthetic turf | 12.00 | impermeable | not named; the Director may accept it |
| Rest of lot | — | | 114.43 | not counted | nothing drawn |
| **Buildings** | | | **146.50** | | 39.16% of the site, limit 50%: PASS |
| **Impermeable total** | | | **259.70** | | **69.41%**, limit 75%: PASS, 20.90 m² to spare |

Pavers: 24.96 + 50.56 = 75.52 m². If they counted as permeable the total
would be 184.18 m² = 49.23%.

The one parking space is "4 or fewer spaces accessory to a residential use",
so the parking surfaces are not a Parking Area and s.3.2.2.13 does not apply.

Tool output for all three: `python3 tool/impermeable_check.py examples/*.json`.
