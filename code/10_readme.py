"""README.md, LICENSE and reddit/post.md, numbers from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
c, sh, lm, lf, st, gn, m = R["counts"], R["shares"], R["lmi"], R["landfall"], R["strongest"], R["genesis"], R["meta"]
h = sh["halves"]
size = lambda f: f"{os.path.getsize(os.path.join(DATA, f)) / 1e6:.1f} MB"
tsize = sum(os.path.getsize(os.path.join(DATA, "tracks", f)) for f in os.listdir(os.path.join(DATA, "tracks"))) / 1e6
readme = f"""# Every storm since 1851: where tropical cyclones form, where they hit, and whether they are getting stronger

Every hurricane, typhoon and cyclone in NOAA's International Best Track Archive for Climate Stewardship (IBTrACS v04r01), {c['n_systems']:,} storms and depressions from {m['first']} to {m['last']} (and 2026 so far on the map), drawn by Saffir-Simpson category, with where they form, where they make landfall, the strongest on record, the share reaching Category 3+ and 4+ by decade and the latitude at which storms peak. Long-run trends are given only with the caveat that the record before about 1970 misses many storms; comparisons use 1980 onwards.

Interactive page: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}

## Headline results

- Since 1980, {c['sat_ts_mean']:.1f} storms a year reached tropical storm strength (34 kt) and {c['sat_hu_mean']:.1f} hurricane strength, with no clear trend in the number ({c['sat_ts_trend']['per_dec']:+.1f} a decade, 95% interval {c['sat_ts_trend']['lo']:+.1f} to {c['sat_ts_trend']['hi']:+.1f}). The western North Pacific has {c['basin_ts_share']['WP']:.0f}% of them.
- Storms form in two belts; only {gn['eq5_pct']:.1f}% start within 5 degrees of the equator. The busiest 2.5 degree square is off southern Mexico ({gn['top'][0]['per_dec']:.1f} storms a decade).
- Landfalls, 1980 to {m['last']}: China {lf['top'][0]['ts']} storms (the most), the Philippines {lf['top_hu'][0]['hu']} at typhoon strength and {lf['top_hu'][0]['mj']} at Category 3+ (the most); the most-hit coast is Guangdong ({lf['top_regions'][0]['ts']}).
- Strongest: Patricia (2015) and Nancy (1961), {st['wind'][0]['kt']} kt 1-minute wind; Tip (1979), {st['pressure'][0]['pres']} hPa.
- Share of storms reaching Category 4+ (US 1-minute winds): {sh['global'][0]['s4']:.1f}% in the 1980s, {sh['global'][3]['s4']:.1f}% in the 2010s; {h['s4_1']:.1f}% in {h['h1']} against {h['s4_2']:.1f}% in {h['h2']} (p {fmt(h['p4'], 'p3')}). Category 3+ changed little ({h['s3_1']:.1f}% against {h['s3_2']:.1f}%, p = {h['p3']:.2f}). Most of the rise came between the 1980s and the 1990s, when satellite methods were maturing.
- Latitude of peak intensity: {lm['N_trend']['km_per_dec']:+.0f} km a decade poleward in the Northern Hemisphere (95% interval {lm['N_trend']['km_lo']:+.0f} to {lm['N_trend']['km_hi']:+.0f}), {lm['S_trend']['km_per_dec']:+.0f} in the Southern; driven by the western North Pacific ({lm['basins']['WP']['km_per_dec']:+.0f}).
- Before satellites: in the North Atlantic, {c['na_far_pct_1851_1900']:.0f}% of 1851 to 1900 storms never came within 500 km of land, against {c['na_far_pct_1976_2025']:.0f}% in 1976 to 2025; open-ocean storms were missed. Outside the Atlantic there are no winds before the 1940s or later.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/07_build_site.py`; results embedded; tracks and other data loaded lazily from `data/`). |
| `header.png` | Social card, 1200 x 630. |
| `data/storms.csv` | One row per storm ({R['meta']['n_storms']:,}): IBTrACS id, season, basin, name, dates, genesis, peak winds (US and agency), category, lowest pressure, position of peak, countries hit ({size('storms.csv')}). |
| `data/landfalls.csv` | Every landfall by storm and state or province: time, position, wind at landfall (interpolated) and category ({size('landfalls.csv')}). |
| `data/landfall_countries.csv`, `data/landfall_regions.csv` | Landfalls 1980 to {m['last']} by country and by state or province, by strength. |
| `data/per_year.csv` | Systems, tropical storms and hurricanes per season by basin, {m['first']} to {m['last']}. |
| `data/shares_by_decade.csv` | Share of storms reaching Category 3+, 4+ and 5 by decade, world and basins, with wind coverage. |
| `data/lmi_latitude.csv` | Mean latitude of lifetime maximum intensity per season and hemisphere, 1980 to {m['last']}. |
| `data/results.json` | Every number used in the page, paper, blog, collage and post. |
| `data/tracks/<decade>.json` | Simplified tracks by decade for the map ({tsize:.1f} MB in all). |
| `data/search.json`, `data/landfalls.json`, `data/genesis.png`, `data/site.json`, `data/world.json`, `data/countries.json`, `data/cities.json` | Page data. |
| `code/` | Scripts, run in order (below), and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source with figures (`paper/`), blog post, figures and meta (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `qa/` | Screenshots of the page at desktop and phone widths. |

## Method in brief

- Tracks: IBTrACS v04r01, all basins, six-hourly synoptic positions; main and provisional tracks, spur tracks left out. Seasons as in IBTrACS (Southern Hemisphere seasons named after the year they end). Analyses use {m['first']} to {m['last']}.
- Strength: USA_WIND (1-minute, US agencies) on the Saffir-Simpson scale; WMO_WIND (often 10-minute) only where USA_WIND is missing, for map colours, counts of storms reaching 34 kt and landfalls. Shares by category, latitude of peak and accumulated cyclone energy use USA_WIND only.
- Landfall: each segment intersected with Natural Earth 1:10m country polygons; an entry from the sea (not a land border) while not extratropical; wind interpolated; one count per storm and country (and per storm and state or province).
- Trends: least squares through seasonal values 1980 to {m['last']}, 4,000 bootstrap resamples of seasons; halves compared with a two-proportion test.
- Caveats: heterogeneous agencies and methods; storms missed before about 1970, especially weak ones far from land; satellite methods changed after 1980 too; landfall winds interpolated between six-hourly positions (often below official values); provisional {m['last']} tracks; no attribution to climate change.

## How to rerun

Needs Python 3 with numpy, pandas, scipy, shapely 2, pyproj, matplotlib, fontTools and Pillow, xelatex and pdftotext; node with Playwright for `code/qa.js`. Raw inputs are read in place (paths in `code/common.py`): `/home/claude/newdata/raw8/hurricanes/ibtracs_6hourly.tsv` (IBTrACS, six-hourly extract) and Natural Earth in `/home/claude/newdata/raw/geo/`. Intermediate files go to `/dev/shm/hurricanes/work` (set `HURTMP`).

```
python3 code/01_tracks.py      # parse IBTrACS, winds and categories, one row per storm
python3 code/02_geo.py         # world outline, country and town names for the page
python3 code/03_landfall.py    # landfalls: data/landfalls.csv
python3 code/04_analysis.py    # counts, genesis, landfalls, strongest, shares, latitude of peak, ACE
python3 code/05_tiles.py       # tracks by decade, search index, landfall points, genesis overlay
python3 code/06_results.py     # data/results.json, checks on statements in words
python3 code/07_build_site.py  # index.html
python3 code/08_figures.py     # header, blog and paper figures
python3 code/09_paper.py       # paper PDF
python3 reddit/collage.py      # collage (labels checked against tracks, land and each other)
python3 code/10_readme.py      # README, LICENSE, Reddit post
python3 code/11_release.py     # blog post, Zenodo files
```

## Sources and licences

- NOAA National Centers for Environmental Information, International Best Track Archive for Climate Stewardship (IBTrACS), version 4r01. Knapp, K. R., Kruk, M. C., Levinson, D. H., Diamond, H. J. and Neumann, C. J. (2010) The International Best Track Archive for Climate Stewardship (IBTrACS): unifying tropical cyclone best track data. Bulletin of the American Meteorological Society 91, 363 to 376; Gahtan, J. et al. (2024) IBTrACS Project, Version 4r01. NOAA data, no copyright restrictions.
- Natural Earth countries, states and provinces, land and populated places (public domain).
- Wikipedia contributors, "Tropical cyclone" and "Saffir-Simpson scale" (CC BY-SA 4.0): category thresholds and background only.
- Base map tiles on the page: © Esri.

## Citation

Hotham, T. (2026) Every storm since 1851: where tropical cyclones form, where they hit, and whether they are getting stronger. Zenodo. https://doi.org/{DOI}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
for bad in ("—", "–", "--", "DSIT", "DCMS"):
    assert bad not in readme.replace("```", "").replace("|---|---|", ""), bad
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
lic = """MIT License

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


This licence covers the code in code/, reddit/collage.py and the page scripts.
The text of the page, the figures and the derived data files in data/ are
released under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/).
They are derived from IBTrACS (NOAA National Centers for Environmental
Information; Knapp et al. 2010), NOAA data with no copyright restrictions,
and from Natural Earth (public domain).
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)

post = f"""## Title

[OC] Every hurricane, typhoon and cyclone since 1851 ({c['n_systems']:,} storms). Since 1980 the share reaching Category 4 or 5 rose from {sh['global'][0]['s4']:.0f}% in the 1980s to {sh['global'][3]['s4']:.0f}% in the 2010s, but the number of storms hasn't changed

## Body

Every track in NOAA's global best track archive (IBTrACS v04r01), coloured by Saffir-Simpson category at every six-hourly point. About {c['sat_ts_mean']:.0f} storms a year reach tropical storm strength, and that number has no clear trend since 1980. What has changed: using only the US agencies' 1-minute winds, {h['s4_1']:.1f}% of storms reached Category 4+ in {h['h1']} against {h['s4_2']:.1f}% in {h['h2']}, and the latitude where storms peak has moved about {lm['N_trend']['km_per_dec']:.0f} km a decade poleward in the Northern Hemisphere, mostly in the western Pacific. China gets the most landfalls ({lf['top'][0]['ts']} since 1980), the Philippines the most at typhoon strength ({lf['top_hu'][0]['hu']}). Big caveats: before satellites (about 1970) many storms far from land were never recorded, so I don't compare the early record; most of the Category 4+ rise came between the 1980s and 1990s, when satellite methods were maturing; the Category 3+ share barely moved. Interactive map with every track, a season player and landfalls: https://maps.tristanhotham.com/hurricane-tracks/

## Source comment

Source: NOAA NCEI, International Best Track Archive for Climate Stewardship (IBTrACS) v04r01, all basins, 6-hourly positions, {m['first']} to {m['last']} (Knapp et al. 2010; Gahtan et al. 2024). NOAA data, no copyright restrictions. Land and coastlines: Natural Earth. Category from USA_WIND (1-minute sustained wind); landfalls by intersecting each track segment with Natural Earth coastlines. Trends 1980 to {m['last']} with bootstrap intervals; halves compared with a two-proportion test. Collage labels were placed by a script that checks they sit on open sea, away from dense tracks, land and each other.

Tools: Python (pandas, shapely, pyproj, matplotlib); Leaflet for the interactive map.

Interactive version: https://maps.tristanhotham.com/hurricane-tracks/
Paper: https://doi.org/{{10.5281/zenodo.23858051}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/hurricane-tracks/}}
"""
for bad in ("—", "–", "--"):
    assert bad not in post, bad
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
print("README", len(readme.split()), "words; post title", len(post.splitlines()[2]), "chars")
