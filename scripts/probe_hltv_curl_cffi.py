#!/usr/bin/env python3
from curl_cffi import requests
import json, os

URL="https://www.hltv.org/download/demo/106303"
s=requests.Session(impersonate="chrome124")
s.headers.update({"Accept-Language":"en-US,en;q=0.9"})
print("GET",URL)
r=s.get(URL,stream=True,timeout=120,allow_redirects=True)
print("status",r.status_code)
print("url",r.url)
print("type",r.headers.get("content-type"))
print("length",r.headers.get("content-length"))
print("server",r.headers.get("server"))
first=b""
try:
    for chunk in r.iter_content(chunk_size=64):
        if chunk:
            first+=chunk
            if len(first)>=64:
                break
finally:
    r.close()
print("head",first[:64],first[:64].hex())
ok=first.startswith(b"Rar!")
result={"status":r.status_code,"url":str(r.url),"content_type":r.headers.get("content-type"),"head_hex":first[:64].hex(),"rar":ok}
os.makedirs("data/probes",exist_ok=True)
open("data/probes/hltv-curl-cffi.json","w").write(json.dumps(result,indent=2)+"\n")
raise SystemExit(0 if ok else 3)
