# Nova Lux — status

Self-contained status page for Nova Lux.

- Live page: https://NovaLux12.github.io/nova-status/
- Repo: https://github.com/NovaLux12/nova-status

Zero tracking, no JS framework. Single static `index.html` + optional build-time fleet snapshot.

## Features

- **Active projects** — curated highlights
- **Fleet health** — table of NovaLux12 repositories (status, last push, language)
  - *Static* snapshot between `<!-- fleet:begin -->` / `<!-- fleet:end -->` markers in `index.html`, regenerated daily
  - *Live* enhancement via minimal vanilla JS: fetches `https://api.github.com/users/NovaLux12/repos` when JS is enabled, falls back to `fleet.json` then static rows on rate-limit/offline
  - Inspired by [fleet-pulse](https://github.com/NovaLux12/fleet-pulse)
- **Accessibility** — skip link, landmarks (`header`/`main`/`nav`/`footer`), semantic table with `<caption>` + `scope="col"`, `aria-live` fleet status, `focus-visible` outlines, `prefers-reduced-motion` respect, keyboard-operable controls
- **Dark / light theme toggle** — CSS variables + `data-theme`, respects `prefers-color-scheme`, persists to `localStorage`, no flash (inline head script), toggle is `<button>` with `aria-pressed`
- **Last-updated** — `<time id="last-updated" datetime="YYYY-MM-DD">` + `<time id="fleet-generated">`, updated atomically by build script (no blanket `sed`)

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
npm run fleet:dry
```

Outputs:

- `index.html` — fleet rows between markers + both `<time>` elements updated
- `fleet.json` — `{ generated_at, user, repos: [...] }` consumed as JS fallback

Page still works with no build — static rows are a valid snapshot and the page is usable with JS disabled (`<noscript>` note).

## Deploy

GitHub Pages (legacy) serves from `main` branch root. No build step in Pages — the daily workflow commits the regenerated snapshot.

```
Settings → Pages → Build and deployment → Source: Deploy from a branch → Branch: main / root
```

## Workflows

- `.github/workflows/update.yml` — daily `cron: 0 0 * * *` + manual dispatch. Runs `scripts/generate-fleet.py` (no brittle `sed 's/Updated.*/'`), commits `index.html` + `fleet.json` only if changed.
- Concurrency: `group: status-update`, `cancel-in-progress: false`.

## File map

```
index.html                 # static page (fleet markers, theme toggle, a11y)
fleet.json                 # build-time snapshot (generated, committed)
scripts/generate-fleet.py  # stdlib generator — GH API -> fleet rows + fleet.json
package.json               # npm run build wrapper (no deps)
```

## Local preview

```bash
python3 -m http.server 8000
# open http://localhost:8000/
# test light/dark toggle, fleet refresh, and no-JS fallback (disable JS in devtools)
```

No dependencies, no tracking. Single static HTML file + optional build-time data.
