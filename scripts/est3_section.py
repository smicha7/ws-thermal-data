"""Section 4.1: the primary fit on the final grid (steady3 alone): form comparison table, choice, diagnostics, residual figure,
cross-check on the earlier sessions. From results-2026-10-24/steady3-fit.json and steady3-points.csv (steady3_fit.py).
Writes <!--est3:start/end--> before <!--stats:start--> and research/img/gpu-map-s3-resid-*.webp. Usage: est3_section.py"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from PIL import Image
G = Path(__file__).resolve().parent.parent; SITE = Path.home() / "Claude/gruency-site"; F = SITE / "research/gpu-cooling-method.html"; IMG = SITE / "research/img"; OUT = Path(__file__).resolve().parent / "out/s3"; OUT.mkdir(parents=True, exist_ok=True)
J = json.load(open(G / "results-2026-10-24/steady3-fit.json")); D = pd.read_csv(G / "results-2026-10-24/steady3-points.csv")
FC, FM = J["forms"]["core"], J["forms"]["mem"]; CH = J["choice"]["core"]; HC, HM = FC[CH], FM[CH]; CUR = FC["current"]; dg = J["diag"]; xc = J["crosscheck_earlier"]; dr = J["drift"]
ORDER = ["current", "power exponent β", "N×C interaction", "case exponent depends on N", "GPU-fan saturation (Hill)", "Hill + N×C", "spline benchmark (4×4 tensor)"]
LBL = {"current": "Two conductances, power law in each fan speed (current)", "power exponent β": "&hellip; with P<sup>&beta;</sup> on the fan term",
       "N×C interaction": "&hellip; with an N&times;C interaction conductance", "case exponent depends on N": "&hellip; with the case exponent depending on N",
       "GPU-fan saturation (Hill)": "&hellip; with a saturating GPU-fan conductance (Hill)", "Hill + N×C": "&hellip; saturating, with an N&times;C interaction",
       "spline benchmark (4×4 tensor)": "Benchmark: P times a 4&times;4 tensor spline in N and C"}
b0c, b0m = FC[CH]["bic"], FM[CH]["bic"]
adm = J["admissible"]
rows = ""
for k in ORDER:
    c, m = FC[k], FM[k]
    note = "" if "spline" in k else ("" if adm["core"][k] and adm["mem"][k] else "<sup>a</sup>")
    cls = ' class="sel"' if k == CH else ""
    rows += (f'<tr{cls}><td>{LBL[k]}{note}</td><td>{c["k"]}</td><td class="g">{c["rmse"]:.2f}</td><td>{c["loo"]:.2f}</td><td>{c["cv10"]:.2f}</td><td>{c["bic"] - b0c:+.1f}</td><td>{c["w1"]}</td>'
             f'<td class="g">{m["rmse"]:.2f}</td><td>{m["loo"]:.2f}</td><td>{m["bic"] - b0m:+.1f}</td></tr>').replace("+0.0", "0.0").replace("-", "&minus;")
import csv as _csv
_r = list(_csv.DictReader(open(SITE / "research/data/gpu-map-steady3-cells.csv"))); VE = (sum((float(r["core_measured_c"]) - float(r["core_earlier_model_c"])) ** 2 for r in _r) / len(_r)) ** 0.5
n = J["n"]; pv = {nm: x for nm, x in zip(HC["names"], HC["x"])}
beta = {q: J["forms"][q]["power exponent β"]["x"][6] for q in ("core", "mem")}
hn = lambda r: f"{r:.0f}"
nhalf_rpm = pv["n½"] * 1000; nhalf_pct = (nhalf_rpm - 180) / 28.33
fm = lambda x, d=2: f"{x:+.{d}f}".replace("-", "&minus;")
TAB = f"""  <p class="ar-tcap"><b>Forms of the settled-temperature model fitted to the final grid alone ({n} points), core and memory: fit, prediction error and BIC.</b> All forms T&nbsp;&minus;&nbsp;T<sub>in</sub> = &theta;<sub>0</sub> + P&middot;[r<sub>&infin;</sub> + 1/G(N,&nbsp;C)], nonlinear least squares; LOO by refitting without each point, 10-fold CV with fixed folds; &Delta;BIC against the chosen form (negative = better).</p>
  <div class="ar-tw ar-tw-wide">
  <table class="ar-tab ar-num ar-st ar-ms ar-forms3">
    <thead><tr><th scope="col" rowspan="2">Form</th><th scope="col" rowspan="2">Parameters</th><th scope="colgroup" colspan="5">Core, &deg;C</th><th scope="colgroup" colspan="3">Memory, &deg;C</th></tr>
    <tr><th scope="col" class="g">RMSE</th><th scope="col">LOO</th><th scope="col">10-fold CV</th><th scope="col">&Delta;BIC</th><th scope="col">within &plusmn;1&nbsp;&deg;C</th><th scope="col" class="g">RMSE</th><th scope="col">LOO</th><th scope="col">&Delta;BIC</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  </div>
  <p class="ar-note"><sup>a</sup> Physically inadmissible in at least one fit: a negative conductance or interaction (Hill&nbsp;+&nbsp;N&times;C on the core; N&times;C on the memory). The memory is read in whole degrees. <a href="/research/data/gpu-map-steady3-fit.json">Fit results (JSON)</a>.</p>
"""
# ---- residual figure
TH = {"light": dict(bg="#ffffff", fg="#1d1d1f", grid="#d9d9de", dim="#86868b"), "dark": dict(bg="#141414", fg="#f5f5f7", grid="#3a3a3c", dim="#98989d")}
PLC = {100: "#ff453a", 90: "#ff9f0a", 80: "#30a46c", 70: "#0a84ff"}
def fig(theme, phone):
    th = TH[theme]; fs = 13 if phone else 11
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Arial", "DejaVu Sans"], "font.size": fs})
    Fg, ax = plt.subplots(4, 2, figsize=(5.2, 13)) if phone else plt.subplots(2, 4, figsize=(15, 6.6), sharey="row")
    Fg.patch.set_facecolor(th["bg"]); ax = ax.T if phone else ax
    X = [("N", "GPU fans, rpm"), ("C", "Case and radiator fans, rpm"), ("P", "Board power, W"), ("t", "Time since start, h")]
    for i, q in enumerate(("core", "mem")):
        e = D[q + "_e"]
        for j, (col, xl) in enumerate(X):
            a = ax[i][j]; a.set_facecolor(th["bg"])
            for sp in a.spines.values(): sp.set_visible(False)
            a.tick_params(colors=th["fg"], labelsize=fs - 2, length=0); a.grid(color=th["grid"], lw=0.6); a.set_axisbelow(True)
            xs = D[col] + (np.random.default_rng(j).uniform(-4, 4, len(D)) if col == "P" else 0)
            for pl, cl in PLC.items():
                k = D.pl == pl; a.scatter(xs[k], e[k], s=14, color=cl, alpha=0.8, lw=0, label=f"{pl} %")
            a.axhline(0, color=th["dim"], lw=0.8); a.axhline(1, color=th["dim"], lw=0.6, ls=":"); a.axhline(-1, color=th["dim"], lw=0.6, ls=":")
            a.set_xlabel(xl, color=th["fg"]); a.set_ylim(-2.5, 2.5)
            if col == "N":
                s2 = a.secondary_xaxis("top", functions=(lambda r: (r - 180) / 28.33, lambda d: 180 + 28.33 * d)); s2.set_xlabel("GPU fans, %", color=th["fg"], fontsize=fs - 2)
                s2.tick_params(colors=th["fg"], labelsize=fs - 3, length=0)
                for sp in s2.spines.values(): sp.set_visible(False)
            if col == "C":
                s2 = a.secondary_xaxis("top", functions=(lambda r: r / 2920 * 100, lambda d: d * 29.2)); s2.set_xlabel("Case fans, % of full speed", color=th["fg"], fontsize=fs - 2)
                s2.tick_params(colors=th["fg"], labelsize=fs - 3, length=0)
                for sp in s2.spines.values(): sp.set_visible(False)
            if j == 0 or phone: a.set_ylabel(("Core" if q == "core" else "Memory") + " residual, °C", color=th["fg"])

    h, l = ax[0][0].get_legend_handles_labels()
    Fg.legend(h, [f"power limit {x}" for x in l], ncol=2 if phone else 4, frameon=False, labelcolor=th["fg"], fontsize=fs - 2, loc="upper center")
    Fg.tight_layout(rect=(0, 0, 1, 0.95 if not phone else 0.965)); name = f"gpu-map-s3-resid{'-phone' if phone else ''}-{theme}"
    Fg.savefig(str(OUT / f"{name}.png"), dpi=200 if not phone else 200, facecolor=th["bg"]); plt.close(Fg)
    im = Image.open(str(OUT / f"{name}.png")).convert("RGB"); im.save(IMG / f"{name}.webp", "WEBP", quality=86, method=6); return im.size
SZ = {(t, p): fig(t, p) for t in TH for p in (False, True)}
(W, Hh), (PW, PH) = SZ[("light", False)], SZ[("light", True)]
pic = "".join(f'<a class="ar-wide th-{t[0]}" href="/research/img/gpu-map-s3-resid-{t}.webp?v=1" aria-label="Open the chart at full size"><picture><source media="(max-width:620px)" srcset="/research/img/gpu-map-s3-resid-phone-{t}.webp?v=1" width="{PW}" height="{PH}"><img src="/research/img/gpu-map-s3-resid-{t}.webp?v=1" width="{W}" height="{Hh}" loading="lazy" decoding="async" alt="Eight panels: residuals of the core (top) and memory (bottom) fits on the final grid against GPU fan speed, case fan speed, board power and time, coloured by power limit; no trend in any panel, nearly all core residuals within one degree"></picture></a>' for t in ("light", "dark"))
dc, dm = dg["core"], dg["mem"]
maxcorr = max(abs(v) for q in ("core", "mem") for v in dg[q]["corr"].values())
rep = J["repeats_detail"]; repd = max(abs(r["core"][-1] - r["core"][0]) for r in rep)
sec = f"""<!--est3:start-->
  <h3 id="est3">Primary fit on the final grid</h3>
  <p>The primary model is estimated on the final grid alone: {n} settled points from one uninterrupted session at one intake air temperature, so no session offsets are needed (<a href="#steady3-grid">Section 3.1</a>). The response is T&nbsp;&minus;&nbsp;T<sub>in</sub> for the core and for the memory, fitted by nonlinear least squares. The two-path form of equation (11), two conductances in parallel with a power law in each fan speed, leaves a core RMSE of {CUR["rmse"]:.2f}&nbsp;&deg;C in sample, close to the {VE:.2f}&nbsp;&deg;C with which the earlier-session model predicts this grid out of sample (<a href="#validation">Section 4.6</a>). The remaining error is therefore a matter of the functional form, not of sampling, and we compared six forms and a spline benchmark ({{tref:forms3}}).</p>
{TAB}
  <p>One change accounts for most of the gain: letting the GPU-fan conductance saturate. With G<sub>N</sub>(N) = g<sub>N</sub>&thinsp;n<sup>m</sup>/(n<sub>&frac12;</sub><sup>m</sup> + n<sup>m</sup>), n = N/1000, the core RMSE falls from {CUR["rmse"]:.2f} to {HC["rmse"]:.2f}&nbsp;&deg;C, the leave-one-out error from {CUR["loo"]:.2f} to {HC["loo"]:.2f}&nbsp;&deg;C and BIC by {CUR["bic"] - HC["bic"]:.0f}; {HC["w1"]} of {n} core residuals are within &plusmn;1&nbsp;&deg;C. The memory gains as much: RMSE {FM["current"]["rmse"]:.2f} to {HM["rmse"]:.2f}&nbsp;&deg;C, BIC by {FM["current"]["bic"] - HM["bic"]:.0f}. The GPU-fan conductance reaches half its ceiling at n<sub>&frac12;</sub> = {nhalf_rpm:.0f}&nbsp;rpm (about {nhalf_pct:.0f}&nbsp;%); beyond it more airflow helps less, because the heat sink rather than the air limits the transfer. A power exponent on the fan term (&beta; = {beta["core"]:.2f} for the core, {beta["mem"]:.2f} for the memory) and a case exponent that depends on N gain little. Two richer forms fit about as well but are physically inadmissible: with an N&times;C interaction the memory fit needs a negative case conductance, and saturation with an interaction gives the core a negative interaction and an undetermined r<sub>&infin;</sub>. We therefore take the saturating form, with seven parameters, for both the core and the memory; it is equations (R1) and (R2), with the constants in {{tref:params}}. The spline benchmark, with {FC["spline benchmark (4×4 tensor)"]["k"]} parameters, reaches {FC["spline benchmark (4×4 tensor)"]["rmse"]:.2f}&nbsp;&deg;C (LOO {FC["spline benchmark (4×4 tensor)"]["loo"]:.2f}): a smooth structure of about {(HC["rmse"]**2 - FC["spline benchmark (4×4 tensor)"]["rmse"]**2)**0.5:.2f}&nbsp;&deg;C (root-mean-square) remains that no seven-parameter form captures, small against the 1&nbsp;&deg;C comfort margins of the controller.</p>
  <p>The residuals of the chosen form show no trend against GPU fan speed, case fan speed, power or time ({{fref:fig-residuals-of-the-primary-fit-on-the-fina}}); their correlation with each of N, C, P, time and intake air is below {maxcorr:.2f} in absolute value. Durbin&ndash;Watson is {dc["dw_N"]:.2f} along the GPU fans and {dc["dw_time"]:.2f} in time order for the core ({dm["dw_N"]:.2f} and {dm["dw_time"]:.2f} for the memory): neighbouring points still share part of their error, the remaining structure of the form, so the HC3 intervals in {{tref:params}} are, if anything, narrow. The anchor point (GPU fans 40&nbsp;%, case fans 1600&nbsp;rpm, 575&nbsp;W) read {dr["core_start"]:.2f}&nbsp;&deg;C at the start and {dr["core_end"]:.2f}&nbsp;&deg;C after {J["hours"]:.1f}&nbsp;h, with the intake air {dr["tin_end"] - dr["tin_start"]:.2f}&nbsp;&deg;C warmer: after the intake air is subtracted, the card drifted by {fm((dr["core_end"] - dr["core_start"]) - (dr["tin_end"] - dr["tin_start"]))}&nbsp;&deg;C over the run, and the residual trend in time is {fm(dc["slope_t"]*10, 3)}&nbsp;&deg;C per 10&nbsp;h. The intake air varied by only {J["tin"]["sd"]:.2f}&nbsp;&deg;C (standard deviation), so the coefficient of T<sub>in</sub> cannot be tested on this grid and stays fixed at one; the residuals do not depend on it (slope {fm(dc["slope_Tin"])}). The three repeated cells differ from their first reading by at most {repd:.2f}&nbsp;&deg;C.</p>
  <figure class="ar-fig ar-fig-wide">
    {pic}
    <figcaption><b>Figure 0.</b> Residuals, measured minus fitted, of equations (R1) for the core (top) and (R2) for the memory (bottom) on the {n} points of the final grid, against GPU fan speed (rpm, with % on the upper axis), case and radiator fan speed, board power (spread slightly for visibility) and time since the start of the run; colour: power limit. Dotted: &plusmn;1&nbsp;&deg;C. The memory is read in whole degrees. <a href="/research/data/gpu-map-steady3-points.csv">Data (CSV)</a>.</figcaption>
  </figure>
  <p>The earlier sessions give an independent check the other way. Applied without refitting to their {xc["core"]["n"]} settled core points, the primary model has a mean error of {fm(xc["core"]["mean"])}&nbsp;&deg;C and an RMSE of {xc["core"]["rmse"]:.2f}&nbsp;&deg;C ({xc["core"]["w1"]} within &plusmn;1&nbsp;&deg;C); most of that is the offset of each session, largest for the first night ({fm(xc["core"]["by_session"]["night"], 1)}&nbsp;&deg;C), and within the sessions the RMSE is {xc["core"]["rmse_within"]:.2f}&nbsp;&deg;C. For the {xc["mem"]["n"]} memory points the RMSE is {xc["mem"]["rmse"]:.2f}&nbsp;&deg;C, {xc["mem"]["rmse_within"]:.2f}&nbsp;&deg;C within sessions. The earlier-session fit itself, with its full set of tests, is kept as a secondary analysis (<a href="#stats">Section 4.2</a>).</p>
<!--est3:end-->"""
s = F.read_text()
a, b = s.find("<!--est3:start-->"), s.find("<!--est3:end-->")
if a >= 0: s = s[:a] + s[b + len("<!--est3:end-->"):]
i = s.find("<!--settle:start-->"); i = i if i >= 0 else s.index("<!--stats:start-->"); s = s[:i] + sec + "\n  " + s[i:]   # 4.1 before the settling analysis
F.write_text(s); print("est3 written", SZ)
