"""Inserts/refreshes the processor subsection (<!--cpu:start--> … <!--cpu:end-->) from data/cpu1-2026-10-22/cpu1b/cpu.csv."""
import pandas as pd
F = "/Users/smicha/Claude/gruency-site/research/gpu-cooling-method.html"; s = open(F).read()
d = pd.read_csv("/Users/smicha/Applications/Pasek/research/gpu-map/data/cpu1-2026-10-22/cpu1b/cpu.csv"); l = d[d.t_s > d.t_s.max() - 60]
row = lambda n, c, f="{:.1f}": f"<tr><td>{n}</td><td>{f.format(d[c].max())}</td><td>{f.format(l[c].mean())}</td></tr>"
sec = f"""<!--cpu:start-->
  <h2 id="cpu">The processor: a first measurement</h2>
  <p>The same controller must also look after the processor, so on the evening of 22 October we loaded it alone. The AMD Ryzen 9 9950X ran at stock settings on all 32 threads with an arithmetic load of our own, the graphics card idle, the liquid cooler&rsquo;s pump at full speed and the three radiator fans and four case fans at 100&nbsp;%. Intake air was {d.intake_c.mean():.1f}&nbsp;&deg;C.</p>
  <div class="ar-tw">
  <table class="ar-tab ar-num ar-set">
    <thead><tr><th scope="col">Quantity</th><th scope="col">Maximum</th><th scope="col">Last 60&nbsp;s</th></tr></thead>
    <tbody>{row('Tctl, &deg;C','tctl_c')}{row('CCD 1, &deg;C','ccd1_c')}{row('CCD 2, &deg;C','ccd2_c')}{row('Package power, W','pkg_w')}{row('Core voltage, V','vcore_v','{:.2f}')}{row('Average clock, MHz','clock_avg_mhz','{:.0f}')}{row('Voltage regulators, &deg;C','vrm_c')}</tbody>
  </table>
  </div>
  <p>Tctl peaked at {d.tctl_c.max():.1f}&nbsp;&deg;C {int(d.t_s[d.tctl_c.idxmax()])} seconds after the start, the short boost at the start of a Zen&nbsp;5 load, and then settled near {l.tctl_c.mean():.0f}&nbsp;&deg;C. Package power sat at {l.pkg_w.mean():.0f}&nbsp;W, the stock limit, so the processor was limited by power, not by temperature: it ran {95 - l.tctl_c.mean():.0f}&nbsp;&deg;C below its 95&nbsp;&deg;C maximum and never throttled. That margin is the room the controller has to slow the radiator fans.</p>
  <p class="ar-note">Provisional. The run lasted {int(d.t_s.max())} seconds and ended with Tctl still falling by about 0.3&nbsp;&deg;C per minute, shorter than the five minutes this article asks of a settled point; the next runs hold each fan setting longer and step the radiator fans down. Throttling is judged from Tctl and the clocks at constant power, because the monitoring library exposes no power-limit or throttle flags on this processor. <a href="/research/data/gpu-map-cpu1b.csv">Data (CSV)</a>.</p>
<!--cpu:end-->"""
a, b = s.find("<!--cpu:start-->"), s.find("<!--cpu:end-->")
if a < 0:
    i = s.index('  <h2 id="pareto">'); s = s[:i] + sec + "\n\n" + s[i:]
    s = s.replace('<li><a href="#controller">From model to controller</a></li>', '<li><a href="#controller">From model to controller</a></li>\n      <li><a href="#cpu">The processor</a></li>', 1)
else:
    s = s[:a] + sec + s[b + len("<!--cpu:end-->"):]
open(F, "w").write(s); print("cpu section written")
