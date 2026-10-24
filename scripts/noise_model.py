"""Literature-based fan noise at 1 m, dBA (provisional until our own sound map) — one place for every consumer.
Card: Lg = 32.5 + 50·log10(N/1570) (GamersNexus anchor, fan law).
Case: 4 × be quiet! Silent Wings Pro 4 120 (aquaero fan 1), Lf(rpm) = −167.1 + 60.2·log10(rpm) (Hardware Busters fit).
Radiator: 3 × SilverStone Hailstone 360 stock fans (aquaero fan 2); no solid independent noise data, so the SW Pro 4 fit is used
(similar construction, Seb 2026-10-24; assumption, provisional), evaluated at the radiator's MEASURED speed: on steady3 it follows
the case target but floors at 888 rpm and tops out at 2745 rpm. Case fans top out at 2920 rpm. Total = energy sum."""
import numpy as np
_hwb = np.array([(1281, 20), (1573, 25), (1871, 30), (2274, 35), (2771, 40)], float)   # Hardware Busters, SW Pro 4 120, rpm at dBA (1 m)
(A, B), *_ = np.linalg.lstsq(np.column_stack([np.ones(5), np.log10(_hwb[:, 0])]), _hwb[:, 1], rcond=None)   # ≈ −167.1, 60.2
CASE_MAX, RAD_MIN, RAD_MAX = 2920.0, 888.0, 2745.0
Lf = lambda r: A + B * np.log10(np.maximum(r, 300.0))
Lg = lambda N: 32.5 + 50 * np.log10(np.maximum(N, 300.0) / 1570)
case_rpm = lambda C: np.minimum(np.maximum(C, 300.0), CASE_MAX)
rad_rpm = lambda C: np.minimum(np.maximum(C, RAD_MIN), RAD_MAX)
e = lambda L: 10 ** (np.asarray(L) / 10)
L_case4 = lambda C: Lf(case_rpm(C)) + 10 * np.log10(4)
L_rad3 = lambda C: Lf(rad_rpm(C)) + 10 * np.log10(3)
L_fans7 = lambda C: 10 * np.log10(e(L_case4(C)) + e(L_rad3(C)))          # 4 case + 3 radiator together
L_total = lambda N, C: 10 * np.log10(e(Lg(N)) + e(L_case4(C)) + e(L_rad3(C)))
if __name__ == "__main__":
    assert abs(float(Lf(2920)) - 41.45) < 0.05 and abs(float(L_rad3(800)) - float(Lf(888)) - 4.771) < 0.01 and float(rad_rpm(3000)) == RAD_MAX
    for c in (800, 1000, 1300, 1600, 1900, 2400, 3000): print(c, round(float(L_case4(c)), 1), round(float(L_rad3(c)), 1), round(float(L_fans7(c)), 1))
