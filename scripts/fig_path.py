"""Path map for steady3 (plan/steady3_path.csv): one panel per GPU fan speed, rows = power limit, columns = case fan speed,
cells coloured by the predicted settled core (model 11), arrows along the measurement order, start and end marked.
House style, light/dark/phone. Usage: fig_path.py outdir"""
import sys
from pathlib import Path
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from PIL import Image
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
d = pd.read_csv(Path(__file__).resolve().parent / "plan/steady3_path.csv")
CASE = sorted(d["case"].unique()); PLS = [100, 90, 80, 70]; CARD = sorted(d.card.unique())
RPM = {40: 1312, 50: 1595, 60: 1879, 70: 2162, 80: 2446, 90: 2729, 100: 3013}
CR, CP = [1007.0, 1500.0, 1999.0, 2923.0], [26.8, 43.9, 62.4, 100.0]
def c2p(r):
    k = (CP[-1] - CP[0]) / (CR[-1] - CR[0]); return float(np.interp(r, CR, CP) + (r - np.clip(r, CR[0], CR[-1])) * k)
TH = {"light": dict(bg="#ffffff", fg="#1d1d1f", grid="#d9d9de", dim="#86868b"), "dark": dict(bg="#141414", fg="#f5f5f7", grid="#3a3a3c", dim="#98989d")}
norm = Normalize(d.core.min(), d.core.max()); cmap = plt.get_cmap("inferno")
def fig(theme, phone):
    th = TH[theme]; fs = 13 if phone else 10
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Arial", "DejaVu Sans"], "font.size": fs})
    if phone: F, axs = plt.subplots(7, 1, figsize=(5, 17.5))
    else: F, axs = plt.subplots(2, 4, figsize=(15, 6.6))
    F.patch.set_facecolor(th["bg"]); axs = np.ravel(axs)
    for ax, g in zip(axs, CARD):
        ax.set_facecolor(th["bg"]); b = d[d.card == g].sort_values("n")
        M = np.full((4, len(CASE)), np.nan)
        for _, r in b.iterrows(): M[PLS.index(r.pl), CASE.index(r["case"])] = r.core
        ax.imshow(M, cmap=cmap, norm=norm, aspect="auto")
        for i in range(4):
            for j in range(len(CASE)):
                v = M[i, j]; ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=fs - 3, color="#000000" if norm(v) > 0.6 else "#ffffff")
        x = [CASE.index(c) for c in b["case"]]; y = [PLS.index(p) for p in b.pl]
        for k in range(len(x) - 1):
            ax.annotate("", xy=(x[k + 1], y[k + 1]), xytext=(x[k], y[k]), arrowprops=dict(arrowstyle="-|>", color="#64d2ff", lw=1.3, shrinkA=7, shrinkB=7, mutation_scale=9))
        first, last = b.iloc[0], b.iloc[-1]
        ax.scatter([CASE.index(first["case"])], [PLS.index(first.pl)], s=180, facecolors="none", edgecolors="#30d158", linewidths=2.2, zorder=5)
        ax.scatter([CASE.index(last["case"])], [PLS.index(last.pl)], s=180, marker="s", facecolors="none", edgecolors="#ff453a", linewidths=2.2, zorder=5)
        ax.set_xticks(range(len(CASE))); ax.set_xticklabels([(f"{c}\n{c2p(c):.0f} %" if c < 2900 else "full\n100 %") for c in CASE], fontsize=fs - 3, color=th["fg"])
        ax.set_yticks(range(4)); ax.set_yticklabels([f"{p} %" for p in PLS], fontsize=fs - 2, color=th["fg"])
        ax.tick_params(length=0)
        for sp in ax.spines.values(): sp.set_visible(False)
        h = b.wait_s.sum() / 3600
        ax.set_title(f"GPU fans {g} % ({RPM[g]} rpm): {len(b)} points, {h:.1f} h", loc="left", fontsize=fs - 1, color=th["fg"])
        ax.set_xlabel("Case fans (rpm, %)", fontsize=fs - 2, color=th["fg"]); ax.set_ylabel("Power limit", fontsize=fs - 2, color=th["fg"])
    if not phone:
        lax = axs[7]; lax.axis("off"); lax.set_facecolor(th["bg"])
        sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap); cb = F.colorbar(sm, ax=lax, orientation="horizontal", fraction=0.18, pad=0.0, aspect=18)
        cb.set_label("Predicted settled core (°C)", color=th["fg"]); cb.ax.tick_params(colors=th["fg"], labelsize=fs - 2, length=0); cb.outline.set_visible(False)
        lax.scatter([0.12], [0.75], s=180, facecolors="none", edgecolors="#30d158", linewidths=2.2, transform=lax.transAxes); lax.text(0.2, 0.75, "first point of the block", transform=lax.transAxes, va="center", color=th["fg"], fontsize=fs - 1)
        lax.scatter([0.12], [0.55], s=180, marker="s", facecolors="none", edgecolors="#ff453a", linewidths=2.2, transform=lax.transAxes); lax.text(0.2, 0.55, "last point; the next block starts here", transform=lax.transAxes, va="center", color=th["fg"], fontsize=fs - 1)
        F.tight_layout()
    else:
        F.tight_layout(rect=(0, 0.06, 1, 1))
        cax = F.add_axes([0.15, 0.025, 0.7, 0.008]); sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap); cb = F.colorbar(sm, cax=cax, orientation="horizontal")
        cb.set_label("Predicted settled core (°C); circle = first, square = last point of a block", color=th["fg"], fontsize=fs - 3); cb.ax.tick_params(colors=th["fg"], labelsize=fs - 3, length=0); cb.outline.set_visible(False)
    name = f"gpu-map-steady3-path{'-phone' if phone else ''}-{theme}"
    F.savefig(out / f"{name}.png", dpi=200 if not phone else 200, facecolor=th["bg"]); plt.close(F)
    im = Image.open(out / f"{name}.png").convert("RGB"); im.save(out / f"{name}.webp", "WEBP", quality=86, method=6); print(name, im.size)
for t in TH:
    for ph in (False, True): fig(t, ph)
