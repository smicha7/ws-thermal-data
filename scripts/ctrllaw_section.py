"""Conclusions: the control law WS.Sensor implements, the figure of its fan settings and predicted temperatures against power,
the panel screenshots (placeholder until PNGs appear in research/gpu-panel-shots/). Between <!--ctrllaw:start/end-->. Usage: ctrllaw_section.py"""
import json, re, shutil, subprocess
from pathlib import Path
G = Path(__file__).resolve().parent.parent; SITE = Path.home() / "Claude/gruency-site"; F = SITE / "research/gpu-cooling-method.html"
M = json.load(open(G / "results-2026-10-23/modes-noise.json"))
TEX = [r"$$\hat T_{\mathrm{core}}(N,C,P)=T_{\mathrm{in}}+\theta_0+P\Big[r_\infty+\frac{1}{g_N (N/1000)^{m}+g_C (C/1500)^{s}}\Big]",
       r"$$\hat T_{\mathrm{mem}}(N,C,P)=T_{\mathrm{in}}+\theta_{0,\mathrm{mem}}+P\Big[r'_\infty+\frac{1}{g'_N (N/1000)^{m'}+g'_C (C/1500)^{s'}}\Big]",
       r"$$L(N,C)=10\log_{10}\!\big(10^{L_g(N)/10}+4\cdot 10^{L_f(C)/10}+3\cdot 10^{L_f(C_r)/10}\big),\quad L_g=32.5+50\log_{10}\tfrac{N}{1570},\quad L_f(x)=-167.1+60.2\log_{10}x,\quad C_r=\min(\max(C,888),2745)",
       r"$$(N^\ast,C^\ast)=\arg\min_{N,C}\ L(N,C)\quad\text{subject to}\quad L(N,C)\le B_{\mathrm{mode}},\ \ \hat T_{\mathrm{core}}\le T_{\mathrm{core}}^{\max}-\Delta_{\mathrm{core}},\ \ \hat T_{\mathrm{mem}}\le T_{\mathrm{mem}}^{\max}-\Delta_{\mathrm{mem}}",
       r"$$\text{if infeasible: }(N^\ast,C^\ast)=\arg\min_{L(N,C)\le B_{\mathrm{mode}}}\hat T_{\mathrm{core}};\ \text{if that breaks }T^{\max}:\ P_{\lim}\leftarrow\max(P_{\lim}-5\%,70\%)\text{ every }30\text{ s};\ \text{only at }70\%\text{ may }L>B_{\mathrm{mode}}",
       r"B_{\mathrm{mode}}", r"T_{\mathrm{core}}^{\max}", r"T_{\mathrm{mem}}^{\max}", r"N", r"C", r"P"]
H = json.loads(subprocess.run(["node", str(Path(__file__).parent / "tex.js")], input=json.dumps(TEX), capture_output=True, text=True, check=True).stdout)
_t0 = 1792749600   # 2026-10-23 12:00: only panels of the noise-budget version
shots = sorted(p for p in (G.parent / "gpu-panel-shots").glob("*.png") if p.stat().st_mtime > _t0 and "dark" not in p.name) if (G.parent / "gpu-panel-shots").exists() else []
for p in shots: shutil.copy(p, SITE / "research/img" / ("gpu-panel-" + p.name))
pic = lambda name, w, h, pw, ph, alt: "".join(f'<a class="ar-wide th-{t[0]}" href="/research/img/{name}-{t}.webp?v=1" aria-label="Open the chart at full size"><picture><source media="(max-width:620px)" srcset="/research/img/{name}-phone-{t}.webp?v=1" width="{pw}" height="{ph}"><img src="/research/img/{name}-{t}.webp?v=1" width="{w}" height="{h}" loading="lazy" decoding="async" alt="{alt}"></picture></a>' for t in ("light", "dark"))
LAW = json.load(open(G / "results-2026-10-23/ctrl-law.json"))
def pt(m):
    x = [r for r in LAW[m]["rows"] if int(r["P"]) == 575][0]
    return f'{m.capitalize()} {x["dBA"]:.1f}&nbsp;dBA with the core at {x["core"]:.1f}&nbsp;&deg;C (GPU fans {x["gpu_pct"]:.0f}&nbsp;%, case fans {x["case_rpm"]:.0f}&nbsp;rpm)'
shot_html = "".join(f'<img src="/research/img/gpu-panel-{p.name}" alt="WS.Sensor graphics-card cooling panel" loading="lazy" style="width:100%;height:auto;margin:6px 0">' for p in shots)

import sys as _s0; _s0.path.insert(0, str(G)); import model3
S3 = json.load(open(G / "results-2026-10-24/steady3-fit.json")); S3H = json.load(open(G / "data/steady3-2026-10-23/status.json"))["elapsed_s"] / 3600; FC3, FM3 = S3["forms"]["core"][model3.FORM], S3["forms"]["mem"][model3.FORM]
CP, MP = model3.P_core, model3.P_mem
def _eq(p, lhs, tag):
    v = {k: x for k, (x, _) in p.items()}
    return (r"$$\hat T_{\mathrm{" + lhs + r"}}=T_{\mathrm{in}}+" + f'{v["θ0"]:.2f}' + r"+P\Big[" + f'{v["r∞"]/1000:.4f}' + r"+\frac{1}{\dfrac{" + f'{v["gN"]:.1f}' + r"\,n^{" + f'{v["m"]:.2f}' + r"}}{" + f'{v["n½"]:.2f}' + r"^{" + f'{v["m"]:.2f}' + r"}+n^{" + f'{v["m"]:.2f}' + r"}}+" + f'{v["gC"]:.2f}' + r"\,c^{" + f'{v["s"]:.2f}' + r"}}\Big]\tag{" + tag + "}")
RT = [_eq(CP, "core", "R1"), _eq(MP, "mem", "R2"),
      r"$$L=10\log_{10}\!\Big(10^{\,[32.5+50\log_{10}(N/1570)]/10}+4\cdot10^{\,[-167.1+60.2\log_{10}C]/10}+3\cdot10^{\,[-167.1+60.2\log_{10}C_r]/10}\Big),\ \ C_r=\min(\max(C,888),2745)\tag{R3}"]
HR = json.loads(subprocess.run(["node", str(Path(__file__).parent / "tex.js")], input=json.dumps(RT), capture_output=True, text=True, check=True).stdout)
HK = json.loads(subprocess.run(["node", str(Path(__file__).parent / "tex.js")], input=json.dumps([re.sub(r"\\tag\{R\d\}", "", t) for t in RT]), capture_output=True, text=True, check=True).stdout)
UN = {"θ0": "&deg;C", "r∞": "m&deg;C/W", "gN": "W/&deg;C", "m": "&mdash;", "n½": "1000&nbsp;rpm", "gC": "W/&deg;C", "s": "&mdash;"}
SY = {"θ0": "&theta;<sub>0</sub>", "r∞": "r<sub>&infin;</sub>", "gN": "g<sub>N</sub>", "m": "m", "n½": "n<sub>&frac12;</sub>", "gC": "g<sub>C</sub>", "s": "s"}
_d = lambda k: 1 if k in ("r∞", "gN") else 2
_ci = lambda p, k: (p[k][0] - 1.96 * p[k][1], p[k][0] + 1.96 * p[k][1])
prow = "".join(f'<tr><td>{SY[k]}</td><td>{UN[k]}</td><td class="g">{CP[k][0]:.{_d(k)}f}</td><td>{_ci(CP, k)[0]:.{_d(k)}f}</td><td>{_ci(CP, k)[1]:.{_d(k)}f}</td>'
               f'<td class="g">{MP[k][0]:.{_d(k)}f}</td><td>{_ci(MP, k)[0]:.{_d(k)}f}</td><td>{_ci(MP, k)[1]:.{_d(k)}f}</td></tr>' for k in ("θ0", "r∞", "gN", "m", "n½", "gC", "s")).replace("-", "&minus;")
MAIN = f"""  <div class="ar-main" id="main-result">
  <p class="ar-main-h"><b>Main result.</b> The control law rests on three estimated equations: (R1) core temperature, (R2) memory temperature and (R3) fan noise, with N the GPU fan speed and C the case and radiator fan speed in rpm, P the board power in W and T<sub>in</sub> the intake air in &deg;C.</p>
  {HR[0]}{HR[1]}{HR[2]}
  </div>
  <p class="ar-tcap"><b>Estimated parameters of the three equations.</b> Core (R1) and memory (R2): the two-path form with a saturating GPU-fan conductance, fitted by nonlinear least squares to the {S3["n"]} settled points of the final grid (<a href="#est3">Section 4.1</a>); 95&nbsp;% intervals heteroscedasticity-consistent (HC3). Core RMSE {FC3["rmse"]:.2f}&nbsp;&deg;C, leave-one-out {FC3["loo"]:.2f}&nbsp;&deg;C; memory {FM3["rmse"]:.2f} and {FM3["loo"]:.2f}&nbsp;&deg;C.</p>
  <div class="ar-tw">
  <table class="ar-tab ar-num ar-st ar-ms ar-params">
    <thead><tr><th scope="col" rowspan="2">Parameter</th><th scope="col" rowspan="2">Unit</th><th scope="colgroup" colspan="3">Core (R1)</th><th scope="colgroup" colspan="3">Memory (R2)</th></tr><tr><th scope="col" class="g">estimate</th><th scope="col">95&nbsp;% CI, lower</th><th scope="col">95&nbsp;% CI, upper</th><th scope="col" class="g">estimate</th><th scope="col">95&nbsp;% CI, lower</th><th scope="col">95&nbsp;% CI, upper</th></tr></thead>
    <tbody>{prow}</tbody>
  </table>
  </div>
  <p class="ar-note">Noise (R3) has no estimated parameters of its own: 32.5&nbsp;dBA at 1570&nbsp;rpm for the card&rsquo;s fans at 1&nbsp;m (GamersNexus) scaled by the fan law 50&nbsp;log<sub>10</sub> of the speed ratio; a = &minus;167.1 and b = 60.2&nbsp;dB per decade of speed for one Silent Wings Pro 4 120 at 1&nbsp;m, a least-squares fit to Hardware Busters&rsquo; measurements, used for the four be quiet! case fans at C and, provisionally, for the three SilverStone radiator fans at their measured speed C<sub>r</sub>, which floors at 888 and tops out at 2745&nbsp;rpm; all summed on an energy basis (<a href="#noise-model">Section 2.5.4</a>, <a href="#appendix-e">Appendix E</a>). n = N/1000 and c = C/1500 (N, C in rpm). &theta;<sub>0</sub>: offset independent of power; r<sub>&infin;</sub>: resistance no airflow removes; g<sub>N</sub>: ceiling of the GPU-fan conductance, reached half-way at n<sub>&frac12;</sub>, with steepness m; g<sub>C</sub>: conductance of the case-fan path at C = 1500&nbsp;rpm, with exponent s (m, s dimensionless).</p>
"""

import sys as _sys; _sys.path.insert(0, str(G)); import controller_sim as cs
PR = ""
for _m in ("quiet", "balanced", "performance"):
    _c = cs.Controller(_m)
    for _T in (19.3, 25.0, 30.0, 35.0):
        _N, _C, _pl, _ov = _c.make_plan(575, _T); _core, _mem = cs.steady_ff(575 * _pl, _N, _C, _T)
        PR += (f'<tr><td>{_m.capitalize()} ({_c.budget:.0f})</td><td>{_T:.1f}</td><td class="g">{_pl*100:.0f}</td><td>{575*_pl:.0f}</td><td class="g">{cs.RPM_DUTY(_N):.1f}</td><td>{_C:.0f}</td>'
               f'<td class="g">{cs.noise(_N, _C):.1f}{"<sup>a</sup>" if _ov else ""}</td><td>{_core:.1f}</td><td>{_mem:.1f}</td></tr>')
POWER = f"""  <h3 id="power-room">Power limit and room temperature</h3>
  <p>The same law answers how much power each mode can keep in a warmer room. Under full load Quiet gives up power first, Balanced only at 35&nbsp;&deg;C intake air, and Performance keeps full power up to 35&nbsp;&deg;C by spending its larger budget. Power costs speed: at 402&nbsp;W, a 70&nbsp;% limit, the core clock was about 24&nbsp;% lower in the preliminary runs (<a href="#power-results">Appendix A.2.6</a>).</p>
  <p class="ar-tcap"><b>Power limit each mode settles at under full load (575&nbsp;W requested) against intake air temperature, with its fans, noise and predicted temperatures.</b> Planning of the released controller with equations (R1) and (R2), literature-based noise at 1&nbsp;m.</p>
  <div class="ar-tw ar-tw-wide">
  <table class="ar-tab ar-num ar-st ar-ms ar-proom">
    <thead><tr><th scope="col" rowspan="2">Mode (budget, dBA)</th><th scope="col" rowspan="2">Intake air, &deg;C</th><th scope="colgroup" colspan="2">Power limit</th><th scope="colgroup" colspan="2">Fans</th><th scope="col" rowspan="2" class="g">Total noise at 1&nbsp;m, dBA</th><th scope="col" rowspan="2">Core, &deg;C</th><th scope="col" rowspan="2">Memory, &deg;C</th></tr><tr><th scope="col" class="g">%</th><th scope="col">W</th><th scope="col" class="g">GPU, %</th><th scope="col">case, rpm</th></tr></thead>
    <tbody>{PR}</tbody>
  </table>
  </div>
  <p class="ar-note"><sup>a</sup> The power limit is at its 70&nbsp;% floor and the fans exceed the budget to hold the safety limits.</p>
"""
PANEL = ""
if shots:
    PANEL = f"""  <figure class="ar-fig ar-ph">
    {shot_html}
    <figcaption><b>Figure 0.</b> WS.Sensor graphics-card cooling panel: three noise preferences, Quiet, Normal and Performance (30, 35 and 40&nbsp;dBA at 1&nbsp;m), and the two adjustable upper temperature limits, core and memory.</figcaption>
  </figure>"""


import csv as _csv
_rows = list(_csv.DictReader(open(Path.home() / "Claude/gruency-site/research/data/gpu-map-steady3-cells.csv")))
def _st(meas, mod):
    e = [float(r[meas]) - float(r[mod]) for r in _rows]; n = len(e)
    return dict(n=n, mean=sum(e) / n, rmse=(sum(x * x for x in e) / n) ** 0.5, mx=max(abs(x) for x in e), w1=sum(1 for x in e if abs(x) <= 1.0))
VC, VM = _st("core_measured_c", "core_earlier_model_c"), _st("mem_measured_c", "mem_earlier_model_c")
def _rm(g):
    e = [float(r["core_measured_c"]) - float(r["core_earlier_model_c"]) for r in _rows if int(r["gpu_pct"]) == g]
    return (sum(x * x for x in e) / len(e)) ** 0.5
BYG = ", ".join(f"{g}&nbsp;% {_rm(g):.2f}" for g in sorted({int(r["gpu_pct"]) for r in _rows}))
_gp = sorted({int(r["gpu_pct"]) for r in _rows}); _pl = sorted({int(r["pl_pct"]) for r in _rows})
FC3c = S3["forms"]["core"]["current"]
fmt = lambda x: f"{x:+.2f}".replace("+", "+").replace("-", "&minus;")
VTAB = f"""<!--validation:start-->
  <h3 id="validation">Cross-check: the earlier-session model on the final grid</h3>
  <p>The model estimated on the 79 points of the earlier sessions (<a href="#stats">Section 4.2</a>) never saw the final grid, so the grid tests it out of sample. Over all {VC["n"]} cells it predicts the settled core within &plusmn;1&nbsp;&deg;C at {VC["w1"]} of {VC["n"]} points and the memory within &plusmn;1&nbsp;&deg;C at {VM["w1"]} of {VM["n"]}; the mean errors are {fmt(VC["mean"])} and {fmt(VM["mean"])}&nbsp;&deg;C. The core RMSE by GPU fan speed is {BYG}&nbsp;&deg;C. Its out-of-sample core RMSE, {VC["rmse"]:.2f}&nbsp;&deg;C, is close to the in-sample RMSE of the same form fitted to the grid itself ({FC3c["rmse"]:.2f}&nbsp;&deg;C, {{tref:forms3}}): the earlier sessions had already pinned down what this form can describe, and the gain of the primary model comes from its saturating GPU-fan term, not from more data.</p>
  <p class="ar-tcap"><b>Out-of-sample accuracy of the earlier-session model on the final grid (steady3).</b> Error = measured minus predicted settled temperature; model (11) and the earlier memory model, estimated on the earlier sessions only; {VC["n"]} points at GPU fans {", ".join(str(g) for g in _gp)}&nbsp;%, case fans 800&nbsp;rpm to full speed, power limits {", ".join(str(p) for p in _pl)}&nbsp;%.</p>
  <div class="ar-tw">
  <table class="ar-tab ar-num ar-st ar-valid">
    <thead><tr><th scope="col">Quantity</th><th scope="col">Points</th><th scope="col">Mean error, &deg;C</th><th scope="col">RMSE, &deg;C</th><th scope="col">Largest |error|, &deg;C</th><th scope="col">Within &plusmn;1&nbsp;&deg;C</th></tr></thead>
    <tbody><tr><td>Core</td><td>{VC["n"]}</td><td>{fmt(VC["mean"])}</td><td>{VC["rmse"]:.2f}</td><td>{VC["mx"]:.2f}</td><td>{VC["w1"]}</td></tr><tr><td>Memory</td><td>{VM["n"]}</td><td>{fmt(VM["mean"])}</td><td>{VM["rmse"]:.2f}</td><td>{VM["mx"]:.2f}</td><td>{VM["w1"]}</td></tr></tbody>
  </table>
  </div>
  <p class="ar-note">The memory is read in whole degrees, which alone adds a rounding error of up to 0.5&nbsp;&deg;C. All figures are computed from unrounded model values. <a href="/research/data/gpu-map-steady3-cells.csv">Data (CSV)</a>, columns core_earlier_model_c and mem_earlier_model_c.</p>
<!--validation:end-->"""
KEY = f"""<!--keyresult:start-->
  <section class="ar-abs ar-keyres" aria-labelledby="kr-h">
    <h2 id="kr-h" class="ar-key-h">Key result</h2>
    <p>The control law rests on three estimated equations, core temperature, memory temperature and fan noise (R1 to R3, <a href="#main-result">Section 5.1</a>), with N the GPU fan speed and C the case and radiator fan speed in rpm, P the board power in W and T<sub>in</sub> the intake air in &deg;C.</p>
    {HK[0]}{HK[1]}{HK[2]}
    <p>Fitted to the {S3["n"]} settled points of the final grid, the equations give the core within &plusmn;1&nbsp;&deg;C at {FC3["w1"]} of {S3["n"]} points (RMSE {FC3["rmse"]:.2f}&nbsp;&deg;C, leave-one-out {FC3["loo"]:.2f}&nbsp;&deg;C; memory {FM3["rmse"]:.2f}&nbsp;&deg;C; {{tref:params}}). A model estimated on six earlier sessions predicts the same grid within {VC["rmse"]:.2f}&nbsp;&deg;C ({{tref:valid}}).</p>
    <p>From them follows the control curve of each mode ({{fref:fig-the-control-law-fan-speeds-noise-and-pre}}): within a noise budget of 30, 35 or 40&nbsp;dBA the quietest fan pair that keeps the core and memory at the mode&rsquo;s comfort level, and a lower power limit only when the budget cannot hold the safety limits.</p>
  </section>
<!--keyresult:end-->"""
SIM = json.load(open(G / "results-2026-10-22/controller-sim.json"))
_k = lambda sc, m: next(v for k, v in SIM[sc].items() if k.startswith("WS.Sensor " + m))
_ms = ("quiet", "balanced", "performance")
_ov = sum((_k(sc, m)["s_over"] or 0) + (_k(sc, m)["s_over_budget"] or 0) for sc in SIM for m in _ms)
_rv = max(_k("bursts 60 s on/off", m)["card_reversals_per_min"] for m in _ms)
_w = {m: _k("intake 19->30 °C", m) for m in _ms}
_cut = [m.capitalize() for m in _ms if _w[m]["pl_min"] < 1]; _full = [m for m in _ms if _w[m]["pl_min"] >= 1]
SIMTXT = (("no mode spent a second over a limit or over its budget" if _ov == 0 else f"the modes spent {_ov}&nbsp;s over a limit or budget in all")
          + (", and none reversed its fans under 60-second bursts of load" if _rv == 0 else f", with at most {_rv:.2f} fan reversals per minute under 60-second bursts")
          + "; with the intake air rising from 19.3 to 30&nbsp;&deg;C, "
          + (" and ".join(f'{m} held its budget by lowering the power limit to {_w[m.lower()]["pl_min"]*100:.0f}&nbsp;%' for m in _cut) + ", while " if _cut else "")
          + " and ".join(m.capitalize() for m in _full) + " stayed at full power with the core at " + " and ".join(f'{_w[m]["peak"]:.1f}' for m in _full) + "&nbsp;&deg;C")
sec = f"""<!--ctrllaw:start-->
  <h3 id="control-law">The derived control law</h3>
  <p>The measurements, the models and the tests lead to one control law, which WS.Sensor implements.</p>
{MAIN}
  <p>Each mode is a noise budget {H[5]}, a ceiling: 30&nbsp;dBA for Quiet, 35 for Balanced (shown as Normal in WS.Sensor) and 40 for Performance, with comfort distances &Delta; below the safety limits {H[6]}, 83&nbsp;&deg;C by default and at most 88&nbsp;&deg;C, and {H[7]}, 90&nbsp;&deg;C by default and never above 91&nbsp;&deg;C: 5 and 3&nbsp;&deg;C in Quiet, 10 and 5&nbsp;&deg;C in Balanced, 15 and 8&nbsp;&deg;C in Performance. The controller picks the quietest pair within the budget that holds both comfort levels; only if none does, the coolest pair within the budget, then a lower power limit, and only at the power-limit floor a pair over the budget:</p>
  {H[3]}{H[4]}
  <p>At light load the comfort levels are met at the fan floors, so every mode runs at the same {_k("light 30->150 W", "quiet")["noise_mean"]:.1f}&nbsp;dBA; as the power rises the fans rise only as far as the comfort level requires, and the modes part when their budgets are reached. At 575&nbsp;W the planned operating points are {pt('quiet')}, {pt('balanced')} and {pt('performance')}. In simulation of the released controller (WS.Sensor 0.30.69) {SIMTXT} (<a href="#controller-res">Section 3.5</a>).</p>
  <figure class="ar-fig ar-fig-wide">
    {pic("gpu-map-ctrl-law", 2600, 1720, 1000, 2800, "Four panels against board power for the Quiet, Balanced and Performance modes: GPU fan speed, case fan speed, total noise with each budget, and predicted core with each comfort level; all modes sit at the fan floors at low power and rise only as far as the comfort level requires")}
    <figcaption><b>Figure 0.</b> Planned fan speeds of the released controller against board power at full load, intake air 19.3&nbsp;&deg;C: GPU fans in % and rpm (top left), case and radiator fans in rpm and % (top right), total noise at 1&nbsp;m with each mode&rsquo;s budget dotted (bottom left), and predicted core with each mode&rsquo;s comfort level dotted (bottom right). Colours: Quiet (&le;&nbsp;30&nbsp;dBA) green, Balanced (&le;&nbsp;35&nbsp;dBA) blue, Performance (&le;&nbsp;40&nbsp;dBA) red.</figcaption>
  </figure>
{PANEL}
{POWER}<!--ctrllaw:end-->"""
s = F.read_text(); a, b = s.index("<!--ctrllaw:start-->"), s.index("<!--ctrllaw:end-->") + len("<!--ctrllaw:end-->")
s = s[:a] + sec + s[b:]
a, b = s.index("<!--keyresult:start-->"), s.index("<!--keyresult:end-->") + len("<!--keyresult:end-->")
s = s[:a] + KEY + s[b:]
a, b = s.index("<!--validation:start-->"), s.index("<!--validation:end-->") + len("<!--validation:end-->")
s = s[:a] + VTAB + s[b:]
ABS = (f'On a final grid of {S3["n"]} settled points (GPU fans {_gp[0]} to {_gp[-1]}&nbsp;%, case and radiator fans 800&nbsp;rpm to full speed, 402 to 575&nbsp;W; {S3H:.1f}&nbsp;h) we estimated a two-path thermal-resistance model, two conductances in parallel, one per fan set, the GPU-fan one saturating; '
       f'it fits the core within {FC3["rmse"]:.2f}&nbsp;&deg;C (leave-one-out {FC3["loo"]:.2f}&nbsp;&deg;C, {FC3["w1"]} of {S3["n"]} points within &plusmn;1&nbsp;&deg;C) and the memory within {FM3["rmse"]:.2f}&nbsp;&deg;C. '
       f'The same model without saturation, estimated on 79 points from six earlier sessions, predicts this grid within {VC["rmse"]:.2f}&nbsp;&deg;C.')
_bc, _bm = S3["forms"]["core"]["power exponent β"], S3["forms"]["mem"]["power exponent β"]
_xs = S3["crosscheck_earlier"]["core"]; _sp = S3["forms"]["core"]["spline benchmark (4×4 tensor)"]
GEN = {
 "interp": (f'Two cooling paths in parallel, the GPU-fan path saturating above about {CP["n½"][0]*1000:.0f}&nbsp;rpm, fit the {S3["n"]} settled points of the final grid within {FC3["rmse"]:.2f}&nbsp;&deg;C (leave-one-out {FC3["loo"]:.2f}&nbsp;&deg;C); '
            f'without saturation the same form, estimated on six earlier sessions, predicts that grid within {VC["rmse"]:.2f}&nbsp;&deg;C. What remains is a smooth error of shape, about {(FC3["rmse"]**2 - _sp["rmse"]**2)**0.5:.2f}&nbsp;&deg;C root-mean-square, and between sessions an offset of up to about {max(abs(v) for v in _xs["by_session"].values()):.1f}&nbsp;&deg;C, most likely the temperature of the air reaching the card.'),
 "limits": (f'though offset and slope are hard to separate in this range. On the final grid a power exponent on the fan term comes out at {_bc["x"][6]:.2f} &plusmn; {_bc["se"][6]:.2f} for the core and {_bm["x"][6]:.2f} &plusmn; {_bm["se"][6]:.2f} for the memory, so the fan-dependent resistance may grow slightly with power; '
            f'it lowers BIC for the memory but not for the core (<a href="#est3">Section 4.1</a>). The intake air varied by only {S3["tin"]["sd"]:.2f}&nbsp;&deg;C during the final grid, so the coefficient of T<sub>in</sub> is assumed, not measured. '
            f'The earlier sessions differ from it by an offset of up to {max(abs(v) for v in _xs["by_session"].values()):.1f}&nbsp;&deg;C, probably warmer air at the card&rsquo;s intake than at our sensor; a sensor at the card&rsquo;s intake will test this.'),
 "concl": (f'Five findings carry the control law. The card&rsquo;s own fans do most of the cooling, with diminishing returns above about {CP["n½"][0]*1000:.0f}&nbsp;rpm; the case fans matter only when the card&rsquo;s fans are slow. '
           f'A two-path model with a saturating GPU-fan path, estimated on the {S3["n"]} settled points of the final grid, gives the settled core within {FC3["rmse"]:.2f}&nbsp;&deg;C (leave-one-out {FC3["loo"]:.2f}&nbsp;&deg;C), and the earlier-session model predicted the same grid within {VC["rmse"]:.2f}&nbsp;&deg;C. '
           f'At full power the memory, not the core, reaches its limit first. The quietest fan pairs keep the case fans near their minimum. And a first controller built on the model held its targets on the real card within 1&nbsp;&deg;C.'),
}
for _g, _t in GEN.items():
    if f"<!--g:{_g}-->" in s: s = s[:s.index(f"<!--g:{_g}-->") + len(f"<!--g:{_g}-->")] + _t + s[s.index(f"<!--/g:{_g}-->"):]
if "<!--absval-->" in s: s = s[:s.index("<!--absval-->") + 13] + ABS + s[s.index("<!--/absval-->"):]
F.write_text(s); print("control law written; screenshots:", len(shots))
