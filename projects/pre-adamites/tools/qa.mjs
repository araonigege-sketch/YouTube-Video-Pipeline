// Framing QA for the Case File player: every shot is rendered at five moments; any key element (text, image, node, pin,
// label, stamp) that leaves the safe area (5% margin) is reported, and so is any frame with no content at all.
//   node tools/qa.mjs [film2/player.html] [--only 120-140] [--out build2/qa.json]
import { createRequire } from 'node:module';
import { writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const args = process.argv.slice(2);
const page_ = resolve(args.find(a => a.endsWith('.html')) || 'film2/player.html');
const onlyArg = args.includes('--only') ? args[args.indexOf('--only') + 1].split('-').map(Number) : null;
const outArg = args.includes('--out') ? args[args.indexOf('--out') + 1] : 'build2/qa.json';
const SAFE = { x0: 96, y0: 54, x1: 1824, y1: 1026 }, TOL = 3;
const CONTENT = new Set(['text', 'image', 'page', 'disc', 'node', 'pin', 'label', 'kicker', 'title', 'stamp', 'map']);

const browser = await chromium.launch({ args: ['--no-sandbox'] });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
page.on('pageerror', e => console.error('page error:', e.message));
await page.goto(pathToFileURL(page_).href + '?qa=1');
await page.evaluate('window.READY');
const shots = await page.evaluate('window.SHOTS.map(s => ({ id: s.id, type: s.type, t0: s.t0, t1: s.t1, anchor: s.anchor, img: s.img || s.clip || null }))');
const issues = [];
for (const s of shots) {
  if (onlyArg && (s.id < onlyArg[0] || s.id > onlyArg[1])) continue;
  const d = s.t1 - s.t0, pts = [Math.min(s.t0 + .6, s.t0 + d * .3), s.t0 + d * .25, s.t0 + d * .5, s.t0 + d * .75, s.t1 - .12];
  for (const t of pts) {
    const f = Math.round(t * 30);
    const boxes = await page.evaluate(`window.qaFrame(${f})`);
    const vis = boxes.filter(b => b.a > .25);
    const out = vis.filter(b => b.imp && (b.x0 < SAFE.x0 - TOL || b.y0 < SAFE.y0 - TOL || b.x1 > SAFE.x1 + TOL || b.y1 > SAFE.y1 + TOL));
    const content = vis.filter(b => CONTENT.has(b.kind));
    if (out.length) issues.push({ id: s.id, type: s.type, t: +t.toFixed(2), kind: 'outside', what: [...new Set(out.map(b => b.kind))].join(','),
      worst: out.map(b => [Math.round(b.x0), Math.round(b.y0), Math.round(b.x1), Math.round(b.y1)]).slice(0, 3), anchor: s.anchor });
    if (!content.length) issues.push({ id: s.id, type: s.type, t: +t.toFixed(2), kind: 'empty', anchor: s.anchor });
  }
}
await browser.close();
writeFileSync(outArg, JSON.stringify(issues, null, 1));
const byShot = new Map(); for (const i of issues) byShot.set(i.id, [...(byShot.get(i.id) || []), i]);
console.log(`QA: ${issues.length} issue(s) in ${byShot.size} shot(s) -> ${outArg}`);
for (const [id, l] of [...byShot].slice(0, 60)) console.log(`  #${id} ${l[0].type} @${l[0].t}s ${[...new Set(l.map(x => x.kind + (x.what ? ':' + x.what : '')))].join(' ')}  "${(l[0].anchor || '').slice(0, 50)}"  ${l[0].worst ? JSON.stringify(l[0].worst[0]) : ''}`);
