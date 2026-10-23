"""Settled memory model (first fit, provisional): same two-path form as the core model (11), with session offsets.
mem − Tin = θ0m + θ_session + P·[r∞ + 1/(gN·(N/1000)^m + gC·(C/1500)^s)]
Points: the settled points of steady-points.csv whose session grid has a memory reading (val1, val2, steady2; whole °C).
Writes results-2026-10-23/mem-model.json and mem-points.csv."""
import json, os, numpy as np, pandas as pd
from scipy.optimize import least_squares
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(H, "results-2026-10-22")
D = pd.read_csv(os.path.join(R, "steady-residuals.csv"))
import glob
SRC = {"val1": "val1-2026-10-21", "val2": "val2-2026-10-21", "steady2": "steady2-2026-10-22"}
for pre in ("pl90", "steady3"):
    for f in sorted(glob.glob(os.path.join(H, "data", pre + "-*", "grid.csv"))): SRC[pre] = os.path.basename(os.path.dirname(f))
rows = []
for sess, d in SRC.items():
    g = pd.read_csv(os.path.join(H, "data", d, "grid.csv"))[["ts_end", "mem_c_max"]]
    m = D[D.session == sess].merge(g, on="ts_end", how="left"); rows.append(m)
M = pd.concat(rows).dropna(subset=["mem_c_max"]).reset_index(drop=True)
grps = sorted(M.session.unique()); ref = "steady2"; others = [g for g in grps if g != ref]
def pred(v, d):
    th0, rinf, gN, m, gC, s = v[:6]; off = dict(zip(others, v[6:])); th = d.session.map(lambda g: off.get(g, 0.0)).to_numpy()
    R_ = rinf / 1000 + 1 / (gN * (d.N.to_numpy() / 1000) ** m + gC * (d.C.to_numpy() / 1500) ** s)
    return d.Tin.to_numpy() + th0 + th + d.P.to_numpy() * R_
y = M.mem_c_max.to_numpy()
fit = least_squares(lambda v: pred(v, M) - y, [12, 50, 8, 2, 6, 1] + [0] * len(others), method="lm")
e = y - pred(fit.x, M); n = len(y); k = len(fit.x)
J = fit.jac; s2 = (e ** 2).sum() / (n - k); cov = s2 * np.linalg.inv(J.T @ J)
# leave-one-out by refit
loo = []
for i in range(n):
    mm = np.ones(n, bool); mm[i] = False
    f = least_squares(lambda v: pred(v, M[mm]) - y[mm], fit.x, method="lm"); loo.append(y[i] - pred(f.x, M.iloc[[i]])[0])
names = ["θ0m", "r∞", "gN", "m", "gC", "s"] + [f"θ[{g}]" for g in others]
res = dict(n=n, sessions=M.session.value_counts().to_dict(), ref=ref, rmse=float(np.sqrt((e ** 2).mean())), loo=float(np.sqrt(np.mean(np.square(loo)))),
           mean_e=float(e.mean()), params={nm: [float(v), float(np.sqrt(cov[i, i]))] for i, (nm, v) in enumerate(zip(names, fit.x))})
os.makedirs(os.path.join(H, "results-2026-10-23"), exist_ok=True)
json.dump(res, open(os.path.join(H, "results-2026-10-23", "mem-model.json"), "w"), indent=1, ensure_ascii=False)
M.assign(mem_fitted=pred(fit.x, M), mem_e=e)[["session", "ts_end", "pl_pct", "gpu_pct", "case_target", "N", "C", "P", "Tin", "mem_c_max", "mem_fitted", "mem_e"]].to_csv(os.path.join(H, "results-2026-10-23", "mem-points.csv"), index=False)
print(json.dumps(res, indent=1, ensure_ascii=False))
