"""Primary settled-temperature model fitted on steady3 alone (final grid, 23–24 Oct 2026): 196 unique settled grid points
(first and last row = anchors 40 % / 1600 rpm / PL 100, excluded; of repeated cells the last settled one kept).
Compares functional forms by RMSE, LOO (exact refit), 10-fold CV, BIC; diagnostics for the chosen form.
Writes results-2026-10-24/steady3-fit.json (+ residuals csv, figure). Usage: steady3_fit.py [outdir_for_figs]"""
import json, os, sys, glob
import numpy as np, pandas as pd
from scipy.optimize import least_squares
from statsmodels.stats.stattools import durbin_watson
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(H, "results-2026-10-24"); os.makedirs(R, exist_ok=True)
GF = sorted(glob.glob(os.path.join(H, "data/steady3-*/grid.csv")))[-1]
g = pd.read_csv(GF); g["row"] = np.arange(len(g))
anch = g.iloc[[0, -1]]; d = g.iloc[1:-1]; d = d[d.settled == 1]
d = d.drop_duplicates(["pl_pct", "gpu_pct", "case_rpm_target"], keep="last").sort_values("row").reset_index(drop=True)
D = pd.DataFrame(dict(pl=d.pl_pct, gpu=d.gpu_pct, case=d.case_rpm_target, N=d.cardA_fan_rpm, C=d.case_rpm, P=d.power_w_sum, Tin=d.intake_c,
                      t=(d.ts_end - d.ts_end.iloc[0]) / 3600, core=d.cardA_core_nvapi_c.fillna(d.core_c_max), mem=d.mem_c_max))
n_, c_, P_ = D.N.to_numpy() / 1000, D.C.to_numpy() / 1500, D.P.to_numpy()
def G0(v, n, c): return v[2] * n ** v[3] + v[4] * c ** v[5]
FORMS = {   # T − Tin = θ0 + P·r∞/1000 + P·S(P)/G(n, c); v = [θ0, r∞, gN, m, gC, s, extra…]
    "current": (["θ0", "r∞", "gN", "m", "gC", "s"], [2, 50, 8, 2, 6, 1], lambda v, n, c, P: v[0] + P * (v[1] / 1000 + 1 / G0(v, n, c))),
    "power exponent β": (["θ0", "r∞", "gN", "m", "gC", "s", "β"], [2, 50, 8, 2, 6, 1, 1], lambda v, n, c, P: v[0] + P * v[1] / 1000 + P * (P / 500) ** (v[6] - 1) / G0(v, n, c)),
    "N×C interaction": (["θ0", "r∞", "gN", "m", "gC", "s", "gNC"], [2, 50, 8, 2, 6, 1, 0], lambda v, n, c, P: v[0] + P * (v[1] / 1000 + 1 / (G0(v, n, c) + v[6] * n * c))),
    "GPU-fan saturation (Hill)": (["θ0", "r∞", "gN", "m", "gC", "s", "n½"], [2, 50, 30, 2, 6, 1, 3], lambda v, n, c, P: v[0] + P * (v[1] / 1000 + 1 / (v[2] * n ** v[3] / (v[6] ** v[3] + n ** v[3]) + v[4] * c ** v[5]))),
    "Hill + N×C": (["θ0", "r∞", "gN", "m", "gC", "s", "n½", "gNC"], [2, 50, 30, 2, 6, 1, 3, 0], lambda v, n, c, P: v[0] + P * (v[1] / 1000 + 1 / (v[2] * n ** v[3] / (v[6] ** v[3] + n ** v[3]) + v[4] * c ** v[5] + v[7] * n * c))),
    "case exponent depends on N": (["θ0", "r∞", "gN", "m", "gC", "s", "s1"], [2, 50, 8, 2, 6, 1, 0], lambda v, n, c, P: v[0] + P * (v[1] / 1000 + 1 / (v[2] * n ** v[3] + v[4] * c ** (v[5] + v[6] * (n - 2))))),
}
def fitnl(f, x0, y, n, c, P):
    return least_squares(lambda v: f(v, n, c, P) - y, x0, method="lm", max_nfev=20000)
def spline_X(n, c, P):   # benchmark: T − Tin = a + P·Σ b_ij B_i(n) B_j(c), natural cubic splines 4 × 4 (patsy cr)
    import patsy
    B = patsy.dmatrix("te(cr(n, df=4), cr(c, df=4)) - 1", dict(n=n, c=c), return_type="matrix")
    return np.column_stack([np.ones(len(n)), P[:, None] * np.asarray(B)])
_sp_design = None
def evaluate(y, name):
    out = {}; nobs = len(y); idx = np.arange(nobs); folds = np.random.default_rng(1).permutation(nobs) % 10
    for fn, (names, x0, f) in FORMS.items():
        r = fitnl(f, x0, y, n_, c_, P_); e = y - f(r.x, n_, c_, P_); k = len(r.x)
        loo = np.array([y[i] - f(fitnl(f, r.x, y[idx != i], n_[idx != i], c_[idx != i], P_[idx != i]).x, n_[i:i+1], c_[i:i+1], P_[i:i+1])[0] for i in idx])
        cv = np.concatenate([y[folds == k_] - f(fitnl(f, r.x, y[folds != k_], n_[folds != k_], c_[folds != k_], P_[folds != k_]).x, n_[folds == k_], c_[folds == k_], P_[folds == k_]) for k_ in range(10)])
        cvo = np.concatenate([np.where(folds == k_)[0] for k_ in range(10)])
        J = r.jac; s2 = (e @ e) / (nobs - k); A = np.linalg.pinv(J.T @ J); cov = s2 * A
        h = np.einsum("ij,jk,ik->i", J, A, J); cov3 = A @ (J.T * (e / (1 - h)) ** 2) @ J @ A   # HC3 sandwich
        out[fn] = dict(k=k, x=r.x.tolist(), se=np.sqrt(np.diag(cov)).tolist(), se_HC3=np.sqrt(np.diag(cov3)).tolist(), names=names, rmse=float(np.sqrt(np.mean(e ** 2))), loo=float(np.sqrt(np.mean(loo ** 2))),
                       cv10=float(np.sqrt(np.mean(cv ** 2))), bic=float(nobs * np.log(e @ e / nobs) + k * np.log(nobs)), max=float(np.abs(e).max()),
                       w1=int((np.abs(e) <= 1).sum()), e=e.tolist())
    X = spline_X(n_, c_, P_); b, *_ = np.linalg.lstsq(X, y, rcond=None); e = y - X @ b; Hm = X @ np.linalg.pinv(X.T @ X) @ X.T; k = np.linalg.matrix_rank(X)
    loo = e / (1 - np.diag(Hm)); cv = np.concatenate([y[folds == k_] - X[folds == k_] @ np.linalg.lstsq(X[folds != k_], y[folds != k_], rcond=None)[0] for k_ in range(10)])
    out["spline benchmark (4×4 tensor)"] = dict(k=int(k), rmse=float(np.sqrt(np.mean(e ** 2))), loo=float(np.sqrt(np.mean(loo ** 2))), cv10=float(np.sqrt(np.mean(cv ** 2))),
                                     bic=float(nobs * np.log(e @ e / nobs) + k * np.log(nobs)), max=float(np.abs(e).max()), w1=int((np.abs(e) <= 1).sum()), e=e.tolist())
    return out
res = {}
for q in ("core", "mem"):
    y = (D[q] - D.Tin).to_numpy(); res[q] = evaluate(y, q)
# choice: lowest BIC among parametric forms, but keep "current" unless another beats it by > 2 in BIC AND by ≥ 0.02 °C in LOO
def admissible(v):   # conductances, exponents, half-speed > 0, r∞ ≥ 0, no negative interaction
    return all(x > 0 for nm, x in zip(v["names"], v["x"]) if nm not in ("θ0", "r∞", "β", "s1")) and v["x"][1] >= 0
def choose(o):   # lowest BIC among admissible parametric forms; a form with more parameters must win by > 2 in BIC
    par = sorted((v["bic"], v["k"], k) for k, v in o.items() if "spline" not in k and admissible(v))
    best = par[0]
    for b, k, nm in par[1:]:
        if b - best[0] <= 2 and k < best[1]: best = (b, k, nm)
    return best[2]
CH = {q: choose(res[q]) for q in res}
# diagnostics on the chosen core / memory form
order_N = D.sort_values(["pl", "case", "N"]).index.to_numpy()
diag = {}
for q in res:
    e = np.array(res[q][CH[q]]["e"]); D[q + "_e"] = e
    reg = lambda x: np.polyfit(x, e, 1)
    diag[q] = dict(dw_time=float(durbin_watson(e)), dw_N=float(durbin_watson(e[order_N])),
                   slope_t=float(reg(D.t.to_numpy())[0]), slope_Tin=float(reg(D.Tin.to_numpy())[0]),
                   corr={v: float(np.corrcoef(D[v], e)[0, 1]) for v in ("N", "C", "P", "t", "Tin")},
                   rmse_by_gpu={int(k): float(np.sqrt(np.mean(np.square(v)))) for k, v in D.groupby("gpu")[q + "_e"]})
a0, a1 = anch.iloc[0], anch.iloc[1]
drift = dict(core_start=float(a0.cardA_core_nvapi_c), core_end=float(a1.cardA_core_nvapi_c), mem_start=float(a0.mem_c_max), mem_end=float(a1.mem_c_max),
             tin_start=float(a0.intake_c), tin_end=float(a1.intake_c), hours=float((a1.ts_end - a0.ts_end) / 3600))
grid_pt = D[(D.pl == 100) & (D.gpu == 40) & (D.case == 1600)].iloc[0]; drift["core_grid"] = float(grid_pt.core)
reps = g.iloc[1:-1].groupby(["pl_pct", "gpu_pct", "case_rpm_target"]).filter(lambda x: len(x) > 1)
out = dict(source=os.path.relpath(GF, H), n=len(D), rows=len(g), anchors=2, repeats=int(len(g) - 2 - len(D)), hours=drift["hours"],
           tin=dict(min=float(D.Tin.min()), max=float(D.Tin.max()), mean=float(D.Tin.mean()), sd=float(D.Tin.std())),
           choice=CH, admissible={q: {k: admissible(v) for k, v in res[q].items() if "spline" not in k} for q in res}, drift=drift, diag=diag,
           repeats_detail=[dict(cell=list(map(int, k)), core=v.cardA_core_nvapi_c.round(2).tolist(), mem=v.mem_c_max.tolist(), settled=v.settled.tolist()) for k, v in reps.groupby(["pl_pct", "gpu_pct", "case_rpm_target"])],
           forms={q: {k: {kk: vv for kk, vv in v.items() if kk != "e"} for k, v in res[q].items()} for q in res})
# cross-check the other way: steady3 model on the 79 / 70 earlier settled points (no refit; raw and after removing each session's mean offset)
E1 = pd.read_csv(os.path.join(H, "results-2026-10-22/steady-residuals.csv")); E2 = pd.read_csv(os.path.join(H, "results-2026-10-23/mem-points.csv"))
xc = {}
for q, Ed, col in (("core", E1, "core"), ("mem", E2, "mem_c_max")):
    f = FORMS[CH[q]][2]; v = np.array(res[q][CH[q]]["x"])
    e = Ed[col].to_numpy() - Ed.Tin.to_numpy() - f(v, Ed.N.to_numpy() / 1000, Ed.C.to_numpy() / 1500, Ed.P.to_numpy())
    sess = Ed.session.to_numpy(); e_c = e - pd.Series(e).groupby(sess).transform("mean").to_numpy()
    xc[q] = dict(n=len(e), mean=float(e.mean()), rmse=float(np.sqrt(np.mean(e ** 2))), w1=int((np.abs(e) <= 1).sum()), rmse_within=float(np.sqrt(np.mean(e_c ** 2))),
                 by_session={k: float(np.mean(e[sess == k])) for k in pd.unique(sess)})
out["crosscheck_earlier"] = xc
json.dump(out, open(os.path.join(R, "steady3-fit.json"), "w"), indent=1, ensure_ascii=False)
D.to_csv(os.path.join(R, "steady3-points.csv"), index=False)
for q in res:
    print(q, "choice:", CH[q])
    for k, v in res[q].items(): print(f"  {k:32s} k={v['k']:2d} rmse={v['rmse']:.3f} loo={v['loo']:.3f} cv={v['cv10']:.3f} bic={v['bic']:.1f} max={v['max']:.2f} w1={v['w1']}")
    for fk in ("current", "GPU-fan saturation (Hill)", "N×C interaction", "Hill + N×C"):
        v = res[q][fk]; print("  ", fk, {nm: (round(x, 4), round(s, 4)) for nm, x, s in zip(v["names"], v["x"], v["se"])})
    v = res[q]["current"]; print("  current:", {nm: (round(x, 4), round(s, 4)) for nm, x, s in zip(v["names"], v["x"], v["se"])})
print(json.dumps(xc)); print({q: res[q][CH[q]]["se_HC3"] for q in res}); print(drift, out["tin"], out["repeats_detail"])
