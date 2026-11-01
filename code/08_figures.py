"""Static figures: header card (header.png), blog figures (release/blog/b_*.png) and paper figures
(release/paper/f_*.png). Numbers from data/results.json."""
import shutil
from figstyle import *

R = jload(f"{DATA}/results.json")
c, sh, lm, lf, gn = R["counts"], R["shares"], R["lmi"], R["landfall"], R["genesis"]
BL = os.path.join(ROOT, "release", "blog"); PA = os.path.join(ROOT, "release", "paper")
os.makedirs(BL, exist_ok=True); os.makedirs(PA, exist_ok=True)
P = pd.read_pickle(f"{WORK}/points.pkl")
seg, cats, seas = segments(P)
B = [b for b in BASINS]


def both(fig, name):
    p = f"{BL}/b_{name}.png"; save(fig, p)
    shutil.copy(p, f"{PA}/f_{name}.png")


# ---------- world map of every track ----------
fig = plt.figure(figsize=(14, 6.4), facecolor=BG)
ax = fig.add_axes([0, .08, 1, .92]); ax.set_facecolor(BG)
world(ax, land="#E2DCCF", edge="#CDC6B8")
tracks(ax, seg, cats, scale=1.25)
ax.set_xlim(-17.25e6, 17.25e6); ax.set_ylim(-6.0e6, 7.25e6)
for i, (nm, _, _) in enumerate(CATS[::-1]):
    k = 6 - i
    x = .03 + i * .118
    fig.add_artist(plt.Line2D([x, x + .025], [.045, .045], color=CAT_COL[k], lw=5, solid_capstyle="round"))
    fig.text(x + .03, .045, nm, fontsize=10, va="center", color=FG)
fig.add_artist(plt.Line2D([.03 + 7 * .118, .03 + 7 * .118 + .025], [.045, .045], color=UNK_COL, lw=5, solid_capstyle="round"))
fig.text(.03 + 7 * .118 + .03, .045, "No wind", fontsize=10, va="center", color=FG)
both(fig, "map")

# ---------- storms per season by basin ----------
PY = R["per_year"]; yrs = np.array(PY["years"])
fig, axs = plt.subplots(2, 1, figsize=(11, 7.2), facecolor=BG, sharex=True)
for ax_, key, ttl in ((axs[0], "all", "Every system in the archive"), (axs[1], "ts", "Reached tropical storm strength (34 kt), where a wind was recorded")):
    ax_.set_facecolor(BG); bot = np.zeros(len(yrs))
    for b, nm, col in B:
        v = np.array(PY[f"{b}_{key}"]); ax_.bar(yrs, v, bottom=bot, color=col, width=.9, label=nm); bot += v
    ax_.axvspan(1850.5, 1969.5, color=PRE, alpha=.15, lw=0)
    ax_.set_title(ttl, loc="left", fontproperties=SERB, fontsize=14, color=FG); spines(ax_)
axs[0].text(1853, axs[0].get_ylim()[1] * .92, "before satellites: storms missed", color=MUT, fontsize=10)
axs[0].legend(ncol=4, fontsize=9, frameon=False, loc="upper left", bbox_to_anchor=(0, -0.04 - 1.25))
axs[1].set_xlim(1850, 2026)
fig.subplots_adjust(left=.06, right=.99, top=.95, bottom=.16, hspace=.18)
both(fig, "peryear")

# ---------- genesis density ----------
Hs = np.load(f"{WORK}/genesis_grid.npy")
fig = plt.figure(figsize=(14, 6.2), facecolor=BG)
ax = fig.add_axes([0, .1, 1, .9]); ax.set_facecolor(BG)
world(ax, land="#E2DCCF", edge="#CDC6B8")
res = 0.25
lat = 90 - (np.arange(Hs.shape[0]) + .5) * res; lon = -180 + (np.arange(Hs.shape[1]) + .5) * res
LO, LA = np.meshgrid(lon, lat)
m = Hs > .15
X, Y = proj(LO[m], LA[m])
from matplotlib.colors import LinearSegmentedColormap, LogNorm
cm = LinearSegmentedColormap.from_list("g", ["#FFECB3", "#FDAE61", "#E45734", "#B2183F", "#5E0A48"])
o = np.argsort(Hs[m])
sc = ax.scatter(X[o], Y[o], c=Hs[m][o], s=1.1, cmap=cm, norm=LogNorm(.15, Hs.max()), marker="s", linewidths=0, zorder=3)
ax.set_xlim(-17.25e6, 17.25e6); ax.set_ylim(-5.0e6, 5.6e6)
cax = fig.add_axes([.3, .06, .4, .025]); cb = fig.colorbar(sc, cax=cax, orientation="horizontal")
cb.set_label("storms forming per decade in a 2.5 degree square, 1980 to 2025", fontsize=10, color=FG); cb.ax.tick_params(labelsize=9)
cb.set_ticks([.2, .5, 1, 2, 4]); cb.set_ticklabels(["0.2", "0.5", "1", "2", "4"]); cb.ax.minorticks_off()
both(fig, "genesis")

# ---------- landfalls by country ----------
T = lf["top"][:20][::-1]
fig, ax = plt.subplots(figsize=(9, 7.4), facecolor=BG); ax.set_facecolor(BG)
y = np.arange(len(T))
ts = np.array([t["ts"] for t in T]); hu = np.array([t["hu"] for t in T]); mj = np.array([t["mj"] for t in T])
ax.barh(y, ts - hu, left=hu, color=CAT_COL[1], label="Tropical storm at landfall")
ax.barh(y, hu - mj, left=mj, color=CAT_COL[2], label="Category 1 or 2")
ax.barh(y, mj, color=CAT_COL[5], label="Category 3 or more")
for i, t in enumerate(T):
    ax.text(t["ts"] + 3, i, f"{t['ts']}", va="center", fontsize=9.5, color=FG)
ax.set_yticks(y); ax.set_yticklabels([t["name"] for t in T], fontproperties=SERP, fontsize=11.5); spines(ax)
ax.set_xlabel("storms making landfall, 1980 to 2025 (a storm counts once per country)", fontsize=10)
ax.legend(frameon=False, fontsize=9.5, loc="lower right")
fig.tight_layout(); both(fig, "landfalls")

# ---------- shares of Category 3+ and 4+ by decade ----------
fig = plt.figure(figsize=(12, 7.6), facecolor=BG)
gs = fig.add_gridspec(2, 4, height_ratios=[1.25, 1], hspace=.55, wspace=.35)
ax = fig.add_subplot(gs[0, :]); ax.set_facecolor(BG)
G = sh["global"]
for i, r in enumerate(G):
    ax.bar(i - .19, r["s3"], width=.36, color=CAT_COL[4], label="Category 3 or more" if i == 0 else None)
    ax.bar(i + .19, r["s4"], width=.36, color=CAT_COL[5], label="Category 4 or more" if i == 0 else None)
    ax.text(i - .19, r["s3"] + .6, f"{r['s3']:.1f}", ha="center", fontsize=9.5); ax.text(i + .19, r["s4"] + .6, f"{r['s4']:.1f}", ha="center", fontsize=9.5)
ax.set_xticks(range(len(G))); ax.set_xticklabels([f"{r['years']}\nn = {r['n']}" for r in G], fontsize=10); ax.set_ylim(0, 36); spines(ax)
ax.set_ylabel("% of storms of 34 kt or more"); ax.legend(frameon=False, fontsize=10, loc="upper left")
ax.set_title("World, 1980 to 2025 (US agencies' 1-minute winds)", loc="left", fontproperties=SERB, fontsize=13.5)
for j, b in enumerate(["NA", "WP", "SI", "SP"]):
    a = fig.add_subplot(gs[1, j]); a.set_facecolor(BG)
    rows = sh["basins"][b]
    xs = np.arange(len(rows))
    for i, r in enumerate(rows):
        pale = r["cov"] < 80 or r["dec"] < 1970
        a.bar(i, r["s4"], color=CAT_COL[5], alpha=.3 if pale else 1, width=.75)
    a.set_xticks(xs[::2]); a.set_xticklabels([f"{r['dec']}s" for r in rows][::2], fontsize=8, rotation=45)
    a.set_ylim(0, 40); a.tick_params(axis="y", labelsize=8); spines(a)
    a.set_title(BNAME[b] + ", Cat 4+", loc="left", fontsize=9.5, fontproperties=SERB)
fig.text(.02, .02, "Pale bars: before 1970 or fewer than 80% of systems with a 1-minute wind.", fontsize=9, color=MUT)
both(fig, "shares")

# ---------- latitude of peak intensity ----------
fig, axs = plt.subplots(1, 2, figsize=(12, 4.8), facecolor=BG, gridspec_kw={"width_ratios": [1.5, 1]})
ax = axs[0]; ax.set_facecolor(BG); yy = np.array(lm["years"])
for h, col, nm in (("N", HOT, "Northern Hemisphere"), ("S", COOL, "Southern Hemisphere")):
    v = np.array(lm[h]); ax.plot(yy, v, "-o", color=col, ms=3, lw=1.2, label=f"{nm}: {lm[h + '_trend']['km_per_dec']:+.0f} km a decade")
    b_ = np.polyfit(yy, v, 1); ax.plot(yy, np.polyval(b_, yy), color=col, lw=2.2, ls="--")
ax.set_ylabel("mean latitude of peak (degrees from equator)"); ax.legend(frameon=False, fontsize=9.5, loc="upper left"); spines(ax); ax.set_ylim(14, 24)
ax = axs[1]; ax.set_facecolor(BG)
rows = [("Both hemispheres", lm["G_trend"], FG), ("Northern", lm["N_trend"], HOT), ("Southern", lm["S_trend"], COOL)] + [(BNAME[b], lm["basins"][b], BCOL[b]) for b in ["NA", "EP", "WP", "NI", "SI", "SP"]]
for i, (nm, t, col) in enumerate(rows):
    yv = len(rows) - 1 - i
    ax.plot([t["km_lo"], t["km_hi"]], [yv, yv], color=col, lw=2.6, alpha=.95 if (t["km_lo"] > 0 or t["km_hi"] < 0) else .45)
    ax.scatter([t["km_per_dec"]], [yv], color=col, s=30, zorder=3)
ax.axvline(0, color=FG, lw=1); ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0].replace("Eastern and central North Pacific", "E and C North Pacific") for r in rows][::-1], fontsize=9)
ax.set_xlabel("km a decade towards the pole, 95% interval", fontsize=9.5); spines(ax)
fig.tight_layout(); both(fig, "lmi")

# ---------- header card 1200 x 630 ----------
fig = plt.figure(figsize=(12, 6.3), facecolor=BG)
ax = fig.add_axes([.30, .02, .72, .96]); ax.set_facecolor(BG)
world(ax, land="#E2DCCF")
tracks(ax, seg, cats, scale=.9)
ax.set_xlim(-12.5e6, 15.5e6); ax.set_ylim(-5.6e6, 6.6e6)
fig.text(.035, .86, "Every\nstorm\nsince\n1851", fontproperties=DISP, fontsize=50, color=FG, va="top", linespacing=.92)
fig.text(.035, .31, f"{c['n_systems']:,} tropical cyclones, from\ndepressions to Category 5.\nCategory 4+ share: {sh['global'][0]['s4']:.0f}% in the\n1980s, {sh['global'][3]['s4']:.0f}% in the 2010s.",
         fontproperties=SERP, fontsize=14, color=FG, va="top", linespacing=1.25)
fig.text(.035, .04, "maps.tristanhotham.com/hurricane-tracks", fontsize=10, color=HOT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG); plt.close(fig)
from PIL import Image
print("header", Image.open(os.path.join(ROOT, "header.png")).size, sorted(os.listdir(BL)), sorted(f for f in os.listdir(PA) if f.endswith(".png")))
