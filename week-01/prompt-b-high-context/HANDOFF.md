# Handoff: Vancouver R1-1 Site Coverage and Impermeability Checker

Date: 2026-09-15
Context: built in claude.ai chat with a landscape designer preparing residential permit applications in Vancouver. Moving to Claude Code for further development.

## What this is

A single-file React tool that:

1. Accepts a scaled site plan (PDF or image).
2. Sends it to Claude (Sonnet 4.6) via the Anthropic Messages API with a prompt that (a) copies any area schedule on the sheet verbatim and (b) independently computes each surface's area from dimension strings / scale bar.
3. Classifies every surface as **building / impermeable / permeable / uncertain** using the Section 2 definitions of the Vancouver Zoning and Development By-law.
4. Tests against the R1-1 District Schedule: **buildings ≤ 50% of site** (s. 3.2.2.7) and **impermeable materials incl. buildings ≤ 75% of site** (s. 3.2.2.8, s. 4.2.2).
5. Shows a summary table with clause citations, an editable surfaces table with schedule-vs-computed comparison, and a pass/fail verdict.

## Files

| File | Status | Notes |
|---|---|---|
| `r1-1-coverage-checker.jsx` | **Current.** Use this. | R1-1 rules, source tracking, recompute-and-compare mode. |
| `impermeable-coverage-checker.jsx` | Superseded, keep for reference | First version built against By-law 8202 (2000). 60% limit, old RS district clause numbering, pre-2000 relaxation, driveway exclusion. The RS schedules no longer exist. |
| `8202_by_law.pdf` | Source, historical | User-supplied. By-law No. 8202, passed 30 May 2000, amending By-law 3575. Now obsolete for permits. |

Both `.jsx` files are self-contained claude.ai artifacts: default export, `useState/useMemo/useRef` only, inline styles plus a `<style>` block, no external deps, no localStorage.

## Regulatory basis (verified 2026-09-15 against bylaws.vancouver.ca)

The RS-1 through RS-7 schedules were replaced by **R1-1 (Residential Inclusive)** on 17 Oct 2023. Current documents:

- R1-1 District Schedule, June 2026 consolidation: https://bylaws.vancouver.ca/zoning/zoning-by-law-district-schedule-r1-1.pdf
- Section 2 Definitions, June 2026: https://bylaws.vancouver.ca/zoning/zoning-by-law-section-2.pdf
- Consolidated by-law: https://bylaws.vancouver.ca/Zoning/zoning-by-law-consolidated.pdf

Rules encoded in `RULES` object in the current file:

| Key | Reference | Rule |
|---|---|---|
| `siteCoverage` | R1-1 s. 3.2.2.7 | Max site coverage for all buildings: 50% |
| `impermeable` | R1-1 s. 3.2.2.8 | Max impermeable materials: 75% |
| `includesBuildings` | R1-1 s. 4.2.2 | Impermeable max includes building coverage |
| `impermDef` | Section 2 | Impermeable: outermost-wall footprint of all buildings incl. carports, entries, porches, verandahs; asphalt; concrete; brick; stone; **permeable pavers**; wood |
| `permDef` | Section 2 | Permeable: gravel; river rock < 5 cm; wood chips; bark mulch; **spaced-board wood decking**; other fully permeable materials on grade with no impermeable layer (e.g. plastic sheeting) |
| `nonDwelling` | R1-1 s. 3.2.2.14 | Director may increase impermeable max for **non-dwelling uses** only |
| `hardship` | Section 2 | "Unnecessary hardship" is a defined term; excludes inconvenience, preference, self-induced hardship |
| `laneway` | R1-1 s. 2.2.4 | Laneway house regulated by Section 11; ss. 3 and 4 of R1-1 don't apply to it |
| `multiplex` | R1-1 s. 3.1 | Multiple dwelling (3–8 units) regulated by s. 3.1; **no impermeable max found restated there** |

Differences from the 2000 by-law the user started with, worth remembering when they compare:
- 60% → 75% impermeable limit.
- Permeable pavers were not named before; now explicitly impermeable.
- Spaced-board decking now explicitly permeable (previously all wood was impermeable).
- Pre-30-May-2000 relaxation to 70%: gone.
- Driveway/parking exclusion where no secondary vehicular access (L × 3.1 m + 67 m²/extra space): gone.
- Separate 50% building coverage test is now checked alongside.

## Architecture of the current file

```
R11CoverageChecker
├── state: use, method ("recompute"|"trust"), rows[], siteArea, siteInfo, scaleHint,
│          fileName, analyzing, error, warnings, hasSchedule, showClauses
├── analyzeDrawing(file)   → base64 → POST api.anthropic.com/v1/messages → parse JSON → rows
├── effectiveArea(row, method)   picks manualArea ?? (trust ? schedule ?? computed : computed ?? schedule)
├── rowDiscrepancy(row)          (computed − schedule) / schedule, null if either missing
├── calc (useMemo)               sums by category, pcts, pass/fail, other-method comparison,
│                                flagged rows (>5%), estimated-area-decides-result check
└── UI: aside (inputs) | main (verdict + bars, discrepancy panel, summary table,
                                surfaces table, by-law text accordion)
```

Row shape:
```js
{ id, label, material, category, basis,
  scheduleArea: number|null,   // copied from table on sheet
  computedArea: number|null,   // reader's own calculation
  dims: string,                // dimensions used, e.g. "6.10 x 12.19"
  source: "both"|"schedule"|"dimensions"|"estimated"|"manual",
  manualArea: string }         // non-empty = user override, wins over both
```

API call conventions (from the claude.ai artifact environment):
- `model: "claude-sonnet-4-6"`, `max_tokens: 1000`, no API key in the request (injected by the platform). **In Claude Code / outside artifacts you'll need to add auth and can raise `max_tokens`.**
- PDF sent as `{type:"document", source:{type:"base64", media_type:"application/pdf"}}`; images as `{type:"image", ...}`.
- Response JSON uses short keys to fit the 1000-token budget: `has_schedule, site_sch, site_cmp, scale_note, s:[{l,m,sch,cmp,dim,cat,src,why}], warn[]`. Max 12 surfaces.

## Known limitations and honest caveats

- **The reader does not measure pixels.** It reads dimension strings and multiplies. Unlabelled surfaces are estimated by proportion and can be off 10–20%+ on irregular shapes. All values are editable for this reason.
- **max_tokens 1000** constrains the JSON; complex plans may get truncated → parse error → user told to enter manually. Raising the budget is the first thing to do outside the artifact sandbox.
- **Single-page assumption.** Multi-sheet PDFs are sent whole; the prompt doesn't tell the model which sheet to read.
- **Unit conversion** (ft² → m²) is left to the model via one prompt line. Not validated.
- **Uncertain surfaces are counted as impermeable** (conservative). The verdict reports what happens if they're confirmed permeable.
- **Unassigned site area** (site area − sum of surfaces) is treated as permeable and reported. Could be wrong if the reader missed hardscape.
- **Laneway house footprint** is counted as building. s. 2.2.4 makes laneway houses subject to Section 11, so whether their footprint counts toward the R1-1 limits is arguable. Flagged in UI; not confirmed with the City.
- **Multiplex (s. 3.1)** shows percentages but "Not assessed"; no impermeable limit was found in s. 3.1 text. Needs confirmation.
- **Parking area limit** (s. 3.2.2.13, 30%) not implemented; the Section 2 definition of "parking area" excludes ≤ 4 spaces accessory to residential, so it rarely applies to houses.
- Pass condition uses `<=` (by-law says "shall not exceed" / "maximum"), so exactly 50.0% / 75.0% passes.

## User-reported issue that drove the last change

User ran an earlier version on a real drawing that had an area table on it and got numbers "slightly different" from their own (result still passed). Root cause: the old prompt didn't distinguish reading the table from computing, so rows were a silent mix of both. Fixed by splitting into schedule vs computed columns, a Δ column, a discrepancy panel (>5%), and a "would have given" line under each headline %. User has not yet re-run with the new version.

A likely source of real (not reader) discrepancy to check with the user: whether their schedule measures building footprint to the **outside face of the outermost walls including porches/entries** as Section 2 requires, versus the architect's gross floor footprint.

## Suggested next steps

1. Port to a standalone Vite/Next app with server-side API key; raise `max_tokens` to 4000+; add streaming or at least a progress state.
2. Add a real measurement path: let the user set scale by clicking two points on the image and trace polygons (canvas), computing area geometrically. Use the LLM only for classification and OCR of the schedule. This removes the biggest accuracy problem.
3. Multi-page PDF: render pages (pdf.js), let user pick the site plan sheet.
4. Persist projects (rows, overrides, site area) per drawing.
5. Export: PDF/print summary with clause citations for inclusion in a permit package.
6. Confirm with the City of Vancouver Development and Building Services Centre: multiplex impermeable limit under s. 3.1; laneway footprint treatment.
7. Unit tests for `effectiveArea`, `rowDiscrepancy`, and the `calc` block (pass/fail edges at exactly 50/75, uncertain handling, manual override precedence).
8. Consider adding the s. 3.2.2.13 parking-area test behind a toggle for sites with > 4 spaces.

## Design notes (if you keep the UI)

Palette: drafting-sheet greys and survey-ink navy; permeable = moss green, impermeable = graphite, uncertain = amber hatch, pass/fail = green/red, limit lines = burnt orange. Coverage bars are drawn like dimension strings with the limit as a vertical tick. Tabular numerals via `font-variant-numeric`. Discrepancy rows shaded `#FFF1E6`. Layout is a 360px input column + fluid results column, collapsing to one column under 880px.
