# GPU thermal map — method

Experiment run on ws298 (Seb's approval, 2026-10-20). Code: `windows-lab/Experiment.cs`, started by the WS.Sensor.Lab cooling service. Analysis: `research/gpu-map/analyze.py`.

## Question

How do the graphics card's own fans and the case fans together set the temperatures of the RTX 5090 (core, memory, hot spot) under constant full load? For each target temperature, which combination is the quietest?

## Machine and conditions

- **Computer:** ws298. Ryzen 9 9950X, ASRock X870E Taichi Lite, one RTX 5090 (575 W default power limit).
- **Case airflow:** 4× be quiet! Silent Wings Pro 4 120 mm on one aquaero output (Fan 1, via Splitty9). Three of them are front intakes blowing onto the GPU, one is a rear exhaust behind the CPU. The aquaero reads the tach of one SWP4, which stands for all four.
- **Case top:** open for this run (top panel removed). Recorded in `conditions.json` as `case`. The run will be repeated with the case closed and later with two GPUs.
- **CPU cooler:** SilverStone Hailstone 360 AIO with 3 fans on aquaero Fan 2 (bottom radiator). These fans stay on their normal curve (Curve 1) and are logged. They don't blow on the GPU.
- **Intake air:** aquaero temperature sensor 1 (air in the bottom chamber).

## Inputs (what we set)

| symbol | meaning | range |
|---|---|---|
| f_g | GPU fan duty, all 3 fans of the card equal (NVML) | card minimum (30 %) … 100 % |
| f_c | case fan duty (aquaero Fan 1 output) | lowest duty that still spins (measured first) … 100 % |

- **Case fans:** for the run, the case output is driven by aquaero curve 4. That curve maps 0–95 °C to 0–100 % linearly. Its input is software sensor 8, which the service sets to f_c × 0.95 every second, so the output equals f_c exactly. This is the same mechanism as the fan calibration sweep.
- **Before:** the aquaero settings are backed up before the run.
- **After:** the backup is written back at the end, on any abort, and also when the service restarts mid-run.

## Outputs (what we log, 1 Hz)

`raw.csv` holds one row per second with these columns:

- **Temperatures:** core, memory and hot spot temperature (°C), intake air (°C).
- **Card load:** board power P (W), core clock (MHz), GPU utilisation (%).
- **Fans:** rpm of each GPU fan and the GPU fan duty; case fan rpm and output %; radiator fan rpm and output %; every motherboard fan header's rpm.
- **Settings:** the power limit (W).

Each temperature is also reported normalised as thermal resistance:

    R = (T − T_intake) / P    [°C/W]

for core, memory and hot spot. R removes the effect of room temperature and of the exact power draw. That makes points measured at different times comparable, and lets a later power-limit stage predict temperature at any wattage: T = T_intake + R·P.

## Sources of the readings

| reading | source |
|---|---|
| Core temperature | NVML |
| Memory temperature | NVAPI thermal sensors, index 2 on RTX 50, read in the user session by the WS.Sensor tray and passed to the service |
| Hot spot | the card's thermal registers via the PawnIO driver and the official signed `Nvidia.bin` module (namazso/PawnIO.Modules 0.2.11); hot spot = maximum of the valid channels, as in HWMonitor |
| Power, clocks, utilisation, fans | NVML |
| Case and radiator fans | aquaero 6 over USB (own protocol code) |

Check on 2026-10-20 at idle against HWMonitor: memory 36 °C = 36.0 °C, hot spot 30 °C = 30.2 °C.

## Load

A constant 100 % GPU load comes from our own compute kernel. It is the same as WS.Remote's Load Test: a D3D11 compute shader with float4 `mad()` chains, 8 × 16 384 groups per pass. Octane was not used because its scene gaps make the load uneven.

- **Where it runs:** the service starts it in the logged-in user's session, with no window.
- **When it stops:** it stops itself if the service stops updating `status.json` for 20 s.
- **Power limit:** stock 575 W for this phase.
- **Memory heating:** besides the pure ALU kernel there are mixed kernels. Each reads a 1 GiB buffer, does k `mad` per element (k = 64, 16 or 4; 0 = pure streaming) and writes the next buffer. The buffers fill about 70 % of VRAM and are swept round-robin, so memory bandwidth and therefore memory junction temperature are loaded too.
- **Calibration (before the grid):** at both fans 100 %, each kernel runs 45 s and the mean board power of the last 20 s is recorded. The run uses the highest-power kernel among those that stream VRAM. Pure ALU is kept only for comparison. The achieved power of every variant is written to `conditions.json` (`load_calibration_w`) and to `log.txt`.
- **Per point:** the mean power and its standard deviation over the 60 s window are recorded. The point is flagged `power_steady = 1` when the variation is ≤ 3 %. R stays valid either way.

## Grid

1. **Case minimum.** With the card idle, the case output steps down 40 → 35 → … → 10 %, 20 s per step. The lowest duty still above 300 rpm, plus 5 %, becomes the minimum f_c,min. The fans are never left stopped.
2. **Warm-up.** Load on at the first grid point, until steady state (at most 10 min). The warm-up isn't recorded as a point.
3. **Coarse grid, 4 × 4.**
   - f_g ∈ {30, 55, 80, 100} %.
   - f_c ∈ {f_c,min, ⅓, ⅔ of the way to 100, 100} %.
   - **Order:** serpentine, starting at the coolest corner (both fans 100 %), with f_c decreasing row by row and f_g alternating direction. Every step between points is small, and temperatures rise gradually.
4. **Refinement, 8 × 5.**
   - f_g ∈ {30, 40, …, 100} %.
   - f_c ∈ {min, 25, 50, 75, 100 % of the way}.
   - **Choice:** the grid points not yet measured, taken in order of the largest hot-spot difference between the corners of their coarse cell (core when hot spot is missing).
   - **How many:** as many as fit the remaining time budget, using the mean time per point so far. They run in serpentine order.

## Steady state and recording

- **Steady:** the slope of a least-squares line over the last 120 s is below 0.2 °C/min for core, memory and hot spot alike. A point lasts at least 150 s.
- **Recorded:** the mean of the last 60 s, written to `points.csv` together with R for core, memory and hot spot.
- **Not settled:** a point gets at most 8 min. If it hasn't settled by then, it is recorded with `settled = 0`.

## Safety

- **Card thresholds:** read from NVML at the start (`nvmlDeviceGetTemperatureThreshold`: shutdown, slowdown, mem_max, gpu_max, acoustic min/current/max) and stored in `conditions.json` (`gpu_thresholds_c`).
- **Per point:**
  - The point ends at once with `too_hot = 1` when core ≥ slowdown − 5 °C (85 °C if the card doesn't report slowdown), memory ≥ 88 °C (and ≥ mem_max − 5 when reported), or hot spot ≥ 95 °C.
  - All fans then go to 100 % until the card is clearly below the thresholds (at most 3 min), and the run moves on to the next point.
- **Fans never at 0:** GPU fans are held at or above the card's NVML minimum, case fans at or above the measured lowest spinning duty.
- **Throttling:** NVML throttle reasons are logged every second as a bitmask. Per point, `power_capped_pct` is the share of seconds with the power-cap bit (0x4), and `thermal_throttled_s` is the number of seconds with a thermal bit (0x8 HW slowdown, 0x20 SW thermal, 0x40 HW thermal). Throttled points are kept: R is valid, performance isn't.
- **Whole run:** the service's own protections stay active the whole time. If the computer goes into emergency mode (all fans to 100 %), the run ends.
- **Load check:** the run ends if the load process stops, or if board power stays below 50 % of the limit for 60 s.
- **Time budget:** 3.5 h, and the run is stopped at 3.5 h + 15 min at the latest.
- **At the end, or on any abort:**
  - the load stops;
  - the card's fans return to the card's own mode;
  - the aquaero settings are restored from the backup taken before the run;
  - the case override ends.
- **Updates:** the service doesn't update itself or install drivers while the run is active.

## Everything is logged (1 Hz)

Every reading the service has each second goes to a long table:

- **Columns:** `long-<start>.csv.gz` holds `ts, point, phase, fg_set, fc_set, source, sensor_id, name, value, unit`.
- **Sources:**
  - CPU per-core temperatures, clocks and power, and board Super I/O temperatures, voltages and fan headers (LibreHardwareMonitor with PawnIO);
  - aquaero: every temperature, and per output the duty, voltage, current, power and rpm;
  - NVMe/SATA, DIMM (DDR5 SPD) and derived values;
  - on the GPU, NVML: graphics/SM/memory/video clocks, GPU/memory-controller/encoder/decoder utilisation, P-state, throttle reasons, PCIe generation and width, VRAM used, board power, enforced power limit, energy, and per fan the actual and target %;
  - on the GPU, every NVAPI thermal sensor and every PawnIO thermal register channel.
- **Inventory:** `inventory.csv` lists every sensor present at the start. Its count is in `conditions.json` (`sensor_count`).
- **Per point:** `points-wide.csv` holds, for every sensor in the inventory, the mean, min, max and standard deviation over the 60 s window.
- **Not available:** the per-rail board readings HWMonitor shows (16-pin, PCIe slot, MSVDD and core supply voltages/currents). They come from the card's power monitor chips over I2C, which our code doesn't read yet.
- **Not logged:** the load kernel's TFLOPS and error count. The load runs in the user session and has no write path back to the service.

## Run v2 (2026-10-20, Seb): short points

Run `2026-10-20-gpu-map-v2` uses the fast mode (`exp:gpu-map:mode = fast`).

- **Grid:** the full 8 × 5 grid directly, with no 4 × 4 stage. It runs in serpentine order from the coolest corner.
- **Reference point:** f_g 55 %, f_c ⅔ of the way, measured at the start, in the middle and at the end: 43 points in total.
- **Normal points:** after a set-point change, 10 s are skipped and the next 60 s are logged and fitted with T(t) = T∞ − B·e^(−t/τ). `fits.csv` holds, for core, memory and hot spot, the 60 s mean, T∞, its ±95 % interval and τ.
  - The interval comes from the residual variance at the best τ and ignores τ's own uncertainty.
  - When τ hits the search limit (900 s), no interval is given.
- **Validation points:** every 4th point and all reference points run on to steady state (same rule, at most 6 min). For them `fits.csv` also holds the steady value and the error T∞(60 s fit) − steady.
- **Results:** the error distribution is reported with the results. The reference point's three R values give the drift/repeatability error.
- **Simulated run:** 43 points in 86 min, maximum T∞ error 0.10 °C. On the real card, τ and the validation errors decide.
- **Unchanged:** safety, logging, load calibration and the restore are the same as above.

## Run v3 (2026-10-20, Seb): power limit as the third dimension

Run `2026-10-20-gpu-map-v3-pl` starts automatically after v2 finishes (`exp:gpu-map-pl:after`).

- **Grid:**
  - power limit 575 / 500 / 425 / 350 W in the outer loop, from high to low;
  - f_g 30 / 50 / 70 / 100 % × f_c min / 50 / 100 % in a serpentine inside each level (ceteris paribus per power limit);
  - 48 points, fast method (10 s skip + 60 s first-order fit), every 4th point to steady state (≤ 6 min).
- **Power limit:**
  - Set through the service's own power-limit control (NVML).
  - It is clamped to the NVML min–max and never above the card's reference limit. The enforced limit is logged every second.
  - Load calibration and cool-down run at the stock limit.
  - At the end, on abort and after a service restart, the service returns the card to its persisted reference limit by itself.
- **Performance cost:**
  - Every 2 s the load process reports TFLOPS (FP32), VRAM traffic (GB/s), passes per second and result errors. Errors are counted in the ALU kernel only, whose result is deterministic.
  - Per point, `points.csv` holds `pl_w`, `enforced_limit_w`, `load_tflops`, `load_gbs` and `load_errors`.
- **Model:** T = T_in + P·R(f_g, f_c), where P is now capped by the power limit, plus a performance curve perf(PL) from the TFLOPS and GB/s per power-limit level.

## Run v4 (2026-10-20, Seb): safe-frontier trace

Run `2026-10-20-gpu-map-v4-trace` starts automatically after v3. It follows Seb's experience-based procedure: the grid gives the model, and v4 traces the quiet-and-safe boundary finely.

- **Order:** for each case-fan level (100 %, 50 %, min), start with GPU fans at 100 % and the stock power limit. Every step is a fast point (10 s + 60 s fit).
- **Watched value:** the hottest sensor, i.e. the maximum of the T∞ estimates for core, memory and hot spot. On a too-hot abort, the observed maximum is used instead.
- **Caps:** hot spot 95 °C, memory 88 °C, core NVML slowdown − 5 °C. "Safe" means at least 5 °C below every cap.
- **Fans down:** the GPU fans are lowered in 5-point steps while the point stays safe and the hottest rise is no more than 2× the previous step's rise.
- **Knee:** when the margin drops below 5 °C, or the rise more than doubles, the fans stop going down. The power limit is lowered instead, 100 → 95 → 90 % of stock (5-point steps, 2-point steps within 2 °C of a cap), until the point is safe again. Then the next lower fan step is tried at that limit.
  - If the rise doubles while the point is still safe, the state is accepted and the next fan step is taken with a 5-point lower limit.
- **Limits:** the power limit never goes below 60 % of stock (≈ 350 W; Seb: hot multi-GPU rigs rarely went below 65–70 %), and the GPU fans never below 30 %.
- **Output:** `frontier.csv` has one row per accepted safe state: case %, GPU fan %, power limit % and W, T∞ per sensor, the hottest value and its margin, power, TFLOPS, GB/s and rpm. For each fan/noise level it gives the highest safe power limit, which is the curve for quiet modes.
- **Simulation:** 52 points in 68 min.
- **Unchanged:** safety, logging, restore and persistence are the same as v3.
- **Updates:** while any of tonight's runs is still pending, the service doesn't update itself, so a restart can't break the v2 → v3 → v4 chain.

## Safety rule for v2, v3 and v4 (Seb, 2026-10-20 22:40)

1. **Fans only step down gradually.** Descending, a fan setting changes by at most 5 points per step. Going up may jump.
   - Every row starts at GPU fans 100 % and descends. Rows run from the highest case level down.
   - When the next planned point is more than 5 points lower in either fan, the service inserts bridge points: first the case fans in 5-point steps (GPU fans held at the higher value), then the GPU fans.
   - Bridges hold 10 s + 20 s, are fully logged and are marked `bridge = 1` in `points.csv`. This applies after a cool-down too (from 100 / 100).
2. **Predictive stop.** Before each lower GPU-fan step, the next value of each sensor is predicted as T∞ now + 1.5 × (trend per point × 5) from the previous step in the same row.
   - If any sensor would exceed its cap − 5 °C, the rest of that row isn't run. Those points go to `skipped.csv` as "predicted unsafe at this power" and stay empty in the plots.
   - A too-hot point skips the rest of its row. If it happens at GPU fans 100 %, the lower case rows at that power are skipped too.
   - In v4 the same prediction triggers the power-limit reduction (5 points, 2 points near the cap) before the next fan step.
3. **Caps:** hot spot ≤ 95 °C, memory ≤ 88 °C, core ≤ NVML slowdown − 5 °C. An abort sets fans to 100 % and the power limit to stock, waits for the cool-down, then continues.
4. **Simulated durations with bridges:** v2 117 min, v3 ~3 h (cap 3 h), v4 ~1.5 h.

## Database (`export_sqlite.py`)

After the files are fetched from ws298, every run is exported into one SQLite database, `thermal-map.sqlite`. This is the source for the analysis and for a later rendered animation.

| table | content |
|---|---|
| `runs` | one row per run: id, start (UTC), mode, case condition, Lab version, sensor count |
| `conditions` | every key of `conditions.json` per run (thresholds, calibration, budget, rules) |
| `sensors` | the sensor inventory per run: id, source, name, unit, first value |
| `raw` | the long 1 Hz table: ts (Unix s, UTC), point, phase, fg_set, fc_set, source, sensor_id, value, unit. A run cut short is read up to its last flushed second. |
| `setpoints` | one row per set-point interval: t_start, t_end, phase, GPU fan %, case fan %, power limit in W and in % of stock. These are the clean transitions that drive an animation. |
| `points`, `fits`, `frontier`, `skipped` | the per-point tables as written on ws298 (every column kept, with run_id) |

- **View:** `raw_named` joins sensor names and adds `ts_iso`.
- **Index:** `raw(run_id, sensor_id, ts)`.
- **Units:** all times are Unix seconds (UTC). The power limit is always given both in W and in % of the card's limit before the run (575 W = 100 %).
- **Dependencies:** Python standard library only.

## Drift and repeatability

Hours at 575 W warm the room. Each point is normalised with its own intake air (R), and `analyze.py` also reports the following.

- **Intake-air drift:** the linear trend (°C/h) and the range over the whole run, from `raw.csv`. Output: `intake-drift.png`, `fit.json → intake_drift`.
- **Repeatability:**
  - Any setting measured more than once gives a spread of R, which is the experiment's own drift/repeatability error (`fit.json → repeatability_R_spread`).
  - Tonight's grid measures each setting once (refinement skips measured points), so tonight's runs have no direct check. The v1 and v2 runs share settings, though, so comparing them gives an indirect one.
  - **Future runs:** a reference point (f_g 55 %, f_c ⅔ of the way) repeated at the start, middle and end of the grid. Its R spread is reported in the article.

## Step response (time constant)

After every set-point change, `analyze.py` fits a first-order response to the 1 Hz data of each point:

    T(t) = T∞ − (T∞ − T0)·e^(−t/τ)

- **Fitting:** τ comes from a grid search over 5–600 s, and T∞ and the amplitude from least squares. This is done separately for core, memory and hot spot.
- **Output:** `step-response.csv` gives τ, T∞ and the steady value per point.
- **Shortening future points:** T∞ is extrapolated from only the first 60 s and 90 s of each point and compared with the full steady-state value (mean of the last 60 s). The mean and maximum error go to `fit.json → step_response`, plotted in `step-response.png`. If the 90 s error stays within about 0.5 °C, future points can stop at ~1.5–2 min, using the extrapolated T∞ instead of waiting for |dT/dt| < 0.2 °C/min.

## Later: control layer (stage 3, policy)

1. At safe temperatures the power limit is never touched.
2. When cooling is needed, raise the fans first: whichever set (GPU or case) gives more temperature drop per added noise according to the fitted model.
3. Only when a noise ceiling is reached (e.g. case fans ≤ 2000 rpm, GPU fans ≤ a set rpm) and the temperature is still too high, lower the power limit.
4. Stage 3 measures this: a power-limit sweep with the fans held fixed (ceteris paribus), then the full 3-D grid (f_g × f_c × power limit) only where it matters.

The 2-D grid is kept rather than changing one factor at a time, because it captures the GPU-fan × case-fan interaction (the `c` term of the fit).

## Files

`%ProgramData%\WS.Sensor\experiments\2026-10-20-gpu-map\`:

- **`conditions.json`:** case state, intake air at the start, GPU, power limit, case minimum, budget, steady-state and abort rules.
- **`raw.csv`:** 1 Hz log of the key channels, all phases.
- **`long-<start>.csv.gz`:** 1 Hz log of every sensor (long format, gzip flushed every second).
- **`inventory.csv`:** the sensors present at the start.
- **`points-wide.csv`:** per point, mean/min/max/std of every sensor.
- **`load-mode.txt`:** the load kernel in use.
- **`points.csv`:** one row per grid point: means, R, power std/variation, power-cap share, thermal-throttle seconds, load kernel.
- **`log.txt`:** the run log (phases, each point, abort reasons, the restore).
- **`status.json`:** live state, also shown in live.json under `experiment`.

## Analysis (`analyze.py`)

- **Fit per temperature (core, memory, hot spot):**

      1/R = h0 + a·rpm_g^0.8 + b·rpm_c^0.8 + c·rpm_g^0.8·rpm_c^0.8

  The exponent 0.8 is the forced-convection scaling of the heat-transfer coefficient with air speed. The fit uses least squares on the settled points that aren't too hot. It reports the coefficients, R², and the error converted back to °C at the measured power (RMSE and maximum).
- **Plots (PNG):**
  - a 3D surface of T_hot spot (and core and memory) over (f_g, f_c);
  - a contour heat-map with iso-rpm lines of the GPU fans;
  - the quietest-combination frontier: for each target hot-spot temperature, the (f_g, f_c) with the lowest total fan noise. Noise is estimated from rpm with each fan type's level at its rpm, so it is relative, not absolute dB.

## Programme: later nights (Seb, 2026-10-20). Design only; code after tonight's results.

The same principles apply in every stage:

- Fans only go down in steps of at most 5 points, with bridge points in between.
- Before each lower step there is a predictive stop (T∞ + 1.5 × trend vs cap − 5 °C).
- An abort puts everything to full and restores stock limits, then cools down and continues.
- Every sensor is logged at 1 Hz, with the inventory and per-point statistics, and exported to SQLite.
- Steps use the fast-point fit (T∞, τ) with periodic steady-state validation points.

Caps:

- **GPU:** as tonight.
- **CPU:** Tctl ≤ 90 °C, below AMD's 95 °C throttle point.
- **VRM/MOS:** ≤ 100 °C, or the board's own limit if lower.

### Stage C: CPU + VRM

- **Inputs:**
  - AIO radiator fans (aquaero Fan 2, 3× SilverStone 120 mm, 800–3000 rpm), from 100 % down in 5-point steps;
  - case fans (aquaero Fan 1, which also blow over the board VRM) at three levels, 100 / 50 / min, rows from the top;
  - the pump (separate sweep, below).
- **Load:** our own constant all-core CPU stress, the WS.Remote Bench engine (same idea as the GPU kernel: deterministic, with a result check). The GPU stays idle.
- **Outputs:** Tctl, CCD1, CCD2, package power, VRM/MOS and chipset temperatures, coolant temperature (if an aquaero sensor sits in the loop; the Hailstone AIO is a closed loop with no sensor today), intake air, every fan, pump rpm.
- **Normalisation:** R_cpu = (T_cpu − T_in) / P_package, plus R_vrm = (T_vrm − T_in) / P_package.
- **Time constant:** an AIO with coolant reacts slower than the GPU (expected τ of a few minutes). Fast points become 10 s + 120 s, and the warm-up waits for coolant steady state.
- **Estimate:** 3 case levels × ~17 radiator steps ≈ 51 points + bridges, ≈ 2.5 h. With the pump sweep and warm-up, ≈ 3 h.

### Pump rule

- **Connection:** the pump is on the motherboard header AIO_PUMP, not the aquaero (station map: "AIO pump, fixed at max").
  - It is a 3-pin pump, so it can only be controlled by voltage (DC mode).
  - Our code doesn't write board fan headers yet. That would need a Super I/O write through PawnIO, the same route LibreHardwareMonitor uses. It's to be built and tested first: header mode readback and restore on exit, like the BMC zones.
  - Until then the pump stays at full.
- **Manufacturer data:** SilverStone lists the Hailstone 360 pump at 3,200 ± 10 % rpm, 12 V, 0.38 A, with a 3-pin 2510 connector ([Computer Alliance](https://www.computeralliance.com.au/360mm-silverstone-hailstone-360-str5-cpu-liquid-cooler-black/), [PCComponentes](https://www.pccomponentes.com/refrigeracion-liquida-silverstone-hailstone-360-360mm-3-ventiladores-pwm-negro)). No minimum speed or voltage is published, and no official SilverStone spec page was found.
- **Floor:** Seb's 2,000 rpm. It is stricter than anything published, so it is the rule.
- **Sweep:** one sweep only, at fixed fans: 12 V → 11 V → 10 V (or the duty equivalent), each to steady state. The step stops at once if the tach drops below 2,000 rpm, reads 0, or wobbles by more than 10 %. ≈ 30 min.
- **Default:** full.

### Stage D: multi-GPU (2× RTX 5090 from Thursday, maybe a 3rd)

- The coupling model from `research/multi-gpu-cooling.md`: identification steps (one card loaded at a time, then both), the coupling matrix c_ij, and feed-forward k_ij.
- **New conditions:** slot positions and spacing (slot numbers, PCIe bus ids, centre-to-centre distance in mm, card thickness and gap). Fixed on ws298, but logged for comparison with boards that allow wider spacing.
- **Grid:** per-card GPU fans × case fans, rows from the top, with the safe-frontier logic per card on the hottest sensor of either card.
- **Estimate:** identification ≈ 1.5 h, plus the 2-card fan grid ≈ 2–3 h.

### Stage E: everything at once

- **Load:** CPU stress + every GPU (ALU + VRAM) together.
- **Inputs:** case fans × radiator fans × GPU fans per card, with the power limits per card.
- **Procedure:** the v4-style safe-frontier trace. Fans down in ≤ 5-point steps; at the knee, first the most efficient fan per dB/rpm according to the fitted models, then GPU power limits down gently (floor 60 %); CPU limits are not touched in this stage.
- **Output:** a combined frontier, the quietest safe state per total load, which is the basis for the quiet/normal/performance modes.
- **Estimate:** ≈ 3–4 h.

## Ready for Thursday (2 × RTX 5090): runs prepared in Lab 0.3.21, started only when Seb is at ws298

Each run starts by adding its keys to `maps/ws298.json` (new `map:rev`) and releasing. Then Check for updates on ws298.

1. **Noise pass** (`mode = noise`, ~30–40 min with typed values):
   - **Settings:** GPU fans 100 → 30 % in 10-point steps × case 100 / 79 / 58 / 36 / 15 %, no load, fans only down in ≤ 5-point steps.
   - **Each setting:** ≥ 20 s, then a topmost window in the WS.Sensor tray: "Now: GPU 60 % (2160 rpm) · case 50 % (1720 rpm) — read the sound meter and type dB". Enter saves the value. With no entry in 120 s, the setting is recorded without dB.
   - **Output:** `noise.csv` (fg, fc, dB, GPU rpm, case rpm, radiator rpm, core, intake).
   - **How to measure:** an iPhone sound meter app at one fixed spot (note the distance and position in `:case` or `:slots`).
2. **Coupling + grid with both cards** (`mode = couple`):
   - **Coupling:** GPU fans 60 %, case 100 % then 50 %; load only card 0, then only card 1, then both. Each to steady state (≤ 6 min). The idle card's rise against the loaded card's power gives c_ij.
   - **Grid:** the 8 × 5 fast grid with both cards loaded and both cards' fans at the same %. Safety, steady state and abort use the hottest card.
   - **Conditions:** `:slots` (slot numbers, centre-to-centre distance, card thickness and gap) and `:case` (open/closed). The cards' PCI bus IDs are logged automatically.
3. **Power limit with both cards** (`mode = pl`, as v3; the limit applies to both cards).

Example keys:

    "exp:noise:id": "2026-10-22-noise", "exp:noise:start": "2026-10-22T00:00", "exp:noise:mode": "noise", "exp:noise:hours": "1.5", "exp:noise:case": "…",
    "exp:gpu2:id": "2026-10-22-2gpu", "exp:gpu2:after": "2026-10-22-noise", "exp:gpu2:start": "2026-10-22T00:00", "exp:gpu2:mode": "couple", "exp:gpu2:hours": "3", "exp:gpu2:slots": "…", "exp:gpu2:case": "…"

## Noise channel: measurement microphone (Lab 0.3.22)

- **Microphone:** Yamaha YPAO (omni electret, 3.5 mm mono) in ws298's rear MIC input, fixed position: 1 m in front of the case at card height. Record the position in the run's `:case` / `:slots`.
- **Settings in `maps/ws298.json`:**
  - `"mic:on": "on"`;
  - `"mic:device": "<part of the input's name>"` (the capture-device list is in the header of `requests\noise-live.txt` and in `live.json → mic.source`);
  - optionally `"mic:gain": "0.75"`, a fixed input gain; the previous gain is restored when the mic is turned off.
- **Capture:** the WS.Sensor tray captures in Seb's session via WASAPI at the shared mix rate (usually 48 kHz). It uses RAW mode (no Windows AGC or enhancements) when the driver allows it; the mode is logged.
- **Processing:** per second, A-weighted Leq (IEC 61672 pole frequencies, bilinear with pre-warped poles; the response is within class-1 tolerance at 31.5 Hz–10 kHz, tested), Z-weighted Leq, peak, and the 1/3-octave spectrum 25 Hz–20 kHz (Hann-windowed FFT). All values are in dBFS. The service logs them as sensors `mic/*` in the long table, so they are in the per-point statistics too.
- **Calibration:** dB SPL = dBFS + offset. In the noise pass, at case 100 % and GPU 100 / 60 / 30 %, the tray also asks for the iPhone sound-meter reading (phone held next to the mic). The offset is the mean of iPhone dBA − mic dBA FS, stored in `noise-cal.json` and in HKLM (`Mic.Offset`) for later runs. It can be overridden with `"mic:offset_db"`. Relative changes (dB vs rpm) are valid without it.
- **Plug-in power:** if the Z level stays below −85 dBFS, `live.json → mic.no_signal` is true, meaning the input gives no bias voltage for the electret capsule.
- **Room floor:** the last grid setting (GPU 30 %, case minimum, no load) is the quietest the machine runs. The radiator fans stay on their curve and are logged.

## Memory limit change (Seb, 2026-10-21)

From Lab 0.3.23 the memory cap is 95 °C, the listed GDDR7 figure (distributor catalogue for Samsung K4VAF325ZC, Tc/Tj not stated, unconfirmed). It replaces 88 °C. The predictive stop stays 5 °C below, at 90 °C. The first night's runs (v1–v4d) used 88 °C, which the sections above describe.

## Memory working limit 100 °C (Seb, 2026-10-21, final)

The memory working limit is 100 °C junction (replacing 95 °C). It is derived from the core limit of 90 °C plus the measured maximum memory − core gap of about 8.5 °C, so the core stays the binding limit. It is not a manufacturer value.

From Lab 0.3.27 the experiment aborts a point at memory ≥ 100 °C, and the predictive stop holds 5 °C below, at 95 °C. `conditions.json` records `mem_working_limit_c` and `core_limits_c` (90 / 93 / 96).

## Card fan minimum depends on load (Seb, 2026-10-21)
- Full load: card fans never below **40 %**. Idle / low load: minimum is the NVML floor (**30 %** on the RTX 5090).
- Implemented in the cooling service GPU curve (`GpuInput.LoadFloor`): linear in board power ÷ power limit — ≤ 30 % → 30 %, ≥ 80 % → 40 %, in between proportional (55 % → 35 %). Map key `gpu:min_full_load_pct` (default 40).
- Not active on ws298 while `safety:off` / `readonly` are set (the service writes nothing to the card).
- Measurement grids (`rpmgrid`) never go below 40 % (rejected at parse time).

## Idle card fans: never 0 rpm (Seb, 2026-10-21)
- Future WS.Sensor GPU curve for normal work: automatic, but **zero-RPM off** — at idle the card fans run at the 30 % minimum, rising to 40 % at full load (rule above). Not built yet: today "Factory" hands the card to the driver, whose curve stops the fans at idle.
- Exception agreed for the measurement program: at the end of an `rpmgrid` run the cards go back to the driver (Auto) once.

## Stage E — rpmgrid (Chełm, 2× RTX 5090 FE, ~2 slots apart)
- Plan string `a:…;b:…;ab:…` (`exp:<run>:plan`): `a` = load only card A (B logged, same fan duty), `b` = only B, `ab` = both. Each part = case rpm list × card % list, case outer descending, card inner descending, never < 40 %.
- Case by tachometer rpm (jump to computed duty ≈ 30 rpm per 1 %, then 5 s correction; 3000 = above max ≈ 2920 → 100 %).
- Point ≥ 5 min and until core and memory slopes < 0.2 °C/min over 120 s, max 20 min; result = mean of last 60 s → `grid.csv`, written immediately per point, every card in its own columns.
- Load process died → interrupted point written (`settled = -1`), load restarted, same point repeated from the start.
- No WS.Sensor safety stops (Seb): NVIDIA driver/firmware only. Room temperature entered by hand.
