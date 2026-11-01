"""Reddit collage (r/dataisbeautiful style): every track in IBTrACS on a light Pacific-centred world map, coloured by
Saffir-Simpson category, with a full legend on the paper below the map, a few labels placed by a script on open sea
only (checked against a track-density grid, the land, the map edge and each other; leader lines checked against every
label), and a strip of small charts. Output: reddit/hurricane_tracks.png. All numbers come from data/results.json.
Set FAST=1 to skip drawing the tracks (shows the density grid instead) while adjusting labels."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from figstyle import *
from matplotlib.path import Path
from matplotlib.patches import Rectangle

R = jload(f"{DATA}/results.json")
c, sh, lm, st, lf, gn = R["counts"], R["shares"], R["lmi"], R["strongest"], R["landfall"], R["genesis"]
P = pd.read_pickle(f"{WORK}/points.pkl")
S = pd.read_pickle(f"{WORK}/storms.pkl")
seg, cats, seas = segments(P)
FAST = os.environ.get("FAST")
OUT = os.path.join(ROOT, "reddit", "hurricane_tracks.png") if not FAST else f"{WORK}/collage_fast.png"

WIN, HIN, DPI = 16, 13, 200          # 3200 x 2600 px
fig = plt.figure(figsize=(WIN, HIN), facecolor=BG)
# ---------- title ----------
fig.text(.035, .962, "Every hurricane, typhoon and cyclone since 1851", fontproperties=DISP, fontsize=41, color=FG, va="top")
L1 = f"All {c['n_systems']:,} tropical storms and depressions in NOAA's global best track archive, {R['meta']['first']} to {R['meta']['last']}, each line"
L2 = f"coloured by its strength at every point. Since 1980 the share reaching Category 4 or 5 has risen from {sh['global'][0]['s4']:.0f}% in the"
L3 = f"1980s to {sh['global'][3]['s4']:.0f}% in the 2010s, and storms peak further from the equator. The number of storms has not clearly changed."
for i, L in enumerate((L1, L2, L3)):
    fig.text(.035, .907 - i * .024, L, fontproperties=SERP, fontsize=17, color=FG, va="top")
fig.text(.035, .835, "Before satellites (about 1970) many storms out at sea were never seen, so the early record is thin.",
         fontproperties=SERI, fontsize=17, color=MUT, va="top")

# ---------- map ----------
ax = fig.add_axes([0.0, .335, 1.0, .475]); ax.set_facecolor(BG)
x0, x1, y0, y1 = -17.25e6, 17.25e6, -6.0e6, 7.25e6
world(ax, land="#E2DCCF", edge="#CDC6B8")
LW.update({-1: .22, 0: .26, 1: .34, 2: .46, 3: .56, 4: .66, 5: .76, 6: .86})
AL.update({-1: .22, 0: .30, 1: .34, 2: .55, 3: .62, 4: .70, 5: .74, 6: .80})
if not FAST:
    tracks(ax, seg, cats, scale=1.75)
ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)
fig.canvas.draw()
rend = fig.canvas.get_renderer()

# occupancy grid in data coordinates: track density, land, outside the map
GX, GY = 690, 266
gx = np.linspace(x0, x1, GX + 1); gy = np.linspace(y0, y1, GY + 1)
mid = (seg[:, 0, :] + seg[:, 1, :]) / 2
H = np.zeros((GY, GX))
for pts in (seg[:, 0, :], mid, seg[:, 1, :], (seg[:, 0, :] + mid) / 2, (mid + seg[:, 1, :]) / 2):
    h, _, _ = np.histogram2d(pts[:, 1], pts[:, 0], bins=[gy, gx]); H += h
cx = (gx[:-1] + gx[1:]) / 2; cy = (gy[:-1] + gy[1:]) / 2
CX, CY = np.meshgrid(cx, cy)
landm = np.zeros(CX.shape, bool)
for poly in land_polys():
    if poly[:, 0].max() < x0 or poly[:, 0].min() > x1:
        continue
    landm |= Path(poly).contains_points(np.c_[CX.ravel(), CY.ravel()]).reshape(CX.shape)
outside = ~Path(outline_xy()).contains_points(np.c_[CX.ravel(), CY.ravel()]).reshape(CX.shape)
if FAST:
    ax.imshow(np.log1p(H), extent=(x0, x1, y0, y1), origin="lower", cmap="Greys", alpha=.6, zorder=2, aspect="auto")
PLACED, LEADERS = [], []


def cells(bb):
    i0 = max(0, np.searchsorted(gx, bb[0]) - 1); i1 = min(GX, np.searchsorted(gx, bb[2]) + 1)
    j0 = max(0, np.searchsorted(gy, bb[1]) - 1); j1 = min(GY, np.searchsorted(gy, bb[3]) + 1)
    return slice(j0, j1), slice(i0, i1)


def overlaps(bb):
    return [o for o in PLACED if bb[0] < o[2] and bb[2] > o[0] and bb[1] < o[3] and bb[3] > o[1]]


def score(bb):
    if bb[0] < x0 or bb[2] > x1 or bb[1] < y0 or bb[3] > y1:
        return 1e9
    sj, si = cells(bb)
    return H[sj, si].sum() + 1000 * landm[sj, si].sum() + 1000 * outside[sj, si].sum() + 1e6 * len(overlaps(bb))


def text_size(t):
    e = t.get_window_extent(rend).transformed(ax.transData.inverted())
    return e.x1 - e.x0, e.y1 - e.y0


def find(w, h, home, maxd=6e6, step=.07e6, pad=.16e6, kd=1500):
    """Best top-left anchor for a w x h box whose centre lies within maxd of home (lon, lat): fewest tracks under it,
    plus kd per 1,000 km from home; never on land, off the map or on another label."""
    hx, hy = proj(*home)
    best = None
    for X in np.arange(hx - maxd - w / 2, hx + maxd - w / 2, step):
        for Y in np.arange(hy - maxd * .6 + h / 2, hy + maxd * .6 + h / 2, step):
            bb = [X - pad, Y - h - pad, X + w + pad, Y + pad]
            d = math.hypot(X + w / 2 - hx, Y - h / 2 - hy)
            if d > maxd:
                continue
            sc = score(bb) + kd * d / 1e6
            if best is None or sc < best[0]:
                best = (sc, X, Y, bb)
    sj, si = cells(best[3])
    ok = landm[sj, si].sum() == 0 and outside[sj, si].sum() == 0 and not overlaps(best[3])
    if not ok:
        msg = ("no open sea for a label", home, round(best[0]), int(landm[sj, si].sum()), int(outside[sj, si].sum()), len(overlaps(best[3])))
        if FAST: print("  WARNING", msg)
        else: raise AssertionError(msg)
    return best


def place(text, home, maxd=6e6, kd=1500, **kw):
    t = ax.text(0, 0, text, zorder=30, **kw)
    w, h = text_size(t)
    sc, X, Y, bb = find(w, h, home, maxd=maxd, kd=kd)
    t.set_position((X, Y)); halo(t, 5, BG); PLACED.append(bb)
    sj, si = cells(bb)
    print(f"  label {text.splitlines()[0]!r}: track density under it {H[sj, si].sum():.0f}, land cells {landm[sj, si].sum()}")
    return t


def callout(name, season, text, lon, lat, home, maxd=4e6):
    s = S[(S.nm == name) & (S.season == season)].iloc[0]
    g = P[P.SID == s.SID].sort_values("t")
    x, y = proj(g.lon.values, g.lat.values)
    ax.plot(x, y, color=FG, lw=4.2, alpha=.92, zorder=20, solid_capstyle="round")
    for i in range(len(x) - 1):
        k = g.cat.values[i]
        ax.plot(x[i:i + 2], y[i:i + 2], color=UNK_COL if k < 0 else CAT_COL[k], lw=2.2, zorder=21, solid_capstyle="round")
    px, py = proj(lon, lat)
    place(text, home, maxd=maxd, **CAL)
    bb = PLACED[-1]
    ex, ey = min(((bb[0] + .11e6, bb[3] - .11e6), (bb[2] - .11e6, bb[3] - .11e6), (bb[0] + .11e6, bb[1] + .11e6), (bb[2] - .11e6, bb[1] + .11e6)),
                 key=lambda q: (q[0] - px) ** 2 + (q[1] - py) ** 2)
    LEADERS.append((np.c_[np.linspace(px, ex, 200), np.linspace(py, ey, 200)], len(PLACED) - 1))
    ax.plot([px, ex], [py, ey], color=FG, lw=1.2, zorder=29, path_effects=[pe.withStroke(linewidth=3.2, foreground=BG)])
    ax.scatter([px], [py], s=40, color=FG, edgecolor=BG, linewidth=1.5, zorder=32)


LAB = dict(fontproperties=SERB, fontsize=13.5, color=FG, va="top", ha="left", linespacing=1.15)
CAL = dict(fontproperties=SERP, fontsize=13, color=FG, va="top", ha="left", linespacing=1.15)
bm = c["basin_ts_mean"]
pt = [x for x in st["wind"] if x["name"] == "Patricia"][0]
s_p = S[(S.nm == "Patricia") & (S.season == 2015)].iloc[0]
hy = lf["strongest"][0]
callout("Haiyan", 2013, f"Haiyan, 2013: the strongest\nlandfall, {hy['kt']:.0f} kt on Leyte", 125.0, 11.0, (165, 1))
callout("Patricia", 2015, f"Patricia, 2015: {pt['kt']} kt ({pt['mph']} mph),\nthe highest wind measured", s_p.lmi_lon, s_p.lmi_lat, (-118, -10))
for txt, home in [(f"Western North Pacific\n{bm['WP']:.1f} storms a year", (160, 48)),
                  (f"Eastern Pacific\n{bm['EP']:.1f} a year", (-140, 1)),
                  (f"North Atlantic\n{bm['NA']:.1f} a year", (-40, 4)),
                  (f"North Indian\n{bm['NI']:.1f} a year", (65, 3)),
                  (f"South Indian\n{bm['SI']:.1f} a year", (75, -40)),
                  (f"South Pacific\n{bm['SP']:.1f} a year", (-175, -42)),
                  (f"South Atlantic\n{gn['sa_n']} storms since 1980", (-20, -20))]:
    place(txt, home, **LAB)
place(f"Almost none form\nnear the equator", (-160, 1), fontproperties=SERI, fontsize=13.5, color=MUT, va="top", ha="left", linespacing=1.15)
# no leader line may cross any label but its own
for line, own in LEADERS:
    for i, o in enumerate(PLACED):
        if i == own:
            continue
        inside = (line[:, 0] > o[0]) & (line[:, 0] < o[2]) & (line[:, 1] > o[1]) & (line[:, 1] < o[3])
        if FAST and inside.any(): print("  WARNING leader crosses label", i)
        else: assert not inside.any(), "a leader line crosses a label"

# ---------- legend (paper, below the map) ----------
lg = [(6, "Category 5", "137 kt or more"), (5, "Category 4", "113 to 136 kt"), (4, "Category 3", "96 to 112 kt"), (3, "Category 2", "83 to 95 kt"),
      (2, "Category 1", "64 to 82 kt"), (1, "Tropical storm", "34 to 63 kt"), (0, "Tropical depression", "under 34 kt"), (-1, "No wind recorded", "mostly before the 1940s")]
fig.text(.035, .325, "Strength at each point", fontproperties=DISPB, fontsize=15.5, color=FG, va="top")
fig.text(.035, .304, "Saffir-Simpson scale, 1-minute\nsustained wind (knots)", fontsize=10.5, color=MUT, va="top", linespacing=1.3)
for i, (k, a_, b_) in enumerate(lg):
    col, row = i % 4, i // 4
    xx, yy = .235 + col * .19, .322 - row * .036
    fig.add_artist(plt.Line2D([xx, xx + .028], [yy - .008, yy - .008], color=UNK_COL if k < 0 else CAT_COL[k], lw=6, solid_capstyle="round"))
    fig.text(xx + .036, yy, a_, fontproperties=SERB, fontsize=13, color=FG, va="top")
    fig.text(xx + .036, yy - .016, b_, fontsize=10.5, color=MUT, va="top")

# ---------- chart strip ----------
yb, hb = .07, .108
ty = yb + hb + .036


def head(x, a, b):
    fig.text(x, ty, a, fontproperties=SERB, fontsize=15.5, color=FG)
    fig.text(x, ty - .018, b, fontsize=10.5, color=MUT)


fig.add_artist(plt.Line2D([.035, .965], [.243, .243], color=RULE, lw=1.2))
# (a) storms per year by decade
a1 = fig.add_axes([.06, yb, .2, hb]); a1.set_facecolor(BG)
PY = R["per_year"]; yrs = np.array(PY["years"])
B = [b[0] for b in BASINS]
allv = np.sum([PY[f"{b}_all"] for b in B], axis=0); tsv = np.sum([PY[f"{b}_ts"] for b in B], axis=0)
decs = list(range(1850, 2030, 10))
da = [allv[(yrs // 10 * 10) == d].mean() for d in decs]; dt = [tsv[(yrs // 10 * 10) == d].mean() for d in decs]
for i, d in enumerate(decs):
    pre = d < 1970
    a1.bar(i, da[i], color="#D9D3C7" if pre else "#B7C7D4", width=.78)
    a1.bar(i, dt[i], color="#8E8778" if pre else INK, width=.78)
a1.axvspan(-.6, (1970 - 1850) / 10 - .5, color=PRE, alpha=.13, lw=0)
a1.text(.0, max(da) * 1.0, "before satellites:\nstorms missed", fontsize=10, color=MUT, va="top")
a1.set_xticks([0, 5, 10, 15]); a1.set_xticklabels(["1850s", "1900s", "1950s", "2000s"], fontsize=10)
a1.tick_params(axis="y", labelsize=10); spines(a1); a1.set_xlim(-.6, len(decs) - .4)
head(.035, "Storms recorded a year", "decade average; dark: reached 34 kt")
# (b) share reaching Cat 3+ and Cat 4+
a2 = fig.add_axes([.305, yb, .2, hb]); a2.set_facecolor(BG)
G = sh["global"]
for i, r in enumerate(G):
    a2.bar(i - .19, r["s3"], width=.36, color=CAT_COL[4]); a2.bar(i + .19, r["s4"], width=.36, color=CAT_COL[5])
    a2.text(i - .19, r["s3"] + .8, f"{r['s3']:.0f}", ha="center", fontsize=9.5, color=FG)
    a2.text(i + .19, r["s4"] + .8, f"{r['s4']:.0f}", ha="center", fontsize=9.5, color=FG)
a2.set_xticks(range(len(G))); a2.set_xticklabels([f"{str(r['dec'])[2:]}s" for r in G], fontsize=10); a2.set_ylim(0, 40)
a2.set_yticks([0, 10, 20, 30]); a2.set_yticklabels(["0%", "10%", "20%", "30%"], fontsize=10); spines(a2)
for j, (k, nm_) in enumerate(((4, "Category 3+"), (5, "Category 4+"))):
    a2.add_patch(Rectangle((.02 + j * .5, .9), .05, .07, transform=a2.transAxes, color=CAT_COL[k], clip_on=False))
    a2.text(.09 + j * .5, .935, nm_, transform=a2.transAxes, fontsize=10, color=FG, va="center")
head(.28, "Share reaching Category 3+ and 4+", "storms of 34 kt or more, 1980 to 2025")
# (c) latitude of peak intensity
a3 = fig.add_axes([.55, yb, .19, hb]); a3.set_facecolor(BG)
yy = np.array(lm["years"])
for h_, col in (("N", HOT), ("S", COOL)):
    v = np.array(lm[h_]); a3.plot(yy, v, color=col, lw=1.2, alpha=.8)
    b_ = np.polyfit(yy, v, 1); a3.plot(yy, np.polyval(b_, yy), color=col, lw=2.4, ls=(0, (4, 2.5)))
a3.set_ylim(14.5, 23.8); a3.set_yticks([16, 18, 20, 22]); a3.set_yticklabels(["16°", "18°", "20°", "22°"], fontsize=10)
a3.set_xticks([1980, 2000, 2020]); a3.tick_params(axis="x", labelsize=10); spines(a3)
a3.text(1981, 23.6, f"North: +{lm['N_trend']['km_per_dec']:.0f} km a decade", color=HOT, fontsize=10, va="top")
a3.text(1981, 14.8, f"South: +{lm['S_trend']['km_per_dec']:.0f} km a decade", color=COOL, fontsize=10, va="bottom")
head(.525, "Storms peak further poleward", "average latitude of each storm's peak")
# (d) records
tp = st["pressure"][0]
head(.78, "Records", "in the archive, 1851 to 2025")
recs = [("Highest wind", f"Patricia, 2015, and Nancy, 1961: {pt['kt']} kt"), ("Lowest pressure", f"Tip, 1979: {tp['pres']} hPa"),
        ("Strongest landfall", f"Haiyan, 2013, Philippines: {hy['kt']:.0f} kt"),
        ("Most landfalls since 1980", f"{lf['top'][0]['name']}: {lf['top'][0]['ts']} storms"),
        ("Most at typhoon strength", f"{lf['top_hu'][0]['name']}: {lf['top_hu'][0]['hu']} storms")]
for i, (a_, b_) in enumerate(recs):
    yy_ = yb + hb + .004 - i * .0265
    fig.text(.78, yy_, a_, fontproperties=SERB, fontsize=11.5, color=FG, va="top")
    fig.text(.78, yy_ - .0125, b_, fontproperties=SERP, fontsize=11, color=FG, va="top")
# ---------- footer ----------
fig.add_artist(plt.Line2D([.035, .965], [.040, .040], color=FG, lw=1.2))
fig.text(.035, .030, f"Data: NOAA NCEI, IBTrACS v04r01 (Knapp et al. 2010), all basins, {R['meta']['first']} to {R['meta']['last']}; NOAA data, no copyright restrictions. Land: Natural Earth.",
         fontsize=10.5, color=MUT, va="top")
fig.text(.035, .015, "Intensity comparisons use 1980 onwards and the US agencies' 1-minute winds. Equal Earth projection.",
         fontsize=10.5, color=MUT, va="top")
fig.text(.965, .030, "Dr Tristan Hotham", fontproperties=SERB, fontsize=13, color=FG, ha="right", va="top")
fig.text(.965, .013, "maps.tristanhotham.com/hurricane-tracks", fontsize=11, color=HOT, ha="right", va="top")
fig.savefig(OUT, dpi=DPI if not FAST else 100, facecolor=BG)
plt.close(fig)
from PIL import Image
im = Image.open(OUT); print("collage", im.size, os.path.getsize(OUT) // 1024, "KB")
