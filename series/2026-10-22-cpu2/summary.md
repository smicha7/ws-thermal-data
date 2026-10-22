# cpu2 — ws298 radiator fan sweep under full CPU load (22 Oct 2026)

AMD Ryzen 9 9950X, stock (PPT 200 W); SilverStone Hailstone 360 AIO, pump at max; case fans 100 %; load = WS.Sensor.Lab FMA on all 32 threads; GPU idle; intake air 19.4 °C.
Procedure: radiator fans 100 % until Tctl settled (≥ 5 min, ≤ 0.5 °C/min) → target −100 rpm every 10 s (2700 → 1500, rpm trimmed from the tachometer every second) → hold 1500 rpm ≥ 5 min to plateau. Aquaero restored at the end.

| | radiator | Tctl °C | CCD1 °C | CCD2 °C | package W | avg clock MHz |
|---|---|---|---|---|---|---|
| settled, 100 % (last 60 s) | 2744 rpm | 70.9 | 66.6 | 66.8 | 200 | 5022 |
| settled, held 1500 rpm (last 60 s, 5 min hold) | 1495 rpm (43 %) | 71.2 | 68.7 | 68.6 | 200 | 5066 |

- Radiator 2744 → 1500 rpm: Tctl +0.3 °C, CCDs about +2 °C. At the end of the hold Tctl still rose +0.36 °C/min (within the plateau rule).
- 10 s steps (steps.csv): end-of-step Tctl 68.8–73.8 °C, per-step slopes −0.31…+0.20 °C/s = Tctl jitter; the coolant loop reacts over minutes, so 10 s steps show no measurable trend.
- Max Tctl 75.6 °C; no thermal throttling (Tjmax 95 °C); package power at the 200 W limit throughout; VRM max 36 °C.
- Files: cpu2/ (sweep.csv 1 Hz with target / measured rpm / %, cpu.csv, long 1 Hz all sensors, log), steps.csv; plot results-2026-10-22/cpu2-sweep.png.
