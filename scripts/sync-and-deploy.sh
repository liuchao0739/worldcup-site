#!/usr/bin/env bash
# 在本机（Mac）执行：拉取 Wikipedia → 有变化才 deploy
# 建议本机 cron：*/15 * * * * /Users/liuchao/worldcup-site/scripts/sync-and-deploy.sh >> /tmp/worldcup-sync.log 2>&1
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

HASH_BEFORE=$(md5 -q site/data.json)
node scripts/update-data.mjs
HASH_AFTER=$(md5 -q site/data.json)

if [ "$HASH_BEFORE" != "$HASH_AFTER" ]; then
  echo "[deploy] data.json changed, syncing…"
  "$ROOT/deploy.sh"
else
  echo "[skip] no content change"
fi
