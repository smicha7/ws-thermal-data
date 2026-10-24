"""steady3 (final grid, 23 Oct) tables: one per power limit, rows GPU fans 40-100 %, columns case+radiator target rpm.
Cell = steady3 measurement only (never averaged with earlier sessions) / model prediction, core and memory, °C.
Source: data/steady3-*/grid.csv (settled rows, path order); until it exists, the Lab log lines and the watch notes.
Writes <!--s3tables:start/end--> before <!--datatables:start--> and research/data/gpu-map-steady3-cells.csv. Usage: steady3_tables.py"""
import csv, glob, json, math, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); from caseclass import label
G = Path(__file__).resolve().parent.parent; F = Path.home() / "Claude/gruency-site/research/gpu-cooling-method.html"
CARDS = [40, 50, 60, 70, 80, 90, 100]; CASES = [800, 1000, 1300, 1600, 1900, 2400, 3000]; PLS = [100, 90, 80, 70]
PLW = {100: 575, 90: 518, 80: 460, 70: 402}
pct2rpm = lambda p: 1313 + (p - 40) * (3012 - 1313) / 60
J = json.load(open(G / "results-2026-10-22/steady-stats.json")); MJ = json.load(open(G / "results-2026-10-23/mem-model.json"))
P = {p["param"]: p["est"] for p in J["params"]}; Q = {k: v[0] for k, v in MJ["params"].items()}
core_e = lambda N, C, W, T: T + P["θ0"] + W * (P["r∞"] / 1000 + 1 / (P["gN"] * (N / 1000) ** P["m"] + P["gC"] * (C / 1500) ** P["s"]))
mem_e = lambda N, C, W, T: T + Q["θ0m"] + W * (Q["r∞"] / 1000 + 1 / (Q["gN"] * (N / 1000) ** Q["m"] + Q["gC"] * (C / 1500) ** Q["s"]))
sys.path.insert(0, str(G)); import model3   # primary model (steady3 fit); core_e / mem_e = the earlier-session model, kept for the cross-check
core = lambda N, C, W, T: float(model3.core(N, C, W, T)); mem = lambda N, C, W, T: float(model3.mem(N, C, W, T))
path = {int(r["n"]): (int(r["card"]), int(r["pl"]), int(r["case"])) for r in csv.DictReader(open(G / "plan/steady3_path.csv"))}
cells, src = {}, "none"
grids = sorted(glob.glob(str(G / "data/steady3-*/grid.csv")))
if grids:
    src = "grid"
    rows = list(csv.DictReader(open(grids[-1])))
    for k, r in enumerate(rows, start=1):           # first and last row are the anchors (40 % / 1600 / PL 100), not grid cells; of repeats the last settled row wins
        if k in (1, len(rows)) or r.get("settled") != "1": continue
        g, pl, c = int(r["gpu_pct"]), int(r["pl_pct"]), int(float(r["case_rpm_target"])); f = lambda x: float(r[x]) if r.get(x) not in (None, "") else None
        cells[(pl, g, c)] = dict(core=f("cardA_core_nvapi_c") or f("core_c_max"), mem=f("mem_c_max"), N=f("cardA_fan_rpm") or pct2rpm(g),
                                 C=f("case_rpm") or c, W=f("power_w_sum") or PLW[pl], T=f("intake_c") or 19.3)
else:   # live fallback: Lab log lines, then the watch notes (core/memory as logged; model at target speeds, 19.3 °C)
    txt = "\n".join(open(p, errors="ignore").read() for p in glob.glob(str(G / "data/steady3-*/*.txt")) + [str(G / "data/steady3-watch.md")] if Path(p).exists())
    for k, g, c, tc, tm in re.findall(r"punkt (\d+)/198: obie (\d+) % / (\d+) rpm → rdzeń ([\d.]+), pamięć ([\d.]+)", txt):
        if int(k) - 1 in path: g, pl, c = path[int(k) - 1]; cells[(pl, g, c)] = dict(core=float(tc), mem=float(tm))
    for line in txt.splitlines():
        if "punkt" in line: continue
        pl = re.findall(r"PL (\d+)", line); card = re.findall(r"card (\d+) %", line)
        if not pl or not card: continue
        for c, tc, tm in re.findall(r"(\d{3,4}) → (?:core )?(\d+(?:\.\d+)?)(?: °C)?(?:, memory |/)(\d+(?:\.\d+)?)", line):
            key = (int(pl[0]), int(card[0]), int(c))
            if key[2] in CASES: cells.setdefault(key, dict(core=float(tc), mem=float(tm)))
    src = "log" if cells else "none"
    for (pl, g, c), v in cells.items(): v.update(N=pct2rpm(g), C=c, W=PLW[pl], T=19.3)
for (pl, g, c), v in cells.items():
    v["core_mod"] = core(v["N"], v["C"], v["W"], v["T"]); v["mem_mod"] = mem(v["N"], v["C"], v["W"], v["T"])
    v["core_e"] = core_e(v["N"], v["C"], v["W"], v["T"]); v["mem_e"] = mem_e(v["N"], v["C"], v["W"], v["T"])
fmt = lambda x: "&middot;" if x is None else f"{x:.1f}"
RPM = {40: 1310, 50: 1600, 60: 1880, 70: 2160, 80: 2450, 90: 2730, 100: 3010}   # nominal, as in the article's Table 7
LEV = {800: "800&nbsp;rpm<br>ultra-quiet", 1000: "1000&nbsp;rpm<br>very quiet", 1300: "1300&nbsp;rpm<br>quiet", 1600: "1600&nbsp;rpm<br>balanced",
       1900: "1900&nbsp;rpm<br>loud", 2400: "2400&nbsp;rpm<br>between loud and very loud", 3000: "&asymp;2920&nbsp;rpm (full)<br>very loud"}
def tab(pl, q):
    n = sum(1 for (p, g, c) in cells if p == pl)
    qn, k, d = {"core": ("GPU core temperature", "core", 1), "mem": ("GPU memory temperature", "mem", 0)}[q]
    top = f'<th scope="colgroup" colspan="{2 * len(CASES)}">Case and radiator fans</th>'
    lev = "".join(f'<th scope="colgroup" colspan="2">{LEV[c]}</th>' for c in CASES)
    sub = '<th scope="col" class="g">measured</th><th scope="col">model</th>' * len(CASES)
    body = ""
    for g in CARDS:
        tds = ""
        for c in CASES:
            v = cells.get((pl, g, c))
            tds += ('<td class="g s3-e">&middot;</td><td class="s3-e">&middot;</td>' if v is None else
                    f'<td class="g">{v[k]:.{d}f}</td><td>{v[k + "_mod"]:.1f}</td>')
        body += f'<tr><td>{g}&nbsp;%</td><td>{RPM[g]}&nbsp;rpm</td>{tds}</tr>'
    return (f'<h4 class="ar-h4">{qn} in &deg;C at power limit {pl}&nbsp;% ({PLW[pl]}&nbsp;W): measured (left sub-column) and fitted by equation ({"R1" if q == "core" else "R2"}) (right sub-column), for each GPU fan speed (rows) and case-and-radiator fan speed (columns). Intake air 19.3 to 20.2&nbsp;&deg;C. {n} of 49 settings.</h4>\n'
            f'<div class="ar-tw ar-tw-wide"><table class="ar-tab ar-num ar-cmp ar-s3 ar-ms"><thead><tr><th scope="colgroup" colspan="2" rowspan="3">GPU fans</th>{top}</tr><tr>{lev}</tr><tr>{sub}</tr></thead><tbody>{body}</tbody></table></div>\n')
ntot = len(cells)
S3 = json.load(open(G / "results-2026-10-24/steady3-fit.json")); S3H = json.load(open(G / "data/steady3-2026-10-23/status.json"))["elapsed_s"] / 3600
legend = ('<p class="ar-note ar-legend">steady3 only, single settled measurement per cell, not averaged with earlier sessions. '
          'Rows: GPU fan duty in % with the nominal rpm; columns: target speed of the four case fans and three radiator fans, in rpm, with their listening class ({tref:caseclass}); below about 880&nbsp;rpm the radiator fans stay at their floor, and 2400&nbsp;rpm is a model point between loud and very loud. '
          'Measured: the settled value of this one point. Model: the prediction for the same fan speeds, power and intake air. Core and memory are in separate tables. '
          'Measured core from the 0.01&nbsp;&deg;C sensor; measured memory in whole degrees, as the card reports it. '
          'Fitted: equations (R1) and (R2), estimated on this grid (<a href="#est3">Section 4.1</a>), at this point&rsquo;s measured fan speeds, power and intake air. '
          'The CSV also gives the prediction of the earlier-session model for each point (<a href="#validation">Section 4.6</a>).'
          + (' <i>Live values are taken from the test log until the full data file arrives; model values then use the target speeds, the nominal power and 19.3&nbsp;&deg;C intake.</i>' if src == "log" else "") + '</p>')
sec = (f'<!--s3tables:start-->\n  <h3 id="steady3-grid">The final grid: steady3, 23 to 24 October</h3>\n'
       f'  <p>The final grid is the estimation data set. It covers all {ntot} cells of the grid, 7 GPU fan speeds &times; 7 case-and-radiator fan speeds &times; 4 power limits, in {S3["rows"]} measurements: the {ntot} cells, {S3["repeats"]} repeats (of a cell the last settled reading is kept) and an anchor point (GPU fans 40&nbsp;%, case fans 1600&nbsp;rpm, 575&nbsp;W) measured at the start and the end. The run took {S3H:.1f}&nbsp;h without intervention; the load program stopped three times and was restarted automatically, with the point repeated each time, and the fan controller&rsquo;s (aquaero) own settings were restored at the end. The intake air stayed between {S3["tin"]["min"]:.1f} and {S3["tin"]["max"]:.1f}&nbsp;&deg;C (standard deviation {S3["tin"]["sd"]:.2f}&nbsp;&deg;C).</p>\n'
       + "".join(tab(p, q) for p in PLS for q in ("core", "mem")) +
       f'  {legend[:-4]} <a href="/research/data/gpu-map-steady3-cells.csv">Data (CSV)</a>.</p>\n<!--s3tables:end-->')
with open(Path.home() / "Claude/gruency-site/research/data/gpu-map-steady3-cells.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["pl_pct", "gpu_pct", "case_target_rpm", "core_measured_c", "core_model_c", "mem_measured_c", "mem_model_c", "core_earlier_model_c", "mem_earlier_model_c", "source"])
    for (pl, g, c), v in sorted(cells.items(), key=lambda kv: (-kv[0][0], kv[0][1], kv[0][2])):
        w.writerow([pl, g, c, v["core"], round(v["core_mod"], 2), v["mem"], round(v["mem_mod"], 2), round(v["core_e"], 2), round(v["mem_e"], 2), src])
s = F.read_text()
css = ".ar-s3 td{line-height:1.25}.ar-s3 .s3-m{font-size:.86em;color:var(--mute-l)}.ar-s3 .s3-r{font-size:.82em;color:var(--mute-l);margin-left:4px}.ar-s3 td.s3-e{color:var(--mute-l);opacity:.55;text-align:center!important}.ar-legend{margin-top:8px}"
if ".ar-s3 td{" not in s: k = s.index("</style>"); s = s[:k] + css + s[k:]
a, b = s.find("<!--s3tables:start-->"), s.find("<!--s3tables:end-->")
if a >= 0: s = s[:a] + s[b + len("<!--s3tables:end-->"):]
i = s.index("<!--estdata:start-->"); s = s[:i] + sec + "\n" + s[i:]   # the final grid comes first: it is the estimation data
F.write_text(s); print("steady3 tables:", src, ntot, "cells")
assert all(0 < v["core"] < 100 and 0 < v["mem"] < 110 for v in cells.values())
