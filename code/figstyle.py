"""House style for static figures: fonts (static instances cut from the variable Fraunces in /home/claude/ref/fonts,
written to WORK), the palette, Natural Earth land in a Pacific-centred Equal Earth projection (seam at 20 degrees east,
through Africa and Europe, where no tropical cyclone track crosses), and tracks drawn by Saffir-Simpson category."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly
from matplotlib.collections import LineCollection, PolyCollection
import matplotlib.patheffects as pe
import numpy as np
import pandas as pd
from pyproj import Transformer
from shapely.geometry import shape, box
from shapely import affinity
from common import *

FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, nm in ((900, "Black"), (700, "Bold"), (600, "Semibold")):
        instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": w, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-{nm}.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
DISPB = fm.FontProperties(fname=f"{FD}/Fraunces-Bold.ttf")
DISPS = fm.FontProperties(fname=f"{FD}/Fraunces-Semibold.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
SERI = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-It.ttf")
SERB = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Semibold.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 12, "axes.edgecolor": "#626870", "axes.labelcolor": "#1C2027",
                     "xtick.color": "#626870", "ytick.color": "#626870"})
BG, FG, MUT, LAND, RULE, SEA = "#F6F4EF", "#1C2027", "#626870", "#E3DED2", "#DDD8CC", "#F6F4EF"
HOT, COOL, GOLD, INK, PRE = "#C01D3D", "#3F8CC4", "#E9A23B", "#1F3A5F", "#B9B2A6"
LON0 = -160.0
EE = Transformer.from_crs("EPSG:4326", "+proj=eqearth +lon_0=0 +datum=WGS84 +units=m", always_xy=True)
rel = lambda lon: (np.asarray(lon, float) - LON0 + 180) % 360 - 180


def proj(lon, lat):
    return EE.transform(rel(lon), np.clip(np.asarray(lat, float), -89.9, 89.9))


_LAND = None


def land_polys():
    """Natural Earth 1:50m land, cut at the seam and projected (list of Nx2 arrays)."""
    global _LAND
    if _LAND is None:
        out = []
        for f in jload(f"{GEO}/ne_50m_land.geojson")["features"]:
            g = affinity.translate(shape(f["geometry"]), xoff=-LON0)
            for bx, sh in ((box(-180, -90, 180, 90), 0), (box(180, -90, 540, 90), -360), (box(-540, -90, -180, 90), 360)):
                part = g.intersection(bx)
                if part.is_empty:
                    continue
                part = affinity.translate(part, xoff=sh)
                for p in getattr(part, "geoms", [part]):
                    if p.geom_type != "Polygon" or p.area < 0.02:
                        continue
                    xy = np.array(p.exterior.coords)
                    x, y = EE.transform(np.clip(xy[:, 0], -179.999, 179.999), np.clip(xy[:, 1], -89.9, 89.9))
                    out.append(np.c_[x, y])
        _LAND = out
    return _LAND


def outline_xy(n=361):
    lat = np.linspace(-90, 90, n)
    xl, yl = EE.transform(np.full(n, -179.999), lat); xr, yr = EE.transform(np.full(n, 179.999), lat[::-1])
    return np.c_[np.r_[xl, xr], np.r_[yl, yr]]


def world(ax, land=LAND, ec="none", lw=0, z=1, sea=None, edge=None):
    if sea:
        ax.add_patch(MPoly(outline_xy(), closed=True, fc=sea, ec="none", zorder=0))
    ax.add_collection(PolyCollection(land_polys(), facecolors=land, edgecolors=ec, linewidths=lw, zorder=z))
    if edge:
        ax.add_patch(MPoly(outline_xy(), closed=True, fc="none", ec=edge, lw=.8, zorder=z + 10))
    ax.set_aspect("equal"); ax.axis("off")


EXT = (-17.3e6, 17.3e6, -6.4e6, 7.9e6)   # x0, x1, y0, y1 (metres, Equal Earth)


def segments(P, cat_col="cat"):
    """Projected segments of every track, by category of the starting point; drops segments across the seam."""
    P = P.sort_values(["SID", "t"])
    x, y = proj(P.lon.values, P.lat.values)
    same = P.SID.values[1:] == P.SID.values[:-1]
    c = P[cat_col].values[:-1]
    seg = np.stack([np.c_[x[:-1], y[:-1]], np.c_[x[1:], y[1:]]], axis=1)
    ok = same & (np.abs(seg[:, 0, 0] - seg[:, 1, 0]) < 1.2e7)
    return seg[ok], c[ok], P.SEASON.values[:-1][ok]


LW = {-1: .25, 0: .25, 1: .32, 2: .45, 3: .55, 4: .7, 5: .85, 6: 1.0}
AL = {-1: .30, 0: .30, 1: .32, 2: .55, 3: .65, 4: .75, 5: .85, 6: .95}


def tracks(ax, seg, cats, scale=1.0, alpha=1.0, z=3, unk=True, cols=None):
    cols = cols or CAT_COL
    for c in range(-1, 7):
        if c == -1 and not unk:
            continue
        m = cats == c
        if not m.any():
            continue
        ax.add_collection(LineCollection(seg[m], colors=UNK_COL if c < 0 else cols[c], linewidths=LW[c] * scale,
                                         alpha=min(1, AL[c] * alpha), capstyle="round", zorder=z + c * .01))


def spines(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def halo(t, w=3, c="white"):
    t.set_path_effects([pe.withStroke(linewidth=w, foreground=c)])
    return t


def save(fig, path, dpi=200):
    fig.savefig(path, dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)
