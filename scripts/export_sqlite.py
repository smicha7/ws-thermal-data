"""All thermal-map runs → one tidy SQLite database (METHOD.md, "Database"). Python stdlib only.
Usage: export_sqlite.py <experiments dir with one folder per run> [thermal-map.sqlite]
Tables: runs, conditions, sensors, raw (long, 1 Hz), points, fits, frontier, skipped, setpoints (one row per set-point interval —
clean transitions for driving an animation). Times are Unix seconds (UTC) everywhere; ts_iso added for readability."""
import csv, gzip, io, json, sqlite3, sys, zlib
from datetime import datetime, timezone
from pathlib import Path

root = Path(sys.argv[1]); out = Path(sys.argv[2]) if len(sys.argv) > 2 else root / "thermal-map.sqlite"
if out.exists(): out.unlink()
db = sqlite3.connect(out)
db.executescript("""
CREATE TABLE runs(run_id TEXT PRIMARY KEY, started_utc TEXT, mode TEXT, case_note TEXT, lab_version TEXT, sensor_count INT, folder TEXT);
CREATE TABLE conditions(run_id TEXT, key TEXT, value TEXT);
CREATE TABLE sensors(run_id TEXT, sensor_id TEXT, source TEXT, name TEXT, unit TEXT, first_value REAL);
CREATE TABLE raw(run_id TEXT, ts INT, point TEXT, phase TEXT, fg_set REAL, fc_set REAL, source TEXT, sensor_id TEXT, value REAL, unit TEXT);
CREATE TABLE setpoints(run_id TEXT, t_start INT, t_end INT, phase TEXT, fg_pct REAL, fc_pct REAL, pl_w REAL, pl_pct REAL);
""")
def iso(t): return datetime.fromtimestamp(int(t), timezone.utc).isoformat()

def read_gz_lenient(p):
    """gzip flushed every second; a run cut short has no trailer — read what is there"""
    data = p.read_bytes(); d = zlib.decompressobj(16 + zlib.MAX_WBITS); txt = b""
    try: txt = d.decompress(data)
    except zlib.error: pass
    return txt.decode("utf-8", "replace")

def table_from_csv(name, run, path):
    rows = list(csv.DictReader(open(path, newline="")))
    if not rows: return 0
    cols = ["run_id"] + list(rows[0].keys())
    have = {r[1] for r in db.execute(f"PRAGMA table_info({name})")}
    if not have: db.execute(f"CREATE TABLE {name}(" + ", ".join(f'"{c}"' for c in cols) + ")")
    else:
        for c in cols:
            if c not in have: db.execute(f'ALTER TABLE {name} ADD COLUMN "{c}"')
    db.executemany(f"INSERT INTO {name}(" + ", ".join(f'"{c}"' for c in cols) + ") VALUES(" + ",".join("?" * len(cols)) + ")",
                   [[run] + [r.get(c) for c in cols[1:]] for r in rows])
    return len(rows)

for d in sorted(p for p in root.iterdir() if p.is_dir()):
    run = d.name; cond = json.load(open(d / "conditions.json")) if (d / "conditions.json").exists() else {}
    db.execute("INSERT INTO runs VALUES(?,?,?,?,?,?,?)", (run, cond.get("started_utc"), cond.get("mode"), cond.get("case"), cond.get("lab_version"), cond.get("sensor_count"), str(d)))
    for k, v in cond.items(): db.execute("INSERT INTO conditions VALUES(?,?,?)", (run, k, json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v))
    if (d / "inventory.csv").exists():
        db.executemany("INSERT INTO sensors VALUES(?,?,?,?,?,?)", [(run, r["sensor_id"], r["source"], r["name"], r["unit"], r["first_value"]) for r in csv.DictReader(open(d / "inventory.csv", newline=""))])
    for g in sorted(d.glob("long-*.csv.gz")):
        rd = csv.DictReader(io.StringIO(read_gz_lenient(g)))
        db.executemany("INSERT INTO raw VALUES(?,?,?,?,?,?,?,?,?,?)", ((run, int(r["ts"]), r["point"], r["phase"], r["fg_set"] or None, r["fc_set"] or None, r["source"], r["sensor_id"], r["value"], r["unit"])
                                                                         for r in rd if r.get("ts") and r.get("value") not in (None, "")))
    for name in ["points", "fits", "frontier", "skipped"]:
        if (d / f"{name}.csv").exists(): table_from_csv(name, run, d / f"{name}.csv")
    # set-point intervals from raw.csv (one row per change) — for animation: t_start/t_end with the fans and power limit in force
    if (d / "raw.csv").exists():
        rows = list(csv.DictReader(open(d / "raw.csv", newline="")))
        pl_by_t = {}
        for r in db.execute("SELECT ts, value FROM raw WHERE run_id=? AND sensor_id='nvml/0/power/limit'", (run,)): pl_by_t[r[0]] = r[1]
        stock = float(cond.get("power_default_w") or cond.get("power_limit_w") or 575)
        cur, t0 = None, None
        for r in rows + [None]:
            key = None if r is None else (r["phase"], r["fg_set"], r["fc_set"], pl_by_t.get(int(r["t"])) if r else None)
            if key != cur:
                if cur is not None:
                    plw = cur[3]; db.execute("INSERT INTO setpoints VALUES(?,?,?,?,?,?,?,?)", (run, t0, tl, cur[0], cur[1] or None, cur[2] or None, plw, round(plw * 100 / stock, 1) if plw else None))
                cur = key; t0 = int(r["t"]) if r else None
            if r is not None: tl = int(r["t"])
for v in ["CREATE INDEX raw_i ON raw(run_id, sensor_id, ts)", "CREATE INDEX sp_i ON setpoints(run_id, t_start)",
          "CREATE VIEW raw_named AS SELECT r.*, s.name, datetime(r.ts, 'unixepoch') AS ts_iso FROM raw r LEFT JOIN sensors s USING(run_id, sensor_id)"]:
    db.execute(v)
db.commit()
print({t: db.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in ["runs", "sensors", "raw", "setpoints"] + [n for n in ["points", "fits", "frontier", "skipped"] if db.execute("SELECT 1 FROM sqlite_master WHERE name=?", (n,)).fetchone()]})
