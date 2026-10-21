# Rdzeń i pamięć vs wentylatory karty 40–100 % przy obudowie 1500 rpm, linia na każdy power limit (final.csv)
import csv, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

src, out = sys.argv[1], sys.argv[2]
rows = [r for r in csv.DictReader(open(src)) if r["case_rpm_target"] == "1500"]
PL = {"100": ("575 W (100 %)", "#b0352a"), "90": ("518 W (90 %)", "#e07b00"), "80": ("460 W (80 %)", "#2a8a4a"), "70": ("402 W (70 %)", "#1f6fd1")}
fig, (a, b) = plt.subplots(1, 2, figsize=(13, 6), sharey=True)
for pl, (lab, c) in PL.items():
    rs = sorted((r for r in rows if r["pl_pct"] == pl), key=lambda r: int(r["gpu_pct"]))
    x = [int(r["gpu_pct"]) for r in rs]
    for ax, k in ((a, "cardA_core_c"), (b, "cardA_mem_c")):
        y = [float(r[k]) for r in rs]
        ax.plot(x, y, "o-", c=c, lw=2.4 if pl == "100" else 1.6, label=lab)
        for xi, yi, r in zip(x, y, rs):
            if pl in ("100", "70"): ax.annotate(f"{yi:.0f}", (xi, yi), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=8, c=c)
            if "UNSETTLED" in r.get("source", ""): ax.scatter([xi], [yi], s=140, facecolors="none", edgecolors="k", lw=1)
for ax, t, lim in ((a, "Rdzeń", 90), (b, "Pamięć (junction)", 100)):
    ax.set_title(t); ax.grid(alpha=.3); ax.set_xlabel("wentylatory karta, %"); ax.set_xticks(range(40, 101, 10))
    ax.axhline(lim, c="#888", lw=.8, ls=":"); ax.text(99, lim + .4, f"limit {lim} °C", ha="right", fontsize=8, c="#666")
    top = ax.secondary_xaxis("top", functions=(lambda p: 180 + 28.33 * p, lambda r: (r - 180) / 28.33)); top.set_xlabel("wentylatory karta, rpm")
a.set_ylabel("°C"); a.set_ylim(45, 102); a.legend(title="power limit", fontsize=9)
fig.suptitle("Obudowa 1500 rpm · 1× RTX 5090 FE · powietrze ~19 °C · 21.10.2026")
fig.text(.01, .01, "PL 100: od 60 % ustalone wartości z nocy (obudowa ~1290 rpm), 40 % powtórka do ustalenia; kółko = 50 % nieustalone (60 s). PL 90–80–70: punkty 60 s.", fontsize=8, c="#555")
fig.tight_layout(rect=(0, .03, 1, 1)); fig.savefig(out, dpi=150)
