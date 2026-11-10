import fs from "node:fs";
import { createRequire } from "node:module";
const require = createRequire(new URL("../../../package.json", import.meta.url));
const { feature } = require("topojson-client");
const { geoMercator, geoPath } = require("d3-geo");
const world = require("world-atlas/land-50m.json");
const land = feature(world, world.objects.land);
const W = 1700, H = 1000;
const bbox = { type: "Feature", geometry: { type: "Polygon", coordinates: [[[-7, 37.5], [-7, 55.5], [19, 55.5], [19, 37.5], [-7, 37.5]]] } };
const proj = geoMercator().fitExtent([[0, 0], [W, H]], bbox);
proj.clipExtent([[-200, -200], [W + 200, H + 200]]);
const path = geoPath(proj);
// clip land to a generous window for smaller path strings
const places = { amsterdam: [4.90, 52.37], paris: [2.35, 48.86], brussels: [4.35, 50.85], rome: [12.50, 41.90] };
const pins = Object.fromEntries(Object.entries(places).map(([k, v]) => [k, proj(v).map(n => +n.toFixed(1))]));
const labels = { mare: proj([4.8, 39.6]), oceanus: proj([-5.0, 46.8]), germanicum: proj([3.3, 54.6]), adriaticum: proj([15.3, 42.6]) };
const out = { w: W, h: H, land: path(land), pins, labels };
fs.writeFileSync(process.argv[2], "window.MAP=" + JSON.stringify(out) + ";");
console.log(pins, (JSON.stringify(out).length / 1024).toFixed(0) + " KB");
