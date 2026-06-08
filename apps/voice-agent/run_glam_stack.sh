#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOG_DIR="$ROOT/logs"
mkdir -p "$LOG_DIR"

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$HOME/.local/bin:$PATH"

load_openai_keychain_key() {
  if [[ -n "${OPENAI_API_KEY:-}" ]]; then
    return 0
  fi
  local account="${KEYCHAIN_ACCOUNT:-dryehoshuapython}"
  local key
  key="$(security find-generic-password -s codex.openai.api_key -a "$account" -w 2>/dev/null || true)"
  if [[ -n "$key" ]]; then
    export OPENAI_API_KEY="$key"
    return 0
  fi
  return 1
}

log() {
  printf '%s %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*" >> "$LOG_DIR/glam-stack.log"
}

port_is_listening() {
  lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
}

pid_is_alive() {
  local pid_file="$1"
  [[ -f "$pid_file" ]] || return 1
  local pid
  pid="$(tr -dc '0-9' < "$pid_file" || true)"
  [[ -n "$pid" ]] || return 1
  kill -0 "$pid" >/dev/null 2>&1
}

start_detached() {
  local name="$1"
  shift
  log "starting $name: $*"
  (
    cd "$ROOT"
    exec "$@"
  ) > "$LOG_DIR/$name.out" 2> "$LOG_DIR/$name.err" < /dev/null &
  echo $! > "$LOG_DIR/$name.pid"
}

ensure_port_process() {
  local name="$1"
  local port="$2"
  shift 2
  if port_is_listening "$port"; then
    return 0
  fi
  start_detached "$name" "$@"
}

ensure_cloudflared() {
  local pid_file="$LOG_DIR/cloudflared-glam.pid"
  if pid_is_alive "$pid_file"; then
    return 0
  fi
  if pgrep -f 'cloudflared.*glam-homes-token.*127.0.0.1:8890' >/dev/null 2>&1; then
    return 0
  fi
  start_detached "cloudflared-glam" "apps/voice-agent/run_cloudflare_tunnel.sh"
}

log "GLAM HOMES stack supervisor started"
if load_openai_keychain_key; then
  log "OpenAI API key loaded for GLAM runtime"
else
  log "OpenAI API key not available for GLAM runtime"
fi

while true; do
  ensure_port_process "server" 3000 "python3" "apps/voice-agent/server.py"
  ensure_port_process "twilio-bridge" 8877 "python3" "apps/voice-agent/twilio_realtime_bridge.py"
  ensure_port_process "public-proxy" 8890 "node" "apps/voice-agent/glam_public_proxy.js"
  ensure_cloudflared
  sleep "${GLAM_STACK_INTERVAL_SECONDS:-30}"
done
