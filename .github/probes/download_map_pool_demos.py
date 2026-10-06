#!/usr/bin/env python3
import json, os, re, hashlib, urllib.request
from datetime import datetime, timezone
BASE="https://cs.rlin.dev"; UA="NadeAtlasMapPoolBackfill/1.0"
START_TS=int(datetime(2026,4,6,tzinfo=timezone.utc).timestamp())
MAPS={"de_mirage","de_inferno","de_nuke","de_ancient","de_anubis","de_cache"}
EVENTS=["8049","8243","8301","9154","8249"]
def req(url,accept="*/*"):
 return urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":UA,"Accept":accept}),timeout=120)
def js(url):
 with req(url,"application/json") as r:return json.load(r)
os.makedirs("downloads/map-pool",exist_ok=True); out=[]
for event in EVENTS:
 try:
  page=req(f"{BASE}/pro-games?event={event}").read().decode("utf-8","ignore")
 except Exception as e:
  print("EVENT_ERR",event,repr(e)); continue
 ids=sorted(set(re.findall(r'hltv-(\d+)-m(\d+)',page)))
 print("EVENT",event,"MAP_IDS",len(ids))
 for series,mapno in ids:
  mid=f"hltv-{series}-m{mapno}"; data=None
  for api in (f"{BASE}/api/matches/{mid}",f"{BASE}/api/match/{mid}",f"{BASE}/api/viewer/{mid}",f"{BASE}/api/demo/{mid}"):
   try:
    x=js(api)
    if isinstance(x,dict) and x.get("demoUrl"): data=x; break
   except: pass
  if not data or data.get("mapName") not in MAPS: continue
  ts=int(data.get("matchTime") or 0)
  if ts and ts<START_TS: continue
  mp=data["mapName"]; url=data["demoUrl"]; d=os.path.join("downloads/map-pool",mp); os.makedirs(d,exist_ok=True)
  name=re.sub(r'[^A-Za-z0-9._-]+','_',url.rsplit('/',1)[-1]); path=os.path.join(d,name)
  try:
   with req(url) as r:
    head=r.read(8)
    if head!=b"PBDEMS2\x00": print("REJECT",mid,mp,head); continue
    h=hashlib.sha256(); h.update(head); size=8
    with open(path,"wb") as f:
     f.write(head)
     while True:
      b=r.read(1024*1024)
      if not b: break
      f.write(b); h.update(b); size+=len(b)
   rec={"matchId":mid,"date":datetime.fromtimestamp(ts,timezone.utc).strftime("%Y-%m-%d") if ts else None,"name":data.get("name"),"map":mp,"url":url,"size":size,"sha256":h.hexdigest(),"file":path}
   out.append(rec); print("OK",json.dumps(rec,ensure_ascii=False))
  except Exception as e: print("DOWNLOAD_ERR",mid,mp,repr(e))
with open("downloads/map-pool/manifest.json","w") as f:json.dump(out,f,ensure_ascii=False,indent=2)
print("TOTAL_OK",len(out))
for m in sorted(MAPS): print("MAP_TOTAL",m,sum(x["map"]==m for x in out))
