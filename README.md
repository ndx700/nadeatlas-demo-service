# NadeAtlas Demo Service

独立的 CS2 职业比赛 Demo 索引与自动同步服务。

## Public index

固定索引：

https://raw.githubusercontent.com/ndx700/nadeatlas-demo-service/main/index.json

`index.json` 永远是 UTF-8 JSON 数组。只有已验证、可直接下载、且能可靠确认是 `de_dust2` 的真实 Demo 才会写入；没有合格 Demo 时保持 `[]`。

## Scope

- 来源 cs.rlin.dev 公开职业比赛存档：它列出的全部赛事（目前约 2026 年 1 月起），不限战队、不限时间窗口
- `index.json` 只收录 `de_dust2`（App 现有约定不变）
- `index-all-maps.json` 收录所有地图，格式相同，`map` 字段区分地图
- 每个条目带 `matchId`，有解析统计时带 `statsUrl`
- 一张地图一个索引条目
- 新到旧排序
- 来源二 HLTV：app 在线版在手机上用系统 WebView（真实浏览器内核）打开 HLTV 页面，拿到 demo 直链后在手机上下载、只解析 Dust2，把录像（.nar）传到本仓库 Release `hltv-replays`，并写 `data/hltv/<matchId>.json`；同步时合并进索引，条目带 `replay`（解析好的录像地址），app 直接打开不再解析。runner 不直接请求 HLTV
- 除上面的真实浏览器外，不绕过登录、验证码、Cloudflare 或其他访问控制
- 不发布假 Demo、示例 URL、pending URL
- Better-CS-API Key 只从 GitHub Actions Secret `BETTER_CS_API_KEY` 读取

## Storage

验证后的 Demo 计划上传到本仓库滚动 GitHub Release `demos`，索引使用 Release 的 HTTPS 下载地址。

## Setup

在仓库 Settings → Secrets and variables → Actions → New repository secret 中添加：

- Name: `BETTER_CS_API_KEY`
- Secret: Better-CS-API Dashboard 生成的 API Key

不要把 Key 写入 issue、代码、README 或聊天。

## Team logos

- `logos/<slug>.png`：从比赛元数据里的队标地址下载，统一 512×512 透明底
- `team_logos.json`：战队名 → 图标地址（旧格式保留）
- `team_colors.json`：战队名 → `{logo, primary, secondary}`，卡片背景从 primary 渐变到 secondary

## Status

`status.json` 只记录非敏感同步状态，不记录 API Key。
