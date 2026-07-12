#!/usr/bin/env bash
# 手动执行一次数据更新（服务器无本地 node 时用 Docker）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
docker run --rm --memory=96m --memory-swap=96m -v "$ROOT:/app" -w /app node:22-alpine node scripts/update-data.mjs
