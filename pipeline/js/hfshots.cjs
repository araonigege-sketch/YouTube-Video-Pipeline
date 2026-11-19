// node hfshots.cjs <build_dir> <out_dir> <t1> [t2 ...] — screenshots of a HyperFrames build at given times
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const [build, outDir, ...ts] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  await pg.addInitScript(() => { window.__timelines = window.__timelines || {}; });
  pg.on('pageerror', e => console.error('pageerror:', e.message));
  await pg.goto('file://' + path.resolve(build, 'index.html'));
  for (let i = 0; i < 100 && !(await pg.evaluate(() => !!(window.__timelines && window.__timelines.main))); i++) await pg.waitForTimeout(200);
  await pg.evaluate(() => document.fonts.ready);
  for (const ts_ of ts) {
    const t = parseFloat(ts_);
    await pg.evaluate(async (t) => {
      window.__timelines.main.seek(t, false);
      document.querySelectorAll('.clip[data-start]').forEach(el => {
        const s = +el.dataset.start, d = +el.dataset.duration;
        el.style.visibility = (t >= s && t < s + d) ? 'visible' : 'hidden';
      });
      const v = document.getElementById('base');
      if (v && v.readyState >= 1) { v.currentTime = t; await new Promise(r => { v.onseeked = r; setTimeout(r, 2000); }); }
    }, t);
    await pg.screenshot({ path: path.join(outDir, `f_${t.toFixed(2)}.jpg`), type: 'jpeg', quality: 85 });
  }
  await b.close();
})();
