// Precompute US map SVG paths + pin positions (Albers USA) for map pops.
// Usage: node mapsvg.mjs <out.json>   Pins are defined below; add places as needed.
import fs from "node:fs";
import { createRequire } from "node:module";
import { feature, mesh } from "topojson-client";
import { geoAlbersUsa, geoPath } from "d3-geo";
const require = createRequire(import.meta.url);
const us = require("us-atlas/states-10m.json");

const W = 1100, H = 680;
const states = feature(us, us.objects.states);
const nation = feature(us, us.objects.nation);
const proj = geoAlbersUsa().fitExtent([[30, 30], [W - 30, H - 30]], nation);
const path = geoPath(proj);
const PLACES = {
  okc: { name: "Oklahoma City", lonlat: [-97.5164, 35.4676] },
  oak: { name: "Oakland, California", lonlat: [-122.2712, 37.8044] },
  dc: { name: "Washington, D.C.", lonlat: [-77.0369, 38.9072] },
};
const pins = Object.fromEntries(Object.entries(PLACES).map(([k, v]) => [k, proj(v.lonlat).map((n) => +n.toFixed(1))]));
const out = {
  w: W, h: H,
  nation: path(nation),
  borders: path(mesh(us, us.objects.states, (a, b) => a !== b)),
  pins,
};
fs.writeFileSync(process.argv[2], JSON.stringify(out));
console.log("pins", pins, "bytes", JSON.stringify(out).length);
