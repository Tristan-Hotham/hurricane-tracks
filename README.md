# Every storm since 1851: where tropical cyclones form, where they hit, and whether they are getting stronger

Every hurricane, typhoon and cyclone in NOAA's International Best Track Archive for Climate Stewardship (IBTrACS v04r01), 13,186 storms and depressions from 1851 to 2025 (and 2026 so far on the map), drawn by Saffir-Simpson category, with where they form, where they make landfall, the strongest on record, the share reaching Category 3+ and 4+ by decade and the latitude at which storms peak. Long-run trends are given only with the caveat that the record before about 1970 misses many storms; comparisons use 1980 onwards.

Interactive page: https://maps.tristanhotham.com/hurricane-tracks/
Paper: https://doi.org/10.5281/zenodo.23858051
Blog post: https://blog.tristanhotham.com/2026/10/31/hurricane-tracks/

## Headline results

- Since 1980, 89.1 storms a year reached tropical storm strength (34 kt) and 47.3 hurricane strength, with no clear trend in the number (+1.1 a decade, 95% interval -0.8 to +2.9). The western North Pacific has 29% of them.
- Storms form in two belts; only 3.8% start within 5 degrees of the equator. The busiest 2.5 degree square is off southern Mexico (7.6 storms a decade).
- Landfalls, 1980 to 2025: China 263 storms (the most), the Philippines 129 at typhoon strength and 67 at Category 3+ (the most); the most-hit coast is Guangdong (118).
- Strongest: Patricia (2015) and Nancy (1961), 185 kt 1-minute wind; Tip (1979), 870 hPa.
- Share of storms reaching Category 4+ (US 1-minute winds): 12.5% in the 1980s, 22.8% in the 2010s; 16.8% in 1980 to 2002 against 21.2% in 2003 to 2025 (p under 0.001). Category 3+ changed little (26.7% against 28.4%, p = 0.21). Most of the rise came between the 1980s and the 1990s, when satellite methods were maturing.
- Latitude of peak intensity: +45 km a decade poleward in the Northern Hemisphere (95% interval +17 to +72), +21 in the Southern; driven by the western North Pacific (+65).
- Before satellites: in the North Atlantic, 12% of 1851 to 1900 storms never came within 500 km of land, against 23% in 1976 to 2025; open-ocean storms were missed. Outside the Atlantic there are no winds before the 1940s or later.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/07_build_site.py`; results embedded; tracks and other data loaded lazily from `data/`). |
| `header.png` | Social card, 1200 x 630. |
| `data/storms.csv` | One row per storm (13,289): IBTrACS id, season, basin, name, dates, genesis, peak winds (US and agency), category, lowest pressure, position of peak, countries hit (1.3 MB). |
| `data/landfalls.csv` | Every landfall by storm and state or province: time, position, wind at landfall (interpolated) and category (1.3 MB). |
| `data/landfall_countries.csv`, `data/landfall_regions.csv` | Landfalls 1980 to 2025 by country and by state or province, by strength. |
| `data/per_year.csv` | Systems, tropical storms and hurricanes per season by basin, 1851 to 2025. |
| `data/shares_by_decade.csv` | Share of storms reaching Category 3+, 4+ and 5 by decade, world and basins, with wind coverage. |
| `data/lmi_latitude.csv` | Mean latitude of lifetime maximum intensity per season and hemisphere, 1980 to 2025. |
| `data/results.json` | Every number used in the page, paper, blog, collage and post. |
| `data/tracks/<decade>.json` | Simplified tracks by decade for the map (2.5 MB in all). |
| `data/search.json`, `data/landfalls.json`, `data/genesis.png`, `data/site.json`, `data/world.json`, `data/countries.json`, `data/cities.json` | Page data. |
| `code/` | Scripts, run in order (below), and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source with figures (`paper/`), blog post, figures and meta (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `qa/` | Screenshots of the page at desktop and phone widths. |

## Method in brief

- Tracks: IBTrACS v04r01, all basins, six-hourly synoptic positions; main and provisional tracks, spur tracks left out. Seasons as in IBTrACS (Southern Hemisphere seasons named after the year they end). Analyses use 1851 to 2025.
- Strength: USA_WIND (1-minute, US agencies) on the Saffir-Simpson scale; WMO_WIND (often 10-minute) only where USA_WIND is missing, for map colours, counts of storms reaching 34 kt and landfalls. Shares by category, latitude of peak and accumulated cyclone energy use USA_WIND only.
- Landfall: each segment intersected with Natural Earth 1:10m country polygons; an entry from the sea (not a land border) while not extratropical; wind interpolated; one count per storm and country (and per storm and state or province).
- Trends: least squares through seasonal values 1980 to 2025, 4,000 bootstrap resamples of seasons; halves compared with a two-proportion test.
- Caveats: heterogeneous agencies and methods; storms missed before about 1970, especially weak ones far from land; satellite methods changed after 1980 too; landfall winds interpolated between six-hourly positions (often below official values); provisional 2025 tracks; no attribution to climate change.

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

Hotham, T. (2026) Every storm since 1851: where tropical cyclones form, where they hit, and whether they are getting stronger. Zenodo. https://doi.org/10.5281/zenodo.23858051

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
