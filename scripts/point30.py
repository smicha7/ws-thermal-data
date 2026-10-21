"""Average of the last 30 s + trend (°C/min, linear fit) from raw.csv (hold/fast runs). Usage: point30.py raw.csv [ts]"""
import csv, sys
rows = list(csv.DictReader(open(sys.argv[1])))
end = int(sys.argv[2]) if len(sys.argv) > 2 else int(rows[-1]['t'])
w = [r for r in rows if end - 30 < int(r['t']) <= end]
def col(k): return [(int(r['t']), float(r[k])) for r in w if r.get(k)]
def mean(k): v = col(k); return sum(x for _, x in v) / len(v) if v else None
def slope(k):
    v = col(k)
    if len(v) < 5: return None
    mt = sum(t for t, _ in v) / len(v); mx = sum(x for _, x in v) / len(v)
    return 60 * sum((t - mt) * (x - mx) for t, x in v) / sum((t - mt) ** 2 for t, _ in v)
fans = [[float(x) for x in r['gpu_rpm'].split('|') if x] for r in w]
print(f"n={len(w)} s, end ts {end}")
for k in ('core_c', 'mem_c', 'hot_c', 'intake_c', 'power_w', 'clock_mhz', 'util_pct', 'gpu_pct', 'case_rpm', 'rad_rpm'):
    m, s = mean(k), slope(k)
    if m is not None: print(f"{k:10} {m:8.1f}" + (f"   trend {s:+.2f}/min" if s is not None and k.endswith('_c') else ""))
if fans and fans[0]: print("gpu fans rpm", [round(sum(f[i] for f in fans if len(f) > i) / len(fans)) for i in range(len(fans[0]))])
