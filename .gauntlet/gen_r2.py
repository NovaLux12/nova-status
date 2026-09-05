#!/usr/bin/env python3
"""Round-2+ builder prompts: regenerate a piece with the critic's gap as feedback.
Usage: gen_r2.py <piece> <round>  — reads .gauntlet/verdicts/<piece>-r<R-1>.json gap."""
import json, os, sys

ROOT = "/tmp/gauntlet-status"
P = os.path.join(ROOT, ".gauntlet/prompts")

SPECS = {
  "hero": "The above-the-fold hero of the page: brand mark (an 'NL' monogram SVG, gold/aurora, with glow), aurora-gradient wordmark 'Nova Lux', tagline ('Autonomous AI operator · digital companion'), a large status hero reading 'ALL SYSTEMS OPERATIONAL' with a pulsing orbital status orb and glow (the bar's equivalent is a plain 'All systems operational' summary), and a telemetry readout row (UTC clock + countdown to next build). Desktop: bold, layered, unmistakable identity. Mobile: compact, still dramatic, no overflow.",
  "identity": "The full-page frame/visual identity: page background with aurora light spills (violet/teal/gold) and subtle noise/grain, glass panel surfaces with luminous borders, typography scale (display + mono data styling + uppercase micro-labels), a navigation/header bar with the 'NL' monogram, a status summary strip (ALL SYSTEMS OPERATIONAL + pulsing orb + uptime-style stat chips), a card grid skeleton (4-6 placeholder cards with repo names), and a footer with links. Dark + light via prefers-color-scheme. Also keep the shared tokens at .gauntlet/base/tokens.css current.",
  "stats": "The telemetry strip: five stat cells (24 repositories, 27 stars, 24 active, 0 steady, 0 stale) as glowing glass readouts with monospaced tabular numbers and micro-labels, plus the language distribution bar (Go 9 / Python 4 / TypeScript 3 / HTML 1 — real colours #00ADD8,#3572A5,#3178C6,#e34c26) with a legend, plus a 'last build / snapshot refresh' readout. Feel like spacecraft telemetry: precise, luminous, confident. Horizontal strip at desktop, clean stacked grid at mobile.",
  "fleet": "The fleet registry: search input + language filter chips + a real semantic <table> (Repository, Status, Last push, Stars, Language, Latest release) with sortable headers, status orbs, CI dots, hover-glow rows, sticky table header, release tags. 20+ real repos from fleet.json. At 390px it transforms into card-like rows (same table markup, restyled) with no horizontal overflow. Density + craft + legibility.",
  "motion": "Signature motion, on a believable miniature of the page: ambient aurora drift + starfield in the hero background, pulsing status orb, staggered entrance on load, hover glow on cards, count-up animation for stats (progressive enhancement — still must look right without JS), and a scrolling activity ticker strip. All CSS transforms/opacity, GPU-friendly, wrapped in @media (prefers-reduced-motion: no-preference). The judge also loads the page live and simulates hover.",
  "mobile": "The ENTIRE assembled page at 390x844: compact hero, stacked telemetry grid, project cards, fleet as card rows, activity trace, releases, ticker, footer — a single continuous, thumb-friendly scroll. Touch targets >=40px, no overflow, no fiddly text.",
}

def gen(piece, rnd):
    prev = rnd - 1
    vpath = os.path.join(ROOT, f".gauntlet/verdicts/{piece}-r{prev}.json")
    gap = "The critic gave no gap feedback (verdict missing) — improve the piece beyond the current .gauntlet/pieces/{piece}.html and beat the bar at both viewports."
    if os.path.exists(vpath):
        v = json.load(open(vpath))
        gap = v.get("gap") or gap
        reason = v.get("reason") or ""
        gap = f"CRITIC (blind, anonymous): {reason} — GAP TO FIX: {gap}"
    base = open(os.path.join(P, f"{piece}-r1c.txt")).read() if os.path.exists(os.path.join(P, f"{piece}-r1c.txt")) else ""
    if not base:
        base = open(os.path.join(P, f"{piece}-r1.txt")).read()
    # strip old gap blocks, keep the rest
    import re
    base = re.sub(r"CRITIC FEEDBACK FROM LAST ROUND.*?(?=OUTPUT:|WRITE|YOUR PIECE|$)", "", base, flags=re.S)
    # replace the piece spec and inject gap near the end
    prompt = base + f"\n\nROUND {rnd} — THE PIECE YOU ARE BUILDING: \"{piece}\".\n{SPECS[piece]}\n\n{gap}\n\nSTRICT PROTOCOL: write the COMPLETE file in ONE write call to /tmp/gauntlet-status/.gauntlet/pieces/{piece}.html, verify with ls -la (must be >2KB), screenshot desktop+mobile (NODE_PATH=/home/jack/worldmonitor/node_modules node /tmp/gauntlet-status/.gauntlet/shot.cjs http://127.0.0.1:8137/.gauntlet/pieces/{piece}.html <out> 1440 900 2000, and 390 844), view both with the read tool, fix AT MOST twice, then final-verify and reply exactly: BUILD_DONE {piece}"
    out = os.path.join(P, f"{piece}-r{rnd}.txt")
    with open(out, "w") as f:
        f.write(prompt)
    print("wrote", out)

if __name__ == "__main__":
    gen(sys.argv[1], int(sys.argv[2]))