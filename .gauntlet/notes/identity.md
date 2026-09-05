# Identity — design notes

The full-page shell / visual identity of the NOVA OBSERVATORY showpiece. This is the
frame every other piece slots into — the shared token language, the ambient space field,
the glass surface system, and the typographic scale.

**What I built**
- **Shared tokens** in `base/tokens.css` (and inlined in the page so it stays
  self-contained): `--bg #07080c`, `--panel rgba(255,255,255,.03)`, `--panel-solid
  #0d0f16`, `--line rgba(255,255,255,.09)`, `--text #eef0f6`, `--muted #8b93a7`,
  `--accent #e8b963` (gold), `--aurora-a #8b5cf6` (violet), `--aurora-b #2dd4bf`
  (teal), `--ok #4ade80`, `--warn #fbbf24`, `--bad #f87171`, `--font-display`,
  `--font-mono`, `--radius`, and `--glow-ok/accent/warn/bad`. Light scheme via
  `prefers-color-scheme`.
- **Ambient field:** fixed auro(a)ra light spills (radial violet/teal/gold) + a subtle
  SVG fractal-noise grain overlay (`mix-blend-mode: overlay`) + a faint 10-point starfield.
- **Glass surfaces:** 1px luminous `--line` borders on panels with soft
  `color-mix` aurora blooms inside cards; translucent header with blur + saturate.
- **Type scale:** system display stack, weight 800, tight tracking on the hero wordmark;
  `ui-monospace` for every data readout with `tabular-nums`; uppercase wide-tracked
  micro-labels for stats/section kickers.
- **Header/nav:** 'NL' monogram mark (gradient SVG), aurora wordmark, mono nav links,
  ALL SYSTEMS GO chip + theme toggle. Sticky, blurred.
- **Status summary strip:** ALL SYSTEMS OPERATIONAL hero with glow, pulsing orbital orb
  (violet→teal core, 3 orbit rings), and four uptime-style stat chips (Uptime 90d
  99.98%, Repositories 24, Stars 27, Incidents 0) — a deliberate upgrade on the bar's
  simpler summary.
- **Card grid:** 6 placeholder cards using **real** repo names & data from
  `fleet.json` (carelink-bridge, nova-status, spotify-mcp-server, fleet-pulse, lumina,
  agent-validate) with status dot, language pill, description, and mono meta row
  (stars / release / CI badge).
- **Telemetry ticker** (repos, stars, languages, CI, generated date/UTC) and a **footer**
  with monogram, © line, and nav links + note.

**Cascade fix worth remembering.** The initial build put the light tokens in
`@media (prefers-color-scheme: light) { :root { ... } }`. Because the screenshot browser
reports a *light* scheme, the light overrides won even though the theme script defaulted
to `data-theme="dark"` — the first render came out parchment, not space. Fix: scope the
media block to `:root:not([data-theme])` so an explicit/persisted theme wins, and the
dark default sticks. Verified: body bg now `rgb(7,8,12)` at render.

**Verified**
- No horizontal overflow at 1440×900 or 390×844 (scrollWidth == clientWidth).
- Dark default confirmed (`rgb(7,8,12)`). Light via `?theme=light` renders `#f4f5f9`
  with ink text and re-tinted aurora accents.
- Desktop: 3-col card grid (327px), 4-col stat strip; Mobile: 1-col card grid (351px
  full-width), nav links collapse to stacked, stats 1/2-col.
- All 6 cards, 4 stat chips, orb, nav, footer, ticker present. Monospace confirmed on
  data readouts. Self-contained: inline CSS, zero external requests, system fonts;
  progressive-enhancement JS (theme) only; motion wrapped in `prefers-reduced-motion`.
- Screenshots: `pieces/identity-check-desktop.png`, `identity-check-mobile.png`,
  `identity-check-light.png`.
