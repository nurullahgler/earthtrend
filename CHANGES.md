# Integration of 15 Nov 2026: what changed, file by file

Request: put `Rain Forecast Data.json` / `Rain Forecast Full Data.json` (rain), `Realistic Forecast.json` and `Upcoming Years Temp (1).json`
into the interface (`globe.html`), connect CountryBot, and compare the forecast algorithms with TEST's own to see whether a hybrid works.
**Second round (same day):** the country details open as a pop-up over the globe from an **Expand** button under the chart, not in
a new tab. **Third round:** everything that found nothing or is unrelated was removed from the site: causes of death (WHO), crops vs deaths,
and the political model. The pop-up shows only the country's rain and air temperature, observed and forecast.

Run it: `python3 -m http.server 3220 --directory REAL/nasa`, then open **http://localhost:3220/globe.html**.

## The data files themselves
Not edited. `Realistic Forecast.json` is byte-identical to `nasa/realisticforecast.json`, which `vendor/temp-5deg.js` was already built
from, so air temperature on the globe was already this forecast.

## Edits outside the data files

| file | new / edited | what | why |
|---|---|---|---|
| `nasa/globe.html` | edited | Every edit is marked `2026-11-15` in a comment. (1) Loads `vendor/rain-5deg.js` and `vendor/temp-upcoming.js`. (2) The code that unpacked the 5° temperature file now unpacks any 5° file (`build5`, `RAW5`, `f5`), so **Precipitation** gets the same treatment as air temperature: observed 1990–2026, forecast years 2027–2050 under "Forecast", the 80 % range in the chart and in the detail. Its map "Change" is in % (as Precipitation already was), not in mm. (3) For air temperature the chart also draws **Upcoming Years Temp** as a dotted orange line next to the Realistic forecast (your choice). (4) **An Expand button under the chart (bottom right, shown when a country is selected) opens the country pop-up over the globe.** The globe stays visible behind a light dim. It closes with Close, Esc, or a click on the globe. The pop-up shows the selected country's air temperature (observed, Realistic forecast with its 80 % band, Upcoming Years dotted) and rain (observed, forecast with its 80 % band). | your request |
| `nasa/globe.html` | edited | The chart click still moves the timeline to that year, as it did before. The first round had changed this; it is reverted. | |
| `nasa/globe.html` | edited | Side effect: **Precipitation on the map now uses the 5° rain cells** (like air temperature), not the sharper 0.5° POWER grid (`vendor/power-hr/PRECTOTCORR.js`), because only the 5° data have forecast years. Its series now starts in 1990, not 1981. | so the observed and forecast years come from one dataset |
| `nasa/countrybot.html` | created in round 1, **deleted** in round 2 | the separate tab is replaced by the pop-up | your request |
| `nasa/build-forecasts.py` | new | Builds `vendor/rain-5deg.js` (same layout as `temp-5deg.js`) and `vendor/temp-upcoming.js` from the files in `REAL/`. Copies the values only; recomputes nothing. | the page reads scripts, like `temp-5deg.js` |
| `nasa/vendor/rain-5deg.js`, `nasa/vendor/temp-upcoming.js` | new (generated) | outputs of the script above | |
| `CountryBot/scripts/export-web.mjs`, `nasa/vendor/countrybot.js` | created in rounds 1–2, **deleted** in round 3 | the cause-of-death, crops-vs-deaths and political results are no longer on the site | your request |
| `nasa/hindcast-forecasts.py`, `nasa/hindcast-results.json` | new | The algorithm comparison below. Changes nothing on the site. | your request ("show me first") |
| `Documents/.claude/launch.json` | edited | added `earthtrend-real` (static server on port 3220) | to open it in the preview |

Nothing was ported from TEST into the site. Every part you asked for had a counterpart in REAL.

## Forecast algorithms: yours vs TEST's, and hybrids (hindcast: fit 1991–2016, score 2017–2025, every 5° cell)

The JSON files hold results, not code, so each method was rebuilt from its own `method` / `model` text. The Realistic method's neighbour
pooling weight is not stated in the file, so I estimated it from the file's own `trend_local` vs `trend_used` (temperature: 0.20 own + 0.74
neighbours, R² 0.94; rain: 0.19 own + 0.42 neighbours, R² 0.78).

| method | temperature RMSE °C | vs Realistic [90 %] | rain RMSE mm/yr | vs Realistic [90 %] | why |
|---|---|---|---|---|---|
| last-20-year mean (no trend) | 0.659 | +0.035 to +0.096 | 209.4 | +4.0 to +18.5 | ignores warming, so its errors grow with the years |
| **Realistic / Rain Forecast (yours)** | **0.593** | — | **197.8** | — | a level from the last 20 years plus a trend pooled with neighbouring cells: one cell's trend is noisy, its neighbours steady it |
| Upcoming Years (OLS line, all years) | 0.616 | +0.013 to +0.032 | 201.4 | +0.1 to +7.5 | the line's level is pulled by the early 1990s; no pooling |
| TEST (Theil–Sen line, EarthTrend) | 0.623 | +0.020 to +0.039 | 205.0 | +2.8 to +11.7 | robust slope, but per cell with no pooling, so the slopes are noisier |
| hybrid 1: mean of the three | 0.605 | +0.006 to +0.018 | 198.0 | −2.3 to +3.0 | averaging with two weaker methods costs a little |
| hybrid 2: your level + TEST's robust slope, pooled your way | 0.594 | −0.000 to +0.002 | 197.9 | −0.6 to +0.8 | the same as yours: pooling, not the slope method, makes the difference |

**Verdict:** your Realistic method is the best of these, for temperature and rain, and no hybrid beats it, so the site keeps it.
The lesson runs the other way: TEST's projection should pool trends with neighbouring cells. I changed nothing in TEST.

Not checked: the 80 % ranges (whether 80 % of the 2017–2025 values fall inside them). That is the next test if you want it.

## Things in the data to know about
- **Turkey rain 2026: +67 % vs 1990–94.** The file's January–September 2026 months match the observed months exactly. They are very wet
  (534 mm by September in the central cells vs 338 mm in all of 2025). This is the data's own number, not a bug, and I have not checked it
  against another source.

## Round 4 (same day)
| file | new / edited | what |
|---|---|---|
| `nasa/globe.html` | edited | **Bottom-right panel = crop detector.** For the selected country it shows each crop's chance of a harvest at least 10 % below trend in 2025, the share of 2011–2024 that fell short ("seen"), and the main crop's production vs trend per year, with shortfall years in red. Expand opens the full detector plus rain and air temperature. The original trend chart is kept in the code as `renderTrendChart` but no longer shown. |
| `nasa/globe.html` | edited | **Forecast years show each cell's forecast trend per decade** (°C/decade, %/decade for rain) on their own colour scale and legend, instead of the year's value, which barely moves (0.02 °C a year). Observed years are unchanged. |
| `nasa/build-cropbot.mjs` → `nasa/vendor/cropbot.js` | new | Crop detector data. **Source: TEST, not REAL**: `TEST/data/crops/shortfall.json` (TEST `bench/run-r17.js`: the political model's machinery turned into a crop shortfall warning) and `TEST/data/crops/yields.json` (FAOSTAT production). REAL has no crop detector of its own. |
| `nasa/build-forecasts.py` → `nasa/vendor/forecast-trends.js` | edited / new | each cell's `trend_used` from Realistic Forecast and Rain Forecast Data |
| `CountryBot/scripts/export-web.mjs`, `nasa/vendor/countrybot.js` | briefly re-created with political data, then **deleted** | that was a mistake; the panel hosts the crop detector |

## Round 5 (same day)
| file | new / edited | what |
|---|---|---|
| `nasa/globe.html` | edited | The trend chart with its 2050 forecasts is back in its place (round 4 had replaced it). The crop detector now has its own panel under the chart, bottom right. Drag its top edge to resize it (120 px up to 75 % of the window); the size is remembered, and double-click resets it. Expand sits in that panel. |
| `nasa/globe.html` | edited | The detail rows keep the year's value and change in forecast years and add the forecast trend. The chart keeps °C and mm; only the globe and the pointer show the per-decade trend. |
| `nasa/globe.html` | edited | Text rewritten to the CarMaker rules: plain words, no quote marks, no arrows, nothing said twice, sources named. The Upcoming Years model note was in Turkish in the data file and is now in English. The page title is Earth Trend Detective. |
| `nasa/README.md`, `nasa/start.command`, `nasa/index.html` | new | Submission README (how to run, what is on screen, data, methods with their test numbers, limits, AI use), a double-click starter, and an index page that opens the globe, which hosting such as GitHub Pages needs |

## Round 6 (same day)
| file | new / edited | what |
|---|---|---|
| `nasa/globe.html` | edited | A sentence under the trend chart says whether scientists would call the trend significant, with the odds that chance alone made it. The test is Mann-Kendall with the Hamed and Rao correction, ported unchanged from TEST `src/lib/engine/stats.js` (the interface may not import the engine, per HIERARCHY.md). It uses the measured years of the range only, leaving out forecast years and partly measured years. It matches TEST's result on the same series (Turkey daily maximum temperature 1990 to 2025, p 0.0064). |
| `nasa/README.md` | edited | the test added to What you can do and Methods |

## Round 7: the final folder (same day)
This folder (`REAL/final`) is the one to publish. It holds only what the page loads, plus the build tools.

| change | why |
|---|---|
| The JSON hierarchy layer (`hierarchy/`, `HIERARCHY.md`, `check-hierarchy.py`, per-user folders) is not here | the page never reads it. Data goes straight from the build tools into `vendor/`, and there are no users or accounts on a static site |
| `vendor/power-hr/PRECTOTCORR.js` (10 MB) is not here | rain comes from the 5° rain data since round 1 |
| The input files (forecast JSON, `fulltempdata.json`, the copy of TEST) are not here | not needed to view the site, about 60 MB more. The tools take their folder as an argument |
| `tools/` scripts take their input folder as an argument; `build-cropbot.mjs` has the smoothing function copied in, so it no longer needs the EarthTrend engine next to it | so they run from this folder anywhere. Checked: they rebuild `vendor/` byte for byte (cropbot apart from its build time) and the hindcast gives identical results |
| No blanket preload of the 0.5° grids | every visitor used to download 30 MB on arrival; now a grid loads when its trend is pointed at or chosen |
| The Earth keeps turning unless Earth Spin is off in Configuration | asked for. It used to stop while held, pointed at or focused. A turn towards a country rides along with the spin, and the lifted country map cancels the spin, so it stays put in front of you |
| `.nojekyll` | GitHub Pages serves the files as they are |

## Round 8: logo and light mode (same day)
| change | why |
|---|---|
| The team logo with EarthTREND (Earth in the text colour, TREND in the logo's teal) sits at the top right. Clicking it switches between dark and light, and the choice is remembered. `vendor/logo.jpg` is the supplied image cut down to 96 px (6 KB) | asked for |
| Light mode: every colour that was written in place (panel glass, hovers, pop-up, chart grid lines, credits shadow, significance colours, the space behind the globe) is now a named variable with a dark and a light value. Charts and the pop-up redraw when the mode changes | so nothing stays dark-on-dark or white-on-white |
| The country name next to the timeline is cut off instead of running under the logo when the window is narrow | it overlapped at 800 px |
| README: the logo switch, and a data note that NASA POWER shows almost no warming over India for 1991-2025 while station records do | found while checking India; the data is shown as it is |

## Round 9: the intro (same day)
| change | why |
|---|---|
| `intro.html` is now the front page, `index.html`. Its animation, stars, buttons and layout are unchanged | asked for |
| Simulate opens the globe; it used to only send an event | that is what the button is for |
| About: the Lorem ipsum placeholder text is replaced with real text. What is our project comes from the README facts. Our story has two plain sentences, because only the team can tell its story; replace them freely | placeholder text cannot go public (CarMaker text rules) |
| The intro keeps its own three.js r128 from cdnjs. The local `vendor/three.min.js` is a 2023 version whose lighting would change the intro's look | keeps the intro as designed |
| `vendor/logo.jpg` is rebuilt from the original logo file at 128 px, and both pages use it as the tab icon | sharper on high-density screens |
| `start.command` opens the front page | |

## Round 10: the intro on every visit (same day)
| change | why |
|---|---|
| `globe.html` sends the visitor to the intro unless they just pressed Simulate. Simulate leaves a one-time pass in the tab's session storage, and the globe uses it up on arrival, so a reload or a direct link to the globe plays the intro again. If the browser blocks session storage, the globe opens rather than looping | asked for: the intro opens every time someone loads the site |

## Round 11: name image, spawn, faster start (same day)
| change | why | measured |
|---|---|---|
| The name next to the logo is the team's own image (`WhatsApp Image 2026-11-15 at 02.22.32.jpeg`), cut out of its dark background into a transparent PNG; bright stars that survived the cut (70 pixels) were removed. Light mode gets a copy with the white letters turned dark and the teal a little deeper. Shown 14 px tall from 32 px files (12 KB and 9 KB) | asked for; a dark box would sit on the light header | |
| The Earth keeps turning except while a clicked country is popped out (or Earth Spin is off) | asked for | checked: frames 8 s apart identical with Brazil popped out |
| Simulate plays a short exit (the scene falls back and fades), then the globe spawns in: it starts faint and far away, the camera flies in over 2.2 s while the Earth spins down to its usual pace, and the bar, side panel and corners slide in after it. It starts once the first imagery is on the globe, or after 2.5 s at the latest. Visitors with reduced motion get the globe directly | asked for | |
| While the intro plays (7 s), it fetches the globe's 12 files at low priority (link prefetch, or plain fetch where the browser has no prefetch), so Simulate opens from the browser's cache | hide the download in the intro | the files total 10.8 MB, about 4.1 MB compressed (GitHub Pages compresses). After the intro, every globe file came from the prefetch: on the local server only a 300-byte "still the same?" check per file; on a host that lets browsers keep files for a while (GitHub Pages: 10 minutes) not even that. Without the prefetch a visitor on 10 Mbit/s would wait about 3 s for the download alone (estimated from the size) |
| The timeline's minimum width is 150 px instead of 200 px | the name image fits at 800 px wide | |
| `.gitignore` with `.DS_Store`; macOS folder files removed | not part of the site | |
| `favicon.ico`, made from the logo | some browsers ask for it regardless of the page icon, and it was the last 404 | |

## Round 12: stress test (same day)
The live site (https://nurullahgler.github.io/earthtrend/) was checked with single page loads only, a handful of requests, so GitHub sees an
ordinary visitor. Every heavy test (hundreds of country clicks, every setting) ran on a local copy of this folder.

### Fixes
| change | why | measured |
|---|---|---|
| A popped-out country's mesh is split along its longest edge only, until every edge is short enough. It used to split every triangle into four | long thin border triangles were split far past need, so large countries froze the page when clicked | Russia 612,000 triangles and 2.3 s to build, now 77,000 and 0.18 s. Turkey 97,000, now 19,000 |
| The mesh's shared-midpoint lookup uses a number key instead of a text key | text keys made a new string per edge | part of the 0.18 s above |
| Hovering a country builds its pop-out mesh ahead of the click also when the forecast trend map is on; only the satellite close-ups are skipped there | hover pre-build was skipped entirely in forecast years, so the click paid the full build | |
| Phones and windows up to 760 px wide: the header goes on two rows, the globe takes the top, and the trends, chart and crop detector sit in a sheet underneath that scrolls as one. The resize grip and credits are hidden there; Exit focus moves to the right corner above the sheet | at 375 px the side panel covered the globe and the header ran off screen | checked at 375 x 812 |

### Checks that passed (local copy)
| check | result | why it passed |
|---|---|---|
| All 242 countries selected one after another, including Antarctica, Fiji and Russia across the date line, and the smallest islands | no errors | every country has a border in `countries.js`; those without crop data show the no-data line |
| 75 selections in a row, 4 rounds | 3.1 s in all, memory 222 to 290 MB, flat across rounds | caches are capped (12 meshes, 8 imagery sets), so old ones are freed |
| 6 world views, 8 regions, a search with no match | each view 0.1 to 0.3 s, no errors | |
| 5 trends x Change / Value x 4 year ranges, Earth Spin on and off | no errors; the significance line leaves out forecast and part years each time | |
| Keyboard: arrows move the year, Space plays, Esc closes the pop-up first, then leaves focus | as described | |
| Crop panel grip: drag, keys, double-click reset; Expand and Close | size kept after reload | |

### Checks that passed (live site, a few single loads)
| check | result | why it passed |
|---|---|---|
| Files on the live site vs this folder | all 23 identical | the team pushed this folder unchanged |
| Compression and caching | gzip on, browsers keep files 10 minutes | GitHub Pages defaults |
| Intro load | 0.46 s | |
| Prefetch during the intro | 4.3 MB compressed, done at 1.6 s, well before the 7 s intro ends | link prefetch at low priority |
| Globe after Simulate | 13 of 13 files from the browser cache, globe ready at 0.82 s | the prefetch above |

### Not checked
| what | why |
|---|---|
| Frame rate while the globe spins | the preview pane was hidden during the tests, which slows its timers to about 1 per second, so frame timings from it mean nothing |
| A real phone | only the browser's 375 px phone size was used |
| The fixes on the live site | they are in this folder; the live site has them only after the team pushes it again |

