"""The primary settled-temperature model (steady3 fit, results-2026-10-24/steady3-fit.json): one place for every consumer.
Form "GPU-fan saturation (Hill)": T − Tin = θ0 + P·[r∞/1000 + 1/(gN·n^m/(n½^m + n^m) + gC·c^s)], n = N/1000, c = C/1500.
core(N, C, P, Tin), mem(N, C, P, Tin); P_core / P_mem = {name: (est, se_HC3)}; LOO = leave-one-out RMSE of the core."""
import json, os
import numpy as np
_J = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results-2026-10-24/steady3-fit.json")))
FORM = _J["choice"]["core"]; assert FORM == _J["choice"]["mem"] == "GPU-fan saturation (Hill)", _J["choice"]   # ponytail: consumers assume the Hill form
def _p(q): f = _J["forms"][q][FORM]; return {nm: (x, s) for nm, x, s in zip(f["names"], f["x"], f["se_HC3"])}
P_core, P_mem = _p("core"), _p("mem")
LOO, LOO_MEM = _J["forms"]["core"][FORM]["loo"], _J["forms"]["mem"][FORM]["loo"]
def _f(p, N, C, P, Tin):
    n, c = np.maximum(N, 300.0) / 1000, np.maximum(C, 300.0) / 1500; v = {k: x for k, (x, _) in p.items()}
    return Tin + v["θ0"] + P * (v["r∞"] / 1000 + 1 / (v["gN"] * n ** v["m"] / (v["n½"] ** v["m"] + n ** v["m"]) + v["gC"] * c ** v["s"]))
core = lambda N, C, P, Tin: _f(P_core, N, C, P, Tin)
mem = lambda N, C, P, Tin: _f(P_mem, N, C, P, Tin)
if __name__ == "__main__":
    assert abs(core(1312, 1600, 575, 19.33) - 79.5) < 1.0, core(1312, 1600, 575, 19.33)   # anchor point measured 79.3–79.7 °C
    print(round(float(core(1312, 1600, 575, 19.33)), 2), round(float(mem(1312, 1600, 575, 19.33)), 2), P_core)
