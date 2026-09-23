# Regulation shortlist

**ARCH 540 Assignment 1 — W1 submission**
Kevin Jinn · 22 September 2026

One preferred source and two ranked alternatives, as required by the W1
submission. All three were read in the current document, not from a summary;
version statements and retrieval routes are in [`../sources/README.md`](../sources/README.md).

The ranking is by *fit to the assignment*, not by how interesting the subject is.
The brief asks for one small provision, one primary operation, a spatial output in
Rhino, and evidence that a claim can be checked against a passage. Each entry
below is argued on those terms.

---

## Preferred — R1-1 s. 3.2.2.8, maximum area of impermeable materials

**Document.** Zoning and Development By-law No. 3575, R1-1 District Schedule,
June 2026 consolidation. Read with Section 2 (Definitions).
**Broad area.** Housing, overlapping Climate Resilience and Water.
**Authority.** By-law. Binding.

### The provision

Three lines of the schedule, plus two definitions:

| Reference | Text |
|---|---|
| s. 3.2.2.7 | Maximum site coverage for all buildings — 50% of the site area |
| s. 3.2.2.8 | Maximum area of impermeable materials — 75% of the site area |
| s. 4.2.2 | The maximum area of impermeable materials includes site coverage for all buildings |
| Section 2, *impermeable materials* | The projected area of the outside of the outermost walls of all buildings, including carports, entries, porches and verandahs; asphalt; concrete; brick; stone; **permeable pavers**; and wood |
| Section 2, *permeable materials* | Gravel; river rock under 5 cm; wood chips; bark mulch; **wood decking with spaced boards**; and other materials the Director of Planning considers fully permeable when placed on grade with no underlying impermeable layer |

### Why this one

The interesting content is in the definitions, not the number. Two things a
designer would reasonably assume are false:

- A **permeable paver driveway is impermeable** under this by-law. Specifying one
  to improve a site's drainage does not move the 75% figure at all.
- **Wood is impermeable, but spaced-board decking is permeable.** The same
  material passes or fails on how the boards are laid.

That is a genuine, checkable piece of design knowledge that changes what someone
draws, and it is exactly the kind of thing a written rule communicates badly. It
is what the tool should teach.

### Input → operation → output

- **Input** — site area; a list of surfaces with area and material.
- **Operation** — classify each surface against the Section 2 lists; sum building
  footprint and sum all impermeable area; test against 50% and 75%.
- **Output** — two percentages, a pass or fail against each limit, the surplus or
  remaining allowance in m², and a clause reference for every classification.

### Spatial output in Rhino

The site boundary as a closed curve; building footprint extruded to a solid;
hardscape as flat surfaces coloured by classification; the permeable remainder as
the leftover region. The allowance is drawn as a dimension line against the
measured figure, so the gap is read as a length rather than a number.

The honest weakness of this choice, stated up front: the operation is area
arithmetic, so the Rhino output risks being a coloured plan with nothing to gain
from being 3D. The intended answer is to extrude the design-storm volume the
impermeable area sheds into a solid sitting on the lot, so that a change in
paving is seen as a change in volume. That is the part of the build that needs
proving, and it is where W3 effort should go.

### What is left outside

Parking-area limit s. 3.2.2.13; laneway houses, which s. 2.2.4 sends to Section 11
of the by-law; the Director's discretion to increase the maximum for non-dwelling
uses under s. 3.2.2.14; relaxations and hardship.

### What remains open to interpretation

- **Multiplex.** s. 3.1 governs multiple dwellings of 3–8 units and does **not**
  restate an impermeable-materials maximum. Whether the s. 3.2 limits reach a
  multiplex at all is unresolved and needs confirmation with the City. The tool
  must report "not assessed" rather than guess.
- **Laneway house footprint.** s. 2.2.4 removes laneway houses from sections 3 and
  4 of this schedule, so whether their footprint counts toward the site's 75% is
  arguable.
- **Where the footprint is measured.** Section 2 says the outside of the outermost
  walls including porches and verandahs. An architect's area schedule often
  reports the gross floor footprint instead. The two disagree, and the difference
  is large enough to change a verdict.

### State of the work

Furthest along of the three, which is the main reason it ranks first with two
weeks of the assignment gone. Two prototypes exist (`week-01/`), a handover
document records the regulatory basis and the known limitations, and a citywide
run over all 63,946 R1-1 parcels exists in `stormwater.py`. A real surveyed site
plan is available to test against. Source depth and evidence of revision are both
assessed, and both already exist here.

The risk attached to being furthest along is scope. `stormwater.py` is a citywide
policy analysis, and the brief asks for something small enough to explain and
verify. The W2 work is to cut, not to add.

---

## Alternative 1 — Protection of Trees By-law No. 9958, Schedule A

**Document.** Protection of Trees By-law No. 9958, consolidated to 9 December 2025,
amended to include By-law No. 14546 effective 1 January 2026.
**Broad area.** Landscape and Ecology.
**Authority.** By-law. Binding.

### The provision

Schedule A, *Protection Barrier Distance from Tree*, referenced from the Section 1.2
definition of "protection barrier", which also requires the barrier to be at least
1.2 m high and the trunk diameter to be measured 1.4 m above existing grade at the
base of the tree.

| Trunk diameter (cm) | 20 | 25 | 30 | 35 | 40 | 45 | 50 | 55 | 60 | 75 | 90 | 100 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Distance from trunk (m)** | 1.2 | 1.5 | 1.8 | 2.1 | 2.4 | 2.7 | 3.0 | 3.3 | 3.6 | 4.5 | **5.0** | 6.0 |

### Why it ranks second

It is the strongest *spatial* candidate of the three. A barrier distance is a
radius, the barrier has a stated height, and the thing it conflicts with is an
excavation. That is a cylinder against a solid — natively three-dimensional, with
nothing forced about the Rhino output.

It also carries the clearest interpretation gaps of any source here, and they are
in the table itself rather than in the surrounding prose:

- **Every row is exactly 0.06 m of distance per 1 cm of diameter, except one.**
  At 90 cm the pattern gives 5.4 m; the schedule says 5.0 m. At 100 cm it returns
  to 6.0 m, which is 0.06 again. Either 90 cm is a deliberate exception or it is
  an error that has been consolidated forward. A tool has to decide which, and
  should say which it chose.
- **Intermediate diameters are undefined.** A 43 cm tree is not in the table. Round
  up to the next row, interpolate, or apply the ratio? The schedule is silent, and
  the three answers differ by up to 0.3 m on the ground.
- **Above 100 cm is undefined.** Vancouver has many such trees.

Compare Schedule B, which handles the same problem differently by using explicit
bands (20–30, 31–32, 33, 34–35 …) and an open top row of "60 and above". The
drafting is inconsistent between two schedules of the same by-law, which is a
useful thing for a student tool to be able to show.

### Input → operation → output

- **Input** — trunk diameter at 1.4 m; trunk position; proposed excavation or
  building footprint.
- **Operation** — look up the required distance; construct the protection radius;
  test the proposed work against it and report the encroachment.
- **Output** — required distance, whether the work encroaches, and by how much.
- **Rhino** — a 1.2 m cylinder at the required radius, the drip line as a separate
  circle, and the proposed excavation, with the overlap highlighted.

### Why not first

Source work would restart in week 3 of a four-week assignment. Schedules A to D
are scanned images in the consolidated PDF with no text layer, so the tables have
to be transcribed and checked by hand before anything can be built. The transcription
above is the first pass at that and is not yet verified against a second reading.

---

## Alternative 2 — Engineering Design Manual 2026, Table 9-2

**Document.** City of Vancouver Engineering Design Manual, 2026 edition,
s. 9.3.3.2 Spacing and Soil Volume Requirements, p. 367.
**Broad area.** Landscape and Ecology, overlapping Public Space and Streets.
**Authority.** **Engineering guidance, not a by-law.** This distinction has to be
carried into the tool's own language.

### The provision

| Tree size category | Average spacing | Soil volume, solitary tree | Soil volume, shared or row |
|---|---|---|---|
| Large | 9.0–11 m | 30 m³ | 20 m³ |
| Medium | 8.0–10 m | 20 m³ | 15 m³ |
| Small | 7.0–10 m | 10 m³ | 5.0 m³ |
| Columnar | 7.0–10 m | 20 m³ | 15 m³ |

With the qualification that structural soil counts at **50% of its volume**, so a
30 m³ requirement met with structural soil needs 60 m³ of trench.

### Why it ranks third

The content is good and the section drawing almost draws itself: a boulevard in
section, the soil volume as a box beneath the sidewalk, and the box doubling when
structural soil is selected. The shared-versus-solitary distinction is a real
design trade-off — planting closer reduces the per-tree requirement — which is the
kind of thing the brief says a qualitative operation should reveal.

Three reasons it is last:

- It is guidance rather than a by-law, and the brief explicitly cautions against
  presenting a recommendation as a legal requirement. Manageable, but it is an
  extra thing to get right in the tool's wording.
- "Tree size category" is not defined in the table. Large, medium, small and
  columnar have to be resolved against a species list elsewhere, which widens the
  source work rather than narrowing it.
- The spacing figures are ranges, not limits, so the compute step produces a band
  rather than a pass or fail. That is honest to the source but weaker as a
  demonstration of a rule becoming an operation.

---

## Summary

| | Source | Authority | Operation | Spatial fit | Work already done |
|---|---|---|---|---|---|
| **Preferred** | R1-1 s. 3.2.2.8 + Section 2 | By-law | Classify and sum areas against 50% / 75% | Moderate — needs the volume extrusion to earn 3D | Substantial |
| **Alt 1** | Trees By-law 9958, Schedule A | By-law | Table lookup → protection radius → encroachment test | Strong — cylinder against excavation | Transcription only |
| **Alt 2** | EDM 2026, Table 9-2 | Guidance | Category → soil volume, halved for structural soil | Strong — boulevard section | None |

**Proceeding with the preferred source.** The decision that still needs making in
W2 is how much of the existing citywide analysis to discard in order to get back
to one provision, one operation, and one example.
