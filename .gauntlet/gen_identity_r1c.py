#!/usr/bin/env python3
"""Generate identity-r1c prompt (one-shot write protocol, GLM builder)."""
import os
ROOT = "/tmp/gauntlet-status"
P = os.path.join(ROOT, ".gauntlet/prompts")

spec = """The full-page frame/visual identity of the NOVA OBSERVATORY design: page background with aurora light spills (violet/teal/gold) and subtle noise/grain, glass panel surfaces with luminous 1px borders, typography scale (display + mono data styling + uppercase micro-labels), a navigation/header bar with the 'NL' monogram, a status summary strip (ALL SYSTEMS OPERATIONAL + pulsing orb + uptime-style stat chips like the bar's summary), a card grid skeleton (4-6 placeholder cards with repo names), and a footer with links. Dark + light via prefers-color-scheme. Also write the shared tokens to /tmp/gauntlet-status/.gauntlet/base/tokens.css (reusable :root custom properties: --bg, --panel, --panel-solid, --line, --text, --muted, --accent, --aurora-a, --aurora-b, --ok, --warn, --bad, --font-display, --font-mono, --radius, --glow-*). The page must look complete and showpiece-grade at 1440x900 AND 390x844."""

prompt = f"""You are the BUILDER for the "identity" piece of a showpiece redesign of the Nova Lux status page. You are a precise engineer-designer: build it ONCE, completely, then verify.

THE BAR (judged blind against you): Upptime live demo status site — clean light mint/teal page with incident cards and uptime stats. View /tmp/gauntlet-status/.gauntlet/shots/bar-desktop.png and bar-mobile.png with the read tool FIRST. You must beat it at desktop AND mobile. Unmistakably different, unmistakably better.

CONCEPT: read /tmp/gauntlet-status/.gauntlet/CONCEPT.md (NOVA OBSERVATORY: deep-space telemetry, aurora glass, gold accent, mono readouts).

YOUR PIECE: {spec}

STRICT PROTOCOL (previous agents failed by dribbling partial files):
1. Compose the ENTIRE file in your head first, then write it in ONE write-tool call to /tmp/gauntlet-status/.gauntlet/pieces/identity.html. Fully self-contained: inline CSS only, zero external requests, system fonts, no JS required for the still screenshot (progressive enhancement only), all motion in @media (prefers-reduced-motion: no-preference), CSS custom properties on :root.
2. Also ONE write call for /tmp/gauntlet-status/.gauntlet/base/tokens.css (same tokens, as a shared file).
3. Verify both files: ls -la /tmp/gauntlet-status/.gauntlet/pieces/identity.html /tmp/gauntlet-status/.gauntlet/base/tokens.css
4. Screenshot: NODE_PATH=/home/jack/worldmonitor/node_modules node /tmp/gauntlet-status/.gauntlet/shot.cjs http://127.0.0.1:8137/.gauntlet/pieces/identity.html /tmp/gauntlet-status/.gauntlet/pieces/identity-check-desktop.png 1440 900 2000 (and mobile 390 844). View BOTH with the read tool.
5. If something is obviously broken, make at most ONE corrective edit pass (write the whole corrected file again in a single write call, re-screenshot). Otherwise stop.
6. Write notes to /tmp/gauntlet-status/.gauntlet/notes/identity.md, then reply with exactly: BUILD_DONE identity"""

os.makedirs(P, exist_ok=True)
with open(os.path.join(P, "identity-r1c.txt"), "w") as f:
    f.write(prompt)
print("wrote identity-r1c.txt")