"""Simulation subsection of the controller (noise-budget modes) from results-2026-10-22/controller-sim.json, between
<!--ctrlsim:start/end--> (first run: replaces from '<h3>What the simulation shows</h3>' to '<!--ctrl1:start-->'). Usage: ctrlsim_section.py <fig ver>"""
import json, sys
from pathlib import Path
G = Path(__file__).resolve().parent.parent; F = Path.home() / "Claude/gruency-site/research/gpu-cooling-method.html"
V = sys.argv[1] if len(sys.argv) > 1 else "9"
J = json.load(open(G / "results-2026-10-22/controller-sim.json")); st, wa, bu = J["step 30->575 W"], J["intake 19->30 °C"], J["bursts 60 s on/off"]; li = J.get("light 30->150 W", st)
key = lambda pre: next(k for k in st if k.startswith(pre))
K = [("factory", "Factory NVIDIA curve (no budget)"), ("WS.Sensor quiet", "Quiet (&le;&nbsp;30&nbsp;dBA)"), ("WS.Sensor balanced", "Balanced (&le;&nbsp;35&nbsp;dBA)"), ("WS.Sensor performance", "Performance (&le;&nbsp;40&nbsp;dBA)")]
K = [(key(p), n) for p, n in K]
def over(k):
    v = [d[k]["s_over_budget"] for d in (st, wa, bu)]
    return "&mdash;" if v[0] is None else f"{max(v)}"
rows = "".join(f'<tr><td>{n}</td><td class="g">{li[k]["noise_mean"]:.1f}</td><td class="g">{st[k]["peak"]:.1f}</td><td>{st[k]["noise_mean"]:.1f}</td><td class="g">{wa[k]["peak"]:.1f}</td><td>{wa[k]["mem_peak"]:.1f}</td>'
               f'<td>{wa[k]["noise_max"]:.1f}</td><td>{wa[k]["pl_min"]*100:.0f}</td><td>{wa[k]["work_W"]:.0f}</td><td class="g">{bu[k]["card_reversals_per_min"]:.2f}</td><td class="g">{over(k)}</td></tr>' for k, n in K)
f_, q, b_, p_ = (k for k, _ in K)
sec = f'''<!--ctrlsim:start-->
  <h3 id="s-what-the-simulation-shows">What the simulation shows</h3>
  <p>The simulated card is the dynamic model (10) with its memory node; the controller is the released WS.Sensor 0.30.69 with the noise-budget modes of <a href="#controller-modes">How it decides</a>. The factory curve is modelled from the card&rsquo;s driver fan curve with the case fans fixed at 1000&nbsp;rpm. Four tests: a light load of 150&nbsp;W, a load step from idle to 575&nbsp;W, intake air rising from 19 to 30&nbsp;&deg;C at full load, and load bursts of 60 seconds on and off.</p>
  <p class="ar-tcap"><b>Simulated controller (noise-budget modes) against the factory fan curve, RTX 5090 in the open case: highest temperatures, noise, power and fan reversals in four tests.</b> Light load: idle to 150&nbsp;W. Load step: idle to 575&nbsp;W at 19.3&nbsp;&deg;C intake. Warm room: intake air rising from 19.3 to 30&nbsp;&deg;C at full load. Short bursts: 60&nbsp;s full load, 60&nbsp;s idle, repeated.</p>
  <div class="ar-tw ar-tw-wide">
  <table class="ar-tab ar-num ar-st ar-ms">
    <thead><tr><th scope="col" rowspan="2">Fan control</th><th scope="col" class="g">Light load, 150&nbsp;W</th><th scope="colgroup" colspan="2">Load step</th><th scope="colgroup" colspan="5">Warm room</th><th scope="col" class="g">Short bursts</th><th scope="col" class="g">Any test</th></tr><tr><th scope="col" class="g">mean noise at 1&nbsp;m, dBA</th><th scope="col" class="g">highest core, &deg;C</th><th scope="col">mean noise at 1&nbsp;m, dBA</th><th scope="col" class="g">highest core, &deg;C</th><th scope="col">highest memory, &deg;C</th><th scope="col">highest noise at 1&nbsp;m, dBA</th><th scope="col">lowest power limit, %</th><th scope="col">mean power, W</th><th scope="col" class="g">fan reversals, per min</th><th scope="col" class="g">time over noise budget, s</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  </div>
  <p class="ar-note">Fan reversals: how often per minute the fans switch from speeding up to slowing down. The controller lowers the power limit when the memory or core limit would otherwise be broken within the noise budget. &mdash;: the factory curve has no noise budget. Noise is the literature-based estimate (<a href="#pareto-lit">section &lsquo;A first frontier&rsquo;</a>), summed by equation (13) provisional until our own sound map.</p>
  <p>At light load every mode runs at the fan floors, {li[q]["noise_mean"]:.1f}&nbsp;dBA, because the comfort levels are met there; the budgets matter only under heavy load. Each mode holds its noise budget in every test: no second over it. After the load step Quiet settles at {st[q]["peak"]:.1f}&nbsp;&deg;C, Balanced at {st[b_]["peak"]:.1f} and Performance at {st[p_]["peak"]:.1f}&nbsp;&deg;C, against {st[f_]["peak"]:.1f}&nbsp;&deg;C for the factory curve at {st[f_]["noise_mean"]:.1f}&nbsp;dBA.{(f' To hold 30&nbsp;dBA while the card heats, Quiet trims the power limit to {st[q]["pl_min"]*100:.0f}&nbsp;% for {st[q]["s_pl_cut"]/60:.0f} minutes after the step.' if st[q]["pl_min"] < 1 else "")} When the room warms by 11&nbsp;&deg;C, the factory curve speeds up to {wa[f_]["noise_max"]:.1f}&nbsp;dBA and its core rises to {wa[f_]["peak"]:.1f}&nbsp;&deg;C. Quiet keeps its 30&nbsp;dBA and protects the memory instead: it lowers the power limit to {wa[q]["pl_min"]*100:.0f}&nbsp;% for {wa[q]["s_pl_cut"]/60:.0f} minutes, the card averages {wa[q]["work_W"]:.0f}&nbsp;W, and the memory peaks at {wa[q]["mem_peak"]:.1f}&nbsp;&deg;C. Balanced and Performance stay at full power within their budgets; their cores rise to {wa[b_]["peak"]:.1f} and {wa[p_]["peak"]:.1f}&nbsp;&deg;C, inside the 83&nbsp;&deg;C core limit. Under load bursts the factory curve reverses its fans {bu[f_]["card_reversals_per_min"]:.2f} times a minute, the audible pumping of a fan that chases every burst; ours never reverses in simulation, though on the real card the first version did (<a href="#controller-hw">Section 5.4.2</a>).</p>
  <p>The load estimate of the controller divides the measured power by the power limit only when the card is actually held at its limit, a correction made in WS.Sensor 0.30.55 after the first version cut its power limit too far in simulation (<a href="#appendix-c">Appendix C</a>).</p>
  <p>Two caveats. The noise figures are literature-based estimates until we have sound-level measurements of these fans, and every result in this subsection is simulated, on one card in an open case: the simulated card is the dynamic model (<a href="#dyn-results">Section 4.5</a>), while the controller plans with equations (R1) and (R2), so the simulation also tests the controller against a model it was not built on; the next subsection compares the first version with the real card.</p>
  <figure class="ar-fig">
    {"".join(f'<a class="ar-wide th-{t[0]}" href="/research/img/gpu-map-controller-sim-{t}.webp?v={V}" aria-label="Open the controller chart at full size"><picture><source media="(max-width:620px)" srcset="/research/img/gpu-map-controller-sim-phone-{t}.webp?v={V}" width="1000" height="3400"><img src="/research/img/gpu-map-controller-sim-{t}.webp?v={V}" width="2600" height="1920" loading="lazy" decoding="async" alt="Simulated core temperature, GPU fan speed and case fan speed over 40 minutes for a load step, intake air rising from 19 to 30 °C and 60-second load bursts, comparing the factory fan curve with the Quiet, Balanced and Performance noise-budget modes"></picture></a>' for t in ("light", "dark"))}
    <figcaption><b>Figure 15.</b> The noise-budget controller in simulation. Simulated core, GPU fans in % and rpm, and case fans in rpm and %, for the factory curve (dashed) and the Quiet (&le;&nbsp;30&nbsp;dBA), Balanced (&le;&nbsp;35&nbsp;dBA) and Performance (&le;&nbsp;40&nbsp;dBA) modes. Rows: three of the four tests, a load step from 30 to 575&nbsp;W, intake air rising from 19 to 30&nbsp;&deg;C, and 60-second load bursts.</figcaption>
  </figure>
<!--ctrlsim:end-->
'''
s = F.read_text()
a, e = s.find("<!--ctrlsim:start-->"), s.find("<!--ctrlsim:end-->")
if a >= 0: s = s[:a] + sec.rstrip("\n") + s[e + len("<!--ctrlsim:end-->"):]
else:
    i = s.index("<!--ctrlsim:start-->"); j = s.index("<!--ctrl1:start-->"); s = s[:i] + sec + "\n" + s[j:]
F.write_text(s); print("ctrlsim written")
