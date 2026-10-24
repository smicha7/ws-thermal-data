"""Writes the 'One temperature, many settings' subsection (Figure 20) from results-2026-10-23/iso-temp.json, between
<!--isotemp:start/end--> (first run: after <!--pmax:end-->), and copies figures + CSV to the site. Usage: iso_section.py <img ver>"""
import json, shutil, sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent)); from caseclass import label, NAME
from pathlib import Path
H = Path(__file__).resolve().parent.parent; SITE = Path.home() / "Claude/gruency-site"; F = SITE / "research/gpu-cooling-method.html"
V = sys.argv[1] if len(sys.argv) > 1 else "1"
J = json.load(open(H / "results-2026-10-23/iso-temp.json")); R = J["rows"]; B = J["best"]
for f in (H / "article_tools/out/iso").glob("*.webp"): shutil.copy(f, SITE / "research/img" / f.name)
shutil.copy(H / "results-2026-10-23/iso-temp.csv", SITE / "research/data/gpu-map-iso-temp.csv")
C = "&nbsp;&deg;C"; PL = [100, 90, 80, 70]; W = {r["pl"]: r["W"] for r in R}
cases = sorted({r["case_rpm"] for r in R}); cell = {(r["pl"], r["case_rpm"]): r for r in R}
mark = {"memory": "<sup>a</sup>", "floor": "<sup>b</sup>", "core": ""}
def td(pl, c):
    r = cell[(pl, c)]
    if r["gpu_pct"] is None: return '<td>&mdash;</td><td>&mdash;</td>'
    q = "<sup>c</sup>" if B[str(pl)]["case_rpm"] == c else ""
    return f'<td class="g">{r["gpu_pct"]}{mark[r["binding"]]}</td><td>{r["dBA"]:.1f}{q}</td>'
rowlab = lambda c: ("&asymp;2920 (full)" if c == 3000 else f"{c}") + f"</td><td class=tl>{NAME[c]}"
head = ('<tr><th scope="col" rowspan="2">Case and radiator fans, rpm</th><th scope="col" rowspan="2" class="tl">Listening class</th>' + "".join(f'<th scope="colgroup" colspan="2">{"Power limit " if pl == 100 else ""}{pl}&nbsp;% ({W[pl]}&nbsp;W)</th>' for pl in PL) + "</tr><tr>"
        + '<th scope="col" class="g">GPU fans needed, %</th><th scope="col">Total noise, dBA</th>' * len(PL) + "</tr>")
body = "".join(f'<tr><td>{rowlab(c)}</td>' + "".join(td(pl, c) for pl in PL) + "</tr>" for c in cases)
b = [B[str(p)] for p in PL]; d = [round(b[i]["dBA"] - b[i + 1]["dBA"], 1) for i in range(3)]
hi = max(r["dBA"] for r in R if r["case_rpm"] == cases[-1] and r["gpu_pct"])
mem80 = B["80"]; f70 = B["70"]
sec = f'''<!--isotemp:start-->
  <h3 id="iso-temp">One temperature, many settings: what it costs in noise</h3>
  <p>A user rarely asks for the quietest fans; more often the request is a temperature. Suppose it is a core at or below 70{C} with the memory at or below 80{C}. Many combinations of power limit, GPU fans and case and radiator fans meet it, and they differ in noise. For each power limit and each case and radiator speed we found, from equations (R1) and (R2) and intake air at {J["intake"]}{C}, the slowest GPU fan speed between 40 and 100&nbsp;% that holds both limits, and summed the literature-based levels of the card&rsquo;s fans and the seven case and radiator fans by equation (13).</p>
  <p class="ar-tcap"><b>How loud is it to keep the core at or below 70{C} (and the memory at or below 80{C})?</b> For each case-and-radiator fan speed (rows) and power limit (columns): the slowest GPU fan speed that meets both limits, and the resulting total noise. Model (11) and the memory model, intake air {J["intake"]}{C}, literature-based noise at 1&nbsp;m.</p>
  <div class="ar-tw ar-tw-wide"><table class="ar-tab ar-num ar-iso ar-ms"><thead>{head}</thead><tbody>{body}</tbody></table></div>
  <p class="ar-note">Rows: the case and radiator fan speeds of the final grid, chosen as our listening classes for this machine at the desk ({{tref:caseclass}}), backed by the literature <a class="cite" href="#n1">[N1]</a> <a class="cite" href="#n12">[N12]</a>. Total noise: all fans of the machine together, the card&rsquo;s and the seven case and radiator fans, by equation (13) provisional until our own sound map. <sup>a</sup> Here the memory limit, not the core, sets the GPU fan speed. <sup>b</sup> GPU fans already at their 40&nbsp;% minimum; the core ends below 70{C}. <sup>c</sup> The quietest setting at this power limit. <a href="/research/data/gpu-map-iso-temp.csv?v={V}">Data (CSV)</a>, with the level of each fan group, the settled core and the settled memory.</p>
  <p>At full power, 575&nbsp;W, the quietest way to 70{C} is GPU fans at {b[0]["gpu_pct"]}&nbsp;% with the case fans at {b[0]["case_rpm"]}&nbsp;rpm, {b[0]["dBA"]:.1f}&nbsp;dBA. At 518&nbsp;W it is {b[1]["gpu_pct"]}&nbsp;% and {b[1]["case_rpm"]}&nbsp;rpm, {b[1]["dBA"]:.1f}&nbsp;dBA. At 460&nbsp;W it is {mem80["gpu_pct"]}&nbsp;% and {mem80["case_rpm"]}&nbsp;rpm, {mem80["dBA"]:.1f}&nbsp;dBA, and here the memory, not the core, sets the fan speed: the core is at {mem80["core"]:.1f}{C} when the memory reaches 80{C}. At 402&nbsp;W the GPU fans sit on their 40&nbsp;% floor and the total is {f70["dBA"]:.1f}&nbsp;dBA with the case fans at {f70["case_rpm"]}&nbsp;rpm, but the core is then at {f70["core"]:.1f}{C}: the card is cooled more than asked, because the fans may go no slower.</p>
  <p>Two rules follow. First, case and radiator fans above about 1300&nbsp;rpm only add noise: they let the GPU fans slow by a few per cent, but their own level grows faster, and at full speed (about 2920&nbsp;rpm) every power limit costs about {hi:.1f}&nbsp;dBA. Second, at a fixed 70{C} each step of 10&nbsp;% in power limit buys {min(d):.1f} to {max(d):.1f}&nbsp;dB ({d[0]:.1f}, {d[1]:.1f} and {d[2]:.1f}&nbsp;dB for the three steps), less at the lower limits, where the floor of the GPU fans and the memory limit take over. Each step is a clearly audible difference, near 3&nbsp;dB (<a href="#noise-scale">How loud things sound</a>). These figures rest on the provisional memory model and on literature noise levels, and will be recomputed with each refit.</p>
  <figure class="ar-fig">
    <a class="ar-wide th-l" href="/research/img/gpu-map-iso-temp-light.webp?v={V}" aria-label="Open the chart at full size"><picture><source media="(max-width:620px)" srcset="/research/img/gpu-map-iso-temp-phone-light.webp?v={V}" width="1000" height="1120"><img src="/research/img/gpu-map-iso-temp-light.webp?v={V}" width="2600" height="1280" loading="lazy" decoding="async" alt="Total fan noise against case and radiator fan speed for power limits of 100, 90, 80 and 70 per cent, each point using the slowest GPU fan speed that keeps the core at or below 70 °C and the memory at or below 80 °C"></picture></a><a class="ar-wide th-d" href="/research/img/gpu-map-iso-temp-dark.webp?v={V}" aria-label="Open the chart at full size"><picture><source media="(max-width:620px)" srcset="/research/img/gpu-map-iso-temp-phone-dark.webp?v={V}" width="1000" height="1120"><img src="/research/img/gpu-map-iso-temp-dark.webp?v={V}" width="2600" height="1280" loading="lazy" decoding="async" alt="Total fan noise against case and radiator fan speed for power limits of 100, 90, 80 and 70 per cent, each point using the slowest GPU fan speed that keeps the core at or below 70 °C and the memory at or below 80 °C"></picture></a>
    <figcaption><b>Figure 20.</b> Total noise of all fans at 1&nbsp;m against the speed of the case and radiator fans in rpm (bottom) and % (top), one line per power limit; each point uses the slowest GPU fan speed that holds the core at or below 70{C} and the memory at or below 80{C}, with intake air at {J["intake"]}{C}. Diamonds: the quietest setting for each power limit. Models (11) and the memory model; literature-based noise, provisional.</figcaption>
  </figure>
<!--isotemp:end-->'''
s = F.read_text()
if "<!--isotemp:start-->" in s:
    a = s.index("<!--isotemp:start-->"); e = s.index("<!--isotemp:end-->") + len("<!--isotemp:end-->"); s = s[:a] + sec + s[e:]
else:
    assert s.count("<b>Figure 20.</b>") == 1 and "<b>Figure 21.</b>" not in s
    s = s.replace("<b>Figure 20.</b>", "<b>Figure 21.</b>")
    k = s.index("<!--pmax:end-->") + len("<!--pmax:end-->"); s = s[:k] + "\n" + sec + s[k:]
F.write_text(s); print("iso-temp written", d, hi)
