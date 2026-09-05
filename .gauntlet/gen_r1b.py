#!/usr/bin/env python3
"""Generate hardened R1b builder prompts for the failed pieces."""
import os

ROOT = "/tmp/gauntlet-status"
P = os.path.join(ROOT, ".gauntlet/prompts")

HARDEN = """EXECUTION RULES (strict — previous agents failed by not following these):
1. WRITE THE PIECE FILE FIRST — before any screenshot — using the write tool to /tmp/gauntlet-status/.gauntlet/pieces/<piece>.html. Never leave it to the end.
2. Then confirm with: ls -la /tmp/gauntlet-status/.gauntlet/pieces/<piece>.html  (must exist, non-empty).
3. Then screenshot at desktop AND mobile, view both, and refine. Make AT MOST 3 refinement iterations (edit -> screenshot -> view). More iterations do not help; judgment does.
4. Before your final reply, re-verify the file exists and is non-empty, then write the notes file.
5. If any tool call fails, retry it once, then move on. Never end without the file written."""

def hardened(spec, piece):
    base = open(os.path.join(P, f"{piece}-r1.txt")).read()
    base = base.replace(
        "OUTPUT: write a fully self-contained HTML file",
        "OUTPUT: write a fully self-contained HTML file")
    base += "\n\n" + HARDEN.replace("<piece>", piece)
    return base

for piece, spec in [
    ("hero", None), ("motion", None), ("fleet", None),
]:
    txt = hardened(spec, piece)
    with open(os.path.join(P, f"{piece}-r1b.txt"), "w") as f:
        f.write(txt)
    print("wrote", f"{piece}-r1b.txt")