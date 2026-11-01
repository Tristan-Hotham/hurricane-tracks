"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.23858051, https://doi.org/10.5281/zenodo.23858051 and https://blog.tristanhotham.com/2026/10/31/hurricane-tracks/ stay as placeholders for the publisher."""
import json as _json, shutil, zipfile
from common import *

R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Every_Storm_since_1851"
c, sh, lm, lf = R["counts"], R["shares"], R["lmi"], R["landfall"]

# numbers written in words in the blog alt text and captions
assert [t["name"] for t in lf["top"][:6]] == ["China", "Philippines", "Japan", "Australia", "Mexico", "United States"] and lf["top"][0]["ts"] == 263
assert 19 < lm["N_mean_1980s"] < 20 and 21 < lm["N_mean_2016_2025"] < 21.5 and 16.5 < lm["S_mean_1980s"] < 17 and 17 < lm["S_mean_2016_2025"] < 17.5
assert 60 < lm["basins"]["WP"]["km_per_dec"] < 70 and -55 < lm["basins"]["NA"]["km_per_dec"] < -50 and lm["basins"]["NA"]["km_hi"] > 0
g = sh["global"]; assert round(g[0]["s4"], 1) == 12.5 and 20 <= g[1]["s4"] < 21 and 20 <= g[2]["s4"] < 21 and round(g[3]["s4"], 1) == 22.8 and round(g[4]["s4"], 1) == 18.5
post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG|DOI_URL|BLOG_URL|DOI\}\})([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u), post, re.M) for u in used) and "wp:image" not in post
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS"):
    assert bad not in vis, bad
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "Every storm since 1851: where hurricanes form, where they hit, and are they getting stronger?",
        "slug": "hurricane-tracks",
        "excerpt": f"I mapped all {c['n_systems']:,} tropical cyclones in NOAA's global archive, from depressions to Category 5 typhoons. The number of storms has not changed since 1980, but more of them reach Category 4 or 5 and they peak further from the equator. Before satellites, the record misses too many storms to say much more.",
        "seo_description": f"Every hurricane, typhoon and cyclone since 1851 on one map: where they form, where they hit, and whether they are getting stronger.",
        "tags": ["hurricanes", "typhoons", "tropical cyclones", "climate", "maps", "data visualisation", "IBTrACS", "NOAA", "open data"],
        "header_alt": f"Title card reading 'Every storm since 1851' in black on pale paper, beside a Pacific-centred world map of thousands of storm tracks coloured from blue to deep red and plum by strength, densest east of the Philippines. Text: {c['n_systems']:,} tropical cyclones, by strength; Category 4+ share {g[0]['s4']:.0f}% in the 1980s, {g[3]['s4']:.0f}% in the 2010s."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/hurricane-tracks_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data"):
        for root, _, files in os.walk(os.path.join(ROOT, d)):
            for fn in sorted(files):
                if fn.endswith(".pyc"):
                    continue
                p = os.path.join(root, fn)
                z.write(p, "hurricane-tracks/" + os.path.relpath(p, ROOT))
    for fn in ("README.md", "LICENSE"):
        z.write(os.path.join(ROOT, fn), f"hurricane-tracks/{fn}")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), "hurricane-tracks/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("~", " ").replace("$<$", "<").replace("$p$", "p").replace("$", "")
zmeta = {"title": "Every Storm since 1851: Where Tropical Cyclones Form, Where They Hit, and Whether They Are Getting Stronger",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {{https://blog.tristanhotham.com/2026/10/31/hurricane-tracks/}}.</p><p>Data: NOAA National Centers for Environmental Information, IBTrACS v04r01 (Knapp et al. 2010; Gahtan et al. 2024), NOAA data with no copyright restrictions; Natural Earth (public domain).</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["tropical cyclones", "hurricanes", "typhoons", "IBTrACS", "landfall", "Saffir-Simpson scale", "climate", "observation bias", "maps", "open data"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "https://www.ncei.noaa.gov/products/international-best-track-archive", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
