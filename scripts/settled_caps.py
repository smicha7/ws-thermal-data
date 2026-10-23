"""Regenerates the captions of Figures 9 and 10 (settled-point model along each fan axis) from settled-axes.json."""
import json, re
F = "/Users/smicha/Claude/gruency-site/research/gpu-cooling-method.html"; s = open(F).read()
A = json.load(open("/Users/smicha/Applications/Pasek/research/gpu-map/article_tools/out/settled-axes.json"))
J = json.load(open("/Users/smicha/Applications/Pasek/research/gpu-map/results-2026-10-22/steady-stats.json"))
S = A["stats"]
def st(k):
    q = S[k]; m = q['mean']
    return (f"For the {q['n']} points drawn, the residuals average {'&minus;' if m < -0.005 else '+' if m > 0.005 else ''}{abs(m):.2f}&nbsp;&deg;C (t-test p = {q['t_p']:.2f}) with an RMSE of {q['rmse']:.2f}&nbsp;&deg;C and at most {q['max_abs']:.1f}&nbsp;&deg;C; Shapiro&ndash;Wilk {'does not reject' if q['shapiro_p'] >= 0.05 else 'rejects'} normality (p = {q['shapiro_p']:.2f}). Along the fan axis within each series Durbin&ndash;Watson is {q['dw_along']:.2f}, the same slow run along the fans that the <a href=\"#stats-open\">statistical tests</a> report as an open item.")
common = f"Points are settled values, moved to the reference session ({J['ref']}) and the mean intake air exactly as the model moves them, so each point is its fitted value plus its residual. Lines: the settled-point model (11), fitted to all {J['n']} settled points. Below: residuals. "
cap = {9: f"<b>Figure 9.</b> Core against GPU fan speed in rpm and %, case fans at 1500&nbsp;rpm (44&nbsp;%). {common}{st('case1500')} <a href=\"/research/data/gpu-map-steady-residuals.csv\">Data (CSV)</a>.",
       10: f"<b>Figure 10.</b> Core against case fan speed in rpm and %, GPU fans at 40&nbsp;%. {common}{st('gpu40')} <a href=\"/research/data/gpu-map-steady-residuals.csv\">Data (CSV)</a>."}
for n, c in cap.items():
    a = s.index(f"<b>Figure {n}.</b>"); b = s.index("</figcaption>", a); s = s[:a] + c + s[b:]
open(F, "w").write(s); print("captions 9, 10 updated")
