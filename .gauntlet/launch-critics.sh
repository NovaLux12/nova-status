#!/bin/bash
# Round-1 critics: one harsh blind critic per piece, in parallel.
cd /tmp/gauntlet-status
for p in hero identity stats fleet motion mobile; do
  mkdir -p .gauntlet/blind/$p/r1 .gauntlet/verdicts
  /tmp/gauntlet-status/.gauntlet/run-agent.sh gauntlet-critic-$p-r1 opencode-go/glm-5.3 /tmp/gauntlet-status/.gauntlet/prompts/$p-critic-1.txt /tmp/gauntlet-status/.gauntlet/out/$p-critic-r1.json 1200 CRITIC_DONE /tmp/gauntlet-status/.gauntlet/verdicts/$p-r1.json &
done
wait
echo ALL_CRITICS_DONE