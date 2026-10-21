"""Memory − core gap vs GPU fan speed, one line per case-fan level (Seb 2026-10-21). v2d grid, 575 W, 60 s means.
Usage: gap_core_mem.py <v2d dir> <out.png>"""
import csv, sys
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
d, out = sys.argv[1], sys.argv[2]
P = [r for r in csv.DictReader(open(f"{d}/points.csv")) if r["bridge"] == "0" and r["too_hot"] == "0"]
lv = {}
for r in P: lv.setdefault(int(r["fc_pct"]), []).append(r)
fig, ax = plt.subplots(figsize=(9, 6.5)); cmap = plt.get_cmap("viridis")
keys = sorted(k for k in lv if len(lv[k]) >= 4)
for i, k in enumerate(keys):
    rr = sorted(lv[k], key=lambda r: float(r["gpu_rpm_mean"]))
    x = [float(r["gpu_rpm_mean"]) for r in rr]; g = [float(r["mem_c"]) - float(r["core_c"]) for r in rr]
    rc = np.mean([float(r["case_rpm"]) for r in rr]); c = cmap(i / (len(keys) - 1))
    ax.plot(x, g, "-o", color=c, ms=5, label=f"case fans {k} % (~{rc:.0f} rpm)")
    for xi, gi in zip(x, g): ax.annotate(f"{gi:.1f}", (xi, gi), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=6.5, color=c)
ref = lv.get(72, [])
if ref:
    ax.plot([float(r["gpu_rpm_mean"]) for r in ref], [float(r["mem_c"]) - float(r["core_c"]) for r in ref], "kx", ms=8, label="reference point, case 72 % (~2250 rpm), ×3")
all_g = [float(r["mem_c"]) - float(r["core_c"]) for r in P]
ax.axhline(np.mean(all_g), color="grey", ls=":", lw=1); ax.text(1290, np.mean(all_g) + 0.1, f"mean {np.mean(all_g):.1f} °C", color="grey", fontsize=8)
ax.set_xlabel("GPU fan speed, rpm (mean of 3 fans)"); ax.set_ylabel("Memory − core, °C")
sec = ax.secondary_xaxis("top", functions=(lambda r: (r - 180) / 28.33, lambda p: p * 28.33 + 180)); sec.set_xlabel("GPU fan duty %")
ax.set_title("RTX 5090 at 575 W, open case, intake ~19 °C — how much hotter memory runs than the core", pad=12)
ax.grid(alpha=0.3); ax.legend(fontsize=8, loc="upper right")
fig.tight_layout(); fig.savefig(out, dpi=150); print(f"{min(all_g):.1f}..{max(all_g):.1f} mean {np.mean(all_g):.2f}")
