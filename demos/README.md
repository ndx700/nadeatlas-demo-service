# Demo 存档索引

HLTV demo 原始文件以 GitHub Release 附件形式存档（单文件超 git 100MB 限制），
本文件登记每场 demo 的存放位置与校验信息。下载脚本见 `download_demo.py` /
`get_demo_link.py`（自托管 Runner 使用，GitHub 托管 Runner 的 Azure IP 段被
r2-demos.hltv.org 封禁）。

## 已存档

### ESL Pro League Season 24 · Falcons vs Aurora（BO3）

- **Release**: [demo-epl-s24-falcons-vs-aurora](https://github.com/ndx700/nadeatlas-demo-service/releases/tag/demo-epl-s24-falcons-vs-aurora)
- **附件**: `esl-pro-league-season-24-falcons-vs-aurora-bo3.rar`（406.6 MB）+ `.sha256`
- **内含**: `falcons-vs-aurora-m1-mirage.dem`、`falcons-vs-aurora-m2-dust2.dem`
- **SHA-256**: `8e6befd046789c6d6286629dc95ff326f5dd91a47b78ad6ce25f031eda404e22`
- **完整性**: 官方 unrar `t` 测试 All OK（2026-10-07）
- **来源**: https://r2-demos.hltv.org/demos/131573/esl-pro-league-season-24-falcons-vs-aurora-bo3-SHwp6i5EMXqaP-2XyfqBwr.rar
- **校验注意**: 用 `unrar t`；ubuntu 自带 7-Zip 23.01 不支持该 RAR5 压缩方法，会误报 "Unsupported Method"
- **状态**: 验收基准文件，尚未解析入库、未写入正式地图索引
