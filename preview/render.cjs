// Render every view of a built map to PNG.  node preview/render.cjs <out/map dir> [dpr] [view names...]
// Serves the repo root over a local HTTP server (ES modules + fetch need http, not file://).
const http = require('http'), fs = require('fs'), path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const dir = path.resolve(process.argv[2]);
const dpr = +(process.argv[3] || 1);
const only = process.argv.slice(4);
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png' };

const server = http.createServer((req, res) => {
  const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
});

server.listen(0, async () => {
  const port = server.address().port;
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: dpr });
  page.on('console', m => { if (m.type() === 'error') console.log('page error:', m.text()); });
  page.on('pageerror', e => console.log('page exception:', e.message));
  const rel = path.relative(ROOT, path.join(dir, 'parts.json')).split(path.sep).join('/');
  await page.goto(`http://127.0.0.1:${port}/preview/viewer.html?map=/${rel}`);
  await page.waitForFunction('window.READY === true', null, { timeout: 180000 });
  const views = await page.evaluate('window.VIEWS');
  fs.mkdirSync(path.join(dir, 'previews'), { recursive: true });
  for (let i = 0; i < views.length; i++) {
    if (only.length && !only.includes(views[i].name)) continue;
    await page.evaluate(`window.setView(${i})`);
    const file = path.join(dir, 'previews', `${views[i].name}.jpg`);
    await (await page.$('canvas')).screenshot({ path: file, type: 'jpeg', quality: 86 });
    console.log('rendered', file);
  }
  console.log('parts', await page.evaluate('window.PARTS'));
  await browser.close();
  server.close();
});
