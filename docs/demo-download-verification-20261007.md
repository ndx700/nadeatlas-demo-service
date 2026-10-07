# Demo 下载复核 2026年10月7日

## GitHub Release 文件完整下载成功

文件：2026-09-04-furia-vs-vitality-dust2.dem

下载地址：https://github.com/ndx700/nadeatlas-demo-service/releases/download/demos/2026-09-04-furia-vs-vitality-dust2.dem

本次下载最终 HTTP 200，完整保存 293349942 字节，与 Release 元数据一致。文件头为 PBDEMS2 加空字节，符合 CS2 demo 标识。SHA-256 为 `11f095dc6dd0dc9d10976f1b929ee6a1272a6651c85f3fb7247356e3da709be3`，与 GitHub asset digest 一致。传输耗时约 23.3 秒。此结果验证文件传输与哈希一致，不代替比赛解析验证。

Release 当前列出 11 个 .dem 文件。本次完整下载验证了上述一个文件，未逐个重新下载其余十个。

## HLTV 有界面 Chromium 复测失败

同一个 browser-only 云端任务重新运行，GitHub job 112749496943。主站会话页面成功打开，标题为 Counter-Strike News & Coverage | HLTV.org。

下载域名 r2-demos.hltv.org 的响应为 307 后 403。90 秒内没有 download 事件，退出码为 3。实际诊断页面标题为 Just a moment...，正文显示 Performing security verification，并明确说明正在验证是否为机器人。因此可以确认：本次 GitHub 托管云端浏览器未通过下载域名的 Cloudflare 安全验证。未出现 Sorry, you have been blocked 封禁页，不能证明 IP 永久封禁。对象是否存在仍未得到验证。

本次没有新的 HLTV RAR 文件，成功文件产物步骤被跳过。

任务：https://github.com/ndx700/nadeatlas-demo-service/actions/runs/37603546100

复测诊断：https://github.com/ndx700/nadeatlas-demo-service/actions/runs/37603546100/artifacts/11475638896

## 自托管状态

手动自托管工作流的 runner.temp 作用域错误已修正，提交 a8e997b2b516a7ef7d3d3ab0b03fa7cefd53a7ba。目前浏览器 GitHub 登录未成功，连接接口不提供 Runner 清单和 workflow_dispatch 操作；因此本次未确认在线自托管机器，也未启动自托管任务。浏览器登录障碍与 HLTV 下载域名的安全验证是两个独立问题。
