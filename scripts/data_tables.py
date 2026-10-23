"""Builds the data-tables block (<!--datatables:start--> … <!--datatables:end-->) after the statistical tests:
settled core points measured / model per power limit, the provisional memory model, and the 112-point comparison (60 s / settled / model)."""
import json, re, pandas as pd, numpy as np
G = "/Users/smicha/Applications/Pasek/research/gpu-map/"; F = "/Users/smicha/Claude/gruency-site/research/gpu-cooling-method.html"
s = open(F).read()
D = pd.read_csv(G + "results-2026-10-22/steady-residuals.csv"); J = json.load(open(G + "results-2026-10-22/steady-stats.json"))
MM = json.load(open(G + "results-2026-10-23/mem-model.json"))
D["case"] = D.case_target.replace({2250: 2240})
lab = lambda c: {3000: "2920"}.get(c, str(c))
def pltab(pl):
    d = D[D.pl_pct == pl]; cases = sorted(d.case.unique()); cards = sorted(d.gpu_pct.unique())
    head = "".join(f'<th scope="col">{lab(c)}</th>' for c in cases)
    body = ""
    for g in cards:
        tds = ""
        for c in cases:
            q = d[(d.gpu_pct == g) & (d.case == c)]
            if len(q): tds += f"<td>{q.core_settled.mean():.1f} / {q.fitted.mean():.1f}{f'<sup>{len(q)}</sup>' if len(q) > 1 else ''}</td>"
            else: tds += "<td></td>"
        body += f"<tr><td>{g}&nbsp;%</td>{tds}</tr>"
    w = round(575 * pl / 100)
    return (f'<details class="ar-det"{" open" if pl == 100 else ""}><summary>Power limit {pl}&nbsp;% ({w}&nbsp;W): {len(d)} settled points</summary>\n'
            f'  <div class="ar-tw"><table class="ar-tab ar-num ar-cmp"><thead><tr><th scope="col">GPU fans \\ case fans, rpm</th>{head}</tr></thead><tbody>{body}</tbody></table></div>\n</details>\n')
tabs = "".join(pltab(p) for p in (100, 90, 80, 70))
P = MM["params"]; nm = {"θ0m": "&theta;<sub>0,mem</sub>", "r∞": "r<sub>&infin;</sub>", "gN": "g<sub>N</sub>", "m": "m", "gC": "g<sub>C</sub>", "s": "s"}
un = {"θ0m": "&deg;C", "r∞": "m&deg;C/W", "gN": "W/&deg;C", "gC": "W/&deg;C", "m": "", "s": ""}
mrows = "".join(f"<tr><td>{nm.get(k, k)}</td><td>{v[0]:.2f} {un.get(k,'&deg;C')}</td><td>{v[1]:.2f}</td></tr>" for k, v in P.items() if not k.startswith("θ["))
off = "; ".join(f"{k[2:-1]} {v[0]:+.2f}&nbsp;&deg;C".replace("+-", "&minus;").replace("-", "&minus;") for k, v in P.items() if k.startswith("θ["))
# 112-point comparison from TABELE (Polish source, decimal commas)
T = open(G + "TABELE-2026-10-23.md").read()
blocks = re.findall(r"\*\*Obudowa (\d+) obr\./min · limit mocy (\d+) % \((\d+) W\)\*\*.*?\n\n\|.*?\n\|.*?\n((?:\|.*\n?)+)", T)
cmp = ""
for case, pl, w, rows in blocks:
    trs = ""
    for line in rows.strip().split("\n"):
        c = [x.strip() for x in line.strip("|").split("|")]
        fx = lambda t: t.replace(",", ".").replace("*", "<sup>*</sup>").replace("—<sup>*</sup>", "&mdash;").replace("—", "&mdash;")
        trs += f"<tr><td>{c[0].replace(' %','&nbsp;%')}</td><td>{c[1]}</td><td>{fx(c[2])}</td><td>{fx(c[3])}</td></tr>"
    cmp += (f'<h4 class="ar-h4">Case fans {lab(int(case))}&nbsp;rpm, power limit {pl}&nbsp;% ({w}&nbsp;W)</h4>\n'
            f'<div class="ar-tw"><table class="ar-tab ar-num ar-cmp"><thead><tr><th scope="col">GPU fans</th><th scope="col">rpm</th><th scope="col">Core, &deg;C</th><th scope="col">Memory, &deg;C</th></tr></thead><tbody>{trs}</tbody></table></div>\n')
nblk = len(blocks)
sec = f"""<!--datatables:start-->
  <h3 id="stats-data">The settled points, measured and modelled</h3>
  <p>Every settled core point, against the value equation (11) gives for it. Each cell reads &ldquo;measured / model&rdquo; in &deg;C; where a setting was measured more than once the cell gives the mean, with the number of points as a superscript. The model value includes the offset of the session in which the point was measured, so measured and model differ only by the residual. Case fans set to 2250&nbsp;rpm are counted with 2240&nbsp;rpm, and the column 2920 holds the case fans at full speed.</p>
{tabs}  <p class="ar-note">Points: {J['n']} settled values from the sessions listed under <a href="#stats">Statistical tests</a>. <a href="/research/data/gpu-map-steady-residuals.csv">Data (CSV)</a>.</p>
  <h3 id="stats-mem">The memory: a first model</h3>
  <p class="ar-status"><b>Provisional.</b> The memory is read in whole degrees and was fitted once, on fewer points than the core.</p>
  <p>The same two-path form fits the settled memory temperatures of val1, val2 and steady2, {MM['n']} points, with an offset per session: RMSE {MM['rmse']:.2f}&nbsp;&deg;C, leave-one-out {MM['loo']:.2f}&nbsp;&deg;C. Most of that is the rounding of the reading itself, whose standard deviation alone is about 0.29&nbsp;&deg;C.</p>
  <div class="ar-tw">
  <table class="ar-tab ar-num ar-set">
    <thead><tr><th scope="col">Constant</th><th scope="col">Estimate</th><th scope="col">SE</th></tr></thead>
    <tbody>{mrows}</tbody>
  </table>
  </div>
  <p class="ar-note">Session offsets against {MM['ref']}: {off}. Standard errors are classical; with whole-degree readings they are indicative only. <a href="/research/data/gpu-map-steady-memory.csv">Data (CSV)</a>.</p>
  <p>The striking constant is the offset, {P['θ0m'][0]:.0f}&nbsp;&deg;C against about 2&nbsp;&deg;C for the core. The memory carries heat of its own that hardly changes with the board power: the load keeps the memory equally busy at every power limit, so cutting the limit removes little of the memory&rsquo;s heat. That is the same fact, seen from the model&rsquo;s side, as the widening gap between memory and core at low power limits in <a href="#memlimit">Memory temperature</a>.</p>
  <details class="ar-det"><summary>All {nblk * 0 + 112} points of the second run: 60-second, settled and model values</summary>
  <p class="ar-note">For every setting of the second run, case fans by power limit, the core and memory as read after 60 seconds (marked *), the settled value where one was measured later, and the model value from equation (11) and the memory model, at 19.3&nbsp;&deg;C intake air and the reference session. A dash means the setting was not measured that way. The 60-second values at 575&nbsp;W read low and those at lower power limits read high, as described under <a href="#run2-settle">How long a point needs</a>.</p>
{cmp}  </details>
<!--datatables:end-->"""
a, b = s.find("<!--datatables:start-->"), s.find("<!--datatables:end-->")
if a < 0:
    i = s.index("<!--stats:end-->") + len("<!--stats:end-->"); s = s[:i] + "\n" + sec + s[i:]
else:
    s = s[:a] + sec + s[b + len("<!--datatables:end-->"):]
if ".ar-det{" not in s:
    s = s.replace(".ar-r2 sup{", ".ar-det{margin:18px 0}.ar-det>summary{cursor:pointer;font-weight:600;min-height:44px;display:flex;align-items:center}.ar-cmp{font-size:13.5px}.ar-cmp td,.ar-cmp th{white-space:nowrap;padding:8px 10px}.ar-cmp sup{font-size:.7em;margin-left:1px}.ar .ar-h4{font:600 15px/1.35 var(--sans);margin:22px 0 6px}\n@media (max-width:620px){.ar-cmp{font-size:12px}.ar-cmp td,.ar-cmp th{padding:7px 5px}.ar-cmp thead{display:table-header-group}.ar-cmp tr{display:table-row}.ar-cmp td{display:table-cell;border-top:1px solid var(--ring-l)}.ar-cmp td:nth-child(3){grid-column:auto;font-size:inherit;color:inherit}}\n.ar-r2 sup{", 1)
open(F, "w").write(s); print("data tables written:", nblk, "comparison blocks")
