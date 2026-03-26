#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/var/www/gg-factory"
HEALTH_URL="http://localhost:8000/health"

echo "── GG AI Factory Deploy ──"

cd "$APP_DIR"
echo "→ Pulling latest..."
git pull origin main

echo "→ Installing dependencies..."
source .venv/bin/activate
pip install -r requirements.txt --quiet

echo "→ Restarting service..."
sudo systemctl restart gg-factory

echo "→ Waiting for startup..."
sleep 2

echo "→ Health check..."
STATUS=$(curl -sf "$HEALTH_URL" | python3 -c "import sys,json;print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "FAIL")

if [ "$STATUS" = "ok" ]; then
  echo "✓ Deploy successful — service is healthy"
else
  echo "✗ Health check failed!"
  sudo journalctl -u gg-factory --no-pager -n 20
  exit 1
fi
