"""Landfalls: where each track crosses from sea onto land.

Every 6-hourly segment of every track is drawn as a straight line and intersected with the Natural Earth 1:10m
countries (each polygon separately, so islands count). A landfall is a point where a segment enters a land polygon
from the sea. Its time, position and wind are interpolated along the segment. A landfall counts only if the storm was
not yet extratropical (IBTrACS NATURE not 'ET' at the start of the segment). Its strength is the interpolated wind:
USA_WIND (1-minute) where recorded, else the agency's WMO_WIND, else unknown. The state or province is the Natural
Earth admin-1 unit that holds (or is nearest to) the landfall point. France's overseas departments are reported under
their own names (Reunion, Guadeloupe, Martinique, Mayotte, French Guiana), since Natural Earth counts them as France.

Writes WORK/landfall_events.pkl (every entry) and data/landfalls.csv (one row per storm and state or province:
the first entry there at the storm's strongest landfall wind).
"""
import numpy as np
import pandas as pd
import shapely
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
from common import *

iso_of = lambda p: p["ISO_A3_EH"] if p.get("ISO_A3_EH") not in ("-99", None) else p["ADM0_A3"]
W10 = jload(f"{GEO}/ne_10m_admin_0_countries.geojson")["features"]
polys, piso = [], []
CNAME = {}
for f in W10:
    p = f["properties"]; iso = iso_of(p)
    if iso == "ATA":
        continue
    nmx = (p["NAME_EN"] or p["NAME"]).replace("United States of America", "United States").replace("People's Republic of China", "China")
    if p["ADM0_A3"] == iso or iso not in CNAME:
        CNAME[iso] = nmx
    g = shape(f["geometry"])
    for part in getattr(g, "geoms", [g]):
        polys.append(part); piso.append(iso)
CNAME.update({"PHL": "Philippines", "BHS": "The Bahamas", "CHN": "China", "TWN": "Taiwan", "KOR": "South Korea", "PRK": "North Korea",
              "VNM": "Vietnam", "LAO": "Laos", "MMR": "Myanmar", "RUS": "Russia", "FSM": "Micronesia", "MHL": "Marshall Islands"})
piso = np.array(piso)
tree = STRtree(polys)
A1 = jload(f"{GEO}/ne_10m_admin_1_states_provinces.geojson")["features"]
a1g = [shape(f["geometry"]) for f in A1]
a1p = [(f["properties"].get("name_en") or f["properties"].get("name") or "", f["properties"].get("adm0_a3"), f["properties"].get("type_en") or "") for f in A1]
a1tree = STRtree(a1g)
OVERSEAS = {"La Réunion": "Réunion", "Guadeloupe": "Guadeloupe", "Martinique": "Martinique", "Mayotte": "Mayotte", "Guyane française": "French Guiana", "French Guiana": "French Guiana"}

P = pd.read_pickle(f"{WORK}/points.pkl")
S = pd.read_pickle(f"{WORK}/storms.pkl")
P = P.reset_index(drop=True)
same = (P.SID.values[1:] == P.SID.values[:-1])
i0 = np.nonzero(same)[0]; i1 = i0 + 1
x0, y0, x1, y1 = P.lon.values[i0], P.lat.values[i0], P.lon.values[i1], P.lat.values[i1]
segs, sidx, sshift = [], [], []
for k in (-360, 0, 360):
    a = np.minimum(x0, x1) + k; b = np.maximum(x0, x1) + k
    ok = (b >= -180) & (a <= 180)
    idx = np.nonzero(ok)[0]
    segs.extend(shapely.linestrings(np.stack([np.c_[x0[idx] + k, y0[idx]], np.c_[x1[idx] + k, y1[idx]]], axis=1)))
    sidx.extend(idx); sshift.extend([k] * len(idx))
segs = np.array(segs, dtype=object); sidx = np.array(sidx); sshift = np.array(sshift)
pairs = tree.query(segs, predicate="intersects")
print("segments", len(i0), "tested", len(segs), "segment-polygon pairs", pairs.shape[1])
ev = []
for si, pj in zip(*pairs):
    line = segs[si]; poly = polys[pj]
    inter = line.intersection(poly)
    if inter.is_empty:
        continue
    pieces = getattr(inter, "geoms", [inter])
    L = line.length
    if L == 0:
        continue
    for pc in pieces:
        cs = list(pc.coords)
        fr = min(line.project(Point(cs[0])), line.project(Point(cs[-1]))) / L
        if fr <= 1e-9:          # the segment starts on land: not an entry
            continue
        k = sidx[si]; a, b = i0[k], i1[k]
        ev.append((a, b, fr, int(pj), float(sshift[si])))
E = pd.DataFrame(ev, columns=["a", "b", "f", "poly", "shift"])
# keep only entries from the sea: a point 3 km back along the segment must not be on land (this drops land borders)
xa, ya = P.lon.values[E.a] + E["shift"].values, P.lat.values[E.a]
xb, yb = P.lon.values[E.b] + E["shift"].values, P.lat.values[E.b]
Ld = np.hypot(xb - xa, yb - ya)
fb = np.clip(E.f.values - 0.027 / np.maximum(Ld, 1e-9), 0, 1)
back = shapely.points(xa + (xb - xa) * fb, ya + (yb - ya) * fb)
onland = np.zeros(len(E), bool)
hit = tree.query(back, predicate="intersects")
onland[np.unique(hit[0])] = True
print("entries", len(E), "of which across a land border", int(onland.sum()))
E = E[~onland].reset_index(drop=True)
pa, pb = P.loc[E.a], P.loc[E.b]
f = E.f.values


def lerp(u, v):
    u = u.values.astype(float); v = v.values.astype(float)
    out = u + (v - u) * f
    out = np.where(np.isnan(u), v, np.where(np.isnan(v), u, out))
    return out


E["SID"] = pa.SID.values
E["lon"] = pa.lon.values + (pb.lon.values - pa.lon.values) * f + E["shift"].values
E["lat"] = pa.lat.values + (pb.lat.values - pa.lat.values) * f
E["t"] = pa.t.values + (pb.t.values - pa.t.values) * f
E["usa"] = lerp(pa.USA_WIND, pb.USA_WIND)
E["wmo"] = lerp(pa.WMO_WIND, pb.WMO_WIND)
E["w"] = np.where(np.isnan(E.usa), E.wmo, E.usa)
E["wsrc"] = np.where(~np.isnan(E.usa), "USA", np.where(~np.isnan(E.wmo), "WMO", ""))
E["nature"] = pa.NATURE.values
E["iso"] = piso[E.poly.values]
E = E[E.nature != "ET"].copy()
# state or province
pts = shapely.points(E.lon.values, E.lat.values)
reg, rtype = [], []
for pt, iso in zip(pts, E.iso.values):
    best, bd = None, 9e9
    for j in a1tree.query(pt.buffer(0.6)):
        if a1p[j][1] != iso and not (iso in ("FRA",) and a1p[j][1] == "FRA"):
            continue
        dd = a1g[j].distance(pt)
        if dd < bd:
            best, bd = j, dd
    reg.append(a1p[best][0] if best is not None else ""); rtype.append(a1p[best][2] if best is not None else "")
E["region"] = reg; E["rtype"] = rtype
E["country"] = [CNAME.get(i, i) for i in E.iso]
fo = E.iso.eq("FRA") & E.region.isin(list(OVERSEAS))
E.loc[fo, "country"] = E.loc[fo, "region"].map(OVERSEAS)
E.loc[fo, "iso"] = E.loc[fo, "region"].map({"La Réunion": "REU", "Guadeloupe": "GLP", "Martinique": "MTQ", "Mayotte": "MYT", "Guyane française": "GUF", "French Guiana": "GUF"})
E["cat"] = [cat_of(x) for x in E.w]
E = E.merge(S[["SID", "season", "basin", "nm"]], on="SID", how="left").sort_values(["SID", "t"]).reset_index(drop=True)
E.to_pickle(f"{WORK}/landfall_events.pkl")

# one row per storm and region: the strongest entry there (first one if tied)
E["wk"] = E.w.fillna(-1)
F = E.sort_values(["SID", "region", "wk", "t"], ascending=[True, True, False, True]).groupby(["SID", "iso", "region"], as_index=False).first()
F = F.sort_values(["season", "SID", "t"])
out = F[["SID", "season", "basin", "nm", "t", "lat", "lon", "iso", "country", "region", "rtype", "w", "wsrc", "cat"]].copy()
out["t"] = out.t.dt.strftime("%Y-%m-%d %H:%M")
out["lat"] = out.lat.round(2); out["lon"] = ((out.lon + 180) % 360 - 180).round(2); out["w"] = out.w.round(0)
out.rename(columns={"SID": "sid", "nm": "name", "t": "time_utc", "w": "wind_kt", "wsrc": "wind_source", "cat": "category"}).to_csv(f"{DATA}/landfalls.csv", index=False)
jsave(CNAME, f"{WORK}/cname.json")
print("entries", len(E), "storm-region rows", len(out), "storms with a landfall", out.SID.nunique())
print(out.groupby("country").SID.nunique().sort_values(ascending=False).head(15).to_dict())
