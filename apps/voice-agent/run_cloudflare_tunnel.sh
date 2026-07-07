#!/usr/bin/env bash
set -euo pipefail

CLOUDFLARED_BIN="${CLOUDFLARED_BIN:-$(command -v cloudflared || true)}"
if [[ -z "$CLOUDFLARED_BIN" && -x "$HOME/.local/bin/cloudflared" ]]; then
  CLOUDFLARED_BIN="$HOME/.local/bin/cloudflared"
fi

if [[ -z "$CLOUDFLARED_BIN" ]]; then
  echo "cloudflared no esta instalado."
  echo "Instalalo con: brew install cloudflared"
  echo "Luego autentica: cloudflared tunnel login"
  exit 1
fi

TOKEN_FILE="${CLOUDFLARE_TUNNEL_TOKEN_FILE:-$HOME/.cloudflared/glam-homes-token}"
TUNNEL_PROTOCOL="${CLOUDFLARE_TUNNEL_PROTOCOL:-http2}"
if [[ -f "$TOKEN_FILE" ]]; then
  PROXY_URL="${GLAM_PUBLIC_PROXY_URL:-http://127.0.0.1:8890}"
  exec "$CLOUDFLARED_BIN" tunnel --no-autoupdate --protocol "$TUNNEL_PROTOCOL" run --token-file "$TOKEN_FILE" --url "$PROXY_URL"
fi

CONFIG_PATH="${CLOUDFLARE_TUNNEL_CONFIG:-apps/voice-agent/cloudflare-tunnel.example.yml}"

if [[ ! -f "$CONFIG_PATH" ]]; then
  echo "No encontre config de tunnel en: $CONFIG_PATH"
  exit 1
fi

exec "$CLOUDFLARED_BIN" tunnel --no-autoupdate --protocol "$TUNNEL_PROTOCOL" --config "$CONFIG_PATH" run glam-homes
