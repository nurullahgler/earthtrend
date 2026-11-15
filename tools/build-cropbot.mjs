/* Crop detector data for globe.html: vendor/cropbot.js (window.CROPBOT).
 *   node tools/build-cropbot.mjs <EarthTrend crop data folder: shortfall.json and yields.json>
 * shortfall.json: each country-crop's chance of a harvest 10 % or more under its trend next season, from the EarthTrend crop shortfall
 * model (the political-risk machinery retrained on harvests; trained to 2010, tested 2011-2024). yields.json: FAOSTAT production.
 * Nothing new is computed: probabilities are copied; each year's departure uses the model's own definition (production against its
 * Gaussian 5-year smooth, gaussSmooth copied from the EarthTrend engine).
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const dir = process.argv[2];
if (!dir) { console.error('usage: node tools/build-cropbot.mjs <folder with shortfall.json and yields.json>'); process.exit(1); }
const isNum = (x) => typeof x === 'number' && Number.isFinite(x);
function gaussSmooth(y, w) {
  const n = y.length, out = Array(n).fill(NaN), s = w / 2;
  for (let i = 0; i < n; i++) {
    let num = 0, den = 0;
    for (let j = Math.max(0, i - 3 * w); j <= Math.min(n - 1, i + 3 * w); j++) { if (!isNum(y[j])) continue; const k = Math.exp(-0.5 * ((j - i) / s) ** 2); num += k * y[j]; den += k; }
    if (den > 0) out[i] = num / den;
  }
  return out;
}
const SF = JSON.parse(readFileSync(join(dir, 'shortfall.json'), 'utf8')), Y = JSON.parse(readFileSync(join(dir, 'yields.json'), 'utf8'));
const out = {};
for (const [iso, crops] of Object.entries(SF.countries)) {
  out[iso] = {};
  for (const [crop, v] of Object.entries(crops)) {
    const prod = Array.from({ length: Y.y1 - Y.y0 + 1 }, (_, k) => { const x = Y.countries[iso]?.[crop]?.prod?.[k]; return isNum(x) && x > 0 ? x : NaN; });
    const sm = gaussSmooth(prod, 5), dep = prod.map((x, k) => (isNum(x) && isNum(sm[k]) ? +(100 * (x / sm[k] - 1)).toFixed(1) : null));
    out[iso][crop] = { p: v.p, u: !!v.u, observedRate2011_24: v.observedRate2011_24, y0: 1986, departure: dep.slice(1986 - Y.y0), lastProdT: isNum(prod.at(-1)) ? Math.round(prod.at(-1)) : null };
  }
}
writeFileSync(new URL('../vendor/cropbot.js', import.meta.url), 'window.CROPBOT=' + JSON.stringify({ built: new Date().toISOString(), forYear: SF.forYear, event: SF.event, validation: SF.validation, yearsTo: Y.y1, countries: out }) + ';\n');
console.log('countries', Object.keys(out).length);
