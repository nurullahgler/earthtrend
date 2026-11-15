"""Turns the forecast files into browser scripts for globe.html, in the same layout as vendor/temp-5deg.js.
   python3 tools/build-forecasts.py <folder with the forecast files>
   Rain Forecast Full Data.json  (observed monthly rain, mm/day, per 5x5 cell, 1990-01 .. 2026-09)
   Rain Forecast Data.json          (rain forecast 2026-2050 per cell: annual_mm, low80_mm, high80_mm; 2026 = Jan-Sep observed)
   Upcoming Years Temp (1).json  (second temperature forecast 2027-2050: OLS constant + linear trend + 3-year harmonic)
-> vendor/rain-5deg.js   window.RAIN5   (obs 1990..2026, proj 2027..2050, lo/hi 2026..2050; value x 10, mm per year)
-> vendor/temp-upcoming.js window.TEMPUP (yearly mean 2027..2050 per cell; value x 100, deg C)
Cell index = row * 72 + col, row from 90S, col from 180W (as temp-5deg.js). Missing = null. Nothing is recomputed: values are the files'.
"""
import json, os, calendar
import sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # the site folder (this script lives in tools/)
if len(sys.argv) < 2: sys.exit('usage: python3 tools/build-forecasts.py <folder with the forecast files>')
SRC = os.path.abspath(sys.argv[1])
cell = lambda lat_min, lon_min: int((lat_min + 90) // 5) * 72 + int((lon_min + 180) // 5) % 72

full = json.load(open(os.path.join(SRC, 'Rain Forecast Full Data.json')))
fc = json.load(open(os.path.join(SRC, 'Rain Forecast Data.json')))
OY0, OY1, PY0, PY1 = 1990, 2026, 2027, 2050
NO, NP, NR = OY1 - OY0 + 1, PY1 - PY0 + 1, PY1 - 2026 + 1
obs, proj, lo, hi = [None] * (2592 * NO), [None] * (2592 * NP), [None] * (2592 * NR), [None] * (2592 * NR)
for c in full:                                   # observed years 1990..2025: 12 months of mm/day x days
    ci = cell(c['lat_min'], c['lon_min'])
    for y in range(OY0, 2026):
        v = [c['data'].get(f'{y}{m:02d}') for m in range(1, 13)]
        if all(x is not None for x in v):
            obs[ci * NO + y - OY0] = round(10 * sum(x * calendar.monthrange(y, m + 1)[1] for m, x in enumerate(v)))
for y in range(2026, PY1 + 1):                   # 2026 (Jan-Sep observed + forecast) and the forecast years
    for r in fc['forecast'][str(y)]:
        ci = cell(r['lat_min'], r['lon_min'])
        if y == 2026: obs[ci * NO + 2026 - OY0] = round(10 * r['annual_mm'])
        else: proj[ci * NP + y - PY0] = round(10 * r['annual_mm'])
        lo[ci * NR + y - 2026] = round(10 * r['low80_mm']); hi[ci * NR + y - 2026] = round(10 * r['high80_mm'])
R = {'parameter': 'PRECTOTCORR', 'unit': 'mm/yr', 'scale': 10, 'years': [OY0, OY1], 'projected': [PY0, PY1], 'range': [2026, PY1], 'partial': {'2026': 9},
     'source': 'Rain Forecast Full Data.json: NASA POWER corrected precipitation (PRECTOTCORR), monthly mm/day per 5 x 5 degree cell, 1990-01 .. 2026-09; yearly = sum of the 12 months (mm/day x days). 2026 = Rain Forecast Data.json (Jan-Sep observed, Oct-Dec forecast).',
     'forecast': 'Rain Forecast Data.json method: ' + fc['method'], 'summary': fc['summary'],
     'layout': 'obs[cell * 37 + (year - 1990)], proj[cell * 24 + (year - 2027)], lo and hi[cell * 25 + (year - 2026)]; value x 10',
     'obs': obs, 'proj': proj, 'lo': lo, 'hi': hi}
open(os.path.join(HERE, 'vendor', 'rain-5deg.js'), 'w').write('window.RAIN5=' + json.dumps(R, separators=(',', ':')) + ';\n')

up = json.load(open(os.path.join(SRC, 'Upcoming Years Temp (1).json')))
yrs = sorted(int(k) for k in up['yearly_mean_T2M']); vals = [None] * (2592 * len(yrs))
for y in yrs:
    for r in up['yearly_mean_T2M'][str(y)]['cells']: vals[cell(r['lat_min'], r['lon_min']) * len(yrs) + y - yrs[0]] = round(100 * r['mean_T2M_C'])
U = {'parameter': 'T2M', 'unit': 'C', 'scale': 100, 'years': [yrs[0], yrs[-1]], 'model': up['model'], 'training_data': up['training_data'],
     'layout': f'vals[cell * {len(yrs)} + (year - {yrs[0]})]; value x 100', 'vals': vals}
open(os.path.join(HERE, 'vendor', 'temp-upcoming.js'), 'w').write('window.TEMPUP=' + json.dumps(U, separators=(',', ':')) + ';\n')
print('rain cells with all 1990-2025 observed:', sum(1 for ci in range(2592) if all(obs[ci * NO + k] is not None for k in range(36))), '| upcoming years', yrs[0], yrs[-1], '| cells', sum(1 for v in vals[::len(yrs)] if v is not None))

# 2026-11-15 (second round): each cell's forecast trend, as the files used it (trend_used), for the globe's forecast years
# -> vendor/forecast-trends.js  window.FTREND = { T2M: {unit, range, vals[2592]}, PRECTOTCORR: {...} }   range = colour-scale end, about the
#    98th percentile of |trend| (T2M 0.84 C/decade, rain 10.5 %/decade), rounded
FT = {}
for key, path, field, unit, rng in [('T2M', 'Realistic Forecast.json', 'trend_used_C_per_decade', '°C/decade', 0.8), ('PRECTOTCORR', 'Rain Forecast Data.json', 'trend_used_pct_per_decade', '%/decade', 10)]:
    v = [None] * 2592
    for t in json.load(open(os.path.join(SRC, path)))['cell_trends']: v[cell(t['lat_min'], t['lon_min'])] = t[field]
    FT[key] = {'unit': unit, 'range': rng, 'source': path + ' cell_trends.' + field, 'vals': v}
open(os.path.join(HERE, 'vendor', 'forecast-trends.js'), 'w').write('window.FTREND=' + json.dumps(FT, separators=(',', ':')) + ';\n')
print('forecast trends:', {k: sum(x is not None for x in v['vals']) for k, v in FT.items()})
