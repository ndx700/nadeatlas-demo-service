#!/usr/bin/env python3
"""Reads better-cs-api's own description of its endpoints (no paid look-ups) and the account balance when the API
offers one, and saves them to data/probes/better-cs-api.json."""
import json, os, urllib.request
API = "https://api.better-cs-api.com"
KEY = os.getenv("BETTER_CS_API_KEY", "").strip()
out = {}
for path in ["/openapi.json", "/swagger.json", "/docs/openapi.json", "/api-docs", "/v1/openapi.json", "/", "/docs",
             "/me", "/account", "/balance", "/credits", "/usage"]:
    req = urllib.request.Request(API + path, headers={"Authorization": f"Bearer {KEY}", "Accept": "application/json", "User-Agent": "NadeAtlas-Demo-Service/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read()[:400000].decode("utf-8", "replace")
            out[path] = {"status": r.status, "type": r.headers.get("Content-Type"), "body": body if len(body) < 200000 else body[:200000]}
    except urllib.error.HTTPError as e:
        out[path] = {"status": e.code, "body": e.read()[:2000].decode("utf-8", "replace")}
    except Exception as e:
        out[path] = {"error": repr(e)}
    if KEY and KEY in json.dumps(out[path]): out[path] = {"redacted": True}
    print(f"::notice::{path} -> {out[path].get('status', out[path].get('error'))}")
os.makedirs("data/probes", exist_ok=True)
json.dump(out, open("data/probes/better-cs-api.json", "w"), ensure_ascii=False, indent=1)
