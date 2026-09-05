#!/usr/bin/env python3
"""Generate a critic prompt for piece+round."""
import os, sys

piece, rnd = sys.argv[1], sys.argv[2]
ROOT = "/tmp/gauntlet-status"
P = os.path.join(ROOT, ".gauntlet/prompts")
os.makedirs(P, exist_ok=True)

prompt = f"""You are the CRITIC for the "{piece}" piece of the Nova Lux status page redesign. You are harsh and skeptical. Praise is not useful. A binary call is required.

CONTEXT: The bar is Upptime's live demo status site (clean light mint/teal page, incident cards, uptime stats). A builder just produced our candidate for this piece. You will judge ours vs the bar BLIND — you will be handed two anonymous screenshots (A and B) at each viewport and you must pick the better page by visual merit alone. One of A/B is the bar; the other is ours. You do not need to know which is which — judge purely on which page looks more professional, more polished, more impressive, better designed.

STEPS:
1. Screenshot the candidate's REAL output yourself (do not trust anyone else's screenshot):
   NODE_PATH=/home/jack/worldmonitor/node_modules node /tmp/gauntlet-status/.gauntlet/shot.cjs http://127.0.0.1:8137/.gauntlet/pieces/{piece}.html /tmp/gauntlet-status/.gauntlet/blind/{piece}/r{rnd}/candidate-desktop.png 1440 900 3000
   and the mobile variant: NODE_PATH=/home/jack/worldmonitor/node_modules node /tmp/gauntlet-status/.gauntlet/shot.cjs http://127.0.0.1:8137/.gauntlet/pieces/{piece}.html /tmp/gauntlet-status/.gauntlet/blind/{piece}/r{rnd}/candidate-mobile.png 390 844 2500
   If the page fails to render (blank, broken layout, unstyled), say so loudly in "reason" and pick the bar.
2. cd /tmp/gauntlet-status && python3 .gauntlet/pair.py {piece} {rnd}   (this relabels the shots anonymously as A/B)
   DO NOT read .gauntlet/blind/{piece}/r{rnd}/mapping.txt — it would break blindness. It exists only for the orchestrator.
3. View with the read tool, at BOTH viewports: .gauntlet/blind/{piece}/r{rnd}/A-desktop.png vs B-desktop.png, and A-mobile.png vs B-mobile.png.
4. Decide, on visual merit alone: layout, hierarchy, typography, colour, spacing, craft, consistency between desktop and mobile, and how "showpiece" each feels. The bar is good but beatable — ours must be clearly better, not merely comparable.

VERDICT: write to /tmp/gauntlet-status/.gauntlet/verdicts/{piece}-r{rnd}.json exactly:
{{"piece":"{piece}","round":{rnd},"winner":"A"|"B"|"TIE","reason":"<2-4 sentences, specific and technical, describing what won and why>","gap":"<THE single biggest remaining gap: one concrete thing the builder must fix next — or 'none — beat the bar on every axis'>"}}
End your reply with exactly: CRITIC_DONE {piece}"""

with open(os.path.join(P, f"{piece}-critic-{rnd}.txt"), "w") as f:
    f.write(prompt)
print(os.path.join(P, f"{piece}-critic-{rnd}.txt"))