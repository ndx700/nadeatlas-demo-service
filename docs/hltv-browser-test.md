# HLTV browser download test

This test uses visible Playwright Chromium navigation for the entire HLTV flow. It does not solve CAPTCHAs, forge clearance cookies, or use an HTTP fallback.

```sh
python -m pip install playwright==1.63.0
python -m playwright install --with-deps chromium
xvfb-run -a python scripts/download_demo.py 'https://www.hltv.org/download/demo/131573' demo.rar --diag-dir diagnostics
7z t demo.rar
```

Fixes: argparse positional handling; guarded startup and session navigation; evidence-based error classification; bounded event and transfer waits; finally cleanup; temporary download validation; complete RAR magic; SHA-256; no overwriting existing output.

Exit codes: 0 saved file with valid RAR signature, 1 other failure, 2 block page (does not prove IP-only blocking), 3 identifiable challenge, 4 missing object. Failure diagnostics include JSON and best-effort screenshot/text. A RAR signature alone is not an integrity test; the workflow additionally runs `7z t`.

The isolated workflow has contents:read, uses ubuntu-latest, and saves successful archives as Actions artifacts. It does not publish Releases or update map indexes. A downloaded series archive is not proof that its maps are Dust2. The historical direct link may have expired.

Local checks passed for CLI argument parsing and error classification. The local execution stopped at browser startup because the Chromium download failed, so it produced no HLTV network result. Cloud test: https://github.com/ndx700/nadeatlas-demo-service/actions/runs/37603546100
