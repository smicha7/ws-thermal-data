"""Core and memory vs CASE fans, one panel per GPU-fan level (Seb 2026-10-21; inverse of fans_core_mem_all.py). v2d grid, 575 W.
Usage: case_core_mem_all.py <v2d dir> <out.png>"""
import csv, sys
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
d, out = sys.argv[1], sys.argv[2]
P = [r for r in csv.DictReader(open(f"{d}/points.csv")) if r["bridge"] == "0" and r["too_hot"] == "0" and r["fc_pct"] != "72"]   # 72 % = punkt referencyjny
lv = {}
for r in P: lv.setdefault(int(r["fg_pct"]), []).append(r)
keys = sorted(lv, reverse=True)
PCT = [15, 36, 58, 79, 100]; RPM = [654, 1286, 1889, 2418, 2921]   # zmierzone poziomy obudowy (nieliniowe)
fig, axs = plt.subplots(len(keys), 1, figsize=(10, 5.2 * len(keys)))
for ax, k in zip(axs, keys):
    rr = sorted(lv[k], key=lambda r: float(r["case_rpm"]))
    x = [float(r["case_rpm"]) for r in rr]; rg = np.mean([float(r["gpu_rpm_mean"]) for r in rr])
    for key, name, col in (("core_c", "core", "tab:blue"), ("mem_c", "memory", "tab:orange")):
        y = [float(r[key]) for r in rr]
        ax.plot(x, y, "-o", ms=6, lw=2, color=col, label=name)
        for xi, yi in zip(x, y): ax.annotate(f"{yi:.1f}", (xi, yi), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=9, color=col)
    ax.axhline(90, color="tab:blue", ls="--", lw=0.9); ax.text(3050, 90.4, "core max operating 90 °C", color="tab:blue", fontsize=9, ha="right")
    ax.axhline(95, color="tab:red", ls="--", lw=0.9); ax.text(3050, 95.4, "memory limit 95 °C", color="tab:red", fontsize=9, ha="right")
    ax.set_ylim(55, 98); ax.set_xlim(500, 3070); ax.set_ylabel("Temperature °C"); ax.grid(alpha=0.3)
    ax.set_title(f"GPU FANS {k} %  (~{rg:.0f} rpm)   ·   {len(rr)} points", fontsize=13, fontweight="bold", loc="left")
    ax.legend(fontsize=9, loc="lower left")
    sec = ax.secondary_xaxis("top", functions=(lambda r: np.interp(r, RPM, PCT), lambda p: np.interp(p, PCT, RPM))); sec.set_xticks(PCT); sec.set_xlabel("case fan duty % (measured levels)")
    ax.set_xlabel("Case fan speed, rpm (mean of 4 fans)")
fig.suptitle("RTX 5090 at 575 W, open case, intake ~19 °C — core and memory vs CASE fans, per GPU-fan level", fontsize=13, y=0.997)
fig.tight_layout(); fig.savefig(out, dpi=130); print("ok")
