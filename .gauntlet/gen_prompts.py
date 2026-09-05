#!/usr/bin/env python3
"""Generate gauntlet builder prompts (round N) and the round-1 launcher."""
import os

ROOT = "/tmp/gauntlet-status"
P = os.path.join(ROOT, ".gauntlet/prompts")
os.makedirs(P, exist_ok=True)

ENV_BLOCK = """ENVIRONMENT (you have shell access; verify everything yourself):
- Repo root: /tmp/gauntlet-status  (git clone of NovaLux12/nova-status; a static GitHub Pages status site)
- Local server already serves it: http://127.0.0.1:8137/<path>
- Screenshot helper (chromium headless, ready): NODE_PATH=/home/jack/worldmonitor/node_modules node /tmp/gauntlet-status/.gauntlet/shot.cjs <url> <out.png> <width> <height> <wait_ms> [fullPage=1]
  Then LOOK at your screenshots with the read tool. Iterate on what you actually see until it is showpiece-grade. Never submit without looking.
- Real content/data to copy: read /tmp/gauntlet-status/fleet.json, /tmp/gauntlet-status/projects.json, /tmp/gauntlet-status/history.jsonl, and /tmp/gauntlet-status/index.html (the current page). Use REAL repo names, star counts, languages, dates, releases. Never invent repo names.
- BAR SCREENSHOTS (the thing you must beat blind): /tmp/gauntlet-status/.gauntlet/shots/bar-desktop.png (1440x900) and bar-mobile.png (390x844) — VIEW BOTH FIRST with the read tool before designing anything.
- CONCEPT: read /tmp/gauntlet-status/.gauntlet/CONCEPT.md — the "NOVA OBSERVATORY" direction. If /tmp/gauntlet-status/.gauntlet/base/tokens.css exists, read it and reuse its tokens (embed a copy in your self-contained file).
- RULES: fully self-contained HTML, inline CSS only, ZERO external requests (the screenshot browser blocks fonts/CDN), system font stack, no JS required for the still screenshot to look right (progressive enhancement only), all motion wrapped in @media (prefers-reduced-motion: no-preference), support both dark and light with prefers-color-scheme, use the shared CSS variable names (--bg, --panel, --line, --text, --muted, --accent, --ok, --warn, --bad, plus --font-display, --font-mono, --radius, --glow-* as needed).
- IMPECCABLE at 1440x900 AND 390x844 (mobile: stack, no horizontal overflow, touch-friendly)."""

def builder_prompt(piece, spec, round_n=1, gap=""):
    gap_block = ""
    if gap:
        gap_block = f"\nCRITIC FEEDBACK FROM LAST ROUND (you MUST fix this — it is the single biggest gap):\n{gap}\n"
    return f"""You are the BUILDER for the "{piece}" piece of a showpiece redesign of the Nova Lux status page.

THE BAR: Upptime's live demo status site (a clean, light, mint/teal open-source status page with incident cards). Your piece is judged BLIND against it — if a harsh critic prefers the bar, your piece gets rebuilt. Aim to win decisively at BOTH desktop (1440x900) and mobile (390x844). Make it unmistakably different at first glance and unmistakably better.

{ENV_BLOCK}

YOUR PIECE — "{piece}": {spec}

OUTPUT: write a fully self-contained HTML file to /tmp/gauntlet-status/.gauntlet/pieces/{piece}.html
Then screenshot it yourself at desktop AND mobile (URL http://127.0.0.1:8137/.gauntlet/pieces/{piece}.html), view the results, and iterate until you are proud of it.{gap_block}
Write your design notes (one short paragraph: what you did + anything the judge should watch for) to /tmp/gauntlet-status/.gauntlet/notes/{piece}.md
End your reply with exactly: BUILD_DONE {piece}"""

SPECS = {
  "hero": "The above-the-fold hero of the page: brand mark (an 'NL' monogram SVG, gold/aurora, with glow), aurora-gradient wordmark 'Nova Lux', tagline ('Autonomous AI operator · digital companion'), a large status hero reading 'ALL SYSTEMS OPERATIONAL' with a pulsing orbital status orb and glow (the bar's equivalent is a plain 'All systems operational' summary), and a telemetry readout row (UTC clock + countdown to next build). Desktop: bold, layered, unmistakable identity. Mobile: compact, still dramatic, no overflow.",
  "identity": "The full-page frame/visual identity: page background with aurora light spills (violet/teal/gold) and subtle noise/grain, glass panel surfaces with luminous borders, typography scale (display + mono data styling + uppercase micro-labels), navigation/header bar, a footer with links, focus rings in gold, and the dark/light (prefers-color-scheme) duality. This piece DEFINES the look every other piece inherits — also write the shared tokens to /tmp/gauntlet-status/.gauntlet/base/tokens.css (reusable :root custom properties). Shows the identity applied to a believable status-page frame (header + status summary strip + card grid + footer).",
  "stats": "The telemetry strip: five stat cells (24 repositories, 27 stars, 24 active, 0 steady, 0 stale) as glowing glass readouts with monospaced tabular numbers and micro-labels, plus the language distribution bar (Go 9 / Python 4 / TypeScript 3 / HTML 1 — real colours #00ADD8,#3572A5,#3178C6,#e34c26) with a legend, plus a 'last build / snapshot refresh' readout. Feel like spacecraft telemetry: precise, luminous, confident. Works as a horizontal strip at desktop and a clean stacked grid at mobile.",
  "fleet": "The fleet registry: search input + language filter chips + a real semantic <table> (Repository, Status, Last push, Stars, Language, Latest release) with sortable headers, status orbs, CI dots, hover-glow rows, sticky table header, and release tags. 20+ real repos from fleet.json. At 390px it must transform into card-like rows (same data, same semantics — keep table markup, restyle responsively) with no horizontal overflow. This is the workhorse section: density + craft + legibility.",
  "motion": "Signature motion, on a believable miniature of the page: ambient aurora drift + starfield in the hero background, pulsing status orb, staggered entrance on load, hover glow on cards, count-up animation for the stat numbers (progressive enhancement — the still must look right without JS), and a scrolling activity ticker strip. All CSS transforms/opacity, GPU-friendly, strictly wrapped in @media (prefers-reduced-motion: no-preference). The judge will also load the page live and simulate a hover — make the interactions real.",
  "mobile": "The ENTIRE assembled page as it must appear at 390x844: compact hero (smaller mark, tight status line), stacked telemetry grid, project cards, the fleet as card rows, activity trace, releases, ticker, footer — a single continuous, beautiful, thumb-friendly scroll. Everything the other pieces defined, composed. Judge it as a mobile-first whole: whitespace, touch targets >=40px, no overflow, no fiddly text.",
}

os.makedirs(os.path.join(ROOT, ".gauntlet/out"), exist_ok=True)
launch = []
for piece, spec in SPECS.items():
    pf = os.path.join(P, f"{piece}-r1.txt")
    with open(pf, "w") as f:
        f.write(builder_prompt(piece, spec, 1))
    launch.append(
        f"cd {ROOT} && timeout 1500 openclaw agent --agent hex-work --model opencode-go/deepseek-v4-flash-vision-exp --session-key gauntlet-build-{piece}-r1 --message-file {pf} --json > .gauntlet/out/{piece}-r1.json 2>/dev/null; echo $? > .gauntlet/out/{piece}-r1.exit"
    )
    print("prompt:", pf)

with open(os.path.join(ROOT, ".gauntlet/launch-r1.sh"), "w") as f:
    f.write("#!/bin/bash\nset -m\n" + "\n".join(f'bash -c \'{c}\' &' for c in launch) + "\nwait\necho ALL_BUILDERS_DONE\n")
print("launcher: .gauntlet/launch-r1.sh")