const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const proxy = process.env.HTTPS_PROXY || process.env.https_proxy;
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'], proxy: proxy ? { server: proxy } : undefined });
  const frame = JSON.parse(fs.readFileSync('frame.json')); const style = JSON.parse(fs.readFileSync('style.json'));
  const ctx = await b.newContext({ viewport: { width: frame.w, height: frame.h }, ignoreHTTPSErrors: true });
  const p = await ctx.newPage(); p.on('console', m => { if (m.type() === 'error') console.log('ERR', m.text().slice(0, 200)); });
  await p.goto('file://' + process.cwd() + '/render.html');
  const res = await p.evaluate(([f, s]) => window.go(f, s), [frame, style]);
  console.log(JSON.stringify(res));
  const data = await p.evaluate(() => map.getCanvas().toDataURL('image/png'));
  fs.writeFileSync('basemap.png', Buffer.from(data.split(',')[1], 'base64'));
  fs.writeFileSync('bounds.json', JSON.stringify(res));
  await b.close();
})();
