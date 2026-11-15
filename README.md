# Earth Trend Detective
(DISCLAIMER: CLAUDE CODE WAS USED IN ORDER TO MAKE THIS PROJECT)

NASA Space Apps Challenge 2026, challenge **Be An Earth System Trend Detective!**

A globe that shows what is changing on Earth, where, and by how much, from 1990 to 2050, and what that change means for each
country's harvests.

## Run it

Open the published page, or on your own machine double-click `start.command` (macOS), or from this folder:

```bash
python3 -m http.server 3220
```

Then open http://localhost:3220. No build step and no account. It works offline too, except for the sharp close-up imagery of a
selected country, which comes live from NASA GIBS.

## Who does what

| Where | What |
|---|---|
| Server | Hands out files and nothing else. Any static host works (GitHub Pages, Netlify, a plain web server). No database, no accounts, nothing about a visitor is stored. |
| Visitor's browser | All the work: the globe, colouring the map, the charts, the significance test, the forecast years, the crop detector and the pop-up. The sharper 0.5° grids load only when their trend is chosen. |
| NASA GIBS | Close-up satellite imagery of a selected country, fetched by the browser straight from NASA. |
| CDNs (intro only) | The intro page loads its fonts (Google Fonts) and two Earth images (unpkg). Neither holds it up: without them it uses its own fonts and its own drawn Earth. three.js comes from this site. The globe page needs none of them. |
| Before publishing (`tools/`) | Turning the raw data into the files in `vendor/`. Not needed to view the site. |

## What you can do

Every visit starts with a short intro (`index.html`), also on a reload or a direct link to the globe. While it plays, the browser
quietly fetches the globe's files, so Simulate opens the globe (`globe.html`) from the browser's cache: the camera flies in from afar
while the Earth spins down, then the panels slide in. About tells who we are and what the project does.

The Earth keeps turning, except while a clicked country is popped out (or Earth Spin is off in Configuration).

| On screen | What it shows |
|---|---|
| Logo and name (top right) | Switches between dark and light; the choice is remembered on that browser |
| Trends list (right) | Air temperature, daily maximum temperature, precipitation, root-zone soil wetness, surface sunlight (NASA POWER) |
| Change / Value | The change since the first five years of the range, or the value itself |
| Year range and timeline | Any range from 1990 to 2050. The years after 2026 are under Forecast. Play runs through them. |
| Globe in forecast years | Each cell's forecast trend per decade. A straight-line forecast moves only about 0.02 °C a year, so the yearly values would barely change colour. |
| Chart (right) | The selected country year by year: measured years solid, forecast dashed inside its 80 % range. Temperature also gets a second forecast as a dotted orange line. |
| Under the chart | Whether scientists would call the trend significant, with the odds that chance alone made it |
| Crop detector (bottom right) | For the selected country: each crop's chance of a 2025 harvest 10 % or more under its trend, and how often 2011 to 2024 fell short. Drag its top edge to resize it. |
| Expand | The crop detector in full, with every harvest since 1986 against its trend, and the country's rain and temperature to 2050 |

## Data

| Data | Source | Used for |
|---|---|---|
| Air temperature, rain, soil wetness, sunlight, monthly | [NASA POWER](https://power.larc.nasa.gov/) (MERRA-2 and CERES) | the globe, the chart, the forecasts |
| Satellite imagery | NASA GIBS | the globe's surface |
| Borders | Natural Earth | countries |
| Crop production 1961-2024 | FAOSTAT | the crop detector |
| Vegetation health 1982-2025 | NOAA STAR (VHI) | the crop detector |
| Ocean and air cycles (El Niño, IOD, NAO, tropical Atlantic, PDO, AMO) | NOAA PSL | the crop detector |

## Methods, and how each was tested

**Forecasts (2026-2050).** Seasonal cycle, plus the level of the last 20 years, plus a trend pooled with the neighbouring 5° cells, with an
80 % range for natural swings. Tested by hiding 2017-2025 and forecasting it from 1991-2016, in every 5° cell (`hindcast-forecasts.py`).

| Method | Temperature error | Rain error |
|---|---|---|
| This forecast | 0.593 °C | 197.8 mm/yr |
| A straight line through all years | 0.616 °C | 201.4 mm/yr |
| A robust straight line (Theil-Sen) | 0.623 °C | 205.0 mm/yr |
| The last 20 years, no trend | 0.659 °C | 209.4 mm/yr |

Pooling a cell's trend with its neighbours is what wins: one cell's trend is noisy, and its neighbours steady it.

**Significant or not.** The Mann-Kendall trend test with the Hamed and Rao (1998) correction for runs of similar years, on the measured
years of the chosen range. Forecast years and partly measured years (2026, and 1990 for temperature) are left out. Significant means
p < 0.05: a rise or fall this steady would come from year-to-year chance fewer than 1 time in 20. The code is the EarthTrend engine's
own, copied unchanged, and gives the same p on the same series (Turkey, daily maximum temperature, 1990 to 2025: p 0.0064 in both).

**Crop detector.** A random forest (500 decision trees), trained on harvests up to 2010 and scored on 2011-2024, years it never saw. Before
each season it reads the crop's past harvests, the weather, soil and plant health (NOAA vegetation health) in the three months before
sowing, and El Niño plus five other ocean and air cycles (NOAA PSL indices). Against the earlier formula: ranks country-crops better
(AUC 0.729 vs 0.702), beats each crop's usual shortfall rate by more (Brier skill 0.105 vs 0.069, lower 5 % bound 0.087), and inside one
country picks the bad year a little better than a coin (AUC 0.566 vs 0.498). Its chances run about 4 points high (24 % said, 20 % happened
in 2011-2024: shortfalls were rarer after 2010). It failed our calibration-slope rule (1.34 vs 1.26); we use it anyway by our own decision,
because judged in tenths its percentages are as honest as the formula's and sharper. "Unsure" marks the crops whose trees disagree most;
those cases had twice the error, and no other model we tested (boosting, distributional, the formula) did better on them. History is
leak-free: each past harvest is judged only against the years before it. The chances shown come from the same forest refitted on every
harvest up to 2024. Training code and every test: `EarthTrend/ML` (not part of this site).

## Limits

- The forecasts carry no single wet, dry, hot or cold years. They carry the drift and its range.
- NASA POWER is a reanalysis on a 0.5° grid, not a weather station. A 5° cell averages a lot of ground.
- NASA POWER (MERRA-2) shows little or no warming over much of India for 1991-2025 (about -0.2 to +0.04 °C per decade per 5° cell),
  while station records there show warming. The globe shows the data as it is.
- The crop detector covers countries with 28 years of harvests and at least 50,000 ha of wheat, maize, rice, soybeans, barley,
  sorghum or millet (136 countries).

## Files

| File | Role |
|---|---|
| `globe.html` | the whole interface |
| `index.html` | the intro (front page), with Simulate and About |
| `vendor/temp-5deg.js`, `vendor/rain-5deg.js`, `vendor/temp-upcoming.js`, `vendor/forecast-trends.js` | observed and forecast data per 5° cell |
| `vendor/cropbot.js` | crop detector results |
| `vendor/trends.js`, `vendor/trends-land.js`, `vendor/power-hr/` | NASA POWER yearly values per country, per land point and on the native grid |
| `vendor/countries.js`, `vendor/textures/`, `vendor/three.min.js` | borders, globe imagery, and the three.js 3D library |
| `vendor/logo.jpg`, `vendor/wordmark-dark.png`, `vendor/wordmark-light.png` | the team logo (128 px) and the team's name image, cut out of its background, with a dark-text version for light mode |
| `tools/build-forecasts.py` | `python3 tools/build-forecasts.py <folder with the forecast files>` rebuilds the four 5° files |
| `tools/build-cropbot.mjs` | `node tools/build-cropbot.mjs <folder with shortfall.json and yields.json>` rebuilds `vendor/cropbot.js` |
| `tools/hindcast-forecasts.py`, `tools/hindcast-results.json` | the forecast test above, and its result |
| `CHANGES.md` | what changed and why |

The raw input files (the forecast JSON files, about 60 MB, and the crop model's data) are not in this folder; `vendor/` holds
everything the page needs.

## AI use

Claude (Anthropic) helped write code, data scripts and these texts. Every number on screen comes from the data sources above, through the
scripts in this folder. No NASA logos or mission marks are used. NASA does not endorse this project.
