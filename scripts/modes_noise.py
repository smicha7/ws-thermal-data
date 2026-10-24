"""Controller modes as released (WS.Sensor 0.30.69): a noise budget is a ceiling; within it the quietest fan pair that keeps the core and
memory at the mode's comfort level, else the coolest pair within the budget, then the power limit (floor 70 %), only then over budget.
Planned operating points at full load for each power limit (controller_sim planning, intake 19.3 °C). Writes <!--modes:start/end-->
and results-2026-10-23/modes-noise.json. Usage: modes_noise.py"""
import json, sys
from pathlib import Path
G = Path(__file__).resolve().parent.parent; sys.path.insert(0, str(G)); F = Path.home() / "Claude/gruency-site/research/gpu-cooling-method.html"
import controller_sim as cs
TIN = 19.3; PLW = {100: 575, 90: 518, 80: 460, 70: 402}; NM = {"quiet": "Quiet", "balanced": "Balanced", "performance": "Performance"}
modes = []
for m in ("quiet", "balanced", "performance"):
    c = cs.Controller(m); d = dict(mode=NM[m], budget=c.budget, core_comfort=cs.CORE_LIMIT_DEFAULT - cs.MODES[m]["comfort"][0],
                                   mem_comfort=c.mem_l - cs.MODES[m]["comfort"][1], points={})
    for pl, W in PLW.items():
        c = cs.Controller(m, P_stock=W)   # the set power limit: full load at W means the 40 % load floor
        N, C, plc, over = c.make_plan(W, TIN); core, mem = cs.steady_ff(W * plc, N, C, TIN)
        d["points"][pl] = dict(W=W, gpu_pct=round(float(cs.RPM_DUTY(N)), 1), gpu_rpm=int(round(N, -1)), case_rpm=int(round(C, -1)), dBA=round(float(cs.noise(N, C)), 1),
                               core=round(float(core), 1), mem=round(float(mem), 1), pl_cut=round(float(plc) * 100), over=bool(over), comfy=bool(core <= d["core_comfort"] + 1e-9 and mem <= d["mem_comfort"] + 1e-9))
    modes.append(d)
json.dump(modes, open(G / "results-2026-10-23/modes-noise.json", "w"), indent=1)
rows = ""
for d in modes:
    for pl, p in d["points"].items():
        mk = "" if p["comfy"] else "<sup>a</sup>"
        rows += (f'<tr><td>{d["mode"]}</td><td>{d["budget"]:.0f}</td><td>{d["core_comfort"]:.0f}</td><td>{d["mem_comfort"]:.0f}</td><td>{pl}&nbsp;% ({p["W"]}&nbsp;W)</td>'
                 f'<td class="g">{p["gpu_pct"]:.1f}</td><td>{p["gpu_rpm"]}</td><td>{p["case_rpm"]}</td><td class="g">{p["dBA"]:.1f}</td><td>{p["core"]:.1f}{mk}</td><td>{p["mem"]:.1f}</td></tr>')
q = modes[0]["points"][100]
sec = f'''<!--modes:start-->
  <h3 id="controller-modes">How it decides: a noise budget per mode</h3>
  <p>A mode is defined by how loud the machine may become, not by a temperature. Each mode has a noise budget, the total level of all fans at 1&nbsp;m, which is a ceiling, and a comfort level for the core and the memory, a set distance below their limits: 5 and 3&nbsp;&deg;C in Quiet, 10 and 5&nbsp;&deg;C in Balanced, 15 and 8&nbsp;&deg;C in Performance. Within the budget the controller chooses the quietest fan pair that keeps both at their comfort levels. If no pair within the budget can, it takes the coolest pair within the budget; if that would break a safety limit, it lowers the power limit, by 5&nbsp;% at most every 30 seconds down to 70&nbsp;%; only at that floor may the fans exceed the budget.</p>
  <p class="ar-tcap"><b>Controller modes: noise budget, comfort levels and the planned operating point at full load for each power limit.</b> Quietest fan pair within the budget that keeps the core and memory at their comfort levels, from equations (R1) and (R2), intake air {TIN}&nbsp;&deg;C, literature-based noise at 1&nbsp;m.</p>
  <div class="ar-tw ar-tw-wide">
  <table class="ar-tab ar-num ar-st ar-modes ar-ms">
    <thead><tr><th scope="col" rowspan="2">Mode</th><th scope="col" rowspan="2">Noise budget, dBA</th><th scope="colgroup" colspan="2">Comfort level, &deg;C</th><th scope="col" rowspan="2">Power limit</th><th scope="colgroup" colspan="2">GPU fans</th><th scope="col" rowspan="2">Case and radiator fans, rpm</th><th scope="col" rowspan="2" class="g">Total noise at 1&nbsp;m, dBA</th><th scope="col" rowspan="2">Core, &deg;C</th><th scope="col" rowspan="2">Memory, &deg;C</th></tr><tr><th scope="col">core</th><th scope="col">memory</th><th scope="col" class="g">%</th><th scope="col">rpm</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  </div>
  <p class="ar-note">Comfort levels are set below the default limits of 83&nbsp;&deg;C (core) and 90&nbsp;&deg;C (memory). <sup>a</sup> The comfort level cannot be reached within the budget; the coolest pair within the budget is used, still inside the safety limits.</p>
  <ul>
    <li><b>Safety constraints.</b> The core stays at or below its safety limit, 83&nbsp;&deg;C by default and at most 88&nbsp;&deg;C, and the memory at or below 90&nbsp;&deg;C by default and never above 91&nbsp;&deg;C, the 95&nbsp;&deg;C hard limit less a 4&nbsp;&deg;C margin (<a href="#templimits">Section 2.2</a>). The feed-forward keeps a model margin of at least 1&nbsp;&deg;C below each limit.</li>
    <li><b>Power before noise.</b> When the budget cannot hold the safety limits, the power limit is lowered before the budget is exceeded (<a href="#control-law">Section 5.1</a>).</li>
    <li><b>Floors and ramps.</b> At light load every mode runs at the fan floors, GPU fans 30&nbsp;% rising to 40&nbsp;% with load, case fans 800&nbsp;rpm, never 0&nbsp;rpm. The fans speed up quickly and slow down slowly, and a pair is kept until a new one is clearly quieter, so the fans do not hunt.</li>
  </ul>
<!--modes:end-->'''
s = F.read_text(); a, b = s.index("<!--modes:start-->"), s.index("<!--modes:end-->") + len("<!--modes:end-->")
F.write_text(s[:a] + sec + s[b:])
for d in modes: print(d["mode"], {k: (v["gpu_pct"], v["case_rpm"], v["dBA"], v["core"], v["mem"], v["comfy"]) for k, v in d["points"].items()})
