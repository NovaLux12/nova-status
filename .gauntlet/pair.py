#!/usr/bin/env python3
"""Blind pairing: relabel bar + candidate shots as A/B with random mapping.
Usage: pair.py <piece> <round>
Writes A-<vp>.png / B-<vp>.png in .gauntlet/blind/<piece>/r<N>/ and mapping.txt
(consumed only by the orchestrator after the critic verdicts).
"""
import random, sys, shutil, os

piece, rnd = sys.argv[1], sys.argv[2]
blind = f".gauntlet/blind/{piece}/r{rnd}"
os.makedirs(blind, exist_ok=True)
bar = ".gauntlet/shots/bar-{vp}.png"
cand = f"{blind}/candidate-{{vp}}.png"
order = random.Random(f"{piece}-{rnd}").choice([("A","B"),("B","A")])
for vp in ("desktop", "mobile"):
    bar_vp = bar.replace("{vp}", vp)
    cand_vp = cand.replace("{vp}", vp)
    for label, src in ((order[0], bar_vp), (order[1], cand_vp)):
        dst = f"{blind}/{label}-{vp}.png"
        shutil.copy(src, dst)
with open(f"{blind}/mapping.txt", "w") as f:
    f.write(f"bar={order[0]}, candidate={order[1]}\n")  # e.g. bar=A, candidate=B
print("PAIRED", piece, rnd)
