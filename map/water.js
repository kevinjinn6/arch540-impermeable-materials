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
    - faint contour lines from the same 2013 ground heights, under the water.
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
  opening_h: 1,
  // What each size is for in the City's design manual (s.5.2.1, p.133), shown under the switch.
  meaning: { 5: "the storm house-street pipes are built for", 10: "the storm business-street pipes are built for",
             25: "the storm trunk sewers are built for", 100: "the storm streets must carry as overflow routes" },
  page_storm: false,      // true = the page's 48 mm (STORM in index.html, Rain City Strategy) in
                          // each length, instead of the City's curves
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
  veil: 0.55,             // how strongly the lots fade while Water is on (0 none, 1 hidden)
  path: "#0b4f9c", pathDark: "#9ad3ff",       // the water's paths (and a full low spot's outline)
  spot: "#2b8fd6", spotDark: "#5fb4f0",       // the low spots
  pipes: "#8a8780",                           // the pipes' share on the card's bar
  route: "#1c1b18", routeDark: "#f2f0eb",     // the selected lot's way downhill, and the lots draining
                                              // to a picked place: the page's ink, so the pick reads
                                              // apart from the water's blue and the lots' sand and slate
  catchment_opacity: 0.3,   // how strongly the lots draining to a picked place are tinted
  dry_paths: 0.35,        // how strongly a dry path is drawn: where water would run (0 = hidden)
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
// The lowest impermeable share (0 to 1, to 0.1%) at which the pipes are full in
// `storm` and water starts to run downhill; null if they take it at every share.
function pipesFullAbove(storm) {
  for (let k = 0; k <= 1000; k++) if (splitMm(k / 1000, storm).downhill > 1e-9) return k / 1000;
  return null;
}
// The smallest storm on the card's switches in which water runs downhill (at least
// 0.1 mm) from a lot at `hardShare`: the smallest size first, then the shortest length.
function firstStormDownhill(hardShare, climate) {
  for (const years of STORMS.years) for (const hours of STORMS.lengths_h)
    if (splitMm(hardShare, { climate, years, hours }).downhill >= 0.1) return { climate, years, hours };
  return null;
}
// Send `mm` from every m2 of lot down the network: each path and low spot in
// turn, uphill ones first. A low spot keeps water up to its volume and spills
// the rest. Returns what arrives at (inn) and leaves (out) each one, m3.
function routeWater(net, mm) {
  const n = net.down.length, inn = new Float64Array(n), out = new Float64Array(n);
  for (const u of net.order) {
    inn[u] += mm / 1000 * net.a[u];
    out[u] = Math.max(0, inn[u] - net.v[u]);
    if (net.down[u] >= 0) inn[net.down[u]] += out[u];
  }
  return { inn, out };
}
// m3 arriving in each park: water entering it from outside, plus what drains
// straight into the paths and low spots inside it.
function parkArrivals(net, out, mm) {
  const got = new Float64Array(net.parkCount);
  for (let u = 0; u < net.down.length; u++) {
    const p = net.park[u];
    if (p < 0) continue;
    got[p] += mm / 1000 * net.a[u];
    for (const q of net.ups[u]) if (net.park[q] !== p) got[p] += out[q];
  }
  return got;
}
// Lot area (m2) draining through each path and low spot: its own and all above it.
function drainedArea(net) {
  const up = Float64Array.from(net.a);
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
                pick: null, route: [], spotCentre: new Map(), spotName: new Map() };
const WATER_PATH = dark ? WATER.pathDark : WATER.path, WATER_SPOT = dark ? WATER.spotDark : WATER.spot;
const WATER_ROUTE = dark ? WATER.routeDark : WATER.route;
const nice = x => x >= 1e6 ? `${(x / 1e6).toFixed(1)} million` : x >= 1e5 ? `${(x / 1e3).toFixed(0)}k` : roundNice(x);   // 1.1 million, 449k, 2,600, 14
const ha = m2 => `${(m2 / 1e4).toFixed(m2 < 1e5 ? 1 : 0)} ha`;
const pctOf = share => `${Math.round(share * 100)}%`;

// The storm picked on the card, at its length or another.
const stormAt = (hours = water.hours) => ({ climate: water.climate, years: water.years, hours });
// Each storm's curve, worked out once: mm running downhill at 0%, 1%, ... 100%, and
// the share where the pipes fill.
const curveCache = new Map();
function curveOf(storm) {
  const key = `${storm.climate}/${storm.years}/${storm.hours}`;
  if (!curveCache.has(key))
    curveCache.set(key, { mm: Array.from({ length: 101 }, (_, k) => splitMm(k / 100, storm).downhill), full: pipesFullAbove(storm) });
  return curveCache.get(key);
}
// One height for the chart across every storm on the switches, so a bigger storm draws a bigger line.
const Y_MAX = Math.max(5, Math.ceil(Math.max(...STORMS.climates.flatMap(climate => STORMS.years.flatMap(years =>
  STORMS.lengths_h.map(hours => splitMm(1, { climate, years, hours }).downhill)))) / 10) * 10);
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

// The chart: mm running downhill (up) against the impermeable share of every lot (across),
// one line per storm length, the chosen one in the water's colour. A dashed purple line
// marks the by-law's 75%; a dot marks the slider; a tick marks where the pipes fill.
const CH = { W: 268, H: 112, l: 4, r: 30, t: 14, b: 18 };
const chX = s => CH.l + s * (CH.W - CH.l - CH.r), chY = mm => CH.t + (1 - mm / Y_MAX) * (CH.H - CH.t - CH.b);
function chartSvg() {
  const h = water.hours, th = curveOf(stormAt()).full, base = chY(0);
  const line = c => c.map((mm, k) => `${k ? "L" : "M"}${chX(k / 100).toFixed(1)},${chY(mm).toFixed(1)}`).join("");
  const others = STORMS.lengths_h.filter(x => x !== h);
  // Line labels at the right end, pushed apart so they never overlap.
  const labs = STORMS.lengths_h.map(x => ({ x, y: chY(curveOf(stormAt(x)).mm[100]) + 3.5 })).sort((a, b) => a.y - b.y);
  for (let k = 1; k < labs.length; k++) labs[k].y = Math.max(labs[k].y, labs[k - 1].y + 11);
  const sliderMax = +slider.max / 100, now = state.hard;
  const say = STORMS.lengths_h.map(x => { const f = curveOf(stormAt(x)).full; return `${x} h: ${f === null ? "pipes never full" : `pipes full above ${pctOf(f)}`}`; }).join("; ");
  return `<svg class="chart" viewBox="0 0 ${CH.W} ${CH.H}" role="img" aria-label="Water running downhill against the impermeable share of every lot. ${say}. The by-law allows ${pctOf(L)}.">` +
    (sliderMax < 1 ? `<rect x="${chX(sliderMax)}" y="${CH.t}" width="${chX(1) - chX(sliderMax)}" height="${base - CH.t}" fill="var(--fill)"></rect>` : "") +
    `<line x1="${CH.l}" x2="${chX(1)}" y1="${base}" y2="${base}" stroke="var(--rule)"></line>` +
    `<text x="${CH.l}" y="${CH.t - 4}">${Y_MAX} mm downhill</text>` +
    `<line x1="${chX(L)}" x2="${chX(L)}" y1="${CH.t}" y2="${base}" stroke="${OVER}" stroke-width="1.5" stroke-dasharray="3 3"></line>` +
    `<text x="${chX(L)}" y="${CH.t - 4}" text-anchor="middle">${pctOf(L)} cap</text>` +
    others.map(x => `<path d="${line(curveOf(stormAt(x)).mm)}" fill="none" stroke="var(--ink-3)" stroke-width="1.25" opacity="0.55"></path>`).join("") +
    `<path d="${line(curveOf(stormAt()).mm)}" fill="none" stroke="${WATER_PATH}" stroke-width="2" stroke-linejoin="round"></path>` +
    labs.map(o => `<text x="${chX(1) + 4}" y="${o.y.toFixed(1)}" class="${o.x === h ? "sel" : ""}">${o.x} h</text>`).join("") +
    (th === null ? "" : `<line x1="${chX(th)}" x2="${chX(th)}" y1="${base - 4}" y2="${base + 4}" stroke="${WATER_PATH}" stroke-width="2"></line>` +
      `<text x="${Math.min(Math.max(chX(th), CH.l + 32), chX(1) - 32)}" y="${CH.H - 3}" text-anchor="middle">full at ${pctOf(th)}</text>`) +
    (th === null || th > 0.15 ? `<text x="${CH.l}" y="${CH.H - 3}">0%</text>` : "") +
    (th === null || th < 0.8 ? `<text x="${chX(1)}" y="${CH.H - 3}" text-anchor="end">100%</text>` : "") +
    `<line class="cross" x1="0" x2="0" y1="${CH.t}" y2="${base}" stroke="var(--ink-3)" visibility="hidden"></line>` +
    `<circle cx="${chX(now)}" cy="${chY(splitMm(now, stormAt()).downhill)}" r="4" fill="${WATER_PATH}" stroke="var(--surface)" stroke-width="2"></circle>` +
    `<rect class="hit" x="0" y="0" width="${CH.W}" height="${CH.H}" fill="transparent"></rect></svg>`;
}
const readoutNow = () => `Slider at ${pctOf(state.hard)}: ${water.last.split.downhill.toFixed(1)} mm runs downhill from every lot.`;
function readoutAt(share) {
  return `At ${pctOf(share)}: ` + STORMS.lengths_h.map(x => `${x} h <b>${splitMm(share, stormAt(x)).downhill.toFixed(1)}</b>`).join(" · ") + " mm downhill";
}

// What the card and the hover say about one path or low spot.
function describeNode(u) {
  const net = water.net, r = water.last, h = water.hours;
  const drains = `drains ${ha(water.drained[u])} of lots`;
  if (u < net.paths)
    return `<b>Downhill path</b> · ${drains}<br>` +
      (r.out[u] >= 0.5 ? `${nice(r.out[u])} m³ passes in the ${h} h storm` : `dry in the ${h} h storm: the pipes take it`);
  const v = net.v[u], inn = r.inn[u], spill = r.out[u];
  return `<b>Low spot</b> · holds ${nice(v)} m³ to ${net.settings.pond_cap_m * 100} cm · ${drains}<br>` +
    (inn < 0.5 ? `dry in the ${h} h storm` : spill >= 0.5 ? `gets ${nice(inn)} m³: full, spills ${nice(spill)} m³` : `gets ${nice(inn)} m³: ${Math.round(inn / v * 100)}% full`);
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
  const net = water.net, r = water.last, s = r.split, h = water.hours, th = curveOf(stormAt()).full;
  const sw = (c, t) => `<span><i class="swatch" style="background:${c}"></i>${t}</span>`;
  const bar = [[s.soaks, PERM], [s.pipes, WATER.pipes], [s.downhill, WATER_PATH], [s.dries, COLOR.out]]
    .map(([mm, c]) => `<span style="width:${(mm / stormMm(stormAt()) * 100).toFixed(2)}%;background:${c}"></span>`).join("");
  const page = STORMS.page_storm, rain = stormMm(stormAt()), ratio = rain / designRainMm(h);
  const meaning = water.climate === PIPES.curve && STORMS.meaning[water.years];
  const first = s.downhill > 0 ? null : firstStormDownhill(state.hard, water.climate);
  // The headline: where the pipes fill, against the by-law's limit.
  const headline = th === null
    ? `<span class="big">Never</span><span>The pipes take this storm at any share of hard surface.</span>`
    : th === 0
      ? `<span class="big">0%</span><span>Even a lot with no hard surface overflows the pipes in this storm.</span>`
    : th <= L
      ? `<span class="big">${pctOf(th)}</span><span>Above this much hard surface the pipes are full and water runs downhill. The by-law allows ${pctOf(L)}.</span>`
      : `<span class="big">${pctOf(th)}</span><span>The pipes fill only above this, past the by-law's ${pctOf(L)}: a lot within the by-law sends nothing downhill.</span>`;
  // The low spots where most water stands (what each holds, up to its volume).
  const ponds = [], standing = u => r.inn[u] - r.out[u];
  for (let u = net.paths; u < net.down.length; u++) if (standing(u) >= 1) ponds.push(u);
  ponds.sort((a, b) => standing(b) - standing(a));
  const topParks = [...r.arrive.entries()].filter(([, m3]) => m3 >= 1).sort((a, b) => b[1] - a[1]).slice(0, WATER.top);
  waterCard.innerHTML =
    `<h2>Water · ${page ? `${STORM.rainfall_mm} mm storm` : `1-in-${water.years}-year storm`}</h2>` +
    (page ? "" : `<div class="seg" role="radiogroup" aria-label="Storm size: 1-in-N-year">` +
      STORMS.years.map(y => `<button type="button" role="radio" aria-checked="${y === water.years}" data-y="${y}" aria-label="1-in-${y}-year">${y} yr</button>`).join("") + `</div>`) +
    `<div class="segs"><div class="seg" role="radiogroup" aria-label="Storm length">` +
      STORMS.lengths_h.map(x => `<button type="button" role="radio" aria-checked="${x === h}" data-h="${x}">${x} h</button>`).join("") + `</div>` +
      (page ? "" : `<div class="seg" role="radiogroup" aria-label="Rain">` + STORMS.climates.map(c =>
        `<button type="button" role="radio" aria-checked="${c === water.climate}" data-c="${c}">${c === PIPES.curve ? "today" : c}</button>`).join("") + `</div>`) + `</div>` +
    `<div class="caption">${rain.toFixed(0)} mm in ${h} h` + (!page && water.climate !== PIPES.curve ? ` with ${water.climate}'s rain` : "") + ": " +
      (Math.abs(ratio - 1) < 0.005 ? "the storm the pipes are built for." : `${ratio.toFixed(1)}× what the pipes are built for` + (meaning ? `; ${meaning}.` : ".")) + `</div>` +
    `<div class="headline">${headline}</div>` +
    `<div class="more">${chartSvg()}<div class="caption" id="waterReadout">${readoutNow()}</div></div>` +
    `<div class="water-bar" aria-hidden="true">${bar}</div>` +
    `<div class="keys">${sw(PERM, "soaks in")}${sw(WATER.pipes, "pipes")}${sw(WATER_PATH, "runs downhill")}${sw(COLOR.out, "dries off")}</div>` +
    (s.downhill > 0
      ? `<p style="margin:8px 0 0">From every lot at ${pctOf(state.hard)}: <b>${nice(r.total)} m³</b> runs downhill; low spots hold ${Math.round(r.held / r.total * 100)}%.</p>`
      : `<p style="margin:8px 0 0">At ${pctOf(state.hard)} nothing runs downhill: ` +
        (s.pipes >= 0.05 ? `the pipes take all ${s.pipes.toFixed(1)} mm that overflows.` : `the soil holds it all.`) +
        (page ? "" : first ? ` <span class="hint">It first does in the 1-in-${first.years}-year ${first.hours} h storm: <button type="button" data-first="${first.years}/${first.hours}">show it</button>.</span>`
                           : ` Not in any storm here, with ${water.climate === PIPES.curve ? "today's" : `${water.climate}'s`} rain.`) + `</p>`) +
    `<div class="more">` +
      (water.pick ? `<div class="pick" role="status">${pickHtml(water.pick)} <button type="button" data-clear>Clear</button></div>` : "") +
      (ponds.length ? `<h3>Where most water stands</h3><ol>` + ponds.slice(0, WATER.top).map(u =>
        `<li><button type="button" data-node="${u}">${esc(spotName(u))}</button> · ${nice(standing(u))} m³` +
        (r.out[u] >= 0.5 ? ", spilling" : "") + `</li>`).join("") + `</ol>` : "") +
      (topParks.length ? `<h3>Parks it reaches most</h3><ol>` + topParks.map(([p, m3]) =>
        `<li><button type="button" data-park="${p}">${esc(water.parks[p].n)}</button> · ${nice(m3)} m³</li>`).join("") + `</ol>` : "") +
      (water.pick ? "" : `<div class="caption" style="margin-top:${ponds.length || topParks.length ? 4 : 10}px">` +
        (ponds.length || topParks.length ? "Pick one, or click" : "Nothing runs downhill here. Click") + ` a path or low spot to tint the lots that drain to it.</div>`) +
      `<div class="keys" style="margin-top:10px">` +
        `<span><i class="legend-line" style="background:${WATER_PATH}"></i>path, thicker = more</span>` +
        (WATER.dry_paths ? `<span><i class="legend-line" style="background:${WATER_PATH};opacity:${WATER.dry_paths}"></i>dry: where it would run</span>` : "") +
        `<span><i class="swatch" style="background:${WATER_SPOT}"></i>low spot, darker = fuller</span>` +
        `<span><i class="swatch ring" style="--c:${WATER_PATH}"></i>full, spilling</span>` +
        (map.getLayer("water-contours") ? `<span><i class="legend-line" style="background:${CONTOUR};height:1px"></i>contour, labelled in m</span>` : "") +
        (water.pick ? `<span><i class="swatch" style="background:${WATER_ROUTE};opacity:${WATER.catchment_opacity + 0.2}"></i>drains to the pick</span>` : "") +
        (water.route.length ? `<span><i class="legend-line" style="background:${WATER_ROUTE}"></i>this lot's way down</span>` : "") +
      `</div>` +
      `<details><summary>What this assumes</summary><dl>` +
        `<dt>Storm</dt><dd>` + (page ? `${STORM.rainfall_mm} mm (${STORM.policy}) falling in ${h} h`
          : `1-in-${water.years}-year, ${water.climate === PIPES.curve ? "today's rain (Table 5-3, p.136)" : `${water.climate}'s rain, RCP 8.5 moderate (Table 5-5, p.138)`}: ${rain.toFixed(0)} mm in ${h} h`) + `</dd>` +
        `<dt>Lots</dt><dd>${Math.round(STORM.soil_mm)} mm held by soil however fast the rain falls, ${Math.round(STORM.runoff * 100)}% runoff from hard surfaces, spread onto the soil (this page's)</dd>` +
        `<dt>Pipes</dt><dd>1-in-${PIPES.return_years}-year rain (today's) × C ${PIPES.design_runoff} per m² of lot: ${pipeCapacityMm(h).toFixed(1)} mm (Engineering Design Manual 2026, pp.133–136)</dd>` +
        `<dt>Low spots</dt><dd>hold water to ${net.settings.pond_cap_m * 100} cm (pp.151, 183); not under houses; hollows over ${net.settings.spot_max_depth_m} m deep left out</dd>` +
        `<dt>Ground</dt><dd>2013 heights at ${net.settings.cell_m} m, 2015 houses as walls; no grading since 2013. Contours: the same heights, about 3 m apart</dd>` +
        ((net.settings.not_low_spots || []).length ? `<dt>Left out</dt><dd>${net.settings.not_low_spots.map(esc).join("; ")}</dd>` : "") +
        `<dt>Not counted</dt><dd>streets and lanes, other zones, culverts, parks soaking water up; combined sewers (about a quarter of mains) that overflow to False Creek and Burrard Inlet</dd>` +
      `</dl><p class="caption" style="margin:6px 0 0">The City's design manual and this page's soil and runoff; not the by-law.</p></details>` +
    `</div>`;
  waterCard.querySelectorAll("[data-h]").forEach(b => b.addEventListener("click", () => { water.hours = +b.dataset.h; updateWater(); }));
  waterCard.querySelectorAll("[data-y]").forEach(b => b.addEventListener("click", () => { water.years = +b.dataset.y; updateWater(); }));
  waterCard.querySelectorAll("[data-c]").forEach(b => b.addEventListener("click", () => { water.climate = +b.dataset.c; updateWater(); }));
  waterCard.querySelector("[data-first]")?.addEventListener("click", e => {
    const [y, h] = e.currentTarget.dataset.first.split("/").map(Number); water.years = y; water.hours = h; updateWater(); });
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
function pickHtml(p) {
  const n = p.lots ? p.lots.length.toLocaleString("en-CA") : "";
  if (p.park !== undefined)
    return `<b>${esc(water.parks[p.park].n)}</b> · ${nice(water.last.arrive.get(p.park) || 0)} m³ arrives` +
      (p.lots.length ? `<br>${n} lots (${ha(p.area)}) reach this park first, tinted on the map.` : "");
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
    water.drained = drainedArea(net);
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
    const full = ["coalesce", ["feature-state", "full"], 0], q = ["coalesce", ["feature-state", "q"], 0];
    const spill = ["boolean", ["feature-state", "spill"], false], onRoute = ["boolean", ["feature-state", "route"], false];
    map.addLayer({ id: "water-spots", type: "fill", source: "water-spots",
      paint: { "fill-color": WATER_SPOT, "fill-opacity": ["interpolate", ["linear"], full, 0, 0.1, 1, 0.8] } }, "basins");
    // A full low spot, spilling over, gets a dark outline; one on the selected lot's way down, the route colour.
    map.addLayer({ id: "water-spots-edge", type: "line", source: "water-spots", minzoom: 11,
      paint: { "line-color": ["case", onRoute, WATER_ROUTE, spill, WATER_PATH, WATER_SPOT],
               "line-width": ["case", onRoute, 2.5, spill, 2, 0.75] } }, "basins");
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

// Route this storm and repaint: once per animation frame, however fast the slider moves.
function updateWater() {
  if (!water.net) return;
  cancelAnimationFrame(water.frame);
  water.frame = requestAnimationFrame(() => {
    const net = water.net, split = splitMm(state.hard, stormAt()), mm = split.downhill;
    const { inn, out } = routeWater(net, mm);
    let held = 0, total = 0;
    for (let u = 0; u < net.down.length; u++) { total += mm / 1000 * net.a[u]; if (u >= net.paths) held += inn[u] - out[u]; }
    water.last = { split, mm, inn, out, held, total, arrive: new Map(parkArrivals(net, out, mm).entries()) };
    if (water.on) {
      for (let k = 0; k < net.paths; k++) map.setFeatureState({ source: "water-paths", id: k }, { q: out[k] });
      for (let k = net.paths; k < net.down.length; k++)
        map.setFeatureState({ source: "water-spots", id: k }, { full: Math.min(1, inn[k] / net.v[k]), spill: out[k] >= 0.5 });
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
const waterAt = point => {
  if (!water.on || !water.last || !map.getLayer("water-paths")) return null;
  const box = [[point.x - 4, point.y - 4], [point.x + 4, point.y + 4]];
  // The amber check sites stay clickable as lots.
  if (map.queryRenderedFeatures(box, { layers: ["check-clusters", "check-single"].filter(id => map.getLayer(id)) }).length) return null;
  const f = map.queryRenderedFeatures(box, { layers: ["water-paths", "water-spots"] })
    .find(f => f.layer.id === "water-spots" || WATER.dry_paths || (map.getFeatureState({ source: "water-paths", id: f.id }).q || 0) > 0.5);
  return f ? +f.id : null;
};
map.on("mousemove", e => {
  const u = waterAt(e.point);
  if (u === null) { tip.remove(); return; }
  tip.setLngLat(e.lngLat).setHTML(describeNode(u)).addTo(map);
});
map.on("mouseout", () => tip.remove());
// This runs before index.html's lot click (it is added first), so it can tell selectLot to sit this click out.
map.on("click", e => {
  const u = waterAt(e.point);
  if (u === null) return;
  water.tookClick = true;
  setTimeout(() => { water.tookClick = false; }, 0);
  pick({ node: u }, false);
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
  const m3 = splitMm(r.share, stormAt()).downhill / 1000 * lot.properties.A, th = curveOf(stormAt()).full;
  const where = [spot >= 0 ? `a low spot that holds ${roundNice(net.v[spot])} m³` : "",
                 park >= 0 ? `${esc(water.parks[park].n)}, about ${roundNice(metres)} m downhill` : "the shore"].filter(Boolean).join(", then ");
  const inStorm = STORMS.page_storm ? `in ${water.hours} h`
    : `in the 1-in-${water.years}-year ${water.hours} h storm (${stormMm(stormAt()).toFixed(0)} mm${water.climate !== PIPES.curve ? `, ${water.climate}'s rain` : ""})`;
  el.insertAdjacentHTML("beforeend", `<br><br><b>Downhill</b> · ` +
    (m3 >= 0.05 ? `${inStorm} this lot is at ${pctOf(r.share)}, past the ${pctOf(th)} where the pipes fill: about ${m3.toFixed(1)} m³ runs off, first to ${where}.`
      : th === null ? `${inStorm} the pipes take its overflow. If they didn't, it would run to ${where}.`
      : `${inStorm} the pipes take its overflow up to ${pctOf(th)} hard surface (this lot: ${pctOf(r.share)}). Past that it would run to ${where}.`) +
    (water.route.length ? (water.on ? " Its way down is drawn on the map." : " Switch on Water to see its way down.") : ""));
};
