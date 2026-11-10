// World map (Natural Earth land, 110m) for the Case File look, plus pin positions.
// Usage: node tools/mapgen_world.mjs film2/world.js
import fs from "node:fs";
import { createRequire } from "node:module";
const require = createRequire(new URL("../../../package.json", import.meta.url));
const { feature } = require("topojson-client");
const { geoNaturalEarth1, geoPath, geoGraticule10 } = require("d3-geo");
const world = require("world-atlas/land-50m.json");
const land = feature(world, world.objects.land);
const W = 1700, H = 940;
const proj = geoNaturalEarth1().scale(330).translate([W * 0.47, H * 0.56]).center([40, 12]);
const path = geoPath(proj);
const P = {
  irhoud: [-8.87, 31.86], neander: [10, 48], denisova: [84.67, 51.4], africa: [25, 2], png: [145, -6.3], muna: [122.5, -4.9],
  maltravieso: [-6.37, 39.47], gobekli: [38.92, 37.22], siberia: [129, 71], middleeast: [44, 33], europe: [10, 48],
  levant: [35.5, 32.5], wasia: [55, 40], oceania: [150, -8], athens: [23.73, 37.98],
};
const pins = Object.fromEntries(Object.entries(P).map(([k, v]) => [k, proj(v).map((n) => +n.toFixed(1))]));
const out = { w: W, h: H, land: path(land), grat: path(geoGraticule10()), pins };
fs.writeFileSync(process.argv[2], "window.WORLD=" + JSON.stringify(out) + ";");
console.log(pins, (JSON.stringify(out).length / 1024).toFixed(0) + " KB");
