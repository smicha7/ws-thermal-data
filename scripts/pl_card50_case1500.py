# Rdzeń, pamięć, hot spot i zegar vs limit mocy przy karcie 50 % i obudowie 1500 rpm (grid1c + ręczne odczyty Seba)
import csv, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

src, out = sys.argv[1], sys.argv[2]
rows = [r for r in csv.DictReader(open(src)) if r["gpu_pct"] == "50" and r["case_rpm_target"] == "1500"]
rows.sort(key=lambda r: float(r["power_w_sum"]))
W = [float(r["power_w_sum"]) for r in rows]
f = lambda k: [float(r[k]) for r in rows]
core, mem, hot, clk = f("cardA_core_c"), f("cardA_mem_c"), f("cardA_hot_c"), f("cardA_clock_mhz")
# ręczne odczyty Seba (ekran, ~2 min po zmianie): W, rdzeń, pamięć
manual = [(575, 73, 80), (518, 70, 78), (460, 65, 76), (402, 60, 72)]

fig, (a, b) = plt.subplots(2, 1, figsize=(9, 8), sharex=True, gridspec_kw={"height_ratios": [3, 1.4]})
a.plot(W, core, "o-", c="#1f6fd1", lw=2, label="rdzeń (60 s)")
a.plot(W, mem, "s--", c="#e07b00", lw=2, label="pamięć (60 s)")
a.plot(W, hot, "^:", c="#b0352a", lw=1.5, label="hot spot (60 s)")
for x, y, k in zip(W, core, core): a.annotate(f"{y:.1f}", (x, y), textcoords="offset points", xytext=(0, -14), ha="center", fontsize=8, c="#1f6fd1")
for x, y in zip(W, mem): a.annotate(f"{y:.0f}", (x, y), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=8, c="#e07b00")
a.scatter([m[0] for m in manual], [m[1] for m in manual], facecolors="none", edgecolors="#1f6fd1", s=70, label="rdzeń, odczyt ręczny")
a.scatter([m[0] for m in manual], [m[2] for m in manual], marker="s", facecolors="none", edgecolors="#e07b00", s=70, label="pamięć, odczyt ręczny")
a.axhline(90, c="#1f6fd1", lw=.8, alpha=.5); a.text(574, 90.4, "rdzeń 90 °C", ha="right", fontsize=8, c="#1f6fd1")
a.set_ylabel("°C"); a.set_ylim(55, 95); a.grid(alpha=.3); a.legend(fontsize=8, loc="upper left", ncol=2)
a.set_title("Karta 50 % (~1595 rpm) · obudowa 1500 rpm · 1× RTX 5090 · powietrze ~19 °C")
top = a.secondary_xaxis("top", functions=(lambda w: w / 5.75, lambda p: p * 5.75)); top.set_xlabel("power limit, %")
b.plot(W, clk, "o-", c="#444", lw=2)
for x, y in zip(W, clk): b.annotate(f"{y:.0f}", (x, y), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=8)
b.set_ylabel("zegar rdzenia, MHz"); b.set_xlabel("moc karty, W"); b.grid(alpha=.3); b.set_ylim(1900, 2800)
fig.text(.01, .005, "Punkty 60 s: PL 100 jeszcze rósł (+2,8 °C/min), PL 90–70 jeszcze spadały (−1,3…−3,3 °C/min). Ręczne = odczyt Seba z ekranu.", fontsize=7.5, c="#555")
fig.tight_layout(rect=(0, .02, 1, 1)); fig.savefig(out, dpi=150)
