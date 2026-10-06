# NadeAtlas Demo Service

独立的 CS2 职业比赛 Demo 索引与自动同步服务。

## Public index

固定索引：

https://raw.githubusercontent.com/ndx700/nadeatlas-demo-service/main/index.json

`index.json` 永远是 UTF-8 JSON 数组。只有已验证、可直接下载、且能可靠确认是 `de_dust2` 的真实 Demo 才会写入；没有合格 Demo 时保持 `[]`。

## Scope

- 固定 50 支战队白名单
- 最近约 2 个月
- 只收录 `de_dust2`
- 一张地图一个索引条目
- 新到旧排序
- 不绕过登录、验证码、Cloudflare 或其他访问控制
- 不发布假 Demo、示例 URL、pending URL
- Better-CS-API Key 只从 GitHub Actions Secret `BETTER_CS_API_KEY` 读取

## Storage

验证后的 Demo 计划上传到本仓库滚动 GitHub Release `demos`，索引使用 Release 的 HTTPS 下载地址。

## Setup

在仓库 Settings → Secrets and variables → Actions → New repository secret 中添加：

- Name: `BETTER_CS_API_KEY`
- Secret: Better-CS-API Dashboard 生成的 API Key

不要把 Key 写入 issue、代码、README 或聊天。

## Status

`status.json` 只记录非敏感同步状态，不记录 API Key。

## Feed for the app's 赛事 screen

`feed/ranking.json`、`feed/matches.json`、`feed/results.json` 由 `scripts/hltv_feed.py` 每 6 小时更新一次，数据来自 HLTV 的公开页面，通过开源库 [hltv-api](https://github.com/SocksPls/hltv-api)（AGPL-3.0）读取。脚本在运行时下载并原样执行该库，不把它的代码放进本仓库，也不做任何绕过 Cloudflare 的事：被拒绝时保留上一次的文件，并在 `feed/status.json` 里记下原因。

