"""Static core model (second run, 2026-10-21) — fit, bootstrap intervals and article figures (fig_export.py style).
Data: final.csv core_c_max (the published final table). Fitted on the 88 same-day points: the two unsettled 575 W
points and the 22 575 W rows taken from the first-run night grid are left out (they were measured at other case speeds).
Model (9): T = Tin + θ0 + P·[r∞ + k·(N/1000)^(−m)·(C/1500)^(−q)].
A) core vs GPU fan rpm at case 1500 rpm; B) core vs case fan rpm at GPU fans 40 %. Also the °C per 100 W table from (9) and (10).
Usage: fig_core_model.py final.csv outdir"""
import csv, sys, json, os
from pathlib import Path
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

src, out = Path(sys.argv[1]), Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
allr = list(csv.DictReader(open(src)))
uns = lambda r: "UNSETTLED" in r["source"]; night = lambda r: r["source"].startswith("night")
f = lambda k, R: np.array([float(r[k]) for r in R])
def arrays(R, key="core_c_max"):
    return dict(N=f("cardA_fan_rpm", R), P=f("power_w_sum", R), C=f("case_rpm", R), T=f(key, R), Tin=f("intake_c", R),
                CT=np.array([r["case_rpm_target"] for r in R]), G=np.array([int(r["gpu_pct"]) for r in R]), PL=np.array([int(r["pl_pct"]) for r in R]))
day = [r for r in allr if not uns(r) and not night(r)]; A = arrays(day)

def X(n_, c_, p_, m_, q_): return np.column_stack([np.ones_like(p_), p_, p_ * (n_ / 1000) ** (-m_) * (c_ / 1500) ** (-q_)])
MG, QG = np.arange(0.8, 2.6001, 0.02), np.arange(0.0, 0.8001, 0.02)
def fit(a, idx=None, qg=QG):
    idx = np.arange(len(a["T"])) if idx is None else idx
    N, C, P, y = a["N"][idx], a["C"][idx], a["P"][idx], (a["T"] - a["Tin"])[idx]
    best = None
    for m_ in MG:
        for q_ in qg:
            Xm = X(N, C, P, m_, q_); c, *_ = np.linalg.lstsq(Xm, y, rcond=None); e = np.sum((y - Xm @ c) ** 2)
            if best is None or e < best[0]: best = (e, c, m_, q_)
    _, c, m_, q_ = best; r = y - X(N, C, P, m_, q_) @ c; T = a["T"][idx]
    return dict(th0=float(c[0]), rinf=float(c[1]), k=float(c[2]), m=float(m_), q=float(q_), n=int(len(idx)), rmse=float(np.sqrt(np.mean(r ** 2))),
                r2=float(1 - np.sum(r ** 2) / np.sum((T - T.mean()) ** 2)), maxres=float(np.abs(r).max()))
def pred(p, n_, c_, pw, tin):
    n_, c_, pw = np.broadcast_arrays(*(np.atleast_1d(np.asarray(v, float)) for v in (n_, c_, pw)))
    return tin + X(n_, c_, pw, p["m"], p["q"]) @ np.array([p["th0"], p["rinf"], p["k"]])

full = fit(A)
rng = np.random.default_rng(1); boots = [fit(A, rng.integers(0, len(A["T"]), len(A["T"]))) for _ in range(300)]
ci = {k: [float(np.percentile([b[k] for b in boots], 2.5)), float(np.percentile([b[k] for b in boots], 97.5))] for k in ("th0", "rinf", "k", "m", "q")}
sum575 = [b["th0"] + 575 * b["rinf"] for b in boots]
m15 = A["CT"] == "1500"; c15 = fit(A, np.where(m15)[0], [0.0])
Xl = np.column_stack([np.ones(m15.sum()), A["P"][m15], np.log(A["N"][m15]), A["P"][m15] * np.log(A["N"][m15])]); b, *_ = np.linalg.lstsq(Xl, A["T"][m15], rcond=None)
loglin = float(np.sqrt(np.mean((A["T"][m15] - Xl @ b) ** 2)))
# comparison fits
A110 = arrays([r for r in allr if not uns(r)]); A110raw = arrays([r for r in allr if not uns(r)], "cardA_core_c")
f110, f110raw = fit(A110), fit(A110raw)
# residuals at GPU 40 %, 575 W
res40 = {r["case_rpm_target"]: float(float(r["core_c_max"]) - pred(full, float(r["cardA_fan_rpm"]), float(r["case_rpm"]), float(r["power_w_sum"]), float(r["intake_c"]))[0])
         for r in day if r["gpu_pct"] == "40" and r["pl_pct"] == "100"}
gp = sorted({int(r["gpu_pct"]) for r in allr}); grpm = [float(np.mean([float(r["cardA_fan_rpm"]) for r in allr if int(r["gpu_pct"]) == g])) for g in gp]
# °C per 100 W at case 1500: static (9) and dynamic (10)
J = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results-2026-10-21", "dyn-model.json")))["M2-pow"]["params"]
Rd = lambda n_, c_=1500: J["Rjs"] + J["ra"] + J["k"] * (np.sqrt(n_ ** 2 + 300 ** 2) / 1000) ** -J["m"] * (c_ / 1500) ** -J["q"]
Rs = lambda n_, c_=1500: full["rinf"] + full["k"] * (n_ / 1000) ** -full["m"] * (c_ / 1500) ** -full["q"]
per100 = {g: dict(rpm=round(n, -1), static=round(float(Rs(n)) * 100, 1), dynamic=round(float(Rd(n)) * 100, 1)) for g, n in zip(gp, grpm)}
summary = dict(full=full, ci95=ci, th0_plus_575rinf_ci=[float(np.percentile(sum575, 2.5)), float(np.percentile(sum575, 97.5))], case1500=c15, loglin_case1500_rmse=loglin,
               all110_final=f110, all110_raw60s=f110raw, res_gpu40_575=res40, per100W_case1500=per100)
json.dump(summary, open(out / "core-model.json", "w"), indent=1)
print(json.dumps(summary, indent=1))

cpm = {}
for r in allr: cpm.setdefault(r["case_rpm_target"], []).append((float(r["case_rpm"]), float(r["case_out_pct"])))
cr = sorted((np.mean([a for a, _ in v]), np.mean([b for _, b in v])) for v in cpm.values()); CR, CP = [a for a, _ in cr], [b for _, b in cr]
THEMES = {"light": dict(bg="#ffffff", fg="#1d1d1f", grid="#d9d9de", dim="#86868b"), "dark": dict(bg="#141414", fg="#f5f5f7", grid="#3a3a3c", dim="#98989d")}
PLC = {100: ("#ff453a", 575), 90: ("#ff9f0a", 518), 80: ("#30d158", 460), 70: ("#0a84ff", 402)}
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
NI = arrays([r for r in allr if night(r)]); tin0 = float(np.mean(A["Tin"]))

def figure(which, theme, phone):
    th = THEMES[theme]; fs = 13 if phone else 12
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Arial", "DejaVu Sans"], "font.size": fs})
    fig, ax = plt.subplots(figsize=(5, 6.4) if phone else (8, 5.6)); fig.patch.set_facecolor(th["bg"]); style(ax, th, fs)
    for pl, (col, w) in PLC.items():
        if which == "a":
            k_ = (A["CT"] == "1500") & (A["PL"] == pl); xx = np.linspace(1250, 3080, 200)
            ax.plot(xx, pred(full, xx, 1500, w, tin0), c=col, lw=1.8, zorder=3, label=f"{pl} % ({w} W)")
            ax.scatter(A["N"][k_], A["T"][k_], s=30 if phone else 34, color=col, edgecolors=th["bg"], linewidths=0.8, zorder=4)
            kn = (NI["CT"] == "1500") & (NI["PL"] == pl)
            if kn.any(): ax.scatter(NI["N"][kn], NI["T"][kn], s=34 if phone else 38, facecolors=th["bg"], edgecolors=col, linewidths=1.3, zorder=5)
        else:
            k_ = (A["G"] == 40) & (A["PL"] == pl); xx = np.linspace(950, 3000, 200)
            ax.plot(xx, pred(full, grpm[0], xx, w, tin0), c=col, lw=1.8, zorder=3, label=f"{pl} % ({w} W)")
            ax.scatter(A["C"][k_], A["T"][k_], s=30 if phone else 34, color=col, edgecolors=th["bg"], linewidths=0.8, zorder=4)
    if which == "a":
        ax.set_xlabel("GPU fans (rpm)"); ax.set_xlim(1200, 3120)
        top = ax.secondary_xaxis("top", functions=(lin(grpm, gp), lin(gp, grpm))); top.set_xticks(range(40, 101, 10)); top.set_xlabel("GPU fans (%)", color=th["fg"])
        note = f"case fans 1500 rpm ({CP[1]:.0f} %)"
    else:
        ax.set_xlabel("Case fans (rpm)"); ax.set_xlim(900, 3050); ax.set_xticks([1000, 1500, 2000, 2500, 2920])
        top = ax.secondary_xaxis("top", functions=(lin(CR, CP), lin(CP, CR))); top.set_xticks([round(v) for v in CP]); top.set_xlabel("Case fans (%)", color=th["fg"])
        note = f"GPU fans 40 % ({round(grpm[0], -1):.0f} rpm)"
    top.tick_params(colors=th["fg"], labelsize=fs - 2, length=0)
    for sp in top.spines.values(): sp.set_visible(False)
    ax.set_ylabel("Core (°C)")
    ax.text(0.98, 0.96, note, transform=ax.transAxes, va="top", ha="right", color=th["fg"], fontsize=fs - 1, bbox=dict(boxstyle="round,pad=0.3", fc=th["bg"], ec=th["grid"]))
    h, l = ax.get_legend_handles_labels()
    h += [plt.Line2D([], [], ls="none", marker="o", color=th["dim"])]; l += ["measured, fitted"]
    if which == "a": h += [plt.Line2D([], [], ls="none", marker="o", mfc=th["bg"], mec=th["dim"])]; l += ["first-run value, not fitted"]
    h += [plt.Line2D([], [], c=th["dim"], lw=1.8)]; l += ["model, equation (9)"]
    ax.legend(h, l, title="Power limit", title_fontsize=fs - 2, loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=2 if phone else 3, fontsize=fs - 2, frameon=False, labelcolor=th["fg"]).get_title().set_color(th["fg"])
    fig.tight_layout()
    save(fig, th, f"gpu-map-2026-10-21-run2-core-model-{'case1500' if which == 'a' else 'gpu40'}{'-phone' if phone else ''}-{theme}")
for w in "ab":
    for t in THEMES:
        for ph in (False, True): figure(w, t, ph)
