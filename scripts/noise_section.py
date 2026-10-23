"""Noise-thresholds section (<!--noise:start--> … <!--noise:end-->) before the controller section, from HALAS-PROGI-2026-10-23.md.
Also writes the tables as CSV files into the site's research/data/."""
import csv, math, os
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
 ("n23", "LanOC Reviews. NVIDIA RTX 5090 Founders Edition.", "https://lanoc.org/review/video-cards/nvidia-rtx-5090-founders-edition?showall=1"),
 ("n24", "Tom&rsquo;s Hardware. Nvidia GeForce RTX 5090 review, p.&nbsp;8.", "https://www.tomshardware.com/pc-components/gpus/nvidia-geforce-rtx-5090-review/8"),
]
N = {k: i + 1 for i, (k, _, _) in enumerate(SRC)}
c = lambda *ks: "".join(f'<a class="cite" href="#{k}">[N{N[k]}]</a>' for k in ks)
def tw(cls, head, rows):
    return ('  <div class="ar-tw">\n  <table class="ar-tab ar-num ' + cls + '"><thead><tr>' + "".join(f'<th scope="col">{h}</th>' for h in head) +
            "</tr></thead><tbody>" + "".join("<tr>" + "".join(f"<td>{x}</td>" for x in r) + "</tr>" for r in rows) + "</tbody></table>\n  </div>\n")
def wcsv(name, head, rows):
    import re
    clean = lambda x: re.sub(r"<[^>]+>", "", str(x)).replace("&nbsp;", " ").replace("&ndash;", "–").replace("&asymp;", "≈").replace("&lt;", "<").replace("&gt;", ">").replace("&deg;", "°").replace("&rsquo;", "’").replace("&mdash;", "—").replace("&times;", "×")
    with open(DATA + name, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow([clean(h) for h in head]); [w.writerow([clean(x) for x in r]) for r in rows]
# 1) perception
H1 = ["Class", "dBA at 1&nbsp;m", "Comparable to"]
R1 = [["Inaudible", "below 15", "&mdash;"], ["Barely audible", "15&ndash;20", "a computer without fans"], ["Very quiet", "20&ndash;25", "a quiet whisper"],
      ["Quiet", "25&ndash;30", "a bedroom at night"], ["Subdued", "35&ndash;45", "a typical computer; a quiet office or library"], ["Clearly audible", "about 50", "&mdash;"], ["Loud", "about 60", "&mdash;"]]
# 2) fans
H2 = ["Fan", "20&nbsp;dBA", "25&nbsp;dBA", "30&nbsp;dBA", "35&nbsp;dBA", "40&nbsp;dBA"]
R2 = [["Noctua NF-A12x25 G2", "1306", "1500", "1820", "&mdash;", "&mdash;"], ["Noctua NF-A12x25 G1", "1476", "1760", "2079", "&mdash;", "&mdash;"],
      ["be quiet! Silent Wings Pro 4 120", "1281", "1573", "1871", "2274", "2771"], ["be quiet! Silent Wings 4 120 high-speed", "1467", "1751", "2094", "&mdash;", "&mdash;"],
      ["Arctic P12 PWM PST", "1559", "1804", "&mdash;", "&mdash;", "&mdash;"], ["Arctic P14 PWM PST (140&nbsp;mm)", "1206", "1429", "1709", "&mdash;", "&mdash;"],
      ["be quiet! Silent Wings Pro 4 140 (140&nbsp;mm)", "1278", "1456", "1731", "&mdash;", "&mdash;"]]
H3 = ["Fan on a radiator", "750&nbsp;rpm", "1000&nbsp;rpm", "1250&nbsp;rpm", "1500&nbsp;rpm"]
R3 = [["Noctua NF-A12x25 G2", "27.4", "30.2", "33.8", "37.4"], ["Noctua NF-A12x25 G1", "27.2", "29.1", "32.8", "36.4"], ["be quiet! Silent Wings Pro 4 120", "27.2", "30.0", "32.8", "36.3"], ["Arctic P12 PWM PST", "27.3", "30.4", "33.4", "37.1"]]
# 3) RTX 5090 reviews
H4 = ["Source", "Distance, room floor", "Result"]
R4 = [[f"GamersNexus {c('n19')}", "1&nbsp;m; anechoic chamber, floor 14 to 14.5&nbsp;dBA; open bench", "32.5&nbsp;dBA at about 1570&nbsp;rpm, gaming"],
      [f"TechPowerUp {c('n20')}", "50&nbsp;cm; open bench", "40.1&nbsp;dBA at 1673&nbsp;rpm (RTX 4090 FE: 35.1&nbsp;dBA)"],
      [f"ComputerBase {c('n21')}", "distance not given; closed case, floor about 28&nbsp;dB(A)", "41.5&nbsp;dB(A) at 1700&nbsp;rpm (RTX 4090 FE: 40.5 at 1540)"],
      [f"PC Games Hardware {c('n22')}", "50&nbsp;cm", "2.8&nbsp;sone at 1620&nbsp;rpm"],
      [f"LanOC {c('n23')}", "46&nbsp;cm; floor 33.3&nbsp;dBA; class 2 meter", "50&nbsp;% fan: 45.7&nbsp;dBA; stock in a game (46&nbsp;%): 44.1; 100&nbsp;% (2873&nbsp;rpm): 58.4"],
      [f"Tom&rsquo;s Hardware {c('n24')}", "10&nbsp;cm; floor 31 to 32&nbsp;dB(A)", "50.0&nbsp;dB(A) in Cyberpunk 2077"]]
# 4) our estimate: anchor GN 32.5 dBA @1570 rpm @1 m; 50·log10 scaling; −6 dB per doubling of distance
L1 = lambda n: 32.5 + 50 * math.log10(n / 1570)
EST = [(30, 1020, "very quiet"), (40, 1310, "quiet"), (50, 1600, "acceptable; the factory curve in games sits at 46 to 54&nbsp;%"), (60, 1880, "loud, lower edge"), (70, 2170, "loud"), (90, 2740, "very loud"), (100, 3030, "very loud")]
H5 = ["GPU fans", "rpm", "dBA at 1&nbsp;m", "dBA at 0.5&nbsp;m", "Class"]
R5 = [[f"{p}&nbsp;%", f"{'~' if p in (30,50,60,70,90) else ''}{r}", f"~{L1(r):.0f}", f"~{L1(r)+6:.0f}", cl] for p, r, cl in EST]
# 5) Seb's scale
H6 = ["Speed, 120&nbsp;mm fan", "Sebastian&rsquo;s description", "Evidence: one fan, 1&nbsp;m, free field", "Verdict"]
R6 = [["800&nbsp;rpm", "inaudible", "NF-A12x25 G2 about 9&nbsp;dBA (extrapolated); about 27 to 28&nbsp;dBA at 15&nbsp;cm on a radiator at 750&nbsp;rpm", "agrees"],
      ["1000&nbsp;rpm", "almost silent", "G2 about 14, G1 about 12&nbsp;dBA", "agrees: below the floor of a room"],
      ["1200&nbsp;rpm", "gentle hum", "G2 about 18, Silent Wings Pro 4 about 19&nbsp;dBA", "agrees: audible only close by in a quiet room"],
      ["1500&nbsp;rpm", "noticeable, acceptable", "G2 25, Silent Wings Pro 4 about 24, G1 about 20&nbsp;dBA", "agrees: &ldquo;quiet&rdquo; to &ldquo;very quiet&rdquo; on the SilentPCReview scale"],
      ["above 1500&nbsp;rpm", "significant", "1800 to 2000&nbsp;rpm: 28 to 32&nbsp;dBA", "agrees for a whole computer; slightly strict for one fan"],
      ["2000&nbsp;rpm", "fairly loud", "G1 about 29, G2 and Silent Wings Pro 4 about 32&nbsp;dBA; six fans in a case about 40", "agrees in a real computer"],
      ["3000&nbsp;rpm", "very loud", "Silent Wings Pro 4: 42.6&nbsp;dBA at 1&nbsp;m", "agrees"]]
for nm, h, r in (("gpu-map-noise-perception.csv", H1, R1), ("gpu-map-noise-fans-hwb.csv", H2, R2), ("gpu-map-noise-fans-tpu.csv", H3, R3), ("gpu-map-noise-rtx5090-reviews.csv", H4, R4), ("gpu-map-noise-gpu-estimate.csv", H5, R5), ("gpu-map-noise-seb-scale.csv", H6, R6)):
    wcsv(nm, h, r)
case1 = lambda n: 20 + 50 * math.log10(n / 1281)   # SW Pro 4 120, one fan, 1 m (HWB anchor)
srcs = "".join(f'<li id="{k}"><span class="ar-tn">N{N[k]}.</span> {t} <a href="{u}">{u.split("/")[2].replace("www.", "")}</a></li>' for k, t, u in SRC)
D = lambda n: f'<a href="/research/data/{n}">CSV</a>'
sec = f"""<!--noise:start-->
  <h2 id="noise">How loud is loud: noise thresholds from the literature</h2>
  <p>The controller trades temperature against noise, so it needs to know what a fan speed sounds like. Until we have measured our own fans, we rely on published measurements, and only on those that state their distance and the noise floor of the room; a level without a distance is not a number one can use. Three rules of thumb connect them: the level falls by about 6&nbsp;dB for each doubling of distance in a free field; by the fan laws it changes by about 50&nbsp;log<sub>10</sub> of the speed ratio {c('n7')}; and at the same speed a 140&nbsp;mm fan is about 4.7&nbsp;dB louder than a 120&nbsp;mm one, which means the same level at about 20&nbsp;% lower speed.</p>
  <h3 id="noise-scale">How loud things sound</h3>
  <p>SilentPCReview&rsquo;s classes, measured at 1&nbsp;m, are the most widely used scale for computers {c('n1')}:</p>
{tw('ar-set', H1, R1)}  <p class="ar-note">{D('gpu-map-noise-perception.csv')}.</p>
  <p>A typical room is at 25 to 30&nbsp;dBA, a quiet room at night at about 20&nbsp;dBA, and a fan 5 to 10&nbsp;dB below that floor is practically inaudible. A level 10&nbsp;dB higher sounds about twice as loud; 3&nbsp;dB is a clearly audible difference and 1&nbsp;dB about the smallest one can hear {c('n1')}. Sources add on an energy basis: <i>n</i> identical fans are 10&nbsp;log<sub>10</sub>&nbsp;<i>n</i>&nbsp;dB louder than one, so two add 3&nbsp;dB, four 6&nbsp;dB and eight 9&nbsp;dB {c('n1')}. At 20&nbsp;dBA at 1&nbsp;m a computer is quieter than nearly all ready-made ones {c('n2')}. German magazines report loudness in sone, which is linear in perceived loudness; very roughly, 1&nbsp;sone at 50&nbsp;cm is about 35&nbsp;dBA at 1&nbsp;m {c('n3','n4')}.</p>
  <p>The standards say how to measure, not what is quiet. ECMA-74 and ISO&nbsp;7779 make the sound power level, in bels, the main quantity, with the pressure at an operator or bystander position as a supplement {c('n5')}. Noctua points out that a fan radiates like a dipole, so its level depends on the angle and on reflections, and different benches give conflicting results {c('n6')}.</p>
  <h3 id="noise-fans">120 and 140&nbsp;mm fans: speed against level</h3>
  <p>Hardware Busters measures fans in a semi-anechoic chamber with a floor of about 6&nbsp;dBA, at 1&nbsp;m, in free air, following ISO&nbsp;7779, and reports the speed at which each fan reaches a given level {c('n12')}. Our case fans are Silent Wings Pro 4 120.</p>
{tw('ar-st', ['Fan, rpm at'] + H2[1:], R2)}  <p class="ar-note">Sources: NF-A12x25 G1 and G2, Silent Wings 4 120 {c('n16')}; Silent Wings Pro 4 120 and Arctic P12 {c('n12')}; Arctic P14 and Silent Wings Pro 4 140 {c('n15')}. {D('gpu-map-noise-fans-hwb.csv')}.</p>
  <p>TechPowerUp measures fans mounted on a radiator with the microphone 15&nbsp;cm away, in a chamber with a floor of about 19&nbsp;dBA {c('n17','n18')}. These levels are in dBA at 15&nbsp;cm; moving to 1&nbsp;m subtracts roughly 16.5&nbsp;dB, an approximation in the near field. The premium fans differ by only about 1&nbsp;dB at equal speed, and the readings at 750&nbsp;rpm lie only 8&nbsp;dB above the floor, so they may read slightly high.</p>
{tw('ar-st', H3, R3)}  <p class="ar-note">{D('gpu-map-noise-fans-tpu.csv')}.</p>
  <p>Manufacturers&rsquo; figures read low. be quiet! lists the Silent Wings Pro 4 120 at 36.9&nbsp;dBA at full speed; Hardware Busters measured 42.6&nbsp;dBA at 1&nbsp;m, 5.7&nbsp;dB more {c('n12')}. Noctua lists the NF-A12x25 G2 at 22.5&nbsp;dBA at 1800&nbsp;rpm {c('n8')}, while the measurements above put it near 29&nbsp;dBA there. The other specifications we checked are of the same kind {c('n9','n10','n11','n13','n14')}; we do not use them.</p>
  <h3 id="noise-gpu">The RTX 5090 Founders Edition</h3>
{tw('ar-txt', H4, R4)}  <p class="ar-note">{D('gpu-map-noise-rtx5090-reviews.csv')}.</p>
  <p>The factory fan curve in games runs the card&rsquo;s fans at 1570 to 1700&nbsp;rpm, which by our mapping of fan duty to speed is about 49 to 54&nbsp;%. Reviewers call it audible, acceptable for gaming and not for a quiet computer {c('n21')}. ComputerBase also notes that the RTX 5090&rsquo;s 41.5&nbsp;dB(A) sounds more pleasant than the RTX 4090&rsquo;s 40.5, which has a resonance at its rear fan: dBA does not capture tones.</p>
  <p class="ar-status"><b>Estimate.</b> The next table is not a measurement. It takes our mapping of fan duty to speed (40&nbsp;% = 1310&nbsp;rpm, 100&nbsp;% = 3030&nbsp;rpm on this card), anchors the level at GamersNexus&rsquo;s 32.5&nbsp;dBA at 1570&nbsp;rpm and 1&nbsp;m, and scales it by 50&nbsp;log<sub>10</sub> of the speed. The anchors agree with each other: GamersNexus moved to 50&nbsp;cm gives 38.7&nbsp;dBA at 1570&nbsp;rpm, as does TechPowerUp scaled to the same speed. LanOC&rsquo;s step from 50 to 100&nbsp;%, +12.7&nbsp;dB, compares with +13.7&nbsp;dB from the model. We take the uncertainty as &plusmn;3&nbsp;dB, more at 30&nbsp;%, where motor and bearing noise stop falling with speed. Our own measurement, with a phone sound meter at 0.5 and 1&nbsp;m and the room floor recorded, at 30 to 90&nbsp;%, will replace it.</p>
{tw('ar-set', H5, R5)}  <p class="ar-note">Class after SilentPCReview at 1&nbsp;m; at a desk, 0.5 to 0.7&nbsp;m away, shift each boundary down one class. {D('gpu-map-noise-gpu-estimate.csv')}.</p>
  <h3 id="noise-seb">A practical scale</h3>
  <p>Sebastian Michalski, who builds and listens to these machines, describes 120&nbsp;mm fan speeds like this. We checked each step against the measurements above.</p>
{tw('ar-txt', H6, R6)}  <p class="ar-note">{D('gpu-map-noise-seb-scale.csv')}.</p>
  <p>The scale describes a whole computer at the desk well: several fans and radiators add 6 to 9&nbsp;dB to a single fan, and the listener sits 0.5 to 1&nbsp;m away. For one fan in a chamber it is about one class too strict. For 140&nbsp;mm fans each boundary moves down by about 10 to 20&nbsp;%, for example 1500 to about 1250 to 1350&nbsp;rpm, as both the 4.7&nbsp;dB rule and the data show: the Arctic P14 reaches 20&nbsp;dBA at 1206&nbsp;rpm, the P12 at 1559. The exception is the Silent Wings Pro 4 140, which sounds like the 120&nbsp;mm version at the same speed.</p>
  <h3 id="noise-ctl">What this means for the controller</h3>
  <p>The noise ceilings of the controller&rsquo;s modes are at present speeds. On the scales above they fall as follows.</p>
{tw('ar-txt', ['Mode', 'GPU fan ceiling', 'Estimated GPU fan level at 1&nbsp;m', 'Case fan ceiling', 'Case fans, four Silent Wings Pro 4 120, at 1&nbsp;m'],
   [["Quiet", "1800&nbsp;rpm (about 57&nbsp;%)", f"~{L1(1800):.0f}&nbsp;dBA: subdued, about 3&nbsp;dB above the factory curve in games", "1200&nbsp;rpm", f"~{case1(1200)+6:.0f}&nbsp;dBA (one fan ~{case1(1200):.0f}): a gentle hum"],
    ["Balanced", "2300&nbsp;rpm (about 75&nbsp;%)", f"~{L1(2300):.0f}&nbsp;dBA: loud", "1500&nbsp;rpm", f"~{case1(1500)+6:.0f}&nbsp;dBA (one fan ~{case1(1500):.0f}): noticeable, acceptable"],
    ["Performance", "100&nbsp;%", f"~{L1(3030):.0f}&nbsp;dBA: very loud", "full speed", f"~{case1(2920)+6:.0f}&nbsp;dBA: loud"]])}  <p>The graphics card, not the case, sets the noise of this machine: at every ceiling the card&rsquo;s fans are estimated to be louder than the four case fans together, by about 11&nbsp;dB in Quiet and Balanced and 3&nbsp;dB at full speed. Once our own measurements exist, the ceilings will be set in decibels instead of revolutions per minute, and the controller&rsquo;s noise proxy will become a measured map.</p>
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
