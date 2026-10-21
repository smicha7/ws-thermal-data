"""Transitions from raw.csv: detects changes in card fans (duty % / mean rpm, e.g. Afterburner) and load (card power jump),
for core and memory gives: temperature before/after, τ63, t90, settling time (|dT/dt| < 0.2 °C/min over a 60 s window), heating/cooling.
Usage: transitions.py raw.csv [markers.txt] [long-*.csv.gz] [HardwareMonitoring.hml]   (no args = self-check on synthetic data)
markers.txt: one line per Seb marker "HH:MM[:SS] description" (Mac time, Europe/Warsaw, day 2026-10-21) → 30 s means + trend before that moment.
Events are detected from the log itself, so a few seconds of Mac ↔ ws298 clock offset does not matter for them."""
import csv, datetime, gzip, math, sys, zoneinfo

def load(path):
    out = []
    for r in csv.DictReader(open(path)):
        f = [float(x) for x in r.get('gpu_rpm', '').split('|') if x]
        def g(k): return float(r[k]) if r.get(k) else math.nan
        out.append(dict(t=int(r['t']), core=g('core_c'), mem=g('mem_c'), p=g('power_w'), clk=g('clock_mhz'), duty=g('gpu_pct'), rpm=sum(f) / len(f) if f else math.nan))
    return out

def mean(v):
    v = [x for x in v if not math.isnan(x)]
    return sum(v) / len(v) if v else math.nan

def events(rows):
    """Event = level change between the 10 s before and the 10 s after (duty ≥ 3 pts, rpm ≥ 150, power ≥ 80 W); one event per 30 s"""
    ev, last = [], -10**9
    for i in range(10, len(rows) - 10):
        t = rows[i]['t']
        if t - last < 30: continue
        a, b = rows[i - 10:i], rows[i:i + 10]
        d = {k: mean([x[k] for x in b]) - mean([x[k] for x in a]) for k in ('duty', 'rpm', 'p')}
        kind = 'load ' + ('start' if d['p'] > 0 else 'stop') if abs(d['p']) >= 80 else \
               'fans ' + ('up' if (d['rpm'] if not math.isnan(d['rpm']) else d['duty']) > 0 else 'down') if abs(d['duty']) >= 3 or abs(d['rpm']) >= 150 else None
        if kind:
            # exact moment: first sample of the window that has already changed by half
            k = 'p' if kind.startswith('load') else ('rpm' if abs(d['rpm']) >= 150 else 'duty')
            base = mean([x[k] for x in a]); j = next((j for j in range(i - 10, i + 10) if abs(rows[j][k] - base) >= abs(d[k]) / 2), i)
            ev.append((j, kind)); last = rows[j]['t']
    return ev

def response(rows, j, end, key):
    t0 = rows[j]['t']
    before = mean([x[key] for x in rows[max(0, j - 30):j]])
    seg = [(x['t'] - t0, x[key]) for x in rows[j:end] if not math.isnan(x[key])]
    settle = None
    for k in range(len(seg)):
        w = [s for s in seg[k:] if s[0] - seg[k][0] < 60]
        if seg[k][0] < 20 or len(w) < 50 or w[-1][0] - w[0][0] < 55: continue
        mt = mean([s[0] for s in w]); mx = mean([s[1] for s in w])
        sl = 60 * sum((s[0] - mt) * (s[1] - mx) for s in w) / sum((s[0] - mt) ** 2 for s in w)
        if abs(sl) < 0.2: settle = seg[k][0]; break
    after = mean([s[1] for s in seg if settle is not None and settle <= s[0] < settle + 30]) if settle is not None else mean([s[1] for s in seg[-30:]])
    dT = after - before
    def reach(f): return next((s[0] for s in seg if abs(dT) > 0.5 and (s[1] - before) / dT >= f), None)
    return dict(before=before, after=after, dT=dT, dir='heating' if dT > 0.5 else 'cooling' if dT < -0.5 else 'flat', tau63=reach(0.632), t90=reach(0.9), settle=settle, settled=settle is not None)

LONG = {'nvml/0/clock/mem': 'memclk', 'nvml/0/power/limit': 'pl', 'nvml/0/throttle': 'thr', 'nvml/0/pstate': 'pst'}
THR = {0x4: 'power', 0x8: 'HW slow', 0x20: 'SW thermal', 0x40: 'HW thermal', 0x80: 'power brake'}

def tctl(path):
    """From long-*.csv.gz: {ts: {'tctl', 'memclk', 'pl', 'thr', 'pst'}} (CPU Tctl + NVML memory clock, enforced limit, throttle mask, P-state)"""
    out = {}
    try:
        with gzip.open(path, 'rt') as f:
            for r in csv.DictReader(f):
                k = 'tctl' if 'tctl' in r['name'].lower() else LONG.get(r['sensor_id'])
                if k and r['value']: out.setdefault(int(r['ts']), {})[k] = float(r['value'])
    except EOFError: pass   # plik jeszcze otwarty przez usługę (gzip bez końca) — bierzemy, co jest
    return out

def point(rows, end, cpu=None):
    """30 s means before ts end + trend (°C/min, linear fit)"""
    w = [x for x in rows if end - 30 < x['t'] <= end]
    if cpu:
        for x in w:
            for k in ('tctl', 'memclk', 'pl'): x[k] = cpu.get(x['t'], {}).get(k, math.nan)
    out = {}
    for k in ('core', 'mem', 'p', 'clk', 'duty', 'rpm') + (('tctl', 'memclk', 'pl') if cpu else ()):
        v = [(x['t'], x[k]) for x in w if not math.isnan(x.get(k, math.nan))]
        m = mean([x for _, x in v]); sl = None
        if len(v) >= 5 and k in ('core', 'mem', 'tctl'):
            mt = mean([t for t, _ in v]); sl = 60 * sum((t - mt) * (x - m) for t, x in v) / sum((t - mt) ** 2 for t, _ in v)
        out[k] = (m, sl)
    if cpu:   # przyczyny dławienia: udział sekund z danym bitem w oknie
        th = [int(cpu.get(x['t'], {}).get('thr', 0)) for x in w]
        out['thr'] = ' '.join(f"{n} {100 * sum(1 for t in th if t & b) / max(1, len(th)):.0f}%" for b, n in THR.items() if any(t & b for t in th)) or 'none'
    return len(w), out

def markers(rows, path, cpu=None, day=datetime.date(2026, 10, 21)):
    tz = zoneinfo.ZoneInfo('Europe/Warsaw')
    for line in open(path):
        if not line.strip(): continue
        hm, _, label = line.strip().partition(' ')
        if '-' in hm: day = datetime.date.fromisoformat(hm); hm, _, label = label.partition(' ')   # "YYYY-MM-DD HH:MM:SS opis"
        parts = [int(x) for x in hm.split(':')] + [0]
        ts = int(datetime.datetime(day.year, day.month, day.day, parts[0], parts[1], parts[2], tzinfo=tz).timestamp())
        n, o = point(rows, ts, cpu)
        print(f"{hm}  {label}  (n={n} s)  " + "  ".join(f"{k} {m:.1f}" + (f" ({sl:+.2f}/min)" if sl is not None else "") for k, (m, sl) in o.items() if not math.isnan(m)))

def steps(rows, cpu=None):
    """Fan-level table: each fan event starts a level; the point = last 30 s before the next event (or the end of the load)"""
    ev = [j for j, k in events(rows) if k.startswith('fans')] 
    load_on = [j for j, k in events(rows) if k == 'load start']
    load_off = [j for j, k in events(rows) if k == 'load stop']
    starts = sorted(set(([load_on[0]] if load_on else []) + ev))
    print(f"{'start':8} {'duty%':>5} {'rpm':>6} {'core':>6} {'trend':>7} {'mem':>6} {'trend':>7} {'power':>6} {'PL':>5} {'clk':>5} {'memclk':>6} {'min':>5}  throttle")
    for n, j in enumerate(starts):
        nxt = starts[n + 1] if n + 1 < len(starts) else next((k for k in load_off if k > j), len(rows) - 1)
        _, o = point(rows, rows[nxt - 1]['t'], cpu)
        hm = datetime.datetime.fromtimestamp(rows[j]['t'], zoneinfo.ZoneInfo('Europe/Warsaw')).strftime('%H:%M:%S')
        tr = lambda k: f"{o[k][1]:+.2f}" if o[k][1] is not None else "—"
        g = lambda k: o[k][0] if k in o else math.nan
        print(f"{hm:8} {g('duty'):5.0f} {g('rpm'):6.0f} {g('core'):6.1f} {tr('core'):>7} {g('mem'):6.1f} {tr('mem'):>7} {g('p'):6.0f} {g('pl'):5.0f} {g('clk'):5.0f} {g('memclk'):6.0f} {(rows[nxt-1]['t']-rows[j]['t'])/60:5.1f}  {o.get('thr', '—')}")

def stop_reason(rows):
    """Why the load ended: GPU Load Test stops at core ≥ 90 / memory ≥ 100 (NVAPI) or after > 10 s without readings"""
    off = [j for j, k in events(rows) if k == 'load stop']
    for j in off:
        w = rows[max(0, j - 15):j + 1]
        core = max((x['core'] for x in w if not math.isnan(x['core'])), default=math.nan)
        mem = max((x['mem'] for x in w if not math.isnan(x['mem'])), default=math.nan)
        why = 'limit core 90' if core >= 90 else 'limit memory 100' if mem >= 100 else 'missing readings' if math.isnan(core) or math.isnan(mem) else \
              'below limits in the service log → NVAPI in the window read higher (index 0) or the load process ended on its own'
        hm = datetime.datetime.fromtimestamp(rows[j]['t'], zoneinfo.ZoneInfo('Europe/Warsaw')).strftime('%H:%M:%S')
        print(f"load stop {hm}: max 15 s before — core {core:.1f}, memory {mem:.1f} °C → {why}")

def hml(path):
    """MSI Afterburner HardwareMonitoring.hml: lines 02 = column names, 80 = data ("dd-mm-yyyy HH:MM:SS") → [(ts, {name: value})]"""
    names, out, tz = [], [], zoneinfo.ZoneInfo('Europe/Warsaw')
    for line in open(path, encoding='latin-1'):
        f = [x.strip() for x in line.split(',')]
        if f[0] == '02': names = f[2:]
        elif f[0] == '80' and names:
            ts = int(datetime.datetime.strptime(f[1], '%d-%m-%Y %H:%M:%S').replace(tzinfo=tz).timestamp())
            out.append((ts, {n: float(v) for n, v in zip(names, f[2:]) if v.replace('.', '', 1).lstrip('-').isdigit()}))
    return out

def report(rows):
    ev = events(rows)
    for n, (j, kind) in enumerate(ev):
        end = ev[n + 1][0] if n + 1 < len(ev) else len(rows)
        print(f"{rows[j]['t']}  {kind}")
        for key in ('core', 'mem'):
            r = response(rows, j, end, key); s = lambda v: f"{v} s" if v is not None else "—"
            print(f"   {key:4} {r['dir']:7} {r['before']:.1f} → {r['after']:.1f} °C (Δ {r['dT']:+.1f})  τ63 {s(r['tau63'])}  t90 {s(r['t90'])}  settled {s(r['settle']) if r['settled'] else 'NOT YET (after = last 30 s)'}")
    return ev

if __name__ == '__main__':
    if len(sys.argv) > 1:
        rows = load(sys.argv[1]); cpu = tctl(sys.argv[3]) if len(sys.argv) > 3 else None
        if len(sys.argv) > 2: print('— Seb markers (30 s mean, trend) —'); markers(rows, sys.argv[2], cpu)
        print('— transitions (from the log) —'); report(rows)
        print('— fan levels (last 30 s of each level) —'); steps(rows, cpu)
        print('— end of load —'); stop_reason(rows)
        if len(sys.argv) > 4:
            ab = hml(sys.argv[4]); print(f'— Afterburner: {len(ab)} rows, columns: {sorted(ab[-1][1]) if ab else []}')
        sys.exit()
    # self-check: load start at 100 s (core τ 50 s, +30 °C), fans up at 800 s (−8 °C, τ 40 s)
    rows = []
    for t in range(1400):
        p = 575 if t >= 100 else 30; rpm = 2500 if t >= 800 else 1500
        core = 40 + (30 * (1 - math.exp(-(t - 100) / 50)) if t >= 100 else 0) - (8 * (1 - math.exp(-(t - 800) / 40)) if t >= 800 else 0)
        rows.append(dict(t=t, core=round(core), mem=round(core + 8), p=p, duty=30 if t < 800 else 60, rpm=rpm))   # 1 °C quantisation as on ws298
    ev = report(rows)
    assert [k for _, k in ev] == ['load start', 'fans up'], ev
    r = response(rows, ev[0][0], ev[1][0], 'core'); assert 40 <= r['tau63'] <= 60 and r['settled'], r
    r = response(rows, ev[1][0], len(rows), 'core'); assert r['dir'] == 'cooling' and 30 <= r['tau63'] <= 50, r
    n, o = point(rows, 790); assert n == 30 and abs(o['core'][0] - 70) < 1 and abs(o['core'][1]) < 0.5, o
    steps(rows); stop_reason(rows)
    print("OK")
