import { useState, useMemo } from "react";

const LIMIT = 60; // max impervious % of total site area

const INK = "#1B2A3A";
const PAPER = "#EEF2F5";
const CONCRETE = "#5A6069";
const RAIN = "#2F6F9F";
const PASS = "#2E7D5B";
const FAIL = "#B23A3A";
const MUTED = "#6B7480";

const PRESETS = [
  { label: "Principal building roof", type: "impervious" },
  { label: "Garage / laneway house roof", type: "impervious" },
  { label: "Concrete driveway", type: "impervious" },
  { label: "Concrete walkway", type: "impervious" },
  { label: "Patio / deck (solid)", type: "impervious" },
  { label: "Permeable pavers", type: "permeable" },
  { label: "Gravel", type: "permeable" },
  { label: "Lawn / planting", type: "permeable" },
  { label: "Other", type: "impervious" },
];

let nextId = 1;
const row = (label, type, area = "") => ({ id: nextId++, label, type, area });

const INITIAL = [
  row("Principal building roof", "impervious"),
  row("Concrete driveway", "impervious"),
  row("Concrete walkway", "impervious"),
  row("Lawn / planting", "permeable"),
];

const num = (v) => {
  const n = parseFloat(v);
  return Number.isFinite(n) && n >= 0 ? n : 0;
};
const fmt = (n, d = 1) =>
  n.toLocaleString(undefined, { maximumFractionDigits: d, minimumFractionDigits: 0 });

export default function LotCoverageChecker() {
  const [unit, setUnit] = useState("m²");
  const [lotArea, setLotArea] = useState("");
  const [rows, setRows] = useState(INITIAL);

  const lot = num(lotArea);

  const calc = useMemo(() => {
    const imp = rows.filter((r) => r.type === "impervious").reduce((s, r) => s + num(r.area), 0);
    const perm = rows.filter((r) => r.type === "permeable").reduce((s, r) => s + num(r.area), 0);
    const listed = imp + perm;
    const unassigned = lot - listed;
    const impPct = lot > 0 ? (imp / lot) * 100 : 0;
    const permPct = lot > 0 ? (perm / lot) * 100 : 0;
    const allowance = lot * (LIMIT / 100);
    return {
      imp, perm, listed, unassigned, impPct, permPct, allowance,
      over: imp - allowance,
      pass: lot > 0 && impPct <= LIMIT,
      ready: lot > 0 && listed > 0,
      overfilled: lot > 0 && listed > lot + 1e-9,
    };
  }, [rows, lot]);

  const update = (id, patch) =>
    setRows((rs) => rs.map((r) => (r.id === id ? { ...r, ...patch } : r)));
  const remove = (id) => setRows((rs) => rs.filter((r) => r.id !== id));
  const add = () => setRows((rs) => [...rs, row("Other", "impervious")]);
  const pickPreset = (id, label) => {
    const p = PRESETS.find((x) => x.label === label);
    update(id, { label, type: p ? p.type : "impervious" });
  };

  const inputStyle = {
    background: "#fff",
    border: `1px solid #C7D0DA`,
    borderRadius: 4,
    padding: "8px 10px",
    color: INK,
    fontSize: 15,
    width: "100%",
    outline: "none",
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: PAPER,
        color: INK,
        fontFamily: 'ui-sans-serif, "Helvetica Neue", Helvetica, Arial, sans-serif',
        padding: "28px 20px 48px",
      }}
    >
      <style>{`
        .lc-input:focus { border-color: ${RAIN} !important; box-shadow: 0 0 0 3px rgba(47,111,159,.18); }
        .lc-btn:focus-visible { outline: 2px solid ${RAIN}; outline-offset: 2px; }
        @media (prefers-reduced-motion: no-preference) { .lc-bar rect { transition: width .35s ease, x .35s ease; } }
      `}</style>

      <div style={{ maxWidth: 820, margin: "0 auto" }}>
        <header style={{ marginBottom: 28 }}>
          <h1 style={{ fontSize: 30, fontWeight: 600, margin: 0, letterSpacing: "-0.01em" }}>
            Lot coverage check
          </h1>
          <p style={{ margin: "8px 0 0", color: MUTED, fontSize: 15, maxWidth: 560, lineHeight: 1.5 }}>
            Vancouver lot. Enter the site area and each surface from the plan. Impervious surfaces may cover at most {LIMIT}% of the total site area.
          </p>
        </header>

        {/* Site area */}
        <section style={{ marginBottom: 24 }}>
          <label htmlFor="lot" style={{ display: "block", fontSize: 14, fontWeight: 600, marginBottom: 6 }}>
            Total site area
          </label>
          <div style={{ display: "flex", gap: 8, maxWidth: 360 }}>
            <input
              id="lot"
              className="lc-input"
              type="number"
              min="0"
              inputMode="decimal"
              placeholder="e.g. 372"
              value={lotArea}
              onChange={(e) => setLotArea(e.target.value)}
              style={inputStyle}
            />
            <div style={{ display: "flex", border: "1px solid #C7D0DA", borderRadius: 4, overflow: "hidden" }}>
              {["m²", "ft²"].map((u) => (
                <button
                  key={u}
                  className="lc-btn"
                  onClick={() => setUnit(u)}
                  aria-pressed={unit === u}
                  style={{
                    padding: "0 14px",
                    border: "none",
                    background: unit === u ? INK : "#fff",
                    color: unit === u ? "#fff" : INK,
                    fontSize: 14,
                    cursor: "pointer",
                  }}
                >
                  {u}
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* Surfaces */}
        <section style={{ marginBottom: 28 }}>
          <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 8 }}>
            <h2 style={{ fontSize: 16, fontWeight: 600, margin: 0 }}>Surfaces on the plan</h2>
            <span style={{ fontSize: 13, color: MUTED }}>Areas in {unit}</span>
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            {rows.map((r) => (
              <div
                key={r.id}
                style={{
                  display: "grid",
                  gridTemplateColumns: "minmax(0,1.6fr) minmax(0,1fr) minmax(0,.8fr) 36px",
                  gap: 8,
                  alignItems: "center",
                  padding: "8px 10px",
                  background: "#fff",
                  borderLeft: `6px solid ${r.type === "impervious" ? CONCRETE : RAIN}`,
                  borderRadius: 4,
                }}
              >
                <select
                  className="lc-input"
                  aria-label="Surface"
                  value={r.label}
                  onChange={(e) => pickPreset(r.id, e.target.value)}
                  style={{ ...inputStyle, border: "1px solid #E1E6EC" }}
                >
                  {PRESETS.map((p) => (
                    <option key={p.label} value={p.label}>{p.label}</option>
                  ))}
                </select>
                <select
                  className="lc-input"
                  aria-label="Surface type"
                  value={r.type}
                  onChange={(e) => update(r.id, { type: e.target.value })}
                  style={{ ...inputStyle, border: "1px solid #E1E6EC" }}
                >
                  <option value="impervious">Impervious</option>
                  <option value="permeable">Permeable</option>
                </select>
                <input
                  className="lc-input"
                  aria-label={`Area of ${r.label}`}
                  type="number"
                  min="0"
                  inputMode="decimal"
                  placeholder="0"
                  value={r.area}
                  onChange={(e) => update(r.id, { area: e.target.value })}
                  style={{ ...inputStyle, border: "1px solid #E1E6EC", textAlign: "right" }}
                />
                <button
                  className="lc-btn"
                  onClick={() => remove(r.id)}
                  aria-label={`Remove ${r.label}`}
                  title="Remove"
                  style={{ border: "none", background: "transparent", color: MUTED, fontSize: 20, cursor: "pointer", lineHeight: 1 }}
                >
                  ×
                </button>
              </div>
            ))}
          </div>

          <button
            className="lc-btn"
            onClick={add}
            style={{
              marginTop: 10,
              background: "transparent",
              border: `1px dashed ${MUTED}`,
              color: INK,
              padding: "8px 14px",
              borderRadius: 4,
              fontSize: 14,
              cursor: "pointer",
            }}
          >
            Add surface
          </button>
        </section>

        {/* Result */}
        <section
          aria-live="polite"
          style={{
            background: "#fff",
            borderRadius: 6,
            padding: "20px 22px",
            borderTop: `6px solid ${!calc.ready ? "#C7D0DA" : calc.pass ? PASS : FAIL}`,
          }}
        >
          {!calc.ready ? (
            <p style={{ margin: 0, color: MUTED, fontSize: 15 }}>
              Enter the site area and at least one surface area to run the check.
            </p>
          ) : (
            <>
              <div style={{ display: "flex", alignItems: "baseline", gap: 14, flexWrap: "wrap", marginBottom: 14 }}>
                <span style={{ fontSize: 26, fontWeight: 700, color: calc.pass ? PASS : FAIL }}>
                  {calc.pass ? "Passes" : "Fails"}
                </span>
                <span style={{ fontSize: 15, color: INK }}>
                  Impervious {fmt(calc.impPct)}% of site · limit {LIMIT}%
                </span>
              </div>

              <CoverageBar impPct={calc.impPct} permPct={calc.permPct} />

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
                  gap: 14,
                  marginTop: 18,
                  fontSize: 14,
                }}
              >
                <Stat swatch={CONCRETE} hatch label="Impervious" value={`${fmt(calc.imp)} ${unit}`} sub={`${fmt(calc.impPct)}%`} />
                <Stat swatch={RAIN} label="Permeable" value={`${fmt(calc.perm)} ${unit}`} sub={`${fmt(calc.permPct)}%`} />
                <Stat
                  swatch={calc.pass ? PASS : FAIL}
                  label={calc.pass ? "Impervious margin remaining" : "Impervious over limit by"}
                  value={`${fmt(Math.abs(calc.over))} ${unit}`}
                  sub={`Allowance ${fmt(calc.allowance)} ${unit}`}
                />
              </div>

              {calc.overfilled && (
                <Note color={FAIL}>
                  Surfaces total {fmt(calc.listed)} {unit}, more than the {fmt(lot)} {unit} site. Check the areas on the plan.
                </Note>
              )}
              {!calc.overfilled && calc.unassigned > 0.5 && (
                <Note color={MUTED}>
                  {fmt(calc.unassigned)} {unit} ({fmt((calc.unassigned / lot) * 100)}%) of the site is not assigned to any surface. Unassigned area is not counted as impervious.
                </Note>
              )}
            </>
          )}
        </section>

        <p style={{ marginTop: 18, fontSize: 13, color: MUTED, lineHeight: 1.5, maxWidth: 620 }}>
          Percentages are measured against the total site area. Confirm the applicable limit and what counts as impervious with the City of Vancouver zoning and building bylaws for your zone before relying on this check.
        </p>
      </div>
    </div>
  );
}

function CoverageBar({ impPct, permPct }) {
  const W = 760, H = 56, y = 10, h = 30;
  const impW = Math.min(impPct, 100) / 100 * W;
  const permW = Math.min(permPct, Math.max(0, 100 - impPct)) / 100 * W;
  const limitX = (LIMIT / 100) * W;
  return (
    <svg className="lc-bar" viewBox={`0 0 ${W} ${H}`} width="100%" role="img"
      aria-label={`Impervious ${fmt(impPct)} percent, permeable ${fmt(permPct)} percent, limit ${LIMIT} percent`}>
      <defs>
        <pattern id="hatch" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <rect width="8" height="8" fill={CONCRETE} />
          <line x1="0" y1="0" x2="0" y2="8" stroke="#fff" strokeWidth="2" opacity=".55" />
        </pattern>
      </defs>
      <rect x="0" y={y} width={W} height={h} fill="#E4EAF0" />
      <rect x="0" y={y} width={impW} height={h} fill="url(#hatch)" />
      <rect x={impW} y={y} width={permW} height={h} fill={RAIN} />
      <line x1={limitX} y1={y - 8} x2={limitX} y2={y + h + 6} stroke={INK} strokeWidth="2" strokeDasharray="4 3" />
      <text x={limitX} y={H - 2} textAnchor="middle" fontSize="12" fill={INK} fontWeight="600">{LIMIT}% limit</text>
      <text x="0" y={H - 2} fontSize="12" fill={MUTED}>0%</text>
      <text x={W} y={H - 2} textAnchor="end" fontSize="12" fill={MUTED}>100%</text>
    </svg>
  );
}

function Stat({ swatch, hatch, label, value, sub }) {
  return (
    <div style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
      <span
        aria-hidden
        style={{
          width: 14, height: 14, marginTop: 3, borderRadius: 2, flexShrink: 0,
          background: hatch
            ? `repeating-linear-gradient(45deg, ${swatch} 0 3px, #fff 3px 4px)`
            : swatch,
        }}
      />
      <div>
        <div style={{ color: MUTED }}>{label}</div>
        <div style={{ fontSize: 18, fontWeight: 600 }}>{value}</div>
        <div style={{ color: MUTED, fontSize: 13 }}>{sub}</div>
      </div>
    </div>
  );
}

function Note({ color, children }) {
  return (
    <p style={{ margin: "16px 0 0", padding: "10px 12px", borderLeft: `3px solid ${color}`, background: PAPER, fontSize: 14, lineHeight: 1.5 }}>
      {children}
    </p>
  );
}
