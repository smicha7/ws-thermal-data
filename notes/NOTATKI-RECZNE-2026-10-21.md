# Notatki robocze — ręczne testy ws298, 2026-10-21

Robocze obserwacje Seba na żywo (wartości odczytane z ekranu, nie z logu). Do potwierdzenia z logów automatem.

**Warunki:** 1× RTX 5090 FE, obciążenie mix64 (GPU Load Test, 575 W), pokój 18,9 °C (Tapo, ręcznie), obudowa top otwarty.
Sterowanie: wentylatory karta = MSI Afterburner (ręcznie), wentylatory obudowa = aquasuite (ręcznie, od 12:21).
WS.Sensor bez własnych zabezpieczeń (tylko NVIDIA). Log co 1 s, tylko odczyt: `C:\ProgramData\WS.Sensor\experiments\2026-10-21-log-1\` (od 12:16).
Wcześniejsze serie: `2026-10-21-case-hold-1000` (seria 1, 10:55–11:16) i `…-1000b` (seria 2) — jeszcze nie pobrane.

## Obserwacje (karta 40 %)

| Czas | Obudowa | Napięcie obudowy | Power limit | Rdzeń | Pamięć | Uwagi |
|---|---|---|---|---|---|---|
| 12:28 | 1000 rpm | — | 100 % | ~81 | ~88 | ustalone |
| 12:40 | 1000 rpm | — | 100 % | 82–83 | 90 | |
| 12:48 | 2920 rpm (max) | — | 100 % | 74–75 | 82 | jeszcze spada |
| 12:51 | 2000 rpm | 7,4–7,5 V | 100 % | — | — | |
| 13:01 | 1500 rpm | 5,1–5,2 V | 100 % | 80 | 88 | |
| 13:02 | 1500 rpm | 5,1–5,2 V | **80 %** | 73 | 84 | ~1 min po zmianie |
| 13:03 | 1500 rpm | 5,1–5,2 V | **80 %** | 72 | 82 | dalej spada |
| 13:03 | 1500 rpm | 5,1–5,2 V | **80 %** | 71 | — | |
| 13:04 | 1500 rpm | 5,1–5,2 V | **70 %** | 67 | 80 | od razu po zmianie, spada |

## Wnioski robocze

1. **Obudowa ma duży wpływ przy niskich obrotach karty.** Karta 40 %: obudowa 1000 → 2920 rpm daje −8 °C na rdzeniu i −8 °C na pamięci. Wcześniejsza teza „obudowa tylko 2–5 °C, nasycenie” była prawdziwa tylko dla karty ≥ 55 % — do poprawki w artykule.
2. **Power limit to bardzo silna dźwignia.** 100 → 80 % przy obudowie 1500 / karcie 40 %: rdzeń −7 °C, pamięć −4 °C w ~1 min, potem −8 / −6 °C (72 / 82). Do sprawdzenia w logu: rzeczywista moc (~460 W?), zegary, koszt wydajności.
3. **Minimum wentylatorów karty:** 40 % pod pełnym obciążeniem (niżej nie ma sensu), 30 % w spoczynku. Nigdy 0 rpm w pracy.
4. **Hałas:** obudowa ~1500 rpm = górna granica akceptowalna akustycznie.
5. **Temperatura pokoju:** nasza piwnica ma ~19 °C. W domu latem 25–27 °C → temperatury karty o ~6–8 °C wyższe (≈ 1:1 z otoczeniem). Krzywe trzeba projektować pod ciepły pokój.
6. Przy 2 kartach (jutro, Chełm, 2× FE, ~2 sloty odstępu) wyniki będą inne — test A osobno / B osobno / obie.

## Seria 1 (rano, obudowa 1000, krótkie kroki — tylko 100 % ustalone)

| Karta | rpm | Rdzeń | Pamięć |
|---|---|---|---|
| 100 % | 3012 | 60,0 | 67,7 |
| 90 % | 2729 | 61,8 | 68,1 |
| 80 % | 2463 | 62,2 | 69,8 |
| 70 % | 2161 | 64,8 | 72,0 |
| 60 % | 1877 | 67,0 | 74,0 |
| 50 % | 1594 | 72,7* | 80,0* |
| 40 % | 1311 | 81,0* | 88,6* |

\* jeszcze rosło. Brak throttlingu termicznego — jedyny limit to moc 575 W; zegar rdzenia 2727 → 2599 MHz (−4,7 %) z temperaturą.

## Do potwierdzenia automatem
- Wszystkie punkty powyżej z logu (średnia 60 s, ustalenie |dT/dt| < 0,2 °C/min).
- Siatka power limit × obudowa × karta.
- Napięcie ↔ rpm obudowy (z logu aquaero).

## Log resolution (checked 2026-10-21 against the morning files hold-2026-10-21)
- aquaero Sensor 1 (intake): the long log (`aquaero/temperature/sensor_1`) is at **0.01 °C** (e.g. 18.76, 18.79). In `raw.csv` (`intake_c` column) it was rounded to **0.1 °C** — fixed (Lab: 2 decimal places), goes in with the next release (rpmgrid start), log-1 not interrupted.
- GPU core: `raw.csv core_c` = NVML, whole °C; at 0.01 °C in the long log as `nvapi/0/1` (since Lab 0.3.33 / tray 0.30.38).
- Hot spot: 0.01 °C (thermal registers) in raw.csv and the long log.
- GPU memory: whole °C only (the driver doesn't give more).

**13:06 (PL 70 %):** rdzeń 66, pamięć 80 → 78. Różnica pamięć−rdzeń ~12 °C (przy pełnej mocy 7–8 °C). Hipoteza: limit mocy obcina głównie zasilanie rdzenia, a pamięć dalej pracuje na 14 001 MHz z tym samym ruchem danych; pamięć reaguje też wolniej (większa bezwładność). Do sprawdzenia w logu po ustaleniu: zegary, moc, różnica ustalona.

**Decyzja Seba 13:08 — power limit w programie:** temperatury po zmianie PL stabilizują się w ~2 min → **2 min na punkt PL wystarczy**. Punkty PL: **100, 90, 80, 70 %** (575 / ~518 / ~460 / ~403 W), resztę interpolujemy. Seb sprawdzi ręcznie, czy karta przyjmie 60 % (~345 W) — możliwe, że minimum NVML na 5090 to ~400 W (= 70 %).

## Power limit in the rpmgrid program (proposal for Seb's decision 13:08)
- **NVML minimum on the RTX 5090 = 400 W (~70 % of 575 W).** Confirmed by last night's v3d run: a 350 W request was raised by the card to 400 W. So **60 % (345 W) is not allowed**; 70 % = 402 W is the lowest real point.
- Points PL 100 / 90 / 80 / 70 % = 575 / 518 / 460 / 402 W per card.
- Placement: a separate block after the main grid, `abpl:1500x40,70,100x100,90,80,70` = 12 points (case 1500 rpm, card fans 40 / 70 / 100 %, both cards loaded). PL 100 points run to steady state (≥ 5 min), the rest 2 min each (mean of the last 60 s). About 35–40 min.
- At the end of the run the limit returns to the reference (575 W) and the card fans to the driver (Auto).
- With `safety:off` WS.Sensor doesn't lower the limit itself; only the program does.
- Manual points today (case 1500, card 40 %): PL 100 % → core 80 / memory 88; PL 80 % → core 71 / memory 82; PL 70 % → core 65 / memory 78 °C.

**Potwierdzone 13:10:** minimalny power limit RTX 5090 = ~400 W = **69–70 %**. Afterburner zamienia 50 % na 69 %; NVML podnosi 350 W do 400 W. Punkt 60 % nie istnieje (spadek 65 → 63 °C to dochodzenie po kroku 70 %).

| 13:13 | 1500 rpm | 5,1–5,2 V | 100 % | 73 | 80 | **karta 50 %**, ~2 min po zmianie |
| 13:16 | 1500 rpm | 5,1–5,2 V | **80 %** | 65 | 76 | karta 50 % (PL 90 %: rdzeń ~70, pamięć 78) |
| 13:16 | 1500 rpm | 5,1–5,2 V | **70 %** | 62 | 74 | karta 50 %, natychmiast |
| 13:17 | 1500 rpm | 5,1–5,2 V | **70 %** | 60 | 72 | karta 50 %, końcowy odczyt |
| 13:20 | 1500 rpm | 5,1–5,2 V | 100 % | 67 | 74 | **karta 60 %** (noc v2d: 1279→66,8/74,2; 1882→66,4/73,8) |
| 13:23 | 2923 rpm | — | 100 % | 66 | 74 | karta 60 % — obudowa 1500→2923 prawie bez zmian (−1/0) |

**Wniosek 13:25:** przy karcie ≥ 60 % obudowa powyżej ~1500 rpm nic nie daje (1500 → 2923: rdzeń −1 °C, pamięć 0). Obudowa liczy się tylko przy wolnej karcie (40 %: −8 °C). Strategia cicha: karta ~60 %, obudowa ≤ 1500, ewentualnie PL.

## "Software sensor 2: aquaero is not receiving the PC temperature" alert (2026-10-21)
- Cause: read-only mode — the service deliberately stops writing the soft sensors to the aquaero (Seb controls in aquasuite).
- Tray 0.30.42 (released, no Lab restart): every cooling-service alert shows **once per episode** (it used to repeat every 10 min); again only after ≥ 30 min without it.
- Lab (goes out tomorrow with the rpmgrid release): with `readonly` the soft-sensor alert doesn't appear at all.
- Seb confirmed: the new tray icons are visible on ws298.
| 13:27 | 1011 rpm | 3,1–3,2 V | 100 % | 68 | ? | karta 60 % |
| 13:27 | 1011 rpm | 3,1–3,2 V | **70 %** | 58 | 72 | karta 60 % |

## Seb's markers vs log-1 (fetched 13:33, 30 s means ending at each marker; core 0.01 = NVAPI)
| time | Seb said | case rpm | card % | PL W | power W | core (0.01) | mem | hot | air | clock | throttle |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 12:24 | case 1000 manual (aquasuite), card 40%, core 75->76 rising,  | 1008 | 40 | 575 | 575 | 75.77 (NVML 75.8) | 82.6 | 86.23 | 19.00 | 2651 | power |
| 12:28 | steady core ~81, mem ~88 at card 40%, case 1000; room 18.9C; | 1008 | 40 | 575 | 50 | 60.18 (NVML 60.3) | 73.2 | 65.53 | 18.87 | 521 | none |
| 12:40 | case 1000, card 40%, core 82-83, mem 90 | 997 | 40 | 575 | 575 | 82.52 (NVML 82.6) | 90.0 | 93.35 | 18.94 | 2601 | power |
| 12:44 | case 2920 -> mem 88 then 86 (was 90), core 79 | 2921 | 40 | 575 | 575 | 78.42 (NVML 78.5) | 86.4 | 88.89 | 19.02 | 2622 | power |
| 12:47 | case 2920, card 40% -> core 75, mem 82 (from 82/90 at case 1 | 2932 | 40 | 575 | 575 | 75.11 (NVML 75.0) | 82.0 | 85.41 | 19.05 | 2653 | power |
| 12:48 | steady? case 2920, card 40% -> core ~75, mem ~82 | 2932 | 40 | 575 | 575 | 74.70 (NVML 74.9) | 82.0 | 84.86 | 19.12 | 2656 | power |
| 13:01 | case 1500, card 40% -> core 80, mem 88. NOW power limit 100% | 1496 | 40 | 575 | 575 | 80.25 (NVML 80.0) | 88.0 | 90.95 | 19.15 | 2614 | power |
| 13:02 | PL 80% -> core 73, mem 84 (from 80/88) | 1485 | 40 | 460 | 460 | 73.44 (NVML 73.5) | 85.1 | 82.08 | 19.14 | 2353 | power |
| 13:03 | PL 80% -> core 72, mem 82 | 1485 | 40 | 460 | 460 | 71.64 (NVML 71.6) | 82.4 | 80.19 | 19.11 | 2363 | power |
| 13:03 | PL 80% -> core 71 | 1485 | 40 | 460 | 460 | 71.24 (NVML 71.0) | 82.0 | 79.77 | 19.11 | 2363 | power |
| 13:04 | PL 70% -> core 67 immediately, mem 80 falling | 1485 | 40 | 405 | 404 | 68.04 (NVML 68.1) | 80.6 | 75.36 | 19.14 | 1994 | power |
| 13:05 | PL70 core 66, mem 80 -> 78; gap ~12C (vs 7-8 at full power) | 1485 | 40 | 402 | 402 | 66.28 (NVML 66.3) | 78.9 | 73.47 | 19.13 | 1993 | power |
| 13:05 | PL70 core 65, mem 78 | 1485 | 40 | 402 | 402 | 65.65 (NVML 65.7) | 78.0 | 72.84 | 19.15 | 1996 | power |
| 13:08 | PL60 core 63, mem 76 | 1485 | 40 | 400 | 400 | 63.40 (NVML 63.0) | 76.0 | 70.53 | 19.14 | 2002 | power |
| 13:10 | PL ~70% (floor) core 63, mem 7x (Seb said '70', unclear - pr | 1485 | 40 | 400 | 400 | 63.13 (NVML 63.0) | 75.7 | 70.20 | 19.11 | 2004 | power |
| 13:13 | card 50%, case 1500, PL100 -> core 73, mem 80 (~2 min) | 1485 | 50 | 575 | 575 | 72.76 (NVML 72.9) | 80.0 | 83.02 | 19.15 | 2675 | power |
| 13:14 | PL90 core falling to ~7x, mem stable 80 | 1485 | 50 | 518 | 518 | 70.05 (NVML 70.0) | 80.0 | 79.25 | 19.11 | 2550 | power |
| 13:14 | PL90 mem -> 78 | 1485 | 50 | 518 | 518 | 69.73 (NVML 69.9) | 79.0 | 78.86 | 19.11 | 2552 | power |
| 13:15 | PL80 core 67 immediately | 1485 | 50 | 489 | 491 | 68.40 (NVML 68.6) | 78.1 | 77.03 | 19.12 | 2478 | power |
| 13:15 | PL80 core 66, mem 78 | 1485 | 50 | 460 | 460 | 66.51 (NVML 66.6) | 78.0 | 74.56 | 19.10 | 2396 | power |
| 13:16 | PL80 core 65, mem 76 (card 50, case 1500) | 1485 | 50 | 460 | 460 | 65.31 (NVML 65.2) | 76.0 | 73.26 | 19.14 | 2402 | power |
| 13:16 | PL70 core 62, mem 74 (card 50, case 1500) | 1485 | 50 | 425 | 425 | 63.18 (NVML 63.3) | 75.5 | 70.51 | 19.15 | 2181 | power |
| 13:17 | PL70 core 61, mem 74 | 1485 | 50 | 402 | 402 | 61.44 (NVML 61.4) | 74.0 | 68.34 | 19.16 | 2038 | power |
| 13:17 | final PL70 card50 case1500 -> core 60, mem 72 | 1485 | 50 | 402 | 402 | 60.32 (NVML 60.2) | 72.9 | 67.19 | 19.13 | 2051 | power |
| 13:18 | PL100 card60 case1500 -> core 67, mem 74 (early) | 1485 | 60 | 575 | 575 | 66.87 (NVML 67.0) | 74.0 | 76.62 | 19.13 | 2707 | power |
| 13:20 | steady card60 case1500 PL100 -> core 67, mem 74; next case - | 1485 | 60 | 575 | 575 | 67.05 (NVML 67.0) | 74.3 | 76.77 | 19.16 | 2698 | power |
| 13:21 | case 2920 card60 -> core 67, mem 74 (no reaction yet) | 2912 | 60 | 575 | 575 | 66.85 (NVML 67.0) | 74.0 | 76.50 | 19.17 | 2707 | power |
| 13:23 | case 2923 card60 PL100 -> core 66, mem 74 (no change vs 1500 | 2923 | 60 | 575 | 575 | 66.30 (NVML 66.2) | 73.9 | 75.99 | 19.18 | 2710 | power |
| 13:24 | case 1011 rpm @ 3.1-3.2 V, card60 PL100 -> core 67, mem 74 ( | 1016 | 60 | 575 | 575 | 66.88 (NVML 67.0) | 74.0 | 76.62 | 19.20 | 2706 | power |
| 13:25 | case 1011 card60 PL100 -> core 68, mem 7? (unclear: 'siement | 1011 | 60 | 575 | 575 | 67.72 (NVML 67.9) | 75.5 | 77.59 | 19.20 | 2704 | power |
| 13:26 | PL70 card60 case1000 -> core 61, mem 74 (falling) | 1011 | 60 | 470 | 474 | 63.75 (NVML 63.9) | 75.0 | 71.84 | 19.18 | 2313 | power |
| 13:27 | PL70 card60 case1000 -> core 58, mem 72 | 1011 | 60 | 402 | 402 | 58.06 (NVML 58.1) | 71.5 | 64.88 | 19.21 | 2058 | power |

- Spoken readings agree with the log to ±1 °C everywhere. At 12:28 the load had already been stopped (power 50 W), hence 60 °C in the log.
- "PL 60 %" in Afterburner → the card takes **400 W** (NVML minimum ≈ 70 %), so 60 % = 70 % in practice.
- Throttle: only power cap the whole time; **no thermal throttling** (SW/HW thermal) at any point, max core 82.5 / memory 90 / hot spot 93.4.
- Card 60 %: case 1000 vs 1500 vs 2920 rpm → core 66.3–67.7, i.e. case speed hardly matters at that card speed; at card 40 % it is 82.5 → 74.7 (−8 °C) between 1000 and 2920.

## grid1c — 1 card, 112 points × 60 s (13:55–15:57) + repeat grid1d (from 15:57)
Files: `data/grid1c-2026-10-21/` (grid.csv 112 rows, raw.csv, long 38 MB, log). Charts: `grid1c.png` (panel per case speed, core solid / memory dashed vs card %, colour = PL), `vs-v2d.png` (PL 100 vs night v2d), tables `grid1c-table.md`, `vs-v2d.md`. Air 19.04–19.55 °C (night 18.8–19.1).

**Data quality (60 s points are mostly NOT settled):**
- Median core trend: PL 100 points **+3.2 °C/min** (after the jump from PL 70 of the previous card, +175 W → read too LOW, typically 1.5–3 °C, memory 2–4.6 °C), PL 90/80/70 points **−2.0 °C/min** (still falling → read slightly too HIGH).
- Card 40 % at the start of the 1500/2000/3000 level (after the jump from card 100 %): **10–15 °C too low** → repeated in grid1d.
- Comparison with night v2d (24 PL 100 pairs, `vs-v2d.md`): agreement ≤ 0.5 °C only where the history is the same (1500/60 %, 2000/50–60 %). The other > 1 °C differences = the 60 s time + order (heating after PL 70), **not the air** (today is even 0.3–0.5 °C warmer).
- Night 2912 rpm / card 100 % (63.95 °C) differs from its neighbours (60–61 °C at 2415/1893) → probably the night point after the cooling-down/ordering of the night grid; treat with caution.

**Repeat grid1d (card 40 %, each level settled first ≥ 5 min; values from log.txt read at 16:27, CSV not yet fetched):**

| case | PL 100 | PL 90 | PL 80 | PL 70 |
|---|---|---|---|---|
| 1500 | 80.0 / 88.0 | 76.6 / 86.0 | 72.0 / 83.2 | 66.8 / 80.0 |
| 2000 | 77.9 / 86.0 | 74.3 / 84.0 | 69.9 / 80.4 | 64.5 / 77.0 |
| 3000 (≈2920) | 74.0 / 82.0 | (after 16:27) | | |

(core / memory °C). Compared with grid1c these points are higher by 10–15 °C at the start of the level (e.g. 2000/40/PL100: 62.7 → 77.9) and agree with the night (74.2 @ 1893, 71.7 @ 2935).

**Conclusions for tomorrow (2 cards):** adaptive time (Lab ≥ 0.3.40) + also after PL up by ≥ 20 pts (in the code, not yet released). For a PL 100 point after PL 70 count ≥ 5 min. Open decision: repeating the 21 PL 100 points from today (~1 h 45 min).

## FINAL TABLE grid1c + grid1d + night v2d (Seb: no PL100 repeat; PL100 = night steady values)
Files: `data/grid1c-2026-10-21/final.csv`, `final-table.md` (112 rows, "source" column), chart `final.png`; `vs-v2d.png` (PL100 today vs night). Repeat `data/grid1d-2026-10-21/` (finished 16:30:33, aquaero restored).
Sources: card 40 % at case 1500/2000/3000 = grid1d (level settled first, PL 90/80/70 after 75 s); PL 100 at card ≥ 50 % = night v2d steady (case 1000 and 1500 both use the night 1279/1290 rpm points — the night had no separate levels there); 1000/40/PL100 = grid1c after 660 s of warm-up (settled); other PL 90/80/70 points = 60/75 s (still falling at −2…−3 °C/min → read ~1–2 °C high).

PL 100 % (575 W), core/memory °C — rows case rpm, columns card 40/50/60/70/80/90/100 %:
| case | 40 | 50 | 60 | 70 | 80 | 90 | 100 |
|---|---|---|---|---|---|---|---|
| 1000 | 83/92 | 75/84* | 67/74 | 65/73 | 62/70 | 61/68 | 61/68 |
| 1500 | 80/88 | 71/78 | 67/74 | 65/73 | 62/70 | 61/68 | 61/68 |
| 2000 | 78/86 | 70/77 | 66/74 | 65/72 | 61/68 | 60/68 | 60/69 |
| ≈2920 | 74/82 | 68/75 | 66/72 | 64/72 | 62/68 | 60/68 | 64/73** |

PL 70 % (402 W):
| case | 40 | 50 | 60 | 70 | 80 | 90 | 100 |
|---|---|---|---|---|---|---|---|
| 1000 | 70/84 | 63/76 | 57/70 | 54/67 | 52/65 | 51/64 | 49/62 |
| 1500 | 67/80 | 61/74 | 56/68 | 52/66 | 51/64 | 49/62 | 48/61 |
| 2000 | 64/77 | 59/72 | 56/68 | 53/66 | 50/63 | 49/62 | 47/60 |
| ≈2920 | 61/74 | 57/69 | 54/66 | 52/64 | 50/63 | 49/62 | 48/60 |

\* today's 60 s, no night point (unsettled, probably ~2–3 °C too low). \** night point 2912 rpm / 100 % deviates from its neighbours (probably order of the night grid) — treat with caution.

**Conclusions:**
1. **Card fans dominate:** at PL 100 going from card 40 → 100 % lowers the core by ~20 °C (83 → 61 at case 1000) and memory by ~24 °C (92 → 68).
2. **Case fans matter only at low card speed:** at card 40 % case 1000 → 2920 rpm = core −9 °C, memory −10 °C; from card 60 % upwards the difference is ≤ 2 °C. 1500 rpm (Seb's acoustic ceiling) gives about 1/3 of that gain at card 40 %.
3. **Power limit 575 → 402 W** = core −13 °C and memory −8 °C at card 40 %; at card 100 % core −12, memory −6. Memory gains less from PL, so the memory−core gap grows from ~8 °C (575 W) to ~13 °C (402 W).
4. **No thermal throttling** anywhere (power cap only); the hottest point 1000 rpm / card 40 % / 575 W = core 83, memory 92, hot spot 94 °C, i.e. below the memory working limit of 100 °C, but memory above 90 °C.
5. **Method:** 60 s per point isn't enough after big jumps (PL 70 → 100 points +3 °C/min, card jump 100 → 40 % 10–15 °C too low). For tomorrow (2 cards) the adaptive time is in the code (≥ 5 min after a change of case, card down > 10 pts, PL up ≥ 20 pts), not yet released.

## Model rdzenia — rozszerzenia fizyczne (17:50, model_physics_core.py)
- Bazowy A: T = Tin + θ0 + P·[r∞ + k·N^−m·C^−q], RMSE 0,82 / LOO 0,85 °C, θ0 = 10,8 °C.
- Po korekcie punktów 60 s do stanu ustalonego (pierwszy rząd, T∞ ≈ T + slope·τ, τ ≈ 70 s): **θ0 spada do ~0,7 °C**, RMSE 0,72 / LOO 0,74 °C, ustalone 0,58 °C. Wniosek: θ0 był artefaktem nieustalonych punktów; fizycznie czysty model T = Tin + P·R(N, C).
- Człon kaloryczny/recyrkulacji P/C lub P/N: poprawa ≤ 0,05 °C i niefizyczne znaki → odrzucone.
- Następny krok: model dynamiczny (sieć RC Fostera/Cauera, τ zależne od N i C) dopasowany do logów 1 Hz zamiast średnich 60 s; dwa węzły rdzeń↔pamięć na wspólnym radiatorze; GP na resztach dla niepewności; jutro zmienne 2. karty (moc sąsiadki, odstęp w slotach, pozycja).

## Model dynamiczny (18:05, `dyn_model.py`)
Sieć RC (Cauer) dopasowana do **całych przebiegów 1 Hz** (symulacja swobodna od pierwszej próbki, bez resetów; dyskretyzacja dokładna przez exp. macierzy, 1 s). Uczenie: grid1c. Test: log-1, grid1d, hold + cała noc v2d. Wejścia: P(t), obroty karty N(t), obudowy C(t), Tin(t). Rdzeń z NVAPI (0,01 °C).
- **Najlepszy: M2 (2 węzły), wzór potęgowy.** Rdzeń = radiator + **natychmiastowy skok P·Rjs** (pojemność krzemu → 0, τ < 1 s, przy 1 Hz niewidoczne) + jedna wolna stała czasu radiatora.
  T∞ = Tin + θ0 + P·[Rjs + ra + k·(N/1000)^−m·(C/1500)^−q]; Rjs = 38,6 m°C/W, ra = 11,4 m°C/W, k = 82,0 m°C/W, m = 1,67, q = 0,24, θ0 = 3,2 °C, C radiatora = 1935 J/°C.
- **RMSE symulacji rdzenia:** uczenie 0,53 °C; test log-1 0,92, grid1d 1,01, hold 1,00 (razem dzień 0,97 °C); noc v2d 1,89 °C (model stale ~2 °C za chłodny). 1 węzeł: 2,3 / 4,2 °C — odrzucony. 3 węzły nic nie dają (drugi węzeł też zapada się do zera).
- **Stała czasu (radiator):** 129 s (40 %, obudowa 1000) → 104 s (40 %, 2920) → 82/68 s (60 %) → 50/43 s (100 %). τ ≈ C·R_radiatora, więc rośnie przy wolnych wentylatorach. Do tego natychmiastowy skok rdzenia ≈ 22 °C przy 575 W (dlatego zmiana PL „działa od razu”).
- **θ0 NIE znika** w modelu dynamicznym: 3,2 °C; wymuszenie θ0 = 0 psuje test (0,97 → 1,68 °C). Na nocnych punktach ustalonych model jest 2,1 °C za nisko (7 pkt). Interpretacja: realny podgrzew powietrza wlotowego karty w obudowie (CPU/zasilacz) zależny od sesji — a nie artefakt 60 s. Warto dołożyć czujnik powietrza tuż przy wlocie karty.
- **Kształt przy niskich obrotach** (uwaga koordynatora: model statyczny za gorący o 1,5–2,2 °C przy 40 %/PL100): w dynamice bias przy N ≤ 1350 rpm i pełnej mocy = **+0,10 °C** — czyli to był efekt nieustalonych punktów, nie kształt. Formy z nasyceniem k/(n^m+s^m) i konwekcja+człon kaloryczny (k·n^−m + kc/n) nie poprawiają testu (sat 1,13 °C, conv = pow, kc → 0).
- **Pamięć:** węzeł 1. rzędu przy radiatorze: τm dTm/dt = Tin + 1,035·(Ts − Tin) + 0,0078·P + 15,3·[obciążenie] + 12,2 − Tm, τm = 10 s. Uczona na grid1c + log-1 (grid1c nie ma biegu jałowego). RMSE: grid1c 0,85, grid1d 1,46, hold 1,32, noc 2,31 °C (odczyt pamięci tylko co 1 °C).
- Pliki: `results-2026-10-21/dyn-a-grid1c.png`, `dyn-b-test.png`, `dyn-c-steady.png`, `dyn-model.json`. Seria val1 jeszcze nie dotarła — skrypt sam ją doda do testu, gdy pojawi się `data/val1-2026-10-21/raw.csv`.

**Seb pyta, czy wszystkie pomiary zrobione (21:2x):** val1 ✓ (20/20, 20:42), dyn1 ✓ (56/56, 23:21), val2 w toku (od 23:21, koniec ~01:30). Model dynamiczny na pełnych danych: przeliczany po dyn1 (cross-walidacja), publikacja po val2.

## Model dynamiczny – pełne dane (wieczór, `dyn_cv.py`)
Dane: grid1c, dyn1 (56 losowych kroków, hiperkostka łacińska), val1 (20 pkt ustalonych), log-1, hold, grid1d; noc v2d tylko jako test. RMSE = symulacja swobodna 1 Hz od pierwszej próbki.
- **Walidacja krzyżowa (rdzeń, °C):**
  (a) uczenie grid1c → dyn1 **0,56**, val1 0,66, log-1 0,92, hold 1,00, grid1d 1,01, noc 1,89 — model z popołudnia przeszedł losowe skoki bez poprawek.
  (b) uczenie dyn1 → grid1c 1,05, val1 0,86, log-1 1,88, hold 1,54, grid1d 1,35 — sam dyn1 słabiej przenosi się na długie biegi z biegiem jałowym (słabo określa θ0/ra).
  (c) pomijanie po jednym przebiegu (LORO): grid1c 0,61, dyn1 0,59, val1 0,65, log-1 0,97, hold 0,99, grid1d 0,86 → **razem 0,72 °C**; noc 2,0 °C.
  val1, punkty ustalone (stan ustalony z modelu vs pomiar): **0,65 °C** (val1 pominięty w uczeniu), 0,60 °C w uczeniu.
- **Forma:** potęgowa = konwekcja+kaloryczny (kc → 0) 0,72; z nasyceniem 0,74; **θ0 = 0: 1,03** (hold 2,15) → stały przesuw jest potrzebny; dryf wlotu (θ0 + φ·P·C^−qa, τ ≈ 200 s) 0,716 — zysk 0,008 °C przy 3 słabo określonych parametrach → odrzucony (zasada: dodatkowe parametry muszą dać > 0,05 °C).
- **Model zalecany (wszystkie dane dzienne), 95 % CI** (poprawione na autokorelację reszt ρ = 0,81):
  T∞ = Tin + θ0 + P·[Rjs + ra + k·(N/1000)^−m·(C/1500)^−q]
  Rjs = 39,2 [38,9–39,5] m°C/W (skok natychmiastowy), ra = 11,5 [10,9–12,1] m°C/W, k = 81,8 [81,5–82,1] m°C/W, m = 1,71 [1,67–1,74], q = 0,281 [0,275–0,287], θ0 = 3,20 [3,10–3,30] °C, C radiatora = 1929 [1900–1959] J/°C. Rozrzut LORO podobnej wielkości (m 1,64–1,74, θ0 3,10–3,44).
- **τ(N, C):** 40 %: 129 s (obudowa 1000) / 117 (1500) / 110 (2000) / 101 (2920); 60 %: 81/75/71/66; 80 %: 60/56/54/50; 100 %: 49/46/44/42 s. Plus natychmiastowy skok rdzenia ≈ 39 m°C/W·ΔP (np. PL 100→70 % = −6,8 °C od razu).
- **Pamięć:** τm = 10 s, Tm∞ = Tin + 1,024·(Ts − Tin) + 0,0103·P + 14,7·[obciążenie] + 11,9; LORO RMSE 0,68–1,42 °C (dyn1 0,68, val1 0,85), noc 2,4 °C.
- **Tabela do krzywych:** `results-2026-10-21/dyn-steady-lookup.md` / `.csv` (Tin 19/25/30 × karta 40–100 % × obudowa 1000/1500/2000/2920 × PL 70–100 %). Np. Tin 30, PL 100, karta 40 %, obudowa 1500 → 90,7 °C (powyżej progu 88 °C). Tin 25/30 to ekstrapolacja 1:1 z temperaturą powietrza (dane tylko 19–20 °C).
- **Ograniczenia:** noc v2d stale ~2 °C cieplejsza od modelu → θ0 zależy od sesji/stanu obudowy (czujnik powietrza przy wlocie karty by to rozstrzygnął). 1 karta, otwarta góra obudowy.
- Wykresy: `dyn-d-dyn1.png`, `dyn-e-cv.png`, `dyn-f-steady-maps.png`; liczby `dyn-cv.json`. val2 (~01:30) — dołożyć do DAY w `dyn_cv.py` i puścić ponownie.

## Model dynamiczny – z val2 (22.10, `dyn_cv.py`, 7 przebiegów dziennych)
Zasada Seba: wszystko w °C (różnice, RMSE, θ0), opory w m°C/W, pojemność w J/°C.
- **val2** (9 pkt ustalonych, powtórki + karta 45/65 % przy obudowie 1500): przebieg pominięty w uczeniu (LORO) **0,79 °C**, punkty ustalone **0,71 °C**; model z samego grid1c: 0,76 / 0,67 °C; z samego dyn1: 1,18 / 1,27 °C.
- **LORO (rdzeń, °C):** grid1c 0,59, dyn1 0,58, val1 0,64, val2 0,79, log-1 0,97, hold 0,99, grid1d 0,90 → razem **0,72 °C**; val1 ustalone 0,63 °C; noc 2,0 °C.
- **Forma bez zmian:** potęgowa = konwekcja+kaloryczny 0,724; nasycenie 0,732; θ0 = 0: 0,996; dryf wlotu 0,717 (zysk 0,007 °C → odrzucony).
- **Model zalecany (95 % CI, wszystkie 7 przebiegów):** Rjs = 39,0 [38,7–39,3] m°C/W, ra = 12,0 [11,4–12,6] m°C/W, k = 81,9 [81,6–82,2] m°C/W, m = 1,72 [1,69–1,75], q = 0,277 [0,271–0,283], θ0 = 3,14 [3,04–3,25] °C, C radiatora = 1914 [1887–1940] J/°C. RMSE w uczeniu: val1 ustalone 0,60, val2 ustalone 0,70 °C.
- **τ** praktycznie bez zmian: 40 %: 128/117/110/101 s (obudowa 1000/1500/2000/2920), 60 %: 81/75/71/66, 80 %: 60/56/54/51, 100 %: 49/46/45/42 s.
- **Pamięć (LORO):** 0,68–1,41 °C, val2 0,91 °C.
- Odświeżone: `dyn-steady-lookup.md/.csv` (nagłówek z parametrami w m°C/W), `dyn-d-dyn1.png`, `dyn-e-cv.png`, `dyn-f-steady-maps.png` (val1 ●, val2 ■), `dyn-a/b/c` (etykiety w °C), `dyn-cv.json`.

## Model stanu ustalonego – diagnostyka (22.10, `steady_data.py` + `steady_stats.py`, uruchamianie `./run_steady.sh`)
Dane: tylko punkty ustalone — val1 (20), val2 (9), grid1d (1, ustalony), start grid1c po 660 s (1), noc v2d (7 z `settled=1`; sesja osobna). Razem n = 38. Sesje: val1 (odniesienie), val2, „popołudnie” (grid1c+grid1d), noc. steady2 wejdzie sam (patrz niżej).
**Rdzeń:** NVAPI 0,01 °C z logu 1 Hz, nie tabela NVML (całe °C). Dodatkowo każdy punkt ekstrapolowany do stanu ustalonego (dopasowanie T∞ − A·e^(−t/τ) do ostatnich minut punktu): punkty przy karcie 40–45 % były jeszcze **0,2–0,4 °C za nisko** po 8 min (τ ≈ 115–155 s). Flaga `settled` tego nie widziała, bo nachylenie liczono z całych °C NVML (kwantyzacja chowała wzrost 0,1–0,2 °C/min).

**Porównanie postaci** (wszystkie z efektem sesji; RMSE / LOO / 5-krotna CV / pomijanie sesji, °C; BIC):
| postać R(N, C) | RMSE | LOO | CV5 | LOSO | BIC | DW po N |
|---|---|---|---|---|---|---|
| potęgowa k·N^−m·C^−q | 0,56 | 0,84 | 0,88 | 1,44 | 97,1 | 0,45 |
| wykładnicza k·e^(−aN)·C^−q (dotychczasowa) | 0,43 | 0,63 | 0,65 | 1,33 | 77,2 | 0,39 |
| wymierna | 0,53 | 0,79 | 0,82 | 1,42 | 91,9 | 0,47 |
| **przewodności równoległe 1/(gN·N^m + gC·C^s)** | **0,37** | **0,52** | **0,55** | 1,35 | 68,2 | 0,42 |
| efektywny przepływ k·(N + b·C)^−m | 0,43 | 0,56 | 0,61 | 1,35 | 76,1 | 0,39 |
| odpowiedź R = (T−Tin)/P (to samo co wyżej, WLS) | 0,37 | 0,51 | 0,54 | 1,31 | 64,1 | 0,41 |
| log-log ln(T−Tin) ~ ln P, ln N, ln C, interakcje | 0,34 | 0,71 | 0,73 | 1,46 | 64,4 | 0,57 |
| splajn naturalny w N (benchmark) | 0,39 | 0,80 | 0,92 | 1,34 | 79,3 | 0,56 |
| splajn tensorowy R(N, C) (benchmark 2D) | 0,13 | 8,0 | 26 | 82 | 11,9 | 1,38 |
Bez efektu sesji wszystkie postaci mają RMSE 0,82–0,96 °C i DW ≈ 0,1 — **efekt sesji jest konieczny** (noc +2,43 °C wobec val1).

**Wybrany model** (najmniejszy LOO wśród postaci parametrycznych): T = Tin + θ0 + θ_sesja + P·[r∞ + 1/(gN·(N/1000)^m + gC·(C/1500)^s)]
θ0 = 1,93 °C (HC3 SE 0,54), r∞ = 53,9 m°C/W (6,0), gN = 6,4 W/°C (2,9), m = 2,46 (0,89), gC = 8,1 W/°C (5,1), s = 0,81 (0,30); θ noc = +2,43 °C (0,43), val2 +0,11, popołudnie +0,08. Fizycznie: przewodność radiatora = część od wentylatorów karty + część od przepływu z obudowy, połączone równolegle; stąd obudowa daje dużo przy wolnej karcie i prawie nic przy szybkiej (to samo, co widać w danych). RMSE 0,37 °C, LOO 0,52 °C, średnia reszt 0,000 °C.

**Testy (wybrany model):**
| test | statystyka | p | werdykt |
|---|---|---|---|
| średnia reszt = 0 | 0,000 °C | 1,00 | OK |
| Durbin–Watson po N w seriach (obudowa, PL) | 0,42 | < 0,001 (MC) | autokorelacja |
| Durbin–Watson w czasie | 2,49 | 0,82 | OK |
| Breusch–Godfrey rz. 1 / 2 po N | 8,5 / 8,5 | 0,004 / 0,014 | autokorelacja |
| Breusch–Godfrey rz. 1 / 2 w czasie | 3,1 / 3,4 | 0,08 / 0,18 | OK |
| korelacja reszt z N, C, P, Tin, czasem | −0,02 … 0,08 | ≥ 0,64 | OK |
| Breusch–Pagan / White | 13,7 / 31,9 | 0,003 / 0,0002 | heteroskedastyczność → SE HC3 |
| White uproszczony (ŷ, ŷ²) | 1,4 | 0,50 | OK |
| Shapiro–Wilk / Jarque–Bera | 0,908 / 19,9 | 0,004 / < 0,001 | jeden punkt odstający |
| ten sam bez nocnego punktu obudowa 654 rpm (t* = +5,5) | 0,956 / 1,4 | 0,15 / 0,51 | OK |
| RESET (ŷ²) / (ŷ², ŷ³) | 0,80 / 1,60 | 0,38 / 0,22 | OK |
| brak dopasowania (czysty błąd z powtórzeń, SD 0,14 °C) | F = 11,1 | 0,003 | kształt niedoskonały |
| model vs splajn naturalny | — | 1,00 | parametryczny nie gorszy |
| efekt sesji = 0 (Wald, HC3) | 33,2 | < 0,001 | sesja istotna |
| Box–Cox (obie strony) λ = 1 | λ̂ = 1,65, CI [−0,95; 3,0] | 0,59 | bez transformacji; log też nieodrzucony (p 0,19) |
| dryf w sesji z kotwic (noc 55/72 ×3) | +0,015 °C/h | 0,51 | brak dryfu |

**Skąd niski DW po N (i co go nie naprawia):** NVML całe °C → DW 0,51; NVAPI 0,01 °C → 0,40; + korekta dojścia → 0,42 (**to nie kwantyzacja**). Dryf sesji — nie (DW w czasie 2,49, kotwice +0,015 °C/h). **Postać funkcyjna — tak:** splajn tensorowy R(N, C) + krzywizna P² + sesja daje DW 2,00 (p MC = 0,50) przy RMSE 0,11 °C, tj. na poziomie czystego błędu 0,14 °C. Reszty są więc gładką resztą kształtu powierzchni R(N, C) (karta × obudowa) i lekkiej wklęsłości w P (P^0,90), ±0,3 °C. Elastyczny model trafia, ale przy obecnym planie pomiarów nie przewiduje (LOO 8 °C — puste komórki siatki), więc nie nadaje się do krzywych. Korekta Praisa–Winstena (ρ = 0,66) zmienia parametry w granicach błędu (r∞ 50,2, m 2,14) — autokorelacja to objaw kształtu, nie cecha błędów, dlatego jej nie „leczymy” FGLS, tylko raportujemy SE HC3 i klastrowe (sesja, seria). Różnice pierwsze wzdłuż N (odpowiednik stóp wzrostu, 15 par, sesja i θ0 znikają): gN 5,7 ± 0,3 W/°C, m 2,44 ± 0,09 — zgodne z poziomami (6,4; 2,46). Elastyczności log-log w średniej: P 0,95, N −0,59, C −0,08.

**Co dalej:** steady2 (karta 40 % × obudowa 1000–2920 × PL 100–70 + karta 60/80/100 + 3 kotwice) wypełnia dokładnie brakujące komórki powierzchni R(N, C) przy jednej sesji. Pipeline sam go weźmie jako sesję odniesienia i przeliczy także samo steady2 (`SUBSET=steady2`). Watcher `./run_steady.sh --watch` działa w tle (co 10 min, kończy po `"state":"done"` albo po 10 h; log `results-2026-10-22/watch.log`).
Pliki: `results-2026-10-22/steady-compare.csv`, `steady-stats.json/.txt`, `steady-residuals.csv`, `steady-points.csv`, `steady-diagnostics.png`, `steady-two-ways.png`, szkic artykułu `article-stats-draft.md`.

## 22.10 wieczór — ctrl1, cpu1b, steady2 long
- ctrl1 (6 × 30 min): regulator na prawdziwej karcie = symulacja (rdzeń ustalony ±0,5 °C, szczyt kroku 0,6–1,0 °C nad celem, 0 s > cel + 1 °C, PL nigdy nie cięty). Kolumna NVAPI 0,01 °C pusta → regulator jechał na 1 °C z NVML; na przebiegach więcej zawróceń wentylatorów niż w symulacji (do wygładzenia przed wydaniem dla klientów). Szczegóły: CONTROLLER.md.
- cpu1 (16:40) przerwany na starcie: aquaero odrzuciło min 100 % przy maks. < 100 %. Poprawka Lab 0.3.50 (controller=none) → cpu1b 19:05.
- cpu1b: 9950X, 32 wątki, chłodnica + obudowa 100 %, wlot 19,3 °C: Tctl maks. 74,3 (szpilka 15 s) / ustalony 68,2 °C; CCD1 70,6 / 66,1; CCD2 69,1 / 65,7; pakiet 200 W (limit PPT), 5,09 GHz; bez dławienia termicznego; zapas ~27 °C do 95 °C. data/cpu1-2026-10-22/summary.md.
- steady2: dziennik 1 Hz (73,7 MB) pobrany i opublikowany (ws-thermal-data, asset).
- cpu2 (20:43–20:55): chłodnica 2744 → 1500 rpm przy 200 W: Tctl ustalony 70,9 → 71,2 °C, CCD ~+2 °C; skoki co 10 s bez mierzalnego trendu (ciecz reaguje w minutach); maks. 75,6 °C, bez dławienia. data/cpu2-2026-10-22/summary.md.
- cpu3 (21:20–21:41): obudowa 1000 rpm; chłodnica 1013 rpm → Tctl 75,1 °C; minimum chłodnicy 882 rpm (5,5 %; 800/600 nieosiągalne) → Tctl 77,4–77,7 °C, 200 W, ~5,04 GHz, bez spowolnienia; wpływ obudowy nierozdzielony (potrzebny punkt obudowa 2930 / chłodnica 1000).
