"""v3d (power limit × fans) from log.txt + fits.csv when points.csv is missing: °C vs power limit at fixed fans. Usage: <run dir> <out dir>"""
import csv, re, sys, json
from pathlib import Path
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
run, out = Path(sys.argv[1]), Path(sys.argv[2])
rx = re.compile(r"punkt f_g (\d+) % · f_c (\d+) % · (\d+) W \(([\d.]+) %\): (60 s|ustalony|nieustalony|ZA GORĄCO) · rdzeń ([\d.]+) · pamięć ([\d.]+) · hot spot ([\d.]+) · ([\d.]+) W")
rows = []
lines = open(run / "log.txt", encoding="utf-8").read().splitlines()
fits = list(csv.DictReader(open(run / "fits.csv")))
for l in lines:
    m = rx.search(l)
    if m: rows.append(dict(fg=int(m[1]), fc=int(m[2]), pl=int(m[3]), plp=float(m[4]), kind=m[5], core=float(m[6]), mem=float(m[7]), hot=float(m[8]), w=float(m[9])))
# T∞ (hot spot) from fits where well determined, matched in order
for r, f in zip(rows, fits):
    def g(k):
        try: return float(f[k])
        except: return np.nan
    ok = np.isfinite(g("hot_tinf_ci95")) and g("hot_tinf_ci95") <= 2 and abs(g("hot_tinf") - g("hot_mean60")) <= 8
    r["hot_est"] = g("hot_tinf") if ok else r["hot"]
grid_fg = {30, 50, 70, 100}
pls = sorted({r["pl"] for r in rows}, reverse=True)
cases = sorted({r["fc"] for r in rows if r["fc"] in (100,) or True}, reverse=True)
tab = {}
for r in rows:
    if r["fg"] in grid_fg and r["kind"] != "ZA GORĄCO": tab[(r["pl"], r["fg"], r["fc"])] = r
summary = {"points": len(rows), "power_by_pl": {str(p): float(np.median([r["w"] for r in rows if r["pl"] == p])) for p in pls}}
fig, axs = plt.subplots(1, 3, figsize=(15, 4.6), sharey=True)
fcs = [c for c in (100, 50, 15) if any(k[2] == c for k in tab)]   # tylko poziomy siatki (mostki obudowy pominięte)
for ax, fc in zip(axs, fcs):
    for fg, mk in ((100, "o"), (70, "s"), (50, "^"), (30, "v")):
        xs = [p for p in pls if (p, fg, fc) in tab]
        if xs: ax.plot([tab[(p, fg, fc)]["w"] for p in xs], [tab[(p, fg, fc)]["hot_est"] for p in xs], "-" + mk, label=f"GPU fans {fg} %")
    ax.set_title(f"case fans {fc} %"); ax.set_xlabel("board power (W) = power limit in force"); ax.invert_xaxis(); ax.grid(alpha=0.3)
axs[0].set_ylabel("hot spot °C (steady estimate)"); axs[0].legend(fontsize=8)
fig.suptitle("Hot spot vs power limit at fixed fans (575 / 500 / 425 W; '350 W' clamped by the card to 400 W)")
fig.tight_layout(); fig.savefig(out / "v3-hotspot-vs-pl.png", dpi=150); plt.close(fig)
# °C saved per 100 W at each fan setting (slope)
slopes = {}
for fc in fcs:
    for fg in (100, 70, 50, 30):
        xs = [p for p in pls if (p, fg, fc) in tab]
        if len(xs) >= 3:
            w = np.array([tab[(p, fg, fc)]["w"] for p in xs]); t = np.array([tab[(p, fg, fc)]["hot_est"] for p in xs])
            slopes[f"case {fc} / GPU {fg}"] = {"c_per_100w": float(np.polyfit(w, t, 1)[0] * 100), "hot_575": float(t[0]), "hot_min_pl": float(t[-1]), "w_min_pl": float(w[-1])}
summary["hot_vs_pl"] = slopes
json.dump(summary, open(out / "v3-summary.json", "w"), indent=1)
print(json.dumps(summary, indent=1))
