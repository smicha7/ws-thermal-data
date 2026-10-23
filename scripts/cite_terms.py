"""Statistical/method references (s16+) and first-use citations in the GPU cooling article. Idempotent; run after every
section generator. Usage: cite_terms.py"""
import re
from pathlib import Path
F = Path.home() / "Claude/gruency-site/research/gpu-cooling-method.html"
REFS = {
 16: "Student [W. S. Gosset]. The probable error of a mean. Biometrika 6 (1908) 1&ndash;25.",
 17: "J. Durbin, G. S. Watson. Testing for serial correlation in least squares regression. I. Biometrika 37 (1950) 409&ndash;428.",
 18: "J. Durbin, G. S. Watson. Testing for serial correlation in least squares regression. II. Biometrika 38 (1951) 159&ndash;178.",
 19: "J.-M. Dufour, L. Khalaf. Monte Carlo test methods in econometrics. In B. H. Baltagi (ed.), A Companion to Theoretical Econometrics, chapter 23, 494&ndash;519. Blackwell, Oxford, 2001.",
 20: "T. S. Breusch. Testing for autocorrelation in dynamic linear models. Australian Economic Papers 17 (1978) 334&ndash;355.",
 21: "L. G. Godfrey. Testing against general autoregressive and moving average error models when the regressors include lagged dependent variables. Econometrica 46 (1978) 1293&ndash;1301.",
 22: "T. S. Breusch, A. R. Pagan. A simple test for heteroscedasticity and random coefficient variation. Econometrica 47 (1979) 1287&ndash;1294.",
 23: "R. Koenker. A note on studentizing a test for heteroscedasticity. Journal of Econometrics 17 (1981) 107&ndash;112.",
 24: "H. White. A heteroskedasticity-consistent covariance matrix estimator and a direct test for heteroskedasticity. Econometrica 48 (1980) 817&ndash;838.",
 25: "J. M. Wooldridge. Introductory Econometrics: A Modern Approach, 7th ed. Cengage, Boston, 2020 (section 8.3, the special form of the White test).",
 26: "S. S. Shapiro, M. B. Wilk. An analysis of variance test for normality (complete samples). Biometrika 52 (1965) 591&ndash;611.",
 27: "P. Royston. Remark AS R94: A remark on algorithm AS 181: the W-test for normality. Journal of the Royal Statistical Society C (Applied Statistics) 44 (1995) 547&ndash;551.",
 28: "C. M. Jarque, A. K. Bera. Efficient tests for normality, homoscedasticity and serial independence of regression residuals. Economics Letters 6 (1980) 255&ndash;259.",
 29: "C. M. Jarque, A. K. Bera. A test for normality of observations and regression residuals. International Statistical Review 55 (1987) 163&ndash;172.",
 30: "J. B. Ramsey. Tests for specification errors in classical linear least-squares regression analysis. Journal of the Royal Statistical Society B 31 (1969) 350&ndash;371.",
 31: "N. R. Draper, H. Smith. Applied Regression Analysis, 3rd ed. Wiley, New York, 1998.",
 32: "J. G. MacKinnon, H. White. Some heteroskedasticity-consistent covariance matrix estimators with improved finite sample properties. Journal of Econometrics 29 (1985) 305&ndash;325.",
 33: "J. S. Long, L. H. Ervin. Using heteroscedasticity consistent standard errors in the linear regression model. The American Statistician 54 (2000) 217&ndash;224.",
 34: "G. E. P. Box, D. R. Cox. An analysis of transformations. Journal of the Royal Statistical Society B 26 (1964) 211&ndash;252.",
 35: "R. J. Carroll, D. Ruppert. Power transformations when fitting theoretical models to data. Journal of the American Statistical Association 79 (1984) 321&ndash;328.",
 36: "D. A. Belsley, E. Kuh, R. E. Welsch. Regression Diagnostics: Identifying Influential Data and Sources of Collinearity. Wiley, New York, 1980.",
 37: "R. D. Cook, S. Weisberg. Residuals and Influence in Regression. Chapman and Hall, New York, 1982.",
 38: "A. C. Cameron, D. L. Miller. A practitioner&rsquo;s guide to cluster-robust inference. Journal of Human Resources 50 (2015) 317&ndash;372.",
 39: "A. Wald. Tests of statistical hypotheses concerning several parameters when the number of observations is large. Transactions of the American Mathematical Society 54 (1943) 426&ndash;482.",
 40: "R. A. Fisher. Frequency distribution of the values of the correlation coefficient in samples from an indefinitely large population. Biometrika 10 (1915) 507&ndash;521.",
 41: "R. Davidson, J. G. MacKinnon. Estimation and Inference in Econometrics. Oxford University Press, New York, 1993 (Gauss&ndash;Newton regression tests for nonlinear models).",
 42: "T. Hastie, R. Tibshirani, J. Friedman. The Elements of Statistical Learning, 2nd ed. Springer, New York, 2009 (section 7.10, cross-validation).",
 43: "G. Schwarz. Estimating the dimension of a model. Annals of Statistics 6 (1978) 461&ndash;464.",
 44: "B. Efron, R. J. Tibshirani. An Introduction to the Bootstrap. Chapman &amp; Hall, New York, 1993.",
 45: "K. Levenberg. A method for the solution of certain non-linear problems in least squares. Quarterly of Applied Mathematics 2 (1944) 164&ndash;168.",
 46: "D. W. Marquardt. An algorithm for least-squares estimation of nonlinear parameters. Journal of the Society for Industrial and Applied Mathematics 11 (1963) 431&ndash;441.",
 47: "S. J. Prais, C. B. Winsten. Trend estimators and serial correlation. Cowles Commission Discussion Paper Statistics No. 383, Chicago, 1954.",
 48: "Y. Y. Haimes, L. S. Lasdon, D. A. Wismer. On a bicriterion formulation of the problems of integrated system identification and system optimization. IEEE Transactions on Systems, Man, and Cybernetics SMC-1 (1971) 296&ndash;297.",
 49: "V. Chankong, Y. Y. Haimes. Multiobjective Decision Making: Theory and Methodology. North-Holland, New York, 1983.",
 50: "L. E. Kinsler, A. R. Frey, A. B. Coppens, J. V. Sanders. Fundamentals of Acoustics, 4th ed. Wiley, New York, 2000.",
 51: "[I. Newton.] Scala graduum caloris. Philosophical Transactions of the Royal Society 22 (1701) 824&ndash;829.",
 52: "S. Seabold, J. Perktold. Statsmodels: econometric and statistical modeling with Python. Proceedings of the 9th Python in Science Conference (2010) 92&ndash;96.",
 53: "P. Virtanen et al. SciPy 1.0: fundamental algorithms for scientific computing in Python. Nature Methods 17 (2020) 261&ndash;272.",
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
