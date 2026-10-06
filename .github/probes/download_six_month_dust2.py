#!/usr/bin/env python3
"""Download and verify public CS2 Dust2 demos from cs.rlin.dev for the last ~6 months.
Only public endpoints are used. Files must start with PBDEMS2 to be accepted.
"""
import json, os, re, time, hashlib, urllib.request
from datetime import datetime, timezone

START_TS=int(datetime(2026,4,6,tzinfo=timezone.utc).timestamp())
BASE="https://cs.rlin.dev"
UA="NadeAtlasDemoSync/1.0"

def get_json(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=60) as r:
        return json.load(r)

def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"*/*"})
    return urllib.request.urlopen(req,timeout=120)

# Public pro-games page/API currently exposes match IDs; seed known events and discover series.
EVENTS=["8049","8243","8301","9154","8249"]
out=[]
os.makedirs("downloads/dust2",exist_ok=True)
for event in EVENTS:
    page=urllib.request.urlopen(urllib.request.Request(f"{BASE}/pro-games?event={event}",headers={"User-Agent":UA}),timeout=60).read().decode("utf-8","ignore")
    ids=sorted(set(re.findall(r'hltv-(\d+)-m(\d+)',page)))
    print("EVENT",event,"MAP_IDS",len(ids))
    for series,mapno in ids:
        mid=f"hltv-{series}-m{mapno}"
        candidates=[
          f"{BASE}/api/matches/{mid}",
          f"{BASE}/api/match/{mid}",
          f"{BASE}/api/viewer/{mid}",
          f"{BASE}/api/demo/{mid}",
        ]
        data=None
        for api in candidates:
            try:
                x=get_json(api)
                if isinstance(x,dict) and x.get("demoUrl"):
                    data=x; break
            except Exception:
                pass
        if not data or data.get("mapName")!="de_dust2": continue
        ts=int(data.get("matchTime") or 0)
        if ts and ts<START_TS: continue
        url=data["demoUrl"]
        name=re.sub(r'[^A-Za-z0-9._-]+','_',url.rsplit('/',1)[-1])
        path=os.path.join("downloads/dust2",name)
        try:
            with get(url) as r:
                total=int(r.headers.get("Content-Length") or 0)
                head=r.read(8)
                if head!=b"PBDEMS2\x00":
                    print("REJECT_HEADER",mid,head,url); continue
                h=hashlib.sha256(); h.update(head); size=len(head)
                with open(path,"wb") as f:
                    f.write(head)
                    while True:
                        b=r.read(1024*1024)
                        if not b: break
                        f.write(b); h.update(b); size+=len(b)
            rec={"matchId":mid,"date":datetime.fromtimestamp(ts,timezone.utc).strftime("%Y-%m-%d") if ts else None,
                 "name":data.get("name"),"map":"de_dust2","url":url,"size":size,"sha256":h.hexdigest(),"file":path}
            out.append(rec)
            print("OK",json.dumps(rec,ensure_ascii=False))
        except Exception as e:
            print("DOWNLOAD_ERR",mid,repr(e))
with open("downloads/dust2/manifest.json","w",encoding="utf-8") as f:
    json.dump(sorted(out,key=lambda x:x.get("date") or "",reverse=True),f,ensure_ascii=False,indent=2)
print("TOTAL_OK",len(out))
