# Zbiór punktów USTALONYCH do modelu stanu ustalonego rdzenia (wszystkie pliki, jakie są na dysku).
# Dla każdego punktu: rdzeń z tabeli (NVML, całe °C uśrednione) ORAZ rdzeń z NVAPI 0,01 °C z logu 1 Hz
# (średnia z ostatnich 60 s punktu), wlot z aquaero 0,01 °C, czas końca punktu.
# Wynik: results-2026-10-22/steady-points.csv (cache długich logów: results-2026-10-22/cache/).
import csv, glob, gzip, json, os
import numpy as np, pandas as pd

D = "data/"; OUT = "results-2026-10-22/"; os.makedirs(OUT + "cache", exist_ok=True)
WANT = {"nvapi/0/1": "core_nvapi", "aquaero/temperature/sensor_1": "intake_aq",
        "nvml/0/temperature/gpu_core": "core_nvml1hz"}
WIN = 60  # s, okno uśredniania na końcu punktu (jak w tabelach grid.csv)


def longlog(path):
    """Długi log 1 Hz -> DataFrame ts, point, phase, kolumny z WANT (cache w parquet/csv)."""
    key = OUT + "cache/" + path.replace("/", "_") + f".{int(os.path.getmtime(path))}.csv"
    if os.path.exists(key): return pd.read_csv(key, keep_default_na=False, na_values=[""])
    rows = []
    with gzip.open(path, "rt", errors="replace") as fh:
        try:
            for line in fh:
                p = line.rstrip("\n").split(",")
                if len(p) >= 9 and p[6] in WANT:
                    try: rows.append((int(p[0]), p[1], p[2], WANT[p[6]], float(p[-2])))
                    except ValueError: pass
        except (EOFError, OSError): pass   # ucięte gzipy (pierwsze pliki val1) — bierzemy, co jest
    df = pd.DataFrame(rows, columns=["ts", "point", "phase", "k", "v"])
    w = df.pivot_table(index=["ts"], columns="k", values="v", aggfunc="mean").reset_index()
    meta = df.groupby("ts")[["point", "phase"]].first().reset_index()
    w = w.merge(meta, on="ts"); w.to_csv(key, index=False); return w


def window_means(logs, t_end):
    for L in logs:
        s = L[(L.ts > t_end - WIN) & (L.ts <= t_end)]
        if len(s) >= 20:
            return {c: float(s[c].mean()) if c in s else np.nan for c in WANT.values()}
    return {c: np.nan for c in WANT.values()}


def settle_fit(logs, t0, t1):
    """Dojście do stanu ustalonego z logu 1 Hz (NVAPI 0,01 °C): T(t) = T∞ − A·exp(−(t − t1)/τ), dopasowane od t0 + 60 s do t1.
    Zwraca T∞ (ekstrapolacja), jego SE, τ, ostatnie nachylenie (°C/min, z dopasowania) i T(t1) z dopasowania."""
    from scipy import optimize
    for L in logs:
        s = L[(L.ts > t0 + 60) & (L.ts <= t1)].dropna(subset=["core_nvapi"])
        if len(s) < 90: continue
        t = (s.ts - t1).to_numpy(float); T = s.core_nvapi.to_numpy()
        best = None
        for tau in (40, 90, 150, 300, 600):
            try:
                r = optimize.least_squares(lambda p: p[0] - p[1] * np.exp(-t / p[2]) - T, [T[-1], T[-1] - T[0], tau],
                                           bounds=([T.min() - 15, -40, 10], [T.max() + 15, 40, 3000]))
            except Exception: continue
            if best is None or r.cost < best.cost: best = r
        p = best.x; J = best.jac; e = best.fun; s2 = e @ e / max(len(e) - 3, 1)
        try: V = s2 * np.linalg.inv(J.T @ J)
        except np.linalg.LinAlgError: V = np.full((3, 3), np.nan)
        # SE z poprawką na autokorelację reszt 1 Hz (efektywna liczba obserwacji)
        rho = np.corrcoef(e[:-1], e[1:])[0, 1] if len(e) > 3 else 0
        infl = (1 + rho) / (1 - rho) if -0.99 < rho < 0.99 else 1
        return dict(core_inf=float(p[0]), core_inf_se=float(np.sqrt(abs(V[0, 0]) * infl)), tau_s=float(p[2]),
                    slope_end=float(p[1] / p[2] * 60), core_fit_end=float(p[0] - p[1]), core_last=float(T[-30:].mean()))
    return dict(core_inf=np.nan, core_inf_se=np.nan, tau_s=np.nan, slope_end=np.nan, core_fit_end=np.nan, core_last=np.nan)


def day_session(folder, sess, filt=None):
    f = D + folder + "/grid.csv"
    if not os.path.exists(f): return []
    logs = [longlog(p) for p in sorted(glob.glob(D + folder + "/long-*.csv.gz"))]
    out = []
    for r in csv.DictReader(open(f)):
        if filt is not None and not filt(r): continue
        if filt is None and r.get("settled", "1") not in ("1", "True", "true"): continue
        if not r.get("cardA_core_c"): continue
        t = int(float(r["ts_end"])); m = window_means(logs, t); m.update(settle_fit(logs, t - float(r["seconds"]), t))
        out.append(dict(session=sess, ts_end=t, pl_pct=int(float(r["pl_pct"] or 100)), gpu_pct=int(float(r["gpu_pct"])),
                        case_target=int(float(r["case_rpm_target"])), N=float(r["cardA_fan_rpm"]), C=float(r["case_rpm"]),
                        P=float(r["power_w_sum"]), Tin_tab=float(r["intake_c"]), core_tab=float(r["cardA_core_c"]),
                        seconds=float(r["seconds"]), **m))
    return out


rows = []
rows += day_session("val1-2026-10-21", "val1")
rows += day_session("val2-2026-10-21", "val2")
rows += day_session("grid1d-2026-10-21", "grid1d")
# grid1c: tylko punkt startowy po 660 s rozgrzewki (source zawiera "warm-up")
fc = D + "grid1c-2026-10-21/final.csv"
if os.path.exists(fc):
    w = [r for r in csv.DictReader(open(fc)) if "warm-up" in r["source"]][:1]
    if w:
        tmp = D + "grid1c-2026-10-21/"; logs = [longlog(p) for p in sorted(glob.glob(tmp + "long-*.csv.gz"))]
        r = w[0]; t = int(r["ts_end"]); m = window_means(logs, t); m.update(settle_fit(logs, t - float(r["seconds"]), t))
        rows.append(dict(session="grid1c", ts_end=t, pl_pct=int(r["pl_pct"]), gpu_pct=int(r["gpu_pct"]), case_target=int(r["case_rpm_target"]),
                         N=float(r["cardA_fan_rpm"]), C=float(r["case_rpm"]), P=float(r["power_w_sum"]), Tin_tab=float(r["intake_c"]),
                         core_tab=float(r["cardA_core_c"]), seconds=float(r["seconds"]), **m))

# Noc v2d: punkty z settled=1; okno = ostatnie 60 s ciągłego bloku danego punktu w logu
V = D + "experiments-2026-10-21/2026-10-20-gpu-map-v2d/"
if os.path.exists(V + "points.csv"):
    L = longlog(glob.glob(V + "long-*.csv.gz")[0])
    L = L[L.phase == "points"].copy(); L["run"] = (L.point != L.point.shift()).cumsum()
    runs = [(g.point.iloc[0], g) for _, g in L.groupby("run", sort=True)]
    pts = list(csv.DictReader(open(V + "points.csv")))
    assert [f"{p['fg_pct']}/{p['fc_pct']}" for p in pts] == [lab for lab, _ in runs], "noc: kolejność punktów ≠ log"
    for p, (lab, g) in zip(pts, runs):
        if p["settled"] != "1": continue
        t = int(g.ts.max()); m = window_means([g], t); m.update(settle_fit([g], int(g.ts.min()), t))
        rows.append(dict(session="night", ts_end=t, pl_pct=100, gpu_pct=int(p["fg_pct"]), case_target=int(round(float(p["case_rpm"]), -1)),
                         N=float(p["gpu_rpm_mean"]), C=float(p["case_rpm"]), P=float(p["power_w"]), Tin_tab=float(p["intake_c"]),
                         core_tab=float(p["core_c"]), seconds=float(p["seconds"]), **m))

# steady2 (seria gęsta, 2026-10-22) — wchodzi automatycznie, gdy plik się pojawi; rdzeń w tabeli już z NVAPI 0,01 °C
for f in sorted(glob.glob(D + "steady2*/grid.csv")):
    rows += day_session(os.path.dirname(f).split("/")[-1], "steady2")

df = pd.DataFrame(rows).sort_values("ts_end").reset_index(drop=True)
# Rdzeń do modelu: NVAPI 0,01 °C, gdy jest w logu; inaczej tabela. Wlot: aquaero 0,01 °C z logu, inaczej tabela.
df["core"] = df.core_nvapi.where(df.core_nvapi.notna(), df.core_tab)
# Rdzeń ekstrapolowany do stanu ustalonego (T∞ z dojścia wykładniczego); gdy brak dopasowania -> średnia 60 s
df["core_settled"] = df.core_inf.where(df.core_inf.notna() & (df.core_inf - df.core).abs().lt(3), df.core)
df["Tin"] = df.intake_aq.where(df.intake_aq.notna(), df.Tin_tab)
df["core_src"] = np.where(df.core_nvapi.notna(), "nvapi", "table")
df.to_csv(OUT + "steady-points.csv", index=False)
if __name__ == "__main__":
    pd.set_option("display.width", 200)
    print(df[["session", "pl_pct", "gpu_pct", "case_target", "N", "C", "P", "Tin", "core_tab", "core_nvapi", "core_inf", "core_inf_se", "tau_s", "slope_end"]].round(2).to_string())
    print(df.groupby("session").size())
