# Rdzeń i pamięć vs wentylatory karty 40–100 % przy obudowie 1500 rpm i PL 100 % (575 W), z final.csv
import csv, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

src, out = sys.argv[1], sys.argv[2]
rs = sorted((r for r in csv.DictReader(open(src)) if r["case_rpm_target"] == "1500" and r["pl_pct"] == "100"), key=lambda r: int(r["gpu_pct"]))
x = [int(r["gpu_pct"]) for r in rs]
core = [float(r["cardA_core_c"]) for r in rs]; mem = [float(r["cardA_mem_c"]) for r in rs]
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(x, core, "o-", c="#1f6fd1", lw=2.5, label="rdzeń")
ax.plot(x, mem, "s--", c="#e07b00", lw=2.5, label="pamięć (junction)")
for xi, c, m, r in zip(x, core, mem, rs):
    ax.annotate(f"{c:.1f}", (xi, c), textcoords="offset points", xytext=(0, -15), ha="center", fontsize=9, c="#1f6fd1")
    ax.annotate(f"{m:.0f}", (xi, m), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=9, c="#e07b00")
    if "UNSETTLED" in r.get("source", ""):
        ax.scatter([xi, xi], [c, m], s=160, facecolors="none", edgecolors="k", lw=1)
ax.axhline(90, c="#1f6fd1", lw=.8, ls=":"); ax.text(99, 90.4, "rdzeń 90 °C", ha="right", fontsize=8, c="#1f6fd1")
ax.axhline(100, c="#e07b00", lw=.8, ls=":"); ax.text(99, 100.4, "pamięć 100 °C", ha="right", fontsize=8, c="#e07b00")
ax.set_xlabel("wentylatory karta, %"); ax.set_ylabel("°C"); ax.set_xticks(range(40, 101, 10)); ax.set_ylim(50, 103); ax.grid(alpha=.3); ax.legend(loc="center right")
top = ax.secondary_xaxis("top", functions=(lambda p: 180 + 28.33 * p, lambda r: (r - 180) / 28.33)); top.set_xlabel("wentylatory karta, rpm")
ax.set_title("Obudowa 1500 rpm · power limit 100 % (575 W) · 1× RTX 5090 FE · powietrze ~19 °C", pad=34)
fig.text(.01, .01, "40 %: powtórka do ustalenia (grid1d). 60–100 %: ustalone wartości z nocy (obudowa ~1290 rpm). Kółko = 50 % nieustalone (60 s, rzeczywiście ~2 °C wyżej).", fontsize=8, c="#555")
fig.tight_layout(rect=(0, .03, 1, 1)); fig.savefig(out, dpi=150)
