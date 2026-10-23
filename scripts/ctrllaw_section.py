"""Conclusions: the control law WS.Sensor implements, the figure of its fan settings and predicted temperatures against power,
the panel screenshots (placeholder until PNGs appear in research/gpu-panel-shots/). Between <!--ctrllaw:start/end-->. Usage: ctrllaw_section.py"""
import json, shutil, subprocess
from pathlib import Path
G = Path(__file__).resolve().parent.parent; SITE = Path.home() / "Claude/gruency-site"; F = SITE / "research/gpu-cooling-method.html"
M = json.load(open(G / "results-2026-10-23/modes-noise.json"))
TEX = [r"$$\hat T_{\mathrm{core}}(N,C,P)=T_{\mathrm{in}}+\theta_0+P\Big[r_\infty+\frac{1}{g_N (N/1000)^{m}+g_C (C/1500)^{s}}\Big]",
       r"$$\hat T_{\mathrm{mem}}(N,C,P)=T_{\mathrm{in}}+\theta_{0,\mathrm{mem}}+P\Big[r'_\infty+\frac{1}{g'_N (N/1000)^{m'}+g'_C (C/1500)^{s'}}\Big]",
       r"$$L(N,C)=10\log_{10}\!\big(10^{L_g(N)/10}+7\cdot 10^{L_c(C)/10}\big),\quad L_g=32.5+50\log_{10}\tfrac{N}{1570},\quad L_c=-167.1+60.2\log_{10}C",
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
shot_html = ("".join(f'<img src="/research/img/gpu-panel-{p.name}" alt="WS.Sensor graphics-card cooling panel" loading="lazy" style="width:100%;height:auto;margin:6px 0">' for p in shots)
             or '<p class="ar-ph-txt">Screenshot follows.</p>')
sec = f"""<!--ctrllaw:start-->
  <h3 id="control-law">The derived control law</h3>
  <p>The measurements, the models and the tests lead to one control law, which WS.Sensor implements. For the power P the card draws and the intake air T<sub>in</sub>, the core and memory temperatures at GPU fan speed N and case and radiator fan speed C (rpm) are predicted by equation (11) and the memory model:</p>
  {H[0]}{H[1]}
  <p>The noise of all fans at 1&nbsp;m follows from the literature-based fits, summed on an energy basis as in equation (13):</p>
  {H[2]}
  <p>Each mode is a noise budget {H[5]}, a ceiling: 30&nbsp;dBA for Quiet, 35 for Balanced (shown as Normal in WS.Sensor) and 40 for Performance, with comfort distances &Delta; below the safety limits {H[6]}, 83&nbsp;&deg;C by default and at most 88&nbsp;&deg;C, and {H[7]}, 90&nbsp;&deg;C by default and never above 91&nbsp;&deg;C: 5 and 3&nbsp;&deg;C in Quiet, 10 and 5&nbsp;&deg;C in Balanced, 15 and 8&nbsp;&deg;C in Performance. The controller picks the quietest pair within the budget that holds both comfort levels; only if none does, the coolest pair within the budget, then a lower power limit, and only at the power-limit floor a pair over the budget:</p>
  {H[3]}{H[4]}
  <p>At light load the comfort levels are met at the fan floors, so every mode runs at the same 24.1&nbsp;dBA; as the power rises the fans rise only as far as the comfort level requires, and the modes part when their budgets are reached. At 575&nbsp;W the planned operating points are {pt('quiet')}, {pt('balanced')} and {pt('performance')}. In simulation of the released controller (WS.Sensor 0.30.69) no mode spent a second over a limit or over its budget, and none reversed its fans under 60-second bursts of load; with the intake air rising from 19.3 to 30&nbsp;&deg;C, Quiet held its budget by lowering the power limit to 75&nbsp;%, while Balanced and Performance stayed at full power with the core at 82.1 and 75.5&nbsp;&deg;C (<a href="#controller-res">Section 3.5</a>).</p>
  <figure class="ar-fig ar-fig-wide">
    {pic("gpu-map-ctrl-law", 2600, 1720, 1000, 2800, "Four panels against board power for the Quiet, Balanced and Performance modes: GPU fan speed, case fan speed, total noise with each budget, and predicted core with each comfort level; all modes sit at the fan floors at low power and rise only as far as the comfort level requires")}
    <figcaption><b>Figure 0.</b> Planned fan speeds of the released controller against board power at full load, intake air 19.3&nbsp;&deg;C: GPU fans in % and rpm (top left), case and radiator fans in rpm and % (top right), total noise at 1&nbsp;m with each mode&rsquo;s budget dotted (bottom left), and predicted core with each mode&rsquo;s comfort level dotted (bottom right). Colours: Quiet (&le;&nbsp;30&nbsp;dBA) green, Balanced (&le;&nbsp;35&nbsp;dBA) blue, Performance (&le;&nbsp;40&nbsp;dBA) red.</figcaption>
  </figure>
  <figure class="ar-fig ar-ph">
    {shot_html}
    <figcaption><b>Figure 0.</b> WS.Sensor graphics-card cooling panel: three noise preferences, Quiet, Normal and Performance (30, 35 and 40&nbsp;dBA at 1&nbsp;m), and the two adjustable upper temperature limits, core and memory.</figcaption>
  </figure>
<!--ctrllaw:end-->"""
s = F.read_text(); a, b = s.index("<!--ctrllaw:start-->"), s.index("<!--ctrllaw:end-->") + len("<!--ctrllaw:end-->")
F.write_text(s[:a] + sec + s[b:]); print("control law written; screenshots:", len(shots))
