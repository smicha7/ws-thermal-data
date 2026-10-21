"""Article figures for the dynamic core model (fig_export.py style, light/dark/phone, webp).
Uses dyn_model.py functions and the fitted parameters in results-2026-10-21/dyn-model.json (no refit).
A) training run grid1c: core measured vs simulated (2-node and 1-node), GPU fans % + rpm, board power.
B) held-out runs: core and memory measured vs simulated, free run from the first sample.
Usage: fig_dyn.py outdir"""
import json, os, sys
from pathlib import Path
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dyn_model as dm

out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
J = json.load(open(os.path.join(dm.OUT, "dyn-model.json")))
p2, p1, pm = J["M2-pow"]["params"], J["M1-pow"]["params"], J["mem"]["params"]
train = dm.load("grid1c")
tests = [dm.load("log-1"), dm.load("grid1d"), dm.load("hold"), dm.load("night-v2d", dm.NIGHT)]
LABEL = {"log-1": "Manual series by hand", "grid1d": "Repeat of the 40 % points", "hold": "Morning hold series", "night-v2d": "First-run night grid"}
pct = lambda r: (np.asarray(r) - 1313) / (3012 - 1313) * 60 + 40
rpm = lambda q: (np.asarray(q) - 40) / 60 * (3012 - 1313) + 1313
THEMES = {"light": dict(bg="#ffffff", fg="#1d1d1f", grid="#d9d9de", dim="#86868b", meas="#1d1d1f"),
          "dark": dict(bg="#141414", fg="#f5f5f7", grid="#3a3a3c", dim="#98989d", meas="#f5f5f7")}
RED, BLUE, PURPLE, GREEN, ORANGE = "#ff453a", "#0a84ff", "#bf5af2", "#30d158", "#ff9f0a"
rm = lambda a, b: float(np.sqrt(np.mean((np.asarray(a) - b) ** 2)))

def style(ax, th, fs):
    ax.set_facecolor(th["bg"])
    for s in ax.spines.values(): s.set_visible(False)
    ax.tick_params(colors=th["fg"], labelsize=fs - 1, length=0); ax.xaxis.label.set_color(th["fg"]); ax.yaxis.label.set_color(th["fg"])
    ax.grid(color=th["grid"], lw=0.6); ax.set_axisbelow(True)
def leg(ax, th, fs, **kw):
    ax.legend(fontsize=fs - 2, frameon=False, labelcolor=th["fg"], **kw)
def save(fig, th, name):
    fig.savefig(out / f"{name}.png", dpi=200, facecolor=th["bg"]); plt.close(fig)
    im = Image.open(out / f"{name}.png").convert("RGB"); im.save(out / f"{name}.webp", "WEBP", quality=86, method=6); print(name, im.size)
def fanaxis(ax, th, fs, D, tm):
    ax.plot(tm, pct(D["N"]), color=GREEN, lw=1.0, label="GPU fans")
    ax.set_ylabel("GPU fans (%)"); ax.set_ylim(25, 105); ax.set_yticks([40, 70, 100])
    r = ax.secondary_yaxis("right", functions=(rpm, pct)); r.set_yticks([1310, 2160, 3010]); r.set_ylabel("GPU fans (rpm)", color=th["fg"])
    r.tick_params(colors=th["fg"], labelsize=fs - 2, length=0)
    for sp in r.spines.values(): sp.set_visible(False)

yc2, X2 = dm.core_pred(p2, train, 2); yc1 = dm.core_pred(p1, train, 1)[0]
def figA(theme, phone):
    th = THEMES[theme]; fs = 13 if phone else 11
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Arial", "DejaVu Sans"], "font.size": fs})
    fig, ax = plt.subplots(3, 1, figsize=(5, 8.4) if phone else (9, 6.4), sharex=True, gridspec_kw=dict(height_ratios=[3, 1.1, 1.1]))
    fig.patch.set_facecolor(th["bg"]); D = train; tm = D["t"] / 60
    for a in ax: style(a, th, fs)
    ax[0].plot(tm, D["core"], color=th["meas"], lw=0.9, label="measured")
    ax[0].plot(tm, yc2, color=RED, lw=1.0, label=f"two nodes, RMSE {rm(yc2, D['core']):.2f} K")
    ax[0].plot(tm, yc1, color=BLUE, lw=0.8, alpha=0.8, label=f"one node, RMSE {rm(yc1, D['core']):.1f} K")
    ax[0].set_ylabel("Core (°C)"); leg(ax[0], th, fs, loc="upper right", ncol=1)
    ax[1].plot(tm, D["P"], color=ORANGE, lw=0.9); ax[1].set_ylabel("Power (W)"); ax[1].set_ylim(350, 620); ax[1].set_yticks([400, 500, 575])
    fanaxis(ax[2], th, fs, D, tm); ax[2].set_xlabel("Minutes from the start of the second run")
    fig.tight_layout(); fig.align_ylabels(ax)
    save(fig, th, f"gpu-map-2026-10-21-dyn-train{'-phone' if phone else ''}-{theme}")

TP = [(D, *dm.core_pred(p2, D, 2)) for D in tests]
def figB(theme, phone):
    th = THEMES[theme]; fs = 13 if phone else 11
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Arial", "DejaVu Sans"], "font.size": fs})
    fig, axs = plt.subplots(4, 1, figsize=(5, 13.6)) if phone else plt.subplots(2, 2, figsize=(10, 7.2))
    fig.patch.set_facecolor(th["bg"]); axs = np.ravel(axs)
    for ax, (D, yc, X) in zip(axs, TP):
        style(ax, th, fs); tm = D["t"] / 60; ym = dm.mem_sim(pm, D, X)
        ax.plot(tm, D["mem"], color=th["dim"], lw=0.9); ax.plot(tm, ym, color=PURPLE, lw=1.0)
        ax.plot(tm, D["core"], color=th["meas"], lw=0.9); ax.plot(tm, yc, color=RED, lw=1.0)
        ax.text(0.02, 0.97, f"{LABEL[D['name']]}\ncore RMSE {rm(yc, D['core']):.2f} K, memory {rm(ym, D['mem']):.1f} K",
                transform=ax.transAxes, va="top", fontsize=fs - 2, color=th["fg"], bbox=dict(boxstyle="round,pad=0.3", fc=th["bg"], ec=th["grid"]))
        ax.set_ylabel("°C"); ax.set_xlabel("Minutes from the start of the log")
        lo, hi = ax.get_ylim(); ax.set_ylim(lo, hi + (hi - lo) * 0.3)
    h = [plt.Line2D([], [], c=th["meas"], lw=1.4), plt.Line2D([], [], c=RED, lw=1.4), plt.Line2D([], [], c=th["dim"], lw=1.4), plt.Line2D([], [], c=PURPLE, lw=1.4)]
    l = ["core, measured", "core, model", "memory, measured", "memory, model"]
    fig.legend(h, l, loc="lower center", ncol=2 if phone else 4, fontsize=fs - 2, frameon=False, labelcolor=th["fg"])
    fig.tight_layout(rect=(0, 0.05 if phone else 0.06, 1, 1))
    save(fig, th, f"gpu-map-2026-10-21-dyn-test{'-phone' if phone else ''}-{theme}")
for t in THEMES:
    for ph in (False, True): figA(t, ph); figB(t, ph)
