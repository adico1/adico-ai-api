#!/bin/zsh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
PORT="${ADICO_API_PORT:-8843}"
if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "[adico-ai-api] already up → http://127.0.0.1:${PORT}/health"
  exit 0
fi
echo "[adico-ai-api] → http://127.0.0.1:${PORT}"
exec python3 -m adico_ai_api.server
