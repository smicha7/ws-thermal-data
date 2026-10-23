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
    rows += (f"<tr><td>{t}</td><td>{a['gpu_pct']}&nbsp;% ({a['gpu_rpm']})</td><td>{a['case_rpm']}</td><td>{a['dBA']:.1f}</td><td>{a['cls']}</td><td>{a['mem']:.0f}</td>"
             f"<td>{b['gpu_pct']}&nbsp;% / {b['case_rpm']}</td><td>{b['dBA']:.1f}</td><td>{b['core']:.1f}</td></tr>")
mrow = "".join(f"<tr><td>{m} ({t}&nbsp;&deg;C)</td><td>{M[m]['575']['gpu_pct']}&nbsp;% ({M[m]['575']['gpu_rpm']}&nbsp;rpm)</td><td>{M[m]['575']['case_rpm']}&nbsp;rpm</td><td>{M[m]['575']['dBA']:.1f}&nbsp;dBA, {M[m]['575']['cls']}</td></tr>" for m, t in (("Quiet", 80), ("Balanced", 77), ("Performance", 72)))
crow = ""
for Tk in ("19", "30"):
    for tg in ("77", "80"):
        d = C[Tk][tg]; v = [d[p]["dBA"] if d[p] else None for p in ("100", "90", "80", "70")]
        steps = [f"{v[i]-v[i+1]:.1f}" for i in range(3)]
        crow += f"<tr><td>{'19.3' if Tk=='19' else '30'}&nbsp;&deg;C</td><td>{tg}&nbsp;&deg;C</td>" + "".join(f"<td>{x:.1f}</td>" for x in v) + f"<td>{' / '.join(steps)}</td></tr>"
clk = R["clock_by_power"]
par = f"""<!--pareto:start-->
  <h3 id="pareto-lit">A first frontier, from the literature</h3>
  <p class="ar-status"><b>Literature-based, provisional until our own sound map.</b> The noise levels below come from the published measurements of <a href="#noise">How loud is loud</a>, not from this machine.</p>
  <p>Two models of noise feed equation (13). For the case and radiator fans, a straight line in the logarithm of speed, ${{Lc}}$, fitted by least squares to the speeds at which Hardware Busters measured the Silent Wings Pro 4 120 at 20, 25, 30, 35 and 40&nbsp;dBA at 1&nbsp;m: <i>a</i> = {cf['a']:.1f} and <i>b</i> = {cf['b']:.1f}&nbsp;dB per decade of speed. The five residuals lie within {max(abs(x) for x in cf['residuals']):.1f}&nbsp;dB, and at 3000&nbsp;rpm the line gives {42.6-cf['check_3000']:.1f}&nbsp;dBA against the 42.6 measured at full speed. The four case fans and three radiator fans run at the same speed here and are counted as seven such fans, {cf['seven_fans_db']:.2f}&nbsp;dB above one; the radiator fans are a different model, and below about 1280&nbsp;rpm the line is an extrapolation, but at low speeds the card dominates the total anyway. For the card, the estimate already used above, ${{Lg}}$ at 1&nbsp;m. Against the review anchors converted to 1&nbsp;m its residuals are {anc}; LanOC&rsquo;s close microphone and high room floor explain most of the last. PC Games Hardware&rsquo;s sone ratios imply a steeper rise than the model: {gf['pcgh']['l40_60']}&nbsp;dB from 40 to 60&nbsp;% against the model&rsquo;s {gf['pcgh']['model40_60']}, and {gf['pcgh']['l40_100']} from 40 to 100&nbsp;% against {gf['pcgh']['model40_100']}. We keep &plusmn;3&nbsp;dB at medium speeds and expect the model to understate the card by up to 4 to 6&nbsp;dB near full speed.</p>
  <p>With the core from equation (11), the memory from its first model, and 19.3&nbsp;&deg;C intake air, every pair of GPU fan speed, 40 to 100&nbsp;%, and case and radiator speed, 800 to 3000&nbsp;rpm, gives a temperature and a total level. The frontier is the set of pairs that no other pair beats on both.</p>
  <figure class="ar-fig ar-fig-wide">
    {pic('gpu-map-noise-pareto', 'Two panels, at 575 and 402 W, of settled core temperature against total fan noise in dBA at 1 m for every pair of GPU and case fan speeds, with the Pareto frontier drawn as a line labelled with the fan speeds along it, horizontal lines for the Quiet, Balanced and Performance targets of 80, 77 and 72 °C, and coloured bands for the noise classes', 2600, 1240, 1000, 2400)}
    <figcaption><b>Figure 18.</b> Settled core against total noise of all fans at 1&nbsp;m, at 575 and 402&nbsp;W: every pair of fan speeds (grey), the frontier (line), labelled &ldquo;GPU fans % / case and radiator fans rpm&rdquo;. Dotted lines: the targets of the three modes; open markers: the quietest pair that meets each. Bands: the noise classes of <a href="#noise-rtx50">How loud is loud</a>. Literature-based noise; core from equation (11). <a href="/research/data/gpu-map-noise-pareto.json">Data (JSON)</a>.</figcaption>
  </figure>
  <p>The frontier answers the question of the paragraph above, for this card and case: it does not spread the airflow. Along almost all of it the case and radiator fans stay between 800 and about 1250&nbsp;rpm and the GPU fans do the work. Seven fans add {cf['seven_fans_db']:.1f}&nbsp;dB to one, and once the GPU fans are past about 45&nbsp;% the case fans cool the core by little, so raising them costs more noise than it saves heat. At 402&nbsp;W the slowest setting allowed under load, GPU fans 40&nbsp;% and case fans 800&nbsp;rpm, already holds the core at {T['402']['80']['core']:.1f}&nbsp;&deg;C, below every target.</p>
  <div class="ar-tw">
  <table class="ar-tab ar-num ar-st">
    <thead><tr><th scope="col">Core target, &deg;C</th><th scope="col">575&nbsp;W: GPU fans</th><th scope="col">575&nbsp;W: case, rpm</th><th scope="col">575&nbsp;W: dBA at 1&nbsp;m</th><th scope="col">575&nbsp;W: class</th><th scope="col">575&nbsp;W: memory, &deg;C</th><th scope="col">402&nbsp;W: GPU fans / case rpm</th><th scope="col">402&nbsp;W: dBA</th><th scope="col">402&nbsp;W: core, &deg;C</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  </div>
  <p class="ar-note">The quietest pair whose settled core is at or below the target and whose memory stays below 96&nbsp;&deg;C. Fan speeds on a grid of 1&nbsp;% and 50&nbsp;rpm; the GPU fans never go below 40&nbsp;% under load. Levels &plusmn;3&nbsp;dB or more, see above.</p>
  <p>For the three modes of the controller at full power this gives:</p>
  <div class="ar-tw">
  <table class="ar-tab ar-num ar-txt">
    <thead><tr><th scope="col">Mode at 575&nbsp;W</th><th scope="col">GPU fans</th><th scope="col">Case and radiator fans</th><th scope="col">Total at 1&nbsp;m</th></tr></thead>
    <tbody>{mrow}</tbody>
  </table>
  </div>
  <p>All three lie well inside the speed ceilings of the modes, and all three keep the case fans near their minimum, where the controller&rsquo;s present noise proxy, which weighs both groups by speed alone, tends to spend more on the case fans. These decibel models are candidates to replace that proxy; we will decide after our own measurements.</p>
<!--pareto:end-->"""
pm = f"""<!--pmax:start-->
  <p>The same models give equation (14). For a core target of 77&nbsp;&deg;C, Figure 19 shows the highest power the card can hold within each noise budget, for intake air at 19.3 and at 30&nbsp;&deg;C, and the table gives the quietest total level at each power limit and what each 10&nbsp;% of power limit buys.</p>
  <figure class="ar-fig">
    {pic('gpu-map-noise-pmax', 'Highest sustainable power for a core target of 77 °C against the noise budget in dBA at 1 m, for intake air at 19.3 and 30 °C, with a second axis giving the average graphics clock at that power; at 19.3 °C full power is reached at about 32 dBA, at 30 °C only at about 38 dBA', 1600, 1040, 1000, 1200)}
    <figcaption><b>Figure 19.</b> Highest power with the core at or below 77&nbsp;&deg;C and the memory below 96&nbsp;&deg;C, against the noise budget of all fans at 1&nbsp;m, for intake air at 19.3&nbsp;&deg;C (blue) and 30&nbsp;&deg;C (red). Right axis: the average graphics clock measured at that power in the second run, a proxy for performance. Literature-based noise, provisional.</figcaption>
  </figure>
  <div class="ar-tw">
  <table class="ar-tab ar-num ar-st">
    <thead><tr><th scope="col">Intake air</th><th scope="col">Core target</th><th scope="col">575&nbsp;W, dBA</th><th scope="col">518&nbsp;W, dBA</th><th scope="col">460&nbsp;W, dBA</th><th scope="col">402&nbsp;W, dBA</th><th scope="col">dB saved per 10&nbsp;% step</th></tr></thead>
    <tbody>{crow}</tbody>
  </table>
  </div>
  <p class="ar-note">Quietest total level of all fans at 1&nbsp;m for each power limit. A level of 28.9&nbsp;dBA is the floor: GPU fans at 40&nbsp;% and case fans at 800&nbsp;rpm.</p>
  <p>In a cool room the power limit buys little quiet: from 575 to 518&nbsp;W about {C['19']['77']['100']['dBA']-C['19']['77']['90']['dBA']:.1f}&nbsp;dB at 77&nbsp;&deg;C, and below that the fans are already at their floor. On a warm day it buys about 3&nbsp;dB for each 10&nbsp;%. The price is speed: the average clock in the second run was {clk['575']}, {clk['518']}, {clk['460']} and {clk['402']}&nbsp;MHz at 575, 518, 460 and 402&nbsp;W. That is why the controller lowers the power limit only after the fans reach the ceiling of the mode.</p>
<!--pmax:end-->"""
def replace_fig(n, new):
    global s
    k = s.index(f"<b>Figure {n}.</b>"); a = s.rindex("<figure", 0, k); b = s.index("</figure>", k) + 9
    s = s[:a] + new + s[b:]
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
