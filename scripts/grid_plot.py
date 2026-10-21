"""rpmgrid (fixed-time) results: one panel per case rpm, core (solid) and memory (dashed) vs card fans, one colour per power limit; % and rpm axes.
Usage: grid_plot.py <grid.csv> <out.png> [table.md] [title]"""
import csv, sys
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
rows = [r for r in csv.DictReader(open(sys.argv[1])) if r["settled"] != "-1"]
def f(r, k):
    try: return float(r[k])
    except (KeyError, ValueError): return None
cases = sorted({int(r["case_rpm_target"]) for r in rows})
pls = sorted({int(r["pl_pct"]) for r in rows}, reverse=True)
col = {100: "tab:red", 90: "tab:orange", 80: "tab:green", 70: "tab:blue"}
fig, axs = plt.subplots(len(cases), 1, figsize=(10, 4.8 * len(cases)), sharex=True, squeeze=False)
for ax, c in zip(axs[:, 0], cases):
    rc = [f(r, "case_rpm") for r in rows if int(r["case_rpm_target"]) == c]
    for pl in pls:
        rr = sorted((r for r in rows if int(r["case_rpm_target"]) == c and int(r["pl_pct"]) == pl), key=lambda r: int(r["gpu_pct"]))
        if not rr: continue
        x = [int(r["gpu_pct"]) for r in rr]; w = sum(f(r, "power_w_sum") or 0 for r in rr) / len(rr)
        ax.plot(x, [f(r, "core_c_max") for r in rr], "-o", color=col.get(pl, "k"), lw=2, ms=5, label=f"core · PL {pl} % (~{w:.0f} W)")
        ax.plot(x, [f(r, "mem_c_max") for r in rr], "--s", color=col.get(pl, "k"), lw=1.4, ms=4, alpha=0.8, label=f"memory · PL {pl} %")
    ax.axhline(90, color="k", ls=":", lw=0.9); ax.text(100.5, 90.3, "core 90 °C", fontsize=8, ha="right")
    ax.set_ylabel("Temperature °C"); ax.grid(alpha=0.3)
    m = [v for v in rc if v]; ax.set_title(f"CASE FANS target {c} rpm (actual ~{sum(m) / len(m):.0f} rpm)", loc="left", fontweight="bold")
    ax.legend(fontsize=7.5, ncol=2, loc="upper right")
    sec = ax.secondary_xaxis("top", functions=(lambda p: p * 28.33 + 180, lambda r: (r - 180) / 28.33)); sec.set_xlabel("GPU fan speed, rpm (≈ from duty)")
    ax.tick_params(labelbottom=True); ax.set_xlabel("GPU fan duty %")
fig.suptitle(sys.argv[4] if len(sys.argv) > 4 else "RTX 5090 (1 card), mix64 load, open case — core and memory vs card fans, per case speed and power limit (60 s points)", fontsize=11, y=0.997)
fig.tight_layout(); fig.savefig(sys.argv[2], dpi=130)
if len(sys.argv) > 3:
    with open(sys.argv[3], "w") as t:
        t.write("| case rpm (target/actual) | card % | PL % | power W | core °C | memory °C | hot spot °C | air °C | trend core °C/min | settled |\n|---|---|---|---|---|---|---|---|---|---|\n")
        for r in rows:
            t.write(f"| {r['case_rpm_target']}/{f(r,'case_rpm') or 0:.0f} | {r['gpu_pct']} | {r['pl_pct']} | {f(r,'power_w_sum') or 0:.0f} | {f(r,'core_c_max') or 0:.2f} | {f(r,'mem_c_max') or 0:.1f} | {f(r,'hot_c_max') or 0:.2f} | {f(r,'intake_c') or 0:.2f} | {r['slope_core_c_min']} | {r['settled']} |\n")
print("ok")
