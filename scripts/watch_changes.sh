#!/bin/sh
# Exits (one notification) as soon as a watched file appears or changes after the marker; prints what changed.
G=/Users/smicha/Applications/Pasek/research/gpu-map; M=$G/article_tools/.marker
[ -f "$M" ] || touch "$M"
while :; do
  ch=$(find $G/results-2026-10-22 $G/data/steady2-2026-10-22 $G/data/ctrl1-2026-10-22 $G/data/cpu1-2026-10-22 $G/data/pl90-2026-10-23 $G/data/steady3-2026-10-23 $G/data/steady3-watch.md $G/NOTATKI-RECZNE-2026-10-21.md -cnewer "$M" -type f 2>/dev/null | grep -v '/cache/' | head -40)
  if [ -n "$ch" ]; then sleep 20; date '+%H:%M:%S'; find $G/results-2026-10-22 $G/data/steady2-2026-10-22 $G/data/ctrl1-2026-10-22 $G/data/cpu1-2026-10-22 $G/data/pl90-2026-10-23 $G/data/steady3-2026-10-23 $G/data/steady3-watch.md $G/NOTATKI-RECZNE-2026-10-21.md -cnewer "$M" -type f 2>/dev/null | grep -v '/cache/' | head -40; exit 0; fi
  sleep 30
done
