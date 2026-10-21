"""Core vs memory on the v2d grid (34 cells, 575 W, 60 s means; Seb 2026-10-21). Limits: core 90 max / 93 slowdown / 96 shutdown, memory working limit 100 (Seb 2026-10-21, derived: core 90 + max gap 8.5; no official GDDR7 junction limit; first night used 88).
Usage: core_vs_mem.py <v2d dir> <out dir>"""
import csv, json, sys
from pathlib import Path
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
d, out = Path(sys.argv[1]), Path(sys.argv[2])
P = [r for r in csv.DictReader(open(d / "points.csv")) if r["bridge"] == "0" and r["too_hot"] == "0"]
F = {(r["fg_pct"], r["fc_pct"]): r for r in csv.DictReader(open(d / "fits.csv"))}
f = lambda r, k: float(r[k])
core = np.array([f(r, "core_c") for r in P]); mem = np.array([f(r, "mem_c") for r in P])
rg = np.array([f(r, "gpu_rpm_mean") for r in P]) / 1000; rc = np.array([f(r, "case_rpm") for r in P]) / 1000
k, b = np.polyfit(core, mem, 1); gap = mem - core
A = np.column_stack([np.ones_like(rg), rg, rc]); sc = np.linalg.lstsq(A, core, rcond=None)[0]; sm = np.linalg.lstsq(A, mem, rcond=None)[0]
rows = []
for r, c, m in zip(P, core, mem):
    mc, mm = 90 - c, 100 - m   # Seb 2026-10-21: rdzeń ≤ 90 (max operating), pamięć ≤ 95
    rows.append({"fg_pct": r["fg_pct"], "fc_pct": r["fc_pct"], "gpu_rpm": round(f(r, "gpu_rpm_mean")), "case_rpm": round(f(r, "case_rpm")), "core_c": c, "mem_c": m,
                 "margin_core_to_90": round(mc, 1), "margin_mem_to_100": round(mm, 1), "binds_first": "memory (100)" if mm < mc else "core (90)"})
with open(out / "core-vs-mem-binding.csv", "w") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
summ = {"dataset": "v2d grid, 34 cells, 575 W, 60 s means (bridge=0)", "corr": float(np.corrcoef(core, mem)[0, 1]), "mem_vs_core": {"slope": float(k), "intercept": float(b)},
        "gap_c": {"min": float(gap.min()), "max": float(gap.max()), "mean": float(gap.mean())},
        "per_1000rpm": {"gpu_fans": {"core": float(sc[1]), "mem": float(sm[1])}, "case_fans": {"core": float(sc[2]), "mem": float(sm[2])}},
        "binds_first": {"memory": sum(r["binds_first"].startswith("memory") for r in rows), "core": sum(r["binds_first"].startswith("core") for r in rows)},
        "margin_difference_c": {"min": float(min(r["margin_core_to_90"] - r["margin_mem_to_100"] for r in rows)), "max": float(max(r["margin_core_to_90"] - r["margin_mem_to_100"] for r in rows)),
                                "mean": float(np.mean([r["margin_core_to_90"] - r["margin_mem_to_100"] for r in rows]))},
        "core_when_mem_100_c_extrapolated": float((100 - b) / k), "note": "extrapolated from the fit; measured memory range 67–81 °C"}
json.dump(summ, open(out / "core-vs-mem.json", "w"), indent=1)
fig, ax = plt.subplots(figsize=(7, 6))
s = ax.scatter(core, mem, c=rg * 1000, cmap="viridis", s=40, edgecolors="k", zorder=3); cb = fig.colorbar(s, label="GPU fans (rpm)")
xs = np.linspace(50, 100, 10); ax.plot(xs, k * xs + b, c="gray", lw=1, label=f"mem ≈ {k:.2f}·core + {b:.1f} (r = {summ['corr']:.3f})")
for x, ls, lw, lab in ((90, "-", 1.5, "core 90 °C max operating"), (93, "--", 1.5, "core 93 °C slowdown"), (96, "-", 3, "core 96 °C shutdown")): ax.axvline(x, c="#d13438", ls=ls, lw=lw, label=lab)
ax.axhline(100, c="#d13438", ls="--", lw=1.5, label="memory working limit 100 °C (derived)"); pass
ax.plot([50, 100], [55, 105], c="#8e8e93", ls=":", lw=1, label="where both margins are equal (mem = core + 5)")
ax.set_xlim(55, 98); ax.set_ylim(60, 98); ax.set_xlabel("Core (°C)"); ax.set_ylabel("Memory (°C)"); ax.legend(fontsize=8, loc="upper left"); ax.grid(alpha=0.3)
for sp in ax.spines.values(): sp.set_visible(False)
fig.tight_layout(); fig.savefig(out / "core-vs-mem.png", dpi=150); plt.close(fig)
print(json.dumps(summ, indent=1))
