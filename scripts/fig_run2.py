"""Run 2 (2026-10-21) figure: panel per case speed, x = GPU fans % (+ rpm on top), core solid / memory dashed, colour = power limit.
Style follows fig_export.py (THEMES, sans, no titles, dpi 200). Usage: fig_run2.py final.csv outdir"""
import csv, sys
from pathlib import Path
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

src, out = Path(sys.argv[1]), Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
rows = list(csv.DictReader(open(src)))
THEMES = {"light": dict(bg="#ffffff", fg="#1d1d1f", grid="#d9d9de", dim="#86868b"),
          "dark": dict(bg="#141414", fg="#f5f5f7", grid="#3a3a3c", dim="#98989d")}
PL = {100: ("#ff453a", 575), 90: ("#ff9f0a", 518), 80: ("#30d158", 460), 70: ("#0a84ff", 402)}
CASES = [("1000", 1000), ("1500", 1500), ("2000", 2000), ("3000", 2920)]
# measured GPU fan rpm per duty (mean over all 112 points)
rpm = {}
for r in rows: rpm.setdefault(int(r["gpu_pct"]), []).append(float(r["cardA_fan_rpm"]))
P = sorted(rpm); R = [np.mean(rpm[p]) for p in P]
def p2r(v): return np.interp(v, P, R, left=None, right=None) if False else np.interp(v, P, R) + (np.asarray(v) - np.clip(v, P[0], P[-1])) * (R[-1] - R[0]) / (P[-1] - P[0])
def r2p(v): return np.interp(v, R, P) + (np.asarray(v) - np.clip(v, R[0], R[-1])) * (P[-1] - P[0]) / (R[-1] - R[0])
def flag(r):
    s = r["source"]
    if "UNSETTLED" in s: return "unsettled"
    if r["case_rpm_target"] == "3000" and r["gpu_pct"] == "100" and r["pl_pct"] == "100": return "outlier"
    return ""

def style(fig, ax, th, fs):
    ax.set_facecolor(th["bg"])
    for s in ax.spines.values(): s.set_visible(False)
    ax.tick_params(colors=th["fg"], labelsize=fs - 1, length=0); ax.xaxis.label.set_color(th["fg"]); ax.yaxis.label.set_color(th["fg"])
    ax.grid(color=th["grid"], lw=0.6); ax.set_axisbelow(True)

def fig(theme, phone):
    th = THEMES[theme]; fs = 13 if phone else 11
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Arial", "DejaVu Sans"], "font.size": fs})
    f, axs = plt.subplots(4, 1, figsize=(5, 13.2), sharey=True) if phone else plt.subplots(2, 2, figsize=(8, 6.6), sharey=True)
    f.patch.set_facecolor(th["bg"]); axs = np.ravel(axs)
    for i, (ax, (tgt, lab)) in enumerate(zip(axs, CASES)):
        style(f, ax, th, fs)
        for pl, (col, w) in PL.items():
            s = sorted([r for r in rows if r["case_rpm_target"] == tgt and int(r["pl_pct"]) == pl], key=lambda r: int(r["gpu_pct"]))
            for key, ls, mk in (("core_c_max", "-", "o"), ("mem_c_max", "--", "s")):
                ok = [r for r in s if flag(r) != "outlier"]
                ax.plot([int(r["gpu_pct"]) for r in ok], [float(r[key]) for r in ok], ls, c=col, lw=1.6, zorder=3)
                fil = [r for r in ok if not flag(r)]; hol = [r for r in s if flag(r)]
                ax.scatter([int(r["gpu_pct"]) for r in fil], [float(r[key]) for r in fil], marker=mk, s=18 if not phone else 22, color=col, zorder=4)
                if hol: ax.scatter([int(r["gpu_pct"]) for r in hol], [float(r[key]) for r in hol], marker=mk, s=30 if not phone else 34, facecolors=th["bg"], edgecolors=col, linewidths=1.3, zorder=5)
        ax.text(0.97, 0.95, f"case fans {lab} rpm" + (" (max)" if lab == 2920 else ""), transform=ax.transAxes, va="top", ha="right", color=th["fg"], fontsize=fs - 1,
                bbox=dict(boxstyle="round,pad=0.3", fc=th["bg"], ec=th["grid"]))
        ax.set_xlim(36, 104); ax.set_ylim(44, 96); ax.set_yticks(range(50, 91, 10)); ax.set_xticks(range(40, 101, 10))
        top = ax.secondary_xaxis("top", functions=(p2r, r2p)); top.set_xticks([1300, 1900, 2400, 3000])
        top.tick_params(colors=th["fg"], labelsize=fs - 2, length=0)
        for sp in top.spines.values(): sp.set_visible(False)
        if phone or i < 2: top.set_xlabel("GPU fans (rpm)", color=th["fg"], fontsize=fs - 1)
        if phone or i >= 2: ax.set_xlabel("GPU fans (%)")
        if phone or i % 2 == 0: ax.set_ylabel("Temperature (°C)")
    h = [plt.Line2D([], [], c=PL[p][0], lw=2.2) for p in PL]; l = [f"power limit {p} % ({PL[p][1]} W)" for p in PL]
    h += [plt.Line2D([], [], c=th["fg"], lw=1.6, marker="o", ms=4), plt.Line2D([], [], c=th["fg"], lw=1.6, ls="--", marker="s", ms=4),
          plt.Line2D([], [], ls="none", marker="o", mfc=th["bg"], mec=th["dim"], ms=6)]
    l += ["core", "memory", "not settled or doubtful"]
    f.legend(h, l, loc="lower center", ncol=2 if phone else 4, columnspacing=1.0, handlelength=1.8, fontsize=fs - 2, frameon=False, labelcolor=th["fg"])
    f.tight_layout(rect=(0, 0.085 if phone else 0.11, 1, 1))
    name = f"gpu-map-2026-10-21-run2-case-gpu-pl{'-phone' if phone else ''}-{theme}"
    f.savefig(out / f"{name}.png", dpi=200, facecolor=th["bg"]); plt.close(f)
    im = Image.open(out / f"{name}.png").convert("RGB"); im.save(out / f"{name}.webp", "WEBP", quality=86, method=6)
    print(name, im.size)

for t in THEMES:
    for ph in (False, True): fig(t, ph)
