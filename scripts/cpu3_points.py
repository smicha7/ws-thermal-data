"""cpu3 (ws298, 22 Oct 2026): 9950X full load, case 1000 rpm, radiator 1000 / 800 / 600 / minimum, each held to plateau."""
import os, pandas as pd, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
H = os.path.dirname(os.path.abspath(__file__)); import sys; RUN = sys.argv[1] if len(sys.argv) > 1 else "cpu3"; D = os.path.join(H, "data", "cpu3-2026-10-22", RUN)
s = pd.read_csv(os.path.join(D, "sweep.csv")); s["t"] = (s.ts - s.ts.iloc[0]) / 60; p = pd.read_csv(os.path.join(D, "points.csv"))
print(s.groupby("point")[["tctl_c", "ccd1_c", "ccd2_c"]].agg(["mean", "std", "min", "max"]).round(1))
fig, ax = plt.subplots(3, 1, figsize=(11, 10), sharex=True)
for k, l in (("tctl_c", "Tctl"), ("ccd1_c", "CCD1"), ("ccd2_c", "CCD2"), ("room_intake_c", "room / intake air")): ax[0].plot(s.t, s[k], lw=.8 if k != "room_intake_c" else 1.5, label=l)
for t in s.groupby("point").t.min().values[1:]: [a.axvline(t, color="k", lw=.6, ls=":") for a in ax]
ax[0].axhline(71.2, color="gray", ls="--", lw=.8, label="cpu2: case 2930 / radiator 1500 → Tctl 71.2")
ax[0].set_ylabel("°C"); ax[0].legend(fontsize=8, ncol=3); ax[0].grid(alpha=.3)
ax[0].set_title("ws298 Ryzen 9 9950X, 32 threads FMA, 200 W; case {s.case_target_rpm.iloc[0]:.0f} rpm; radiator targets {' / '.join(map(str, s.rad_target_rpm.unique()))} ({RUN}, 22 Oct 2026)", loc="left", fontsize=10)
ax[1].plot(s.t, s.rad_rpm, "C0", label="radiator rpm"); ax[1].plot(s.t, s.case_rpm, "C2", label="case rpm")
a1 = ax[1].twinx(); a1.plot(s.t, s.rad_pct, "C0:", label="radiator %"); a1.plot(s.t, s.case_pct, "C2:", label="case %"); a1.set_ylabel("fan %"); a1.set_ylim(0, 105)
ax[1].set_ylabel("rpm"); ax[1].legend(loc="upper right"); a1.legend(loc="center right"); ax[1].grid(alpha=.3)
ax[2].plot(s.t, s.pkg_w, "C3", label="package W"); a2 = ax[2].twinx(); a2.plot(s.t, s.clock_avg_mhz, "C1", lw=.7, label="avg clock MHz"); a2.set_ylabel("MHz")
ax[2].set_ylabel("W"); ax[2].set_xlabel("min"); ax[2].legend(loc="lower left"); a2.legend(loc="lower right"); ax[2].grid(alpha=.3)
fig.tight_layout(); fig.savefig(os.path.join(H, "results-2026-10-22", f"{RUN}-points.png"), dpi=110)
