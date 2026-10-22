"""Article figure for ctrl1 (ws298, 22 Oct 2026): the WS.Sensor controller on real hardware vs its simulation, load-step runs.
Rows: Quiet, Balanced, Performance; columns: core and memory (°C), GPU fans (% and rpm), case fans (rpm and %).
House style (light/dark/phone, webp). Usage: fig_ctrl1.py outdir"""
import glob, os, sys
from pathlib import Path
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpecFromSubplotSpec
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import controller_sim as cs
import importlib.util
spec = importlib.util.spec_from_file_location("c1", os.path.join(os.path.dirname(os.path.abspath(__file__)), "ctrl1_compare.py"))
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "ctrl1-2026-10-22")
def sim(m, P_dem, tin):                                   # same as ctrl1_compare.sim
    ctl = cs.Controller(m); pl = cs.Plant(tin[0]); core, mem = cs.steady(30, 0, 1000, tin[0], 0)
    pl.ts = core - 30 * cs.CORE["Rjs"] - cs.CORE["th0"]; pl.tm = mem; N, C, lim = ctl.N, ctl.C, 1.0; rows = []
    for t in range(len(P_dem)):
        P = min(P_dem[t], 575 * lim); core, mem = pl.step(P, N, C, tin[t], 1.0 if P_dem[t] > 100 else 0.0)
        N, C, lim = ctl.step(core, mem, P, tin[t]); rows.append((P, core, mem, N, C, lim))
    return np.array(rows)
MODES = [("quiet", "Quiet, target 80 °C"), ("balanced", "Balanced, target 77 °C"), ("performance", "Performance, target 72 °C")]
RUNS = {}
for m, _ in MODES:
    d = pd.read_csv(glob.glob(os.path.join(D, f"{m}-step", "ctrl.csv"))[0]); tin = d.intake_c.ffill().bfill().values
    RUNS[m] = (d, sim(m, np.where(d.load.values > 0, 575.0, d.P_w.values), tin))
THEMES = {"light": dict(bg="#ffffff", fg="#1d1d1f", grid="#d9d9de", dim="#86868b"), "dark": dict(bg="#141414", fg="#f5f5f7", grid="#3a3a3c", dim="#98989d")}
CORE, MEM, GPU, CASE = "#ff453a", "#bf5af2", "#30d158", "#64d2ff"
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
    og = F.add_gridspec(3, 1, hspace=0.42) if phone else F.add_gridspec(3, 3, hspace=0.45, wspace=0.42)
    for r_, (m, title) in enumerate(MODES):
        d, s = RUNS[m]; t = d.t_s.values / 60; tgt = cs.MODES[m]["target"]
        if phone:
            sub = GridSpecFromSubplotSpec(3, 1, subplot_spec=og[r_], height_ratios=[2.2, 1, 1], hspace=0.12)
            axs = [F.add_subplot(sub[0])]; axs += [F.add_subplot(sub[1], sharex=axs[0]), F.add_subplot(sub[2], sharex=axs[0])]
        else:
            axs = [F.add_subplot(og[r_, j]) for j in range(3)]
        for a in axs: style(a, th, fs)
        core = d.core_nvapi_c.fillna(d.core_c).values
        axs[0].plot(t, core, color=CORE, lw=1.2, label="core, measured"); axs[0].plot(t, s[:, 1], color=CORE, lw=1.0, ls="--", label="core, simulated")
        axs[0].plot(t, d.mem_c, color=MEM, lw=1.2, label="memory, measured"); axs[0].plot(t, s[:, 2], color=MEM, lw=1.0, ls="--", label="memory, simulated")
        axs[0].axhline(tgt, color=th["dim"], lw=0.9, ls=":"); axs[0].set_ylabel("°C"); axs[0].set_title(title, loc="left", fontsize=fs - 1, color=th["fg"])
        axs[1].plot(t, cs.RPM_DUTY(d.gpu_rpm.values), color=GPU, lw=1.2); axs[1].plot(t, cs.RPM_DUTY(s[:, 3]), color=GPU, lw=1.0, ls="--")
        axs[1].set_ylim(0, 105); axs[1].set_yticks([0, 40, 70, 100]); axs[1].set_ylabel("GPU fans\n(%)" if phone else "GPU fans (%)", fontsize=fs - 2)
        right(axs[1], th, fs, cs.DUTY_RPM, cs.RPM_DUTY, [round(float(cs.DUTY_RPM(v)), -1) for v in (40, 70, 100)], "rpm")
        axs[2].plot(t, d.case_rpm, color=CASE, lw=1.0); axs[2].plot(t, s[:, 4], color=CASE, lw=1.0, ls="--")
        axs[2].set_ylim(0, 3100); axs[2].set_yticks([1000, 2000, 2920]); axs[2].set_ylabel("Case fans\n(rpm)" if phone else "Case fans (rpm)", fontsize=fs - 2)
        right(axs[2], th, fs, cpct, crpm, [27, 62, 100], "%")
        if phone:
            for a in axs[:2]: a.tick_params(labelbottom=False)
            axs[2].set_xlabel("Minutes")
        else:
            for a in axs: a.set_xlabel("Minutes")
            if r_ == 0: axs[1].set_title("GPU fans", loc="left", fontsize=fs - 1, color=th["fg"]); axs[2].set_title("Case fans", loc="left", fontsize=fs - 1, color=th["fg"])
    h = [plt.Line2D([], [], color=CORE, lw=1.4), plt.Line2D([], [], color=MEM, lw=1.4), plt.Line2D([], [], color=th["fg"], lw=1.2), plt.Line2D([], [], color=th["fg"], lw=1.2, ls="--"), plt.Line2D([], [], color=th["dim"], lw=0.9, ls=":")]
    l = ["core", "memory", "measured on ws298", "simulated", "target"]
    F.legend(h, l, loc="lower center", ncol=2 if phone else 5, fontsize=fs - 2, frameon=False, labelcolor=th["fg"])
    F.subplots_adjust(left=0.2 if phone else 0.06, right=0.84 if phone else 0.95, top=0.97, bottom=0.1 if phone else 0.1)
    name = f"gpu-map-ctrl1{'-phone' if phone else ''}-{theme}"
    F.savefig(out / f"{name}.png", dpi=200, facecolor=th["bg"]); plt.close(F)
    im = Image.open(out / f"{name}.png").convert("RGB"); im.save(out / f"{name}.webp", "WEBP", quality=86, method=6); print(name, im.size)
for t in THEMES:
    for ph in (False, True): fig(t, ph)
