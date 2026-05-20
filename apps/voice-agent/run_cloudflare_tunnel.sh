#!/usr/bin/env bash
set -euo pipefail

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "cloudflared no esta instalado."
  echo "Instalalo con: brew install cloudflared"
  echo "Luego autentica: cloudflared tunnel login"
  exit 1
fi

CONFIG_PATH="${CLOUDFLARE_TUNNEL_CONFIG:-apps/voice-agent/cloudflare-tunnel.example.yml}"

if [[ ! -f "$CONFIG_PATH" ]]; then
  echo "No encontre config de tunnel en: $CONFIG_PATH"
  exit 1
fi

exec cloudflared tunnel --config "$CONFIG_PATH" run glam-homes
