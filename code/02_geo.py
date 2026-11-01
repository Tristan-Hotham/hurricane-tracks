"""Geography for the page, the figures and the collage: a light world outline (Natural Earth 1:50m, simplified), country names and label
points, and town names for map labels (Natural Earth populated places)."""
from shapely.geometry import shape, mapping
from common import *

iso_of = lambda p: p["ISO_A3_EH"] if p.get("ISO_A3_EH") not in ("-99", None) else p["ADM0_A3"]


def rnd(c, k=2):
    if isinstance(c, (list, tuple)) and c and isinstance(c[0], (int, float)):
        return [round(c[0], k), round(c[1], k)]
    return [rnd(x, k) for x in c]


W50 = jload(f"{GEO}/ne_50m_admin_0_countries.geojson")
feats, cname, cpos = [], {}, {}
for f in W50["features"]:
    p = f["properties"]; iso = iso_of(p)
    gs = shape(f["geometry"]).simplify(0.04, preserve_topology=True)
    if gs.is_empty:
        continue
    gm = mapping(gs)
    feats.append({"type": "Feature", "properties": {"iso": iso}, "geometry": {"type": gm["type"], "coordinates": rnd(gm["coordinates"])}})
    cname[iso] = (p["NAME_EN"] or p["NAME"]).replace("United States of America", "United States").replace("People's Republic of China", "China")
    cpos[iso] = [round(p["LABEL_X"], 2), round(p["LABEL_Y"], 2), float(p["POP_EST"] or 0)]
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/world.json")
jsave({"cname": cname, "cpos": cpos}, f"{DATA}/countries.json")

P = jload(f"{GEO}/ne_10m_populated_places_simple.geojson")
cities = []
for f in P["features"]:
    p = f["properties"]; pop = p.get("pop_max") or 0
    if pop >= 100000 or p.get("adm0cap") == 1:
        cities.append({"name": re.sub(r"\s+", " ", p["name"]), "lat": round(p["latitude"], 3), "lon": round(p["longitude"], 3), "pop": int(pop)})
cities.sort(key=lambda c: -c["pop"])
jsave(cities, f"{DATA}/cities.json")
print("countries", len(cname), "cities", len(cities), "world", os.path.getsize(f"{DATA}/world.json") // 1024, "KB")
