#!/usr/bin/env python3
"""Can a plain HTTP client (a GitHub runner) fetch an HLTV r2-demos direct link once the phone has
resolved it? Writes data/probes/hltv-r2.json. Only reads the first KB of each file."""
import json, time, urllib.error, urllib.request
from pathlib import Path

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
R2 = "https://r2-demos.hltv.org/demos/131573/esl-pro-league-season-24-falcons-vs-aurora-bo3-SHwp6i5EMXqaP-2XyfqBwr.rar"
TESTS = [
    ("r2_plain", R2, {}),
    ("r2_referer", R2, {"Referer": "https://www.hltv.org/"}),
    ("r2_bad_token", R2.replace("SHwp6i5EMXqaP", "AAAAAAAAAAAAA"), {}),
    ("hltv_download_endpoint", "https://www.hltv.org/download/demo/131573", {}),
    ("hltv_results", "https://www.hltv.org/results?map=de_dust2&rankingFilter=Top20", {}),
]


def probe(url, extra):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*", "Range": "bytes=0-1023", **extra})
    t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            body = r.read(1024)
            return {"status": r.status, "finalUrl": r.geturl(), "type": r.headers.get("content-type"),
                    "contentRange": r.headers.get("content-range"), "length": r.headers.get("content-length"),
                    "server": r.headers.get("server"), "head": body[:16].hex(), "rar": body.startswith(b"Rar!"),
                    "ms": int((time.time() - t) * 1000)}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "type": e.headers.get("content-type"), "server": e.headers.get("server"),
                "cfMitigated": e.headers.get("cf-mitigated"), "body": e.read(300).decode("utf-8", "ignore")}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


out = {"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
for name, url, extra in TESTS:
    out[name] = probe(url, extra)
    print(name, json.dumps(out[name], ensure_ascii=False))
p = Path("data/probes/hltv-r2.json")
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(out, ensure_ascii=False, indent=2), "utf-8")
