#!/bin/bash
# Robust subagent runner: retries runs with empty/error completions.
# Usage: run-agent.sh <session-key> <model> <abs-prompt-file> <abs-out-json> <timeout-s> <marker> [abs-verify-file]
set -u
KEY="$1"; MODEL="$2"; PROMPT="$3"; OUT="$4"; TIMEOUT="${5:-900}"; MARKER="${6:-}"; VERIFY="${7:-}"
for attempt in 1 2 3 4; do
  timeout "$TIMEOUT" openclaw agent --agent hex-work --model "$MODEL" --session-key "$KEY" --message-file "$PROMPT" --json > "$OUT" 2>/dev/null
  code=$?
  ok=""
  if [ -s "$OUT" ]; then
    text=$(python3 -c "
import json,sys
try:
    d=json.load(open('$OUT'))
    t=(d.get('result') or {}).get('payloads') or [{}]
    txt=t[0].get('text','') if t else ''
    print(txt.strip()[:400])
except Exception:
    print('')
" 2>/dev/null)
    bad=$(python3 -c "
import sys
t=sys.argv[1]
bad_markers=['Tool Call failed','no final summary was produced','Run failed','Error:','Cannot read property']
print('BAD' if any(b in t for b in bad_markers) else 'OK')
" "$text" 2>/dev/null)
    if [ -n "$text" ] && [ "$bad" != "BAD" ]; then
      if [ -z "$MARKER" ] || [[ "$text" == *"$MARKER"* ]]; then ok=1; fi
    fi
  fi
  if [ -z "$ok" ] && [ -n "$VERIFY" ] && [ -s "$VERIFY" ] && [ $(stat -c%s "$VERIFY" 2>/dev/null || echo 0) -gt 2048 ]; then
    ok=1
  fi
  if [ -n "$ok" ]; then
    echo "RUN_OK $KEY attempt=$attempt code=$code" >> "${OUT}.log"
    exit 0
  fi
  echo "RUN_RETRY $KEY attempt=$attempt code=$code text='${text:0:80}'" >> "${OUT}.log"
  sleep 5
done
echo "RUN_FAILED $KEY after 4 attempts" >> "${OUT}.log"
exit 1