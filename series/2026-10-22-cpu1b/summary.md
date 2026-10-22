# cpu1 — ws298 CPU full load, all cooling fans 100 % (22 Oct 2026)

AMD Ryzen 9 9950X, stock settings (no PBO / no own limits); SilverStone Hailstone 360 AIO, pump at max; 3 radiator fans + 4 case fans at 100 %;
load = WS.Sensor.Lab FMA vector loop on all 32 threads; GPU idle. Intake air 19.3 °C. Run `cpu1b` (the first `cpu1` at 16:40 aborted at setup: aquaero refused min 100 % with max < 100; no load ran).

| | max | steady (last 60 s) |
|---|---|---|
| Tctl °C | 74.3 (15 s after start, Zen 5 boost spike) | 68.2 |
| CCD1 °C | 70.6 | 66.1 |
| CCD2 °C | 69.1 | 65.7 |
| package W | 200.3 | 199.9 |
| VCore V | 1.30 | 1.26 |
| clock max / avg MHz | 5480 / 5195 | 5244 / 5094 |
| VRM °C | 34.5 | 34.3 |
| pump / radiator / case rpm | 3177 / 2757 / 2929 | 3140 / 2757 / 2929 |

- Run ended at 180 s with Tctl still falling −0.29 °C/min: shorter than the 5-min settling rule, so the steady values are provisional (true steady likely ≤ 1 °C lower). Future CPU points run ≥ 5 min (Lab ≥ 0.3.52).
- No thermal throttling (Tctl 26.8 °C below Tjmax 95 °C). The CPU sits at its stock power limit (PPT 200 W): power-limited, not temperature-limited.
- Headroom: ~27 °C to Tjmax at full fan speed → plenty of room to slow the radiator fans; next step = lower radiator rpm.
- Files: cpu1b/ (cpu.csv 1 Hz, long 1 Hz all sensors, log), cpu1b.png. Note: LHM exposes no PPT/TDC/EDC/PROCHOT sensors on this CPU; throttling judged from Tctl and clocks at constant package power.
