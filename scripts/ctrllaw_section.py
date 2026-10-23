"""Conclusions: the control law WS.Sensor implements, the figure of its fan settings and predicted temperatures against power,
the panel screenshots (placeholder until PNGs appear in research/gpu-panel-shots/). Between <!--ctrllaw:start/end-->. Usage: ctrllaw_section.py"""
import json, shutil, subprocess
from pathlib import Path
G = Path(__file__).resolve().parent.parent; SITE = Path.home() / "Claude/gruency-site"; F = SITE / "research/gpu-cooling-method.html"
M = json.load(open(G / "results-2026-10-23/modes-noise.json"))
TEX = [r"$$\hat T_{\mathrm{core}}(N,C,P)=T_{\mathrm{in}}+\theta_0+P\Big[r_\infty+\frac{1}{g_N (N/1000)^{m}+g_C (C/1500)^{s}}\Big]",
       r"$$\hat T_{\mathrm{mem}}(N,C,P)=T_{\mathrm{in}}+\theta_{0,\mathrm{mem}}+P\Big[r'_\infty+\frac{1}{g'_N (N/1000)^{m'}+g'_C (C/1500)^{s'}}\Big]",
       r"$$L(N,C)=10\log_{10}\!\big(10^{L_g(N)/10}+7\cdot 10^{L_c(C)/10}\big),\quad L_g=32.5+50\log_{10}\tfrac{N}{1570},\quad L_c=-167.1+60.2\log_{10}C",
       r"$$(N^\ast,C^\ast)=\arg\min_{N,C}\ \hat T_{\mathrm{core}}(N,C,P)\quad\text{subject to}\quad L(N,C)\le B_{\mathrm{mode}},\ \ \hat T_{\mathrm{core}}\le T_{\mathrm{core}}^{\max},\ \ \hat T_{\mathrm{mem}}\le T_{\mathrm{mem}}^{\max}",
       r"$$\text{if no pair is feasible:}\quad P_{\lim}\leftarrow\max\big(P_{\lim}-5\%,\ 70\%\big)\ \text{every }30\text{ s};\quad\text{only at }P_{\lim}=70\%\ \text{may }L\text{ exceed }B_{\mathrm{mode}}",
       r"B_{\mathrm{mode}}", r"T_{\mathrm{core}}^{\max}", r"T_{\mathrm{mem}}^{\max}", r"N", r"C", r"P"]
H = json.loads(subprocess.run(["node", str(Path(__file__).parent / "tex.js")], input=json.dumps(TEX), capture_output=True, text=True, check=True).stdout)
_t0 = 1792749600   # 2026-10-23 12:00: only panels of the noise-budget version
shots = sorted(p for p in (G.parent / "gpu-panel-shots").glob("*.png") if p.stat().st_mtime > _t0 and "dark" not in p.name) if (G.parent / "gpu-panel-shots").exists() else []
for p in shots: shutil.copy(p, SITE / "research/img" / ("gpu-panel-" + p.name))
pic = lambda name, w, h, pw, ph, alt: "".join(f'<a class="ar-wide th-{t[0]}" href="/research/img/{name}-{t}.webp?v=1" aria-label="Open the chart at full size"><picture><source media="(max-width:620px)" srcset="/research/img/{name}-phone-{t}.webp?v=1" width="{pw}" height="{ph}"><img src="/research/img/{name}-{t}.webp?v=1" width="{w}" height="{h}" loading="lazy" decoding="async" alt="{alt}"></picture></a>' for t in ("light", "dark"))
rows = ", ".join(f'{m["mode"]} {m["gpu_pct"]:.1f}&nbsp;% GPU fans with {m["case_rpm"]:.0f}&nbsp;rpm case fans' for m in M)
shot_html = ("".join(f'<img src="/research/img/gpu-panel-{p.name}" alt="WS.Sensor graphics-card cooling panel" loading="lazy" style="width:100%;height:auto;margin:6px 0">' for p in shots)
             or '<p class="ar-ph-txt">Screenshot follows.</p>')
sec = f"""<!--ctrllaw:start-->
  <p>The measurements, the models and the tests lead to one control law, which WS.Sensor implements. For the power P the card draws and the intake air T<sub>in</sub>, the core and memory temperatures at GPU fan speed N and case and radiator fan speed C (rpm) are predicted by equation (11) and the memory model:</p>
  {H[0]}{H[1]}
  <p>The noise of all fans at 1&nbsp;m follows from the literature-based fits, summed on an energy basis as in equation (13):</p>
  {H[2]}
  <p>Each mode is a noise budget {H[5]}: 30&nbsp;dBA for Quiet, 35 for Normal (Balanced) and 40 for Performance. The controller picks the coolest fan pair within the budget, subject to the safety limits {H[6]}, 83&nbsp;&deg;C by default and at most 88&nbsp;&deg;C, and {H[7]}, 90&nbsp;&deg;C by default and at most 95&nbsp;&deg;C:</p>
  {H[3]}{H[4]}
  <p>Because the predicted temperature is linear in P while the noise does not depend on it, the coolest pair within a budget is the same at every power: {rows}. The fans therefore stay at the mode&rsquo;s pair under load, and the predicted temperatures rise with power until a limit would be reached; there the power limit, not the noise, gives way. A proportional-integral term on the measured temperatures corrects what the model misses.</p>
  <figure class="ar-fig ar-fig-wide">
    {pic("gpu-map-ctrl-law", 2600, 920, 1000, 2200, "Three panels against board power for the Quiet, Balanced and Performance modes: fan speeds constant at each mode's pair, predicted core and predicted memory with the default limits of 83 and 90 °C")}
    <figcaption><b>Figure 0.</b> Left: fan speeds of each mode against board power, GPU fans in % (solid) and case and radiator fans in % of 3000&nbsp;rpm (dashed, right axis in rpm). Middle and right: predicted core and memory at those fans, intake air 19.3&nbsp;&deg;C, with the default limits (dotted). Colours: Quiet (&le;&nbsp;30&nbsp;dBA) green, Balanced (&le;&nbsp;35&nbsp;dBA) blue, Performance (&le;&nbsp;40&nbsp;dBA) red.</figcaption>
  </figure>
  <figure class="ar-fig ar-ph">
    {shot_html}
    <figcaption><b>Figure 0.</b> WS.Sensor graphics-card cooling panel: three noise preferences, Quiet, Normal and Performance (30, 35 and 40&nbsp;dBA at 1&nbsp;m), and the two adjustable upper temperature limits, core and memory.</figcaption>
  </figure>
  <p>This is what the user sees: three noise preferences and two temperature ceilings. Everything else, the choice of fan speeds, the response to the room and the load, and the power limit as the last resort, is automatic.</p>
<!--ctrllaw:end-->"""
s = F.read_text(); a, b = s.index("<!--ctrllaw:start-->"), s.index("<!--ctrllaw:end-->") + len("<!--ctrllaw:end-->")
F.write_text(s[:a] + sec + s[b:]); print("control law written; screenshots:", len(shots))
