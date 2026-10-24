"""Experiment chronology (Appendix A, first subsection) built from the data folders: start/end from raw.csv (1 Hz, unix t),
points from grid.csv / points.csv / status.json, GPU energy integrated from raw.csv power_w (board power, all cards), CPU
package energy from the long logs (sensor lhm/amdcpu/0/power/0) where they exist (cached in out/chrono-cache.json).
New run folders (stress1, steady4 ...) appear automatically. Writes <!--chrono:start/end--> after the Appendix A heading and
research/data/gpu-map-chronology.csv. Usage: chronology.py"""
import csv, glob, gzip, json, os, re, zoneinfo, datetime
from pathlib import Path
G = Path(__file__).resolve().parent.parent; D = G / "data"; F = Path.home() / "Claude/gruency-site/research/gpu-cooling-method.html"
CACHE = Path(__file__).resolve().parent / "out/chrono-cache.json"; Z = zoneinfo.ZoneInfo("Europe/Warsaw")
# what each stage was for and what came of it (short; the numbers in the table come from the files)
NOTE = {
 "2026-10-20-gpu-map": ("night grid, try 1", "first GPU × case fan grid at 575&nbsp;W", "load stopped; restarted"),
 "2026-10-20-gpu-map-v2": ("night grid, restarts", "restarts and power-limit calibration", "load stopped during calibration; fixed in the Lab"),
 "2026-10-20-gpu-map-v2c": ("night grid (first run)", "GPU and case fan grid, 60&nbsp;s points", "first map of both fan sets; 60&nbsp;s points later found unsettled"),
 "2026-10-20-gpu-map-v2d": ("night grid, power limit", "power-limit levels added to the grid", "first power-limit data"),
 "2026-10-21-case-hold-1000": ("case-fan hold", "case fans held at 1000&nbsp;rpm while the operator varied the card", "case-fan effect seen by hand"),
 "2026-10-21-log-1": ("manual log", "logging only, fans set by hand", "reference for the Lab&rsquo;s own control"),
 "2026-10-21-grid1c-1card": ("second run (grid1c)", "112 settings, 60&nbsp;s points, four power limits", "first static fit; bias from unsettled points"),
 "2026-10-21-grid1d-repeat40": ("grid1d", "repeat of the card-40&nbsp;% points", "repeatability and drift of the slow-fan points"),
 "2026-10-21-val1": ("val1", "validation: every point to its steady state", "60&nbsp;s readings shown to be biased; settled-point protocol"),
 "2026-10-21-dyn1": ("dyn1", "random steps for the dynamic model", "dynamic model (7)"),
 "2026-10-21-val2": ("val2", "re-test of the worst 60&nbsp;s points; slow-fan points", "settled points added to the estimation data"),
 "2026-10-22-steady2": ("steady2", "settled points, |dT/dt| &lt; 0.1&nbsp;&deg;C/min", "reference session of the earlier-session model"),
 "2026-10-22-ctrl1": ("ctrl1", "first controller on the card: three modes &times; step and bursts", "targets held within 1&nbsp;&deg;C; fan reversals under bursts"),
 "2026-10-22-ctrl2": ("ctrl2", "anti-pumping corrections", "fewer reversals, slow dips remain"),
 "2026-10-22-ctrl3": ("ctrl3", "load hold near peak, NVAPI core", "no reversals"),
 "2026-10-22-cpu1b": ("cpu1b", "processor at full load, both fan sets fast", "processor limited by power, not temperature"),
 "2026-10-22-cpu2": ("cpu2", "radiator fans slowed under processor load", "Tctl up by about 0.3&nbsp;&deg;C"),
 "2026-10-22-cpu3": ("cpu3", "both fan sets slow, pump at maximum", "no throttling"),
 "2026-10-22-cpu3e": ("cpu3e", "case fans varied at slow radiator fans", "case fans do not cool the processor"),
 "2026-10-23-pl90-case1500": ("pl90", "power limit 90&nbsp;% at case fans 1500&nbsp;rpm", "points for the power term"),
 "2026-10-24-top-off": ("top-off", "memory let past every limit to find the card&rsquo;s own protection", "GDDR7 protection at about 106&nbsp;&deg;C, reported as a power cap"),
 "2026-10-24-pl-sweep-top-off": ("power-limit sweep, top off", "both cards at GPU fans 90&nbsp;%, power limit 100 down to 80&nbsp;%", "card A memory 90&nbsp;&deg;C at 95&nbsp;%"),
 "2026-10-24-steady4": ("steady4 (two-card grid)", "the steady3 levels on both cards together", "in progress"),
 "2026-10-24-sweep-top-off": ("fan sweep, top off", "both cards, GPU fans 100 down to 60&nbsp;%, safety stops", "lowest safe GPU fan speed of the pair"),
 "2026-10-24-stress1": ("stress1", "two cards at 575&nbsp;W, fans at full speed: each alone, then both", "card A +11&nbsp;&deg;C core, +10&nbsp;&deg;C memory with both loaded"),
 "2026-10-23-steady3": ("steady3 (final grid)", "all 196 cells, settled", "estimation data of the primary model"),
}
def note(rid):
    for k in sorted(NOTE, key=len, reverse=True):
        if rid.startswith(k):
            n, a, b = NOTE[k]; extra = rid[len(k):].strip("-").replace("-", " ")
            return (f"{n}, {extra}" if extra and k.split("-")[-1].startswith(("ctrl", "cpu")) else n), a, b
    return (rid, "&mdash;", "&mdash;")
cache = json.load(open(CACHE)) if CACHE.exists() else {}
def cpu_kwh(folder):
    L = sorted(folder.glob("long-*.csv.gz"))
    if not L: return None
    key = "|".join(f"{p.name}:{p.stat().st_size}" for p in L)
    if cache.get(str(folder), {}).get("key") == key: return cache[str(folder)]["kwh"]
    e = 0.0
    for p in L:
        last = None
        try:
          with gzip.open(p, "rt", errors="ignore") as f:
            for line in f:
                if "lhm/amdcpu/0/power/0," not in line: continue
                x = line.split(",")
                try: t, w = float(x[0]), float(x[8])
                except (ValueError, IndexError): continue
                if last and 0 < t - last[0] <= 10: e += (w + last[1]) / 2 * (t - last[0])
                last = (t, w)
        except EOFError: pass   # ponytail: a log cut short (run still writing or copied mid-run) counts up to its end
    cache[str(folder)] = dict(key=key, kwh=e / 3.6e6); return e / 3.6e6
runs = []
for raw in sorted(D.glob("**/raw.csv")):
    fo = raw.parent; rows = list(csv.DictReader(open(raw)))
    if len(rows) < 10: continue
    cj = json.load(open(fo / "conditions.json")) if (fo / "conditions.json").exists() else {}
    st = json.load(open(fo / "status.json")) if (fo / "status.json").exists() else {}
    rid = cj.get("id") or fo.name
    t = [float(r["t"]) for r in rows]; e = 0.0
    for a, b in zip(rows, rows[1:]):
        dt = float(b["t"]) - float(a["t"])
        try:
            if 0 < dt <= 10: e += (float(a["power_w"]) + float(b["power_w"])) / 2 * dt
        except ValueError: pass
    m = re.search(r"(\d+) punkt", str(st.get("note", "")))
    if m: pts = int(m.group(1))
    elif (fo / "points.csv").exists(): pts = sum(1 for _ in open(fo / "points.csv")) - 1
    elif (fo / "grid.csv").exists(): pts = sum(1 for _ in open(fo / "grid.csv")) - 1
    else: pts = None
    case = str(cj.get("case", "")).lower(); cards = 2 if re.search(r"\b2 (gpu|cards|× rtx)|two cards", case) else 1
    inv = (fo / "inventory.csv").read_text(errors="ignore") if (fo / "inventory.csv").exists() else ""
    nf = inv.count("nvml/0/fan/gpu_fan_") or max((len((r.get("gpu_rpm") or "").split("|")) for r in rows[:50]), default=0)
    if "nvml/1/" in inv: cards = 2
    model = "FE" if cards == 2 or nf == 2 else "ZOTAC"   # verified 2026-10-24: 3 GPU fans (≈ 3030 rpm max) up to steady3, 2 per card (≈ 2900 rpm) from 24 Oct
    enc = "open frame" if "panels off" in case else "open top" if "open top" in case else ("panels closed" if re.search(r"panels (on|closed)|closed (case|panels)", case) else "open top")
    runs.append(dict(rid=rid, t0=min(t), t1=max(t), gpu_kwh=e / 3.6e6, cpu_kwh=cpu_kwh(fo), pts=pts, cards=cards, enc=enc,
                     state=st.get("state", ""), pump_max="pump at max" in case, model=model, load=cj.get("load_mode") or "", folder=str(fo.relative_to(D))))
CACHE.parent.mkdir(exist_ok=True); json.dump(cache, open(CACHE, "w"), indent=1)
# hardware and configuration changes reported by the operator (no log file of their own)
EVENTS = [(datetime.datetime(2026, 10, 24, 10, 0, tzinfo=Z).timestamp(), "ZOTAC RTX 5090 Solid removed; two RTX 5090 Founders Edition installed in PCIE1 and PCIE2; display moved to the processor&rsquo;s integrated graphics (HDMI)"),
          (datetime.datetime(2026, 10, 24, 13, 0, tzinfo=Z).timestamp(), "Front panel with dust filter fitted, side panels off, top panel tested on and off; pump fixed at 2200&nbsp;rpm")]
runs.sort(key=lambda r: r["t0"])
tm = lambda ts, f="%d %b %H:%M": (re.sub(r"^0", "", datetime.datetime.fromtimestamp(ts, Z).strftime(f)) if f.startswith("%d") else datetime.datetime.fromtimestamp(ts, Z).strftime(f))
endf = lambda a, b: tm(b, "%H:%M") if tm(a, "%d") == tm(b, "%d") else tm(b, "%d %b %H:%M")
dur = lambda s: f"{int(s // 3600)}&nbsp;h&nbsp;{int(s % 3600 // 60):02d}" if s >= 3600 else f"{int(s // 60)}&nbsp;min"
SHORT = [r for r in runs if r["t1"] - r["t0"] < 300 and r["state"] == "aborted"]   # restarts under 5 min: counted in the totals, not listed
items = [("run", r["t0"], r) for r in runs if r not in SHORT] + [("event", ts, txt) for ts, txt in EVENTS]
items.sort(key=lambda x: x[1])
rows = ""
with open(F.parent / "data/gpu-map-chronology.csv", "w", newline="") as fo:
    w = csv.writer(fo); w.writerow(["start_local", "end_local", "duration_min", "stage", "folder", "cards", "enclosure", "load", "points", "gpu_kwh", "cpu_kwh", "purpose", "outcome"])
    for kind, ts, x in items:
        if kind == "event":
            rows += f'<tr class="ev"><td>{tm(ts, "%d %b, about %H:%M") if ts % 1 == 0 else tm(ts, "%d %b")}</td><td>&mdash;</td><td colspan="2">{x}</td><td>&mdash;</td><td>&mdash;</td><td>&mdash;</td><td>&mdash;</td></tr>'
            w.writerow([tm(ts, "%Y-%m-%d %H:%M"), "", "", "event", "", "", "", "", "", "", "", x, ""]); continue
        nm, why, out = note(x["rid"]); d = x["t1"] - x["t0"]
        cfg = f'{x["cards"]}&nbsp;&times;&nbsp;{x["model"]}, {x["enc"]}' + (", pump at maximum" if x.get("pump_max") else "")
        rows += (f'<tr><td>{tm(x["t0"])}&ndash;{endf(x["t0"], x["t1"])}</td><td>{dur(d)}</td><td class="tl">{nm}</td><td class="tl">{why}; {out}</td><td class="tl">{cfg}</td>'
                 f'<td>{x["pts"] if x["pts"] is not None else "&mdash;"}</td><td>{x["gpu_kwh"]:.2f}</td><td>{"&mdash;" if x["cpu_kwh"] is None else format(x["cpu_kwh"], ".2f")}</td></tr>')
        w.writerow([tm(x["t0"], "%Y-%m-%d %H:%M"), tm(x["t1"], "%Y-%m-%d %H:%M"), round(d / 60, 1), nm, x["folder"], x["cards"], x["enc"], x["load"], x["pts"], round(x["gpu_kwh"], 3),
                    None if x["cpu_kwh"] is None else round(x["cpu_kwh"], 3), re.sub("&[a-z]+;", " ", why), re.sub("&[a-z]+;", " ", out)])
T_h = sum(r["t1"] - r["t0"] for r in runs) / 3600; E_g = sum(r["gpu_kwh"] for r in runs); E_c = sum(r["cpu_kwh"] or 0 for r in runs)
nc = sum(1 for r in runs if r["cpu_kwh"] is not None)
first, last = runs[0]["t0"], runs[-1]["t1"]
SEC = f"""  <h3 id="chronology">Experiment chronology</h3>
  <p>The measurements ran from {tm(first, "%d %B %Y, %H:%M")} to {tm(last, "%d %B %Y, %H:%M")} local time (CEST), in {len(runs)} logged stages ({{tref:chrono}}). They add up to {T_h:.1f}&nbsp;h of logged measurement, during which the graphics card drew {E_g:.1f}&nbsp;kWh, integrated from its board power at 1&nbsp;Hz; the processor package drew {E_c:.1f}&nbsp;kWh in the {nc} stages whose full sensor log includes it. The stages built on one another: the 60-second points of the first night and the second run looked usable until val1 held every point to its steady state and showed them biased, which led to the settled-point protocol of steady2 and steady3; the controller runs ctrl1 to ctrl3 each corrected the fan pumping seen in the one before; the processor runs checked that the slow radiator fans chosen for the card do not limit the processor; and steady3 then measured the whole grid in one uninterrupted session. Every stage up to steady3 ran on one ZOTAC Gaming RTX 5090 Solid; on 24 October it was replaced by two RTX 5090 Founders Edition cards for the two-card study.</p>
  <p>The platform power budget grows with two cards: one RTX 5090 draws up to about 575 to 600&nbsp;W, so two cards and the processor at its 200&nbsp;W limit put about 1.35 to 1.4&nbsp;kW on the power supply, a Seasonic PRIME (its rating is not in the logged inventory).</p>
  <p class="ar-tcap"><b>Experiment chronology: every logged stage and configuration change, with its configuration, purpose, outcome and energy.</b> Times local (CEST); duration from the first to the last 1&nbsp;Hz record; points = settled points where a grid was run; GPU energy integrated from the board power of all cards; CPU energy from the package sensor where the full sensor log exists.</p>
  <div class="ar-tw ar-tw-wide">
  <table class="ar-tab ar-num ar-st ar-chrono">
    <thead><tr><th scope="col">Date and time</th><th scope="col">Duration</th><th scope="col" class="tl">Stage</th><th scope="col" class="tl">Purpose and outcome</th><th scope="col" class="tl">Configuration</th><th scope="col">Points</th><th scope="col">GPU energy, kWh</th><th scope="col">CPU energy, kWh</th></tr></thead>
    <tbody>{rows}<tr class="tot"><td>Total</td><td>{T_h:.1f}&nbsp;h</td><td class="tl" colspan="3">{len(runs)} stages</td><td>{sum(r["pts"] or 0 for r in runs)}</td><td>{E_g:.1f}</td><td>{E_c:.1f}</td></tr></tbody>
  </table>
  </div>
  <p class="ar-note">ZOTAC: ZOTAC Gaming GeForce RTX 5090 Solid, the card of every single-card stage; FE: RTX 5090 Founders Edition, the two cards of the two-card study; the card is identified from the logged fans (three per card on the ZOTAC, two on the FE). Open top: the frame of {{fref:fig-test-set-up-schematic}} without panels; panels closed: the set-up of {{fref:fig-two-card-set-up-panels-on-schematic}}. Configuration changes without a log of their own are reported by the operator and timed approximately. {len(SHORT)} restarts shorter than 5&nbsp;min ({sum(r["gpu_kwh"] for r in SHORT):.2f}&nbsp;kWh) are counted in the totals but not listed. <a href="/research/data/gpu-map-chronology.csv">Data (CSV)</a>.</p>"""
s = F.read_text(); blk = f"<!--chrono:start-->\n{SEC}\n<!--chrono:end-->"
if "<!--chrono:start-->" in s: s = s[:s.index("<!--chrono:start-->")] + blk + s[s.index("<!--chrono:end-->") + len("<!--chrono:end-->"):]
else: i = s.index('<h2 id="appendix-a">'); i = s.index("</h2>", i) + 5; s = s[:i] + "\n" + blk + s[i:]
F.write_text(s); print(f"chronology: {len(runs)} runs, {T_h:.1f} h, GPU {E_g:.2f} kWh, CPU {E_c:.2f} kWh ({nc} runs)")
