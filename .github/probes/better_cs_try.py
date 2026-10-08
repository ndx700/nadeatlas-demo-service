#!/usr/bin/env python3
"""A few paid look-ups (1 credit each) named in PATHS, saved to data/probes/better-cs-samples/ to see what they hold."""
import json, os, re, urllib.request, urllib.error
API = "https://api.better-cs-api.com"; KEY = os.getenv("BETTER_CS_API_KEY", "").strip()
os.makedirs("data/probes/better-cs-samples", exist_ok=True)
for path in os.getenv("PATHS", "").split():
    req = urllib.request.Request(API + path, headers={"Authorization": f"Bearer {KEY}", "Accept": "application/json", "User-Agent": "NadeAtlas-Demo-Service/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r: code, body = r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e: code, body = e.code, e.read()[:3000].decode("utf-8", "replace")
    except Exception as e: code, body = 0, repr(e)
    if KEY and KEY in body: body = "redacted"
    name = re.sub(r"[^a-zA-Z0-9]+", "_", path).strip("_")
    open(f"data/probes/better-cs-samples/{name}.json", "w").write(body)
    print(f"::notice::{path} -> {code} ({len(body)} bytes) {body[:150] if code != 200 else ''}")
