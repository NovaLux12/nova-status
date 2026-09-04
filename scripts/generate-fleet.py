#!/usr/bin/env python3
"""
Generate fleet health snapshot for nova-status.

- Fetches NovaLux12 repos via GitHub API (uses GITHUB_TOKEN if available).
- Renders HTML rows between <!-- fleet:begin --> / <!-- fleet:end --> markers.
- Updates <time id="last-updated"> and <time id="fleet-generated"> precisely (no blanket sed).
- Writes fleet.json (build-time data consumed by client JS fallback).

Zero deps — stdlib only.
Usage:
  python3 scripts/generate-fleet.py            # fetch live, update index.html + fleet.json
  python3 scripts/generate-fleet.py --date 2026-08-20 --dry-run
  GITHUB_TOKEN=... python3 scripts/generate-fleet.py
"""

from __future__ import annotations

import argparse
import datetime
import html
import json
import os
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
FLEET_JSON = ROOT / "fleet.json"
USER = "NovaLux12"
PER_PAGE = 100

# Markers — must match index.html
FLEET_BEGIN = "<!-- fleet:begin"
FLEET_END = "<!-- fleet:end"

# Precise time element patterns (id-targeted, not blanket "Updated")
RE_LAST_UPDATED = re.compile(
    r'(<time\s+id="last-updated"\s+datetime=")[^"]*(">[^<]*</time>)'
)
RE_FLEET_GENERATED = re.compile(
    r'(<time\s+id="fleet-generated"\s+datetime=")[^"]*(">[^<]*</time>)'
)


def fetch_repos(token: str | None) -> list[dict]:
    url = f"https://api.github.com/users/{USER}/repos?per_page={PER_PAGE}&sort=pushed"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "nova-status-generate-fleet",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if not isinstance(data, list):
                raise RuntimeError(f"Unexpected API shape: {type(data)}")
            return data
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"GitHub API {e.code} {e.reason}: {body}") from e


def health_label(pushed_at: str | None, now: datetime.datetime) -> tuple[str, str]:
    if not pushed_at:
        return ("stale", "bad")
    try:
        dt = datetime.datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
    except ValueError:
        return ("stale", "bad")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    days = (now - dt).total_seconds() / 86400
    if days <= 14:
        return ("active", "")
    if days <= 45:
        return ("steady", "warn")
    return ("stale", "bad")


def render_rows(repos: list[dict], date_str: str) -> tuple[str, list[dict]]:
    now = datetime.datetime.now(datetime.timezone.utc)
    # Filter forks/archived, sort by pushed_at desc
    filtered = [r for r in repos if not r.get("fork") and not r.get("archived")]
    filtered.sort(key=lambda r: r.get("pushed_at") or "", reverse=True)
    top = filtered[:20]

    rows: list[str] = []
    fleet_entries: list[dict] = []
    for r in top:
        name = r.get("name", "")
        html_url = r.get("html_url", f"https://github.com/{USER}/{name}")
        pushed = r.get("pushed_at", "")
        lang = r.get("language") or "—"
        pushed_date = pushed[:10] if pushed else date_str
        label, cls = health_label(pushed, now)
        dot_cls = f" {cls}" if cls else ""
        # Keep markup identical to index.html static fallback so diff is minimal
        row = (
            f'          <tr><td><a class="repo-link" href="{html.escape(html_url)}" rel="noopener">{html.escape(name)}</a></td>'
            f'<td><span class="health"><span class="dot{dot_cls}" aria-hidden="true"></span> <strong>{html.escape(label)}</strong></span></td>'
            f'<td><time datetime="{html.escape(pushed_date)}">{html.escape(pushed_date)}</time></td>'
            f'<td class="lang">{html.escape(lang)}</td></tr>'
        )
        rows.append(row)
        fleet_entries.append(
            {
                "name": name,
                "html_url": html_url,
                "pushed_at": pushed,
                "language": r.get("language"),
                "fork": r.get("fork"),
                "archived": r.get("archived"),
                "stargazers_count": r.get("stargazers_count"),
            }
        )

    rendered = "\n".join(rows) if rows else '          <tr><td colspan="4" style="color:var(--muted);text-align:center;padding:16px">No repositories found.</td></tr>'
    return rendered, fleet_entries


def update_index_html(rendered_rows: str, date_str: str) -> bool:
    text = INDEX.read_text(encoding="utf-8")

    if FLEET_BEGIN not in text or FLEET_END not in text:
        raise RuntimeError("fleet markers not found in index.html (expected fleet:begin / fleet:end)")

    # Replace only between markers (precise, not blanket sed)
    begin_idx = text.index(FLEET_BEGIN)
    end_idx = text.index(FLEET_END)
    if end_idx <= begin_idx:
        raise RuntimeError("fleet:end appears before fleet:begin")

    # Find end of begin line and start of end line to preserve marker lines
    begin_line_end = text.index("\n", begin_idx) + 1 if "\n" in text[begin_idx:] else begin_idx + len(FLEET_BEGIN)
    # Keep the begin marker line intact, inject rows, then preserve end marker
    before = text[:begin_line_end]
    after = text[end_idx:]
    # rendered rows should be between markers
    new_mid = rendered_rows + "\n          "

    # Update time elements precisely via id-targeted regex
    def replace_time(pattern: re.Pattern[str], replacement_text: str, source: str) -> str:
        def _repl(m: re.Match[str]) -> str:
            prefix, suffix = m.group(1), m.group(2)
            # suffix is like '">Updated 2026-08-19</time>' or '">2026-08-19</time>'
            # Preserve prefix/suffix structure, inject date
            if "Updated" in suffix:
                return f'{prefix}{date_str}">Updated {date_str}</time>'
            return f'{prefix}{date_str}">{date_str}</time>'
        new, n = pattern.subn(_repl, source, count=1)
        if n == 0:
            print(f"warn: pattern {pattern.pattern[:40]}... not matched", file=sys.stderr)
            return source
        return new

    combined = before + new_mid + after
    combined = replace_time(RE_LAST_UPDATED, date_str, combined)
    combined = replace_time(RE_FLEET_GENERATED, date_str, combined)

    if combined == text:
        print("no changes to index.html")
        return False

    INDEX.write_text(combined, encoding="utf-8")
    print(f"updated {INDEX} (fleet rows + timestamps -> {date_str})")
    return True


def write_fleet_json(entries: list[dict], date_str: str) -> None:
    payload = {
        "generated_at": date_str,
        "user": USER,
        "repos": entries,
    }
    FLEET_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {FLEET_JSON} ({len(entries)} repos)")


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate fleet health for nova-status")
    ap.add_argument("--date", help="override date YYYY-MM-DD (default: today UTC)")
    ap.add_argument("--dry-run", action="store_true", help="print rendered rows, don't write files")
    ap.add_argument("--token", help="GitHub token (default: $GITHUB_TOKEN)")
    args = ap.parse_args()

    date_str = args.date or datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    # Validate date format
    try:
        datetime.date.fromisoformat(date_str)
    except ValueError:
        print(f"invalid --date {date_str!r}, expected YYYY-MM-DD", file=sys.stderr)
        return 2

    token = args.token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    print(f"fetching repos for {USER} (token: {'yes' if token else 'no'}) ...")
    try:
        repos = fetch_repos(token)
    except Exception as e:
        # Offline / API failure: still update timestamps so workflow can succeed with stale data
        print(f"fetch failed: {e}", file=sys.stderr)
        if args.dry_run:
            return 1
        # Try to keep existing fleet.json if present; just update timestamps
        if FLEET_JSON.exists():
            try:
                existing = json.loads(FLEET_JSON.read_text(encoding="utf-8"))
                entries = existing.get("repos", [])
                # Re-render from existing entries mapped to API shape (preserve all fields)
                fake_repos = [
                    {
                        "name": r["name"],
                        "html_url": r["html_url"],
                        "pushed_at": r["pushed_at"],
                        "language": r.get("language"),
                        "fork": bool(r.get("fork")) if r.get("fork") is not None else False,
                        "archived": bool(r.get("archived")) if r.get("archived") is not None else False,
                        "stargazers_count": r.get("stargazers_count") or 0,
                    }
                    for r in entries
                ]
                rendered, fleet_entries = render_rows(fake_repos, date_str)
                update_index_html(rendered, date_str)
                # Refresh generated_at
                write_fleet_json(fleet_entries, date_str)
                print("updated from cached fleet.json (API unavailable)")
                return 0
            except Exception as e2:
                print(f"cached fallback also failed: {e2}", file=sys.stderr)
        # Fallback: just update timestamps in index.html with existing rows
        try:
            text = INDEX.read_text(encoding="utf-8")
            # Only timestamp update, no row regeneration
            new_text = RE_LAST_UPDATED.sub(f'\\1{date_str}">Updated {date_str}</time>', text, count=1)
            new_text = RE_FLEET_GENERATED.sub(f'\\1{date_str}">{date_str}</time>', new_text, count=1)
            if new_text != text:
                INDEX.write_text(new_text, encoding="utf-8")
                print(f"updated timestamps only -> {date_str} (no API data)")
                return 0
        except Exception as e3:
            print(f"timestamp-only fallback failed: {e3}", file=sys.stderr)
        return 1

    rendered, entries = render_rows(repos, date_str)

    if args.dry_run:
        print(rendered)
        print(f"\n-- would write {len(entries)} repos to {FLEET_JSON} and update {INDEX} --")
        return 0

    write_fleet_json(entries, date_str)
    update_index_html(rendered, date_str)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
