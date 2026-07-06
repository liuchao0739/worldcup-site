#!/usr/bin/env bash
# 在服务器上安装 cron：每 15 分钟自动更新 data.json
set -euo pipefail

ROOT="/opt/worldcup-site"
RUN='cd '"$ROOT"' && docker run --rm -v '"$ROOT"':/app -w /app node:22-alpine node scripts/update-data.mjs'
LINE="*/15 * * * * $RUN >> /var/log/worldcup-update.log 2>&1"

if crontab -l 2>/dev/null | grep -q 'worldcup-site.*node:22-alpine'; then
  echo "✅ cron 已存在"
else
  (crontab -l 2>/dev/null; echo "$LINE") | crontab -
  echo "✅ 已添加 cron：每 15 分钟自动更新 data.json"
fi
