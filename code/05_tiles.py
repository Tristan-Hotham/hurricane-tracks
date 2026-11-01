"""Page data: tracks tiled by decade (simplified), a search index, landfall points, the genesis density overlay and
per-country landfall summaries.

- The map filters storms by the calendar year in which they began (the analyses use IBTrACS seasons).
- data/tracks/<decade>.json: every storm whose season falls in that decade (the 2020s file also holds the incomplete
  2026 season and the first storms of the Southern Hemisphere 2027 season). Each storm: [g, sid, name, season, basin,
  peak kt, peak source (1 USA, 2 WMO, 0 none), peak category, min pressure, start, end, countries hit [[name, cat]],
  delta-encoded longitude and latitude in tenths of a degree, category string (one character per vertex: 0..6 or 'u')].
  Tracks are simplified with Douglas-Peucker (0.12 degrees) within each run of constant category, so every change of
  category is kept.
- data/search.json: [g, name, season, basin, peak category, decade] for every storm.
- data/landfalls.json: [lat, lon, category, g, country index, season, region index, wind kt or -1, calendar year] for every landfall at tropical storm strength or
  with unknown wind, plus the country names.
- data/genesis.png: where storms that reached 34 kt formed, 1980 to 2025, smoothed counts in Web Mercator.
- data/site.json: country summaries for the side panel.
"""
import numpy as np
import pandas as pd
from shapely.geometry import LineString
from scipy.ndimage import gaussian_filter
from PIL import Image
from common import *

S = pd.read_pickle(f"{WORK}/storms.pkl").reset_index(drop=True)
P = pd.read_pickle(f"{WORK}/points.pkl")
LF = pd.read_csv(f"{DATA}/landfalls.csv", keep_default_na=False, na_values={"wind_kt": [""]})
HITS = jload(f"{WORK}/hits.json")
S["g"] = np.arange(len(S)); gof = dict(zip(S.SID, S.g))
S["dec"] = S.season // 10 * 10
S.loc[S.season > 2020, "dec"] = 2020
TOL = 0.12


def simplify(xy, cats):
    keep = [0]
    i = 0; n = len(xy)
    while i < n - 1:
        j = i
        while j + 1 < n - 1 and cats[j + 1] == cats[i]:
            j += 1
        j += 1   # run from i to j (j is the first vertex of the next run, or the last vertex)
        seg = xy[i:j + 1]
        if len(seg) > 2:
            ls = LineString(seg).simplify(TOL, preserve_topology=False)
            kept = set(map(tuple, np.round(np.array(ls.coords), 6)))
            for k in range(i + 1, j):
                if tuple(np.round(seg[k - i], 6)) in kept:
                    keep.append(k)
        keep.append(j)
        i = j
    return sorted(set(keep))


tot_in = tot_out = 0
files = {}
P = P.sort_values(["SID", "t"])
for sid, g in P.groupby("SID", sort=False):
    s = S.loc[gof[sid]]
    xy = np.c_[g.lon.values, g.lat.values]
    cats = g.cat.values.tolist()
    k = simplify(xy, cats) if len(xy) > 2 else list(range(len(xy)))
    tot_in += len(xy); tot_out += len(k)
    q = np.round(xy[k] * 10).astype(int)
    d = np.r_[q[:1], np.diff(q, axis=0)].ravel().tolist()
    cs = "".join("u" if cats[i] < 0 else str(cats[i]) for i in k)
    src = 1 if s.peak_src == "USA" else 2 if s.peak_src == "WMO" else 0
    row = [int(s.g), sid, s.nm, int(s.season), s.basin, None if np.isnan(s.peak) else int(s.peak), src, int(s.peak_cat),
           None if np.isnan(s.pres_min) else int(s.pres_min), s.start.strftime("%Y-%m-%d"), s.end.strftime("%Y-%m-%d"),
           [[c, k_] for c, k_ in HITS.get(sid, [])], d, cs]
    files.setdefault(int(s.dec), []).append(row)
sizes = {}
for dcd, rows in sorted(files.items()):
    rows.sort(key=lambda r: r[0])
    jsave({"dec": dcd, "s": rows}, f"{DATA}/tracks/{dcd}.json")
    sizes[dcd] = os.path.getsize(f"{DATA}/tracks/{dcd}.json")
print("vertices", tot_in, "->", tot_out, "; files KB", {k: v // 1024 for k, v in sizes.items()})

jsave([[int(r.g), r.nm, int(r.season), r.basin, int(r.peak_cat), int(r.dec)] for r in S.itertuples()], f"{DATA}/search.json")

# landfall points
L = LF[(LF.wind_kt >= 34) | LF.wind_kt.isna()].copy()
cn = sorted(L.country.unique())
ci = {c: i for i, c in enumerate(cn)}
L["wk"] = L.wind_kt.fillna(-1)
rg = sorted(L.region.unique()); ri_ = {c: i for i, c in enumerate(rg)}
rows = [[round(r.lat, 2), round(r.lon, 2), int(r.category), int(gof[r.sid]), ci[r.country], int(r.season), ri_[r.region], int(r.wk), int(r.time_utc[:4])] for r in L.itertuples()]
jsave({"countries": cn, "regions": rg, "rows": rows}, f"{DATA}/landfalls.json")
print("landfall points", len(rows), os.path.getsize(f"{DATA}/landfalls.json") // 1024, "KB")

# genesis density 1980 to 2025, Web Mercator image
G = pd.read_pickle(f"{WORK}/genesis.pkl")
res = 0.25
H = np.zeros((int(180 / res), int(360 / res)))
for la, lo in zip(G.gen_lat, G.glon):
    H[min(int((90 - la) / res), H.shape[0] - 1), min(int((lo + 180) / res), H.shape[1] - 1)] += 1
Hs = gaussian_filter(H, sigma=1.6 / res, mode=("constant", "wrap"))
Hs = Hs / (LAST - SAT0 + 1) * 10 / (res * res) * (2.5 * 2.5)     # storms per decade per 2.5 degree square
Wpx = 2048
ymax = math.log(math.tan(math.pi / 4 + math.radians(85.0511) / 2))
ys = np.linspace(ymax, -ymax, Wpx)
lat = np.degrees(2 * np.arctan(np.exp(ys)) - math.pi / 2)
lon = np.linspace(-180, 180, Wpx, endpoint=False) + 180 / Wpx
ri = np.clip(((90 - lat) / res).astype(int), 0, H.shape[0] - 1); cj = np.clip(((lon + 180) / res).astype(int), 0, H.shape[1] - 1)
V = Hs[ri][:, cj]
vmax = float(np.percentile(V[V > 0], 99.7))
t = np.clip(V / vmax, 0, 1)
ramp = np.array([[255, 236, 179], [253, 174, 97], [228, 87, 52], [178, 24, 63], [94, 10, 72]], float)
s_ = t * (len(ramp) - 1); a0 = np.minimum(len(ramp) - 2, s_.astype(int)); u = (s_ - a0)[..., None]
rgb = ramp[a0] * (1 - u) + ramp[a0 + 1] * u
alpha = np.where(t > 0.03, np.clip(0.45 + 0.55 * t ** 0.5, 0, 1), 0) * 255
img = np.dstack([rgb, alpha]).astype(np.uint8)
Image.fromarray(img, "RGBA").save(f"{DATA}/genesis.png", optimize=True)
np.save(f"{WORK}/genesis_grid.npy", Hs)
print("genesis.png", os.path.getsize(f"{DATA}/genesis.png") // 1024, "KB; vmax per decade per 2.5 deg", round(vmax, 2))

# country summaries for the side panel (1980 to 2025 and the whole record), strongest and latest landfalls
Lw = LF[(LF.wind_kt >= 34) & (LF.season <= LAST)]
C = {}
for (iso, country), g in Lw.groupby(["iso", "country"]):
    sat = g[g.season >= SAT0]
    one = g.sort_values("wind_kt", ascending=False).drop_duplicates("sid")
    C[country] = {"iso": iso,
                  "sat": [int(sat.sid.nunique()), int(sat[sat.wind_kt >= 64].sid.nunique()), int(sat[sat.wind_kt >= 96].sid.nunique())],
                  "all": [int(g.sid.nunique()), int(g[g.wind_kt >= 64].sid.nunique()), int(g[g.wind_kt >= 96].sid.nunique())],
                  "first": int(g.season.min()),
                  "top": [[int(gof[r.sid]), r["name"], int(r.season), int(r.wind_kt), r.region] for _, r in one.head(6).iterrows()],
                  "regions": [[k, int(v)] for k, v in sat.groupby("region").sid.nunique().sort_values(ascending=False).head(6).items()],
                  "lat": round(float(g.lat.median()), 2), "lon": round(float(g.lon.median()), 2)}
site = {"cats": [[c[0], c[1], c[2]] for c in CATS], "col": CAT_COL, "col_dark": CAT_COL_DARK, "unk": UNK_COL,
        "basins": [[b[0], b[1], b[2]] for b in BASINS], "decades": sorted(files), "sizes": sizes, "countries": C,
        "first": FIRST, "last": LAST, "sat0": SAT0, "maxseason": int(S.season.max()), "ymin": int(S.start.dt.year.min()), "ymax": int(S.start.dt.year.max())}
jsave(site, f"{DATA}/site.json")
print("site.json", os.path.getsize(f"{DATA}/site.json") // 1024, "KB; countries", len(C))
