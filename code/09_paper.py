"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex.
Output: release/paper/<NAME>.pdf and .tex (figures f_*.png sit beside them). The DOI stays a placeholder."""
import subprocess
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Every_Storm_since_1851"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "sf1": return f"{float(v):+.1f}"
    if f == "p3": return "$<$ 0.001" if float(v) < 0.001 else f"= {float(v):.3f}"
    return tex(str(v))


lf, st, sh, lm = R["landfall"], R["strongest"], R["shares"], R["lmi"]
rows = "".join(f"{tex(t['name'])} & {t['ts']} & {t['hu']} & {t['mj']} & {t['c5']} & {t['ts_py']:.1f}\\\\\n" for t in lf["top"][:25])
TC = ("\\begin{table}[tbp]\\centering\\small\\caption{Countries and territories with most landfalls, 1980 to " + str(R['meta']['last']) + ": storms making landfall at least once, by strength at landfall (interpolated wind).}\\label{tab:countries}"
      "\\begin{tabular}{lrrrrr}\\toprule Country & Tropical storm+ & Hurricane+ & Cat 3+ & Cat 5 & A year\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(t['region'])} & {tex(t['name'])} & {t['ts']} & {t['hu']} & {t['mj']}\\\\\n" for t in lf["top_regions"][:20])
TR = ("\\begin{table}[tbp]\\centering\\small\\caption{The most-hit states, provinces and prefectures (Natural Earth admin 1), 1980 to " + str(R['meta']['last']) + ".}\\label{tab:regions}"
      "\\begin{tabular}{llrrr}\\toprule Region & Country & Tropical storm+ & Hurricane+ & Cat 3+\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
BN = {b[0]: b[1] for b in BASINS}
rows = "".join(f"{tex(t['name'] or 'Unnamed')} & {t['season']} & {tex(BN[t['basin']])} & {t['kt']} & {t['pres'] or ''} & {tex(', '.join(t['hits']) or 'none')}\\\\\n" for t in st["wind"][:20])
TS = ("\\begin{table}[tbp]\\centering\\small\\caption{The 20 strongest storms by peak 1-minute wind (US agencies), ties ordered by lowest pressure, with countries where they made landfall at tropical storm strength or more.}\\label{tab:strongest}"
      "\\begin{tabular}{lrp{3.6cm}rrp{4.2cm}}\\toprule Storm & Season & Basin & kt & hPa & Landfalls\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
hb = sh["halves"]["basins"]
pf = lambda p: "$<$0.001" if p < .001 else f"{p:.3f}"
rows = "".join(f"{tex(BN[b])} & {x['n1']} / {x['n2']} & {x['s3_1']:.1f} & {x['s3_2']:.1f} & {pf(x['p3'])} & {x['s4_1']:.1f} & {x['s4_2']:.1f} & {pf(x['p4'])}\\\\\n" for b, x in hb.items())
h = sh["halves"]
rows += f"\\midrule World & {h['n1']} / {h['n2']} & {h['s3_1']:.1f} & {h['s3_2']:.1f} & {pf(h['p3'])} & {h['s4_1']:.1f} & {h['s4_2']:.1f} & {pf(h['p4'])}\\\\\n"
TSH = ("\\begin{table}[tbp]\\centering\\small\\caption{Share of storms (34 kt or more, US 1-minute wind) reaching Category 3+ and 4+, " + h["h1"] + " against " + h["h2"] + ", with two-proportion test $p$-values.}\\label{tab:shares}"
       "\\begin{tabular}{p{4.6cm}rrrrrrr}\\toprule Basin & $n$ & Cat 3+ \\% & & $p$ & Cat 4+ \\% & & $p$\\\\ & & first & second & & first & second & \\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{nm} & {t['km_per_dec']:+.0f} & {t['km_lo']:+.0f} to {t['km_hi']:+.0f} & {t['p']:.3f}\\\\\n" for nm, t in
               [("Both hemispheres", lm["G_trend"]), ("Northern Hemisphere", lm["N_trend"]), ("Southern Hemisphere", lm["S_trend"])] + [(tex(BN[b]), lm["basins"][b]) for b in lm["basins"]])
TL = ("\\begin{table}[tbp]\\centering\\small\\caption{Trend in the latitude of lifetime maximum intensity, 1980 to " + str(R['meta']['last']) + ", km a decade (positive: towards the pole), with 95\\% bootstrap intervals and OLS $p$-values.}\\label{tab:lmi}"
      "\\begin{tabular}{lrrr}\\toprule & km a decade & 95\\% interval & $p$\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k in ("page", "repo"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = t.replace("{{meta.doi}}", "@@DOI@@")
t = re.sub(r"\{\{(?!TABLE_)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
for k, v in (("COUNTRIES", TC), ("REGIONS", TR), ("STRONGEST", TS), ("SHARES", TSH), ("LMI", TL)):
    t = t.replace("{{TABLE_%s}}" % k, v)
assert "{{" not in t and "--" not in t and "\u2014" not in t and "\u2013" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:3]
t = t.replace("\\href{https://doi.org/@@DOI@@}{https://doi.org/@@DOI@@}", "https://doi.org/\\{\\{DOI\\}\\}")
t = t.replace("\\url{https://doi.org/@@DOI@@}", "https://doi.org/\\{\\{DOI\\}\\}")
assert "@@" not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l or l.startswith("!")][:12])
for ext in (".aux", ".log", ".out", ".bbl", ".blg"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("\u2014") + txt.count("\u2013") + txt.count("--"))
