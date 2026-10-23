"""Control law of the released controller (WS.Sensor 0.30.69): for each mode, the planned fan pair, noise, power limit and predicted
core/memory against board power (intake 19.3 °C), computed with controller_sim's own planning functions. Writes the figure and
results-2026-10-23/ctrl-law.json (also the modes table). Usage: ctrl_law.py outdir"""
import json, sys
from pathlib import Path
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image
G = Path(__file__).resolve().parent.parent; sys.path.insert(0, str(G)); out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
import controller_sim as cs
TIN = 19.3; W = np.arange(30, 576, 5.0)
res = {}
for mode in ("quiet", "balanced", "performance"):
    c = cs.Controller(mode); rows = []
    for P in W:
        N, C, pl, over = c.make_plan(P, TIN)
        core, mem = cs.steady_ff(P * pl, N, C, TIN)
        rows.append(dict(P=float(P), gpu_rpm=float(N), gpu_pct=float(cs.RPM_DUTY(N)), case_rpm=float(C), pl=float(pl), over=bool(over),
                         dBA=float(cs.noise(N, C)), core=float(core), mem=float(mem)))
    res[mode] = dict(budget=c.budget, comfort=list(cs.MODES[mode]["comfort"]), core_comfort=cs.CORE_LIMIT_DEFAULT - cs.MODES[mode]["comfort"][0],
                     mem_comfort=c.mem_l - cs.MODES[mode]["comfort"][1], rows=rows)
json.dump(res, open(G / "results-2026-10-23/ctrl-law.json", "w"), indent=1)
TH = {"light": dict(bg="#ffffff", fg="#1d1d1f", grid="#d9d9de", dim="#86868b"), "dark": dict(bg="#141414", fg="#f5f5f7", grid="#3a3a3c", dim="#98989d")}
COL = {"quiet": "#30d158", "balanced": "#0a84ff", "performance": "#ff453a"}; NM = {"quiet": "Quiet", "balanced": "Balanced", "performance": "Performance"}
def fig(theme, phone):
    th = TH[theme]; fs = 13 if phone else 11
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Arial", "DejaVu Sans"], "font.size": fs})
    F, axs = plt.subplots(4 if phone else 2, 1 if phone else 2, figsize=(5, 14) if phone else (13, 8.6), facecolor=th["bg"]); axs = np.ravel(axs)
    for ax in axs:
        ax.set_facecolor(th["bg"]); [sp.set_visible(False) for sp in ax.spines.values()]
        ax.tick_params(colors=th["fg"], labelsize=fs - 2, length=0); ax.grid(color=th["grid"], lw=0.6); ax.set_axisbelow(True)
        ax.xaxis.label.set_color(th["fg"]); ax.yaxis.label.set_color(th["fg"]); ax.set_xlabel("Board power, W")
    for m, d in res.items():
        r = d["rows"]; P = [x["P"] for x in r]; col = COL[m]
        axs[0].plot(P, [x["gpu_pct"] for x in r], color=col, lw=2, label=f'{NM[m]} (≤ {d["budget"]:.0f} dBA)')
        axs[1].plot(P, [x["case_rpm"] for x in r], color=col, lw=2)
        axs[2].plot(P, [x["dBA"] for x in r], color=col, lw=2); axs[2].axhline(d["budget"], color=col, ls=":", lw=1)
        axs[3].plot(P, [x["core"] for x in r], color=col, lw=2); axs[3].axhline(d["core_comfort"], color=col, ls=":", lw=1)
    axs[0].set_ylabel("GPU fans, %"); sec = axs[0].secondary_yaxis("right", functions=(cs.DUTY_RPM, cs.RPM_DUTY)); sec.set_ylabel("rpm", color=th["fg"]); sec.tick_params(colors=th["fg"], labelsize=fs - 2, length=0)
    axs[1].set_ylabel("Case and radiator fans, rpm"); sec = axs[1].secondary_yaxis("right", functions=(lambda r: np.asarray(r) / 29.2, lambda p: np.asarray(p) * 29.2)); sec.set_ylabel("%", color=th["fg"]); sec.tick_params(colors=th["fg"], labelsize=fs - 2, length=0)
    axs[2].set_ylabel("Total noise at 1 m, dBA (dotted: budget)"); axs[3].set_ylabel("Predicted core, °C (dotted: comfort level)")
    axs[0].legend(frameon=False, labelcolor=th["fg"], fontsize=fs - 3, loc="upper left")
    F.tight_layout(); name = f"gpu-map-ctrl-law-{'phone-' if phone else ''}{theme}"
    F.savefig(out / f"{name}.png", dpi=200, facecolor=th["bg"]); plt.close(F)
    Image.open(out / f"{name}.png").convert("RGB").save(out / f"{name}.webp", "WEBP", quality=86, method=6); print(name, Image.open(out / f"{name}.png").size)
for t in TH:
    for ph in (False, True): fig(t, ph)
for m, d in res.items():
    pick = {int(x["P"]): x for x in d["rows"] if int(x["P"]) in (30, 150, 300, 402, 460, 520, 575)}
    print(m, {k: (round(v["gpu_pct"], 1), int(v["case_rpm"]), round(v["dBA"], 1), round(v["core"], 1), round(v["mem"], 1), v["pl"]) for k, v in pick.items()})
