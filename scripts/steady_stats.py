# Model STANU USTALONEGO rdzenia RTX 5090 z pełną diagnostyką reszt (ekonometria).
#   1) postaci kandydujące (potęga, wykładnik, wymierna, przewodność, log-log, R = (T−Tin)/P, splajn naturalny)
#      × efekt sesji; porównanie AIC/BIC (na skali T − Tin, z jakobianem przekształceń), LOO, 5-krotna CV, LOSO;
#   2) dla wybranego modelu: DW, Breusch–Godfrey, Breusch–Pagan, White, Shapiro–Wilk, Jarque–Bera, RESET,
#      brak dopasowania (czysty błąd z powtórzeń), Box–Cox (transform-both-sides), SE klasyczne / HC3 / klaster,
#      efekt sesji stały i losowy (MixedLM);
#   3) rysunki diagnostyczne i wykres „w obie strony”.
# Uruchamia się na wszystkich plikach, jakie są (steady_data.py); steady2 staje się zbiorem głównym, gdy istnieje.
# Jednostki: °C, opory w m°C/W. Wyniki: results-2026-10-22/.
import json, os, subprocess, sys, warnings
import numpy as np, pandas as pd, patsy
from scipy import stats, optimize
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan, het_white
from statsmodels.stats.stattools import durbin_watson, jarque_bera
from statsmodels.tsa.stattools import acf
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")
OUT = "results-2026-10-22/"
subprocess.run([sys.executable, "steady_data.py"], check=True, stdout=subprocess.DEVNULL)
D = pd.read_csv(OUT + "steady-points.csv")
CORE = os.environ.get("CORE", "core_settled")  # core_settled = NVAPI 0,01 °C ekstrapolowany do T∞; core = NVAPI średnia 60 s; core_tab = NVML całe °C
SESS_GROUPS = {"grid1c": "afternoon", "grid1d": "afternoon"}   # sesje jednopunktowe łączymy (popołudnie 21.10)
D["grp"] = D.session.map(lambda s: SESS_GROUPS.get(s, s))
HAS_S2 = (D.session == "steady2").sum() >= 20
PRIMARY = "steady2" if HAS_S2 else "pooled"
# Zbiór estymacji: wszystkie sesje (efekt sesji w modelu). steady2, gdy jest, ma pierwszeństwo jako sesja odniesienia.
REF = "steady2" if HAS_S2 else "val1"
SUBSET = os.environ.get("SUBSET")            # np. SUBSET=steady2 -> analiza tylko tej sesji
if SUBSET: D = D[D.session == SUBSET]; REF = SUBSET
TAG = ("" if CORE == "core_settled" else "-" + CORE) + (f"-{SUBSET}" if SUBSET else "")
D = D.reset_index(drop=True)
y = (D[CORE] - D.Tin).to_numpy(); n_ = D.N.to_numpy() / 1000; c_ = D.C.to_numpy() / 1500; P = D.P.to_numpy()
groups = [g for g in [REF] + sorted(set(D.grp) - {REF})]
S = np.column_stack([(D.grp == g).to_numpy(float) for g in groups[1:]]) if len(groups) > 1 else np.zeros((len(D), 0))   # dummies (odniesienie = REF)
gid = D.grp.map({g: i for i, g in enumerate(groups)}).to_numpy()
t_h = (D.ts_end.to_numpy() - D.ts_end.min()) / 3600
N = len(y)
SER = list(zip((np.round(D.C / 250) * 250).astype(int), D.pl_pct))   # seria (obudowa, PL) — kolejność po N
ser_id = pd.factorize(pd.Series([f"{a}/{b}" for a, b in SER]))[0]


# ---------------------------------------------------------------- modele
# Każdy model: response ∈ {y, lny, R}, f(p, X) -> średnia na skali odpowiedzi BEZ efektu sesji, p0, nazwy.
def R_pow(p, n, c):  r, k, m, q = p; return r + k * n**-m * c**-q
def R_exp(p, n, c):  r, k, a, q = p; return r + k * np.exp(-a * n) * c**-q
def R_rat(p, n, c):  r, k, b, q = p; return r + k * c**-q / (1 + b * n**2)
def R_cond(p, n, c): r, gN, m, gC, s_ = p; return r + 1 / (gN * n**m + gC * c**s_)     # przewodności równoległe: karta + obudowa
def R_flow(p, n, c): r, k, b, m = p; return r + k * (n + b * c)**-m                       # efektywny przepływ N + b·C

PARAM = {"pow": (R_pow, [0.01, .08, 1.7, .3], ["r∞", "k", "m", "q"]),
         "exp": (R_exp, [0.02, .3, 1.5, .3], ["r∞", "k", "a", "q"]),
         "rat": (R_rat, [0.02, .1, .5, .3], ["r∞", "k", "b", "q"]),
         "cond": (R_cond, [0.05, 7, 2.4, 8, .8], ["r∞", "gN", "m", "gC", "s"]),
         "flow": (R_flow, [0.05, .1, .25, 2], ["r∞", "k", "b", "m"])}

KN = None  # węzły splajnu z pełnych danych (stałe w CV)


def spline_X(n, c, Pw):
    global KN
    ln = np.log(n)
    if KN is None:
        b = patsy.dmatrix("cr(x, df=4) - 1", {"x": ln}); KN = b.design_info
    B4 = np.asarray(patsy.build_design_matrices([KN], {"x": ln})[0])
    lc = np.log(c)
    return np.column_stack([np.ones_like(n), Pw[:, None] * B4, (Pw * lc)[:, None] * B4[:, [0, 3]], Pw * lc * ln])


KT = None
def tensor_X(n, c, Pw):
    """Splajn tensorowy R(n, c): naturalne sześcienne B(ln n) ⊗ B(ln c), skalowane przez P (benchmark nieparametryczny 2D)."""
    global KT
    d = {"x": np.log(n), "z": np.log(c)}
    if KT is None: KT = (patsy.dmatrix("cr(x, df=4) - 1", d).design_info, patsy.dmatrix("cr(z, df=3) - 1", d).design_info)
    Bn = np.asarray(patsy.build_design_matrices([KT[0]], d)[0]); Bc = np.asarray(patsy.build_design_matrices([KT[1]], d)[0])
    return np.column_stack([np.ones_like(n)] + [Pw * Bn[:, i] * Bc[:, j] for i in range(4) for j in range(3)])


def loglog_X(n, c, Pw):
    ln, lc, lp = np.log(n), np.log(c), np.log(Pw / 575)
    return np.column_stack([np.ones_like(n), lp, ln, lc, ln * lc, ln**2, lp * ln])


class Model:
    def __init__(s, name, kind, resp, sess, form=None):
        s.name, s.kind, s.resp, s.sess, s.form = name, kind, resp, sess, form

    def k(s):
        return len(s.p) if s.kind == "nls" else s.p.size

    def _X(s, idx):
        if s.kind == "spline": X = spline_X(n_[idx], c_[idx], P[idx])
        elif s.kind == "tensor": X = tensor_X(n_[idx], c_[idx], P[idx])
        elif s.kind == "loglog": X = loglog_X(n_[idx], c_[idx], P[idx])
        else: X = None
        return X

    def mean(s, p, idx):  # na skali odpowiedzi
        ns = S.shape[1] if s.sess else 0
        sh = (S[idx] @ p[len(p) - ns:]) if ns else 0
        if s.kind == "nls":
            f, _, _ = PARAM[s.form]; th0 = p[0]; core = p[1:len(p) - ns]
            Rv = f(core, n_[idx], c_[idx])
            if s.resp == "y": return th0 + sh + P[idx] * Rv
            if s.resp == "R": return (th0 + sh) / P[idx] + Rv
        X = s._X(idx); return X @ p[:X.shape[1]] + sh

    def target(s, idx):
        return {"y": y[idx], "lny": np.log(y[idx]), "R": y[idx] / P[idx]}[s.resp]

    def fit(s, idx=None, p0=None):
        """Dopasowanie. Przesunięcia sesji nieobecnych w zbiorze uczącym są przypięte do 0; gdy w zbiorze uczącym
        nie ma sesji odniesienia, odniesieniem staje się pierwsza obecna (jej przesunięcie też 0)."""
        idx = np.arange(N) if idx is None else idx
        ns = S.shape[1] if s.sess else 0
        act = np.array([S[idx, j].sum() > 0 for j in range(ns)], bool)
        if ns and act.any() and not np.any(S[idx].sum(1) == 0): act[np.argmax(act)] = False
        s.act = act; s.ref_present = (not ns) or np.any(S[idx].sum(1) == 0)
        if s.kind in ("spline", "loglog", "tensor"):
            X0 = s._X(idx); X = np.column_stack([X0, S[idx][:, act]]) if ns else X0
            keep = X.std(0) > 0; keep[0] = True
            b = np.zeros(X.shape[1]); b[keep] = np.linalg.lstsq(X[:, keep], s.target(idx), rcond=None)[0]
            s.p = np.r_[b[:X0.shape[1]], np.zeros(ns)]
            if ns: s.p[X0.shape[1]:][act] = b[X0.shape[1]:]
            return s
        f, start, _ = PARAM[s.form]; nb = 1 + len(start)
        def full(q):
            p = np.r_[q[:nb], np.zeros(ns)]
            if ns: p[nb:][act] = q[nb:]
            return p
        res = lambda q: s.mean(full(q), idx) - s.target(idx)
        best = None
        for jit in ([1, 1, 1, 1, 1], [1, .5, 2, .7, 1], [1, 2, .6, 1.3, 2]):
            x0 = np.r_[2.0 if s.resp != "R" else 2.0, np.array(start) * np.array(jit[:len(start)]), np.zeros(act.sum())]
            try: r = optimize.least_squares(res, x0, method="lm", max_nfev=20000)
            except Exception: continue
            if best is None or r.cost < best.cost: best = r
        if best is None:
            try: best = optimize.least_squares(res, x0, method="trf", max_nfev=20000)
            except Exception: s.p = np.full(nb + ns, np.nan); return s
        s.p = full(best.x); return s

    def pred_y(s, idx, resid_train=None):  # predykcja na skali T − Tin
        m = s.mean(s.p, idx)
        if s.resp == "y": return m
        if s.resp == "R": return m * P[idx]
        sm_ = np.mean(np.exp(resid_train)) if resid_train is not None else 1.0   # smearing Duana
        return np.exp(m) * sm_

    def loglik_y(s):  # log-wiarygodność gaussowska na skali T − Tin (jakobian przekształcenia)
        e = s.target(np.arange(N)) - s.mean(s.p, np.arange(N)); sig2 = np.mean(e**2)
        L = -N / 2 * (np.log(2 * np.pi * sig2) + 1)
        if s.resp == "lny": L -= np.sum(np.log(y))
        if s.resp == "R": L -= np.sum(np.log(P))
        return L


def cv(make, folds):
    pred = np.full(N, np.nan)
    for te in folds:
        tr = np.setdiff1d(np.arange(N), te); m = make().fit(tr)
        if m.sess and S.shape[1]:
            # sesje bez danych w zbiorze uczącym -> przesunięcie = średnia przesunięć sesji obecnych (odniesienie = 0)
            ns = S.shape[1]; p = m.p.copy(); off = p[len(p) - ns:]
            present = np.array([S[tr, j].sum() > 0 for j in range(ns)])
            vals = list(off[present]) + ([0.0] if np.any(S[tr].sum(1) == 0) else [])
            off[~present] = np.mean(vals); m.p = p
            if m.resp == "y" or m.resp == "R" or m.resp == "lny":
                pass
            # sesja odniesienia nieobecna -> jej wiersze (S = 0) dostają średnią przez korektę poziomu
            if not np.any(S[tr].sum(1) == 0):
                shift = np.mean(vals)
                m.p = p; ref_rows = te[S[te].sum(1) == 0]
                if len(ref_rows):
                    rt = m.target(tr) - m.mean(m.p, tr)
                    base = m.mean(m.p, ref_rows)
                    adj = base + (shift / P[ref_rows] if m.resp == "R" else shift)
                    pr = {"y": adj, "R": adj * P[ref_rows], "lny": np.exp(adj) * np.mean(np.exp(rt))}[m.resp]
                    pred[ref_rows] = pr
                    te = te[S[te].sum(1) > 0]
                    if not len(te): continue
        rt = m.target(tr) - m.mean(m.p, tr)
        pred[te] = m.pred_y(te, rt)
    return np.sqrt(np.mean((y - pred)**2))


rng = np.random.default_rng(1)
LOO = [np.array([i]) for i in range(N)]
KF = [np.array_split(rng.permutation(N), 5) for _ in range(20)]
LOSO = [np.where(D.grp == g)[0] for g in groups]

SPECS = []
for sess in (False, True):
    for form in ("pow", "exp", "rat", "cond", "flow"):
        SPECS.append((f"{form}{' +S' if sess else ''}", lambda f=form, s=sess: Model(f, "nls", "y", s, f)))
    SPECS.append((f"R-resp cond{' +S' if sess else ''}", lambda s=sess: Model("Rcond", "nls", "R", s, "cond")))
    SPECS.append((f"log-log{' +S' if sess else ''}", lambda s=sess: Model("loglog", "loglog", "lny", s)))
    SPECS.append((f"spline{' +S' if sess else ''}", lambda s=sess: Model("spline", "spline", "y", s)))
    SPECS.append((f"tensor{' +S' if sess else ''}", lambda s=sess: Model("tensor", "tensor", "y", s)))


def dw_series(e):
    num = den = 0
    for k_ in np.unique(ser_id):
        i = np.where(ser_id == k_)[0]; i = i[np.lexsort((t_h[i], n_[i]))]
        if len(i) > 2: num += np.sum(np.diff(e[i])**2); den += np.sum(e[i]**2)
    return num / den


rows = []; fitted = {}
for name, mk in SPECS:
    m = mk().fit(); fitted[name] = m
    e = y - m.pred_y(np.arange(N), m.target(np.arange(N)) - m.mean(m.p, np.arange(N)))
    L = m.loglik_y(); k = m.k() + 1
    rows.append(dict(model=name, k=k, rmse=np.sqrt(np.mean(e**2)), mean_e=e.mean(), AIC=-2 * L + 2 * k, BIC=-2 * L + k * np.log(N),
                     LOO=cv(mk, LOO), CV5=np.mean([cv(mk, f) for f in KF[:10]]), LOSO=cv(mk, LOSO) if len(groups) > 1 else np.nan, DWser=dw_series(e),
                     DWtime=durbin_watson(e[np.argsort(t_h)])))
T = pd.DataFrame(rows).round(3)
T.to_csv(OUT + f"steady-compare{TAG}.csv", index=False)
pd.set_option("display.width", 220)
print(f"n = {N}, rdzeń = {CORE}, sesje = {dict(D.grp.value_counts())}, odniesienie = {REF}\n")
print(T.to_string(index=False))

# ---------------------------------------------------------------- wybór: najmniejszy BIC wśród postaci parametrycznych na skali y
CHOICE = os.environ.get("CHOICE")
par = T[T.model.str.match(r"^(pow|exp|rat|cond|flow) \+S$")]
CH = CHOICE or par.sort_values("LOO").model.iloc[0]      # wybór: najmniejszy błąd LOO (cel = przewidywanie); BIC raportowany obok
M = fitted[CH]; idx = np.arange(N)
yhat = M.pred_y(idx); e = y - yhat
f, _, names = PARAM[M.form]
pn = ["θ0"] + names + [f"θ[{g}]" for g in groups[1:]]


def jac(p):
    h = 1e-6 * np.maximum(1, np.abs(p)); J = np.empty((N, len(p)))
    for j in range(len(p)):
        a, b = p.copy(), p.copy(); a[j] += h[j]; b[j] -= h[j]
        J[:, j] = (M.mean(a, idx) - M.mean(b, idx)) / (2 * h[j])
    return J


J = jac(M.p); kp = J.shape[1]; XtXi = np.linalg.inv(J.T @ J); H = np.einsum("ij,jk,ik->i", J, XtXi, J)
s2 = e @ e / (N - kp)
V_cl = s2 * XtXi
V_hc3 = XtXi @ (J.T * (e / (1 - H))**2) @ J @ XtXi
G = len(groups); meat = sum(np.outer(J[gid == g].T @ e[gid == g], J[gid == g].T @ e[gid == g]) for g in range(G))
V_cr = G / (G - 1) * (N - 1) / (N - kp) * XtXi @ meat @ XtXi if G > 1 else np.full_like(XtXi, np.nan)
# klaster = seria (obudowa, PL): odporne na korelację reszt wzdłuż N w obrębie serii
GS = ser_id.max() + 1; meatS = sum(np.outer(J[ser_id == g].T @ e[ser_id == g], J[ser_id == g].T @ e[ser_id == g]) for g in range(GS))
V_crS = GS / (GS - 1) * (N - 1) / (N - kp) * XtXi @ meatS @ XtXi

# klaster bez efektu sesji (model zbiorczy + SE klastrowe) — alternatywa dla efektu stałego
Mpool = fitted[CH.replace(" +S", "")]; Mp = Mpool
Jp = (lambda p: np.column_stack([(Mp.mean(p + np.eye(len(p))[j] * 1e-6 * max(1, abs(p[j])), idx) - Mp.mean(p - np.eye(len(p))[j] * 1e-6 * max(1, abs(p[j])), idx)) / (2e-6 * max(1, abs(p[j]))) for j in range(len(p))]))(Mp.p)
ep = y - Mp.mean(Mp.p, idx); XiP = np.linalg.inv(Jp.T @ Jp)
meatP = sum(np.outer(Jp[gid == g].T @ ep[gid == g], Jp[gid == g].T @ ep[gid == g]) for g in range(G))
V_crP = G / (G - 1) * (N - 1) / (N - Jp.shape[1]) * XiP @ meatP @ XiP if G > 1 else np.full_like(XiP, np.nan)

scale = {"r∞": 1000, "k": 1000}
UNIT = {"gN": "W/°C", "gC": "W/°C"}
partab = []
for j, nm in enumerate(pn):
    sc = scale.get(nm, 1); unit = "m°C/W" if sc == 1000 else ("°C" if nm.startswith("θ") else UNIT.get(nm, ""))
    se = [np.sqrt(V[j, j]) * sc for V in (V_cl, V_hc3, V_cr, V_crS)]
    partab.append(dict(param=nm, unit=unit, est=M.p[j] * sc, se_classic=se[0], se_HC3=se[1], se_cluster=se[2], se_cluster_series=se[3],
                       ci95_HC3=(M.p[j] * sc - 1.96 * se[1], M.p[j] * sc + 1.96 * se[1])))
partabP = [dict(param=(["θ0"] + names)[j], est=Mp.p[j] * scale.get((["θ0"] + names)[j], 1),
                se_cluster=np.sqrt(V_crP[j, j]) * scale.get((["θ0"] + names)[j], 1)) for j in range(len(Mp.p))]

# ---------------------------------------------------------------- testy
tests = []
def add(name, stat, p, h0, verdict=None, note=""):
    tests.append(dict(test=name, stat=float(stat), p=None if p is None else float(p), H0=h0,
                      verdict=verdict or ("reject H0" if p is not None and p < 0.05 else "do not reject H0"), note=note))

add("Mean of residuals (t-test)", e.mean() / (e.std(ddof=1) / np.sqrt(N)), stats.ttest_1samp(e, 0).pvalue, "E[e] = 0",
    note=f"mean {e.mean():+.4f} °C, sum {e.sum():+.3f} °C")
# Autokorelacja: (i) seria po N w obrębie (obudowa, PL); (ii) kolejność czasowa
def bg(e, order_idx_list, p_lag):
    """Breusch–Godfrey: e ~ J + e_{t-1..t-p} (opóźnienia w obrębie list), LM = n·R² ~ χ²(p)."""
    L = np.zeros((N, p_lag))
    for seq in order_idx_list:
        for l in range(1, p_lag + 1):
            L[seq[l:], l - 1] = e[seq[:-l]]
    X = np.column_stack([J, L]); b = np.linalg.lstsq(X, e, rcond=None)[0]; u = e - X @ b
    R2 = 1 - u @ u / (e @ e); LM = N * R2
    return LM, stats.chi2.sf(LM, p_lag)

seqs_ser = [np.where(ser_id == k_)[0][np.lexsort((t_h[ser_id == k_], n_[ser_id == k_]))] for k_ in np.unique(ser_id)]
seq_time = [np.argsort(t_h)]
seqs_sess_time = [np.where(gid == g)[0][np.argsort(t_h[gid == g])] for g in range(G)]

def dw_p(e, seqs, nsim=20000, X=None):
    """p-wartość DW (jednostronna, dodatnia autokorelacja) z rozkładu dokładnego pod H0 dla danego J (symulacja Monte Carlo)."""
    X = J if X is None else X
    Mx = np.eye(N) - X @ np.linalg.pinv(X)
    def dwv(u):
        num = sum(np.sum(np.diff(u[s])**2) for s in seqs if len(s) > 1); den = sum(np.sum(u[s]**2) for s in seqs if len(s) > 1)
        return num / den
    obs = dwv(e); Z = np.random.default_rng(7).standard_normal((nsim, N)) @ Mx.T
    sim = np.array([dwv(z) for z in Z]); return obs, np.mean(sim <= obs)

dws, pdws = dw_p(e, [s for s in seqs_ser if len(s) > 2])
add("Durbin–Watson, along N within (case, PL) series", dws, pdws, "no 1st-order autocorrelation along N", note="exact p by Monte Carlo under H0 given the regressors")
dwt, pdwt = dw_p(e, seq_time)
add("Durbin–Watson, time order", dwt, pdwt, "no 1st-order autocorrelation in time")
for pl in (1, 2):
    LM, p = bg(e, seqs_ser, pl); add(f"Breusch–Godfrey LM, order {pl}, along N", LM, p, "no autocorrelation up to order p")
    LM, p = bg(e, seqs_sess_time, pl); add(f"Breusch–Godfrey LM, order {pl}, time (within session)", LM, p, "no autocorrelation up to order p")
# korelacja z regresorami (orthogonality)
for nm, v in (("N", n_), ("C", c_), ("P", P), ("fitted", yhat), ("Tin", D.Tin.to_numpy()), ("time", t_h)):
    r, p = stats.pearsonr(e, v); add(f"corr(e, {nm})", r, p, "ρ = 0")
# Heteroskedastyczność
Xh = sm.add_constant(np.column_stack([n_, np.log(c_), P]))
lm, lmp, fv, fp = het_breuschpagan(e, Xh); add("Breusch–Pagan (Koenker) on N, ln C, P", lm, lmp, "homoscedastic")
try:
    lm, lmp, fv, fp = het_white(e, Xh); add("White (levels, squares, cross-products)", lm, lmp, "homoscedastic")
except Exception as ex: add("White", np.nan, None, "homoscedastic", "n/a", str(ex))
lm, lmp, _, _ = het_breuschpagan(e, sm.add_constant(np.column_stack([yhat, yhat**2]))); add("White special (ŷ, ŷ²)", lm, lmp, "homoscedastic")
# Normalność
w, p = stats.shapiro(e); add("Shapiro–Wilk", w, p, "normal residuals")
jb, jbp, sk, ku = jarque_bera(e); add("Jarque–Bera", jb, jbp, "normal residuals", note=f"skewness {sk:+.2f}, kurtosis {ku:.2f}")
# RESET (Gauss–Newton): e ~ J + ŷ² + ŷ³
for pw in ((2,), (2, 3)):
    Z = np.column_stack([J] + [(yhat / yhat.std())**k for k in pw]); b = np.linalg.lstsq(Z, e, rcond=None)[0]; u = e - Z @ b
    q = len(pw); F = ((e @ e - u @ u) / q) / (u @ u / (N - Z.shape[1])); add(f"Ramsey RESET (ŷ^{','.join(map(str, pw))})", F, stats.f.sf(F, q, N - Z.shape[1]), "functional form adequate")
# brak dopasowania: czysty błąd z powtórzeń (te same nastawy), po zdjęciu efektu sesji
key = pd.Series([f"{a}/{b}/{c}" for a, b, c in zip(D.gpu_pct, np.round(D.C / 250).astype(int) * 250, D.pl_pct)])
ns = S.shape[1]; sh = S @ M.p[len(M.p) - ns:]
yadj = y - sh; grpm = pd.Series(yadj).groupby(key).transform("mean").to_numpy(); m_g = key.nunique()
SSPE = np.sum((yadj - grpm)**2); dfPE = N - m_g; SSLF = e @ e - SSPE; dfLF = (N - kp) - dfPE
if dfPE > 0 and dfLF > 0:
    F = (SSLF / dfLF) / (SSPE / dfPE); add("Lack-of-fit F (pure error from replicates)", F, stats.f.sf(F, dfLF, dfPE), "functional form adequate",
                                          note=f"{N - m_g} replicate d.o.f., pure-error SD {np.sqrt(SSPE / dfPE):.2f} °C")
# Spline vs parametric (zagnieżdżenie przybliżone: F na podstawie SSR)
Msp = fitted["spline +S"]; esp = y - Msp.pred_y(idx); ksp = Msp.k()
F = ((e @ e - esp @ esp) / max(ksp - kp, 1)) / (esp @ esp / (N - ksp))
add("Parametric vs natural-spline benchmark (F, approx.)", F, stats.f.sf(F, max(ksp - kp, 1), N - ksp), "parametric form not worse than spline")
# efekt sesji: Wald (HC3) na przesunięciach sesji
if ns:
  js = np.arange(len(M.p) - ns, len(M.p)); b_ = M.p[js]; W = b_ @ np.linalg.solve(V_hc3[np.ix_(js, js)], b_)
  add("Session effect = 0 (Wald, HC3)", W, stats.chi2.sf(W, ns), "no session effect")

# Box–Cox (transform both sides, Carroll–Ruppert): h_λ(y) = h_λ(f(x;β)) + ε
def hl(v, l): return np.log(v) if abs(l) < 1e-9 else (v**l - 1) / l
def prof(l):
    r = optimize.least_squares(lambda p: hl(y, l) - hl(np.maximum(M.mean(p, idx), 1e-3), l), M.p, method="lm", max_nfev=5000)
    u = r.fun; return -N / 2 * np.log(u @ u / N) + (l - 1) * np.sum(np.log(y))
lam = np.linspace(-1.5, 3, 91); LL = np.array([prof(l) for l in lam]); lhat = lam[LL.argmax()]
ci = lam[LL >= LL.max() - 1.92]
add("Box–Cox λ (transform-both-sides), LR test λ = 1", 2 * (LL.max() - prof(1.0)), stats.chi2.sf(2 * (LL.max() - prof(1.0)), 1), "λ = 1 (no transform)",
    note=f"λ̂ = {lhat:.2f}, 95 % CI [{ci.min():.2f}, {ci.max():.2f}]; LR for λ = 0 (log): p = {stats.chi2.sf(2 * (LL.max() - prof(0.0)), 1):.3f}")

# Mixed model: losowy wyraz wolny sesji, przy stałych parametrach nieliniowych (linearyzacja)
core = M.p[1:len(M.p) - ns]
lin_cols = [np.ones(N), P, P * (f(core, n_, c_) - core[0])]     # θ0, r∞, mnożnik części zależnej od wentylatorów (≈ 1)
Xm = np.column_stack(lin_cols)
if G > 2:
  mx = sm.MixedLM(y, Xm, groups=D.grp.to_numpy()).fit(reml=True)
  sig_u = float(np.sqrt(np.asarray(mx.cov_re)[0, 0])); sig_e = float(np.sqrt(mx.scale))
  mixed = dict(fe=[float(v) for v in mx.fe_params], fe_se=[float(v) for v in mx.bse_fe], sigma_session=sig_u, sigma_resid=sig_e,
             ICC=sig_u**2 / (sig_u**2 + sig_e**2), re={k: float(np.asarray(v)[0]) for k, v in mx.random_effects.items()})
else:
  sig_u = sig_e = np.nan; mixed = dict(note="one or two sessions: random effect not estimable", ICC=np.nan, re={})

# ---------------------------------------------------------------- przyczyny niskiego DW: dodatkowe analizy
def refit_form(yv, form=M.form, sess=True, pbeta=False):
    """Ten sam kształt dopasowany do innej odpowiedzi (inny odczyt rdzenia) — zwraca reszty."""
    fR, st, _ = PARAM[form]; nsx = S.shape[1] if sess else 0; nb = 1 + len(st)
    def mu(q):
        sh_ = S @ q[nb:nb + nsx] if nsx else 0
        return (q[0] + sh_ + (575 * (P / 575)**q[-1]) * fR(q[1:nb], n_, c_)) if pbeta else (q[0] + sh_ + P * fR(q[1:nb], n_, c_))
    x0 = np.r_[M.p[:nb], M.p[nb:] if sess else [], [1.0] if pbeta else []]
    r = optimize.least_squares(lambda q: mu(q) - yv, x0, method="lm", max_nfev=20000)
    return -r.fun, r.x

def dw_distinct(e):
    num = den = 0
    for s_ in seqs_ser:
        u = pd.Series(e[s_]).groupby(np.round(n_[s_], 2)).mean().to_numpy()
        if len(u) > 2: num += np.sum(np.diff(u)**2); den += np.sum(u**2)
    return num / den

cause = []
for lab, col in (("NVML table, whole °C (quantised)", "core_tab"), ("NVAPI 0.01 °C, mean of last 60 s", "core"), ("NVAPI 0.01 °C, extrapolated to T∞ (settling-corrected)", "core_settled")):
    yv = (D[col] - D.Tin).to_numpy(); ee, _ = refit_form(yv)
    cause.append(dict(variant=lab, rmse=float(np.sqrt(np.mean(ee**2))), DW_series=float(dw_series(ee)), DW_distinctN=float(dw_distinct(ee))))
ee, qb = refit_form(y, pbeta=True)
cause.append(dict(variant=f"+ power curvature P^β (β = {qb[-1]:.3f})", rmse=float(np.sqrt(np.mean(ee**2))), DW_series=float(dw_series(ee)), DW_distinctN=float(dw_distinct(ee))))
ee, _ = refit_form(y, sess=False)
cause.append(dict(variant="without session effect", rmse=float(np.sqrt(np.mean(ee**2))), DW_series=float(dw_series(ee)), DW_distinctN=float(dw_distinct(ee))))
for nm in ("spline +S", "tensor +S"):
    ee = y - fitted[nm].pred_y(idx)
    cause.append(dict(variant=f"non-parametric benchmark: {nm}", rmse=float(np.sqrt(np.mean(ee**2))), DW_series=float(dw_series(ee)), DW_distinctN=float(dw_distinct(ee))))
Xt = np.column_stack([tensor_X(n_, c_, P), S, P**2]); bt = np.linalg.lstsq(Xt, y, rcond=None)[0]; ee = y - Xt @ bt
cause.append(dict(variant="tensor spline R(N, C) + P² + session", rmse=float(np.sqrt(np.mean(ee**2))), DW_series=float(dw_series(ee)), DW_distinctN=float(dw_distinct(ee)),
                  p_MC=float(dw_p(ee, [s_ for s_ in seqs_ser if len(s_) > 2], 5000, Xt)[1])))
cause.append(dict(variant="chosen model, replicate points at equal N averaged", rmse=float(np.sqrt(np.mean(e**2))), DW_series=float(dw_series(e)), DW_distinctN=float(dw_distinct(e))))
CA = pd.DataFrame(cause)

# Prais–Winsten FGLS z AR(1) wzdłuż N w obrębie serii (klasyczna korekta autokorelacji)
rho = float(np.sum([np.sum(e[s_][1:] * e[s_][:-1]) for s_ in seqs_ser if len(s_) > 1]) / np.sum([np.sum(e[s_][:-1]**2) for s_ in seqs_ser if len(s_) > 1]))
def pw(u):
    out = u.copy()
    for s_ in seqs_ser:
        if len(s_) > 1:
            out[s_[1:]] = u[s_[1:]] - rho * u[s_[:-1]]; out[s_[0]] = np.sqrt(1 - rho**2) * u[s_[0]]
    return out
rpw = optimize.least_squares(lambda q: pw(M.mean(q, idx) - y), M.p, method="lm", max_nfev=20000)
Jpw = -rpw.jac if rpw.jac is not None else None
upw = rpw.fun; Vpw = (upw @ upw / (N - kp)) * np.linalg.inv(rpw.jac.T @ rpw.jac)
fgls = dict(rho=rho, params={pn[j]: (float(rpw.x[j] * scale.get(pn[j], 1)), float(np.sqrt(Vpw[j, j]) * scale.get(pn[j], 1))) for j in range(kp)},
            DW_transformed=float(dw_series(-upw)), rmse_levels=float(np.sqrt(np.mean((y - M.mean(rpw.x, idx))**2))))

# Różnice pierwsze wzdłuż N (odpowiednik „stóp wzrostu”): Δ(T − Tin) = P·ΔR w obrębie (sesja, obudowa, PL) — θ0 i sesja znikają
pairs = []
for key_, g_ in D.groupby([D.grp, np.round(D.C / 250), D.pl_pct]):
    i = g_.sort_values("N").index.to_numpy()
    for a_, b2 in zip(i[:-1], i[1:]):
        if abs(n_[b2] - n_[a_]) > 0.05: pairs.append((a_, b2))
pairs = np.array(pairs)
fR = PARAM[M.form][0]; nb = 1 + len(PARAM[M.form][1])
def fd_res(q):
    Rv = fR(q, n_, c_); return (P[pairs[:, 1]] * Rv[pairs[:, 1]] - P[pairs[:, 0]] * Rv[pairs[:, 0]]) - (y[pairs[:, 1]] - y[pairs[:, 0]])
FREE = {"cond": ["gN", "m"], "exp": ["k", "a"], "pow": ["k", "m"], "rat": ["k", "b"], "flow": ["k", "m"]}[M.form]
fi = [names.index(v) for v in FREE]; base_q = M.p[1:nb].copy()
def fd_free(z):
    q = base_q.copy(); q[fi] = z; return fd_res(q)
rfd = optimize.least_squares(fd_free, base_q[fi], method="lm", max_nfev=20000)
Jf = rfd.jac; Vf = (rfd.fun @ rfd.fun / max(len(pairs) - len(fi), 1)) * np.linalg.inv(Jf.T @ Jf)
fd = dict(n_pairs=int(len(pairs)), free=FREE, params={FREE[j]: (float(rfd.x[j] * scale.get(FREE[j], 1)), float(np.sqrt(Vf[j, j]) * scale.get(FREE[j], 1))) for j in range(len(fi))},
          levels={names[j]: float(M.p[1 + j] * scale.get(names[j], 1)) for j in range(len(names))},
          rmse_diff=float(np.sqrt(np.mean(rfd.fun**2))), rmse_diff_levels_model=float(np.sqrt(np.mean(fd_res(M.p[1:nb])**2))))
# log-log: elastyczności w średniej
LL_ = fitted["log-log +S"]; bl = LL_.p; lnm = np.log(n_).mean(); lcm = np.log(c_).mean(); lpm = np.log(P / 575).mean()
elast = dict(P=float(bl[1] + bl[6] * lnm), N=float(bl[2] + bl[4] * lcm + 2 * bl[5] * lnm + bl[6] * lpm), C=float(bl[3] + bl[4] * lnm))

# Dryf w sesji z kotwic (powtórzone nastawy w tej samej sesji): reszta względem średniej grupy ~ czas
key_s = D.grp + "/" + key
gm = pd.Series(e).groupby(key_s).transform("mean").to_numpy(); cnt = key_s.map(key_s.value_counts()).to_numpy()
ia = cnt >= 2
if ia.sum() >= 3:
    th = t_h[ia] - pd.Series(t_h[ia]).groupby(key_s[ia].to_numpy()).transform("mean").to_numpy(); u = (e - gm)[ia]
    if np.sum(th**2) > 0:
        b1 = np.sum(th * u) / np.sum(th**2); dof = ia.sum() - key_s[ia].nunique() - 1
        se1 = np.sqrt(np.sum((u - b1 * th)**2) / max(dof, 1) / np.sum(th**2))
        add("Within-session drift from repeated anchors (slope)", b1, 2 * stats.t.sf(abs(b1 / se1), max(dof, 1)) if dof > 0 else None,
            "no drift", note=f"{b1:+.3f} °C/h ± {se1:.3f}; {ia.sum()} points in {key_s[ia].nunique()} anchor groups ({', '.join(sorted(set(key_s[ia])))})")
# Wrażliwość normalności na punkty odstające (|reszta studentyzowana zewnętrznie| > 3)
r_int = e / np.sqrt(s2 * (1 - H)); r_ext = r_int * np.sqrt((N - kp - 1) / (N - kp - r_int**2))
out_i = np.where(np.abs(r_ext) > 3)[0]
if len(out_i):
    keep = np.setdiff1d(idx, out_i); e2 = e[keep]
    lab = "; ".join(f"{D.grp[i]} card {D.gpu_pct[i]} % / case {D.C[i]:.0f} rpm / PL {D.pl_pct[i]} (t = {r_ext[i]:+.1f})" for i in out_i)
    add("Shapiro–Wilk without outliers |t*| > 3", stats.shapiro(e2)[0], stats.shapiro(e2)[1], "normal residuals", note=f"removed: {lab}")
    jb2 = jarque_bera(e2); add("Jarque–Bera without outliers |t*| > 3", jb2[0], jb2[1], "normal residuals")

TT = pd.DataFrame(tests)
print(f"\nWYBRANY: {CH}  (najmniejszy LOO wśród postaci parametrycznych z efektem sesji)")
for r in partab: print(f"  {r['param']:12s} {r['est']:9.3f} {r['unit']:6s}  SE kl {r['se_classic']:.3f}  HC3 {r['se_HC3']:.3f}  klaster-sesja {r['se_cluster']:.3f}  klaster-seria {r['se_cluster_series']:.3f}")
print("  zbiorczy (bez efektu sesji) + SE klastrowe:", [(r["param"], round(r["est"], 3), round(r["se_cluster"], 3)) for r in partabP])
print(f"  mixed: σ_sesji {sig_u:.2f} °C, σ_reszt {sig_e:.2f} °C, ICC {mixed['ICC']:.2f}, RE {mixed['re']}")
print(TT.assign(stat=TT.stat.round(3), p=TT.p.round(4)).to_string(index=False))
print("\nPrzyczyny niskiego DW:\n" + CA.round(3).to_string(index=False))
print(f"\nFGLS Prais–Winsten: ρ = {rho:.2f}, DW po transformacji {fgls['DW_transformed']:.2f}, parametry {fgls['params']}")
print(f"Różnice pierwsze ({fd['n_pairs']} par): {fd['params']} vs poziomy {fd['levels']}; RMSE różnic {fd['rmse_diff']:.3f} (model z poziomów {fd['rmse_diff_levels_model']:.3f})")
print(f"Elastyczności log-log (w średniej): {elast}")

# ---------------------------------------------------------------- kwantyzacja: ten sam model na rdzeniu z tabeli (NVML całe °C)
res = dict(n=N, core=CORE, primary=PRIMARY, ref=REF, groups=groups, choice=CH, compare=T.to_dict("records"),
           params=partab, params_pooled_cluster=partabP, tests=tests, mixed=mixed, dw_causes=cause, fgls=fgls, first_diff=fd, elasticities=elast, boxcox=dict(lam=lhat, ci=[float(ci.min()), float(ci.max())]),
           rmse=float(np.sqrt(np.mean(e**2))), loo=float(T.set_index("model").loc[CH, "LOO"]), sessions=dict(D.grp.value_counts()))
json.dump(res, open(OUT + f"steady-stats{TAG}.json", "w"), indent=1, default=float, ensure_ascii=False)
D.assign(e=e, fitted=yhat + D.Tin, series=ser_id).to_csv(OUT + f"steady-residuals{TAG}.csv", index=False)
if CORE != "core_settled": sys.exit()

# ---------------------------------------------------------------- rysunki diagnostyczne
COL = {"val1": "#2166ac", "val2": "#67a9cf", "afternoon": "#1b7837", "night": "#b2182b", "steady2": "#000000"}
cs = [COL.get(g, "#777") for g in D.grp]
fig, ax = plt.subplots(3, 3, figsize=(15, 12.5)); ax = ax.ravel()
def sc(a, x, xl, title):
    a.scatter(x, e, c=cs, s=36, edgecolors="k", lw=.4); a.axhline(0, c="k", lw=.8)
    lo = sm.nonparametric.lowess(e, x, frac=.7); a.plot(lo[:, 0], lo[:, 1], c="#e08214", lw=1.5)
    a.set_xlabel(xl); a.set_ylabel("residual, °C"); a.set_title(title, fontsize=10); a.grid(alpha=.3)
sc(ax[0], yhat + D.Tin, "fitted core, °C", "Residuals vs fitted (orange = LOWESS)")
sc(ax[1], D.N, "GPU fans, rpm", "Residuals vs GPU fan speed N")
s2a = ax[1].secondary_xaxis("top", functions=(lambda r: (r - 180) / 28.33, lambda p: 180 + 28.33 * p)); s2a.set_xlabel("GPU fans, %")
sc(ax[2], D.C, "case fans, rpm", "Residuals vs case fan speed C")
CP = np.array([[15, 654], [26.5, 1002], [36, 1290], [43.8, 1500], [58, 1893], [79, 2417], [100, 2912]])
s2b = ax[2].secondary_xaxis("top", functions=(lambda r: np.interp(r, CP[:, 1], CP[:, 0]), lambda p: np.interp(p, CP[:, 0], CP[:, 1]))); s2b.set_xlabel("case fans, %")
sc(ax[3], P, "board power, W", "Residuals vs power P")
o = np.argsort(t_h); ax[4].plot(np.arange(N), e[o], c="#999", lw=.8); ax[4].scatter(np.arange(N), e[o], c=np.array(cs)[o], s=36, edgecolors="k", lw=.4)
ax[4].axhline(0, c="k", lw=.8); ax[4].set_xlabel("measurement order (time)"); ax[4].set_ylabel("residual, °C"); ax[4].set_title("Residuals in time order", fontsize=10); ax[4].grid(alpha=.3)
sm.qqplot(e / e.std(ddof=kp), line="45", ax=ax[5]); ax[5].set_title(f"Normal Q–Q (Shapiro–Wilk p = {stats.shapiro(e).pvalue:.2f})", fontsize=10); ax[5].grid(alpha=.3)
lags = min(10, N // 3); a_t = acf(e[o], nlags=lags)
ax[6].bar(range(lags + 1), a_t, color="#4d4d4d", width=.4); ax[6].axhspan(-1.96 / np.sqrt(N), 1.96 / np.sqrt(N), color="#9ecae1", alpha=.5)
ax[6].set_title("ACF of residuals, time order (band = ±1.96/√n)", fontsize=10); ax[6].set_xlabel("lag"); ax[6].grid(alpha=.3)
for k_, s in enumerate(seqs_ser):
    if len(s) > 2: ax[7].plot(n_[s] * 1000, e[s], "-o", ms=4, lw=1, label=f"case {SER[s[0]][0]}, PL {SER[s[0]][1]}")
ax[7].axhline(0, c="k", lw=.8); ax[7].set_xlabel("GPU fans, rpm"); ax[7].set_ylabel("residual, °C"); ax[7].legend(fontsize=7)
ax[7].set_title(f"Residual runs along N inside series (DW = {dws:.2f}, p = {pdws:.3f})", fontsize=10); ax[7].grid(alpha=.3)
ax[8].plot(lam, LL - LL.max(), c="k"); ax[8].axhline(-1.92, c="#b2182b", ls=":"); ax[8].set_ylim(-8, .5)
ax[8].set_title(f"Box–Cox profile (transform-both-sides): λ̂ = {lhat:.2f}", fontsize=10); ax[8].set_xlabel("λ"); ax[8].set_ylabel("log-lik − max"); ax[8].grid(alpha=.3)
for g, cl in COL.items():
    if g in groups: ax[0].scatter([], [], c=cl, label=g, edgecolors="k", lw=.4)
ax[0].legend(fontsize=8, title="session")
fig.suptitle(f"RTX 5090 core, steady state — residual diagnostics of the chosen model ({CH}), n = {N}, core = {CORE} (NVAPI 0.01 °C, settling-corrected)", fontsize=12)
fig.tight_layout(); fig.savefig(OUT + f"steady-diagnostics{TAG}.png", dpi=140); plt.close(fig)

# ---------------------------------------------------------------- wykres „w obie strony” (owner)
TIN = float(D.Tin[D.grp == REF].mean())
def curve(Nr, Cr, Pw):
    p = M.p; th = p[0]; Rv = f(p[1:len(p) - ns], np.asarray(Nr) / 1000, np.asarray(Cr) / 1500)
    return TIN + th + Pw * Rv
adj = D[CORE].to_numpy() - (D.Tin.to_numpy() - TIN) - sh     # pomiar sprowadzony do Tin i sesji odniesienia
rpm = lambda p: 180 + 28.33 * p
fig = plt.figure(figsize=(15, 10)); gs = fig.add_gridspec(2, 2, height_ratios=[3, 1.2])
A, B = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]); RA, RB = fig.add_subplot(gs[1, 0], sharex=A), fig.add_subplot(gs[1, 1], sharex=B)
gp = np.linspace(40, 100, 200); cc = np.linspace(950, 2950, 200)
mk = {"val1": "o", "val2": "s", "afternoon": "D", "steady2": "^", "night": "v"}
for pl, col in ((100, "#08306b"), (90, "#2171b5"), (80, "#6baed6"), (70, "#9ecae1")):
    Pw = 575 * pl / 100
    A.plot(gp, curve(rpm(gp), 1500, Pw), c=col, lw=2, label=f"PL {pl} % ({Pw:.0f} W)"); B.plot(cc, curve(rpm(40), cc, Pw), c=col, lw=2, label=f"PL {pl} % ({Pw:.0f} W)")
    i = (np.abs(D.C - 1500) < 60).to_numpy() & (D.pl_pct == pl).to_numpy()
    j = (D.gpu_pct == 40).to_numpy() & (D.pl_pct == pl).to_numpy()
    for g in groups:
        ig = i & (D.grp == g).to_numpy(); jg = j & (D.grp == g).to_numpy()
        A.scatter(D.gpu_pct[ig], adj[ig], c=col, marker=mk.get(g, "o"), s=60, edgecolors="k", lw=.6, zorder=3)
        RA.scatter(D.gpu_pct[ig], e[ig], c=col, marker=mk.get(g, "o"), s=44, edgecolors="k", lw=.5)
        B.scatter(D.C[jg], adj[jg], c=col, marker=mk.get(g, "o"), s=60, edgecolors="k", lw=.6, zorder=3)
        RB.scatter(D.C[jg], e[jg], c=col, marker=mk.get(g, "o"), s=44, edgecolors="k", lw=.5)
for g in groups:
    if ((np.abs(D.C - 1500) < 60) | (D.gpu_pct == 40))[D.grp == g].any(): A.scatter([], [], c="w", marker=mk.get(g, "o"), edgecolors="k", label=f"session {g}")
for a in (A, B): a.grid(alpha=.3); a.legend(fontsize=9, loc="upper right"); a.set_ylim(45, 88)
lim = max(1.0, np.ceil(np.abs(e).max() * 2) / 2)
for a in (RA, RB): a.axhline(0, c="k", lw=.8); a.set_ylim(-lim, lim); a.grid(alpha=.3); a.set_ylabel("residual, °C")
A.set_title("Case fans fixed at 1500 rpm (43.8 %)"); A.set_ylabel("GPU core, °C"); B.set_ylabel("GPU core, °C")
RA.set_xlabel("GPU fans, %"); A.secondary_xaxis("top", functions=(rpm, lambda r: (r - 180) / 28.33)).set_xlabel("GPU fans, rpm")
RA.secondary_xaxis(-0.42, functions=(rpm, lambda r: (r - 180) / 28.33)).set_xlabel("GPU fans, rpm")
B.set_title("GPU fans fixed at 40 % (1310 rpm)"); RB.set_xlabel("case fans, rpm")
cp = lambda r: np.interp(r, CP[:, 1], CP[:, 0]); cr_ = lambda p: np.interp(p, CP[:, 0], CP[:, 1])
B.secondary_xaxis("top", functions=(cp, cr_)).set_xlabel("case fans, %")
RB.secondary_xaxis(-0.42, functions=(cp, cr_)).set_xlabel("case fans, %")
pp = {r["param"]: r for r in partab}
txt = " · ".join(f"{k} = {v['est']:.2f} {v['unit']}".strip() for k, v in pp.items() if not k.startswith("θ["))
fig.suptitle(f"RTX 5090 FE core, settled points only (n = {N}; plotted points adjusted to intake {TIN:.2f} °C and session {REF})\n"
             f"Model {CH}: T = Tin + θ0 + θ_session + P·R(N, C) · {txt}\n"
             f"RMSE {res['rmse']:.2f} °C · LOO {res['loo']:.2f} °C · mean residual {e.mean():+.3f} °C · DW along N {dws:.2f} (p {pdws:.2f})", fontsize=10)
fig.tight_layout(); fig.savefig(OUT + f"steady-two-ways{TAG}.png", dpi=150); plt.close(fig)
print("zapisano:", OUT + f"steady-diagnostics{TAG}.png", OUT + f"steady-two-ways{TAG}.png", OUT + f"steady-stats{TAG}.json")
