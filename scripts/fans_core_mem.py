"""Core and memory vs GPU fan speed at one case-fan level (Seb 2026-10-21). v2d grid, 575 W, 60 s means.
Usage: fans_core_mem.py <v2d dir> <out.png> <case rpm target> [<case rpm target> ...]  — nearest measured level is used."""
import csv, sys
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
d, out, targets = sys.argv[1], sys.argv[2], [float(x) for x in sys.argv[3:]]
P = [r for r in csv.DictReader(open(f"{d}/points.csv")) if r["bridge"] == "0" and r["too_hot"] == "0"]
levels = {}
for r in P: levels.setdefault(r["fc_pct"], []).append(r)
levels = {k: v for k, v in levels.items() if len(v) >= 4}   # 72 % = 3 powtórzenia punktu referencyjnego, nie wiersz
fig, ax = plt.subplots(figsize=(9, 6.5))
styles = ["-", "--", ":"]
for i, t in enumerate(targets):
    k = min(levels, key=lambda k: abs(np.mean([float(r["case_rpm"]) for r in levels[k]]) - t))
    rr = sorted(levels[k], key=lambda r: float(r["gpu_rpm_mean"]))
    x = [float(r["gpu_rpm_mean"]) for r in rr]; rc = np.mean([float(r["case_rpm"]) for r in rr])
    for key, name, col in (("core_c", "core", "tab:blue"), ("mem_c", "memory", "tab:orange")):
        y = [float(r[key]) for r in rr]
        ax.plot(x, y, styles[i % 3], marker="o", ms=5, color=col, label=f"{name} · case fans ~{rc:.0f} rpm ({k} %)")
        if len(targets) == 1:
            for xi, yi in zip(x, y): ax.annotate(f"{yi:.1f}", (xi, yi), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=7, color=col)
ax.axhline(90, color="tab:blue", ls="--", lw=0.9); ax.text(3050, 90.3, "core max operating 90 °C", color="tab:blue", fontsize=8, ha="right")
ax.axhline(95, color="tab:red", ls="--", lw=0.9); ax.text(3050, 95.3, "memory limit 95 °C", color="tab:red", fontsize=8, ha="right")
ax.set_ylim(55, 98); ax.set_xlabel("GPU fan speed, rpm (mean of 3 fans)"); ax.set_ylabel("Temperature °C")
sec = ax.secondary_xaxis("top", functions=(lambda r: (r - 180) / 28.33, lambda p: p * 28.33 + 180)); sec.set_xlabel("GPU fan duty %")
ax.set_title("RTX 5090 at 575 W, open case, intake ~19 °C — core and memory vs GPU fans", pad=12)
ax.grid(alpha=0.3); ax.legend(fontsize=8, loc="lower left")
fig.tight_layout(); fig.savefig(out, dpi=150); print("ok")
