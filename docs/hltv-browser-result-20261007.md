# HLTV browser download result — 2026-10-07

Run: https://github.com/ndx700/nadeatlas-demo-service/actions/runs/37603546100

Environment: GitHub ubuntu-latest, Python 3.12, Playwright 1.63.0, headed Chromium under Xvfb.

Browser installation and launch succeeded. Navigation to the existing Falcons vs Aurora demo 131573 direct RAR URL returned document responses 307 then 403. No download event arrived within 90 seconds. The downloader classified the observed page as a challenge (exit 3), not an IP-block page. This does not establish whether the original archive URL is still valid behind that challenge, or whether another authorized device can download it.

No demo archive was downloaded or added to the library/index/Release. Five diagnostic files (session screenshot/text, failure screenshot/text, result.json) were saved in the Actions artifact:
https://github.com/ndx700/nadeatlas-demo-service/actions/runs/37603546100/artifacts/11473747742

Do not interpret the successful diagnostic upload as a successful demo download. The successful-demo artifact step was skipped.
