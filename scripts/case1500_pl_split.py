# Dwa panele: rdzeń i pamięć vs wentylatory karty przy obudowie 1500 rpm, linia na każdy power limit (final.csv)
import csv, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

src, out, pls = sys.argv[1], sys.argv[2], sys.argv[3:] or ["100", "90"]
ALL = list(csv.DictReader(open(src)))
SHADE = {"core": ["#08306b", "#2171b5", "#6baed6", "#9ecae1"], "mem": ["#7f2704", "#d94801", "#fd8d3c", "#fdae6b"]}
LW = [2.8, 2.3, 2.0, 1.8]
fig, axes = plt.subplots(1, 2, figsize=(14, 6.5), sharey=True)
for ax, key, col, title, lim, ls in ((axes[0], "cardA_core_c", "core", "Rdzeń", 90, "o-"), (axes[1], "cardA_mem_c", "mem", "Pamięć (junction)", 100, "s--")):
    for i, pl in enumerate(pls):
        rs = sorted((r for r in ALL if r["case_rpm_target"] == "1500" and r["pl_pct"] == pl), key=lambda r: int(r["gpu_pct"]))
        x = [int(r["gpu_pct"]) for r in rs]; y = [float(r[key]) for r in rs]
        c = SHADE[col][i]; w = round(575 * int(pl) / 100)
        ax.plot(x, y, ls, c=c, lw=LW[i], label=f"PL {pl} % ({w} W)")
        for xi, yi in zip(x, y) if i in (0, len(pls) - 1) else ():
            ax.annotate(f"{yi:.0f}", (xi, yi), textcoords="offset points", xytext=(0, 7 if i == 0 else -14), ha="center", fontsize=8, c=c)
    ax.axhline(lim, c=SHADE[col][0], lw=.8, ls=":"); ax.text(99, lim + .4, f"limit {lim} °C", ha="right", fontsize=8, c=SHADE[col][0])
    ax.set_title(title); ax.set_xlabel("wentylatory karta, %"); ax.set_xticks(range(40, 101, 10)); ax.grid(alpha=.3); ax.legend(loc="upper right", fontsize=9, bbox_to_anchor=(1, .93))
    top = ax.secondary_xaxis("top", functions=(lambda p: 180 + 28.33 * p, lambda r: (r - 180) / 28.33)); top.set_xlabel("wentylatory karta, rpm")
axes[0].set_ylabel("°C"); axes[0].set_ylim(45, 103)
fig.suptitle("Obudowa 1500 rpm · 1× RTX 5090 FE · powietrze ~19 °C · ciemne = wyższy power limit")
fig.text(.01, .01, "PL 100: 40 % powtórka ustalona, 60–100 % ustalone z nocy (obudowa ~1290 rpm), 50 % = 60 s (~2 °C za nisko). PL 90 i niższe: punkty 60 s (pamięć mierzona tuż po PL 100, raczej 1–2 °C za wysoko).", fontsize=8, c="#555")
fig.tight_layout(rect=(0, .03, 1, 1)); fig.savefig(out, dpi=150)
