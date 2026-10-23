"""Statistical/method references (s16+) and first-use citations in the GPU cooling article. Idempotent; run after every
section generator. Usage: cite_terms.py"""
import re, html as _html
from pathlib import Path
F = Path.home() / "Claude/gruency-site/research/gpu-cooling-method.html"
_t = F.read_text(); F.write_text(re.sub(r'<span class="hn[^"]*">(.*?)</span><br>', r"\1, ", _t))   # undo the header split; redone at the end
REFS = {
 16: "Student [W. S. Gosset]. The probable error of a mean. <i>Biometrika</i> 6 (1908) 1&ndash;25. <a href=\"https://doi.org/10.2307/2331554\">doi:10.2307/2331554</a>",
 17: "J. Durbin, G. S. Watson. Testing for serial correlation in least squares regression. I. <i>Biometrika</i> 37 (1950) 409&ndash;428. <a href=\"https://doi.org/10.1093/biomet/37.3-4.409\">doi:10.1093/biomet/37.3-4.409</a>",
 18: "J. Durbin, G. S. Watson. Testing for serial correlation in least squares regression. II. <i>Biometrika</i> 38 (1951) 159&ndash;178. <a href=\"https://doi.org/10.1093/biomet/38.1-2.159\">doi:10.1093/biomet/38.1-2.159</a>",
 19: "J.-M. Dufour, L. Khalaf. Monte Carlo test methods in econometrics. In B. H. Baltagi (ed.), <i>A Companion to Theoretical Econometrics</i>, chapter 23, 494&ndash;519. Blackwell, Oxford, 2001. <a href=\"https://doi.org/10.1002/9780470996249.ch24\">doi:10.1002/9780470996249.ch24</a>",
 20: "T. S. Breusch. Testing for autocorrelation in dynamic linear models. <i>Australian Economic Papers</i> 17 (1978) 334&ndash;355. <a href=\"https://doi.org/10.1111/j.1467-8454.1978.tb00635.x\">doi:10.1111/j.1467-8454.1978.tb00635.x</a>",
 21: "L. G. Godfrey. Testing against general autoregressive and moving average error models when the regressors include lagged dependent variables. <i>Econometrica</i> 46 (1978) 1293&ndash;1301. <a href=\"https://doi.org/10.2307/1913829\">doi:10.2307/1913829</a>",
 22: "T. S. Breusch, A. R. Pagan. A simple test for heteroscedasticity and random coefficient variation. <i>Econometrica</i> 47 (1979) 1287&ndash;1294. <a href=\"https://doi.org/10.2307/1911963\">doi:10.2307/1911963</a>",
 23: "R. Koenker. A note on studentizing a test for heteroscedasticity. <i>Journal of Econometrics</i> 17 (1981) 107&ndash;112. <a href=\"https://doi.org/10.1016/0304-4076(81)90062-2\">doi:10.1016/0304-4076(81)90062-2</a>",
 24: "H. White. A heteroskedasticity-consistent covariance matrix estimator and a direct test for heteroskedasticity. <i>Econometrica</i> 48 (1980) 817&ndash;838. <a href=\"https://doi.org/10.2307/1912934\">doi:10.2307/1912934</a>",
 25: "J. M. Wooldridge. <i>Introductory Econometrics: A Modern Approach</i>, 7th ed. Cengage, Boston, 2020 (section 8.3, the special form of the White test).",
 26: "S. S. Shapiro, M. B. Wilk. An analysis of variance test for normality (complete samples). <i>Biometrika</i> 52 (1965) 591&ndash;611. <a href=\"https://doi.org/10.1093/biomet/52.3-4.591\">doi:10.1093/biomet/52.3-4.591</a>",
 27: "P. Royston. Remark AS R94: A remark on algorithm AS 181: the W-test for normality. <i>Journal of the Royal Statistical Society C (Applied Statistics)</i> 44 (1995) 547&ndash;551. <a href=\"https://doi.org/10.2307/2986146\">doi:10.2307/2986146</a>",
 28: "C. M. Jarque, A. K. Bera. Efficient tests for normality, homoscedasticity and serial independence of regression residuals. <i>Economics Letters</i> 6 (1980) 255&ndash;259. <a href=\"https://doi.org/10.1016/0165-1765(80)90024-5\">doi:10.1016/0165-1765(80)90024-5</a>",
 29: "C. M. Jarque, A. K. Bera. A test for normality of observations and regression residuals. <i>International Statistical Review</i> 55 (1987) 163&ndash;172. <a href=\"https://doi.org/10.2307/1403192\">doi:10.2307/1403192</a>",
 30: "J. B. Ramsey. Tests for specification errors in classical linear least-squares regression analysis. <i>Journal of the Royal Statistical Society B</i> 31 (1969) 350&ndash;371. <a href=\"https://doi.org/10.1111/j.2517-6161.1969.tb00796.x\">doi:10.1111/j.2517-6161.1969.tb00796.x</a>",
 31: "N. R. Draper, H. Smith. <i>Applied Regression Analysis</i>, 3rd ed. Wiley, New York, 1998. <a href=\"https://doi.org/10.1002/9781118625590\">doi:10.1002/9781118625590</a>",
 32: "J. G. MacKinnon, H. White. Some heteroskedasticity-consistent covariance matrix estimators with improved finite sample properties. <i>Journal of Econometrics</i> 29 (1985) 305&ndash;325. <a href=\"https://doi.org/10.1016/0304-4076(85)90158-7\">doi:10.1016/0304-4076(85)90158-7</a>",
 33: "J. S. Long, L. H. Ervin. Using heteroscedasticity consistent standard errors in the linear regression model. <i>The American Statistician</i> 54 (2000) 217&ndash;224. <a href=\"https://doi.org/10.1080/00031305.2000.10474549\">doi:10.1080/00031305.2000.10474549</a>",
 34: "G. E. P. Box, D. R. Cox. An analysis of transformations. <i>Journal of the Royal Statistical Society B</i> 26 (1964) 211&ndash;252. <a href=\"https://doi.org/10.1111/j.2517-6161.1964.tb00553.x\">doi:10.1111/j.2517-6161.1964.tb00553.x</a>",
 35: "R. J. Carroll, D. Ruppert. Power transformations when fitting theoretical models to data. <i>Journal of the American Statistical Association</i> 79 (1984) 321&ndash;328. <a href=\"https://doi.org/10.1080/01621459.1984.10478052\">doi:10.1080/01621459.1984.10478052</a>",
 36: "D. A. Belsley, E. Kuh, R. E. Welsch. <i>Regression Diagnostics: Identifying Influential Data and Sources of Collinearity</i>. Wiley, New York, 1980. <a href=\"https://doi.org/10.1002/0471725153\">doi:10.1002/0471725153</a>",
 37: "R. D. Cook, S. Weisberg. <i>Residuals and Influence in Regression</i>. Chapman and Hall, New York, 1982.",
 38: "A. C. Cameron, D. L. Miller. A practitioner&rsquo;s guide to cluster-robust inference. <i>Journal of Human Resources</i> 50 (2015) 317&ndash;372. <a href=\"https://doi.org/10.3368/jhr.50.2.317\">doi:10.3368/jhr.50.2.317</a>",
 39: "A. Wald. Tests of statistical hypotheses concerning several parameters when the number of observations is large. <i>Transactions of the American Mathematical Society</i> 54 (1943) 426&ndash;482. <a href=\"https://doi.org/10.1090/S0002-9947-1943-0012401-3\">doi:10.1090/S0002-9947-1943-0012401-3</a>",
 40: "R. A. Fisher. Frequency distribution of the values of the correlation coefficient in samples from an indefinitely large population. <i>Biometrika</i> 10 (1915) 507&ndash;521. <a href=\"https://doi.org/10.1093/biomet/10.4.507\">doi:10.1093/biomet/10.4.507</a>",
 41: "R. Davidson, J. G. MacKinnon. <i>Estimation and Inference in Econometrics</i>. Oxford University Press, New York, 1993 (Gauss&ndash;Newton regression tests for nonlinear models).",
 42: "T. Hastie, R. Tibshirani, J. Friedman. <i>The Elements of Statistical Learning</i>, 2nd ed. Springer, New York, 2009 (section 7.10, cross-validation). <a href=\"https://doi.org/10.1007/978-0-387-84858-7\">doi:10.1007/978-0-387-84858-7</a>",
 43: "G. Schwarz. Estimating the dimension of a model. <i>Annals of Statistics</i> 6 (1978) 461&ndash;464. <a href=\"https://doi.org/10.1214/aos/1176344136\">doi:10.1214/aos/1176344136</a>",
 44: "B. Efron, R. J. Tibshirani. <i>An Introduction to the Bootstrap</i>. Chapman &amp; Hall, New York, 1993. <a href=\"https://doi.org/10.1007/978-1-4899-4541-9\">doi:10.1007/978-1-4899-4541-9</a>",
 45: "K. Levenberg. A method for the solution of certain non-linear problems in least squares. <i>Quarterly of Applied Mathematics</i> 2 (1944) 164&ndash;168. <a href=\"https://doi.org/10.1090/qam/10666\">doi:10.1090/qam/10666</a>",
 46: "D. W. Marquardt. An algorithm for least-squares estimation of nonlinear parameters. <i>Journal of the Society for Industrial and Applied Mathematics</i> 11 (1963) 431&ndash;441. <a href=\"https://doi.org/10.1137/0111030\">doi:10.1137/0111030</a>",
 47: "S. J. Prais, C. B. Winsten. Trend estimators and serial correlation. Cowles Commission Discussion Paper: Statistics No. 383, Chicago, 1954.",
 48: "Y. Y. Haimes, L. S. Lasdon, D. A. Wismer. On a bicriterion formulation of the problems of integrated system identification and system optimization. <i>IEEE Transactions on Systems, Man, and Cybernetics</i> SMC-1 (1971) 296&ndash;297. <a href=\"https://doi.org/10.1109/TSMC.1971.4308298\">doi:10.1109/TSMC.1971.4308298</a>",
 49: "V. Chankong, Y. Y. Haimes. <i>Multiobjective Decision Making: Theory and Methodology</i>. North-Holland, New York, 1983.",
 50: "L. E. Kinsler, A. R. Frey, A. B. Coppens, J. V. Sanders. <i>Fundamentals of Acoustics</i>, 4th ed. Wiley, New York, 2000.",
 51: "[I. Newton.] Scala graduum caloris. <i>Philosophical Transactions of the Royal Society of London</i> 22 (1701) 824&ndash;829. <a href=\"https://doi.org/10.1098/rstl.1700.0082\">doi:10.1098/rstl.1700.0082</a>",
 52: "S. Seabold, J. Perktold. Statsmodels: econometric and statistical modeling with Python. <i>Proceedings of the 9th Python in Science Conference</i> (2010) 92&ndash;96. <a href=\"https://doi.org/10.25080/Majora-92bf1922-011\">doi:10.25080/Majora-92bf1922-011</a>",
 53: "P. Virtanen et al. SciPy 1.0: fundamental algorithms for scientific computing in Python. <i>Nature Methods</i> 17 (2020) 261&ndash;272. <a href=\"https://doi.org/10.1038/s41592-019-0686-2\">doi:10.1038/s41592-019-0686-2</a>",
 54: "Z. Wang, C. Bash, N. Tolia, M. Marwah, X. Zhu, P. Ranganathan. Optimal fan speed control for thermal management of servers. In: <i>Proc. ASME InterPACK 2009</i>, Vol. 2, ASME, 2009, 709&ndash;719. <a href=\"https://doi.org/10.1115/InterPACK2009-89074\">doi:10.1115/InterPACK2009-89074</a>",
 55: "D. Shin, J. Kim, N. Chang, J. Choi, S. W. Chung, E.-Y. Chung. Energy-optimal dynamic thermal management for green computing. In: <i>Proc. ICCAD 2009</i>, ACM, 2009, 652&ndash;657. <a href=\"https://doi.org/10.1145/1687399.1687520\">doi:10.1145/1687399.1687520</a>",
 56: "D. Shin, S. W. Chung, E.-Y. Chung, N. Chang. Energy-optimal dynamic thermal management: computation and cooling power co-optimization. <i>IEEE Transactions on Industrial Informatics</i> 6 (2010) 340&ndash;351. <a href=\"https://doi.org/10.1109/TII.2010.2052059\">doi:10.1109/TII.2010.2052059</a>",
 57: "R. Ayoub, R. Nath, T. Rosing. JETC: joint energy thermal and cooling management for memory and CPU subsystems in servers. In: <i>Proc. IEEE HPCA 2012</i>, 2012, 1&ndash;12. <a href=\"https://doi.org/10.1109/HPCA.2012.6169035\">doi:10.1109/HPCA.2012.6169035</a>",
 58: "X. Han, Y. Joshi. Energy reduction in server cooling via real time thermal control. In: <i>Proc. 28th IEEE SEMI-THERM</i>, 2012. <a href=\"https://doi.org/10.1109/STHERM.2012.6188829\">doi:10.1109/STHERM.2012.6188829</a>",
 59: "J. Kim, M. M. Sabry, D. Atienza, K. Vaidyanathan, K. Gross. Global fan speed control considering non-ideal temperature measurements in enterprise servers. In: <i>Proc. DATE 2014</i>, 2014, 1&ndash;6. <a href=\"https://doi.org/10.7873/DATE.2014.289\">doi:10.7873/DATE.2014.289</a>",
 60: "M. Zapater, O. Tuncer, J. L. Ayala, J. M. Moya, K. Vaidyanathan, K. Gross, A. K. Coskun. Leakage-aware cooling management for improving server energy efficiency. <i>IEEE Transactions on Parallel and Distributed Systems</i> 26 (2015) 2764&ndash;2777. <a href=\"https://doi.org/10.1109/TPDS.2014.2361519\">doi:10.1109/TPDS.2014.2361519</a>",
 61: "J. Sarkinen, R. Brannvall, J. Gustafsson, J. Summers. Experimental analysis of server fan control strategies for improved data center air-based thermal management. In: <i>Proc. 19th IEEE ITherm</i>, 2020, 341&ndash;349. <a href=\"https://doi.org/10.1109/ITherm45881.2020.9190337\">doi:10.1109/ITherm45881.2020.9190337</a>",
 62: "E. Pakbaznia, M. Pedram. Minimizing data center cooling and server power costs. In: <i>Proc. ISLPED 2009</i>, ACM, 2009, 145&ndash;150. <a href=\"https://doi.org/10.1145/1594233.1594268\">doi:10.1145/1594233.1594268</a>",
 63: "L. Huang. Characterizing computer cooling fan noise. <i>Journal of the Acoustical Society of America</i> 114 (2003) 3189&ndash;3200. <a href=\"https://doi.org/10.1121/1.1624074\">doi:10.1121/1.1624074</a>",
 64: "R. H. Lyon, A. E. Bergles. Noise and cooling in electronics packages. <i>IEEE Transactions on Components and Packaging Technologies</i> 29 (2006) 535&ndash;542. <a href=\"https://doi.org/10.1109/TCAPT.2006.880512\">doi:10.1109/TCAPT.2006.880512</a>",
 65: "P. P. Nagrani, A. Alfoqaha, D. Demetriou, S. Bard. Multiphysics thermal-acoustic modeling of a server in a data center. In: <i>Proc. 21st IEEE ITherm</i>, 2022, 1&ndash;7. <a href=\"https://doi.org/10.1109/iTherm54085.2022.9899616\">doi:10.1109/iTherm54085.2022.9899616</a>",
 66: "N. Cerkovnik, J. Murovec, T. Novakovi&#263;, J. Prezelj. A psychoacoustic evaluation and predictive model for computer axial fan sound quality. <i>Applied Acoustics</i> 237 (2025) 110749. <a href=\"https://doi.org/10.1016/j.apacoust.2025.110749\">doi:10.1016/j.apacoust.2025.110749</a>",
 67: "H. Fastl, E. Zwicker. <i>Psychoacoustics: Facts and Models</i>, 3rd ed. Springer, Berlin, 2007. <a href=\"https://doi.org/10.1007/978-3-540-68888-4\">doi:10.1007/978-3-540-68888-4</a>",
 68: "D. Brooks, M. Martonosi. Dynamic thermal management for high-performance microprocessors. In: <i>Proc. 7th IEEE HPCA</i>, 2001, 171&ndash;182. <a href=\"https://doi.org/10.1109/HPCA.2001.903261\">doi:10.1109/HPCA.2001.903261</a>",
 69: "J. W. Sheaffer, K. Skadron, D. P. Luebke. Studying thermal management for graphics-processor architectures. In: <i>Proc. IEEE ISPASS 2005</i>, 2005. <a href=\"https://doi.org/10.1109/ISPASS.2005.1430559\">doi:10.1109/ISPASS.2005.1430559</a>",
 70: "X. Mei, Q. Wang, X. Chu. A survey and measurement study of GPU DVFS on energy conservation. <i>Digital Communications and Networks</i> 3 (2017) 89&ndash;100. <a href=\"https://doi.org/10.1016/j.dcan.2016.10.001\">doi:10.1016/j.dcan.2016.10.001</a>",
 71: "A. Krzywaniak, P. Czarnul, J. Proficz. GPU power capping for energy-performance trade-offs in training of deep convolutional neural networks for image recognition. In: <i>Computational Science &ndash; ICCS 2022</i>, LNCS, Springer, 2022, 667&ndash;681. <a href=\"https://doi.org/10.1007/978-3-031-08751-6_48\">doi:10.1007/978-3-031-08751-6_48</a>",
 72: "D. Zhao, S. Samsi, J. McDonald, B. Li, D. Bestor, M. Jones, D. Tiwari, V. Gadepally. Sustainable supercomputing for AI: GPU power capping at HPC scale. In: <i>Proc. ACM SoCC 2023</i>, 2023, 588&ndash;596. <a href=\"https://doi.org/10.1145/3620678.3624793\">doi:10.1145/3620678.3624793</a>",
 73: "W. Huang, S. Ghosh, S. Velusamy, K. Sankaranarayanan, K. Skadron, M. R. Stan. HotSpot: a compact thermal modeling methodology for early-stage VLSI design. <i>IEEE Transactions on VLSI Systems</i> 14 (2006) 501&ndash;513. <a href=\"https://doi.org/10.1109/TVLSI.2006.876103\">doi:10.1109/TVLSI.2006.876103</a>",
 74: "C. J. M. Lasance. Ten years of boundary-condition-independent compact thermal modeling of electronic parts: a review. <i>Heat Transfer Engineering</i> 29 (2008) 149&ndash;168. <a href=\"https://doi.org/10.1080/01457630701673188\">doi:10.1080/01457630701673188</a>",
 75: "lm-sensors project. fancontrol(8): automated software based fan speed regulation. <a href=\"https://github.com/lm-sensors/lm-sensors\">github.com/lm-sensors</a>",
 76: "Rem0o. FanControl: a highly customizable fan controlling software for Windows. <a href=\"https://github.com/Rem0o/FanControl.Releases\">github.com/Rem0o/FanControl.Releases</a>",
 77: "T. E. Dewey, M. Irwin, S. Lai, S. Y. K. Li (NVIDIA Corp.). Techniques for controlling computing performance for power-constrained multi-processor computing systems. US Patent 12,130,687 B2, 2024. <a href=\"https://patents.google.com/patent/US12130687B2/en\">patents.google.com</a>",
}
c = lambda *n: "".join(f' <a class="cite" href="#s{i}">[{i}]</a>' for i in n)
# (phrase at first use, refs, optional plain sentence appended after the phrase's sentence)
FIRST = [
 ("A first-order response is fitted to each temperature:", (51, 10, 11)),
 ("Noise from several fans adds on an energy basis", (50,)),
 ("With 95&nbsp;% bootstrap intervals over the points:", (44,)),
 ("t-test", (16,)),
 ("Shapiro&ndash;Wilk does not reject normality", (26, 27)),
 ("Durbin&ndash;Watson", (17, 18)),
 ("nonlinear least squares (Levenberg&ndash;Marquardt)", (45, 46)),
 ("five-fold cross-validation", (42,)),
 ("heteroscedasticity-consistent (HC3) standard errors", (24, 32, 33)),
 ("Cluster-robust errors by session", (38,)),
 ("Bayesian information criterion (BIC)", (43,)),
 ("The Box&ndash;Cox profile, transforming both sides,", (34, 35)),
 ("Monte Carlo under the null given the regressors", (19,)),
 ("studentised residual", (36, 37)),
 ("lack-of-fit test against the pure error of repeated points", (31,)),
 ("generalised least squares", (47,)),
 ("We trace it with the &epsilon;-constraint method", (48, 49)),
 ("Sources add on an energy basis", (50,)),
 ("A proportional-integral term", (15,)),
]
s = F.read_text()
# reference list: replace everything after s15 up to the end of that list
for k, v in REFS.items():   # update in place or append to the reference list; never drop other entries
    if f'<li id="s{k}">' in s: s = re.sub(rf'<li id="s{k}">.*?</li>', lambda m: f'<li id="s{k}">{v}</li>', s, count=1, flags=re.S)
    else:
        e = s.index("</ol>", s.index('<h2 id="sources">')); s = s[:e] + f'<li id="s{k}">{v}</li>' + s[e:]
body_end = s.index('</article>'); miss = []
GL = (s.find('ar-gl"'), s.find("</table>", s.find('ar-gl"')))
for ph, refs in FIRST:  # noqa
    i = s.find(ph)
    while i >= 0 and GL[0] >= 0 and GL[0] < i < GL[1]: i = s.find(ph, i + 1)
    if i < 0 or i > body_end: miss.append(ph); continue
    j = i + len(ph); tag = c(*refs)
    if f'<a class="cite" href="#s{refs[0]}">' not in s[j:j + 120]: s = s[:j] + tag + s[j:]; body_end += len(tag)
s = re.sub(r'\.((?: <a class="cite" href="#[tns]\d+">\[[^\]]*\]</a>)+)(?=\s|<)', r"\1.", s)   # citation before the full stop
F.write_text(s)
used = set(map(int, re.findall(r'href="#s(\d+)"', s)))
print("missing anchors:", miss); print("refs never cited:", sorted(set(REFS) - used))
# --- table width: text column by default; the 980 px wide box only where the content cannot fit the column (measured 2026-10-23)
def ncols(head):
    first = re.search(r"<tr>(.*?)</tr>", head, re.S).group(1)
    return sum(int((re.search(r'colspan="(\d+)"', t) or [0, 1])[1]) for t in re.findall(r"<th[^>]*>", first))
def wide(cls, head):
    th = re.sub(r"<[^>]+>", "", re.search(r"<th[^>]*>(.*?)</th>", head, re.S).group(1)).strip(); n = ncols(head)
    return n >= 8 or "ar-s3" in cls or "ar-iso" in cls or th in ("Fan control",) or (th == "Constant" and n >= 7)
def fix(m):
    cls, head = m.group(2), m.group(3)
    return f'<div class="ar-tw{" ar-tw-wide" if wide(cls, head) else ""}">{m.group(1)}<table class="{cls}"{m.group(4)}>{head}'
s = F.read_text()
s, k = re.subn(r'<div class="ar-tw(?: ar-tw-wide)?">(\s*)<table class="([^"]*)"([^>]*)>(\s*(?:<caption>.*?</caption>\s*)?<thead>.*?</thead>)', lambda m: fix(type("M", (), {"group": lambda self, i: [None, m.group(1), m.group(2), m.group(4), m.group(3)][i]})()), s, flags=re.S)
F.write_text(s); print("tables laid out:", k, "wide:", s.count('class="ar-tw ar-tw-wide"'))
# --- plain-language terms under every table (Seb 2026-10-23): explained in the note directly after the table
TERMS = [
 (r"\bTctl\b", "Tctl", "the processor&rsquo;s overall temperature as AMD reports it"),
 (r"\bCCD\b", "CCD 1/2", "the two chiplets that hold the processor cores"),
 (r"\bPackage\b", "Package", "the electrical power the whole processor draws"),
 (r"\bPL\b", "Power limit (PL)", "the share of the card&rsquo;s maximum power, 575&nbsp;W, that it may use"),
 (r"\bmeas\.", "meas.", "measured; the column beside it (sim. or model) is computed by our model for the same conditions"),
 (r"dBA", "dBA", "A-weighted sound pressure level in decibels"),
 (r"reversals", "Reversals/min", "how often per minute the fans switch between speeding up and slowing down"),
 (r"\bRMSE\b", "RMSE", "root-mean-square error, the typical size of the gap between model and measurement"),
 (r"Leave-one-out", "Leave-one-out", "the error when each point is predicted by the model fitted without that point"),
 (r"5-fold", "5-fold", "the same with a fifth of the points left out at a time"),
 (r"Leave session out", "Leave session out", "the same with a whole session left out at a time"),
 (r"\bBIC\b", "BIC", "Bayesian information criterion: lower is better, with a penalty for every extra constant"),
 (r"\bDW\b|Durbin", "DW (Durbin&ndash;Watson)", "near 2 the residuals are independent; below 2 they run in streaks"),
 (r"\bSE\b", "SE", "standard error, the uncertainty of an estimate"),
 (r"HC3", "HC3", "a standard error that stays valid when the scatter of the residuals is uneven"),
 (r"cluster", "Cluster", "a standard error that allows correlated errors within a session or series"),
 (r"95&nbsp;% interval|95 % interval", "95&nbsp;% interval", "the range that holds the true value with 95&nbsp;% confidence"),
 (r"<th[^>]*>p</th>", "p", "the chance of a result at least this extreme if the null hypothesis were true; below 0.05 we reject it"),
 (r"Verdict on the null", "Null", "the hypothesis that the model is adequate in the tested respect"),
 (r"\bLOO\b", "LOO", "leave-one-out error, as above"),
 (r"[Hh]ot spot", "Hot spot", "the hottest point on the GPU die"),
 (r"NVML|NVAPI", "NVML, NVAPI", "NVIDIA&rsquo;s two driver interfaces for reading the sensors"),
 (r"Intake air", "Intake air", "the temperature of the air entering the case"),
 (r"\bctrl[123]\b", "ctrl1&ndash;ctrl3", "our three controller test runs on the card, 22 October"),
 (r"\bcpu[23]\b", "cpu2, cpu3", "our processor test runs"),
 (r"SilentPCReview", "SilentPCReview class", "the noise class on the SilentPCReview scale"),
 (r"R<sup>2</sup>|R\^2", "R&sup2;", "the share of the variation the model explains"),
 (r"θ|&theta;", "&theta;", "a fixed temperature offset that does not depend on power"),
]
s = F.read_text(); s = re.sub(r' ?<span class="ar-terms">.*?</span>', "", s, flags=re.S)
out, pos, n = [], 0, 0
for m in re.finditer(r'<div class="ar-tw[^"]*">\s*<table[^>]*>(.*?)</table>\s*</div>', s, re.S):
    tab = m.group(1); head = (re.search(r"<thead>(.*?)</thead>", tab, re.S) or [None, ""])[1] if re.search(r"<thead>", tab) else ""
    firstcol = " ".join(re.findall(r"<tr><td[^>]*>(.*?)</td>", tab))
    hay = head + " " + firstcol
    after = re.match(r'\s*<p class="ar-note[^"]*"[^>]*>(.*?)</p>', s[m.end():], re.S); after = after.group(1).lower() if after else ""
    found = [f"{lab}: {txt}" for rx, lab, txt in TERMS if re.search(rx, hay) and lab.lower().split("/")[0].split(" ")[0] + ":" not in after]
    if 'ar-cmp2' in m.group(0)[:300] or re.match(r"\s*(<tr>)?\s*<th[^>]*>\s*(Method|Constant|Fan control)", head): found = []   # row labels already spell the terms out
    out.append(s[pos:m.end()]); pos = m.end()
    if not found: continue
    span = f' <span class="ar-terms">Terms: {"; ".join(found)}.</span>'; n += 1
    nxt = re.match(r'(\s*<p class="ar-note[^"]*">)(.*?)(</p>)', s[pos:], re.S)
    if nxt: out.append(s[pos:pos + nxt.end(2)] + span + nxt.group(3)); pos += nxt.end()
    else: out.append(f'\n  <p class="ar-note">{span.strip()}</p>')
out.append(s[pos:]); F.write_text("".join(out)); print("terms added to", n, "tables")
# --- one quantity given as % and rpm: one spanning header, units in the cells (Seb 2026-10-23)
def pct_rpm(m):
    t = m.group(0); hd = re.search(r"<thead><tr>(.*?)</tr></thead>", t, re.S)
    if not hd: return t
    first = hd.group(1).split("</tr><tr>")[0]
    ths = re.findall(r"<th[^>]*>.*?</th>", first, re.S)
    names = [re.sub(r"<[^>]+>", "", x).strip() for x in ths]
    for j in range(len(names) - 1):
        a, b = names[j], names[j + 1]
        if a.endswith(", %") and b.endswith(", rpm") and a[:-3] == b[:-5] and "colspan" not in ths[j] + ths[j + 1]:
            rs = ' rowspan="2"' if 'rowspan="2"' in ths[j] else ""
            ths2 = ths[:j] + [f'<th scope="colgroup" colspan="2"{rs}>{a[:-3]}</th>'] + ths[j + 2:]
            t = t.replace(first, "".join(ths2), 1)
            def row(r):
                cells = re.findall(r"<td[^>]*>.*?</td>", r.group(1), re.S)
                if len(cells) <= j + 1: return r.group(0)
                for k, u in ((j, "%"), (j + 1, "rpm")):
                    cells[k] = re.sub(r"^(<td[^>]*>)([\d.]+)((?:<sup>[a-z]</sup>)?</td>)$", rf"\1\2&nbsp;{u}\3", cells[k])
                return "<tr>" + "".join(cells) + "</tr>"
            t = re.sub(r"<tr>(.*?)</tr>", lambda r: row(r) if "<td" in r.group(1) else r.group(0), t, flags=re.S)
            break
    return t
s_ = F.read_text(); s_ = re.sub(r"<table[^>]*>.*?</table>", pct_rpm, s_, flags=re.S); F.write_text(s_)
# --- text columns left-aligned, numeric columns right-aligned (decided per column from the body cells)
NUMC = re.compile(r"^[\s~<>&;a-z]*?(?:&asymp;|&lt;|&gt;|&le;|&ge;|&minus;|[-+~&#;0-9.,%/()\s]|&nbsp;|&deg;C|&rarr;|dBA|rpm|MHz|W|s|min|°C|&mdash;|&#9670;|<sup>[a-z]</sup>|<br>|<span[^>]*>|</span>)*$")
def align(m):
    t = m.group(0)
    if "colspan" in t or "rowspan" in t: return t
    rows = re.findall(r"<tr>(.*?)</tr>", re.search(r"<tbody>(.*?)</tbody>", t, re.S).group(1), re.S) if "<tbody>" in t else []
    if not rows: return t
    cells = [re.findall(r"<td[^>]*>(.*?)</td>", r, re.S) for r in rows]; n = max(len(c) for c in cells)
    txt = set()
    for j in range(1, n):
        col = [re.sub(r"<a [^>]*>.*?</a>", "", c[j]).strip() for c in cells if len(c) > j]
        col = [v for v in col if v not in ("&mdash;", "—", "", "&middot;", "&ndash;")] or ["0"]
        if sum(1 for v in col if not NUMC.match(v)) > len(col) / 2: txt.add(j)
    def mark(row, tag):
        k = [-1]
        def f(mm):
            k[0] += 1
            if k[0] in txt and 'class="tl"' not in mm.group(0): return mm.group(0)[:-1] + ' class="tl">' if " class=" not in mm.group(0) else mm.group(0).replace(' class="', ' class="tl ')
            return mm.group(0)
        return re.sub(rf"<{tag}(?: [^>]*)?>", f, row)
    t = re.sub(r"<tr>.*?</tr>", lambda r: mark(mark(r.group(0), "td"), "th"), t, flags=re.S)
    return t
s_ = F.read_text(); s_ = re.sub(r' class="tl"', "", s_); s_ = s_.replace('class="tl ', 'class="')
s_ = re.sub(r"<table[^>]*>.*?</table>", align, s_, flags=re.S); F.write_text(s_)
# --- a value, its unit, note letter and citations never break apart
s_ = F.read_text(); s_ = re.sub(r'<span class="nw">(.*?)</span><!--nw-->', r"\1", s_, flags=re.S)
s_ = re.sub(r'(?<=>)((?:&asymp;|~)?[\d.,&ndash;&minus;+]+(?:&nbsp;(?:&deg;C|rpm|W|dBA|%|s|MHz))?(?:<sup>[a-z]</sup>)?(?:\s*<a class="cite"[^>]*>\[[^\]]+\]</a>)+)', r'<span class="nw">\1</span><!--nw-->', s_)
F.write_text(s_)
# --- journal-style tables (Seb 2026-10-23): "Table N." + caption above (what, why, which dimension), a lead sentence in the text,
#     groups numbered N a, b, c ...; {tref:key} in the text becomes a link "Table N". Captions from generators (ar-tcap without data-auto) are kept.
REG = [  # (regex on header key, key, caption title or None = keep the generator's, lead sentence; {T} = "Table N")
 (r"^Symbol¦", "vars", "Quantities of the test and their roles: what we set, what we only measure, and what the card returns.", "{T} lists the quantities; the role column separates what the test sets from what it only observes."),
 (r"^Card¦Generation", "limits", "Published temperature limits of NVIDIA GPUs by generation, core and memory: the basis for the limits we work to.", "{T} compares the published limits across generations; note how few memory limits are published at all."),
 (r"^Sensor¦", "static7", "First fit of the static model (7) for each sensor at 575&nbsp;W, first run: how strongly each fan set cools each sensor.", "{T} gives the fitted constants per sensor; the ratio a/b says how much more the GPU fans matter than the case fans."),
 (r"^Time after the change, s¦Share", "settle", "Share of a temperature step completed a given time after a change of fans or power, for a first-order response with &tau; = 50&nbsp;s: why a reading must wait.", "{T} shows how slowly a step completes; a reading after 20&nbsp;s has seen only a third of the change."),
 (r"^Case fans, rpm¦GPU fans", "run2", "Second run, 21 October: core and memory temperature over case fan speed (rows) and GPU fan speed (columns) at two power limits, the effect of both fan sets and of power.", "{T} gives the measured grid of the second run at the highest and the lowest power limit; read down a column for the case fans and along a row for the GPU fans."),
 (r"^Time after the change, min¦Small", "early", "Early reading minus settled value, core temperature, val1 validation series (21 October, evening): how long a point must run.", "{T} shows how far a reading after 1 to 5 minutes still lies from the settled value, for small and large steps."),
 (r"^GPU fans(?:, %¦GPU fans, rpm)?¦Core rise per 100", "per100", "Core temperature rise per 100&nbsp;W of board power, by GPU fan speed, from models (9), (10) and (11): the effect of power at fixed fans.", "{T} compares the three models&rsquo; slope against power; they agree within about 1&nbsp;&deg;C per 100&nbsp;W."),
 (r"^GPU fans, %¦Run time", "s3plan", "Plan of the final grid (steady3) by GPU fan speed: points, run time, predicted core range and the largest step between consecutive points.", "{T} summarises the plan of the final grid; the largest steps show where settling takes longest."),
 (r"^GPU fans(?:, %¦GPU fans, rpm)?¦Estimated level at 1&nbsp;m, dBA¦(?:Sebastian|Class on our)", "gpuclass", "GPU fan speeds of the final grid with their estimated noise at 1&nbsp;m and their class on our RTX 5090 scale ({tref:gpuclassrange}).", "{T} links each GPU fan speed of the grid to an estimated level and a noise class."),
 (r"^Case and radiator fans, rpm¦Estimated level", "caseclass", "Case and radiator fan levels of the final grid, chosen as listening classes for this machine at the desk, with the literature-based level of one fan and of all seven.", "{T} explains why the case and radiator fans are measured at these seven speeds: each is one listening class."),
 (r"^Method¦", "methods", "Statistical methods and terms used in this article, with what each does and why we use it.", "{T} is a glossary of the statistical methods; each is cited where first used."),
 (r"^Constant¦Unit¦Estimate¦Standard error, in", "consts11", "Constants of the settled-point model (11), fitted to the settled points of the earlier sessions, with four kinds of standard error.", "{T} gives each constant with its uncertainty; compare the columns to see how much the choice of standard error matters."),
 (r"^Form of R", "forms", "Candidate forms of the fan-response term R(N,&nbsp;C), all with session offsets, compared by fit and by prediction error: why we chose two parallel conductances.", "{T} ranks the forms; prediction errors (leave-one-out, 5-fold, leave session out) matter more than the fit error."),
 (r"^Test¦Statistic", "tests", "Statistical tests on the residuals of model (11): which assumptions of the fit hold.", "{T} lists each test with its verdict; the rejected ones are discussed below it."),
 (r"^Variant¦", "variants", "Sensitivity of model (11) to the core reading and to the form: fit error and Durbin&ndash;Watson along the GPU fans.", "{T} tests the causes of the residual pattern; only a richer form moves Durbin&ndash;Watson towards 2."),
 (r"^GPU fans¦Case and radiator fans¦800", "s3", "Final grid (steady3, 23 October): measured core and memory temperature against the model, over GPU fans (rows) and case and radiator fan listening classes (columns), one table per power limit and quantity: the primary result.", "{T} is the validation data set: compare each measured value with the model value beside it."),
 (r"^GPU fans, %¦Case fans, rpm¦Core, measured", "old", "Earlier sessions (21&ndash;22 October): every settled core point against model (11), one table per power limit: the points the model was fitted to.", "{T} shows the points of the earlier sessions behind the model; the residual is the gap between the measured and model columns."),
 (r"^Constant¦Unit¦Estimate¦Standard error$", "constsmem", "Constants of the memory model (provisional), with standard errors, fitted to the settled memory points of the earlier sessions.", "{T} gives the memory model; its large offset &theta;<sub>0,mem</sub> is discussed below."),
 (r"^GPU fans(?:, %¦GPU fans, rpm)?¦Core(?:, &deg;C| temperature)¦Memory", "cmp", "Second run, all 112 settings: core and memory after 60&nbsp;s, settled, and from the model, by case fan speed and power limit: how far the 60-second readings were off.", "{T} sets the 60-second readings of the second run beside the settled and model values."),
 (r"^Class \(SilentPCReview\)", "spcr", "Noise classes after SilentPCReview for one source at 1&nbsp;m, with everyday comparisons: the reference scale; the article&rsquo;s own classes are in {tref:caseclass} and {tref:gpuclassrange}.", "{T} gives the published reference scale for computer noise."),
 (r"^Fan¦Speed at which", "hwb", "120 and 140&nbsp;mm fans: speed at which each reaches a given noise level, free field at 1&nbsp;m (Hardware Busters): the basis of the case-fan noise model.", "{T} shows that premium fans reach each level within a few hundred rpm of one another."),
 (r"^Fan on a radiator", "tpu", "120&nbsp;mm fans on a radiator: noise at four speeds, at 15&nbsp;cm (TechPowerUp): a check of the case-fan model on a radiator.", "{T} gives radiator-mounted levels; they differ by about 1&nbsp;dB between fans."),
 (r"^Source¦Distance", "reviews", "RTX 5090 Founders Edition noise in published reviews: distance, room floor and result, the basis of the GPU-fan noise model.", "{T} collects the review measurements of the card; mind the different distances."),
 (r"^GPU fans(?:, %¦GPU fans, rpm)?¦Estimated level at 1&nbsp;m, dBA¦Estimated level at 0.5", "gpuest", "RTX 5090 FE fans: estimated noise at 1&nbsp;m and 0.5&nbsp;m by fan speed, from the GPU-fan noise model.", "{T} gives the estimated level of the card&rsquo;s fans at each speed."),
 (r"^Class¦GPU fans, %", "gpuclassrange", "Noise classes applied to the RTX 5090 FE fans: the fan-speed range of each class.", "{T} turns the noise classes into fan-speed ranges for this card."),
 (r"^Card¦Setting¦Fan speed", "rtx50", "Other RTX 50 cards in reviews: fan speeds, levels and fan stop at idle, for comparison with the RTX 5090 FE.", "{T} compares other RTX 50 cards; most are louder at equal speed."),
 (r"^Speed of a 120", "sebscale", "Sebastian&rsquo;s listening scale for a 120&nbsp;mm case fan against published measurements, a qualitative comparison: does the ear agree with the meter?", "{T} checks each listening class against measurements; most agree."),
 (r"^Mode \(first version\)", "v1noise", "First version of the controller: estimated noise at the fan-speed ceilings of its modes, at 1&nbsp;m.", "{T} shows that in the first version the card&rsquo;s fans set the noise in Quiet and Balanced."),
 (r"^Quantity¦Points¦Mean error", "valid", None, "{T} gives the out-of-sample accuracy of the estimated equations."),
 (r"^Mode \(budget, dBA\)¦Intake air", "proom", None, "{T} gives the power limit each mode settles at in a warmer room."),
 (r"^Parameter¦Unit¦Core \(R1\)", "params", None, "{T} lists the estimated parameters behind the control law."),
 (r"^Mode¦Noise budget", "modes", None, "{T} is the definition of the modes: read across a row to see the fans each budget allows and the temperatures that result at each power limit."),
 (r"^Mode¦Core target, &deg;C¦GPU fan ceiling", "v1modes", "First version of the controller (superseded): modes defined by a core target, with fan-speed ceilings and limits.", "{T} records the first, temperature-target design for comparison."),
 (r"^Fan control¦", "sim", None, "{T} compares the simulated controller with the factory fan curve in four tests; look at noise first, then at the temperatures."),
 (r"^Mode \(target\)¦", "hw", "The first controller version on the real RTX 5090 against its simulation, open case, intake about 19.3&nbsp;&deg;C, 22 October: how well the model predicts the controlled card.", "{T} sets the first version on the real card beside its simulation; the closer each pair, the better the model."),
 (r"^Mode¦GPU fan reversals", "pump", "Fan pumping under 60-second load bursts on the real card in three controller runs, ctrl1, ctrl2 and ctrl3: the effect of the corrections.", "{T} shows the fan reversals falling to zero over the three runs."),
 (r"^Quantity¦Radiator fans at full speed", "cpu2", None, "{T} answers one question: does slowing the radiator fans heat the processor?"),
 (r"^Radiator fans, rpm¦Radiator control", "cpu3", None, "{T} goes further: both sets of fans slow, down to the radiator fans&rsquo; floor."),
 (r"^Core target, &deg;C¦Power limit 100", "pareto", "Quietest fan settings for each core target at 575&nbsp;W and 402&nbsp;W, intake 19.3&nbsp;&deg;C (model, literature-based noise): the effect of the target on noise.", "{T} reads the frontier at fixed targets; at 402&nbsp;W the fans are already at their floor."),
 (r"^Mode at 575 W NOTUSED", "paretomodes", "Quietest fan settings for the core targets of the first version&rsquo;s modes at 575&nbsp;W, intake 19.3&nbsp;&deg;C (model, literature-based noise).", "{T} places the first version&rsquo;s modes on the frontier."),
 (r"^Intake air(?:, &deg;C)?¦Core target", "pmax", "Quietest total noise at each power limit for core targets of 77 and 80&nbsp;&deg;C, at two room temperatures (model, literature-based noise): the effect of power and of room temperature on noise.", "{T} shows what lowering the power limit buys in noise, in a cool and in a warm room."),
 (r"^Case and radiator fans, rpm¦Listening class", "iso", None, "{T} shows the many settings that give one temperature; look down each noise column for marker c, the quietest setting."),
]
TNO = lambda n: f'<span class="tno">Table {n}.</span> '
s = F.read_text()
s = s.replace('<div class="ar-tblock ar-tblock-wide">', "").replace('<div class="ar-tblock">', "").replace("</div><!--/tblock-->", "")
assert "<details" not in s.split("</style>", 1)[1], "tables must never be hidden in <details> (Seb 2026-10-23)"
s = re.sub(r'(?::root\[data-theme="dark"\] (?:#ar )?)?\.ar-det[^{]*\{[^}]*\}', "", s)
s = re.sub(r'<p class="ar-(?:tcap|lead)" data-auto="1"[^>]*>.*?</p>\s*', "", s, flags=re.S)
s = re.sub(r'<span class="tno">[^<]*</span> ', "", s); s = re.sub(r' <span class="tdesc">.*?</span><!--tdesc-->', "", s, flags=re.S)
s = re.sub(r'(<p class="ar-tcap"[^>]*?) id="table-[\dA-Za-z]+"', r"\1", s); s = re.sub(r'(<p class="ar-tcap"[^>]*?) id="table-[\dA-Za-z]+"', r"\1", s)
s = re.sub(r'<span class="tgl">[^<]*</span> ', "", s)
s = re.sub(r'\n?  <p class="ar-note" data-copy="1">.*?</p>', "", s, flags=re.S)
# sub-tables become separate tables: an <h4> or <caption> directly above/inside a table turns into its own caption
s = re.sub(r'<h4 class="ar-h4"[^>]*>(.*?)</h4>(\s*<div class="ar-tw)', r'<p class="ar-tcap" data-sub="1"><b>\1</b></p>\2', s, flags=re.S)
def capout(m):
    return f'<p class="ar-tcap" data-sub="1"><b>{m.group(3)}</b></p>\n  {m.group(1)}{m.group(2)}'
s = re.sub(r'(<div class="ar-tw[^"]*">\s*)(<table[^>]*>)\s*<caption>(.*?)</caption>', capout, s, flags=re.S)
items = []
for m in re.finditer(r'<div class="ar-tw[^"]*">\s*<table[^>]*>(.*?)</table>\s*</div>', s, re.S):
    head = re.sub(r'<span class="katex-html".*?</span></span></span>|<annotation.*?</annotation>', "", (re.search(r"<thead>(.*?)</thead>", m.group(1), re.S) or [0, ""])[1], flags=re.S)
    key = "¦".join(re.sub(r"<[^>]+>", "", x).strip() for x in re.findall(r"<th[^>]*>(.*?)</th>", head, re.S))
    reg = next((r for r in REG if re.search(r[0], key)), None)
    if not reg: raise SystemExit(f"no table registry entry for: {key[:60]}")
    items.append((m.start(), m.end(), reg))
num, out_n, prev, letters = 0, [], None, {}
for st, en, reg in items:
    if reg[1] != prev: num += 1; letters[num] = 0
    letters[num] += 1; out_n.append((st, en, reg, num, letters[num])); prev = reg[1]
APOS = sorted((m.start(), m.group(1).upper()) for m in re.finditer(r'<h2 id="appendix-([a-z])"', s))
def appx(pos):
    a = [L for p_, L in APOS if p_ <= pos]; return a[-1] if a else ""
disp, cnt_by = {}, {}
for st, en, reg, n, l in out_n:
    if n in disp: continue
    px = appx(st); cnt_by[px] = cnt_by.get(px, 0) + 1; disp[n] = f"{px}{cnt_by[px]}"
gsize = dict(letters)
lab = lambda n, l: disp[n] if gsize[n] == 1 else f"{disp[n]}{chr(64 + l) if not disp[n][0].isalpha() else chr(96 + l)}"
REF = {}
for st, en, reg, n, l in out_n: REF.setdefault(reg[1], (n, lab(n, l)))
ins = []
for st, en, reg, n, l in out_n:
    pre = s[max(0, st - 1500):st]; base = st - len(pre)
    k0 = pre.rfind('<p class="ar-tcap"'); pre = pre[k0:] if k0 >= 0 else ""; base = st - len(pre)
    cap = re.search(r'(<p class="ar-tcap"( data-sub="1")?>)(.*?)</p>\s*$', pre, re.S)
    tl = lab(n, l)
    rng = f"Table {disp[n]}" if gsize[n] == 1 else f"Tables {lab(n, 1)}&ndash;{lab(n, gsize[n])}"
    ltxt = reg[3]
    if gsize[n] > 1: ltxt = re.sub(r"\{T\} (?!is\b)(\w+?)s\b", r"{T} \1", re.sub(r"\{T\} is\b", "{T} are", ltxt))
    lead = f'<p class="ar-lead" data-auto="1">{ltxt.replace("{T}", f"<a href=\"#table-{tl}\">{rng}</a>")}</p>\n  '
    if cap:
        p0 = base + cap.start()
        if l == 1: ins.append((p0, lead))
        ins.append((p0 + len('<p class="ar-tcap"'), f' id="table-{tl}"'))
        ins.append((base + cap.end(1), TNO(tl)))
    else:
        if reg[2] is None: raise SystemExit(f"no caption for table {tl} ({reg[1]})")
        ins.append((st, (lead if l == 1 else "") + f'<p class="ar-tcap" data-auto="1" id="table-{tl}">{TNO(tl)}<b>{reg[2]}</b></p>\n  '))
# group members without their own note get a copy of the group's note
for n in [k for k, v in gsize.items() if v > 1]:
    mem = [(st, en) for st, en, reg, nn, l in out_n if nn == n]
    last_en = mem[-1][1]; mm = re.match(r'(\s*<p class="ar-note[^"]*">.*?</p>)+', s[last_en:], re.S)
    if not mm: continue
    notes = re.findall(r'<p class="ar-note[^"]*">(.*?)</p>', mm.group(0), re.S)
    txt = " ".join(notes)
    for st, en in mem[:-1]:
        if not re.match(r'\s*<p class="ar-note', s[en:]): ins.append((en, f'\n  <p class="ar-note" data-copy="1">{txt}</p>'))
for pos, txt in sorted(ins, key=lambda x: x[0], reverse=True): s = s[:pos] + txt + s[pos:]
s = re.sub(r"\{tref:(\w+)\}", lambda m: f'<a href="#table-{REF[m.group(1)][1]}">Table {REF[m.group(1)][1]}</a>' if m.group(1) in REF else m.group(0), s)
def letters_fix(m):
    t = m.group(0)
    if "*" not in t and "&dagger;" not in t: return t
    t = re.sub(r"<sup>\*</sup>|\*(?![^<]*>)", "<sup>a</sup>", t); t = t.replace("<sup>&dagger;</sup>", "<sup>b</sup>").replace("&dagger;", "<sup>b</sup>")
    return t
s = re.sub(r'<div class="ar-tw[^"]*">\s*<table.*?</table>\s*</div>(?:\s*<p class="ar-note[^"]*">.*?</p>)?', letters_fix, s, flags=re.S)
s = s.replace("(marked *)", "(marked <sup>a</sup>)")
F.write_text(s); print("tables numbered:", len(disp), "appendix:", sum(1 for v in disp.values() if v[0].isalpha()), "groups:", sum(1 for v in gsize.values() if v > 1))

# --- one flat panel per table block: caption + table(s) + notes (Swiss: no shadow, no radius)
s = F.read_text()
s = s.replace('<div class="ar-tblock ar-tblock-wide">', "").replace('<div class="ar-tblock">', "").replace("</div><!--/tblock-->", "")
caps = [(m.start(), m.group(1)) for m in re.finditer(r'<p class="ar-tcap"[^>]*id="table-([A-Z]?\d+[A-Za-z]?)"', s)]
wr = []
for k, (st, n) in enumerate(caps):
    lim = caps[k + 1][0] if k + 1 < len(caps) else len(s)
    lim = min(lim, *(x for x in (s.find("<h2", st), s.find("<h3", st), s.find('<p class="ar-lead"', st + 10)) if x > 0), len(s))
    ends = [m.end() for m in re.finditer(r"</table>\s*</div>", s[st:lim])]
    if not ends: continue
    e = st + ends[-1]
    while True:
        mm = re.match(r'\s*<p class="ar-note[^"]*"[^>]*>.*?</p>', s[e:], re.S)
        if not mm: break
        e += mm.end()
    wide = 'ar-tw-wide' in s[st:e]
    wr.append((st, e, wide))
for st, e, wide in reversed(wr):
    s = s[:e] + "</div><!--/tblock-->" + s[e:]
    s = s[:st] + f'<div class="ar-tblock{" ar-tblock-wide" if wide else ""}">' + s[st:]
F.write_text(s); print("table panels:", len(wr))

s = F.read_text()
# header cells: "Name, unit" -> name on one line, unit on the next
UNIT = r"(?:&deg;C|rpm|%|dBA|W|s|h|MHz|n|per min|m&deg;C/W|W/&deg;C|dBA at 1&nbsp;m|&deg;C per 100&nbsp;W)"
s = re.sub(r'(<th[^>]*>)([^<]{2,40}?), (' + UNIT + r')(</th>)', lambda m: f'{m.group(1)}<span class="hn{"" if len(m.group(2)) <= 14 else " hw"}">{m.group(2)}</span><br>{m.group(3)}{m.group(4)}', s)
F.write_text(s)

# --- figures: "Figure N." + bold title, then the description (Seb 2026-10-23); same flat panel as tables (CSS)
FIGT = [
 (r"The test set-up, side view|Air enters through three 120", "Test set-up (side view, not to scale).", " Legend: arrows, airflow; bars, fans; &#9679; T<sub>in</sub>, the air temperature sensor; f<sub>g</sub>, f<sub>c</sub>, the GPU and case fan speeds."),
 (r"The grid as run on the first night", "The first-night measurement grid.", ""),
 (r"Hot-spot temperature at 575", "Hot-spot temperature over both fan speeds at 575&nbsp;W.", ""),
 (r"Interactive surfaces", "Interactive temperature surfaces at 575&nbsp;W.", ""),
 (r"Memory against core temperature", "Memory against core temperature at 575&nbsp;W.", ""),
 (r"Graphics clock against GPU fan speed", "Graphics clock against GPU fan speed at 575&nbsp;W.", ""),
 (r"Hot spot against board power", "Hot spot against board power at fixed fan speeds.", ""),
 (r"Core \(solid\) and memory \(dashed\) against GPU fan speed", "Second run: core and memory over GPU fans, case fans and power limit.", ""),
 (r"Core against GPU fan speed in rpm", "Settled core against GPU fan speed, with model (11).", ""),
 (r"Core against case fan speed", "Settled core against case fan speed, with model (11).", ""),
 (r"The second run, used for training", "Dynamic model on its training run.", ""),
 (r"Runs the core model was not fitted to", "Dynamic model on runs it was not fitted to.", ""),
 (r"The planned path of steady3", "Planned measurement path of the final grid (steady3).", ""),
 (r"Residuals of equation", "Residual diagnostics of model (11).", ""),
 (r"controller in simulation", "The controller in simulation.", ""),
 (r"The controller on the real card", "The first controller version on the real card.", ""),
 (r"Full processor load", "Processor temperatures as the radiator fans slow.", ""),
 (r"Settled core against total noise", "The quiet frontier: settled core against total fan noise.", ""),
 (r"Highest power with the core", "Highest power within a noise budget.", ""),
 (r"Total noise of all fans at 1&nbsp;m against the speed of the case", "Noise needed to hold 70&nbsp;&deg;C, by case fan speed and power limit.", ""),
 (r"Planned fan speeds of the released controller", "The control law: fan speeds, noise and predicted core of each mode against power.", ""),
 (r"WS.Sensor graphics-card cooling panel", "The WS.Sensor graphics-card cooling panel.", ""),
 (r"coupling matrix for two cards", "Two cards in one case: coupling and feed-forward.", ""),
]
s = F.read_text()
s = re.sub(r' <b class="ftitle">.*?</b>', "", s); s = re.sub(r'<span class="flegend">.*?</span><!--fl-->', "", s, flags=re.S)
miss = []
def figfix(m):
    cap = m.group(2); t = next(((ti, lg) for rx, ti, lg in FIGT if re.search(rx, cap)), None)
    if not t: miss.append(re.sub(r"<[^>]+>", "", cap)[:50]); return m.group(0)
    return f'{m.group(1)} <b class="ftitle">{t[0]}</b>{cap}' + (f'<span class="flegend">{t[1]}</span><!--fl-->' if t[1] else "")
s = re.sub(r'(<figcaption><b>Figure [A-Z]?\d+\.</b>)(.*?)(?=</figcaption>)', figfix, s, flags=re.S)
F.write_text(s); print("figure titles; untitled:", miss)

# --- the glossary's method-name cells carry no citations (the references column has them)
s = F.read_text()
def glfix(m):
    return re.sub(r'(<tr><td[^>]*>)(.*?)(</td>)', lambda r: r.group(1) + re.sub(r' ?<a class="cite"[^>]*>\[[^\]]*\]</a>', "", r.group(2)) + r.group(3), m.group(0))
s = re.sub(r'<table class="ar-tab ar-txt ar-wrap ar-gl">.*?</table>', glfix, s, flags=re.S)
F.write_text(s)
# --- remove repeated citation runs left by earlier runs: "[a] [b] [a] [b]" -> "[a] [b]"
s = F.read_text()
CIT = r'(?: ?<a class="cite" href="#[tns]\d+">\[[^\]]*\]</a>)'
def dedup(m):
    links = re.findall(r'<a class="cite" href="#([tns]\d+)">\[[^\]]*\]</a>', m.group(0)); seen = []
    for k in links:
        if k not in seen: seen.append(k)
    lead = " " if m.group(0).startswith(" ") else ""
    return lead + " ".join(f'<a class="cite" href="#{k}">[{k}]</a>' for k in seen)
s = re.sub(CIT + "{2,}", dedup, s)
F.write_text(s)
# --- one numbered reference list, in order of first citation (Elsevier numeric); in-section source lists are folded into it
s = F.read_text()
items = {}
for m in re.finditer(r'<li id="([tns]\d+)">(.*?)</li>', s, re.S):
    items.setdefault(m.group(1), re.sub(r'^\s*<span class="ar-tn">[^<]*</span>\s*', "", m.group(2)))
s = re.sub(r'\s*<ol class="ar-src ar-src-t">.*?</ol>', "", s, flags=re.S)
ra = s.index('<h2 id="sources">'); rb = s.index("</ol>", ra) + 5
body = s[:ra]; tail = s[rb:]
norm = lambda t: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", t)).strip().lower()
seen_txt = {}
for k in list(items):   # identical entries under two ids: keep the first, point the second to it
    n_ = norm(items[k])
    if n_ in seen_txt:
        body = body.replace(f'href="#{k}"', f'href="#{seen_txt[n_]}"'); tail = tail.replace(f'href="#{k}"', f'href="#{seen_txt[n_]}"'); del items[k]
    else: seen_txt[n_] = k
import json as _j0
WT = _j0.load(open(Path(__file__).parent / "webtitles.json"))
def webtitle(k, t):   # web source: author/organisation, real page title, site, year, full URL, access date
    w = WT.get(k)
    if not w or not w.get("title") or "doi" in t.lower(): return t
    u = re.search(r'href="(https?://[^"]+)"', t)
    if not u: return t
    esc = lambda x: _html.escape(x, quote=False) if x else x
    head = ". ".join(x for x in [esc(w.get("author")) if w.get("author") and w.get("author") != w.get("site") else None, f"<i>{esc(w['title'].rstrip('.'))}</i>", ", ".join(x for x in [esc(w.get("site")), w.get("year")] if x)] if x)
    return f'{head}. <a href="{u.group(1)}">{u.group(1)}</a>. Accessed 23 October 2026.'
def webfix(t):   # full URL as link text, access date for web sources without a DOI
    t = re.sub(r'<a href="(https?://[^"]+)">([a-z0-9.-]+\.[a-z]{2,})</a>', lambda m: f'<a href="{m.group(1)}">{m.group(1)}</a>', t)
    if "doi" not in t.lower() and "Accessed" not in t and re.search(r'href="https?://', t): t = t.rstrip() + " Accessed 23 October 2026."
    return t
items = {k: webfix(webtitle(k, v)) for k, v in items.items()}
order = []
for m in re.finditer(r'<a class="cite" href="#([tns]\d+)">', body + tail):
    if m.group(1) not in order and m.group(1) in items: order.append(m.group(1))
# references never cited are left out (Elsevier: every listed reference is cited)
numof = {k: i + 1 for i, k in enumerate(order)}
fix = lambda t: re.sub(r'<a class="cite" href="#([tns]\d+)">\[[^\]]*\]</a>', lambda m: f'<a class="cite" href="#{m.group(1)}">[{numof.get(m.group(1), "?")}]</a>', t)
refs = "\n".join(f'    <li id="{k}">{items[k]}</li>' for k in order)
s = fix(body) + '<h2 id="sources">References</h2>\n  <ol class="ar-src ar-refs">\n' + refs + "\n  </ol>" + fix(tail)
F.write_text(s); print("references:", len(order), "cited:", sum(1 for k in order if re.search(rf'href="#{k}"', body + tail)))
# --- status labels: the noise caveat is stated once in Section 2.5.4
s = F.read_text()
for rx in [r" ?Literature-based, provisional until our own sound map\.", r" ?Literature-based noise, provisional\.", r";? ?literature-based noise, provisional", r" ?provisional until our own sound map"]:
    s = re.sub(rx, "", s)
F.write_text(s)
# --- journal structure: heading levels and titles (generators emit their own levels), numbering 1, 1.1, 1.1.1; appendices A, A.1
HEADMAP = {
 "setup": ("h3", "Test machine and set-up"), "variables": ("h4", "Quantities measured"), "templimits": ("h3", "Operating limits"),
 "memlimit": ("h3", "Memory and core: the binding limit"), "uncertainty": ("h3", "Sensors, logging and uncertainty"),
 "grid": ("h3", "Measurement protocol"), "s-settling-and-extrapolation": ("h4", None), "s-checking-the-extrapolation": ("h4", None),
 "s-safety-limits": ("h4", None), "s-repeats-and-drift": ("h4", None), "method-next": ("h4", "The final grid (steady3)"),
 "resistance": ("h4", "Thermal resistance: one number per setting"), "model": ("h4", "A model of the cooler"),
 "s-what-we-do-not-assume": ("h5", None), "run2-dyn": ("h4", "A dynamic model"), "dyn-results": ("h3", "Dynamic model"),
 "controller": ("h3", "Controller design"), "controller-modes": ("h4", "Modes defined by a noise budget"), "controller-mem": ("h4", "Memory temperature limit"),
 "steady3-grid": ("h3", "Validation data (steady3)"), "stats": ("h3", "Model fit and diagnostics"),
 "stats-methods": ("h4", "Methods and terms"), "stats-model": ("h4", "The model"), "stats-forms": ("h4", "Forms and transforms tried"),
 "stats-tests": ("h4", "Tests on the residuals"), "stats-open": ("h4", "An open item: residuals along the GPU fans"), "stats-sessions": ("h4", "Sessions"),
 "stats-mem": ("h3", "Memory model"), "pareto": ("h3", "Noise&ndash;temperature frontier"), "pareto-lit": ("h4", "A first frontier, from the literature"),
 "iso-temp": ("h4", "One temperature, many settings"), "power": ("h3", "Power and room temperature"),
 "s-what-the-simulation-shows": ("h4", "In simulation"), "controller-hw": ("h4", "On the real card"), "controller-fix": ("h4", "Stopping the pumping"),
 "cpu": ("h3", "The processor"), "cpu-low": ("h4", "Both sets of fans slow"),
 "limits": ("h3", "Limitations"), "multi": ("h3", "Coupling of two cards"), "s-acting-before-the-temperature-rises": ("h4", None),
 "results": ("h3", "First run (20 to 21 October)"), "s-the-cards-own-fans-dominate": ("h4", None), "core-mem": ("h4", None), "clocks": ("h4", None),
 "settling": ("h4", None), "s-repeatability": ("h4", None), "power-results": ("h4", None),
 "run2": ("h3", "Second run (21 October)"), "s-what-the-second-run-shows": ("h4", None), "s-how-settled-these-points-are": ("h4", None),
 "run2-settle": ("h4", None), "run2-model": ("h3", "The first static fit"), "method-log": ("h3", "How the method was refined"),
 "s-20-to-21-october-a-fast-grid": ("h4", None), "s-21-october-morning-looking-by-hand": ("h4", None), "s-21-october-afternoon-a-bigger-grid-and-i": ("h4", None),
 "s-fitting-the-whole-time-series": ("h4", None), "s-21-to-22-october-evening-and-night-valid": ("h4", None),
 "s-22-october-statistics-on-settled-points": ("h4", None), "s-in-numbers": ("h4", None), "stats-112": ("h3", "All 112 points of the second run"),
 "stats-data": ("h3", "Earlier sessions (21 to 22 October)"), "controller-v1": ("h3", "Temperature targets"),
 "noise": ("h3", "How loud is loud"), "noise-scale": ("h4", None), "noise-fans": ("h4", None), "noise-gpu": ("h4", None), "noise-rtx50": ("h4", None),
 "noise-seb": ("h4", None), "noise-ctl": ("h4", None), "sources": ("h2", "References"),
}
UNNUM = {"data-availability", "contributions", "competing", "sources", "tools"}
s = F.read_text()
s = re.sub(r'<span class="secno">[^<]*</span> ', "", s)
def remap(m):
    tag, attrs, txt = m.group(1), m.group(2), m.group(3)
    hid = re.search(r'id="([^"]+)"', attrs)
    if hid and hid.group(1) in HEADMAP:
        nt, ti = HEADMAP[hid.group(1)]; return f"<{nt}{attrs}>{ti or txt}</{nt}>"
    return m.group(0)
s = re.sub(r"<(h[2-5])((?:\s[^>]*)?)>(.*?)</\1>", remap, s, flags=re.S)
body_a = s.index('<h2 id="intro">'); body_b = s.index("</article>")
part = s[body_a:body_b]; cnt = [0, 0, 0]; app = None; toc = []
def slug(t): return "s-" + re.sub(r"[^a-z0-9]+", "-", re.sub(r"<[^>]+>|&[a-z]+;", "", t).lower()).strip("-")[:40]
def num(m):
    global app
    tag, attrs, txt = m.group(1), m.group(2), m.group(3)
    hid = re.search(r'id="([^"]+)"', attrs); hv = hid.group(1) if hid else slug(txt)
    if not hid: attrs += f' id="{hv}"'
    if tag == "h5" or 'class="foot-h"' in attrs: return m.group(0) if hid else f"<{tag}{attrs}>{txt}</{tag}>"
    lvl = int(tag[1]) - 2
    if tag == "h2":
        txt = re.sub(r"^Appendix [A-Z]\. ", "", txt)
        if hv.startswith("appendix-"):
            app = hv[-1].upper(); cnt[1:] = [0, 0]; no = app; txt = f"Appendix {app}. {txt}"
            toc.append((tag, "", hv, re.sub(r"<[^>]+>", "", txt))); return f"<h2{attrs}>{txt}</h2>"
        if hv in UNNUM: toc.append((tag, "", hv, re.sub(r"<[^>]+>", "", txt))); return f"<h2{attrs}>{txt}</h2>"
        cnt[0] += 1; cnt[1:] = [0, 0]; no = f"{cnt[0]}"
    elif tag == "h3": cnt[1] += 1; cnt[2] = 0; no = f"{app or cnt[0]}.{cnt[1]}"
    else: cnt[2] += 1; no = f"{app or cnt[0]}.{cnt[1]}.{cnt[2]}"
    toc.append((tag, no, hv, re.sub(r"<[^>]+>", "", txt)))
    return f'<{tag}{attrs}><span class="secno">{no}</span> {txt}</{tag}>'
part = re.sub(r"<(h[2-5])((?:\s[^>]*)?)>(.*?)</\1>", num, part, flags=re.S)
s = s[:body_a] + part + s[body_b:]
lis = "".join(f'<li><a href="#{h}">' + (f'<span class="secno">{no}</span> ' if no else "") + f"{t}</a></li>" for tag, no, h, t in toc if tag == "h2")
s = re.sub(r'(<nav class="ar-toc"[^>]*>\s*<h2 class="ar-toc-h">Contents</h2>\s*<ul>).*?(</ul>)', lambda m: m.group(1) + lis + m.group(2), s, count=1, flags=re.S)
SECNO = {h: no for tag, no, h, t in toc if no}
APPNO = {h: t.split(".")[0] for tag, no, h, t in toc if h.startswith("appendix-")}
def secref(m):
    h, txt = m.group(1), m.group(2)
    if "<span" in txt or (re.match(r"\s*(Table|Figure|Section|Appendix|\d)", txt) and not re.fullmatch(r"(Section [\d.]+|Appendix [A-Z][\d.]*)", txt.strip())): return m.group(0)
    if h in SECNO: return f'<a href="#{h}">{"Appendix " + SECNO[h] if SECNO[h][0].isalpha() else "Section " + SECNO[h]}</a>'
    if h in APPNO: return f'<a href="#{h}">{APPNO[h]}</a>'
    return m.group(0)
ba = s.index('<main')
s = s[:ba] + re.sub(r'<a href="#([a-z0-9-]+)">(.*?)</a>', secref, s[ba:], flags=re.S)
# grammar around numbered references produced from link text
NOUN = {"run2": "second run", "run2-model": "first static fit", "settling": "first run", "run2-dyn": "dynamic model", "results": "first run",
        "power-results": "first run", "run2-settle": "second run"}
L = r'(<a href="#([a-z0-9-]+)">((?:Section|Appendix) [A-Z0-9.]+)</a>)'
s = re.sub(r"\(section " + L + r"\)", r"(\1)", s)
s = re.sub(r"\b(under) " + L, r"in \2", s)
def the(m):
    art, link, h = m.group(1), m.group(2), m.group(3)
    return f"{art} {NOUN[h]} ({link})" if h in NOUN else (link if art in ("the", "The") else f"{art} {link}")
s = re.sub(r"\b(the|The) " + L, lambda m: the(m) if not m.group(0).startswith("The") else "The " + NOUN.get(m.group(3), "") + f" ({m.group(2)})" if m.group(3) in NOUN else the(m), s)
s = re.sub(L + r" report as", r"\1 reports as", s)
F.write_text(s); print("sections numbered:", cnt[0], "headings:", len(toc))

# --- figures: ids from their titles, numbered in order of appearance; "Figure N" in the text becomes a link that follows the number
s = F.read_text()
def fkey(t): return "fig-" + re.sub(r"[^a-z0-9]+", "-", re.sub(r"<[^>]+>|&[a-z]+;", "", t).lower()).strip("-")[:40]
figs = list(re.finditer(r'<figure([^>]*)>(.*?)</figure>', s, re.S))
old2key, order = {}, []
for m in figs:
    cap = re.search(r'<figcaption><b>Figure ([A-Z]?\d+)\.</b> <b class="ftitle">(.*?)</b>', m.group(2), re.S)
    if not cap: continue
    k = fkey(cap.group(2)); old2key.setdefault(cap.group(1), k); order.append(k)
APOS = sorted((m.start(), m.group(1).upper()) for m in re.finditer(r'<h2 id="appendix-([a-z])"', s))
kpos = {}
for m in figs:
    cap = re.search(r'<b class="ftitle">(.*?)</b>', m.group(2), re.S)
    if cap: kpos[fkey(cap.group(1))] = m.start()
new, cnt_f = {}, {}
for k in order:
    px = "".join(L for p_, L in APOS if p_ <= kpos[k])[-1:] ; cnt_f[px] = cnt_f.get(px, 0) + 1; new[k] = f"{px}{cnt_f[px]}"
def figtag(m):
    cap = re.search(r'<b class="ftitle">(.*?)</b>', m.group(2), re.S)
    if not cap: return m.group(0)
    k = fkey(cap.group(1)); attrs = re.sub(r'\s*id="fig-[^"]*"', "", m.group(1))
    body = re.sub(r'<figcaption><b>Figure [A-Z]?\d+\.</b>', f'<figcaption><b>Figure {new[k]}.</b>', m.group(2), count=1)
    return f'<figure{attrs} id="{k}">{body}</figure>'
s = re.sub(r'<figure([^>]*)>(.*?)</figure>', figtag, s, flags=re.S)
s = re.sub(r'<a class="fref" href="#(fig-[^"]+)">(Figure )?[^<]*</a>', lambda m: f'<a class="fref" href="#{m.group(1)}">{m.group(2) or ""}{new.get(m.group(1), "?")}</a>', s)
s = re.sub(r"\{fref:(fig-[a-z0-9-]+)\}", lambda m: f'<a class="fref" href="#{m.group(1)}">Figure {new.get(m.group(1), "?")}</a>', s)
def plain(m):   # plain references outside captions and links, written with the numbering of their own generator
    k = old2key.get(m.group(1))
    return f'<a class="fref" href="#{k}">Figure {new[k]}</a>' if k else m.group(0)
parts = re.split(r"(<figcaption>.*?</figcaption>|<a [^>]*>.*?</a>|<title>.*?</title>|<meta[^>]*>|<script.*?</script>)", s, flags=re.S)
def plain2(m):
    k1, k2 = old2key.get(m.group(1)), old2key.get(m.group(2))
    if not (k1 and k2): return m.group(0)
    return f'Figures <a class="fref" href="#{k1}">{new[k1]}</a> and <a class="fref" href="#{k2}">{new[k2]}</a>'
s = "".join(p if i % 2 else re.sub(r"(?<![\w>])Figure (\d+)(?!\d)", plain, re.sub(r"Figures (\d+) and (\d+)", plain2, p)) for i, p in enumerate(parts))
F.write_text(s); print("figures numbered:", len(order))

# --- equations numbered in order of appearance (appendix: A1, B1 ...); text references follow by the original label
import html as _html, json as _json, subprocess as _sp
s = F.read_text()
def span_end(t, i):
    d = 0
    for m in re.finditer(r"<span\b|</span>", t[i:]):
        d += 1 if m.group(0) == "<span" else -1
        if d == 0: return i + m.end()
    raise ValueError("unbalanced span")
eqs = []
for m in re.finditer(r'(<span class="eqw" data-eq="(\w+)">)?<span class="katex-display">', s):
    st = m.start(); ks = m.start() + (len(m.group(1)) if m.group(1) else 0); ke = span_end(s, ks)
    en = ke + (len("</span>") if m.group(1) and s.startswith("</span>", ke) else 0)
    ann = re.search(r'<annotation encoding="application/x-tex">(.*?)</annotation>', s[ks:ke], re.S)
    if not ann: continue
    tex = _html.unescape(ann.group(1)); tg = re.search(r"\\tag\{([^}]*)\}", tex)
    orig = m.group(2) or (tg.group(1) if tg else None)
    if not orig or not re.fullmatch(r"\d+", orig): continue
    eqs.append((st, en, orig, tex))
APOS = sorted((m.start(), m.group(1).upper()) for m in re.finditer(r'<h2 id="appendix-([a-z])"', s))
newno, cnt_e = {}, {}
for st, en, orig, tex in eqs:
    px = "".join(L for p_, L in APOS if p_ <= st)[-1:]; cnt_e[px] = cnt_e.get(px, 0) + 1; newno.setdefault(orig, f"{px}{cnt_e[px]}")
texs = ["$$" + re.sub(r"\\tag\{[^}]*\}", lambda m_: "\\tag{" + newno[orig] + "}", tex) for st, en, orig, tex in eqs]
rend = _json.loads(_sp.run(["node", str(Path(__file__).parent / "tex.js")], input=_json.dumps(texs), capture_output=True, text=True, check=True).stdout)
for (st, en, orig, tex), h in sorted(zip(eqs, rend), key=lambda x: -x[0][0]):
    s = s[:st] + f'<span class="eqw" data-eq="{orig}">{h}</span>' + s[en:]
# references in the text (outside math): plain ones carry the original label; eqref spans are renumbered
s = re.sub(r'<span class="eqref" data-eq="(\w+)">\([^)]*\)</span>', lambda m: f'<span class="eqref" data-eq="{m.group(1)}">({newno.get(m.group(1), m.group(1))})</span>', s)
WORD = r"(equations?|Equations?|model|fit|form|eq\.|Eq\.|law|residuals of|Solving|solving|evaluate|as in|of)"
def textfix(t):
    t = re.sub(WORD + r"(\s+)\((\d+)\)", lambda m: f'{m.group(1)}{m.group(2)}<span class="eqref" data-eq="{m.group(3)}">({newno.get(m.group(3), m.group(3))})</span>' if m.group(3) in newno else m.group(0), t)
    for _ in range(3):
        t = re.sub(r'(<span class="eqref" data-eq="\w+">\([^)]*\)</span>)(,? and |, |&ndash;| to | or )\((\d+)\)', lambda m: f'{m.group(1)}{m.group(2)}<span class="eqref" data-eq="{m.group(3)}">({newno.get(m.group(3), m.group(3))})</span>' if m.group(3) in newno else m.group(0), t)
    return t
parts = re.split(r'(<span class="katex(?:-display)?">.*?</math></span>|<annotation.*?</annotation>|<script.*?</script>|<style.*?</style>)', s, flags=re.S)
s = "".join(p_ if i % 2 else textfix(p_) for i, p_ in enumerate(parts))
F.write_text(s); print("equations numbered:", len(eqs), {k: v for k, v in list(newno.items())})
