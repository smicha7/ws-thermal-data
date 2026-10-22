"""val1 (2026-10-21 evening): 20 settled points with snapshots at 1/2/3/5/8/12 min.
Checks: dynamic model (dyn-model.json, M2-pow) steady law and free-run simulation vs settled values; static eq (9)
(core-model.json from fig_core_model.py) vs settled values; R = (T - Tin)/P across power limit at fixed fans;
static fit on val1 alone with and without theta0; convergence of snapshots to the settled value by step type.
Usage: val1_check.py core-model.json outdir"""
import csv, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dyn_model as dm
HERE = os.path.dirname(os.path.abspath(__file__)); out = sys.argv[2]
rows = sorted(csv.DictReader(open(os.path.join(HERE, "data", "val1-2026-10-21", "grid.csv"))), key=lambda r: float(r["ts_end"]))
f = lambda k: np.array([float(r[k]) for r in rows])
N, C, P, Tin, T = f("cardA_fan_rpm"), f("case_rpm"), f("power_w_sum"), f("intake_c"), f("core_c_max")
J = json.load(open(os.path.join(dm.OUT, "dyn-model.json")))["M2-pow"]["params"]
S = json.load(open(sys.argv[1]))["full"]
rm = lambda e: float(np.sqrt(np.mean(np.asarray(e) ** 2)))
dyn_ss = Tin + J["th0"] + P * dm.R_total(J, N, C, 2)
stat = Tin + S["th0"] + P * (S["rinf"] + S["k"] * (N / 1000) ** -S["m"] * (C / 1500) ** -S["q"])
# free-run simulation: mean of the last 60 s of each point
D = dm.load("val1"); yc, _ = dm.core_pred(J, D, 2); t_abs = D["t"] + D["t0"]
sim_end = np.array([float(np.mean(yc[(t_abs > float(r["ts_end"]) - 60) & (t_abs <= float(r["ts_end"]))])) for r in rows])
meas_end = np.array([float(np.mean(D["core"][(t_abs > float(r["ts_end"]) - 60) & (t_abs <= float(r["ts_end"]))])) for r in rows])
res = dict(n=len(rows), traj_rmse=rm(yc - D["core"]),
           dyn_steady_rmse=rm(dyn_ss - T), dyn_steady_bias=float(np.mean(dyn_ss - T)),
           dyn_sim_end_rmse=rm(sim_end - meas_end), dyn_sim_end_bias=float(np.mean(sim_end - meas_end)),
           static9_rmse=rm(stat - T), static9_bias=float(np.mean(stat - T)),
           static9_by_pl={pl: float(np.mean((stat - T)[f("pl_pct") == pl])) for pl in (100, 90, 80, 70)})
# R across power limit at fixed fans
grp = {}
for r, Ti, Tv, Pv in zip(rows, Tin, T, P): grp.setdefault((r["case_rpm_target"], r["gpu_pct"]), []).append((int(r["pl_pct"]), round(1000 * (Tv - Ti) / Pv, 1)))
res["R_mK_per_W"] = {f"{c}/{g}": sorted(v, reverse=True) for (c, g), v in grp.items() if len(v) > 1}
# static fit on val1 alone
y = T - Tin
def fit(th0=True):
    best = None
    for m in np.arange(0.8, 2.6, 0.02):
        for q in np.arange(0, 0.8, 0.02):
            cols = [P, P * (N / 1000) ** -m * (C / 1500) ** -q]
            X = np.column_stack(([np.ones_like(P)] if th0 else []) + cols); c, *_ = np.linalg.lstsq(X, y, rcond=None); e = np.sum((y - X @ c) ** 2)
            if best is None or e < best[0]: best = (e, c, m, q)
    e, c, m, q = best
    return dict(rmse=float(np.sqrt(e / len(y))), th0=float(c[0]) if th0 else 0.0, rinf=float(c[-2]), k=float(c[-1]), m=float(m), q=float(q))
res["fit_val1_th0"], res["fit_val1_no_th0"] = fit(True), fit(False)
# convergence by step type
conv = []
for i, r in enumerate(rows):
    if i == 0: kind = "first point (after warm-up)"
    else:
        p = rows[i - 1]; dpl = int(r["pl_pct"]) - int(p["pl_pct"]); dg = int(r["gpu_pct"]) - int(p["gpu_pct"]); dc = r["case_rpm_target"] != p["case_rpm_target"]
        kind = "small falling step" if (not dc and dg == 0 and -10 <= dpl < 0) else "large step"
        kind_d = f"case {p['case_rpm_target']}→{r['case_rpm_target']}, GPU {p['gpu_pct']}→{r['gpu_pct']} %, PL {p['pl_pct']}→{r['pl_pct']} %"
    d = {m: (float(r[f"core_{m}min"]) - float(r["core_c_max"])) if r.get(f"core_{m}min") not in (None, "") else None for m in (1, 2, 3, 5, 8, 12)}
    conv.append(dict(i=i, kind=kind, step=kind_d if i else "", d=d))
summ = {}
for kind in ("small falling step", "large step"):
    sel = [c for c in conv if c["kind"] == kind]
    summ[kind] = dict(n=len(sel), **{f"{m}min": [round(min(c["d"][m] for c in sel if c["d"][m] is not None), 1), round(max(c["d"][m] for c in sel if c["d"][m] is not None), 1)] for m in (1, 2, 3, 5, 8)})
res["convergence"] = summ; res["convergence_points"] = conv
json.dump(res, open(os.path.join(out, "val1-check.json"), "w"), indent=1)
with open(os.path.join(out, "val1-convergence.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["order", "case_rpm", "gpu_pct", "pl_pct", "step_type", "step", "settled_core_c", *[f"core_{m}min_minus_settled_c" for m in (1, 2, 3, 5, 8, 12)]])
    for c, r in zip(conv, rows): w.writerow([c["i"] + 1, r["case_rpm_target"], r["gpu_pct"], r["pl_pct"], c["kind"], c["step"], r["core_c_max"], *[("" if c["d"][m] is None else round(c["d"][m], 2)) for m in (1, 2, 3, 5, 8, 12)]])
print(json.dumps({k: v for k, v in res.items() if k != "convergence_points"}, indent=1))
for c in conv: print(c["i"] + 1, c["kind"][:5], c["step"], {m: (None if v is None else round(v, 1)) for m, v in c["d"].items()})
