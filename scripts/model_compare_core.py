# Porównanie modeli rdzenia na całej siatce run2 (final.csv bez nieustalonych): N karta rpm, C obudowa rpm, P moc W, Tin powietrze.
# Kryterium: RMSE w leave-one-out (LOO) — uczciwa prognoza, nie tylko dopasowanie. Wykresy reszt najlepszego modelu.
import csv, sys, itertools, json
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

src, outdir = sys.argv[1], sys.argv[2]
rs = [r for r in csv.DictReader(open(src)) if "UNSETTLED" not in r.get("source", "")]
f = lambda k: np.array([float(r[k]) for r in rs])
N, P, T, C = f("cardA_fan_rpm") / 1000, f("power_w_sum") / 100, f("cardA_core_c"), f("case_rpm") / 1000
Tin = np.array([float(r["intake_c"] or 19.1) for r in rs]); y = T - Tin; n = len(T)
src_tag = np.array(["60 s" if "60 s" in r["source"] and "night" not in r["source"] else "ustalony" for r in rs])

# każdy model: (nazwa, siatka parametrów nieliniowych, funkcja budująca macierz liniową)
M = {
 "A  P·[r∞ + k·N^−m·C^−q] + θ0": (dict(m=np.arange(.6, 3.01, .04), q=np.arange(0, 1.21, .04)),
     lambda m, q: np.column_stack([np.ones(n), P, P * N**-m * C**-q])),
 "B  P/(g0 + a·N^m + b·C^q) + θ0": (dict(m=np.arange(.4, 2.41, .05), q=np.arange(.2, 2.01, .1), g=[0]),
     None),
 "C  P·[r∞ + k·N^−m·C^−q] + θ0 + s·C": (dict(m=np.arange(.6, 3.01, .04), q=np.arange(0, 1.21, .04)),
     lambda m, q: np.column_stack([np.ones(n), P, P * N**-m * C**-q, C])),
 "D  log-lin: lnN, lnC, P i interakcje": ({}, lambda: np.column_stack([np.ones(n), P, np.log(N), np.log(C), P*np.log(N), P*np.log(C), np.log(N)*np.log(C)])),
 "E  wielomian 2. stopnia (N, C, P)": ({}, lambda: np.column_stack([np.ones(n), N, C, P, N*N, C*C, P*P, N*C, N*P, C*P])),
}

def loo(X):
    # LOO dla liniowego MNK przez macierz kapelusza
    H = X @ np.linalg.pinv(X); b = np.linalg.pinv(X) @ y; e = y - X @ b
    return np.sqrt(np.mean((e / (1 - np.diag(H))) ** 2)), np.sqrt(np.mean(e ** 2)), b, e

def fitB(m, q):
    # T−Tin = θ0 + P/G, G = g0 + a N^m + b C^q — nieliniowe w θ0; siatka po θ0 i liniowe MNK na G
    best = None
    for th in np.arange(0, 20.1, .5):
        z = y - th
        if np.any(z <= 0.5): continue
        X = np.column_stack([np.ones(n), N**m, C**q]); g = np.linalg.lstsq(X, P / z, rcond=None)[0]
        G = X @ g
        if np.any(G <= 0): continue
        e = y - th - P / G; s = np.sum(e**2)
        if best is None or s < best[0]: best = (s, th, g, e)
    return best

results = {}
for name, (grid, build) in M.items():
    if name.startswith("B"):
        best = None
        for m, q in itertools.product(grid["m"], grid["q"]):
            r_ = fitB(m, q)
            if r_ and (best is None or r_[0] < best[0][0]): best = (r_, m, q)
        (s, th, g, e), m, q = best
        results[name] = dict(rmse=float(np.sqrt(s / n)), loo=None, k=6, par=dict(th0=th, g0=g[0], a=g[1], b=g[2], m=m, q=q), e=e)
        continue
    if not grid:
        X = build(); l, r_, b, e = loo(X); results[name] = dict(rmse=r_, loo=l, k=X.shape[1], par=dict(b=b.round(4).tolist()), e=e); continue
    best = None
    for m, q in itertools.product(grid["m"], grid["q"]):
        X = build(m, q); l, r_, b, e = loo(X)
        if best is None or r_ < best[1]: best = (l, r_, b, e, m, q, X.shape[1])
    l, r_, b, e, m, q, kk = best
    results[name] = dict(rmse=r_, loo=l, k=kk + 2, par=dict(b=b.round(5).tolist(), m=round(m, 2), q=round(q, 2)), e=e)

print(f"n = {n}")
for name, r_ in sorted(results.items(), key=lambda t: t[1]["rmse"]):
    loo_s = f"{r_['loo']:.2f}" if r_["loo"] else "  — "
    print(f"{name:42s} param={r_['k']:2d}  RMSE={r_['rmse']:.2f}  LOO≈{loo_s}  max={np.abs(r_['e']).max():.2f}   {r_['par']}")

best = "A  P·[r∞ + k·N^−m·C^−q] + θ0"
e = results[best]["e"]; pred = T - e
fig, ax = plt.subplots(2, 2, figsize=(13, 9))
for a_, x, lab in ((ax[0, 0], N * 1000, "wentylatory karta, rpm"), (ax[0, 1], C * 1000, "wentylatory obudowa, rpm"), (ax[1, 0], P * 100, "moc karty, W")):
    for tag, mk in (("ustalony", "o"), ("60 s", "x")):
        k_ = src_tag == tag; a_.scatter(x[k_], e[k_], marker=mk, s=30, label=tag)
    a_.axhline(0, c="k", lw=.8); a_.axhspan(-1, 1, color="#ddd", alpha=.5); a_.set_xlabel(lab); a_.set_ylabel("reszta (pomiar − model), K"); a_.grid(alpha=.3)
ax[0, 0].legend(title="punkt")
a_ = ax[1, 1]; a_.scatter(pred, T, s=25, c=e, cmap="coolwarm", vmin=-2.5, vmax=2.5); lim = [45, 87]
a_.plot(lim, lim, c="k", lw=.8); a_.set_xlim(lim); a_.set_ylim(lim); a_.set_xlabel("model, °C"); a_.set_ylabel("pomiar, °C"); a_.grid(alpha=.3)
a_.set_title(f"model A: RMSE {results[best]['rmse']:.2f} K, LOO {results[best]['loo']:.2f} K, n = {n}")
fig.suptitle("Reszty modelu rdzenia  T = Tin + θ0 + P·[r∞ + k·N^−m·C^−q]  (szary pas = ±1 K)")
fig.tight_layout(); fig.savefig(f"{outdir}/core-model-residuals.png", dpi=140)
