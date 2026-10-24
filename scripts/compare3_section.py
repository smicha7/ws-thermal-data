"""Three setups, one equation (prepared 2026-10-24, publishes only when at least two setups have grid data):
(1) ZOTAC RTX 5090 Solid, single card (steady3); (2) RTX 5090 FE single (card B alone); (3) 2 × RTX 5090 FE, cards A and B (steady4).
Fits the primary form (saturating GPU-fan conductance, model3/steady3_fit) to each setup and card: parameter table with RMSE and LOO,
a figure of settled core against GPU fan speed at 575 W and case fans 1600 rpm, and a Discussion subsection (brand/cooler, second card).
Writes <!--compare3:start/end--> before the 'Comparison with the literature' subsection. Usage: compare3_section.py"""
import csv, glob
from pathlib import Path
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.optimize import least_squares
from PIL import Image
G = Path(__file__).resolve().parent.parent; F = Path.home() / "Claude/gruency-site/research/gpu-cooling-method.html"; IMG = F.parent / "img"
OUT = Path(__file__).resolve().parent / "out/cmp3"; OUT.mkdir(parents=True, exist_ok=True)
# (label, folder glob, card column prefix, exclude substring) — ponytail: adjust the FE-single glob when its folder name is known
SETUPS = [("ZOTAC RTX 5090 Solid, single card", "steady3-*", "cardA", None),
          ("RTX 5090 FE, single card (card B alone)", "*fe-single*", "cardB", None),
          ("2 &times; RTX 5090 FE, card A (upper)", "*steady4*", "cardA", None),
          ("2 &times; RTX 5090 FE, card B (lower)", "*steady4*", "cardB", None)]
NAMES = ["θ0", "r∞", "gN", "m", "n½", "gC", "s"]
def model(v, n, c, P): return v[0] + P * (v[1] / 1000 + 1 / (v[2] * n ** v[3] / (v[6] ** v[3] + n ** v[3]) + v[4] * c ** v[5]))
X0 = [2, 40, 40, 2.5, 7, 0.5, 2.3]   # order θ0, r∞, gN, m, gC, s, n½ (as in model())
def load(pat, card):
    fs = sorted(glob.glob(str(G / "data" / pat / "grid.csv")))
    if not fs: return None
    r = list(csv.DictReader(open(fs[-1])))
    key = lambda x: (x["pl_pct"], x["gpu_pct"], x["case_rpm_target"])
    if len(r) > 1 and key(r[0]) == key(r[-1]): r = r[1:-1]
    d = {}
    for x in r:
        if x.get("settled") != "1": continue
        try: d[key(x)] = (float(x[f"{card}_fan_rpm"]) / 1000, float(x["case_rpm"]) / 1500, float(x[f"{card}_power_w"] or x["power_w_sum"]),
                          float(x[f"{card}_core_nvapi_c"] or x[f"{card}_core_c"]) - float(x["intake_c"]))
        except (ValueError, KeyError): pass
    return np.array(list(d.values())) if len(d) >= 20 else None
res = []
for lab, pat, card, _ in SETUPS:
    a = load(pat, card)
    if a is None: continue
    n, c, P, y = a.T
    f = least_squares(lambda v: model(v, n, c, P) - y, X0, method="lm", max_nfev=20000); e = y - model(f.x, n, c, P)
    loo = [y[i] - model(least_squares(lambda v: model(v, n[m_], c[m_], P[m_]) - y[m_], f.x, method="lm").x, n[i:i+1], c[i:i+1], P[i:i+1])[0]
           for i in range(len(y)) for m_ in [np.arange(len(y)) != i]]
    v = dict(zip(["θ0", "r∞", "gN", "m", "gC", "s", "n½"], f.x))
    res.append(dict(lab=lab, n=len(y), v=v, rmse=float(np.sqrt(np.mean(e ** 2))), loo=float(np.sqrt(np.mean(np.square(loo)))), x=f.x))
s = F.read_text(); a_, b_ = s.find("<!--compare3:start-->"), s.find("<!--compare3:end-->")
PUBLISH = False   # Seb 2026-10-24: prepare only; set True when the FE single-card run and steady4 are complete
for r in res: print(r["lab"], r["n"], {k: round(float(x), 3) for k, x in r["v"].items()}, round(r["rmse"], 2), round(r["loo"], 2))
if len(res) < 2 or not PUBLISH:   # nothing to publish yet: keep the page free of a half-built section
    if a_ >= 0: s = s[:a_] + s[b_ + len("<!--compare3:end-->"):]; F.write_text(s)
    print("compare3: setups with data:", [r["lab"] for r in res], "— not published"); raise SystemExit(0)
fmt = {"θ0": 2, "r∞": 1, "gN": 1, "m": 2, "n½": 2, "gC": 2, "s": 2}
rows = "".join(f'<tr><td class="tl">{r["lab"]}</td><td>{r["n"]}</td>' + "".join(f'<td>{r["v"][k]:.{fmt[k]}f}</td>' for k in NAMES) + f'<td class="g">{r["rmse"]:.2f}</td><td>{r["loo"]:.2f}</td></tr>' for r in res)
TH = {"light": dict(bg="#ffffff", fg="#1d1d1f", grid="#d9d9de"), "dark": dict(bg="#141414", fg="#f5f5f7", grid="#3a3a3c")}
NN = np.linspace(1.0, 3.1, 120)
for t, th in TH.items():
    Fg, ax = plt.subplots(figsize=(7.5, 4.6)); Fg.patch.set_facecolor(th["bg"]); ax.set_facecolor(th["bg"])
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.tick_params(colors=th["fg"], length=0); ax.grid(color=th["grid"], lw=.6)
    for r in res: ax.plot(NN * 1000, 19.3 + model(r["x"], NN, 1600 / 1500, 575), lw=2, label=r["lab"].replace("&times;", "×"))
    ax.set_xlabel("GPU fans, rpm", color=th["fg"]); ax.set_ylabel("Settled core at 575 W, °C (intake 19.3 °C)", color=th["fg"])
    ax.legend(frameon=False, labelcolor=th["fg"], fontsize=9); Fg.tight_layout(); Fg.savefig(OUT / f"cmp3-{t}.png", dpi=200, facecolor=th["bg"]); plt.close(Fg)
    Image.open(OUT / f"cmp3-{t}.png").convert("RGB").save(IMG / f"gpu-map-cmp3-{t}.webp", "WEBP", quality=86)
pic = "".join(f'<a class="ar-wide th-{t[0]}" href="/research/img/gpu-map-cmp3-{t}.webp?v=1"><img src="/research/img/gpu-map-cmp3-{t}.webp?v=1" width="1500" height="920" loading="lazy" decoding="async" alt="Settled core against GPU fan speed at 575 W and case fans 1600 rpm for each fitted setup"></a>' for t in TH)
SEC = f"""<!--compare3:start-->
  <h3 id="three-setups">Three setups, one equation</h3>
  <p>The same equation, two conductances in parallel with a saturating GPU-fan path, was fitted to each setup and card on its own grid ({{tref:cmp3}}, {{fref:fig-the-three-setups-at-equal-power}}).</p>
  <p class="ar-tcap"><b>The same model fitted to each setup and card: constants, fit error and leave-one-out error.</b> Core temperature, nonlinear least squares, settled grid points of each setup.</p>
  <div class="ar-tw ar-tw-wide"><table class="ar-tab ar-num ar-st ar-cmp3"><thead><tr><th scope="col" class="tl">Setup and card</th><th scope="col">Points</th><th scope="col">&theta;<sub>0</sub>, &deg;C</th><th scope="col">r<sub>&infin;</sub>, m&deg;C/W</th><th scope="col">g<sub>N</sub>, W/&deg;C</th><th scope="col">m</th><th scope="col">n<sub>&frac12;</sub>, 1000&nbsp;rpm</th><th scope="col">g<sub>C</sub>, W/&deg;C</th><th scope="col">s</th><th scope="col" class="g">RMSE, &deg;C</th><th scope="col">LOO, &deg;C</th></tr></thead><tbody>{rows}</tbody></table></div>
  <figure class="ar-fig ar-fig-wide">{pic}<figcaption><b>Figure 0.</b> The three setups at equal power: settled core of each fitted setup and card against GPU fan speed, at 575&nbsp;W per card, case and radiator fans 1600&nbsp;rpm and intake air 19.3&nbsp;&deg;C.</figcaption></figure>
  <p>[Discussion to be written with the data: the open-air three-fan ZOTAC against the flow-through Founders Edition at equal power, and the effect of the second card, card A drawing in card B&rsquo;s exhaust.]</p>
<!--compare3:end-->"""
if a_ >= 0: s = s[:a_] + SEC + s[b_ + len("<!--compare3:end-->"):]
else: i = s.index('<h3 id="lit-compare"'); s = s[:i] + SEC + "\n  " + s[i:]
F.write_text(s); print("compare3 written:", [(r["lab"], r["n"], round(r["rmse"], 2)) for r in res])
