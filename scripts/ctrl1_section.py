"""Inserts/refreshes the ctrl1 hardware subsection (between <!--ctrl1:start--> and <!--ctrl1:end-->) from results-2026-10-22/ctrl1-compare.json."""
import json, re, sys
G = "/Users/smicha/Applications/Pasek/research/gpu-map/"; F = "/Users/smicha/Claude/gruency-site/research/gpu-cooling-method.html"
V = sys.argv[1] if len(sys.argv) > 1 else "1"; FIG = int(sys.argv[2]) if len(sys.argv) > 2 else 16
C = json.load(open(G + "results-2026-10-22/ctrl1-compare.json")); s = open(F).read()
TG = {"quiet": 80, "balanced": 77, "performance": 72}; NM = {"quiet": "Quiet", "balanced": "Balanced", "performance": "Performance"}
def row(k):
    m, sc = k.split("-"); r = C[k]
    return (f"<tr><td>{NM[m]} (target {TG[m]}&nbsp;&deg;C)</td><td class='g'>{r['peak_core']:.1f}</td><td>{r['sim_peak_core']:.1f}</td>"
            f"<td class='g'>{r['core_late_mean']:.1f}</td><td>{r['sim_core_late']:.1f}</td><td class='g'>{r['mem_peak']:.1f}</td><td>{r['sim_mem_peak']:.1f}</td>"
            f"<td class='g'>{r['card_rpm_mean_loaded']}</td><td>{r['sim_card_rpm']}</td><td class='g'>{r['card_rev_per_min']:.2f}</td><td>{r['sim_rev_per_min']:.2f}</td></tr>")
GRP = [("Highest core, &deg;C"), ("Core after 10&nbsp;min, &deg;C"), ("Highest memory, &deg;C"), ("GPU fans under load, rpm"), ("Fan reversals, per min")]
HEAD = ('<thead><tr><th scope="col" rowspan="2">Mode (target)</th>' + "".join(f'<th scope="colgroup" colspan="2">{g}</th>' for g in GRP) + "</tr><tr>"
        + '<th scope="col" class="g">on the card</th><th scope="col">simulation</th>' * len(GRP) + "</tr></thead>")
def table(sc, title):
    return (f'  <p class="ar-tcap"><b>{title}</b></p>\n  <div class="ar-tw">\n  <table class="ar-tab ar-num ar-st ar-ms">\n    {HEAD}\n'
            f'    <tbody>{"".join(row(f"{m}-{sc}") for m in ("quiet", "balanced", "performance"))}</tbody>\n  </table>\n  </div>\n')
keys = [f"{m}-{sc}" for m in ("quiet", "balanced", "performance") for sc in ("step", "bursts")]
st = [C[f"{m}-step"] for m in ("quiet", "balanced", "performance")]
dl = max(abs(r["core_late_mean"] - r["sim_core_late"]) for r in st); dr = max(abs(r["card_rpm_mean_loaded"] - r["sim_card_rpm"]) for r in st)
rev = [C[k]["card_rev_per_min"] for k in keys]; intake = [C[k]["intake"] for k in keys]

import os
B = json.load(open(G + "article_tools/ctrl123-bursts.json")) if os.path.exists(G + "article_tools/ctrl123-bursts.json") else None
fix = ""
if B:
    br = lambda m: (f"<tr><td>{NM[m]}</td><td>{B['ctrl1-'+m]['card']:.2f} &rarr; {B['ctrl2-'+m]['card']:.2f} &rarr; {B['ctrl3-'+m]['card']:.2f}</td>"
                    f"<td>{B['ctrl1-'+m]['case']:.2f} &rarr; {B['ctrl2-'+m]['case']:.2f} &rarr; {B['ctrl3-'+m]['case']:.2f}</td><td>{B['ctrl3-'+m]['over']}</td><td>{B['ctrl3-'+m]['peak']:.1f}</td></tr>")
    fix = f"""  <h3 id="controller-fix">Stopping the pumping</h3>
  <p>Two more runs on the card, late on 22 October, tested the corrections. The second, ctrl2, with the first changes against pumping, cut the reversals to 0.2 to 0.4 a minute but still let the fans dip slowly every five to seven minutes: bursts at 574&nbsp;W never quite matched the 575&nbsp;W peak that held the load estimate, so the hold expired. The third, ctrl3, ran with all the corrections made since ctrl1: a low-pass filter on the intake reading, hysteresis in the feed-forward, a dead band and a pause before the fans slow down after a rise, any burst within 3&nbsp;% of the peak renewing the load hold, a margin never below 1.0&nbsp;&deg;C, and the core reaching the controller at 0.01&nbsp;&deg;C from the NVAPI sensor instead of in whole degrees.</p>
  <div class="ar-tw">
  <table class="ar-tab ar-num ar-st">
    <thead><tr><th scope="col">Mode, 60-second bursts</th><th scope="col">GPU fan reversals per minute, ctrl1 &rarr; ctrl2 &rarr; ctrl3</th><th scope="col">Case fan reversals per minute, ctrl1 &rarr; ctrl2 &rarr; ctrl3</th><th scope="col">ctrl3: seconds above target + 1&nbsp;&deg;C</th><th scope="col">ctrl3: peak core, &deg;C</th></tr></thead>
    <tbody>{br('performance')}{br('balanced')}</tbody>
  </table>
  </div>
  <p class="ar-note">Reversals counted on the commanded fan speeds from two to twelve minutes after the start of each run, the span all three runs share. In ctrl3 the 0.01&nbsp;&deg;C core reading was present in every logged second. Data: ctrl2 <a href="/research/data/gpu-map-ctrl2-performance-bursts.csv">Performance</a>, <a href="/research/data/gpu-map-ctrl2-balanced-bursts.csv">Balanced</a>; ctrl3 <a href="/research/data/gpu-map-ctrl3-performance-bursts.csv">Performance</a>, <a href="/research/data/gpu-map-ctrl3-balanced-bursts.csv">Balanced</a> (CSV).</p>
  <p>In ctrl3 the fans rose once, at the first burst, and then held still: no reversal of either set of fans in either mode, and no second more than 1&nbsp;&deg;C above the target. The claim that our fans do not pump under bursty loads now holds on the real card, for these two modes; Quiet was not part of these runs.</p>
"""
alt = "Three rows for the Quiet, Balanced and Performance modes after a load step on the real card: measured and simulated core and memory temperature with the target line, GPU fan speed and case fan speed; measured and simulated curves lie close together"
pic = lambda th: (f'<a class="ar-wide th-{th[0]}" href="/research/img/gpu-map-ctrl1-{th}.webp?v={V}" aria-label="Open the controller test chart at full size"><picture>'
                  f'<source media="(max-width:620px)" srcset="/research/img/gpu-map-ctrl1-phone-{th}.webp?v={V}" width="1000" height="3400">'
                  f'<img src="/research/img/gpu-map-ctrl1-{th}.webp?v={V}" width="2600" height="1920" loading="lazy" decoding="async" alt="{alt}"></picture></a>')
sec = f"""<!--ctrl1:start-->
  <h3 id="controller-hw">On the real card</h3>
  <p>On 22 October the controller ran on the test machine itself, the same GeForce RTX 5090 in the open case, with intake air at about {sum(intake)/len(intake):.1f}&nbsp;&deg;C. Each mode met two loads, a step from idle to full power and bursts of 60 seconds, and each run was simulated again with the same load and the measured intake air, so that measurement and model can be compared second by second.</p>
{table("step", f"Load step: idle &rarr; 575&nbsp;W. RTX 5090 on the real card vs simulation, open case, intake about {sum(intake)/len(intake):.1f}&nbsp;&deg;C, 22 October")}{table("bursts", f"Short bursts: 60&nbsp;s full load, 60&nbsp;s idle. RTX 5090 on the real card vs simulation, open case, intake about {sum(intake)/len(intake):.1f}&nbsp;&deg;C, 22 October")}  <p class="ar-note">On the card: measured on the real RTX 5090 on 22 October. Simulation: our model given the same load and intake air. Core after 10&nbsp;min: the mean from ten minutes after the load began to the end of the run. Fan reversals: how often per minute the GPU fans switch between speeding up and slowing down. The measured core and memory were logged in whole degrees in this run, so their highest values end in .0. {"In no run did the core spend a second more than 1&nbsp;&deg;C above target." if all(C[k]["s_over_target_1"] == 0 for k in keys) else ""}</p>
  <p>The controller did what it was designed to do. After the load step every mode reached its target and stayed there: the measured peaks were {st[0]['peak_core']:.0f}, {st[1]['peak_core']:.0f} and {st[2]['peak_core']:.0f}&nbsp;&deg;C against targets of 80, 77 and 72&nbsp;&deg;C, and no run spent a second more than 1&nbsp;&deg;C above its target. Once settled, the measured core and GPU fan speed agreed with the simulation within {dl:.1f}&nbsp;&deg;C and {dr:.0f}&nbsp;rpm. After the load step the memory ran up to 2&nbsp;&deg;C warmer than simulated, peaking at {C['quiet-step']['mem_peak']:.0f}&nbsp;&deg;C in Quiet, which is the default memory limit of 90&nbsp;&deg;C. This run used the earlier ceiling of 100&nbsp;&deg;C; the controller now acts at the 90&nbsp;&deg;C default and never above 91&nbsp;&deg;C, under the 95&nbsp;&deg;C hard limit (<a href="#controller-mem">Memory temperature limit</a>). The power limit was never lowered.</p>
  <p>One prediction did not survive contact with the card. In simulation the fans almost never changed direction under bursts, at most {max(C[k]['sim_rev_per_min'] for k in keys if k.endswith('bursts')):.2f} times a minute; on the card they reversed {min(rev):.1f} to {max(rev):.1f} times a minute, most in Performance mode under bursts, more than the simulated factory curve&rsquo;s 0.97. The simulated card is smoother than the real one: its temperature and power carry no measurement noise, while the controller on the card reacted to every whole degree the sensor reported.</p>
{fix}
  <figure class="ar-fig">
    {pic('light')}{pic('dark')}
    <figcaption><b>Figure {FIG}.</b> The controller on the real card after a load step, measured (solid) and simulated with the same load and intake air (dashed). Rows: Quiet, Balanced and Performance; columns: core and memory with the target (dotted), GPU fans in % and rpm, case fans in rpm and %.</figcaption>
  </figure>
<!--ctrl1:end-->"""
a, b = s.find("<!--ctrl1:start-->"), s.find("<!--ctrl1:end-->")
if a < 0:
    anchor = '  <h2 id="pareto">'; i = s.index(anchor); s = s[:i] + sec + "\n\n" + s[i:]
else:
    s = s[:a] + sec + s[b + len("<!--ctrl1:end-->"):]
open(F, "w").write(s); print("ctrl1 section written")
