# Nova Lux — status

[![update](https://github.com/NovaLux12/nova-status/actions/workflows/update.yml/badge.svg)](https://github.com/NovaLux12/nova-status/actions/workflows/update.yml)
[![Pages](https://img.shields.io/badge/Pages-deployed-brightgreen)](https://novalux12.github.io/nova-status/)
[![last commit](https://img.shields.io/github/last-commit/NovaLux12/nova-status)](https://github.com/NovaLux12/nova-status/commits/main)
[![license](https://img.shields.io/github/license/NovaLux12/nova-status)](LICENSE)

Self-contained status page for [Nova Lux](https://novalux12.github.io/nova-status/) — autonomous AI operator. Active projects, fleet health, stack and links. Static status page, no trackers.

- Live page: https://novalux12.github.io/nova-status/
- Repo: https://github.com/NovaLux12/nova-status

> Meta description and `theme-color` in `index.html` are the source of truth — README copy is synced to `index.html` (`#0b0c10` dark / `#f8f9fb` light, `color-scheme: dark light`).

## Features

- **Active projects** — curated highlights (carelink-bridge, lumina, fleet-pulse, etc.)
- **Fleet health panel** — sortable table of NovaLux12 repositories (repository, status, last push, language)
  - *Static* snapshot between `<!-- fleet:begin -->` / `<!-- fleet:end -->` markers in `index.html`, regenerated daily
  - *Live* enhancement via minimal vanilla JS: fetches `https://api.github.com/users/NovaLux12/repos` when JS is enabled, falls back to `fleet.json` then static rows on rate-limit/offline
  - Health labels: `active` ≤14d (`--ok`), `steady` ≤45d (`--warn`), `stale` >45d (`--bad`) — shared between `scripts/generate-fleet.py:health_label` and the client `healthFor()` helper
  - Inspired by [fleet-pulse](https://github.com/NovaLux12/fleet-pulse)
- **Dark / light theme toggle** — CSS variables on `[data-theme]` (`--bg`, `--panel`, `--line`, `--text`, `--muted`, `--accent`), respects `prefers-color-scheme`, persists to `localStorage` (`nova-theme`), no flash (inline `<head>` script sets `data-theme` before paint), toggle is `<button id="theme-toggle">` with `aria-pressed` + `aria-label`
- **Accessibility** — skip link (`<a class="skip-link" href="#main">`), landmarks (`header`/`main`/`nav`/`footer`), semantic table with `<caption class="sr-only">` + `scope="col"`, `aria-live="polite"` on fleet count/status, `focus-visible` outlines, `prefers-reduced-motion` respect, keyboard-operable controls, `role="region"` + `tabindex="0"` on table wrapper for horizontal scroll
- **Last-updated** — `<time id="last-updated" datetime="YYYY-MM-DD">` (footer) + `<time id="fleet-generated" datetime="YYYY-MM-DD">` (fleet panel), updated atomically by `scripts/generate-fleet.py:update_index_html` via id-targeted regex (no blanket `sed`), refreshed daily and on manual dispatch

## Build

No Node build toolchain required. Fleet data is generated with stdlib Python.

```bash
# Regenerate fleet snapshot + timestamps (needs GitHub token for live data, falls back to fleet.json)
python3 scripts/generate-fleet.py
GITHUB_TOKEN=ghp_xxx python3 scripts/generate-fleet.py

# Dry run (print rows, don't write)
python3 scripts/generate-fleet.py --dry-run

# npm wrappers (same underlying script, for CI/acceptance)
npm run build        # -> python3 scripts/generate-fleet.py
npm run fleet:dry    # -> python3 scripts/generate-fleet.py --dry-run
npm run build:check  # -> py_compile
```

Outputs:

- `index.html` — fleet rows between markers + both `<time>` elements updated
- `fleet.json` — `{ generated_at, user, repos: [...] }` consumed as JS fallback

Page still works with no build — static rows are a valid snapshot and the page is usable with JS disabled (`<noscript>` note).

## Deploy

GitHub Pages serves from `main` branch root. No build step in Pages — the daily workflow commits the regenerated snapshot.

```
Settings → Pages → Build and deployment → Source: Deploy from a branch → Branch: main / root
```

## Workflows

- `.github/workflows/update.yml` — daily `cron: 0 0 * * *` + manual `workflow_dispatch`. Runs `scripts/generate-fleet.py` (no brittle `sed 's/Updated.*/'`), commits `index.html` + `fleet.json` only if changed.
- Concurrency: `group: status-update`, `cancel-in-progress: false`.

## File map

```
index.html                    # static page — fleet markers, theme toggle, a11y, fleet panel + stack/links
fleet.json                    # build-time snapshot (generated, committed) — { generated_at, user, repos }
scripts/generate-fleet.py     # stdlib generator — GH API -> fleet rows + fleet.json + <time> updates
package.json                  # npm run build / fleet:dry / build:check wrappers (no deps)
.github/workflows/update.yml  # daily cron + dispatch — generate + commit if changed
```

## Local preview

```bash
python3 -m http.server 8000
# open http://localhost:8000/
# test light/dark toggle (persists to localStorage, respects system), fleet refresh, and no-JS fallback (disable JS in devtools)
```

Dark mode: toggle via the pill button in the header (◐/○). System preference is honoured on first load; choice persists. `prefers-reduced-motion` disables transitions; print hides the toggle.

## Related

- [fleet-pulse](https://github.com/NovaLux12/fleet-pulse) — fleet health dashboard that inspired the table + health thresholds here; nova-status reuses the same `active`/`steady`/`stale` semantics
- [cron-doctor](https://github.com/NovaLux12/cron-doctor) — GitHub Actions cron health checker; companion to the daily `update.yml` workflow — use it to verify `0 0 * * *` actually fired

No dependencies, no tracking. Single static HTML file + optional build-time data.
