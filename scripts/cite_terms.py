"""Statistical/method references (s16+) and first-use citations in the GPU cooling article. Idempotent; run after every
section generator. Usage: cite_terms.py"""
import re
from pathlib import Path
F = Path.home() / "Claude/gruency-site/research/gpu-cooling-method.html"
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
}
c = lambda *n: "".join(f' <a class="cite" href="#s{i}">[{i}]</a>' for i in n)
# (phrase at first use, refs, optional plain sentence appended after the phrase's sentence)
FIRST = [
 ("settles exponentially with a time constant of about 50&nbsp;s.", (51, 10)),
 ("A first-order response is fitted to each temperature:", (10, 11)),
 ("With 95&nbsp;% bootstrap intervals over the points:", (44,)),
 ("(t-test p", (16,)),
 ("Shapiro&ndash;Wilk does not reject normality", (26, 27)),
 ("Durbin&ndash;Watson is", (17, 18)),
 ("nonlinear least squares (Levenberg&ndash;Marquardt).", (45, 46)),
 ("five-fold cross-validation gives", (42,)),
 ("heteroscedasticity-consistent (HC3) standard errors.", (24, 32, 33)),
 ("Cluster-robust errors by session", (38,)),
 ("Bayesian information criterion (BIC).", (43,)),
 ("The Box&ndash;Cox profile, transforming both sides,", (34, 35)),
 ("Monte Carlo under the null given the regressors.", (19,)),
 ("studentised residual", (36, 37)),
 ("lack-of-fit test against the pure error of repeated points", (31,)),
 ("generalised least squares,", (47,)),
 ("We trace it with the &epsilon;-constraint method", (48, 49)),
 ("Sources add on an energy basis", (50,)),
 ("A proportional-integral term", (15,)),
]
s = F.read_text()
# reference list: replace everything after s15 up to the end of that list
a = s.index('<li id="s15">'); a = s.index("</li>", a) + 5; b = s.index("</ol>", a)
s = s[:a] + "".join(f'<li id="s{k}">{v}</li>' for k, v in REFS.items()) + s[b:]
body_end = s.index('<h2 id="sources">'); miss = []
for ph, refs in FIRST:
    i = s.find(ph)
    if i < 0 or i > body_end: miss.append(ph); continue
    j = i + len(ph); tag = c(*refs)
    if s[j:j + len(tag)] != tag: s = s[:j] + tag + s[j:]; body_end += len(tag)
F.write_text(s)
used = set(map(int, re.findall(r'href="#s(\d+)"', s)))
print("missing anchors:", miss); print("refs never cited:", sorted(set(REFS) - used))
# --- table width: text column by default; the 980 px wide box only where the content cannot fit the column (measured 2026-10-23)
def ncols(head):
    first = re.search(r"<tr>(.*?)</tr>", head, re.S).group(1)
    return sum(int(m or 1) for m in re.findall(r"<th[^>]*?(?:colspan=\"(\d+)\")?[^>]*>", first))
def wide(cls, head):
    th = re.sub(r"<[^>]+>", "", re.search(r"<th[^>]*>(.*?)</th>", head, re.S).group(1)).strip(); n = ncols(head)
    return n >= 8 or "ar-s3" in cls or th in ("Source", "Mode, 60-second bursts", "Card", "Controller", "Fan control") or (th == "Constant" and n >= 7)
def fix(m):
    cls, head = m.group(2), m.group(3)
    return f'<div class="ar-tw{" ar-tw-wide" if wide(cls, head) else ""}">{m.group(1)}<table class="{cls}"{m.group(4)}>{head}'
s = F.read_text()
s, k = re.subn(r'<div class="ar-tw(?: ar-tw-wide)?">(\s*)<table class="([^"]*)"([^>]*)>(\s*<thead>.*?</thead>)', lambda m: fix(type("M", (), {"group": lambda self, i: [None, m.group(1), m.group(2), m.group(4), m.group(3)][i]})()), s, flags=re.S)
F.write_text(s); print("tables laid out:", k, "wide:", s.count('class="ar-tw ar-tw-wide"'))
# --- plain-language terms under every table (Seb 2026-10-23): explained in the note directly after the table
TERMS = [
 (r"\bTctl\b", "Tctl", "the processor&rsquo;s overall temperature as AMD reports it"),
 (r"\bCCD\b", "CCD 1/2", "the two chiplets that hold the processor cores"),
 (r"\bPackage\b", "Package", "the electrical power the whole processor draws"),
 (r"\bPL\b|[Pp]ower limit", "Power limit (PL)", "the share of the card&rsquo;s maximum power, 575&nbsp;W, that it may use"),
 (r"\bmeas\.", "meas./sim.", "measured on the card / computed by our simulation of the card"),
 (r"dBA", "dBA at 1&nbsp;m", "sound level at 1&nbsp;m"),
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
    found = [f"{lab}: {txt}" for rx, lab, txt in TERMS if re.search(rx, hay)]
    out.append(s[pos:m.end()]); pos = m.end()
    if not found: continue
    span = f' <span class="ar-terms">Terms: {"; ".join(found)}.</span>'; n += 1
    nxt = re.match(r'(\s*<p class="ar-note[^"]*">)(.*?)(</p>)', s[pos:], re.S)
    if nxt: out.append(s[pos:pos + nxt.end(2)] + span + nxt.group(3)); pos += nxt.end()
    else: out.append(f'\n  <p class="ar-note">{span.strip()}</p>')
out.append(s[pos:]); F.write_text("".join(out)); print("terms added to", n, "tables")
