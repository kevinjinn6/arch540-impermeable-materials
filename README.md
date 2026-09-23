# Impermeable materials in Vancouver R1-1

**ARCH 540 — Assignment 1, Making Design Knowledge Interactive**
Kevin Jinn · Instructor: Xun Liu · Phase 1, Weeks 1–4

An interactive tool that explains one provision of Vancouver's R1-1 District
Schedule — the 75% cap on impermeable materials — and lets someone test a real
lot against it.

The provision is three lines long. The part worth building a tool around is not
the number but the definition behind it: under Section 2 of the Zoning and
Development By-law, **permeable pavers count as impermeable**, and **wood decking
counts as permeable only if the boards are spaced**. A designer specifying a
paver driveway to improve drainage gains nothing against this limit. That gap
between what the words suggest and what the by-law means is what the tool is for.

---

## Current state

**Week 2 of 4.** Source selected and read; two prototypes built; no Rhino
connection yet. Nothing here is a finished submission.

| Deliverable | Where | State |
|---|---|---|
| W1 — README and first-week materials | this file, `week-01/` | Complete |
| W1 — preferred regulation and two ranked alternatives | [`docs/regulation-shortlist.md`](docs/regulation-shortlist.md) | Complete |
| W1 — comparison of prompt approaches | [`docs/prompt-comparison.md`](docs/prompt-comparison.md) | Two of three approaches; the shortfall is stated in the document |
| W2 — source interpretation | — | Not started |
| W3 — working tool with Rhino output | `stormwater.py` is a partial, oversized precursor | Needs cutting down |
| W4 — reusable skill, testing, peer review | — | Not started |

---

## Repository map

```
README.md                     you are here
docs/
  regulation-shortlist.md     preferred source + two ranked alternatives, argued
  prompt-comparison.md        W1 exercise: what changed between two prompt approaches
week-01/
  prompt-a-low-context/       the tool a low-context prompt produced
  prompt-b-high-context/      the tool a high-context prompt produced, plus HANDOFF.md
sources/
  README.md                   source register: version, authority, retrieval date
  *.pdf                       the by-laws themselves
stormwater.py                 citywide R1-1 analysis. Precursor, not the assignment tool.
assignment 1.qgz              QGIS project for viewing the output
```

Start with [`docs/regulation-shortlist.md`](docs/regulation-shortlist.md) for the
choice of source, and [`docs/prompt-comparison.md`](docs/prompt-comparison.md) for
the W1 exercise.

---

## The two prototypes

Both are self-contained React single-file components written as Claude artifacts.
They have no build step and no dependencies beyond React, and they are included as
**evidence for the W1 prompt comparison**, not as the assignment tool.

- `week-01/prompt-a-low-context/lot-coverage-checker.jsx` — applies a 60% limit and
  names no source. The 60% is the superseded By-law 8202 (2000) figure.
- `week-01/prompt-b-high-context/r1-1-coverage-checker.jsx` — applies the current
  75% and 50% limits with a clause reference attached to every rule.

`prompt-b-high-context/HANDOFF.md` records the regulatory basis, the file's
architecture, and its known limitations, including two questions still open with
the City.

The same 500 m² lot passes under A and fails under B. The worked numbers are in
[`docs/prompt-comparison.md`](docs/prompt-comparison.md).

---

## Running `stormwater.py`

A citywide gap analysis across all 63,946 R1-1 parcels. It is **too large to be
the assignment tool** and is kept as a precursor; the W2 task is to cut it back to
one provision, one operation and one example.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install geopandas pandas requests shapely pyproj
python stormwater.py
```

The first run downloads about 54 MB from the City of Vancouver open data portal
and takes a couple of minutes. No API key is needed. Later runs read from `cache/`
and take under a minute. Output is `r11_stormwater.geojson` plus a summary CSV,
neither of which is committed — the GeoJSON is 109 MB, above GitHub's file limit,
and both are reproducible by re-running the script.

Everything intended to be adjusted sits in the `CONFIGURATION` block at the top of
the file, above the line marked `END OF CONFIGURATION`, with a plain-language
comment on every constant.

**Read the caveats in the file header before quoting any number it produces.** The
most important one: the 48 mm Rain City Strategy standard it measures against is
**not a legal requirement** for R1-1. Everything in R1-1 falls within 1.0 FSR and
takes the City's small-site detention-tank pathway instead. The script measures a
distance from an aspiration, not a breach of a rule.

---

## Sources

Every document, with the version printed on it and the date it was retrieved, is
listed in [`sources/README.md`](sources/README.md).

Two things that register is careful about, because the brief asks for them:

- **Authority is not flattened.** A by-law, an engineering manual and a strategy
  are recorded as three different kinds of thing.
- **Retrieval route is recorded.** `bylaws.vancouver.ca` returns HTTP 403 to
  command-line tools. Two documents were retrieved through the Internet Archive's
  copy of the City URL, which is noted and needs re-checking against the live page
  before those sources are relied on.

---

## Not in this repository

- `.venv/` and `cache/` — recreated by the commands above.
- The GeoJSON and summary CSV outputs — regenerated by `stormwater.py`.
- The surveyed site plan used for real-world testing. It is a client drawing and
  is held back pending permission to include it. A synthetic example will be added
  for W3 so the tool can be run by someone else regardless.
