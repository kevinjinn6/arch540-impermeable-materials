---
name: r1-1-impermeable-materials
description: Read any Vancouver R1-1 lot against s.3.2.2.7 (50% buildings) and s.3.2.2.8 (75% impermeable materials, buildings included) of the Zoning and Development By-law, using the R1-1 map, its data, the Rhino drawing and Section 2's own definitions. Use when a design for a single detached house or duplex lot in R1-1 needs its hard landscaping budget, or when someone asks whether permeable pavers, a deck, gravel or a laneway house "count".
---

# R1-1 impermeable materials: reading a lot

A reusable procedure for one provision of the R1-1 District Schedule,
"Maximum area of impermeable materials — 75% of the site area" (s.3.2.2.8,
p.12), read with s.3.2.2.7 (buildings, 50%), s.4.2.2 (the 75% includes the
buildings, p.16) and Section 2's definitions of Impermeable Materials (p.20)
and Permeable Materials (p.31). The tools are the map in `map/index.html`
(live at kevinjinn6.github.io/arch540-impermeable-materials/), the Rhino
script `map/rhino_site.py`, and, for a full surface-by-surface check with a
drawn plan, the companion checker `tool/impermeable_check.py`.

## When to use this

- An R1-1 lot with a single detached house or duplex (any use under s.3.2),
  and a landscape plan with hard surfaces on it, or the question "how much
  paving can this lot still take?"
- A question of the form "does X count as impermeable?" where X is a material
  or a structure: pavers, decking, gravel, a pool, a porch, a laneway house.

Do **not** use it for a multiplex (s.3.1 sets no numeric limit), for yards,
height or FSR, or as a substitute for the City's own review from a survey.

## Steps

1. **Find the lot on the map.** Type the civic address the City's way
   (`3528 W 30TH AV`) or click it. Read the card:
   - *Site area* is the City parcel polygon; adjoining parcels with one
     address are merged into one site (Section 2, Site). Not a legal survey.
   - *Roofs to the roof edge* is the 2015 air-photo footprint. *Roofs to the
     walls* takes a 0.45 m eave off, because the by-law measures "the outside
     of the outermost walls". Use the walls figure for the by-law; say so.
   - *s.3.2.2.7*: within, within-by-the-walls (roof edge reads over), or
     over-even-to-the-walls (check against a survey).
   - *Room left* = 0.75 × site area − roofs to the walls. This is the budget
     for every driveway, walk, patio, deck and paver in the design.
2. **Write the schedule** in the card: each surface with a material named in
   the by-law's words and its area. The card classifies each one, sums the
   impermeable ones with the roofs, and tests against 75%. Expand *Why each
   surface counts or not* for the passage behind each row.
3. **Check it by hand** with the line the card prints: limit × site area,
   minus roofs to the walls, minus the counted surfaces.
4. **Draw it in Rhino** when a client needs to see it: set `ADDRESSES` in
   `map/rhino_site.py`, run it, open the `R1-1 map Plan - …` view. The area
   bar beside the site shows the roofs, the eave strip and the room left,
   marked at 50% and 75%.
5. **For a drawn design with overlapping surfaces, lot-line crossings or a
   laneway house**, use `tool/impermeable_check.py` with a JSON file of the
   surfaces (see `tool/` and `examples/`); it clips to the lot, counts every
   square metre once in the stricter class, and prints the same passages.

## What to say out loud with the result

- **Permeable pavers are impermeable** (Section 2, p.20, names them beside
  concrete and asphalt). Specifying them changes drainage, not this limit.
- **Wood decking escapes only with spaced boards, on grade, with no layer
  under it** (p.31). A raised deck (a *Deck* is over 600 mm, p.11) is wood,
  so impermeable. A spaced deck on a membrane is impermeable.
- **The on-grade, no-layer condition is read as applying to every listed
  permeable material** (gravel over plastic is impermeable). The plain grammar
  can be read the other way; this is the author's reading.
- **The roof figure is 2015 and traced from the air.** Anything built since
  is missing; the eave allowance is an estimate (0.3–0.6 m is usual). For a
  permit, measure the walls from the survey or the building permit drawings.
- **A laneway house is regulated by Section 11** (s.2.2.4), not in this
  repository. It is counted here as a building; a permit reviewer may treat
  it differently.
- For a dwelling there is no relaxation of the 75% (s.3.2.2.14 is for
  non-dwelling uses): the test is binary. At exactly 75% a lot passes.
- **The storm card is not the by-law.** 48 mm is the Rain City Strategy's
  design standard, a policy; R1-1 has no retention requirement.

## Changing the numbers

Every constant the page prints is in the `CONFIGURATION` block at the top of
the script in `map/index.html` (limits, eave allowance, materials and the
passage each rests on, storm assumptions, colours, where the map opens).
`map/rhino_site.py` and `map/roof_walls.py` carry the same `EAVE_M`. After a
change to the data:

```bash
python map/roof_walls.py        # roofs to the walls, from the published footprints
python3 map/check_data.py       # the published figures still hold
```

Record any new reading, with the date and the by-law words it rests on, in
`sources/r1-1-impermeable-extract.md` §2.

## Installing as a Claude Code skill

Copy this folder to `.claude/skills/r1-1-impermeable-materials/` in the
project, or to `~/.claude/skills/` for every project.
