#!/usr/bin/env python3
"""Generate fleet-r1c prompt (one-shot write protocol, GLM builder)."""
import os
ROOT = "/tmp/gauntlet-status"
P = os.path.join(ROOT, ".gauntlet/prompts")

spec = """The fleet registry section of the NOVA OBSERVATORY status page: a search input, language filter chips, and a real semantic <table> with columns Repository (name link + CI dot + one-line description), Status (orb + label), Last push (mono date), Stars (mono ★n), Language, Latest release (tag pill). Sortable headers (▲/▼ affordance), sticky table header, hover-glow rows, generous padding, uppercase micro-label column heads. Use 20+ REAL repos from /tmp/gauntlet-status/fleet.json (real names, stars, languages, push dates, release tags). At 390px the table restyles into stacked card-like rows (SAME table markup, responsive CSS only) with no horizontal overflow. Density + craft + legibility: this is the workhorse of the page."""

prompt = f"""You are the BUILDER for the "fleet" piece of a showpiece redesign of the Nova Lux status page. You are a precise engineer-designer: build it ONCE, completely, then verify.

THE BAR (judged blind against you): Upptime live demo status site — clean light mint/teal page with incident cards and uptime stats. View /tmp/gauntlet-status/.gauntlet/shots/bar-desktop.png and bar-mobile.png with the read tool FIRST. You must beat it at desktop AND mobile. Unmistakably different, unmistakably better.

CONCEPT: read /tmp/gauntlet-status/.gauntlet/CONCEPT.md (NOVA OBSERVATORY: deep-space telemetry, aurora glass, gold accent, mono readouts). If /tmp/gauntlet-status/.gauntlet/base/tokens.css exists, embed its tokens in your file's :root.

DATA: read /tmp/gauntlet-status/fleet.json — use REAL repo names/stars/languages/dates/releases. 20+ rows.

YOUR PIECE: {spec}

STRICT PROTOCOL (previous agents failed by dribbling partial files):
1. Compose the ENTIRE file in your head first, then write it in ONE write-tool call to /tmp/gauntlet-status/.gauntlet/pieces/fleet.html. Fully self-contained: inline CSS only, zero external requests, system fonts, no JS required for the still screenshot (progressive enhancement only; the search/chips/sort are static-looking in the screenshot), table markup + responsive card restyle at 390px, CSS custom properties on :root.
2. Verify: ls -la /tmp/gauntlet-status/.gauntlet/pieces/fleet.html
3. Screenshot: NODE_PATH=/home/jack/worldmonitor/node_modules node /tmp/gauntlet-status/.gauntlet/shot.cjs http://127.0.0.1:8137/.gauntlet/pieces/fleet.html /tmp/gauntlet-status/.gauntlet/pieces/fleet-check-desktop.png 1440 900 2000 (and mobile 390 844). View BOTH with the read tool.
4. If something is obviously broken, make at most ONE corrective edit pass (single write call, re-screenshot). Otherwise stop.
5. Write notes to /tmp/gauntlet-status/.gauntlet/notes/fleet.md, then reply with exactly: BUILD_DONE fleet"""

os.makedirs(P, exist_ok=True)
with open(os.path.join(P, "fleet-r1c.txt"), "w") as f:
    f.write(prompt)
print("wrote fleet-r1c.txt")