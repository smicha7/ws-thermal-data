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
import noise_model, model3   # 2026-10-24: feed-forward = the primary model, fitted on steady3 alone (saturating GPU-fan conductance), core AND memory
SS_MARGIN = max(2 * float(model3.LOO), 1.0)   # rule (2026-10-22): never below 1.0 °C — safety over extra quietness

DUTY_RPM = lambda d: 180 + 28.33 * d            # ZOTAC RTX 5090 Solid (single-card study): fan duty % -> rpm (ws298 measurement)
RPM_DUTY = lambda r: (r - 180) / 28.33
CASE_MAX, CARD_MAX = 2920.0, DUTY_RPM(100)
A_CARD, A_CASE = 38.0, 33.0                      # noise proxy offsets at 1000 rpm (placeholders, to be replaced by measured dB curves)

MODES = {   # noise budget at 1 m, dBA = a CEILING (Seb 2026-10-23); comfort = °C below the core / memory limit the controller aims for when the budget allows
    "quiet":       dict(budget=30.0, comfort=(5.0, 3.0)),
    "balanced":    dict(budget=35.0, comfort=(10.0, 5.0)),
    "performance": dict(budget=40.0, comfort=(15.0, 8.0)),
}
CORE_LIMIT_DEFAULT, CORE_LIMIT_HARD = 83.0, 88.0   # core safety limit (user-adjustable, never above 88 / NVIDIA's own limits)
CASE_MIN = 800.0
PLAN_HYST_C, PLAN_HYST_DB = 0.3, 0.5
MEM_MAX, MEM_MARGIN = 100.0, 5.0   # Seb 2026-10-24: hard abort 100 °C (cards self-throttle ≈ 104 °C); acting limit = min(mode mem_limit, 100 − 5)
MEM_DEFAULT = 95.0                 # memory operating limit (controller default)
TIN_TAU, FF_HYST_DB, UP_DEADBAND, DOWN_DEADBAND, HOLD_AFTER_UP = 60.0, 0.5, 0.0, 50.0, 60.0   # ctrl2 anti-pumping (2026-10-22)
BOOST_MARGIN, BOOST_MIN_S = 1.0, 120   # transient boost after a load step: extra °C below target for the feedforward, minimum seconds


# ---------------------------------------------------------------- plant
def rf(N, C):
    n = math.sqrt(N * N + 300.0 ** 2) / 1000.0
    return CORE["k"] * n ** -CORE["m"] * (max(C, 300.0) / 1500.0) ** -CORE["q"]


def steady_ff(P, N, C, Tin, load=1.0):
    """Feed-forward steady state: core and memory from the primary model (model3.py, results-2026-10-24/steady3-fit.json)."""
    return float(model3.core(N, C, P, Tin)), float(model3.mem(N, C, P, Tin))


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
    """Literature noise at 1 m, dBA (noise_model.py): card RTX 5090 FE 32.5 + 50·log10(N/1570); 4 case SW Pro 4 120 at C and
    3 SilverStone radiator fans at their measured speed (888–2745 rpm), SW Pro 4 fit (assumption, provisional); energy sum."""
    return float(noise_model.L_total(N, C))


# ---------------------------------------------------------------- controller
def card_min(P, P_lim):   # P_lim = the CURRENT power limit in W (no 575 default: 402 W at PL 70 % is full load → 40 %)
    f = min(max((P / P_lim - 0.3) / 0.5, 0.0), 1.0)          # 30 % idle -> 40 % full load (rule in METHOD.md)
    return DUTY_RPM(30 + 10 * f)


class Controller:
    """Noise-budget controller (Seb 2026-10-23): a mode is a noise budget at 1 m (literature models, case/radiator ×7 + GPU, energy sum).
    Within the budget it picks the fan pair with the lowest predicted core. Safety: core ≤ core limit (default 83, hard 88) and memory ≤ limit
    (default 90, acts ≤ 91), each with the model margin. If the budget pair would break a limit: lower the power limit first (5 % steps,
    ≥ 30 s apart, floor 70 %); only at the PL floor may the fans exceed the budget ("over noise budget"). Floors 30 → 40 %, never 0 rpm.
    Anti-pumping (intake low-pass, plan hysteresis, down deadband, hold after rise), boost after a load step and ramps are kept."""
    def __init__(self, mode="balanced", P_stock=575.0, budget=None, core_limit=None, mem_limit=None, pl_floor=0.70):
        self.mode = mode; self.Pst = P_stock; self.m = MODES[mode]
        self.budget = budget if budget is not None else self.m["budget"]
        self.core_lim = min(core_limit if core_limit is not None else CORE_LIMIT_DEFAULT, CORE_LIMIT_HARD)
        self.mem_l = min(mem_limit if mem_limit is not None else MEM_DEFAULT, MEM_MAX - MEM_MARGIN); self.pl_floor = pl_floor
        self.N = DUTY_RPM(30); self.C = CASE_MIN; self.down = {"N": False, "C": False}; self.floor_now = DUTY_RPM(30); self.pl = 1.0; self.p_s = None; self.p_at = 0; self.t = 0; self.p_last = 0.0   # start at the idle floors
        self.plan = (self.N, self.C, 1.0, False); self.tin_f = None; self.up_at = {"N": -999, "C": -999}; self.pl_at = -999
        self.boost_at = None; self.calm_since = None; self.over_budget = False

    def mem_lim(self): return self.mem_l

    def fits(self, P, N, C, Tin, extra):
        core, mem = steady_ff(P, N, C, Tin)
        return core <= self.core_lim - SS_MARGIN - extra and mem <= self.mem_l

    def floor(self, P):
        """Card floor now: max of the demand floor (P vs stock power) and the measured one (draw ÷ current limit, as GpuControl.LoadFloor)."""
        return max(card_min(P, self.Pst), self.floor_now)

    def comfort_ok(self, P, N, C, Tin):
        core, mem = steady_ff(P, N, C, Tin); dc, dm = self.m["comfort"]
        return core <= self.core_lim - dc and mem <= self.mem_l - dm

    def best_in_budget(self, P, Tin):
        """Budget = ceiling: the QUIETEST pair within the budget that keeps core ≤ limit − comfort and memory ≤ limit − comfort (comfy=True);
        only if none does, the pair with the lowest predicted core (for each case speed: the fastest card fans still within the budget)."""
        lo = self.floor(P); quiet = cool = None
        for C in np.linspace(CASE_MIN, CASE_MAX, 43):
            if noise(lo, C) > self.budget: break
            N = lo; comfy = False
            for n in np.linspace(lo, CARD_MAX, 120):
                if noise(n, C) > self.budget: break
                N = n
                if self.comfort_ok(P, N, C, Tin): comfy = True; break
            if comfy:
                if quiet is None or noise(N, C) < quiet[0]: quiet = (noise(N, C), N, C)
                continue
            core = steady_ff(P, N, C, Tin)[0]
            if cool is None or core < cool[0]: cool = (core, N, C)
        if quiet: return quiet[1], quiet[2], True
        return (cool[1], cool[2], False) if cool else None

    def make_plan(self, P, Tin, extra=0.0):
        b = self.best_in_budget(P, Tin)
        if b is None: return self.floor(P), CASE_MIN, 1.0, True        # floors alone are louder than the budget
        N, C, _ = b
        for pl in np.arange(1.0, self.pl_floor - 1e-6, -0.05):                    # 1) power limit first
            if self.fits(P * pl, N, C, Tin, extra): return N, C, round(pl, 2), False
        best = None                                                              # 2) PL at its floor: quietest pair that holds the limits
        for C2 in np.linspace(CASE_MIN, CASE_MAX, 43):
            for n in np.linspace(self.floor(P), CARD_MAX, 120):
                if self.fits(P * self.pl_floor, n, C2, Tin, extra):
                    L = noise(n, C2)
                    if best is None or L < best[0]: best = (L, n, C2)
                    break
        if best: return best[1], best[2], self.pl_floor, True
        return CARD_MAX, CASE_MAX, self.pl_floor, True

    def keep_plan(self, new, P):
        """Hysteresis: keep the current pair while it is in budget, holds the limits and the new one is not ≥ 0.3 °C cooler."""
        N, C, pl, ov = self.plan
        if ov or new[3] or pl != new[2] or noise(N, C) > self.budget + 0.05 or N < self.floor(P): return new
        if not self.fits(P * pl, N, C, self.tin_f, 0.0): return new
        if self.comfort_ok(P * new[2], new[0], new[1], self.tin_f):   # comfort reachable: keep while current is comfy and new is < 0.5 dB quieter
            return self.plan if self.comfort_ok(P * pl, N, C, self.tin_f) and noise(N, C) - noise(new[0], new[1]) < PLAN_HYST_DB else new
        return self.plan if steady_ff(P, N, C, self.tin_f)[0] - steady_ff(P, new[0], new[1], self.tin_f)[0] < PLAN_HYST_C else new

    def step(self, core, mem, P_meas, Tin, dt=1.0, limit_w=None):
        self.t += dt
        self.floor_now = card_min(P_meas, limit_w if limit_w else self.pl * self.Pst)
        dem = P_meas / self.pl if P_meas >= 0.97 * self.pl * self.Pst else P_meas
        if self.p_s is not None and dem > 1.2 * self.p_s and self.t > 1: self.boost_at = self.t
        if self.p_s is None or dem >= self.p_s: self.p_s, self.p_at = dem, self.t
        elif dem >= 0.97 * self.p_s: self.p_at = self.t
        elif self.t - self.p_at > 300: self.p_s += (dem - self.p_s) * dt / 60
        self.tin_f = Tin if self.tin_f is None else self.tin_f + (Tin - self.tin_f) * dt / TIN_TAU
        if self.boost_at is not None and self.t - self.boost_at >= BOOST_MIN_S and core < self.core_lim - 3: self.boost_at = None
        if self.boost_at is not None: self.plan = self.make_plan(self.p_s, self.tin_f, BOOST_MARGIN)
        elif self.t % 5 < dt or P_meas > self.p_last + 100: self.plan = self.keep_plan(self.make_plan(self.p_s, self.tin_f), self.p_s)
        self.p_last = P_meas
        Nw, Cw, pl_t, over = self.plan
        # measured safety: over a limit → lower the PL beyond the plan; at the PL floor push the fans (over budget)
        exc = max(core - self.core_lim, mem - self.mem_l)
        if exc > 0:
            self.calm_since = None
            if self.pl > self.pl_floor + 1e-6 and self.t - self.pl_at >= 30: self.pl = max(self.pl_floor, self.pl - 0.05); self.pl_at = self.t
            elif self.pl <= self.pl_floor + 1e-6: Nw = min(CARD_MAX, max(Nw, self.N) + 100 * exc); Cw = min(CASE_MAX, max(Cw, self.C) + 50 * exc); over = True
        elif exc < -2: self.calm_since = self.calm_since or self.t
        else: self.calm_since = None
        calm = self.calm_since is not None and self.t - self.calm_since >= 60
        if pl_t < self.pl - 1e-6 and self.t - self.pl_at >= 30: self.pl = max(pl_t, self.pl - 0.05); self.pl_at = self.t   # plan: down in 5 % steps ≥ 30 s apart
        elif pl_t > self.pl + 1e-6 and (calm or exc < -2) and self.t - self.pl_at >= 30: self.pl = min(pl_t, self.pl + 0.05); self.pl_at = self.t
        Nw = max(Nw, self.floor(self.p_s))
        for attr, want in (("N", Nw), ("C", Cw)):
            cur = getattr(self, attr)
            if want > cur + UP_DEADBAND: cur = min(want, cur + 150 * dt); self.up_at[attr] = self.t; self.down[attr] = False
            elif not ((calm or exc < -2) and self.t - self.up_at[attr] >= HOLD_AFTER_UP): self.down[attr] = False
            elif self.down[attr] or want < cur - DOWN_DEADBAND:   # dead band only decides whether to START a descent; a started one finishes at the target
                cur = max(want, cur - 15 * dt); self.down[attr] = cur > want
            setattr(self, attr, cur)
        self.over_budget = over or noise(self.N, self.C) > self.budget + 0.3
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
    N, C = getattr(ctl, "N", 0.0), getattr(ctl, "C", 0.0); lim = 1.0
    for t in range(T):
        P_dem = P_of_t(t); load = 1.0 if P_dem > 100 else 0.0
        P = min(P_dem, 575 * lim)
        core, mem = pl.step(P, N, C, Tin_of_t(t), load)
        N, C, lim = ctl.step(core, mem, P, Tin_of_t(t))
        rows.append((t, P, core, mem, N, C, lim, noise(N, C)))
    return np.array(rows)


def metrics(r, core_lim=CORE_LIMIT_DEFAULT, mem_lim=MEM_DEFAULT, budget=None):
    core, mem = r[:, 2], r[:, 3]
    d = np.sign(np.diff(r[:, 4])); d = d[d != 0]; rev = int((np.diff(d) != 0).sum())   # fan direction reversals = audible "pumping"
    return dict(peak=round(float(core.max()), 1), mem_peak=round(float(mem.max()), 1), s_over=int(((core > core_lim) | (mem > mem_lim)).sum()),
                noise_mean=round(float(r[:, 7].mean()), 1), noise_max=round(float(r[:, 7].max()), 1),
                s_over_budget=int((r[:, 7] > budget + 0.3).sum()) if budget is not None else None,
                pl_min=round(float(r[:, 6].min()), 2), s_pl_cut=int((r[:, 6] < 0.999).sum()),
                work_W=round(float(r[:, 1].mean()), 1), card_reversals_per_min=round(rev / (len(r) / 60), 2))


SCEN = {
    "idle 30 W": (lambda t: 30, lambda t: 19.0),
    "light 30->150 W": (lambda t: 30 if t < 120 else 150, lambda t: 19.0),
    "step 30->575 W": (lambda t: 30 if t < 120 else 575, lambda t: 19.0),
    "intake 19->30 °C": (lambda t: 575, lambda t: 19.0 if t < 900 else min(30.0, 19.0 + (t - 900) / 60)),
    "bursts 60 s on/off": (lambda t: 575 if (t // 60) % 2 else 60, lambda t: 19.0),
}


def self_check():
    c, m = steady(575, DUTY_RPM(40), 1000, 19)
    assert abs(c - 83) < 1.5 and abs(m - 91.6) < 2.0, (c, m)            # ws298: 82.5 / 90 measured (grid1c start, val1)
    ctl = Controller("quiet"); N, C, pl, ov = ctl.make_plan(575, 19.3)
    assert abs(noise(N, C) - 30) < 0.5 and pl == 1.0 and not ov, (N, C, pl, noise(N, C))   # reference: Quiet 42 % / 925 rpm, 30 dBA
    assert abs(card_min(402, 402.5) - DUTY_RPM(40)) < 0.5                    # PL 70 %, 402 W = full load → 40 % (not 38 % as with ÷ 575)
    fl = Controller("quiet", budget=25.0)
    for _ in range(300): Nf, _, _ = fl.step(70.0, 80.0, 402.0, 20.0, limit_w=402.5)
    assert (Nf - 180) / 28.33 >= 39.95, Nf
    print("self-check ok")


if __name__ == "__main__":
    self_check()
    res = {}
    fig, axs = plt.subplots(len(SCEN), 2, figsize=(14, 4.2 * len(SCEN)))
    for row, (name, (Pf, Tf)) in zip(axs, SCEN.items()):
        for label, ctl, col in [("factory (driver curve, case 1000)", Factory(), "gray")] + [(f"WS.Sensor {k} ({MODES[k]['budget']:.0f} dBA)", Controller(k), c) for k, c in (("quiet", "tab:green"), ("balanced", "tab:blue"), ("performance", "tab:red"))]:
            r = run(ctl, Pf, Tf)
            res.setdefault(name, {})[label] = metrics(r, budget=getattr(ctl, "budget", None))
            row[0].plot(r[:, 0] / 60, r[:, 2], color=col, label=label); row[0].plot(r[:, 0] / 60, r[:, 3], color=col, ls=":", lw=1)
            row[1].plot(r[:, 0] / 60, r[:, 7], color=col)
        row[0].axhline(CORE_LIMIT_DEFAULT, color="k", lw=.7, ls="--"); row[0].axhline(MEM_DEFAULT, color="k", lw=.7, ls=":")
        row[0].set_title(f"{name}: core (solid) / memory (dotted) °C; limits 83 / 90 °C", loc="left"); row[0].grid(alpha=.3); row[0].legend(fontsize=8)
        row[1].set_title("total noise at 1 m, dBA (literature models)", loc="left"); row[1].grid(alpha=.3)
        for a in row: a.set_xlabel("min")
    fig.suptitle("RTX 5090 (ws298 model M2-pow): WS.Sensor noise-budget controller vs factory — simulation", y=0.995)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "controller-sim.png"), dpi=120)
    json.dump(res, open(os.path.join(OUT, "controller-sim.json"), "w"), indent=1, ensure_ascii=False)
    for s_, d in res.items():
        print(s_)
        for k, v in d.items(): print(f"  {k:38} {v}")
