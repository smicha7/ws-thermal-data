"""Core and memory vs GPU fans, one panel per case-fan level (Seb 2026-10-21; same style as fans-core-mem-case1900.png). v2d grid, 575 W.
Usage: fans_core_mem_all.py <v2d dir> <out.png>"""
import csv, sys
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
d, out = sys.argv[1], sys.argv[2]
P = [r for r in csv.DictReader(open(f"{d}/points.csv")) if r["bridge"] == "0" and r["too_hot"] == "0"]
lv = {}
for r in P: lv.setdefault(int(r["fc_pct"]), []).append(r)
keys = sorted(k for k in lv if len(lv[k]) >= 4)
fig, axs = plt.subplots(len(keys), 1, figsize=(10, 5.2 * len(keys)), sharex=True)
for ax, k in zip(axs, keys):
    rr = sorted(lv[k], key=lambda r: float(r["gpu_rpm_mean"]))
    x = [float(r["gpu_rpm_mean"]) for r in rr]; rc = np.mean([float(r["case_rpm"]) for r in rr])
    for key, name, col in (("core_c", "core", "tab:blue"), ("mem_c", "memory", "tab:orange")):
        y = [float(r[key]) for r in rr]
        ax.plot(x, y, "-o", ms=6, lw=2, color=col, label=name)
        for xi, yi in zip(x, y): ax.annotate(f"{yi:.1f}", (xi, yi), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=9, color=col)
    ax.axhline(90, color="tab:blue", ls="--", lw=0.9); ax.text(3060, 90.4, "core max operating 90 °C", color="tab:blue", fontsize=9, ha="right")
    ax.axhline(95, color="tab:red", ls="--", lw=0.9); ax.text(3060, 95.4, "memory limit 95 °C", color="tab:red", fontsize=9, ha="right")
    ax.set_ylim(55, 98); ax.set_xlim(1200, 3080); ax.set_ylabel("Temperature °C"); ax.grid(alpha=0.3)
    ax.set_title(f"CASE FANS {k} %  (~{rc:.0f} rpm)", fontsize=13, fontweight="bold", loc="left")
    ax.legend(fontsize=9, loc="lower left")
    sec = ax.secondary_xaxis("top", functions=(lambda r: (r - 180) / 28.33, lambda p: p * 28.33 + 180)); sec.set_xlabel("GPU fan duty %")
    ax.tick_params(labelbottom=True); ax.set_xlabel("GPU fan speed, rpm (mean of 3 fans)")
fig.suptitle("RTX 5090 at 575 W, open case, intake ~19 °C — core and memory vs GPU fans, per case-fan level", fontsize=13, y=0.995)
fig.tight_layout(); fig.savefig(out, dpi=130); print("ok")
