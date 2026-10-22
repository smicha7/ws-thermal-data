"""Dynamic grey-box thermal model of the RTX 5090 core (+ memory) from 1 Hz logs.

Cauer RC ladders, inputs P(t) board W, N(t) GPU fan rpm, C(t) case rpm, Tin(t) intake air:
  M1  1 node   C dT/dt = P - (T - Tin)/(r0 + Rf)
  M2  2 node   die Tj --Rjs-- sink Ts --(ra + Rf)-- Tin       (Cj, Cs)
  M3  3 node   die Tj --Rjs-- spreader Tp --Rps-- fins Ts --(ra + Rf)-- Tin   (Cj, Cp, Cs)
Fan law Rf(N, C) = f(n) * (C/1500)^-q, n = Ne/1000, Ne = sqrt(N^2 + 300^2) (300 rpm floor = fan stop at idle):
  pow   f = k n^-m                        (static-model form)
  sat   f = k / (n^m + s^m)               (saturates at low airflow)
  conv  f = k n^-m + kc / n               (convection h ~ N^m + caloric 1/(m_dot cp) ~ 1/N)
core = Tj + theta0 (theta0 fitted to test whether it vanishes)
memory: tau_m dTm/dt = Tin + lam*(Ts - Tin) + a1*P + a0*load + thm - Tm   (Ts = sink node, load = util > 50 %;
        fitted after the core on grid1c + log-1, because grid1c has no idle data to separate thm from a0)
Discretisation: exact matrix exponential per 1 s step, inputs held at the step midpoint (L-stable, so a
near-instant die node does not ring). Fit = least squares on SIMULATED trajectories (free run, no resets).
Train: grid1c. Test: log-1, grid1d, hold, whole night v2d run (+ val1 if present). Steady: night v2d points.
Run:  .venv/bin/python dyn_model.py        (self-check runs first)
"""
import csv, glob, itertools, json, os, zlib
import numpy as np
from scipy.linalg import expm
from scipy.optimize import least_squares
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results-2026-10-21")
NIGHT = os.path.join(HERE, "data", "experiments-2026-10-21", "2026-10-20-gpu-map-v2d")
N0 = 300.0


# ---------------------------------------------------------------- data
def _nvapi_core(d):
    """0.01 degC core (nvapi/0/1) from the long log; tolerates truncated gzip."""
    out = {}
    for fn in sorted(glob.glob(os.path.join(d, "long-*.csv.gz"))):
        txt = zlib.decompressobj(31).decompress(open(fn, "rb").read()).decode(errors="ignore")
        for line in txt.splitlines():
            if ",nvapi/0/1," in line:
                p = line.split(",")
                try:
                    out[int(p[0])] = float(p[-2])
                except ValueError:
                    pass
    return out


def load(name, d=None):
    d = d or os.path.join(HERE, "data", f"{name}-2026-10-21")
    rows = list(csv.DictReader(open(os.path.join(d, "raw.csv"))))
    tt = np.array([int(r["t"]) for r in rows])
    gaps = np.where(np.diff(tt) > 20)[0]                               # logger restarts: keep the part after the last one
    if len(gaps):
        rows = rows[gaps[-1] + 1:]
    nv = _nvapi_core(d)
    t = np.array([int(r["t"]) for r in rows], float)
    f = lambda k: np.array([float(r[k]) for r in rows])
    cols = dict(P=f("power_w"), C=f("case_rpm"), Tin=f("intake_c"), mem=f("mem_c"), load=(f("util_pct") > 50).astype(float),
                core=np.array([nv.get(int(r["t"]), float(r["core_c"])) for r in rows]),
                N=np.array([np.mean([float(v) for v in r["gpu_rpm"].split("|")]) for r in rows]))
    for k, (lo, hi) in {"Tin": (10, 35), "C": (200, 3500)}.items():   # aquaero dropouts (0, 282.6, 30066)
        ok = (cols[k] >= lo) & (cols[k] <= hi)
        cols[k] = np.interp(t, t[ok], cols[k][ok])
    tg = np.arange(t[0], t[-1] + 1)                                    # 1 s grid over 2-3 s logging gaps
    D = {k: np.interp(tg, t, v) for k, v in cols.items()}
    D.update(t=tg - tg[0], t0=tg[0], name=name, rows=rows, traw=t)
    return D


# ---------------------------------------------------------------- model
BASE = {1: dict(r0=0.03, Cj=3000), 2: dict(Rjs=0.02, ra=0.01, Cj=200, Cs=3000),
        3: dict(Rjs=0.015, Rps=0.01, ra=0.01, Cj=50, Cp=500, Cs=3000)}
FORM = {"pow": dict(k=0.09, m=1.6), "sat": dict(k=0.2, m=2.0, s=0.8), "conv": dict(k=0.05, m=0.8, kc=0.03)}
LIN = dict(m=(0.2, 4.0), q=(0.0, 1.5), th0=(-15.0, 15.0), qa=(0.0, 3.0))       # linear params; all others log in [1e-5, 1e6]


def spec(kind, form, theta="free"):
    """theta: free = constant offset th0; zero = none; drift = slow intake offset
    tau_a dtheta/dt = th0 + phi*P*(C/1500)^-qa - theta  (case air warmed by the card's own heat)."""
    s = {**BASE[kind], **FORM[form], "q": 0.3, "th0": 0.0}
    if theta == "drift":
        s.update(phi=0.003, qa=0.5, taua=300.0)
    return s


def drift(p):
    return "taua" in p


def tin_eff(p, D):
    if not drift(p):
        return np.asarray(D["Tin"], float)
    tgt = p["th0"] + p["phi"] * np.asarray(D["P"], float) * (np.asarray(D["C"], float) / 1500.0) ** -p["qa"]
    a = np.exp(-1.0 / p["taua"]); th = np.empty_like(tgt); x = tgt[0]
    for i, g in enumerate(tgt.tolist()):
        th[i] = x; x = a * x + (1 - a) * g
    return np.asarray(D["Tin"], float) + th


def offset(p):
    return 0.0 if drift(p) else p["th0"]


def rfan(p, N, C):
    n = np.sqrt(np.asarray(N, float) ** 2 + N0 ** 2) / 1000.0
    form = p.get("form", "pow")
    if form == "pow":
        f = p["k"] * n ** -p["m"]
    elif form == "sat":
        f = p["k"] / (n ** p["m"] + p["s"] ** p["m"])
    else:
        f = p["k"] * n ** -p["m"] + p["kc"] / n
    return f * (np.asarray(C, float) / 1500.0) ** -p["q"]


def system(p, D, kind):
    """Per-sample A (n,K,K), b (n,K) of x' = A x + b; node 0 = die, last node = sink."""
    P, Tin = np.asarray(D["P"], float), np.asarray(D["Tin"], float)
    Ga = 1.0 / ((p["r0"] if kind == 1 else p["ra"]) + rfan(p, D["N"], D["C"]))
    caps = {1: ["Cj"], 2: ["Cj", "Cs"], 3: ["Cj", "Cp", "Cs"]}[kind]
    links = {1: [], 2: ["Rjs"], 3: ["Rjs", "Rps"]}[kind]
    K, n = len(caps), len(P)
    G = np.zeros((n, K, K))
    for i, name in enumerate(links):
        g = 1.0 / p[name]
        G[:, i, i] -= g; G[:, i + 1, i + 1] -= g; G[:, i, i + 1] += g; G[:, i + 1, i] += g
    G[:, K - 1, K - 1] -= Ga
    q = np.zeros((n, K)); q[:, 0] += P; q[:, K - 1] += Ga * Tin
    Cv = np.array([p[c] for c in caps])
    return G / Cv[None, :, None], q / Cv[None, :]


def simulate(A, b, x0):
    """x_{k+1} = Phi x_k + A^-1 (Phi - I) b with A, b at the step midpoint, dt = 1 s (exact for held inputs)."""
    n, K = b.shape
    Am, bm = 0.5 * (A[1:] + A[:-1]), 0.5 * (b[1:] + b[:-1])
    Phi = expm(Am)
    c = np.einsum("nij,nj->ni", Phi - np.eye(K), np.linalg.solve(Am, bm[..., None])[..., 0])
    X = np.empty((n, K)); X[0] = x0; x = np.asarray(x0, float)
    Phi, c = Phi.tolist(), c.tolist()
    if K == 2:                                                   # fast path
        a, b2 = x
        for i in range(n - 1):
            F, cc = Phi[i], c[i]
            a, b2 = F[0][0] * a + F[0][1] * b2 + cc[0], F[1][0] * a + F[1][1] * b2 + cc[1]
            X[i + 1, 0] = a; X[i + 1, 1] = b2
        return X
    for i in range(n - 1):
        F, cc = Phi[i], c[i]
        x = [sum(F[r][j] * x[j] for j in range(K)) + cc[r] for r in range(K)]
        X[i + 1] = x
    return X


def steady(A, b):
    return -np.linalg.solve(A, b)


def run(p, D, kind):
    A, b = system(p, dict(D, Tin=tin_eff(p, D)), kind)
    x0 = steady(A[0], b[0])
    x0 = x0 + (D["core"][0] - offset(p) - x0[0])         # start in equilibrium, shifted to the first reading
    return simulate(A, b, x0)


def core_pred(p, D, kind):
    X = run(p, D, kind)
    return X[:, 0] + offset(p), X


def steady_core(p, N, C, P, Tin, kind):
    """Steady core temperature for constant inputs."""
    N, C, P, Tin = (np.asarray(v, float) for v in (N, C, P, Tin))
    extra = p["th0"] + (p["phi"] * P * (C / 1500.0) ** -p["qa"] if drift(p) else 0.0)
    return Tin + extra + P * R_total(p, N, C, kind)


def R_total(p, N, C, kind):
    """(T_inf - Tin - theta0)/P = sum of ladder resistances."""
    s = p["r0"] if kind == 1 else p["Rjs"] + p.get("Rps", 0.0) + p["ra"]
    return s + rfan(p, N, C)


def fit_core(Ds, kind, form="pow", fixed=None, p0=None, theta="free", full=False):
    fixed = {**(fixed or {}), "form": form}
    if theta == "zero":
        fixed["th0"] = 0.0
    p0 = {**spec(kind, form, theta), **(p0 or {})}
    names = [k for k in spec(kind, form, theta) if k not in fixed]
    lo = np.array([LIN[k][0] if k in LIN else np.log(1e-5) for k in names])
    hi = np.array([LIN[k][1] if k in LIN else np.log(1e6) for k in names])
    unp = lambda v: {**fixed, **{k: (float(x) if k in LIN else float(np.exp(x))) for k, x in zip(names, v)}}
    v0 = np.clip([p0[k] if k in LIN else np.log(p0[k]) for k in names], lo + 1e-6, hi - 1e-6)
    res = lambda v: np.concatenate([core_pred(unp(v), D, kind)[0] - D["core"] for D in Ds])
    r = least_squares(res, v0, bounds=(lo, hi), x_scale="jac", max_nfev=300)
    return (unp(r.x), r, names) if full else unp(r.x)


# ---------------------------------------------------------------- memory node (after the core)
def mem_sim(pm, D, X):
    tgt = D["Tin"] + pm["lam"] * (X[:, -1] - D["Tin"]) + pm["a1"] * D["P"] + pm["a0"] * D["load"] + pm["thm"]
    a = np.exp(-1.0 / pm["tau"]); out = np.empty_like(tgt); x = D["mem"][0]
    for i in range(len(tgt)):
        out[i] = x; x = a * x + (1 - a) * tgt[i]
    return out


def fit_mem(Ds, Xs):
    unp = lambda v: dict(tau=float(np.exp(v[0])), lam=float(v[1]), a1=float(v[2]), a0=float(v[3]), thm=float(v[4]))
    res = lambda v: np.concatenate([mem_sim(unp(v), D, X) - D["mem"] for D, X in zip(Ds, Xs)])
    return unp(least_squares(res, [np.log(60), 1.0, 0.01, 15.0, 10.0], x_scale="jac").x)


# ---------------------------------------------------------------- self-check on synthetic data
def selfcheck():
    n = 3000; t = np.arange(n, dtype=float)
    D = dict(P=np.where(t < 1500, 500.0, 100.0), N=np.full(n, 1500.0), C=np.full(n, 1500.0), Tin=np.full(n, 20.0))
    D["P"][0] = 100.0
    p1 = dict(r0=0.03, k=0.09, m=1.6, q=0.3, Cj=2000.0, th0=0.0)
    R = R_total(p1, 1500.0, 1500.0, 1); tau = R * p1["Cj"]
    D["core"] = np.full(n, 20 + 100 * R)
    X = run(p1, D, 1)[:, 0]
    T1 = 20 + R * (300 - 200 * np.exp(-1 / tau))                 # step 0 holds the midpoint input (100+500)/2
    ana = 20 + R * 500 + (T1 - 20 - R * 500) * np.exp(-(t - 1) / tau)
    assert np.max(np.abs(X[1:1500] - ana[1:1500])) < 1e-6
    D["N"] = 1300 + 1200 * (np.sin(t / 200) > 0)                 # time-varying fan, vs fine explicit Euler
    for kind, p in ((2, dict(Rjs=0.02, ra=0.01, k=0.09, m=1.6, q=0.3, Cj=150.0, Cs=3000.0, th0=0.0)),
                    (3, dict(Rjs=0.015, Rps=0.01, ra=0.01, k=0.09, m=1.6, q=0.3, Cj=60.0, Cp=400.0, Cs=3000.0, th0=0.0))):
        X = run(p, D, kind); A, b = system(p, D, kind); x = X[0].copy(); ref = [x.copy()]
        for i in range(n - 1):
            for j in range(200):
                w = (j + 0.5) / 200
                x = x + 0.005 * (((1 - w) * A[i] + w * A[i + 1]) @ x + (1 - w) * b[i] + w * b[i + 1])
            ref.append(x.copy())
        err = np.abs(np.array(ref) - X)[:, 0]
        assert err.max() < 0.5 and np.sqrt(np.mean(err ** 2)) < 0.03, (kind, err.max())
        assert abs(steady(A[10], b[10])[0] - (20 + D["P"][10] * R_total(p, D["N"][10], 1500.0, kind))) < 1e-9
    for form in ("sat", "conv"):                                  # alternative fan laws are finite and decreasing
        r = rfan({**FORM[form], "q": 0.3, "form": form}, np.array([0.0, 1300, 3000]), 1500.0)
        assert np.all(np.isfinite(r)) and r[0] > r[1] > r[2] > 0
    print("self-check OK (1-node analytic, 2/3-node vs fine Euler, steady law, fan forms)")


# ---------------------------------------------------------------- night v2d points
def night_points(Dn, pc, kind):
    """Last-60 s mean per point; model-corrected steady value = meas + (T_inf_model - sim_mean)."""
    pts = list(csv.DictReader(open(os.path.join(NIGHT, "points.csv"))))
    fits = list(csv.DictReader(open(os.path.join(NIGHT, "fits.csv"))))
    yc, _ = core_pred(pc, Dn, kind)
    rows = Dn["rows"]
    segs = [list(g) for key, g in itertools.groupby(range(len(rows)), key=lambda i: (rows[i]["phase"], rows[i]["fg_set"], rows[i]["fc_set"]))
            if key[0] == "points"]
    assert len(segs) == len(pts)
    out = []
    for a, f, g in zip(pts, fits, segs):
        tend = Dn["traw"][g[-1]] - Dn["t0"]
        w = (Dn["t"] > tend - 60) & (Dn["t"] <= tend)
        N, C, P, Tin = (float(np.mean(Dn[k][w])) for k in ("N", "C", "P", "Tin"))
        Tss = Tin + pc["th0"] + P * float(R_total(pc, N, C, kind))
        meas, sim = float(np.mean(Dn["core"][w])), float(np.mean(yc[w]))
        out.append(dict(N=N, C=C, P=P, Tin=Tin, meas=meas, sim=sim, model_ss=Tss, corr_ss=meas + Tss - sim,
                        settled=f["core_steady"] != "", steady=float(f["core_steady"]) if f["core_steady"] else None))
    return out


def rmse(a, b=0.0):
    return float(np.sqrt(np.mean((np.asarray(a) - b) ** 2)))


def evaluate(p, kind, train, test):
    r = dict(params=p, train=rmse(core_pred(p, train[0], kind)[0], train[0]["core"]),
             test={D["name"]: rmse(core_pred(p, D, kind)[0], D["core"]) for D in test})
    r["test_pooled"] = rmse(np.concatenate([core_pred(p, D, kind)[0] - D["core"] for D in test]))
    # low-airflow bias check: mean residual where GPU fan <= 1350 rpm, P >= 560 W, after 120 s at that fan speed
    lb = []
    for D in [*train, *test]:
        e = core_pred(p, D, kind)[0] - D["core"]
        lowN = D["N"] <= 1350
        held = np.convolve(lowN, np.ones(120), "full")[:len(lowN)] >= 120
        lb.append(e[held & (D["P"] >= 560)])
    r["lowN_fullP_bias"] = float(np.mean(np.concatenate(lb)))
    return r


# ---------------------------------------------------------------- main
def main():
    selfcheck()
    train = [load("grid1c")]
    test = [load(n) for n in ("log-1", "grid1d", "hold")]
    Dn = load("night-v2d", NIGHT); test.append(Dn)
    if os.path.exists(os.path.join(HERE, "data", "val1-2026-10-21", "raw.csv")):
        test.append(load("val1"))
    day = [D for D in test if D["name"] != "night-v2d"]
    res, fits = {}, {}
    for kind in (1, 2, 3):
        for form in ("pow", "sat", "conv"):
            if kind == 1 and form != "pow":
                continue
            key = f"M{kind}-{form}"
            p = fit_core(train, kind, form); fits[key] = (kind, p)
            r = evaluate(p, kind, train, test); res[key] = r
            r["test_pooled_day"] = rmse(np.concatenate([core_pred(p, D, kind)[0] - D["core"] for D in day]))
            print(f"{key}: train {r['train']:.3f} test {({k: round(v, 3) for k, v in r['test'].items()})} "
                  f"pooled-day {r['test_pooled_day']:.3f} lowN bias {r['lowN_fullP_bias']:+.2f}")
            print("    ", {k: (round(v, 5) if isinstance(v, float) else v) for k, v in p.items()})
    best = min(fits, key=lambda k: res[k]["test_pooled_day"])
    kind, p = fits[best]
    p0 = fit_core(train, kind, p["form"], fixed=dict(th0=0.0), p0=p)
    r0 = evaluate(p0, kind, train, test)
    r0["test_pooled_day"] = rmse(np.concatenate([core_pred(p0, D, kind)[0] - D["core"] for D in day]))
    res[f"{best}_th0=0"] = r0
    print(f"{best} th0=0: train {r0['train']:.3f} test {r0['test']} pooled-day {r0['test_pooled_day']:.3f}")

    taus = {}
    for N in (1313, 1880, 2450, 3012):
        for C in (1000, 2920):
            A, _ = system(p, dict(P=[575.0], N=[N], C=[C], Tin=[19.0]), kind)
            taus[f"N{N}_C{C}"] = sorted((round(float(-1 / e), 2) for e in np.linalg.eigvals(A[0]).real), reverse=True)
    res["taus_s"] = taus; res["best"] = best
    print("tau [s]:", taus)

    mtrain = [train[0], test[0]]                                   # grid1c + log-1 (idle + load)
    pm = fit_mem(mtrain, [core_pred(p, D, kind)[1] for D in mtrain])
    res["mem"] = dict(params=pm, trained_on=["grid1c", "log-1"],
                      train=rmse(mem_sim(pm, train[0], core_pred(p, train[0], kind)[1]), train[0]["mem"]),
                      test={D["name"]: rmse(mem_sim(pm, D, core_pred(p, D, kind)[1]), D["mem"]) for D in test})
    print("mem:", pm, res["mem"]["train"], res["mem"]["test"])

    night = night_points(Dn, p, kind)
    st = [n for n in night if n["settled"]]
    res["night"] = dict(n=len(night), settled_n=len(st),
                        settled_rmse=rmse([n["model_ss"] - n["steady"] for n in st]),
                        settled_bias=float(np.mean([n["model_ss"] - n["steady"] for n in st])),
                        sim_vs_meas_last60_rmse=rmse([n["sim"] - n["meas"] for n in night]),
                        ss_vs_meas_naive_rmse=rmse([n["model_ss"] - n["meas"] for n in night]))
    print("night:", res["night"])
    json.dump(res, open(os.path.join(OUT, "dyn-model.json"), "w"), indent=1)

    # ------------------------------------------------ figures
    rpm2pct = lambda r: (np.asarray(r) - 1313) / (3012 - 1313) * 60 + 40
    pct2rpm = lambda q: (np.asarray(q) - 40) / 60 * (3012 - 1313) + 1313
    k1, p1 = fits["M1-pow"]

    D = train[0]; yc, X = core_pred(p, D, kind); ym = mem_sim(pm, D, X); y1 = core_pred(p1, D, 1)[0]
    fig, ax = plt.subplots(4, 1, figsize=(15, 11), sharex=True, gridspec_kw=dict(height_ratios=[3, 3, 1.3, 1.3]))
    tm = D["t"] / 60
    ax[0].plot(tm, D["core"], color="0.2", lw=0.8, label="core measured (NVAPI 0.01 °C)")
    ax[0].plot(tm, yc, color="tab:red", lw=0.9, label=f"{best} simulated, free run (RMSE {rmse(yc, D['core']):.2f} °C)")
    ax[0].plot(tm, y1, color="tab:blue", lw=0.6, alpha=0.6, label=f"M1 1-node (RMSE {rmse(y1, D['core']):.2f} °C)")
    ax[0].set_ylabel("core °C"); ax[0].legend(loc="lower right", fontsize=8)
    ax[1].plot(tm, D["mem"], color="0.2", lw=0.8, label="memory measured (1 °C steps)")
    ax[1].plot(tm, ym, color="tab:purple", lw=0.9, label=f"memory node (RMSE {rmse(ym, D['mem']):.2f} °C)")
    ax[1].set_ylabel("memory °C"); ax[1].legend(loc="lower right", fontsize=8)
    ax[2].plot(tm, yc - D["core"], color="tab:red", lw=0.6); ax[2].axhline(0, color="0.5", lw=0.5)
    ax[2].set_ylabel("core sim−meas °C")
    ax[3].plot(tm, D["P"], color="tab:orange", lw=0.6); ax[3].set_ylabel("board W", color="tab:orange")
    a3 = ax[3].twinx(); a3.plot(tm, rpm2pct(D["N"]), color="tab:green", lw=0.6); a3.set_ylabel("GPU fan % (green)", fontsize=8)
    a3b = a3.secondary_yaxis(1.07, functions=(pct2rpm, rpm2pct)); a3b.set_ylabel("GPU fan rpm", fontsize=8)
    ax[3].set_xlabel("minutes since 13:55 (grid1c = training run)")
    fig.suptitle(f"RTX 5090 dynamic model {best} — grid1c, 1 Hz, simulated from the first sample (no resets)")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "dyn-a-grid1c.png"), dpi=130); plt.close(fig)

    fig, ax = plt.subplots(len(test), 1, figsize=(15, 3.4 * len(test)))
    for a, D in zip(ax, test):
        yc, X = core_pred(p, D, kind); ym = mem_sim(pm, D, X); tm = D["t"] / 60
        a.plot(tm, D["core"], color="0.2", lw=0.8, label="core measured")
        a.plot(tm, yc, color="tab:red", lw=0.9, label=f"core sim (RMSE {rmse(yc, D['core']):.2f} °C)")
        a.plot(tm, D["mem"], color="0.6", lw=0.8, label="memory measured")
        a.plot(tm, ym, color="tab:purple", lw=0.9, label=f"memory sim (RMSE {rmse(ym, D['mem']):.2f} °C)")
        note = " (memory node trained on it)" if D["name"] == "log-1" else ""
        a.set_title(f"TEST {D['name']} — core not fitted on it{note}; free-run simulation from the first sample", fontsize=10)
        a.set_ylabel("°C"); a.legend(fontsize=8, loc="lower right", ncol=2)
        b2 = a.twinx(); b2.plot(tm, rpm2pct(D["N"]), color="tab:green", lw=0.5, alpha=0.6); b2.set_ylabel("GPU fan % (green)", fontsize=8)
        b3 = b2.secondary_yaxis(1.06, functions=(pct2rpm, rpm2pct)); b3.set_ylabel("GPU fan rpm", fontsize=8)
    ax[-1].set_xlabel("minutes from start of log")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "dyn-b-test.png"), dpi=130); plt.close(fig)

    fig, ax = plt.subplots(figsize=(10.5, 6.5))
    Ng = np.linspace(1150, 3050, 200); cm = plt.get_cmap("viridis"); col = lambda C: cm((C - 600) / 2400)
    for C in (1000, 1500, 2000, 2920):
        ax.plot(Ng, 1000 * R_total(p, Ng, C, kind), color=col(C), lw=2, label=f"model, case {C} rpm")
    for n in night:
        ax.scatter(n["N"], 1000 * (n["corr_ss"] - n["Tin"] - p["th0"]) / n["P"], color=col(n["C"]), s=34, zorder=3)
        if n["settled"]:
            ax.scatter(n["N"], 1000 * (n["steady"] - n["Tin"] - p["th0"]) / n["P"], facecolor="none", edgecolor="k", s=90, lw=1.2, zorder=4)
    ax.scatter([], [], color="0.5", s=34, label="night v2d point (meas. + model transient correction)")
    ax.scatter([], [], facecolor="none", edgecolor="k", s=90, label="night v2d settled point (raw)")
    ax.set_xlabel("GPU fan rpm"); ax.set_ylabel("R_total = (T∞ − Tin − θ0) / P   [m°C/W]")
    sec = ax.secondary_xaxis("top", functions=(rpm2pct, pct2rpm)); sec.set_xlabel("GPU fan %")
    lo, hi = ax.get_ylim(); a2 = ax.twinx(); a2.set_ylim(lo * 0.575, hi * 0.575); a2.set_ylabel("T∞ − Tin − θ0 at 575 W  [°C]")
    fig.colorbar(plt.cm.ScalarMappable(cmap=cm, norm=plt.Normalize(600, 3000)), ax=a2, pad=0.12, label="case rpm")
    ax.legend(loc="upper right", fontsize=8)
    ax.set_title(f"Steady-state law from dynamic model {best} (θ0 = {p["th0"]:.2f} °C) vs night v2d")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "dyn-c-steady.png"), dpi=130); plt.close(fig)


if __name__ == "__main__":
    main()
