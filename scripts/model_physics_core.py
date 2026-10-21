# Rozszerzenia fizyczne modelu rdzenia (run2, final.csv bez nieustalonych). Porównanie: dopasowanie i LOO.
#  A   bazowy:     θ0 + P·[r∞ + k·N^−m·C^−q]
#  A1  + kaloryczny/recyrkulacja: + P·c/C   (podgrzanie powietrza w obudowie ∝ P/ṁ_obudowy)
#  A2  + kaloryczny karty:        + P·d/N   (podgrzanie powietrza w żebrach ∝ P/ṁ_karty)
#  A3  A na danych poprawionych do stanu ustalonego: T∞ ≈ T + slope·τ (pierwszy rząd, τ z logu)
import csv, sys, itertools
import numpy as np
src = sys.argv[1]; TAU = float(sys.argv[2]) if len(sys.argv) > 2 else 70.0
rs = [r for r in csv.DictReader(open(src)) if "UNSETTLED" not in r.get("source", "")]
f = lambda k: np.array([float(r[k] or 0) for r in rs])
N, P, T, C = f("cardA_fan_rpm") / 1000, f("power_w_sum") / 100, f("cardA_core_c"), f("case_rpm") / 1000
Tin = np.array([float(r["intake_c"] or 19.1) for r in rs]); n = len(T)
slope = f("slope_core_c_min")
is60 = np.array(["60 s" in r["source"] and "night" not in r["source"] for r in rs])
Tcorr = T + np.where(is60, slope * TAU / 60, 0)   # ponytail: korekta pierwszego rzędu, tylko dla punktów 60 s

def fit(y, extra):
    best = None
    for m, q in itertools.product(np.arange(.6, 3.01, .04), np.arange(0, 1.21, .04)):
        cols = [np.ones(n), P, P * N**-m * C**-q] + [e for e in extra]
        X = np.column_stack(cols); Xp = np.linalg.pinv(X); b = Xp @ y; e = y - X @ b
        s = np.sum(e**2)
        if best is None or s < best[0]:
            H = np.diag(X @ Xp); best = (s, b, m, q, np.sqrt(np.mean(e**2)), np.sqrt(np.mean((e / (1 - H))**2)), e)
    return best
for name, y, extra in (("A  bazowy", T - Tin, []), ("A1 + P/C (recyrkulacja)", T - Tin, [P / C]), ("A2 + P/N (kaloryczny karty)", T - Tin, [P / N]),
                       ("A3 bazowy na T∞ (τ=%.0f s)" % TAU, Tcorr - Tin, []), ("A4 A1 na T∞", Tcorr - Tin, [P / C])):
    s, b, m, q, rmse, loo, e = fit(y, extra)
    e_set = e[~is60]
    print(f"{name:30s} RMSE={rmse:.2f} LOO={loo:.2f} max={np.abs(e).max():.2f} | ustalone: RMSE={np.sqrt(np.mean(e_set**2)):.2f} (n={len(e_set)})  m={m:.2f} q={q:.2f} b={np.round(b,3).tolist()}")
