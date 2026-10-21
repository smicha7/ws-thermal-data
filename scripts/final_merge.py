"""Final grid1c table (Seb 2026-10-21): card-40 % points at case 1500/2000/3000 replaced by the settled repeat grid1d; PL 100 points
replaced by night v2d steady values (same card %, nearest case ≤ 300 rpm) where available; today's 60 s PL 100 kept but marked unsettled.
Usage: final_merge.py <grid1c.csv> <grid1d.csv> <v2d points.csv> <out merged.csv> <out table.md>"""
import csv, sys
c = list(csv.DictReader(open(sys.argv[1]))); d = list(csv.DictReader(open(sys.argv[2]))); n = [r for r in csv.DictReader(open(sys.argv[3])) if r["bridge"] == "0" and r["too_hot"] == "0"]
F = lambda r, k: float(r[k]) if r.get(k) not in (None, "") else None
key = lambda r: (r["case_rpm_target"], r["gpu_pct"], r["pl_pct"])
rep = {key(r): r for r in d}
out = []
for r in c:
    src = "grid1c 60 s"
    if key(r) in rep: old = r; r = dict(rep[key(r)]); src = f"grid1d (settled first){'' if r['pl_pct'] == '100' else ', 75 s'}; old 60 s {F(old,'core_c_max'):.1f}/{F(old,'mem_c_max'):.1f}"
    elif int(r["seconds"]) >= 300: src = f"grid1c after {r['seconds']} s warm-up (settled)"
    elif r["pl_pct"] == "100":
        cand = [x for x in n if int(x["fg_pct"]) == int(r["gpu_pct"]) and abs(F(x, "case_rpm") - F(r, "case_rpm")) <= 300]
        if cand:
            x = min(cand, key=lambda x: abs(F(x, "case_rpm") - F(r, "case_rpm")))
            src = f"night v2d steady @ {F(x,'case_rpm'):.0f} rpm; today 60 s {F(r,'core_c_max'):.1f}/{F(r,'mem_c_max'):.1f} (unsettled)"
            r = dict(r); r["core_c_max"], r["mem_c_max"], r["hot_c_max"] = x["core_c"], x["mem_c"], x["hot_c"]
        else: src = "grid1c 60 s (UNSETTLED, no night point)"
    r = dict(r); r["source"] = src; out.append(r)
fields = list(out[0].keys())
with open(sys.argv[4], "w", newline="") as f: w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore"); w.writeheader(); w.writerows(out)
with open(sys.argv[5], "w") as t:
    t.write("| case rpm | card % | PL % | power W | core °C | memory °C | hot spot °C | source |\n|---|---|---|---|---|---|---|---|\n")
    for r in out:
        t.write(f"| {r['case_rpm_target']} | {r['gpu_pct']} | {r['pl_pct']} | {F(r,'power_w_sum') or 0:.0f} | {F(r,'core_c_max'):.1f} | {F(r,'mem_c_max'):.1f} | {(F(r,'hot_c_max') or 0):.1f} | {r['source']} |\n")
print(len(out), "rows")
