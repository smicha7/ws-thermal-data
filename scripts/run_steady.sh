#!/bin/sh
# Pipeline stanu ustalonego: przelicza wszystko na plikach, które są (steady_data.py -> steady_stats.py).
# Gdy jest steady2 (>= 20 pkt), sesją odniesienia staje się steady2, a dodatkowo liczona jest analiza samego steady2.
# Użycie: ./run_steady.sh            — jednorazowo
#         ./run_steady.sh --watch    — co 10 min sprawdza data/steady2-*/grid.csv; przelicza po każdej zmianie,
#                                      kończy, gdy status.json steady2 ma "state":"done" (albo po 10 h). Log: results-2026-10-22/watch.log
cd "$(dirname "$0")"
PY=.venv/bin/python
run() {
  $PY steady_stats.py > results-2026-10-22/steady-stats.txt 2>&1
  n2=$($PY -c "import pandas as p; d=p.read_csv('results-2026-10-22/steady-points.csv'); print((d.session=='steady2').sum())")
  if [ "$n2" -ge 20 ]; then SUBSET=steady2 $PY steady_stats.py > results-2026-10-22/steady-stats-steady2.txt 2>&1; fi
  echo "$(date '+%F %T') przeliczono, steady2 = $n2 pkt" >> results-2026-10-22/watch.log
}
if [ "$1" != "--watch" ]; then run; exit; fi
last=""; end=$(( $(date +%s) + 36000 ))
while [ "$(date +%s)" -lt "$end" ]; do
  f=$(ls data/steady2-*/grid.csv 2>/dev/null | head -1)
  if [ -n "$f" ]; then
    m=$(stat -f %m "$f")
    if [ "$m" != "$last" ]; then last=$m; run; fi
    grep -q '"state":"done"' "$(dirname "$f")/status.json" 2>/dev/null && { echo "$(date '+%F %T') steady2 done — koniec" >> results-2026-10-22/watch.log; exit; }
  fi
  sleep 600
done
