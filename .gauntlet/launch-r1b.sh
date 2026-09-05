#!/bin/bash
set -m
for p in hero motion fleet; do
  bash -c "cd /tmp/gauntlet-status && timeout 900 openclaw agent --agent hex-work --model opencode-go/deepseek-v4-flash-vision-exp --session-key gauntlet-build-${p}-r1b --message-file .gauntlet/prompts/${p}-r1b.txt --json > .gauntlet/out/${p}-r1b.json 2>/dev/null; echo \$? > .gauntlet/out/${p}-r1b.exit" &
done
wait
echo R1B_DONE
