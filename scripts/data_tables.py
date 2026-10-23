"""Builds the data-tables block (<!--datatables:start--> … <!--datatables:end-->) after the statistical tests:
settled core points measured / model per power limit, the provisional memory model, and the 112-point comparison (60 s / settled / model)."""
import json, re, pandas as pd, numpy as np
G = "/Users/smicha/Applications/Pasek/research/gpu-map/"; F = "/Users/smicha/Claude/gruency-site/research/gpu-cooling-method.html"
s = open(F).read()
D = pd.read_csv(G + "results-2026-10-22/steady-residuals.csv"); J = json.load(open(G + "results-2026-10-22/steady-stats.json"))
MM = json.load(open(G + "results-2026-10-23/mem-model.json"))
D["case"] = D.case_target.replace({2250: 2240, 3000: 2920})
lab = lambda c: {2920: "2920 (full speed)", 3000: "2920 (full speed)"}.get(c, str(c))
def pltab(pl):
    d = D[D.pl_pct == pl]; body = ""
    for (g, c), q in d.groupby(["gpu_pct", "case"]):
        body += f'<tr><td>{g}</td><td>{lab(c).replace(" (full speed)", "")}{"<sup>a</sup>" if c in (2920, 3000) else ""}</td><td>{q.core_settled.mean():.1f}</td><td>{q.fitted.mean():.1f}</td><td>{len(q)}</td></tr>'
    w = round(575 * pl / 100)
    return (f'<h4 class="ar-h4">Earlier sessions (21&ndash;22 October), power limit {pl}&nbsp;% ({w}&nbsp;W): settled core temperature in &deg;C, measured and predicted by model (11), one row per measured setting; {len(d)} settled points.</h4>\n'
            f'  <div class="ar-tw"><table class="ar-tab ar-num ar-old"><thead><tr><th scope="col">GPU fans, %</th><th scope="col">Case fans, rpm</th><th scope="col">Core, measured, &deg;C</th><th scope="col">Core, predicted by model, &deg;C</th><th scope="col">Settled measurements averaged, n</th></tr></thead><tbody>{body}</tbody></table></div>\n')
tabs = "".join(pltab(p) for p in (100, 90, 80, 70))
P = MM["params"]; nm = {"θ0m": "&theta;<sub>0,mem</sub>", "r∞": "r<sub>&infin;</sub>", "gN": "g<sub>N</sub>", "m": "m", "gC": "g<sub>C</sub>", "s": "s"}
un = {"θ0m": "&deg;C", "r∞": "m&deg;C/W", "gN": "W/&deg;C", "gC": "W/&deg;C", "m": "", "s": ""}
mrows = "".join(f"<tr><td>{nm.get(k, k)}</td><td>{un.get(k,'&deg;C') or '&mdash;'}</td><td>{v[0]:.2f}</td><td>{v[1]:.2f}</td></tr>" for k, v in P.items() if not k.startswith("θ["))
off = "; ".join(f"{k[2:-1]} {v[0]:+.2f}&nbsp;&deg;C".replace("+-", "&minus;").replace("-", "&minus;") for k, v in P.items() if k.startswith("θ["))
# 112-point comparison, computed from the data by compare_tables.py
CMP = json.load(open(G + "results-2026-10-23/compare-112.json"))
f1 = lambda v, d=1: "&mdash;" if v is None else f"{v:.{d}f}&nbsp;&deg;C"
cmp = ""
for blk in CMP:
    trs = "".join(f"<tr><td>{r['gpu']}{'<sup>a</sup>' if r['c60'] is None else ''}</td><td>{r['rpm']}</td><td class='g'>{f1(r['c60'])}</td><td>{f1(r['cs'])}</td><td>{r['cm']:.1f}&nbsp;&deg;C</td><td class='g'>{f1(r['m60'],0)}</td><td>{f1(r['ms'],0) + ('<sup>b</sup>' if r['ms'] is None and r['cs'] is not None else '')}</td><td>{r['mmod']:.1f}&nbsp;&deg;C</td></tr>" for r in blk["rows"])
    cmp += (f'<h4 class="ar-h4">Second run, case fans {lab(blk["case"]).replace(" (full", "&nbsp;rpm (full") if blk["case"] in (2920, 3000) else lab(blk["case"]) + "&nbsp;rpm"}, power limit {blk["pl"]}&nbsp;% ({blk["w"]}&nbsp;W): core and memory temperature after 60&nbsp;s, settled, and from the model.</h4>\n'
            f'<div class="ar-tw"><table class="ar-tab ar-num ar-cmp ar-ms"><thead><tr><th scope="col" rowspan="2">GPU fans, %</th><th scope="col" rowspan="2">GPU fans, rpm</th><th scope="colgroup" colspan="3">Core temperature</th><th scope="colgroup" colspan="3">Memory temperature</th></tr><tr><th scope="col" class="g">after 60&nbsp;s</th><th scope="col">settled (&ge;&nbsp;5&nbsp;min)</th><th scope="col">model (eq. 11)</th><th scope="col" class="g">after 60&nbsp;s, whole &deg;C</th><th scope="col">settled, whole &deg;C</th><th scope="col">model</th></tr></thead><tbody>{trs}</tbody></table></div>\n')
blocks = CMP
nblk = len(blocks)
sec = f"""<!--datatables:start-->
  <h3 id="stats-data">Earlier sessions (21&ndash;22 October)</h3>
  <p>The settled core points of the sessions before steady3, against the value equation (11) gives for them; these are the points the model was fitted to.</p>
{tabs}  <p class="ar-note">One row per setting that was measured. Core measured: the settled core temperature; where a setting was measured more than once, the mean; the last column gives how many settled measurements of this setting were averaged. Core, predicted by model: equation (11) (<a href="#stats-model">The model</a>) with the offset of the session in which the point was measured, so the two differ only by the residual. Case fans set to 2250&nbsp;rpm are counted with 2240&nbsp;rpm. <sup>a</sup> 2920&nbsp;rpm: full speed, whether set as full speed or as 3000&nbsp;rpm. Points: {J['n']} settled values from the sessions listed under <a href="#stats">Statistical tests</a>. <a href="/research/data/gpu-map-steady-residuals.csv">Data (CSV)</a>.</p>
<!--datatables:end-->
<!--dtmem:start-->
  <h3 id="stats-mem">The memory: a first model</h3>
  <p class="ar-status"><b>Provisional.</b> The memory is read in whole degrees and was fitted once, on fewer points than the core.</p>
  <p>The same two-path form fits the settled memory temperatures of {', '.join(list(MM['sessions'])[:-1])} and {list(MM['sessions'])[-1]}, {MM['n']} points, with an offset per session: RMSE {MM['rmse']:.2f}&nbsp;&deg;C, leave-one-out {MM['loo']:.2f}&nbsp;&deg;C. Most of that is the rounding of the reading itself, whose standard deviation alone is about 0.29&nbsp;&deg;C.</p>
  <div class="ar-tw">
  <table class="ar-tab ar-num ar-set">
    <thead><tr><th scope="col">Constant</th><th scope="col">Unit</th><th scope="col">Estimate</th><th scope="col">Standard error</th></tr></thead>
    <tbody>{mrows}</tbody>
  </table>
  </div>
  <p class="ar-note">Same form as equation (11), for the memory: &theta;<sub>0,mem</sub>, the temperature offset that does not depend on power; r<sub>&infin;</sub>, the resistance no airflow removes; g<sub>N</sub>, g<sub>C</sub>, the conductance of the GPU-fan and case-fan paths; m, s, their exponents (dimensionless, &mdash; in the Unit column). Session offsets against {MM['ref']}: {off}. Standard errors are classical; with whole-degree readings they are indicative only. <a href="/research/data/gpu-map-steady-memory.csv">Data (CSV)</a>.</p>
  <p>The striking constant is the offset, {P['θ0m'][0]:.0f}&nbsp;&deg;C against about 2&nbsp;&deg;C for the core. The memory carries heat of its own that hardly changes with the board power: the load keeps the memory equally busy at every power limit, so cutting the limit removes little of the memory&rsquo;s heat. That is the same fact, seen from the model&rsquo;s side, as the widening gap between memory and core at low power limits in <a href="#memlimit">Memory temperature</a>.</p>
<!--dtmem:end-->
<!--dt112:start-->
  <h3 id="stats-112">All 112 points of the second run</h3>
  <p>For every setting of the second run, the readings after 60 seconds, the settled values and the model, side by side.</p>
{cmp}  <p class="ar-note">For every setting of the second run, case fans by power limit, the core and memory as read after 60 seconds, the settled value where one was measured later, and the model value from equation (11) and the memory model, at 19.3&nbsp;&deg;C intake air and the reference session. A dash (&mdash;) means the setting was not measured that way. GPU fans, rpm: the measured mean at this setting. <sup>a</sup> No 60-second value: a settled point from another session at this setting. <sup>b</sup> The settled memory reading was not logged for this point. Memory readings are whole degrees, as the card reports them. The 60-second values at 575&nbsp;W read low and those at lower power limits read high, as described under <a href="#run2-settle">How long a point needs</a>. <a href="/research/data/gpu-map-compare-112.csv">All rows (CSV)</a>.</p>
<!--dt112:end-->"""
import re as _re
blocks = dict((k, v) for k, v in _re.findall(r"<!--(datatables|dtmem|dt112):start-->(.*?)<!--\1:end-->", sec, _re.S))
if "<!--dtmem:start-->" in s:
    for k, v in blocks.items():
        a, b = s.index(f"<!--{k}:start-->"), s.index(f"<!--{k}:end-->") + len(f"<!--{k}:end-->")
        s = s[:a] + f"<!--{k}:start-->{v}<!--{k}:end-->" + s[b:]
else:   # first run after the split: replace the old combined block by the three blocks in a row
    a, b = s.find("<!--datatables:start-->"), s.find("<!--datatables:end-->")
    s = s[:a] + sec + s[b + len("<!--datatables:end-->"):]
open(F, "w").write(s); print("data tables written:", nblk, "comparison blocks")
