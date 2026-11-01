"""data/results.json: every number quoted in the page, paper, blog, README, collage and Reddit post.
Built from WORK/analysis.json plus metadata; adds a few derived figures used in the text."""
from common import *

A = jload(f"{WORK}/analysis.json")
C1 = jload(f"{WORK}/counts01.json")
R = dict(A)
c, sh, lm, lf, st = A["counts"], A["shares"], A["lmi"], A["landfall"], A["strongest"]
R["meta"] = {"page": PAGE, "repo": REPO, "retrieved": RETRIEVED, "version": "v04r01", "first": FIRST, "last": LAST, "sat0": SAT0,
             "presat": PRESAT, "n_rows": C1["n_rows"], "n_points": C1["n_points"], "n_storms": C1["n_storms"],
             "n_seasons": LAST - FIRST + 1, "doi": DOI}
hv = sh["halves"]
g = {x["dec"]: x for x in sh["global"]}
R["k"] = {
    "c4_1980s": g[1980]["s4"], "c4_2010s": g[2010]["s4"], "c3_1980s": g[1980]["s3"], "c3_2010s": g[2010]["s3"],
    "c4_2020s": g[2020]["s4"], "c3_2020s": g[2020]["s3"],
    "c4_rel": 100 * (hv["s4_2"] / hv["s4_1"] - 1), "c4_ratio": hv["s4_2"] / hv["s4_1"],
    "lmi_n_km": lm["N_trend"]["km_per_dec"], "lmi_s_km": lm["S_trend"]["km_per_dec"], "lmi_g_km": lm["G_trend"]["km_per_dec"],
    "lmi_wp_km": lm["basins"]["WP"]["km_per_dec"], "lmi_na_km": lm["basins"]["NA"]["km_per_dec"],
    "lmi_g_total_km": lm["G_trend"]["km_per_dec"] * (LAST - SAT0) / 10,
    "ts_per_year": c["sat_ts_mean"], "hu_per_year": c["sat_hu_mean"], "c4_per_year": c["sat_c4_mean"],
    "top_country": lf["top"][0]["name"], "top_country_ts": lf["top"][0]["ts"], "top_hu_country": lf["top_hu"][0]["name"], "top_hu_country_hu": lf["top_hu"][0]["hu"],
    "top_region": lf["top_regions"][0]["region"], "top_region_ts": lf["top_regions"][0]["ts"],
    "gen_lon_w": -A["genesis"]["top"][0]["lon"],
    "n_ts_all": c["n_ts"], "n_hu_all": c["n_hu"], "n_systems": c["n_systems"],
}
# checks on the statements made in words
assert lf["top"][0]["name"] == "China" and lf["top_hu"][0]["name"] == "Philippines" and lf["top_mj"][0]["name"] == "Philippines"
assert lf["top_regions"][0]["region"] == "Guangdong"
assert st["wind"][0]["name"] == "Patricia" and st["wind"][0]["kt"] == 185 and st["wind"][1]["name"] == "Nancy" and st["wind"][1]["kt"] == 185
assert st["pressure"][0]["name"] == "Tip" and st["pressure"][0]["pres"] == 870
assert hv["p4"] < 0.01 and hv["p3"] > 0.05 and hv["trend3"]["lo"] < 0 < hv["trend3"]["hi"] and hv["trend4"]["lo"] > 0
assert lm["N_trend"]["lo"] > 0 and lm["basins"]["WP"]["km_lo"] > 0 and lm["basins"]["NA"]["km_per_dec"] < 0 and lm["basins"]["NA"]["km_hi"] > 0
assert c["sat_ts_trend"]["lo"] < 0 < c["sat_ts_trend"]["hi"] and A["ace"]["trend"]["lo"] < 0 < A["ace"]["trend"]["hi"]
assert max(g, key=lambda d: g[d]["s4"]) == 2010 and min(g, key=lambda d: g[d]["s4"]) == 1980
jsave(R, f"{DATA}/results.json", indent=1)
print("results.json", os.path.getsize(f"{DATA}/results.json") // 1024, "KB")
print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in R["k"].items()})
