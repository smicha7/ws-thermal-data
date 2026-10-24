"""Two-card study (steady4, in progress): methods subsection under 2.4 (with Figure 'two-card set-up' via setup_fig.py),
the settling-time analysis of steady3 in Section 4 (justifies the shorter protocol), and live data tables in Section 3 from
data/steady4-*/grid.csv (empty until the file exists). Markers: s4method, settle, s4tables. Usage: s4_section.py"""
import csv, glob, json, re
from pathlib import Path
import numpy as np, pandas as pd
G = Path(__file__).resolve().parent.parent; F = Path.home() / "Claude/gruency-site/research/gpu-cooling-method.html"; SITE = F.parent
CARDS = [40, 50, 60, 70, 80, 90, 100]; CASES = [800, 1000, 1300, 1600, 1900, 2400, 3000]; PLS = [100, 90, 80, 70]
PLW = {100: 575, 90: 518, 80: 460, 70: 402}
HOLD = {40: 5, 50: 5, 60: 4}; hold = lambda g: HOLD.get(g, 3)   # Lab steady4 holds                       # minutes, from the settling analysis below
def put(s, name, html, before=None, after=None):
    a, b = s.find(f"<!--{name}:start-->"), s.find(f"<!--{name}:end-->")
    blk = f"<!--{name}:start-->\n{html}\n<!--{name}:end-->"
    if a >= 0: return s[:a] + blk + s[b + len(f"<!--{name}:end-->"):]
    i = s.index(before) if before else s.index(after) + len(after)
    return s[:i] + blk + "\n" + s[i:]
# ---- settling analysis (steady3, same sensor as the settled value)
g3 = pd.read_csv(sorted(glob.glob(str(G / "data/steady3-*/grid.csv")))[-1]); d = g3.iloc[1:-1]
d = d[d.settled == 1].drop_duplicates(["pl_pct", "gpu_pct", "case_rpm_target"], keep="last")
MINS = [1, 2, 3, 5]
def p95(col, ref, sel=None):
    x = d if sel is None else d[sel]; e = (x[col] - x[ref]).abs().dropna(); return float(e.quantile(0.95))
rows = ""
for gp in CARDS + ["all"]:
    sel = None if gp == "all" else d.gpu_pct == gp
    c = [p95(f"core_nvapi_{m}min", "cardA_core_nvapi_c", sel) for m in MINS]; mm = [p95(f"mem_{m}min", "mem_c_max", sel) for m in (3, 5)]
    lab = "all speeds" if gp == "all" else f"{gp}&nbsp;%"
    rows += (f'<tr><td>{lab}</td><td class="g">{c[0]:.2f}</td><td>{c[1]:.2f}</td><td>{c[2]:.2f}</td><td>{c[3]:.2f}</td><td class="g">{mm[0]:.2f}</td><td>{mm[1]:.2f}</td>'
             f'<td class="g">{"&mdash;" if gp == "all" else hold(gp)}</td></tr>')
S = {gp: p95("core_nvapi_3min", "cardA_core_nvapi_c", d.gpu_pct == gp) for gp in CARDS}
S5 = {gp: p95("core_nvapi_5min", "cardA_core_nvapi_c", d.gpu_pct == gp) for gp in CARDS}
nvml3 = p95("core_3min", "cardA_core_nvapi_c")
SET = f"""  <h3 id="settle">Settling time on the final grid</h3>
  <p>Every point of the final grid was held for at least five minutes (eight at GPU fans 40&nbsp;%), and the Lab recorded the core and memory after 1, 2, 3 and 5 minutes. Comparing these early readings with the settled value of the same point shows how long a point really needs ({{tref:settle3}}). For the core, read on the same 0.01&nbsp;&deg;C sensor as the settled value, the 95th percentile of the error after 3 minutes is {S[40]:.2f}&nbsp;&deg;C at GPU fans 40&nbsp;%, {S[50]:.2f} at 50&nbsp;% and {S[60]:.2f} at 60&nbsp;%, and at most {max(S[g] for g in CARDS if g >= 70):.2f}&nbsp;&deg;C from 70&nbsp;% up; after 5 minutes it is {S5[40]:.2f}&nbsp;&deg;C at 40&nbsp;% and at most {max(S5[g] for g in CARDS if g >= 50):.2f}&nbsp;&deg;C elsewhere. The slow GPU fans need the longest because the card&rsquo;s time constant grows as its airflow falls. The memory, read in whole degrees, needs 5 minutes at every speed. Mixing sensors inflates the error: the 1&nbsp;&deg;C NVML core after 3 minutes against the NVAPI settled value gives a 95th percentile of {nvml3:.2f}&nbsp;&deg;C overall, so early and settled readings must come from the same sensor.</p>
  <p class="ar-tcap"><b>How far an early reading lies from the settled value on the final grid, by GPU fan speed: 95th percentile of the absolute error, and the hold time chosen for the two-card grid.</b> {len(d)} settled points of steady3; core from the NVAPI sensor (0.01&nbsp;&deg;C), memory in whole degrees.</p>
  <div class="ar-tw">
  <table class="ar-tab ar-num ar-st ar-ms ar-settle">
    <thead><tr><th scope="col" rowspan="2">GPU fans</th><th scope="colgroup" colspan="4">Core: error after, &deg;C</th><th scope="colgroup" colspan="2">Memory: error after, &deg;C</th><th scope="col" rowspan="2" class="g">Hold, steady4, min</th></tr>
    <tr><th scope="col" class="g">1&nbsp;min</th><th scope="col">2&nbsp;min</th><th scope="col">3&nbsp;min</th><th scope="col">5&nbsp;min</th><th scope="col" class="g">3&nbsp;min</th><th scope="col">5&nbsp;min</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  </div>
  <p class="ar-note">Error = |reading after the given time &minus; settled value| of the same point. The hold is a minimum: a point ends only when the core and memory of both cards have also stopped rising (<a href="#steady4-method">Section 2.4.2</a>). <a href="/research/data/gpu-map-steady3-cells.csv">Data (CSV)</a>; early readings in the steady3 grid file of the repository.</p>"""
# ---- PCIe links and the first two-card stress test (spot values until the data folders arrive)
PC = sorted(glob.glob(str(G / "data/pcie-*")))
PR = []   # rows of the link check (SUMMARY.md table): card, link, H→D alone, D→H alone, H→D both, D→H both, replays, Δ, WHEA
if PC and (Path(PC[-1]) / "SUMMARY.md").exists():
    for l in open(Path(PC[-1]) / "SUMMARY.md"):
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        if len(c) == 9 and re.match(r"^[AB] \(bus", c[0]): PR.append(c)
num = lambda x: float(re.sub(r"[^\d.]", "", x))
if PR:
    al = num(PR[0][2]); both = [num(r[4]) + num(r[5]) for r in PR]; tot = sum(num(r[4]) for r in PR) + sum(num(r[5]) for r in PR)
    pcrows = "".join(f'<tr><td>{r[0][0]}</td><td>{"PCIE1" if r[0][0] == "A" else "PCIE2"}</td><td class="tl">{r[1].replace(" (max x16)", "")}</td><td class="g">{num(r[2]):.1f}</td><td>{num(r[3]):.1f}</td><td class="g">{num(r[4]):.1f}</td><td>{num(r[5]):.1f}</td><td class="g">{r[6]}</td><td>{r[7]}</td><td>{r[8]}</td></tr>' for r in PR)
    aggr = sum(num(r[4]) for r in PR)
    pc_txt = (f'A copy test settles it ({{tref:pcie}}): 1&nbsp;GiB copies between system memory and each card&rsquo;s memory, 10 repetitions per direction, each card alone and then both at once, in two full runs with identical results. '
              f'Alone, each card moves {al:.1f}&nbsp;GB/s from host to device and {num(PR[0][3]):.1f}&nbsp;GB/s back, {al / 31.5 * 100:.0f}&nbsp;% of the 31.5&nbsp;GB/s a Gen5 x8 link carries in theory and {al / 15.8:.1f} times the 15.8&nbsp;GB/s ceiling of Gen4 x8, so the links really run at Gen5. '
              f'With both cards copying at once each gets {num(PR[0][4]):.1f} and {num(PR[0][5]):.1f}&nbsp;GB/s, {aggr:.0f}&nbsp;GB/s together from host to device; the drop of about {(1 - num(PR[0][4]) / al) * 100:.0f}&nbsp;% is set by the processor&rsquo;s input-output die, not by the links. '
              f'The replay counters stood at {PR[0][6]} and {PR[1][6]} since the driver started and did not move during the tests, and the system logged no hardware error (WHEA) in seven days. One repetition on card B, at 17.1&nbsp;GB/s, is an outlier; every other lay within &plusmn;0.3&nbsp;%. Both links therefore run stably at Gen5 x8.')
    PTAB = f"""
  <p class="ar-tcap"><b>PCIe link check of the two cards: negotiated link, copy bandwidth with each card alone and both at once, and link errors.</b> 1&nbsp;GiB copies (D3D11), 10 repetitions per direction, two runs with identical results, 24 October 2026; GB/s = 10<sup>9</sup>&nbsp;bytes/s.</p>
  <div class="ar-tw ar-tw-wide">
  <table class="ar-tab ar-num ar-st ar-ms ar-pcie">
    <thead><tr><th scope="col" rowspan="2">Card</th><th scope="col" rowspan="2">Slot</th><th scope="col" rowspan="2" class="tl">Link under copy</th><th scope="colgroup" colspan="2">Card alone, GB/s</th><th scope="colgroup" colspan="2">Both cards at once, GB/s</th><th scope="colgroup" colspan="3">Link errors</th></tr>
    <tr><th scope="col" class="g">host to device</th><th scope="col">device to host</th><th scope="col" class="g">host to device</th><th scope="col">device to host</th><th scope="col" class="g">replays since driver start</th><th scope="col">new replays in the tests</th><th scope="col">WHEA events, 7 days</th></tr></thead>
    <tbody>{pcrows}</tbody>
  </table>
  </div>
  <p class="ar-note">Theoretical x8 bandwidth: Gen5 31.5, Gen4 15.8, Gen3 7.9&nbsp;GB/s. Each card&rsquo;s link maximum is x16; the board gives x8 to each slot when both are used. <a href="https://github.com/smicha7/ws-thermal-data/tree/main/{Path(PC[-1]).name}">Data</a>.</p>"""
else:
    pc_txt = 'The copy bandwidth between host and each card and the PCIe replay counters after load are being measured; the results will be added here.'; PTAB = ""
PCIE = f"""  <h4 id="pcie-links">PCIe links of the two cards</h4>
  <p>The board splits the processor&rsquo;s sixteen PCIe 5.0 lanes between its two x16 slots, eight each, when both are populated. NVML reports both cards at PCIe Gen5 x8 under load: the slot could take x16 and the card supports Gen5, so the width is set by the board&rsquo;s split. At idle both links drop to Gen1, the normal power-saving down-training, and return to Gen5 under load. The replay counters, which count retransmitted packets, show whether a link is clean. {pc_txt} For our load, which streams from the card&rsquo;s own memory, the link does not limit the board power, which stays at the 575&nbsp;W limit.</p>{PTAB}"""
ST = sorted(glob.glob(str(G / "data/*stress1*/grid.csv")))
SR = []
if ST:
    for x in csv.DictReader(open(ST[-1])):
        if x.get("settled") != "1": continue
        on = [c for c in "AB" if float(x[f"card{c}_power_w"] or 0) > 300]
        for c in on: SR.append(dict(load="both cards" if len(on) == 2 else f"card {c} alone", card=c, core=float(x[f"card{c}_core_nvapi_c"] or x[f"card{c}_core_c"]), mem=float(x[f"card{c}_mem_c"]),
                                    hot=float(x[f"card{c}_hot_c"]), clk=float(x[f"card{c}_clock_mhz"]), w=float(x[f"card{c}_power_w"]), rpm=float(x[f"card{c}_fan_rpm"]),
                                    tin=float(x["intake_c"]), case=float(x["case_rpm"]), rad=float(x["rad_rpm"])))
    SR.sort(key=lambda r: (r["load"] == "both cards", r["card"]))
    g = lambda load, c: next(r for r in SR if r["load"] == load and r["card"] == c)
    A1, B1, A2, B2 = g("card A alone", "A"), g("card B alone", "B"), g("both cards", "A"), g("both cards", "B")
    srows = "".join(f'<tr><td class="tl">{r["load"]}</td><td>{r["card"]}</td><td class="g">{r["core"]:.1f}</td><td>{r["mem"]:.0f}</td><td>{r["hot"]:.1f}</td><td class="g">{r["clk"]:.0f}</td><td>{r["w"]:.0f}</td></tr>' for r in SR)
    STRESS = f"""  <h4 id="stress1">A two-card stress test (stress1)</h4>
  <p>Before steady4, both cards ran our load in the open frame at their stock 575&nbsp;W, with the card fans at 100&nbsp;% (about {A2["rpm"]:.0f}&nbsp;rpm), case and radiator fans at about 1600&nbsp;rpm and the pump at 2200&nbsp;rpm, intake air {min(r["tin"] for r in SR):.1f} to {max(r["tin"] for r in SR):.1f}&nbsp;&deg;C: card A alone, card B alone, then both, each point held to its plateau ({{tref:stress1}}). Alone, the two cards differ by little: card A settled at {A1["core"]:.1f}&nbsp;&deg;C core and {A1["mem"]:.0f}&nbsp;&deg;C memory, card B at {B1["core"]:.1f} and {B1["mem"]:.0f}&nbsp;&deg;C. With both loaded, card A, in the upper slot, ran {A2["core"] - A1["core"]:.0f}&nbsp;&deg;C hotter at the core and {A2["mem"] - A1["mem"]:.0f}&nbsp;&deg;C hotter at the memory than alone, because its fans draw in card B&rsquo;s flow-through exhaust, and its clock fell by {A1["clk"] - A2["clk"]:.0f}&nbsp;MHz; card B was unchanged within {max(abs(B2["core"] - B1["core"]), abs(B2["mem"] - B1["mem"])):.1f}&nbsp;&deg;C. Both cards stayed at 575&nbsp;W, held only by the software power cap with no thermal throttling, on PCIe Gen5 x8 links and without errors. Card A&rsquo;s memory, at {A2["mem"]:.0f}&nbsp;&deg;C even with every fan at full speed, is the binding temperature of the two-card machine and of its controller.</p>
  <p class="ar-tcap"><b>Two-card stress test (stress1): settled temperatures and clock of each card with one card or both under full load.</b> Open frame, 575&nbsp;W per card, card fans 100&nbsp;%, case and radiator fans about 1600&nbsp;rpm, pump 2200&nbsp;rpm, 24 October 2026; each point held to a plateau below 0.1&nbsp;&deg;C per minute on each card.</p>
  <div class="ar-tw">
  <table class="ar-tab ar-num ar-st ar-stress1">
    <thead><tr><th scope="col" class="tl">Load</th><th scope="col">Card</th><th scope="col" class="g">Core, &deg;C</th><th scope="col">Memory, &deg;C</th><th scope="col">Hot spot, &deg;C</th><th scope="col" class="g">Graphics clock, MHz</th><th scope="col">Board power, W</th></tr></thead>
    <tbody>{srows}</tbody>
  </table>
  </div>
  <p class="ar-note">Card A: first slot (PCIE1), upper; card B: second slot (PCIE2). Core from the NVAPI sensor; memory in whole degrees. Throttle reasons reported: software power cap only. <a href="https://github.com/smicha7/ws-thermal-data/tree/main/{Path(ST[-1]).parent.name}">Data</a>.</p>"""
else:
    STRESS = ""
# ---- fan and power-limit sweeps of the pair (each its own table; PL sweep appears when its folder lands)
def sweep(pattern, hid, title, var, excl=None):
    fs = sorted(f for f in glob.glob(str(G / f"data/{pattern}/grid.csv")) if not (excl and excl in f))
    if not fs: return "", None
    rows = list(csv.DictReader(open(fs[-1]))); cj = json.load(open(Path(fs[-1]).parent / "conditions.json")); st = json.load(open(Path(fs[-1]).parent / "status.json"))
    f = lambda x, k: float(x[k]) if x.get(k) not in (None, "") else float("nan")
    body = ""
    for x in rows:
        stop = x.get("settled") != "1"
        lab = (f'{x["gpu_pct"]}&nbsp;%' if var == "gpu" else f'{x["pl_pct"]}&nbsp;% ({f(x, "power_w_sum") / 2:.0f}&nbsp;W)') + ("<sup>a</sup>" if stop else "")
        body += (f'<tr><td>{lab}</td><td class="g">{f(x, "cardA_core_nvapi_c"):.1f}</td><td>{f(x, "cardA_mem_c"):.0f}</td><td>{f(x, "cardA_hot_c"):.1f}</td>'
                 f'<td class="g">{f(x, "cardB_core_nvapi_c"):.1f}</td><td>{f(x, "cardB_mem_c"):.0f}</td><td>{f(x, "cardB_hot_c"):.1f}</td>' + (f'<td class="g">{f(x, "cardA_fan_rpm"):.0f}</td><td>{x["seconds"]}</td></tr>' if var == "gpu" else f'<td class="g">{f(x, "cardA_clock_mhz"):.0f}</td><td>{f(x, "cardB_clock_mhz"):.0f}</td></tr>'))
    tin = sum(f(x, "intake_c") for x in rows) / len(rows)
    tab = (f'  <p class="ar-tcap"><b>{title}</b> Both cards at the same setting, case and radiator fans about 1600&nbsp;rpm, intake air {tin:.1f}&nbsp;&deg;C, front panel with dust filter on, top and side panels off; {cj["started_utc"][:10]}.</p>\n'
           f'  <div class="ar-tw ar-tw-wide">\n  <table class="ar-tab ar-num ar-st ar-ms ar-sweep">\n    <thead><tr><th scope="col" rowspan="2">{"GPU fans, both cards" if var == "gpu" else "Power limit, both cards"}</th><th scope="colgroup" colspan="3">Card A (PCIE1), &deg;C</th><th scope="colgroup" colspan="3">Card B (PCIE2), &deg;C</th>' + ('<th scope="col" rowspan="2" class="g">GPU fans, rpm</th><th scope="col" rowspan="2">Held, s</th></tr>' if var == "gpu" else '<th scope="colgroup" colspan="2">Graphics clock, MHz</th></tr>') +
           f'<tr><th scope="col" class="g">core</th><th scope="col">memory</th><th scope="col">hot spot</th><th scope="col" class="g">core</th><th scope="col">memory</th><th scope="col">hot spot</th>{"" if var == "gpu" else '<th scope="col" class="g">card A</th><th scope="col">card B</th>'}</tr></thead>\n    <tbody>{body}</tbody>\n  </table>\n  </div>\n'
           f'  <p class="ar-note">{"<sup>a</sup> Stopped before settling by the safety rule (memory 95, core 85 or hot spot 92&nbsp;&deg;C on either card); the values are the last readings. " if any(x.get("settled") != "1" for x in rows) else ""}Core from the NVAPI sensor; memory in whole degrees. <a href="https://github.com/smicha7/ws-thermal-data/tree/main/{Path(fs[-1]).parent.name}">Data</a>.</p>')
    return tab, rows
SW_TAB, SWR = sweep("*sweep-top-off", "sweep", "Fan sweep of the two Founders Edition cards at 575&nbsp;W each: settled temperatures of both cards as the GPU fans of both step down from 100&nbsp;%.", "gpu", excl="pl-sweep")
PL_TAB, PLR = sweep("*pl-sweep*", "plsweep", "Power-limit sweep of the two Founders Edition cards at GPU fans 90&nbsp;%: settled temperatures and clocks of both cards by power limit.", "pl")
PLTXT = WALL = ""
if PLR:
    W = np.array([float(x["power_w_sum"]) / 2 for x in PLR]); am = np.array([float(x["cardA_mem_c"]) for x in PLR]); ck = np.array([float(x["cardA_clock_mhz"]) for x in PLR])
    sl = np.polyfit(W, am, 1)[0] * 10; ok90 = [x for x in PLR if float(x["cardA_mem_c"]) <= 90.0]; top = max(ok90, key=lambda x: int(x["pl_pct"])) if ok90 else None
    pls = np.array([int(x["pl_pct"]) for x in PLR]); hi = pls >= 85; dck = np.polyfit(pls[hi], ck[hi], 1)[0] * 5 / ck.max() * 100
    PLTXT = (f"At GPU fans 90&nbsp;% the power limit of both cards was then stepped down from 100 to {pls.min()}&nbsp;% ({{tref:plsweep}}), every step settled. Card A&rsquo;s memory falls by about {sl:.1f}&nbsp;&deg;C per 10&nbsp;W"
             + (f"; a power limit of {top['pl_pct']}&nbsp;% ({float(top['power_w_sum']) / 2:.0f}&nbsp;W per card) holds it at {float(top['cardA_mem_c']):.0f}&nbsp;&deg;C" if top else "")
             + f". The price is speed: card A&rsquo;s graphics clock falls by about {dck:.1f}&nbsp;% for each 5&nbsp;% of power limit down to 85&nbsp;%, and more steeply below.")
    wp = sorted(glob.glob(str(G / "data/*sweep-top-off/wall-power.md")))
    if wp:
        WALL = ("During this sweep, at a power limit of 90&nbsp;% (518&nbsp;W per card), a meter at the wall socket read 1341&nbsp;W for the whole computer, while NVML reported 1036&nbsp;W for the two cards and the processor package drew 60.6&nbsp;W. "
                "The remaining 305&nbsp;W are the rest of the system and the losses of the power supply; with an assumed efficiency of 92&nbsp;% they split into about 107&nbsp;W of supply losses and about 137&nbsp;W for the board, memory, drives, pump and fans, an estimate, since the supply&rsquo;s efficiency curve was not measured.")
SWEEP = ""
if SWR:
    _lg = (Path(sorted(glob.glob(str(G / "data/*sweep-top-off/log.txt")))[-1])).read_text(errors="ignore")
    _m = re.search(r"karta A rdzeń [\d.]+ / pamięć (\d+)", _lg); STOPM = _m.group(1) if _m else "&mdash;"
    ok = [x for x in SWR if x.get("settled") == "1"]; bad = [x for x in SWR if x.get("settled") != "1"]
    d = [float(x["cardA_mem_c"]) - float(x["cardB_mem_c"]) for x in SWR]
    SWEEP = (f"""  <h4 id="sweep">How slow the fans of the pair can run</h4>
  <p>With the top panel off and both cards at 575&nbsp;W, the GPU fans of both cards were stepped down from 100&nbsp;% until a safety limit stopped the run ({{tref:sweep}}). At {ok[0]["gpu_pct"]}&nbsp;% card A&rsquo;s memory settled at {float(ok[0]["cardA_mem_c"]):.0f}&nbsp;&deg;C"""
             + (f""", at {ok[-1]["gpu_pct"]}&nbsp;% at {float(ok[-1]["cardA_mem_c"]):.0f}&nbsp;&deg;C""" if len(ok) > 1 else "")
             + (f"""; at {bad[0]["gpu_pct"]}&nbsp;% the safety stop ended the run after {bad[0]["seconds"]}&nbsp;s, with card A&rsquo;s memory at {STOPM}&nbsp;&deg;C""" if bad else "")
             + f""". The lowest safe GPU fan speed of the pair at full power in this configuration is therefore {ok[-1]["gpu_pct"]}&nbsp;%. Card B&rsquo;s memory stayed {min(d):.1f} to {max(d):.1f}&nbsp;&deg;C cooler than card A&rsquo;s throughout: the upper card sets the fans.</p>
{SW_TAB}""" + (f"""
  <p>{PLTXT}</p>
{PL_TAB}
  <p>{WALL}</p>""" if PLR else "\n  <p>A power-limit sweep at GPU fans 90&nbsp;% follows; its results will be added here.</p>"))
# the two cards compared
s3c = [x for x in csv.DictReader(open(sorted(glob.glob(str(G / "data/steady3-*/grid.csv")))[-1]))][1:-1]
zc = [x for x in s3c if x["settled"] == "1" and x["pl_pct"] == "100" and x["gpu_pct"] == "40" and x["case_rpm_target"] == "1600"][-1]
TWO = f"""  <h4 id="two-cards">Two different cards</h4>
  <p>The single-card study and the two-card study use different cards, and they cool differently. The ZOTAC Gaming RTX 5090 Solid of the single-card study has an open-air cooler: three axial fans blow into a large fin stack, about 3.5 slots thick, and the air leaves at the card&rsquo;s edges. The Founders Edition is a double-slot, flow-through design: two fans push the air through the fins and out on both faces. Alone at 575&nbsp;W, with its fans at only 40&nbsp;% and the case fans at 1600&nbsp;rpm, the ZOTAC settled at {float(zc["cardA_core_nvapi_c"]):.0f}&nbsp;&deg;C core and {float(zc["mem_c_max"]):.0f}&nbsp;&deg;C memory. The Founders Edition pair needs its fans at 90 to 100&nbsp;% to keep card A&rsquo;s memory at 88 to 92&nbsp;&deg;C (<a href="#sweep">Section 2.4.5</a>), and that memory protects itself at about 106&nbsp;&deg;C (<a href="#controller-mem">Section 2.8.2</a>). The cooling law estimated on the ZOTAC therefore does not transfer to the Founders Edition: the two-card study fits its own model to its own grid.</p>"""
# ---- the steady4 run so far
S4RUN = ""
_s4 = sorted(glob.glob(str(G / "data/*steady4*/status.json")))
if _s4:
    _st = json.load(open(_s4[-1])); _cj = json.load(open(Path(_s4[-1]).parent / "conditions.json"))
    _g = list(csv.DictReader(open(Path(_s4[-1]).parent / "grid.csv"))) if (Path(_s4[-1]).parent / "grid.csv").exists() else []
    _ok = sum(1 for x in _g if x.get("settled") == "1"); _sk = sum(1 for x in _g if x.get("settled") == "-2")
    _panels = "with the top and side panels off and the front panel with its dust filter on" if "TOP panel OFF" in _cj.get("case", "") else "with the panels on"
    S4RUN = (f"The first run of the grid, {_panels}, " + ("stopped on request" if _st.get("state") == "aborted" else "has run") + f" after {_st.get('elapsed_s', 0) / 3600:.1f}&nbsp;h with {_ok} settled points" + (f" and {_sk} skipped at a safety limit" if _sk else "") + ".")
# ---- methods subsection
mins = sum(28 * hold(gp) for gp in CARDS) / 60
MET = f"""  <h4 id="steady4-method">The two-card study (in progress)</h4>
  <p>For the two-card study the ZOTAC was replaced on 24 October by two RTX 5090 Founders Edition cards, card A in the first PCIe slot and card B in the second, at the board&rsquo;s slot spacing ({{fref:fig-two-card-set-up-panels-on-schematic}}). The two-card grid steady4 repeats the levels of steady3 on both cards together, with one change forced by the hotter pair: the power limit of 100&nbsp;% is run only at GPU fans of 90&nbsp;% and above, the lowest safe speed found at full power (<a href="#sweep">Section 2.4.5</a>), which leaves 161 of the 198 points. A point ends by the fit rule, at least 2&nbsp;min after a small predicted step and otherwise 5, 4 or 3&nbsp;min by GPU fan speed as the settling analysis of steady3 suggests (<a href="#settle">Section 4.2</a>), then until the fitted final value of each card is known within &plusmn;0.2&nbsp;&deg;C, at most 15&nbsp;min; a point is skipped when either card reaches 95&nbsp;&deg;C memory, 85&nbsp;&deg;C core or 92&nbsp;&deg;C hot spot, and the run aborts at 100&nbsp;&deg;C memory. The measurement microphone records a raw level at every point for later calibration. {S4RUN}</p>
  <p>The grid answers three questions: how much card A, whose fans draw in card B&rsquo;s flow-through exhaust (<a href="#stress1">Section 2.4.4</a>), runs hotter than when alone, and how that depends on both fan sets; how much the closed case changes the settled temperatures and the role of the case fans, against the open frame of steady3; and what control law two cards need, with one noise budget for the whole machine and the hotter card setting the fans.</p>
<!--setupfig2:start--><!--setupfig2:end-->
{PCIE}
{STRESS}
{SWEEP}
{TWO}"""
# ---- live tables
G4 = sorted(glob.glob(str(G / "data/*steady4*/grid.csv")))
cells, SKIP = {}, set()
if G4:
    r = list(csv.DictReader(open(G4[-1])))
    key = lambda x: (int(x["pl_pct"]), int(x["gpu_pct"]), int(float(x["case_rpm_target"])))
    if len(r) > 1 and key(r[0]) == key(r[-1]): r = r[1:-1]          # anchors at start and end
    f = lambda x, k: float(x[k]) if x.get(k) not in (None, "") else None
    for x in r:
        if x.get("settled") == "-2": SKIP.add(key(x)); continue
        if x.get("settled") != "1": continue
        cells[key(x)] = dict(A=f(x, "cardA_core_nvapi_c") or f(x, "cardA_core_c"), B=f(x, "cardB_core_nvapi_c") or f(x, "cardB_core_c"),
                             mA=f(x, "cardA_mem_c"), mB=f(x, "cardB_mem_c"), T=f(x, "intake_c"))
    with open(SITE / "data/gpu-map-steady4-cells.csv", "w", newline="") as fo:
        w = csv.writer(fo); w.writerow(["pl_pct", "gpu_pct", "case_target_rpm", "cardA_core_c", "cardB_core_c", "cardA_mem_c", "cardB_mem_c", "intake_c"])
        for k, v in sorted(cells.items(), key=lambda kv: (-kv[0][0], kv[0][1], kv[0][2])): w.writerow([*k, v["A"], v["B"], v["mA"], v["mB"], v["T"]])
fmt = lambda v: "&middot;" if v is None else f"{v:.1f}"
cellv = lambda k, c: "&times;" if k in SKIP and k not in cells else fmt(cells.get(k, {}).get(c))
def tab(pl, c):
    body = "".join(f'<tr><td>{gp}&nbsp;%</td>' + "".join(f'<td{" class=\"s3-e\"" if (pl, gp, cc) not in cells else ""}>{cellv((pl, gp, cc), c)}</td>' for cc in CASES) + "</tr>" for gp in CARDS)
    n = sum(1 for k in cells if k[0] == pl)
    return (f'<h4 class="ar-h4">Card {c}, GPU core temperature in &deg;C at power limit {pl}&nbsp;% ({PLW[pl]}&nbsp;W per card), two cards, top and side panels off: GPU fan speed of both cards (rows) against case and radiator fan target (columns). {n} of 49 settings measured.</h4>\n'
            f'<div class="ar-tw ar-tw-wide"><table class="ar-tab ar-num ar-s3 ar-s4"><thead><tr><th scope="col">GPU fans, both cards</th>' + "".join(f'<th scope="col">{("&asymp;2920" if cc == 3000 else cc)}&nbsp;rpm</th>' for cc in CASES) + f'</tr></thead><tbody>{body}</tbody></table></div>\n')
TB = (f'  <h3 id="steady4-grid">Two-card data: steady4 (in progress)</h3>\n  <p>' + (f'The two-card grid has reached {len(cells)} of its 161 points, with {len(SKIP - set(cells))} skipped at a safety limit; the tables fill as it runs.' if cells else 'The two-card grid has not started yet; the tables below fill as it runs, one per card and power limit.')
      + '</p>\n' + "".join(tab(pl, c) for pl in PLS for c in "AB")
      + '  <p class="ar-note">A dot (&middot;) means the setting has not been measured yet; a cross (&times;) that it was skipped because a card reached a safety limit (memory 95, core 85 or hot spot 92&nbsp;&deg;C); at 100&nbsp;% power limit only GPU fans of 90&nbsp;% and above are run. Core from the NVAPI sensor of each card. ' + ('<a href="/research/data/gpu-map-steady4-cells.csv">Data (CSV)</a>, with the memory of both cards and the intake air.' if cells else 'The data file appears here once the run starts.') + '</p>')
s = F.read_text()
s = put(s, "settle", SET, before="<!--stats:start-->")
s = put(s, "s4method", MET, before='<h3 id="models"')
s = put(s, "s4tables", TB, after="<!--estdata:end-->")
css = ".ar-s4 td.s3-e{color:var(--mute-l);opacity:.55;text-align:center!important}"
if ".ar-s4 td.s3-e" not in s: k = s.index("</style>"); s = s[:k] + css + s[k:]
F.write_text(s); print("steady4 sections written; cells:", len(cells), "min hold h:", round(mins, 1), {g: round(v, 2) for g, v in S.items()})
