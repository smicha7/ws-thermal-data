"""WS.Sensor model-based thermal-acoustic controller — design + simulation (Seb 2026-10-22).

Plant (results-2026-10-21/dyn-model.json, best = M2-pow, 2 RC nodes):
  die Tj = Ts + P*Rjs (Cj ~ 0, quasi-static);  Cs dTs/dt = P - (Ts - Tin)/(ra + Rf);  core = Tj + th0
  Rf(N, C) = k * n^-m * (C/1500)^-q,  n = sqrt(N^2 + 300^2)/1000   (N card fan rpm, C case rpm)
  memory: tau dTm/dt = Tin + lam*(Ts - Tin) + a1*P + a0*load + thm - Tm
Controller (per control step dt = 1 s, same logic as the planned C# port):
  feedforward every 5 s — minimum noise (N, C) with steady core <= target - margin and memory <= mem_max - margin;
  if even the mode's noise ceiling is not enough: power limit lowered as late as possible (5 % steps, never in Performance);
  feedback — PI on core error, adds to N first, then to C (anti-windup at limits);
  limits — up fast (+150 rpm/s), down slow (-15 rpm/s), down only after 60 s below target - 1.5 K; card min 30 -> 40 % by load;
  never 0 rpm under load.
Noise proxy (until iPhone dB curves exist): per fan group L = 50*log10(rpm/1000) + A; total = energy sum.
Run:  .venv/bin/python controller_sim.py      (self-check, scenarios, plots -> results-2026-10-22/controller-*.png)
"""
import json, math, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results-2026-10-22")
M = json.load(open(os.path.join(HERE, "results-2026-10-21", "dyn-model.json")))
CORE = M["M2-pow"]["params"]; MEM = M["mem"]["params"]
# Feed-forward uses the model fitted DIRECTLY to steady points (koncertmistrz/Seb 2026-10-22: the static part of the dynamic
# model is biased on steady points). results-2026-10-22/steady-stats.json, form "cond": core − Tin = θ0 + P·(r∞ + 1/(gN·n^m + gC·c^s)),
# n = N/1000, c = C/1500; margin = 2 × leave-one-out RMSE of that model (≈ 95 %). The dynamic model is only the simulated plant.
SS = json.load(open(os.path.join(HERE, "results-2026-10-22", "steady-stats.json")))
SP = {d["param"]: d["est"] for d in SS["params"]}
SS_MARGIN = max(2 * float(SS["loo"]), 1.0)   # rule (2026-10-22): never below 1.0 °C — safety over extra quietness

DUTY_RPM = lambda d: 180 + 28.33 * d            # RTX 5090 FE: fan duty % -> rpm (ws298 measurement)
RPM_DUTY = lambda r: (r - 180) / 28.33
CASE_MAX, CARD_MAX = 2920.0, DUTY_RPM(100)
A_CARD, A_CASE = 38.0, 33.0                      # noise proxy offsets at 1000 rpm (placeholders, to be replaced by measured dB curves)

MODES = {   # target core °C, card / case noise ceilings (rpm), may lower the power limit
    "quiet":       dict(target=80.0, card_max=1800.0, case_max=1200.0, pl_cut=True),
    "balanced":    dict(target=77.0, card_max=2300.0, case_max=1500.0, pl_cut=True),
    "performance": dict(target=72.0, card_max=CARD_MAX, case_max=CASE_MAX, pl_cut=False),
}
MEM_MAX, MEM_MARGIN = 100.0, 4.0
TIN_TAU, FF_HYST_DB, UP_DEADBAND, DOWN_DEADBAND, HOLD_AFTER_UP = 60.0, 0.5, 0.0, 50.0, 60.0   # ctrl2 anti-pumping (2026-10-22)


# ---------------------------------------------------------------- plant
def rf(N, C):
    n = math.sqrt(N * N + 300.0 ** 2) / 1000.0
    return CORE["k"] * n ** -CORE["m"] * (max(C, 300.0) / 1500.0) ** -CORE["q"]


def steady_ff(P, N, C, Tin, load=1.0):
    """Feed-forward steady state: core from steady-stats.json (cond), memory from the dynamic model's static part (no steady memory fit yet)."""
    n, c = max(N, 300.0) / 1000, max(C, 300.0) / 1500
    core = Tin + SP["θ0"] + P * (SP["r∞"] / 1000 + 1 / (SP["gN"] * n ** SP["m"] + SP["gC"] * c ** SP["s"]))
    return core, steady(P, N, C, Tin, load)[1]


def steady(P, N, C, Tin, load=1.0):
    ts = Tin + P * (CORE["ra"] + rf(N, C))
    core = ts + P * CORE["Rjs"] + CORE["th0"]
    mem = Tin + MEM["lam"] * (ts - Tin) + MEM["a1"] * P + MEM["a0"] * load + MEM["thm"]
    return core, mem


class Plant:
    def __init__(self, Tin=19.0):
        self.ts = Tin + 5; self.tm = Tin + 15

    def step(self, P, N, C, Tin, load, dt=1.0):
        R = CORE["ra"] + rf(N, C)
        self.ts += dt * (P - (self.ts - Tin) / R) / CORE["Cs"]
        tm_inf = Tin + MEM["lam"] * (self.ts - Tin) + MEM["a1"] * P + MEM["a0"] * load + MEM["thm"]
        self.tm += dt * (tm_inf - self.tm) / max(MEM["tau"], 1.0)
        return self.ts + P * CORE["Rjs"] + CORE["th0"], self.tm


def noise(N, C):
    lg = 50 * math.log10(max(N, 300) / 1000) + A_CARD
    lc = 50 * math.log10(max(C, 300) / 1000) + A_CASE
    return 10 * math.log10(10 ** (lg / 10) + 10 ** (lc / 10))


# ---------------------------------------------------------------- controller
def card_min(P, P_lim=575.0):
    f = min(max((P / P_lim - 0.3) / 0.5, 0.0), 1.0)          # 30 % idle -> 40 % full load (rule in METHOD.md)
    return DUTY_RPM(30 + 10 * f)


class Controller:
    def __init__(self, mode="balanced", P_stock=575.0):
        self.m = MODES[mode]; self.mode = mode; self.Pst = P_stock
        self.N = DUTY_RPM(40); self.C = 1000.0; self.pl = 1.0
        self.i = 0.0; self.p_s = None; self.ff = (self.N, self.C, 1.0); self.cool_since = None; self.t = 0; self.p_last = 0.0; self.p_at = 0; self.pl_at = -999
        self.tin_f = None; self.up_at = {"N": -999, "C": -999}   # ctrl2: filtered intake for the feedforward, time of last up-ramp per fan group

    def feedforward(self, P, Tin):
        tgt = self.m["target"] - SS_MARGIN; best = None
        for C in np.linspace(800, self.m["case_max"], 18):
            for N in np.linspace(card_min(P, self.Pst), self.m["card_max"], 40):
                core, mem = steady_ff(P, N, C, Tin)
                if core <= tgt and mem <= MEM_MAX - MEM_MARGIN:
                    L = noise(N, C)
                    if best is None or L < best[0]: best = (L, N, C)
                    break                                     # smallest N for this C that works
        if best: return best[1], best[2], 1.0
        if not self.m["pl_cut"]: return self.m["card_max"], self.m["case_max"], 1.0
        for pl in np.arange(0.95, 0.69, -0.05):              # fans at the ceiling are not enough -> lower the power limit
            core, mem = steady_ff(P * pl, self.m["card_max"], self.m["case_max"], Tin)
            if core <= tgt and mem <= MEM_MAX - MEM_MARGIN: return self.m["card_max"], self.m["case_max"], pl
        return self.m["card_max"], self.m["case_max"], 0.70

    def keep_ff(self, new):
        """ctrl2 hysteresis: keep the current (N, C) while it still meets the targets and the new optimum is not clearly quieter (ties flipped case 1174 ↔ 1548 rpm on ws298)."""
        N, C, pl = self.ff
        if new[2] != 1.0 or pl != 1.0 or N < card_min(self.p_s, self.Pst) or N > self.m["card_max"] or C > self.m["case_max"]: return new
        core, mem = steady_ff(self.p_s, N, C, self.tin_f)
        if core <= self.m["target"] - SS_MARGIN and mem <= MEM_MAX - MEM_MARGIN and noise(new[0], new[1]) > noise(N, C) - FF_HYST_DB: return self.ff
        return new

    def step(self, core, mem, P_meas, Tin, dt=1.0):
        self.t += dt
        dem = P_meas / self.pl if P_meas >= 0.97 * self.pl * self.Pst else P_meas   # demand: a capped card would draw more without the cap
        if self.p_s is None or dem >= self.p_s: self.p_s, self.p_at = dem, self.t           # load estimate: up at once,
        elif dem >= 0.97 * self.p_s: self.p_at = self.t                                       # ctrl2: a near-peak burst renews the hold
        elif self.t - self.p_at > 300: self.p_s += (dem - self.p_s) * dt / 60                  # held 5 min, then down slowly (no pumping on bursty loads)
        self.tin_f = Tin if self.tin_f is None else self.tin_f + (Tin - self.tin_f) * dt / TIN_TAU   # ctrl2: intake low-pass (sensor noise flipped the optimum)
        if self.t % 5 < dt or P_meas > self.p_last + 100: self.ff = self.keep_ff(self.feedforward(self.p_s, self.tin_f))   # load step: recompute now
        self.p_last = P_meas
        Nff, Cff, pl_t = self.ff
        e = core - self.m["target"]
        if abs(e) < 3 and not ((self.N >= self.m["card_max"] and e > 0) or (self.N <= card_min(self.p_s) and e < 0)):
            self.i = min(max(self.i + e * dt, -150), 300)       # integrate only near the target (no idle windup); anti-windup at limits
        u = 60.0 * max(e, 0.0) + 1.2 * self.i                   # rpm; P only pushes up (a cool card never drags fans below the feedforward), I trims both ways near target
        Nw = min(max(Nff + u, card_min(self.p_s)), self.m["card_max"])
        spill = max(Nff + u - self.m["card_max"], 0)            # card at ceiling -> rest goes to the case fans
        Cw = min(max(Cff + spill * 0.5, 800), self.m["case_max"])
        if e < -1.5: self.cool_since = self.cool_since or self.t
        else: self.cool_since = None
        may_drop = self.cool_since is not None and self.t - self.cool_since >= 60
        for attr, want in (("N", Nw), ("C", Cw)):
            cur = getattr(self, attr)
            if want > cur + UP_DEADBAND: cur = min(want, cur + 150 * dt); self.up_at[attr] = self.t
            elif want < cur - DOWN_DEADBAND and may_drop and self.t - self.up_at[attr] >= HOLD_AFTER_UP: cur = max(want, cur - 15 * dt)   # ctrl2: down only past a deadband and ≥ 60 s after the last rise
            setattr(self, attr, cur)
        # power limit: down in 5 % steps at most every 30 s and never below what the model needs; back up at once when the core is below target − 1.5 °C
        if pl_t < self.pl - 1e-6 and self.t - self.pl_at >= 30: self.pl = max(pl_t, self.pl - 0.05); self.pl_at = self.t
        elif pl_t > self.pl + 1e-6 and (e < -1.5 or pl_t >= 1.0): self.pl = min(pl_t, 1.0)
        return self.N, self.C, self.pl


class Factory:
    """NVIDIA driver curve (recorded on ws298, heating branch) + BIOS case fans at a fixed 1000 rpm."""
    PTS = [(30, 0), (50, 30), (60, 36), (70, 48), (80, 66), (85, 80), (95, 100)]

    def step(self, core, mem, P_meas, Tin, dt=1.0):
        d = np.interp(core, [p[0] for p in self.PTS], [p[1] for p in self.PTS])
        return (DUTY_RPM(d) if d > 0 else 0.0), 1000.0, 1.0


# ---------------------------------------------------------------- scenarios
def run(ctl, P_of_t, Tin_of_t, T=2400):
    pl = Plant(Tin_of_t(0)); rows = []; core, mem = steady(30, 0, 1000, Tin_of_t(0), 0)
    pl.ts = core - 30 * CORE["Rjs"] - CORE["th0"]; pl.tm = mem
    N = C = 0; lim = 1.0
    for t in range(T):
        P_dem = P_of_t(t); load = 1.0 if P_dem > 100 else 0.0
        P = min(P_dem, 575 * lim)
        core, mem = pl.step(P, N, C, Tin_of_t(t), load)
        N, C, lim = ctl.step(core, mem, P, Tin_of_t(t))
        rows.append((t, P, core, mem, N, C, lim, noise(N, C)))
    return np.array(rows)


def metrics(r, target):
    core = r[:, 2]; t_over = int((core > target + 1).sum())
    d = np.sign(np.diff(r[:, 4])); d = d[d != 0]; rev = int((np.diff(d) != 0).sum())   # fan direction reversals = audible "pumping"
    return dict(peak=round(float(core.max()), 1), mem_peak=round(float(r[:, 3].max()), 1), s_over=t_over,
                noise_mean=round(float(r[:, 7].mean()), 1), work_W=round(float(r[:, 1].mean()), 1), card_reversals_per_min=round(rev / (len(r) / 60), 2))


SCEN = {
    "step 30->575 W": (lambda t: 30 if t < 120 else 575, lambda t: 19.0),
    "intake 19->30 °C": (lambda t: 575, lambda t: 19.0 if t < 900 else min(30.0, 19.0 + (t - 900) / 60)),
    "bursts 60 s on/off": (lambda t: 575 if (t // 60) % 2 else 60, lambda t: 19.0),
}


def self_check():
    c, m = steady(575, DUTY_RPM(40), 1000, 19)
    assert abs(c - 83) < 1.5 and abs(m - 91.6) < 2.0, (c, m)            # ws298: 82.5 / 90 measured (grid1c start, val1)
    c, m = steady(575, DUTY_RPM(100), 2920, 19)
    assert c < 66, c
    ctl = Controller("balanced"); r = run(ctl, *SCEN["step 30->575 W"], T=1500)
    assert r[-300:, 2].max() < MODES["balanced"]["target"] + 0.7 and r[:, 4].min() > 0, r[-300:, 2].max()
    print("self-check ok")


if __name__ == "__main__":
    self_check()
    res = {}
    fig, axs = plt.subplots(len(SCEN), 2, figsize=(14, 4.2 * len(SCEN)))
    for row, (name, (Pf, Tf)) in zip(axs, SCEN.items()):
        for label, ctl, col in [("factory (driver curve, case 1000)", Factory(), "gray")] + [(f"WS.Sensor {k}", Controller(k), c) for k, c in (("quiet", "tab:green"), ("balanced", "tab:blue"), ("performance", "tab:red"))]:
            r = run(ctl, Pf, Tf)
            tgt = MODES.get(label.split()[-1], MODES["balanced"])["target"]
            res.setdefault(name, {})[label] = metrics(r, tgt)
            row[0].plot(r[:, 0] / 60, r[:, 2], color=col, label=label); row[0].plot(r[:, 0] / 60, r[:, 3], color=col, ls=":", lw=1)
            row[1].plot(r[:, 0] / 60, r[:, 4], color=col); row[1].plot(r[:, 0] / 60, r[:, 5], color=col, ls="--", lw=1)
        row[0].set_title(f"{name}: core (solid) / memory (dotted) °C", loc="left"); row[0].grid(alpha=.3); row[0].legend(fontsize=8)
        row[1].set_title("card fan rpm (solid) / case rpm (dashed)", loc="left"); row[1].grid(alpha=.3)
        sec = row[1].secondary_yaxis("right", functions=(RPM_DUTY, DUTY_RPM)); sec.set_ylabel("card fan duty %")
        for a in row: a.set_xlabel("min")
    fig.suptitle("RTX 5090 (ws298 model M2-pow): WS.Sensor model-based controller vs factory — simulation", y=0.995)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "controller-sim.png"), dpi=120)
    json.dump(res, open(os.path.join(OUT, "controller-sim.json"), "w"), indent=1, ensure_ascii=False)
    for s, d in res.items():
        print(s)
        for k, v in d.items(): print(f"  {k:36} {v}")
