# W1 exercise — comparing prompt approaches to one task

**ARCH 540 Assignment 1 — W1 submission**
Kevin Jinn · work done 15 September 2026, written up 22 September 2026

**The task, held constant:** build a tool that checks whether a residential lot in
Vancouver exceeds the permitted amount of hard surface.

> **Completeness note.** The brief asks for three prompt approaches. Two were
> carried through to working tools and both are in `week-01/`. A third was not
> completed. This write-up covers the two that exist and does not pad the count.
> The gap is recorded here rather than disguised.

---

## The two approaches

| | A — low context | B — high context |
|---|---|---|
| Folder | `week-01/prompt-a-low-context/` | `week-01/prompt-b-high-context/` |
| Artefact | `lot-coverage-checker.jsx`, 13.7 KB | `r1-1-coverage-checker.jsx`, 42.5 KB |
| What the prompt supplied | The task, in plain language. No document, no district, no instruction to cite. | The district and its schedule, the Section 2 definitions, an instruction to cite a clause for every rule, and an instruction to separate what is read from a drawing from what is computed. |
| Named its source? | No. No by-law, section or date appears anywhere in the file. | Yes. Nine clause references held in a `RULES` object, each with reference and text. |
| Limit applied | `const LIMIT = 60;` | 75% impermeable (s. 3.2.2.8) **and** 50% building site coverage (s. 3.2.2.7), tested separately |
| Permeable pavers | Classified **permeable** | Classified **impermeable**, per the Section 2 definition |
| How it handles doubt | A closing line telling the user to go and confirm the limit themselves | A discrepancy panel, a per-row source field, an "uncertain" category counted conservatively, and a verdict that reports what would change if the uncertain surfaces were confirmed permeable |

> **To be completed before submission:** the verbatim text of both prompts, from
> the 15 September chat transcript. The comparison below is drawn from the two
> artefacts, which are the evidence actually in hand; the prompt wording should
> sit alongside it.

---

## What the difference produced

Approach A did not fail visibly. It produced a clean, working, plausible tool. It
is wrong in two specific ways, and neither announces itself.

**1. The limit is wrong, but not randomly wrong.**
`LIMIT = 60` is not invented. 60% was the real Vancouver figure under By-law No.
8202 (2000), which is in this repo as `sources/zoning-by-law-8202-2000-superseded.pdf`.
The RS district schedules that carried it were replaced by R1-1 on 17 October 2023,
and the current limit is 75%. Whether the 60 came from the model's own training
material or from that PDF being in the same conversation is not something the
artefact can settle, and it is left open rather than asserted.

The lesson is not "the model hallucinated". It is that a **superseded but genuine**
figure is far harder to catch than an invented one, because it survives a sanity
check.

**2. Permeable pavers are classified by their name.**
Approach A lists them as permeable, which is what the words say and what a
designer would expect. Section 2 of the by-law counts them as impermeable. A tool
that takes the plain meaning gets this backwards, and it matters — a paver
driveway is a common move for exactly the purpose of improving a site's drainage,
and under this by-law it buys nothing.

### The two errors do not cancel

A is stricter on the limit (60 rather than 75) and more lenient on classification
(pavers excluded). It would be convenient if that balanced out. It does not.

Worked check, on a 500 m² lot:

| Surface | Area |
|---|---|
| Building footprint | 240 m² |
| Concrete driveway | 20 m² |
| Permeable paver patio | 130 m² |
| Gravel path | 30 m² |
| Lawn | 80 m² |

| | Impermeable counted | Percentage | Limit | Verdict |
|---|---|---|---|---|
| Approach A | 260 m² | 52% | 60% | **Pass** |
| Approach B, s. 3.2.2.8 | 390 m² | 78% | 75% | **Fail** |
| Approach B, s. 3.2.2.7 | 240 m² building | 48% | 50% | Pass |

The same lot passes comfortably under A and fails under B. The difference is
entirely the 130 m² of pavers and the limit that was applied to them. A user of
approach A would have no way of noticing, because A never names a source they
could check it against.

---

## What this says about prompting

- **Supplying the document is what fixed the number.** Naming the role, or asking
  for more care, would not have. The 60 was a factual gap, and only a source
  closes a factual gap.
- **Asking for a citation per rule changes the artefact's structure, not just its
  text.** Approach B holds its rules in a `RULES` object with a reference attached
  to each, because the prompt asked for something that had to be carried through
  to the interface. A vaguer instruction to "cite sources" would not have produced
  that.
- **The quality most worth asking for was the ability to disagree with itself.**
  Approach B separates what it reads off a drawing from what it computes, and
  flags rows where the two differ by more than 5%. That came directly from a real
  user finding numbers that were "slightly different" from their own, and it is
  the single change that made the tool checkable rather than merely usable.
- **A confident wrong answer is the expensive failure mode.** Approach A is the
  more pleasant tool to use. Being easier to trust is what makes it worse.

---

## Carried forward

The 5%-discrepancy panel in approach B is the part of this exercise that survives
into the assignment proper. It is the mechanism by which a claim can be checked
against a source, which is what the brief asks the final tool to demonstrate.

Known limitations of approach B are recorded in
[`../week-01/prompt-b-high-context/HANDOFF.md`](../week-01/prompt-b-high-context/HANDOFF.md),
including the ones that are still unresolved: whether the s. 3.2 limits reach a
multiplex under s. 3.1, and whether a laneway house footprint counts toward the
site total.
