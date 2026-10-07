# Demo 存档索引

HLTV demo 原始文件以 GitHub Release 附件形式存档（单文件超 git 100MB 限制），
本文件登记每场 demo 的存放位置、内含地图与校验信息。

> **注意**：一个 `.rar` 是一个比赛的**完整 demo 包**，内含该场打过的所有地图
> （BO3 通常 2-3 张图）。所以按图检索时，同一文件会在多张地图下出现，不会重复占空间。
> 下载脚本与完整方法论见 `hltv-demo-download/`（自托管 Runner / 手机 Termux 使用；
> GitHub 托管 Runner 的 Azure IP 段被 r2-demos.hltv.org 封禁）。

## 试点批次 Dust2 · Pilot 2026-10（更新于 2026-10-07 23:03）

- **Release**: [dust2-pilot-2026-10](https://github.com/ndx700/nadeatlas-demo-service/releases/tag/dust2-pilot-2026-10)
- **范围**: Spirit / Vitality / MOUZ / FURIA / Falcons / Lynn Vision，2026-09-07 ~ 2026-10-07
- **进度**: 已下载 21 场（11.6 GB）／索引共 51 场，剩余 32 场下载中
- **内容**: 这 51 场覆盖 7 张地图（Dust2 / Mirage / Inferno / Ancient / Nuke / Cache / Anubis）
- **完整性**: 每个附件配 `.sha256` 边车；校验用官方 `unrar t`（7-Zip 23.01 对 RAR5 会误报 Unsupported Method）

### 按地图检索

| 地图 | 已下载场次 | 说明 |
|---|---:|---|
| Dust2 | 20 | |
| Ancient | 11 | |
| Mirage | 11 | |
| Anubis | 5 | |
| Nuke | 5 | |
| Inferno | 4 | |
| Cache | 2 | |

### 已下载场次明细

| # | 队伍 | 比赛 | 内含地图 | 大小 | SHA-256（前16位） |
|---:|---|---|---|---:|---|
| 1 | falcons | 100-thieves-vs-falcons-blast-bounty-2026-season-2 | Nuke/Dust2/Anubis | 710 MB | `173ad5c704c6dc14` |
| 2 | falcons | falcons-vs-astralis-esports-world-cup-2026 | Ancient/Dust2/Mirage | 473 MB | `0fd4d7c7faa5c11b` |
| 3 | falcons | falcons-vs-aurora-esl-pro-league-season-24 |  | 406 MB | `8e6befd046789c6d` |
| 4 | falcons | falcons-vs-g2-blast-open-porto-2026 | Inferno/Dust2/Mirage | 490 MB | `8f0b77e74200740e` |
| 5 | falcons | falcons-vs-k27-esports-world-cup-2026 | Dust2 | 204 MB | `673c635b19f17d03` |
| 6 | falcons | falcons-vs-lynn-vision-blast-open-porto-2026 | Inferno/Ancient/Dust2 | 679 MB | `6e92dc96b8e9ac7c` |
| 7 | falcons | falcons-vs-the-mongolz-esports-world-cup-2026 | Inferno/Dust2/Nuke | 385 MB | `38f5be69b6941c14` |
| 8 | falcons | legacy-vs-falcons-blast-open-porto-2026 | Mirage/Ancient/Dust2 | 656 MB | `2fb3b04becde913e` |
| 9 | falcons | legacy-vs-falcons-esports-world-cup-2026 | Mirage/Dust2/Ancient | 482 MB | `c43aae7fd7ff61af` |
| 10 | falcons | spirit-vs-falcons-blast-open-porto-2026 | Nuke/Ancient/Dust2 | 472 MB | `64dd4f3343a19cd7` |
| 11 | falcons | spirit-vs-falcons-iem-cologne-major-2026 | Anubis/Mirage/Dust2 | 948 MB | `1ff354c57c59ba5f` |
| 12 | falcons | vitality-vs-falcons-esl-pro-league-season-24 | Anubis/Dust2/Mirage | 635 MB | `e049f297bc3bd39f` |
| 13 | lynn-vision | falcons-vs-lynn-vision-blast-open-porto-2026 | Inferno/Ancient/Dust2 | 679 MB | `6e92dc96b8e9ac7c` |
| 14 | spirit | b8-vs-spirit-esports-world-cup-2026 | Dust2/Mirage/Ancient | 473 MB | `e318c309aaa668a0` |
| 15 | spirit | g2-vs-spirit-blast-open-porto-2026 | Dust2/Cache/Ancient | 463 MB | `e3c11dda854366b6` |
| 16 | spirit | legacy-vs-spirit-esports-world-cup-2026 | Dust2/Ancient/Mirage | 483 MB | `01af1d3d7b5cfdab` |
| 17 | spirit | luminosity-vs-spirit-esports-world-cup-2026 | Ancient/Dust2/Nuke | 534 MB | `e3955b8398c75963` |
| 18 | spirit | spirit-vs-big-esports-world-cup-2026 | Cache/Dust2/Mirage | 694 MB | `1632da82b541a4bb` |
| 19 | spirit | spirit-vs-parivision-esl-pro-league-season-24 | Ancient/Dust2/Anubis | 673 MB | `dbc1eb5268485dea` |
| 20 | spirit | spirit-vs-shinden-esl-pro-league-season-24 | Dust2/Nuke/Mirage | 675 MB | `52abc6ab51157cb8` |
| 21 | vitality | vitality-vs-falcons-esl-pro-league-season-24 | Anubis/Dust2/Mirage | 635 MB | `e049f297bc3bd39f` |

### 待下载场次

| 队伍 | 比赛 | 内含地图 | 状态 |
|---|---|---|---|
| falcons | falcons-vs-aurora-esl-pro-league-season-24 | Mirage/Dust2/Anubis | 下载中 |
| falcons | furia-vs-falcons-iem-cologne-major-2026 | Mirage/Anubis/Inferno/Dust2/Nuke | 下载中 |
| vitality | vitality-vs-1win-esl-pro-league-season-24 | Dust2/Cache/Inferno | 下载中 |
| vitality | vitality-vs-magic-starladder-starseries-fall-2026 | Mirage/Dust2/Inferno | 下载中 |
| vitality | mouz-vs-vitality-blast-open-porto-2026 | Dust2/Mirage/Inferno | 下载中 |
| vitality | furia-vs-vitality-blast-open-porto-2026 | Nuke/Cache/Dust2 | 下载中 |
| vitality | fut-vs-vitality-blast-open-porto-2026 | Anubis/Dust2/Cache | 下载中 |
| vitality | vitality-vs-legacy-blast-open-porto-2026 | Nuke/Mirage/Dust2 | 下载中 |
| vitality | vitality-vs-9z-blast-open-porto-2026 | Dust2/Nuke/Cache | 下载中 |
| vitality | vitality-vs-inner-circle-blast-open-porto-2026 | Anubis/Cache/Dust2 | 下载中 |
| vitality | faze-vs-vitality-esports-world-cup-2026 | Dust2/Cache/Nuke | 下载中 |
| mouz | mouz-vs-vitality-blast-open-porto-2026 | Dust2/Mirage/Inferno | 下载中 |
| mouz | spirit-vs-mouz-esl-pro-league-season-24 | Dust2/Mirage/Nuke | 下载中 |
| mouz | furia-vs-mouz-esl-pro-league-season-24 | Cache/Mirage/Dust2 | 下载中 |
| mouz | mouz-vs-nrg-starladder-starseries-fall-2026 | Cache/Inferno/Dust2 | 下载中 |
| mouz | mouz-vs-9z-blast-open-porto-2026 | Cache/Nuke/Dust2 | 下载中 |
| mouz | fut-vs-mouz-esports-world-cup-2026 | Dust2/Ancient/Mirage | 下载中 |
| mouz | mouz-vs-parivision-esports-world-cup-2026 | Dust2/Inferno/Ancient | 下载中 |
| mouz | lynn-vision-vs-mouz-esports-world-cup-2026 | Dust2 | 下载中 |
| furia | furia-vs-vitality-blast-open-porto-2026 | Nuke/Cache/Dust2 | 下载中 |
| furia | furia-vs-mouz-esl-pro-league-season-24 | Cache/Mirage/Dust2 | 下载中 |
| furia | furia-vs-9z-esl-pro-league-season-24 | Nuke/Inferno/Mirage/Nuke/Inferno/Mirage/Cache/Dust2/Ancient/Anubis/Nuke/Inferno/Mirage/Cache/Dust2/Ancient/Anubis/Nuke/Inferno/Mirage/Cache/Dust2/Ancient/Anubis | 下载中 |
| furia | furia-vs-aurora-esl-pro-league-season-24 | Dust2/Mirage/Nuke | 下载中 |
| furia | vitality-vs-furia-starladder-starseries-fall-2026 | Mirage/Dust2/Cache | 下载中 |
| furia | furia-vs-g2-fissure-playground-3 | Ancient/Dust2/Mirage | 下载中 |
| furia | legacy-vs-furia-fissure-playground-3 | Mirage/Ancient/Dust2 | 下载中 |
| furia | furia-vs-gamerlegion-fissure-playground-3 | Cache/Mirage/Dust2 | 下载中 |
| lynn-vision | lynn-vision-vs-mouz-esports-world-cup-2026 | Dust2 | 下载中 |
| lynn-vision | lynn-vision-vs-the-huns-esl-challenger-league-season-52-asia-pacific-cup-2 | Nuke/Inferno/Dust2 | 下载中 |
| lynn-vision | lynn-vision-vs-vitalem-aerem-esl-challenger-league-season-52-asia-pacific-cup-2 | Ancient/Dust2/Inferno | 下载中 |
| lynn-vision | lynn-vision-vs-ur-esl-challenger-league-season-52-asia-pacific-cup-2 | Default/Inferno/Dust2 | 下载中 |
| lynn-vision | lynn-vision-vs-depo-iem-beijing-2026-asia-closed-qualifier | Ancient/Dust2/Cache | 下载中 |
| lynn-vision | lynn-vision-vs-nexvoid-iem-beijing-2026-asia-closed-qualifier | Inferno/Dust2/Nuke | 下载中 |
| lynn-vision | rare-atom-vs-lynn-vision-iem-beijing-2026-asia-closed-qualifier | Cache/Dust2/Inferno | 下载中 |
| lynn-vision | fut-vs-lynn-vision-blast-open-porto-2026 | Dust2/Anubis/Ancient | 下载中 |
| lynn-vision | lynn-vision-vs-vitality-esports-world-cup-2026 | Dust2/Inferno/Anubis | 下载中 |
| lynn-vision | lynn-vision-vs-ground-zero-ggmedia-challenger-series-1-blast-premier-rising-event | Nuke/Dust2/Inferno | 下载中 |

---

## 历史存档

### ESL Pro League Season 24 · Falcons vs Aurora（BO3）

- **Release**: [demo-epl-s24-falcons-vs-aurora](https://github.com/ndx700/nadeatlas-demo-service/releases/tag/demo-epl-s24-falcons-vs-aurora)
- **附件**: `esl-pro-league-season-24-falcons-vs-aurora-bo3.rar`（406.6 MB）+ `.sha256`
- **内含**: `falcons-vs-aurora-m1-mirage.dem`、`falcons-vs-aurora-m2-dust2.dem`
- **SHA-256**: `8e6befd046789c6d6286629dc95ff326f5dd91a47b78ad6ce25f031eda404e22`
- **状态**: 验收基准文件（亦以 `falcons-vs-aurora-esl-pro-league-season-24.rar` 收录于试点批次 Release）
