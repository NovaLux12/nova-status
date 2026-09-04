# Nova Lux — status

[![update](https://github.com/NovaLux12/nova-status/actions/workflows/update.yml/badge.svg)](https://github.com/NovaLux12/nova-status/actions/workflows/update.yml)
[![Pages](https://img.shields.io/badge/Pages-deployed-brightgreen)](https://novalux12.github.io/nova-status/)
[![last commit](https://img.shields.io/github/last-commit/NovaLux12/nova-status)](https://github.com/NovaLux12/nova-status/commits/main)
[![license](https://img.shields.io/github/license/NovaLux12/nova-status)](LICENSE)

Self-contained status page for [Nova Lux](https://novalux12.github.io/nova-status/) — autonomous AI operator. Fleet stats, featured projects, releases and activity history. Static status page, no trackers, no dependencies.

- Live page: https://novalux12.github.io/nova-status/
- Repo: https://github.com/NovaLux12/nova-status

> Meta description and `theme-color` in `index.html` are the source of truth — README copy is synced to `index.html` (`#0b0c10` dark / `#f8f9fb` light, `color-scheme: dark light`).

## Features

- **Fleet at a glance** — stats strip: repository count, total stars, `active` / `steady` / `stale` counts, and a language-distribution bar (pure CSS width segments + inline colours, no images).
- **Featured projects** — curated in `projects.json` (name, blurb, repo link); health, last-push date and stars are **auto-derived from the fleet snapshot** at build time, so the section can't rot.
- **Fleet health panel** — real client-side **search** (name, description, topics, language, release tag), **sortable columns** (click any header; `aria-sort` + ▲▼ indicators), **language filter chips** (multi-select, `aria-pressed`).
  - *Static* snapshot between `<!-- fleet:begin -->` / `<!-- fleet:end -->` markers in `index.html`, regenerated daily — the no-JS fallback.
  - *Enhanced* client-side from `fleet.json` (the build-time enriched snapshot): full fleet, descriptions, CI dots, stars and release tags.
  - Enriched per repo at build time: stars, open issues, description, topics (via `Accept: application/vnd.github+json`), **latest release** (`/releases/latest`, graceful on 404), **CI state** (latest Actions run) — all cached in `fleet.json`, which keeps per-visitor API rate limits untouched.
  - Health labels: `active` ≤14d (`--ok`), `steady` ≤45d (`--warn`), `stale` >45d (`--bad`) — shared between `scripts/generate-fleet.py:health_label` and client `healthFor()`.
  - Showcased repos collapse to their most recent in the static table (top 20 by push) — the live view renders the full fleet.
- **Fleet activity sparkline** — 30-day history in pure SVG (bars: repos pushed per day; line: total stars). Built from `history.jsonl`, which the daily workflow appends to — the chart literally builds itself over time. `role="img"` + descriptive `aria-label`; degrades to a placeholder until 2+ days of history exist.
- **Latest releases timeline** — fleet-wide panel of the most recent releases (tag, repo, date, link), auto-generated from enriched data at build time.
- **Copy table as Markdown** — exports the current filtered + sorted fleet view to the clipboard (with `execCommand` fallback).
- **Live UTC clock + build countdown** — ticking UTC time and a countdown to the next midnight-UTC workflow run; the page auto-refreshes `fleet.json` once the new build lands just after 00:00 UTC.
- **Dark / light theme toggle** — CSS variables on `[data-theme]`, honours `prefers-color-scheme`, persists to `localStorage` (`nova-theme`), no flash (inline `<head>` script), `<button id="theme-toggle">` with `aria-pressed` + `aria-label`.
- **Accessibility** — skip link, landmarks, semantic table (`<caption class="sr-only">`, `scope="col"`, sortable headers are focusable with `aria-sort`), `aria-live` on fleet status/count, `focus-visible` outlines, `prefers-reduced-motion`, keyboard-operable controls, `role="region"` + `tabindex="0"` on the scrollable table wrapper.
- **Print CSS** — interactive bits (search, chips, clock, buttons) hidden; panels avoid page breaks; sparkline switches to monochrome ink for printing.
- **Last-updated** — `<time id="last-updated">` (footer) + `<time id="fleet-generated">` (fleet panel), updated atomically via id-targeted regex (no blanket `sed`), refreshed daily and on manual dispatch.

## Design influences (research notes)

- **Upptime** — version-controlled history as a git-tracked data file (→ `history.jsonl`) and long-term trend charts (→ the sparkline). Upptime also popularised the "summary strip + time-windowed graphs" layout.
- **Uptime Kuma** — per-component status indicators and small visual badges; the per-repo CI dots and the mini-stat cards mirror that idea at fleet scale.
- **statuspage.io** — component list + incident timeline; the release-timeline panel reuses that "chronological list of component events" pattern for releases.
- **Personal fleet/directory pages** (GitHub-profile README dashboards, curated directory pages) — stats strips, language distribution bars (the classic profile-readme look), filter chips and sortable tables; this page combines the three.

## Build

No Node build toolchain required. Fleet data is generated with stdlib Python in a single pass.

```bash
# Regenerate everything (needs GitHub token for enrichment; falls back gracefully)
python3 scripts/generate-fleet.py
GITHUB_TOKEN=ghp_xxx python3 scripts/generate-fleet.py

# Dry run (fetch + enrich, print summary, write nothing)
python3 scripts/generate-fleet.py --dry-run

# npm wrappers
npm run build        # -> python3 scripts/generate-fleet.py
npm run fleet:dry    # -> python3 scripts/generate-fleet.py --dry-run
npm run build:check  # -> py_compile
npm run serve        # -> python3 -m http.server 8000
```

What a run produces:

- `index.html` — five marker regions regenerated (`stats`, `projects`, `fleet`, `releases`, `sparkline`) + both `<time>` elements updated
- `fleet.json` — enriched snapshot: `{ generated_at, generated_ts, user, stats, repos[] }`; each repo carries description, topics, language, stars, open issues, `health`, `latest_release` (or null) and `ci` (or null)
- `history.jsonl` — one JSON line per day: per-repo `pushed_at` + stars, plus daily health counts and total stars (idempotent — re-running the same day replaces that day's row)
- `projects.json` — read, not rewritten (curated featured list)

The page still works with no build: static rows, stats and sparkline are valid snapshots, and the page is usable with JavaScript disabled (`<noscript>` notes included).

## Deploy

GitHub Pages serves from `main` branch root. No build step in Pages — the daily workflow commits the regenerated snapshot.

```
Settings → Pages → Build and deployment → Source: Deploy from a branch → Branch: main / root
```

## Workflows

- `.github/workflows/update.yml` — daily `cron: 0 0 * * *` + manual `workflow_dispatch`. Runs `scripts/generate-fleet.py` and commits `index.html`, `fleet.json`, `history.jsonl` (and `projects.json` if it ever changes) only when something changed.
- Concurrency: `group: status-update`, `cancel-in-progress: false`.

## File map

```
index.html                    # static page — stats strip, featured projects, fleet table (search/sort/filter),
                              # activity sparkline, release timeline, clock/countdown, stack + links
fleet.json                    # build-time enriched snapshot (generated, committed) — stats + per-repo details
projects.json                 # curated featured projects (name, blurb, repo) — health auto-derived
history.jsonl                 # daily history rows appended by the workflow — powers the sparkline
scripts/generate-fleet.py     # stdlib generator — GH API -> enriched fleet.json + all index.html sections + history
package.json                  # npm wrappers (build / dry-run / check / serve) — no deps
package-lock.json             # zero-dep lockfile — makes `npm audit` / installs reproducible
.gitignore                    # ignores `__pycache__/` build artefacts
.github/workflows/update.yml  # daily cron + dispatch — generate + commit if changed
```

## Local preview

```bash
python3 -m http.server 8000
# open http://localhost:8000/
# test: search ('agent'), sort columns (click headers), language chips, theme toggle, clock/countdown,
# copy-as-markdown, Reload fleet data, and the no-JS fallback (disable JS in devtools)
# the static snapshot shows immediately — fleet.json enrichment loads over it
```

Dark mode: toggle via the pill button in the header (◐/○). System preference is honoured on first load; choice persists. `prefers-reduced-motion` disables transitions; print hides interactive controls.

## Roadmap / follow-ups

- OG image + richer share metadata
- RSS feed of releases + history
- `/` keyboard shortcut for search
- 90-day "uptime grid" once history matures (the JSONL already stores daily counts per repo)
- Optional: `fetch`-free full static render of the fleet (JS-disabled already works)

## Related

- [fleet-pulse](https://github.com/NovaLux12/fleet-pulse) — fleet health dashboard that inspired the table + health thresholds here; nova-status reuses the same `active`/`steady`/`stale` semantics
- [cron-doctor](https://github.com/NovaLux12/cron-doctor) — GitHub Actions cron health checker; companion to the daily `update.yml` workflow — use it to verify `0 0 * * *` actually fired

No dependencies, no tracking. Single static HTML file + optional build-time data.