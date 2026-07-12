#!/usr/bin/env bash
# 2G VPS 内存防护：earlyoom + sysctl + cron 限内存
# 在服务器上以 root 执行一次：bash /opt/worldcup-site/scripts/server-memory-guard.sh
set -euo pipefail

echo ">>> sysctl 调优"
cat > /etc/sysctl.d/99-seafile.conf << 'EOF'
# 内存有余时优先用 RAM；保留一定空闲页避免 OOM 雪崩
vm.swappiness=30
vm.min_free_kbytes=32768
vm.vfs_cache_pressure=150
EOF
sysctl -p /etc/sysctl.d/99-seafile.conf

echo ">>> 安装 earlyoom（内存不足时主动杀进程，避免整机假死）"
if ! command -v earlyoom >/dev/null 2>&1; then
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y earlyoom
fi

cat > /etc/default/earlyoom << 'EOF'
EARLYOOM_ARGS="-m 8,5 -r 120 -n --avoid dockerd --avoid sshd --avoid caddy"
EOF
systemctl enable earlyoom
systemctl restart earlyoom

echo ">>> 内存巡检 cron（每小时记录，可用内存 <120MB 时写告警）"
GUARD='/usr/local/bin/memory-watch.sh'
cat > "$GUARD" << 'EOF'
#!/usr/bin/env bash
LOG=/var/log/memory-watch.log
TS=$(date -Iseconds)
read -r total used free shared cache avail <<< "$(free -m | awk 'NR==2{print $2,$3,$4,$5,$6,$7}')"
MSG="$TS avail=${avail}MB used=${used}MB swap=$(free -m | awk 'NR==3{print $3}')MB"
echo "$MSG" >> "$LOG"
if [ "$avail" -lt 120 ]; then
  echo "$TS [WARN] low memory avail=${avail}MB" >> "$LOG"
  docker stats --no-stream --format '{{.Name}} {{.MemPerc}}' >> "$LOG" 2>/dev/null || true
fi
tail -n 200 "$LOG" > "${LOG}.tmp" && mv "${LOG}.tmp" "$LOG"
EOF
chmod +x "$GUARD"
CRON_LINE='0 * * * * /usr/local/bin/memory-watch.sh'
if ! crontab -l 2>/dev/null | grep -q memory-watch.sh; then
  (crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -
fi

echo ">>> 完成。验证："
free -h
systemctl is-active earlyoom
swapon --show
