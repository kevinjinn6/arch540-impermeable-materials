# Review B — "Impermeable materials in Vancouver R1-1" (ARCH 540 A1)

Reviewer persona: design-faculty critic, first sight of the project, judged against ARCH540_A1_WrapUp.pdf.
Repository as found on disk 2026-10-01/02 (branch `stage2-policy-map`, working tree), plus the public remote `origin/main`.

---

## PART 1 — class peer-review format

**1. What input I tried.**
Both shipped examples (`examples/3528-w-30th-ave*.json`), the 33-test suite, and five lots of my own: a 10.06 × 37.2 m lot with classmate-style mistakes (material typo "permable pavers", "artificial turf", capitalised zone/use, a deck with no conditions, a garage overlapping the driveway); the same lot typed in feet (33 × 122); a file with `"rectangle"` instead of `"rect"`; an L-shaped polygon house with unsized river rock and a 1.2 m raised deck; and a lot whose surfaces exceed it. I also loaded `tool/web/index.html` in headless Chrome.

**2. Whether I understood the result, and whether I could match it to the source.**
Yes. The per-surface "counts as / because" table is clear, and the hand-worked example in `sources/r1-1-impermeable-extract.md` §4 let me reproduce 454.87 m² / 451.53 m² / 3.34 m² over against s.3.2.2.8, s.4.2.2 and the Section 2 lists with a calculator. I checked the two definitions against the June 2026 Section 2 PDF now in `sources/`: verbatim match (Impermeable Materials p.20, Permeable Materials p.31). I could not match the page numbers the tool cites (Nov 2025, p.21).

**3. What broke or confused me.**
A missing `"label"` or a misspelled `"rect"` key crashes with a raw Python traceback; a lot in feet is accepted as 4,026 m² and PASSES with no warning; a typo in a material name produces the opposite explanation to the lesson ("the Director of Planning may accept it as permeable"). Most seriously: the public GitHub repository does not contain this tool at all — `origin/main` says "The interactive map is the current tool" and the live Pages link is a citywide map. The README says "Week 3 of 4, not a finished submission" the day before the deadline.

**4. The one change I would make first.**
Commit `tool/`, `examples/`, `output/`, the extract and the Section 2 PDF, and rewrite the README front page to the brief's five headings, so the tool a classmate opens is the tool that exists.

---

## PART 2 — full critique

### Weaknesses

**1. CRITICAL — The tool is not in the repository anyone else can see.**
Evidence: `git status` lists `tool/`, `examples/`, `output/`, `sources/r1-1-impermeable-extract.md`, `sources/zoning-by-law-section-2.pdf` as untracked; `git ls-tree origin/main` has none of them. `origin/main:README.md` ("Current state") reads "The interactive map is the current tool", its repo map lists `map/index.html` as the tool, and `.github/workflows/pages.yml` deploys `map/` to `kevinjinn6.github.io/arch540-impermeable-materials/`.
Why it matters: the brief's whole mechanism (public repo, classmates use it with their own inputs, issues as evidence of revision) runs on the remote. A reviewer assigned this repo at 1:30 pm reviews a different, larger, policy-map tool — the one the README itself calls "too large to be the assignment tool".
Fix: commit the five items above (the .3dm is 0.7 MB; fine); make the working-tree README the README on `main`; either publish `tool/web/` with Pages (and put the link at the top, as the brief asks) or remove the map's Pages link so it does not masquerade as the tool.

**2. CRITICAL — README does not meet the brief's structure and is a week stale.**
Evidence: `README.md:21` "Week 3 of 4 … It is a tool in progress, not a finished submission." No heading named Purpose, How to use it, Source, or Skill. The intro (lines 6–15, 109 words) would serve as Purpose but is unlabelled and does not say for whom. Source version appears only under Limitations (line 191). Line 31: "skill and peer review not started." No Pages link at top.
Why it matters: the brief lists five sections a reviewer looks for; a classmate scanning for "Source" finds a register of seven documents instead of "R1-1 District Schedule, June 2026, s.3.2.2.7–8, s.4.2.2; Section 2, June 2026, Impermeable/Permeable Materials, p.20/p.31".
Fix: five headings at the top in the brief's order; Purpose in the author's own first-person voice with the audience named (landscape designers preparing R1-1 permit sets); Source as one short table; move "Current state", precursors and the W1 material below a rule.

**3. MAJOR — README statements that are false against the repo.**
Evidence: "25 test cases" (`README.md:31, :44`) — `python3 -m unittest tool/test_impermeable_check.py -v` runs 33. "The June 2026 PDF is not yet in the repo" (`README.md:192`) — `sources/zoning-by-law-section-2.pdf` is the June 2026 consolidation (PDF header "City of Vancouver June 2026", CreationDate 2026-06-08). Same stale claim in `sources/README.md:13` ("not yet stored … Download before W2 Friday"), `sources/r1-1-impermeable-extract.md:31–38`, `tool/web/index.html:268` (footer) and `:557–559` (`PAGE_REF` "p.21 (Nov 2025 consolidation)"). In the June 2026 PDF, Impermeable Materials is p.20 (not p.21) and Deck is p.11 (not p.12); Permeable p.31 and Patio p.30 match; the quoted wording matches verbatim. The repo map (lines 37–63) omits `buildings.py`, `map/`, `test lot.3dm`, `vancouver bylaw assignment 1.pages`.
Why it matters: the brief says every README step must be reviewed and true; a reviewer who catches "25" and "not yet in the repo" stops trusting the rest.
Fix: do the line-by-line comparison the extract promises (ten minutes), change the four page references and the version string in all five places, delete the ‡ caveat, register the PDF in `sources/README.md`, correct the test count, complete the repo map.

**4. MAJOR — The command-line tool has no input validation.**
Evidence: missing `"label"` → `KeyError: 'label'` (`tool/impermeable_check.py:369`); `"rectangle"` instead of `"rect"` → `KeyError: 'polygon'` (`:284`), a misleading message; a wrong path → `FileNotFoundError` traceback. Meanwhile the web page already has a careful `validate()` with readable messages (`tool/web/index.html` ≈ lines 1290–1325: "Surface 'X' needs a rect [x, y, width, depth] or a polygon…").
Why it matters: "use it with your own inputs" means hand-typed JSON; the first mistake a classmate makes ends in a stack trace.
Fix: port `validate()` to Python, run it before `check()`, print one line per problem and exit 2.

**5. MAJOR — Units and scale are unguarded; feet pass as metres.**
Evidence: `my-lot-feet.json` (33 × 122, frontage 33) → "Site area 4,026.00 m² … s.3.2.2.8 impermeable 35.77% PASS", no warning. The tool flags a lot under 306 m² (`impermeable_check.py:345`) but nothing above.
Why it matters: Vancouver drawings are routinely in feet; a confident PASS on a feet lot is exactly the "confident wrong answer" `docs/prompt-comparison.md:102` names as the expensive failure.
Fix: warn when site area > 1,500 m² or frontage > 30 m ("R1-1 lots are rarely this large — are these dimensions in feet?"); print "metres" next to every number in the input hint; optionally accept `"units": "ft"`.

**6. MAJOR — Material names are matched exactly, so a typo inverts the lesson.**
Evidence: `"permable pavers"` → "IMPERMEABLE — Not named in the by-law. Counted as impermeable; the Director of Planning may accept it as permeable." (`my-lot-typos2.json`; logic at `impermeable_check.py:244–246`). `"artificial turf"` likewise, though `"synthetic turf"` is known.
Why it matters: the verdict is right by accident and the explanation is the opposite of the one sentence the tool exists to teach.
Fix: an alias table (paver, pavers, permeable paving, interlocking pavers, unit pavers, artificial turf…); for anything still unknown, say "unrecognised material 'permable pavers' — did you mean 'permeable pavers'?" and flag it, rather than silently applying the Director clause.

**7. MAJOR — Wood with no conditions is reported with facts the user never gave.**
Evidence: a `"wood decking"` surface with no `spaced`/`on_grade` keys → "Counts as 'wood': boards not spaced, not installed on grade." (`impermeable_check.py:183–192`; pinned by `test_conditions_missing_defaults_to_impermeable`).
Why it matters: the conservative default is right; the sentence asserts a site condition that was simply not stated, which teaches the wrong thing about how the by-law reads.
Fix: distinguish absent from false — "spacing not stated, on-grade not stated: counted as 'wood' until confirmed" — and raise a flag, as river rock without a size already does (`:230–232`).

**8. MAJOR — The 3D does not earn its third dimension, by the author's own stated test.**
Evidence: `docs/regulation-shortlist.md:65–70`: "the Rhino output risks being a coloured plan with nothing to gain from being 3D. The intended answer is to extrude the design-storm volume … That is the part of the build that needs proving, and it is where W3 effort should go." Delivered: a stacked bar chart (`rhino_draw.py:346–425`) standing 44 m from a 7 m box whose height is "massing only, for legibility — not a claim" (`:53`). In `output/*_axon_*.png` the block labels slope in perspective at ~10 px, the 50% plane and its label are grey-on-grey and barely visible, and half the frame is empty. The web page's 2D dimension bars (screenshot, verdict panel) communicate the same stack better.
Why it matters: the brief wants a spatial output that does work; a crit panel will ask what the axon tells them that the bar does not, and the answer today is "nothing".
Fix: either (a) make the plan plus a drawn dimension bar the Rhino output and drop the axon, or (b) give the column one thing only 3D can carry — the runoff volume the impermeable area sheds in a 48 mm event, as the shortlist proposed, sized against the lot — and say in the README that this is what changed between W1 intent and W3 delivery.

**9. MAJOR — The drawing does not separate what is real from what is invented.**
Evidence: `rhino_draw.py:255–258` fills the entire lot polygon pale green as "lawn / planting"; `:262–267` draws front/rear yard lines labelled with s.3.2.2.4 and s.3.2.2.6 (clauses verified on R1-1 schedule p.12) but the "for orientation only" qualifier exists only as a code comment and in the README; in `output/*_plan_*.png` those labels are near-illegible light grey on grey. The title block says "3528 W 30th Ave / As designed" with no note that the design is synthetic. Lot line and design rectangles have the same line weight.
Why it matters: the README is careful ("The lot is real; the house, pad and patio were laid out for the example") but the sheet, which is what gets pinned up and screenshotted, is not.
Fix: a title-block line: "Lot: City parcel polygon 006141498. Design: illustrative. Yards shown for orientation; not checked." Draw unassigned ground white and label it "not counted", not as a lawn that nobody designed; dash or hatch the synthetic surfaces.

**10. MAJOR — `rhino_draw.py` deletes the user's own named views.**
Evidence: `rhino_draw.py:494–496` deletes every named view whose name starts with "Plan" or "Axon", in whatever document the script runs in. `README.md:120–122`: "Nothing else in the model is touched."
Why it matters: a classmate running it inside their studio model loses "Plan - Level 2". The claim of safety is the kind that must be exactly true.
Fix: prefix the views ("R1-1 Plan - …") and delete only those with that prefix.

**11. MAJOR (pedagogy) — The surprise is told, not experienced.**
Evidence: the web page opens on the answer, "75.55% FAIL", and the designer's expectation appears as a sentence ("If they counted as permeable, the total would be 60.21%", `index.html` `renderVerdict`); Rhino prints the same sentence under the column (`rhino_draw.py:420–425`).
Why it matters: the brief is "making design knowledge interactive". The one interaction that would make the lesson stick — holding the wrong belief and watching it fail — is not offered.
Fix: a toggle "Count pavers as permeable (what the name suggests)" that drops the bar/column to 60.21%, then snaps back and highlights the Section 2 passage; or open with a one-line "What do you expect this lot to score?" before revealing.

**12. MAJOR (usability) — There is no way to enter your own lot without writing JSON.**
Evidence: surfaces are editable in the schedule (`index.html` `renderSchedule`), but the lot outline has no fields; "Try another lot" is a JSON textarea (`index.html:226–236`). `README.md:169–186` ("Try your own example") sends a classmate to copy a JSON file and edit `EXAMPLES` in a Python script.
Why it matters: reviewers are told to "use each one with your own inputs". Most will not write coordinate pairs.
Fix: two fields — lot width and depth in metres (optional address) — that generate a rectangular outline; keep JSON for irregular lots.

**13. MINOR — No printable or copyable result.** "Copy this design" copies the input JSON only. The audience in `week-01/prompt-b-high-context/HANDOFF.md` is someone assembling a permit package; they need the verdict with clause citations on paper. Fix: a print stylesheet, or "Copy result as text" using the `report()` wording the Python tool already produces.

**14. MINOR — Negative dimensions are silently accepted on the command line.** `rect: [5, 5, -3, 4]` → 12.00 m² counted (shoelace `abs()` at `impermeable_check.py:259`); the web `validate()` rejects this, the CLI does not. Fix: same validation (see 4).

**15. MINOR — "Pervious concrete is impermeable" is a judgement presented as a reading.** `impermeable_check.py:127–137` and extract §2 treat pervious concrete/porous asphalt as named-impermeable with no Director note, while synthetic turf gets one. It is a defensible call, but it is exactly the kind of unlisted-material question the Director clause exists for, and the tool output does not flag it as a decision the way the extract does. Fix: add the same "confirm with the City" flag, or say in the reason "author's reading".

**16. MINOR — The repository carries a second, larger project and loose files.** Tracked on the remote: `buildings.py` (36 KB), `map/` with 49 MB of data, `stormwater.py` (63 KB), `assignment 1.qgz`, the Pages workflow. On disk: `r11_stage2.geojson` 146 MB, `r11_stormwater.geojson` 109 MB, a 25 MB CSV (ignored, but present), `test lot.3dm` 3.3 MB, a `.pages` file. `README.md:227–255` spends thirty lines on `stormwater.py`, which it calls "not the assignment tool". Fix: a `precursor/` folder with one README line, or a separate repository; remove the scratch files.

**17. MINOR — Author voice and review status are uncertain where the brief needs them certain.** `README.md:29`: the source interpretation is "Not yet reviewed by the author". `sources/r1-1-impermeable-extract.md:91`: "Extensions made while building, awaiting the author's confirmation"; `impermeable_check.py:130`: "The author's decision, 2026-09-24". Documents that refer to the author in the third person read as drafted for, not by, the student. `docs/prompt-comparison.md:28–31`: "To be completed before submission: the verbatim text of both prompts" — still absent; the third prompt approach was never done. Fix: the author reads the extract and turns "awaiting confirmation" into decided/rejected with a date; Purpose written in first person; add the prompts or delete the promise.

**18. MINOR — Evidence of revision exists in prose but not in version control.** The `FixesFromReview` tests (`test_impermeable_check.py:183–245`) and the dated correction in the extract (`:69–73`) are good practice, but the tool has zero commits, so none of it can be diffed. Fix: commit now; handle reviews as commits that close issues, as the brief prescribes.

### The five changes I would make first, in order

1. **Put the tool in the public repo and make it the front page.** Commit `tool/`, `examples/`, `output/`, the extract and the Section 2 PDF; replace the README on `main`; publish `tool/web/` or drop the map's Pages link. (Weaknesses 1, 18)
2. **Rewrite the top of the README to the brief's five headings**, in the author's voice, with the Source table (June 2026 for both documents, p.20/p.31), the corrected test count, and no "Week 3 of 4". (2, 3, 17)
3. **Make the command-line tool survive a classmate**: port `validate()` to Python; warn on feet-sized lots; alias common material spellings and say "unrecognised" when it is; stop asserting unstated deck conditions. (4, 5, 6, 7, 14)
4. **Make the drawing honest and make the 3D earn itself**: title-block line separating real lot from illustrative design; unassigned ground as "not counted"; either drop the column or let it carry a volume; stop deleting user views. (8, 9, 10)
5. **Let the user hold the wrong belief first**: a pavers-as-permeable toggle in the page and a lot width × depth input, so a reviewer can test their own lot and feel the 60 → 75 jump. (11, 12)

### What works

The choice of provision is exactly right for this brief: a three-line rule whose teachable content lives in a definition most designers would get backwards, and the project says so in one clean sentence on line 12. The operation is small, dependency-free and runs first time; the per-surface table that says what each surface counts as, why, and which passage that rests on is precisely how a rule should become an operation. The hand-worked example in the extract makes the code checkable without trusting it, and it checked. The web page's self-verification against the Python tool's own answers (133 classification cases, 74 lots, 2,957 formatted numbers — I confirmed it reports a full match on load) is a genuinely thoughtful piece of engineering for a four-week studio project, and the `export_web_data.py` pattern of never letting the page hold its own copy of a rule is worth teaching to the class. The plan drawing is legible and the decision to colour by by-law class rather than material — pavers come out graphite, like concrete — makes the argument visually in one glance. Source, interpretation and open questions are kept apart and dated; the limitations are candid; and the W1 comparison's lesson that a superseded-but-genuine 60% is harder to catch than an invented number is a real insight. Scope is right for four weeks — if anything the parity harness is over-built relative to the input path a classmate actually needs — and the precursors should simply leave the room.
