"""Inserts/refreshes the ctrl1 hardware subsection (between <!--ctrl1:start--> and <!--ctrl1:end-->) from results-2026-10-22/ctrl1-compare.json."""
import json, re, sys
G = "/Users/smicha/Applications/Pasek/research/gpu-map/"; F = "/Users/smicha/Claude/gruency-site/research/gpu-cooling-method.html"
V = sys.argv[1] if len(sys.argv) > 1 else "1"; FIG = int(sys.argv[2]) if len(sys.argv) > 2 else 16
C = json.load(open(G + "results-2026-10-22/ctrl1-compare.json")); s = open(F).read()
TG = {"quiet": 80, "balanced": 77, "performance": 72}; NM = {"quiet": "Quiet", "balanced": "Balanced", "performance": "Performance"}
def row(k):
    m, sc = k.split("-"); r = C[k]
    return (f"<tr><td>{NM[m]}, {'load step' if sc == 'step' else 'bursts'}</td><td>{TG[m]}</td><td>{r['peak_core']:.0f} / {r['sim_peak_core']:.1f}</td>"
            f"<td>{r['core_late_mean']:.1f} / {r['sim_core_late']:.1f}</td><td>{r['s_over_target_1']}</td><td>{r['mem_peak']:.0f} / {r['sim_mem_peak']:.1f}</td>"
            f"<td>{r['card_rpm_mean_loaded']} / {r['sim_card_rpm']}</td><td>{r['card_rev_per_min']:.2f} / {r['sim_rev_per_min']:.2f}</td></tr>")
keys = [f"{m}-{sc}" for m in ("quiet", "balanced", "performance") for sc in ("step", "bursts")]
st = [C[f"{m}-step"] for m in ("quiet", "balanced", "performance")]
dl = max(abs(r["core_late_mean"] - r["sim_core_late"]) for r in st); dr = max(abs(r["card_rpm_mean_loaded"] - r["sim_card_rpm"]) for r in st)
rev = [C[k]["card_rev_per_min"] for k in keys]; intake = [C[k]["intake"] for k in keys]
alt = "Three rows for the Quiet, Balanced and Performance modes after a load step on the real card: measured and simulated core and memory temperature with the target line, GPU fan speed and case fan speed; measured and simulated curves lie close together"
pic = lambda th: (f'<a class="ar-wide th-{th[0]}" href="/research/img/gpu-map-ctrl1-{th}.webp?v={V}" aria-label="Open the controller test chart at full size"><picture>'
                  f'<source media="(max-width:620px)" srcset="/research/img/gpu-map-ctrl1-phone-{th}.webp?v={V}" width="1000" height="3400">'
                  f'<img src="/research/img/gpu-map-ctrl1-{th}.webp?v={V}" width="2600" height="1920" loading="lazy" decoding="async" alt="{alt}"></picture></a>')
sec = f"""<!--ctrl1:start-->
  <h3 id="controller-hw">On the real card</h3>
  <p>On 22 October the controller ran on the test machine itself, the same GeForce RTX 5090 in the open case, with intake air at about {sum(intake)/len(intake):.1f}&nbsp;&deg;C. Each mode met two loads, a step from idle to full power and bursts of 60 seconds, and each run was simulated again with the same load and the measured intake air, so that measurement and model can be compared second by second.</p>
  <div class="ar-tw">
  <table class="ar-tab ar-num ar-st">
    <thead><tr><th scope="col">Mode and load</th><th scope="col">Target, &deg;C</th><th scope="col">Peak core, measured / simulated, &deg;C</th><th scope="col">Core after 10 min, measured / simulated, &deg;C</th><th scope="col">Seconds above target + 1&nbsp;&deg;C</th><th scope="col">Peak memory, measured / simulated, &deg;C</th><th scope="col">GPU fans under load, measured / simulated, rpm</th><th scope="col">GPU fan reversals per minute, measured / simulated</th></tr></thead>
    <tbody>{''.join(row(k) for k in keys)}</tbody>
  </table>
  </div>
  <p class="ar-note">The core was logged in whole degrees on this run (the 0.01&nbsp;&deg;C column was empty), so the measured peaks are rounded to the degree. &ldquo;After 10 min&rdquo; is the mean from ten minutes after the load began to the end of the run.</p>
  <p>The controller did what it was designed to do. After the load step every mode reached its target and stayed there: the measured peaks were {st[0]['peak_core']:.0f}, {st[1]['peak_core']:.0f} and {st[2]['peak_core']:.0f}&nbsp;&deg;C against targets of 80, 77 and 72&nbsp;&deg;C, and no run spent a second more than 1&nbsp;&deg;C above its target. Once settled, the measured core and GPU fan speed agreed with the simulation within {dl:.1f}&nbsp;&deg;C and {dr:.0f}&nbsp;rpm. After the load step the memory ran up to 2&nbsp;&deg;C warmer than simulated, peaking at {C['quiet-step']['mem_peak']:.0f}&nbsp;&deg;C in Quiet, still 6&nbsp;&deg;C under the controller&rsquo;s memory ceiling. The power limit was never lowered.</p>
  <p>One prediction did not survive contact with the card. In simulation the fans almost never changed direction under bursts, at most {max(C[k]['sim_rev_per_min'] for k in keys if k.endswith('bursts')):.2f} times a minute; on the card they reversed {min(rev):.1f} to {max(rev):.1f} times a minute, most in Performance mode under bursts, more than the simulated factory curve&rsquo;s 0.97. The simulated card is smoother than the real one: its temperature and power carry no measurement noise, while the controller on the card reacts to every degree the sensor reports. Smoothing the controller&rsquo;s input is the next change; until it is made and tested, the claim that our fans do not pump under bursty loads holds only in simulation.</p>
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
