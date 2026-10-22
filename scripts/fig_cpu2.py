"""Article figure for cpu2 (ws298, 22 Oct 2026): radiator fan sweep under full CPU load. House style, light/dark/phone.
Panels: Tctl and CCD temperatures (°C, 10 s rolling mean over 1 Hz data), radiator fans (rpm and %), package power (W)."""
import sys
from pathlib import Path
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
s = pd.read_csv(Path(__file__).resolve().parent / "data/cpu2-2026-10-22/cpu2/sweep.csv"); s["t"] = (s.ts - s.ts.iloc[0]) / 60
q = s.dropna(subset=["rad_pct"]).groupby(s.rad_pct.round(0)).rad_rpm.median().sort_index(); q = q[q.index >= 30]
P_, R_ = list(q.index.astype(float)), list(np.maximum.accumulate(q.values))
lin = lambda xs, ys: (lambda v: np.interp(v, xs, ys))
r2p, p2r = lin(R_, P_), lin(P_, R_)
TH = {"light": dict(bg="#ffffff", fg="#1d1d1f", grid="#d9d9de", dim="#86868b"), "dark": dict(bg="#141414", fg="#f5f5f7", grid="#3a3a3c", dim="#98989d")}
def style(ax, th, fs):
    ax.set_facecolor(th["bg"])
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.tick_params(colors=th["fg"], labelsize=fs - 2, length=0); ax.xaxis.label.set_color(th["fg"]); ax.yaxis.label.set_color(th["fg"])
    ax.grid(color=th["grid"], lw=0.6); ax.set_axisbelow(True)
def fig(theme, phone):
    th = TH[theme]; fs = 15 if phone else 11
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Arial", "DejaVu Sans"], "font.size": fs})
    F, ax = plt.subplots(3, 1, figsize=(5, 9) if phone else (9, 6.6), sharex=True, gridspec_kw=dict(height_ratios=[2.2, 1, 0.8]))
    F.patch.set_facecolor(th["bg"])
    for a in ax: style(a, th, fs)
    for c, col, lab in (("tctl_c", "#ff453a", "Tctl"), ("ccd1_c", "#ff9f0a", "CCD 1"), ("ccd2_c", "#bf5af2", "CCD 2")):
        ax[0].plot(s.t, s[c].rolling(10, min_periods=1).mean(), color=col, lw=1.3, label=lab)
    ax[0].set_ylabel("°C"); ax[0].legend(fontsize=fs - 2, frameon=False, labelcolor=th["fg"], ncol=3, loc="lower right")
    ax[1].plot(s.t, s.rad_rpm, color="#64d2ff", lw=1.1, label="measured"); ax[1].plot(s.t, s.target_rpm, color=th["fg"], lw=1.0, ls="--", label="target")
    ax[1].set_ylabel("Radiator\nfans (rpm)" if phone else "Radiator fans (rpm)", fontsize=fs - 2); ax[1].set_ylim(1200, 2900)
    ax[1].legend(fontsize=fs - 3, frameon=False, labelcolor=th["fg"], loc="upper right")
    r = ax[1].secondary_yaxis("right", functions=(r2p, p2r)); r.set_yticks([40, 60, 80, 100]); r.set_ylabel("%", color=th["fg"], fontsize=fs - 2)
    r.tick_params(colors=th["fg"], labelsize=fs - 3, length=0)
    for sp in r.spines.values(): sp.set_visible(False)
    ax[2].plot(s.t, s.pkg_w, color="#30d158", lw=1.2); ax[2].set_ylabel("Package\n(W)", fontsize=fs - 2); ax[2].set_ylim(0, 230); ax[2].set_yticks([0, 100, 200])
    ax[2].set_xlabel("Minutes")
    for a in ax:
        for x in (s.t[s.stage == 1].min(), s.t[s.stage == 2].min()): a.axvline(x, color=th["dim"], lw=0.8, ls=":")
    F.tight_layout(); F.align_ylabels(ax)
    name = f"gpu-map-cpu2{'-phone' if phone else ''}-{theme}"
    F.savefig(out / f"{name}.png", dpi=200, facecolor=th["bg"]); plt.close(F)
    im = Image.open(out / f"{name}.png").convert("RGB"); im.save(out / f"{name}.webp", "WEBP", quality=86, method=6); print(name, im.size)
for t in TH:
    for ph in (False, True): fig(t, ph)
