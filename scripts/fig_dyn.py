"""Article figures for the dynamic core model (fig_export.py style, light/dark/phone, webp).
Uses dyn_model.py functions and the fitted parameters in results-2026-10-21/dyn-model.json (no refit).
A) training run grid1c: core measured vs simulated (one thermal mass + die resistance, and one node), inputs below.
B) held-out runs: core and memory measured vs simulated, free run from the first sample, inputs below each.
Every fan axis shows % (left) and rpm (right). Usage: fig_dyn.py outdir"""
import json, os, sys
from pathlib import Path
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dyn_model as dm

out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
J = json.load(open(os.path.join(dm.OUT, "dyn-model.json")))
p2, p1, pm = J["M2-pow"]["params"], J["M1-pow"]["params"], J["mem"]["params"]
train = dm.load("grid1c")
tests = [dm.load("log-1"), dm.load("grid1d"), dm.load("hold"), dm.load("night-v2d", dm.NIGHT)]
LABEL = {"log-1": "Manual series", "grid1d": "Repeat of the 40 % points", "hold": "Morning series", "night-v2d": "First-run night grid"}
gpct = lambda r: (np.asarray(r) - 1313) / (3012 - 1313) * 60 + 40
grpm = lambda q: (np.asarray(q) - 40) / 60 * (3012 - 1313) + 1313
cpct = lambda r: (np.asarray(r) - 330.4) / 26.13          # case controller duty ↔ rpm, linear fit on the second run
crpm = lambda q: np.asarray(q) * 26.13 + 330.4
THEMES = {"light": dict(bg="#ffffff", fg="#1d1d1f", grid="#d9d9de", dim="#86868b", meas="#1d1d1f"),
          "dark": dict(bg="#141414", fg="#f5f5f7", grid="#3a3a3c", dim="#98989d", meas="#f5f5f7")}
RED, BLUE, PURPLE, GREEN, ORANGE, TEAL = "#ff453a", "#0a84ff", "#bf5af2", "#30d158", "#ff9f0a", "#64d2ff"
rm = lambda a, b: float(np.sqrt(np.mean((np.asarray(a) - b) ** 2)))

def style(ax, th, fs):
    ax.set_facecolor(th["bg"])
    for s in ax.spines.values(): s.set_visible(False)
    ax.tick_params(colors=th["fg"], labelsize=fs - 2, length=0); ax.xaxis.label.set_color(th["fg"]); ax.yaxis.label.set_color(th["fg"])
    ax.grid(color=th["grid"], lw=0.6); ax.set_axisbelow(True)
def save(fig, th, name):
    fig.savefig(out / f"{name}.png", dpi=200, facecolor=th["bg"]); plt.close(fig)
    im = Image.open(out / f"{name}.png").convert("RGB"); im.save(out / f"{name}.webp", "WEBP", quality=86, method=6); print(name, im.size)
def fanstrip(ax, th, fs, tm, v, col, name, to_pct, to_rpm, ticks_pct, lim):
    ax.plot(tm, to_pct(v), color=col, lw=1.0); ax.set_ylim(*lim); ax.set_yticks(ticks_pct); ax.set_ylabel(f"{name}\n(%)", fontsize=fs - 2)
    r = ax.secondary_yaxis("right", functions=(to_rpm, to_pct)); r.set_yticks([round(float(to_rpm(t)), -1) for t in ticks_pct])
    r.set_ylabel("rpm", color=th["fg"], fontsize=fs - 2); r.tick_params(colors=th["fg"], labelsize=fs - 3, length=0)
    for sp in r.spines.values(): sp.set_visible(False)
def inputs(axs, th, fs, D, tm):
    a, b, c = axs
    a.plot(tm, D["P"], color=ORANGE, lw=0.9); a.set_ylabel("Power\n(W)", fontsize=fs - 2); a.set_ylim(0, 640); a.set_yticks([0, 300, 575])
    fanstrip(b, th, fs, tm, D["N"], GREEN, "GPU fans", gpct, grpm, [40, 100], (10, 110))
    fanstrip(c, th, fs, tm, D["C"], TEAL, "Case fans", cpct, crpm, [25, 100], (0, 110))
    for x in (a, b): x.tick_params(labelbottom=False)
def rc(phone): plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Arial", "DejaVu Sans"], "font.size": 13 if phone else 11})

yc2, X2 = dm.core_pred(p2, train, 2); yc1 = dm.core_pred(p1, train, 1)[0]
def figA(theme, phone):
    th = THEMES[theme]; fs = 13 if phone else 11; rc(phone)
    fig, ax = plt.subplots(4, 1, figsize=(5, 9.4) if phone else (9, 7.2), sharex=True, gridspec_kw=dict(height_ratios=[3, 0.9, 0.9, 0.9]))
    fig.patch.set_facecolor(th["bg"]); D = train; tm = D["t"] / 60
    for a in ax: style(a, th, fs)
    ax[0].plot(tm, D["core"], color=th["meas"], lw=0.9, label="measured")
    ax[0].plot(tm, yc2, color=RED, lw=1.0, label=f"thermal mass + die resistance, RMSE {rm(yc2, D['core']):.2f} K")
    ax[0].plot(tm, yc1, color=BLUE, lw=0.8, alpha=0.8, label=f"one node, RMSE {rm(yc1, D['core']):.1f} K")
    ax[0].set_ylabel("Core (°C)"); ax[0].legend(fontsize=fs - 2, frameon=False, labelcolor=th["fg"], loc="upper right")
    inputs(ax[1:], th, fs, D, tm); ax[3].set_xlabel("Minutes from the start of the second run")
    fig.tight_layout(); fig.align_ylabels(ax)
    save(fig, th, f"gpu-map-2026-10-21-dyn-train{'-phone' if phone else ''}-{theme}")

TP = [(D, *dm.core_pred(p2, D, 2)) for D in tests]
def figB(theme, phone):
    th = THEMES[theme]; fs = 13 if phone else 11; rc(phone)
    fig = plt.figure(figsize=(5, 25) if phone else (11, 11.5)); fig.patch.set_facecolor(th["bg"])
    gs = GridSpec(4, 1, figure=fig, hspace=0.32) if phone else GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.32)
    for i, (D, yc, X) in enumerate(TP):
        sub = GridSpecFromSubplotSpec(4, 1, subplot_spec=gs[i], height_ratios=[3, 0.8, 0.8, 0.8], hspace=0.12)
        ax = fig.add_subplot(sub[0]); ins = [fig.add_subplot(sub[j], sharex=ax) for j in (1, 2, 3)]
        for a in [ax, *ins]: style(a, th, fs)
        tm = D["t"] / 60; ym = dm.mem_sim(pm, D, X)
        ax.plot(tm, D["mem"], color=th["dim"], lw=0.9); ax.plot(tm, ym, color=PURPLE, lw=1.0)
        ax.plot(tm, D["core"], color=th["meas"], lw=0.9); ax.plot(tm, yc, color=RED, lw=1.0)
        ax.set_title(f"{LABEL[D['name']]}" + ("\n" if phone else ": ") + f"core RMSE {rm(yc, D['core']):.2f} K, memory {rm(ym, D['mem']):.1f} K", loc="left", fontsize=fs - 1, color=th["fg"])
        ax.set_ylabel("°C"); ax.tick_params(labelbottom=False)
        inputs(ins, th, fs, D, tm); ins[-1].set_xlabel("Minutes from the start of the log")
        fig.align_ylabels([ax, *ins])
    h = [plt.Line2D([], [], c=th["meas"], lw=1.4), plt.Line2D([], [], c=RED, lw=1.4), plt.Line2D([], [], c=th["dim"], lw=1.4), plt.Line2D([], [], c=PURPLE, lw=1.4)]
    l = ["core, measured", "core, model", "memory, measured", "memory, model"]
    fig.legend(h, l, loc="lower center", ncol=2 if phone else 4, fontsize=fs - 2, frameon=False, labelcolor=th["fg"])
    fig.subplots_adjust(left=0.16 if phone else 0.08, right=0.84 if phone else 0.93, top=0.98 if phone else 0.96, bottom=0.05 if phone else 0.08)
    save(fig, th, f"gpu-map-2026-10-21-dyn-test{'-phone' if phone else ''}-{theme}")
for t in THEMES:
    for ph in (False, True): figA(t, ph); figB(t, ph)
