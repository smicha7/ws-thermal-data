"""Figures 9 and 10 of the article: settled points with the settled-point model (11), one fan axis each, with a residual panel.
A) case fans 1500 rpm: core vs GPU fans; B) GPU fans 40 %: core vs case fans. Points are adjusted to the reference session and the
mean intake air exactly as the model does (core − (Tin − Tmean) − θ_session), so each drawn point sits at fitted + residual.
Writes residual statistics of the drawn points to settled-axes.json. Usage: fig_settled_axes.py outdir"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
from PIL import Image
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
R = Path(__file__).resolve().parent / "results-2026-10-22"
D = pd.read_csv(R / "steady-residuals.csv"); J = json.load(open(R / "steady-stats.json"))
assert "cond" in J["choice"]
P_ = {p["param"]: p["est"] for p in J["params"]}
th0, rinf, gN, m, gC, s = (P_[k] for k in ("θ0", "r∞", "gN", "m", "gC", "s")); rinf /= 1000
TIN = float(D.Tin.mean()); sess = {g: P_.get(f"θ[{g}]", 0.0) for g in D.grp.unique()}
Rf = lambda N, C: rinf + 1.0 / (gN * (np.asarray(N) / 1000) ** m + gC * (np.asarray(C) / 1500) ** s)
curve = lambda N, C, P: TIN + th0 + P * Rf(N, C)
D["adj"] = D.core_settled - (D.Tin - TIN) - D.grp.map(sess)
assert np.allclose(D.adj, curve(D.N, D.C, D.P) + D.e, atol=1e-6)          # drawn point = model + residual, by construction
g = D.groupby("gpu_pct").N.mean(); GP, GR = list(g.index.astype(float)), list(g.values)
CR, CP = [1007.0, 1500.0, 1999.0, 2923.0], [26.8, 43.9, 62.4, 100.0]
def lin(xs, ys):
    k_ = (ys[-1] - ys[0]) / (xs[-1] - xs[0])
    return lambda v: np.interp(v, xs, ys) + (np.asarray(v, float) - np.clip(v, xs[0], xs[-1])) * k_
g2r, r2g, c2p, p2c = lin(GP, GR), lin(GR, GP), lin(CR, CP), lin(CP, CR)
SEL = {"case1500": (np.abs(D.C - 1500) < 60).to_numpy(), "gpu40": (D.gpu_pct == 40).to_numpy()}
def rstats(sel, axis):
    d = D[sel]; e = d.e.to_numpy(); n = len(e)
    t = stats.ttest_1samp(e, 0.0)
    sw = stats.shapiro(e) if n >= 3 else None
    num = den = 0.0
    for _, q in d.groupby(["grp", "pl_pct"] + (["case_target"] if axis == "N" else ["gpu_pct"])):
        q = q.sort_values(axis); ee = q.e.to_numpy()
        if len(ee) > 1: num += float(np.sum(np.diff(ee) ** 2))
    den = float(np.sum(e ** 2))
    return dict(n=n, mean=float(e.mean()), rmse=float(np.sqrt(np.mean(e ** 2))), t_p=float(t.pvalue), shapiro_p=float(sw.pvalue) if sw else None, dw_along=num / den if den else None,
                max_abs=float(np.abs(e).max()))
ST = {"case1500": rstats(SEL["case1500"], "N"), "gpu40": rstats(SEL["gpu40"], "C")}
json.dump(dict(stats=ST, n_total=int(len(D)), rmse_total=float(np.sqrt((D.e ** 2).mean()))), open(out / "settled-axes.json", "w"), indent=1)
print(json.dumps(ST, indent=1))
THEMES = {"light": dict(bg="#ffffff", fg="#1d1d1f", grid="#d9d9de", dim="#86868b"), "dark": dict(bg="#141414", fg="#f5f5f7", grid="#3a3a3c", dim="#98989d")}
PLC = {100: ("#ff453a", 575), 90: ("#ff9f0a", 518), 80: ("#30d158", 460), 70: ("#0a84ff", 402)}
MK = {"val1": "o", "val2": "s", "afternoon": "D", "night": "v", "steady2": "^", "grid1c": "D", "grid1d": "D"}
SN = {"val1": "val1, 21 Oct", "val2": "val2, 21–22 Oct", "afternoon": "second run, 21 Oct", "night": "first-run night", "steady2": "steady2, 22 Oct"}
def style(ax, th, fs):
    ax.set_facecolor(th["bg"])
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.tick_params(colors=th["fg"], labelsize=fs - 2, length=0); ax.xaxis.label.set_color(th["fg"]); ax.yaxis.label.set_color(th["fg"])
    ax.grid(color=th["grid"], lw=0.6); ax.set_axisbelow(True)
def fig(which, theme, phone):
    th = THEMES[theme]; fs = 14 if phone else 12
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Arial", "DejaVu Sans"], "font.size": fs})
    F, (A, RA) = plt.subplots(2, 1, figsize=(5, 7.4) if phone else (8, 6.6), sharex=True, gridspec_kw=dict(height_ratios=[3, 1], hspace=0.08))
    F.patch.set_facecolor(th["bg"]); style(A, th, fs); style(RA, th, fs)
    sel = SEL[which]; xcol = "N" if which == "case1500" else "C"
    xs = np.linspace(GR[0] - 40, 3060, 200) if which == "case1500" else np.linspace(950, 2960, 200)
    for pl, (col, w) in PLC.items():
        A.plot(xs, curve(xs, 1500, w) if which == "case1500" else curve(g2r(40), xs, w), color=col, lw=1.8, zorder=2, label=f"{pl} % ({w} W)")
        for grp in D.grp.unique():
            k = sel & (D.pl_pct == pl).to_numpy() & (D.grp == grp).to_numpy()
            if k.any():
                A.scatter(D[xcol][k], D.adj[k], marker=MK.get(grp, "o"), s=40, color=col, edgecolors=th["bg"], linewidths=0.8, zorder=4)
                RA.scatter(D[xcol][k], D.e[k], marker=MK.get(grp, "o"), s=32, color=col, edgecolors=th["bg"], linewidths=0.6, zorder=4)
    lim = max(1.0, float(np.ceil(np.abs(D.e[sel]).max() * 2) / 2)); RA.axhline(0, color=th["dim"], lw=0.8); RA.set_ylim(-lim, lim)
    RA.set_ylabel("Residual\n(°C)", fontsize=fs - 2); A.set_ylabel("Core (°C)")
    if which == "case1500":
        RA.set_xlabel("GPU fans (rpm)"); A.set_xlim(GR[0] - 60, 3080); top = A.secondary_xaxis("top", functions=(r2g, g2r)); top.set_xticks(range(40, 101, 10)); top.set_xlabel("GPU fans (%)", color=th["fg"])
        note = "case fans 1500 rpm (44 %)"
    else:
        RA.set_xlabel("Case fans (rpm)"); A.set_xlim(900, 3000); RA.set_xticks([1000, 1500, 2000, 2500, 2920]); top = A.secondary_xaxis("top", functions=(c2p, p2c)); top.set_xticks([27, 44, 62, 100]); top.set_xlabel("Case fans (%)", color=th["fg"])
        note = f"GPU fans 40 % ({round(float(g2r(40)), -1):.0f} rpm)"
    top.tick_params(colors=th["fg"], labelsize=fs - 2, length=0)
    for sp in top.spines.values(): sp.set_visible(False)
    A.text(0.98, 0.96, note, transform=A.transAxes, va="top", ha="right", color=th["fg"], fontsize=fs - 1, bbox=dict(boxstyle="round,pad=0.3", fc=th["bg"], ec=th["grid"]))
    h, l = A.get_legend_handles_labels()
    for grp in [x for x in SN if x in set(D.grp[sel])]:
        h.append(plt.Line2D([], [], ls="none", marker=MK[grp], color=th["dim"])); l.append(SN[grp])
    F.legend(h, l, title="Power limit, session", title_fontsize=fs - 3, loc="lower center", ncol=2 if phone else 3, fontsize=fs - 3, frameon=False, labelcolor=th["fg"]).get_title().set_color(th["fg"])
    F.subplots_adjust(left=0.17 if phone else 0.1, right=0.96, top=0.9 if phone else 0.9, bottom=0.3 if phone else 0.25)
    name = f"gpu-map-settled-{which}{'-phone' if phone else ''}-{theme}"
    F.savefig(out / f"{name}.png", dpi=200, facecolor=th["bg"]); plt.close(F)
    im = Image.open(out / f"{name}.png").convert("RGB"); im.save(out / f"{name}.webp", "WEBP", quality=86, method=6); print(name, im.size)
for w in ("case1500", "gpu40"):
    for t in THEMES:
        for ph in (False, True): fig(w, t, ph)
