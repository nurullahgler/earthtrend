"""Which forecast method works best? A hindcast of the three forecast algorithms in REAL/ against TEST's own (2026-11-15).
Rules written before the first run; nothing on the site changes from this (the user asked to see the result first).

Data: yearly means per 5x5 cell from the observed monthly files: fulltempdata.json (air temperature, 1991-2025 full years) and
Rain Forecast Full Data.json (rain, mm/day x days summed per year, 1991-2025). Fit on 1991-2016, score 2017-2025 (9 years never seen).
Methods, rebuilt from each file's own 'method' / 'model' text (the files hold results, not code; where a number is not stated it is
estimated from the file itself, and said so):
  P20   persistence: mean of the last 20 training years (the plain baseline)
  REAL  Realistic Forecast / Rain Forecast: level = mean of the last 20 years, plus a straight-line trend from the middle of those years,
        the trend pooled with the 8 neighbouring cells. The pooling weight is not stated: it is estimated by regressing the file's
        trend_used on trend_local and the neighbours' mean trend_local. Rain: relative trend (% of level) and factor limited to [0.3, 3].
  UPC   Upcoming Years Temp: OLS on the monthly series with a constant, a linear trend and 3 harmonics of the year; for yearly means the
        harmonics average out, so it is the OLS line through all training years.
  TEST  EarthTrend TEST (src/lib/engine/detect.js project): Theil-Sen line through the yearly series, extended.
  HYB1  hybrid, average of REAL, UPC and TEST.
  HYB2  hybrid, REAL's level (last 20 years) + TEST's Theil-Sen slope pooled with the neighbours the way REAL pools.
Score: RMSE over cells and test years, cells weighted by cos(latitude); and the share of cells where each method has the lowest error.
Uncertainty: bootstrap over test years (1,000; years resampled, all cells kept), 90 % interval of each method's RMSE minus REAL's.
   python3 tools/hindcast-forecasts.py <folder with the forecast files and fulltempdata.json>   -> tools/hindcast-results.json"""
import json, os, calendar
import numpy as np
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
if len(sys.argv) < 2: sys.exit('usage: python3 tools/hindcast-forecasts.py <folder with the forecast files and fulltempdata.json>')
SRC = os.path.abspath(sys.argv[1])
TR0, TR1, TE0, TE1 = 1991, 2016, 2017, 2025
cell = lambda la, lo: int((la + 90) // 5) * 72 + int((lo + 180) // 5) % 72

def yearly(path, rain):
    out = np.full((2592, TE1 - TR0 + 1), np.nan)
    for c in json.load(open(path)):
        ci = cell(c['lat_min'], c['lon_min'])
        for y in range(TR0, TE1 + 1):
            v = [c['data'].get(f'{y}{m:02d}') for m in range(1, 13)]
            if all(x is not None for x in v):
                out[ci, y - TR0] = sum(x * calendar.monthrange(y, m + 1)[1] for m, x in enumerate(v)) if rain else sum(v) / 12
    return out

def neighbours(ci):
    r, c = divmod(ci, 72)
    return [rr * 72 + (c + dc) % 72 for rr in (r - 1, r, r + 1) for dc in (-1, 0, 1) if 0 <= rr < 36 and not (rr == r and dc == 0)]

def theil_sen(x, y):
    s = [(y[j] - y[i]) / (x[j] - x[i]) for i in range(len(x)) for j in range(i + 1, len(x))]
    return np.median(s)

def pool_weight(fc_file, rain):
    """the file's own pooling: trend_used ~ a * trend_local + b * mean(neighbours' trend_local)"""
    F = json.load(open(fc_file)); key_l, key_u = ('trend_local_pct_per_decade', 'trend_used_pct_per_decade') if rain else ('trend_local_C_per_decade', 'trend_used_C_per_decade')
    loc = np.full(2592, np.nan); used = np.full(2592, np.nan)
    for t in F['cell_trends']:
        ci = cell(t['lat_min'], t['lon_min']); loc[ci] = t[key_l]; used[ci] = t[key_u]
    nb = np.array([np.nanmean(loc[neighbours(ci)]) for ci in range(2592)])
    ok = np.isfinite(loc) & np.isfinite(used) & np.isfinite(nb)
    A = np.c_[loc[ok], nb[ok]]; w, *_ = np.linalg.lstsq(A, used[ok], rcond=None)
    r2 = 1 - np.sum((used[ok] - A @ w) ** 2) / np.sum((used[ok] - used[ok].mean()) ** 2)
    return w, r2

def run(Y, rain, w):
    yrs = np.arange(TR0, TE1 + 1); tr = (yrs >= TR0) & (yrs <= TR1); te = yrs >= TE0
    n = Y.shape[0]; last20 = (yrs > TR1 - 20) & tr; mid20 = yrs[last20].mean()
    ols = np.full(n, np.nan); ts = np.full(n, np.nan); lev = np.full(n, np.nan); a_ols = np.full(n, np.nan)
    for ci in range(n):
        y = Y[ci, tr]; x = yrs[tr]; ok = np.isfinite(y)
        if ok.sum() < 20: continue
        b, a = np.polyfit(x[ok], y[ok], 1); ols[ci] = b; a_ols[ci] = a
        ts[ci] = theil_sen(x[ok], y[ok]); lev[ci] = np.nanmean(Y[ci, last20])
    rel = lambda s: s / np.where(np.abs(lev) > 1e-9, lev, np.nan)            # rain: relative slope (per year, fraction of level)
    def pooled(s):
        nb = np.array([np.nanmean(s[neighbours(ci)]) if np.isfinite(s[neighbours(ci)]).any() else np.nan for ci in range(n)])
        return w[0] * s + w[1] * np.where(np.isfinite(nb), nb, s)
    P = {}
    T = yrs[te]
    P['P20'] = np.repeat(lev[:, None], len(T), 1)
    if rain:
        fac = lambda sl: np.clip(1 + sl[:, None] * (T[None, :] - mid20), 0.3, 3)
        P['REAL'] = lev[:, None] * fac(pooled(rel(ols)))
        P['HYB2'] = lev[:, None] * fac(pooled(rel(ts)))
    else:
        P['REAL'] = lev[:, None] + pooled(ols)[:, None] * (T[None, :] - mid20)
        P['HYB2'] = lev[:, None] + pooled(ts)[:, None] * (T[None, :] - mid20)
    P['UPC'] = a_ols[:, None] + ols[:, None] * T[None, :]
    med = np.array([np.median(yrs[tr]) for _ in range(n)])
    tsint = np.array([np.nanmedian(Y[ci, tr] - ts[ci] * yrs[tr]) if np.isfinite(ts[ci]) else np.nan for ci in range(n)])
    P['TEST'] = tsint[:, None] + ts[:, None] * T[None, :]
    P['HYB1'] = (P['REAL'] + P['UPC'] + P['TEST']) / 3
    obs = Y[:, te]; lat = (np.arange(n) // 72) * 5 - 87.5; wc = np.cos(np.radians(lat))
    ok = np.isfinite(obs).all(1) & np.all([np.isfinite(p).all(1) for p in P.values()], 0)
    err = {k: (p[ok] - obs[ok]) for k, p in P.items()}; W = wc[ok][:, None] * np.ones((1, len(T)))
    rmse = lambda e, cols=slice(None): float(np.sqrt(np.sum(W[:, cols] * e[:, cols] ** 2) / np.sum(W[:, cols])))
    res = {'cells': int(ok.sum()), 'rmse': {k: rmse(e) for k, e in err.items()}}
    cell_rmse = {k: np.sqrt(np.mean(e ** 2, 1)) for k, e in err.items()}; best = np.argmin(np.array(list(cell_rmse.values())), 0)
    res['bestShare'] = {k: float(np.average(best == i, weights=wc[ok])) for i, k in enumerate(cell_rmse)}
    rng = np.random.default_rng(7); bs = {k: [] for k in err}
    for _ in range(1000):
        cols = rng.integers(0, len(T), len(T)); r0 = rmse(err['REAL'], cols)
        for k in err: bs[k].append(rmse(err[k], cols) - r0)
    res['vsREAL'] = {k: [float(np.quantile(v, 0.05)), float(np.quantile(v, 0.95))] for k, v in bs.items() if k != 'REAL'}
    if rain: res['unit'] = 'mm/yr'
    else: res['unit'] = 'deg C'
    return res

out = {}
for name, path, rain, fc in [('temperature', os.path.join(SRC, 'fulltempdata.json'), False, os.path.join(SRC, 'Realistic Forecast.json')),
                             ('rain', os.path.join(SRC, 'Rain Forecast Full Data.json'), True, os.path.join(SRC, 'Rain Forecast Data.json'))]:
    w, r2 = pool_weight(fc, rain)
    r = run(yearly(path, rain), rain, w); r['poolWeights'] = {'own': float(w[0]), 'neighbours': float(w[1]), 'r2': float(r2)}
    out[name] = r
    print(f"\n{name} ({r['cells']} cells, unit {r['unit']}; REAL pooling estimated from the file: own {w[0]:.2f}, neighbours {w[1]:.2f}, R2 {r2:.3f})")
    for k in ['P20', 'REAL', 'UPC', 'TEST', 'HYB1', 'HYB2']:
        ci = r['vsREAL'].get(k)
        print(f"  {k:5s} RMSE {r['rmse'][k]:8.3f}   best in {100 * r['bestShare'][k]:5.1f} % of cells" + (f"   minus REAL [90 %]: {ci[0]:+.3f} .. {ci[1]:+.3f}" if ci else ''))
json.dump(out, open(os.path.join(HERE, 'hindcast-results.json'), 'w'), indent=1)
