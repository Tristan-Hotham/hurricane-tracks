"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json; results and site.json are embedded; tracks (tiled by decade), the search index, landfalls,
outlines and town names are loaded by the page from data/. The full-screen map snippet is pasted before </body>.
10.5281/zenodo.23858051 and https://blog.tristanhotham.com/2026/10/31/hurricane-tracks/ stay as placeholders for the publisher. Facts stated in words are checked here."""
import json
from common import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")
KEEP = ("DOI", "BLOG_URL")
lf, st, sh, lm, gn = R["landfall"], R["strongest"], R["shares"], R["lmi"], R["genesis"]

# facts stated in words (page, blog and paper share them)
pm = gn["peak_month"]
assert (pm["NA"], pm["EP"], pm["WP"], pm["SI"], pm["SP"]) == (9, 8, 8, 1, 2)
ni = gn["by_month"]["NI"]; assert max(ni[:6]) == ni[4] and max(ni[6:]) == ni[10]          # North Indian: May and November
assert lf["top"][5]["name"] == "United States" and lf["all_top"][0]["name"] == "United States"
assert [x["region"] for x in lf["top_regions"][:5]] == ["Guangdong", "Western Australia", "Fujian", "Queensland", "Florida"]
assert lf["top_regions_mj"][2]["region"] == "Cagayan"
assert [(x["name"], x["region"]) for x in lf["strongest"][:3]] == [("Haiyan", "Leyte"), ("Meranti", "Batanes"), ("Dorian", "Central Abaco")]
assert lf["top_hu"][0]["name"] == lf["top_mj"][0]["name"] == "Philippines"
g = {x["dec"]: x["s4"] for x in sh["global"]}
assert g[1990] - g[1980] > max(abs(g[2000] - g[1990]), abs(g[2010] - g[2000]))      # most of the rise between the 1980s and 1990s
hb = sh["halves"]["basins"]
assert hb["SP"]["p4"] < .01 and hb["WP"]["p4"] < .01 and hb["SI"]["p4"] < .05 and hb["NA"]["p4"] > .2 and hb["EP"]["p4"] > .2 and hb["NI"]["p4"] > .05
assert round(sh["halves"]["inv4_1"]) == 6 and round(sh["halves"]["inv4_2"]) == 5
assert max(lm["basins"], key=lambda b: lm["basins"][b]["km_per_dec"]) == "WP"
assert st["c5_by_basin"]["WP"] > st["n_c5"] / 2
assert R["counts"]["first_wind"]["SI"] == 1957 and R["counts"]["first_wind"]["NI"] == 1972
assert R["counts"]["coverage"][5]["dec"] == 1900 and R["counts"]["coverage"][14]["dec"] == 1990
assert gn["sa_n"] <= 3
L_and = [x for x in jload(f"{DATA}/landfalls.json")["rows"]]
assert R["landfall"]["strongest"][0]["season"] == 2013


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = re.sub(r"\{\{(?!DOI\}\}|BLOG_URL\}\})([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), tpl)
    left = [x for x in re.findall(r"\{\{([^}]*)\}\}", html) if x not in KEEP]
    assert not left, left[:5]
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*RESULTS*/", J(R)).replace("/*SITE*/", J(SITE))
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
