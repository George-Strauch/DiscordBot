#!/usr/bin/env bash
set -euo pipefail
SSH_HOST="discord-bot"
CONTAINER_NAME="discord-bot"

echo "======================================"
echo "Stopping Discord Bot"
echo "======================================"
ssh -t "${SSH_HOST}" "docker stop ${CONTAINER_NAME} 2>/dev/null && echo 'Container stopped' || echo 'Container was not running'"
