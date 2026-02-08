#!/usr/bin/env bash
set -euo pipefail
SSH_HOST="discord-bot"   # Configure in ~/.ssh/config (see deployment/README.md)
BOT_DIR="~/DiscordBot"
LOCAL_BOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "======================================"
echo "Deploying Discord Bot"
echo "======================================"
echo "[LOCAL] Pushing to origin/master..."
cd "${LOCAL_BOT_DIR}"
git push origin master --tags

echo "[REMOTE] Deploying..."
ssh -t "${SSH_HOST}" "cd ${BOT_DIR} && git pull origin master && docker compose up -d --build && docker logs -f discord-bot"

echo "======================================"
echo "Bot Deployment Complete"
echo "======================================"
