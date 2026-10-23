"""Simulation subsection of the controller (noise-budget modes) from results-2026-10-22/controller-sim.json, between
<!--ctrlsim:start/end--> (first run: replaces from '<h3>What the simulation shows</h3>' to '<!--ctrl1:start-->'). Usage: ctrlsim_section.py <fig ver>"""
import json, sys
from pathlib import Path
G = Path(__file__).resolve().parent.parent; F = Path.home() / "Claude/gruency-site/research/gpu-cooling-method.html"
V = sys.argv[1] if len(sys.argv) > 1 else "8"
J = json.load(open(G / "results-2026-10-22/controller-sim.json")); st, wa, bu = J["step 30->575 W"], J["intake 19->30 °C"], J["bursts 60 s on/off"]
key = lambda pre: next(k for k in st if k.startswith(pre))
K = [("factory", "Factory NVIDIA curve (no budget)"), ("WS.Sensor quiet", "Quiet (&le;&nbsp;30&nbsp;dBA)"), ("WS.Sensor balanced", "Balanced (&le;&nbsp;35&nbsp;dBA)"), ("WS.Sensor performance", "Performance (&le;&nbsp;40&nbsp;dBA)")]
K = [(key(p), n) for p, n in K]
def over(k):
    v = [d[k]["s_over_budget"] for d in (st, wa, bu)]
    return "&mdash;" if v[0] is None else f"{max(v)}&nbsp;s"
rows = "".join(f'<tr><td>{n}</td><td>{st[k]["peak"]:.1f}&nbsp;&deg;C</td><td>{st[k]["noise_mean"]:.1f}&nbsp;dBA</td><td>{wa[k]["peak"]:.1f}&nbsp;&deg;C</td><td>{wa[k]["mem_peak"]:.1f}&nbsp;&deg;C</td>'
               f'<td>{wa[k]["noise_max"]:.1f}&nbsp;dBA</td><td>{wa[k]["pl_min"]*100:.0f}&nbsp;%</td><td>{wa[k]["work_W"]:.0f}&nbsp;W</td><td>{bu[k]["card_reversals_per_min"]:.1f}</td><td>{over(k)}</td></tr>' for k, n in K)
f_, q, b_, p_ = (k for k, _ in K)
sec = f'''<!--ctrlsim:start-->
  <h3>What the simulation shows</h3>
  <p>The simulated card is the dynamic model (10) with its memory node; the controller runs the noise-budget modes of <a href="#controller-modes">How it decides</a>. The factory curve is modelled from the card&rsquo;s driver fan curve with the case fans fixed at 1000&nbsp;rpm. Three tests: a load step from idle to 575&nbsp;W, intake air rising from 19 to 30&nbsp;&deg;C at full load, and load bursts of 60 seconds on and off.</p>
  <p class="ar-tcap"><b>Simulated controller (noise-budget modes) vs the factory fan curve, RTX 5090, open case</b><br>Load step: idle &rarr; 575&nbsp;W at 19&nbsp;&deg;C intake. Warm room: intake air rising from 19 to 30&nbsp;&deg;C at full load. Short bursts: 60&nbsp;s full load, 60&nbsp;s idle.</p>
  <div class="ar-tw ar-tw-wide">
  <table class="ar-tab ar-num ar-st">
    <thead><tr><th scope="col">Fan control</th><th scope="col">Load step: highest core</th><th scope="col">Load step: mean noise at 1&nbsp;m</th><th scope="col">Warm room: highest core</th><th scope="col">Warm room: highest memory</th><th scope="col">Warm room: highest noise at 1&nbsp;m</th><th scope="col">Warm room: lowest power limit</th><th scope="col">Warm room: mean power</th><th scope="col">Short bursts: fan reversals per min</th><th scope="col">Time over noise budget, any test</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  </div>
  <p class="ar-note">Fan reversals: how often per minute the fans switch from speeding up to slowing down. Power limit: the share of the card&rsquo;s 575&nbsp;W it may use; the controller lowers it when the memory or core limit would otherwise be broken within the noise budget. The factory curve has no noise budget. Noise is the literature-based estimate of <a href="#pareto-lit">A first frontier, from the literature</a>, summed by equation (13); provisional until our own sound map.</p>
  <p>Each mode holds its noise budget in every test: no second over it. After the load step Quiet settles at {st[q]["peak"]:.1f}&nbsp;&deg;C, Balanced at {st[b_]["peak"]:.1f} and Performance at {st[p_]["peak"]:.1f}&nbsp;&deg;C, against {st[f_]["peak"]:.1f}&nbsp;&deg;C for the factory curve at {st[f_]["noise_mean"]:.1f}&nbsp;dBA. When the room warms by 11&nbsp;&deg;C, the factory curve speeds up to {wa[f_]["noise_max"]:.1f}&nbsp;dBA and its core rises to {wa[f_]["peak"]:.1f}&nbsp;&deg;C. Quiet keeps its 30&nbsp;dBA and protects the memory instead: it lowers the power limit to {wa[q]["pl_min"]*100:.0f}&nbsp;% for {wa[q]["s_pl_cut"]/60:.0f} minutes, the card averages {wa[q]["work_W"]:.0f}&nbsp;W, and the memory peaks at {wa[q]["mem_peak"]:.1f}&nbsp;&deg;C. Balanced and Performance stay at full power within their budgets; their cores rise to {wa[b_]["peak"]:.1f} and {wa[p_]["peak"]:.1f}&nbsp;&deg;C, inside the 83&nbsp;&deg;C core limit. Under load bursts the factory curve reverses its fans {bu[f_]["card_reversals_per_min"]:.2f} times a minute, the audible pumping of a fan that chases every burst; ours never reverses in simulation, though on the real card the first version did (see below).</p>
  <p>The first version, with temperature targets, was simulated the same way. It held its targets of 80, 77 and 72&nbsp;&deg;C with no second more than 1&nbsp;&deg;C above them, while the factory curve stayed above 78&nbsp;&deg;C for 842 seconds of the warm-room test. Its simulation also exposed a fault: in Quiet mode with warm intake air the controller cut the power limit to 70&nbsp;% for about five minutes, because the load estimate divided the held peak of power by the current power limit, so every step down of the limit raised the estimated demand. The corrected controller, WS.Sensor 0.30.55, divides the measured power by the limit only when the card is actually held at its limit and lowers the limit by at most 5&nbsp;% every 30 seconds; the noise-budget modes keep that logic.</p>
  <p>Two caveats. The noise figures are literature-based estimates until we have sound-level measurements of these fans, and every result in this subsection is simulated, on a model fitted to one card in an open case; the next subsection compares the first version with the real card.</p>
  <figure class="ar-fig">
    {"".join(f'<a class="ar-wide th-{t[0]}" href="/research/img/gpu-map-controller-sim-{t}.webp?v={V}" aria-label="Open the controller chart at full size"><picture><source media="(max-width:620px)" srcset="/research/img/gpu-map-controller-sim-phone-{t}.webp?v={V}" width="1000" height="3400"><img src="/research/img/gpu-map-controller-sim-{t}.webp?v={V}" width="2600" height="1920" loading="lazy" decoding="async" alt="Simulated core temperature, GPU fan speed and case fan speed over 40 minutes for a load step, intake air rising from 19 to 30 °C and 60-second load bursts, comparing the factory fan curve with the Quiet, Balanced and Performance noise-budget modes"></picture></a>' for t in ("light", "dark"))}
    <figcaption><b>Figure 15.</b> The noise-budget controller in simulation. Simulated core, GPU fans in % and rpm, and case fans in rpm and %, for the factory curve (dashed) and the Quiet (&le;&nbsp;30&nbsp;dBA), Balanced (&le;&nbsp;35&nbsp;dBA) and Performance (&le;&nbsp;40&nbsp;dBA) modes. Rows: a load step from 30 to 575&nbsp;W, intake air rising from 19 to 30&nbsp;&deg;C, and 60-second load bursts.</figcaption>
  </figure>
<!--ctrlsim:end-->
'''
s = F.read_text()
a, e = s.find("<!--ctrlsim:start-->"), s.find("<!--ctrlsim:end-->")
if a >= 0: s = s[:a] + sec.rstrip("\n") + s[e + len("<!--ctrlsim:end-->"):]
else:
    i = s.index("  <h3>What the simulation shows</h3>"); j = s.index("<!--ctrl1:start-->"); s = s[:i] + sec + "\n" + s[j:]
F.write_text(s); print("ctrlsim written")
