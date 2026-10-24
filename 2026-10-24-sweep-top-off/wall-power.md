# Wall power reading — ws298, 2026-10-24

| Reading | Seb's time | Lab state (live.json 13:46:46, message received 13:46) | NVML GPU sum | Other NVML/LHM |
|---|---|---|---|---|
| 1341 W at the wall (whole PC) | "~14:00" (Lab clock: received 13:46) | PL sweep (top off, 90 % GPU fans): step 3, PL 90 % = 518 W per card, just after step 2 (95 % = 546 W, last seen 13:45:24); case 1603 rpm, radiator 1594 rpm, pump 2202 rpm, AIO fan 1888 rpm | 1036 W (518 + 518) — or 1092 W if the reading was taken during step 2 | CPU package 60.6 W |

Overhead (wall − GPU NVML): 305 W at 518 W/card (249 W if step 2). Includes CPU ~61 W, PSU loss, board, RAM, NVMe, pump and fans.
Assuming PSU efficiency ~92 % at this load (≈ 1234 W DC), DC rest-of-system ≈ 1234 − 1036 − 61 ≈ 137 W (step 3) — estimate, PSU curve not measured.
