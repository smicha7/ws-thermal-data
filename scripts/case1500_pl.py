# Rdzeń (ciągła) i pamięć (przerywana) vs wentylatory karty przy obudowie 1500 rpm, kilka power limitów na jednym wykresie (final.csv)
import csv, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

src, out, pls = sys.argv[1], sys.argv[2], sys.argv[3:] or ["100", "90"]
ALL = list(csv.DictReader(open(src)))
SHADE = [("#0b3d91", "#b85c00", 2.8), ("#5b9be6", "#f2a54a", 2.0), ("#9cc3f2", "#f7cd94", 1.6), ("#c9def7", "#fbe2c2", 1.4)]
fig, ax = plt.subplots(figsize=(11, 6.5))
for pl, (cc, cm, lw) in zip(pls, SHADE):
    rs = sorted((r for r in ALL if r["case_rpm_target"] == "1500" and r["pl_pct"] == pl), key=lambda r: int(r["gpu_pct"]))
    x = [int(r["gpu_pct"]) for r in rs]
    core = [float(r["cardA_core_c"]) for r in rs]; mem = [float(r["cardA_mem_c"]) for r in rs]
    w = round(575 * int(pl) / 100)
    ax.plot(x, core, "o-", c=cc, lw=lw, label=f"rdzeń · PL {pl} % ({w} W)")
    ax.plot(x, mem, "s--", c=cm, lw=lw, label=f"pamięć · PL {pl} % ({w} W)")
    for xi, c, m in zip(x, core, mem):
        ax.annotate(f"{c:.0f}", (xi, c), textcoords="offset points", xytext=(0, -14 if pl == pls[-1] else 7), ha="center", fontsize=8, c=cc)
        ax.annotate(f"{m:.0f}", (xi, m), textcoords="offset points", xytext=(0, 7 if pl == pls[0] else -14), ha="center", fontsize=8, c=cm)
    ax.text(101, core[-1], f"PL {pl} %", va="center", fontsize=8, c=cc)
ax.axhline(90, c="#1f6fd1", lw=.8, ls=":"); ax.text(99, 90.4, "rdzeń 90 °C", ha="right", fontsize=8, c="#1f6fd1")
ax.axhline(100, c="#e07b00", lw=.8, ls=":"); ax.text(99, 100.4, "pamięć 100 °C", ha="right", fontsize=8, c="#e07b00")
ax.set_xlabel("wentylatory karta, %"); ax.set_ylabel("°C"); ax.set_xticks(range(40, 101, 10)); ax.set_xlim(37, 106); ax.set_ylim(50, 103); ax.grid(alpha=.3)
ax.legend(loc="upper right", fontsize=8, ncol=2, bbox_to_anchor=(1, .93))
top = ax.secondary_xaxis("top", functions=(lambda p: 180 + 28.33 * p, lambda r: (r - 180) / 28.33)); top.set_xlabel("wentylatory karta, rpm")
ax.set_title("Obudowa 1500 rpm · 1× RTX 5090 FE · powietrze ~19 °C · ciemne = wyższy power limit", pad=34)
fig.text(.01, .01, "PL 100: 40 % powtórka ustalona, 60–100 % ustalone z nocy (obudowa ~1290 rpm), 50 % = 60 s (nieustalone, ~2 °C za nisko). PL 90 i niższe: punkty 60 s.", fontsize=8, c="#555")
fig.tight_layout(rect=(0, .03, 1, 1)); fig.savefig(out, dpi=150)
