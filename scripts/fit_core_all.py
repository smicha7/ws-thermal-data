# Model rdzenia dla całej siatki (obudowa C × karta N × moc P), final.csv bez punktów nieustalonych:
#   T = Tin + θ0 + P·[ r∞ + k·(N/1000)^(−m)·(C/1500)^(−q) ]
# obudowa skaluje człon zależny od wentylatorów karty: przy wolnej karcie działa mocno, przy szybkiej prawie wcale.
import csv, sys, json
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

src, outdir = sys.argv[1], sys.argv[2]
rs = [r for r in csv.DictReader(open(src)) if "UNSETTLED" not in r.get("source", "")]
f = lambda k: np.array([float(r[k]) for r in rs])
N, P, T, C = f("cardA_fan_rpm"), f("power_w_sum"), f("cardA_core_c"), f("case_rpm")
Tin = np.array([float(r["intake_c"] or 19.1) for r in rs]); y = T - Tin; n = len(T)
CT = np.array([int(r["case_rpm_target"]) for r in rs]); G = np.array([int(r["gpu_pct"]) for r in rs]); PL = np.array([r["pl_pct"] for r in rs])

def design(n_, c_, p_, m_, q_): return np.column_stack([np.ones_like(p_), p_, p_ * (n_ / 1000) ** (-m_) * (c_ / 1500) ** (-q_)])
best = None
for m_ in np.arange(0.5, 3.01, 0.02):          # ponytail: siatka po (m, q) + liniowe MNK
    for q_ in np.arange(0.0, 1.51, 0.02):
        X = design(N, C, P, m_, q_); c, *_ = np.linalg.lstsq(X, y, rcond=None)
        e = np.sum((y - X @ c) ** 2)
        if best is None or e < best[0]: best = (e, c, m_, q_)
_, (th0, rinf, k), m, q = best
pred = lambda n_, c_, p_, tin=19.1: tin + design(np.atleast_1d(n_).astype(float), np.atleast_1d(c_).astype(float), np.atleast_1d(p_).astype(float), m, q) @ np.array([th0, rinf, k])
res = T - pred(N, C, P, Tin); rmse = np.sqrt(np.mean(res ** 2)); r2 = 1 - np.sum(res ** 2) / np.sum((T - T.mean()) ** 2)
print(f"n={n} θ0={th0:.2f} K r∞={rinf*1000:.2f} mK/W k={k*1000:.2f} mK/W m={m:.2f} q={q:.2f} RMSE={rmse:.2f} R²={r2:.4f} max={np.abs(res).max():.2f}")
for r, e in sorted(zip(rs, res), key=lambda t: -abs(t[1]))[:5]: print("res", r["case_rpm_target"], r["pl_pct"], r["gpu_pct"], f"{e:+.2f}", r["source"][:30])
json.dump(dict(th0=th0, rinf=rinf, k=k, m=m, q=q, rmse=rmse, r2=r2, n=n), open(f"{outdir}/core-model-all.json", "w"), indent=1)

# wykres: karta 40 %, rdzeń vs obroty obudowy, linia na każdy PL
fig, ax = plt.subplots(figsize=(11, 6.8))
cols = {"100": ("#08306b", 575), "90": ("#2171b5", 517.5), "80": ("#6baed6", 460), "70": ("#9ecae1", 402.5)}
cc = np.linspace(950, 3000, 200); n40 = 180 + 28.33 * 40
for pl, (c, pw) in cols.items():
    kk = (G == 40) & (PL == pl)
    ax.scatter(C[kk], T[kk], c=c, s=50, zorder=3, edgecolors="white")
    ax.plot(cc, pred(np.full_like(cc, n40), cc, np.full_like(cc, pw)), c=c, lw=2, label=f"PL {pl} % ({pw:.0f} W)")
    for x_, y_ in zip(C[kk], T[kk]): ax.annotate(f"{y_:.1f}", (x_, y_), textcoords="offset points", xytext=(8, 4), fontsize=8, c=c)
ax.set_xlabel("wentylatory obudowa C, rpm"); ax.set_ylabel("rdzeń T, °C"); ax.grid(alpha=.3); ax.legend(loc="lower left")
top = ax.secondary_xaxis("top", functions=(lambda r: np.interp(r, [654, 1286, 1889, 2418, 2921], [15, 36, 58, 79, 100]), lambda p: np.interp(p, [15, 36, 58, 79, 100], [654, 1286, 1889, 2418, 2921])))
top.set_xlabel("wentylatory obudowa, %")
eq = (r"$T = T_{in} + \theta_0 + P\,\left[r_\infty + k\,(N/1000)^{-m}\,(C/1500)^{-q}\right]$" + "\n\n" +
      rf"$\theta_0 = {th0:.1f}$ K,  $r_\infty = {rinf*1000:.1f}$ mK/W,  $k = {k*1000:.1f}$ mK/W,  $m = {m:.2f}$,  $q = {q:.2f}$" + "\n" +
      rf"cała siatka: RMSE = {rmse:.2f} K,  $R^2$ = {r2:.3f},  n = {n}")
ax.text(.30, .97, eq, transform=ax.transAxes, va="top", fontsize=10, bbox=dict(fc="white", ec="#bbb"))
ax.set_title("Rdzeń przy wentylatorach karty 40 % (~1310 rpm) · zmienne obroty obudowy · RTX 5090 FE · powietrze ~19 °C", pad=34)
fig.tight_layout(); fig.savefig(f"{outdir}/core-card40-vs-case.png", dpi=150)
