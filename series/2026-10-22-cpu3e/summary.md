# cpu3 — ws298 CPU full load, case 1000 rpm, radiator low (22 Oct 2026, Lab 0.3.55)

AMD Ryzen 9 9950X, stock (PPT 200 W), all 32 threads FMA; AIO pump at max (never touched); GPU idle. Each point ≥ 5 min, then Tctl ≤ 0.5 °C/min; values = mean after the first minute of each point (Tctl jitters ±2 °C second to second). Limit 90 °C — not reached.

| point | radiator rpm (%) | case rpm | Tctl °C | CCD1 °C | CCD2 °C | Tctl max °C | package W | avg clock MHz | room (intake) °C |
|---|---|---|---|---|---|---|---|---|---|
| cpu2 hold (reference) | 1495 (43 %) | ~2930 (100 %) | 71.2 | 68.7 | 68.6 | — | 200 | 5066 | 19.4 |
| A: target 1000 | 1013 (30 %) | 1005 | 75.1 | 72.3 | 70.5 | 78.4 | 200.0 | 5052 | 19.3 |
| B: target 800 | 882 (5.5 %) | 996 | 77.6 | 74.7 | 73.6 | 84.5 | 199.9 | 5046 | 19.3 |
| C: target 600 | 882 (5.5 %) | 996 | 77.7 | 74.7 | 73.1 | 83.6 | 200.0 | 5005 | 19.3 |
| D: minimum | 882 (5.5 %) | 996 | 77.4 | 74.8 | 72.7 | 83.9 | 199.8 | 5045 | 19.3 |

- The radiator fans (SilverStone, Hailstone 360) do not go below ~880 rpm: at 5.5 % they still turn 882 rpm, so 800 and 600 rpm are not reachable; B, C and D are the same setting (three repeats: Tctl 77.4–77.7 °C).
- No slowdown anywhere: package power stays at the 200 W limit, average clock 5005–5052 MHz (−14…−61 MHz vs cpu2, within the run-to-run spread; C is the only point past −50 MHz, B and D at the same fans are not). Tctl at the fan minimum is ~12 °C below the 90 °C limit.
- Case fans: cpu2 → A changes both case (2930 → 1000 rpm) and radiator (1500 → 1013 rpm): Tctl +3.9 °C, CCDs +2–4 °C. cpu2 showed the radiator 2744 → 1500 rpm costs only +0.3 °C, so most of the +3.9 °C is likely the case fans and/or the radiator below 1500 rpm — not separated yet (needs one point: case 2930, radiator 1000).
- Air at the radiator (aquaero Sensor 1, bottom chamber) stayed 19.2–19.3 °C at all points.

## cpu3e — same, case fans at maximum (23:15–23:29, Lab 0.3.58)

| point | radiator rpm (%) | case rpm | Tctl °C | CCD1 °C | CCD2 °C | Tctl max °C | package W | avg clock MHz | room (intake) °C |
|---|---|---|---|---|---|---|---|---|---|
| E1: radiator 1000 | 1021 (30 %) | 2925 | 75.8 | 73.1 | 69.7 | 79.8 | 199.9 | 5052 | 19.4 |
| E2: radiator minimum | 859 (7.5 %) | 2918 | 78.4 | 76.0 | 72.6 | 82.8 | 200.0 | 5028 | 19.5 |

**Do the case fans cool the CPU? No.** At the same radiator speed, case fans 2925 rpm vs 1000 rpm: Tctl 75.8 vs 75.1 °C (radiator ~1015 rpm) and 78.4 vs 77.5 °C (radiator minimum) — the difference (+0.7…+0.9 °C, room air +0.2 °C warmer) is within the Tctl spread; no cooling benefit from the case fans for the CPU on this open-top build.
The radiator is what matters, and its effect is strongly non-linear: 2744 → 1500 rpm costs +0.3 °C (cpu2), 1500 → ~1015 rpm +3.9 °C, ~1015 → ~870 rpm another +2.5 °C. No slowdown at any point (200 W, ~5.03–5.05 GHz, max Tctl 84.5 °C).
