"""Figure 1: the test set-up as built (Seb's photos, 24 Oct 2026). (a) top view of the upper tier with the real board layout from
WS.Remote's board file (ASRock X870E Taichi Lite), (b) side elevation of the three tiers. Inline SVG, currentColor (light/dark),
two panels side by side, stacked on phones. A second card goes in PCIE2 (dashed): set CARDS = 2 when it is installed.
Replaces the first <figure> of section 2 between <!--setupfig:start/end-->. Usage: setup_fig.py"""
import json, re
from pathlib import Path
F = Path.home() / "Claude/gruency-site/research/gpu-cooling-method.html"
B = json.load(open(Path.home() / "Applications/Zdalnie/boards/asrock-x870e-taichi-lite.json"))
BH = 305.0; BW = BH * B["aspect"]           # board, mm (E-ATX height 305 mm; width from the board file's aspect)
FX0, FY0, FX1, FY1 = 30, 40, 520, 440       # upper tier of the frame, top view (schematic, 1 unit ≈ 1 mm)
X0, Y0 = 100, 70                            # board origin (top-left: rear I/O edge left, CPU power and fan headers at the top)
CARD_L, CARD_T = 304, 40                    # RTX 5090 Founders Edition: 304 mm long, two slots (about 40 mm)
bx = lambda u: X0 + u * BW; by = lambda v: Y0 + v * BH
R = lambda k: B["rects"][k]
EX = {e[0]: e[1:5] for e in B["extras"]}
def rect(x, y, w, h, extra=""): return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" {extra}/>'
def brect(r, extra=""): return rect(bx(r[0]), by(r[1]), r[2] * BW, r[3] * BH, extra)
LINE = 'fill="none" stroke="currentColor" stroke-width="1.5"'
THIN = 'fill="none" stroke="currentColor" stroke-opacity=".55" stroke-width="1"'
FAN = 'fill="currentColor" fill-opacity=".85"'
ARW0 = 'stroke="currentColor" stroke-opacity=".7" stroke-width="1.5" fill="none" marker-end="url(#ah1)"'
T = lambda x, y, s, a="start", extra="": f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="{a}" {extra}>{s}</text>'
sub = lambda s: f'<tspan baseline-shift="sub" font-size="78%">{s}</tspan>'
def build(CARDS, closed, tag):
    ARW = ARW0.replace("#ah1", f"#ah{tag}")
    # ---- (a) top view
    a = [rect(FX0, FY0, FX1 - FX0, FY1 - FY0, LINE)]
    a.append(rect(X0, Y0, BW, BH, THIN))                                      # board
    a.append(brect(R("CPU"), THIN)); a.append(f'<circle cx="{bx(R("CPU")[0] + R("CPU")[2] / 2):.1f}" cy="{by(R("CPU")[1] + R("CPU")[3] / 2):.1f}" r="27" {THIN}/>')  # pump block
    for k in B["mem"]: a.append(brect(R(k), 'fill="currentColor" fill-opacity=".25"'))
    for k in ("CPU_FAN2", "AIO_PUMP"): a.append(rect(bx(EX[k][0]), by(EX[k][1]), EX[k][2] * BW, EX[k][3] * BH, 'fill="currentColor"'))
    for k in B["pcie"]: a.append(brect(R(k), 'fill="currentColor" fill-opacity=".35"'))
    cards = []
    for i, k in enumerate(B["pcie"][:2]):
        y = by(R(k)[1]) + R(k)[3] * BH / 2
        dashed = i >= CARDS
        cards.append((y, dashed))
        a.append(rect(X0 - 6, y - 2, CARD_L, CARD_T, ('fill="none" stroke="currentColor" stroke-width="1.2" stroke-dasharray="5 4"' if dashed else LINE)))
        if not dashed:   # FE: two axial fans on the +y face, flow-through: air passes through the fins and leaves on the board side
            for j in range(2): a.append(rect(X0 + 40 + j * 150, y + CARD_T - 6, 90, 5, FAN))
            for j in range(2): a.append(f'<path d="M{X0 + 85 + j * 150} {y + CARD_T + 22}V{y - 14}" {ARW} stroke-opacity=".45"/>')
    # case fans: 3 intake on the right wall, 1 exhaust on the left wall by the CPU
    for c in (FY0 + 70, FY0 + 200, FY0 + 330): a.append(rect(FX1 - 6, c - 60, 12, 120, FAN))
    ex_y = by(R("CPU")[1] + R("CPU")[3] / 2); a.append(rect(FX0 - 6, ex_y - 60, 12, 120, FAN))
    # airflow
    for c in (FY0 + 70, FY0 + 200, FY0 + 330): a.append(f'<path d="M{FX1 + 44} {c}H{FX1 + 10}" {ARW}/>')
    a.append(f'<path d="M{FX1 - 14} {FY0 + 70}C380 {FY0 + 70} 200 {ex_y} {FX0 + 12} {ex_y}" {ARW}/>')
    a.append(f'<path d="M{FX1 - 14} {FY0 + 200}C420 {FY0 + 200} 300 {cards[0][0] - 20} {X0 + 40} {cards[0][0] - 24}" {ARW}/>')
    a.append(f'<path d="M{FX1 - 14} {FY0 + 330}C440 {FY0 + 330} 380 {cards[0][0] + CARD_T + 18} {X0 + 60} {cards[0][0] + CARD_T + 18}" {ARW}/>')
    a.append(f'<path d="M{FX0 - 8} {ex_y}H{FX0 - 40}" {ARW}/>')
    a.append(f'<circle cx="{X0 + 210}" cy="{cards[0][0] + CARD_T + 18}" r="0"/>')
    tin = None   # T_in is in the bottom tier (side view only)
    lab = [T(FX1 - 14, FY0 - 10, "intake, f" + sub("c"), "end"), T(FX0 + 14, ex_y - 66, "exhaust"),
           T(bx(R("CPU")[0] + R("CPU")[2] / 2), by(R("CPU")[1]) - 8, "CPU, pump", "middle"),
           T(bx(R("A1")[0]) - 2, by(R("A1")[1] + R("A1")[3]) + 18, "DIMMs"),
           T(bx(EX["CPU_FAN2"][0]) - 10, Y0 - 8, "AIO fan, pump headers", "end"),
           T(X0 + CARD_L / 2, cards[0][0] + CARD_T / 2 - 2, ("RTX 5090 FE, card A (PCIE1)" if CARDS == 2 else "RTX 5090 FE, f" + sub("g") + " (PCIE1)"), "middle", 'dominant-baseline="middle"'),
           T((FX0 + FX1) / 2, FY1 + 30, "(a) top view, upper tier &middot; " + ("panels on" if closed else "top open"), "middle")]
    if not cards[1][1]: lab.append(T(X0 + CARD_L / 2, cards[1][0] + CARD_T / 2 + 2, "RTX 5090 FE, card B (PCIE2)", "middle", 'dominant-baseline="middle"'))
    if closed: a.append(f'<rect x="{FX0 - 3}" y="{FY0 - 3}" width="{FX1 - FX0 + 6}" height="{FY1 - FY0 + 6}" fill="none" stroke="currentColor" stroke-width="4" stroke-opacity=".35"/>')
    if cards[1][1]: lab.append(T(X0 + CARD_L / 2, cards[1][0] + CARD_T / 2 + 2, "second card (PCIE2)", "middle", 'dominant-baseline="middle" fill-opacity=".6"'))
    A = (f'<svg class="ar-svg" viewBox="-20 0 610 490" role="img" aria-labelledby="f{tag}a"><title id="f{tag}a">Top view of the upper tier: the motherboard lies flat with the processor, its pump block and the memory; the graphics card stands in the first PCIe slot with its fans facing sideways; three case fans on the right wall blow across the card and board, one fan on the left wall by the processor exhausts; the second PCIe slot is reserved for a second card.</title>'
         f'<defs><marker id="ah{tag}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="currentColor"/></marker></defs>'
         + "".join(a) + '<g class="ar-svg-t" fill="currentColor">' + "".join(lab) + "</g></svg>")
    # ---- (b) side elevation, seen from the card's fan side
    Z = {"top": 40, "t1": 230, "t2": 340, "t3": 470}            # open top, tray of the upper tier, floor of the middle tier, bottom
    b = [f'<path d="M{FX0} {Z["top"]}V{Z["t3"]}M{FX1} {Z["top"]}V{Z["t3"]}M{FX0} {Z["t1"]}H{FX1}M{FX0} {Z["t2"]}H{FX1}M{FX0} {Z["t3"]}H{FX1}" {LINE}/>']
    b.append(rect(X0, Z["t1"] - 8, BW, 6, THIN))                                     # board on the tray
    b.append(rect(X0 - 6, Z["t1"] - 8 - 137, CARD_L, 137, LINE))                      # card standing in its slot
    for j in range(2): b.append(f'<circle cx="{X0 + 80 + j * 150}" cy="{Z["t1"] - 83}" r="52" {THIN}/>')   # FE: two axial fans
    cpu_x = bx(R("CPU")[0] + R("CPU")[2] / 2)
    b.append(rect(FX1 - 6, Z["t1"] - 130, 12, 120, FAN)); b.append(rect(FX0 - 6, Z["t1"] - 130, 12, 120, FAN))
    b.append(f'<path d="M{FX1 + 44} {Z["t1"] - 70}H{FX1 + 10}" {ARW}/><path d="M{FX1 - 14} {Z["t1"] - 175}C380 {Z["t1"] - 175} 200 {Z["t1"] - 70} {FX0 + 12} {Z["t1"] - 70}" {ARW}/>'
             f'<path d="M{FX0 - 8} {Z["t1"] - 70}H{FX0 - 40}" {ARW}/><path d="M{X0 + 170} {Z["t1"] - 165}V{Z["top"] - 6}" {ARW} stroke-dasharray="4 4"/>')
    b.append(rect(160, Z["t2"] - 92, 190, 86, LINE)); b.append(rect(66, Z["t2"] - 98, 12, 92, FAN))              # PSU and the small fan beside it
    b.append(rect(FX0 + 22, Z["t3"] - 128, 26, 120, LINE)); b.append(rect(FX0 + 50, Z["t3"] - 128, 12, 120, FAN))  # radiator and its fans
    b.append(f'<path d="M{FX0 + 35} {Z["t3"] - 128}V{Z["t2"] + 6}M{FX0 + 35} {Z["t2"] - 2}C{FX0 + 35} 300 {cpu_x} 270 {cpu_x} {Z["t1"] - 12}" fill="none" stroke="currentColor" stroke-opacity=".55" stroke-width="1.2" stroke-dasharray="3 3"/>')
    b.append(f'<path d="M{FX0 + 140} {Z["t3"] - 68}H{FX0 + 70}" {ARW}/><path d="M{FX0 + 16} {Z["t3"] - 68}H{FX0 - 40}" {ARW}/>')
    b.append(f'<circle cx="{FX1 - 60}" cy="{Z["t3"] - 60}" r="5" fill="currentColor"/>')
    lb = [T(FX1 - 14, Z["top"] + 18, "intake, f" + sub("c"), "end"), T(FX0 + 14, Z["top"] + 18, "exhaust"),
          T(X0 + CARD_L / 2, Z["t1"] - 30, ("cards A and B (B behind A), f" if CARDS == 2 else "graphics card, f") + sub("g"), "middle"), T(X0 + 170, Z["top"] - 12, "top panel" if closed else "open top", "middle"),
          T(255, Z["t2"] - 46, "power supply", "middle", 'dominant-baseline="middle"'), T(84, Z["t2"] - 104, "small fan"),
          T(FX0 + 70, Z["t3"] - 100, "radiator, f" + sub("r")), T(FX1 - 72, Z["t3"] - 54, "T" + sub("in"), "end"),
          T(FX1 - 14, Z["t1"] - 12, "upper tier", "end"), T(FX1 - 14, Z["t3"] - 12, "bottom tier: radiator air stays here", "end"),
          T(FX1 - 14, Z["t2"] - 12, "middle tier", "end"),
          T((FX0 + FX1) / 2, Z["t3"] + 40, "(b) side elevation, three tiers" + (", panels on" if closed else ""), "middle")]
    Bsvg = (f'<svg class="ar-svg" viewBox="-20 0 610 530" role="img" aria-labelledby="f{tag}b"><title id="f{tag}b">Side elevation of the open frame: on top the board and the standing graphics card with the case fans blowing across them and an open top; in the middle the power supply with a small fan; at the bottom the processor radiator with its three fans, whose air stays in the bottom tier, and its tubes running up to the pump block.</title>'
            + "".join(b) + '<g class="ar-svg-t" fill="currentColor">' + "".join(lb) + "</g></svg>")
    if closed:
        Bsvg = Bsvg.replace(f'<path d="M{X0 + 170} {Z["t1"] - 165}V{Z["top"] - 6}" {ARW} stroke-dasharray="4 4"/>', "")
        Bsvg = Bsvg.replace("</svg>", f'<path d="M{FX0 - 3} {Z["top"]}H{FX1 + 3}M{FX0 - 3} {Z["top"]}V{Z["t3"]}M{FX1 + 3} {Z["top"]}V{Z["t3"]}" fill="none" stroke="currentColor" stroke-width="4" stroke-opacity=".35"/></svg>')
    return A, Bsvg
A, Bsvg = build(1, False, "set1")
A2, B2 = build(2, True, "set2")
CAP = ('<figcaption><b>Figure 1.</b> As built; board layout to scale. (a) Top view of the upper tier of the open frame: the motherboard (ASRock X870E Taichi Lite) lies flat, facing up, with the processor and its pump block next to the memory; the graphics card, an RTX 5090 Founders Edition (two axial fans, flow-through), stands in the first PCIe slot (PCIE1) with its fans facing sideways; their air passes through the fins and leaves on the board side. Three 120&nbsp;mm be quiet! case fans on one side wall blow across the card and the board; one more, on the opposite wall by the processor, is the exhaust; the top is open. The second slot (PCIE2, dashed) takes the second card of the two-card study at the same spacing; it was not fitted for the measurements reported here. '
       '(b) Side elevation of the three tiers: board and card on top, the power supply with a small fan in the middle, and at the bottom the processor&rsquo;s radiator, mounted upright with its three SilverStone fans, its tubes running up to the pump block. The radiator&rsquo;s air stays in the bottom tier: it does not pass through the tier of the board and the card and does not affect the airflow there. The fan controller (aquaero 6) sits in a slot bracket at the top of the frame; its air sensor, T<sub>in</sub>, is in the bottom tier. As drawn, to be confirmed: the position of T<sub>in</sub>, the direction of the small fan beside the power supply (drawn without one), and the directions of the radiator fans and the case fans.</figcaption>')
FIG = f'<!--setupfig:start-->\n  <figure class="ar-fig ar-fig-wide ar-setup">\n    <div class="ar-svg2">{A}{Bsvg}</div>\n    {CAP}\n  </figure>\n<!--setupfig:end-->'
CAP2 = ('<figcaption><b>Figure 0.</b> Study in progress; board layout to scale. (a) Top view of the upper tier: card A, an RTX 5090 Founders Edition, in the first PCIe slot (PCIE1) and card B, the same model, in the second (PCIE2), at the board&rsquo;s slot spacing; card A&rsquo;s fans face the back of card B, about 40&nbsp;mm away. (b) Side elevation: the three tiers with the side, front and top panels fitted (heavy grey lines); fans and airflow as in Figure 1. As drawn, to be confirmed: the panel layout, the position of T<sub>in</sub> and the directions of the radiator, case and small fans.</figcaption>')
FIG2 = f'<!--setupfig2:start-->\n  <figure class="ar-fig ar-fig-wide ar-setup">\n    <div class="ar-svg2">{A2}{B2}</div>\n    {CAP2}\n  </figure>\n<!--setupfig2:end-->'
s = F.read_text()
if "<!--setupfig2:start-->" in s:
    s = s[:s.index("<!--setupfig2:start-->")] + FIG2 + s[s.index("<!--setupfig2:end-->") + len("<!--setupfig2:end-->"):]
if "<!--setupfig:start-->" in s:
    s = s[:s.index("<!--setupfig:start-->")] + FIG + s[s.index("<!--setupfig:end-->") + len("<!--setupfig:end-->"):]
else:
    i = s.index('<figure class="ar-fig" id="fig-test-set-up'); j = s.index("</figure>", i) + len("</figure>"); s = s[:i] + FIG + s[j:]
css = ".ar-svg2{display:grid;grid-template-columns:1fr 1fr;gap:12px;align-items:end}@media (max-width:620px){.ar-svg2{grid-template-columns:1fr}}"
if ".ar-svg2{" not in s: k = s.index("</style>"); s = s[:k] + css + s[k:]
F.write_text(s); print("set-up figures written")
