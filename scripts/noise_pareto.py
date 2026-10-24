"""Literature-based noise models and the quiet-vs-temperature Pareto frontier (provisional until our own sound map).
Case/radiator 120 mm (SW Pro 4 120): L = a + b·log10(rpm), least squares on Hardware Busters' rpm at 20/25/30/35/40 dBA (1 m).
GPU (RTX 5090 FE): L = 32.5 + 50·log10(rpm/1570) dBA at 1 m (GamersNexus anchor, 50·log10 fan law), the estimate already in the article.
Total (eq. 13): L = 10·log10(10^(Lg/10) + 7·10^(Lc/10)): 4 case + 3 radiator fans at the same rpm.
Core and memory: the primary model (model3.py, steady3 fit), intake 19.3 °C.
Writes results-2026-10-23/noise-pareto.json and the article figures. Usage: noise_pareto.py outdir"""
import json, os, sys
from pathlib import Path
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import controller_sim as cs
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__)); out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
J = json.load(open(os.path.join(H, "results-2026-10-22/steady-stats.json"))); MJ = json.load(open(os.path.join(H, "results-2026-10-23/mem-model.json")))
P = {p["param"]: p["est"] for p in J["params"]}; Q = {k: v[0] for k, v in MJ["params"].items()}
TIN = 19.3
import model3   # primary model (steady3 fit)
core = lambda N, C, W, T=TIN: model3.core(N, C, W, T)
mem = lambda N, C, W, T=TIN: model3.mem(N, C, W, T)
# --- fan noise fits
hwb = np.array([(1281, 20), (1573, 25), (1871, 30), (2274, 35), (2771, 40)], float)
X = np.column_stack([np.ones(len(hwb)), np.log10(hwb[:, 0])]); (a, b), *_ = np.linalg.lstsq(X, hwb[:, 1], rcond=None)
Lc = lambda r: a + b * np.log10(r); res_c = hwb[:, 1] - Lc(hwb[:, 0]); chk_c = 42.6 - Lc(3000)
Lg = lambda r: 32.5 + 50 * np.log10(r / 1570)
anchors = [("GamersNexus, 1 m", 1570, 32.5, 0.0), ("TechPowerUp, 50 cm", 1673, 40.1, 0.5), ("HWCooling, 35 cm", 1750, 44.0, 0.35), ("LanOC 100 %, 46 cm", 2873, 58.4, 0.46)]
res_g = [(n, r, L, round(L + (20 * np.log10(d) if d else 0) - Lg(r), 1)) for n, r, L, d in anchors]
pcgh = dict(l40_60=round(10 * np.log2(4.2 / 2.3), 1), model40_60=round(50 * np.log10(1920 / 1440), 1), l40_100=round(10 * np.log2(9.5 / 2.3), 1), model40_100=round(50 * np.log10(3030 / 1440), 1))
import noise_model
Ltot = lambda N, C: noise_model.L_total(N, C)   # GPU + 4 case + 3 radiator (measured speed), energy sum
pct2rpm = lambda p: 1313 + (p - 40) * (3012 - 1313) / 60; rpm2pct = lambda r: 40 + (r - 1313) * 60 / (3012 - 1313)
GP = np.arange(40, 101, 1.0); CC = np.arange(800, 3001, 50.0); GG, CCm = np.meshgrid(GP, CC); NN = pct2rpm(GG)
CLASSES = [(0, 24, "ultra-quiet"), (24, 29, "very quiet"), (29, 33, "quiet"), (33, 37, "balanced"), (37, 42, "loud"), (42, 99, "very loud")]
cls = lambda L: next(n for lo, hi, n in CLASSES if lo <= L < hi)
def grid(W, T=TIN):
    Tc = core(NN, CCm, W, T); Tm = mem(NN, CCm, W, T); L = Ltot(NN, CCm); return Tc, Tm, L
def frontier(Tc, L):
    o = np.argsort(L.ravel()); best = np.inf; f = []
    for i in o:
        if Tc.ravel()[i] < best - 1e-9: best = Tc.ravel()[i]; f.append(i)
    return f
def quietest(W, target, T=TIN, memmax=90.0):
    Tc, Tm, L = grid(W, T); ok = (Tc <= target) & (Tm <= memmax)
    if not ok.any(): return None
    i = np.argmin(np.where(ok, L, np.inf)); g, c = GG.ravel()[i], CCm.ravel()[i]
    return dict(gpu_pct=int(g), gpu_rpm=int(round(pct2rpm(g), -1)), case_rpm=int(c), dBA=round(float(L.ravel()[i]), 1), core=round(float(Tc.ravel()[i]), 1), mem=round(float(Tm.ravel()[i]), 1), cls=cls(L.ravel()[i]))
TARGETS = [70, 72.5, 75, 77.5, 80, 82.5, 85]
table = {str(W): {str(t): quietest(W, t) for t in TARGETS} for W in (575, 402)}
modes = {m: {str(W): quietest(W, t) for W in (575, 402)} for m, t in (("Quiet", 80), ("Balanced", 77), ("Performance", 72))}
# --- power within a noise budget (eq. 14) at a fixed core target, two intakes
PLW = {100: 575, 90: 518, 80: 460, 70: 402}
cost = {f"{T:.0f}": {str(t): {str(pl): quietest(w, t, T) for pl, w in PLW.items()} for t in (77, 80)} for T in (19.3, 30.0)}
budgets = np.arange(20, 50.01, 0.25)
def pmax(budget, target, T):
    Ws = np.arange(402, 575.01, 1.0); best = None
    for W in Ws[::-1]:
        Tc, Tm, L = grid(W, T)
        if ((Tc <= target) & (Tm <= 90) & (L <= budget)).any(): return W
    return np.nan
PM = {f"{T:.0f}": [pmax(B, 77, T) for B in budgets] for T in (19.3, 30.0)}
g1 = pd.read_csv(os.path.join(H, "data/grid1c-2026-10-21/grid.csv")); cg = g1.groupby("pl_pct").agg(W=("power_w_sum", "mean"), f=("cardA_clock_mhz", "mean")).sort_values("W")
clkW = cg.W.round().to_numpy(); clkV = cg.f.to_numpy()
clock = lambda W: float(np.interp(W, clkW, clkV)) if np.isfinite(W) else np.nan
res = dict(case_fit=dict(a=round(a, 2), b=round(b, 2), residuals=[round(x, 2) for x in res_c], check_3000=round(float(chk_c), 1), seven_fans_db=round(10 * np.log10(7), 2)),
           gpu_fit=dict(level=32.5, ref_rpm=1570, slope=50, anchors=res_g, pcgh=pcgh), table=table, modes=modes, cost=cost,
           pmax=dict(budgets=budgets.tolist(), **{k: [None if not np.isfinite(v) else float(v) for v in vs] for k, vs in PM.items()}),
           clock_by_power={str(int(round(w))): round(float(v)) for w, v in zip(clkW, clkV)})
def _fr(W):
    Tc, Tm, L = grid(W); return [dict(gpu_pct=float(GG.ravel()[i]), case_rpm=float(CCm.ravel()[i]), dBA=float(L.ravel()[i]), core=float(Tc.ravel()[i])) for i in frontier(Tc, L)]
res["frontier"] = {str(W): _fr(W) for W in (575, 402)}
json.dump(res, open(os.path.join(H, "results-2026-10-23/noise-pareto.json"), "w"), indent=1, default=float)
print(json.dumps({k: res[k] for k in ("case_fit", "gpu_fit")}, indent=1, default=float)); print(json.dumps(table, indent=0)[:1500]); print(json.dumps(cost)[:800])
# --- figures
TH = {"light": dict(bg="#ffffff", fg="#1d1d1f", grid="#d9d9de", dim="#86868b"), "dark": dict(bg="#141414", fg="#f5f5f7", grid="#3a3a3c", dim="#98989d")}
def style(ax, th, fs):
    ax.set_facecolor(th["bg"])
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.tick_params(colors=th["fg"], labelsize=fs - 2, length=0); ax.xaxis.label.set_color(th["fg"]); ax.yaxis.label.set_color(th["fg"])
    ax.grid(color=th["grid"], lw=0.6); ax.set_axisbelow(True)
def save(F, th, name):
    F.savefig(out / f"{name}.png", dpi=200, facecolor=th["bg"]); plt.close(F)
    im = Image.open(out / f"{name}.png").convert("RGB"); im.save(out / f"{name}.webp", "WEBP", quality=86, method=6); print(name, im.size)
BAND = ["#30d158", "#64d2ff", "#0a84ff", "#ff9f0a", "#ff453a", "#bf5af2"]
def fig_pareto(theme, phone):
    th = TH[theme]; fs = 13 if phone else 11
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Arial", "DejaVu Sans"], "font.size": fs})
    F, axs = plt.subplots(2, 1, figsize=(5, 12)) if phone else plt.subplots(1, 2, figsize=(13, 6.2), sharey=True)
    F.patch.set_facecolor(th["bg"])
    for ax, W, col in zip(axs, (575, 402), ("#ff453a", "#0a84ff")):
        style(ax, th, fs); Tc, Tm, L = grid(W)
        for (lo, hi, n), bc in zip(CLASSES, BAND):
            ax.axvspan(max(lo, 18), min(hi, 52), color=bc, alpha=0.08, lw=0)
            ax.text((max(lo, 18) + min(hi, 52)) / 2, 0.01, n, transform=ax.get_xaxis_transform(), ha="center", va="bottom", fontsize=fs - 4, color=th["dim"], rotation=90 if phone else 0)
        ax.scatter(L.ravel()[::7], Tc.ravel()[::7], s=4, color=th["dim"], alpha=0.35, lw=0, zorder=2)
        f = frontier(Tc, L); fl, ft = L.ravel()[f], Tc.ravel()[f]
        ax.plot(fl, ft, color=col, lw=2.2, zorder=4)
        last = -9
        for i in f:
            if Tc.ravel()[i] < last - 1.6 or last == -9:
                ax.scatter([L.ravel()[i]], [Tc.ravel()[i]], s=22, color=col, zorder=5)
                ax.annotate(f"{int(GG.ravel()[i])} % / {int(CCm.ravel()[i])}", (L.ravel()[i], Tc.ravel()[i]), xytext=(5, 3), textcoords="offset points", fontsize=fs - 4, color=th["fg"])
                last = Tc.ravel()[i]
        for m, mk in (("quiet", "o"), ("balanced", "s"), ("performance", "D")):   # released modes (WS.Sensor 0.30.69), controller_sim planning
            c = cs.Controller(m, P_stock=W); t = cs.CORE_LIMIT_DEFAULT - cs.MODES[m]["comfort"][0]; B = cs.MODES[m]["budget"]
            N, C, plc, over = c.make_plan(W, TIN); qc = core(N, C, W * plc)   # model (11), as the frontier
            ax.axhline(t, color=th["dim"], lw=0.8, ls=":"); ax.axvline(B, color=th["dim"], lw=0.8, ls="--")
            ax.scatter([cs.noise(N, C)], [qc], s=90, marker=mk, facecolors="none", edgecolors=th["fg"], linewidths=1.6, zorder=6)
            ax.text(0.01, t, f"{m.capitalize()} comfort {t:.0f} °C", transform=ax.get_yaxis_transform(), ha="left", va="bottom", fontsize=fs - 3, color=th["fg"])
            ax.text(B + 0.3, 0.97, f"{B:.0f} dBA", transform=ax.get_xaxis_transform(), ha="left", va="top", fontsize=fs - 4, color=th["dim"])
        ax.set_xlim(18, 52); ax.set_ylim(min(45, float(np.nanmin(Tc)) - 1), 90)
        ax.set_xlabel("Total noise, all fans, dBA at 1 m (literature-based estimate)"); ax.set_ylabel("Settled core (°C)")
        ax.set_title(f"Power limit {W} W", loc="left", fontsize=fs, color=th["fg"])
    F.tight_layout(); save(F, th, f"gpu-map-noise-pareto{'-phone' if phone else ''}-{theme}")
def fig_pmax(theme, phone):
    th = TH[theme]; fs = 13 if phone else 11
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Arial", "DejaVu Sans"], "font.size": fs})
    F, ax = plt.subplots(figsize=(5, 6) if phone else (8, 5.2)); F.patch.set_facecolor(th["bg"]); style(ax, th, fs)
    ax2 = ax.secondary_yaxis("right", functions=(lambda w: np.interp(w, clkW, clkV), lambda c: np.interp(c, clkV, clkW)))
    for (k, vs), col in zip(PM.items(), ("#0a84ff", "#ff453a")):
        ax.plot(budgets, vs, color=col, lw=2, label=f"intake {k} °C")
    ax.set_xlabel("Noise budget, all fans, dBA at 1 m"); ax.set_ylabel("Highest power, core ≤ 77 °C (W)")
    ax2.set_ylabel("Average clock at that power (MHz)", color=th["fg"]); ax2.tick_params(colors=th["fg"], labelsize=fs - 2, length=0)
    for sp in ax2.spines.values(): sp.set_visible(False)
    ax.set_ylim(390, 585); ax.set_xlim(20, 50); ax.legend(frameon=False, labelcolor=th["fg"], fontsize=fs - 2, loc="lower right")
    F.tight_layout(); save(F, th, f"gpu-map-noise-pmax{'-phone' if phone else ''}-{theme}")
for t in TH:
    for ph in (False, True): fig_pareto(t, ph); fig_pmax(t, ph)
