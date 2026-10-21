"""GPU thermal map — fit and plots (METHOD.md). Usage: analyze.py <run dir with points.csv> [out dir]
Fit per temperature:  1/R = h0 + a·rg^0.8 + b·rc^0.8 + c·rg^0.8·rc^0.8   (rg, rc = GPU / case fan rpm)
Plots: 3D surface, contour heat-map with iso-rpm lines, quietest-combination frontier. Writes fit.json + PNGs."""
import csv, json, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

run = Path(sys.argv[1]); out = Path(sys.argv[2]) if len(sys.argv) > 2 else run
out.mkdir(parents=True, exist_ok=True)
rows = list(csv.DictReader(open(run / "points.csv")))
def f(r, k):
    try: return float(r[k])
    except (ValueError, KeyError): return np.nan
P = {k: np.array([f(r, k) for r in rows]) for k in rows[0]}
ok = (P["settled"] == 1) & (P["too_hot"] == 0)
cond = json.load(open(run / "conditions.json")) if (run / "conditions.json").exists() else {}

def X(rg, rc):
    a, b = np.power(rg, 0.8), np.power(rc, 0.8)
    return np.column_stack([np.ones_like(a), a, b, a * b])

fits = {}
for t in ["core", "mem", "hot"]:
    R = P[f"R_{t}"]; m = ok & np.isfinite(R) & np.isfinite(P["gpu_rpm_mean"]) & np.isfinite(P["case_rpm"]) & (R > 0)
    if m.sum() < 5: continue
    A = X(P["gpu_rpm_mean"][m], P["case_rpm"][m]); y = 1 / R[m]
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    Rhat = 1 / (A @ coef)
    T = P[f"{t}_c"][m]; That = P["intake_c"][m] + Rhat * P["power_w"][m]
    ss = np.sum((y - A @ coef) ** 2); r2 = 1 - ss / np.sum((y - y.mean()) ** 2)
    fits[t] = {"h0": coef[0], "a": coef[1], "b": coef[2], "c": coef[3], "r2_invR": r2, "n": int(m.sum()),
               "rmse_c": float(np.sqrt(np.mean((T - That) ** 2))), "max_err_c": float(np.max(np.abs(T - That)))}
json.dump({"conditions": cond, "fit": fits, "points": int(len(rows)), "settled_ok": int(ok.sum()),
           "too_hot": int((P["too_hot"] == 1).sum()), "not_settled": int((P["settled"] == 0).sum())},
          open(out / "fit.json", "w"), indent=2, default=float)

names = {"core": "Core", "mem": "Memory", "hot": "Hot spot"}
fg, fc = P["fg_pct"], P["fc_pct"]
for t in fits:
    v = P[f"{t}_c"]
    # 3D surface (measured points + fitted surface on the rpm grid at mean intake and power)
    fig = plt.figure(figsize=(8, 6)); ax = fig.add_subplot(projection="3d")
    gi = np.linspace(np.nanmin(fg), 100, 30); ci = np.linspace(np.nanmin(fc), 100, 30); G, C = np.meshgrid(gi, ci)
    rg_of = np.poly1d(np.polyfit(fg[ok], P["gpu_rpm_mean"][ok], 1)); rc_of = np.poly1d(np.polyfit(fc[ok], P["case_rpm"][ok], 1))
    k = fits[t]; RG, RC = np.clip(rg_of(G), 1, None), np.clip(rc_of(C), 1, None)
    Rs = 1 / (k["h0"] + k["a"] * RG ** 0.8 + k["b"] * RC ** 0.8 + k["c"] * RG ** 0.8 * RC ** 0.8)
    Ts = np.nanmean(P["intake_c"][ok]) + Rs * np.nanmean(P["power_w"][ok])
    ax.plot_surface(G, C, Ts, cmap="viridis", alpha=0.75, linewidth=0)
    ax.scatter(fg[ok], fc[ok], v[ok], color="k", s=14); ax.scatter(fg[P["too_hot"] == 1], fc[P["too_hot"] == 1], v[P["too_hot"] == 1], color="r", s=24, label="too hot (stopped)")
    ax.set_xlabel("GPU fans %"); ax.set_ylabel("Case fans %"); ax.set_zlabel(f"{names[t]} °C")
    ax.set_title(f"{names[t]} temperature at {np.nanmean(P['power_w'][ok]):.0f} W, intake {np.nanmean(P['intake_c'][ok]):.1f} °C · fit ±{k['rmse_c']:.1f} °C")
    fig.tight_layout(); fig.savefig(out / f"surface-{t}.png", dpi=150); plt.close(fig)
    # contour heat-map + iso-rpm lines of the GPU fans
    fig, ax = plt.subplots(figsize=(8, 6))
    cs = ax.contourf(G, C, Ts, levels=14, cmap="inferno"); fig.colorbar(cs, label=f"{names[t]} °C (fit)")
    ax.contour(G, C, Ts, levels=14, colors="w", linewidths=0.4, alpha=0.6)
    il = ax.contour(G, C, RG, levels=6, colors="c", linestyles="--", linewidths=0.8); ax.clabel(il, fmt="%d rpm", fontsize=7)
    ax.scatter(fg, fc, c=np.where(P["too_hot"] == 1, "r", "w"), edgecolors="k", s=28, zorder=3)
    ax.set_xlabel("GPU fans %"); ax.set_ylabel("Case fans %"); ax.set_title(f"{names[t]} — measured points and iso-rpm lines (GPU fans)")
    fig.tight_layout(); fig.savefig(out / f"heatmap-{t}.png", dpi=150); plt.close(fig)

# quietest combination per target hot-spot temperature (relative noise: fan affinity law, sound power ∝ rpm^5 → 50·log10)
t = "hot" if "hot" in fits else next(iter(fits), None)
if t:
    k = fits[t]; G, C = np.meshgrid(np.linspace(np.nanmin(fg), 100, 141), np.linspace(np.nanmin(fc), 100, 141))
    RG, RC = np.clip(rg_of(G), 1, None), np.clip(rc_of(C), 1, None)
    Ts = np.nanmean(P["intake_c"][ok]) + np.nanmean(P["power_w"][ok]) / (k["h0"] + k["a"] * RG ** 0.8 + k["b"] * RC ** 0.8 + k["c"] * RG ** 0.8 * RC ** 0.8)
    rg_ref, rc_ref = np.nanmax(P["gpu_rpm_mean"]), np.nanmax(P["case_rpm"])
    noise = 10 * np.log10((3 * (RG / rg_ref) ** 5 + 4 * (RC / rc_ref) ** 5) / 7)   # 3 GPU fans + 4 case fans, 0 dB = all at max (relative)
    targets = np.arange(np.ceil(np.nanmin(Ts)), np.floor(np.nanmax(Ts)) + 1)
    front = []
    for T0 in targets:
        m = Ts <= T0
        if m.any(): i = np.argmin(np.where(m, noise, np.inf)); front.append((T0, G.flat[i], C.flat[i], noise.flat[i]))
    fr = np.array(front)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 5))
    a1.plot(fr[:, 0], fr[:, 3], "-o", ms=3); a1.set_xlabel(f"target {names[t]} °C"); a1.set_ylabel("relative fan noise, dB (0 = all fans at max)"); a1.set_title("Quietest combination per target")
    sc = a2.scatter(fr[:, 1], fr[:, 2], c=fr[:, 0], cmap="coolwarm", s=24); fig.colorbar(sc, ax=a2, label=f"target {names[t]} °C")
    a2.set_xlabel("GPU fans %"); a2.set_ylabel("Case fans %"); a2.set_title("Where the quietest combination lies"); a2.set_xlim(25, 102); a2.set_ylim(0, 102)
    fig.tight_layout(); fig.savefig(out / "frontier.png", dpi=150); plt.close(fig)
    with open(out / "frontier.csv", "w") as fh:
        fh.write("target_c,gpu_fans_pct,case_fans_pct,rel_noise_db\n"); [fh.write(f"{a:.0f},{b:.0f},{c:.0f},{d:.1f}\n") for a, b, c, d in fr]
print(json.dumps(json.load(open(out / "fit.json"))["fit"], indent=1))

# ── drift and dynamics (koncertmistrz 2026-10-20) ──
raw_path = run / "raw.csv"
if raw_path.exists():
    raw = list(csv.DictReader(open(raw_path)))
    def col(k): return np.array([f(r, k) for r in raw])
    t, ia = col("t"), col("intake_c")
    # (1a) intake-air drift over the run: linear trend °C/h and range
    m = np.isfinite(t) & np.isfinite(ia)
    drift = {}
    if m.sum() > 60:
        k1, k0 = np.polyfit((t[m] - t[m][0]) / 3600, ia[m], 1)
        drift = {"intake_slope_c_per_h": float(k1), "intake_min_c": float(ia[m].min()), "intake_max_c": float(ia[m].max()), "hours": float((t[m][-1] - t[m][0]) / 3600)}
        fig, ax = plt.subplots(figsize=(9, 3.5)); ax.plot((t[m] - t[m][0]) / 3600, ia[m], lw=0.8)
        ax.set_xlabel("hours since start"); ax.set_ylabel("intake air °C"); ax.set_title(f"Intake air over the run: {k1:+.2f} °C/h, {ia[m].min():.1f}–{ia[m].max():.1f} °C")
        fig.tight_layout(); fig.savefig(out / "intake-drift.png", dpi=150); plt.close(fig)
    # (1b) repeatability: settings measured more than once (reference point in future runs) → spread of R
    rep = {}
    for (g, c) in {(a, b) for a, b in zip(fg, fc)}:
        mm = ok & (fg == g) & (fc == c)
        if mm.sum() >= 2: rep[f"{g:.0f}/{c:.0f}"] = {t2: float(np.nanmax(P[f"R_{t2}"][mm]) - np.nanmin(P[f"R_{t2}"][mm])) for t2 in ["core", "mem", "hot"]}
    # (2) first-order step response per point: T(t) = T∞ − (T∞ − T0)·e^(−t/τ); τ by grid search, T∞ and amplitude by least squares.
    #     Then T∞ extrapolated from only the first 60 / 90 s, compared with the full steady value (mean of the last 60 s of the point).
    seg, cur_key, start = [], None, 0
    keys = [(r["phase"], r["fg_set"], r["fc_set"]) for r in raw]
    for i, kk in enumerate(keys + [None]):
        if kk != cur_key:
            if cur_key and cur_key[0] == "points" and i - start >= 60: seg.append((start, i))
            cur_key, start = kk, i
    taus = np.arange(5, 601, 5)
    def fit1(tt, yy):
        best = None
        for tau in taus:
            e = np.exp(-tt / tau); A = np.column_stack([np.ones_like(e), -e])   # y = Tinf − B·e
            co, res, *_ = np.linalg.lstsq(A, yy, rcond=None); sse = float(np.sum((A @ co - yy) ** 2))
            if best is None or sse < best[0]: best = (sse, tau, co[0])
        return best[1], best[2]
    dyn = []
    for a, b in seg:
        tt = t[a:b] - t[a]
        row = {"fg_pct": raw[a]["fg_set"], "fc_pct": raw[a]["fc_set"], "seconds": float(tt[-1])}
        for t2 in ["core", "mem", "hot"]:
            y = col(f"{t2}_c")[a:b]; mm = np.isfinite(y)
            if mm.sum() < 60: continue
            tau, tinf = fit1(tt[mm], y[mm]); steady = float(np.nanmean(y[mm][tt[mm] > tt[mm][-1] - 60]))
            row[f"{t2}_tau_s"], row[f"{t2}_Tinf"], row[f"{t2}_steady"] = tau, float(tinf), steady
            for w in (60, 90):
                mw = mm & (tt <= w)
                if mw.sum() >= 30: row[f"{t2}_Tinf_{w}s_err"] = float(fit1(tt[mw], y[mw])[1] - steady)
        dyn.append(row)
    if dyn:
        keys2 = sorted({k for r in dyn for k in r}, key=lambda k: (k not in ("fg_pct", "fc_pct", "seconds"), k))
        with open(out / "step-response.csv", "w") as fh:
            fh.write(",".join(keys2) + "\n"); [fh.write(",".join(str(r.get(k, "")) for k in keys2) + "\n") for r in dyn]
        summ = {}
        for t2 in ["core", "mem", "hot"]:
            tv = [r[f"{t2}_tau_s"] for r in dyn if f"{t2}_tau_s" in r]
            if not tv: continue
            summ[t2] = {"tau_median_s": float(np.median(tv)), "tau_min_s": float(min(tv)), "tau_max_s": float(max(tv))}
            for w in (60, 90):
                ev = [abs(r[f"{t2}_Tinf_{w}s_err"]) for r in dyn if f"{t2}_Tinf_{w}s_err" in r]
                if ev: summ[t2][f"extrapolation_{w}s_mae_c"], summ[t2][f"extrapolation_{w}s_max_c"] = float(np.mean(ev)), float(np.max(ev))
        fig, ax = plt.subplots(figsize=(8, 4))
        for t2, mk in (("core", "o"), ("mem", "s"), ("hot", "^")):
            ev = [r.get(f"{t2}_Tinf_90s_err") for r in dyn]; tv = [r.get(f"{t2}_tau_s") for r in dyn]
            xs = [a for a, e in zip(tv, ev) if a is not None and e is not None]; ys = [e for a, e in zip(tv, ev) if a is not None and e is not None]
            if xs: ax.scatter(xs, ys, marker=mk, s=18, label=names[t2])
        ax.axhline(0, color="k", lw=0.6); ax.set_xlabel("fitted time constant τ (s)"); ax.set_ylabel("T∞ from first 90 s − steady value (°C)")
        ax.set_title("Can a point be shortened? Extrapolation error after 90 s"); ax.legend(); fig.tight_layout(); fig.savefig(out / "step-response.png", dpi=150); plt.close(fig)
    else: summ = {}
    fj = json.load(open(out / "fit.json")); fj.update({"intake_drift": drift, "repeatability_R_spread": rep or "no setting measured twice", "step_response": summ})
    json.dump(fj, open(out / "fit.json", "w"), indent=2, default=float)
    print(json.dumps({"intake_drift": drift, "step_response": summ}, indent=1))

