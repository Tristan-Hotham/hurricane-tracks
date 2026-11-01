"""All the numbers: storms per year by basin, where storms form, landfalls by country and region, the strongest storms,
the share reaching Category 3+ and 4+ by decade, the latitude of peak intensity and accumulated cyclone energy.
Writes WORK/analysis.json (read by 06_results.py) and data/storms.csv, data/per_year.csv, data/shares_by_decade.csv,
data/landfall_countries.csv, data/landfall_regions.csv, data/lmi_latitude.csv.

Definitions (see the paper):
- best wind: USA_WIND (1-minute, knots) where recorded, else WMO_WIND; used for counting tropical storms and for landfalls.
- intensity analyses (shares by category, latitude of peak intensity, accumulated cyclone energy) use USA_WIND only,
  so that every storm is measured as a 1-minute wind; the denominator is storms whose USA_WIND reached 34 kt.
- comparisons use 1980 to 2025 (global geostationary satellite coverage); earlier decades are shown with a caveat.
"""
import numpy as np
import pandas as pd
from scipy import stats
from common import *

rng = np.random.default_rng(20261101)
S = pd.read_pickle(f"{WORK}/storms.pkl")
P = pd.read_pickle(f"{WORK}/points.pkl")
LF = pd.read_csv(f"{DATA}/landfalls.csv", keep_default_na=False, na_values={"wind_kt": [""], "lat": [""], "lon": [""]})
CN = jload(f"{WORK}/cname.json")
A = S[(S.season >= FIRST) & (S.season <= LAST)].copy()
A["ts"] = A.peak >= 34; A["hu"] = A.peak >= 64; A["mj"] = A.peak >= 96
A["uts"] = A.usa_max >= 34; A["u3"] = A.usa_max >= 96; A["u4"] = A.usa_max >= 113; A["u5"] = A.usa_max >= 137
A["dec"] = A.season // 10 * 10
B = [b[0] for b in BASINS]
out = {}

# ---------- counts ----------
years = list(range(FIRST, LAST + 1))
py = {"years": years}
rows = []
for b in B:
    sb = A[A.basin == b]
    for k, col in (("all", None), ("ts", "ts"), ("hu", "hu")):
        c = (sb if col is None else sb[sb[col]]).groupby("season").size().reindex(years, fill_value=0)
        py[f"{b}_{k}"] = c.tolist()
for y in years:
    r = {"season": y}
    for b in B:
        for k in ("all", "ts", "hu"):
            r[f"{b}_{k}"] = py[f"{b}_{k}"][y - FIRST]
    rows.append(r)
pd.DataFrame(rows).to_csv(f"{DATA}/per_year.csv", index=False)
out["per_year"] = py
sat = A[A.season >= SAT0]
nyrs = LAST - SAT0 + 1
gl_ts = sat[sat.ts].groupby("season").size().reindex(range(SAT0, LAST + 1), fill_value=0)
gl_hu = sat[sat.hu].groupby("season").size().reindex(range(SAT0, LAST + 1), fill_value=0)
gl_mj = sat[sat.u3].groupby("season").size().reindex(range(SAT0, LAST + 1), fill_value=0)
gl_c4 = sat[sat.u4].groupby("season").size().reindex(range(SAT0, LAST + 1), fill_value=0)


def trend(y, x=None, nb=4000):
    """OLS slope per decade with a pairs bootstrap 95% interval and the OLS p-value."""
    y = np.asarray(y, float); x = np.arange(len(y)) if x is None else np.asarray(x, float)
    ok = ~np.isnan(y); x, y = x[ok], y[ok]
    lr = stats.linregress(x, y)
    bs = []
    for _ in range(nb):
        i = rng.integers(0, len(x), len(x))
        if np.ptp(x[i]) == 0:
            continue
        bs.append(np.polyfit(x[i], y[i], 1)[0])
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return {"per_dec": lr.slope * 10, "lo": lo * 10, "hi": hi * 10, "p": lr.pvalue, "n": int(len(x))}


cnt = {"n_systems": int(len(A)), "n_ts": int(A.ts.sum()), "n_hu": int(A.hu.sum()), "n_nowind": int(A.peak.isna().sum()),
       "nowind_pct": 100 * A.peak.isna().mean(),
       "n_all_incl_current": int(len(S)), "n_current": int((S.season > LAST).sum()),
       "sat_ts_mean": float(gl_ts.mean()), "sat_hu_mean": float(gl_hu.mean()), "sat_mj_mean": float(gl_mj.mean()), "sat_c4_mean": float(gl_c4.mean()),
       "sat_ts_min": int(gl_ts.min()), "sat_ts_min_year": int(gl_ts.idxmin()), "sat_ts_max": int(gl_ts.max()), "sat_ts_max_year": int(gl_ts.idxmax()),
       "sat_ts_trend": trend(gl_ts.values), "sat_hu_trend": trend(gl_hu.values), "sat_c4_trend": trend(gl_c4.values),
       "sat_years": nyrs, "sat_n_ts": int(sat.ts.sum()), "sat_n_uts": int(sat.uts.sum()),
       "basin_ts_mean": {b: float(sat[sat.ts & (sat.basin == b)].groupby("season").size().reindex(range(SAT0, LAST + 1), fill_value=0).mean()) for b in B},
       "basin_hu_mean": {b: float(sat[sat.hu & (sat.basin == b)].groupby("season").size().reindex(range(SAT0, LAST + 1), fill_value=0).mean()) for b in B},
       "basin_ts_share": {b: 100 * float((sat.ts & (sat.basin == b)).sum() / sat.ts.sum()) for b in B}}
# wind coverage by decade (share of systems with any USA wind), and the North Atlantic long run
cov = []
for dcd, g in A.groupby("dec"):
    cov.append({"dec": int(dcd), "n": int(len(g)), "usa_pct": 100 * g.usa_max.notna().mean(), "any_pct": 100 * g.peak.notna().mean()})
cnt["coverage"] = cov
na = A[A.basin == "NA"]
nadec = []
for dcd in range(1850, 2030, 10):
    g = na[na.dec == dcd]; ny = len([y for y in years if y // 10 * 10 == dcd])
    nadec.append({"dec": dcd, "years": ny, "ts": int(g.ts.sum()), "hu": int(g.hu.sum()), "mj": int(g.u3.sum()),
                  "ts_py": g.ts.sum() / ny, "hu_py": g.hu.sum() / ny, "mj_py": g.u3.sum() / ny})
cnt["na_decades"] = nadec
na_ts_pre = na[(na.season <= 1900)].ts.sum() / 50; na_ts_post = na[(na.season >= 1976)].ts.sum() / 50
cnt["na_ts_py_1851_1900"] = float(na[(na.season <= 1900)].ts.sum() / 50)
cnt["na_ts_py_1976_2025"] = float(na[(na.season >= 1976)].ts.sum() / 50)
cnt["na_hu_py_1851_1900"] = float(na[(na.season <= 1900)].hu.sum() / 50)
cnt["na_hu_py_1976_2025"] = float(na[(na.season >= 1976)].hu.sum() / 50)
cnt["na_ts_ratio"] = cnt["na_ts_py_1976_2025"] / cnt["na_ts_py_1851_1900"]
cnt["na_hu_ratio"] = cnt["na_hu_py_1976_2025"] / cnt["na_hu_py_1851_1900"]
# North Atlantic storms that never came near land: the kind most likely to be missed before satellites
na["far"] = na.dist_min >= 500
cnt["na_far_pct_1851_1900"] = 100 * float(na[(na.season <= 1900) & na.ts].far.mean())
cnt["na_far_pct_1976_2025"] = 100 * float(na[(na.season >= 1976) & na.ts].far.mean())


first_wind = {b: int(A[(A.basin == b) & A.peak.notna()].season.min()) for b in B}
first_cov = {}
for b in B:
    g = A[A.basin == b].groupby("dec").apply(lambda x: x.usa_max.notna().mean(), include_groups=False)
    ok = g[g >= .8]
    first_cov[b] = int(ok.index.min()) if len(ok) else None
cnt["first_wind"] = first_wind; cnt["first_cov80"] = first_cov
first_track = {b: int(A[A.basin == b].season.min()) for b in B}
cnt["first_track"] = first_track
out["counts"] = cnt

# ---------- genesis ----------
G = sat[sat.ts].copy()
G["glon"] = (G.gen_lon + 180) % 360 - 180
cell = 2.5
G["ci"] = np.floor(G.gen_lat / cell).astype(int); G["cj"] = np.floor(G.glon / cell).astype(int)
gc = G.groupby(["ci", "cj"]).size().sort_values(ascending=False)
top = []
for (ci, cj), n in gc.head(12).items():
    top.append({"lat": ci * cell + cell / 2, "lon": cj * cell + cell / 2, "n": int(n), "per_dec": n / nyrs * 10})
G["month"] = G.start.dt.month
bm = {b: G[G.basin == b].groupby("month").size().reindex(range(1, 13), fill_value=0).tolist() for b in B}
gen = {"n": int(len(G)), "cell": cell, "top": top, "eq5_n": int((G.gen_lat.abs() < 5).sum()), "eq5_pct": 100 * float((G.gen_lat.abs() < 5).mean()),
       "eq3_n": int((G.gen_lat.abs() < 3).sum()),
       "mean_abs_lat": float(G.gen_lat.abs().mean()), "median_abs_lat": float(G.gen_lat.abs().median()),
       "nh_pct": 100 * float((G.gen_lat > 0).mean()), "within_10_25_pct": 100 * float(G.gen_lat.abs().between(5, 20).mean()),
       "by_month": bm, "peak_month": {b: int(np.argmax(bm[b]) + 1) for b in B if sum(bm[b])},
       "wp_share": 100 * float((G.basin == "WP").mean()), "sa_n": int((G.basin == "SA").sum())}
out["genesis"] = gen
G[["SID", "season", "basin", "gen_lat", "glon"]].to_pickle(f"{WORK}/genesis.pkl")

# ---------- landfalls ----------
L = LF[(LF.season >= FIRST) & (LF.season <= LAST)].copy()
Lw = L[L.wind_kt >= 34]
Ls = Lw[Lw.season >= SAT0]


def by(df, keys):
    g = df.groupby(keys)
    r = pd.DataFrame({"ts": g.sid.nunique(), "hu": df[df.wind_kt >= 64].groupby(keys).sid.nunique(),
                      "mj": df[df.wind_kt >= 96].groupby(keys).sid.nunique(), "c5": df[df.wind_kt >= 137].groupby(keys).sid.nunique()}).fillna(0).astype(int)
    return r.sort_values(["ts", "hu"], ascending=False)


cs = by(Ls, ["iso", "country"]); ca = by(Lw, ["iso", "country"])
cs.reset_index().to_csv(f"{DATA}/landfall_countries.csv", index=False)
rs = by(Ls, ["iso", "country", "region"]); rs.reset_index().to_csv(f"{DATA}/landfall_regions.csv", index=False)
hu_rank = cs.sort_values(["hu", "mj"], ascending=False)
mj_rank = cs.sort_values(["mj", "hu"], ascending=False)
toL = lambda df, n: [{"iso": i[0], "name": i[1], **({"region": i[2]} if len(i) > 2 else {}), "ts": int(r.ts), "hu": int(r.hu), "mj": int(r.mj), "c5": int(r.c5),
                       "ts_py": r.ts / nyrs} for i, r in df.head(n).iterrows()]
sat_uts = sat[sat.ts]
hit = set(Ls.sid)
lf = {"n_storm_country": int(len(Ls.groupby(["sid", "iso"]))), "n_countries": int(Ls.iso.nunique()),
      "n_storms_landfall": int(Ls.sid.nunique()), "landfall_pct": 100 * len(hit) / len(sat_uts),
      "hu_landfall_pct": 100 * Ls[Ls.wind_kt >= 64].sid.nunique() / int(sat.hu.sum()),
      "top": toL(cs, 30), "top_hu": toL(hu_rank, 15), "top_mj": toL(mj_rank, 12), "top_regions": toL(rs, 30), "top_regions_mj": toL(rs.sort_values(["mj", "hu"], ascending=False), 10),
      "all_top": toL(ca, 15), "all_n_storm_country": int(len(Lw.groupby(["sid", "iso"])))}
# strongest landfalls since 1851 (interpolated, USA wind only)
Lu = L[(L.wind_source == "USA")].sort_values("wind_kt", ascending=False).drop_duplicates("sid")
lf["strongest"] = [{"sid": r.sid, "name": r["name"] if isinstance(r["name"], str) else "", "season": int(r.season), "country": r.country, "region": r.region if isinstance(r.region, str) else "",
                    "kt": float(r.wind_kt), "basin": r.basin} for _, r in Lu.head(15).iterrows()]
# landfalls of each storm (TS+ or wind unknown) for the storm table
LS = L[(L.wind_kt >= 34) | L.wind_kt.isna()]
hits = LS.sort_values("time_utc").groupby("sid").apply(lambda g: [(c, int(cat_of(w))) for c, w in g.groupby("country", sort=False).wind_kt.max().items()], include_groups=False).to_dict()
# the US, the Philippines and China in the long run, decade by decade (best wind; caveat on early records)
lf["us_decades"] = [{"dec": d, "hu": int(Lw[(Lw.iso == "USA") & (Lw.wind_kt >= 64) & (Lw.season // 10 * 10 == d)].sid.nunique()),
                     "mj": int(Lw[(Lw.iso == "USA") & (Lw.wind_kt >= 96) & (Lw.season // 10 * 10 == d)].sid.nunique())} for d in range(1850, 2030, 10)]
out["landfall"] = lf

# ---------- strongest ----------
U = A[A.usa_max.notna()].copy()
U["pres"] = U.pres_min
U = U.sort_values(["usa_max", "pres"], ascending=[False, True])
st = []
for _, r in U.head(30).iterrows():
    st.append({"sid": r.SID, "name": r.nm, "season": int(r.season), "basin": r.basin, "kt": int(r.usa_max), "mph": kt_mph(r.usa_max), "kmh": kt_kmh(r.usa_max),
               "pres": None if np.isnan(r.pres) else int(r.pres), "hits": [h[0] for h in hits.get(r.SID, [])]})
Pp = A[A.pres_min.notna()].sort_values(["pres_min", "usa_max"], ascending=[True, False])
lp = [{"sid": r.SID, "name": r.nm, "season": int(r.season), "basin": r.basin, "pres": int(r.pres_min), "kt": None if np.isnan(r.usa_max) else int(r.usa_max)} for _, r in Pp.head(15).iterrows()]
sts = []
for _, r in U[U.season >= SAT0].head(30).iterrows():
    sts.append({"sid": r.SID, "name": r.nm, "season": int(r.season), "basin": r.basin, "kt": int(r.usa_max), "mph": kt_mph(r.usa_max), "kmh": kt_kmh(r.usa_max),
                "pres": None if np.isnan(r.pres) else int(r.pres), "hits": [h[0] for h in hits.get(r.SID, [])]})
c5 = A[A.u5]
out["strongest"] = {"wind": st, "wind_sat": sts, "n_top20_5060": sum(1 for x in st[:20] if x["basin"] == "WP" and 1950 <= x["season"] <= 1969), "pressure": lp, "n_c5": int(len(c5)), "n_c5_sat": int((c5.season >= SAT0).sum()),
                    "n_ge160": int((A.usa_max >= 160).sum()), "c5_by_basin": c5.groupby("basin").size().to_dict()}

# ---------- shares of Category 3+ and 4+ ----------
D = A[A.uts].copy()


def share_row(g):
    n = len(g)
    return {"n": int(n), "c3": int(g.u3.sum()), "c4": int(g.u4.sum()), "c5": int(g.u5.sum()),
            "s3": 100 * g.u3.mean() if n else None, "s4": 100 * g.u4.mean() if n else None, "s5": 100 * g.u5.mean() if n else None}


sh = {"global": [], "basins": {}}
for dcd in range(SAT0, LAST + 1, 10):
    g = D[(D.dec == dcd)]
    sh["global"].append({"dec": dcd, "years": f"{dcd} to {min(dcd + 9, LAST)}", **share_row(g)})
for b in B:
    if b == "SA":
        continue
    rr = []
    for dcd in range(1850, 2030, 10):
        g = D[(D.dec == dcd) & (D.basin == b)]
        allg = A[(A.dec == dcd) & (A.basin == b)]
        if len(g) < 5:
            continue
        rr.append({"dec": dcd, **share_row(g), "cov": 100 * allg.usa_max.notna().mean()})
    sh["basins"][b] = rr
# halves
h1 = D[(D.season >= SAT0) & (D.season <= 2002)]; h2 = D[(D.season >= 2003) & (D.season <= LAST)]


def prop_test(a, n1, b, n2):
    p = (a + b) / (n1 + n2); se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    z = (b / n2 - a / n1) / se
    return 2 * (1 - stats.norm.cdf(abs(z)))


halves = {"h1": f"{SAT0} to 2002", "h2": f"2003 to {LAST}"}
for k, col in (("3", "u3"), ("4", "u4"), ("5", "u5")):
    a, n1, b_, n2 = int(h1[col].sum()), len(h1), int(h2[col].sum()), len(h2)
    halves[f"s{k}_1"] = 100 * a / n1; halves[f"s{k}_2"] = 100 * b_ / n2; halves[f"d{k}"] = 100 * (b_ / n2 - a / n1); halves[f"p{k}"] = prop_test(a, n1, b_, n2)
halves["n1"], halves["n2"] = len(h1), len(h2)
halves["inv4_1"] = 100 / halves["s4_1"]; halves["inv4_2"] = 100 / halves["s4_2"]
bh = {}
for b in B:
    if b == "SA":
        continue
    x1, x2 = h1[h1.basin == b], h2[h2.basin == b]
    bh[b] = {"n1": len(x1), "n2": len(x2), "s3_1": 100 * x1.u3.mean(), "s3_2": 100 * x2.u3.mean(), "s4_1": 100 * x1.u4.mean(), "s4_2": 100 * x2.u4.mean(),
             "p3": prop_test(int(x1.u3.sum()), len(x1), int(x2.u3.sum()), len(x2)), "p4": prop_test(int(x1.u4.sum()), len(x1), int(x2.u4.sum()), len(x2))}
halves["basins"] = bh
ys = D[D.season >= SAT0].groupby("season")
halves["trend3"] = trend((100 * ys.u3.mean()).values)
halves["trend4"] = trend((100 * ys.u4.mean()).values)
sh["halves"] = halves
sh["annual"] = {"years": list(range(SAT0, LAST + 1)), "s3": (100 * ys.u3.mean()).round(2).tolist(), "s4": (100 * ys.u4.mean()).round(2).tolist(), "n": ys.size().tolist()}
# North Atlantic long run (with the caveat): first and last fifty years
nal = D[D.basin == "NA"]
sh["na_long"] = {"s3_1851_1900": 100 * nal[nal.season <= 1900].u3.mean(), "s3_1976_2025": 100 * nal[nal.season >= 1976].u3.mean(),
                 "s3_1851_1900_n": int((nal.season <= 1900).sum())}
pd.DataFrame([{"basin": "Global", **r} for r in sh["global"]] + [{"basin": b, **r} for b, rr in sh["basins"].items() for r in rr]).to_csv(f"{DATA}/shares_by_decade.csv", index=False)
out["shares"] = sh

# ---------- latitude of lifetime maximum intensity ----------
M = D[(D.season >= SAT0) & D.lmi_lat.notna()].copy()
M["alat"] = M.lmi_lat.abs()
M["hem"] = np.where(M.basin.isin(NH), "N", "S")
lm = {"years": list(range(SAT0, LAST + 1))}
rows = []
for hem in ("N", "S"):
    g = M[M.hem == hem].groupby("season").alat.mean().reindex(range(SAT0, LAST + 1))
    lm[hem] = g.round(3).tolist()
    t = trend(g.values); t["km_per_dec"] = t["per_dec"] * 111.2; t["km_lo"] = t["lo"] * 111.2; t["km_hi"] = t["hi"] * 111.2
    lm[f"{hem}_trend"] = t
    lm[f"{hem}_mean_1980s"] = float(M[(M.hem == hem) & (M.season < 1990)].alat.mean())
    lm[f"{hem}_mean_2016_2025"] = float(M[(M.hem == hem) & (M.season >= 2016)].alat.mean())
g = M.groupby("season").alat.mean().reindex(range(SAT0, LAST + 1))
t = trend(g.values); t["km_per_dec"] = t["per_dec"] * 111.2; t["km_lo"] = t["lo"] * 111.2; t["km_hi"] = t["hi"] * 111.2
lm["G"] = g.round(3).tolist(); lm["G_trend"] = t
lm["basins"] = {}
for b in B:
    if b == "SA":
        continue
    gb = M[M.basin == b].groupby("season").alat.mean().reindex(range(SAT0, LAST + 1))
    tb = trend(gb.values); tb["km_per_dec"] = tb["per_dec"] * 111.2; tb["km_lo"] = tb["lo"] * 111.2; tb["km_hi"] = tb["hi"] * 111.2
    tb["mean"] = float(M[M.basin == b].alat.mean())
    lm["basins"][b] = tb
for hem in ("N", "S", "G"):
    rows.extend({"season": y, "hemisphere": {"N": "Northern", "S": "Southern", "G": "Both"}[hem], "mean_abs_lat_lmi": v} for y, v in zip(lm["years"], lm[hem]))
pd.DataFrame(rows).to_csv(f"{DATA}/lmi_latitude.csv", index=False)
lm["n"] = int(len(M))
out["lmi"] = lm

# ---------- accumulated cyclone energy (USA wind, 6-hourly, tropical or subtropical points at 35 kt or more) ----------
Q = P[(P.SEASON >= SAT0) & (P.SEASON <= LAST) & (P.USA_WIND >= 35) & P.NATURE.isin(["TS", "SS", "NR", "MX"])]
ace = (Q.USA_WIND ** 2).groupby(Q.SEASON).sum() / 1e4
ace = ace.reindex(range(SAT0, LAST + 1), fill_value=0)
out["ace"] = {"years": list(ace.index), "v": ace.round(1).tolist(), "mean": float(ace.mean()), "max": float(ace.max()), "max_year": int(ace.idxmax()),
              "min": float(ace.min()), "min_year": int(ace.idxmin()), "trend": trend(ace.values)}

# ---------- storms table ----------
T = S.copy()
T["countries_hit"] = ["; ".join(f"{c}" for c, k in hits.get(s, [])) for s in T.SID]
T["start"] = T.start.dt.strftime("%Y-%m-%d"); T["end"] = T.end.dt.strftime("%Y-%m-%d")
T[["SID", "season", "basin", "subbasin", "nm", "start", "end", "n", "gen_lat", "gen_lon", "usa_max", "wmo_max", "peak", "peak_src", "peak_cat", "pres_min",
   "lmi_lat", "lmi_lon", "track_type", "countries_hit"]].rename(columns={"SID": "sid", "nm": "name", "n": "n_points_6h", "usa_max": "usa_wind_max_kt", "wmo_max": "wmo_wind_max_kt",
   "peak": "peak_wind_kt", "peak_src": "peak_wind_source", "peak_cat": "peak_category", "pres_min": "min_pressure_hpa"}).round(2).to_csv(f"{DATA}/storms.csv", index=False)
jsave({k: v for k, v in hits.items()}, f"{WORK}/hits.json")
jsave(out, f"{WORK}/analysis.json", indent=1)
print(json.dumps({"ts_mean": cnt["sat_ts_mean"], "hu_mean": cnt["sat_hu_mean"], "ts_trend": cnt["sat_ts_trend"], "c4_trend": cnt["sat_c4_trend"],
                  "global": sh["global"], "halves": {k: v for k, v in halves.items() if k != "basins"}, "lmiN": lm["N_trend"], "lmiS": lm["S_trend"], "lmiG": lm["G_trend"],
                  "gen": {k: gen[k] for k in ("n", "eq5_pct", "mean_abs_lat", "nh_pct")}, "lf_pct": lf["landfall_pct"], "ace": out["ace"]["trend"]}, indent=1, default=float))
for b, x in bh.items(): print(b, {k: round(v, 3) for k, v in x.items()})
for b, x in lm["basins"].items(): print("lmi", b, round(x["km_per_dec"]), round(x["km_lo"]), round(x["km_hi"]), round(x["p"], 3))
print(cnt["na_decades"])
print(st[:12]); print(lp[:5])
print(lf["top"][:12]); print(lf["top_regions"][:12]); print(lf["strongest"][:8])
