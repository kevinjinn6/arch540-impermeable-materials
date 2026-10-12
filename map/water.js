/*
================================================================================
 WHERE THE WATER GOES  --  the map's "Water" layers
================================================================================

WHAT THIS ADDS TO THE MAP
  A "Water" button under the City button. Switched on, it shows:
    - the paths water takes downhill once it leaves the lots, thicker where
      more water runs, and faint where they are dry: where it would run;
    - the low spots where it ponds, filling darker as they fill, with a dark
      outline once they are full and spilling over;
    - a card that answers the policy question first: above what share of
      hard surface are the pipes full, and how does that compare with the
      by-law's 75%? A small chart shows it for each storm length;
    - the low spots where most water stands and the parks that receive most; pick
      one (or click a path or low spot on the map) and the lots that drain
      to it are tinted: its catchment, where on-lot work would help it;
    - with a lot selected, that lot's own way downhill, drawn on the map;
    - faint contour lines from the same 2013 ground heights, under the water;
    - a second view, "Which storm fills": each low spot coloured by the
      smallest storm that fills it, so the map reads at any setting.
  Hover a path or low spot for its numbers; a click on one picks only it
  (the lot underneath is not selected). The lots are dimmed behind a
  veil so the water reads. The parks are not.

THE MODEL (Kevin's decisions, 2026-10-06, 2026-10-09 and 2026-10-11; NOT the by-law)
  1. Every lot is at the Every-lot slider's impermeable share, in the storm
     picked on the card: a 1-in-N-year storm of a length, from the City's
     rainfall curves for today or for 2100 (STORMS; it opens on the 1-in-5,
     the storm the pipes are built for; STORMS.page_storm puts the page's
     48 mm back). The page's own water balance (waterBalance in
     index.html, with this storm's rain) gives each m2 of lot its overflow:
     what neither the ground nor the hard surfaces' losses keep.
  2. The storm sewer takes that overflow up to what it was built for. City
     residential storm sewers are sized for the 1-in-5-year storm (Engineering
     Design Manual 2026, p.133), from the City's rainfall curve:
         intensity (mm/h) = IDF_A x hours ^ IDF_B
     so the 1-in-5-year rain in a storm of that length is intensity x hours.
     The pipes carry DESIGN_RUNOFF of that rain from each m2 of lot: the
     manual's runoff coefficient for one- and two-family housing.
     Streets and lanes in R1-1 zoning send their rain too (STREETS: 85% runs
     off, no soil), and share the pipes with the lots.
  3. Whatever is left runs downhill along the paths in data/flow-paths.geojson,
     fills each low spot in data/low-spots.geojson up to its volume (counted
     only to 15 cm deep, the City's ponding limit beside roads), spills
     over, and carries on until it reaches the shore. Parks only report what
     arrives: until a figure is set, they hold nothing.
  Where everything drains was worked out once from the 2013 ground heights by
  map/water_layers.py; read its LIMITS before quoting a number.

HOW IT IS CONNECTED TO index.html
  index.html loads this file after its own script and uses nothing else of
  it. This file reads the page's map, state, slider, STORM, COLOR, PERM, esc, L (the
  75% limit) and OVER (its purple), adds one line to the lot card's "Storm"
  row, and keeps selectLot from selecting a lot when a click picked water. It draws on the page's "lots" source to tint a
  catchment; it changes no lot's colour or result.
================================================================================
*/

// =============================================================================
//  CONFIGURATION  --  change these numbers, not the code below
// =============================================================================
// The City's rainfall curves: intensity (mm/h) = A x hours ^ B, so the rain in a storm of
// that length is intensity x hours. City of Vancouver Engineering Design Manual (2026),
// Table 5-3 (2018: today's rain), p.136, and Table 5-5 (2100, RCP 8.5 moderate projection),
// p.138; read from the PDF 2026-10-11. For each 1-in-N-year storm: [A, B].
const RAIN = {
  2018: { 2: [12.386, -0.447], 5: [16.517, -0.471], 10: [19.449, -0.486], 25: [23.487, -0.508],
          50: [26.673, -0.522], 100: [30.043, -0.537], 200: [33.646, -0.553] },
  2100: { 2: [16.607, -0.440], 5: [22.698, -0.466], 10: [26.651, -0.482], 25: [32.615, -0.506],
          50: [37.252, -0.520], 100: [42.014, -0.535], 200: [46.968, -0.551] },
};
const PIPES = {
  curve: 2018,            // residential pipes are sized for the 1-in-5-year storm (s.5.2.1, p.133);
  return_years: 5,        // the pipes in the ground were built to today's rain, not 2100's
  design_runoff: 0.70,    // Table 5-1, p.134: "One and Two Family Dwelling" C = 0.70. The pipes
                          // carry this share of the design rain from each m2 of lot (Kevin's call
                          // 2026-10-09, replacing the 0.5 first assumed)
};
const STORMS = {
  years: [5, 10, 25, 100, 200],   // the storm-size switch on the card: the 1-in-N-year storm
  opening_years: 5,               // Kevin's call, 2026-10-11: open on the storm the pipes are built for
  climates: [2018, 2100],         // the rain switch: today's curve, or the City's 2100 projection
  opening_climate: 2018,
  lengths_h: [1, 6, 24],          // the storm-length switch
  opening_h: 24,                  // a day: in the 1-in-5-year storm the limit's effect shows most
                                  // (2026-10-11: 38 places flood at 50%, 271 at 75%); in 1 h, almost none
  // What each size is for in the City's design manual (s.5.2.1, p.133), shown under the switch.
  meaning: { 5: "the storm house-street pipes are built for", 10: "the storm business-street pipes are built for",
             25: "the storm trunk sewers are built for", 100: "the storm streets must carry as overflow routes" },
  page_storm: false,      // true = the page's 48 mm (STORM in index.html, Rain City Strategy) in
                          // each length, instead of the City's curves
};
const STREETS = {
  // Streets and lanes in R1-1 zoning (data/water.json "s", from map/water_layers.py) send
  // their water too (Kevin's call, 2026-10-11: "try it").
  runoff: 0.85,           // share of rain running off streets and lanes: the page's figure for hard
                          // surfaces (STORM.runoff); no soil under them
  pipes: "shared",        // "shared": the pipes take water from lots and streets together, up to their
                          // share per m2 of both: one pipe serves the whole catchment (Engineering
                          // Design Manual s.5.2.2). "separate": lots and streets each get only their own
                          // share, as if every catch basin could take no more than its street's rain
};
const FLOOD_MAP = {
  // "Which storm fills it": each low spot coloured by the smallest storm on the switches that fills
  // it (sizes from STORMS.years, any length), darkest for the most frequent. One colour per size,
  // light to dark; then the colour for a low spot no storm here fills.
  colors: ["#08306b", "#1d5fa6", "#3f8fd0", "#8cbfe6", "#c9e0f3"],
  colorsDark: ["#eaf4ff", "#b5d6f6", "#7db4ea", "#4a8bd0", "#2c639e"],
  never_opacity: 0.08,
};
const CONTOURS = {
  library: "https://cdn.jsdelivr.net/npm/maplibre-contour@0.1.0/dist/index.min.js",
  // Contour interval by zoom, m: [every line, every bold labelled line]. Drawn from the shaded
  // relief's tiles (the 2013 DEM, about 3 m per pixel), so only while Water is on.
  intervals: { 11: [10, 50], 13: [5, 25], 14: [2, 10], 15: [1, 5] },
  color: "#65635c", colorDark: "#9c9991",     // the page's quiet ink (--ink-3)
  opacity: 0.3, bold_opacity: 0.55,           // faint, so they sit under the water
  labels_from_zoom: 14,
};
const WATER = {
  network_file: "data/water.json",
  paths_file: "data/flow-paths.geojson",
  spots_file: "data/low-spots.geojson",
  veil: 0.3,              // how strongly the lots fade while Water is on (0 none, 1 hidden): light, so
                          // the sand and slate stay readable under the water
  path: "#0b4f9c", pathDark: "#9ad3ff",       // the water's paths (and a full low spot's outline)
  spot: "#2b8fd6", spotDark: "#5fb4f0",       // the low spots
  pipes: "#8a8780",                           // the pipes' share on the card's bar
  route: "#1c1b18", routeDark: "#f2f0eb",     // the selected lot's way downhill, and the lots draining
                                              // to a picked place: the page's ink, so the pick reads
                                              // apart from the water's blue and the lots' sand and slate
  catchment_opacity: 0.3,   // how strongly the lots draining to a picked place are tinted
  dry_paths: 0,           // how strongly a dry path is drawn: where water would run (0 = hidden)
  top: 3,                 // how many low spots and parks the card names
};
// =============================================================================
//  END OF CONFIGURATION
// =============================================================================


// ---- PURE: the arithmetic, with no map in it ----------------------------------
// A storm is { climate, years, hours }: the 1-in-`years`-year storm lasting `hours`.
// Its rain, mm.
function rainMm(climate, years, hours) { const [A, B] = RAIN[climate][years]; return A * Math.pow(hours, B) * hours; }
function stormMm(storm) { return STORMS.page_storm ? STORM.rainfall_mm : rainMm(storm.climate, storm.years, storm.hours); }
// The rain the pipes are built for in a storm of `hours`, mm, and what they take from each m2 of lot.
function designRainMm(hours) { return rainMm(PIPES.curve, PIPES.return_years, hours); }
function pipeCapacityMm(hours) { return PIPES.design_runoff * designRainMm(hours); }
// index.html's waterBalance for one m2, in mm, with the rain as an input (the page's
// uses its 48 mm). Same terms: the page's runoff share and soil.
function balanceMm(hardShare, rainMm) {
  const P = rainMm, C = STORM.runoff, D = STORM.soil_mm, perm = 1 - hardShare;
  const reaching = P * perm + P * C * hardShare;        // what lands on soil, and runs off hard surfaces
  const held = Math.min(reaching, D * perm);            // what the soil holds
  return { held, sewer: reaching - held, surface: P - reaching };
}
// One m2 of lot at `hardShare` impermeable, in `storm`: mm that soak in, go to the
// pipes, run downhill, and dry off hard surfaces (the 15% that never runs off).
function splitMm(hardShare, storm) {
  const w = balanceMm(hardShare, stormMm(storm));
  const pipes = Math.min(w.sewer, pipeCapacityMm(storm.hours));
  return { soaks: w.held, pipes, downhill: w.sewer - pipes, dries: w.surface };
}
// Water each path and low spot takes in from its own catchment (the lots and streets
// draining straight into it), m3, past the pipes: every lot at `hardShare`, in `storm`.
function nodeSources(net, storm, hardShare, into = new Float64Array(net.down.length)) {
  const rain = stormMm(storm), cap = pipeCapacityMm(storm.hours);
  const lot = balanceMm(hardShare, rain).sewer;       // mm per m2 of lot reaching the pipes
  const street = net.s ? STREETS.runoff * rain : 0;    // mm per m2 of street reaching the pipes
  for (let u = 0; u < into.length; u++) {
    const a = net.a[u], b = net.s ? net.s[u] : 0;
    into[u] = (STREETS.pipes === "shared" ? Math.max(0, a * lot + b * street - (a + b) * cap)
                                          : a * Math.max(0, lot - cap) + b * Math.max(0, street - cap)) / 1000;
  }
  return into;
}
// A low spot floods when it fills: its water stands 15 cm deep or more (it is counted
// only to POND_CAP_M in map/water_layers.py, the City's limit beside roads and walks).
const floods = (net, inn, u) => inn[u] > 0.5 && inn[u] >= net.v[u] - 0.5;
// How many low spots flood in `storm`, every lot at `hardShare`.
function floodedCount(net, storm, hardShare) {
  const { inn } = routeWater(net, nodeSources(net, storm, hardShare));
  let n = 0;
  for (let u = net.paths; u < net.down.length; u++) if (floods(net, inn, u)) n++;
  return n;
}
// Send each path's and low spot's own water (`src`, m3) down the network, uphill ones
// first. A low spot keeps water up to its volume and spills the rest. Returns what
// arrives at (inn) and leaves (out) each one, m3.
function routeWater(net, src) {
  const n = net.down.length, inn = new Float64Array(n), out = new Float64Array(n);
  for (const u of net.order) {
    inn[u] += src[u];
    out[u] = Math.max(0, inn[u] - net.v[u]);
    if (net.down[u] >= 0) inn[net.down[u]] += out[u];
  }
  return { inn, out };
}
// m3 arriving in each park: water entering it from outside, plus what drains
// straight into the paths and low spots inside it.
function parkArrivals(net, out, src) {
  const got = new Float64Array(net.parkCount);
  for (let u = 0; u < net.down.length; u++) {
    const p = net.park[u];
    if (p < 0) continue;
    got[p] += src[u];
    for (const q of net.ups[u]) if (net.park[q] !== p) got[p] += out[q];
  }
  return got;
}
// For each low spot, the smallest storm on the switches that fills it (its place in
// STORMS.years, and its length), every lot at `hardShare`, with `climate`'s rain; -1 = none.
function firstFills(net, hardShare, climate) {
  const n = net.down.length, size = new Int8Array(n).fill(-1), length = new Float32Array(n);
  STORMS.years.forEach((years, yi) => {
    for (const hours of STORMS.lengths_h) {
      const { inn } = routeWater(net, nodeSources(net, { climate, years, hours }, hardShare));
      for (let u = net.paths; u < n; u++) if (size[u] < 0 && floods(net, inn, u)) { size[u] = yi; length[u] = hours; }
    }
  });
  return { size, length };
}
// Lot and street area (m2) draining through each path and low spot: its own and all above it.
function drainedArea(net, key) {
  const up = Float64Array.from(net[key] || net.a.map(() => 0));
  for (const u of net.order) if (net.down[u] >= 0) up[net.down[u]] += up[u];
  return up;
}
// Every path and low spot whose water passes through `node`, itself included.
function upstreamOf(net, node) {
  const seen = new Set([node]), stack = [node];
  while (stack.length) for (const q of net.ups[stack.pop()]) if (!seen.has(q)) { seen.add(q); stack.push(q); }
  return seen;
}
// The paths and low spots water from `node` runs through, down to the shore.
function downstreamOf(net, node) {
  const out = [], seen = new Set();
  for (let u = node; u >= 0 && !seen.has(u); u = net.down[u]) { seen.add(u); out.push(u); }
  return out;
}
// The assessed lots (their places in lots.geojson) whose water reaches a place:
// a park (as the first park it reaches), or a path or low spot. `counted(i)` says
// whether lot i sends water (grey, not-assessed lots send none).
function lotsDrainingTo(net, place, counted) {
  const hit = [];
  if (place.park !== undefined) {
    for (let i = 0; i < net.lots; i++) if (net.lot_park[i] === place.park && counted(i)) hit.push(i);
    return hit;
  }
  // water.json from before 2026-10-11 has no lot_node: then only the lots that
  // meet a low spot on the way can be traced, and a path's catchment is unknown.
  if (!net.lot_node && place.node < net.paths) return null;
  const up = upstreamOf(net, place.node), first = net.lot_node || net.lot_spot;
  for (let i = 0; i < net.lots; i++) if (up.has(first[i]) && counted(i)) hit.push(i);
  return hit;
}
// ---- END PURE -----------------------------------------------------------------


const water = { on: false, loading: false, net: null, parks: [], frame: 0, last: null,
                hours: STORMS.opening_h, years: STORMS.opening_years, climate: STORMS.opening_climate,
                mode: "storm", fills: null, area: 0, streetArea: 0, moreOpen: false,
                pick: null, route: [], spotCentre: new Map(), spotName: new Map() };
const WATER_PATH = dark ? WATER.pathDark : WATER.path, WATER_SPOT = dark ? WATER.spotDark : WATER.spot;
const WATER_ROUTE = dark ? WATER.routeDark : WATER.route;
const nice = x => x >= 1e6 ? `${(x / 1e6).toFixed(1)} million` : x >= 1e5 ? `${(x / 1e3).toFixed(0)}k` : roundNice(x);   // 1.1 million, 449k, 2,600, 14
const ha = m2 => `${(m2 / 1e4).toFixed(m2 < 1e5 ? 1 : 0)} ha`;
const pctOf = share => `${Math.round(share * 100)}%`;

// The storm picked on the card, at its length or another.
const stormAt = (hours = water.hours) => ({ climate: water.climate, years: water.years, hours });
// Each storm's curve, worked out once: how many places flood with every lot at 0%, 1%, ... 100%.
const curveCache = new Map();
function floodCurve(storm) {
  const key = `${storm.climate}/${storm.years}/${storm.hours}`;
  if (!curveCache.has(key)) curveCache.set(key, Array.from({ length: 101 }, (_, k) => floodedCount(water.net, storm, k / 100)));
  return curveCache.get(key);
}
// The card's storm, in words: "a common storm" for the one it opens on.
const isOpeningStorm = () => water.years === STORMS.opening_years && water.hours === STORMS.opening_h && water.climate === STORMS.opening_climate;
const lengthText = h => h === 24 ? "a day" : `${h} h`;
const stormTitle = () => isOpeningStorm() ? "a common storm" : `a 1-in-${water.years}-year storm`;
const FLOOD = dark ? FLOOD_MAP.colorsDark : FLOOD_MAP.colors;
const CONTOUR = dark ? CONTOURS.colorDark : CONTOURS.color;

// ---- The card on the map ------------------------------------------------------
const waterCard = document.createElement("div");
waterCard.id = "waterCard"; waterCard.className = "water-card"; waterCard.hidden = true;
waterCard.setAttribute("aria-label", "Where the water goes");
document.body.appendChild(waterCard);
document.head.insertAdjacentHTML("beforeend", `<style>
  .water-card { position: absolute; right: 12px; bottom: 36px; width: 300px; max-height: calc(100vh - 250px); overflow-y: auto;
    box-sizing: border-box; padding: 14px 16px; z-index: 2;
    background: var(--glass); -webkit-backdrop-filter: blur(16px) saturate(1.4); backdrop-filter: blur(16px) saturate(1.4);
    border-radius: 12px; box-shadow: var(--float); font-size: 12px; line-height: 16px; color: var(--ink-2); }
  .water-card h2 { margin: 0 0 8px; }
  .water-card h3 { margin: 12px 0 2px; font-size: 12px; font-weight: 600; color: var(--ink); }
  .water-card .seg { height: 32px; margin: 8px 0 6px; }
  .water-card .seg button { font-size: 12px; padding: 0 2px; }
  .water-card .segs { display: flex; gap: 6px; } .water-card .segs .seg { margin-top: 0; }
  .water-card .segs .seg:first-child { flex: 3 1 0; } .water-card .segs .seg:last-child { flex: 2 1 0; }
  .water-card .flood-key { display: grid; grid-template-columns: repeat(6, 1fr); gap: 2px; margin: 10px 0 4px; text-align: center; font-variant-numeric: tabular-nums; }
  .water-card .flood-key i { display: block; height: 10px; border-radius: 2px; margin-bottom: 3px; }
  .water-card .flood-key b { display: block; font-weight: 600; color: var(--ink); font-size: 11px; } .water-card .flood-key span { font-size: 11px; }
  .water-card .hint button { border: 0; background: none; padding: 0; font: inherit; color: var(--accent); cursor: pointer; }
  .water-card .water-bar { height: 10px; margin: 8px 0 4px; }
  .water-card .keys { display: flex; flex-wrap: wrap; gap: 2px 10px; }
  .water-card .keys span { display: inline-flex; align-items: center; gap: 4px; }
  .water-card .headline { display: flex; gap: 10px; align-items: baseline; margin: 10px 0 2px; }
  .water-card .big { font-size: 22px; line-height: 26px; font-weight: 600; color: var(--ink); font-variant-numeric: tabular-nums; flex: none; }
  .water-card .chart { display: block; width: 100%; height: auto; margin-top: 6px; }
  .water-card .chart text { font-size: 10px; fill: var(--ink-3); font-variant-numeric: tabular-nums; }
  .water-card .chart .sel { fill: var(--ink); font-weight: 600; }
  .water-card ol { margin: 2px 0 0; padding-left: 18px; }
  .water-card ol button, .water-card .pick button { border: 0; background: none; padding: 0; font: inherit; color: var(--accent); cursor: pointer; text-align: left; }
  .water-card .pick { margin: 10px 0 0; padding: 8px 10px; background: var(--fill); border-radius: 8px; }
  .water-card .legend-line { display: inline-block; width: 18px; height: 3px; border-radius: 2px; }
  .water-card .swatch.ring { background: transparent !important; box-shadow: inset 0 0 0 2px var(--c); }
  .water-card details { margin-top: 10px; } .water-card summary { color: var(--accent); cursor: pointer; }
  .water-card dl { display: grid; grid-template-columns: auto 1fr; gap: 3px 10px; margin: 6px 0 0; }
  .water-card dt { color: var(--ink); } .water-card dd { margin: 0; }
  .water-tip .maplibregl-popup-content { padding: 6px 9px; font-size: 12px; line-height: 16px; color: var(--ink-2);
    background: var(--surface); border-radius: 8px; box-shadow: var(--float); }
  .water-tip .maplibregl-popup-tip { display: none; }
  /* On a phone the card keeps the switch, the headline and the bar; the rest would cover the map. */
  @media (max-width: 560px) { .water-card { top: 12px; bottom: auto; left: 12px; right: 60px; width: auto; padding: 10px 12px; }
    .water-card .more { display: none; } .water-card .seg { margin: 6px 0 4px; } }
</style>`);

// The chart: places flooding (up) against the hard surface on every lot (across), the same
// 0-100% as the Every-lot slider. A dashed purple line marks the by-law's 75%; a dot, the slider.
const CH = { W: 268, H: 92, l: 4, r: 6, t: 16, b: 16 };
const chX = s => CH.l + s * (CH.W - CH.l - CH.r);
function chartSvg() {
  const c = floodCurve(stormAt()), top = Math.max(10, Math.ceil(Math.max(...c) / 100) * 100);
  const y = n => CH.t + (1 - n / top) * (CH.H - CH.t - CH.b), base = y(0), now = state.hard;
  const pts = c.map((n, k) => `${chX(k / 100).toFixed(1)},${y(n).toFixed(1)}`);
  return `<svg class="chart" viewBox="0 0 ${CH.W} ${CH.H}" role="img" aria-label="Places flooding against hard surface on every lot: ${c[0]} at 0%, ${c[50]} at 50%, ${c[Math.round(L * 100)]} at the ${pctOf(L)} limit, ${c[100]} at 100%.">` +
    `<line x1="${CH.l}" x2="${chX(1)}" y1="${base}" y2="${base}" stroke="var(--rule)"></line>` +
    `<path d="M${chX(0)},${base}L${pts.join("L")}L${chX(1)},${base}Z" fill="${WATER_SPOT}" opacity="0.22"></path>` +
    `<path d="M${pts.join("L")}" fill="none" stroke="${WATER_PATH}" stroke-width="2" stroke-linejoin="round"></path>` +
    `<line x1="${chX(L)}" x2="${chX(L)}" y1="${CH.t}" y2="${base}" stroke="${OVER}" stroke-width="1.5" stroke-dasharray="3 3"></line>` +
    `<text x="${chX(L)}" y="${CH.t - 5}" text-anchor="middle">${pctOf(L)} limit</text>` +
    `<text x="${CH.l}" y="${CH.t - 5}">${top} places</text>` +
    `<text x="${CH.l}" y="${CH.H - 2}">0% hard</text><text x="${chX(0.5)}" y="${CH.H - 2}" text-anchor="middle">50%</text>` +
    `<text x="${chX(1)}" y="${CH.H - 2}" text-anchor="end">100%</text>` +
    `<line class="cross" x1="0" x2="0" y1="${CH.t}" y2="${base}" stroke="var(--ink-3)" visibility="hidden"></line>` +
    `<circle cx="${chX(now)}" cy="${y(water.last.flooded)}" r="4.5" fill="${WATER_PATH}" stroke="var(--surface)" stroke-width="2"></circle>` +
    `<rect class="hit" x="0" y="0" width="${CH.W}" height="${CH.H}" fill="transparent"></rect></svg>`;
}
function readoutNow() {
  const c = floodCurve(stormAt()), k = Math.round(L * 100);
  return `At 50%: <b>${c[50]}</b> · at the ${pctOf(L)} limit: <b>${c[k]}</b>`;
}
const readoutAt = share => `At ${pctOf(share)} hard: <b>${floodCurve(stormAt())[Math.round(share * 100)]}</b> places flood`;

// What the card and the hover say about one path or low spot.
function describeNode(u) {
  const net = water.net, r = water.last;
  const drains = `drains ${ha(water.drained[u])} of lots` + (net.s ? ` and ${ha(water.drainedStreets[u])} of street` : "");
  if (u < net.paths)
    return `<b>Water running downhill</b> · ${r.out[u] >= 0.5 ? `${nice(r.out[u])} m³` : "dry"}<br>${drains}`;
  const v = net.v[u], inn = r.inn[u];
  if (water.mode === "flood") {
    const k = water.fills.size[u];
    return `<b>${k < 0 ? "No storm here floods it" : `Floods in a 1-in-${STORMS.years[k]}-year storm`}</b>` +
      (k < 0 ? "" : ` (${lengthText(water.fills.length[u])})`) + `<br>holds ${nice(v)} m³ · ${drains}`;
  }
  return `<b>${floods(net, r.inn, u) ? "Floods: 15 cm deep or more" : inn < 0.5 ? "Dry" : `${Math.round(inn / v * 100)}% full`}</b>` +
    `<br>holds ${nice(v)} m³ · ${drains}`;
}
// A name for a low spot: the street of the nearest lot that drains into it (or, if
// none does, the nearest lot), else its park.
function spotName(u) {
  if (water.spotName.has(u)) return water.spotName.get(u);
  const net = water.net, c = water.spotCentre.get(u);
  const nearest = draining => {
    let best = null, bestD = Infinity;
    for (let i = 0; i < net.lots; i++) {
      if ((draining && net.lot_spot[i] !== u) || !state.lots[i].properties.ad) continue;
      const q = featureCenter(state.lots[i]), d = (q[0] - c[0]) ** 2 + (q[1] - c[1]) ** 2;
      if (d < bestD) { bestD = d; best = state.lots[i].properties.ad; }
    }
    return best;
  };
  const ad = (c && (nearest(true) || nearest(false))) || "";
  // "3528 W 30TH AV" -> "W 30th Av": drop the number, keep compass letters in capitals.
  const street = ad.replace(/^\S+\s+/, "").split(" ")
    .map(w => /^(N|S|E|W|NE|NW|SE|SW)$/.test(w) ? w : w.charAt(0) + w.slice(1).toLowerCase()).join(" ");
  const name = street ? `near ${street}` : net.park[u] >= 0 ? `in ${water.parks[net.park[u]].n}` : "low spot";
  water.spotName.set(u, name);
  return name;
}

function renderCard() {
  if (!water.net) { waterCard.innerHTML = `<h2>Water</h2>Loading the paths and low spots…`; return; }
  const net = water.net, r = water.last, h = water.hours, flood = water.mode === "flood";
  const page = STORMS.page_storm, rain = stormMm(stormAt()), ratio = rain / designRainMm(h);
  const meaning = Math.abs(ratio - 1) < 0.005 ? "the storm the pipes are built for"
    : `${ratio.toFixed(1)}× what the pipes are built for` + (water.climate === PIPES.curve && STORMS.meaning[water.years] ? `; ${STORMS.meaning[water.years]}` : "");
  const seg = (label, items) => `<div class="seg" role="radiogroup" aria-label="${label}">` +
    items.map(([on, data, text, aria]) => `<button type="button" role="radio" aria-checked="${on}" ${data}${aria ? ` aria-label="${aria}"` : ""}>${text}</button>`).join("") + `</div>`;
  const key = (c, t, line) => `<span><i class="${line ? "legend-line" : "swatch"}" style="background:${c}"></i>${t}</span>`;

  // The top of the card: one number, one picture.
  let top;
  if (flood) {
    const f = water.fills, K = net.down.length - net.paths, count = STORMS.years.map(() => 0);
    for (let u = net.paths; u < net.down.length; u++) if (f.size[u] >= 0) count[f.size[u]]++;
    const k10 = STORMS.years.findIndex(y => y >= 10), early = count.slice(0, k10 + 1).reduce((t, x) => t + x, 0);
    const never = K - count.reduce((t, x) => t + x, 0);
    top = `<h2>Water · which storm floods each place</h2>` +
      `<div class="headline"><span class="big">${early}</span><span>places flood in a 1-in-${STORMS.years[k10]}-year storm or a more common one, with every lot ${pctOf(state.hard)} hard.</span></div>` +
      `<div class="flood-key" role="img" aria-label="${STORMS.years.map((y, k) => `1-in-${y}: ${count[k]}`).join(", ")}, none: ${never}">` +
        STORMS.years.map((y, k) => `<div><i style="background:${FLOOD[k]}"></i><b>${y} yr</b><span>${count[k]}</span></div>`).join("") +
        `<div><i style="background:var(--rule)"></i><b>none</b><span>${never}</span></div></div>` +
      `<div class="caption">Darker: floods in a more common storm.</div>`;
  } else {
    top = `<h2>Water · ${stormTitle()}</h2>` +
      `<div class="caption">${rain.toFixed(0)} mm in ${lengthText(h)}${!page && water.climate !== PIPES.curve ? ` with ${water.climate}'s rain` : ""}: ${meaning}.</div>` +
      `<div class="headline"><span class="big">${r.flooded}</span><span>places flood 15 cm deep or more (the City's limit), with every lot ${pctOf(state.hard)} hard.</span></div>` +
      chartSvg() + `<div class="caption" id="waterReadout">${readoutNow()}</div>` +
      `<div class="keys" style="margin-top:6px">${key(WATER_SPOT, "flooded 15 cm+")}${key(WATER_PATH, "water running downhill", true)}</div>`;
  }

  // Everything else, folded away.
  const ponds = [], standing = u => r.inn[u] - r.out[u];
  if (!flood) { for (let u = net.paths; u < net.down.length; u++) if (floods(net, r.inn, u)) ponds.push(u); ponds.sort((a, b) => standing(b) - standing(a)); }
  const topParks = flood ? [] : [...r.arrive.entries()].filter(([, m3]) => m3 >= 1).sort((a, b) => b[1] - a[1]).slice(0, WATER.top);
  const streetKm2 = net.s ? (water.streetArea / 1e6).toFixed(1) : 0;
  const more = `<details class="more" data-more${water.moreOpen ? " open" : ""}><summary>Other storms, places, and how it's worked out</summary>` +
    (page ? "" : seg("Colour places by", [[!flood, `data-mode="storm"`, "This storm"], [flood, `data-mode="flood"`, "Which storm floods"]])) +
    (page || flood ? "" : seg("Storm size: 1-in-N-year", STORMS.years.map(y => [y === water.years, `data-y="${y}"`, `${y} yr`, `1-in-${y}-year`]))) +
    `<div class="segs">` + (flood ? "" : seg("Storm length", STORMS.lengths_h.map(x => [x === h, `data-h="${x}"`, `${x} h`]))) +
      (page ? "" : seg("Rain", STORMS.climates.map(c => [c === water.climate, `data-c="${c}"`, c === PIPES.curve ? "today" : c]))) + `</div>` +
    (ponds.length ? `<h3>Deepest flooding</h3><ol>` + ponds.slice(0, WATER.top).map(u =>
      `<li><button type="button" data-node="${u}">${esc(spotName(u))}</button> · ${nice(standing(u))} m³</li>`).join("") + `</ol>` : "") +
    (topParks.length ? `<h3>Parks the water reaches</h3><ol>` + topParks.map(([p, m3]) =>
      `<li><button type="button" data-park="${p}">${esc(water.parks[p].n)}</button> · ${nice(m3)} m³</li>`).join("") + `</ol>` : "") +
    `<div class="caption" style="margin-top:6px">Click a park, a flooded place or a water path to see the lots that drain to it.</div>` +
    `<div class="keys" style="margin-top:8px">` +
      (map.getLayer("water-contours") ? key(CONTOUR, "contour, in m", true) : "") +
      (water.route.length ? key(WATER_ROUTE, "this lot's way down", true) : "") + `</div>` +
    `<h3>How it's worked out</h3><dl>` +
      `<dt>Lots</dt><dd>soil holds ${Math.round(STORM.soil_mm)} mm; ${Math.round(STORM.runoff * 100)}% of the rain on hard surfaces runs off onto it (this page's)</dd>` +
      (net.s ? `<dt>Streets</dt><dd>${streetKm2} km² in R1-1 zoning, ${Math.round(STREETS.runoff * 100)}% runoff` + (STREETS.pipes === "shared" ? ", sharing the pipes with the lots" : "") + `</dd>` : "") +
      `<dt>Pipes</dt><dd>take the 1-in-${PIPES.return_years}-year rain × ${PIPES.design_runoff} (Engineering Design Manual 2026, pp.133–136)</dd>` +
      `<dt>Places</dt><dd>low spots in the 2013 ground; flooded when water reaches ${net.settings.pond_cap_m * 100} cm (pp.151, 183)</dd>` +
      `<dt>Rain</dt><dd>${page ? `${STORM.rainfall_mm} mm (${STORM.policy})` : "the City's curves, today's (p.136) or 2100's (p.138)"}</dd>` +
      ((net.settings.not_low_spots || []).length ? `<dt>Left out</dt><dd>${net.settings.not_low_spots.map(esc).join("; ")}</dd>` : "") +
      `<dt>Not counted</dt><dd>other zones, culverts, parks soaking water up, how fast soil soaks, combined sewers</dd>` +
    `</dl><p class="caption" style="margin:6px 0 0">Not the by-law: the City's design manual and this page's soil and runoff.</p></details>`;
  const pickBox = water.pick ? `<div class="pick" role="status">${pickHtml(water.pick)} <button type="button" data-clear>Clear</button></div>` : "";
  waterCard.innerHTML = top + pickBox + more;
  waterCard.querySelector("[data-more]").addEventListener("toggle", e => { water.moreOpen = e.target.open; });
  waterCard.querySelectorAll("[data-h]").forEach(b => b.addEventListener("click", () => { water.hours = +b.dataset.h; updateWater(); }));
  waterCard.querySelectorAll("[data-y]").forEach(b => b.addEventListener("click", () => { water.years = +b.dataset.y; updateWater(); }));
  waterCard.querySelectorAll("[data-c]").forEach(b => b.addEventListener("click", () => { water.climate = +b.dataset.c; updateWater(); }));
  waterCard.querySelectorAll("[data-mode]").forEach(b => b.addEventListener("click", () => setMapMode(b.dataset.mode)));
  waterCard.querySelectorAll("[data-node]").forEach(b => b.addEventListener("click", () => pick({ node: +b.dataset.node }, true)));
  waterCard.querySelectorAll("[data-park]").forEach(b => b.addEventListener("click", () => pick({ park: +b.dataset.park }, true)));
  waterCard.querySelector("[data-clear]")?.addEventListener("click", () => pick(null));
  // Hover the chart: a crosshair and every storm length's figure at that share.
  const svg = waterCard.querySelector(".chart"), cross = svg?.querySelector(".cross"), out = $("waterReadout");
  if (svg) {
    const at = e => { const b = svg.getBoundingClientRect();
      return Math.min(1, Math.max(0, ((e.clientX - b.left) * CH.W / b.width - CH.l) / (CH.W - CH.l - CH.r))); };
    svg.addEventListener("pointermove", e => { const s = at(e);
      cross.setAttribute("x1", chX(s)); cross.setAttribute("x2", chX(s)); cross.setAttribute("visibility", "visible"); out.innerHTML = readoutAt(s); });
    svg.addEventListener("pointerleave", () => { cross.setAttribute("visibility", "hidden"); out.innerHTML = readoutNow(); });
  }
}

// ---- Picking a place: its catchment tinted on the map ----------------------------
// `place` is { park } or { node }; null clears. Its lots are found once, here; its
// figures (pickHtml) follow the storm and the slider.
function pick(place, fly) {
  water.pick = null;
  if (place && water.net) {
    place.lots = lotsDrainingTo(water.net, place, i => state.lots[i].properties.assessed === 1);
    place.area = place.lots ? place.lots.reduce((t, i) => t + state.lots[i].properties.A, 0) : 0;
    water.pick = place;
  }
  const keys = water.pick && water.pick.lots ? water.pick.lots.map(i => state.lots[i].properties.k) : [];
  if (map.getLayer("water-catchment")) for (const id of ["water-catchment", "water-catchment-edge"])
    map.setFilter(id, keys.length ? ["in", ["get", "k"], ["literal", keys]] : ["==", ["get", "k"], ""]);
  if (fly && water.pick) {
    const c = place.park !== undefined ? water.parks[place.park].c : water.spotCentre.get(place.node);
    if (c) map.flyTo({ center: c, zoom: Math.max(map.getZoom(), 14) });
  }
  renderCard();
}
// A park, for the hover and the card: the water arriving in this storm. Parks hold none
// in this model (Kevin's call, 2026-10-06): no figure for how much a park can take is set yet.
function describePark(p) {
  const m3 = water.last.arrive.get(p) || 0;
  return `<b>${esc(water.parks[p].n)}</b><br>` + (m3 >= 1 ? `${nice(m3)} m³ of water arrives in ${stormTitle()}`
    : `no water arrives in ${stormTitle()}: the soil and pipes above it take it all`);
}
function pickHtml(p) {
  const n = p.lots ? p.lots.length.toLocaleString("en-CA") : "";
  if (p.park !== undefined)
    return describePark(p.park) + (p.lots.length ? `<br>${n} lots drain toward it, tinted on the map.` : `<br>No lot drains toward it first.`);
  return describeNode(p.node) + (p.lots === null ? "" : p.lots.length ? `<br>${n} lots drain here, tinted on the map.`
                                                                      : `<br>No lot's water traced here.`);
}

// ---- The selected lot's way downhill -------------------------------------------
function setRoute(nodes) {
  const src = u => u < water.net.paths ? "water-paths" : "water-spots";
  for (const u of water.route) map.setFeatureState({ source: src(u), id: u }, { route: false });
  water.route = nodes;
  for (const u of nodes) map.setFeatureState({ source: src(u), id: u }, { route: true });
}

// ---- The layers -----------------------------------------------------------------
async function loadWater() {
  water.loading = true; renderCard();
  try {
    const [net, paths, spots, parks] = await Promise.all([WATER.network_file, WATER.paths_file, WATER.spots_file, PARKS_FILE]
      .map(f => fetch(f).then(r => { if (!r.ok) throw new Error(`${f}: ${r.status}`); return r.json(); })));
    if (net.lots !== state.lots.length) throw new Error(`water.json was made for ${net.lots} lots; the map has ${state.lots.length}. Re-run map/water_layers.py.`);
    net.ups = net.down.map(() => []);
    net.down.forEach((d, u) => { if (d >= 0) net.ups[d].push(u); });
    net.parkCount = parks.features.length;
    water.parks = parks.features.map(f => ({ n: f.properties.n, c: featureCenter(f) }));
    for (const f of spots.features) water.spotCentre.set(f.id, featureCenter(f));
    water.drained = drainedArea(net, "a");
    water.drainedStreets = drainedArea(net, "s");
    water.streetArea = net.s ? net.s.reduce((t, x) => t + x, 0) : 0;
    water.area = net.a.reduce((t, x) => t + x, 0) + water.streetArea;   // what the chart averages over
    water.net = net;
    // A veil over the lots (and the basemap under them), below the parks, so the water reads.
    map.addLayer({ id: "water-veil", type: "background",
      paint: { "background-color": getComputedStyle(document.documentElement).getPropertyValue("--surface").trim() || "#fbfaf7",
               "background-opacity": WATER.veil } }, "parks");
    // The lots that drain to the picked place: above the veil, below the parks.
    map.addLayer({ id: "water-catchment", type: "fill", source: "lots", filter: ["==", ["get", "k"], ""],
      paint: { "fill-color": WATER_ROUTE, "fill-opacity": WATER.catchment_opacity } }, "parks");
    map.addLayer({ id: "water-catchment-edge", type: "line", source: "lots", minzoom: 14, filter: ["==", ["get", "k"], ""],
      paint: { "line-color": WATER_ROUTE, "line-width": 0.75, "line-opacity": 0.6 } }, "parks");
    // Paths and low spots go above the relief and below the catch basins.
    map.addSource("water-spots", { type: "geojson", data: spots });
    map.addSource("water-paths", { type: "geojson", data: paths });
    const q = ["coalesce", ["feature-state", "q"], 0];
    const spill = ["boolean", ["feature-state", "spill"], false], onRoute = ["boolean", ["feature-state", "route"], false];
    // A low spot is drawn only when it floods (filled to 15 cm): blue, or nothing.
    map.addLayer({ id: "water-spots", type: "fill", source: "water-spots",
      paint: { "fill-color": WATER_SPOT, "fill-opacity": SPOT_OPACITY.storm } }, "basins");
    // A flooded low spot gets an outline; one on the selected lot's way down, the route colour.
    map.addLayer({ id: "water-spots-edge", type: "line", source: "water-spots", minzoom: 11,
      paint: { "line-color": ["case", onRoute, WATER_ROUTE, WATER_PATH],
               "line-opacity": ["case", onRoute, 1, spill, 0.8, 0],
               "line-width": ["case", onRoute, 2.5, 1] } }, "basins");
    // Width follows the water passing, m3: hairline when dry (hidden if dry_paths is 0), about 8 px for 100,000 m3 at street zoom.
    const width = k => ["interpolate", ["linear"], q, 0, WATER.dry_paths ? 1.2 * k : 0, 1, WATER.dry_paths ? 1.2 * k : 0.4 * k, 100, 1.2 * k, 10000, 3 * k, 100000, 6 * k, 1000000, 9 * k];
    map.addLayer({ id: "water-paths-casing", type: "line", source: "water-paths",
      layout: { "line-join": "round", "line-cap": "round" },
      paint: { "line-color": dark ? "#1a1a19" : "#fcfcfb", "line-opacity": ["case", [">", q, 0.5], 0.9, 0],
               "line-width": ["interpolate", ["linear"], ["zoom"], 11, ["+", 1, width(0.6)], 17, ["+", 2.5, width(1.6)]] } }, "basins");
    map.addLayer({ id: "water-paths", type: "line", source: "water-paths",
      layout: { "line-join": "round", "line-cap": "round" },
      paint: { "line-color": WATER_PATH, "line-opacity": ["case", [">", q, 0.5], 1, WATER.dry_paths],
               "line-width": ["interpolate", ["linear"], ["zoom"], 11, width(0.6), 17, width(1.6)] } }, "basins");
    // The selected lot's way downhill, drawn even where it is dry: where its water would go.
    map.addLayer({ id: "water-route", type: "line", source: "water-paths",
      layout: { "line-join": "round", "line-cap": "round" },
      paint: { "line-color": WATER_ROUTE, "line-opacity": ["case", onRoute, 1, 0],
               "line-width": ["interpolate", ["linear"], ["zoom"], 11, 2, 17, 4] } }, "basins");
    setWaterVisible(water.on);
    updateWater();
    loadContours();                           // on its own: the water works without it
  } catch (e) {
    console.warn("Water layers not available.", e);
    waterCard.innerHTML = `<h2>Water</h2>The water data could not be loaded (${esc(e.message)}). Run <code>python map/water_layers.py</code>.`;
  }
  water.loading = false;
}

// Contour lines, made in the browser from the shaded relief's tiles (the 2013 DEM) by the
// maplibre-contour library. They sit above the veil and under the low spots and paths, so the
// water reads first.
async function loadContours() {
  try {
    if (!window.mlcontour) await new Promise((ok, fail) => {
      const el = document.createElement("script");
      el.src = CONTOURS.library; el.onload = ok; el.onerror = () => fail(new Error(`${CONTOURS.library} did not load`));
      document.head.appendChild(el);
    });
    const dem = new mlcontour.DemSource({
      url: new URL(TERRAIN_TILES, location.href).href.replace(/%7B/g, "{").replace(/%7D/g, "}"),
      encoding: "mapbox", minzoom: 10, maxzoom: 15, worker: true });
    dem.setupMaplibre(maplibregl);
    map.addSource("contours", { type: "vector", bounds: TERRAIN_BOUNDS, minzoom: 11, maxzoom: 15,
      tiles: [dem.contourProtocolUrl({
        multiplier: 1 / VIEW_3D.tile_exaggeration,    // the tiles' heights are 5x: back to metres
        thresholds: CONTOURS.intervals, contourLayer: "contours", elevationKey: "ele", levelKey: "level" })] });
    const bold = [">", ["get", "level"], 0];
    map.addLayer({ id: "water-contours", type: "line", source: "contours", "source-layer": "contours", minzoom: 11,
      paint: { "line-color": CONTOUR, "line-opacity": ["case", bold, CONTOURS.bold_opacity, CONTOURS.opacity],
               "line-width": ["case", bold, 0.9, 0.5] } }, "water-spots");
    map.addLayer({ id: "water-contour-labels", type: "symbol", source: "contours", "source-layer": "contours",
      minzoom: CONTOURS.labels_from_zoom, filter: bold,
      layout: { "symbol-placement": "line", "text-field": ["concat", ["number-format", ["get", "ele"], {}], " m"],
                "text-font": ["Noto Sans Regular"], "text-size": 10, "symbol-spacing": 300 },
      paint: { "text-color": CONTOUR, "text-halo-color": dark ? "#1a1a19" : "#fcfcfb", "text-halo-width": 1.2 } }, "water-spots");
    setWaterVisible(water.on);
    if (water.on) renderCard();               // the legend's contour key
  } catch (e) {
    console.warn("Contours not available.", e);
  }
}

const WATER_LAYERS = ["water-veil", "water-catchment", "water-catchment-edge", "water-contours", "water-contour-labels",
                      "water-spots", "water-spots-edge", "water-paths-casing", "water-paths", "water-route"];
function setWaterVisible(on) {
  for (const id of WATER_LAYERS) if (map.getLayer(id)) map.setLayoutProperty(id, "visibility", on ? "visible" : "none");
}

// "storm": this storm's water. "flood": each low spot coloured by the smallest storm that fills it.
const SPOT_FIRST = ["coalesce", ["feature-state", "first"], -1];
const SPOT_OPACITY = { storm: ["case", ["boolean", ["feature-state", "spill"], false], 0.85, 0],
                       flood: ["case", [">=", SPOT_FIRST, 0], 0.85, FLOOD_MAP.never_opacity] };
function setMapMode(mode) {
  water.mode = mode;
  if (map.getLayer("water-spots")) {
    map.setPaintProperty("water-spots", "fill-color", mode === "flood"
      ? ["match", SPOT_FIRST, ...FLOOD.flatMap((c, k) => [k, c]), WATER_SPOT] : WATER_SPOT);
    map.setPaintProperty("water-spots", "fill-opacity", SPOT_OPACITY[mode]);
  }
  updateWater();
}

// Route this storm and repaint: once per animation frame, however fast the slider moves.
function updateWater() {
  if (!water.net) return;
  cancelAnimationFrame(water.frame);
  water.frame = requestAnimationFrame(() => {
    const net = water.net, storm = stormAt(), split = splitMm(state.hard, storm);
    const src = nodeSources(net, storm, state.hard);
    const { inn, out } = routeWater(net, src);
    let held = 0, total = 0;
    for (let u = 0; u < net.down.length; u++) { total += src[u]; if (u >= net.paths) held += inn[u] - out[u]; }
    let flooded = 0;
    for (let u = net.paths; u < net.down.length; u++) if (floods(net, inn, u)) flooded++;
    water.last = { split, src, inn, out, held, total, flooded, arrive: new Map(parkArrivals(net, out, src).entries()) };
    const flood = water.mode === "flood";
    if (flood) water.fills = firstFills(net, state.hard, water.climate);
    if (water.on) {
      // In the flood map the paths are drawn dry (the network) and each low spot by its first storm.
      for (let k = 0; k < net.paths; k++) map.setFeatureState({ source: "water-paths", id: k }, { q: flood ? 0 : out[k] });
      for (let k = net.paths; k < net.down.length; k++)
        map.setFeatureState({ source: "water-spots", id: k }, flood ? { first: water.fills.size[k], spill: false }
          : { first: -1, spill: floods(net, inn, k) });
      renderCard();
    }
    renderLotTotals();                        // the lot card's water line follows
  });
}

function setWater(on) {
  water.on = on;
  waterCard.hidden = !on;
  waterBtn.setAttribute("aria-pressed", String(on));
  waterBtn.style.background = on ? "var(--fill)" : "";
  if (on && !water.net && !water.loading) loadWater();
  setWaterVisible(on);
  if (!on) tip.remove();
  if (on) updateWater();
}

// The button, under City and 3D.
const waterBtn = document.createElement("button");
class WaterControl {
  onAdd() {
    this.el = document.createElement("div"); this.el.className = "maplibregl-ctrl maplibregl-ctrl-group";
    waterBtn.type = "button"; waterBtn.className = "city-ctrl"; waterBtn.textContent = "Water";
    waterBtn.title = "Where the water goes"; waterBtn.setAttribute("aria-label", "Show where the water goes");
    waterBtn.setAttribute("aria-pressed", "false");
    waterBtn.addEventListener("click", () => { if (state.ready) setWater(!water.on); });
    this.el.appendChild(waterBtn); return this.el;
  }
  onRemove() { this.el.remove(); }
}
map.addControl(new WaterControl(), "top-right");
slider.addEventListener("input", updateWater);
document.addEventListener("keydown", e => { if (e.key === "Escape" && water.pick) pick(null); });

// ---- On the map: hover a path or low spot for its numbers, click it for its catchment ----
// A click also reaches the lot underneath, as before: its card opens and its own way down is drawn.
const tip = new maplibregl.Popup({ closeButton: false, closeOnClick: false, className: "water-tip", offset: 12, maxWidth: "260px" });
// What is under the pointer, as a place to pick: { node } for a path or low spot that is
// drawn (a hidden low spot does not count), { park } for a park, or null.
const waterAt = point => {
  if (!water.on || !water.last || !map.getLayer("water-paths")) return null;
  const box = [[point.x - 4, point.y - 4], [point.x + 4, point.y + 4]];
  // The amber check sites stay clickable as lots.
  if (map.queryRenderedFeatures(box, { layers: ["check-clusters", "check-single"].filter(id => map.getLayer(id)) }).length) return null;
  const drawn = f => {
    const st = map.getFeatureState({ source: f.layer.id === "water-spots" ? "water-spots" : "water-paths", id: f.id });
    if (f.layer.id === "water-spots") return water.mode === "flood" ? true : !!st.spill;
    return WATER.dry_paths || (st.q || 0) > 0.5;
  };
  const f = map.queryRenderedFeatures(box, { layers: ["water-paths", "water-spots"] }).find(drawn);
  if (f) return { node: +f.id };
  // A park: the parks layer has no ids, so find it by name, nearest the pointer if two share one.
  const pk = map.getLayer("parks") && map.queryRenderedFeatures(point, { layers: ["parks"] })[0];
  if (!pk) return null;
  const ll = map.unproject(point), named = water.parks.map((q, i) => [q, i]).filter(([q]) => q.n === pk.properties.n);
  if (!named.length) return null;
  named.sort(([a], [b]) => ((a.c[0] - ll.lng) ** 2 + (a.c[1] - ll.lat) ** 2) - ((b.c[0] - ll.lng) ** 2 + (b.c[1] - ll.lat) ** 2));
  return { park: named[0][1] };
};
map.on("mousemove", e => {
  const at = waterAt(e.point);
  if (!at) { tip.remove(); return; }
  tip.setLngLat(e.lngLat).setHTML(at.park !== undefined ? describePark(at.park) : describeNode(at.node)).addTo(map);
});
map.on("mouseout", () => tip.remove());
// This runs before index.html's lot click (it is added first), so it can tell selectLot to sit this click out.
map.on("click", e => {
  const at = waterAt(e.point);
  if (!at) return;
  water.tookClick = true;
  setTimeout(() => { water.tookClick = false; }, 0);
  pick(at, false);
});
const selectLotWithoutWater = selectLot;
selectLot = function (feature, fly) { if (!water.tookClick) selectLotWithoutWater(feature, fly); };

// ---- The lot card: where this lot's water goes ----------------------------------
// index.html's renderLotTotals fills the card's "Storm" row; this adds a line to it
// and draws the lot's way downhill on the map.
const renderLotTotalsWithoutWater = renderLotTotals;
renderLotTotals = function () {
  renderLotTotalsWithoutWater();
  const el = $("lotStorm"), lot = state.selected, net = water.net, r = state.lotResult;
  if (!net) return;
  if (!el || !lot || !r) { if (water.route.length) { setRoute([]); if (water.on) renderCard(); } return; }
  const i = lot.properties._mi - 1;                     // the lot's place in lots.geojson (set by buildLotMesh)
  const park = net.lot_park[i], metres = net.lot_park_m[i], spot = net.lot_spot[i];
  const start = net.lot_node ? net.lot_node[i] : spot;  // older water.json: the route starts at the first low spot
  const had = water.route.length;
  setRoute(start >= 0 ? downstreamOf(net, start) : []);
  if (water.on && had !== water.route.length) renderCard();   // the legend's route key
  // This lot as the card has it (its roofs and the paving schedule), not the Every-lot slider.
  const m3 = splitMm(r.share, stormAt()).downhill / 1000 * lot.properties.A;
  const where = park >= 0 ? `${esc(water.parks[park].n)}, ${roundNice(metres)} m downhill` : "the shore";
  el.insertAdjacentHTML("beforeend", `<br><br><b>In ${stormTitle()}</b> · ` +
    (m3 >= 0.05 ? `about ${m3.toFixed(1)} m³ runs off this lot, toward ${where}.` : `nothing runs off this lot; the soil and pipes take it.`) +
    (water.route.length && water.on ? (m3 >= 0.05 ? " Its way down is drawn on the map." : " Where it would go is drawn on the map.") : ""));
};
