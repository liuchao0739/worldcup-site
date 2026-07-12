#!/usr/bin/env bash
# 在服务器上安装 cron：每 15 分钟自动更新 data.json
set -euo pipefail

ROOT="/opt/worldcup-site"
RUN='cd '"$ROOT"' && docker run --rm --memory=96m --memory-swap=96m -v '"$ROOT"':/app -w /app node:22-alpine node scripts/update-data.mjs'
LINE="*/15 * * * * $RUN >> /var/log/worldcup-update.log 2>&1"

TMP=$(mktemp)
crontab -l 2>/dev/null | grep -v 'worldcup-site.*node:22-alpine' > "$TMP" || true
echo "$LINE" >> "$TMP"
crontab "$TMP"
rm -f "$TMP"
echo "✅ cron 已更新：每 15 分钟自动更新 data.json（Docker 限 96MB）"
