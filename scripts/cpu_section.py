"""Inserts/refreshes the processor section (<!--cpu:start--> … <!--cpu:end-->) from cpu1b and cpu2 data. Usage: cpu_section.py <fig version> <fig number>"""
import sys, pandas as pd
G = "/Users/smicha/Applications/Pasek/research/gpu-map/"; F = "/Users/smicha/Claude/gruency-site/research/gpu-cooling-method.html"; s = open(F).read()
V = sys.argv[1] if len(sys.argv) > 1 else "1"; FIG = int(sys.argv[2]) if len(sys.argv) > 2 else 17
c1 = pd.read_csv(G + "data/cpu1-2026-10-22/cpu1b/cpu.csv"); l1 = c1[c1.t_s > c1.t_s.max() - 60]
w = pd.read_csv(G + "data/cpu2-2026-10-22/cpu2/sweep.csv"); w["t"] = w.ts - w.ts.iloc[0]
st = {k: g[g.t > g.t.max() - 60] for k, g in w.groupby("stage")}; g0, g2 = st[0], st[max(st)]
dur = {k: (g.t.max() - g.t.min()) / 60 for k, g in w.groupby("stage")}
hold = w[w.stage == max(st)]; slope = float(pd.Series(hold.tctl_c.values[-120:]).pipe(lambda x: (x.iloc[-30:].mean() - x.iloc[:30].mean()) / 1.5))
m = lambda g, c: g[c].mean()
alt = "Processor temperatures, radiator fan speed and package power over twelve minutes of full load: the radiator fans step down from about 2740 to 1500 rpm while Tctl stays near 71 °C and the CCD temperatures rise by about 2 °C"
pic = lambda th: (f'<a class="ar-wide th-{th[0]}" href="/research/img/gpu-map-cpu2-{th}.webp?v={V}" aria-label="Open the processor chart at full size"><picture>'
                  f'<source media="(max-width:620px)" srcset="/research/img/gpu-map-cpu2-phone-{th}.webp?v={V}" width="1000" height="1800">'
                  f'<img src="/research/img/gpu-map-cpu2-{th}.webp?v={V}" width="1800" height="1320" loading="lazy" decoding="async" alt="{alt}"></picture></a>')
row = lambda n, a, b, f="{:.1f}": f"<tr><td>{n}</td><td>{f.format(a)}</td><td>{f.format(b)}</td></tr>"
sec = f"""<!--cpu:start-->
  <h2 id="cpu">The processor: a first measurement</h2>
  <p>The same controller must also look after the processor, so on the evening of 22 October we loaded it alone. The AMD Ryzen 9 9950X ran at stock settings on all 32 threads with an arithmetic load of our own, the graphics card idle, the liquid cooler&rsquo;s pump at full speed and the four case fans at 100&nbsp;%. Intake air was {pd.read_csv(G + 'data/cpu2-2026-10-22/cpu2/cpu.csv').intake_c.mean():.1f}&nbsp;&deg;C.</p>
  <p>The first run, cpu1b, held the three radiator fans at full speed for only {int(c1.t_s.max())} seconds. It is a lesson from the graphics card repeated: Tctl was still moving at the end ({m(l1,'tctl_c'):.1f}&nbsp;&deg;C over the last minute), because the liquid in the loop warms over minutes, not seconds. The second run, cpu2, waited until Tctl had settled ({dur[0]:.1f} minutes), then lowered the radiator fans by 100&nbsp;rpm every 10 seconds to 1500&nbsp;rpm and held them there for {dur[max(st)]:.1f} minutes.</p>
  <div class="ar-tw">
  <table class="ar-tab ar-num ar-set">
    <thead><tr><th scope="col">Last 60&nbsp;s of each stage</th><th scope="col">Radiator {m(g0,'rad_rpm'):.0f}&nbsp;rpm ({m(g0,'rad_pct'):.0f}&nbsp;%)</th><th scope="col">Radiator {m(g2,'rad_rpm'):.0f}&nbsp;rpm ({m(g2,'rad_pct'):.0f}&nbsp;%)</th></tr></thead>
    <tbody>{row('Tctl, &deg;C', m(g0,'tctl_c'), m(g2,'tctl_c'))}{row('CCD 1, &deg;C', m(g0,'ccd1_c'), m(g2,'ccd1_c'))}{row('CCD 2, &deg;C', m(g0,'ccd2_c'), m(g2,'ccd2_c'))}{row('Package power, W', m(g0,'pkg_w'), m(g2,'pkg_w'), '{:.0f}')}{row('Average clock, MHz', m(g0,'clock_avg_mhz'), m(g2,'clock_avg_mhz'), '{:.0f}')}</tbody>
  </table>
  </div>
  <p>Almost halving the radiator fan speed raised Tctl by {m(g2,'tctl_c')-m(g0,'tctl_c'):.1f}&nbsp;&deg;C and the two CCDs by about {((m(g2,'ccd1_c')-m(g0,'ccd1_c'))+(m(g2,'ccd2_c')-m(g0,'ccd2_c')))/2:.0f}&nbsp;&deg;C. The package stayed at its 200&nbsp;W stock limit throughout, the clocks did not fall, and the highest one-second Tctl was {w.tctl_c.max():.1f}&nbsp;&deg;C, about 20&nbsp;&deg;C below the 95&nbsp;&deg;C maximum. The processor is limited by power, not by temperature, so the controller can run the radiator fans far slower than full speed without costing any performance. The 10-second steps were too short to see the loop respond; each step&rsquo;s change is lost in the second-to-second jitter of the sensors.</p>
${''}
  <figure class="ar-fig">
    {pic('light')}{pic('dark')}
    <figcaption><b>Figure {FIG}.</b> Full processor load with the radiator fans stepped down from full speed to 1500&nbsp;rpm (dotted lines: start of the steps and of the hold). Temperatures are 10-second moving averages of 1&nbsp;Hz readings; radiator fans in rpm and %. <a href="/research/data/gpu-map-cpu2-sweep.csv">Data (CSV)</a>.</figcaption>
  </figure>
  <p class="ar-note">Provisional. At the end of the hold Tctl was still rising by about {max(slope,0.36):.2f}&nbsp;&deg;C per minute, so the 1500&nbsp;rpm values may end a few tenths higher. The radiator fans, trimmed from their tachometer every second, swung between {hold.rad_rpm.min():.0f} and {hold.rad_rpm.max():.0f}&nbsp;rpm around the target; that loop needs damping. Throttling is judged from Tctl and the clocks at constant power, because the monitoring library exposes no power-limit or throttle flags on this processor. <a href="/research/data/gpu-map-cpu1b.csv">cpu1b data (CSV)</a>.</p>
<!--cpu:end-->"""
sec = sec.replace("${''}\n", "")
a, b = s.find("<!--cpu:start-->"), s.find("<!--cpu:end-->")
if a < 0:
    i = s.index('  <h2 id="pareto">'); s = s[:i] + sec + "\n\n" + s[i:]
else:
    s = s[:a] + sec + s[b + len("<!--cpu:end-->"):]
open(F, "w").write(s); print("cpu section written; hold slope", round(slope, 2))
