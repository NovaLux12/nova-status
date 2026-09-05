#!/usr/bin/env python3
"""Build the fleet piece (fallback builder): NOVA OBSERVATORY fleet registry.
Reads fleet.json; writes self-contained pieces/fleet.html."""
import json, html, os, datetime as dt

ROOT = "/tmp/gauntlet-status"
data = json.load(open(os.path.join(ROOT, "fleet.json")))
repos = [r for r in data["repos"] if not r.get("fork") and not r.get("archived")]
repos.sort(key=lambda r: r.get("pushed_at", ""), reverse=True)

def esc(s): return html.escape(str(s), quote=True)

def health(r):
    h = r.get("health") or "active"
    try:
        days = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(r["pushed_at"].replace("Z", "+00:00"))).days
    except Exception:
        days = 999
    if h == "active" and days > 45: h = "stale"
    elif h == "active" and days > 14: h = "steady"
    return h

def fmt_date(iso):
    try: return iso[:10]
    except Exception: return "—"

def ci_cls(r):
    ci = r.get("ci") or {}
    if not ci: return "", ""
    concl = ci.get("conclusion") or ci.get("status") or ""
    if concl == "success": return "ci-ok", "CI success"
    if concl in ("failure", "timed_out", "startup_failure"): return "ci-bad", f"CI {concl}"
    return "ci-warn", f"CI {concl or 'pending'}"

LANG_COLORS = {"Go": "#00ADD8", "Python": "#3572A5", "TypeScript": "#3178C6",
               "JavaScript": "#f1e05a", "HTML": "#e34c26", "CSS": "#563d7c",
               "Shell": "#89e051", "Rust": "#dea584", "PowerShell": "#6fa8dc"}

rows = []
for r in repos:
    h = health(r)
    orb = "ok" if h == "active" else ("warn" if h == "steady" else "bad")
    ci_cls_s, ci_title = ci_cls(r)
    ci = f'<span class="ci-dot {ci_cls_s}" title="{esc(ci_title)}" aria-label="{esc(ci_title)}"></span>' if ci_cls_s else ""
    rel = ""
    lr = r.get("latest_release")
    if lr:
        rel = f'<a class="rel-tag" href="{esc(lr.get("html_url", "#"))}" rel="noopener">{esc(lr.get("tag_name", ""))}</a>'
    else:
        rel = '<span class="rel-none">—</span>'
    lang = r.get("language") or ""
    lang_html = f'<span class="lang"><i style="background:{LANG_COLORS.get(lang, "#8b93a7")}"></i>{esc(lang)}</span>' if lang else '<span class="lang muted">—</span>'
    desc = r.get("description") or ""
    if len(desc) > 110: desc = desc[:107] + "…"
    rows.append(f"""          <tr>
            <td data-label="Repository"><a class="repo-link" href="{esc(r.get('html_url','#'))}" rel="noopener">{esc(r['name'])}</a>{ci}<div class="repo-desc">{esc(desc)}</div></td>
            <td data-label="Status"><span class="health"><span class="orb {orb}" aria-hidden="true"></span>{esc(h)}</span></td>
            <td data-label="Last push" class="mono"><time datetime="{esc(fmt_date(r.get('pushed_at')))}">{esc(fmt_date(r.get('pushed_at')))}</time></td>
            <td data-label="Stars" class="mono stars">★ {r.get('stargazers_count', 0)}</td>
            <td data-label="Language">{lang_html}</td>
            <td data-label="Latest release">{rel}</td>
          </tr>""")

rows_html = "\n".join(rows)
n_eff = len(repos)

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<meta name="color-scheme" content="dark light" />
<meta name="theme-color" content="#07080c" media="(prefers-color-scheme: dark)" />
<meta name="theme-color" content="#f4f5f9" media="(prefers-color-scheme: light)" />
<title>Nova Observatory — Fleet Registry</title>
<style>
  :root {{
    --bg: #07080c;
    --panel: rgba(255,255,255,.03);
    --panel-solid: #0d0f16;
    --line: rgba(255,255,255,.09);
    --text: #eef0f6;
    --muted: #8b93a7;
    --accent: #e8b963;
    --aurora-a: #8b5cf6;
    --aurora-b: #2dd4bf;
    --ok: #4ade80;
    --warn: #fbbf24;
    --bad: #f87171;
    --font-display: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    --font-mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;
    --radius: 20px;
    --radius-sm: 12px;
    --glow-ok: 0 0 0 3px rgba(74,222,128,.15), 0 0 22px rgba(74,222,128,.22);
    --glow-accent: 0 0 0 3px rgba(232,185,99,.14), 0 0 26px rgba(232,185,99,.26);
  }}
  @media (prefers-color-scheme: light) {{
    :root {{
      --bg: #f4f5f9; --panel: rgba(15,18,23,.02); --panel-solid: #ffffff;
      --line: rgba(15,18,23,.10); --text: #14181f; --muted: #5b6472;
      --accent: #9a6b00; --ok: #15803d; --warn: #b45309; --bad: #b91c1c;
      --glow-ok: 0 0 0 3px rgba(21,128,61,.12), 0 0 22px rgba(21,128,61,.16);
      --glow-accent: 0 0 0 3px rgba(154,107,0,.10), 0 0 26px rgba(154,107,0,.14);
    }}
  }}
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; padding: 0; background: var(--bg); color: var(--text); font-family: var(--font-display); }}
  body {{
    min-height: 100vh;
    background:
      radial-gradient(1200px 600px at 85% -10%, rgba(139,92,246,.16), transparent 60%),
      radial-gradient(1000px 500px at -10% 20%, rgba(45,212,191,.12), transparent 55%),
      radial-gradient(900px 500px at 50% 110%, rgba(232,185,99,.08), transparent 60%),
      var(--bg);
    overflow-x: hidden;
  }}
  .wrap {{ max-width: 1080px; margin: 0 auto; padding: 40px 28px 72px; }}
  .overline {{ font-family: var(--font-mono); font-size: 11px; letter-spacing: .22em; text-transform: uppercase; color: var(--muted); margin: 0 0 10px; display: flex; align-items: center; gap: 10px; }}
  .overline::before {{ content: ""; width: 28px; height: 1px; background: linear-gradient(90deg, var(--accent), transparent); }}
  h1 {{ margin: 0 0 12px; font-size: 30px; letter-spacing: -.02em; line-height: 1.15; }}
  h1 .grad {{ background: linear-gradient(92deg, var(--accent) 0%, var(--aurora-b) 55%, var(--aurora-a) 100%); -webkit-background-clip: text; background-clip: text; color: transparent; }}
  .lede {{ color: var(--muted); font-size: 14px; line-height: 1.6; max-width: 640px; margin: 0 0 28px; }}
  .glass {{
    background: linear-gradient(180deg, rgba(255,255,255,.045), rgba(255,255,255,.015));
    border: 1px solid var(--line);
    border-radius: var(--radius);
    box-shadow: 0 30px 60px -30px rgba(0,0,0,.55), inset 0 1px 0 rgba(255,255,255,.06);
    backdrop-filter: blur(14px);
    padding: 22px 22px 16px;
  }}
  @media (prefers-color-scheme: light) {{
    .glass {{ background: linear-gradient(180deg, rgba(255,255,255,.9), rgba(255,255,255,.6)); box-shadow: 0 30px 60px -40px rgba(20,24,31,.35), inset 0 1px 0 rgba(255,255,255,.9); }}
  }}
  .toolbar {{ display: flex; flex-direction: column; gap: 12px; margin-bottom: 16px; }}
  .search {{ position: relative; }}
  .search svg {{ position: absolute; left: 14px; top: 50%; transform: translateY(-50%); opacity: .55; }}
  .search input {{
    width: 100%; background: rgba(0,0,0,.22); border: 1px solid var(--line); color: var(--text);
    border-radius: 999px; padding: 11px 16px 11px 40px; font-size: 13px; font-family: inherit; outline: none;
  }}
  .search input:focus {{ border-color: var(--accent); box-shadow: 0 0 0 3px rgba(232,185,99,.14); }}
  .search input::placeholder {{ color: var(--muted); }}
  @media (prefers-color-scheme: light) {{ .search input {{ background: rgba(0,0,0,.03); }} }}
  .chips {{ display: flex; flex-wrap: wrap; gap: 8px; }}
  .chip {{
    background: transparent; border: 1px solid var(--line); color: var(--muted); font-family: inherit;
    border-radius: 999px; padding: 5px 12px; font-size: 12px; cursor: pointer;
  }}
  .chip:hover {{ color: var(--text); border-color: var(--accent); }}
  .chip .n {{ font-family: var(--font-mono); font-size: 11px; margin-left: 5px; color: var(--accent); }}
  .table-scroll {{ overflow-x: auto; border-radius: 14px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; min-width: 760px; }}
  thead th {{
    position: sticky; top: 0; text-align: left; font-family: var(--font-mono); font-size: 10.5px;
    letter-spacing: .14em; text-transform: uppercase; color: var(--muted); font-weight: 600;
    padding: 12px 14px; border-bottom: 1px solid var(--line);
    background: rgba(13,15,22,.92); backdrop-filter: blur(8px); white-space: nowrap;
    user-select: none;
  }}
  th .arrow {{ opacity: 0; font-size: 9px; margin-left: 4px; color: var(--accent); }}
  th:hover .arrow {{ opacity: .8; }}
  th[aria-sort] .arrow {{ opacity: 1; }}
  td {{
    padding: 12px 14px; border-top: 1px solid var(--line); vertical-align: middle;
  }}
  tbody tr:first-child td {{ border-top: 0; }}
  tbody tr {{ transition: background-color .15s ease, box-shadow .15s ease; }}
  tbody tr:hover {{
    background: linear-gradient(90deg, rgba(139,92,246,.07), rgba(45,212,191,.05), transparent);
    box-shadow: inset 2px 0 0 var(--accent);
  }}
  .repo-link {{ color: var(--text); font-weight: 650; text-decoration: none; font-size: 13.5px; }}
  .repo-link:hover {{ color: var(--accent); }}
  .repo-desc {{ color: var(--muted); font-size: 11.5px; line-height: 1.4; margin-top: 3px; max-width: 380px; }}
  .ci-dot {{ display: inline-block; width: 6px; height: 6px; border-radius: 999px; margin-left: 8px; vertical-align: 2px; }}
  .ci-ok {{ background: var(--ok); box-shadow: 0 0 8px var(--ok); }}
  .ci-warn {{ background: var(--warn); box-shadow: 0 0 8px var(--warn); }}
  .ci-bad {{ background: var(--bad); box-shadow: 0 0 8px var(--bad); }}
  .health {{ display: inline-flex; align-items: center; gap: 8px; color: var(--muted); font-size: 12.5px; }}
  .orb {{ width: 8px; height: 8px; border-radius: 999px; flex-shrink: 0; }}
  .orb.ok {{ background: var(--ok); box-shadow: var(--glow-ok); }}
  .orb.warn {{ background: var(--warn); box-shadow: 0 0 0 3px rgba(251,191,36,.15), 0 0 20px rgba(251,191,36,.25); }}
  .orb.bad {{ background: var(--bad); box-shadow: 0 0 0 3px rgba(248,113,113,.15), 0 0 20px rgba(248,113,113,.25); }}
  .mono {{ font-family: var(--font-mono); font-variant-numeric: tabular-nums; color: var(--muted); }}
  .stars {{ color: var(--accent); font-weight: 600; }}
  .lang {{ display: inline-flex; align-items: center; gap: 7px; font-size: 12.5px; }}
  .lang i {{ width: 8px; height: 8px; border-radius: 3px; display: inline-block; }}
  .rel-tag {{
    display: inline-block; font-family: var(--font-mono); font-size: 11px; font-weight: 600;
    color: var(--accent); border: 1px solid rgba(232,185,99,.35); background: rgba(232,185,99,.08);
    border-radius: 999px; padding: 2px 9px; text-decoration: none; white-space: nowrap;
  }}
  .rel-tag:hover {{ background: rgba(232,185,99,.16); }}
  .rel-none {{ color: var(--muted); }}
  .muted {{ color: var(--muted); }}
  .foot {{ display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; margin-top: 14px; color: var(--muted); font-size: 12px; }}
  .foot .mono {{ font-size: 11.5px; }}
  .foot a {{ color: var(--accent); text-decoration: none; }}
  .foot a:hover {{ text-decoration: underline; }}
  .count-pill {{
    font-family: var(--font-mono); font-size: 11px; color: var(--accent);
    border: 1px solid rgba(232,185,99,.3); border-radius: 999px; padding: 2px 10px; margin-left: 10px;
    vertical-align: 3px;
  }}
  @media (max-width: 680px) {{
    .wrap {{ padding: 26px 16px 48px; }}
    h1 {{ font-size: 24px; }}
    thead {{ display: none; }}
    table, tbody, tr, td {{ display: block; width: 100%; }}
    table {{ min-width: 0; }}
    tbody tr {{
      border: 1px solid var(--line); border-radius: 14px; margin-bottom: 12px; padding: 4px 14px;
      background: linear-gradient(180deg, rgba(255,255,255,.03), rgba(255,255,255,.01));
    }}
    tbody tr:hover {{ box-shadow: 0 0 0 1px var(--accent); background: rgba(139,92,246,.05); }}
    td {{ border: 0; padding: 8px 0; display: flex; justify-content: space-between; align-items: baseline; gap: 12px; }}
    td::before {{
      content: attr(data-label); font-family: var(--font-mono); font-size: 10px; letter-spacing: .12em;
      text-transform: uppercase; color: var(--muted); flex-shrink: 0;
    }}
    td:first-child {{ display: block; padding: 12px 0 6px; }}
    td:first-child::before {{ content: none; }}
    .repo-desc {{ max-width: none; }}
    td[data-label="Language"] i {{ display: none; }}
  }}
</style>
</head>
<body>
  <div class="wrap">
    <p class="overline">Nova Lux · Observatory</p>
    <h1>Fleet <span class="grad">Registry</span></h1>
    <p class="lede">Every live repository under NovaLux12 — status orb, last telemetry, stars and latest release. Enriched nightly by the build pipeline; search, sort and filter are yours. <span class="count-pill">{n_eff} repos</span></p>

    <section class="glass" aria-labelledby="fleet-h">
      <h2 id="fleet-h" class="sr-only" style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);">Fleet table</h2>
      <div class="toolbar">
        <div class="search">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>
          <input type="search" placeholder="Search name, description, language, tag…" aria-label="Search repositories" autocomplete="off" />
        </div>
        <div class="chips" role="group" aria-label="Filter by language">
          <button class="chip" type="button" aria-pressed="true">All<span class="n">{n_eff}</span></button>
          <button class="chip" type="button" aria-pressed="false">Go<span class="n">9</span></button>
          <button class="chip" type="button" aria-pressed="false">Python<span class="n">4</span></button>
          <button class="chip" type="button" aria-pressed="false">TypeScript<span class="n">3</span></button>
          <button class="chip" type="button" aria-pressed="false">HTML<span class="n">1</span></button>
        </div>
      </div>
      <div class="table-scroll">
      <table aria-describedby="fleet-note">
        <caption class="sr-only" style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);">NovaLux12 fleet — repository, status, last push, stars, language, latest release</caption>
        <thead>
          <tr>
            <th scope="col" aria-sort="none">Repository<span class="arrow">▼</span></th>
            <th scope="col" aria-sort="none">Status<span class="arrow">▼</span></th>
            <th scope="col" aria-sort="descending">Last push<span class="arrow">▼</span></th>
            <th scope="col" aria-sort="none">Stars<span class="arrow">▼</span></th>
            <th scope="col" aria-sort="none">Language<span class="arrow">▼</span></th>
            <th scope="col" aria-sort="none">Latest release<span class="arrow">▼</span></th>
          </tr>
        </thead>
        <tbody>
{rows_html}
        </tbody>
      </table>
      </div>
      <p id="fleet-note" class="foot">
        <span class="mono">SNAPSHOT {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d')} · REGENERATED DAILY 00:00 UTC</span>
        <span><a href="https://github.com/NovaLux12" rel="noopener">github.com/NovaLux12</a> · <a href="history.jsonl" rel="noopener">history</a></span>
      </p>
    </section>
  </div>
</body>
</html>"""

out = os.path.join(ROOT, ".gauntlet/pieces/fleet.html")
with open(out, "w") as f:
    f.write(page)
print("WROTE", out, len(page), "bytes,", n_eff, "repos")