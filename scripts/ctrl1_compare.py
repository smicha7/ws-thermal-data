"""ctrl1 (ws298, 2026-10-22): measured ctrl.csv vs controller_sim.py with the same load pattern and measured intake."""
import sys, os, json, glob, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(__file__)); import controller_sim as cs
D = os.path.join(os.path.dirname(__file__), "data"); OUT = os.path.join(os.path.dirname(__file__), "results-2026-10-22")

def rev_per_min(x):
    d = np.sign(np.diff(np.round(x / 25))); d = d[d != 0]; return (np.diff(d) != 0).sum() / (len(x) / 60)

def sim(m, P_dem, tin):
    ctl = cs.Controller(m); pl = cs.Plant(tin[0]); core, mem = cs.steady(30, 0, 1000, tin[0], 0)
    pl.ts = core - 30 * cs.CORE["Rjs"] - cs.CORE["th0"]; pl.tm = mem; N, C, lim = ctl.N, ctl.C, 1.0; rows = []
    for t in range(len(P_dem)):
        P = min(P_dem[t], 575 * lim); core, mem = pl.step(P, N, C, tin[t], 1.0 if P_dem[t] > 100 else 0.0)
        N, C, lim = ctl.step(core, mem, P, tin[t]); rows.append((P, core, mem, N, C, lim))
    return np.array(rows)

res = {}
for mode in ("balanced", "quiet", "performance"):
    fig, axs = plt.subplots(2, 3, figsize=(17, 8), sharex="col")
    for col, sc in enumerate(("step", "bursts")):
        f = glob.glob(os.path.join(D, "ctrl1-2026-10-22", f"{mode}-{sc}", "ctrl.csv"))[0]
        d = pd.read_csv(f); t = d.t_s.values / 60
        tin = d.intake_c.ffill().bfill().values
        P_dem = np.where(d.load.values > 0, 575.0, d.P_w.values)
        s = sim(mode, P_dem, tin); tgt = cs.MODES[mode]["target"]
        core = d.core_nvapi_c.fillna(d.core_c).values; on = d.load.values > 0; first = np.argmax(on)
        late = (d.t_s.values >= d.t_s.values[first] + 600) & on
        r = dict(peak_core=round(float(core[on].max()), 1), sim_peak_core=round(float(s[on, 1].max()), 1),
                 s_over_target_1=int((core > tgt + 1).sum()), sim_s_over=int((s[:, 1] > tgt + 1).sum()),
                 core_late_mean=round(float(core[late].mean()), 1) if late.any() else None, sim_core_late=round(float(s[late, 1].mean()), 1) if late.any() else None,
                 mem_peak=round(float(d.mem_c[on].max()), 1), sim_mem_peak=round(float(s[on, 2].max()), 1),
                 card_rpm_mean_loaded=round(float(d.gpu_rpm[on].mean())), sim_card_rpm=round(float(s[on, 3].mean())),
                 case_rpm_mean=round(float(d.case_rpm.mean())), case_cmd_mean=round(float(d.C_cmd_rpm.mean())), sim_case=round(float(s[:, 4].mean())),
                 pl_min=float(d.pl.min()), sim_pl_min=round(float(s[:, 5].min()), 2), P_mean_loaded=round(float(d.P_w[on].mean())),
                 card_rev_per_min=round(rev_per_min(d.N_cmd_rpm.values), 2), sim_rev_per_min=round(rev_per_min(s[:, 3]), 2), intake=round(float(np.nanmean(tin)), 2))
        res[f"{mode}-{sc}"] = r
        a = axs[0, col]; a.plot(t, core, "C0", label="core measured"); a.plot(t, s[:, 1], "C0--", label="core sim")
        a.plot(t, d.mem_c, "C3", label="memory measured"); a.plot(t, s[:, 2], "C3--", label="memory sim"); a.axhline(tgt, color="k", lw=.7, ls=":")
        a.set_title(f"{mode} / {sc}: °C", loc="left"); a.legend(fontsize=7); a.grid(alpha=.3)
        b = axs[1, col]; b.plot(t, d.gpu_rpm, "C2", label="card rpm measured"); b.plot(t, s[:, 3], "C2--", label="card rpm sim")
        b.plot(t, d.case_rpm, "C4", label="case rpm measured"); b.plot(t, s[:, 4], "C4--", label="case rpm sim"); b.set_xlabel("min")
        sec = b.secondary_yaxis("right", functions=(cs.RPM_DUTY, cs.DUTY_RPM)); sec.set_ylabel("card fan %"); b.legend(fontsize=7); b.grid(alpha=.3)
        b.set_title("fans rpm (card % on right axis)", loc="left")
        c = axs[col, 2]; c.plot(t, d.pl * 100, "C1", label="PL measured %"); c.plot(t, s[:, 5] * 100, "C1--", label="PL sim %")
        c2 = c.twinx(); c2.plot(t, d.P_w, "C7", lw=.6); c2.set_ylabel("power W"); c.set_title(f"{sc}: power limit % / power W", loc="left"); c.legend(fontsize=7); c.grid(alpha=.3)
    fig.suptitle(f"ws298 RTX 5090 — WS.Sensor controller ({mode}, target {cs.MODES[mode]['target']} °C): measured vs simulation", y=.995)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, f"ctrl1-{mode}.png"), dpi=110); plt.close(fig)
json.dump(res, open(os.path.join(OUT, "ctrl1-compare.json"), "w"), indent=1)
for k, v in res.items(): print(k, v)
