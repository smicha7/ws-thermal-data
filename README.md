# WS.Sensor thermal measurements — RTX 5090 cooling map

Raw data behind the GRUENCY / WS.COMPUTER article on cooling an NVIDIA GeForce RTX 5090 Founders Edition in a workstation
(open-top case, front intake fans, mix64 compute load). Measured with our own WS.Sensor cooling service (NVML, NVAPI,
aquaero, own GPU thermal-register reader). Free to use; please cite "GRUENCY / WS.COMPUTER, ws-thermal-data".

## Layout
- `series/<name>/` — one folder per measurement series:
  - `conditions.json` — setup, limits, software version
  - `raw.csv` — 1 Hz summary: core / memory / hot spot / intake air °C, power, clock, card fan rpm & duty, case & radiator rpm
  - `grid.csv` / `points.csv` — one row per measurement point (averages + trend)
  - `inventory.csv` — every logged sensor; `log.txt` — run log
- **Release assets** (large): `<series>--long-*.csv.gz` (every sensor, 1 Hz, long format: ts, point, phase, set-points, source, sensor_id, name, value, unit)
  and `<series>--HardwareMonitoring.hml` (MSI Afterburner log, where used)
- `scripts/` — analysis and plotting (Python: numpy, matplotlib); `notes/` — method and lab notes (partly Polish); `figures/` — plots

## Series (2026-10-20/21, Chełm, intake air ~19 °C)
| series | what |
|---|---|
| night-2026-10-20-gpu-map-v2d | fan grid (card % × case %), steady state, 575 W |
| night-…-v3*-pl | power-limit runs (575/500/425/400 W) |
| 2026-10-21-hold-1000 | case fans held at 1000 rpm, card fans set by hand (Afterburner) |
| 2026-10-21-log-1-manual | read-only log while card / case / PL were changed by hand |
| 2026-10-21-grid1c-1card | 112 points: case 1000/1500/2000/max × card 40–100 % × PL 100/90/80/70 %, 60 s each |
| 2026-10-21-grid1d-repeat40 | repeat of the card-40 % points, each case level settled first |
| 2026-10-21-val1-settled | val1: 20 points run to steady state (~8 min) with core snapshots at 1/2/3/5/8 min; 1 Hz long log not included (49 MB) |
| 2026-10-21-val1 | model validation: 20 points, each held to steady state (|dT/dt| < 0.1 °C/min, 8–15 min) with core/memory snapshots at 1/2/3/5/8/12 min |
| 2026-10-21-dyn1 | system identification: 56 random steps (Latin hypercube, seed 2110) of card 40–100 %, case 1000–2920 rpm, PL 70–100 %, 60–240 s each + 600 s anchors; plan in steps-plan.csv |
| 2026-10-21-val2 | validation part 2: re-test of the 60 s points with the largest model residuals + denser slow-card points (case 1500, card 45/65 % × PL 100/70), each to steady state with snapshots |
| 2026-10-22-steady2 | 37 points each held to steady state (|dT/dt| < 0.1 °C/min) with snapshots; 1 Hz long log in release assets |
| 2026-10-22-ctrl1-{balanced,quiet,performance}-{step,bursts} | WS.Sensor model-based controller on the real card, 30 min each: step = 2 min idle then 575 W; bursts = 60 s on / 60 s off; `ctrl.csv` = 1 Hz commands and measurements; measured vs simulation in figures/ctrl1-*.png |
| 2026-10-22-ctrl2-{performance,balanced}-bursts | controller after the anti-pumping fix (intake low-pass, feedforward hysteresis, down-ramp deadband, hold after a rise); 60/60 s bursts, 12 min; results in notes/CONTROLLER.md |
| 2026-10-22-cpu1b | CPU (Ryzen 9 9950X) all 32 threads loaded, radiator + case fans 100 %, GPU idle, until Tctl plateau; `cpu.csv` 1 Hz Tctl, CCD1/2, package W, VCore, clocks, fans; summary.md |
| 2026-10-22-cpu2 | CPU full load, radiator fans 100 % until settled, then −100 rpm every 10 s to 1500 rpm, then held 1500 rpm to plateau; `sweep.csv` 1 Hz (target/measured rpm, %, Tctl, CCD1/2, package W, clock); summary.md |
| 2026-10-22-cpu3 | CPU full load, case fans 1000 rpm, radiator 1000 / 800 / 600 / minimum (fans bottom out at ~880 rpm), each to plateau; `points.csv` per point, `sweep.csv` 1 Hz incl. room (intake) °C; summary.md |
| 2026-10-22-cpu3e | as cpu3 with case fans at maximum (2930 rpm): radiator 1000 / minimum — case fans do not cool the CPU (see cpu3 summary.md) |

**Data quality:** grid1c points are 60 s each and mostly not settled after big jumps — see `notes/NOTATKI-RECZNE-2026-10-21.md`
(final table = `series/2026-10-21-grid1c-1card/final.csv`, column `source`). RTX 5090 power limit cannot go below 400 W (NVML minimum).
