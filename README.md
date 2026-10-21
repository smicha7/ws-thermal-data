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

**Data quality:** grid1c points are 60 s each and mostly not settled after big jumps — see `notes/NOTATKI-RECZNE-2026-10-21.md`
(final table = `series/2026-10-21-grid1c-1card/final.csv`, column `source`). RTX 5090 power limit cannot go below 400 W (NVML minimum).
