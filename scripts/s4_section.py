"""Two-card study (steady4, in progress): methods subsection under 2.4 (with Figure 'two-card set-up' via setup_fig.py),
the settling-time analysis of steady3 in Section 4 (justifies the shorter protocol), and live data tables in Section 3 from
data/steady4-*/grid.csv (empty until the file exists). Markers: s4method, settle, s4tables. Usage: s4_section.py"""
import csv, glob, json
from pathlib import Path
import numpy as np, pandas as pd
G = Path(__file__).resolve().parent.parent; F = Path.home() / "Claude/gruency-site/research/gpu-cooling-method.html"; SITE = F.parent
CARDS = [40, 50, 60, 70, 80, 90, 100]; CASES = [800, 1000, 1300, 1600, 1900, 2400, 3000]; PLS = [100, 90, 80, 70]
PLW = {100: 575, 90: 518, 80: 460, 70: 402}
HOLD = {40: 5, 50: 4}; hold = lambda g: HOLD.get(g, 3)                       # minutes, from the settling analysis below
def put(s, name, html, before=None, after=None):
    a, b = s.find(f"<!--{name}:start-->"), s.find(f"<!--{name}:end-->")
    blk = f"<!--{name}:start-->\n{html}\n<!--{name}:end-->"
    if a >= 0: return s[:a] + blk + s[b + len(f"<!--{name}:end-->"):]
    i = s.index(before) if before else s.index(after) + len(after)
    return s[:i] + blk + "\n" + s[i:]
# ---- settling analysis (steady3, same sensor as the settled value)
g3 = pd.read_csv(sorted(glob.glob(str(G / "data/steady3-*/grid.csv")))[-1]); d = g3.iloc[1:-1]
d = d[d.settled == 1].drop_duplicates(["pl_pct", "gpu_pct", "case_rpm_target"], keep="last")
MINS = [1, 2, 3, 5]
def p95(col, ref, sel=None):
    x = d if sel is None else d[sel]; e = (x[col] - x[ref]).abs().dropna(); return float(e.quantile(0.95))
rows = ""
for gp in CARDS + ["all"]:
    sel = None if gp == "all" else d.gpu_pct == gp
    c = [p95(f"core_nvapi_{m}min", "cardA_core_nvapi_c", sel) for m in MINS]; mm = [p95(f"mem_{m}min", "mem_c_max", sel) for m in (3, 5)]
    lab = "all speeds" if gp == "all" else f"{gp}&nbsp;%"
    rows += (f'<tr><td>{lab}</td><td class="g">{c[0]:.2f}</td><td>{c[1]:.2f}</td><td>{c[2]:.2f}</td><td>{c[3]:.2f}</td><td class="g">{mm[0]:.2f}</td><td>{mm[1]:.2f}</td>'
             f'<td class="g">{"&mdash;" if gp == "all" else hold(gp)}</td></tr>')
S = {gp: p95("core_nvapi_3min", "cardA_core_nvapi_c", d.gpu_pct == gp) for gp in CARDS}
S5 = {gp: p95("core_nvapi_5min", "cardA_core_nvapi_c", d.gpu_pct == gp) for gp in CARDS}
nvml3 = p95("core_3min", "cardA_core_nvapi_c")
SET = f"""  <h3 id="settle">Settling time on the final grid</h3>
  <p>Every point of the final grid was held for at least five minutes (eight at GPU fans 40&nbsp;%), and the Lab recorded the core and memory after 1, 2, 3 and 5 minutes. Comparing these early readings with the settled value of the same point shows how long a point really needs ({{tref:settle3}}). For the core, read on the same 0.01&nbsp;&deg;C sensor as the settled value, the 95th percentile of the error after 3 minutes is {S[40]:.2f}&nbsp;&deg;C at GPU fans 40&nbsp;%, {S[50]:.2f} at 50&nbsp;% and {S[60]:.2f} at 60&nbsp;%, and at most {max(S[g] for g in CARDS if g >= 70):.2f}&nbsp;&deg;C from 70&nbsp;% up; after 5 minutes it is {S5[40]:.2f}&nbsp;&deg;C at 40&nbsp;% and at most {max(S5[g] for g in CARDS if g >= 50):.2f}&nbsp;&deg;C elsewhere. The slow GPU fans need the longest because the card&rsquo;s time constant grows as its airflow falls. The memory, read in whole degrees, needs 5 minutes at every speed. Mixing sensors inflates the error: the 1&nbsp;&deg;C NVML core after 3 minutes against the NVAPI settled value gives a 95th percentile of {nvml3:.2f}&nbsp;&deg;C overall, so early and settled readings must come from the same sensor.</p>
  <p class="ar-tcap"><b>How far an early reading lies from the settled value on the final grid, by GPU fan speed: 95th percentile of the absolute error, and the hold time chosen for the two-card grid.</b> {len(d)} settled points of steady3; core from the NVAPI sensor (0.01&nbsp;&deg;C), memory in whole degrees.</p>
  <div class="ar-tw">
  <table class="ar-tab ar-num ar-st ar-ms ar-settle">
    <thead><tr><th scope="col" rowspan="2">GPU fans</th><th scope="colgroup" colspan="4">Core: error after, &deg;C</th><th scope="colgroup" colspan="2">Memory: error after, &deg;C</th><th scope="col" rowspan="2" class="g">Hold, steady4, min</th></tr>
    <tr><th scope="col" class="g">1&nbsp;min</th><th scope="col">2&nbsp;min</th><th scope="col">3&nbsp;min</th><th scope="col">5&nbsp;min</th><th scope="col" class="g">3&nbsp;min</th><th scope="col">5&nbsp;min</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  </div>
  <p class="ar-note">Error = |reading after the given time &minus; settled value| of the same point. The hold is a minimum: a point ends only when the core and memory of both cards have also stopped rising (<a href="#steady4-method">Section 2.4.2</a>). <a href="/research/data/gpu-map-steady3-cells.csv">Data (CSV)</a>; early readings in the steady3 grid file of the repository.</p>"""
# ---- methods subsection
mins = sum(28 * hold(gp) for gp in CARDS) / 60
MET = f"""  <h4 id="steady4-method">The two-card study (in progress)</h4>
  <p>A second RTX 5090 Founders Edition is now fitted: card A in the first PCIe slot, card B in the second, at the board&rsquo;s slot spacing ({{fref:fig-two-card-set-up-panels-on-schematic}}), and the side, front and top panels of the frame are closed. The grid steady4 repeats the levels of steady3, GPU fans 40 to 100&nbsp;% on both cards together, case and radiator fans 800&nbsp;rpm to full speed and power limits 100, 90, 80 and 70&nbsp;%, both cards under the same load. Following the settling analysis of steady3 (<a href="#settle">Section 4.2</a>), each point is held for at least 5 minutes at GPU fans 40&nbsp;%, 4 at 50&nbsp;% and 3 from 60&nbsp;% up, and then until the core and memory of both cards have stopped rising, the same plateau test as in steady3. The minimum holds alone add up to {mins:.1f}&nbsp;h for the 196 points; with the plateau extensions and the transitions we expect about 12 to 14 hours, against 18.8 for steady3.</p>
  <p>The grid answers three questions: how much the two cards heat each other, card A&rsquo;s fans facing card B, whose flow-through air leaves towards them, and how that depends on both fan sets; how much the closed case changes the settled temperatures and the role of the case fans, against the open frame of steady3; and what control law two cards need, with one noise budget for the whole machine and the hotter card setting the fans.</p>
<!--setupfig2:start--><!--setupfig2:end-->"""
# ---- live tables
G4 = sorted(glob.glob(str(G / "data/steady4-*/grid.csv")))
cells = {}
if G4:
    r = list(csv.DictReader(open(G4[-1])))
    key = lambda x: (int(x["pl_pct"]), int(x["gpu_pct"]), int(float(x["case_rpm_target"])))
    if len(r) > 1 and key(r[0]) == key(r[-1]): r = r[1:-1]          # anchors at start and end
    f = lambda x, k: float(x[k]) if x.get(k) not in (None, "") else None
    for x in r:
        if x.get("settled") != "1": continue
        cells[key(x)] = dict(A=f(x, "cardA_core_nvapi_c") or f(x, "cardA_core_c"), B=f(x, "cardB_core_nvapi_c") or f(x, "cardB_core_c"),
                             mA=f(x, "cardA_mem_c"), mB=f(x, "cardB_mem_c"), T=f(x, "intake_c"))
    with open(SITE / "research/data/gpu-map-steady4-cells.csv", "w", newline="") as fo:
        w = csv.writer(fo); w.writerow(["pl_pct", "gpu_pct", "case_target_rpm", "cardA_core_c", "cardB_core_c", "cardA_mem_c", "cardB_mem_c", "intake_c"])
        for k, v in sorted(cells.items(), key=lambda kv: (-kv[0][0], kv[0][1], kv[0][2])): w.writerow([*k, v["A"], v["B"], v["mA"], v["mB"], v["T"]])
fmt = lambda v: "&middot;" if v is None else f"{v:.1f}"
def tab(pl, c):
    body = "".join(f'<tr><td>{gp}&nbsp;%</td>' + "".join(f'<td{" class=\"s3-e\"" if (pl, gp, cc) not in cells else ""}>{fmt(cells.get((pl, gp, cc), {}).get(c))}</td>' for cc in CASES) + "</tr>" for gp in CARDS)
    n = sum(1 for k in cells if k[0] == pl)
    return (f'<h4 class="ar-h4">Card {c}, GPU core temperature in &deg;C at power limit {pl}&nbsp;% ({PLW[pl]}&nbsp;W per card), two cards, panels on: GPU fan speed of both cards (rows) against case and radiator fan target (columns). {n} of 49 settings measured.</h4>\n'
            f'<div class="ar-tw ar-tw-wide"><table class="ar-tab ar-num ar-s3 ar-s4"><thead><tr><th scope="col">GPU fans, both cards</th>' + "".join(f'<th scope="col">{("&asymp;2920" if cc == 3000 else cc)}&nbsp;rpm</th>' for cc in CASES) + f'</tr></thead><tbody>{body}</tbody></table></div>\n')
TB = (f'  <h3 id="steady4-grid">Two-card data: steady4 (in progress)</h3>\n  <p>' + (f'The two-card grid has reached {len(cells)} of 196 points; the tables fill as it runs.' if cells else 'The two-card grid has not started yet; the tables below fill as it runs, one per card and power limit.')
      + '</p>\n' + "".join(tab(pl, c) for pl in PLS for c in "AB")
      + '  <p class="ar-note">A dot (&middot;) means the setting has not been measured yet. Core from the NVAPI sensor of each card. ' + ('<a href="/research/data/gpu-map-steady4-cells.csv">Data (CSV)</a>, with the memory of both cards and the intake air.' if cells else 'The data file appears here once the run starts.') + '</p>')
s = F.read_text()
s = put(s, "settle", SET, before="<!--stats:start-->")
s = put(s, "s4method", MET, before='<h3 id="models"')
s = put(s, "s4tables", TB, after="<!--estdata:end-->")
css = ".ar-s4 td.s3-e{color:var(--mute-l);opacity:.55;text-align:center!important}"
if ".ar-s4 td.s3-e" not in s: k = s.index("</style>"); s = s[:k] + css + s[k:]
F.write_text(s); print("steady4 sections written; cells:", len(cells), "min hold h:", round(mins, 1), {g: round(v, 2) for g, v in S.items()})
