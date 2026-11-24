// Map geometry for the pencil pages: projects atlas shapes, points and routes into page pixels.
// stdin JSON: {topo, object, projection, fit: [[lon0,lat0],[lon1,lat1]] | null, box: [x, y, w, h], rotate,
//              points: {name: [lon,lat]}, routes: {name: [[lon,lat], ...]}, step}
// stdout JSON: {shapes: ["M...Z", ...], points: {name: [x,y]}, routes: {name: [[x,y], ...]}}
const fs = require("fs");
const path = require("path");
const d3 = require("d3-geo");
const topo = require("topojson-client");

const req = JSON.parse(fs.readFileSync(0, "utf8"));
const root = path.join(__dirname, "../../node_modules");
const t = JSON.parse(fs.readFileSync(path.join(root, req.topo), "utf8"));
const feat = topo.feature(t, t.objects[req.object]);
const make = { mercator: d3.geoMercator, equalEarth: d3.geoEqualEarth, naturalEarth: d3.geoNaturalEarth1,
               albersUsa: d3.geoAlbersUsa, equirect: d3.geoEquirectangular, conic: d3.geoConicConformal };
const proj = make[req.projection || "mercator"]();
if (req.rotate) proj.rotate(req.rotate);
if (req.parallels && proj.parallels) proj.parallels(req.parallels);
const [bx, by, bw, bh] = req.box;
if (req.fit) {
  const [[a, b], [c, d]] = req.fit;
  const poly = { type: "Feature", geometry: { type: "Polygon", coordinates: [[[a, b], [a, d], [c, d], [c, b], [a, b]]] } };
  proj.fitExtent([[bx, by], [bx + bw, by + bh]], poly);
} else {
  proj.fitExtent([[bx, by], [bx + bw, by + bh]], feat);
}
const gp = d3.geoPath(proj).digits(1);
const clip = req.clip !== false;
const shapes = [];
for (const f of (feat.features || [feat])) {
  const d = gp(f);
  if (d) shapes.push(d);
}
const points = {};
for (const [k, v] of Object.entries(req.points || {})) points[k] = proj(v);
const routes = {};
const step = req.step || 1.5;   // degrees between interpolated points along each leg (great circle)
for (const [k, legs] of Object.entries(req.routes || {})) {
  const out = [];
  for (let i = 0; i + 1 < legs.length; i++) {
    const it = d3.geoInterpolate(legs[i], legs[i + 1]);
    const dist = d3.geoDistance(legs[i], legs[i + 1]) * 180 / Math.PI;
    const n = Math.max(2, Math.ceil(dist / step));
    for (let j = (i ? 1 : 0); j <= n; j++) out.push(proj(it(j / n)));
  }
  routes[k] = out.filter(p => p);
}
process.stdout.write(JSON.stringify({ shapes, points, routes, clip }));
