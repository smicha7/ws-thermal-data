#!/bin/bash
# Regenerate every generated part of the GPU cooling article, then the post-processor. Stops on the first error.
# All-or-nothing: the page is backed up first and restored if any step fails, so it is never left half-processed.
set -euo pipefail
F=/Users/smicha/Claude/gruency-site/research/gpu-cooling-method.html; BK=$(mktemp); cp "$F" "$BK"
trap 'rc=$?; if [ $rc -ne 0 ]; then cp "$BK" "$F"; echo "run_all: step failed (exit $rc), page restored" >&2; fi; rm -f "$BK"' EXIT
G=/Users/smicha/Applications/Pasek/research/gpu-map; cd $G
PY=$G/.venv/bin/python
# one command per line: set -e does not stop inside an && list
$PY steady3_fit.py >/dev/null
cp results-2026-10-24/steady3-fit.json /Users/smicha/Claude/gruency-site/research/data/gpu-map-steady3-fit.json
cp results-2026-10-24/steady3-points.csv /Users/smicha/Claude/gruency-site/research/data/gpu-map-steady3-points.csv
$PY model3.py >/dev/null
(cd article_tools && node stats_section.js 5 14 '{"dw":2400,"dh":1520,"dpw":1000,"dph":4200}')
$PY article_tools/steady3_section.py
(cd article_tools && node fill_wait.js)
$PY article_tools/steady3_tables.py
$PY article_tools/est3_section.py
$PY article_tools/data_tables.py
$PY article_tools/noise_section.py
$PY controller_sim.py >/dev/null
$PY fig_controller.py article_tools/out >/dev/null
cp article_tools/out/gpu-map-controller-sim-*.webp /Users/smicha/Claude/gruency-site/research/img/
$PY article_tools/modes_noise.py >/dev/null
$PY article_tools/ctrlsim_section.py 10
python3 article_tools/ctrl1_section.py 2 16
$PY article_tools/cpu_section.py 1 17
$PY noise_pareto.py article_tools/out/pareto >/dev/null
cp article_tools/out/pareto/*.webp /Users/smicha/Claude/gruency-site/research/img/
cp results-2026-10-23/noise-pareto.json /Users/smicha/Claude/gruency-site/research/data/gpu-map-noise-pareto.json
$PY iso_temp.py article_tools/out/iso >/dev/null
$PY article_tools/pareto_section.py
(cd article_tools && node fill_pareto.js)
$PY article_tools/iso_section.py 1
$PY article_tools/ctrl_law.py article_tools/out/law >/dev/null
cp article_tools/out/law/*.webp /Users/smicha/Claude/gruency-site/research/img/
$PY article_tools/ctrllaw_section.py
python3 article_tools/setup_fig.py
python3 article_tools/cite_terms.py
