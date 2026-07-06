# worldcup-site

2026 美加墨世界杯赛程追踪页，线上地址：https://worldcup.xiandan.me

**完整部署文档**（DNS / Caddy / cron 自动更新 / 排错）：见 Seafile  
`私人资料库/Seafile/世界杯赛程-worldcup.xiandan.me-部署实战记录.md`

## 结构

```
site/           静态页面 + data.json
scripts/        数据更新脚本（Wikipedia → data.json）
deploy.sh       rsync 部署到服务器
docker-compose.yml
```

## 本地开发

编辑 `site/index.html` 或 `site/data.json`，浏览器直接打开 `site/index.html`（需本地 HTTP 服务才能 fetch data.json）。

## 部署

```bash
./deploy.sh
```

## 服务器自动更新

每 15 分钟从 Wikipedia 拉取赛果写入 `data.json`（cron + Docker node）：

```bash
# 服务器上
/opt/worldcup-site/scripts/install-cron.sh
/opt/worldcup-site/scripts/run-update.sh   # 手动触发
tail -f /var/log/worldcup-update.log
```

页面每 15 分钟自动 `fetch('data.json')` 刷新，切回标签页也会补刷。
