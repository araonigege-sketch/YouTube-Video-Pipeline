// Render single frames of the player to JPEG for review: node tools/still.mjs film2/player.html <outdir> <t1> [t2 ...] (seconds)
import { createRequire } from 'node:module'; import { resolve } from 'node:path'; import { pathToFileURL } from 'node:url';
const require = createRequire(import.meta.url); const { chromium } = require('playwright');
const [html, out, ...ts] = process.argv.slice(2);
const b = await chromium.launch({ args: ['--no-sandbox'] }); const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
p.on('pageerror', e => console.error('err', e.message)); p.on('console', m => { if (m.type() === 'error') console.error(m.text()); });
await p.goto(pathToFileURL(resolve(html)).href); await p.evaluate('window.READY');
for (const t of ts) { const f = Math.round(+t * 30); await p.evaluate(async f => { await window.qaFrame(f); window.renderFrame(f); }, f);
  await p.locator('#c').screenshot({ path: `${out}/t${t}.jpg`, type: 'jpeg', quality: 80 }); }
await b.close();
