# Impermeable materials map: a UI redesign proposal

Written 2026-10-02 by a UX review pass (Apple HIG lens) requested by Kevin. Before/after mockups of every state in this document are on the design canvas at <https://claude.ai/artifact/2YCj6gUnqPzARLqZgphgF7> (private until shared). **Implemented 2026-10-02** in `map/index.html` with one departure: Kevin kept a percent-of-site slider for Every lot (an empty lot at 0% to 100%, with the 75% by-law maximum marked on the track and each house appearing once its roofs fit) in place of the m²-of-material slider proposed in Sections 4, 5(d) and 8, so the material switch and the "room" tick were not built. Everything else below was built as written.

For Kevin. Read against `map/index.html` as of 2026-10-02 (909 lines); line numbers refer to that file. Nothing here changes a number, a constant, a formula or a data file; every change is to what is shown, where, in what order and at what size. All eight core functions survive; most move closer to the top.

Terms, glossed once: a **segmented control** is the pill-shaped switch with labelled segments that iOS Maps uses for Explore / Driving / Transit; a **disclosure** is a row with a chevron (›) that opens in place; a **sheet** is a card that slides up from the bottom of a phone screen and rests at a "peek" height or expands; a **chip** is a small tappable label; a **pill** is a small coloured capsule holding one word.

Figures in the wireframes are the page's own, recomputed from `map/data/`: 3528 W 30th Ave is 602.04 m²; roofs 237.2 m² to the walls (39.4%), 280.4 m² to the roof edge; room 214.3 m²; with the default schedule 319.2 m² (53.0%), PASS with 132.3 m² spare. Citywide: 62,188 assessed lots; 1 over 75% at rest, 157 at +60 m² of concrete; 769 roofs over 50% to the walls (13,581 to the roof edge); 94% of a 48 mm storm soaks in at rest.

---

## 1. First sixty seconds, as a stranger

Setting: a 13-inch MacBook, Safari, viewport about 1440 × 790. The panel is 372 px wide and at most 766 px tall (`#panel`, lines 89–94). Heights below are my measurements from the CSS.

**0–2 s.** A pale street map, zoomed to 17.2 on a block of W 30th Ave; in its centre, in grey, "Loading about 62,000 lots…" (line 189). On the left the panel is already fully typeset: the title **"Impermeable materials on R1-1 lots"** (16 px); a two-line grey subtitle "R1-1 District Schedule, June 2026, with Section 2 · City parcels · 2015 roof footprints"; a bordered box **"Buildings · 50% of the site"** quoting "Maximum site coverage for all buildings — 50% of the site area" *s.3.2.2.7, p.12*; a taller box **"Impermeable materials · 75% of the site, buildings included"** with two quotes; a blue link "What counts as impermeable? (Section 2, verbatim)"; a blue-tinted callout beginning **"Permeable pavers count as impermeable** (p.20; added 2023 by By-law 13670 …)"; the small-caps header **ONE LOT**; a field whose placeholder reads "3528 W 30TH AV, or click a lot", a "Find" button, and a bordered card saying "Loading…" (line 208), about 516 px down. The fold cuts just below it.

*Hesitation 1.* The only finished things on screen are quotations, so a stranger starts reading law before being shown what the page does.

**2–20 s** (the 17 MB lot file). The lots paint: every lot red with a blue band along its north edge, a black outline on the opening lot, and on every lot a 10 px label, "roofs 39% · room 214 m²" (lines 857–863).

*Hesitation 2.* "Room" is the page's key word; this label is the first place it appears, undefined.

The card fills (`renderLot`, 590–672): **"3528 W 30TH AV"** / "602.0 m² site"; the area bar marked "50%" and "75%"; "Roofs to the walls (2015; 0.45 m eave off)" / "237.2 m² · 39.4%"; "Room under 75% after the roofs" / **214.3 m²**; "Paving on this lot *illustrative; edit it*"; the top of a table. The fold lands here.

*Hesitation 3.* The field still shows its placeholder, not the selected address, so field and card disagree about whether a lot has been chosen.

**Meanwhile, silently,** a second file (35 MB of footprints, 886–903) downloads; dark roofs appear 10–40 s later with no sign that anything was pending, and because the red/blue split ignores where the house is, a dark roof lands on blue "permeable" ground. (The legend that calls the split "a diagram, not a plan" is 1,350 px further down.)

**20–35 s. Scrolling.** Three table rows: an 11 px select reading "permeable pavers", a 56 px number "45", a 10 px red badge "counts"; then "concrete or asphalt / 25 / counts"; then "wood decking, tight boards or r…" (truncated) "/ 12 / counts". "+ add a surface". "Roofs + paving" / **"319.2 m² · 53.0%"**. Then, about 840 px down, in 12 px green bold: **"PASS, 132.3 m² spare"** beside "s.3.2.2.8". The page's answer is the size of its labels and below the fold on a laptop. Under it: "As permeable, the pavers would read 45.5%. The by-law counts them (p.20)." and a link "Arithmetic, passages, storm, Rhino".

**35–50 s. EVERY LOT.** "Paving added to every lot" / **0 m²** (20 px). A slider with a purple tick whose 11 px label "this lot's room 214 m²" sits in the same band as "0: roofs only" and "250 m²". Three uneven buttons: "concrete or asphalt / counts", "permeable pavers / counts", "gravel or river rock under 5 cm / does not count" (three lines). Then **"1"** / "of 62,188 lots over 75% (0.0%)" and "Roofs alone, to the walls. Drag to add paving to every lot." Then, in 24 px amber, **"769"** / "roofs over 50% even to the walls: check", and "13,581 to the roof edge; the 0.45 m eave allowance leaves 769. The air photo cannot say which is right."

*Hesitation 4.* At rest, 769 in amber is the largest and most saturated number in the panel (`.count b`, 162–164). It reads as the headline result, and it concerns the 50% rule, not the 75% rule in the title. The lot's by-law verdict, two screens up, is 12 px.

**50–60 s.** A dashed card tagged "NOT THE BY-LAW": "48 mm storm, every lot as set above", a three-colour bar, **"94%** soaks in · **19,300 m³** to the storm sewer, about 8 Olympic pools", and the Rain City sentence. Then a six-entry legend, the button "Zoom out to the whole city" (the only way to see the city, about 1,450 px down), "Assumptions and limits", a footer. The panel scrolls roughly 1,600 px: two viewports.

**Count above the fold:** thirteen elements compete: title, subtitle, two rule boxes, disclosure link, callout, section header, search field, Find button, address row, area bar with two marks, roofs row, room row. Four are reference, three are controls, four are results, two are labels. **Where the eye goes:** to the two bordered boxes and the tinted callout, the only shapes with borders and colour. **Where it should go:** to the bar and the verdict, which arrive last, 500–840 px down, after the data loads.

What a stranger concludes at sixty seconds: a page of by-law quotations with a map attached; the map is mostly red; 769 of something is wrong. They have not seen that it tests a lot, and have not touched the control that teaches the pavers lesson.

---

## 2. Diagnosis

Eight root problems. Each is checked against the source; two of the candidates I was given are rejected or reframed.

**1. Reference before task (progressive disclosure, inverted).** The by-law boxes, the Section 2 disclosure and the lesson callout (lines 195–201) all sit above the first control (203–207). About 350 px of reading before the task. HIG: show the result, make the explanation one tap away. *Confirmed.*

**2. Two subjects in one column, with equal weight.** "One lot" and "Every lot" are identical `h2`s (203, 210) in one scroll; the slider is about 1,000 px down. Worse, the two sections use near-identical labels within one screen: "Paving on this lot" (636) and "Paving added to every lot" (212), so a reader takes the slider as a continuation of the lot's schedule. There is no single obvious primary action. *Confirmed.*

**3. Reading, editing and result are interleaved, and editing rebuilds everything.** `renderLot` emits read-only rows, then a form, then results, then a disclosure, all in one `innerHTML` (603–661). Changing a material re-renders the whole card; typing an area re-renders it 600 ms after the last keystroke (`renderLotTotalsOnly`, 697), which blurs the field you are typing in if you pause. The comment at 694–695 names the problem; the pause only delays it. *Confirmed, and partly a behaviour bug.*

**4. Controls below the size a thumb or an eye can use.** Selects at 11 px in a 34%-wide cell (125, 640) truncate every long material name; number inputs 56 px wide (127); badges at 10 px (129); material buttons at 11 px with 10 px sublabels (157–158); a 16 px slider thumb (139). HIG's minimum target is 44 pt; the minimum legible caption is 11 pt and most of this panel is 10–12 px. *Confirmed.*

**5. The hierarchy of numbers is upside down.** Verdict 12 px (`.verdict`, 121); slider readout 20 px (133); city counts 24 px (162), with the 50% check count in amber. The least important number is the biggest. Separately, `.check { color: var(--check) }` (122) paints "over, even to the walls: check" in raw #ffbf00 on a near-white surface, about 1.6:1 contrast, while `--check-ink` exists for exactly this and is unused there. *Confirmed, plus an accessibility bug.*

**6. Things far from what they explain.** The legend (231) is 1,350 px from the map colours it decodes; "Zoom out to the whole city" (233) is 1,450 px from the map. The candidate finding "the legend explains colours the user has not yet wondered about" I **reject**: the problem is the opposite. The legend arrives long after the question, not before it.

**7. The storm card still out-dresses the by-law result.** It has been demoted and tagged (223–229), which is right. But it keeps the only dashed border, a colour bar and two bold numbers (770–773), so at rest it is typographically louder than "PASS, 132.3 m² spare". *Confirmed, in weakened form.*

**8. The loading, empty and error states teach the wrong lesson.** During load, the quotes are complete and the task says "Loading…" (208) while the slider is drawn at half opacity (143), which reads as broken. The second 35 MB download is silent. The placeholder "3528 W 30TH AV, or click a lot" (205) is an instruction wearing a field's clothes: it vanishes on focus, and it never reflects the lot actually selected. A failed search replaces the whole lot card with the error (730), destroying the result the visitor had. *Confirmed on all four counts.*

---

## 3. Design principles for this redesign

1. **The answer first, the law one tap away.** Verdict and bar at the top; every number carries a chip (`s.3.2.2.8 · p.12 ›`) that opens the passage in place. (Sections 4, 5b)
2. **One subject per screen.** One lot or every lot, chosen with a segmented control; never both in view. (Section 4)
3. **Show, then say.** A bar, a pill, a tick or a ghost mark replaces nine of the current sentences. The sentence survives only as a caption on the mark. (Sections 5, 6)
4. **Read with the thumb, not a loupe.** Nothing under 12 px; rows 44 px; a 24 px slider thumb; full-width selects. (Section 7)
5. **Things live next to what they explain.** Legend on the map; the city button on the map; the passage under the number; the eave caption under the roof figure. (Sections 4, 8)
6. **Honest at the point of use, not in a preamble.** "2015", "Illustrative. Edit it.", "Council policy, not the by-law" sit on the figures they qualify, in caption type, once. (Section 6)

---

## 4. The proposed structure

**Recommendation: two modes under one segmented control, "One lot | Every lot", at the top of the panel, like Maps' Explore / Transit.** The selected lot persists across both as a one-line chip (address · room), because the slider's purple tick depends on it.

Why two modes rather than one flow: the two operations have different subjects (one lot, 62,188 lots), different controls (a schedule, a slider), different map states (zoom 17, the whole city) and different outputs (a verdict, a count). A single column makes a reader take them as one argument, and the near-identical "Paving on this lot / Paving added to every lot" labels prove that reading is already happening. **Rejected alternative:** two stacked cards with stronger borders. It keeps the scroll, keeps the competition, and borders are the thing this panel already has too many of. **Second rejected alternative:** a floating slider along the bottom of the map, Weather-timeline style, with the panel for the lot only. Elegant on a desktop, but the tick label, the count and the material switch need the panel's width, and on a phone there is nowhere to put it beside the sheet.

Switching to "Every lot" also moves the camera to the city bounds; switching back eases to the selected lot. That absorbs "Zoom out to the whole city". A small "City" button stays on the map, under the +/− control, for anyone in One-lot mode who wants the overview without changing mode.

**Primary (always visible, both modes):** title and a one-line subtitle that *is* the two rules ("Buildings ≤ 50% · impermeable ≤ 75%, buildings included"); the segmented control; the selected-lot chip.

**One lot, in order:** search; the hero (area bar, verdict pill and margin); three rows: Roofs, Buildings ≤ 50%, Room after roofs; the Paving schedule as a list; Roofs + paving; disclosure rows: Check the arithmetic, Storm (not the by-law), Draw it in Rhino, The by-law verbatim.

**Every lot, in order:** the hero (the count over 75%); the added amount and material; the slider with the tick; the material segmented control; one hint line; disclosure rows: 769 roofs over 50% · check; 48 mm storm; The by-law verbatim.

**Secondary (one tap):** every passage, under its chip, inline; the hand-check sum; each material's "why"; the eave sentence behind the check count; the full storm card.

**Tertiary (a sheet):** "The by-law, verbatim": s.3.2.2.7, s.3.2.2.8, s.4.2.2, the three Section 2 definitions, the June 2026 consolidation note, PDF links, Assumptions and limits, sources and repository. Reached from the last row of either mode and from "Full text ↗" inside any inline passage. This is where `#rule50`, `#rule75`, `#defs`, `#notes` and `#footer` go, unchanged in content.

**Where the lesson goes.** The callout dissolves into the controls that teach it: on the schedule row for pavers the classification reads "● Counts, despite the name"; the material segmented control carries "Counts / Counts / Doesn't count" under its three names; the hint line under it says "Pavers count the same as concrete (p.20)" when pavers are chosen. The "if pavers were permeable, 45.5%" sentence becomes a dotted ghost mark on the lot's bar.

**Where the storm card goes.** A collapsed disclosure row at the bottom of Every lot: "48 mm storm · 94% soaks in ›" with the caption "Rain City Strategy, a Council policy · not the by-law". Opened, it is the current card minus the dashed border. In One lot it stays one line inside "Storm · not the by-law ›", as now.

**Where the legend goes.** On the map, bottom-left, as a strip of five swatches with one-word labels; always shown on desktop; on a phone, behind a small ⓘ button at the map's bottom-right so it never fights the sheet. The two amber entries merge into one ("Check: roof over 50%"), since the outline and the cluster circle mean the same thing at different zooms. **Rejected:** a legend toggle inside the panel. The question "what is red?" is asked while looking at the map.

---

## 5. Screen states, as text wireframes

Panel width stays 372 px (46 characters here). Type sizes in the margin are from Section 7. "Fixed" means it does not scroll.

### (a) First load, before a lot is chosen

```
┌──────────────────────────────────────────────┐
│ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ │  2 px moving progress bar, --accent
│ Impermeable materials                        │  Title 17/600
│ Vancouver R1-1 · buildings ≤ 50% ·           │  Caption 12, --ink-2
│ impermeable ≤ 75%, buildings included        │
│                                              │
│ ┌──────────────────────┬───────────────────┐ │
│ │       One lot        │     Every lot     │ │  Segmented, 36 px; "One lot" selected
│ └──────────────────────┴───────────────────┘ │
│                                              │
│ ┌──────────────────────────────────────────┐ │
│ │ ⌕  Search an address                     │ │  Field, 44 px
│ └──────────────────────────────────────────┘ │
│                                              │
│ ░░░░░░░░░░░░░░░░░░░░░░░░░                    │  skeleton: address
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │  skeleton: bar
│ ░░░░░░░░░░░░░░░░░                            │  skeleton: verdict
│                                              │
│ Loading 62,000 lots (17 MB)…                 │  Caption 12
└──────────────────────────────────────────────┘
```
Nothing scrolls. The map keeps its centred "Loading about 62,000 lots…". The segmented control and field are live-looking but inert until the data arrives (a tap on "Every lot" shows the same skeleton). No half-opacity slider anywhere.

### (b) A lot selected, at rest (One lot)

```
┌──────────────────────────────────────────────┐
│ Impermeable materials                        │  fixed
│ Vancouver R1-1 · buildings ≤ 50% ·           │
│ impermeable ≤ 75%, buildings included        │
│ ┌──────────────────────┬───────────────────┐ │
│ │       One lot        │     Every lot     │ │  fixed
│ └──────────────────────┴───────────────────┘ │
│ ┌──────────────────────────────────────────┐ │
│ │ ⌕  3528 W 30th Ave                     ⊗ │ │  shows the selected address; ⊗ clears
│ └──────────────────────────────────────────┘ │
│ ──────────────────────────────────────────── │  hairline; everything below scrolls
│ 3528 W 30th Ave                 602.0 m² site│  Title 17/600 · Caption 12
│                                              │
│ ████████████▒▒▒▒▓▓▓▓▓▓▓░░░░░░░░              │  bar 14 px: dark roof, red paving, blue spare, grey past 75%
│               ╎50%           ╎75%            │  marks, Caption 12
│                                              │
│ ┌────┐                                       │
│ │PASS│ 132.3 m² spare                        │  pill + Display 28/600 in --pass
│ └────┘ s.3.2.2.8 · p.12 ›    with the paving below   Caption 12; chip in --accent
│                                              │
│ Roofs                        237.2 m² · 39%  │  Body 14, row 44 px
│   2015, to the walls (0.45 m eave off) ·     │  Caption 12
│   280.4 m² to the roof edge                  │
│ Buildings ≤ 50%        ✓ within   s.3.2.2.7 ›│  Body 14 + chip
│ Room after roofs                   214.3 m²  │  Body 14/600 number
│   s.3.2.2.8 · s.4.2.2 ›                      │  chip
│                                              │
│ PAVING                 Illustrative. Edit it.│  Section header 12 caps · Caption
│ Driveway and parking pad          [ 45 ] m²  │  row 56 px: label 14; input 64 px
│   Permeable pavers ▾  ● Counts, despite the name     select as text + chevron; red dot
│ Walks and patio                   [ 25 ] m²  │
│   Concrete or asphalt ▾       ● Counts · p.20│
│ Deck                              [ 12 ] m²  │
│   Wood decking, tight or raised ▾ ● Counts · p.20
│ + Add a surface                              │  row 44 px, --accent
│                                              │
│ Roofs + paving              319.2 m² · 53%   │  Body 14
│                                              │
│ Check the arithmetic                       › │  disclosure rows, 44 px
│ Storm · Council policy, not the by-law     › │
│ Draw it in Rhino                           › │
│ The by-law, verbatim                       › │
└──────────────────────────────────────────────┘
```
By my sums the verdict sits about 250 px from the top of the panel and the whole schedule fits above a laptop fold; only the four disclosure rows scroll. "Check the arithmetic" opens the current hand-check line set as an aligned sum (same figures, same formula):

```
   0.75 × 602.04   =  451.53   limit under s.3.2.2.8
   − roofs            237.22   2015, to the walls
   = room             214.31
   − paving            82.00   the schedule above
   = spare            132.31   PASS
```

### (c) Editing the schedule (driveway set to 190 m²)

```
│ ████████████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▓░░░░░            │  red grows live; purple past 75%
│               ╎50%     ┊if pavers│75%        │  dotted ghost mark at 45.5%
│               │        │were permeable        │  Caption 12, --ink-3
│ ┌────┐                                       │
│ │FAIL│ 12.7 m² over                          │  pill + Display 28/600 in --fail
│ └────┘ s.3.2.2.8 · p.12 ›    with the paving below
│  …                                           │
│ PAVING                 Illustrative. Edit it.│
│ Driveway and parking pad         [190|] m² ⊖ │  focused field keeps focus; ⊖ removes the row
│   Permeable pavers ▾  ● Counts, despite the name
│   The by-law counts pavers as impermeable:   │  the row's "why", one tap on the dot
│   By-law 13670 (2023), "most permeable pavers│  Caption 12
│   lose their permeability over time". p.20   │
│ Walks and patio                   [ 25 ] m²  │
│   Concrete or asphalt ▾       ● Counts · p.20│
│ Deck                              [ 12 ] m²  │
│   Wood decking, tight or raised ▾ ● Counts · p.20
│ + Add a surface                              │
│ Roofs + paving              464.2 m² · 77%   │
```
The bar and verdict update on every keystroke without rebuilding the rows (Section 9, item 4). Tapping the material text opens the native picker, grouped as now: "Counts as impermeable (p.20)" / "Does not count (p.31)". A row set to a material that does not count shows "○ Doesn't count · p.31" with a blue ring.

### (d) Every lot, slider at +60 m², concrete

```
┌──────────────────────────────────────────────┐
│ Impermeable materials                        │  fixed
│ Vancouver R1-1 · buildings ≤ 50% ·           │
│ impermeable ≤ 75%, buildings included        │
│ ┌──────────────────────┬───────────────────┐ │
│ │       One lot        │     Every lot     │ │  "Every lot" selected; camera at city bounds
│ └──────────────────────┴───────────────────┘ │
│ ● 3528 W 30th Ave · 214 m² room    Change ›  │  chip row, 44 px; "Change" → One lot
│ ──────────────────────────────────────────── │
│ 157                                          │  Display 28/600, --over
│ of 62,188 lots over 75%  ·  0.3%             │  Body 14
│                                              │
│ +60 m²   concrete on every lot               │  Title 17/600 · Body 14
│                  This lot's room · 214 m²    │  Caption 12 in --over, centred on the tick
│ ━━━━━━━━━━━━━━●━━━━━━━━━━━━┃▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ │  track 4 px: blue to the tick, purple past; thumb 24 px
│ Roofs only                          250 m²   │  Caption 12
│                                              │
│ ┌──────────┬──────────────────┬────────────┐ │
│ │ Concrete │ Permeable pavers │   Gravel   │ │  Segmented, 48 px, two lines
│ │  Counts  │      Counts      │Doesn't count│ │  sublabels Caption 12
│ └──────────┴──────────────────┴────────────┘ │
│ Lots with less than 60 m² of room.           │  Caption 12, one line, changes with material
│                                              │
│ 769 roofs over 50% · check                 › │  disclosure rows
│ 48 mm storm · 81% soaks in                 › │
│ The by-law, verbatim                       › │
└──────────────────────────────────────────────┘
```
Nothing scrolls until a disclosure opens. Past the tick the "+60 m²" number turns purple (as the readout does now). With Gravel chosen: the track is all blue, the count reads "1", the hint reads "Gravel doesn't count (p.31). As pavers, 157 would be over." With Permeable pavers: nothing moves, and the hint reads "Pavers count the same as concrete (p.20)." For the 14,057 lots whose room exceeds 250 m², the tick sits at the right end with "This lot's room 480 m² →".

### (e) A not-assessed lot

```
│ ┌──────────────────────────────────────────┐ │
│ │ ⌕  R1-1 lot (no civic address)         ⊗ │ │
│ └──────────────────────────────────────────┘ │
│ ──────────────────────────────────────────── │
│ R1-1 lot (no civic address)      92.0 m² site│
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │  bar in --out, no marks
│ ┌────────────┐                               │
│ │NOT ASSESSED│                               │  pill in --out
│ └────────────┘                               │
│ Under 150 m²: not assessed as a site.        │  Body 14 (the existing flag strings)
│                                              │
│ Why some lots are grey                     › │  → Assumptions and limits
│ The by-law, verbatim                       › │
```
The slider's tick hides, as now. The chip in Every lot reads "● R1-1 lot (no civic address) · not assessed".

### (f) The phone sheet, under 560 px

Collapsed ("peek", 96 px), so the map and the verdict are visible together:
```
┌──────────────────────────────────────────────┐
│                  ▬▬▬▬                        │  grab handle
│ 3528 W 30th Ave                     PASS     │  Title 17 · pill
│ 132.3 m² spare · room 214 m²                 │  Body 14
└──────────────────────────────────────────────┘
```
Expanded (90% of the screen): the handle, then exactly the desktop layout of state (b) or (d), with the segmented control fixed under the handle and the body scrolling. Tapping the handle toggles; dragging it is optional (Section 9, item 11). Selecting a lot on the map while collapsed updates the peek row and does not expand the sheet. In Every-lot mode the peek row reads "157 of 62,188 over 75% · +60 m² concrete".

---

## 6. Microcopy

| Current | Proposed | Why |
|---|---|---|
| **Impermeable materials on R1-1 lots** | **Impermeable materials** | Shorter title; the place and rules move to the line under it. |
| R1-1 District Schedule, June 2026, with Section 2 · City parcels · 2015 roof footprints | Vancouver R1-1 · buildings ≤ 50% · impermeable ≤ 75%, buildings included | The subtitle states the two rules in nine words and replaces the two boxes. Sources move to the by-law sheet. |
| Buildings · 50% of the site (box) | Buildings ≤ 50% · ✓ within · s.3.2.2.7 › | Becomes a result row with a chip. The quote opens under it. |
| Impermeable materials · 75% of the site, buildings included (box) | the subtitle, and chips on the Room and verdict rows | Same words, placed where the number is. |
| What counts as impermeable? (Section 2, verbatim) | What counts, in the by-law's words (in the sheet) | Statement, not question; and taught by the pills before anyone reads it. |
| Permeable pavers count as impermeable (p.20; added 2023 by By-law 13670 …). Decking escapes only with spaced boards on grade. Gravel, mulch and planting do not count. | ● Counts, despite the name (pavers row); "Counts / Counts / Doesn't count" (material control); hint: Pavers count the same as concrete (p.20) | The lesson is delivered by the controls that embody it. The By-law 13670 sentence lives behind the pavers' dot. |
| One lot / Every lot (headers) | One lot / Every lot (segments) | Kept: parallel, the author's words. |
| 3528 W 30TH AV, or click a lot (placeholder) | Search an address; the field then shows the selected address | A field shows what is in it; the instruction moves to the empty state. |
| Find (button) | removed; Enter or the suggestion list | One fewer control; the list makes "Find" redundant. |
| Loading… (card) | Loading 62,000 lots (17 MB)… under a skeleton | Says what, how much, and looks like what is coming. |
| Click a lot, or type an address above. | Select a lot on the map, or search an address. | Device-neutral verb; order matches the layout. |
| No R1-1 lot matches "X". Spell it the City's way: number, street, AV / ST / DR. | No R1-1 lot at "X". Try the City's spelling, like 3528 W 30TH AV. (under the field; card untouched) | Concrete example instead of a rule; the result is not destroyed. |
| 602.0 m² site | 602.0 m² site | Kept. |
| Roofs to the walls (2015; 0.45 m eave off) · 237.2 m² · 39.4% | Roofs 237.2 m² · 39% / caption: 2015, to the walls (0.45 m eave off) · 280.4 m² to the roof edge | Number first; the honest qualifier in caption type, with the edge figure beside it. |
| Room under 75% after the roofs | Room after roofs · s.3.2.2.8 · s.4.2.2 › | "Under 75%" is on the chip and the bar. |
| Paving on this lot · illustrative; edit it | PAVING · Illustrative. Edit it. | Two sentences, four words. |
| counts / no (badges) | ● Counts · p.20 / ○ Doesn't count · p.31 | Symmetric, page-referenced, colour-coded to the map. |
| + add a surface | + Add a surface | Row-sized, sentence case. |
| s.3.2.2.8 · PASS, 132.3 m² spare | PASS pill · 132.3 m² spare · s.3.2.2.8 · p.12 › · with the paving below | Status as a pill, margin as the big number, honesty as a caption. |
| FAIL, over by 12.3 m² | FAIL pill · 12.3 m² over | Same information, number leads. |
| over, even to the walls: check | CHECK pill · Roofs over 50%, even to the walls | Status as a pill in `--check-ink`, readable. |
| As permeable, the pavers would read 45.5%. The by-law counts them (p.20). | dotted mark on the bar: "if pavers were permeable" | A sentence becomes a mark. |
| Arithmetic, passages, storm, Rhino | Check the arithmetic › / Storm · Council policy, not the by-law › / Draw it in Rhino › / The by-law, verbatim › | Four things, four rows. |
| Rhino: set ADDRESSES to "…" in map/rhino_site.py and run it. | Draw it in Rhino › opens the same sentence | Kept, one tap down. |
| Paving added to every lot · 0 m² | +60 m² concrete on every lot | Amount and material in one line. |
| 0: roofs only / 250 m² | Roofs only / 250 m² | The colon-zero was code, not a label. |
| this lot's room 214 m² (tick) | This lot's room · 214 m² (above the track) | Capitalised, separated from the stops. |
| this lot: no room, roof alone over | This lot: no room | Shorter; the lot's own card explains. |
| this lot's room 480 m², past the end | This lot's room 480 m² → | An arrow says "past the end". |
| concrete or asphalt · counts | Concrete · Counts | Full by-law name lives in the passage. |
| permeable pavers · counts | Permeable pavers · Counts | Kept: the name is the lesson. |
| gravel or river rock under 5 cm · does not count | Gravel · Doesn't count | Fits one line. |
| 1 of 62,188 lots over 75% (0.0%) | 1 / of 62,188 lots over 75% · 0.0% | Big number, then the sentence. |
| Roofs alone, to the walls. Drag to add paving to every lot. | Roofs only. Drag to pave every lot. | Half the words. |
| Lots with under 60 m² of room after their roofs. | Lots with less than 60 m² of room. | "Room" is defined by now. |
| Gravel or river rock under 5 cm does not count (p.31). As pavers, 157 lots would be over. | Gravel doesn't count (p.31). As pavers, 157 would be over. | Shorter. |
| 769 roofs over 50% even to the walls: check / 13,581 to the roof edge; the 0.45 m eave allowance leaves 769. The air photo cannot say which is right. | 769 roofs over 50% · check › opening to the eave sentence | Demoted from headline to disclosure, as the author intended after review B3. |
| NOT THE BY-LAW (tag) | Council policy · not the by-law (caption on the row) | Says what it *is* as well as what it is not. |
| 48 mm storm, every lot as set above | 48 mm storm · 94% soaks in › | The row carries its own headline. |
| 39% soaks in · 717,300 m³ to the storm sewer, about 287 Olympic pools | unchanged inside the open row | Fine as is. |
| Rain City Strategy (2019), a Council policy; R1-1 has no retention rule. 85% runoff and 75 mm soil storage are assumptions. | Rain City Strategy, 2019. R1-1 has no retention rule. Assumes 85% runoff, 75 mm soil. | Same facts, fewer clauses. |
| permeable / impermeable / over 75% / not assessed / roof over 50%: check / check sites, zoomed out | Permeable · Impermeable · Over 75% · Check: roof over 50% · Not assessed | Five entries; the two amber ones are one meaning. |
| The split in each lot is a diagram, not a plan. | Split drawn as a diagram | Four words, same honesty. |
| Zoom out to the whole city | City (map button); also the "Every lot" segment | Lives on the map. |
| Assumptions and limits | Assumptions and limits (in the sheet) | Kept. |

---

## 7. Visual system

**Type scale (four levels; nothing smaller than 12 px).**
- Display 28/32, weight 600, tabular numerals: the one big number per mode (verdict margin, city count). Replaces `.count b` 24 px and `.readout b` 20 px.
- Title 17/22, weight 600: panel title, address, "+60 m²". Replaces `h1` 16 px and `.addr` 14 px.
- Body 14/20, weight 400 (600 for the number in a row): rows, labels, hint lines. Most of the panel moves up from 12 px to this.
- Caption 12/16, weight 400, `--ink-2` (never `--ink-3` for anything that must be read): references, qualifiers, legend, stops. Replaces `.small` 11 px, `.cls` 10 px, `.mark i` 10 px, `.mat small` 10 px.

**Spacing scale:** 4, 8, 12, 16, 24, 32. Panel padding 20 (16 on phone). Row height 44 (`--row: 44px`); schedule row 56. Section gap 24. Hero to first row 16.

**Radii:** panel 12; field, buttons, segmented-control track 10 (inner segment 8); pills 999; bars 4; chips none (they are text).

**Separation.** No bordered boxes inside the panel. Sections separate by 24 px and a 12 px caps header where one is needed (PAVING). One hairline (`--rule`) between the fixed header and the scrolling body. Remove the borders on `.rule`, `#lot`, `.water`; remove the `.lesson` tint. The panel keeps its single outer border and shadow.

**Primary controls.**
- Mode segmented control: full width, 36 px, track `--fill`, selected segment `--surface` with `0 1px 3px rgba(0,0,0,.12)`, Body 14/600; `role="tablist"`.
- Material segmented control: same style, 48 px, two lines per segment (Body 13/600 name, Caption 12 sublabel), segments sized to content so "Permeable pavers" fits on one line; the sublabel of the selected segment in `--ink`, others `--ink-2`.
- Slider: track 4 px, blue to the tick and purple past it (as now), thumb 24 px `--surface` with a 1 px `--rule` ring and a soft shadow; focus ring 2 px `--accent`. Tick 2 px `--over`, 16 px tall, centred on the track; label above the track.
- Search field: 44 px, `--fill` background, no border, magnifier glyph, Body 14; a clear (⊗) button when it holds text.
- PASS / FAIL / CHECK / NOT ASSESSED pills: Caption 12/600 uppercase, letter-spacing .04em, 22 px tall, filled `--pass` / `--fail` / `--check-ink` / `--out`, white text. The margin beside them in the same colour at Display size.
- Classification dots: 8 px, `--impermeable` filled for Counts, `--permeable` ring for Doesn't count.
- Disclosure rows: 44 px, Body 14, chevron in `--ink-3` at the trailing edge; implemented as `<details>` so they work without JavaScript and announce themselves.

**The lot colours in the panel.** They appear in exactly four places: the area bar (roof dark, red paving, blue spare, grey past 75%, purple over), the slider track, the classification dots, and the legend. Red and blue are never used for text. Purple is used for text only on the city count and the tick label, grey (`--out`) only on the Not-assessed pill and bar.

**Variables.** Keep every existing one. Add: `--fill: color-mix(in srgb, var(--ink) 6%, var(--surface))` (control tracks, skeletons); `--roof: #3d3d3a` with `#6b6a65` in the two dark blocks, so the panel bar's roof matches the map's dark-mode roof (today `COLOR.roof` is used in both modes and nearly vanishes on the dark surface); `--row: 44px`. Fix `.check` to use `--check-ink`. Change the `.swatch.outline` and `.swatch.cluster` fixed `#17212b` to `var(--ink)` so they survive dark mode.

---

## 8. Interaction details

**Slider.** Drag or arrow keys, step 5 as now. The "+N m²" title updates on every input; the count and hint update on every input (they do now). Past the tick, "+N m²" turns purple and the count's number is already purple when non-zero. `aria-valuetext` on each change: "60 square metres of concrete on every lot; 157 lots over 75 percent". The tick label sits above the track so it never collides with the stops; when the tick is within 40 px of an end, its label aligns to that end (the current `l / c / r` classes do this; only the vertical position moves). When the selected lot is not assessed, the tick hides and the track is plain blue.

**Material control.** Tap or arrow keys (`role="radiogroup"`). Choosing pavers after concrete changes nothing on the map; the hint line immediately says why, and the count does a 300 ms "settle" (a brief scale to 1.04 and back) so the eye notices that nothing changed on purpose. Choosing gravel turns the track blue and the count drops to 1.

**Address search.** Typing three characters shows up to eight matching addresses in a `<datalist>` (native, accessible, works on iOS). Enter or picking one selects the lot and eases the camera to zoom 17 (as `selectLot(f, true)` does now). The field then shows the selected address; the ⊗ clears the field *and* the selection. A failed search puts one caption line under the field and leaves the card alone. Matching uses the existing `normalise`/`startsWith` logic; only the presentation of multiple matches is new.

**Selecting a lot on the map.** The card header cross-fades (150 ms) and the bar's segments animate to their new widths (250 ms ease-out). The black selection outline stays as now. No camera move on a map click (as now). On a phone with the sheet collapsed, only the peek row changes, so the map stays visible.

**Progressive disclosure.** Chips and rows are `<details>` elements: tap to open in place, tap again to close; the chevron rotates 90°. Only one passage disclosure needs to be open at a time, but do not enforce it; let the reader keep two open to compare. "Full text ↗" inside any passage opens the by-law sheet, which on desktop is a scrolling section replacing the mode body with a "‹ Back" row, and on phone is the sheet at full height.

**City.** "Every lot" eases the camera to `CITY_BOUNDS`; "One lot" eases back to the selected lot at zoom 17, or does nothing if no lot is selected. The map button "City" does only the camera move.

**Keyboard and screen reader.** Tab order: segmented control, search, then the body. The verdict block is `aria-live="polite"` so a change in the schedule announces "FAIL, 12.7 m² over". Each pill carries its word as text (not colour alone). The area bar keeps `aria-hidden`; its meaning is in the rows. Material selects keep their current `aria-label`s. Every disclosure is a native `<summary>`.

**While 17 MB loads.** The panel renders at once with the skeleton of state (a) and an indeterminate 2 px progress bar at its top edge (a determinate bar is unreliable because GitHub Pages reports compressed byte counts). When `lots.geojson` has parsed, the skeleton cross-fades to the card. The second file (35 MB of roofs) gets a one-word indicator: a small "Roofs…" caption at the bottom of the legend strip that disappears when the layer is added, and "Roof outlines not available" if it fails (the current `legendNote` text, shortened).

---

## 9. Implementation plan

Ordered so each step leaves the page working. "Behaviour" flags anything beyond presentation. Arithmetic (`assess`, `sumSchedule`, `waterBalance`, `normalise`, the CONFIGURATION block) is untouched throughout.

1. **Type, spacing, radii, borders — CSS only. Small.** New scale from Section 7; remove borders on `.rule`, `#lot`, `.water`; remove `.lesson` background; `.check` → `var(--check-ink)`; `.swatch.outline`/`.cluster` → `var(--ink)`; add `--fill`, `--roof`, `--row`; slider thumb to 24 px. *Flag:* `THUMB_PX` (line 678) is a layout constant in JS that must become 24 so the tick stays aligned; not arithmetic.

2. **Header and modes — HTML + CSS + a small JS handler. Small.** Replace `#subtitle`'s text with the two-rule line (still templated from `BYLAW`). Add `<div id="modes" role="tablist">` with two buttons. Wrap `.search` + `#lot` in `<section id="modeLot">` and `.readout`, `.track`, `.stops`, `#mat`, `#cityStatus`, `#water` in `<section id="modeCity">`. A `data-mode` attribute on `#panel` shows one section. *Behaviour:* the handler also calls `map.fitBounds(CITY_BOUNDS)` or eases to the selected lot. Add `#lotChip` under the segmented control; `renderLot` writes one line into it.

3. **The by-law sheet — HTML move. Small.** Move `#rule50`, `#rule75`, `#defs`, the `#notes` details and `#footer` into `<details id="bylaw">` at the bottom of both modes (one element, moved by CSS order or duplicated by reference; simplest is one `<details>` after the sections, visible in both modes). Delete `#lesson` after step 4 absorbs its text. The render code at 392–404 keeps writing to the same ids.

4. **renderLot — JS render function. Large (the one big change).** Reorder the output to: header row, bar (now with the ghost mark when `t.pavers > 0`), verdict block (pill + margin + chip + "with the paving below"), three rows with inline `<details class="ref">` passages (text from `PASSAGES`), the schedule as a `<ul>` of rows (full-width select, 64 px input, dot + classification + page from `MAT[id].why`), "Roofs + paving", and four `<details>` rows replacing the single "Arithmetic, passages, storm, Rhino" one. **Split the function** into `renderLotShell()` (structure, run on select/material/add/remove) and `renderLotTotals()` (bar widths, verdict, roofs+paving, hand-check, ghost mark, tick) run on every keystroke by updating existing nodes, so the field never loses focus; delete the 600 ms timer. *Behaviour:* add a remove (⊖) control per row (`state.schedule.splice`). *Behaviour fix:* the not-found message (line 730) goes to a new `#addrError` caption instead of `#lot.innerHTML`.

5. **Search — HTML + JS. Medium.** Remove `#addrGo`; add `<datalist id="addrList">`; on `input`, fill it with up to eight `normalise(...).startsWith(want)` matches (a new `suggestAddresses` beside `findAddress`, which stays). On select, `document.getElementById("addr").value = p.ad` in `selectLot`. Add the ⊗ clear button (sets `state.selected = null`, clears the map filter, `renderLot()`).

6. **Legend and City button — HTML/CSS move + small JS. Small.** Move `#legend` out of `#panel` to `<div id="mapLegend">` positioned bottom-left over `#map`; merge the two amber entries in the array at 412–419; on phone, toggle it with a ⓘ button. Replace `#cityBtn` with a MapLibre `IControl` (a 36 px button labelled "City") added `"top-right"` after the navigation control; same click handler (line 787).

7. **Slider and material control — CSS + small JS. Small.** `.tick span` moves above the track (`bottom: 100%`); `.stops` copy; `#mat` buttons restyled as segments with `role="radio"`; `cityUpdate` sets `slider.setAttribute("aria-valuetext", …)` from strings it already builds. Shorten the three names via a small display-name map beside `SLIDER_MATERIALS` (the by-law names in `MATERIALS` stay for the passages).

8. **cityUpdate — JS render function. Medium.** Split `#cityStatus` output into the Display count block, the "+N m² material" title, the one-line hint, and a `<details>` row for the 769 check count with the eave sentence inside. Wrap `#water` in a `<details>` whose summary is built from the same `share("heldM3")`; the card inside is unchanged. Keep every string templated as now.

9. **Loading and empty states — HTML + CSS + 3 lines of JS. Small.** Skeleton markup inside `#lot` and `#modeCity` at first paint; a `.progress` bar on `#panel` removed in the `map.on("load")` handler where `loading.remove()` runs (878); drop `disabled` opacity styling (the slider is hidden by the skeleton instead). The empty-state string at 593 changes.

10. **Dark mode check — CSS. Small.** `--roof` per theme; `renderLot` uses `var(--roof)` instead of `COLOR.roof` for the bar (one string).

11. **Phone sheet — CSS + small JS. Medium.** Under 560 px: `#panel` gets a handle, two heights (`--peek: 96px`, 90%), a `data-sheet="peek|full"` attribute toggled by the handle; a `#peek` row written by `renderLot`/`cityUpdate` (address, pill, margin, or the city count). Dragging with pointer events is optional and can come later.

12. **Animation — CSS. Small.** `transition: width 250ms ease-out` on `.areabar span` (works once step 4 updates nodes instead of rebuilding them); `transition: opacity 150ms` on the header.

Order of payoff: steps 1, 2 and 4 deliver most of the change; 5–9 finish it; 10–12 polish.

---

## 10. What not to change, and why

- **The colour language** (blue, red, purple, amber, grey) and its reuse in the panel's bar, slider and dots. It is consistent and it ties the card to the map. Only its text uses change.
- **The purple tick at the selected lot's room, and the blue-to-purple track.** It is the single best piece of interaction on the page: the one lot's number, visible while operating on all lots. The redesign moves its label above the track and leaves everything else.
- **The area bar as the lot's hero**, with marks at 50% and 75%. Promote it; do not redraw it.
- **The slider as square metres of a named material added to every lot**, with pavers behaving as concrete and gravel never crossing. This *is* the lesson, operated. Keep the three materials and the 0–250 range.
- **"Counts / does not count" as the classification vocabulary**, and every material carrying the passage it rests on (`MATERIALS[].why`). The redesign only makes them more visible.
- **Passages verbatim with page numbers and PDF links; the hand-check line; the two roof figures (edge and walls); "check", never "exceedance"; "illustrative" on the schedule; "2015" on the roofs; the storm card's tag and its separation from the by-law.** These are the honesty of the page. They move to caption type at the point of use and lose nothing.
- **Every string built from the CONFIGURATION constants.** The new strings must be templated the same way.
- **Opening on a real lot with its card filled, at zoom 17**, and the street-zoom labels "roofs 39% · room 214 m²". Answer first.
- **System font stack, the existing CSS variables, light and dark via `prefers-color-scheme`, the 560 px breakpoint, plain HTML/CSS/JS.** The redesign fits inside them.
- **The grey "not assessed" rule and its flag sentences.** They are correct and short; they only gain a pill.
