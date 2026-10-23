"""Control law figure: for each noise-budget mode, the fan pair (flat in power) and the predicted core and memory against board
power, with the safety limits and the power at which the power limit must be lowered. Usage: ctrl_law.py outdir"""
import json, sys
from pathlib import Path
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image
G = Path(__file__).resolve().parent.parent; out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
M = json.load(open(G / "results-2026-10-23/modes-noise.json"))
J = json.load(open(G / "results-2026-10-22/steady-stats.json")); MJ = json.load(open(G / "results-2026-10-23/mem-model.json"))
P = {p["param"]: p["est"] for p in J["params"]}; Q = {k: v[0] for k, v in MJ["params"].items()}
TIN = 19.3
core = lambda N, C, W: TIN + P["θ0"] + W * (P["r∞"] / 1000 + 1 / (P["gN"] * (N / 1000) ** P["m"] + P["gC"] * (C / 1500) ** P["s"]))
mem = lambda N, C, W: TIN + Q["θ0m"] + W * (Q["r∞"] / 1000 + 1 / (Q["gN"] * (N / 1000) ** Q["m"] + Q["gC"] * (C / 1500) ** Q["s"]))
W = np.linspace(100, 575, 200)
TH = {"light": dict(bg="#ffffff", fg="#1d1d1f", grid="#d9d9de", dim="#86868b"), "dark": dict(bg="#141414", fg="#f5f5f7", grid="#3a3a3c", dim="#98989d")}
COL = {"Quiet": "#30d158", "Balanced": "#0a84ff", "Performance": "#ff453a"}
res = {}
for m in M:
    tc, tm = core(m["gpu_rpm"], m["case_rpm"], W), mem(m["gpu_rpm"], m["case_rpm"], W)
    lim = W[(tc <= 83) & (tm <= 90)]
    res[m["mode"]] = dict(pmax=float(lim.max()) if len(lim) else None)
json.dump(res, open(G / "results-2026-10-23/ctrl-law.json", "w"), indent=1)
def fig(theme, phone):
    th = TH[theme]; fs = 13 if phone else 11
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Arial", "DejaVu Sans"], "font.size": fs})
    F, axs = plt.subplots(3 if phone else 1, 1 if phone else 3, figsize=(5, 11) if phone else (13, 4.6), facecolor=th["bg"])
    for ax in axs:
        ax.set_facecolor(th["bg"]); [sp.set_visible(False) for sp in ax.spines.values()]
        ax.tick_params(colors=th["fg"], labelsize=fs - 2, length=0); ax.grid(color=th["grid"], lw=0.6); ax.set_axisbelow(True)
        ax.xaxis.label.set_color(th["fg"]); ax.yaxis.label.set_color(th["fg"]); ax.set_xlabel("Board power, W")
    for m in M:
        c = COL[m["mode"]]; lab = f'{m["mode"]} (≤ {m["budget"]} dBA)'
        axs[0].plot(W, np.full_like(W, m["gpu_pct"]), color=c, lw=2, label=lab)
        axs[0].plot(W, np.full_like(W, m["case_rpm"] / 3000 * 100), color=c, lw=1.5, ls="--")
        axs[1].plot(W, core(m["gpu_rpm"], m["case_rpm"], W), color=c, lw=2)
        axs[2].plot(W, mem(m["gpu_rpm"], m["case_rpm"], W), color=c, lw=2)
    axs[0].set_ylabel("Fan speed, % (solid: GPU fans; dashed: case and radiator fans, % of 3000 rpm)" if not phone else "Fan speed, %"); axs[0].set_ylim(0, 100)
    sec = axs[0].secondary_yaxis("right", functions=(lambda p: np.asarray(p) * 30, lambda r: np.asarray(r) / 30)); sec.set_ylabel("rpm (case fans)", color=th["fg"]); sec.tick_params(colors=th["fg"], labelsize=fs - 2, length=0)
    axs[1].axhline(83, color=th["fg"], ls=":", lw=1); axs[1].text(110, 84, "core limit 83 °C (default)", color=th["dim"], fontsize=fs - 3); axs[1].set_ylabel("Predicted core, °C")
    axs[2].axhline(90, color=th["fg"], ls=":", lw=1); axs[2].text(110, 91, "memory limit 90 °C (default)", color=th["dim"], fontsize=fs - 3); axs[2].set_ylabel("Predicted memory, °C")
    axs[0].legend(frameon=False, labelcolor=th["fg"], fontsize=fs - 3, loc="lower right")
    F.tight_layout(); name = f"gpu-map-ctrl-law-{'phone-' if phone else ''}{theme}"
    F.savefig(out / f"{name}.png", dpi=200, facecolor=th["bg"]); plt.close(F)
    Image.open(out / f"{name}.png").convert("RGB").save(out / f"{name}.webp", "WEBP", quality=86, method=6); print(name)
for t in TH:
    for ph in (False, True): fig(t, ph)
print(res)
