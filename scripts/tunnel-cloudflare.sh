#!/usr/bin/env bash
set -euo pipefail

PORT=${PORT:-3002}
URL="http://localhost:${PORT}"

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "cloudflared is not installed. Install with one of:" >&2
  echo "  brew install cloudflared    # macOS" >&2
  echo "  or download: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/" >&2
  exit 1
fi

echo "Starting Cloudflare Quick Tunnel to ${URL} (no login required)…"
echo "Tip: leave this process running to keep the URL alive."
echo
exec cloudflared tunnel --url "${URL}" --no-autoupdate

