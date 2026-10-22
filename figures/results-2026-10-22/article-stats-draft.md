# Statistical tests (draft, 2026-10-22)

Status: draft on the 38 settled points measured 21 October (four sessions). The dense steady2 series (22 October) is being added by the same pipeline (`run_steady.sh`). All numbers below will be recomputed when it lands. Units: °C throughout, thermal resistance in m°C/W, conductance in W/°C.

## Data
Only settled points enter the steady-state model: val1 (20), val2 (9), grid1d (1), the grid1c start point after a 660 s warm-up (1) and the 7 settled points of the night grid v2d. Each session gets its own intercept. Core temperature comes from the NVAPI sensor at 0.01 °C (1 Hz log), not from NVML, which only reports whole °C. For every point we fit an exponential approach T(t) = T∞ − A·e^(−t/τ) to the last minutes and use T∞. At card 40–45 % the points were still 0.2–0.4 °C below steady state after 8 minutes (τ ≈ 115–155 s). The rise was hidden from the settling check because its slope was computed from whole-degree readings.

## Model
T − Tin = θ0 + θ_session + P·[r∞ + 1/(gN·(N/1000)^m + gC·(C/1500)^s)]

N = GPU fan speed (rpm), C = case fan speed (rpm), P = board power (W). The heatsink conductance is modelled as two parallel paths: one driven by the card's fans and one by case airflow. This is why the case fans matter at low card speed and hardly at all at high card speed. It is estimated by nonlinear least squares (NLS, Levenberg–Marquardt).

| parameter | estimate | SE classical | SE HC3 | SE cluster (session) | SE cluster (series) |
|---|---|---|---|---|---|
| θ0 | 1.93 °C | 0.59 | 0.54 | 0.14 | 0.54 |
| r∞ | 53.9 m°C/W | 3.1 | 6.0 | 5.5 | 5.6 |
| gN | 6.4 W/°C | 1.7 | 2.9 | 2.3 | 2.2 |
| m | 2.46 | 0.43 | 0.89 | 0.78 | 0.73 |
| gC | 8.1 W/°C | 2.8 | 5.1 | 4.1 | 4.1 |
| s | 0.81 | 0.19 | 0.30 | 0.21 | 0.23 |
| θ night − val1 | +2.43 °C | 0.22 | 0.43 | 0.09 | 0.41 |
| θ val2 − val1 | +0.11 °C | 0.19 | 0.25 | 0.10 | 0.16 |

Fit: RMSE 0.37 °C, leave-one-out 0.52 °C, 5-fold CV 0.55 °C, mean residual 0.000 °C. The model is used with HC3 standard errors because Breusch–Pagan rejects homoscedasticity. Cluster-robust errors by session have only 4 clusters and are indicative only.

## Functional forms and transforms tried
All forms below were fitted with and without session intercepts. Comparison by AIC/BIC (Gaussian likelihood on the T − Tin scale, with the Jacobian term for transformed responses), exact leave-one-out (refit), 5-fold CV (10 repeats) and leave-one-session-out.

| R(N, C) form | params | RMSE | LOO | 5-fold | leave-session-out | BIC |
|---|---|---|---|---|---|---|
| power k·N^−m·C^−q | 9 | 0.56 | 0.84 | 0.88 | 1.44 | 97.1 |
| exponential k·e^(−aN)·C^−q | 9 | 0.43 | 0.63 | 0.65 | 1.33 | 77.2 |
| rational k·C^−q/(1 + bN²) | 9 | 0.53 | 0.79 | 0.82 | 1.42 | 91.9 |
| **parallel conductance** | 10 | **0.37** | **0.52** | **0.55** | 1.35 | 68.2 |
| effective airflow k·(N + bC)^−m | 9 | 0.43 | 0.56 | 0.61 | 1.35 | 76.1 |
| per-watt response R = (T − Tin)/P, conductance form | 10 | 0.37 | 0.51 | 0.54 | 1.31 | 64.1 |
| log-log: ln(T − Tin) on ln P, ln N, ln C, ln N·ln C, (ln N)², ln P·ln N | 11 | 0.34 | 0.71 | 0.73 | 1.46 | 64.4 |
| natural cubic spline in ln N (4 df) × P, with ln C terms | 12 | 0.39 | 0.80 | 0.92 | 1.34 | 79.3 |
| tensor spline R(ln N, ln C) × P | 17 | 0.13 | 8.0 | 26 | 82 | 11.9 |

- Without session intercepts every form has RMSE 0.82–0.96 °C and DW ≈ 0.1.
- The per-watt response is the same mean function with weights proportional to 1/P². It gives nearly identical estimates.
- The log-log elasticities at the mean are: P 0.95, N −0.59, C −0.08.
- A first-difference ("growth-rate") estimator along N within each (session, case speed, power limit) series removes θ0 and the session effect. On 15 pairs it gives gN = 5.7 ± 0.3 W/°C and m = 2.44 ± 0.09, which agrees with the levels fit.
- A power-curvature variant P^β gives β = 0.90 and a small gain (RMSE 0.36 °C).

## Statistical tests (chosen model)
| test | H0 | statistic | p-value | verdict |
|---|---|---|---|---|
| t-test on mean residual | E[e] = 0 | mean 0.000 °C | 1.00 | not rejected |
| Durbin–Watson, along N within (case, PL) series | no AR(1) along N | 0.42 | < 0.001 (exact, Monte Carlo) | rejected |
| Durbin–Watson, time order | no AR(1) in time | 2.49 | 0.82 | not rejected |
| Breusch–Godfrey LM, order 1 / 2, along N | no autocorrelation | 8.5 / 8.5 | 0.004 / 0.014 | rejected |
| Breusch–Godfrey LM, order 1 / 2, time within session | no autocorrelation | 3.1 / 3.4 | 0.08 / 0.18 | not rejected |
| Pearson corr(e, N / C / P / Tin / time / fitted) | ρ = 0 | −0.02 / 0.08 / 0.00 / 0.08 / 0.00 / 0.00 | ≥ 0.64 | not rejected |
| Breusch–Pagan (Koenker) on N, ln C, P | homoscedastic | 13.7 | 0.003 | rejected → HC3 |
| White (levels, squares, cross-products) | homoscedastic | 31.9 | 0.0002 | rejected → HC3 |
| White special form (ŷ, ŷ²) | homoscedastic | 1.4 | 0.50 | not rejected |
| Shapiro–Wilk | normal | W = 0.908 | 0.004 | rejected (one outlier) |
| Jarque–Bera | normal | 19.9 (skew +1.13, kurt 5.7) | < 0.001 | rejected (one outlier) |
| Shapiro–Wilk / Jarque–Bera without night point case 654 rpm (t* = +5.5) | normal | 0.956 / 1.4 | 0.15 / 0.51 | not rejected |
| Ramsey RESET (ŷ²) / (ŷ², ŷ³), Gauss–Newton form | form adequate | F = 0.80 / 1.60 | 0.38 / 0.22 | not rejected |
| Lack-of-fit F, pure error from replicates (6 df, SD 0.14 °C) | form adequate | 11.1 | 0.003 | rejected |
| Parametric vs natural-spline benchmark | parametric not worse | — | 1.00 | not rejected |
| Session intercepts = 0 (Wald, HC3) | no session effect | χ²(3) = 33.2 | < 0.001 | rejected |
| Box–Cox, transform both sides, LR λ = 1 | no transform | λ̂ = 1.65, 95 % CI [−0.95, 3.0] | 0.59 (λ = 0: 0.19) | not rejected |
| Within-session drift from repeated anchors | no drift | +0.015 °C/h | 0.51 | not rejected |

## Interpretation of the autocorrelation along N
The residuals of the parametric model still run in sign along the card-fan axis (DW 0.42). We tested three causes:

- **Sensor quantisation is not the cause.** DW is 0.51 with whole-degree NVML values, 0.40 with NVAPI 0.01 °C, and 0.42 after the settling correction.
- **Session drift is not the cause.** DW in time order is 2.49, Breusch–Godfrey in time is not significant, and the anchor drift is +0.015 °C/h.
- **Functional form is the cause.** A tensor-product spline surface R(N, C) with a P² term and session intercepts brings DW to 2.00 (Monte Carlo p = 0.50) and RMSE to 0.11 °C, close to the pure-error SD of 0.14 °C. This agrees with the lack-of-fit test.

The remaining ±0.3 °C is therefore a smooth shape error of the fan-response surface, plus a slight concavity in power. That flexible surface cannot yet be estimated reliably (LOO 8 °C, empty cells in the design), so it is a diagnostic benchmark, not the reported model.

We do not "correct" this autocorrelation with FGLS, because it is a symptom of the functional form. Prais–Winsten (ρ = 0.66) moves the estimates within their standard errors. Instead we report the parametric model with heteroscedasticity-robust (HC3) and cluster-robust standard errors. The steady2 series, a dense case-speed × power-limit grid at card 40 % plus card 60/80/100 % points and drift anchors in one session, is designed to fill those cells.

## Random-effects check
A linear mixed model with a random session intercept (REML, nonlinear shape parameters held at the NLS estimates) gives σ_session = 1.17 °C, σ_residual = 0.40 °C, ICC 0.90. The night session sits about +1.7 °C above the average session; the three day sessions sit within 0.1 °C of each other. Predicting a completely unseen session costs about 1.3 °C RMSE (leave-one-session-out). The case state on the day matters more than any remaining shape error.

## Reproducibility
`steady_data.py` (point extraction, settling fit), `steady_stats.py` (models, CV, tests, figures), `run_steady.sh` (runs both; `SUBSET=steady2` for the single-session analysis). Figures: `steady-diagnostics.png`, `steady-two-ways.png`.
