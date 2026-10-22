"""Cross-validation + final recommended dynamic core model (uses dyn_model.py).

(a) fit grid1c -> test all runs   (b) fit dyn1 -> test all runs
(c) leave-one-run-out over the daytime runs, for model variants (fan law pow/sat/conv; theta free/zero/drift)
Then: final model on all daytime runs, 95 % CI, tau(N, C), steady lookup Tin 19/25/30 x GPU % x case x PL, PNGs.
Run:  .venv/bin/python dyn_cv.py
"""
import csv, json, multiprocessing as mp, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import dyn_model as dm

OUT = dm.OUT
DAY = ["grid1c", "dyn1", "val1", "val2", "log-1", "hold", "grid1d"]
VALS = ["val1", "val2"]
VARIANTS = {"pow": ("pow", "free"), "sat": ("sat", "free"), "conv": ("conv", "free"),
            "pow-th0=0": ("pow", "zero"), "pow-drift": ("pow", "drift")}
_DATA = None


def data():
    global _DATA
    if _DATA is None:
        _DATA = {n: dm.load(n) for n in DAY}           # loaded once in the parent, inherited by forked workers
        _DATA["night-v2d"] = dm.load("night-v2d", dm.NIGHT)
    return _DATA


def job(args):
    tag, form, theta, train = args
    D = data()
    p = dm.fit_core([D[n] for n in train], 2, form, theta=theta)
    return tag, p


def per_run_rmse(p):
    D = data()
    return {n: dm.rmse(dm.core_pred(p, D[n], 2)[0], D[n]["core"]) for n in D}


def val_settled(p, name):
    """Settled points of val1/val2: measured last-60 s mean vs model steady value (and vs simulated mean)."""
    D = data()[name]
    yc, _ = dm.core_pred(p, D, 2)
    out = []
    for r in csv.DictReader(open(os.path.join(dm.HERE, "data", f"{name}-2026-10-21", "grid.csv"))):
        if r["settled"] != "1":
            continue
        te = float(r["ts_end"]) - D["t0"]
        w = (D["t"] > te - 60) & (D["t"] <= te)
        N, C, P, Tin = (float(np.mean(D[k][w])) for k in ("N", "C", "P", "Tin"))
        out.append(dict(run=name, pct=float(r["gpu_pct"]), pl=float(r["pl_pct"]), N=N, C=C, P=P, Tin=Tin,
                        meas=float(np.mean(D["core"][w])), sim=float(np.mean(yc[w])),
                        ss=float(dm.steady_core(p, N, C, P, Tin, 2))))
    return out


def fan_map():
    """Linear GPU fan % -> rpm from steady dyn1/val1 samples."""
    rows = []
    for n in ("dyn1", "val1"):
        for r in data()[n]["rows"]:
            if r["gpu_pct"] and float(r["gpu_pct"]) >= 40:
                rpm = np.mean([float(v) for v in r["gpu_rpm"].split("|")])
                if rpm > 500:
                    rows.append((float(r["gpu_pct"]), rpm))
    a = np.array(rows)
    b1, b0 = np.polyfit(a[:, 0], a[:, 1], 1)
    return b1, b0


def ci(p, r, names, Ds):
    """95 % CI from the Jacobian, variance inflated for AR(1)-correlated 1 Hz residuals."""
    e = r.fun; J = r.jac
    rho = np.mean([np.corrcoef(x[:-1], x[1:])[0, 1] for x in np.split(e, np.cumsum([len(D["P"]) for D in Ds])[:-1])])
    s2 = np.sum(e ** 2) / (len(e) - len(names)) * (1 + rho) / (1 - rho)
    cov = np.linalg.pinv(J.T @ J) * s2
    out = {}
    for i, k in enumerate(names):
        sd = float(np.sqrt(max(cov[i, i], 0)))
        v = r.x[i]
        out[k] = (float(v - 1.96 * sd), float(v + 1.96 * sd)) if k in dm.LIN else (float(np.exp(v - 1.96 * sd)), float(np.exp(v + 1.96 * sd)))
    return out, float(rho)


def main():
    data()
    jobs = [("A:grid1c", "pow", "free", ["grid1c"]), ("B:dyn1", "pow", "free", ["dyn1"])]
    for v, (form, theta) in VARIANTS.items():
        for hold in DAY:
            jobs.append((f"L:{v}:{hold}", form, theta, [n for n in DAY if n != hold]))
    with mp.get_context("fork").Pool(min(8, os.cpu_count() or 4)) as pool:
        fits = dict(pool.map(job, jobs))

    res = {"A_grid1c": dict(params=fits["A:grid1c"], rmse=per_run_rmse(fits["A:grid1c"])),
           "B_dyn1": dict(params=fits["B:dyn1"], rmse=per_run_rmse(fits["B:dyn1"]))}
    for k in ("A_grid1c", "B_dyn1"):
        pk = res[k]["params"]
        res[k]["settled_rmse"] = {v: dm.rmse([x["ss"] - x["meas"] for x in val_settled(pk, v)]) for v in VALS}
        print(k, {n: round(x, 2) for n, x in res[k]["rmse"].items()}, "settled", {v: round(x, 2) for v, x in res[k]["settled_rmse"].items()})
    loro = {}
    for v in VARIANTS:
        per, held_err, v1err, night = {}, [], {}, []
        for hold in DAY:
            p = fits[f"L:{v}:{hold}"]
            D = data()[hold]; e = dm.core_pred(p, D, 2)[0] - D["core"]
            per[hold] = dm.rmse(e); held_err.append(e)
            night.append(dm.rmse(dm.core_pred(p, data()["night-v2d"], 2)[0], data()["night-v2d"]["core"]))
            if hold in VALS:
                v1err[hold] = dm.rmse([x["ss"] - x["meas"] for x in val_settled(p, hold)])
        loro[v] = dict(per_run=per, pooled=dm.rmse(np.concatenate(held_err)), mean=float(np.mean(list(per.values()))),
                       settled_heldout=v1err, night_mean=float(np.mean(night)),
                       params={h: fits[f"L:{v}:{h}"] for h in DAY})
        print(f"LORO {v}: pooled {loro[v]['pooled']:.3f} mean {loro[v]['mean']:.3f} per {({k: round(x, 2) for k, x in per.items()})} "
              f"settled(held-out) {({k: round(x, 2) for k, x in v1err.items()})} night {loro[v]['night_mean']:.2f}")
    res["LORO"] = loro
    best = min(VARIANTS, key=lambda v: loro[v]["pooled"])
    if loro["pow"]["pooled"] - loro[best]["pooled"] < 0.05:      # parsimony: extra parameters must earn > 0.05 °C
        best = "pow"
    res["selection"] = f"{best} (best pooled LORO {min(loro[v]['pooled'] for v in VARIANTS):.3f} °C; >0.05 °C gain needed for extra params)"
    form, theta = VARIANTS[best]

    # ---------------- final model on all daytime runs
    Ds = [data()[n] for n in DAY]
    p, r, names = dm.fit_core(Ds, 2, form, theta=theta, p0=fits[f"L:{best}:{DAY[0]}"], full=True)
    cis, rho = ci(p, r, names, Ds)
    spread = {k: (min(loro[best]["params"][h][k] for h in DAY), max(loro[best]["params"][h][k] for h in DAY))
              for k in names}
    final = dict(variant=best, params=p, ci95=cis, residual_lag1_rho=rho, loro_param_range=spread,
                 train_rmse=per_run_rmse(p))
    v1 = [x for v in VALS for x in val_settled(p, v)]
    final["settled_rmse_in_sample"] = {v: dm.rmse([x["ss"] - x["meas"] for x in v1 if x["run"] == v]) for v in VALS}
    final["settled_points"] = v1
    # memory node: LORO + final
    mem = {}
    for hold in DAY:
        tr = [n for n in DAY if n != hold]; pl = loro[best]["params"][hold]
        pm = dm.fit_mem([data()[n] for n in tr], [dm.core_pred(pl, data()[n], 2)[1] for n in tr])
        mem[hold] = dm.rmse(dm.mem_sim(pm, data()[hold], dm.core_pred(pl, data()[hold], 2)[1]), data()[hold]["mem"])
    pm = dm.fit_mem(Ds, [dm.core_pred(p, D, 2)[1] for D in Ds])
    final["memory"] = dict(params=pm, loro_rmse=mem,
                           night_rmse=dm.rmse(dm.mem_sim(pm, data()["night-v2d"], dm.core_pred(p, data()["night-v2d"], 2)[1]), data()["night-v2d"]["mem"]))
    print("memory LORO:", {k: round(x, 2) for k, x in mem.items()}, pm)

    b1, b0 = fan_map(); pct2rpm = lambda q: b1 * np.asarray(q) + b0; rpm2pct = lambda n: (np.asarray(n) - b0) / b1
    final["fan_map_rpm"] = dict(slope=b1, intercept=b0)
    taus = {}
    for pct in (40, 50, 60, 70, 80, 90, 100):
        for C in (1000, 1500, 2000, 2920):
            A, _ = dm.system(p, dict(P=[575.0], N=[pct2rpm(pct)], C=[C], Tin=[19.0]), 2)
            taus[f"{pct}%_C{C}"] = round(float(max(-1 / np.linalg.eigvals(A[0]).real)), 1)
    final["tau_s"] = taus
    res["final"] = final
    print("final", best, {k: round(v, 5) if isinstance(v, float) else v for k, v in p.items()})
    print("CI", cis, "rho", rho); print("tau", taus)

    # ---------------- steady lookup
    pcts = [40, 50, 60, 70, 80, 90, 100]; cases = [1000, 1500, 2000, 2920]; pls = [70, 80, 90, 100]
    with open(os.path.join(OUT, "dyn-steady-lookup.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["tin_c", "pl_pct", "power_w", "case_rpm", "gpu_pct", "gpu_rpm", "core_c"])
        for Tin in (19, 25, 30):
            for pl in pls:
                for C in cases:
                    for q in pcts:
                        w.writerow([Tin, pl, round(5.75 * pl, 1), C, q, round(float(pct2rpm(q))),
                                    round(float(dm.steady_core(p, pct2rpm(q), C, 5.75 * pl, Tin, 2)), 1)])
    md = [f"# Steady core °C — dynamic model {best} (fit on all daytime runs 2026-10-21)", "",
          "Load power-capped at PL (575 W × PL %). Rows: case rpm; columns: GPU fan % (rpm).",
          f"Model: T = Tin + θ0 + P·[Rjs + ra + k·(N/1000)^−m·(C/1500)^−q], Rjs {1000 * p['Rjs']:.1f} m°C/W, ra {1000 * p['ra']:.1f} m°C/W, "
          f"k {1000 * p['k']:.1f} m°C/W, m {p['m']:.3f}, q {p['q']:.3f}, θ0 {p['th0']:.2f} °C, heatsink {p['Cs']:.0f} J/°C. "
          "Tin 25/30 °C = extrapolation (data at 19–20 °C).", ""]
    for Tin in (19, 25, 30):
        for pl in pls:
            md.append(f"**Tin {Tin} °C, PL {pl} % ({5.75 * pl:.0f} W)**"); md.append("")
            md.append("| case \\ GPU | " + " | ".join(f"{q} % ({pct2rpm(q):.0f})" for q in pcts) + " |")
            md.append("|---|" + "---|" * len(pcts))
            for C in cases:
                md.append(f"| {C} | " + " | ".join(f"{float(dm.steady_core(p, pct2rpm(q), C, 5.75 * pl, Tin, 2)):.1f}" for q in pcts) + " |")
            md.append("")
    open(os.path.join(OUT, "dyn-steady-lookup.md"), "w").write("\n".join(md))
    json.dump(res, open(os.path.join(OUT, "dyn-cv.json"), "w"), indent=1, default=float)

    # ---------------- figures
    D = data()["dyn1"]; yc, X = dm.core_pred(p, D, 2); ya = dm.core_pred(fits["A:grid1c"], D, 2)[0]
    ym = dm.mem_sim(pm, D, X); tm = D["t"] / 60
    fig, ax = plt.subplots(4, 1, figsize=(15, 11), sharex=True, gridspec_kw=dict(height_ratios=[3, 2.4, 1.2, 1.6]))
    ax[0].plot(tm, D["core"], color="0.2", lw=0.8, label="core measured (NVAPI 0.01 °C)")
    ax[0].plot(tm, ya, color="tab:blue", lw=0.8, alpha=0.8, label=f"fit on grid1c only (RMSE {dm.rmse(ya, D['core']):.2f} °C)")
    ax[0].plot(tm, yc, color="tab:red", lw=0.9, label=f"final {best}, LORO fit without dyn1 (RMSE "
               f"{loro[best]['per_run']['dyn1']:.2f} °C); all-data fit shown (RMSE {dm.rmse(yc, D['core']):.2f} °C)")
    ax[0].set_ylabel("core °C"); ax[0].legend(fontsize=8, loc="lower right")
    ax[1].plot(tm, D["mem"], color="0.4", lw=0.8, label="memory measured")
    ax[1].plot(tm, ym, color="tab:purple", lw=0.9, label=f"memory node (LORO RMSE {mem['dyn1']:.2f} °C)")
    ax[1].set_ylabel("memory °C"); ax[1].legend(fontsize=8, loc="lower right")
    ax[2].plot(tm, yc - D["core"], color="tab:red", lw=0.6); ax[2].plot(tm, ya - D["core"], color="tab:blue", lw=0.5, alpha=0.6)
    ax[2].axhline(0, color="0.5", lw=0.5); ax[2].set_ylabel("sim − meas °C")
    ax[3].plot(tm, D["P"], color="tab:orange", lw=0.7); ax[3].set_ylabel("board W", color="tab:orange")
    a3 = ax[3].twinx(); a3.plot(tm, rpm2pct(D["N"]), color="tab:green", lw=0.7); a3.plot(tm, D["C"] / 30, color="tab:cyan", lw=0.7)
    a3.set_ylabel("GPU fan % (green); case rpm/30 (cyan)", fontsize=8)
    a3b = a3.secondary_yaxis(1.07, functions=(pct2rpm, rpm2pct)); a3b.set_ylabel("GPU fan rpm", fontsize=8)
    ax[3].set_xlabel("minutes from start of dyn1 (56 random steps)")
    fig.suptitle("dyn1 — measured vs simulated (free run from first sample)")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "dyn-d-dyn1.png"), dpi=130); plt.close(fig)

    runs = DAY + ["night-v2d"]
    schemes = [("A: fit grid1c", res["A_grid1c"]["rmse"]), ("B: fit dyn1", res["B_dyn1"]["rmse"])]
    schemes += [(f"LORO {v}", {**loro[v]["per_run"], "night-v2d": loro[v]["night_mean"]}) for v in VARIANTS]
    fig, ax = plt.subplots(figsize=(14, 5.5)); w = 0.8 / len(schemes); x = np.arange(len(runs))
    for i, (lab, d) in enumerate(schemes):
        ax.bar(x + i * w - 0.4 + w / 2, [d[n] for n in runs], w, label=lab)
    ax.set_xticks(x, [n + ("\n(test for all)" if n == "night-v2d" else "") for n in runs])
    ax.set_ylabel("core RMSE of simulated trajectory [°C]")
    ax.set_title("Cross-validation: held-out runs in LORO; A/B bars on their own training run are in-sample (grid1c in A, dyn1 in B)")
    ax.legend(fontsize=8, ncol=4); ax.grid(axis="y", alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "dyn-e-cv.png"), dpi=130); plt.close(fig)

    fig, axs = plt.subplots(2, 2, figsize=(15, 10))
    qg = np.linspace(40, 100, 61); Cg = np.linspace(1000, 2920, 50)
    for a, (Tin, pl) in zip(axs.flat[:3], ((19, 100), (19, 70), (25, 100))):
        Z = dm.steady_core(p, pct2rpm(qg)[None, :], Cg[:, None], 5.75 * pl, Tin, 2)
        im = a.contourf(qg, Cg, Z, levels=np.arange(40, 96, 2), cmap="inferno")
        cs = a.contour(qg, Cg, Z, levels=[60, 70, 80, 85, 90], colors="w", linewidths=0.8); a.clabel(cs, fmt="%d °C", fontsize=8)
        fig.colorbar(im, ax=a, label="steady core °C")
        a.set_xlabel("GPU fan %"); a.set_ylabel("case rpm"); a.set_title(f"Tin {Tin} °C, PL {pl} % ({5.75 * pl:.0f} W)")
        s2 = a.secondary_xaxis("top", functions=(pct2rpm, rpm2pct)); s2.set_xlabel("GPU fan rpm", fontsize=8)
    a = axs.flat[3]; cm = plt.get_cmap("viridis")
    for pl, ls in ((100, "-"), (70, "--")):
        for C in (1500,):
            a.plot(qg, dm.steady_core(p, pct2rpm(qg), C, 5.75 * pl, 19.0, 2), ls, color="k", lw=1.5, label=f"model case 1500, PL {pl}, Tin 19")
    for xv in v1:
        a.scatter(xv["pct"], xv["meas"] - xv["Tin"] + 19.0, color=cm((xv["pl"] - 70) / 30), edgecolor="k" if 1300 < xv["C"] < 1700 else "r",
                  marker="o" if xv["run"] == "val1" else "s", s=45, zorder=3)
        a.scatter(xv["pct"], xv["ss"] - xv["Tin"] + 19.0, marker="x", color=cm((xv["pl"] - 70) / 30), s=35, zorder=4)
    a.scatter([], [], color="0.5", edgecolor="k", label="val1 (●) / val2 (■) settled, measured (red edge: case ≠ 1500)")
    a.scatter([], [], marker="x", color="0.5", label="model at the same inputs")
    a.set_xlabel("GPU fan %"); a.set_ylabel("core °C (shifted to Tin 19)"); a.legend(fontsize=7)
    hs = loro[best]["settled_heldout"]
    a.set_title(f"Settled points vs model, RMSE held-out: val1 {hs['val1']:.2f} °C, val2 {hs['val2']:.2f} °C; colour = PL 70→100", fontsize=10)
    s2 = a.secondary_xaxis("top", functions=(pct2rpm, rpm2pct)); s2.set_xlabel("GPU fan rpm", fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "dyn-f-steady-maps.png"), dpi=130); plt.close(fig)


if __name__ == "__main__":
    main()
