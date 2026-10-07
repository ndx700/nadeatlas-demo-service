# HLTV 自托管下载运行说明

这份工作流需要先有真实的自托管 Runner。`runs-on` 不会创建电脑、云主机或网络来源。本次没有确认在线自托管机器，也没有取得自托管下载成功结果。

## 已修正的内容

- 使用已修复的 `scripts/download_demo.py`，不再调用不存在的根目录脚本。
- 仅手动触发，使用 `contents:read` 权限，定向运行到带 `self-hosted` 和 `hltv-demo` 两个标签的 Runner。
- 默认输入 `/download/demo/131573` 端点；也可输入当前有效的 RAR 直链。旧直链是否有效尚未确认。
- 使用独立 Python venv 和固定 Playwright 版本，不自动改动机器的系统包。
- 使用 7-Zip 的 `t` 命令验证完整性，再选择是否解压；解决 `rar`/`unrar` 名称不一致问题。
- 每次运行使用独立临时输出目录和产物名称，避免覆盖旧文件。
- 成功时保存真实 RAR 和可选解压文件，失败时保存截图与诊断。产物保留 7 天，不等于永久 Release 保存。

## 机器准备

1. 在仓库的 Runner 设置中连接自己管理的 Linux、Windows 或 macOS 机器，增加自定义标签 `hltv-demo`，保持 Runner 在线。
2. 安装支持 RAR 的 7-Zip，并确保 `7z` 或 `7zz` 在 Runner 的 PATH 中。Linux 还需安装 Xvfb 和 Chromium 所需系统依赖。
3. Windows 和 macOS 使用有图形界面的用户会话；Linux 使用 Xvfb。Xvfb 不提供人工操作界面，遇到需人工验证的页面时，任务仍可能失败。
4. 准备好后合并 PR，工作流需要进入默认分支才能通过 `workflow_dispatch` 手动触发。
5. 选择 `Download HLTV Demo on self-hosted runner`，输入 demo 端点或当前有效直链；选择是否解压，然后启动。

没有匹配的在线 Runner 时，任务不能开始。只有手机并不自动满足这份桌面 Runner 工作流的执行条件。

## 判断是否成功

退出码 0 表示脚本保存了通过 RAR 文件头校验的文件，工作流还必须通过 `7z t` 才会上传成功产物。退出码 2 表示观测到封禁页，不证明原因仅限 IP；3 表示观测到挑战；4 表示对象不存在；1 为其他错误。

上一次 GitHub 托管环境的实测得到 307 后 403、退出码 3。用户提供的“住宅 IP 下载了 407MB”说明尚未在当前会话复现，不能作为本次成功记录。切换自托管机器也不保证站点会允许下载。

## 当前交付边界

代码和工作流已准备，尚未合并。没有启动自托管任务，没有新增 demo、Release 或正式地图索引。成功下载后，还需确认 .dem 内容和地图，再进入沙二索引与永久保存流程。

## 官方说明

- https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/use-in-a-workflow
- https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow
- https://playwright.dev/python/docs/browsers
