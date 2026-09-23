import { useState, useMemo, useRef } from "react";

// ------------------------------------------------------------------
// City of Vancouver Zoning and Development By-law No. 3575
// R1-1 District Schedule (June 2026 consolidation) and Section 2 Definitions.
// The RS schedules were replaced by R1-1 on October 17, 2023.
// ------------------------------------------------------------------

const RULES = {
  siteCoverage: { ref: "R1-1 s. 3.2.2.7", text: "Maximum site coverage for all buildings: 50% of the site area." },
  impermeable: { ref: "R1-1 s. 3.2.2.8", text: "Maximum area of impermeable materials: 75% of the site area." },
  includesBuildings: { ref: "R1-1 s. 4.2.2", text: "The maximum area of impermeable materials includes site coverage for all buildings." },
  impermDef: { ref: "Section 2, Impermeable Materials", text: "The projected area of the outside of the outermost walls of all buildings, including carports, entries, porches and verandahs, asphalt, concrete, brick, stone, permeable pavers, and wood." },
  permDef: { ref: "Section 2, Permeable Materials", text: "Materials including gravel, river rock less than 5 cm in size, wood chips, bark mulch, wood decking with spaced boards and other materials which, in the opinion of the Director of Planning, have fully permeable characteristics when placed or installed on grade with no associated layer of impermeable material, such as plastic sheeting, that would impede the movement of water directly to the soil below." },
  nonDwelling: { ref: "R1-1 s. 3.2.2.14", text: "The Director of Planning may increase the maximum area of impermeable materials for non-dwelling uses if there is a demonstrated need for increased paved or otherwise impermeable surface area and the Director considers the intent of the schedule and Council policies and guidelines." },
  hardship: { ref: "Section 2, Unnecessary Hardship", text: "Hardship that results from unique physical circumstances peculiar to the site; does not include mere inconvenience, preference for a more lenient standard or a more profitable use, or self-induced hardship." },
  laneway: { ref: "R1-1 s. 2.2.4", text: "Laneway house is regulated by Section 11 of the by-law; sections 3 and 4 of the R1-1 schedule do not apply to it." },
  multiplex: { ref: "R1-1 s. 3.1", text: "Multiple dwelling (3 to 8 units) is regulated by section 3.1, which sets building placement and separation rules but does not restate an impermeable-materials maximum." },
};

const USES = {
  "Single detached house": { section: "3.2", limits: true },
  "Single detached house with secondary suite": { section: "3.2", limits: true },
  "Duplex / duplex with secondary suite": { section: "3.2", limits: true },
  "Multiple dwelling, 3 to 8 units (multiplex)": { section: "3.1", limits: false },
};

const DISCREPANCY_TOLERANCE = 0.05; // 5%

const C = {
  sheet: "#F7F9FB", line: "#C9D3DC", ink: "#17263B", inkSoft: "#5B6B7F",
  building: "#1F2A3A", imperm: "#5F6E80", perm: "#4E8A5E", permSoft: "#E3F0E5",
  unsure: "#B98A2E", pass: "#2C7A4B", fail: "#B3392F", limit: "#C2410C", flag: "#FFF1E6",
};

const uid = () => Math.random().toString(36).slice(2, 9);
const num = (v) => (v === "" || v == null || isNaN(+v) ? null : +v);
const emptyRow = () => ({ id: uid(), label: "", material: "", category: "impermeable", basis: "", scheduleArea: null, computedArea: null, dims: "", source: "manual", manualArea: "" });

function readAsBase64(file) {
  return new Promise((res, rej) => {
    const r = new FileReader();
    r.onload = () => res(r.result.split(",")[1]);
    r.onerror = () => rej(new Error("Could not read file"));
    r.readAsDataURL(file);
  });
}

// The area that counts for a row, given the chosen method.
function effectiveArea(row, method) {
  if (row.manualArea !== "" && row.manualArea != null) return num(row.manualArea) ?? 0;
  const s = row.scheduleArea, c = row.computedArea;
  if (method === "trust") return s ?? c ?? 0;
  return c ?? s ?? 0; // recompute: prefer own calculation
}

function rowDiscrepancy(row) {
  const s = row.scheduleArea, c = row.computedArea;
  if (s == null || c == null || s === 0) return null;
  return (c - s) / s;
}

const SOURCE_LABEL = { schedule: "Drawing schedule", dimensions: "From dimensions", estimated: "Estimated", both: "Schedule + computed", manual: "Entered by hand" };

const Swatch = ({ color, hatched }) => (
  <span style={{ display: "inline-block", width: 10, height: 10, marginRight: 8, verticalAlign: "middle", background: hatched ? `repeating-linear-gradient(135deg, ${color} 0 3px, #fff 3px 6px)` : color, border: hatched || color === C.permSoft ? `1px solid ${hatched ? C.unsure : C.line}` : "none" }} />
);

export default function R11CoverageChecker() {
  const [use, setUse] = useState("Single detached house");
  const [method, setMethod] = useState("recompute"); // "trust" | "recompute"
  const [rows, setRows] = useState([]);
  const [siteArea, setSiteArea] = useState("");
  const [siteInfo, setSiteInfo] = useState(null); // {schedule, computed}
  const [scaleHint, setScaleHint] = useState("");
  const [fileName, setFileName] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState("");
  const [warnings, setWarnings] = useState([]);
  const [hasSchedule, setHasSchedule] = useState(null);
  const [showClauses, setShowClauses] = useState(false);
  const fileRef = useRef(null);

  const u = USES[use];

  async function analyzeDrawing(file) {
    setError(""); setAnalyzing(true); setWarnings([]);
    try {
      const b64 = await readAsBase64(file);
      const isPdf = file.type === "application/pdf";
      const mediaBlock = isPdf
        ? { type: "document", source: { type: "base64", media_type: "application/pdf", data: b64 } }
        : { type: "image", source: { type: "base64", media_type: file.type || "image/png", data: b64 } };

      const instructions = `You are checking a scaled residential site plan in Vancouver's R1-1 zone. Two separate jobs, keep them separate:

JOB 1, READ: if the sheet contains a materials/area schedule or table, copy each listed area exactly into "sch" (m², convert from ft² if needed). If there is no table, set "sch" null everywhere and "has_schedule" false.

JOB 2, COMPUTE: independently, for every ground surface (including surfaces inside setbacks), find its dimensions from dimension strings, lot dimensions or the scale bar${scaleHint ? ` (user note: "${scaleHint}")` : ""} and calculate the area yourself into "cmp". Put the dimensions you used in "dim" (e.g. "6.10 x 12.19" or "L-shape 4.2x3.0 + 2.1x1.5"). Do NOT copy the schedule value into "cmp". If you had no dimensions and had to judge by proportion, still give a number but set "src" to "estimated".

"src" is how the number was obtained: "both" (schedule value and your own computation), "schedule" (table only, could not compute), "dimensions" (computed from labelled dimensions, no table entry), "estimated" (proportional guess).

Classify by the by-law's Section 2 definitions:
BUILDING: outside of outermost walls of every building incl. carports, entries, porches, verandahs, garages, sheds, laneway houses.
IMPERMEABLE: asphalt; concrete; brick; stone; permeable pavers (count as impermeable); tight-board wood decks.
PERMEABLE: gravel; river rock under 5 cm; wood chips; bark mulch; spaced-board wood decking; lawn, planting, soil.
UNCERTAIN: unknown rock size, unknown board spacing, possible plastic sheeting or impermeable base, unidentifiable.

Respond with ONLY compact JSON, no markdown:
{"has_schedule":bool,"site_sch":number|null,"site_cmp":number|null,"scale_note":"max 12 words","s":[{"l":"label max 4 words","m":"material max 3 words","sch":number|null,"cmp":number|null,"dim":"max 30 chars","cat":"building"|"impermeable"|"permeable"|"uncertain","src":"both"|"schedule"|"dimensions"|"estimated","why":"max 6 words"}],"warn":["max 12 words"]}
At most 12 surfaces; merge like materials. Round to 0.1.`;

      const response = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model: "claude-sonnet-4-6", max_tokens: 1000, messages: [{ role: "user", content: [mediaBlock, { type: "text", text: instructions }] }] }),
      });
      const data = await response.json();
      if (data.error) throw new Error(data.error.message || "Analysis failed");
      const text = data.content.filter((b) => b.type === "text").map((b) => b.text).join("\n");
      const p = JSON.parse(text.replace(/```json|```/g, "").trim());

      setRows((p.s || []).map((s) => ({
        id: uid(), label: s.l || "", material: s.m || "",
        category: ["building", "impermeable", "permeable", "uncertain"].includes(s.cat) ? s.cat : "uncertain",
        basis: s.why || "", scheduleArea: num(s.sch), computedArea: num(s.cmp), dims: s.dim || "",
        source: ["both", "schedule", "dimensions", "estimated"].includes(s.src) ? s.src : (s.sch != null && s.cmp != null ? "both" : s.sch != null ? "schedule" : "estimated"),
        manualArea: "",
      })));
      setHasSchedule(!!p.has_schedule);
      setSiteInfo({ schedule: num(p.site_sch), computed: num(p.site_cmp) });
      const siteGuess = method === "trust" ? (num(p.site_sch) ?? num(p.site_cmp)) : (num(p.site_cmp) ?? num(p.site_sch));
      if (siteGuess && !siteArea) setSiteArea(String(Math.round(siteGuess * 10) / 10));
      const w = [...(p.warn || [])];
      if (p.scale_note) w.unshift(`Scale: ${p.scale_note}`);
      setWarnings(w);
    } catch (e) {
      setError(`The drawing could not be read: ${e.message}. Enter the surfaces manually below, or try a clearer export with a visible scale bar.`);
    } finally { setAnalyzing(false); }
  }

  function onFile(e) { const f = e.target.files?.[0]; if (!f) return; setFileName(f.name); analyzeDrawing(f); }

  const calc = useMemo(() => {
    const area = (r) => effectiveArea(r, method);
    const sum = (cat) => rows.filter((r) => r.category === cat).reduce((a, r) => a + area(r), 0);
    const building = sum("building"), hard = sum("impermeable"), perm = sum("permeable"), unsure = sum("uncertain");
    const drawn = building + hard + perm + unsure;
    const site = (num(siteArea) ?? 0) > 0 ? num(siteArea) : drawn;
    const unaccounted = Math.max(0, site - drawn);
    const pctSite = (a) => (site > 0 ? (a / site) * 100 : 0);

    const impermTotal = building + hard + unsure;
    const impermStrict = building + hard;
    const coveragePct = pctSite(building), impermPct = pctSite(impermTotal), impermStrictPct = pctSite(impermStrict);
    const passCoverage = site > 0 && coveragePct <= 50;
    const passImperm = site > 0 && impermPct <= 75;
    const passImpermIfUnsurePerm = site > 0 && impermStrictPct <= 75;
    const passes = passCoverage && passImperm;

    // Comparison: what would the other method give?
    const other = method === "trust" ? "recompute" : "trust";
    const otherSum = (cats) => rows.filter((r) => cats.includes(r.category)).reduce((a, r) => a + effectiveArea(r, other), 0);
    const otherImpermPct = pctSite(otherSum(["building", "impermeable", "uncertain"]));
    const otherCoveragePct = pctSite(otherSum(["building"]));

    const flagged = rows.map((r) => ({ r, d: rowDiscrepancy(r) })).filter((x) => x.d != null && Math.abs(x.d) > DISCREPANCY_TOLERANCE);
    const estimated = rows.filter((r) => r.source === "estimated" && (r.manualArea === "" || r.manualArea == null));
    const estimatedCounted = estimated.filter((r) => r.category !== "permeable").reduce((a, r) => a + area(r), 0);
    const marginImperm = 0.75 * site - impermTotal; // m² of headroom (negative if failing)
    const decidedByEstimate = site > 0 && estimatedCounted > 0 && Math.abs(marginImperm) < estimatedCounted;

    return { building, hard, perm, unsure, drawn, site, unaccounted, impermTotal, coveragePct, impermPct, impermStrictPct, passCoverage, passImperm, passImpermIfUnsurePerm, passes, otherImpermPct, otherCoveragePct, flagged, estimated, estimatedCounted, marginImperm, decidedByEstimate };
  }, [rows, siteArea, method]);

  const pctOf = (a) => (calc.site > 0 ? ((a / calc.site) * 100).toFixed(1) + "%" : "—");
  const m2 = (a) => (Math.round(a * 10) / 10).toLocaleString() + " m²";
  const fmt = (a) => (a == null ? "—" : (Math.round(a * 10) / 10).toLocaleString());
  const updateRow = (id, patch) => setRows((rs) => rs.map((r) => (r.id === id ? { ...r, ...patch } : r)));
  const hasData = rows.length > 0;
  const catColor = { building: C.building, impermeable: C.imperm, permeable: C.perm, uncertain: C.unsure };
  const anyCompared = rows.some((r) => r.scheduleArea != null && r.computedArea != null);

  const Bar = ({ value, extra, limit, fillColor }) => (
    <div style={{ position: "relative", height: 58 }}>
      <div style={{ position: "absolute", top: 18, left: 0, right: 0, height: 20, background: C.permSoft, border: `1px solid ${C.line}`, overflow: "hidden" }}>
        <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: `${Math.min(100, Math.max(0, value))}%`, background: fillColor, transition: "width .3s" }} />
        {extra > 0 && <div style={{ position: "absolute", left: `${Math.min(100, Math.max(0, value))}%`, top: 0, bottom: 0, width: `${Math.min(100 - Math.min(100, value), extra)}%`, background: `repeating-linear-gradient(135deg, ${C.unsure} 0 4px, #fff 4px 8px)`, transition: "width .3s" }} />}
      </div>
      <div style={{ position: "absolute", left: `${limit}%`, top: 0, bottom: 0, width: 0 }}>
        <div style={{ position: "absolute", top: 12, bottom: 12, left: -1, width: 2, background: C.limit }} />
        <div style={{ position: "absolute", top: 0, left: 6, fontSize: 12, color: C.limit, whiteSpace: "nowrap" }}>{limit}% maximum</div>
      </div>
      <div style={{ position: "absolute", bottom: 0, right: 0, fontSize: 12, color: C.inkSoft }}>100% of site</div>
    </div>
  );

  return (
    <div style={{ background: C.sheet, minHeight: "100vh", color: C.ink, fontFamily: "'Avenir Next', 'Segoe UI', 'Helvetica Neue', system-ui, sans-serif", fontVariantNumeric: "tabular-nums" }}>
      <style>{`
        .ck-input { width:100%; border:1px solid ${C.line}; background:#fff; padding:8px 10px; border-radius:4px; font:inherit; color:${C.ink}; }
        .ck-input:focus { outline:2px solid ${C.ink}; outline-offset:1px; }
        .ck-btn { border:1px solid ${C.ink}; background:${C.ink}; color:#fff; padding:9px 14px; border-radius:4px; font:inherit; font-weight:600; cursor:pointer; }
        .ck-btn:focus-visible { outline:2px solid ${C.limit}; outline-offset:2px; }
        .ck-btn.ghost { background:#fff; color:${C.ink}; }
        .ck-seg { display:flex; border:1px solid ${C.ink}; border-radius:4px; overflow:hidden; }
        .ck-seg button { flex:1; border:0; background:#fff; color:${C.ink}; padding:8px 6px; font:inherit; font-size:13px; cursor:pointer; }
        .ck-seg button[aria-pressed="true"] { background:${C.ink}; color:#fff; font-weight:600; }
        .ck-seg button:focus-visible { outline:2px solid ${C.limit}; outline-offset:-2px; }
        .ck-td { padding:8px 8px; border-bottom:1px solid ${C.line}; vertical-align:top; }
        .ck-td input, .ck-td select { border:1px solid transparent; background:transparent; font:inherit; color:${C.ink}; padding:3px 5px; border-radius:3px; width:100%; }
        .ck-td input:hover, .ck-td select:hover { border-color:${C.line}; background:#fff; }
        .ck-td input:focus, .ck-td select:focus { outline:2px solid ${C.ink}; background:#fff; }
        @media (prefers-reduced-motion: reduce) { * { transition:none !important; } }
        @media (max-width: 880px) { .ck-grid { grid-template-columns: 1fr !important; } }
      `}</style>

      <div style={{ maxWidth: 1240, margin: "0 auto", padding: "36px 24px 64px" }}>
        <header style={{ borderBottom: `2px solid ${C.ink}`, paddingBottom: 18, marginBottom: 28 }}>
          <h1 style={{ fontSize: 30, fontWeight: 600, margin: 0, letterSpacing: "-0.01em" }}>R1-1 site coverage and impermeability check</h1>
          <p style={{ margin: "8px 0 0", color: C.inkSoft, maxWidth: 760, lineHeight: 1.5 }}>
            Reads a scaled site plan, sorts each surface using the Section 2 definitions of the Vancouver Zoning and Development By-law, and tests it against the R1-1 District Schedule (June 2026 consolidation): buildings no more than 50% of the site, impermeable materials no more than 75%.
          </p>
        </header>

        <div className="ck-grid" style={{ display: "grid", gridTemplateColumns: "360px 1fr", gap: 32, alignItems: "start" }}>
          <aside style={{ display: "flex", flexDirection: "column", gap: 22 }}>
            <section>
              <label htmlFor="use" style={{ display: "block", fontWeight: 600, marginBottom: 6 }}>Proposed use</label>
              <select id="use" className="ck-input" value={use} onChange={(e) => setUse(e.target.value)}>
                {Object.keys(USES).map((k) => <option key={k}>{k}</option>)}
              </select>
              {u.limits ? (
                <p style={{ margin: "6px 0 0", fontSize: 13, color: C.inkSoft, lineHeight: 1.45 }}>Regulated under section 3.2: 50% building coverage (3.2.2.7) and 75% impermeable materials (3.2.2.8).</p>
              ) : (
                <p style={{ margin: "6px 0 0", fontSize: 13, color: C.unsure, lineHeight: 1.45 }}>Multiplexes are regulated under section 3.1, which does not restate an impermeable maximum. Percentages are calculated, but no pass/fail is given.</p>
              )}
            </section>

            <section>
              <label htmlFor="file" style={{ display: "block", fontWeight: 600, marginBottom: 6 }}>Scaled drawing</label>
              <input ref={fileRef} id="file" type="file" accept="image/png,image/jpeg,image/webp,image/gif,application/pdf" onChange={onFile} style={{ display: "none" }} />
              <button className="ck-btn" style={{ width: "100%" }} onClick={() => fileRef.current?.click()} disabled={analyzing}>
                {analyzing ? "Reading drawing…" : fileName ? "Replace drawing" : "Upload site plan (PDF or image)"}
              </button>
              {fileName && <p style={{ margin: "6px 0 0", fontSize: 13, color: C.inkSoft, wordBreak: "break-all" }}>{fileName}</p>}
              <label htmlFor="scale" style={{ display: "block", fontSize: 13, color: C.inkSoft, margin: "12px 0 4px" }}>Scale or lot dimensions, if the sheet doesn't show them</label>
              <input id="scale" className="ck-input" placeholder="e.g. 1:200 on A3, or lot 10.06 m × 37.19 m" value={scaleHint} onChange={(e) => setScaleHint(e.target.value)} />
            </section>

            <section>
              <div style={{ fontWeight: 600, marginBottom: 6 }}>Which areas to count</div>
              <div className="ck-seg" role="group" aria-label="Area source">
                <button aria-pressed={method === "recompute"} onClick={() => setMethod("recompute")}>Recompute and compare</button>
                <button aria-pressed={method === "trust"} onClick={() => setMethod("trust")}>Trust drawing schedule</button>
              </div>
              <p style={{ margin: "6px 0 0", fontSize: 13, color: C.inkSoft, lineHeight: 1.45 }}>
                {method === "recompute"
                  ? "Areas are calculated from the dimensions on the sheet. Any schedule on the drawing is read separately and shown alongside so you can see where the two differ."
                  : "Areas are taken from the schedule on the drawing where one exists. Computed values are still shown for comparison, and used only where the schedule has no entry."}
                {" "}Editing an area by hand overrides both.
              </p>
            </section>

            <section>
              <label htmlFor="site" style={{ display: "block", fontWeight: 600, marginBottom: 6 }}>Total site area (m²)</label>
              <input id="site" className="ck-input" type="number" min="0" step="0.1" placeholder={calc.drawn ? `Defaults to sum of surfaces: ${Math.round(calc.drawn)}` : "From survey or legal plan"} value={siteArea} onChange={(e) => setSiteArea(e.target.value)} />
              <p style={{ margin: "6px 0 0", fontSize: 13, color: C.inkSoft, lineHeight: 1.45 }}>
                Setback areas are part of the site and are included.
                {siteInfo && (siteInfo.schedule != null || siteInfo.computed != null) && (
                  <> Drawing: schedule {siteInfo.schedule != null ? m2(siteInfo.schedule) : "none"}, computed {siteInfo.computed != null ? m2(siteInfo.computed) : "—"}.</>
                )}
              </p>
            </section>

            <section style={{ borderTop: `1px solid ${C.line}`, paddingTop: 18, fontSize: 13, color: C.inkSoft, lineHeight: 1.5 }}>
              <p style={{ margin: 0 }}>Changed from the old RS rules: the impermeable limit is 75% rather than 60%; permeable pavers now count as impermeable; spaced-board decking is now permeable; the pre-2000 relaxation and the driveway exclusion no longer exist.</p>
            </section>
          </aside>

          <main style={{ display: "flex", flexDirection: "column", gap: 24 }}>
            {error && <div role="alert" style={{ border: `1px solid ${C.fail}`, background: "#FBEDEB", padding: "12px 14px", borderRadius: 4, fontSize: 14, lineHeight: 1.5 }}>{error}</div>}

            {/* Verdict */}
            <section style={{ background: "#fff", border: `1px solid ${C.line}`, borderRadius: 4, padding: 22 }}>
              {!hasData ? (
                <p style={{ margin: 0, color: C.inkSoft, lineHeight: 1.5 }}>Upload a scaled site plan to begin, or add surfaces by hand in the table below. List every surface on the lot, including buildings, so the percentages read against the whole site.</p>
              ) : (
                <>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 16, flexWrap: "wrap" }}>
                    <div style={{ fontSize: 24, fontWeight: 600, color: !u.limits ? C.inkSoft : calc.passes ? C.pass : C.fail }}>
                      {!u.limits ? "Coverage calculated, limit not assessed" : calc.passes ? "Passes both R1-1 tests" : !calc.passCoverage && !calc.passImperm ? "Fails building coverage and impermeability" : !calc.passCoverage ? "Fails building coverage" : "Fails impermeable materials"}
                    </div>
                    <div style={{ fontSize: 13, color: C.inkSoft }}>{use}, site {m2(calc.site)}, {method === "recompute" ? "computed areas" : "schedule areas"}</div>
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, marginTop: 20 }}>
                    <div>
                      <div style={{ fontSize: 13, color: C.inkSoft }}>Building coverage, {RULES.siteCoverage.ref}</div>
                      <div style={{ fontSize: 40, fontWeight: 600, lineHeight: 1.1, color: !u.limits ? C.ink : calc.passCoverage ? C.pass : C.fail }}>{calc.coveragePct.toFixed(1)}%</div>
                      {anyCompared && <div style={{ fontSize: 12, color: C.inkSoft }}>{method === "recompute" ? "Schedule would give" : "Computed would give"} {calc.otherCoveragePct.toFixed(1)}%</div>}
                      <Bar value={calc.coveragePct} extra={0} limit={50} fillColor={C.building} />
                    </div>
                    <div>
                      <div style={{ fontSize: 13, color: C.inkSoft }}>Impermeable materials, {RULES.impermeable.ref}</div>
                      <div style={{ fontSize: 40, fontWeight: 600, lineHeight: 1.1, color: !u.limits ? C.ink : calc.passImperm ? C.pass : C.fail }}>{calc.impermPct.toFixed(1)}%</div>
                      {anyCompared && <div style={{ fontSize: 12, color: C.inkSoft }}>{method === "recompute" ? "Schedule would give" : "Computed would give"} {calc.otherImpermPct.toFixed(1)}%</div>}
                      <Bar value={calc.impermStrictPct} extra={(calc.unsure / (calc.site || 1)) * 100} limit={75} fillColor={C.imperm} />
                    </div>
                  </div>

                  <div style={{ display: "flex", gap: 18, marginTop: 6, fontSize: 13, color: C.inkSoft, flexWrap: "wrap" }}>
                    <span><Swatch color={C.building} />Buildings</span>
                    <span><Swatch color={C.imperm} />Other impermeable</span>
                    <span><Swatch color={C.unsure} hatched />Uncertain, counted as impermeable</span>
                    <span><Swatch color={C.permSoft} />Permeable</span>
                  </div>

                  <div style={{ marginTop: 18, fontSize: 14, lineHeight: 1.55, borderTop: `1px solid ${C.line}`, paddingTop: 14 }}>
                    {u.limits && calc.passes && (
                      <p style={{ margin: 0 }}>Buildings cover no more than 50% of the site ({RULES.siteCoverage.ref}) and impermeable materials, which include all building coverage ({RULES.includesBuildings.ref}), do not exceed 75% ({RULES.impermeable.ref}). Headroom under the impermeable limit: {m2(calc.marginImperm)}.</p>
                    )}
                    {u.limits && !calc.passCoverage && (
                      <p style={{ margin: 0 }}>Building footprints exceed 50% of the site area, the maximum in {RULES.siteCoverage.ref}. Reduce building coverage by at least {m2(Math.max(0, calc.building - 0.5 * calc.site))}. Landscape changes cannot fix this test.</p>
                    )}
                    {u.limits && !calc.passImperm && (
                      <p style={{ margin: calc.passCoverage ? 0 : "8px 0 0" }}>Impermeable materials exceed 75% of the site area, the maximum in {RULES.impermeable.ref}. Reduce impermeable surfaces by at least {m2(-calc.marginImperm)}, for example with gravel, river rock under 5 cm, mulch or spaced-board decking (Section 2, Permeable Materials). Permeable pavers do not help; they are defined as impermeable.</p>
                    )}
                    {u.limits && calc.unsure > 0 && !calc.passImperm && calc.passImpermIfUnsurePerm && (
                      <p style={{ margin: "8px 0 0", color: C.unsure }}>The result turns on the uncertain surfaces: if confirmed permeable, coverage drops to {calc.impermStrictPct.toFixed(1)}% and passes.</p>
                    )}
                    {u.limits && calc.decidedByEstimate && (
                      <p style={{ margin: "8px 0 0", color: C.unsure }}>Caution: {m2(calc.estimatedCounted)} of counted area is estimated by proportion rather than calculated from dimensions, and that is larger than the {m2(Math.abs(calc.marginImperm))} margin to the 75% line. The result could flip either way; confirm those surfaces before relying on it.</p>
                    )}
                    {!u.limits && (
                      <p style={{ margin: 0 }}>{RULES.multiplex.text} Figures are shown for information; the 50% and 75% marks are the section 3.2 limits for houses and duplexes.</p>
                    )}
                    {calc.unaccounted > 0.5 && (
                      <p style={{ margin: "8px 0 0", color: C.inkSoft }}>{m2(calc.unaccounted)} of the site is not assigned to any surface and is treated as permeable.</p>
                    )}
                  </div>
                </>
              )}
            </section>

            {/* Where the numbers differ */}
            {hasData && anyCompared && (
              <section style={{ background: "#fff", border: `1px solid ${C.line}`, borderRadius: 4, padding: "16px 18px" }}>
                <div style={{ fontWeight: 600 }}>Where the drawing schedule and the computed areas differ</div>
                {calc.flagged.length === 0 ? (
                  <p style={{ margin: "6px 0 0", fontSize: 14, color: C.inkSoft, lineHeight: 1.5 }}>Every surface that appears in both agrees within {DISCREPANCY_TOLERANCE * 100}%. Small differences are rounding and how L-shapes were split.</p>
                ) : (
                  <>
                    <p style={{ margin: "6px 0 10px", fontSize: 14, color: C.inkSoft, lineHeight: 1.5 }}>{calc.flagged.length} surface{calc.flagged.length > 1 ? "s" : ""} differ by more than {DISCREPANCY_TOLERANCE * 100}%. Rows are shaded in the table below. Check the dimensions shown against your plan; the one that matches your takeoff is the one to keep, and you can type it into the area cell to lock it.</p>
                    <ul style={{ margin: 0, paddingLeft: 20, fontSize: 14, lineHeight: 1.6 }}>
                      {calc.flagged.map(({ r, d }) => (
                        <li key={r.id}><strong>{r.label || "Unnamed"}</strong> ({r.material}): schedule {fmt(r.scheduleArea)} m², computed {fmt(r.computedArea)} m² from {r.dims || "unstated dimensions"}, a difference of {d > 0 ? "+" : ""}{(d * 100).toFixed(0)}%.</li>
                      ))}
                    </ul>
                  </>
                )}
                {hasSchedule === false && <p style={{ margin: "8px 0 0", fontSize: 13, color: C.inkSoft }}>No area schedule was found on this sheet; all figures are computed.</p>}
              </section>
            )}

            {warnings.length > 0 && (
              <ul style={{ margin: 0, padding: "12px 16px 12px 32px", background: "#FFF8E8", border: "1px solid #EBD9A8", borderRadius: 4, fontSize: 13, lineHeight: 1.5 }}>
                {warnings.map((w, i) => <li key={i}>{w}</li>)}
              </ul>
            )}

            {/* Summary table */}
            <section style={{ background: "#fff", border: `1px solid ${C.line}`, borderRadius: 4, overflow: "hidden" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
                <thead>
                  <tr style={{ background: C.sheet }}>
                    <th className="ck-td" style={{ textAlign: "left", fontWeight: 600 }}>Category</th>
                    <th className="ck-td" style={{ textAlign: "right", fontWeight: 600 }}>Area</th>
                    <th className="ck-td" style={{ textAlign: "right", fontWeight: 600 }}>Share of site</th>
                    <th className="ck-td" style={{ textAlign: "left", fontWeight: 600 }}>Reference</th>
                  </tr>
                </thead>
                <tbody>
                  <tr><td className="ck-td">Total site area</td><td className="ck-td" style={{ textAlign: "right" }}>{m2(calc.site)}</td><td className="ck-td" style={{ textAlign: "right" }}>100%</td><td className="ck-td" style={{ color: C.inkSoft }}>Denominator for 3.2.2.7 and 3.2.2.8</td></tr>
                  <tr style={{ fontWeight: 600 }}><td className="ck-td"><Swatch color={C.building} />Building coverage</td><td className="ck-td" style={{ textAlign: "right" }}>{m2(calc.building)}</td><td className="ck-td" style={{ textAlign: "right", color: !u.limits ? C.ink : calc.passCoverage ? C.pass : C.fail }}>{calc.coveragePct.toFixed(1)}%</td><td className="ck-td" style={{ color: C.inkSoft, fontWeight: 400 }}>{RULES.siteCoverage.ref}: max 50%</td></tr>
                  <tr><td className="ck-td"><Swatch color={C.imperm} />Other impermeable materials</td><td className="ck-td" style={{ textAlign: "right" }}>{m2(calc.hard)}</td><td className="ck-td" style={{ textAlign: "right" }}>{pctOf(calc.hard)}</td><td className="ck-td" style={{ color: C.inkSoft }}>{RULES.impermDef.ref}</td></tr>
                  {calc.unsure > 0 && <tr><td className="ck-td"><Swatch color={C.unsure} hatched />Uncertain, counted as impermeable</td><td className="ck-td" style={{ textAlign: "right" }}>{m2(calc.unsure)}</td><td className="ck-td" style={{ textAlign: "right" }}>{pctOf(calc.unsure)}</td><td className="ck-td" style={{ color: C.inkSoft }}>{RULES.permDef.ref} (not confirmed)</td></tr>}
                  <tr style={{ fontWeight: 600 }}><td className="ck-td">Impermeable materials, total</td><td className="ck-td" style={{ textAlign: "right" }}>{m2(calc.impermTotal)}</td><td className="ck-td" style={{ textAlign: "right", color: !u.limits ? C.ink : calc.passImperm ? C.pass : C.fail }}>{calc.impermPct.toFixed(1)}%</td><td className="ck-td" style={{ color: C.inkSoft, fontWeight: 400 }}>{RULES.impermeable.ref}: max 75%; includes buildings per {RULES.includesBuildings.ref}</td></tr>
                  <tr><td className="ck-td"><Swatch color={C.permSoft} />Permeable materials</td><td className="ck-td" style={{ textAlign: "right" }}>{m2(calc.perm)}</td><td className="ck-td" style={{ textAlign: "right" }}>{pctOf(calc.perm)}</td><td className="ck-td" style={{ color: C.inkSoft }}>{RULES.permDef.ref}</td></tr>
                  {calc.unaccounted > 0.5 && <tr><td className="ck-td" style={{ color: C.inkSoft }}>Unassigned site area</td><td className="ck-td" style={{ textAlign: "right", color: C.inkSoft }}>{m2(calc.unaccounted)}</td><td className="ck-td" style={{ textAlign: "right", color: C.inkSoft }}>{pctOf(calc.unaccounted)}</td><td className="ck-td" style={{ color: C.inkSoft }}>—</td></tr>}
                  <tr style={{ borderTop: `2px solid ${C.ink}` }}>
                    <td className="ck-td" style={{ borderBottom: 0 }}>Result</td>
                    <td className="ck-td" colSpan={2} style={{ borderBottom: 0, textAlign: "right", fontWeight: 600, color: !u.limits ? C.inkSoft : calc.passes ? C.pass : C.fail }}>{!hasData ? "—" : !u.limits ? "Not assessed" : calc.passes ? "Pass" : "Fail"}</td>
                    <td className="ck-td" style={{ borderBottom: 0, color: C.inkSoft }}>{hasData && u.limits ? `Coverage ${calc.passCoverage ? "pass" : "fail"}, impermeability ${calc.passImperm ? "pass" : "fail"}` : hasData ? RULES.multiplex.ref : ""}</td>
                  </tr>
                </tbody>
              </table>
            </section>

            {/* Surfaces */}
            <section style={{ background: "#fff", border: `1px solid ${C.line}`, borderRadius: 4, overflow: "hidden" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "14px 16px", borderBottom: `1px solid ${C.line}` }}>
                <div>
                  <div style={{ fontWeight: 600 }}>Surfaces read from the drawing</div>
                  <div style={{ fontSize: 13, color: C.inkSoft }}>The bold column is what counts. Type a value into it to override both sources.</div>
                </div>
                <button className="ck-btn ghost" onClick={() => setRows((r) => [...r, emptyRow()])}>Add surface</button>
              </div>
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13, minWidth: 900 }}>
                  <thead>
                    <tr style={{ background: C.sheet }}>
                      <th className="ck-td" style={{ textAlign: "left", fontWeight: 600 }}>Surface</th>
                      <th className="ck-td" style={{ textAlign: "left", fontWeight: 600 }}>Material</th>
                      <th className="ck-td" style={{ textAlign: "right", fontWeight: 600, width: 84 }}>Schedule m²</th>
                      <th className="ck-td" style={{ textAlign: "right", fontWeight: 600, width: 84 }}>Computed m²</th>
                      <th className="ck-td" style={{ textAlign: "left", fontWeight: 600, width: 130 }}>Dimensions used</th>
                      <th className="ck-td" style={{ textAlign: "right", fontWeight: 600, width: 60 }}>Δ</th>
                      <th className="ck-td" style={{ textAlign: "right", fontWeight: 600, width: 92 }}>Counted m²</th>
                      <th className="ck-td" style={{ textAlign: "right", fontWeight: 600, width: 64 }}>Share</th>
                      <th className="ck-td" style={{ textAlign: "left", fontWeight: 600, width: 118 }}>Category</th>
                      <th className="ck-td" style={{ textAlign: "left", fontWeight: 600, width: 128 }}>Source</th>
                      <th className="ck-td" style={{ width: 32 }}></th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.length === 0 && <tr><td className="ck-td" colSpan={11} style={{ color: C.inkSoft, textAlign: "center", padding: 28 }}>No surfaces yet. Upload a drawing or add a surface.</td></tr>}
                    {rows.map((r) => {
                      const d = rowDiscrepancy(r);
                      const flagged = d != null && Math.abs(d) > DISCREPANCY_TOLERANCE;
                      const counted = effectiveArea(r, method);
                      const overridden = r.manualArea !== "" && r.manualArea != null;
                      const usingSchedule = !overridden && (method === "trust" ? r.scheduleArea != null : r.computedArea == null && r.scheduleArea != null);
                      return (
                        <tr key={r.id} style={{ background: flagged ? C.flag : "transparent" }}>
                          <td className="ck-td"><input aria-label="Surface" value={r.label} onChange={(e) => updateRow(r.id, { label: e.target.value })} placeholder="e.g. Front walk" /></td>
                          <td className="ck-td"><input aria-label="Material" value={r.material} onChange={(e) => updateRow(r.id, { material: e.target.value })} placeholder="e.g. Concrete" /></td>
                          <td className="ck-td" style={{ textAlign: "right", color: usingSchedule ? C.ink : C.inkSoft, fontWeight: usingSchedule ? 600 : 400 }}>{fmt(r.scheduleArea)}</td>
                          <td className="ck-td" style={{ textAlign: "right", color: !overridden && !usingSchedule && r.computedArea != null ? C.ink : C.inkSoft, fontWeight: !overridden && !usingSchedule && r.computedArea != null ? 600 : 400 }}>{fmt(r.computedArea)}</td>
                          <td className="ck-td" style={{ color: C.inkSoft, fontSize: 12 }}>{r.dims || "—"}</td>
                          <td className="ck-td" style={{ textAlign: "right", color: flagged ? C.limit : C.inkSoft, fontWeight: flagged ? 600 : 400 }}>{d == null ? "—" : `${d > 0 ? "+" : ""}${(d * 100).toFixed(0)}%`}</td>
                          <td className="ck-td"><input aria-label="Counted area in square metres" type="number" min="0" step="0.1" value={overridden ? r.manualArea : ""} placeholder={fmt(counted)} onChange={(e) => updateRow(r.id, { manualArea: e.target.value })} style={{ textAlign: "right", fontWeight: 600, color: C.ink }} /></td>
                          <td className="ck-td" style={{ textAlign: "right", color: C.inkSoft }}>{pctOf(counted)}</td>
                          <td className="ck-td">
                            <select aria-label="Category" value={r.category} onChange={(e) => updateRow(r.id, { category: e.target.value })} style={{ color: catColor[r.category], fontWeight: 600 }}>
                              <option value="building">Building</option>
                              <option value="impermeable">Impermeable</option>
                              <option value="permeable">Permeable</option>
                              <option value="uncertain">Uncertain</option>
                            </select>
                          </td>
                          <td className="ck-td" style={{ fontSize: 12, color: overridden ? C.ink : r.source === "estimated" ? C.unsure : C.inkSoft, fontWeight: r.source === "estimated" && !overridden ? 600 : 400 }}>
                            {overridden ? SOURCE_LABEL.manual : SOURCE_LABEL[r.source] || "—"}
                            {r.basis && <div style={{ color: C.inkSoft, fontWeight: 400 }}>{r.basis}</div>}
                          </td>
                          <td className="ck-td"><button aria-label="Remove surface" onClick={() => setRows((rs) => rs.filter((x) => x.id !== r.id))} style={{ border: 0, background: "transparent", color: C.inkSoft, cursor: "pointer", fontSize: 18, lineHeight: 1 }}>×</button></td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <div style={{ padding: "12px 16px", fontSize: 13, color: C.inkSoft, lineHeight: 1.55, borderTop: `1px solid ${C.line}` }}>
                <strong style={{ color: C.ink }}>How the numbers are obtained.</strong> "Schedule" is copied from any area table drawn on your sheet. "Computed" is the reader's own calculation from dimension strings, lot dimensions or the scale bar, never copied from the table; the dimensions it used are shown so you can check its arithmetic. "Estimated" means it had no dimensions and judged the area by proportion, which can be off by 10–20% or more on irregular shapes. Rows shaded orange differ between the two sources by more than {DISCREPANCY_TOLERANCE * 100}%. Classification follows the Section 2 definitions; anything unconfirmed is flagged uncertain and counted against you. Laneway houses are governed by Section 11 ({RULES.laneway.ref}); their footprint is counted as building here, the conservative reading of {RULES.includesBuildings.ref}.
              </div>
            </section>

            <section style={{ border: `1px solid ${C.line}`, borderRadius: 4, background: "#fff" }}>
              <button className="ck-btn ghost" style={{ width: "100%", textAlign: "left", border: 0, borderRadius: 4, display: "flex", justifyContent: "space-between" }} onClick={() => setShowClauses((s) => !s)} aria-expanded={showClauses}>
                <span>By-law text applied</span><span>{showClauses ? "Hide" : "Show"}</span>
              </button>
              {showClauses && (
                <div style={{ padding: "4px 16px 18px", fontSize: 14, lineHeight: 1.6 }}>
                  {[RULES.siteCoverage, RULES.impermeable, RULES.includesBuildings, RULES.impermDef, RULES.permDef, RULES.nonDwelling, RULES.hardship, RULES.laneway, RULES.multiplex].map((r) => (
                    <p key={r.ref} style={{ margin: "10px 0" }}><strong>{r.ref}.</strong> {r.text}</p>
                  ))}
                  <p style={{ margin: "10px 0 0", color: C.inkSoft, fontSize: 13 }}>Source: City of Vancouver Zoning and Development By-law No. 3575, R1-1 District Schedule and Section 2 Definitions, June 2026 consolidations (bylaws.vancouver.ca). This is a pre-check only and does not replace review by the Development and Building Services Centre.</p>
                </div>
              )}
            </section>
          </main>
        </div>
      </div>
    </div>
  );
}
