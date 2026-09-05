#!/bin/bash
cd /tmp/gauntlet-status
bash .gauntlet/run-agent.sh gauntlet-build-identity-r1c opencode-go/glm-5.3 /tmp/gauntlet-status/.gauntlet/prompts/identity-r1c.txt /tmp/gauntlet-status/.gauntlet/out/identity-r1c.json 900 /tmp/gauntlet-status/.gauntlet/pieces/identity.html &
bash .gauntlet/run-agent.sh gauntlet-build-fleet-r1c opencode-go/glm-5.3 /tmp/gauntlet-status/.gauntlet/prompts/fleet-r1c.txt /tmp/gauntlet-status/.gauntlet/out/fleet-r1c.json 900 /tmp/gauntlet-status/.gauntlet/pieces/fleet.html &
wait
echo R1C_DONE
