# Model rdzenia przy obudowie 1500 rpm (final.csv, 4 PL × 7 poziomów karty, bez nieustalonego PL100/50 %):
#   T = Tin + θ0 + P·(r∞ + k·(N/1000)^(−m))      N = rpm wentylatorów karty, P = moc karty [W]
# czyli opór cieplny R(N) = r∞ + k·N^−m maleje z obrotami; θ0 = stały offset (ciepło niezależne od limitu).
# Dla porównania model log-liniowy T = b0 + b1·P + b2·ln N + b3·P·ln N.
import csv, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

src, out = sys.argv[1], sys.argv[2]
rs = [r for r in csv.DictReader(open(src)) if r["case_rpm_target"] == "1500" and "UNSETTLED" not in r.get("source", "")]
N = np.array([float(r["cardA_fan_rpm"]) for r in rs]); P = np.array([float(r["power_w_sum"]) for r in rs])
T = np.array([float(r["cardA_core_c"]) for r in rs]); Tin = np.array([float(r["intake_c"] or 19.1) for r in rs])
PL = np.array([r["pl_pct"] for r in rs]); n = len(T); y = T - Tin

def design(n_, p_, m_): return np.column_stack([np.ones_like(p_), p_, p_ * (n_ / 1000) ** (-m_)])
best = None
for m_ in np.arange(0.1, 4.01, 0.01):   # ponytail: siatka po m + liniowe MNK, bez scipy
    c, *_ = np.linalg.lstsq(design(N, P, m_), y, rcond=None)
    e = np.sum((y - design(N, P, m_) @ c) ** 2)
    if best is None or e < best[0]: best = (e, c, m_)
_, (th0, rinf, k), m = best
pred = lambda n_, p_, tin=19.1: tin + design(np.atleast_1d(n_), np.atleast_1d(p_), m) @ np.array([th0, rinf, k])
res = T - pred(N, P, Tin); rmse = np.sqrt(np.mean(res ** 2)); r2 = 1 - np.sum(res ** 2) / np.sum((T - T.mean()) ** 2)
X = np.column_stack([np.ones(n), P, np.log(N), P * np.log(N)]); b, *_ = np.linalg.lstsq(X, T, rcond=None)
rl = T - X @ b; rmse_l = np.sqrt(np.mean(rl ** 2)); r2_l = 1 - np.sum(rl ** 2) / np.sum((T - T.mean()) ** 2)
R = lambda n_: rinf + k * (n_ / 1000) ** (-m)
print(f"n={n}  θ0={th0:.2f} K  r∞={rinf*1000:.2f} mK/W  k={k*1000:.2f} mK/W  m={m:.2f}  RMSE={rmse:.2f} K  R²={r2:.4f}  maxres={np.abs(res).max():.2f}")
print(f"log-lin: b0={b[0]:.2f} b1={b[1]:.4f} b2={b[2]:.3f} b3={b[3]:.5f}  RMSE={rmse_l:.2f} K  R²={r2_l:.4f}")
for rpm in (1312, 1595, 1879, 2162, 2446, 2729, 3012):
    print(f"N={rpm}: R={R(rpm)*1000:.1f} mK/W → {R(rpm)*100:.2f} K na 100 W")
for r, e in sorted(zip(rs, res), key=lambda t: -abs(t[1]))[:4]: print("res", r["pl_pct"], r["gpu_pct"], f"{e:+.2f}")

fig, ax = plt.subplots(figsize=(11, 6.8))
cols = {"100": ("#08306b", 575), "90": ("#2171b5", 517.5), "80": ("#6baed6", 460), "70": ("#9ecae1", 402.5)}
nn = np.linspace(1250, 3050, 200)
for pl, (c, pw) in cols.items():
    kk = PL == pl
    ax.scatter(N[kk], T[kk], c=c, s=45, zorder=3, edgecolors="white")
    ax.plot(nn, pred(nn, np.full_like(nn, pw)), c=c, lw=2, label=f"PL {pl} % ({pw:.0f} W)")
ax.set_xlabel("wentylatory karta N, rpm"); ax.set_ylabel("rdzeń T, °C"); ax.grid(alpha=.3); ax.legend(loc="upper right", bbox_to_anchor=(1, .62))
top = ax.secondary_xaxis("top", functions=(lambda r: (r - 180) / 28.33, lambda p: 180 + 28.33 * p)); top.set_xlabel("wentylatory karta, %")
eq = (r"$T = T_{in} + \theta_0 + P\,\left[r_\infty + k\,(N/1000)^{-m}\right]$" + "\n\n" +
      rf"$\theta_0 = {th0:.1f}$ K,   $r_\infty = {rinf*1000:.1f}$ mK/W,   $k = {k*1000:.1f}$ mK/W,   $m = {m:.2f}$" + "\n" +
      rf"RMSE = {rmse:.2f} K,   $R^2$ = {r2:.3f},   n = {n},   $T_{{in}}$ ≈ 19 °C" + "\n" +
      rf"ΔT na 100 W: {R(1312)*100:.1f} K przy 40 %  →  {R(3012)*100:.1f} K przy 100 %")
ax.text(.30, .97, eq, transform=ax.transAxes, va="top", fontsize=10.5, bbox=dict(fc="white", ec="#bbb"))
ax.set_title("Rdzeń RTX 5090 FE · obudowa 1500 rpm · punkty = pomiar, linie = jeden model dla 4 power limitów", pad=34)
fig.tight_layout(); fig.savefig(out, dpi=150)
