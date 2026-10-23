"""Fills the Pareto and power-budget placeholders (Figures 18-20) from results-2026-10-23/noise-pareto.json."""
import json, re
F = "/Users/smicha/Claude/gruency-site/research/gpu-cooling-method.html"; s = open(F).read()
R = json.load(open("/Users/smicha/Applications/Pasek/research/gpu-map/results-2026-10-23/noise-pareto.json"))
cf, gf = R["case_fit"], R["gpu_fit"]; T = R["table"]; M = R["modes"]; C = R["cost"]
def pic(name, alt, w, h, pw, ph):
    p = lambda th: (f'<a class="ar-wide th-{th[0]}" href="/research/img/{name}-{th}.webp?v=1" aria-label="Open the chart at full size"><picture>'
                    f'<source media="(max-width:620px)" srcset="/research/img/{name}-phone-{th}.webp?v=1" width="{pw}" height="{ph}">'
                    f'<img src="/research/img/{name}-{th}.webp?v=1" width="{w}" height="{h}" loading="lazy" decoding="async" alt="{alt}"></picture></a>')
    return p("light") + p("dark")
anc = "; ".join(f"{n}: {('+' if d > 0 else '&minus;' if d < 0 else '')}{abs(d):.1f}&nbsp;dB" for n, r, L, d in gf["anchors"])
rows = ""
for t in ["70", "72.5", "75", "77.5", "80", "82.5", "85"]:
    a, b = T["575"][t], T["402"][t]
    rows += (f"<tr><td>{float(t):.1f}</td><td class=g>{a['gpu_pct']}</td><td>{a['gpu_rpm']}</td><td>{a['case_rpm']}</td><td>{a['dBA']:.1f}</td><td class=tl>{a['cls']}</td><td>{a['core']:.1f}</td><td>{a['mem']:.1f}</td>"
             f"<td class=g>{b['gpu_pct']}</td><td>{b['case_rpm']}</td><td>{b['dBA']:.1f}</td><td>{b['core']:.1f}</td><td>{b['mem']:.1f}</td></tr>")
mrow = "".join(f"<tr><td>{m} ({t}&nbsp;&deg;C)</td><td>{M[m]['575']['gpu_pct']}</td><td>{M[m]['575']['gpu_rpm']}</td><td>{M[m]['575']['case_rpm']}</td><td>{M[m]['575']['dBA']:.1f}</td><td class=tl>{M[m]['575']['cls']}</td></tr>" for m, t in (("Quiet", 80), ("Balanced", 77), ("Performance", 72)))
crow = ""
for Tk in ("19", "30"):
    for tg in ("77", "80"):
        d = C[Tk][tg]; v = [d[p]["dBA"] if d[p] else None for p in ("100", "90", "80", "70")]
        dl = lambda i: "" if i == 0 else f' <span class="dlt">({v[i]-v[i-1]:+.1f})</span>'.replace("+-", "&minus;").replace("(-", "(&minus;").replace("(+0.0)", "(0.0)").replace("(&minus;0.0)", "(0.0)")
        crow += f"<tr><td>{'19.3' if Tk=='19' else '30.0'}</td><td>{tg}</td><td class=tl>{'Balanced' if tg=='77' else 'Quiet'}</td>" + "".join(f"<td>{x:.1f}{dl(i)}</td>" for i, x in enumerate(v)) + "</tr>"
clk = R["clock_by_power"]
fit = f"""<!--noisefit:start-->
  <p>Two models of noise feed equation (13). For the case and radiator fans, a straight line in the logarithm of speed, ${{Lc}}$, fitted by least squares to the speeds at which Hardware Busters measured the Silent Wings Pro 4 120 at 20, 25, 30, 35 and 40&nbsp;dBA at 1&nbsp;m: <i>a</i> = {format(cf['a'], '.1f').replace('-', '&minus;')} and <i>b</i> = {cf['b']:.1f}&nbsp;dB per decade of speed. The five residuals lie within {max(abs(x) for x in cf['residuals']):.1f}&nbsp;dB, and at full speed (about 2920&nbsp;rpm) the line gives {42.6-cf['check_3000']:.1f}&nbsp;dBA against the 42.6 measured at full speed. The four case fans and three radiator fans run at the same speed here and are counted as seven such fans, 8.5&nbsp;dB above one; the radiator fans are a different model, and below about 1280&nbsp;rpm the line is an extrapolation, but at low speeds the card dominates the total anyway. For the card, the estimate of Appendix E.1.3, ${{Lg}}$ at 1&nbsp;m. Against the review anchors converted to 1&nbsp;m its residuals are {anc}; LanOC&rsquo;s close microphone and high room floor explain most of the last. PC Games Hardware&rsquo;s sone ratios imply a steeper rise than the model: {gf['pcgh']['l40_60']}&nbsp;dB from 40 to 60&nbsp;% against the model&rsquo;s {gf['pcgh']['model40_60']}, and {gf['pcgh']['l40_100']} from 40 to 100&nbsp;% against {gf['pcgh']['model40_100']}. We keep &plusmn;3&nbsp;dB at medium speeds and expect the model to understate the card by up to 4 to 6&nbsp;dB near full speed.</p>

<!--noisefit:end-->"""
par = f"""<!--pareto:start-->
  <h3 id="pareto-lit">A first frontier, from the literature</h3>
  <p>With the core from equation (11), the memory from the memory model (Section 4.2), and 19.3&nbsp;&deg;C intake air, every pair of GPU fan speed, 40 to 100&nbsp;%, and case and radiator speed, 800&nbsp;rpm to full speed (about 2920&nbsp;rpm), gives a temperature and a total level. The frontier is the set of pairs that no other pair beats on both.</p>
  <figure class="ar-fig ar-fig-wide">
    {pic('gpu-map-noise-pareto', 'Two panels, at 575 and 402 W, of settled core temperature against total fan noise in dBA at 1 m for every pair of GPU and case fan speeds, with the Pareto frontier drawn as a line labelled with the fan speeds along it, horizontal lines for the comfort levels of the Quiet, Balanced and Performance modes (78, 73 and 68 °C), vertical lines for their noise budgets of 30, 35 and 40 dBA, open markers for each mode’s planned operating point, and coloured bands for the noise classes', 2600, 1240, 1000, 2400)}
    <figcaption><b>Figure 18.</b> Settled core against total noise of all fans at 1&nbsp;m, at 575 and 402&nbsp;W: every pair of fan speeds (grey), the frontier (line), labelled &ldquo;GPU fans % / case and radiator fans rpm&rdquo;. Dotted lines: the comfort levels of the three released modes at the default core limit (Quiet 78, Balanced 73, Performance 68&nbsp;&deg;C); dashed lines: their noise budgets (30, 35 and 40&nbsp;dBA); open markers (circle, square, diamond): each mode&rsquo;s planned operating point from the controller&rsquo;s planning code (<a href="#main-result">Section 5.1</a>). At 575&nbsp;W Quiet cannot reach its comfort level within 30&nbsp;dBA and takes the coolest pair within the budget; at 402&nbsp;W all three modes sit at the load floors (GPU fans 40&nbsp;%, case fans 800&nbsp;rpm), already below every comfort level. Bands: the noise classes of <a href="#noise-rtx50">How loud is loud</a>. Literature-based noise; core from equation (11). <a href="/research/data/gpu-map-noise-pareto.json">Data (JSON)</a>.</figcaption>
  </figure>
  <p>The frontier ({{fref:fig-the-quiet-frontier-settled-core-against-}}) answers this question for this card and case: it does not spread the airflow. Along almost all of it the case and radiator fans stay between 800 and about 1250&nbsp;rpm and the GPU fans do the work. Seven fans add 8.5&nbsp;dB to one, and once the GPU fans are past about 45&nbsp;% the case fans cool the core by little, so raising them costs more noise than it saves heat. At 402&nbsp;W the slowest setting allowed under load, GPU fans 40&nbsp;% and case fans 800&nbsp;rpm, already holds the core at {T['402']['80']['core']:.1f}&nbsp;&deg;C, below every mode&rsquo;s comfort level.</p>
  <div class="ar-tw">
  <table class="ar-tab ar-num ar-st ar-ms">
    <thead><tr><th scope="col" rowspan="2">Core target, &deg;C</th><th scope="colgroup" colspan="7">Power limit 100&nbsp;% (575&nbsp;W)</th><th scope="colgroup" colspan="5">Power limit 70&nbsp;% (402&nbsp;W)</th></tr><tr><th scope="col" class="g">GPU fans, %</th><th scope="col">GPU fans, rpm</th><th scope="col">case fans, rpm</th><th scope="col">noise at 1&nbsp;m, dBA</th><th scope="col" class="tl">class of total noise ({{tref:gpuclassrange}})</th><th scope="col">core, &deg;C</th><th scope="col">memory, &deg;C</th><th scope="col" class="g">GPU fans, %</th><th scope="col">case fans, rpm</th><th scope="col">noise at 1&nbsp;m, dBA</th><th scope="col">core, &deg;C</th><th scope="col">memory, &deg;C</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  </div>
  <p class="ar-note">The quietest pair whose settled core is at or below the target and whose memory stays at or below the default memory limit of 90&nbsp;&deg;C. Fan speeds on a grid of 1&nbsp;% and 50&nbsp;rpm; the GPU fans never go below 40&nbsp;% under load. Levels &plusmn;3&nbsp;dB or more (<a href="#noise-gpu">the GPU-fan noise estimate</a>).</p>
<!--pareto:end-->"""
pm = f"""<!--pmax:start-->
  <p>The same models give equation (14). For a core target of 77&nbsp;&deg;C, {{fref:fig-highest-power-within-a-noise-budget}} shows the highest power the card can hold within each noise budget, for intake air at 19.3 and at 30&nbsp;&deg;C, and the table below gives the quietest total level at each power limit; look at how much each step down in power limit saves in a cool and in a warm room.</p>
  <figure class="ar-fig">
    {pic('gpu-map-noise-pmax', 'Highest sustainable power for a core target of 77 °C against the noise budget in dBA at 1 m, for intake air at 19.3 and 30 °C, with a second axis giving the average graphics clock at that power; at 19.3 °C full power is reached at about 32 dBA, at 30 °C only at about 38 dBA', 1600, 1040, 1000, 1200)}
    <figcaption><b>Figure 19.</b> Highest power with the core at or below 77&nbsp;&deg;C and the memory at or below 90&nbsp;&deg;C, against the noise budget of all fans at 1&nbsp;m, for intake air at 19.3&nbsp;&deg;C (blue) and 30&nbsp;&deg;C (red). Right axis: the average graphics clock measured at that power in the second run, a proxy for performance. Literature-based noise, provisional.</figcaption>
  </figure>
  <div class="ar-tw">
  <table class="ar-tab ar-num ar-st">
    <thead><tr><th scope="col">Intake air, &deg;C</th><th scope="col">Core target, &deg;C</th><th scope="col" class="tl">Mode with this target, first version</th><th scope="col">Power limit 100&nbsp;% (575&nbsp;W), dBA</th><th scope="col">90&nbsp;% (518&nbsp;W), dBA</th><th scope="col">80&nbsp;% (460&nbsp;W), dBA</th><th scope="col">70&nbsp;% (402&nbsp;W), dBA</th></tr></thead>
    <tbody>{crow}</tbody>
  </table>
  </div>
  <p class="ar-note">Each cell: the quietest total level of all fans at 1&nbsp;m that holds the core target with the memory at or below 90&nbsp;&deg;C (model (11), literature-based noise). In parentheses: change from the column to the left, in dB. The core targets 77 and 80&nbsp;&deg;C are those of Balanced and Quiet in the first, temperature-target version of the controller. A level of 28.9&nbsp;dBA is the floor: GPU fans at 40&nbsp;% and case fans at 800&nbsp;rpm.</p>
  <p>In a cool room the power limit buys little quiet: from 575 to 518&nbsp;W about {C['19']['77']['100']['dBA']-C['19']['77']['90']['dBA']:.1f}&nbsp;dB at 77&nbsp;&deg;C, and below that the fans are already at their floor. On a warm day it buys about 3&nbsp;dB for each 10&nbsp;%. The price is speed: the average clock in the second run was {clk['575']}, {clk['518']}, {clk['460']} and {clk['402']}&nbsp;MHz at 575, 518, 460 and 402&nbsp;W. That is why the controller lowers the power limit only when a temperature limit cannot be held within the mode&rsquo;s noise budget.</p>
<!--pmax:end-->"""
def replace_fig(n, new):
    global s
    k = s.index(f"<b>Figure {n}.</b>"); a = s.rindex("<figure", 0, k); b = s.index("</figure>", k) + 9
    s = s[:a] + new + s[b:]
if "<!--noisefit:start-->" in s:
    a = s.index("<!--noisefit:start-->"); b = s.index("<!--noisefit:end-->") + len("<!--noisefit:end-->"); s = s[:a] + fit + s[b:]
if "<!--pareto:start-->" in s:
    a = s.index("<!--pareto:start-->"); b = s.index("<!--pareto:end-->") + len("<!--pareto:end-->"); s = s[:a] + par + s[b:]
else:
    replace_fig(18, par)
if "<!--pmax:start-->" in s:
    a = s.index("<!--pmax:start-->"); b = s.index("<!--pmax:end-->") + len("<!--pmax:end-->"); s = s[:a] + pm + s[b:]
else:
    replace_fig(19, pm)
    # Figure 20 (performance against noise) is covered by Figure 19's clock axis
    k = s.index("<b>Figure 20.</b>"); a = s.rindex("<figure", 0, k); b = s.index("</figure>", k) + 9
    s = s[:a].rstrip() + "\n" + s[b:]
    s = s.replace("<b>Figure 21.</b>", "<b>Figure 20.</b>")
s = s.replace("The measurements show whether it does for a given card and case.</p>", "Whether it does depends on the card and the case; the frontier below shows that here it does not.</p>")
s = s.replace("The power-limit runs are reported under", "The power-limit runs themselves are reported under")
open(F, "w").write(s); print("pareto + pmax written")
