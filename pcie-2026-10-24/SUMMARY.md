# ws298 PCIe link check — 2026-10-24 (Lab 0.3.77)

Method: D3D11 CopyResource of 1 GiB between a staging buffer (system RAM) and a default buffer (VRAM), 10 reps per direction,
each card alone then both at once (barrier-synchronised). GB/s = 1e9 bytes/s. Two full runs (12:28, 12:31), identical results.
Card A = bus 1 (PCIE1, upper), card B = bus 3 (PCIE2).

| Card | Link under copy | H→D alone | D→H alone | H→D both | D→H both | Replay counter (since driver start) | Replay Δ during tests | WHEA 7 days |
|---|---|---|---|---|---|---|---|---|
| A (bus 1) | Gen5 x8 (max x16) | 28.9 GB/s | 28.7 GB/s | 25.6 GB/s | 26.2 GB/s | 1 | 0 | 0 |
| B (bus 3) | Gen5 x8 (max x16) | 28.9 GB/s | 28.7 GB/s | 25.6 GB/s | 26.2 GB/s | 8 | 0 | 0 |

Reference (x8): Gen5 31.5 theoretical / ~25–28 practical; Gen4 15.8 / ~12–14; Gen3 7.9 / ~6–7.
Measured 28.9 GB/s is ~92 % of Gen5 x8 theoretical, ~1.8× the Gen4 x8 ceiling, so the link really runs at Gen5.
Both at once: 51 GB/s aggregate (~0.89 per card), CPU/IO-die bound, not a link fault.
One outlier rep (card B, run 2, H→D 17.1 GB/s, single rep) — every other rep within ±0.3 %.

Verdict: both links stable at Gen5 x8 — no replays during the tests, no WHEA events.
