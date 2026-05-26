#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."
exec node apps/voice-agent/glam_public_proxy.js
