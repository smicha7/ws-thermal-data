# Hałas GPU RTX 50: % → rpm → dBA (research 2026-10-23)

Uzupełnia HALAS-PROGI-2026-10-23.md (skala SPCR, przeliczenia, dane GN/TPU/LanOC/THG dla 5090 FE są tam, tu ich nie powtarzam). Przeliczenie odległości: ×2 → −6 dB. Uwaga: TPU i Igor's Lab blokują boty (TPU ma bot-check), więc ich liczby pochodzą z podsumowań wyszukiwarki, a nie ze stron.

**Stanowiska pomiarowe (do czytania tabel):**
- CB: 30 cm, w obudowie Fractal Torrent, drzwi otwarte, wentylatory obudowy stoją ([CB 5080 custom](https://www.computerbase.de/artikel/grafikkarten/rtx-5080-asus-rog-astral-msi-suprim-zotac-amp-test.91179/seite-5)). Poprawka do HALAS-PROGI: dystans CB jest podany i wynosi 30 cm.
- PCGH: komora, 50 cm prostopadle do piasty, wynik w sone ([PCGH 5090](https://www.pcgameshardware.de/Geforce-RTX-5090-Grafikkarte-281029/Tests/Reviews-Benchmarks-Vergleich-RTX-4090-1463971/6/)).
- HWCooling: 35 cm od slotu PCIe, miernik Reed R8080 ([metodyka](https://www.hwcooling.net/en/gigabyte-rx-7900-gre-gaming-oc-16g-in-test-of-30-graphics-cards-review/5/)). Miernik nie mierzy poniżej ~30 dBA.
- LanOC: 46 cm, tło 33,3 dB.
- TPU: 50 cm.
- HWB: 1 m, komora, tło ~6 dBA ([metodyka HWB](https://hwbusters.com/chassis/xpg-invader-x-mini-review-noise-damping-output-evaluation/2/)).

## (a) Tabele per karta

**RTX 5090 FE: nowe punkty**

| % | rpm | Głośność | Źródło |
|---|---|---|---|
| 30 % (min.) | ~1200 (wg użytkownika) | „na granicy znośności” na otwartej ławie | [overclock.net](https://www.overclock.net/threads/official-nvidia-rtx-5090-owners-club.1814246/page-125) (anegdota, cytowane za podsumowaniem wyszukiwarki) |
| 40 % PWM | ~1440 | 2,3 sone, „przyjemnie”, sweet spot | [PCGH](https://www.pcgameshardware.de/Geforce-RTX-5090-Grafikkarte-281029/Tests/Reviews-Benchmarks-Vergleich-RTX-4090-1463971/6/) |
| 46 % (fabr., AIDA) | – | – | [LanOC](https://lanoc.org/review/video-cards/nvidia-rtx-5090-founders-edition?showall=1) |
| 52 % PWM (maks. w grze) | 1730 | „wysoka głośność”; typowo 2,0–2,5 sone | PCGH |
| – | 1750 (gra) | ~44 dBA @35 cm, „nieco powyżej średniej” | [HWCooling](https://www.hwcooling.net/en/nvidia-geforce-rtx-5090-fe-review-next-level-gaming/5/) |
| 60 % PWM | ~1920 | 4,2 sone (≈1,8× głośniej niż 40 %) | PCGH |
| 100 % | – | 9,5 sone (≈4× głośniej niż 40 %) | PCGH |

Bezczynność: fan-stop działa, ale w systemie testowym CB w jednym egzemplarzu nie zadziałał ([CB 5080/5090](https://www.computerbase.de/artikel/grafikkarten/nvidia-geforce-rtx-5080-test.91176/seite-9)). Na forum NVIDII użytkownicy piszą, że wentylatory co kilka minut wskakują na ~30 % przy przeglądaniu stron ([NVIDIA forum](https://www.nvidia.com/en-us/geforce/forums/geforce-graphics-cards/5/556735/5090-fe-fan-curve-starting-rpm-is-too-aggressive/), anegdota).

**RTX 5080 FE** (fan-stop: tak, wentylatory na pulpicie stoją od razu, [CB](https://www.computerbase.de/artikel/grafikkarten/nvidia-geforce-rtx-5080-test.91176/seite-9))

| Stan | rpm | dBA | Źródło (dystans) |
|---|---|---|---|
| fabr. 42 % (AIDA) | – | 39,7 | [LanOC](https://lanoc.org/review/video-cards/nvidia-rtx-5080-founders-edition?start=8) (46 cm) |
| 50 % | – | 41,4 | LanOC |
| 100 % | – | 57,0 | LanOC |
| gra | 1493 | 36,8 | TPU (50 cm), wg [wyszukiwarki](https://www.techpowerup.com/review/nvidia-geforce-rtx-5080-founders-edition/41.html) |
| gra | 1470–1500 | – | [GN](https://gamersnexus.net/gpus/nvidia-geforce-rtx-5080-founders-edition-review-benchmarks-vs-5090-7900-xtx-4080-more) |
| gra | 1620 | 41,0 (5090 FE: 41,5 @1700) | CB (30 cm) |
| gra maks. / 100 % | – | 2,9 / 9,2 sone | [PCGH](https://www.pcgameshardware.de/Geforce-RTX-5080-Grafikkarte-281030/Tests/Release-Preis-kaufen-Benchmark-Review-vs-4080-Super-1464610/6/) (50 cm) |

Maks. rpm: nie znalazłem (luka).

**RTX 5070 FE** (fan-stop w bezczynności: tak, TPU)

| Stan | rpm | dBA | Źródło |
|---|---|---|---|
| 50 % | – | 40,5 | [LanOC](https://lanoc.org/review/video-cards/nvidia-rtx-5070-founders-edition?start=8) (46 cm) |
| 100 % | 4351 | 57,5 | LanOC |
| fabr. (AIDA) | – | 40,9 | LanOC |
| gra | 2578 | 37,7 | [TPU](https://www.techpowerup.com/review/nvidia-geforce-rtx-5070-founders-edition/41.html) (50 cm, wg wyszukiwarki) |
| gra | do 2520 | 42,5 | [CB](https://www.computerbase.de/artikel/grafikkarten/nvidia-geforce-rtx-5070-test.91530/seite-7) (30 cm) |

Mniejsze wentylatory (wyższe rpm przy tym samym hałasie), więc rpm 5070 FE nie da się porównać z 5090 FE.

**RTX 5070 Ti** (nie ma wersji FE)

| Karta | rpm | dBA | Źródło |
|---|---|---|---|
| Galax 1-Click: 50 / 75 / 100 % | – | 24,2 / 38,5 / 48,1 | [HWB](https://hwbusters.com/gpu/galax-geforce-rtx-5070-ti-1-click-oc-performance-power-analysis-noise-output/21/) (1 m)* |
| ASUS TUF OC perf / quiet | 1413 / 1064 | 30,8 / 25,4 | [TPU](https://www.techpowerup.com/review/asus-geforce-rtx-5070-ti-tuf-oc/40.html) (wg wyszukiwarki) |
| TUF OC perf / quiet | 1550 / 1100 | 39 / 31 | [CB](https://www.computerbase.de/artikel/grafikkarten/nvidia-geforce-rtx-5070-ti-test.91379/seite-9) (30 cm) |
| MSI Gaming Trio OC+ | 1172 | 24,3 | [TPU](https://www.techpowerup.com/review/msi-geforce-rtx-5070-ti-gaming-trio-oc/) |
| Gaming Trio silent | 1422 | 31 | [HWCooling](https://www.hwcooling.net/en/msi-geforce-rtx-5070-ti-gaming-trio-oc-plus-review-for-picky-users/15/) (35 cm) |
| MSI Ventus 3X | 2480 | 45, „przerażająco głośno” | CB (30 cm) |

\*HWB podaje identyczne 24,2/38,5/48,1 dBA w recenzji Galax 5080 ([HWB](https://hwbusters.com/gpu/galax-geforce-rtx-5080-1-click-oc-performance-power-analysis-noise-output/21/)). Możliwe, że to kopia szablonu tekstu. Traktować ostrożnie.

**Partnerskie 5090 / 5080**

| Karta | Punkty % / rpm → dBA | Maks. | Źródło |
|---|---|---|---|
| MSI 5090 Suprim SOC | 30 % = 1000 rpm / 30; silent 1400–1500 / 36–38; gaming 1780–1850 / 42,1–43,4 | 3000 rpm / 58 | [HWCooling](https://www.hwcooling.net/en/msi-geforce-rtx-5090-suprim-soc-review-600w-with-ease/8/) (35 cm) |
| MSI 5090 Suprim SOC (TPU) | 1093 rpm / 28,4 | – | [TPU](https://www.techpowerup.com/review/msi-geforce-rtx-5090-suprim/39.html) (50 cm) |
| ASUS 5090 Astral | 1675 / 39,3; Quiet 1385 / 36,5 | – | [TPU](https://www.techpowerup.com/review/asus-geforce-rtx-5090-astral/39.html) |
| Gigabyte 5090 Gaming OC | 43,2; Quiet 32,4 (rpm brak) | – | [TPU](https://www.techpowerup.com/review/gigabyte-geforce-rtx-5090-gaming-oc/37.html) |
| Aorus 5090 Infinity | główne 1000–3000 rpm, środkowy do 4000 | – | [zod.kr](https://zod.kr/news/8156085) (dane producenta) |
| MSI 5080 Suprim SOC | 30 % = 1000 / 30,5; silent 1300–1400 / 35–36; gaming 1640 / 40 | 3000 / 59,3 | [HWCooling](https://www.hwcooling.net/en/msi-geforce-rtx-5080-suprim-soc-review-top-of-the-line/9/) |
| 5080 Astral / Suprim / FE | Quiet 36 (nowy BIOS 31), Perf 48 (4. wentylator ~2000 rpm) / silent 36, gaming 44 / FE 41 | – | [CB](https://www.computerbase.de/artikel/grafikkarten/rtx-5080-asus-rog-astral-msi-suprim-zotac-amp-test.91179/seite-5) (30 cm) |
| ASUS 5080 Noctua | 30–100 % = 530–1750 rpm = 29,1–46,8 | 1750 | [HWCooling](https://www.hwcooling.net/en/asus-geforce-rtx-5080-noctua-oc-ed-16gb-review-silent-monster/14/) |

Wszystkie wymienione karty partnerskie 5080 mają fan-stop (CB: 0,0 dB(A) na pulpicie). Windforce i Gaming Trio dla 5090/5080: brak danych (luka).

**Kluczowa obserwacja:** w tym samym stanowisku HWCooling 5090 FE przy 1750 rpm daje 44 dBA, a Suprim przy 1780–1850 rpm 42–43 dBA. Przy tych samych obrotach FE nie jest więc wyraźnie głośniejsza. Partnerskie karty są cichsze, bo przy tej samej mocy potrzebują mniej rpm. Słyszalność u Suprim zaczyna się od ~1400 rpm (HWCooling).

## (b) Skala klas dla 5090 FE (nasze mapowanie: 40 % = 1310, 100 % = 3030)

Model: dBA = 32,5 + 50·log10(rpm/1570), kotwica GN @1 m. Sprawdzenie z TPU @1 m (~34 przy 1673) i HWCooling @1 m (~35 przy 1750): zgodność ±2 dB. Na 100 % LanOC i HWCooling (Suprim) przeliczone na 1 m dają 49–52, model daje 47, więc górę traktować jako 47–52.

| Klasa | Wentylator % | rpm | dBA @1 m | @0,5 m |
|---|---|---|---|---|
| Ultra-cichy | fan-stop / ≤32 % | ≤~1080 | <24 | <30 |
| Bardzo cichy | 33–40 % | 1100–1310 | 24–29 | 30–35 |
| Cichy | 41–49 % | 1340–1570 | 29–32,5 | 35–38,5 |
| Zrównoważony | 50–60 % | 1600–1880 | 33–36,5 | 39–42,5 |
| Głośny | 61–80 % | 1910–2460 | 37–42 | 43–48 |
| Bardzo głośny | >80 % | >2460 | 42–52 | 48–58 |

Ocena percepcyjna według PCGH (sone są liniowe w odczuciu): 40 % → 60 % = 1,8× głośniej, 40 % → 100 % = 4×.

## (c) Czy „50 % cicho, 60 % na granicy” się trzyma?

**Prawie.** 50 % (~1600 rpm) to dokładnie fabryczny punkt pracy w grze (LanOC 46 %, PCGH maks. 52 % PWM / 1730 rpm). Recenzenci opisują go jako „dobrze słyszalny, akceptowalny dla graczy, nie do bardzo cichego PC” (CB) albo „już wysoka głośność” (PCGH). To raczej górna granica „cichego” niż cichy w sensie SPCR: ~33 dBA @1 m, ~39 dBA przy biurku.

60 % (~1880 rpm) to 4,2 sone. Wyraźnie słyszalne i głośniejsze niż fabryka (1,8× od 40 %). „Na granicy” się zgadza, jeśli rozumieć to jako granicę zrównoważony/głośny.

Dla stacji roboczej przy biurku (0,5 m) proponuję: **cicho ≤45 %, zrównoważony 45–55 %, od 60 % głośno.** Prawdziwie cicho (przyjemne 2,3 sone wg PCGH) jest przy ~40 %.

## (d) Zastrzeżenia

1. **% to nie rpm.** PCGH: 40 % PWM = 1440 rpm, nasze 40 % = 1310. Użytkownik na overclock.net podaje 30 % ≈ 1200, nasza ekstrapolacja daje ~1020. Procent w NVAPI/Afterburner, cykl PWM i obroty to trzy różne skale, a do tego dochodzi rozrzut egzemplarzy. Granice klas trzymać w **rpm**, nie w %.
2. Maks. 5090 FE: nasze 3030 rpm, LanOC 2873. Dla 5080 FE nie znalazłem żadnego źródła.
3. Strony TPU, Igor's Lab i Hardwareluxx zwróciły 403 albo bot-check. Liczby TPU pochodzą z podsumowań wyszukiwarki i zgadzają się z HALAS-PROGI, ale nie sprawdziłem ich na samej stronie. Pomiarów Igora w dB(A) (podobno ~38 dBA dla 5080 FE, bez dystansu) i krzywych % → dBA z wykresów (HWB, Guru3D, HWCooling) nie dało się odczytać, bo są tylko w obrazkach.
4. Sone → dBA nie przelicza się jednoznacznie. Wartości PCGH podaję tylko jako proporcje.
5. Ton: 5080 FE ma buczenie ~170–200 Hz ([THG](https://www.tomshardware.com/pc-components/gpus/asus-geforce-rtx-5080-noctua-edition-review/3), [Igor](https://www.igorslab.de/en/nvidia-geforce-rtx-5080-founders-edition-im-test-geforce-rtx-4080-ti-mit-blackwell-genen/12/)), 5070 FE pik ~300 Hz (Igor). Ton jest bardziej uciążliwy niż wynika z dBA. U 5090 FE CB słyszało cykanie elektroniki.
6. Anegdoty (oznaczone jako takie): na Hardwareluxx użytkownik karty partnerskiej pisze, że przy 44 % / 1000 rpm jest „flüsterleise” pod pełnym obciążeniem, a przy 600 W „hörbar ~1300 rpm” ([HWLuxx](https://www.hardwareluxx.de/community/threads/blackwell-rtx-5xxx-coilwhine-fiep-rassel-thread-here-we-go-again.1363471/page-5), z podsumowania wyszukiwarki). Użytkownik ASUS 5090 w komentarzu na HWB podaje 45 → 55–60 % pod dużym obciążeniem ([HWB](https://hwbusters.com/gpu/asus-tuf-gaming-geforce-rtx-5090-performance-power-analysis-noise-output/25/)). Reddit był niedostępny dla narzędzia.
7. Weryfikacja: własny pomiar iPhone 0,5 m i 1 m dla 30/40/45/50/55/60/70/100 % z zapisanym tłem. Zmierzyć też, przy jakim rpm 5090 FE wychodzi z fan-stopu.
