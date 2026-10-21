"""Seb's spoken readings (markers) vs the log: 30 s means ending at each marker. Usage: compare_markers.py <run dir> <markers.txt> [from HH:MM]"""
import csv, datetime, gzip, re, sys, zoneinfo
D, M = sys.argv[1], sys.argv[2]; since = sys.argv[3] if len(sys.argv) > 3 else "00:00"
tz = zoneinfo.ZoneInfo('Europe/Warsaw')
raw = {int(r['t']): r for r in csv.DictReader(open(f"{D}/raw.csv"))}
want = {'nvapi/0/1': 'core01', 'nvml/0/power/limit': 'pl', 'nvml/0/throttle': 'thr', 'aquaero/temperature/sensor_1': 'air'}
lng = {}
import glob
try:
    with gzip.open(glob.glob(f"{D}/long-*.csv.gz")[0], 'rt') as f:
        for r in csv.DictReader(f):
            k = want.get(r['sensor_id'])
            if k and r['value']: lng.setdefault(int(r['ts']), {})[k] = float(r['value'])
except (EOFError, OSError): pass
def mean(vals): v = [x for x in vals if x is not None]; return sum(v) / len(v) if v else None
def f(x, d=1): return "—" if x is None else f"{x:.{d}f}"
TH = {4: 'power', 8: 'HWslow', 32: 'SWtherm', 64: 'HWtherm', 128: 'brake'}
print("| time | Seb said | case rpm | card % | PL W | power W | core (0.01) | mem | hot | air | clock | throttle |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|")
for line in open(M):
    m = re.match(r"(\d{4}-\d\d-\d\d) (\d\d:\d\d:\d\d) (.*)", line.strip())
    if not m or m.group(2) < since or not re.search(r"core|mem", m.group(3)): continue
    ts = int(datetime.datetime.fromisoformat(f"{m.group(1)}T{m.group(2)}").replace(tzinfo=tz).timestamp())
    w = [raw[t] for t in range(ts - 29, ts + 1) if t in raw]; l = [lng[t] for t in range(ts - 29, ts + 1) if t in lng]
    if not w: continue
    g = lambda k: mean([float(r[k]) for r in w if r.get(k)])
    lg = lambda k: mean([x.get(k) for x in l])
    thr = set(); [thr.update(n for b, n in TH.items() if int(x.get('thr', 0)) & b) for x in l]
    say = m.group(3).replace('Seb: ', '').replace('|', '/')
    print(f"| {m.group(2)[:5]} | {say[:60]} | {f(g('case_rpm'),0)} | {f(g('gpu_pct'),0)} | {f(lg('pl'),0)} | {f(g('power_w'),0)} | {f(lg('core01'),2)} (NVML {f(g('core_c'),1)}) | {f(g('mem_c'),1)} | {f(g('hot_c'),2)} | {f(lg('air'),2)} | {f(g('clock_mhz'),0)} | {' '.join(sorted(thr)) or 'none'} |")
