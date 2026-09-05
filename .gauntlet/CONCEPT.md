# Nova Status — Showpiece Redesign (v3) · Gauntlet Concept

**Bar (to beat blind):** Upptime live demo status site — https://demo.upptime.js.org
Screenshots: `.gauntlet/shots/bar-desktop.png` (1440×900), `.gauntlet/shots/bar-mobile.png` (390×844).
The bar is clean, light, mint/teal, incident-card based. Competent, generic open-source status page.

**Goal:** our page must win a blind A/B against the bar at desktop AND mobile, and be *unmistakably different at first glance* — a showpiece, not a reskin of the current dark/gold panel page.

## Direction: "NOVA OBSERVATORY"

A deep-space mission-control aesthetic for an autonomous AI operator. Telemetry, not dashboard.

- **Surface:** near-black space (`#07080c`-ish), layered glass panels with 1px luminous borders, subtle noise/grain, aurora light spills (violet → teal → gold) confined to hero + accents; body areas stay quiet and legible.
- **Light** (respect `prefers-color-scheme`): same architecture in a "daylight" mode — parchment-white, ink text, restrained aurora accents. Both modes must look showpiece-grade; dark is judged first but check both.
- **Type:** system font stack; display weighting from the stack (e.g. `font-weight 800`, tight tracking, uppercase micro-labels with wide letter-spacing); monospace (ui-monospace/SF Mono/Consolas) for all data readouts (numbers, UTC clock, table numeric columns).
- **Colour tokens (roadmap; identity piece refines):**
  `--bg #07080c` · `--panel rgba(255,255,255,.03)` · `--panel-solid #0d0f16` · `--line rgba(255,255,255,.09)` · `--text #eef0f6` · `--muted #8b93a7` · `--accent #e8b963` (gold) · `--aurora-a #8b5cf6` (violet) · `--aurora-b #2dd4bf` (teal) · `--ok #4ade80` · `--warn #fbbf24` · `--bad #f87171`
- **Signature elements (own them):** pulsing orbital status orb(s) in the hero; aurora gradient wordmark; telemetry ticker strip (recent activity); monospaced readouts with tabular figures; "ALL SYSTEMS OPERATIONAL" status hero with glow; subtle starfield/aurora drift animation (CSS only, reduced-motion safe); hover-glow cards; focus rings in gold.
- **Layout:** single column, max ~1080px, generous whitespace, 12px+ grid discipline; desktop 1440 and mobile 390 both must be impeccable (mobile: stack, larger touch targets, no horizontal overflow).

## Pieces (each a fully self-contained HTML file in `.gauntlet/pieces/`)

| Piece | File | What it proves |
|---|---|---|
| hero | `hero.html` | Brand mark, aurora wordmark, tagline, status hero with orb + "ALL SYSTEMS OPERATIONAL", UTC/next-build readout, theme toggle. Above-the-fold at 1440 and 390. |
| identity | `identity.html` | The full-page shell: tokens, background/aurora treatment, surfaces/glass, type scale, glow/focus rules, footer. Also writes `.gauntlet/base/tokens.css`. |
| stats | `stats.html` | Telemetry strip: repos/stars/active/steady/stale cells, language distribution bar + legend, last-build readout. |
| fleet | `fleet.html` | Fleet registry: search input, filter chips, sortable table (repo, status, last push, stars, language, latest release), status orbs, CI dots, hover states, responsive card-ization at mobile. |
| motion | `motion.html` | Signature interactions: aurora drift, orb pulse, count-up stats, hover glow, staggered entrance, ticker scroll — all reduced-motion safe, no required JS. |
| mobile | `mobile.html` | The assembled full page as it must look at 390×844: compact hero, stacked telemetry, card fleet, ticker, touch targets. |

## Data (real, from the repo)
Read `/tmp/gauntlet-status/fleet.json`, `projects.json`, `history.jsonl`, and `index.html` for real repo names, star counts, languages, push dates, releases. Never invent repo names.

## Rules for every piece
- Self-contained: inline CSS only, zero external requests (fonts/CDN blocked in the screenshot browser), system font stack, no JS required for the piece to look right in a still screenshot (progressive enhancement only).
- CSS custom properties on `:root` following the token names above (extend with `--font-display`, `--font-mono`, `--radius`, `--glow-*` as needed).
- `@media (prefers-reduced-motion: no-preference)` wraps all motion.
- Both dark and light via `prefers-color-scheme` unless the piece says otherwise.
- Impeccable at 1440×900 AND 390×844.