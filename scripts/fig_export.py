"""Article figures (site thread spec 2026-10-21): heatmap-hot / surface-hot / heatmap-core / heatmap-mem / v3-hotspot-vs-pl,
each as -light, -dark and -phone-light/-phone-dark. Usage: fig_export.py <experiments dir> <out dir>
Only the 34 grid cells are markers (bridges = small pale dots, labelled); one colour scale for hot spot across heatmap and surface;
model masked outside the measured area (left of the lowest measured GPU-fan setting per case level); no titles; sans 11–12 pt."""
import csv, json, re, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe

root, out = Path(sys.argv[1]), Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
sys.argv = [sys.argv[0], str(root), str(out / "_tmp")]
NAMES = {"core": "Core", "mem": "Memory", "hot": "Hot spot"}
def num(x):
    try: return float(x)
    except (TypeError, ValueError): return np.nan

# ── v2d points with the service's steady estimate ──
d = root / "2026-10-20-gpu-map-v2d"
pts = list(csv.DictReader(open(d / "points.csv"))); fits = list(csv.DictReader(open(d / "fits.csv")))
rows = []
for p, f in zip(pts, fits):
    r = {k: num(v) for k, v in p.items() if k not in ("gpu_rpm", "load_mode")}
    for t in NAMES:
        m60, tinf, ci = num(f.get(f"{t}_mean60")), num(f.get(f"{t}_tinf")), num(f.get(f"{t}_tinf_ci95"))
        ok = np.isfinite(tinf) and np.isfinite(ci) and ci <= 2 and np.isfinite(m60) and abs(tinf - m60) <= 8
        r[f"{t}_est"] = tinf if ok else m60
        r[f"R_{t}"] = (r[f"{t}_est"] - r["intake_c"]) / r["power_w"]
    rows.append(r)
grid = [r for r in rows if r["bridge"] == 0 and r["too_hot"] == 0]
bridges = [r for r in rows if r["bridge"] == 1 and r["too_hot"] == 0]
skipped = [(num(s["fg_pct"]), num(s["fc_pct"])) for s in csv.DictReader(open(d / "skipped.csv"))]

def X(rg, rc): a, b = np.power(rg, 0.8), np.power(rc, 0.8); return np.column_stack([np.ones_like(a), a, b, a * b])
rg = np.array([r["gpu_rpm_mean"] for r in grid]); rc = np.array([r["case_rpm"] for r in grid])
fg = np.array([r["fg_pct"] for r in grid]); fc = np.array([r["fc_pct"] for r in grid])
coef = {t: np.linalg.lstsq(X(rg, rc), 1 / np.array([r[f"R_{t}"] for r in grid]), rcond=None)[0] for t in NAMES}
rg_of = np.poly1d(np.polyfit(fg, rg, 2)); rc_of = np.poly1d(np.polyfit(fc, rc, 2))
ia, P = np.mean([r["intake_c"] for r in grid]), np.mean([r["power_w"] for r in grid])
G, C = np.meshgrid(np.linspace(30, 100, 141), np.linspace(fc.min(), 100, 121))
RG, RC = np.clip(rg_of(G), 1, None), np.clip(rc_of(C), 1, None)
# measured area: per case level the lowest measured GPU-fan setting (grid + bridges), interpolated over case %
meas = [(r["fg_pct"], r["fc_pct"]) for r in grid + bridges]
rowsfc = sorted({r["fc_pct"] for r in grid if len({q["fg_pct"] for q in grid if q["fc_pct"] == r["fc_pct"]}) >= 3})   # rzędy siatki (bez punktu odniesienia i mostków obudowy)
lv = rowsfc; lo = [min(g for g, c in meas if c == l) for l in lv]
edge = np.interp(C, lv, lo)
model = {t: np.where(G >= edge - 0.01, ia + P / (X(RG.ravel(), RC.ravel()) @ coef[t]).reshape(G.shape), np.nan) for t in NAMES}
rng = {t: (np.floor(np.nanmin(model[t])), np.ceil(np.nanmax(model[t]))) for t in NAMES}
rng["hot"] = (min(rng["hot"][0], 67.0), max(rng["hot"][1], 90.0))   # krytyk R5: dopasowane T∞ przy 40 % sięga 90 °C

THEMES = {"light": dict(bg="#ffffff", fg="#1d1d1f", grid="#d9d9de", dim="#86868b", iso="#3a3a3c", halo="#ffffff", bridge="#b0b0b5"),
          "dark": dict(bg="#141414", fg="#f5f5f7", grid="#3a3a3c", dim="#98989d", iso="#e5e5ea", halo="#141414", bridge="#5a5a5e")}
CMAP = "inferno"

def style(fig, ax, th, fs):
    fig.patch.set_facecolor(th["bg"]); ax.set_facecolor(th["bg"])
    for s in ax.spines.values(): s.set_visible(False)
    ax.tick_params(colors=th["fg"], labelsize=fs, length=0); ax.xaxis.label.set_color(th["fg"]); ax.yaxis.label.set_color(th["fg"])
    ax.grid(color=th["grid"], lw=0.6); ax.set_axisbelow(True)

# (Seb 2026-10-21) każdy wykres wentylatorów: % i obroty — górna oś = rpm wentylatorów karty, prawa = rpm wentylatorów obudowy (dopasowanie % → rpm)
_xs = np.linspace(25, 105, 200); _gx = rg_of(_xs); _ys = np.linspace(5, 105, 200); _cy = rc_of(_ys)
def RPMG(pct): return int(round(float(rg_of(pct)), -1))
def RPMC(pct): return int(round(float(rc_of(pct)), -1))
def dual(ax, th, fs):
    top = ax.secondary_xaxis("top", functions=(lambda v: np.interp(v, _xs, _gx), lambda v: np.interp(v, _gx, _xs)))
    top.set_xticks([RPMG(v) for v in (30, 50, 70, 90, 100)]); top.set_xlabel("GPU fans (rpm)", color=th["fg"])
    right = ax.secondary_yaxis("right", functions=(lambda v: np.interp(v, _ys, _cy), lambda v: np.interp(v, _cy, _ys)))
    right.set_yticks([RPMC(v) for v in (15, 36, 58, 79, 100)]); right.set_ylabel("Case fans (rpm)", color=th["fg"])
    for a in (top, right):
        a.tick_params(colors=th["fg"], labelsize=fs - 2, length=0)
        for sp in a.spines.values(): sp.set_visible(False)

def heatmap(t, theme, phone):
    th = THEMES[theme]; fs = 13 if phone else 12
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Arial", "DejaVu Sans"], "font.size": fs})
    fig, ax = plt.subplots(figsize=(5, 6.2) if phone else (8, 5.6)); style(fig, ax, th, fs)
    lo_, hi_ = rng["hot"] if t == "hot" else rng[t]
    cs = ax.contourf(G, C, model[t], levels=np.linspace(lo_, hi_, 15), cmap=CMAP)
    # unmeasured area: hatched, no colour
    ax.contourf(G, C, np.where(np.isnan(model[t]), 1, np.nan), levels=[0.5, 1.5], colors="none", hatches=["////"])
    for c in ax.collections[-1:]:
        try: c.set_edgecolor(th["grid"])
        except Exception: pass
    iso = ax.contour(G, C, RG, levels=[1200, 1600, 2000, 2400, 2800], colors=th["iso"], linestyles="--", linewidths=0.8)
    lbl = ax.clabel(iso, fmt="%d rpm", fontsize=fs - 2, inline=True)
    for l in lbl: l.set_color(th["iso"]); l.set_path_effects([pe.withStroke(linewidth=2.5, foreground=th["halo"])])
    ax.scatter([r["fg_pct"] for r in bridges], [r["fc_pct"] for r in bridges], s=6, c=th["bridge"], zorder=3, label="bridge steps (30 s)")
    ax.scatter(fg, fc, s=26 if phone else 34, c=th["bg"], edgecolors=th["fg"], linewidths=1, zorder=4, label="grid cell (34)")
    if skipped: ax.scatter([s[0] for s in skipped], [s[1] for s in skipped], marker="x", c="#ff453a", s=36, zorder=5, label="skipped in the run (predicted over a limit at 575 W)")
    ax.set_xlim(27, 101.5); ax.set_ylim(fc.min() - 3, 101.5)
    ax.set_xlabel("GPU fans (%)"); ax.set_ylabel("Case fans (%)")
    dual(ax, th, fs)
    cb = fig.colorbar(cs, ax=ax, pad=0.16, fraction=0.05) if not phone else fig.colorbar(cs, ax=ax, orientation="horizontal", pad=0.2, fraction=0.06, aspect=30)
    cb.outline.set_visible(False)
    cb.set_ticks(np.arange(np.ceil(lo_ / 3) * 3, hi_ + 0.1, 3 if not phone else 6))
    cb.set_label(f"{NAMES[t]} (°C, model)", color=th["fg"]); cb.ax.tick_params(colors=th["fg"], labelsize=fs - 1, length=0)
    if phone: cb.ax.xaxis.set_label_position("top")
    leg = ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.14 if not phone else -0.5), ncol=3 if not phone else 1, fontsize=fs - 2, frameon=False, labelcolor=th["fg"])
    fig.tight_layout(); name = f"heatmap-{t}{'-phone' if phone else ''}-{theme}.png"; fig.savefig(out / name, dpi=200, facecolor=th["bg"]); plt.close(fig); return name

def surface(theme, phone):
    th = THEMES[theme]; fs = 13 if phone else 12; t = "hot"
    fig = plt.figure(figsize=(5, 4) if phone else (8, 6)); fig.patch.set_facecolor(th["bg"])
    ax = fig.add_subplot(projection="3d"); ax.set_facecolor(th["bg"])
    lo_, hi_ = rng[t]
    ax.plot_surface(G, C, np.ma.masked_invalid(model[t]), cmap=CMAP, vmin=lo_, vmax=hi_, linewidth=0, alpha=0.9, rstride=2, cstride=2, antialiased=True)
    ax.scatter(fg, fc, [r[f"{t}_est"] for r in grid], c=th["fg"], s=10, depthshade=False)
    for a in (ax.xaxis, ax.yaxis, ax.zaxis):
        a.set_pane_color((0, 0, 0, 0)); a.label.set_color(th["fg"]); a._axinfo["grid"]["color"] = th["grid"]
    ax.tick_params(colors=th["fg"], labelsize=fs - 2)
    ax.set_xlabel("GPU fans (%)", fontsize=fs - 1); ax.set_ylabel("Case fans (%)", fontsize=fs - 1); ax.zaxis.set_rotate_label(False); ax.set_zlabel("Hot spot (°C)", fontsize=fs - 1, rotation=90)
    ax.set_zlim(lo_, hi_); ax.view_init(elev=24, azim=-128)
    fig.tight_layout(); name = f"surface-hot{'-phone' if phone else ''}-{theme}.png"; fig.savefig(out / name, dpi=200, facecolor=th["bg"]); plt.close(fig); return name

# ── v3d from the run log (points.csv not yet transferred) ──
log = open(root / "2026-10-20-gpu-map-v3d-pl" / "log.txt", encoding="utf-8").read()
rx = re.compile(r"punkt f_g (\d+) % · f_c (\d+) % · (\d+) W \(([\d.]+) %\): (\S+)[^·]*· rdzeń ([\d.]+) · pamięć ([\d.]+) · hot spot ([\d.]+) · ([\d.]+) W")
v3 = [dict(fg=int(m[1]), fc=int(m[2]), pl=int(m[3]), kind=m[5], hot=float(m[8]), w=float(m[9])) for m in rx.finditer(log)]
f3 = list(csv.DictReader(open(root / "2026-10-20-gpu-map-v3d-pl" / "fits.csv")))
for r, f in zip(v3, f3):
    m60, tinf, ci = num(f.get("hot_mean60")), num(f.get("hot_tinf")), num(f.get("hot_tinf_ci95"))
    r["hot_est"] = tinf if np.isfinite(ci) and ci <= 2 and np.isfinite(m60) and abs(tinf - m60) <= 8 else r["hot"]
# first point of every power level (GPU 100 / case 100) comes straight after the hottest cell of the previous level: still cooling → not settled, shown hollow
firsts = set()
for i, r in enumerate(v3):
    if i == 0 or v3[i - 1]["pl"] != r["pl"]: firsts.add(i)
for i in firsts: v3[i]["transient"] = True

def v3fig(theme, phone):
    th = THEMES[theme]; fs = 13 if phone else 12
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Arial", "DejaVu Sans"], "font.size": fs})
    fcs = [100, 50, 15]
    fig, axs = plt.subplots(3, 1, figsize=(5, 10.5), sharex=True) if phone else plt.subplots(1, 3, figsize=(14, 5.4), sharey=True)
    fig.patch.set_facecolor(th["bg"])
    cols = {100: "#0a84ff", 70: "#ff9f0a", 50: "#30d158", 30: "#ff453a"}
    for ax, fcv in zip(axs, fcs):
        style(fig, ax, th, fs)
        for fgv, mk in ((100, "o"), (70, "s"), (50, "^"), (30, "v")):
            s = [r for r in v3 if r["fg"] == fgv and r["fc"] == fcv and r["kind"] != "ZA"]
            ok = [r for r in s if not r.get("transient")]; bad = [r for r in s if r.get("transient")]
            ok.sort(key=lambda r: -r["w"])
            if ok: ax.plot([r["w"] for r in ok], [r["hot_est"] for r in ok], "-" + mk, c=cols[fgv], ms=6, lw=1.6, label=f"GPU fans {fgv} % ({RPMG(fgv)} rpm)")
            if bad: ax.scatter([r["w"] for r in bad], [r["hot_est"] for r in bad], marker=mk, facecolors="none", edgecolors=cols[fgv], s=40, zorder=5)
        ax.text(0.98, 0.97, f"case fans {fcv} % ({RPMC(fcv)} rpm)", transform=ax.transAxes, va="top", ha="right", color=th["fg"], fontsize=fs,
                bbox=dict(boxstyle="round,pad=0.3", fc=th["bg"], ec=th["grid"]))
        ax.set_xlim(585, 390); ax.set_ylabel("Hot spot (°C)")
    axs[-1].set_xlabel("Board power = power limit in force (W)")
    if not phone:
        for a in axs: a.set_xlabel("Board power = power limit in force (W)")
    h = [plt.Line2D([], [], marker=mk, c=cols[g], lw=1.6) for g, mk in ((100, "o"), (70, "s"), (50, "^"), (30, "v"))]; l = [f"GPU fans {g} % ({RPMG(g)} rpm)" for g in (100, 70, 50, 30)]
    h.append(plt.Line2D([], [], marker="o", ls="none", mfc="none", mec=th["dim"])); l.append("first point after a power-limit change (not settled)")
    fig.legend(h, l, loc="lower center", ncol=2 if phone else 5, fontsize=fs - 2, frameon=False, labelcolor=th["fg"])
    fig.tight_layout(rect=(0, 0.09 if phone else 0.1, 1, 1))
    name = f"v3-hotspot-vs-pl{'-phone' if phone else ''}-{theme}.png"; fig.savefig(out / name, dpi=200, facecolor=th["bg"]); plt.close(fig); return name

made = []
for theme in THEMES:
    for phone in (False, True):
        for t in NAMES: made.append(heatmap(t, theme, phone))
        made.append(surface(theme, phone)); made.append(v3fig(theme, phone))
json.dump({"hot_range_c": rng["hot"], "files": made}, open(out / "figures.json", "w"), indent=1)
print("\n".join(made))

# ── core vs memory (v2d grid; site spec 2026-10-21): limit lines with short labels, colour = GPU fans % (rpm on a second colourbar axis) ──
def corevsmem(theme, phone):
    th = THEMES[theme]; fs = 13 if phone else 12
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Arial", "DejaVu Sans"], "font.size": fs})
    core = np.array([r["core_c"] for r in grid]); mem = np.array([r["mem_c"] for r in grid]); g = np.array([r["fg_pct"] for r in grid])
    k, b = np.polyfit(core, mem, 1)
    fig, ax = plt.subplots(figsize=(5, 6.2) if phone else (8, 6)); style(fig, ax, th, fs)
    red = "#ff453a" if theme == "dark" else "#d13438"
    sc = ax.scatter(core, mem, c=g, cmap="viridis", s=34 if phone else 44, edgecolors=th["fg"], linewidths=0.6, zorder=4)
    xs = np.linspace(55, 98, 10); ax.plot(xs, k * xs + b, c=th["dim"], lw=1, zorder=2)
    ax.text(57, k * 57 + b + 1.0, f"mem ≈ {k:.2f}·core + {b:.1f}", color=th["dim"], fontsize=fs - 2)
    for x, ls, lw, lab in ((90, "-", 1.6, "core max operating 90"), (93, "--", 1.6, "core slowdown 93"), (96, "-", 3.2, "core shutdown 96")):
        ax.axvline(x, c=red, ls=ls, lw=lw, zorder=3)
        ax.text(x - 0.4, 61, lab, rotation=90, va="bottom", ha="right", color=red, fontsize=fs - 3, path_effects=[pe.withStroke(linewidth=2.5, foreground=th["bg"])])
    ax.axhline(100, c=red, ls="--", lw=1.6, zorder=3); ax.text(56, 100.4, "mem working limit 100 (derived)", color=red, fontsize=fs - 3, va="bottom")
    ax.axhline(88, c=th["dim"], lw=0.8, zorder=2); ax.text(56, 88.3, "first-night limit 88", color=th["dim"], fontsize=fs - 3, va="bottom")
    ax.set_xlim(55, 98); ax.set_ylim(60, 102.5); ax.set_xlabel("Core (°C)"); ax.set_ylabel("Memory (°C)")
    cb = fig.colorbar(sc, ax=ax, pad=0.14 if not phone else 0.26, fraction=0.05, orientation="vertical" if not phone else "horizontal", aspect=30)
    cb.outline.set_visible(False); cb.set_label("GPU fans (%)", color=th["fg"]); cb.ax.tick_params(colors=th["fg"], labelsize=fs - 2, length=0)
    ticks = [30, 50, 70, 90, 100]; cb.set_ticks([t for t in ticks if g.min() - 1 <= t <= 100])
    # druga oś paska: rpm (zasada Seba % + rpm)
    if not phone:
        r2 = cb.ax.secondary_yaxis("left", functions=(lambda v: np.interp(v, _xs, _gx), lambda v: np.interp(v, _gx, _xs)))
        r2.set_yticks([RPMG(t) for t in cb.get_ticks()]); r2.set_ylabel("GPU fans (rpm)", color=th["fg"])
    else:
        r2 = cb.ax.secondary_xaxis("top", functions=(lambda v: np.interp(v, _xs, _gx), lambda v: np.interp(v, _gx, _xs)))
        r2.set_xticks([RPMG(t) for t in cb.get_ticks()]); r2.set_xlabel("GPU fans (rpm)", color=th["fg"]); cb.ax.xaxis.set_label_position("bottom")
    r2.tick_params(colors=th["fg"], labelsize=fs - 3, length=0)
    for sp in r2.spines.values(): sp.set_visible(False)
    fig.tight_layout(); name = f"core-vs-mem{'-phone' if phone else ''}-{theme}.png"; fig.savefig(out / name, dpi=200, facecolor=th["bg"]); plt.close(fig); return name

for theme in THEMES:
    for phone in (False, True): print(corevsmem(theme, phone))

# ── surfaces.json dla interaktywnego rys. 3 (wątek strony 2026-10-21): ten sam model i maska co heatmapy, siatka ~25 × 25 ──
def surfaces_json():
    gs = np.round(np.linspace(30, 100, 29), 2); cs_ = np.round(np.linspace(fc.min(), 100, 25), 2)
    Gg, Cc = np.meshgrid(gs, cs_); rgg, rcc = np.clip(rg_of(Gg), 1, None), np.clip(rc_of(Cc), 1, None)
    edge2 = np.interp(Cc, lv, lo)
    def mdl(t, a, b): return ia + P / (X(np.atleast_1d(a), np.atleast_1d(b)) @ coef[t])
    lim = {"hot": [], "core": [90, 93, 96], "mem": [88]}
    out_ = {"meta": {"run": "2026-10-20-gpu-map-v2d", "power_w": round(float(P)), "intake_c": round(float(ia), 1),
                     "note": "model 1/R = h0 + a·rpm_g^0.8 + b·rpm_c^0.8 + c·(rpm_g·rpm_c)^0.8 fitted on the 34 grid cells; z = null outside the measured area"},
            "fg_pct": gs.tolist(), "fc_pct": cs_.tolist(), "rpm_g": [round(float(v)) for v in rg_of(gs)], "rpm_c": [round(float(v)) for v in rc_of(cs_)], "sensors": {},
            "skipped": [{"fg": a, "fc": b} for a, b in skipped]}
    for t in ("hot", "core", "mem"):
        z = mdl(t, rgg.ravel(), rcc.ravel()).reshape(Gg.shape); z = np.where(Gg >= edge2 - 0.01, z, np.nan)
        pts = [{"fg": r["fg_pct"], "fc": r["fc_pct"], "rg": round(r["gpu_rpm_mean"]), "rc": round(r["case_rpm"]), "t": round(r[f"{t}_est"], 1),
                "model": round(float(mdl(t, r["gpu_rpm_mean"], r["case_rpm"])[0]), 1), "ref": r["fg_pct"] == 55 and r["fc_pct"] not in lv} for r in grid]
        out_["sensors"][t] = {"z": [[None if np.isnan(v) else round(float(v), 1) for v in row] for row in z], "points": pts, "limits": lim[t], "range": [float(rng[t][0]), float(rng[t][1])]}
    json.dump(out_, open(out / "surfaces.json", "w"), separators=(",", ":"))
    return "surfaces.json"
print(surfaces_json())

# ── zegar grafiki vs wentylatory karty (akapit „Clocks”, wątek strony 2026-10-21): 34 komórki siatki, kolor = poziom obudowy (% i rpm) ──
def clockfig(theme, phone):
    th = THEMES[theme]; fs = 13 if phone else 12
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Arial", "DejaVu Sans"], "font.size": fs})
    fig, ax = plt.subplots(figsize=(5, 5.6) if phone else (8, 5.2)); style(fig, ax, th, fs)
    cmap = plt.get_cmap("viridis"); levels = [15, 36, 58, 79, 100]
    for i, c in enumerate(levels):
        pts_ = [r for r in grid if round(r["fc_pct"]) == c]
        if pts_: ax.scatter([r["fg_pct"] for r in pts_], [r["clock_mhz"] for r in pts_], s=40 if not phone else 32, color=cmap(i / (len(levels) - 1)), edgecolors=th["fg"], linewidths=0.6, zorder=4, label=f"case {c} % ({RPMC(c)} rpm)")
    ref = [r for r in grid if round(r["fc_pct"]) not in levels]
    if ref: ax.scatter([r["fg_pct"] for r in ref], [r["clock_mhz"] for r in ref], s=40 if not phone else 32, marker="D", facecolors="none", edgecolors=th["fg"], zorder=4, label=f"reference 55 % / case {round(ref[0]['fc_pct'])} % (×{len(ref)})")
    xs_ = np.array([r["fg_pct"] for r in grid]); ys_ = np.array([r["clock_mhz"] for r in grid]); k, b = np.polyfit(xs_, ys_, 1); rr = np.corrcoef(xs_, ys_)[0, 1]
    xl = np.linspace(xs_.min(), 100, 10); ax.plot(xl, k * xl + b, c=th["dim"], lw=1, zorder=2)
    ax.text(0.02, 0.97, f"+{k * 10:.0f} MHz per +10 % GPU fans (r = {rr:.2f})", transform=ax.transAxes, va="top", color=th["dim"], fontsize=fs - 2)
    ax.set_xlabel("GPU fans (%)"); ax.set_ylabel("Graphics clock (MHz)")
    top = ax.secondary_xaxis("top", functions=(lambda v: np.interp(v, _xs, _gx), lambda v: np.interp(v, _gx, _xs)))
    top.set_xticks([RPMG(v) for v in (40, 60, 80, 100)]); top.set_xlabel("GPU fans (rpm)", color=th["fg"]); top.tick_params(colors=th["fg"], labelsize=fs - 2, length=0)
    for sp in top.spines.values(): sp.set_visible(False)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=1 if phone else 3, fontsize=fs - 3, frameon=False, labelcolor=th["fg"])
    fig.tight_layout(); name = f"clock-vs-fan{'-phone' if phone else ''}-{theme}.png"; fig.savefig(out / name, dpi=200, facecolor=th["bg"]); plt.close(fig); return name
for theme in THEMES:
    for phone in (False, True): print(clockfig(theme, phone))
