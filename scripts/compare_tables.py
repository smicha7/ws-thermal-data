"""60 s / settled / model comparison for all 112 points of the second run (grid1c), plus settled-only settings, per case speed and
power limit. 60 s = grid1c raw reading (core 0.01 where logged, memory whole °C); settled = mean of settled points (core: steady
model input core_settled; memory: mem-points); model = equation (11) and the memory model for the reference session at the
point's measured intake air. Writes results-2026-10-23/compare-112.json."""
import json, os, numpy as np, pandas as pd
H = os.path.dirname(os.path.abspath(__file__))
g = pd.read_csv(os.path.join(H, "data/grid1c-2026-10-21/grid.csv"))
S = pd.read_csv(os.path.join(H, "results-2026-10-22/steady-residuals.csv")); J = json.load(open(os.path.join(H, "results-2026-10-22/steady-stats.json")))
M = pd.read_csv(os.path.join(H, "results-2026-10-23/mem-points.csv")); MJ = json.load(open(os.path.join(H, "results-2026-10-23/mem-model.json")))
P = {p["param"]: p["est"] for p in J["params"]}; Q = {k: v[0] for k, v in MJ["params"].items()}
core = lambda N, C, W, T: T + P["θ0"] + W * (P["r∞"] / 1000 + 1 / (P["gN"] * (N / 1000) ** P["m"] + P["gC"] * (C / 1500) ** P["s"]))
mem = lambda N, C, W, T: T + Q["θ0m"] + W * (Q["r∞"] / 1000 + 1 / (Q["gN"] * (N / 1000) ** Q["m"] + Q["gC"] * (C / 1500) ** Q["s"]))
ck = lambda c: 3000 if c >= 2900 else (2240 if c == 2250 else int(c))
S["ck"] = S.case_target.map(ck); M["ck"] = M.case_target.map(ck); g["ck"] = g.case_rpm_target.map(ck)
out = []
for case in (1000, 1500, 2000, 3000):
    for pl in (100, 90, 80, 70):
        gg = g[(g.ck == case) & (g.pl_pct == pl)]; ss = S[(S.ck == case) & (S.pl_pct == pl)]; mm = M[(M.ck == case) & (M.pl_pct == pl)]
        cards = sorted(set(gg.gpu_pct) | set(ss.gpu_pct)); rows = []
        for c in cards:
            a = gg[gg.gpu_pct == c]; b = ss[ss.gpu_pct == c]; m_ = mm[mm.gpu_pct == c]
            src = a.iloc[0] if len(a) else None
            N = float(src.cardA_fan_rpm) if src is not None else float(b.N.mean()); C = float(src.case_rpm) if src is not None else float(b.C.mean())
            W = float(src.power_w_sum) if src is not None else float(b.P.mean()); T = float(src.intake_c) if src is not None else float(b.Tin.mean())
            rows.append(dict(gpu=int(c), rpm=round(N), c60=(round(float(src.cardA_core_c), 1) if src is not None else None), m60=(round(float(src.cardA_mem_c)) if src is not None else None),
                             cs=(round(float(b.core_settled.mean()), 1) if len(b) else None), ms=(round(float(m_.mem_c_max.mean())) if len(m_) else None),
                             cm=round(float(core(N, C, W, T)), 1), mmod=round(float(mem(N, C, W, T)), 1)))
        out.append(dict(case=case, pl=pl, w=round(575 * pl / 100), rows=rows))
json.dump(out, open(os.path.join(H, "results-2026-10-23/compare-112.json"), "w"), indent=1)
print(sum(1 for b in out for r in b["rows"] if r["c60"] is not None), "60-s points;", sum(1 for b in out for r in b["rows"] if r["cs"] is not None), "settled cells")
b = [x for x in out if x["case"] == 1500 and x["pl"] == 90][0]; print(b["rows"])
rows = [dict(case_rpm=("full" if b["case"] == 3000 else b["case"]), pl_pct=b["pl"], **r) for b in out for r in b["rows"]]
pd.DataFrame(rows).rename(columns=dict(gpu="gpu_fan_pct", rpm="gpu_fan_rpm", c60="core_60s_c", m60="mem_60s_c", cs="core_settled_c", ms="mem_settled_c", cm="core_model_c", mmod="mem_model_c")).to_csv("/Users/smicha/Claude/gruency-site/research/data/gpu-map-compare-112.csv", index=False)
