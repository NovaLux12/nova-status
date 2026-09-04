#!/usr/bin/env python3
"""
Generate the nova-status v2 snapshot — one stdlib-only pass, everything cache-friendly.

Renders, between their marker comments in index.html:
  - projects:    featured projects (from projects.json) with health auto-derived from pushed_at
  - stats:       stats strip — repo count, total stars, active/steady/stale counts + language bar
  - fleet:       static top-20 fleet rows (no-JS fallback; client JS renders the full fleet)
  - releases:    release timeline (latest release per repo, fleet-wide, newest first)
  - sparkline:   30-day fleet-activity SVG (repos pushed per day + total stars trend)

Also writes:
  - fleet.json   enriched per-repo snapshot (stars, open issues, description, topics,
                 latest release, CI state) + fleet-wide stats — the client's single data file
  - history.jsonl  one JSON line per run date: per-repo pushed_at + stars + daily counts
                 (appended/replaced idempotently; powers the sparkline)

Zero deps — stdlib only.
Usage:
  python3 scripts/generate-fleet.py                    # fetch live + enrich, update page + data
  python3 scripts/generate-fleet.py --date 2026-09-04 --dry-run
  GITHUB_TOKEN=... python3 scripts/generate-fleet.py   # token enables per-repo enrichment
"""

from __future__ import annotations

import argparse
import collections
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
PROJECTS_JSON = ROOT / "projects.json"
HISTORY_JSONL = ROOT / "history.jsonl"
USER = "NovaLux12"
PER_PAGE = 100
TIMEOUT = 10

# Health thresholds (shared semantics with the client JS — keep in sync)
ACTIVE_DAYS = 14
STEADY_DAYS = 45

# Marker ids — must match index.html
SECTIONS = ("projects", "stats", "fleet", "releases", "sparkline")

# Precise time element patterns (id-targeted, not blanket sed)
RE_LAST_UPDATED = re.compile(
    r'(<time\s+id="last-updated"\s+datetime=")[^"]*(">[^<]*</time>)'
)
RE_FLEET_GENERATED = re.compile(
    r'(<time\s+id="fleet-generated"\s+datetime=")[^"]*(">[^<]*</time>)'
)

# Stable-ish palette for the language bar (pure CSS width % + inline colour).
# Mirrored client-side (langColor()) so JS re-renders look identical.
LANG_COLORS = {
    "Go": "#00ADD8",
    "Python": "#3572A5",
    "TypeScript": "#3178C6",
    "JavaScript": "#f1e05a",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Shell": "#89e051",
    "Rust": "#dea584",
    "PowerShell": "#6fa8dc",
    "C#": "#178600",
    "Java": "#b07219",
    "Ruby": "#701516",
    "PHP": "#4F5D95",
    "Swift": "#F05138",
    "Kotlin": "#A97BFF",
    "Dockerfile": "#384d54",
}


class ApiStop(Exception):
    """Raised when we should stop hitting the API (rate limit / auth)."""


def utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def health_label(pushed_at: str | None, now: datetime.datetime) -> str:
    """Return 'active' | 'steady' | 'stale' for a pushed_at ISO string."""
    if not pushed_at:
        return "stale"
    try:
        dt = datetime.datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
    except ValueError:
        return "stale"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    days = (now - dt).total_seconds() / 86400
    if days <= ACTIVE_DAYS:
        return "active"
    if days <= STEADY_DAYS:
        return "steady"
    return "stale"


# --------------------------------------------------------------------------
# API
# --------------------------------------------------------------------------

class GitHubAPI:
    def __init__(self, token: str | None):
        self.token = token
        self.remaining: int | None = None

    def get(self, path: str) -> dict | list | None:
        """GET an API path. 404 -> None. 403/429/ratelimit -> ApiStop."""
        url = f"https://api.github.com/{path.lstrip('/')}"
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "nova-status-generate-fleet",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = urllib.request.Request(url, headers=headers)
        last_err: Exception | None = None
        for attempt in range(2):  # one retry on 5xx / 429
            try:
                with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                    self._track_limits(resp.headers)
                    body = resp.read().decode("utf-8")
                    return json.loads(body) if body else None
            except urllib.error.HTTPError as e:
                self._track_limits(e.headers)
                if e.code == 404:
                    return None
                if e.code in (403, 429):
                    remaining = self.remaining
                    if remaining is not None and remaining < 5:
                        print(
                            f"warn: rate limit low (remaining={remaining}), stopping enrichment",
                            file=sys.stderr,
                        )
                        raise ApiStop() from e
                    # 403 without rate-limit exhaustion is usually auth-scope; bail once
                    if attempt == 1:
                        raise ApiStop(f"API {e.code} {e.reason} (x-ratelimit-remaining={remaining})") from e
                last_err = e
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                last_err = e
        raise RuntimeError(f"request failed for {path}: {last_err}")

    def _track_limits(self, headers) -> None:
        try:
            self.remaining = int(headers.get("X-RateLimit-Remaining", ""))
        except (TypeError, ValueError):
            pass


def fetch_repos(api: GitHubAPI) -> list[dict]:
    repos: list[dict] = []
    page = 1
    while True:
        data = api.get(
            f"users/{USER}/repos?per_page={PER_PAGE}&sort=pushed&page={page}"
        )
        if not isinstance(data, list):
            raise RuntimeError(f"Unexpected API shape: {type(data)}")
        repos.extend(data)
        if len(data) < PER_PAGE:
            break
        page += 1
    return repos


def enrich_repo(api: GitHubAPI, repo: dict) -> dict:
    """Add release + CI info. Requires a token; degrades to None fields."""
    name = repo["name"]
    out = {
        "name": name,
        "html_url": repo.get("html_url", f"https://github.com/{USER}/{name}"),
        "description": repo.get("description"),
        "topics": repo.get("topics") or [],
        "language": repo.get("language"),
        "fork": bool(repo.get("fork")),
        "archived": bool(repo.get("archived")),
        "pushed_at": repo.get("pushed_at"),
        "stargazers_count": repo.get("stargazers_count") or 0,
        "open_issues_count": repo.get("open_issues_count") or 0,
        "latest_release": None,
        "ci": None,
    }
    if not api.token:
        return out
    # /releases/latest 404s for repos without releases — graceful null.
    rel = api.get(f"repos/{USER}/{name}/releases/latest")
    if isinstance(rel, dict) and rel.get("tag_name"):
        out["latest_release"] = {
            "tag_name": rel.get("tag_name"),
            "name": rel.get("name") or rel.get("tag_name"),
            "published_at": rel.get("published_at"),
            "html_url": rel.get("html_url"),
        }
    runs = api.get(f"repos/{USER}/{name}/actions/runs?per_page=1")
    if isinstance(runs, dict) and runs.get("workflow_runs"):
        wr = runs["workflow_runs"][0]
        out["ci"] = {
            "conclusion": wr.get("conclusion"),
            "status": wr.get("status"),
            "html_url": wr.get("html_url"),
            "head_branch": wr.get("head_branch"),
        }
    return out


def ci_dot_class(ci: dict | None) -> str:
    """Map CI state to a dot modifier ('' / 'warn' / 'bad')."""
    if not ci:
        return ""
    conclusion = ci.get("conclusion")
    status = ci.get("status")
    if status != "completed" or not conclusion:
        return "warn"  # queued / in_progress
    if conclusion == "success":
        return ""
    if conclusion in ("failure", "startup_failure", "timed_out"):
        return "bad"
    return "warn"  # neutral / cancelled / skipped / action_required / stale


# --------------------------------------------------------------------------
# Section renderers  (all return plain text without leading indentation)
# --------------------------------------------------------------------------

def esc(s) -> str:
    return html.escape("" if s is None else str(s))


def fmt_date(iso: str | None) -> str:
    return (iso or "")[:10]


def effective_repos(repos: list[dict]) -> list[dict]:
    return [r for r in repos if not r.get("fork") and not r.get("archived")]


def render_projects(projects: list[dict], by_name: dict[str, dict], now: datetime.datetime) -> str:
    rows: list[str] = []
    for p in projects:
        repo = by_name.get(p.get("repo", ""))
        name = p.get("name") or p.get("repo", "")
        url = p.get("repo_url") or f"https://github.com/{USER}/{p.get('repo', '')}"
        blurb = p.get("blurb", "")
        if repo:
            health = health_label(repo.get("pushed_at"), now)
            dot_cls = "" if health == "active" else ("warn" if health == "steady" else "bad")
            pushed = fmt_date(repo.get("pushed_at")) or "—"
            stars = int(repo.get("stargazers_count") or 0)
            bits = [f"<strong>{esc(health)}</strong>", f"pushed {esc(pushed)}"]
            if stars:
                bits.append(f"★ {stars}")
            badge = (
                f'<div class="badge"><span class="dot {dot_cls}" aria-hidden="true"></span> '
                + " · ".join(bits)
                + "</div>"
            )
        else:
            badge = '<div class="badge"><span class="dot warn" aria-hidden="true"></span> not in fleet data</div>'
        rows.append(
            '<div class="row">'
            f'<div><div class="name"><a href="{esc(url)}" rel="noopener">{esc(name)}</a></div>'
            f'<div class="meta">{esc(blurb)}</div></div>'
            f"{badge}</div>"
        )
    return "\n".join(rows) if rows else "<!-- no projects configured -->"


def render_stats(repos: list[dict], now: datetime.datetime) -> str:
    active = steady = stale = 0
    total_stars = 0
    langs: collections.Counter[str] = collections.Counter()
    for r in repos:
        h = health_label(r.get("pushed_at"), now)
        if h == "active":
            active += 1
        elif h == "steady":
            steady += 1
        else:
            stale += 1
        total_stars += int(r.get("stargazers_count") or 0)
        lang = r.get("language")
        if lang:
            langs[lang] += 1

    n = len(repos)
    cards = (
        '<div class="statgrid">'
        f'<div class="stat"><span class="stat-value" id="stat-repos">{n}</span>'
        '<span class="stat-label">repositories</span></div>'
        f'<div class="stat"><span class="stat-value" id="stat-stars">{total_stars}</span>'
        '<span class="stat-label">stars</span></div>'
        f'<div class="stat"><span class="stat-value stat-ok" id="stat-active">{active}</span>'
        '<span class="stat-label">active</span></div>'
        f'<div class="stat"><span class="stat-value stat-warn" id="stat-steady">{steady}</span>'
        '<span class="stat-label">steady</span></div>'
        f'<div class="stat"><span class="stat-value stat-bad" id="stat-stale">{stale}</span>'
        '<span class="stat-label">stale</span></div>'
        "</div>"
    )

    total_langs = sum(langs.values()) or 1
    segs: list[str] = []
    legend: list[str] = []
    for lang, count in langs.most_common():
        pct = round(count * 100 / total_langs)
        color = LANG_COLORS.get(lang, "var(--accent)")
        segs.append(
            f'<span class="langbar-seg" style="width:{pct}%;background:{color}" '
            f'title="{esc(lang)}: {count}"></span>'
        )
        legend.append(
            f'<li><i style="background:{color}" aria-hidden="true"></i>{esc(lang)} '
            f"<b>{count}</b></li>"
        )
    bar = "\n".join(
        [
            '<div class="langbar" id="langbar" role="img" '
            f'aria-label="Language distribution across {n} repositories">',
            "".join(segs),
            "</div>",
            '<ul class="lang-legend" id="lang-legend">' + "".join(legend) + "</ul>",
        ]
    )
    return cards + "\n" + bar


def render_fleet_rows(repos: list[dict], date_str: str) -> str:
    """Top-20 static rows — no-JS fallback. Same columns as the JS-rendered table."""
    filtered = effective_repos(repos)
    filtered.sort(key=lambda r: r.get("pushed_at") or "", reverse=True)
    top = filtered[:20]
    rows: list[str] = []
    for r in top:
        name = r.get("name", "")
        url = r.get("html_url", f"https://github.com/{USER}/{name}")
        pushed = fmt_date(r.get("pushed_at")) or date_str
        lang = r.get("language") or "—"
        health = r.get("health", "active")
        dot_cls = "" if health == "active" else ("warn" if health == "steady" else "bad")
        stars = int(r.get("stargazers_count") or 0)
        rel = r.get("latest_release")
        ci = r.get("ci")
        ci_dot = (
            f'<span class="ci-dot {ci_dot_class(ci)}" title="CI: {esc(ci.get("conclusion") or ci.get("status"))}" aria-label="CI: {esc(ci.get("conclusion") or "pending")}"></span>'
            if ci
            else ""
        )
        desc = r.get("description")
        desc_line = (
            f'<div class="repo-desc">{esc(desc[:120])}</div>' if desc else ""
        )
        rel_cell = (
            f'<a href="{esc(rel["html_url"])}" rel="noopener" class="rel-tag">{esc(rel["tag_name"])}</a>'
            if rel
            else '<span class="muted">—</span>'
        )
        rows.append(
            '<tr>'
            f'<td><a class="repo-link" href="{esc(url)}" rel="noopener">{esc(name)}</a>{ci_dot}{desc_line}</td>'
            f'<td><span class="health"><span class="dot {dot_cls}" aria-hidden="true"></span> <strong>{esc(health)}</strong></span></td>'
            f'<td><time datetime="{esc(pushed)}">{esc(pushed)}</time></td>'
            f'<td><span class="stars">★ {stars}</span></td>'
            f'<td class="lang">{esc(lang)}</td>'
            f"<td>{rel_cell}</td>"
            "</tr>"
        )
    if not rows:
        rows.append(
            '<tr><td colspan="6" class="empty-cell">No repositories found.</td></tr>'
        )
    return "\n".join(rows)


def render_releases(repos: list[dict]) -> str:
    releases = []
    for r in effective_repos(repos):
        rel = r.get("latest_release")
        if rel:
            releases.append((rel.get("published_at") or "", r.get("name", ""), rel))
    releases.sort(key=lambda t: t[0], reverse=True)
    rows: list[str] = []
    for published, repo_name, rel in releases[:8]:
        when = fmt_date(published) or "—"
        rows.append(
            '<div class="row rel-row">'
            f'<div class="rel-info"><div class="name"><a href="{esc(rel["html_url"])}" rel="noopener">'
            f'{esc(repo_name)} <span class="rel-tag">{esc(rel["tag_name"])}</span></a></div>'
            f'<div class="meta">{esc(rel.get("name") or "")}</div></div>'
            f'<div class="badge"><time datetime="{esc(when)}">{esc(when)}</time></div>'
            "</div>"
        )
    if not rows:
        rows.append('<p class="fleet-intro">No releases yet — first tag will appear here.</p>')
    return "\n".join(rows)


def render_sparkline(history: list[dict], now: datetime.datetime) -> str:
    """30-day fleet activity: bars = repos pushed that day, line = total stars."""
    if not history:
        return (
            '<svg class="sparkline" viewBox="0 0 640 120" role="img" '
            'aria-label="Fleet activity history — no data yet">'
            '<text x="320" y="60" text-anchor="middle" class="spark-note">'
            "History builds daily from the midnight UTC run.</text></svg>"
        )
    dates = sorted({row["date"] for row in history})
    end_day = datetime.date.fromisoformat(dates[-1])
    start_day = end_day - datetime.timedelta(days=29)

    by_date = {row["date"]: row for row in history}
    days: list[datetime.date] = [start_day + datetime.timedelta(days=i) for i in range(30)]

    activity: list[int] = []
    stars: list[int] = []
    running_stars = 0
    for d in days:
        iso = d.isoformat()
        row = by_date.get(iso)
        if row:
            act = sum(
                1 for r in (row.get("repos") or {}).values()
                if str(r.get("pushed_at", ""))[:10] == iso
            )
            running_stars = int(row.get("total_stars") or running_stars)
        else:
            act = 0
        activity.append(act)
        stars.append(running_stars)

    width, height, pad = 640, 120, 8
    plot_w, plot_h = width - 2 * pad, height - 2 * pad - 14
    slot = plot_w / 30
    max_act = max(activity + [1])
    max_stars = max(stars + [1])

    bars: list[str] = []
    for i, act in enumerate(activity):
        h = round(act / max_act * plot_h) if act else 0
        x = pad + i * slot + slot * 0.18
        w = slot * 0.64
        if h:
            bars.append(
                f'<rect class="spark-bar" x="{x:.1f}" y="{pad + plot_h - h:.1f}" '
                f'width="{w:.1f}" height="{h}" rx="1.5"><title>{days[i].isoformat()}: '
                f"{act} repo(s) pushed</title></rect>"
            )

    pts: list[str] = []
    for i, s in enumerate(stars):
        x = pad + i * slot + slot / 2
        y = pad + plot_h - (s / max_stars) * plot_h
        pts.append(f"{x:.1f},{y:.1f}")
    polyline = (
        f'<polyline class="spark-line" points="{" ".join(pts)}" fill="none" '
        'stroke-width="2" vector-effect="non-scaling-stroke"/>'
        f'<circle class="spark-dot" cx="{pad + 29 * slot + slot / 2:.1f}" cy="{(pad + plot_h - (stars[-1] / max_stars) * plot_h):.1f}" r="3"/>'
    )

    ytick = f'{max_act} pushed/day'
    labels = "".join(
        f'<text class="spark-axis" x="{pad + i * slot + slot / 2:.1f}" y="{height - 4}" '
        f'text-anchor="middle">{days[i].strftime("%d %b")}</text>'
        for i in (0, 10, 20, 29)
    )
    svg = (
        '<svg class="sparkline" viewBox="0 0 640 122" role="img" '
        f'aria-label="Fleet activity over the last 30 days ending {end_day.isoformat()}: '
        f'repos pushed per day (bars), total stars (line). Max {max_act} repos in a day, '
        f'{running_stars} stars total.">'
        + "".join(bars)
        + polyline
        + f'<text class="spark-note" x="{width - pad}" y="{pad + 8}" text-anchor="end">{esc(ytick)}</text>'
        + labels
        + "</svg>"
    )
    return svg


# --------------------------------------------------------------------------
# History (history.jsonl)
# --------------------------------------------------------------------------

def load_history() -> list[dict]:
    if not HISTORY_JSONL.exists():
        return []
    rows = []
    for line in HISTORY_JSONL.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            print(f"warn: skipping malformed history line: {line[:60]}", file=sys.stderr)
    return rows


def upsert_history(history: list[dict], row: dict) -> list[dict]:
    """Replace an existing row for the same date, else append. Returns date-sorted rows."""
    out = [r for r in history if r.get("date") != row["date"]]
    out.append(row)
    out.sort(key=lambda r: r.get("date", ""))
    return out


def build_history_row(repos: list[dict], date_str: str) -> dict:
    now = utcnow()
    repos_map: dict[str, dict] = {}
    counts = {"active": 0, "steady": 0, "stale": 0}
    total_stars = 0
    for r in effective_repos(repos):
        pushed = r.get("pushed_at")
        stars = int(r.get("stargazers_count") or 0)
        repos_map[r.get("name", "")] = {"pushed_at": pushed, "stars": stars}
        counts[health_label(pushed, now)] += 1
        total_stars += stars
    return {
        "date": date_str,
        "repos": repos_map,
        "counts": counts,
        "total_stars": total_stars,
    }


# --------------------------------------------------------------------------
# index.html marker surgery
# --------------------------------------------------------------------------

def replace_section(text: str, name: str, content: str) -> str:
    begin = f"<!-- {name}:begin"
    end = f"<!-- {name}:end"
    b_idx = text.index(begin)
    e_idx = text.index(end)
    if e_idx <= b_idx:
        raise RuntimeError(f"marker {name}:end appears before {name}:begin")
    b_line_end = text.index("\n", b_idx) + 1
    end_line = text[e_idx : text.index("\n", e_idx)]
    indent = end_line[: end_line.index("<!--")]
    if not indent:
        indent = "          "
    body_lines = [indent + ln for ln in content.splitlines()] if content else [indent]
    return text[:b_line_end] + "\n".join(body_lines) + "\n" + text[e_idx:]


def update_index_html(sections: dict[str, str], date_str: str) -> bool:
    text = INDEX.read_text(encoding="utf-8")
    for name in SECTIONS:
        if f"<!-- {name}:begin" not in text or f"<!-- {name}:end" not in text:
            raise RuntimeError(f"markers not found for section {name!r} in index.html")
        text = replace_section(text, name, sections[name])

    def replace_time(pattern: re.Pattern[str], source: str) -> str:
        def _repl(m: re.Match[str]) -> str:
            prefix, suffix = m.group(1), m.group(2)
            if "Updated" in suffix:
                return f'{prefix}{date_str}">Updated {date_str}</time>'
            return f'{prefix}{date_str}">{date_str}</time>'
        new, n = pattern.subn(_repl, source, count=1)
        if n == 0:
            print(f"warn: pattern {pattern.pattern[:40]}... not matched", file=sys.stderr)
            return source
        return new

    text = replace_time(RE_LAST_UPDATED, text)
    text = replace_time(RE_FLEET_GENERATED, text)

    if text == INDEX.read_text(encoding="utf-8"):
        print("no changes to index.html")
        return False
    INDEX.write_text(text, encoding="utf-8")
    print(f"updated {INDEX} ({', '.join(SECTIONS)} sections + timestamps -> {date_str})")
    return True


def write_fleet_json(repos: list[dict], date_str: str, now: datetime.datetime) -> None:
    effective = effective_repos(repos)
    stats = {
        "total_repos": len(effective),
        "total_stars": sum(int(r.get("stargazers_count") or 0) for r in effective),
        "counts": {
            "active": sum(1 for r in effective if r.get("health") == "active"),
            "steady": sum(1 for r in effective if r.get("health") == "steady"),
            "stale": sum(1 for r in effective if r.get("health") == "stale"),
        },
        "languages": collections.Counter(
            r.get("language") for r in effective if r.get("language")
        ),
    }
    payload = {
        "generated_at": date_str,
        "generated_ts": now.isoformat(),
        "user": USER,
        "stats": {k: dict(v) if isinstance(v, collections.Counter) else v for k, v in stats.items()},
        "repos": repos,
    }
    FLEET_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {FLEET_JSON} ({len(repos)} repos, {len(effective)} effective)")


def write_history(history: list[dict]) -> None:
    HISTORY_JSONL.write_text(
        "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in history),
        encoding="utf-8",
    )
    print(f"wrote {HISTORY_JSONL} ({len(history)} day(s))")


# --------------------------------------------------------------------------
# Offline fallback (API unavailable): rebuild everything from cached fleet.json
# --------------------------------------------------------------------------

def rebuild_from_cache() -> int:
    print("rebuilding from cached fleet.json (API unavailable)", file=sys.stderr)
    try:
        data = json.loads(FLEET_JSON.read_text(encoding="utf-8"))
        repos = data.get("repos", [])
        # restore health (not stored in old caches; compute now)
        now = utcnow()
        for r in repos:
            r["health"] = health_label(r.get("pushed_at"), now)
        build_and_write(repos, data.get("generated_at", utcnow().date().isoformat()))
        return 0
    except Exception as e:
        print(f"cached fallback failed: {e}", file=sys.stderr)
        return 1


# --------------------------------------------------------------------------
# Main pipeline
# --------------------------------------------------------------------------

def build_and_write(repos: list[dict], date_str: str) -> None:
    now = utcnow()
    for r in repos:
        r["health"] = health_label(r.get("pushed_at"), now)

    # projects (data-driven featured section)
    projects = []
    if PROJECTS_JSON.exists():
        try:
            projects = json.loads(PROJECTS_JSON.read_text(encoding="utf-8")).get("projects", [])
        except (json.JSONDecodeError, OSError) as e:
            print(f"warn: could not read projects.json: {e}", file=sys.stderr)
    by_name = {r.get("name", ""): r for r in repos}

    # history: append/replace today's row (idempotent), then render the sparkline
    history = load_history()
    history = upsert_history(history, build_history_row(repos, date_str))

    sections = {
        "projects": render_projects(projects, by_name, now),
        "stats": render_stats(effective_repos(repos), now),
        "fleet": render_fleet_rows(repos, date_str),
        "releases": render_releases(repos),
        "sparkline": render_sparkline(history, now),
    }
    for name, content in sections.items():
        print(f"section {name}: {len(content)} chars, {content.count(chr(10)) + 1} lines")

    update_index_html(sections, date_str)
    write_fleet_json(repos, date_str, now)
    write_history(history)


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate fleet health for nova-status v2")
    ap.add_argument("--date", help="override date YYYY-MM-DD (default: today UTC)")
    ap.add_argument("--dry-run", action="store_true", help="fetch + render, do not write files")
    ap.add_argument("--token", help="GitHub token (default: $GITHUB_TOKEN or $GH_TOKEN)")
    args = ap.parse_args()

    date_str = args.date or utcnow().date().isoformat()
    try:
        datetime.date.fromisoformat(date_str)
    except ValueError:
        print(f"invalid --date {date_str!r}, expected YYYY-MM-DD", file=sys.stderr)
        return 2

    token = args.token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    api = GitHubAPI(token)

    print(f"fetching repos for {USER} (enrichment: {'on' if token else 'OFF — set GITHUB_TOKEN'} ) ...")
    try:
        repos = fetch_repos(api)
        print(f"fetched {len(repos)} repos")
    except (ApiStop, RuntimeError, OSError) as e:
        print(f"fetch failed: {e}", file=sys.stderr)
        if args.dry_run:
            return 1
        return rebuild_from_cache()

    # per-repo enrichment (releases + CI) — token-gated, cache-friendly
    enriched: list[dict] = []
    for i, repo in enumerate(repos, 1):
        r = repo
        try:
            r = enrich_repo(api, repo)
        except ApiStop as e:
            print(f"warn: enrichment stopped after {i-1}/{len(repos)} repos: {e}", file=sys.stderr)
            r = repo
            if "latest_release" not in r:
                r["latest_release"] = None
            if "ci" not in r:
                r["ci"] = None
        enriched.append(r)
        print(f"  [{i}/{len(repos)}] {repo.get('name','?')} ({repo.get('language') or '-'})")

    if args.dry_run:
        now = utcnow()
        for r in enriched:
            r["health"] = health_label(r.get("pushed_at"), now)
        n_eff = len(effective_repos(enriched))
        n_rel = sum(1 for r in effective_repos(enriched) if r.get("latest_release"))
        n_ci = sum(1 for r in effective_repos(enriched) if r.get("ci"))
        print(
            f"\n-- dry run: would write fleet.json ({len(enriched)} repos, {n_eff} effective, "
            f"{n_rel} with releases, {n_ci} with CI state) + update index.html "
            f"({', '.join(SECTIONS)} sections) + append history.jsonl [{date_str}] --"
        )
        return 0

    build_and_write(enriched, date_str)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())