"""Night of 2026-10-20/21 on ws298: analysis of the fast-point runs (v2d grid, v3d power limit, v4d frontier). METHOD.md.
Usage: analyze_night.py <experiments dir> <out dir>
Per point the steady estimate is the same rule the service uses: T∞ from the 60 s first-order fit when well determined
(95 % CI ≤ 2 °C and within 8 °C of the measured mean), otherwise the 60 s mean. Bridge points (≤ 5-point steps) and too-hot points are left out of fits."""
import csv, json, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

root, out = Path(sys.argv[1]), Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
NAMES = {"core": "Core", "mem": "Memory", "hot": "Hot spot"}
def num(x):
    try: return float(x)
    except (TypeError, ValueError): return np.nan

def load(run):
    d = root / run
    pts = list(csv.DictReader(open(d / "points.csv"))); fits = list(csv.DictReader(open(d / "fits.csv"))) if (d / "fits.csv").exists() else []
    rows = []
    for i, p in enumerate(pts):
        f = fits[i] if i < len(fits) else {}
        r = {k: num(v) for k, v in p.items() if k not in ("gpu_rpm", "load_mode")}
        for t in NAMES:
            m60, tinf, ci = num(f.get(f"{t}_mean60")), num(f.get(f"{t}_tinf")), num(f.get(f"{t}_tinf_ci95"))
            ok = np.isfinite(tinf) and np.isfinite(ci) and ci <= 2 and np.isfinite(m60) and abs(tinf - m60) <= 8
            r[f"{t}_est"] = tinf if ok else (m60 if np.isfinite(m60) else r.get(f"{t}_c", np.nan))
            r[f"{t}_m60"], r[f"{t}_tinf"], r[f"{t}_tau"], r[f"{t}_err"], r[f"{t}_fitok"] = m60, tinf, num(f.get(f"{t}_tau_s")), num(f.get(f"{t}_tinf_err")), ok
            r[f"R_{t}_est"] = (r[f"{t}_est"] - r["intake_c"]) / r["power_w"] if r["power_w"] > 50 else np.nan
        r["full"], r["ref"] = num(f.get("full")), num(f.get("ref"))
        rows.append(r)
    return rows, json.load(open(d / "conditions.json"))

summary = {}
v2, c2 = load("2026-10-20-gpu-map-v2d")
grid = [r for r in v2 if r.get("bridge", 0) == 0 and r["too_hot"] == 0]
allp = [r for r in v2 if r["too_hot"] == 0]   # mostki też są pomiarem (krótszym) — do mapy τ i wykresów

# ── 1/R = h0 + a·rg^0.8 + b·rc^0.8 + c·rg^0.8·rc^0.8 (v2d, 575 W) ──
def X(rg, rc): a, b = np.power(rg, 0.8), np.power(rc, 0.8); return np.column_stack([np.ones_like(a), a, b, a * b])
fit = {}
fitset = grid   # tylko punkty siatki (mostki 30 s są nieustalone)
rg_all = np.array([r["gpu_rpm_mean"] for r in fitset]); rc_all = np.array([r["case_rpm"] for r in fitset])
for t in NAMES:
    R = np.array([r[f"R_{t}_est"] for r in fitset]); m = np.isfinite(R) & np.isfinite(rg_all) & np.isfinite(rc_all) & (R > 0)
    A = X(rg_all[m], rc_all[m]); y = 1 / R[m]; co, *_ = np.linalg.lstsq(A, y, rcond=None)
    T = np.array([r[f"{t}_est"] for r in fitset])[m]; ia = np.array([r["intake_c"] for r in fitset])[m]; P = np.array([r["power_w"] for r in fitset])[m]
    That = ia + P / (A @ co); r2 = 1 - np.sum((y - A @ co) ** 2) / np.sum((y - y.mean()) ** 2)
    fit[t] = {"h0": co[0], "a": co[1], "b": co[2], "c": co[3], "r2_invR": r2, "n": int(m.sum()), "rmse_c": float(np.sqrt(np.mean((T - That) ** 2))), "max_err_c": float(np.max(np.abs(T - That)))}
summary["fit_v2d"] = fit

fg = np.array([r["fg_pct"] for r in allp]); fc = np.array([r["fc_pct"] for r in allp])
fg_f = np.array([r["fg_pct"] for r in fitset]); fc_f = np.array([r["fc_pct"] for r in fitset])
rg_of = np.poly1d(np.polyfit(fg_f, rg_all, 2)); rc_of = np.poly1d(np.polyfit(fc_f, rc_all, 2))
G, C = np.meshgrid(np.linspace(fg.min(), 100, 60), np.linspace(fc.min(), 100, 60))
RG, RC = np.clip(rg_of(G), 1, None), np.clip(rc_of(C), 1, None)
ia_m, P_m = np.nanmean([r["intake_c"] for r in allp]), np.nanmean([r["power_w"] for r in allp])
skipped = list(csv.DictReader(open(root / "2026-10-20-gpu-map-v2d" / "skipped.csv"))) if (root / "2026-10-20-gpu-map-v2d" / "skipped.csv").exists() else []
for t in NAMES:
    k = fit[t]; Ts = ia_m + P_m / (k["h0"] + k["a"] * RG ** 0.8 + k["b"] * RC ** 0.8 + k["c"] * RG ** 0.8 * RC ** 0.8)
    v = np.array([r[f"{t}_est"] for r in allp])
    fig = plt.figure(figsize=(8, 6)); ax = fig.add_subplot(projection="3d")
    ax.plot_surface(G, C, Ts, cmap="viridis", alpha=0.7, linewidth=0); ax.scatter(fg, fc, v, color="k", s=10)
    ax.set_xlabel("GPU fans %"); ax.set_ylabel("Case fans %"); ax.set_zlabel(f"{NAMES[t]} °C")
    ax.set_title(f"{NAMES[t]} at {P_m:.0f} W, intake {ia_m:.1f} °C — fit ±{k['rmse_c']:.1f} °C (R² of 1/R {k['r2_invR']:.3f})", fontsize=9)
    fig.tight_layout(); fig.savefig(out / f"surface-{t}.png", dpi=150); plt.close(fig)
    fig, ax = plt.subplots(figsize=(9, 6.5))
    cs = ax.contourf(G, C, Ts, levels=14, cmap="inferno"); fig.colorbar(cs, label=f"{NAMES[t]} °C (model)", pad=0.14)
    il = ax.contour(G, C, RG, levels=[1000, 1400, 1800, 2200, 2600, 3000], colors="c", linestyles="--", linewidths=0.8); ax.clabel(il, fmt="%d rpm", fontsize=7)
    ax.scatter(fg, fc, c="w", edgecolors="k", s=16, zorder=3, label="measured")
    if skipped: ax.scatter([num(s["fg_pct"]) for s in skipped], [num(s["fc_pct"]) for s in skipped], marker="x", c="r", s=40, zorder=4, label="skipped: unsafe at 575 W")
    ax.set_xlabel("GPU fans %"); ax.set_ylabel("Case fans %"); ax.set_title(f"{NAMES[t]} — measured points, model, iso-rpm (GPU fans)", pad=28); ax.legend(loc="lower right", fontsize=8)
    # (Seb 2026-10-21) obroty obok procentów: górna oś = rpm wentylatorów karty, prawa = rpm wentylatorów obudowy (z dopasowania % → rpm)
    xs, ys = np.linspace(0, 100, 201), np.linspace(0, 100, 201)
    gx, cy = rg_of(xs), rc_of(ys)
    top = ax.secondary_xaxis("top", functions=(lambda v: np.interp(v, xs, gx), lambda v: np.interp(v, gx, xs)))
    top.set_xlabel("GPU fans rpm"); top.set_xticks([int(round(rg_of(v), -1)) for v in (30, 40, 50, 60, 70, 80, 90, 100)])
    right = ax.secondary_yaxis("right", functions=(lambda v: np.interp(v, ys, cy), lambda v: np.interp(v, cy, ys)))
    right.set_ylabel("Case fans rpm"); right.set_yticks([int(round(rc_of(v), -1)) for v in (15, 30, 50, 70, 100)])
    fig.tight_layout(); fig.savefig(out / f"heatmap-{t}.png", dpi=150); plt.close(fig)

# ── τ map (hot spot, well-determined fits) ──
tm = [(r["fg_pct"], r["fc_pct"], r["hot_tau"]) for r in allp if r["hot_fitok"] and np.isfinite(r["hot_tau"]) and r["hot_tau"] < 900]
if tm:
    a = np.array(tm); fig, ax = plt.subplots(figsize=(8, 5.5)); sc = ax.scatter(a[:, 0], a[:, 1], c=a[:, 2], cmap="viridis", s=60, edgecolors="k")
    fig.colorbar(sc, label="hot-spot time constant τ (s)"); ax.set_xlabel("GPU fans %"); ax.set_ylabel("Case fans %")
    ax.set_title(f"Hot-spot step-response τ (median {np.median(a[:, 2]):.0f} s, n = {len(a)})"); fig.tight_layout(); fig.savefig(out / "tau-map.png", dpi=150); plt.close(fig)
    summary["tau_hot_s"] = {"median": float(np.median(a[:, 2])), "p10": float(np.percentile(a[:, 2], 10)), "p90": float(np.percentile(a[:, 2], 90)), "n": len(a)}

# ── validation: 60 s T∞ vs steady (full points) and reference repeatability ──
val = {}
for t in NAMES:
    e = np.array([r[f"{t}_err"] for r in v2 if r["full"] == 1 and np.isfinite(r[f"{t}_err"]) and r[f"{t}_fitok"]])
    e_all = np.array([r[f"{t}_err"] for r in v2 if r["full"] == 1 and np.isfinite(r[f"{t}_err"])])
    val[t] = {"n_wellfit": int(len(e)), "mae_wellfit_c": float(np.mean(np.abs(e))) if len(e) else None, "max_wellfit_c": float(np.max(np.abs(e))) if len(e) else None,
              "n_all": int(len(e_all)), "mae_all_c": float(np.mean(np.abs(e_all))) if len(e_all) else None}
refs = [r for r in v2 if r["ref"] == 1]
summary["validation_tinf60_vs_steady"] = val
summary["reference_point"] = {"n": len(refs), **{f"{t}_c": [round(r[f"{t}_c"], 2) for r in refs] for t in NAMES}, **{f"R_{t}": [round(r[f"R_{t}"], 5) for r in refs] for t in NAMES},
                              "intake_c": [r["intake_c"] for r in refs]}

# ── intake drift over the night (all runs' raw.csv) ──
fig, ax = plt.subplots(figsize=(10, 3.5)); t0 = None; drift = {}
for run in sorted(p.name for p in root.iterdir() if p.is_dir() and (p / "raw.csv").exists() and ("v2d" in p.name or "v3d" in p.name or "v4d" in p.name)):
    rr = list(csv.DictReader(open(root / run / "raw.csv"))); t = np.array([num(r["t"]) for r in rr]); ia = np.array([num(r["intake_c"]) for r in rr]); m = np.isfinite(t) & np.isfinite(ia)
    if m.sum() < 60: continue
    t0 = t0 or t[m][0]; ax.plot((t[m] - t0) / 3600, ia[m], lw=0.7, label=run.replace("2026-10-20-gpu-map-", ""))
    drift[run] = {"slope_c_per_h": float(np.polyfit((t[m] - t[m][0]) / 3600, ia[m], 1)[0]), "min": float(ia[m].min()), "max": float(ia[m].max())}
ax.set_xlabel("hours since v2d start"); ax.set_ylabel("intake air °C"); ax.legend(fontsize=8); ax.set_title("Intake air over the night (open-top case)")
fig.tight_layout(); fig.savefig(out / "intake-drift.png", dpi=150); plt.close(fig); summary["intake_drift"] = drift

# ── v3d: performance vs power limit and °C vs performance ──
if not (root / "2026-10-20-gpu-map-v3d-pl" / "points.csv").exists():
    json.dump(summary, open(out / "night-summary.json", "w"), indent=1, default=float); print(json.dumps(summary, indent=1, default=float)[:6000]); print("v3d points.csv missing — stop"); sys.exit(0)
v3, c3 = load("2026-10-20-gpu-map-v3d-pl")
v3g = [r for r in v3 if r.get("bridge", 0) == 0 and r["too_hot"] == 0]
pls = sorted({r["pl_w"] for r in v3g if np.isfinite(r["pl_w"])}, reverse=True)
perf = []
for w in pls:
    s = [r for r in v3g if r["pl_w"] == w]
    perf.append({"pl_w": w, "pl_pct": s[0].get("pl_pct"), "enforced_w": float(np.nanmedian([r["enforced_limit_w"] for r in s])), "power_w": float(np.nanmedian([r["power_w"] for r in s])),
                 "tflops": float(np.nanmedian([r["load_tflops"] for r in s])), "gbs": float(np.nanmedian([r["load_gbs"] for r in s])), "n": len(s),
                 "hot_at_fg100_fc100": next((r["hot_est"] for r in s if r["fg_pct"] == 100 and r["fc_pct"] == 100), None),
                 "hot_at_fg30_fcmin": next((r["hot_est"] for r in s if r["fg_pct"] == 30 and r["fc_pct"] == min(x["fc_pct"] for x in s)), None)})
summary["v3_perf_vs_pl"] = perf
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.8))
P = [p["power_w"] for p in perf]; TF = [p["tflops"] for p in perf]; GB = [p["gbs"] for p in perf]
a1.plot([p["pl_w"] for p in perf], [x / TF[0] * 100 for x in TF], "-o", label="FP32 throughput"); a1.plot([p["pl_w"] for p in perf], [x / GB[0] * 100 for x in GB], "-s", label="VRAM traffic")
a1.plot([p["pl_w"] for p in perf], [x / P[0] * 100 for x in P], "--", c="gray", label="board power")
for p in perf: a1.annotate(f"{p['enforced_w']:.0f} W enforced", (p["pl_w"], p["tflops"] / TF[0] * 100), fontsize=7, xytext=(4, -10), textcoords="offset points")
a1.set_xlabel("power limit set (W)"); a1.set_ylabel("% of 575 W value"); a1.set_title("Performance vs power limit"); a1.legend(fontsize=8); a1.invert_xaxis()
for fgv, mk in ((100, "o"), (70, "s"), (50, "^"), (30, "v")):
    for fcv in sorted({r["fc_pct"] for r in v3g}, reverse=True)[:1]:
        s = sorted([r for r in v3g if r["fg_pct"] == fgv and r["fc_pct"] == fcv], key=lambda r: -r["pl_w"])
        if s: a2.plot([r["load_tflops"] for r in s], [r["hot_est"] for r in s], "-" + mk, label=f"GPU fans {fgv} %, case {fcv:.0f} %")
a2.set_xlabel("FP32 TFLOPS (our load)"); a2.set_ylabel("hot spot °C (steady estimate)"); a2.set_title("°C vs performance as the power limit drops"); a2.legend(fontsize=8)
fig.tight_layout(); fig.savefig(out / "v3-perf-vs-pl.png", dpi=150); plt.close(fig)

# ── v4d frontier ──
fr_path = root / "2026-10-20-gpu-map-v4d-trace" / "frontier.csv"
if fr_path.exists():
    fr = list(csv.DictReader(open(fr_path))); summary["v4_frontier_rows"] = len(fr)
    best = {}
    for r in fr:
        key = (r["case_pct"], r["fg_pct"]); best[key] = max(best.get(key, 0), num(r["pl_pct"]))
    summary["v4_frontier_highest_pl_pct"] = {f"case {k[0]} % / GPU {k[1]} %": v for k, v in sorted(best.items(), key=lambda kv: (-num(kv[0][0]), -num(kv[0][1])))}
json.dump(summary, open(out / "night-summary.json", "w"), indent=1, default=float)
print(json.dumps(summary, indent=1, default=float)[:6000])
