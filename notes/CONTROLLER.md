# WS.Sensor thermal-acoustic controller (model-based) — design notes

Goal (Seb, 2026-10-22): our own controller that keeps the GPU at full performance and safe, and only as loud as needed.

## Plant model (from our measurements, ws298, RTX 5090 FE, open case, intake ~19 °C)
2-node RC model fitted on 1 Hz logs (`dyn_model.py`, best = M2-pow, test RMSE ~1.2 °C):
- die ≈ sink + P·Rjs; sink: `Cs·dTs/dt = P − (Ts − Tin)/(ra + Rf(N, C))`; core = die + θ0
- fan law `Rf = k·n^−m·(C/1500)^−q`, n = √(N² + 300²)/1000 (N card fan rpm, C case rpm)
- memory: first-order lag to `Tin + λ(Ts − Tin) + a1·P + a0·load + θm`
Checked against measurements: 575 W, card 40 %, case 1000 → model 83 °C core / 91.6 °C memory (measured 82.5–83 / 90–91.6).

## Controller (every second)
1. **Load estimate**: board power, rises immediately, held 5 min, then falls slowly → no fan "pumping" on bursty loads.
2. **Feed-forward** (every 5 s and at once on a load step): search card × case fan speeds for the **quietest** pair whose
   steady-state core ≤ target − margin and memory ≤ 100 − 4 °C. The steady state comes from the model fitted **directly to
   steady points** (`results-2026-10-22/steady-stats.json`, form "cond": core − Tin = θ0 + P·(r∞ + 1/(gN·n^m + gC·c^s))), not from the
   dynamic model (its static part is biased on steady points). Margin = 2 × leave-one-out RMSE of that model (now 1.04 °C).
   The dynamic model is used only as the simulated plant and to tune the PI. Noise = energy sum of both fan groups
   (proxy 50·log10(rpm/1000) + offset until the iPhone dB curves exist).
3. **Power limit last**: only if the mode's noise ceiling is not enough, lower PL in 5 % steps, at most one step per 30 s and never below what the model needs; back up at once when the core is more than 1.5 °C below target (Performance mode never lowers it). The load estimate uses the card's *demand* (measured power ÷ current limit when the card is capped) — an earlier version divided the held peak by the limit and spiralled down to 70 % for ~5 min (core fell to 67 °C), found by the article editor.
4. **Feedback**: PI on core error — P only pushes fans up, I trims both ways within ±3 °C of target (no idle wind-up, anti-windup at limits).
5. **Limits**: up +150 rpm/s, down −15 rpm/s and only after 60 s below target − 1.5 °C; card fan minimum 30 % idle → 40 % full load; never 0 rpm under load.

| Mode | core target | card ceiling | case ceiling | may lower PL |
|---|---|---|---|---|
| Quiet | 80 °C | 1800 rpm (~57 %) | 1200 rpm | yes |
| Balanced | 77 °C | 2300 rpm (~75 %) | 1500 rpm | yes |
| Performance | 72 °C | 100 % | max | no |

## Simulation (`controller_sim.py`, results-2026-10-22/controller-sim.png/.json)
| scenario | factory (driver curve + case 1000) | Quiet | Balanced | Performance |
|---|---|---|---|---|
| 30 → 575 W step: peak core / noise proxy | 72.5 °C / 48.3 | 80.3 / 45.1 | 77.9 / 46.4 | 72.8 / 48.9 (0.8 °C over its 72 °C target, within the +1 °C band) |
| intake 19 → 30 °C: peak core, s above target+1 | 78.5, 842 s | 80.3, 0 (PL only 100 → 95 %, never below; mean 564 W) | 77.9, 0 | 72.8, 0 |
| 60 s load bursts: fan reversals / min | 0.97 | 0 | 0 | 0 |
Trade-off: on bursty loads the fans stay at the loaded level (steady, slightly louder) instead of pumping every minute.

## Open
- Refit feed-forward from steady2 (single session, NVAPI 0.01 °C) when it finishes; memory steady model is still the dynamic one.
- dB curves (iPhone, Chełm) → replace the noise proxy offsets; per-model JSON for other cards; validate on ws298 (after steady2, on the koncertmistrz's signal); C# port in WS.Sensor.Lab with the same scenarios as unit tests.

## Real-card test ctrl1 (ws298, 22 Oct 2026, Lab 0.3.48)
Six 30-min runs on the RTX 5090 FE, intake air 19.3 °C: each mode with a step (2 min idle, then 575 W) and with bursts (60 s on / 60 s off).
The simulation was re-run with the same load pattern and the measured intake (`ctrl1_compare.py`, figures `results-2026-10-22/ctrl1-*.png`).

| run | peak core °C (sim) | s > target + 1 °C | core after 10 min °C (sim) | memory peak °C (sim) | card rpm loaded (sim) | case rpm (sim) | PL min | card reversals/min (sim) |
|---|---|---|---|---|---|---|---|---|
| balanced step (77) | 78.0 (77.7) | 0 | 76.3 (76.7) | 86 (85.4) | 1477 (1453) | 1270 (1250) | 100 % | 0.39 (0.60) |
| balanced bursts | 66.0 (65.0) | 0 | 59.7 (61.3) | 72 (71.1) | 1508 (1511) | 1236 (1167) | 100 % | 1.03 (1.38) |
| quiet step (80) | 81.0 (80.4) | 0 | 79.8 (79.5) | 90 (88.1) | 1392 (1379) | 1178 (1154) | 100 % | 0.46 (0.11) |
| quiet bursts | 68.0 (66.5) | 0 | 61.2 (62.8) | 72 (72.6) | 1417 (1413) | 1147 (1150) | 100 % | 0.71 (0.04) |
| performance step (72) | 73.0 (72.6) | 0 | 71.9 (71.9) | 82 (80.1) | 1639 (1630) | 1415 (1376) | 100 % | 0.18 (0.11) |
| performance bursts | 63.0 (62.7) | 0 | 57.2 (58.8) | 70 (68.8) | 1710 (1704) | 1288 (1335) | 100 % | 1.56 (0.04) |

Findings:
- The controller holds every target on the real card: 0 s more than 1 °C above target in all six runs; the step peak is 0.6–1.0 °C over target, as simulated.
- The simulation predicts the real card within 0.5 °C (steady core), 2 °C (memory peak) and ~25 rpm (card fans). The model is good enough to tune the controller offline.
- The power limit was never cut at 19 °C intake (as designed: fans alone are enough in all modes).
- On bursts the real controller moves the card fans more often than the simulation (up to 1.6 direction changes per minute vs 0.04): measurement noise from the whole-degree core reading. To do: smooth the core input or widen the integrator dead band before the customer release.
- Caveat: the NVAPI 0.01 °C core column was empty in these runs, so the controller ran on the 1 °C NVML reading. To check in Lab.

## ctrl2 — anti-pumping on the real card (ws298, 22 Oct 2026, Lab 0.3.53)
Bursts 60 s on / 60 s off, 10 min after the 2-min warm-up; direction changes per minute, ctrl1 → ctrl2:

| mode | card fans | case fans | s > target + 1 °C | peak core °C |
|---|---|---|---|---|
| Performance (72) | 2.33 → 0.21 | 3.49 → 0.21 | 0 | 62 |
| Balanced (77) | 0.53 → 0.21 | 3.60 → 0.42 | 0 | 65 |

The remaining changes are one slow dip every 5–7 min: bursts at 574 W never matched the 575 W peak, so the 5-min load hold expired. Fixed after the run (a burst within 3 % of the peak renews the hold); simulation with ±2 W burst jitter: 0.08 (Performance) and 0.07 (Balanced) changes per minute. The NVAPI 0.01 °C core was not reaching the controller (empty column); exposed as `core_nvapi_c` for the next run.
