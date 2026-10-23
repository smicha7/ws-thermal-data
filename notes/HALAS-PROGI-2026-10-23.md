# Hałas wentylatorów: progi, obroty, dBA (research 2026-10-23)

Skrót: niezależne pomiary z podanym dystansem i tłem. Bez dystansu = liczba słaba. Przeliczenia: odległość ×2 → −6 dB (pole swobodne); obroty: ΔL ≈ 50·log10(N2/N1) (prawo wentylatorowe, [Comair Rotron](https://comairrotron.com/article/acoustic-noise-causes-rating-systems-and-design-guidelines.html)); średnica: +70·log10(D2/D1) (140 vs 120 mm ≈ +4,7 dB przy tych samych obrotach, czyli ten sam hałas przy ~20 % niższych rpm).

## 1. Percepcja – punkty odniesienia

| Fakt | Liczba | Źródło |
|---|---|---|
| Skala SPCR (dBA @1 m) | <15 niesłyszalne · 15–20 ledwo słyszalne (PC bez wentylatorów) · 20–25 bardzo cicho (cichy szept) · 25–30 cicho (sypialnia w nocy) · 35–45 „stonowane” (typowy PC, cichy biuro/biblioteka) · 50 wyraźnie słyszalne · 60 głośno | [SPCR primer](https://silentpcreview.com/archive-a-primer-on-noise-in-computing/) |
| +10 dB ≈ 2× głośniej; 3 dB wyraźnie słyszalne; 1 dB próg różnicy | — | jw. |
| Źródła się sumują: 2 identyczne +3 dB, 4 → +6 dB, 8 → +9 dB | — | jw. |
| WHO: wnętrze domu ≤35 dBA | — | jw. |
| 20 dBA @1 m = „ciszej niż 99,9 % gotowych PC” | — | [SPCR](https://silentpcreview.com/book/six-hdd-sff-server-test-results/) |
| Sone: liniowa głośność (2× sone = 2× głośniej); 1 sone @50 cm ≈ 35 dBA @1 m (zgrubnie, c't) | — | [heise/c't](https://www.heise.de/ratgeber/Laerm-messen-297358.html), [PCGH](https://www.pcgameshardware.de/Luftkuehlung-Hardware-217993/Specials/wissen-Geraeusch-Messungen-1280621/) |
| ECMA-74 / ISO 7779: główna wielkość = moc akustyczna LWA (bel); ciśnienie na stanowisku operatora/obserwatora tylko pomocniczo | — | [ECMA-74](https://ecma-international.org/publications-and-standards/standards/ecma-74) |
| Noctua: hałas wentylatora ma charakter dipola, zależy od kąta i odbić → różne stanowiska dają sprzeczne wyniki | — | [HWCooling / Noctua](https://www.hwcooling.net/en/noctua-on-measuring-fan-noise-different-angles-different-results/2/) |

Tło typowego pokoju: 25–30 dBA (sypialnia nocą wg SPCR), ciche pomieszczenie nocą ~20 dBA. Wentylator ~5–10 dB poniżej tła jest praktycznie niesłyszalny (zależy od charakteru tonu).

## (a) Tabela progów (pojedynczy wentylator, wolna przestrzeń)

| Klasa | dBA @1 m | dBA @0,5 m (+6) | 120 mm (rpm) | 140 mm (rpm) |
|---|---|---|---|---|
| Ultra-cichy / niesłyszalny | <15 | <21 | <~1000 (A12x25 G2), <~1150 (G1) | <~950 |
| Bardzo cichy | 15–20 | 21–26 | 1000–1300 (G2), 1150–1480 (G1), do ~1560 (P12) | 950–1200 (P14), do ~1280 (SW Pro 4 140) |
| Cichy | 20–25 | 26–31 | 1300–1500 (G2), 1280–1570 (SW Pro 4), 1480–1760 (G1) | 1200–1450 |
| Akceptowalny / słyszalny | 25–35 | 31–41 | 1500–2270 (SW Pro 4); G2 przy max 1800 ≈ 29 dBA | 1450–1730+ |
| Głośny | 35–45 | 41–51 | 2270–3030 (SW Pro 4: 40 dBA @2771) | >~1900 |
| Bardzo głośny | >45 | >51 | tylko wentylatory 3000+ rpm / GPU 90–100 % | — |

Wartości rpm z normalizowanych testów Hardware Busters (tabela b). Dla całego komputera dodaj sumowanie: 6 wentylatorów ≈ +8 dB, radiator/grill zwykle +3–6 dB.

## (b) Wentylatory: rpm → dBA

**Specyfikacje producentów (zwykle 1 m, komora, optymistyczne)**

| Wentylator | Max | z LNA | Źródło |
|---|---|---|---|
| NF-A12x25 G2 PWM | 1800 rpm / 22,5 dBA | 1500 / 18,1 | [Noctua](https://www.noctua.at/en/products/nf-a12x25-g2-pwm/specifications) |
| NF-A12x25 G2 LS-PWM | 1100 / 11,8 | 850 / 7,8 | [Noctua](https://www.noctua.at/en/products/nf-a12x25-g2-ls-pwm/specifications) |
| NF-A12x25 PWM (G1) | 2000 / 22,6 | 1700 / 18,8 | [Noctua](https://www.noctua.at/en/products/nf-a12x25-pwm/specifications) |
| NF-A14 PWM | 1500 / 24,6 | 1200 / – | [Noctua](https://noctua.at/en/nf-a14-pwm/specification) |
| Silent Wings Pro 4 120 | 3000 / 36,9 | – | [HWB](https://hwbusters.com/cooling/be-quiet-silent-wings-pro-4-120mm-fan-review/) |
| Silent Wings Pro 4 140 | 2400 / 36,8 | – | [Aquacomputer](https://shop.aquacomputer.de/Fans-Accessories/Fans/140-mm/be-quiet-Silent-Wings-Pro-4-140-mm-PWM::4198.html) |
| Silent Wings 4 140 PWM | 1170 / 13,6 | – | [HWB](https://hwbusters.com/cooling/be-quiet-silent-wings-4-140mm-pwm-fan-review/) |
| Arctic P14 PWM PST | 1700 / 0,3 sone (22,5 dBA) | – | [HWB](https://hwbusters.com/cooling/arctic-p14-pwm-pst-140mm-fan-review/) |

Uwaga: HWB zmierzył SW Pro 4 120 przy max 42,6 dBA @1 m vs 36,9 w specyfikacji (+5,7 dB) ([HWB s.11](https://hwbusters.com/cooling/be-quiet-silent-wings-pro-4-120mm-fan-review/11/)).

**Hardware Busters – rpm przy zadanym hałasie** (komora półbezechowa, tło ~6 dBA, 1 m, wolna przestrzeń, ISO 7779 – [metodyka](https://hwbusters.com/cooling/be-quiet-silent-wings-pro-4-120mm-fan-review/6/))

| Wentylator | 20 dBA | 25 dBA | 30 dBA | 35 | 40 | Źródło |
|---|---|---|---|---|---|---|
| NF-A12x25 G2 | 1306 | 1500 | 1820 | – | – | [HWB G2 LS rev. s.8](https://hwbusters.com/cooling/noctua-nf-a12x25-g2-ls-pwm-120mm-fan-review-money-for-nothing/8/) |
| NF-A12x25 G1 | 1476 | 1760 | 2079 | – | – | jw. |
| SW Pro 4 120 | 1281 | 1573 | 1871 | 2274 | 2771 | [HWB s.10](https://hwbusters.com/cooling/be-quiet-silent-wings-pro-4-120mm-fan-review/10/) |
| SW 4 120 High-Speed | 1467 | 1751 | 2094 | – | – | [HWB G2 LS s.8](https://hwbusters.com/cooling/noctua-nf-a12x25-g2-ls-pwm-120mm-fan-review-money-for-nothing/8/) |
| Arctic P12 PWM PST | 1559 | 1804 | – | – | – | [HWB s.10](https://hwbusters.com/cooling/be-quiet-silent-wings-pro-4-120mm-fan-review/10/) |
| Arctic P14 PWM PST | 1206 | 1429 | 1709 | – | – | [HWB P14](https://hwbusters.com/cooling/arctic-p14-pwm-pst-140mm-fan-review/) |
| SW Pro 4 140 (HS) | 1278 | 1456 | 1731 | – | – | jw. |

**TechPowerUp – dBA przy zadanych rpm** (wentylator na radiatorze, sonda 15 cm, komora z tłem ~19 dBA – [metodyka](https://www.techpowerup.com/reviews/Darkside/Gentle_Typhoon_1450_Black_Edition/4.html); dane z [recenzji G2](https://www.techpowerup.com/review/noctua-nf-a12x25-g2-pwm-fan/4.html)). Przeliczenie 15 cm → 1 m ≈ −16,5 dB (tylko orientacyjnie, pole bliskie).

| Wentylator | 750 | 1000 | 1250 | 1500 rpm |
|---|---|---|---|---|
| NF-A12x25 G2 | 27,4 | 30,2 | 33,8 | 37,4 |
| NF-A12x25 G1 | 27,2 | 29,1 | 32,8 | 36,4 |
| SW Pro 4 120 | 27,2 | 30,0 | 32,8 | 36,3 |
| Arctic P12 PWM PST | 27,3 | 30,4 | 33,4 | 37,1 |

Spójność: G2 przy 1500 rpm = 37,4 @15 cm → ~21 dBA @1 m, HWB: 25 dBA @1500 (wolna przestrzeń). Rząd wielkości się zgadza. Między modelami premium różnica przy tych samych obrotach to tylko ~1 dB.

Brak niezależnych pomiarów NF-A14 z dystansem (luka).

## (c) GPU RTX 5090 FE: % → rpm → dBA

Pomiary niezależne:

| Źródło | Warunki | Wynik |
|---|---|---|
| GamersNexus | komora, tło 14–14,5 dBA, 1 m, otwarta ława | 32,5 dBA @ ~1570 rpm (gra) – [GN](https://gamersnexus.net/gpus/nvidia-geforce-rtx-5090-founders-edition-review-benchmarks-gaming-thermals-power) |
| TechPowerUp | otwarta ława, pasywna, 50 cm | 40,1 dBA @1673 rpm; 4090 FE 35,1 dBA – [TPU](https://www.techpowerup.com/review/nvidia-geforce-rtx-5090-founders-edition/41.html) |
| TPU, karty partnerów | 50 cm | Suprim SOC 28,4 @1093; Astral Quiet 36,5 @1385; Astral 39,3 @1675; GameRock 39,8 @1894 – jw. |
| ComputerBase | zamknięta Fractal Torrent, tło ≈28 dB(A), dystans niepodany | 41,5 dB(A) @1700 rpm; 4090 FE 40,5 @1540 – [CB](https://www.computerbase.de/artikel/grafikkarten/nvidia-geforce-rtx-5090-test.91081/seite-10) |
| PCGH | 50 cm, sone | 2,8 sone @1620 rpm – [PCGH](https://www.pcgameshardware.de/Geforce-RTX-5090-Grafikkarte-281029/Tests/Reviews-Benchmarks-Vergleich-RTX-4090-1463971/6/) |
| LanOC | 18" (46 cm), tło 33,3 dBA, miernik klasy 2 | 50 % → 45,7; stock w grze 46 % → 44,1; 100 % (2873 rpm) → 58,4 dBA – [LanOC](https://lanoc.org/review/video-cards/nvidia-rtx-5090-founders-edition?showall=1) |
| Tom's Hardware | 10 cm, tło 31–32 dB(A) | 50,0 dB(A) w Cyberpunk – [THG](https://www.tomshardware.com/pc-components/gpus/nvidia-geforce-rtx-5090-review/8) |

Nasze mapowanie (40 % = 1310, 100 % = 3030, liniowo) + skalowanie 50·log10 od kotwic GN (1 m) i TPU (50 cm). Kotwice są ze sobą zgodne (GN przeliczony na 50 cm daje 38,7 vs TPU 38,7 przy 1570 rpm). LanOC daje dla 50→100 % przyrost +12,7 dB. Model 50·log daje +13,7 dB, więc zgodność w granicach ~1–2 dB. Bezwzględne wartości LanOC są o ~7 dB wyższe (mniejszy dystans, mikrofon na wentylator, wysokie tło).

| Wentylator GPU | rpm (nasze) | dBA @1 m (est.) | dBA @0,5 m (est.) | Klasa |
|---|---|---|---|---|
| 30 % | ~1020 (ekstrapol.) | ~23 | ~29 | bardzo cichy |
| 40 % | 1310 | ~29 | ~35 | cichy |
| 50 % | ~1600 | ~33 | ~39 | akceptowalny (≈ fabryczna krzywa w grze: 46–53 %) |
| 60 % | ~1880 | ~36,5 | ~43 | głośny (dolna granica) |
| 70 % | ~2170 | ~39,5 | ~46 | głośny |
| 90 % | ~2740 | ~44,5 | ~51 | bardzo głośny |
| 100 % | 3030 | ~47 | ~53 | bardzo głośny |

Fabryczny punkt pracy (TPU 1673 rpm, CB 1700, GN 1570) to wg naszego mapowania ~49–54 %. Recenzenci oceniają go jako „słyszalny, akceptowalny dla graczy, nie do cichego PC” (CB). Proponowana skala: ≤40 % cicha, 40–55 % akceptowalna, 55–70 % głośna, >70 % bardzo głośna. Dla stacji roboczej przy biurku (0,5–0,7 m) warto przesunąć granice o jeden stopień w dół.

## (d) Werdykt – skala Seba (120/140 mm)

| Seb | Dowody (pojedynczy wentylator, 1 m, wolna przestrzeń) | Ocena |
|---|---|---|
| ~800 rpm niesłyszalny | G2: ~9 dBA (ekstrapolacja z 20 dBA @1306); TPU @15 cm ~27–28 dBA przy 750 rpm | **Zgodne** |
| 1000 prawie bezgłośny | G2 ~14, G1 ~12 dBA @1 m | **Zgodne** (poniżej tła pokoju) |
| 1200 delikatny szum | G2 ~18, SW Pro 4 ~19 dBA | **Zgodne** (słyszalny tylko w cichym pokoju, z bliska) |
| 1500 zauważalny, OK | G2 25, SW Pro 4 ~24, G1 ~20 dBA | **Zgodne** (SPCR: „cicho / bardzo cicho”) |
| >1500 znaczący | 1800–2000 rpm: 28–32 dBA | **Zgodne dla całego komputera** (kilka wentylatorów +6–9 dB). Dla jednego wentylatora trochę surowo |
| 2000 dość głośny | G1 ~29, G2 ~32, SW Pro 4 ~32 dBA; w obudowie z 6 szt. ~40 | **Zgodne w realnym PC** |
| 3000 bardzo głośny | SW Pro 4: 42,6 dBA @1 m; jeden wentylator jak „typowy głośny PC” | **Zgodne** |

Wniosek: skala Seba dobrze opisuje **cały komputer przy biurku** (wiele wentylatorów, radiatory, 0,5–1 m). Dla pojedynczego wentylatora w komorze jest o ~1 klasę ostrożniejsza. Dla 140 mm każdą granicę należy obniżyć o ~10–20 % (np. 1500 → ~1250–1350). Wynika to z teorii (+4,7 dB) i z danych (P14 osiąga 20 dBA przy 1206 rpm, P12 przy 1559). Wyjątek: SW Pro 4 140 brzmi jak wersja 120 przy tych samych obrotach.

## (e) Zastrzeżenia

1. Specyfikacje producentów są zaniżone względem niezależnych pomiarów, nawet o +5,7 dB (SW Pro 4). Noctua G2 ma 22,5 dBA przy max, a HWB mierzy ~29 dBA (ekstrapolacja z 30 dBA @1820).
2. Dystans i tło decydują o wyniku: TPU fan 15 cm / 19 dBA, TPU GPU 50 cm, GN 1 m / 14 dBA, LanOC 46 cm / 33 dBA, THG 10 cm / 31 dBA. Liczb między serwisami nie porównujemy bez przeliczenia.
3. Odczyty TPU przy 750 rpm (~27 dBA) leżą tylko ~8 dB nad tłem 19 dBA, więc mogą być lekko zawyżone.
4. 50·log10 to średnia empiryczna. Przy niskich obrotach dominuje silnik i łożysko (szum nie spada tak szybko), więc estymaty dla 30 % i dla 800 rpm są niepewne (±3 dB).
5. dBA nie oddaje tonów ani rezonansów. CB pisze, że 41,5 dB(A) 5090 FE brzmi przyjemniej niż 40,5 dB(A) 4090 FE (rezonans tylnego wentylatora). Do tego dochodzi cewkowe piszczenie (coil whine) przy >200 FPS.
6. LanOC zmierzył max 2873 rpm, my 3030 rpm (rozrzut egzemplarzy albo VBIOS).
7. Nie dotarłem do pomiarów GN dla wentylatora 5090 FE przy stałym 100 % ani do pomiarów Igor's Lab i Hardwareluxx (strona 403). Krzywa % → dBA w tabeli (c) to model zakotwiczony w 2–3 punktach, a nie pomiar.
8. Najlepsza weryfikacja: nasz własny pomiar (iPhone + aplikacja dB, 0,5 m i 1 m, zapisane tło) dla 30/40/50/60/70/90 %.
