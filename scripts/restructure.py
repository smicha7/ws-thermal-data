"""One-time restructure of the GPU cooling article into journal form (Seb 2026-10-23). Moves existing blocks (generator markers
travel with them) and adds the new sections. Headings are re-levelled every run by cite_terms.py (HEADMAP). Usage: restructure.py"""
import re
from pathlib import Path
F = Path.home() / "Claude/gruency-site/research/gpu-cooling-method.html"
s = F.read_text()
assert '<h2 id="intro">' not in s, "already restructured"
s = re.sub(r'<span class="secno">[^<]*</span> ', "", s)
A = s.index('<h2 id="problem">'); Z = s.index('<h2 id="sources">')
body = s[A:Z]
def pos(tok):
    i = body.find(tok); assert i >= 0, tok; return i
cuts = [("problem", '<h2 id="problem">'), ("variables", '<h2 id="variables">'), ("templimits", '<h2 id="templimits">'),
        ("resistance", '<h2 id="resistance">'), ("grid", '<h2 id="grid">'), ("setup", '<h2 id="setup">'),
        ("uncertainty", '<h2 id="uncertainty">'), ("model", '<h2 id="model">'), ("results", '<h2 id="results">'),
        ("run2", '<h2 id="run2">'), ("run2model", '<h3 id="run2-model"'), ("run2dyn", '<h3 id="run2-dyn"'),
        ("methodlog", '<h2 id="method-log">'), ("plan", '<h3 id="method-next"'), ("stats", "<!--stats:start-->"),
        ("s3", "<!--s3tables:start-->"), ("dtold", "<!--datatables:start-->"), ("dtmem", "<!--dtmem:start-->"),
        ("dt112", "<!--dt112:start-->"), ("noise", "<!--noise:start-->"), ("ctrlintro", '<h2 id="controller">'),
        ("modes", "<!--modes:start-->"), ("v1", '<h3 id="controller-v1"'), ("cmem", '<h3 id="controller-mem"'),
        ("ctrlsim", "<!--ctrlsim:start-->"), ("ctrl1", "<!--ctrl1:start-->"), ("cpu", "<!--cpu:start-->"),
        ("pareto", '<h2 id="pareto">'), ("power", '<h2 id="power">'), ("iso", "<!--isotemp:start-->"),
        ("multi", '<h2 id="multi">'), ("concl", '<h2 id="conclusions">'), ("limits", '<h2 id="limits">')]
P = [(k, pos(t)) for k, t in cuts]
assert [p for _, p in P] == sorted(p for _, p in P), "segment order changed"
SEG = {}
for i, (k, p) in enumerate(P):
    SEG[k] = body[p:(P[i + 1][1] if i + 1 < len(P) else len(body))]
assert "".join(SEG[k] for k, _ in P) == body
def drop_h2(seg):   # remove the leading h2 of a segment (its content stays)
    return re.sub(r"^\s*<h2[^>]*>.*?</h2>\s*", "", seg, count=1, flags=re.S)
H = lambda tag, i, t: f"\n  <{tag} id=\"{i}\">{t}</{tag}>\n"
c = lambda *k: " ".join(f'<a class="cite" href="#s{n}">[{n}]</a>' for n in k)
new_intro = (H("h2", "intro", "Introduction") + H("h3", "problem", "The problem") + """  <p>A graphics card in a workstation can be fast, cool or quiet, but not all three at full measure. Most computers settle the matter with fan curves chosen by feel; we want the workstation to settle it with evidence: to keep the card at full speed and inside its safe limits, and to make no more noise than the moment requires.</p>
""" + drop_h2(SEG["problem"]) + H("h3", "sota", "State of the art") + f"""  <p>Fan control of computers has been studied mostly for servers and data centres, where the cost is energy rather than noise. Model-based optimal fan control of a multi-fan server against component limits {c(54)}, joint control of processor power and fan speed {c(55,56,57)}, real-time control on reduced-order thermal models {c(58)}, robustness to quantised and noisy sensors {c(59)}, leakage-aware cooling {c(60)}, experimental comparisons of fan strategies {c(61)} and cooling-versus-compute trade-offs at data-centre scale {c(62)} all treat cooling and computation as coupled decisions. Dynamic thermal management throttles a processor to stay under a thermal limit {c(68)}, and was carried over to graphics processors early {c(69)}; frequency and power capping of GPUs is now a common lever for energy and temperature {c(70,71,72)}. Compact thermal-resistance and RC models describe heat sinks and packages {c(73,74)}, and the classical heat-transfer texts give the dependence of the convective resistance on airflow {c(7,8,10)}.</p>
  <p>Noise enters this literature less often. The coupled cooling-and-noise problem of electronics packages was stated by Lyon and Bergles {c(64)}; computer fan noise and its dependence on speed were characterised by Huang {c(63)}; multiphysics thermal&ndash;acoustic models of a server exist {c(65)}; and recent listening studies predict how annoying a computer fan sounds {c(66)}, beyond the A-weighted level {c(67)}. In practice, fans are controlled by fixed temperature-to-speed curves: the vendor curve of the graphics card, Linux fancontrol {c(75)}, FanControl on Windows {c(76)} or overclocking tools, none of which models the cooler or knows the noise. The closest prior art we found is a patent for a controller that keeps a laptop under a target sound level by capping the processor&rsquo;s performance {c(77)}; it does not model separate GPU and case fans. We found no published work that fits a thermal-resistance model over both fan sets of a high-power graphics card and uses it, with a fan-noise model, to choose the coolest fan pair within a noise budget and to lower the power limit only when the budget runs out.</p>
""" + H("h3", "aim", "Aim and contribution") + """  <p>The aim of this work is to derive the fan and power control law for our own software, WS.Sensor, so that a workstation runs fully automatically at the best trade-off between noise and performance without overheating. The contribution is fourfold: a measurement rig and protocol on our own test machine (ws298) with our own logging software (WS.Sensor Lab); a two-path settled-temperature model of an RTX 5090 over both fan sets and the power limit, with a dynamic model and a memory model, tested statistically; a controller that defines its modes by noise and treats temperatures as constraints; and the open data of every measurement.</p>
""")
new_methods = (H("h2", "methods", "Materials and methods") + SEG["setup"] + SEG["variables"] + SEG["templimits"] + SEG["uncertainty"]
    + SEG["grid"] + SEG["plan"]
    + H("h3", "models", "Models") + SEG["resistance"] + SEG["model"] + SEG["run2dyn"]
    + H("h4", "noise-model", "Noise model") + """  <p>Without our own sound map, each set of fans is given its level from published measurements: the case and radiator fans from a free-field fit of level against speed, the card&rsquo;s fans from a review anchor scaled by 50&nbsp;log<sub>10</sub> of the speed ratio; the sets are summed on an energy basis, equation (13). The sources and the fits are collected in <a href="#appendix-d">Appendix D</a>.</p>
""" + H("h3", "stat-methods", "Statistical methods") + """  <p>Constants are estimated by nonlinear least squares and compared by cross-validation and the Bayesian information criterion; residuals are tested for serial correlation, constant variance, normality and functional form, and standard errors are heteroscedasticity-consistent. Each method is described, with its source, in the glossary table of <a href="#stats-methods">Section 3.2</a>.</p>
""" + SEG["ctrlintro"] + SEG["modes"] + SEG["cmem"])
new_results = (H("h2", "results-main", "Results") + SEG["s3"] + SEG["stats"] + SEG["dtmem"] + SEG["pareto"] + SEG["iso"] + SEG["power"]
    + H("h3", "controller-res", "The controller in simulation and on the real card") + SEG["ctrlsim"] + SEG["ctrl1"] + SEG["cpu"])
new_disc = (H("h2", "discussion", "Discussion") + H("h3", "interpretation", "Interpretation") + drop_h2(SEG["concl"])
    + H("h3", "lit-compare", "Comparison with the literature") + f"""  <p>The structure we find, two conductances in parallel with exponents that carry the fans&rsquo; own airflow curves, is the compact-model view of a heat sink {c(73,74)} with the boundary condition set by two fan sets. As in the server studies {c(54,55,56)}, cooling and power are coupled decisions; unlike them, the cost here is noise at the desk, not energy, and the power limit is the last resort rather than a co-equal variable. The fan-noise models rest on published speed&ndash;level data {c(63)} and remain the weakest link until our own measurements replace them {c(64,66)}.</p>
""" + SEG["limits"] + SEG["multi"])
new_concl = H("h2", "conclusions", "Conclusions") + "<!--ctrllaw:start--><!--ctrllaw:end-->\n"
new_end = (H("h2", "data-availability", "Data and code availability") + """  <p>Every measurement behind the tables and figures is published as CSV next to its table; the complete data set, the analysis scripts and the figure sources are kept in the repository ws-thermal-data and are available on request.</p>
""" + H("h2", "contributions", "Author contributions") + """  <p>Sebastian Michalski: conception, method, test rig, measurements, WS.Sensor software and supervision. Data analysis, model fitting and drafting were carried out with the assistance of an AI model (Claude, Anthropic) under the author&rsquo;s direction; the author takes responsibility for the content.</p>
""")
new_app = (H("h2", "appendix-a", "Preliminary runs") + """  <p>The first runs used 60-second cells and a fast grid; they taught us how long a point must settle and why the final grid was measured again. They are kept here for completeness.</p>
""" + SEG["results"] + SEG["run2"] + SEG["run2model"] + SEG["methodlog"] + SEG["dt112"]
    + H("h2", "appendix-b", "Earlier-session tables") + SEG["dtold"]
    + H("h2", "appendix-c", "The first controller version") + SEG["v1"]
    + H("h2", "appendix-d", "Noise data from the literature") + SEG["noise"])
main = new_intro + new_methods + new_results + new_disc + new_concl + new_end
s = s[:A] + main + s[Z:]
# references, then appendices after the sources section
srcA = s.index('<h2 id="sources">'); srcZ = s.index("</section>", srcA) if "</section>" in s[srcA:srcA + 200000] else None
# append appendices after the sources list (end of the sources block: the next </ol> after the last <li id="s..">)
last = max(m.end() for m in re.finditer(r'<li id="s\d+">.*?</li>', s))
end_ol = s.index("</ol>", last) + 5
s = s[:end_ol] + "\n" + new_app + s[end_ol:]
F.write_text(s); print("restructured")
