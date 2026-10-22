"""Article figure for the controller simulation (house style: light/dark/phone, webp). Reruns controller_sim scenarios.
Rows: scenarios; columns: core (°C), GPU fans (% and rpm), case fans (rpm and %). Usage: fig_controller.py outdir"""
import json, os, sys
from pathlib import Path
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpecFromSubplotSpec
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import controller_sim as cs

out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
CTL = [("factory", "Factory curve, case 1000 rpm", lambda: cs.Factory()), ("quiet", "Quiet, 80 °C", lambda: cs.Controller("quiet")),
       ("balanced", "Balanced, 77 °C", lambda: cs.Controller("balanced")), ("performance", "Performance, 72 °C", lambda: cs.Controller("performance"))]
TITLE = {"step 30->575 W": "Load step, 30 to 575 W", "intake 19->30 °C": "Intake air rising from 19 to 30 °C", "bursts 60 s on/off": "Load bursts, 60 s on and off"}
RUNS = {name: {k: cs.run(f(), Pf, Tf) for k, _, f in CTL} for name, (Pf, Tf) in cs.SCEN.items()}
THEMES = {"light": dict(bg="#ffffff", fg="#1d1d1f", grid="#d9d9de", dim="#86868b"), "dark": dict(bg="#141414", fg="#f5f5f7", grid="#3a3a3c", dim="#98989d")}
COL = {"quiet": "#30d158", "balanced": "#0a84ff", "performance": "#ff453a"}
cpct = lambda r: (np.asarray(r) - 330.4) / 26.13; crpm = lambda q: np.asarray(q) * 26.13 + 330.4
def style(ax, th, fs):
    ax.set_facecolor(th["bg"])
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.tick_params(colors=th["fg"], labelsize=fs - 2, length=0); ax.xaxis.label.set_color(th["fg"]); ax.yaxis.label.set_color(th["fg"])
    ax.grid(color=th["grid"], lw=0.6); ax.set_axisbelow(True)
def right(ax, th, fs, f, finv, ticks, label):
    a = ax.secondary_yaxis("right", functions=(f, finv)); a.set_yticks(ticks); a.set_ylabel(label, color=th["fg"], fontsize=fs - 2)
    a.tick_params(colors=th["fg"], labelsize=fs - 3, length=0)
    for sp in a.spines.values(): sp.set_visible(False)
def fig(theme, phone):
    th = THEMES[theme]; fs = 15 if phone else 11
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Arial", "DejaVu Sans"], "font.size": fs})
    F = plt.figure(figsize=(5, 17) if phone else (13, 9.6)); F.patch.set_facecolor(th["bg"])
    og = F.add_gridspec(3, 1, hspace=0.42) if phone else F.add_gridspec(3, 3, hspace=0.42, wspace=0.42)
    col = lambda k: th["dim"] if k == "factory" else COL[k]
    for r_, (name, runs) in enumerate(RUNS.items()):
        if phone:
            sub = GridSpecFromSubplotSpec(3, 1, subplot_spec=og[r_], height_ratios=[2.2, 1, 1], hspace=0.12)
            axs = [F.add_subplot(sub[0])]; axs += [F.add_subplot(sub[1], sharex=axs[0]), F.add_subplot(sub[2], sharex=axs[0])]
        else:
            axs = [F.add_subplot(og[r_, j]) for j in range(3)]
        for a in axs: style(a, th, fs)
        for k, lab, _ in CTL:
            r = runs[k]; tm = r[:, 0] / 60
            axs[0].plot(tm, r[:, 2], color=col(k), lw=1.4 if k != "factory" else 1.2, ls="-" if k != "factory" else "--", label=lab)
            axs[1].plot(tm, cs.RPM_DUTY(r[:, 4]), color=col(k), lw=1.2, ls="-" if k != "factory" else "--")
            axs[2].plot(tm, r[:, 5], color=col(k), lw=1.2, ls="-" if k != "factory" else "--")
        axs[0].set_ylabel("Core (°C)"); axs[0].set_title(TITLE.get(name, name), loc="left", fontsize=fs - 1, color=th["fg"])
        axs[1].set_ylabel("GPU fans\n(%)" if phone else "GPU fans (%)", fontsize=fs - 2); axs[1].set_ylim(0, 105); axs[1].set_yticks([0, 40, 70, 100])
        right(axs[1], th, fs, cs.DUTY_RPM, cs.RPM_DUTY, [round(float(cs.DUTY_RPM(v)), -1) for v in (40, 70, 100)], "rpm")
        axs[2].set_ylabel("Case fans\n(rpm)" if phone else "Case fans (rpm)", fontsize=fs - 2); axs[2].set_ylim(0, 3100); axs[2].set_yticks([1000, 2000, 2920])
        right(axs[2], th, fs, cpct, crpm, [27, 62, 100], "%")
        if phone:
            for a in axs[:2]: a.tick_params(labelbottom=False)
            axs[2].set_xlabel("Minutes")
        else:
            for a in axs: a.set_xlabel("Minutes")
            if r_ == 0: axs[1].set_title("GPU fans", loc="left", fontsize=fs - 1, color=th["fg"]); axs[2].set_title("Case fans", loc="left", fontsize=fs - 1, color=th["fg"])
    h, l = axs[0].get_legend_handles_labels()
    F.legend(h, l, loc="lower center", ncol=1 if phone else 4, fontsize=fs - 2, frameon=False, labelcolor=th["fg"])
    F.subplots_adjust(left=0.2 if phone else 0.06, right=0.84 if phone else 0.95, top=0.97, bottom=0.1 if phone else 0.1)
    name = f"gpu-map-controller-sim{'-phone' if phone else ''}-{theme}"
    F.savefig(out / f"{name}.png", dpi=200, facecolor=th["bg"]); plt.close(F)
    im = Image.open(out / f"{name}.png").convert("RGB"); im.save(out / f"{name}.webp", "WEBP", quality=86, method=6); print(name, im.size)
for t in THEMES:
    for ph in (False, True): fig(t, ph)
