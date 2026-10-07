# HLTV 下载任务接手记录

## 本次可确认的结果

- 恢复了仓库 `fix/hltv-browser-diagnostic-test` 分支上的旧单场下载器及自托管工作流，作为实现参考；本次新增独立批量脚本，不改变现有同步管线。
- 当前云浏览器能读取 HLTV 主站及 Spirit vs PARIVISION 比赛页（2398725），实际地图为 Ancient、Dust2、Anubis，页面 demo 属性是 `/download/demo/112384`。最终跳转至 r2 压缩包后持续安全验证。正常重载一次仍未放行，因此停止该站下载尝试。
- 从已有 GitHub Release 取回 Falcons vs Aurora 基准压缩包；它是旧成果的恢复，不计作新下载比赛。426,402,619 字节，SHA-256 与原交接文档一致。官方 unrar 7.23 完整性测试通过，解出的 Dust2 文件头为 `PBDEMS2\0`。详细校验数据见 `hltv_baseline_verification.json`。
- main 的 `index-all-maps.json` 有 98 个地图记录，其中 Dust2 11 条。另存为 `hltv_takeover_candidates.json`，只作候选来源记录，不冒充完整 HLTV 比赛页索引或本次已下载文件。
- 原沙箱脚本、完整试点索引、原 `manifest.json` 及后台进程均无法从当前环境恢复；不能把文档中的进度描述当作实时已完成进度。

## 批量下载器

新增 `scripts/batch_download.py`，采用正常有头 Chromium 页面导航及下载事件，使用实际地图框过滤 Dust2。读取与原交接文档一致的 `teams[].matches` 索引格式。

- 按 HLTV 数字比赛 ID 去重，不因 URL slug 不同重复下载。
- 场间隔默认 20 秒，最小 8 秒；串行下载。
- 遇站点验证或封锁立即停止整批，不自动解题、调整指纹、切换网络或反复重试。
- 只有下载完成、RAR 文件头正确、官方 unrar 测试成功后，才记录 `status=ok` 和 SHA-256。校验工具缺失时直接失败。
- 续跑要求 `status=ok`、文件存在、哈希匹配且完整性通过。损坏、缺失、尚未完成的记录不能直接跳过。
- 台账原子写入；输出锁防止两个批次同时修改；共有比赛用硬链接，不支持时复制并校验；已有不同内容的文件不覆盖。
- 完成文件可恢复；未完成的传输重新下载。没有实现 HTTP Range 字节续传。
- 支持旧台账记录的 `path`、`file` 或 `output` 字段，路径必须位于输出目录中。未知台账结构明确报错，不猜测、不清空。

## 执行

运行环境需要 Python 3.9+、Playwright、有头 Chromium 和官方 unrar。Linux 无显示器环境需 Xvfb。应在原本获得正常站点访问许可的执行环境运行；本次云浏览器被阻塞时不启动另一个客户端绕过。

```bash
python3 scripts/batch_download.py --index config/hltv_takeover_seed.json --out pilot_demos --dry-run

# 用恢复后的完整 dust2_index.json 替换索引参数即可。
UNRAR=/path/to/official/unrar xvfb-run -a python3 -u scripts/batch_download.py \
  --index dust2_index.json --out pilot_demos --limit 10 --delay 20

python3 -m unittest discover -s tests -p 'test_hltv_batch.py' -v
```

`config/hltv_takeover_seed.json` 只有本次确实查看的一场比赛，用于 dry-run/试点，不能代表 51 场或 Top20 六个月全量。退出码：0 为索引全部完成，1 为部分未完成/环境或文件错误，3 为站点验证阻塞。达到 `--limit` 但仍有未完成记录时退出 1，不能视为全量成功。

## 数量与验证限制

交接文档各队场次数为 7+13+10+8+8+11=57，却写 total=51 和待下50+基准1，且同时写共有6场。这些数字可能混用了队伍归属数量与去重后场数；只有原始索引能确定真实计划。新脚本分别计算 `team_memberships`、`unique_matches` 和 `shared_memberships`，不采用声明 total 推断完成量。

15 项离线测试通过，覆盖去重、危险路径、双写锁、台账落盘、RAR 假头、哈希不符、文件缺失、恢复条件、Android 复制回退、dry-run、验证页误分类、veto 地图误判、全部完成时离线恢复，以及验证阻塞后不再请求第二场。另有基准压缩包的真实 unrar 校验及 Dust2 文件头/哈希校验。新批量脚本的实时 HLTV 下载仍未端到端跑通，原全量索引未恢复；本 PR 不声明解决站点验证。

参考：
- Playwright 下载事件及保存： https://playwright.dev/python/docs/downloads
- 官方 unrar 来源： https://www.rarlab.com/download.htm
- 基准存档： https://github.com/ndx700/nadeatlas-demo-service/releases/tag/demo-epl-s24-falcons-vs-aurora
