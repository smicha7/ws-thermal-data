"""grid1c (today, 60 s points) vs night v2d (steady / fitted T∞) at PL 100 %: same card %, nearest case rpm (≤ 300 rpm apart).
Usage: compare_v2d.py <grid.csv> <v2d points.csv> <out.png> <table.md>"""
import csv, sys
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
g = [r for r in csv.DictReader(open(sys.argv[1])) if r["settled"] != "-1" and r["pl_pct"] == "100"]
n = [r for r in csv.DictReader(open(sys.argv[2])) if r["bridge"] == "0" and r["too_hot"] == "0"]
F = lambda r, k: float(r[k]) if r.get(k) not in (None, "") else None
pairs = []
for r in g:
    cand = [x for x in n if int(x["fg_pct"]) == int(r["gpu_pct"]) and abs(F(x, "case_rpm") - F(r, "case_rpm")) <= 300]
    if cand: pairs.append((r, min(cand, key=lambda x: abs(F(x, "case_rpm") - F(r, "case_rpm")))))
with open(sys.argv[4], "w") as t:
    t.write("| card % | case rpm today / night | core today / night (Δ) | memory today / night (Δ) | air today / night | today trend core °C/min |\n|---|---|---|---|---|---|\n")
    for r, x in pairs:
        dc, dm = F(r, "core_c_max") - F(x, "core_c"), F(r, "mem_c_max") - F(x, "mem_c")
        flag = " **>1 °C**" if abs(dc) > 1 or abs(dm) > 1 else ""
        t.write(f"| {r['gpu_pct']} | {F(r,'case_rpm'):.0f} / {F(x,'case_rpm'):.0f} | {F(r,'core_c_max'):.2f} / {F(x,'core_c'):.2f} ({dc:+.1f}) | {F(r,'mem_c_max'):.1f} / {F(x,'mem_c'):.1f} ({dm:+.1f}){flag} | {F(r,'intake_c'):.2f} / {F(x,'intake_c'):.2f} | {r['slope_core_c_min']} |\n")
cases = sorted({int(r["case_rpm_target"]) for r in g})
fig, axs = plt.subplots(len(cases), 1, figsize=(10, 4.4 * len(cases)), sharex=True, squeeze=False)
for ax, c in zip(axs[:, 0], cases):
    rr = sorted((r for r in g if int(r["case_rpm_target"]) == c), key=lambda r: int(r["gpu_pct"]))
    ax.plot([int(r["gpu_pct"]) for r in rr], [F(r, "core_c_max") for r in rr], "-o", color="tab:red", label="core today (60 s)")
    ax.plot([int(r["gpu_pct"]) for r in rr], [F(r, "mem_c_max") for r in rr], "--s", color="tab:red", alpha=0.7, label="memory today (60 s)")
    pp = [(r, x) for r, x in pairs if int(r["case_rpm_target"]) == c]
    ax.plot([int(x["fg_pct"]) for _, x in pp], [F(x, "core_c") for _, x in pp], "D", ms=8, mfc="none", color="k", label="core night v2d (steady)")
    ax.plot([int(x["fg_pct"]) for _, x in pp], [F(x, "mem_c") for _, x in pp], "^", ms=8, mfc="none", color="gray", label="memory night v2d (steady)")
    nr = sorted({round(F(x, "case_rpm")) for _, x in pp})
    ax.set_title(f"PL 100 % · case target {c} rpm · night points at {nr} rpm", loc="left", fontweight="bold"); ax.grid(alpha=0.3); ax.set_ylabel("°C"); ax.legend(fontsize=8)
    sec = ax.secondary_xaxis("top", functions=(lambda p: p * 28.33 + 180, lambda q: (q - 180) / 28.33)); sec.set_xlabel("GPU fan rpm (≈)")
    ax.tick_params(labelbottom=True); ax.set_xlabel("GPU fan duty %")
fig.tight_layout(); fig.savefig(sys.argv[3], dpi=130); print(len(pairs), "pairs")
