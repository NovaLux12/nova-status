#!/usr/bin/env python3
"""Decode a round's blind verdicts: did OUR candidate win?
Reads .gauntlet/verdicts/<piece>-r<N>.json + .gauntlet/blind/<piece>/r<N>/mapping.txt.
Usage: decode.py <piece> <round>   (or: decode.py all <round>)"""
import json, os, sys

ROOT = "/tmp/gauntlet-status"

def decode(piece, rnd):
    v = os.path.join(ROOT, f".gauntlet/verdicts/{piece}-r{rnd}.json")
    m = os.path.join(ROOT, f".gauntlet/blind/{piece}/r{rnd}/mapping.txt")
    if not os.path.exists(v):
        return {"piece": piece, "round": rnd, "state": "NO_VERDICT"}
    verdict = json.load(open(v))
    mapping = {}
    if os.path.exists(m):
        line = open(m).read().strip()
        parts = line.replace("bar=", "").replace("candidate=", "").split(", ")
        mapping = {"bar": parts[0], "candidate": parts[1]}
    winner = verdict.get("winner", "?")
    ours = mapping.get("candidate", "?")
    if winner == "TIE":
        state = "TIE"
    elif winner == ours:
        state = "WIN"
    else:
        state = "LOSE"
    return {"piece": piece, "round": rnd, "winner": winner, "candidateWas": ours,
            "barWas": mapping.get("bar", "?"), "state": state,
            "reason": verdict.get("reason", ""), "gap": verdict.get("gap", "")}

if __name__ == "__main__":
    piece, rnd = sys.argv[1], sys.argv[2]
    if piece == "all":
        alls = decode("all", rnd)  # placeholder
        results = []
        for p in ["hero", "identity", "stats", "fleet", "motion", "mobile"]:
            results.append(decode(p, rnd))
        print(json.dumps(results, indent=1))
    else:
        print(json.dumps(decode(piece, rnd), indent=1))