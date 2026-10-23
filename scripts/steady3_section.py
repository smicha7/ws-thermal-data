import pandas as pd, math
p='/Users/smicha/Claude/gruency-site/research/gpu-cooling-method.html'; s=open(p).read()
d=pd.read_csv('/Users/smicha/Applications/Pasek/research/gpu-map/plan/steady3_path.csv'); d['h']=d.wait_s/3600
if ' The next series, steady3, is planned this way:' in s:
    a=s.index(' The next series, steady3, is planned this way:'); b=s.index('</p>',a); s=s[:a]+s[b:]
rows=''
for c,g in d.groupby('card'):
    i=g.dT.abs().idxmax(); r=d.loc[i]; pr=d.loc[i-1]
    where=(f"the change of GPU fans, {int(pr.card)} to {int(r.card)}&nbsp;%" if pr.card!=r.card else f"power limit {int(pr.pl)} to {int(r.pl)}&nbsp;% at case fans {int(r['case'])}&nbsp;rpm")
    rows+=f"<tr><td>{c}&nbsp;%</td><td>{len(g)}</td><td>{g.h.sum():.2f}</td><td>{g.core.min():.0f} to {g.core.max():.0f}</td><td>{abs(r.dT):.1f}</td><td>{where}</td></tr>"
tot=d.h.sum()
L1=lambda n: 32.5+50*math.log10(n/1570)
gpu=[(30,1020,'inaudible to super quiet'),(40,1312,'inaudible to super quiet'),(50,1595,'very quiet'),(60,1879,'moderate'),(70,2162,'loud'),(80,2446,'very loud'),(90,2729,'very loud'),(100,3013,'very loud')]
grow=''.join(f"<tr><td>{g}&nbsp;%</td><td>{'~' if g==30 else ''}{n}</td><td>~{L1(n):.0f}</td><td>{c}</td></tr>" for g,n,c in gpu)
case=[(800,'ultra-quiet; the radiator fans cannot go below about 880&nbsp;rpm'),(1000,'very quiet'),(1300,'quiet'),(1600,'balanced'),(1900,'loud'),(2400,'loud; a reference point of the model'),(3000,'very loud; full speed, about 2920&nbsp;rpm')]
crow=''.join(f"<tr><td>{c}&nbsp;rpm</td><td>{t}</td></tr>" for c,t in case)
pic=lambda th: (f'<a class="ar-wide th-{th[0]}" href="/research/img/gpu-map-steady3-path-{th}.webp?v=1" aria-label="Open the measurement path at full size"><picture>'
  f'<source media="(max-width:620px)" srcset="/research/img/gpu-map-steady3-path-phone-{th}.webp?v=1" width="1000" height="3500">'
  f'<img src="/research/img/gpu-map-steady3-path-{th}.webp?v=1" width="3000" height="1320" loading="lazy" decoding="async" alt="Seven grids, one per GPU fan speed from 40 to 100 %, each with four power limits by seven case fan speeds, coloured by the predicted settled core temperature from about 85 °C at the top left of the 40 % grid down to 47 °C, with arrows tracing a serpentine path through every cell and marks at the first and last point of each grid"></picture></a>')
block=f'''<!--steady3:start-->
  <p>The next series, steady3, follows this order: seven GPU fan speeds from 40 to 100&nbsp;%, four power limits and seven case fan speeds from 800 to 3000&nbsp;rpm, 196 settings. An anchor point, GPU fans 40&nbsp;%, case fans 1600&nbsp;rpm and full power, is measured only at the start and at the end, 198 points in all. Anchors in the middle of the run were dropped: going back to 40&nbsp;% from 90&nbsp;% would be a step of about 25&nbsp;&deg;C and would undo what the serpentine order saves. Drift within the run is instead tracked by the intake air logged every second and by the session term of the model.</p>
  <figure class="ar-fig ar-fig-wide">
    {pic('light')}{pic('dark')}
    <figcaption><b>Figure 13.</b> The planned path of steady3. One grid per GPU fan speed (in % and rpm); rows are power limits, columns case fan speeds in rpm and %. Colour and numbers: the settled core predicted by equation (11) at 19.3&nbsp;&deg;C intake air. Arrows follow the measurement order; a circle marks the first and a square the last point of each grid, where the next grid begins. <a href="/research/data/gpu-map-steady3-path.csv">Plan (CSV)</a>.</figcaption>
  </figure>
  <div class="ar-tw">
  <table class="ar-tab ar-num ar-txt">
    <thead><tr><th scope="col">GPU fans</th><th scope="col">Points</th><th scope="col">Hours</th><th scope="col">Predicted core, &deg;C</th><th scope="col">Largest step, &deg;C</th><th scope="col">Where</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  </div>
  <p class="ar-note">Planned; the 196 points take about {tot:.1f} hours, and the two anchors bring the run to about 18.5 hours.</p>
  <p>Each point waits at least eight minutes with the GPU fans at 40&nbsp;% and five minutes otherwise, and then until the core changes by less than 0.1&nbsp;&deg;C per minute. After a step of size $$dT$$ the slope, in &deg;C per minute, starts at $$s0$$ and decays as $$decay$$, so it falls below 0.1&nbsp;&deg;C per minute after about $$tw$$, with $$tau$$ in seconds and $$dT$$ in &deg;C; no point waits more than fifteen minutes. The first point adds a ten-minute warm-up. The waits come from equation (11) and the time constants measured on the settled points, so the plan is only as good as the model, and the run itself will show where it was wrong.</p>
  <p>The fan speeds of the plan sound, by Sebastian Michalski&rsquo;s scale for this machine, as follows; the levels for the card are the estimate of <a href="#noise-gpu">How loud is loud</a>, &plusmn;3&nbsp;dB.</p>
  <div class="ar-tw">
  <table class="ar-tab ar-num ar-txt">
    <thead><tr><th scope="col">GPU fans</th><th scope="col">rpm</th><th scope="col">Estimated dBA at 1&nbsp;m</th><th scope="col">Class</th></tr></thead>
    <tbody>{grow}</tbody>
  </table>
  </div>
  <div class="ar-tw">
  <table class="ar-tab ar-num ar-txt">
    <thead><tr><th scope="col">Case and radiator fans</th><th scope="col">Class</th></tr></thead>
    <tbody>{crow}</tbody>
  </table>
  </div>
  <p class="ar-note">These classes are listening judgments of this machine in its room, at the desk. For the card they are more lenient than the SilentPCReview scale for a single source at 1&nbsp;m: a card at 40&nbsp;% and about 29&nbsp;dBA is &ldquo;quiet&rdquo; there and &ldquo;super quiet&rdquo; here, because the room&rsquo;s own floor and the other fans mask it.</p>
<!--steady3:end-->'''
if '<!--steady3:start-->' in s:
    a2=s.index('<!--steady3:start-->'); b2=s.index('<!--steady3:end-->')+len('<!--steady3:end-->'); s=s[:a2]+block+s[b2:]
else:
    i=s.index('id="method-next"'); j=s.index('</p>',i)+4; s=s[:j]+'\n'+block+s[j:]
open(p,'w').write(s); print('ok', round(tot,2))
