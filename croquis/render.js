const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const H = +fs.readFileSync(path.join(__dirname, 'mapa_localidades.svg'), 'utf8').match(/height="(\d+)"/)[1];
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1728, height: H }, deviceScaleFactor: 2 });
  await p.goto('file://' + path.join(__dirname, 'mapa_localidades.html'));
  await p.pdf({ path: path.join(__dirname, 'mapa_localidades.pdf'), preferCSSPageSize: true, printBackground: true, pageRanges: '1' });
  await p.screenshot({ path: path.join(__dirname, 'mapa_localidades.png'), fullPage: true });
  await b.close();
})();
