"""steady3 (final grid, 23 Oct) tables: one per power limit, rows GPU fans 40-100 %, columns case+radiator target rpm.
Cell = steady3 measurement only (never averaged with earlier sessions) / model prediction, core and memory, °C.
Source: data/steady3-*/grid.csv (settled rows, path order); until it exists, the Lab log lines and the watch notes.
Writes <!--s3tables:start/end--> before <!--datatables:start--> and research/data/gpu-map-steady3-cells.csv. Usage: steady3_tables.py"""
import csv, glob, json, math, re
from pathlib import Path
G = Path(__file__).resolve().parent.parent; F = Path.home() / "Claude/gruency-site/research/gpu-cooling-method.html"
CARDS = [40, 50, 60, 70, 80, 90, 100]; CASES = [800, 1000, 1300, 1600, 1900, 2400, 3000]; PLS = [100, 90, 80, 70]
PLW = {100: 575, 90: 518, 80: 460, 70: 402}
pct2rpm = lambda p: 1313 + (p - 40) * (3012 - 1313) / 60
J = json.load(open(G / "results-2026-10-22/steady-stats.json")); MJ = json.load(open(G / "results-2026-10-23/mem-model.json"))
P = {p["param"]: p["est"] for p in J["params"]}; Q = {k: v[0] for k, v in MJ["params"].items()}
core = lambda N, C, W, T: T + P["θ0"] + W * (P["r∞"] / 1000 + 1 / (P["gN"] * (N / 1000) ** P["m"] + P["gC"] * (C / 1500) ** P["s"]))
mem = lambda N, C, W, T: T + Q["θ0m"] + W * (Q["r∞"] / 1000 + 1 / (Q["gN"] * (N / 1000) ** Q["m"] + Q["gC"] * (C / 1500) ** Q["s"]))
path = {int(r["n"]): (int(r["card"]), int(r["pl"]), int(r["case"])) for r in csv.DictReader(open(G / "plan/steady3_path.csv"))}
cells, src = {}, "none"
grids = sorted(glob.glob(str(G / "data/steady3-*/grid.csv")))
if grids:
    src = "grid"
    rows = list(csv.DictReader(open(grids[-1])))
    for k, r in enumerate(rows, start=1):           # Lab point k = path n k-1; k = 1 and k = 198 are the anchors
        if k - 1 not in path or r.get("settled") != "1": continue
        g, pl, c = path[k - 1]; f = lambda x: float(r[x]) if r.get(x) not in (None, "") else None
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
for (pl, g, c), v in cells.items(): v["core_mod"] = core(v["N"], v["C"], v["W"], v["T"]); v["mem_mod"] = mem(v["N"], v["C"], v["W"], v["T"])
fmt = lambda x: "&middot;" if x is None else f"{x:.1f}"
def tab(pl):
    n = sum(1 for (p, g, c) in cells if p == pl)
    head = "".join(f'<th scope="col">{c if c != 3000 else "3000 (full, ~2920)"}</th>' for c in CASES)
    body = ""
    for g in CARDS:
        tds = ""
        for c in CASES:
            v = cells.get((pl, g, c))
            tds += ('<td class="s3-e">&middot;</td>' if v is None else
                    f'<td>{v["core"]:.1f} / {v["core_mod"]:.1f}<br><span class="s3-m">{v["mem"]:.1f} / {v["mem_mod"]:.1f}</span></td>')
        body += f'<tr><td>{g}&nbsp;% <span class="s3-r">{round(pct2rpm(g), -1):.0f}</span></td>{tds}</tr>'
    return (f'<h4 class="ar-h4">Power limit {pl}&nbsp;% ({PLW[pl]}&nbsp;W): core and memory, &deg;C, measured / model &middot; {n}/49 measured</h4>\n'
            f'<div class="ar-tw ar-tw-wide"><table class="ar-tab ar-num ar-cmp ar-s3"><thead><tr><th scope="col">GPU fans, % and rpm \\ case and radiator fans, rpm</th>{head}</tr></thead><tbody>{body}</tbody></table></div>\n')
ntot = len(cells)
legend = ('<p class="ar-note ar-legend"><b>How to read these tables.</b> steady3 only, single settled measurement per cell, not averaged with earlier sessions. '
          'Rows: GPU fan duty in % with the nominal rpm; columns: target speed of the four case fans and three radiator fans, in rpm (below about 880&nbsp;rpm the radiator fans stay at their floor; 3000 means full speed, about 2920&nbsp;rpm). '
          'Each cell, first line: core temperature, measured / model, &deg;C; second line, smaller: memory junction temperature, measured / model, &deg;C. '
          'Measured: the settled value of this one point (core from the 0.01&nbsp;&deg;C sensor where logged, memory in whole degrees). '
          'Model: equation (11) and the memory model fitted to the earlier sessions (21&ndash;22 October), evaluated at this point&rsquo;s fan speeds, power and intake air with the reference-session offset; steady3 is not in that fit, so the model column is a prediction. '
          'A grey dot (&middot;) means not measured yet. A fit on steady3 alone follows once the grid covers enough GPU fan speeds.'
          + (' <i>Live values are taken from the test log until the full data file arrives; model values then use the target speeds, the nominal power and 19.3&nbsp;&deg;C intake.</i>' if src == "log" else "") + '</p>')
sec = (f'<!--s3tables:start-->\n  <h3 id="steady3-grid">The final grid: steady3, 23 October</h3>\n'
       f'  <p class="ar-status"><b>Live.</b> The run is in progress; {ntot} of 196 grid points are measured. These tables are the primary result and fill in as points arrive.</p>\n'
       f'  {legend}\n' + "".join(tab(p) for p in PLS) +
       f'  <p class="ar-note"><a href="/research/data/gpu-map-steady3-cells.csv">Data (CSV)</a>.</p>\n<!--s3tables:end-->')
with open(Path.home() / "Claude/gruency-site/research/data/gpu-map-steady3-cells.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["pl_pct", "gpu_pct", "case_target_rpm", "core_measured_c", "core_model_c", "mem_measured_c", "mem_model_c", "source"])
    for (pl, g, c), v in sorted(cells.items(), key=lambda kv: (-kv[0][0], kv[0][1], kv[0][2])):
        w.writerow([pl, g, c, v["core"], round(v["core_mod"], 2), v["mem"], round(v["mem_mod"], 2), src])
s = F.read_text()
css = ".ar-s3 td{line-height:1.25}.ar-s3 .s3-m{font-size:.86em;color:var(--mute-l)}.ar-s3 .s3-r{font-size:.82em;color:var(--mute-l);margin-left:4px}.ar-s3 td.s3-e{color:var(--mute-l);opacity:.55;text-align:center!important}.ar-legend{margin-top:8px}"
if ".ar-s3 td{" not in s: k = s.index("</style>"); s = s[:k] + css + s[k:]
a, b = s.find("<!--s3tables:start-->"), s.find("<!--s3tables:end-->")
if a < 0: i = s.index("<!--datatables:start-->"); s = s[:i] + sec + "\n" + s[i:]
else: s = s[:a] + sec + s[b + len("<!--s3tables:end-->"):]
F.write_text(s); print("steady3 tables:", src, ntot, "cells")
assert all(0 < v["core"] < 100 and 0 < v["mem"] < 110 for v in cells.values())
