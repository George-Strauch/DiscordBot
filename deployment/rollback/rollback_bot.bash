#!/usr/bin/env bash
set -euo pipefail
ROLLBACK_COMMIT="HEAD~1"   # Edit to target a specific commit
SSH_HOST="discord-bot"
BOT_DIR="~/DiscordBot"

echo "======================================"
echo "Rolling Back Discord Bot"
echo "======================================"
ssh -t "${SSH_HOST}" "cd ${BOT_DIR} && git checkout ${ROLLBACK_COMMIT} && docker compose up -d --build && docker logs -f discord-bot"
