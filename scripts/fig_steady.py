"""Article figures for the steady-state statistics (house style of fig_export.py: light/dark/phone, webp).
Reads results-2026-10-22/steady-residuals{TAG}.csv and steady-stats{TAG}.json written by steady_stats.py.
A) "two ways": core vs GPU fans at case 1500 rpm, and core vs case fans at GPU 40 %, points adjusted to the reference
   session and mean intake, model lines per power limit, residuals below; % and rpm on every fan axis.
B) diagnostics: residuals vs fitted, along N inside series (Durbin–Watson), vs case fans, vs power, in time order, normal Q–Q.
Usage: fig_steady.py outdir [TAG]"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
from PIL import Image

out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True); TAG = sys.argv[2] if len(sys.argv) > 2 else ""
R = Path(__file__).resolve().parent / "results-2026-10-22"
D = pd.read_csv(R / f"steady-residuals{TAG}.csv"); J = json.load(open(R / f"steady-stats{TAG}.json"))
assert "cond" in J["choice"], J["choice"]                       # figure implements the parallel-conductance form
P_ = {p["param"]: p["est"] for p in J["params"]}
th0, rinf, gN, m, gC, s = (P_[k] for k in ("θ0", "r∞", "gN", "m", "gC", "s")); rinf /= 1000
REF = J["ref"]; TIN = float(D.Tin.mean())
sess = {g: P_.get(f"θ[{g}]", 0.0) for g in D.grp.unique()}
Rf = lambda N, C: rinf + 1.0 / (gN * (np.asarray(N) / 1000) ** m + gC * (np.asarray(C) / 1500) ** s)
curve = lambda N, C, P: TIN + th0 + P * Rf(N, C)
adj = D.core_settled - (D.Tin - TIN) - D.grp.map(sess)
e = D.e.to_numpy()
tests = {t["test"]: t for t in J["tests"]}
dw = tests["Durbin–Watson, along N within (case, PL) series"]
# % ↔ rpm maps: GPU fans from the data, case fans from the second-run levels
g = D.groupby("gpu_pct").N.mean(); GP, GR = list(g.index.astype(float)), list(g.values)
if len(GP) < 2: GP, GR = [40, 100], [1313, 3012]
CR, CP = [1007.0, 1500.0, 1999.0, 2923.0], [26.8, 43.9, 62.4, 100.0]
def lin(xs, ys):
    k_ = (ys[-1] - ys[0]) / (xs[-1] - xs[0])
    return lambda v: np.interp(v, xs, ys) + (np.asarray(v, float) - np.clip(v, xs[0], xs[-1])) * k_
g2r, r2g, c2p, p2c = lin(GP, GR), lin(GR, GP), lin(CR, CP), lin(CP, CR)
THEMES = {"light": dict(bg="#ffffff", fg="#1d1d1f", grid="#d9d9de", dim="#86868b"), "dark": dict(bg="#141414", fg="#f5f5f7", grid="#3a3a3c", dim="#98989d")}
PLC = {100: ("#ff453a", 575), 90: ("#ff9f0a", 518), 80: ("#30d158", 460), 70: ("#0a84ff", 402)}
SESS = {"val1": ("o", "val1, 21 Oct evening"), "val2": ("s", "val2, 21 Oct night"), "afternoon": ("D", "second run, 21 Oct afternoon"),
        "night": ("v", "first-run night grid"), "steady2": ("^", "steady2, 22 Oct")}
SC = {"val1": "#0a84ff", "val2": "#64d2ff", "afternoon": "#30d158", "night": "#ff453a", "steady2": "#bf5af2"}
def style(ax, th, fs):
    ax.set_facecolor(th["bg"])
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.tick_params(colors=th["fg"], labelsize=fs - 2, length=0); ax.xaxis.label.set_color(th["fg"]); ax.yaxis.label.set_color(th["fg"])
    ax.title.set_color(th["fg"]); ax.grid(color=th["grid"], lw=0.6); ax.set_axisbelow(True)
def sec(ax, th, fs, f, finv, ticks, label, where="top"):
    a = ax.secondary_xaxis(where, functions=(f, finv)); a.set_xticks(ticks); a.set_xlabel(label, color=th["fg"], fontsize=fs - 2)
    a.tick_params(colors=th["fg"], labelsize=fs - 3, length=0)
    for sp in a.spines.values(): sp.set_visible(False)
def save(fig, th, name):
    fig.savefig(out / f"{name}.png", dpi=200, facecolor=th["bg"]); plt.close(fig)
    im = Image.open(out / f"{name}.png").convert("RGB"); im.save(out / f"{name}.webp", "WEBP", quality=86, method=6); print(name, im.size)
def rc(fs): plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Arial", "DejaVu Sans"], "font.size": fs})

def two_ways(theme, phone):
    th = THEMES[theme]; fs = 15 if phone else 11; rc(fs)
    fig = plt.figure(figsize=(5, 15) if phone else (11, 7.4)); fig.patch.set_facecolor(th["bg"])
    if phone:
        from matplotlib.gridspec import GridSpecFromSubplotSpec
        og = fig.add_gridspec(2, 1, hspace=0.32)
        g1 = GridSpecFromSubplotSpec(2, 1, subplot_spec=og[0], height_ratios=[3, 1], hspace=0.08); g2 = GridSpecFromSubplotSpec(2, 1, subplot_spec=og[1], height_ratios=[3, 1], hspace=0.08)
        A, RA, B, RB = fig.add_subplot(g1[0]), fig.add_subplot(g1[1]), fig.add_subplot(g2[0]), fig.add_subplot(g2[1])
    else:
        gs = fig.add_gridspec(2, 2, height_ratios=[3, 1], hspace=0.12, wspace=0.22)
        A, RA, B, RB = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[1, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, 1])
    RA.sharex(A); RB.sharex(B)
    for a in (A, RA, B, RB): style(a, th, fs)
    ia = (np.abs(D.C - 1500) < 60).to_numpy(); ib = (D.gpu_pct == 40).to_numpy()
    gx, cx = np.linspace(GR[0] - 40, 3060, 200), np.linspace(950, 2960, 200)
    for pl, (col, w) in PLC.items():
        A.plot(gx, curve(gx, 1500, w), c=col, lw=1.8, zorder=2); B.plot(cx, curve(g2r(40), cx, w), c=col, lw=1.8, zorder=2, label=f"{pl} % ({w} W)")
        for grp in D.grp.unique():
            mk = SESS.get(grp, ("o", grp))[0]; k = (D.pl_pct == pl).to_numpy() & (D.grp == grp).to_numpy()
            for ax, rx, sel, x in ((A, RA, ia, D.N), (B, RB, ib, D.C)):
                kk = k & sel
                if kk.any():
                    ax.scatter(x[kk], adj[kk], marker=mk, s=40, color=col, edgecolors=th["bg"], linewidths=0.8, zorder=4)
                    rx.scatter(x[kk], e[kk], marker=mk, s=30, color=col, edgecolors=th["bg"], linewidths=0.6, zorder=4)
    lim = max(1.0, float(np.ceil(np.abs(e[ia | ib]).max() * 2) / 2))
    for r in (RA, RB): r.axhline(0, color=th["dim"], lw=0.8); r.set_ylim(-lim, lim); r.set_ylabel("Residual\n(°C)", fontsize=fs - 2)
    for a in (A, B): a.set_ylabel("Core (°C)"); a.tick_params(labelbottom=False)
    A.set_xlim(GR[0] - 60, 3080); B.set_xlim(900, 3000)
    RA.set_xlabel("GPU fans (rpm)"); RB.set_xlabel("Case fans (rpm)"); RB.set_xticks([1000, 1500, 2000, 2500, 2920])
    sec(A, th, fs, r2g, g2r, [40, 50, 60, 70, 80, 90, 100], "GPU fans (%)"); sec(B, th, fs, c2p, p2c, [27, 44, 62, 100], "Case fans (%)")
    for a, t in ((A, f"case fans 1500 rpm (44 %)"), (B, f"GPU fans 40 % ({round(float(g2r(40)), -1):.0f} rpm)")):
        a.text(0.98, 0.96, t, transform=a.transAxes, va="top", ha="right", color=th["fg"], fontsize=fs - 2, bbox=dict(boxstyle="round,pad=0.3", fc=th["bg"], ec=th["grid"]))
    h, l = B.get_legend_handles_labels()
    for grp in [x for x in SESS if x in set(D.grp[ia | ib])]:
        h.append(plt.Line2D([], [], ls="none", marker=SESS[grp][0], color=th["dim"])); l.append(SESS[grp][1])
    fig.legend(h, l, title="Power limit and session", title_fontsize=fs - 3, loc="lower center", ncol=2 if phone else 4, fontsize=fs - 3, frameon=False, labelcolor=th["fg"]).get_title().set_color(th["fg"])
    fig.subplots_adjust(left=0.17 if phone else 0.07, right=0.97, top=0.95 if phone else 0.9, bottom=0.17 if phone else 0.2)
    save(fig, th, f"gpu-map-steady-two-ways{TAG}{'-phone' if phone else ''}-{theme}")

def diagnostics(theme, phone):
    th = THEMES[theme]; fs = 15 if phone else 11; rc(fs)
    fig, axs = plt.subplots(6, 1, figsize=(5, 21)) if phone else plt.subplots(2, 3, figsize=(12, 7.6))
    fig.patch.set_facecolor(th["bg"]); axs = np.ravel(axs)
    for a in axs: style(a, th, fs)
    col = D.grp.map(lambda x: SC.get(x, th["dim"]))
    def sc(a, x): a.scatter(x, e, s=26, c=col, edgecolors=th["bg"], linewidths=0.5, zorder=3); a.axhline(0, color=th["dim"], lw=0.8); a.set_ylabel("Residual (°C)")
    def lowess(a, x):
        try:
            from statsmodels.nonparametric.smoothers_lowess import lowess as lw
            z = lw(e, x, frac=0.7); a.plot(z[:, 0], z[:, 1], color=th["fg"], lw=1.2, zorder=2)
        except Exception: pass
    a = axs[0]; sc(a, D.fitted); lowess(a, D.fitted.to_numpy()); a.set_xlabel("Fitted core (°C)"); a.set_title("Residuals against fitted values", fontsize=fs - 1, loc="left", color=th["fg"], pad=42 if not phone else 8)
    a = axs[1]
    for k, (sid, grp_) in enumerate(D.groupby("series")):
        if len(grp_) < 2: continue
        grp_ = grp_.sort_values("N"); a.plot(grp_.N, grp_.e, color=th["dim"], lw=0.9, zorder=2)
    sc(a, D.N); a.set_xlabel("GPU fans (rpm)"); a.set_title((f"Along GPU fans, per series: DW {dw['stat']:.2f}" if phone else f"Along the GPU fans within each series: DW {dw['stat']:.2f}"), fontsize=fs - 1, loc="left", color=th["fg"], pad=42)
    sec(a, th, fs, r2g, g2r, [40, 60, 80, 100], "GPU fans (%)")
    a = axs[2]; sc(a, D.C); lowess(a, D.C.to_numpy()); a.set_xlabel("Case fans (rpm)"); a.set_title("Against case fans", fontsize=fs - 1, loc="left", color=th["fg"], pad=42)
    sec(a, th, fs, c2p, p2c, [27, 44, 62, 100], "Case fans (%)")
    a = axs[3]; sc(a, D.P); a.set_xlabel("Board power (W)"); a.set_title("Against power", fontsize=fs - 1, loc="left", color=th["fg"], pad=42 if not phone else 8)
    a = axs[4]; o = np.argsort(D.ts_end.to_numpy()); a.plot(np.arange(len(e)), e[o], color=th["dim"], lw=0.8, zorder=2)
    a.scatter(np.arange(len(e)), e[o], s=26, c=col.to_numpy()[o], edgecolors=th["bg"], linewidths=0.5, zorder=3); a.axhline(0, color=th["dim"], lw=0.8)
    dwt = tests["Durbin–Watson, time order"]; a.set_xlabel("Measurement order"); a.set_ylabel("Residual (°C)"); a.set_title(f"In time order: DW {dwt['stat']:.2f}", fontsize=fs - 1, loc="left", color=th["fg"], pad=42 if not phone else 8)
    a = axs[5]; (osm, osr), (sl, ic, _) = stats.probplot(e / e.std(ddof=1), dist="norm")
    a.scatter(osm, osr, s=26, color=th["fg"], zorder=3); a.plot(osm, sl * osm + ic, color="#ff453a", lw=1.2)
    sw = tests["Shapiro–Wilk"]; a.set_xlabel("Normal quantile"); a.set_ylabel("Standardised residual"); a.set_title(f"Normal Q–Q: Shapiro–Wilk p = {sw['p']:.3f}", fontsize=fs - 1, loc="left", color=th["fg"], pad=42 if not phone else 8)
    h = [plt.Line2D([], [], ls="none", marker="o", color=SC.get(gp_, th["dim"])) for gp_ in SESS if gp_ in set(D.grp)]
    l = [SESS[gp_][1] for gp_ in SESS if gp_ in set(D.grp)]
    fig.legend(h, l, loc="lower center", ncol=1 if phone else len(h), fontsize=fs - 3, frameon=False, labelcolor=th["fg"])
    fig.tight_layout(rect=(0, 0.06 if phone else 0.06, 1, 1))
    save(fig, th, f"gpu-map-steady-diagnostics{TAG}{'-phone' if phone else ''}-{theme}")
for t in THEMES:
    for ph in (False, True): two_ways(t, ph); diagnostics(t, ph)
