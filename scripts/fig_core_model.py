"""Article figures for the core model (second run, 2026-10-21), fig_export.py style (light/dark/phone, webp).
A) core vs GPU fan rpm at case 1500 rpm, points + model per power limit; B) core vs case fan rpm at GPU fans 40 %.
Model (whole grid, final.csv without unsettled points): T = Tin + θ0 + P·[r∞ + k·(N/1000)^(−m)·(C/1500)^(−q)].
Usage: fig_core_model.py final.csv outdir"""
import csv, sys, json
from pathlib import Path
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

src, out = Path(sys.argv[1]), Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
allr = list(csv.DictReader(open(src)))
rs = [r for r in allr if "UNSETTLED" not in r["source"]]
f = lambda k, R=rs: np.array([float(r[k]) for r in R])
N, P, T, C = f("cardA_fan_rpm"), f("power_w_sum"), f("cardA_core_c"), f("case_rpm")
Tin = np.array([float(r["intake_c"] or 19.1) for r in rs]); y = T - Tin
CT = np.array([r["case_rpm_target"] for r in rs]); G = np.array([int(r["gpu_pct"]) for r in rs]); PLs = np.array([int(r["pl_pct"]) for r in rs])

def D(n_, c_, p_, m_, q_): return np.column_stack([np.ones_like(p_), p_, p_ * (n_ / 1000) ** (-m_) * (c_ / 1500) ** (-q_)])
def fit(mask, qgrid):
    best = None
    for m_ in np.arange(0.5, 3.001, 0.02):
        for q_ in qgrid:
            X = D(N[mask], C[mask], P[mask], m_, q_); c, *_ = np.linalg.lstsq(X, y[mask], rcond=None)
            e = np.sum((y[mask] - X @ c) ** 2)
            if best is None or e < best[0]: best = (e, c, m_, q_)
    _, c, m_, q_ = best; res = y[mask] - D(N[mask], C[mask], P[mask], m_, q_) @ c
    return dict(th0=c[0], rinf=c[1], k=c[2], m=m_, q=q_, n=int(mask.sum()), rmse=float(np.sqrt(np.mean(res ** 2))),
                r2=float(1 - np.sum(res ** 2) / np.sum((T[mask] - T[mask].mean()) ** 2)), maxres=float(np.abs(res).max()))
full = fit(np.ones(len(T), bool), np.arange(0, 1.001, 0.02))
c15 = fit(CT == "1500", [0.0])
print("full", {k: round(v, 4) for k, v in full.items()}); print("1500", {k: round(v, 4) for k, v in c15.items()})
def pred(p, n_, c_, pw, tin):
    n_, c_, pw = np.broadcast_arrays(*(np.atleast_1d(np.asarray(v, float)) for v in (n_, c_, pw)))
    return tin + D(n_, c_, pw, p["m"], p["q"]) @ np.array([p["th0"], p["rinf"], p["k"]])
R15 = lambda n_: c15["rinf"] + c15["k"] * (n_ / 1000) ** (-c15["m"])
gp = sorted({int(r["gpu_pct"]) for r in allr}); grpm = [np.mean([float(r["cardA_fan_rpm"]) for r in allr if int(r["gpu_pct"]) == g]) for g in gp]
print("°C per 100 W @1500:", {g: round(R15(n) * 100, 1) for g, n in zip(gp, grpm)})
# log-linear alternative at case 1500
m15 = CT == "1500"; X = np.column_stack([np.ones(m15.sum()), P[m15], np.log(N[m15]), P[m15] * np.log(N[m15])]); b, *_ = np.linalg.lstsq(X, T[m15], rcond=None)
print("loglin RMSE", round(float(np.sqrt(np.mean((T[m15] - X @ b) ** 2))), 2))
json.dump(dict(full=full, case1500=c15), open(out / "core-model.json", "w"), indent=1)
tin0 = float(np.mean(Tin))
# case % ↔ rpm from the controller output
cpm = {}
for r in allr: cpm.setdefault(r["case_rpm_target"], []).append((float(r["case_rpm"]), float(r["case_out_pct"])))
cr = sorted((np.mean([a for a, _ in v]), np.mean([b for _, b in v])) for v in cpm.values()); CR, CP = [a for a, _ in cr], [b for _, b in cr]
print("case map", [(round(a), round(b, 1)) for a, b in cr])

THEMES = {"light": dict(bg="#ffffff", fg="#1d1d1f", grid="#d9d9de", dim="#86868b"), "dark": dict(bg="#141414", fg="#f5f5f7", grid="#3a3a3c", dim="#98989d")}
PL = {100: ("#ff453a", 575), 90: ("#ff9f0a", 518), 80: ("#30d158", 460), 70: ("#0a84ff", 402)}
def lin(xs, ys):
    k_ = (ys[-1] - ys[0]) / (xs[-1] - xs[0])
    return lambda v: np.interp(v, xs, ys) + (np.asarray(v) - np.clip(v, xs[0], xs[-1])) * k_
def style(ax, th, fs):
    ax.set_facecolor(th["bg"])
    for s_ in ax.spines.values(): s_.set_visible(False)
    ax.tick_params(colors=th["fg"], labelsize=fs - 1, length=0); ax.xaxis.label.set_color(th["fg"]); ax.yaxis.label.set_color(th["fg"])
    ax.grid(color=th["grid"], lw=0.6); ax.set_axisbelow(True)
def save(fig, th, name):
    fig.savefig(out / f"{name}.png", dpi=200, facecolor=th["bg"]); plt.close(fig)
    im = Image.open(out / f"{name}.png").convert("RGB"); im.save(out / f"{name}.webp", "WEBP", quality=86, method=6); print(name, im.size)

def figure(which, theme, phone):
    th = THEMES[theme]; fs = 13 if phone else 12
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Arial", "DejaVu Sans"], "font.size": fs})
    fig, ax = plt.subplots(figsize=(5, 6.2) if phone else (8, 5.4)); fig.patch.set_facecolor(th["bg"]); style(ax, th, fs)
    for pl, (col, w) in PL.items():
        if which == "a":
            k_ = (CT == "1500") & (PLs == pl); xx = np.linspace(1250, 3080, 200)
            ax.plot(xx, pred(c15, xx, 1500, w, tin0), c=col, lw=1.8, zorder=3, label=f"{pl} % ({w} W)")
            ax.scatter(N[k_], T[k_], s=30 if phone else 34, color=col, edgecolors=th["bg"], linewidths=0.8, zorder=4)
        else:
            k_ = (G == 40) & (PLs == pl); xx = np.linspace(950, 3000, 200)
            ax.plot(xx, pred(full, grpm[0], xx, w, tin0), c=col, lw=1.8, zorder=3, label=f"{pl} % ({w} W)")
            ax.scatter(C[k_], T[k_], s=30 if phone else 34, color=col, edgecolors=th["bg"], linewidths=0.8, zorder=4)
    if which == "a":
        ax.set_xlabel("GPU fans (rpm)"); ax.set_xlim(1200, 3120)
        top = ax.secondary_xaxis("top", functions=(lin(grpm, gp), lin(gp, grpm))); top.set_xticks(range(40, 101, 10)); top.set_xlabel("GPU fans (%)", color=th["fg"])
        note = "case fans 1500 rpm"
    else:
        ax.set_xlabel("Case fans (rpm)"); ax.set_xlim(900, 3050); ax.set_xticks([1000, 1500, 2000, 2500, 2920])
        top = ax.secondary_xaxis("top", functions=(lin(CR, CP), lin(CP, CR))); top.set_xticks([round(v) for v in CP]); top.set_xlabel("Case fans (%)", color=th["fg"])
        note = f"GPU fans 40 % ({round(grpm[0], -1):.0f} rpm)"
    top.tick_params(colors=th["fg"], labelsize=fs - 2, length=0)
    for sp in top.spines.values(): sp.set_visible(False)
    ax.set_ylabel("Core (°C)")
    ax.text(0.98, 0.96, note, transform=ax.transAxes, va="top", ha="right", color=th["fg"], fontsize=fs - 1, bbox=dict(boxstyle="round,pad=0.3", fc=th["bg"], ec=th["grid"]))
    h, l = ax.get_legend_handles_labels()
    h += [plt.Line2D([], [], ls="none", marker="o", color=th["dim"])]; l += ["measured"]
    h += [plt.Line2D([], [], c=th["dim"], lw=1.8)]; l += ["model, equation (9)"]
    ax.legend(h, l, title="Power limit", title_fontsize=fs - 2, loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=2 if phone else 3, fontsize=fs - 2, frameon=False, labelcolor=th["fg"]).get_title().set_color(th["fg"])
    fig.tight_layout()
    save(fig, th, f"gpu-map-2026-10-21-run2-core-model-{'case1500' if which == 'a' else 'gpu40'}{'-phone' if phone else ''}-{theme}")
for w in "ab":
    for t in THEMES:
        for ph in (False, True): figure(w, t, ph)
