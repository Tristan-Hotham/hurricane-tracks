"""Shared paths, constants and helpers for the hurricane-tracks project.

Raw inputs (read in place, never modified):
  /home/claude/newdata/raw8/hurricanes/ibtracs_6hourly.tsv
      NOAA NCEI, International Best Track Archive for Climate Stewardship (IBTrACS) version 4, revision v04r01
      (Knapp et al. 2010; Gahtan et al. 2024), all basins, fetched 2026 and reduced to the synoptic 6-hourly points
      (00, 06, 12 and 18 UTC). Columns: SID, SEASON, BASIN, SUBBASIN, NAME, ISO_TIME, NATURE, LAT, LON, WMO_WIND,
      WMO_PRES, USA_WIND, USA_SSHS, DIST2LAND, LANDFALL, TRACK_TYPE, STORM_SPEED, STORM_DIR. NOAA data, no copyright
      restrictions (public domain in the United States).
  /home/claude/newdata/raw8/hurricanes/wiki_Tropical_cyclone.json, wiki_Saffir_Simpson_scale.json
      English Wikipedia articles (parsed HTML), CC BY-SA 4.0; used only for the Saffir-Simpson thresholds and for
      background statements that are quoted and credited.
  /home/claude/newdata/raw/geo/ne_10m_admin_0_countries.geojson, ne_10m_admin_1_states_provinces.geojson,
      ne_50m_admin_0_countries.geojson, ne_50m_land.geojson, ne_10m_populated_places_simple.geojson
      Natural Earth (public domain).
"""
import json, gzip, os, re, math, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("HUR_RAW", "/home/claude/newdata/raw8/hurricanes")
IBT = os.path.join(RAW, "ibtracs_6hourly.tsv")
GEO = os.environ.get("HUR_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("HUR_FONTS", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
WORK = os.path.join(os.environ.get("HURTMP", "/dev/shm/hurricanes"), "work")
for d in (DATA, WORK, os.path.join(DATA, "tracks")):
    os.makedirs(d, exist_ok=True)

SLUG = "hurricane-tracks"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
DOI = "10.5281/zenodo.23858051"                  # filled in by the publisher
BLOG = "https://blog.tristanhotham.com/2026/10/31/hurricane-tracks/"            # filled in by the publisher
RETRIEVED = "2026"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
IBT_CREDIT = ("NOAA National Centers for Environmental Information, International Best Track Archive for Climate "
              "Stewardship (IBTrACS) v04r01 (Knapp et al. 2010; Gahtan et al. 2024). NOAA data, no copyright restrictions")

FIRST, LAST = 1851, 2025      # complete seasons analysed (2026 is shown on the map but is incomplete and provisional)
SAT0 = 1980                   # start of the era used for comparisons (global geostationary satellite coverage)
PRESAT = 1970                 # before this the record clearly misses storms

# Saffir-Simpson categories by 1-minute sustained wind in knots (Wikipedia, Saffir-Simpson scale)
# index: 0 tropical depression (<34), 1 tropical storm (34-63), 2..6 categories 1..5; -1 = wind not recorded
CATS = [("Tropical depression", "TD", 0), ("Tropical storm", "TS", 34), ("Category 1", "C1", 64), ("Category 2", "C2", 83),
        ("Category 3", "C3", 96), ("Category 4", "C4", 113), ("Category 5", "C5", 137)]
CAT_COL = ["#9FB6C9", "#3F8CC4", "#E9C33F", "#F0952F", "#E0552A", "#C01D3D", "#6E1150"]
CAT_COL_DARK = ["#6F8698", "#5FB0EA", "#F5D45A", "#FFAA45", "#FF6E42", "#FF4D6A", "#E05CC2"]
UNK_COL = "#B8B0A2"

# genesis basins as IBTrACS codes them (CP storms are coded EP with sub-basin CP)
BASINS = [("NA", "North Atlantic", "#1F5A99"), ("EP", "Eastern and central North Pacific", "#2A9D8F"),
          ("WP", "Western North Pacific", "#B3202A"), ("NI", "North Indian", "#C98A12"),
          ("SI", "South Indian", "#7A4E9C"), ("SP", "South Pacific", "#5E7D2A"), ("SA", "South Atlantic", "#8A8A8A")]
BNAME = {b[0]: b[1] for b in BASINS}
BCOL = {b[0]: b[2] for b in BASINS}
NH = ("NA", "EP", "WP", "NI")


def cat_of(w):
    """Saffir-Simpson index (0..6) for a wind in knots, or -1 if missing."""
    if w is None or (isinstance(w, float) and math.isnan(w)):
        return -1
    c = 0
    for i, (_, _, t) in enumerate(CATS):
        if w >= t:
            c = i
    return c


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[\W_]+", " ", s).strip()


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "sf1": return f"{float(v):+.1f}"
    if f == "sf2": return f"{float(v):+.2f}"
    if f == "p3": return "under 0.001" if float(v) < 0.001 else f"{float(v):.3f}"
    if f == "p2": return "under 0.01" if float(v) < 0.01 else f"{float(v):.2f}"
    raise ValueError(f)


def kt_mph(k): return int(5 * round(k * 1.15078 / 5))
def kt_kmh(k): return int(5 * round(k * 1.852 / 5))


def title_name(n):
    """IBTrACS names are upper case; 'NOT_NAMED' and 'UNNAMED' mean no name."""
    if not n or n in ("NOT_NAMED", "UNNAMED", "NAMELESS"):
        return ""
    parts = n.split(":")
    return ":".join(p.title().replace("'S", "'s") for p in parts)
