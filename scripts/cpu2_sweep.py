"""cpu2 (ws298, 22 Oct 2026): Ryzen 9 9950X full load, radiator fans stepped down 100 rpm / 10 s to 1500 rpm, then held."""
import os, sys, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
H = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(H, "data", "cpu2-2026-10-22")
s = pd.read_csv(os.path.join(D, "cpu2", "sweep.csv")); s["t"] = s.ts - s.ts.iloc[0]
c = pd.read_csv(os.path.join(D, "cpu2", "cpu.csv"))
warm = s[s.stage == 0]; w60 = warm[warm.ts >= warm.ts.max() - 60]
rows = []
for tg, g in s[s.stage == 1].groupby("target_rpm", sort=False):
    sl = np.polyfit(g.t, g.tctl_c, 1)[0] if len(g) > 2 else np.nan
    e = g.iloc[-1]
    rows.append(dict(target_rpm=int(tg), rad_rpm_end=int(e.rad_rpm), rad_pct_end=round(e.rad_pct, 1), tctl_end=e.tctl_c, ccd1_end=e.ccd1_c, ccd2_end=e.ccd2_c,
                     slope_c_per_s=round(sl, 3), pkg_w=round(g.pkg_w.mean(), 1), clock_avg=round(g.clock_avg_mhz.mean())))
st = pd.DataFrame(rows)
hold = s[s.stage == 2]; h60 = hold[hold.ts >= hold.ts.max() - 60]
summ = dict(warm_tctl=round(w60.tctl_c.mean(), 1), warm_ccd1=round(w60.ccd1_c.mean(), 1), warm_ccd2=round(w60.ccd2_c.mean(), 1), warm_rpm=round(w60.rad_rpm.mean()),
            hold_tctl=round(h60.tctl_c.mean(), 1), hold_ccd1=round(h60.ccd1_c.mean(), 1), hold_ccd2=round(h60.ccd2_c.mean(), 1), hold_rpm=round(h60.rad_rpm.mean()), hold_pct=round(h60.rad_pct.mean(), 1),
            hold_pkg=round(h60.pkg_w.mean(), 1), hold_clock=round(h60.clock_avg_mhz.mean()), warm_clock=round(w60.clock_avg_mhz.mean()), warm_pkg=round(w60.pkg_w.mean(), 1),
            tctl_max=float(s.tctl_c.max()), hold_s=int(hold.t.max() - hold.t.min()), throttle_max=float(c.throttle.max()), vrm_max=float(c.vrm_c.max()), intake=round(c.intake_c.mean(), 2))
print(st.to_string(index=False)); print(summ)
st.to_csv(os.path.join(D, "steps.csv"), index=False)
fig, ax = plt.subplots(3, 1, figsize=(11, 10), sharex=True)
for k, l in (("tctl_c", "Tctl"), ("ccd1_c", "CCD1"), ("ccd2_c", "CCD2")): ax[0].plot(s.t, s[k], label=l)
for x in (warm.t.max(), hold.t.min()): ax[0].axvline(x, color="k", lw=.6, ls=":")
ax[0].set_ylabel("°C"); ax[0].legend(); ax[0].grid(alpha=.3)
ax[0].set_title("ws298 Ryzen 9 9950X, 32 threads FMA, case fans 100 %: radiator 100 % → −100 rpm every 10 s → hold 1500 rpm (cpu2, 22 Oct 2026)", loc="left", fontsize=10)
ax[1].plot(s.t, s.rad_rpm, "C0", label="radiator rpm (measured)"); ax[1].plot(s.t, s.target_rpm, "C0--", lw=1, label="target rpm")
a1 = ax[1].twinx(); a1.plot(s.t, s.rad_pct, "C1", lw=1, label="radiator %"); a1.set_ylabel("radiator fan %"); a1.set_ylim(0, 105)
ax[1].set_ylabel("rpm"); ax[1].legend(loc="lower left"); a1.legend(loc="lower right"); ax[1].grid(alpha=.3)
ax[2].plot(s.t, s.pkg_w, "C3", label="package W"); a2 = ax[2].twinx(); a2.plot(s.t, s.clock_avg_mhz, "C2", lw=.8, label="avg clock MHz"); a2.set_ylabel("MHz")
ax[2].set_ylabel("W"); ax[2].set_xlabel("s"); ax[2].legend(loc="lower left"); a2.legend(loc="lower right"); ax[2].grid(alpha=.3)
fig.tight_layout(); fig.savefig(os.path.join(H, "results-2026-10-22", "cpu2-sweep.png"), dpi=110)
