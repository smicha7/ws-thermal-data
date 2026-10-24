"""One temperature, many settings: for each power limit and case/radiator speed, the lowest GPU fan % (40-100) that holds
core <= 70 °C and memory <= 80 °C, with its literature-based noise (eq. 13). Same models as noise_pareto.py, intake 19.3 °C.
Writes results-2026-10-23/iso-temp.json, iso-temp.csv and the article figures. Usage: iso_temp.py outdir"""
import csv, json, os, sys
from pathlib import Path
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__)); out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
J = json.load(open(os.path.join(H, "results-2026-10-22/steady-stats.json"))); MJ = json.load(open(os.path.join(H, "results-2026-10-23/mem-model.json")))
P = {p["param"]: p["est"] for p in J["params"]}; Q = {k: v[0] for k, v in MJ["params"].items()}
TIN, TCORE, TMEM = 19.3, 70.0, 80.0
sys.path.insert(0, H); import model3   # primary model (steady3 fit)
core = lambda N, C, W: model3.core(N, C, W, TIN)
mem = lambda N, C, W: model3.mem(N, C, W, TIN)
hwb = np.array([(1281, 20), (1573, 25), (1871, 30), (2274, 35), (2771, 40)], float)
(a, b), *_ = np.linalg.lstsq(np.column_stack([np.ones(5), np.log10(hwb[:, 0])]), hwb[:, 1], rcond=None)
import noise_model
Lc7 = lambda r: float(noise_model.L_fans7(r))          # 4 case + 3 radiator fans together (radiator at its measured speed)
Lg = lambda r: 32.5 + 50 * np.log10(r / 1570)
pct2rpm = lambda p: 1313 + (p - 40) * (3012 - 1313) / 60
PLW = {100: 575, 90: 518, 80: 460, 70: 402}; CASE = [800, 1000, 1300, 1600, 1900, 2400, 3000]
rows = []
for pl, W in PLW.items():
    for C in CASE:
        g = next((g for g in range(40, 101) if core(pct2rpm(g), C, W) <= TCORE and mem(pct2rpm(g), C, W) <= TMEM), None)
        if g is None: rows.append(dict(pl=pl, W=W, case_rpm=C, gpu_pct=None)); continue
        N = pct2rpm(g); lg, lc = Lg(N), Lc7(C); tc, tm = core(N, C, W), mem(N, C, W)
        bind = "floor" if g == 40 else ("core" if core(pct2rpm(g - 1), C, W) > TCORE else "memory")   # which limit fails one step lower
        rows.append(dict(pl=pl, W=W, case_rpm=C, gpu_pct=g, gpu_rpm=int(round(N, -1)), core=round(tc, 1), mem=round(tm, 1), binding=bind,
                         dBA_gpu=round(float(lg), 1), dBA_case7=round(float(lc), 1), dBA=round(float(10 * np.log10(10 ** (lg / 10) + 10 ** (lc / 10))), 1)))
best = {pl: min((r for r in rows if r["pl"] == pl and r["gpu_pct"]), key=lambda r: r["dBA"]) for pl in PLW}
assert all(r["core"] <= TCORE and r["mem"] <= TMEM for r in rows if r["gpu_pct"])   # self-check
json.dump(dict(intake=TIN, core_max=TCORE, mem_max=TMEM, rows=rows, best={str(k): v for k, v in best.items()}),
          open(os.path.join(H, "results-2026-10-23/iso-temp.json"), "w"), indent=1)
with open(os.path.join(H, "results-2026-10-23/iso-temp.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(next(r for r in rows if r["gpu_pct"]).keys())); w.writeheader(); w.writerows(rows)
for r in rows: print(r)
print("best", best)
TH = {"light": dict(bg="#ffffff", fg="#1d1d1f", grid="#d9d9de", dim="#86868b"), "dark": dict(bg="#141414", fg="#f5f5f7", grid="#3a3a3c", dim="#98989d")}
COL = {100: "#ff453a", 90: "#ff9f0a", 80: "#0a84ff", 70: "#30d158"}
def fig(theme, phone):
    th = TH[theme]; fs = 13 if phone else 11
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Arial", "DejaVu Sans"], "font.size": fs})
    F, ax = plt.subplots(figsize=(5, 5.6) if phone else (13, 6.4), facecolor=th["bg"]); ax.set_facecolor(th["bg"])
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.tick_params(colors=th["fg"], labelsize=fs - 2, length=0); ax.grid(color=th["grid"], lw=0.6); ax.set_axisbelow(True)
    for pl, W in PLW.items():
        rr = [r for r in rows if r["pl"] == pl and r["gpu_pct"]]
        ax.plot([r["case_rpm"] for r in rr], [r["dBA"] for r in rr], "-o", color=COL[pl], lw=2, ms=4, label=f"{pl} % ({W} W)")
        bb = best[pl]; ax.plot(bb["case_rpm"], bb["dBA"], "D", color=COL[pl], ms=10, mec=th["fg"], mew=0.8)
    ax.set_xlabel("Case and radiator fans, rpm", color=th["fg"]); ax.set_ylabel("Total noise, dBA at 1 m (estimate)", color=th["fg"])
    ax.set_xticks(CASE); ax.tick_params(axis="x", labelsize=fs - 4 if phone else fs - 2)
    tx = ax.secondary_xaxis("top", functions=(lambda r: (np.asarray(r) - 330.4) / 26.13, lambda q: np.asarray(q) * 26.13 + 330.4))
    tx.set_xticks([20, 40, 60, 80, 100]); tx.set_xlabel("Case and radiator fans, %", color=th["fg"], fontsize=fs - 2); tx.tick_params(colors=th["fg"], labelsize=fs - 3, length=0)
    for sp in tx.spines.values(): sp.set_visible(False)
    ax.legend(title="Power limit", frameon=False, labelcolor=th["fg"], fontsize=fs - 2, title_fontsize=fs - 2, loc="upper left").get_title().set_color(th["fg"])
    ax.text(0.99, 0.03, "core ≤ 70 °C, memory ≤ 80 °C\nintake 19.3 °C; diamond = quietest", transform=ax.transAxes, ha="right", va="bottom", color=th["dim"], fontsize=fs - 3)
    F.tight_layout(); name = f"gpu-map-iso-temp-{'phone-' if phone else ''}{theme}"
    F.savefig(out / f"{name}.png", dpi=200, facecolor=th["bg"]); plt.close(F)
    im = Image.open(out / f"{name}.png").convert("RGB"); im.save(out / f"{name}.webp", "WEBP", quality=86, method=6); print(name, im.size)
for t in TH:
    for ph in (False, True): fig(t, ph)
