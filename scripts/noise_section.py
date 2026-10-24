"""Noise-thresholds section (<!--noise:start--> … <!--noise:end-->) before the controller section, from HALAS-PROGI-2026-10-23.md.
Also writes the tables as CSV files into the site's research/data/."""
import csv, math, os, re
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from caseclass import L7
F = "/Users/smicha/Claude/gruency-site/research/gpu-cooling-method.html"; DATA = "/Users/smicha/Claude/gruency-site/research/data/"
s = open(F).read()
SRC = [  # (id, text, url)
 ("n1", "SilentPCReview. A primer on noise in computing.", "https://silentpcreview.com/archive-a-primer-on-noise-in-computing/"),
 ("n2", "SilentPCReview. Six-HDD SFF server test results.", "https://silentpcreview.com/book/six-hdd-sff-server-test-results/"),
 ("n3", "heise / c&rsquo;t. L&auml;rm messen.", "https://www.heise.de/ratgeber/Laerm-messen-297358.html"),
 ("n4", "PC Games Hardware. Wissen: Ger&auml;usch-Messungen.", "https://www.pcgameshardware.de/Luftkuehlung-Hardware-217993/Specials/wissen-Geraeusch-Messungen-1280621/"),
 ("n5", "Ecma International. ECMA-74, Measurement of airborne noise emitted by information technology and telecommunications equipment.", "https://ecma-international.org/publications-and-standards/standards/ecma-74"),
 ("n6", "HWCooling. Noctua on measuring fan noise: different angles, different results.", "https://www.hwcooling.net/en/noctua-on-measuring-fan-noise-different-angles-different-results/2/"),
 ("n7", "Comair Rotron. Acoustic noise: causes, rating systems and design guidelines.", "https://comairrotron.com/article/acoustic-noise-causes-rating-systems-and-design-guidelines.html"),
 ("n8", "Noctua. NF-A12x25 G2 PWM specifications.", "https://www.noctua.at/en/products/nf-a12x25-g2-pwm/specifications"),
 ("n9", "Noctua. NF-A12x25 G2 LS-PWM specifications.", "https://www.noctua.at/en/products/nf-a12x25-g2-ls-pwm/specifications"),
 ("n10", "Noctua. NF-A12x25 PWM specifications.", "https://www.noctua.at/en/products/nf-a12x25-pwm/specifications"),
 ("n11", "Noctua. NF-A14 PWM specifications.", "https://noctua.at/en/nf-a14-pwm/specification"),
 ("n12", "Hardware Busters. be quiet! Silent Wings Pro 4 120&nbsp;mm fan review (methodology p.&nbsp;6, results p.&nbsp;10&ndash;11).", "https://hwbusters.com/cooling/be-quiet-silent-wings-pro-4-120mm-fan-review/"),
 ("n13", "Aqua Computer shop. be quiet! Silent Wings Pro 4 140&nbsp;mm PWM.", "https://shop.aquacomputer.de/Fans-Accessories/Fans/140-mm/be-quiet-Silent-Wings-Pro-4-140-mm-PWM::4198.html"),
 ("n14", "Hardware Busters. be quiet! Silent Wings 4 140&nbsp;mm PWM fan review.", "https://hwbusters.com/cooling/be-quiet-silent-wings-4-140mm-pwm-fan-review/"),
 ("n15", "Hardware Busters. Arctic P14 PWM PST 140&nbsp;mm fan review.", "https://hwbusters.com/cooling/arctic-p14-pwm-pst-140mm-fan-review/"),
 ("n16", "Hardware Busters. Noctua NF-A12x25 G2 LS-PWM 120&nbsp;mm fan review, p.&nbsp;8.", "https://hwbusters.com/cooling/noctua-nf-a12x25-g2-ls-pwm-120mm-fan-review-money-for-nothing/8/"),
 ("n17", "TechPowerUp. Fan test methodology (Darkside Gentle Typhoon review, p.&nbsp;4).", "https://www.techpowerup.com/reviews/Darkside/Gentle_Typhoon_1450_Black_Edition/4.html"),
 ("n18", "TechPowerUp. Noctua NF-A12x25 G2 PWM fan review, p.&nbsp;4.", "https://www.techpowerup.com/review/noctua-nf-a12x25-g2-pwm-fan/4.html"),
 ("n19", "GamersNexus. NVIDIA GeForce RTX 5090 Founders Edition review.", "https://gamersnexus.net/gpus/nvidia-geforce-rtx-5090-founders-edition-review-benchmarks-gaming-thermals-power"),
 ("n20", "TechPowerUp. NVIDIA GeForce RTX 5090 Founders Edition review, p.&nbsp;41.", "https://www.techpowerup.com/review/nvidia-geforce-rtx-5090-founders-edition/41.html"),
 ("n21", "ComputerBase. Nvidia GeForce RTX 5090 im Test, p.&nbsp;10.", "https://www.computerbase.de/artikel/grafikkarten/nvidia-geforce-rtx-5090-test.91081/seite-10"),
 ("n22", "PC Games Hardware. Geforce RTX 5090 review, p.&nbsp;6.", "https://www.pcgameshardware.de/Geforce-RTX-5090-Grafikkarte-281029/Tests/Reviews-Benchmarks-Vergleich-RTX-4090-1463971/6/"),
 ("n56", "AVADirect. SilverStone Hailstone 360 (SST-HT360), 360&nbsp;mm radiator liquid cooling system: specifications.", "https://www.avadirect.com/Hailstone-360-360mm-Radiator-Liquid-Cooling-System/Product/20149898"),
 ("n57", "P. Moosdorf. SilverStone Hailstone 360 im Test. Hardwareluxx, 28 June 2026.", "https://www.hardwareluxx.de/index.php/artikel/hardware/kuehlung/69437-silverstone-hailstone-360-im-test-industrie-l%C3%BCfter,-threadr%C3%ADpper-eignung-und-vrm-l%C3%BCfteroption.html"),
 ("n23", "LanOC Reviews. NVIDIA RTX 5090 Founders Edition.", "https://lanoc.org/review/video-cards/nvidia-rtx-5090-founders-edition?showall=1"),
 ("n24", "Tom&rsquo;s Hardware. Nvidia GeForce RTX 5090 review, p.&nbsp;8.", "https://www.tomshardware.com/pc-components/gpus/nvidia-geforce-rtx-5090-review/8"),
 ("n25", "ComputerBase. RTX 5080: ASUS ROG Astral, MSI Suprim and Zotac AMP in test, p.&nbsp;5 (test set-up: 30&nbsp;cm).", "https://www.computerbase.de/artikel/grafikkarten/rtx-5080-asus-rog-astral-msi-suprim-zotac-amp-test.91179/seite-5"),
 ("n26", "HWCooling. Test methodology (Gigabyte RX 7900 GRE Gaming OC in a test of 30 graphics cards, p.&nbsp;5).", "https://www.hwcooling.net/en/gigabyte-rx-7900-gre-gaming-oc-16g-in-test-of-30-graphics-cards-review/5/"),
 ("n27", "Hardware Busters. Noise methodology (XPG Invader X Mini review, p.&nbsp;2).", "https://hwbusters.com/chassis/xpg-invader-x-mini-review-noise-damping-output-evaluation/2/"),
 ("n28", "overclock.net. Official NVIDIA RTX 5090 owner&rsquo;s club, p.&nbsp;125 (user report).", "https://www.overclock.net/threads/official-nvidia-rtx-5090-owners-club.1814246/page-125"),
 ("n29", "HWCooling. Nvidia GeForce RTX 5090 FE review, p.&nbsp;5.", "https://www.hwcooling.net/en/nvidia-geforce-rtx-5090-fe-review-next-level-gaming/5/"),
 ("n30", "ComputerBase. Nvidia GeForce RTX 5080 im Test, p.&nbsp;9.", "https://www.computerbase.de/artikel/grafikkarten/nvidia-geforce-rtx-5080-test.91176/seite-9"),
 ("n31", "NVIDIA forums. 5090 FE fan curve starting rpm is too aggressive (user reports).", "https://www.nvidia.com/en-us/geforce/forums/geforce-graphics-cards/5/556735/5090-fe-fan-curve-starting-rpm-is-too-aggressive/"),
 ("n32", "LanOC Reviews. NVIDIA RTX 5080 Founders Edition.", "https://lanoc.org/review/video-cards/nvidia-rtx-5080-founders-edition?start=8"),
 ("n33", "TechPowerUp. NVIDIA GeForce RTX 5080 Founders Edition review, p.&nbsp;41.", "https://www.techpowerup.com/review/nvidia-geforce-rtx-5080-founders-edition/41.html"),
 ("n34", "GamersNexus. NVIDIA GeForce RTX 5080 Founders Edition review.", "https://gamersnexus.net/gpus/nvidia-geforce-rtx-5080-founders-edition-review-benchmarks-vs-5090-7900-xtx-4080-more"),
 ("n35", "PC Games Hardware. Geforce RTX 5080 review, p.&nbsp;6.", "https://www.pcgameshardware.de/Geforce-RTX-5080-Grafikkarte-281030/Tests/Release-Preis-kaufen-Benchmark-Review-vs-4080-Super-1464610/6/"),
 ("n36", "LanOC Reviews. NVIDIA RTX 5070 Founders Edition.", "https://lanoc.org/review/video-cards/nvidia-rtx-5070-founders-edition?start=8"),
 ("n37", "TechPowerUp. NVIDIA GeForce RTX 5070 Founders Edition review, p.&nbsp;41.", "https://www.techpowerup.com/review/nvidia-geforce-rtx-5070-founders-edition/41.html"),
 ("n38", "ComputerBase. Nvidia GeForce RTX 5070 im Test, p.&nbsp;7.", "https://www.computerbase.de/artikel/grafikkarten/nvidia-geforce-rtx-5070-test.91530/seite-7"),
 ("n39", "Hardware Busters. Galax GeForce RTX 5070 Ti 1-Click OC review, p.&nbsp;21.", "https://hwbusters.com/gpu/galax-geforce-rtx-5070-ti-1-click-oc-performance-power-analysis-noise-output/21/"),
 ("n40", "TechPowerUp. ASUS GeForce RTX 5070 Ti TUF OC review, p.&nbsp;40.", "https://www.techpowerup.com/review/asus-geforce-rtx-5070-ti-tuf-oc/40.html"),
 ("n41", "ComputerBase. Nvidia GeForce RTX 5070 Ti im Test, p.&nbsp;9.", "https://www.computerbase.de/artikel/grafikkarten/nvidia-geforce-rtx-5070-ti-test.91379/seite-9"),
 ("n42", "TechPowerUp. MSI GeForce RTX 5070 Ti Gaming Trio OC review.", "https://www.techpowerup.com/review/msi-geforce-rtx-5070-ti-gaming-trio-oc/"),
 ("n43", "HWCooling. MSI GeForce RTX 5070 Ti Gaming Trio OC+ review, p.&nbsp;15.", "https://www.hwcooling.net/en/msi-geforce-rtx-5070-ti-gaming-trio-oc-plus-review-for-picky-users/15/"),
 ("n44", "Hardware Busters. Galax GeForce RTX 5080 1-Click OC review, p.&nbsp;21.", "https://hwbusters.com/gpu/galax-geforce-rtx-5080-1-click-oc-performance-power-analysis-noise-output/21/"),
 ("n45", "HWCooling. MSI GeForce RTX 5090 Suprim SOC review, p.&nbsp;8.", "https://www.hwcooling.net/en/msi-geforce-rtx-5090-suprim-soc-review-600w-with-ease/8/"),
 ("n46", "TechPowerUp. MSI GeForce RTX 5090 Suprim review, p.&nbsp;39.", "https://www.techpowerup.com/review/msi-geforce-rtx-5090-suprim/39.html"),
 ("n47", "TechPowerUp. ASUS GeForce RTX 5090 Astral review, p.&nbsp;39.", "https://www.techpowerup.com/review/asus-geforce-rtx-5090-astral/39.html"),
 ("n48", "TechPowerUp. Gigabyte GeForce RTX 5090 Gaming OC review, p.&nbsp;37.", "https://www.techpowerup.com/review/gigabyte-geforce-rtx-5090-gaming-oc/37.html"),
 ("n49", "zod.kr. Aorus RTX 5090 Infinity (manufacturer data).", "https://zod.kr/news/8156085"),
 ("n50", "HWCooling. MSI GeForce RTX 5080 Suprim SOC review, p.&nbsp;9.", "https://www.hwcooling.net/en/msi-geforce-rtx-5080-suprim-soc-review-top-of-the-line/9/"),
 ("n51", "HWCooling. ASUS GeForce RTX 5080 Noctua OC Edition review, p.&nbsp;14.", "https://www.hwcooling.net/en/asus-geforce-rtx-5080-noctua-oc-ed-16gb-review-silent-monster/14/"),
 ("n52", "Tom&rsquo;s Hardware. ASUS GeForce RTX 5080 Noctua Edition review, p.&nbsp;3.", "https://www.tomshardware.com/pc-components/gpus/asus-geforce-rtx-5080-noctua-edition-review/3"),
 ("n53", "Igor&rsquo;s Lab. Nvidia GeForce RTX 5080 Founders Edition im Test, p.&nbsp;12.", "https://www.igorslab.de/en/nvidia-geforce-rtx-5080-founders-edition-im-test-geforce-rtx-4080-ti-mit-blackwell-genen/12/"),
 ("n54", "Hardwareluxx forum. Blackwell RTX 5xxx coil whine thread, p.&nbsp;5 (user reports).", "https://www.hardwareluxx.de/community/threads/blackwell-rtx-5xxx-coilwhine-fiep-rassel-thread-here-we-go-again.1363471/page-5"),
 ("n55", "Hardware Busters. ASUS TUF Gaming GeForce RTX 5090 review, p.&nbsp;25 (reader comment).", "https://hwbusters.com/gpu/asus-tuf-gaming-geforce-rtx-5090-performance-power-analysis-noise-output/25/"),
]
N = {k: i + 1 for i, (k, _, _) in enumerate(SRC)}
c = lambda *ks: "".join(f'<a class="cite" href="#{k}">[N{N[k]}]</a>' for k in ks)
def tw(cls, head, rows, top=None):
    if top:   # [(label, span)]: span 1 = column spanning both header rows
        i, h2 = 0, []
        th = ""
        for lab, sp in top:
            if sp == 1: th += f'<th scope="col" rowspan="2">{lab}</th>'
            else: th += f'<th scope="colgroup" colspan="{sp}">{lab}</th>'; h2 += head[i:i + sp]
            i += sp
        hh = "<tr>" + th + "</tr><tr>" + "".join(f'<th scope="col">{h}</th>' for h in h2) + "</tr>"
    else: hh = "<tr>" + "".join(f'<th scope="col">{h}</th>' for h in head) + "</tr>"
    return ('  <div class="ar-tw' + (' ar-tw-wide' if 'ar-rev' in cls else '') + '">\n  <table class="ar-tab ar-num ' + cls + '"><thead>' + hh +
            "</thead><tbody>" + "".join("<tr>" + "".join(f"<td>{x}</td>" for x in r) + "</tr>" for r in rows) + "</tbody></table>\n  </div>\n")
def wcsv(name, head, rows):
    import re
    clean = lambda x: re.sub(r"<[^>]+>", "", str(x)).replace("&nbsp;", " ").replace("&ndash;", "–").replace("&asymp;", "≈").replace("&lt;", "<").replace("&gt;", ">").replace("&deg;", "°").replace("&rsquo;", "’").replace("&mdash;", "—").replace("&times;", "×")
    with open(DATA + name, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow([clean(h) for h in head]); [w.writerow([clean(x) for x in r]) for r in rows]
# 1) perception
H1 = ["Class (SilentPCReview)", "from", "to", "Comparable to"]
R1 = [["Inaudible", "&mdash;", "15", "&mdash;"], ["Barely audible", "15", "20", "a computer without fans"], ["Very quiet", "20", "25", "a quiet whisper"],
      ["Quiet", "25", "30", "a bedroom at night"], ["(no class named)<sup>a</sup>", "30", "35", "&mdash;"], ["Subdued", "35", "45", "a typical computer; a quiet office or library"], ["Clearly audible<sup>b</sup>", "&mdash;", "50", "&mdash;"], ["Loud<sup>b</sup>", "&mdash;", "60", "&mdash;"]]
T1 = [("Class (SilentPCReview)", 1), ("Level at 1&nbsp;m, dBA", 2), ("Comparable to", 1)]
# 2) fans
H2 = ["Fan", "20&nbsp;dBA", "25&nbsp;dBA", "30&nbsp;dBA", "35&nbsp;dBA", "40&nbsp;dBA"]
R2 = [["Noctua NF-A12x25 G2", "1306", "1500", "1820", "&mdash;", "&mdash;"], ["Noctua NF-A12x25 G1", "1476", "1760", "2079", "&mdash;", "&mdash;"],
      ["be quiet! Silent Wings Pro 4 120", "1281", "1573", "1871", "2274", "2771"], ["be quiet! Silent Wings 4 120 high-speed", "1467", "1751", "2094", "&mdash;", "&mdash;"],
      ["Arctic P12 PWM PST", "1559", "1804", "&mdash;", "&mdash;", "&mdash;"], ["Arctic P14 PWM PST (140&nbsp;mm)", "1206", "1429", "1709", "&mdash;", "&mdash;"],
      ["be quiet! Silent Wings Pro 4 140 (140&nbsp;mm)", "1278", "1456", "1731", "&mdash;", "&mdash;"]]
H3 = ["Fan on a radiator", "750&nbsp;rpm", "1000&nbsp;rpm", "1250&nbsp;rpm", "1500&nbsp;rpm"]
T3 = [("Fan on a radiator", 1), ("Level at 15&nbsp;cm, dBA, at fan speed", 4)]
R3 = [["Noctua NF-A12x25 G2", "27.4", "30.2", "33.8", "37.4"], ["Noctua NF-A12x25 G1", "27.2", "29.1", "32.8", "36.4"], ["be quiet! Silent Wings Pro 4 120", "27.2", "30.0", "32.8", "36.3"], ["Arctic P12 PWM PST", "27.3", "30.4", "33.4", "37.1"]]
# 3) RTX 5090 reviews
H4 = ["Source", "Distance, cm", "Set-up and room floor", "Setting", "Fan speed, rpm", "Level"]
R4 = [[f"GamersNexus {c('n19')}", "100", "anechoic chamber, floor 14 to 14.5&nbsp;dBA; open bench", "gaming", "1570", "32.5&nbsp;dBA"],
      [f"TechPowerUp {c('n20')}", "50", "open bench", "gaming", "1673", "40.1&nbsp;dBA"],
      [f"TechPowerUp {c('n20')}", "50", "open bench", "RTX 4090 FE, gaming", "&mdash;", "35.1&nbsp;dBA"],
      [f"ComputerBase {c('n21','n25')}", "30", "closed Fractal Torrent case, door open, case fans stopped; floor about 28&nbsp;dBA", "gaming", "1700", "41.5&nbsp;dBA"],
      [f"ComputerBase {c('n21','n25')}", "30", "as above", "RTX 4090 FE, gaming", "1540", "40.5&nbsp;dBA"],
      [f"PC Games Hardware {c('n22')}", "50", "chamber", "gaming", "1620", "2.8&nbsp;sone"],
      [f"LanOC {c('n23')}", "46", "floor 33.3&nbsp;dBA; class 2 meter", "fans at 50&nbsp;%", "&mdash;", "45.7&nbsp;dBA"],
      [f"LanOC {c('n23')}", "46", "as above", "stock, in a game (46&nbsp;%)", "&mdash;", "44.1&nbsp;dBA"],
      [f"LanOC {c('n23')}", "46", "as above", "fans at 100&nbsp;%", "2873", "58.5&nbsp;dBA"],
      [f"Tom&rsquo;s Hardware {c('n24')}", "10", "floor 31 to 32&nbsp;dBA", "Cyberpunk 2077", "&mdash;", "50.0&nbsp;dBA"]]
# 4) our estimate: anchor GN 32.5 dBA @1570 rpm @1 m; 50·log10 scaling; −6 dB per doubling of distance
L1 = lambda n: 32.5 + 50 * math.log10(n / 1570)
EST = [(30, 1020, "ultra-quiet"), (40, 1310, "very quiet"), (50, 1600, "balanced<sup>a</sup>"), (60, 1880, "balanced"), (70, 2160, "loud"), (80, 2450, "loud"), (90, 2730, "very loud"), (100, 3010, "very loud")]
H5 = ["GPU fans, %", "GPU fans, rpm", "Estimated level at 1&nbsp;m, dBA", "Estimated level at 0.5&nbsp;m, dBA", "Class on our RTX 5090 scale"]
R5 = [[f"{p}", f"{r}", f"{L1(r):.0f}", f"{L1(r)+6:.0f}", cl] for p, r, cl in EST]
# 5) Seb's scale
H6 = ["Speed of a 120&nbsp;mm fan, rpm", "Listening description (author)", "Published evidence", "Verdict"]
R6 = [["800", "inaudible", "NF-A12x25 G2 about 9&nbsp;dBA (extrapolated); about 27 to 28&nbsp;dBA at 15&nbsp;cm on a radiator at 750&nbsp;rpm", "agrees"],
      ["1000", "almost silent", "G2 about 14, G1 about 12&nbsp;dBA", "agrees: below the floor of a room"],
      ["1200", "gentle hum", "G2 about 18, Silent Wings Pro 4 about 19&nbsp;dBA", "agrees: audible only close by in a quiet room"],
      ["1500", "noticeable, acceptable", "G2 25, Silent Wings Pro 4 about 24, G1 about 20&nbsp;dBA", "agrees: &ldquo;quiet&rdquo; to &ldquo;very quiet&rdquo; on the SilentPCReview scale"],
      ["1800", "significant", "1800 to 2000&nbsp;rpm: 28 to 32&nbsp;dBA", "agrees for a whole computer; slightly strict for one fan"],
      ["2000", "fairly loud", "G1 about 29, G2 and Silent Wings Pro 4 about 32&nbsp;dBA; six fans in a case about 40", "agrees in a real computer"],
      ["3000", "very loud", "Silent Wings Pro 4: 42.6&nbsp;dBA at 1&nbsp;m", "agrees"]]
for nm, h, r in (("gpu-map-noise-perception.csv", H1, R1), ("gpu-map-noise-fans-hwb.csv", H2, R2), ("gpu-map-noise-fans-tpu.csv", H3, R3), ("gpu-map-noise-rtx5090-reviews.csv", H4, R4), ("gpu-map-noise-gpu-estimate.csv", H5, R5), ("gpu-map-noise-seb-scale.csv", H6, R6)):
    wcsv(nm, h, r)
case1 = lambda n: 20 + 50 * math.log10(n / 1281)   # SW Pro 4 120, one fan, 1 m (HWB anchor)

D = lambda n: f'<a href="/research/data/{n}">CSV</a>'
T = lambda k: f"{c(k)}<sup>a</sup>"
HC = ["Class", "from", "to", "from", "to", "from", "to", "from", "to"]
RC = [["Ultra-quiet<sup>a</sup>", "0", "32", "0", "1080", "&mdash;", "24", "&mdash;", "30"], ["Very quiet", "33", "40", "1100", "1310", "24", "29", "30", "35"],
      ["Quiet", "41", "49", "1340", "1570", "29", "33", "35", "39"], ["Balanced", "50", "60", "1600", "1880", "33", "37", "39", "43"],
      ["Loud", "61", "80", "1910", "2460", "37", "42", "43", "48"], ["Very loud<sup>b</sup>", "81", "100", "2490", "3010", "42", "52", "48", "58"]]
TC = [("Class", 1), ("GPU fans, %", 2), ("GPU fans, rpm", 2), ("Level at 1&nbsp;m, dBA", 2), ("Level at 0.5&nbsp;m, dBA", 2)]
HO = ["Card", "Setting", "Fan speed, rpm", "Level, dBA", "Distance, cm", "Source"]
_o = [
 ("RTX 5080 FE", "games", "1493", "36.8", "50", T('n33')), ("RTX 5080 FE", "games", "1470&ndash;1500", "&mdash;", "&mdash;", c('n34')),
 ("RTX 5080 FE", "games", "1620", "41.0", "30", c('n30')), ("RTX 5080 FE", "factory curve (42&nbsp;%)", "&mdash;", "39.7", "46", c('n32')),
 ("RTX 5080 FE", "fans at 50&nbsp;%", "&mdash;", "41.4", "46", c('n32')), ("RTX 5080 FE", "fans at 100&nbsp;%", "&mdash;", "57.0", "46", c('n32')),
 ("RTX 5080 FE", "fan stop at idle", "0", "&mdash;", "&mdash;", c('n30')),
 ("RTX 5070 FE<sup>c</sup>", "games", "2578", "37.7", "50", T('n37')), ("RTX 5070 FE<sup>c</sup>", "games", "2520", "42.5", "30", c('n38')),
 ("RTX 5070 FE<sup>c</sup>", "fans at 50&nbsp;%", "&mdash;", "40.5", "46", c('n36')), ("RTX 5070 FE<sup>c</sup>", "factory curve", "&mdash;", "40.9", "46", c('n36')),
 ("RTX 5070 FE<sup>c</sup>", "highest speed", "4351", "57.5", "46", c('n36')),
 ("RTX 5070 Ti, ASUS TUF OC", "performance BIOS", "1413", "30.8", "50", T('n40')), ("RTX 5070 Ti, ASUS TUF OC", "quiet BIOS", "1064", "25.4", "50", T('n40')),
 ("RTX 5070 Ti, ASUS TUF OC", "performance BIOS", "1550", "39", "30", c('n41')), ("RTX 5070 Ti, ASUS TUF OC", "quiet BIOS", "1100", "31", "30", c('n41')),
 ("RTX 5070 Ti, MSI Gaming Trio OC+", "default", "1172", "24.3", "50", T('n42')), ("RTX 5070 Ti, MSI Gaming Trio OC+", "silent BIOS", "1422", "31", "35", c('n43')),
 ("RTX 5070 Ti, MSI Ventus 3X", "games", "2480", "45", "30", c('n41')),
 ("RTX 5070 Ti, Galax 1-Click<sup>d</sup>", "fans at 50&nbsp;%", "&mdash;", "24.2", "100", c('n39')), ("RTX 5070 Ti, Galax 1-Click<sup>d</sup>", "fans at 75&nbsp;%", "&mdash;", "38.5", "100", c('n39')),
 ("RTX 5070 Ti, Galax 1-Click<sup>d</sup>", "fans at 100&nbsp;%", "&mdash;", "48.1", "100", c('n39')),
 ("RTX 5090, MSI Suprim SOC", "fans at 30&nbsp;%", "1000", "30", "35", c('n45')), ("RTX 5090, MSI Suprim SOC", "silent BIOS", "1400&ndash;1500", "36&ndash;38", "35", c('n45')),
 ("RTX 5090, MSI Suprim SOC", "gaming BIOS", "1780&ndash;1850", "42.1&ndash;43.4", "35", c('n45')), ("RTX 5090, MSI Suprim SOC", "default", "1093", "28.4", "50", c('n46')),
 ("RTX 5090, MSI Suprim SOC", "highest speed", "3000", "58", "35", c('n45')),
 ("RTX 5090, ASUS Astral", "default", "1675", "39.3", "50", T('n47')), ("RTX 5090, ASUS Astral", "quiet BIOS", "1385", "36.5", "50", T('n47')),
 ("RTX 5090, Gigabyte Gaming OC", "default", "&mdash;", "43.2", "50", T('n48')), ("RTX 5090, Gigabyte Gaming OC", "quiet BIOS", "&mdash;", "32.4", "50", T('n48')),
 ("RTX 5090, Aorus Infinity", "outer fans, lowest (manufacturer)", "1000", "&mdash;", "&mdash;", c('n49')), ("RTX 5090, Aorus Infinity", "outer fans, highest (manufacturer)", "3000", "&mdash;", "&mdash;", c('n49')), ("RTX 5090, Aorus Infinity", "centre fan, highest", "4000", "&mdash;", "&mdash;", c('n49')),
 ("RTX 5080, MSI Suprim SOC", "fans at 30&nbsp;%", "1000", "30.5", "35", c('n50')), ("RTX 5080, MSI Suprim SOC", "silent BIOS", "1300&ndash;1400", "35&ndash;36", "35", c('n50')),
 ("RTX 5080, MSI Suprim SOC", "gaming BIOS", "1640", "40", "35", c('n50')), ("RTX 5080, MSI Suprim SOC", "highest speed", "3000", "59.3", "35", c('n50')),
 ("RTX 5080, MSI Suprim SOC", "fan stop at idle", "0", "&mdash;", "&mdash;", c('n25')),
 ("RTX 5080, ASUS Astral", "quiet BIOS", "&mdash;", "36", "30", c('n25')), ("RTX 5080, ASUS Astral", "quiet BIOS, newer version", "&mdash;", "31", "30", c('n25')),
 ("RTX 5080, ASUS Astral", "performance BIOS", "&mdash;", "48", "30", c('n25')), ("RTX 5080, MSI Suprim", "silent BIOS", "&mdash;", "36", "30", c('n25')),
 ("RTX 5080, MSI Suprim", "gaming BIOS", "&mdash;", "44", "30", c('n25')), ("RTX 5080 FE", "default", "&mdash;", "41", "30", c('n25')),
 ("RTX 5080, ASUS Noctua", "fans at 30&nbsp;%", "530", "29.1", "&mdash;", c('n51')), ("RTX 5080, ASUS Noctua", "fans at 100&nbsp;%", "1750", "46.8", "&mdash;", c('n51')),
]
def _mid(x):
    m = re.match(r"^([\d.]+)&ndash;([\d.]+)$", x)
    if not m: return x
    a, b = float(m.group(1)), float(m.group(2)); d = max(len(m.group(1).split(".")[1]) if "." in m.group(1) else 0, 0)
    return f"{(a + b) / 2:.{d}f}<sup>b</sup>"
RO = [[r[0], r[1], _mid(r[2]), _mid(r[3]), r[4], r[5]] for r in _o]
RO_CSV = [list(r) for r in _o]
wcsv("gpu-map-noise-rtx5090-classes.csv", HC, RC); wcsv("gpu-map-noise-rtx50-cards.csv", HO, RO_CSV)
rtx50 = f"""  <h3 id="noise-rtx50">The RTX 5090 more closely, and other RTX 50 cards</h3>
  <p>The reviews differ in how they measure, so each figure needs its set-up: ComputerBase at 30&nbsp;cm in a closed case with the door open and the case fans stopped {c('n25')}; PC Games Hardware in a chamber at 50&nbsp;cm, perpendicular to the fan hub, in sone {c('n22')}; HWCooling at 35&nbsp;cm from the PCIe slot, with a meter that reads nothing below about 30&nbsp;dBA {c('n26')}; LanOC at 46&nbsp;cm with a floor of 33.3&nbsp;dBA; TechPowerUp at 50&nbsp;cm; Hardware Busters at 1&nbsp;m in a chamber with a floor of about 6&nbsp;dBA {c('n27')}.</p>
  <p>At the same speed the Founders Edition is not louder than a large partner card. On HWCooling&rsquo;s bench it read 44&nbsp;dBA at 35&nbsp;cm at 1750&nbsp;rpm in games {c('n29')}, and MSI&rsquo;s RTX 5090 Suprim SOC 42.1 to 43.4&nbsp;dBA at 1780 to 1850&nbsp;rpm {c('n45')}. Partner cards are quieter because they need fewer revolutions for the same power; the Suprim becomes audible from about 1400&nbsp;rpm {c('n45')}.</p>
  <p class="ar-status"><b>Estimate.</b> A class scale for the RTX 5090 Founders Edition, from the same model as the estimate above. It agrees with TechPowerUp and HWCooling scaled to 1&nbsp;m within about 2&nbsp;dB (about 34&nbsp;dBA at 1673&nbsp;rpm and 35 at 1750). At 100&nbsp;% LanOC and HWCooling scaled to 1&nbsp;m give 49 to 52&nbsp;dBA against the model&rsquo;s 47, so the top of the scale spans 47 to 52.</p>
{tw('ar-st', HC, RC, TC)}  <p class="ar-note">Our class scale for the RTX 5090 Founders Edition fans, used throughout the article; band edges rounded to 1&nbsp;dB, so neighbouring classes meet. <sup>a</sup> Includes fan stop at idle. <sup>b</sup> The model gives 47&nbsp;dBA at 100&nbsp;%; reviews scaled to 1&nbsp;m give 49 to 52&nbsp;dBA. {D('gpu-map-noise-rtx5090-classes.csv')}.</p>
  <p>For a workstation at a desk, 0.5&nbsp;m from the listener, this suggests: quiet up to 45&nbsp;%, balanced from 45 to 55&nbsp;%, loud from 60&nbsp;%, and truly quiet near 40&nbsp;%, the 2.3&nbsp;sone that PC Games Hardware found pleasant {c('n22')}. The class limits belong in revolutions per minute, not in percent: duty in the driver or Afterburner, the PWM duty cycle and the speed are three different scales, and cards differ. Our 40&nbsp;% is 1310&nbsp;rpm, PC Games Hardware&rsquo;s 40&nbsp;% PWM is 1440&nbsp;rpm {c('n22')}, and an owner reports 30&nbsp;% as about 1200&nbsp;rpm {c('n28')} where we extrapolate about 1020.</p>
{tw('ar-txt ar-rev', HO, RO)}  <p class="ar-note">One row per published measurement. &mdash;: not given. PC Games Hardware gives 2.9&nbsp;sone in games for the RTX 5080 FE {c('n35')}; sone, a unit of perceived loudness, does not convert uniquely to dBA. <sup>a</sup> TechPowerUp&rsquo;s pages could not be opened directly; these figures come from search-engine summaries, agree with the rest, but were not checked on the page. <sup>b</sup> The source gives a range; the cell shows its midpoint, the range is in the CSV. <sup>c</sup> Smaller fans: its rpm is not comparable with the RTX 5090&rsquo;s. <sup>d</sup> Hardware Busters gives exactly the same three levels in its review of the Galax RTX 5080 {c('n44')}, possibly a copied template; treat with caution. {D('gpu-map-noise-rtx50-cards.csv')}.</p>
  <p>Gaps and caveats. We found no highest fan speed for the RTX 5080 FE; for the 5090 FE we measure 3030&nbsp;rpm and LanOC 2873 {c('n23')}. Igor&rsquo;s Lab and Hardwareluxx were not accessible to our tools, and several curves from Hardware Busters, Guru3D and HWCooling exist only as images we could not read. Sone do not convert uniquely to dBA, so the PC Games Hardware values are used only as ratios. dBA misses tones: the RTX 5080 FE hums at about 170 to 200&nbsp;Hz {c('n52','n53')}, and ComputerBase heard the electronics of a 5090 FE tick {c('n21')}. In one ComputerBase sample the fan stop did not engage {c('n30')}, and owners report the 5090 FE spinning up to about 30&nbsp;% every few minutes while browsing {c('n31')}. Other owner reports are anecdotes: a partner card &ldquo;whisper quiet&rdquo; at 44&nbsp;% and 1000&nbsp;rpm under full load and audible at about 1300&nbsp;rpm at 600&nbsp;W {c('n54')}, and an ASUS card moving from 45 to 55&ndash;60&nbsp;% under heavy load {c('n55')}. Our own measurement at 30, 40, 45, 50, 55, 60, 70 and 100&nbsp;%, and of the speed at which the card leaves its fan stop, will settle these.</p>
"""
srcs = "".join(f'<li id="{k}"><span class="ar-tn">N{N[k]}.</span> {t} <a href="{u}">{u.split("/")[2].replace("www.", "")}</a></li>' for k, t, u in SRC)
D = lambda n: f'<a href="/research/data/{n}">CSV</a>'
sec = f"""<!--noise:start-->
  <h2 id="noise">How loud is loud: noise thresholds from the literature</h2>
  <p>The controller trades temperature against noise, so it needs to know what a fan speed sounds like. Until we have measured our own fans, we rely on published measurements, and only on those that state their distance and the noise floor of the room; a level without a distance is not a number one can use. Three rules of thumb connect them: the level falls by about 6&nbsp;dB for each doubling of distance in a free field; by the fan laws it changes by about 50&nbsp;log<sub>10</sub> of the speed ratio {c('n7')}; and at the same speed a 140&nbsp;mm fan is about 4.7&nbsp;dB louder than a 120&nbsp;mm one, which means the same level at about 20&nbsp;% lower speed.</p>
  <h3 id="noise-scale">How loud things sound</h3>
  <p>SilentPCReview&rsquo;s classes, measured at 1&nbsp;m, are the most widely used scale for computers {c('n1')}:</p>
{tw('ar-set', H1, R1, T1)}  <p class="ar-note">&mdash;: no lower bound or no comparison given. <sup>a</sup> The scale as we transcribed it from the source names no class between 30 and 35&nbsp;dBA; the source page could not be reopened today to check. <sup>b</sup> The source gives a single level, not a band; 45 to 50 and 50 to 60&nbsp;dBA are not named. {D('gpu-map-noise-perception.csv')}.</p>
  <p>A typical room is at 25 to 30&nbsp;dBA, a quiet room at night at about 20&nbsp;dBA, and a fan 5 to 10&nbsp;dB below that floor is practically inaudible. A level 10&nbsp;dB higher sounds about twice as loud; 3&nbsp;dB is a clearly audible difference and 1&nbsp;dB about the smallest one can hear {c('n1')}. Sources add on an energy basis: <i>n</i> identical fans are 10&nbsp;log<sub>10</sub>&nbsp;<i>n</i>&nbsp;dB louder than one, so two add 3&nbsp;dB, four 6&nbsp;dB and eight 9&nbsp;dB {c('n1')}. At 20&nbsp;dBA at 1&nbsp;m a computer is quieter than nearly all ready-made ones {c('n2')}. German magazines report loudness in sone, which is linear in perceived loudness; very roughly, 1&nbsp;sone at 50&nbsp;cm is about 35&nbsp;dBA at 1&nbsp;m {c('n3','n4')}.</p>
  <p>The standards say how to measure, not what is quiet. ECMA-74 and ISO&nbsp;7779 make the sound power level, in bels, the main quantity, with the pressure at an operator or bystander position as a supplement {c('n5')}. Noctua points out that a fan radiates like a dipole, so its level depends on the angle and on reflections, and different benches give conflicting results {c('n6')}.</p>
  <h3 id="noise-fans">120 and 140&nbsp;mm fans: speed against level</h3>
  <p>Hardware Busters measures fans in a semi-anechoic chamber with a floor of about 6&nbsp;dBA, at 1&nbsp;m, in free air, following ISO&nbsp;7779, and reports the speed at which each fan reaches a given level {c('n12')}. Our four case fans are Silent Wings Pro 4 120.</p>
{tw('ar-st', H2, R2, [("Fan", 1), ("Speed at which the fan reaches the level at 1&nbsp;m, rpm", 5)])}  <p class="ar-note">Sources: NF-A12x25 G1 and G2, Silent Wings 4 120 {c('n16')}; Silent Wings Pro 4 120 and Arctic P12 {c('n12')}; Arctic P14 and Silent Wings Pro 4 140 {c('n15')}. {D('gpu-map-noise-fans-hwb.csv')}.</p>
  <p>TechPowerUp measures fans mounted on a radiator with the microphone 15&nbsp;cm away, in a chamber with a floor of about 19&nbsp;dBA {c('n17','n18')}. These levels are in dBA at 15&nbsp;cm; moving to 1&nbsp;m subtracts roughly 16.5&nbsp;dB, an approximation in the near field. The premium fans differ by only about 1&nbsp;dB at equal speed, and the readings at 750&nbsp;rpm lie only 8&nbsp;dB above the floor, so they may read slightly high.</p>
{tw('ar-st', H3, R3, T3)}  <p class="ar-note">{D('gpu-map-noise-fans-tpu.csv')}.</p>
  <p>Manufacturers&rsquo; figures read low. be quiet! lists the Silent Wings Pro 4 120 at 36.9&nbsp;dBA at full speed; Hardware Busters measured 42.6&nbsp;dBA at 1&nbsp;m, 5.7&nbsp;dB more {c('n12')}. Noctua lists the NF-A12x25 G2 at 22.5&nbsp;dBA at 1800&nbsp;rpm {c('n8')}, while the measurements above put it near 29&nbsp;dBA there. The other specifications we checked are of the same kind {c('n9','n10','n11','n13','n14')}; we do not use them.</p>
  <p class="ar-status"><b>Assumption, provisional.</b> The three radiator fans are the stock fans of the SilverStone Hailstone 360, on their own fan-controller output. SilverStone rates them at 800 to 3000&nbsp;rpm and 39.6&nbsp;dBA {c('n56')}. We found no free-field measurement of them: the one review that measured the cooler did so at 20&nbsp;cm from an open case, three fans and the pump together, 54.4&nbsp;dBA at full speed and 30.9&nbsp;dBA at 1000&nbsp;rpm, the latter at the level its other coolers bottom out at {c('n57')}; these cannot be converted to 1&nbsp;m. Since the fans are of similar construction to the Silent Wings Pro 4 120, we use the case-fan line for them as well, evaluated at their measured speed, which on this machine never falls below 888&nbsp;rpm or rises above 2745&nbsp;rpm. Applying the rating with the 5.7&nbsp;dB by which the Silent Wings Pro 4 rating reads low would put one SilverStone fan at 45.3&nbsp;dBA at 3000&nbsp;rpm, 3&nbsp;dB above the line; the radiator level may therefore be underestimated near full speed.</p>
  <h3 id="noise-gpu">The RTX 5090 Founders Edition</h3>
{tw('ar-txt ar-rev', H4, R4)}  <p class="ar-note">One row per published measurement. Sone: a unit of perceived loudness that does not convert uniquely to dBA. Class 2 meter: a sound level meter of the lower accuracy class of IEC 61672. &mdash;: not given. {D('gpu-map-noise-rtx5090-reviews.csv')}.</p>
  <p>In games the factory fan curve runs the card&rsquo;s fans at 46 to 52&nbsp;%, about 1600 to 1730&nbsp;rpm: LanOC read 46&nbsp;% {c('n23')}, PC Games Hardware a maximum of 52&nbsp;% PWM at 1730&nbsp;rpm {c('n22')}. Reviewers call it clearly audible, acceptable for gaming and not for a very quiet computer {c('n21')}, or &ldquo;already a high level&rdquo; {c('n22')}. PC Games Hardware measured 2.3&nbsp;sone at 40&nbsp;% PWM (about 1440&nbsp;rpm on their card) and called it pleasant, the sweet spot; 4.2&nbsp;sone at 60&nbsp;%, about 1.8 times as loud; and 9.5&nbsp;sone at 100&nbsp;%, about four times as loud {c('n22')}. ComputerBase also notes that the RTX 5090&rsquo;s 41.5&nbsp;dBA sounds more pleasant than the RTX 4090&rsquo;s 40.5, which has a resonance at its rear fan: dBA does not capture tones.</p>
  <p class="ar-status"><b>Estimate.</b> The next table is not a measurement. It takes our mapping of fan duty to speed (40&nbsp;% = 1310&nbsp;rpm, 100&nbsp;% = 3030&nbsp;rpm on this card), anchors the level at GamersNexus&rsquo;s 32.5&nbsp;dBA at 1570&nbsp;rpm and 1&nbsp;m, and scales it by 50&nbsp;log<sub>10</sub> of the speed. The anchors agree with each other: GamersNexus moved to 50&nbsp;cm gives 38.7&nbsp;dBA at 1570&nbsp;rpm, as does TechPowerUp scaled to the same speed. LanOC&rsquo;s step from 50 to 100&nbsp;%, +12.7&nbsp;dB, compares with +13.7&nbsp;dB from the model. We take the uncertainty as &plusmn;3&nbsp;dB, more at 30&nbsp;%, where motor and bearing noise stop falling with speed. Our own measurement, with a phone sound meter at 0.5 and 1&nbsp;m and the room floor recorded, at 30 to 90&nbsp;%, will replace it.</p>
{tw('ar-set', H5, R5)}  <p class="ar-note">Nominal fan speeds; class on our RTX 5090 scale ({{tref:gpuclassrange}}). <sup>a</sup> The factory fan curve sits at 46 to 52&nbsp;% in games. At a desk, 0.5 to 0.7&nbsp;m away, shift each boundary down one class. {D('gpu-map-noise-gpu-estimate.csv')}.</p>
{rtx50}  <h3 id="noise-seb">A practical scale</h3>
  <p>The author&rsquo;s listening scale for 120&nbsp;mm fan speeds is as follows. We checked each step against the measurements above.</p>
{tw('ar-txt ar-wrap', H6, R6)}  <p class="ar-note">Levels in dBA at 1&nbsp;m, free field, unless stated. {D('gpu-map-noise-seb-scale.csv')}.</p>
  <p>The scale describes a whole computer at the desk well: several fans and radiators add 6 to 9&nbsp;dB to a single fan, and the listener sits 0.5 to 1&nbsp;m away. For one fan in a chamber it is about one class too strict. For 140&nbsp;mm fans each boundary moves down by about 10 to 20&nbsp;%, for example 1500 to about 1250 to 1350&nbsp;rpm, as both the 4.7&nbsp;dB rule and the data show: the Arctic P14 reaches 20&nbsp;dBA at 1206&nbsp;rpm, the P12 at 1559. The exception is the Silent Wings Pro 4 140, which sounds like the 120&nbsp;mm version at the same speed.</p>
  <h3 id="noise-ctl">What this means for the controller</h3>
  <p>The current modes are defined directly by a noise budget, 30, 35 and 40&nbsp;dBA at 1&nbsp;m (<a href="#controller-modes">How it decides</a>). The first version set its ceilings as fan speeds; on the scales above they fall as follows.</p>
{tw('ar-st', ['Mode', 'rpm', '%', 'level at 1&nbsp;m, dBA', 'class', 'rpm', 'level of 4 case + 3 radiator fans at 1&nbsp;m, dBA', 'class'],
   [["Quiet", "1800", "57", f"{L1(1800):.0f}", "balanced", "1200", f"{L7(1200):.0f}", "quiet<sup>a</sup>"],
    ["Balanced", "2300", "75", f"{L1(2300):.0f}", "loud", "1500", f"{L7(1500):.0f}", "balanced<sup>a</sup>"],
    ["Performance", "3010", "100", f"{L1(3010):.0f}", "very loud", "&asymp;2920 (full)", f"{L7(2920):.0f}", "very loud"]],
   [("Mode (first version)", 1), ("GPU fan ceiling", 4), ("Case and radiator fan ceiling", 3)])}  <p class="ar-note">Estimated levels at 1&nbsp;m from the literature-based models; GPU-fan classes on our RTX 5090 scale ({{tref:gpuclassrange}}), case-fan classes on the listening scale of the final grid ({{tref:caseclass}}). <sup>a</sup> Between two classes of that scale; the nearer one is given.</p>
  <p>The graphics card, not the case, sets the noise of this machine at the Quiet and Balanced ceilings: there the card&rsquo;s fans are estimated {L1(1800)-L7(1200):.0f} and {L1(2300)-L7(1500):.0f}&nbsp;dB louder than the seven case and radiator fans together. At full speed the seven fans are {"louder, by " + format(L7(2920)-L1(3010), ".0f") + "&nbsp;dB" if L7(2920) > L1(3010) + 1 else "about as loud"}. Once our own measurements exist, the controller&rsquo;s literature-based noise estimate will become a measured map.</p>
  <ol class="ar-src ar-src-t">{srcs}</ol>
<!--noise:end-->"""
a, b = s.find("<!--noise:start-->"), s.find("<!--noise:end-->")
if a < 0:
    i = s.index('  <h2 id="controller">'); s = s[:i] + sec + "\n\n" + s[i:]
    s = s.replace('<li><a href="#controller">From model to controller</a></li>', '<li><a href="#noise">How loud is loud</a></li>\n      <li><a href="#controller">From model to controller</a></li>', 1)
else:
    s = s[:a] + sec + s[b + len("<!--noise:end-->"):]
if ".ar-txt{" not in s:
    s = s.replace(".ar-r2 sup{", ".ar-txt{font-size:14px}.ar-txt td,.ar-txt th{white-space:normal;text-align:start!important;vertical-align:top;min-width:7em}.ar-txt td:first-child{min-width:6em}\n@media (max-width:620px){.ar-txt{font-size:12.5px}.ar-txt thead{display:table-header-group}.ar-txt tr{display:table-row}.ar-txt td{display:table-cell;padding:8px 6px;border-top:1px solid var(--ring-l)}.ar-txt td:nth-child(3){grid-column:auto;font-size:inherit;color:inherit}.ar-txt td,.ar-txt th{min-width:5.5em}}\n.ar-r2 sup{", 1)
open(F, "w").write(s); print("noise section written", round(L1(1800), 1), round(L1(2300), 1), round(case1(1200), 1), round(case1(1500), 1), round(case1(2920), 1))
