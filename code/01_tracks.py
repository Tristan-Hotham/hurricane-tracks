"""Read IBTrACS (6-hourly, all basins), keep one track per storm, attach a wind and a Saffir-Simpson category to every
point, and summarise every storm. Writes WORK/points.pkl (all kept points) and data/storms.csv (one row per storm).

Choices:
- Tracks: TRACK_TYPE main, PROVISIONAL and US-PROVISIONAL (the provisional tracks are the latest storms, not yet
  re-analysed). Spur tracks (short alternative positions for splits and merges) are left out, as IBTrACS advises.
- Seasons 1850 to 2026. IBTrACS gives Southern Hemisphere storms the season of the year in which the season ends.
- Wind: USA_WIND, the 1-minute sustained wind in knots from the US agencies (NHC, CPHC, JTWC), which is what the
  Saffir-Simpson scale is defined on. Where it is missing, WMO_WIND (the wind of the agency responsible, often a
  10-minute average, which reads lower) is used for the map colours only; analyses of intensity use USA_WIND alone.
- Longitudes are unwrapped so that each track is continuous across the date line.
"""
import numpy as np
import pandas as pd
from common import *

d = pd.read_csv(IBT, sep="\t", low_memory=False, keep_default_na=False, dtype=str)
n_rows = len(d)
d = d[d.TRACK_TYPE.isin(["main", "PROVISIONAL", "US-PROVISIONAL"])].copy()
d["SEASON"] = d.SEASON.astype(int)
d = d[d.SEASON >= 1850].copy()
for c in ("LAT", "LON", "USA_WIND", "WMO_WIND", "WMO_PRES", "DIST2LAND", "USA_SSHS"):
    d[c] = pd.to_numeric(d[c], errors="coerce")
d["t"] = pd.to_datetime(d.ISO_TIME)
d = d.sort_values(["SID", "t"]).reset_index(drop=True)
# unwrap longitude within each storm
dl = d.groupby("SID").LON.diff().fillna(0)
step = np.where(dl > 180, -360, np.where(dl < -180, 360, 0))
d["lon"] = d.LON + pd.Series(step, index=d.index).groupby(d.SID).cumsum()
first = d.groupby("SID").lon.transform("first")
shift = np.where(first > 180, -360, np.where(first < -180, 360, 0))
d["lon"] = d.lon + shift
d["lat"] = d.LAT
d["w"] = d.USA_WIND.where(d.USA_WIND.notna(), d.WMO_WIND)
d["wsrc"] = np.where(d.USA_WIND.notna(), 1, np.where(d.WMO_WIND.notna(), 2, 0))
d["cat"] = [cat_of(x) for x in d.w]
d["ucat"] = [cat_of(x) for x in d.USA_WIND]
d.to_pickle(f"{WORK}/points.pkl")

g = d.groupby("SID", sort=False)
S = g.agg(season=("SEASON", "first"), basin=("BASIN", "first"), subbasin=("SUBBASIN", "first"), name=("NAME", "first"),
          track_type=("TRACK_TYPE", "first"), start=("t", "first"), end=("t", "last"), n=("t", "size"),
          gen_lat=("lat", "first"), gen_lon=("lon", "first"),
          usa_max=("USA_WIND", "max"), wmo_max=("WMO_WIND", "max"), pres_min=("WMO_PRES", "min")).reset_index()
# lifetime maximum intensity (first time the USA wind peaks)
iu = d[d.USA_WIND.notna()].groupby("SID").USA_WIND.idxmax()
lmi = d.loc[iu.values, ["SID", "lat", "lon", "t"]].rename(columns={"lat": "lmi_lat", "lon": "lmi_lon", "t": "lmi_t"})
S = S.merge(lmi, on="SID", how="left")
S["peak"] = S.usa_max.where(S.usa_max.notna(), S.wmo_max)
S["peak_src"] = np.where(S.usa_max.notna(), "USA", np.where(S.wmo_max.notna(), "WMO", ""))
S["peak_cat"] = [cat_of(x) for x in S.peak]
S["usa_cat"] = [cat_of(x) for x in S.usa_max]
S["nm"] = [title_name(x) for x in S.name]
S["dist_min"] = g.DIST2LAND.min().reindex(S.SID).values
S = S.sort_values(["season", "start"]).reset_index(drop=True)
S.to_pickle(f"{WORK}/storms.pkl")
print("rows read", n_rows, "kept points", len(d), "storms", len(S), "seasons", S.season.min(), S.season.max())
print(S.groupby("peak_src").size().to_dict(), "USA cat counts", S.usa_cat.value_counts().sort_index().to_dict())
jsave({"n_rows": n_rows, "n_points": len(d), "n_storms": len(S)}, f"{WORK}/counts01.json")
