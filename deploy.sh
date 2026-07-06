#!/usr/bin/env bash
set -euo pipefail

LOCAL="/Users/liuchao/worldcup-site"
REMOTE="seafile:/opt/worldcup-site"

rsync -avz --delete "$LOCAL/site/" "$REMOTE/site/"
rsync -avz "$LOCAL/scripts/" "$REMOTE/scripts/"
rsync -avz "$LOCAL/docker-compose.yml" "$REMOTE/"
ssh seafile "cd /opt/worldcup-site && docker compose up -d"

echo "✅ 已同步至 https://worldcup.xiandan.me"
