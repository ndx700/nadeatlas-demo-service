#!/usr/bin/env python3
import json, socket, urllib.error, urllib.request
from pathlib import Path

rel="demos/manually_uploaded/1791318510_legacy-vs-m80-m3-dust2.dem"
hosts=[
 f"https://files.bo3.gg/{rel}",
 f"https://files.bo3.gg/uploads/{rel}",
 f"https://api.bo3.gg/{rel}",
 f"https://api.bo3.gg/storage/{rel}",
 f"https://api.bo3.gg/api/v1/{rel}",
 f"https://bo3.gg/{rel}",
 f"https://cdn.bo3.gg/{rel}",
 f"https://static.bo3.gg/{rel}",
 f"https://demos.bo3.gg/{rel}",
]
out={}
for u in hosts:
 try:
  req=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0","Accept":"*/*","Range":"bytes=0-31","Referer":"https://bo3.gg/"})
  with urllib.request.urlopen(req,timeout=20) as r:
   b=r.read(32)
   out[u]={"status":r.status,"final":r.geturl(),"type":r.headers.get("content-type"),"length":r.headers.get("content-length"),"range":r.headers.get("content-range"),"head":b.hex(),"ascii":repr(b)}
 except urllib.error.HTTPError as e:
  b=e.read(128)
  out[u]={"status":e.code,"final":e.geturl(),"type":e.headers.get("content-type"),"length":e.headers.get("content-length"),"head":b[:32].hex(),"body":b.decode("utf-8","ignore")}
 except Exception as e:
  out[u]={"error":f"{type(e).__name__}: {e}"}
 print(u,out[u])
Path("data/probes/bo3-demo-hosts.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
