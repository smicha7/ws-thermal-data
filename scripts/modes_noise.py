"""Noise-defined controller modes (Seb 2026-10-23): a noise budget at 1 m defines the mode; within it, the fan pair that keeps the core
coolest at 575 W (model 11, literature noise, intake 19.3 °C); core and memory at each power limit are the result.
Writes results-2026-10-23/modes-noise.json and the block <!--modes:start/end--> in the controller section. Usage: modes_noise.py"""
import json, re
from pathlib import Path
import numpy as np
G = Path(__file__).resolve().parent.parent; F = Path.home() / "Claude/gruency-site/research/gpu-cooling-method.html"
J = json.load(open(G / "results-2026-10-22/steady-stats.json")); MJ = json.load(open(G / "results-2026-10-23/mem-model.json"))
P = {p["param"]: p["est"] for p in J["params"]}; Q = {k: v[0] for k, v in MJ["params"].items()}
TIN = 19.3; PLW = {100: 575, 90: 518, 80: 460, 70: 402}; BUD = [("Quiet", 30), ("Balanced", 35), ("Performance", 40)]
core = lambda N, C, W: TIN + P["θ0"] + W * (P["r∞"] / 1000 + 1 / (P["gN"] * (N / 1000) ** P["m"] + P["gC"] * (C / 1500) ** P["s"]))
mem = lambda N, C, W: TIN + Q["θ0m"] + W * (Q["r∞"] / 1000 + 1 / (Q["gN"] * (N / 1000) ** Q["m"] + Q["gC"] * (C / 1500) ** Q["s"]))
hwb = np.array([(1281, 20), (1573, 25), (1871, 30), (2274, 35), (2771, 40)], float)
(a, b), *_ = np.linalg.lstsq(np.column_stack([np.ones(5), np.log10(hwb[:, 0])]), hwb[:, 1], rcond=None)
Ltot = lambda N, C: 10 * np.log10(10 ** ((32.5 + 50 * np.log10(N / 1570)) / 10) + 7 * 10 ** ((a + b * np.log10(C)) / 10))
pct2rpm = lambda p: 1313 + (p - 40) * (3012 - 1313) / 60
GP, CC = np.meshgrid(np.arange(40, 100.01, 0.5), np.arange(800, 3000.1, 25)); NN = pct2rpm(GP); L = Ltot(NN, CC)
modes = []
for name, bud in BUD:
    ok = L <= bud + 1e-9; i = np.argmin(np.where(ok, core(NN, CC, 575), np.inf))
    g, c, n = float(GP.ravel()[i]), float(CC.ravel()[i]), float(NN.ravel()[i])
    modes.append(dict(mode=name, budget=bud, gpu_pct=g, gpu_rpm=round(n, -1), case_rpm=c, dBA=round(float(L.ravel()[i]), 1),
                      temps={pl: (round(core(n, c, w), 1), round(mem(n, c, w), 1)) for pl, w in PLW.items()}))
assert all(m["dBA"] <= m["budget"] for m in modes)
json.dump(modes, open(G / "results-2026-10-23/modes-noise.json", "w"), indent=1)
pc = lambda g: f"{g:.0f}" if g == int(g) else f"{g:.1f}"
rows = "".join(f'<tr><td>{m["mode"]} (&le;&nbsp;{m["budget"]}&nbsp;dBA)</td><td>{pc(m["gpu_pct"])}&nbsp;% ({m["gpu_rpm"]:.0f}&nbsp;rpm)</td><td>{m["case_rpm"]:.0f}&nbsp;rpm</td><td>{m["dBA"]:.1f}&nbsp;dBA</td>'
               + "".join(f'<td>{m["temps"][pl][0]:.1f} / {m["temps"][pl][1]:.1f}&nbsp;&deg;C</td>' for pl in PLW) + "</tr>" for m in modes)
q = modes[0]; qm = q["temps"][100][1]
sec = f'''<!--modes:start-->
  <h3 id="controller-modes">How it decides: a noise budget per mode</h3>
  <p>A mode is defined by how loud the machine may be, not by a temperature. Each mode has a noise budget, the total level of all fans at 1&nbsp;m. Within the budget the controller picks the pair of GPU fan and case and radiator fan speeds that keeps the core coolest; the core and memory temperatures then follow from the power the card draws. Noise is what the user hears, so it is what the mode fixes; temperature is what the hardware must be protected from, so it is a constraint.</p>
  <p class="ar-tcap"><b>Controller modes defined by noise: the fan speeds each budget allows and the temperatures that result</b><br>Fan pair that keeps the core coolest within the budget at 575&nbsp;W; settled core / memory at each power limit from model (11) and the memory model, intake air {TIN}&nbsp;&deg;C, literature-based noise at 1&nbsp;m.</p>
  <div class="ar-tw ar-tw-wide">
  <table class="ar-tab ar-num ar-st ar-modes">
    <thead><tr><th scope="col">Mode (noise budget at 1&nbsp;m)</th><th scope="col">GPU fans</th><th scope="col">Case and radiator fans</th><th scope="col">Total noise at 1&nbsp;m</th><th scope="col">Core / memory, power limit 100&nbsp;% (575&nbsp;W)</th><th scope="col">Core / memory, 90&nbsp;% (518&nbsp;W)</th><th scope="col">Core / memory, 80&nbsp;% (460&nbsp;W)</th><th scope="col">Core / memory, 70&nbsp;% (402&nbsp;W)</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  </div>
  <p class="ar-note">Seven case and radiator fans run at the same speed; below about 880&nbsp;rpm the radiator fans stay at their floor. The noise models are literature-based and provisional until our own sound map; the temperatures are model predictions in an open case.</p>
  <ul>
    <li><b>Safety constraints.</b> The memory stays at or below its limit, 90&nbsp;&deg;C by default and never above 91&nbsp;&deg;C, the 95&nbsp;&deg;C hard limit less 4&nbsp;&deg;C (<a href="#controller-mem">Memory temperature limit</a>), and the core stays at or below its safety limit, 83&nbsp;&deg;C by default, adjustable by the user up to a hard cap of 88&nbsp;&deg;C, always below NVIDIA&rsquo;s own limits (maximum operating 90&nbsp;&deg;C, slowdown 93&nbsp;&deg;C).</li>
    <li><b>Power before noise.</b> If a constraint would be broken within the budget, the controller first lowers the power limit, by at most 5&nbsp;% every 30 seconds; it goes over the noise budget only when the power limit is already at its floor, 70&nbsp;% (402&nbsp;W), about the lowest the card accepts (a request for 50&nbsp;% is raised to 69&nbsp;%). Quiet at 575&nbsp;W already puts the memory at {qm:.1f}&nbsp;&deg;C at {TIN}&nbsp;&deg;C intake, {"right at" if qm > 89 else "close to"} the default limit, so in a warmer room Quiet lowers the power limit rather than speed up the fans.</li>
    <li><b>Model, then feedback.</b> The fan pair comes from equation (11); a proportional-integral term <a class="cite" href="#s15">[15]</a> on the measured temperatures corrects what the model misses, and the fans speed up quickly and slow down slowly, as in the first version below.</li>
  </ul>
<!--modes:end-->'''
s = F.read_text()
a, e = s.find("<!--modes:start-->"), s.find("<!--modes:end-->")
if a >= 0: s = s[:a] + sec + s[e + len("<!--modes:end-->"):]
else:
    i = s.index("  <h3>How it decides</h3>"); s = s[:i] + sec + "\n" + s[i:]
F.write_text(s)
for m in modes: print(m)
