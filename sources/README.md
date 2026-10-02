# Source register

Every document this project cites, with the version statement printed on the
document itself, where it came from, and when it was retrieved. The brief asks
for the original jurisdiction, intended audience, version and conditions to stay
visible, so this register is the place that holds them.

All documents are City of Vancouver publications unless noted.

| File / document | Version statement on the document | Authority | Retrieved | From |
|---|---|---|---|---|
| `zoning-by-law-district-schedule-r1-1.pdf` | "City of Vancouver June 2026", 17 pp. | By-law (Zoning and Development By-law No. 3575, district schedule) | 2026-09-21 | `bylaws.vancouver.ca/zoning/zoning-by-law-district-schedule-r1-1.pdf` |
| `zoning-by-law-section-2.pdf` | "City of Vancouver June 2026", 50 pp. | By-law (Zoning and Development By-law No. 3575, Section 2 Definitions) | 2026-10-01 | `bylaws.vancouver.ca/zoning/zoning-by-law-section-2.pdf`, downloaded in a browser. Until 2026-10-02 the tool cited a November 2025 copy of this document; the wording of the four definitions used is identical in both, two page numbers were not (see `r1-1-impermeable-extract.md`). |
| `zoning-by-law-13670-2023-amendments.pdf` | By-law No. 13670, "enacted by Council this 26th day of April, 2023", 4 pp. | By-law (amending No. 3575) | 2026-10-02 | `bylaws.vancouver.ca/consolidated/13670.PDF` via the Internet Archive raw-file URL (see retrieval note). s.2(a) adds "permeable pavers" to the definition of Impermeable Materials. |
| RM-7A Guidelines | "April 2025", 25 pp. | **Guidelines, not a by-law.** Quoted only for the City's stated reason: "since most permeable pavers lose their permeability over time, parking areas with permeable pavers are counted as impermeable surface" (pp.16–17). | 2026-10-02 | `guidelines.vancouver.ca/guidelines-rm-7a.pdf` via the Internet Archive; not stored (2 MB) |
| Policy Report RTS 00291, "Referral to Public Hearing - RS zoning schedules to limit impervious surface" | 20 March 2000 (Council 4 April 2000) | Council report, **not a by-law**. The origin of the impermeability regulations and of the Permeable Materials wording; pavers not yet named. | 2026-10-02 | `council.vancouver.ca/000516/ph3.htm` via the Internet Archive; not stored |
| `protection-of-trees-bylaw-9958.pdf` | "Consolidated for convenience only to December 9, 2025"; "amended to include By-law No. 14546 effective January 1, 2026", 35 pp. | By-law | 2026-09-22 | `bylaws.vancouver.ca/9958c.pdf` (see retrieval note below) |
| Engineering Design Manual | "City of Vancouver Engineering Design Manual \| 2026", 420 pp. Section 9.3 Urban Forest begins p. 365. | Engineering guidance, **not** a by-law | 2026-09-22 | `vancouver.ca/files/cov/engineering-design-manual.pdf` — not stored here (8 MB); see `tree-bylaw-9958-schedule-a.md` sibling note |
| `2025-vbbl-book-II-insert-pages.pdf` | Vancouver Building By-law 2025, Book II insert pages | By-law | 2026-09-21 | City of Vancouver. Held for the small-site detention pathway; not currently cited in a claim. |
| `zoning-by-law-8202-2000-superseded.pdf` | By-law No. 8202, passed 30 May 2000, amending By-law No. 3575 | **Superseded. Do not use for a current claim.** | supplied by author | Held only as evidence for the W1 prompt comparison, where it explains where a wrong 60% figure came from. |
| City of Vancouver open data: property parcel polygons; zoning districts | portal records, "updated weekly" | **Data, not a by-law.** Site outlines and areas (UTM 10N). The parcel polygon is not a legal survey. | 2026-09-21 | `opendata.vancouver.ca`, cached by `stormwater.py` |
| City of Vancouver open data: building footprints 2015; building footprints 2009 (LiDAR heights) | 2015 orthophoto trace ("outermost exterior outline", roof edge); 2009 LiDAR | **Data, not a by-law.** Roof areas on the map; heights for the Rhino drawing only. A 0.45 m eave allowance is taken off for the by-law test (see the extract §2). | 2026-09-25 | `opendata.vancouver.ca`, cached by `buildings.py` |
| Rain City Strategy (2019) | Council policy | **Strategy / policy, not a by-law.** Its 48 mm daily design standard is the storm card's context only. | — | `vancouver.ca` |

## Retrieval note — please read before repeating this

`bylaws.vancouver.ca` and `vancouver.ca/files` sit behind Cloudflare and return
HTTP 403 to command-line tools and automated fetchers. They open normally in an
ordinary browser.

The tree by-law and the Engineering Design Manual in this register were retrieved
on 2026-09-22 through the Internet Archive's raw-file URL form
(`https://web.archive.org/web/2026id_/<city url>`), which serves the City's own
PDF. The version statements in the table above are the ones printed inside those
files, not the archive's snapshot date.

**This is a real limitation and it is recorded rather than hidden.** An archived
copy can lag the live document. Before either alternative source is promoted from
the shortlist into actual use, open the City URL in a browser and confirm the
consolidation date still matches the table above.

The R1-1 District Schedule and Section 2 Definitions were downloaded directly in a
browser and are not subject to this caveat.

## Authority levels, kept distinct

The brief warns against flattening these, and this project has already been caught
by it once:

- **By-law** — Zoning and Development By-law No. 3575 (including the R1-1 District
  Schedule and Section 2), Protection of Trees By-law No. 9958, Vancouver Building
  By-law. Legally binding.
- **Engineering guidance** — Engineering Design Manual. Binding on City works and
  on what the City will accept, but not a by-law provision.
- **Strategy / policy** — Rain City Strategy. A statement of intent. Its 48 mm
  daily design standard is **not** a requirement for an R1-1 lot: everything in
  R1-1 sits within 1.0 FSR and therefore takes the City's small-site detention-tank
  pathway instead. The earlier "retain 24 mm / treat 48 mm" rule left the Zoning
  and Development By-law on 1 January 2024.

Any gap this project reports against 48 mm is a gap against an aspiration, and
must be described that way. It is not a finding that anyone is breaking a rule.
