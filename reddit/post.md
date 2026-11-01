## Title

[OC] Every hurricane, typhoon and cyclone since 1851 (13,186 storms). Since 1980 the share reaching Category 4 or 5 rose from 12% in the 1980s to 23% in the 2010s, but the number of storms hasn't changed

## Body

Every track in NOAA's global best track archive (IBTrACS v04r01), coloured by Saffir-Simpson category at every six-hourly point. About 89 storms a year reach tropical storm strength, and that number has no clear trend since 1980. What has changed: using only the US agencies' 1-minute winds, 16.8% of storms reached Category 4+ in 1980 to 2002 against 21.2% in 2003 to 2025, and the latitude where storms peak has moved about 45 km a decade poleward in the Northern Hemisphere, mostly in the western Pacific. China gets the most landfalls (263 since 1980), the Philippines the most at typhoon strength (129). Big caveats: before satellites (about 1970) many storms far from land were never recorded, so I don't compare the early record; most of the Category 4+ rise came between the 1980s and 1990s, when satellite methods were maturing; the Category 3+ share barely moved. Interactive map with every track, a season player and landfalls: https://maps.tristanhotham.com/hurricane-tracks/

## Source comment

Source: NOAA NCEI, International Best Track Archive for Climate Stewardship (IBTrACS) v04r01, all basins, 6-hourly positions, 1851 to 2025 (Knapp et al. 2010; Gahtan et al. 2024). NOAA data, no copyright restrictions. Land and coastlines: Natural Earth. Category from USA_WIND (1-minute sustained wind); landfalls by intersecting each track segment with Natural Earth coastlines. Trends 1980 to 2025 with bootstrap intervals; halves compared with a two-proportion test. Collage labels were placed by a script that checks they sit on open sea, away from dense tracks, land and each other.

Tools: Python (pandas, shapely, pyproj, matplotlib); Leaflet for the interactive map.

Interactive version: https://maps.tristanhotham.com/hurricane-tracks/
Paper: https://doi.org/10.5281/zenodo.23858051
Blog post: https://blog.tristanhotham.com/2026/10/31/hurricane-tracks/
