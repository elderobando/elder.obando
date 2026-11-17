const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1728, height: 2304 }, deviceScaleFactor: 2 });
  await p.goto('file://' + path.join(__dirname, 'mapa_localidades.html'));
  await p.pdf({ path: path.join(__dirname, 'mapa_localidades.pdf'), width: '18in', height: '24in', printBackground: true, pageRanges: '1' });
  await p.screenshot({ path: path.join(__dirname, 'mapa_localidades.png'), fullPage: false });
  await b.close();
})();
