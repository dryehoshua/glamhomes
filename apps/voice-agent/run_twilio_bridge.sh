#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."
exec python3 apps/voice-agent/twilio_realtime_bridge.py
