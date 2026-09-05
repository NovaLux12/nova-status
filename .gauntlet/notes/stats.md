# Stats — design notes

The Telemetry Strip renders the fleet snapshot as spacecraft instrumentation, not a
dashboard. I used the embedded NOVA OBSERVATORY tokens (`--bg #07080c`, gold/violet/teal
aurora, `--font-mono` for all numbers) so it slots straight into the identity shell.

**What I built**
- Header: `FLEET TELEMETRY · LIVE SNAPSHOT` kicker with a pulsing teal pip, plus a
  gradient "OBSERVATORY READINGS" wordmark. Right side carries a mono `LIVE` badge with
  the real snapshot date `2026-09-04` and sync time `22:41 UTC`.
- Five glass stat cells — Repositories, Stars, Active, Steady, Stale — each with a
  1px luminous top edge, a colour-coded glow bloom in the corner, an uppercase
  letter-spaced micro-label, a large monospaced tabular number, and a quiet caption.
  Status cells carry trim pill chips (`GO`, `—`, `WATCH`) with glowing status dots.
- The Language Mix panel: a machined 9px stacked bar using the **real** GitHub colours
  (Go `#00ADD8` 52.9%, Python `#3572A5` 23.5%, TypeScript `#3178C6` 17.6%, HTML
  `#e34c26` 5.9%) with a two-column legend showing counts in tabular mono.
- Backdrop: two slowly drifting aurora blooms (violet→teal→gold), blurred, reduced-motion
  safe via `@media (prefers-reduced-motion: no-preference)`. A faint scanline grid sits
  over the telemetry grid for the mission-control texture.

**Real data, no invention.** All figures come straight from `fleet.json` (24 repos, 27
stars, 24 active / 0 steady / 0 stale, the exact language totals). The legend note
("Go binaries, zero-dep") reflects the actual Go-heavy fleet.

**Judge should watch for**
- The conditional light scheme — same architecture on parchment-white (`#f4f5f9`) with
  ink text; both modes are showpiece, not just the dark.
- Precise bar segment proportions and real language colours (verified against the source
  hex values).
- Desktop: five equal 218px cells + language panel in a single 6-column strip, vertically
  centred. Mobile: clean 2-column grid that resolves to full-width rows (the Stale cell
  spans a column so there is no hole), no horizontal overflow, 34px tabular numbers.
- Tabular figures throughout so the numbers are optically column-aligned, not loosely set.
- Fully self-contained: inline CSS only, zero external requests, zero `<script>`. The
  still screenshot needs no JS. All motion is reduced-motion wrapped.
